# DRY 0.0.15 upstream seams: to-do list

These are the places where the package re-derives, hand-models or copies something an upstream library already
exposes. AGENTS.md line 6 governs them: ask upstream through its own seam; where there is no seam, adapt upstream's
code with attribution; hand-model only as a last resort. The list comes from a six-agent read-only sweep at
`b890b75b`, one agent per area:
- optimizer and pagination;
- ORM utils and permissions;
- filters and orders;
- forms, mutations and DRF;
- types, schema and Relay;
- transport, extensions and patches.

It also carries the items still open from the first sweep (O, F and S ids).

The first sweep's removals already landed as `ed9be44a` (O1), `3ed8565a` (O3), `61deefd3` (F4, F10), `6f555782` (F6),
`3f99e6d5` (F7), `036d3d37` (F9), `05ceb214` (S3), `9d12b310` (S7), `a935a894` (S8) and `7b059c0d` (S9).
They are not repeated here.

How to read the entries:
- **Status:**
  - CONFIRMED means a probe compared ours with upstream on fakeshop. The diff count is given.
  - SUSPECTED means read only.
- **Lines** are the agents' net estimates.
- **"Reason to keep ours: none"** means the swap is a plain replacement.
- **An item whose behaviour change says "fixes"** keeps a known defect for as long as our copy stays.

Every item is a candidate, not a plan. Each one still gets the research pass, a root-cause fix and a live test before
it lands with its tick.

## Fixes behaviour (our copy is wrong today)

- [x] 1. (OPT-1, was S4 + the argument half of S1) Nested planner and plan-cache key read connection arguments by wire
  name
  - Our code (deleted): `nested_planner.py`'s `_argument_value` and `_coerce_pagination_int`, `walker.py`'s
    `_normalized_alias_payload`, `utils/connections.py`'s `CONNECTION_ORDER_KWARG_GRAPHQL` and `orderBy` twin read,
    and the wire-literal `_PAGINATION_ARG_NAMES` in `optimizer/extension.py`.
  - Upstream: `graphql/execution/values.py::get_argument_values(field_def, node, variable_values)`, re-keyed by
    `utils/typing.py::published_python_name`. Public, present at 3.2.0.
  - Landed:
    - `optimizer/selections.py::ast_to_converted_selections` threads the parent GraphQL type and stamps each field
      selection's coerced, Python-named arguments (`python_arguments`). The planner, the alias merge and the sidecar
      predicate read only those.
    - The plan-cache key collects variables under every wire name the schema publishes a pagination argument under
      (`optimizer/extension.py::_pagination_wire_names`, memoized per schema). The document-key cache keys on that
      set too.
  - Status: CONFIRMED worse than the sweep said. On the old code a renamed or swapped `first`/`last` served wrong
    rows, because the resolver consumed the dead window:
    - `last`→`tail: 1` returned all 3 books instead of the last one;
    - swapped, wire `last: 1` returned empty pages.

    15 of the 19 new live rows failed on the old code; all pass now.
  - Behaviour change: fixes wrong rows, overfetch to `relay_max_results`, a missed strictness N+1 and a plan-cache
    key that ignored renamed variables, under any `NameConverter` that renames or swaps a pagination argument.
  - Tests: the live rows in `test_library_api.py` on the `/graphql-test/` holder (renamed and swapped converters):
    - `test_nested_connection_window_reads_page_arguments_by_python_name`
    - `test_nested_connection_plan_cache_keys_a_renamed_page_variable`
    - `test_nested_connection_literal_and_variable_aliases_share_one_window`
    - `test_nested_connection_per_parent_page_stays_strictness_visible_under_any_names`

    Plus the union-arm package row in `tests/optimizer/test_selections.py`.
  - Follow-up: item 34. The resolver accepted a prefetched window whose bounds disagree with its own arguments.

- [x] 2. (OPT-2, was the name half of S1, plus the walker's hardcoded `to_camel_case`) The walker resolves selections
  by snake_case reversal, then re-runs the NameConverter
  - Our code (deleted): `walker.py`'s snake_case reversal, `_schema_name_converter`, `_relay_id_graphql_name`,
    `_graphql_names_by_python_name`, `_ForwardNames` / `_forward_names_memo`, `_build_forward_names`,
    `_forward_names` and `_field_by_graphql_name`; `selections.py`'s `ConnectionFieldNames`,
    `DEFAULT_CONNECTION_FIELD_NAMES` and `connection_field_names` (the `apply_naming_config` re-run).
  - Upstream: `GraphQLCoreConverter.DEFINITION_BACKREF`, read through `utils/typing.py::published_python_name`.
  - Landed:
    - `optimizer/selections.py::ast_to_converted_selections` stamps each field selection with the Python name of the
      field it selects (`selection_python_name`). The walker, the connection walks and the count predicates match by
      Python name only.
    - `optimizer/selections.py::info_selections` gives resolve time (`connection.py`) the same stamped selections.
    - The Relay GlobalID is recognised by `relay.Node`'s declared field.
  - Status: CONFIRMED. Three of the five new live rows failed on the old code:
    - `displayName` planned the `display_name` column: 4 statements, i.e. per-row deferred loads;
    - a converter-renamed connection vocabulary lost `totalCount` (`_django_total_count` missing).
  - Behaviour change: fixes wrong-column planning when two published names differ only by case or underscore, and
    connection planning under a converter that renames `edges`/`node`/`totalCount`/`hasNextPage`.
  - Tests:
    - `test_library_shapes_api.py::test_distributor_published_names_differing_by_case_each_project_their_own_column`.
      Fakeshop's `Distributor` gains `display_name` (migration `library/0019`).
    - `test_library_api.py::test_connection_vocabulary_renamed_by_the_name_converter_plans_what_the_defaults_plan`.
  - Follow-up: item 35. Strawberry hardcodes `edges`/`pageInfo` when deciding whether to resolve edges.
  - The tracked `examples/fakeshop/db.sqlite3` is not migrated to `library/0019`.

- [x] 3. (FLT-1, the remainder of F1) `_leaf_column` hand-walks the filter path and misses `FilteredRelation` aliases
  and `pk`
  - Our code (deleted): `filters/sets.py`'s `_leaf_column`.
  - Upstream: `Query.solve_lookup_type` then `Query.names_to_path` (through the existing
    `utils/querysets.py::_names_to_path` wrapper), the order `Query.build_filter` resolves a filter argument in.
  - Landed: `utils/querysets.py::lookup_target_fields(query, lookup)` returns the walk's targets, or an annotation's
    `output_field`, over the queryset the filter runs on. `FieldError` gives `()`.
    `filters/sets.py::_unbindable_temporal_errors` asks Django when any target is temporal. A path that ends on a
    relation is now checked against the target's key field too.
  - Status: CONFIRMED. On the old code the live row let `OverflowError: date value out of range` escape, and the
    package `pk` row did not raise.
  - Behaviour change: fixes the case where a temporal value Django cannot bind, sent through a `FilteredRelation`
    alias or a temporal primary key reached by `pk`, escaped as `OverflowError` instead of `FILTER_INVALID`.
  - Tests:
    - Live: `test_scalars_filter_api.py::test_datetime_crossing_a_filtered_relation_alias_outside_years_one_to_9999_is_filter_invalid`,
      over the new root field `allScalarSpecimensByParentStamp` (`ScalarSpecimenParentStampFilter`).
    - Package: `tests/filters/test_sets.py::test_temporal_primary_key_reached_through_pk_is_asked`. No fakeshop model
      has a temporal pk.

- [x] 4. (TYP-1, was S5, plus `mutations/inputs.py::_predicted_input_field_name`) The collision guards use
  `to_camel_case`, not the schema's `NameConverter`
  - Our code: the camel half of `types/finalizer.py`'s `_field_surface_names` / `_audit_field_surface` /
    `_synthesize_relation_connections` was removed, and so was `mutations/inputs.py`'s
    `_audit_mutation_input_surface`.
    - Finalize keeps the empty-surface check and the Python-name clobber check.
    - `_predicted_input_field_name` stays, only to seed the bind-time spec name.
  - Upstream: `strawberry/schema/name_converter.py::NameConverter.from_field` through `schema.config.name_converter`,
    over the schema's own `get_fields`, the walk `_get_thunk_mapping` does.
  - Landed: `schema.py::_refuse_field_name_collisions` runs at `DjangoSchema` build over every published object,
    interface and input type. It skips `strawberry.Private` fields and raises `ConfigurationError` naming the type,
    both fields and the wire text.
  - Status: CONFIRMED. All 8 new rows failed on the old code.
  - Behaviour change:
    - fixes a false refusal under `auto_camel_case=False` (`foo_bar` beside `fooBar`, `field_2` beside `field2`);
    - fixes a silent field drop under a custom converter;
    - a `(str, Enum)` `name=` now collides as its text (closes `dry-0_0_15_3.md` 13 and 56);
    - a consumer's plain `@strawberry.type` with a colliding pair is refused too, where Strawberry silently drops
      one;
    - a DjangoType served by a plain `strawberry.Schema` no longer gets a collision check.
  - Tests:
    - `tests/types/test_definition_order.py`: the default, `auto_camel_case=False`, custom-converter, explicit-name and
      StrEnum rows;
    - `tests/test_relay_connection.py::test_generated_name_graphql_collision_is_the_schema_converters`;
    - two `tests/mutations/test_inputs.py` rows;
    - `tests/test_schema.py::test_postponed_private_field_does_not_collide_with_the_name_it_spells`;
    - live: `test_library_shapes_api.py::test_distributor_unpinned_case_pair_is_served_by_a_snake_case_schema`.
  - `DistributorType`'s `name="display_name"` pin stays: under the shipped `auto_camel_case=True`, `display_name`
    really collides with `displayName`.

- [ ] 5. (TYP-2) A `GeneratedField` column has no conversion
  - Our code: `types/converters.py::_scalar_map_entry`, `::scalar_route` and `::convert_scalar`. No `GeneratedField`
    arm exists in `types/`.
  - Upstream: `django/db/models/fields/generated.py::GeneratedField.output_field`. Public, Django 5.0+.
    strawberry-django routes on it in `fields/types.py::resolve_model_field_type` (crib only).
  - Lines: about +4 (route on `field.output_field`).
  - Status: CONFIRMED.
    - `convert_scalar` raises `ConfigurationError: Unsupported Django field type 'GeneratedField'`.
    - `scalar_for_field(gf.output_field)` gives `int`.
  - Reason to keep ours: none.
  - Behaviour change: fixes the `Meta.fields = "__all__"` build failure on any model with a `GeneratedField`.
  - Risk / blockers:
    - Nullability reads `GeneratedField.null`, and the field has no write side.
    - Coordinate with spec-051, which plans the filter-side `GeneratedField` unwrap.
  - Owner: spec-051 Slice 2. The maintainer left the conversion to the builder flow; it lands with that slice, not
    here.

- [x] 6. (TYP-5) The Relay `resolve_node` default does not delegate to `resolve_nodes`
  - Our code: `types/relay.py`'s `_resolve_node_default`, `_resolve_node_async`, `_apply_node_filter` and the
    `resolve_node` row of `_RELAY_RESOLVER_DEFAULTS` were removed. The package injects three defaults.
  - Upstream: `strawberry/relay/types.py::Node.resolve_node` (public). It calls
    `cls.resolve_nodes(info=, node_ids=[node_id], required=)`.
  - Landed: `node(id:)`, `relay.node()` and `GlobalID.resolve_node` read one id through the type's `resolve_nodes`,
    the package default or a consumer's override.
    - A single id is still one query (`pk__in` of one value); `test_node_hidden_and_missing_issue_equal_queries_live`
      still pins it.
    - The batch path keeps the visibility hooks (sync and async), `SyncMisuseError`, `check_deadline` first and the
      `DoesNotExist` type on a `required=True` miss.
  - Status: CONFIRMED. The live row failed on the old code (the draft list answered its row instead of `null`).
  - Behaviour change:
    - fixes a consumer overriding only `resolve_nodes` being bypassed by every single-id refetch;
    - non-unique ids answer the last row, as upstream's `map_results` does, on both paths (the old single path
      raised `MultipleObjectsReturned` or returned the lowest pk);
    - a `required=True` miss message is now the batch path's (`"<Model>: no row matching pk='7'."`), same type.
  - Tests:
    - live: `test_library_api.py::test_node_refetch_reads_a_resolve_nodes_only_override_live`, over
      `ReadingListType`, which now overrides only `resolve_nodes` and withholds `DRAFT_READING_LIST_PREFIX` titles;
    - `tests/types/test_relay_interfaces.py` and `tests/test_registry.py` expect three injected resolvers.
  - Glossary: the `relay-node-integration`, `djangonodefield`, `check_deadline`, `execution-resource-policy` and
    `syncmisuseerror` bodies were rewritten in the DB and re-rendered.

- [x] 7. (TYP-6) The per-row node-type stamp duplicates `strawberry.cast` and ignores a consumer's cast
  - Our code: `types/relay.py`'s `_NODE_TYPE_HINT_ATTR` was removed. The `install_is_type_of` closure reads
    upstream's `TYPE_CAST_ATTRIBUTE` through `truth.static_attr` and answers `type_cast is type_cls`, the
    strawberry-django branch. `relay.py::_stamp_node_type` now calls `strawberry.cast`.
  - Upstream: `strawberry/types/cast.py::cast` and `::TYPE_CAST_ATTRIBUTE` (public, identical at 0.322.2).
  - Status: CONFIRMED. The live row failed on the old code (`BookType` answered where the cast named
    `NullabilityOverrideBookType`).
  - Behaviour change: fixes a consumer's `strawberry.cast(TypeB, row)` on a multi-type model being ignored on
    interface and union fields. The root `node`/`nodes` fields still cast their copy to the type the GlobalID
    named, over any cast a consumer `resolve_nodes` put on the row.
  - Tests:
    - live: `test_library_api.py::test_consumer_cast_book_resolves_to_the_secondary_type_under_node_over_http`, over
      the new `libraryCastSecondaryBookNodes` field behind `FAKESHOP_TEST_RELAY_SECONDARY_NODE`;
    - `tests/test_relay_node_field.py` and `tests/types/test_relay_interfaces.py` read `TYPE_CAST_ATTRIBUTE`.

- [x] 8. (TYP-7) Two `relay.NodeID` annotations fall back silently to `"pk"`
  - Our code: `types/relay.py::_stamp_relay_id_attr` keeps the `"pk"` fallback for zero candidates only; any other
    `NodeIDAnnotationError` is a `ConfigurationError` at finalize naming the type and embedding upstream's message.
  - Upstream: `strawberry/relay/types.py::Node.resolve_id_attr`. Its `NodeIDAnnotationError` carries the same
    `cls`, `rich_message` and `suggestion` for zero and for more than one candidate, so only the message opening
    (`types/relay.py::_NO_NODE_ID_MESSAGE`) tells them apart. The match is fail-closed: a reworded zero case is
    refused loudly, never read as `"pk"`.
  - Status: CONFIRMED. The new row did not raise on the old code.
  - Behaviour change: fixes a type with two `NodeID` fields silently encoding and filtering on the pk.
  - Tests: `tests/types/test_relay_interfaces.py::test_two_node_id_annotations_are_refused_not_read_as_pk`; the zero
    case stays pinned by `test_resolve_id_attr_falls_back_to_pk`.

- [x] 9. (WRT-1 = TYP-9, also tracked in `dry-0_0_15_3.md`) The model and auth flavors hardcode Django's English
  `"null"` message
  - Our code: `utils/errors.py::null_field_error(path, column)` sends the column's `error_messages["null"]`. Its
    callers pass the column: `mutations/resolvers.py::_explicit_null_error` and `::_created_row_integrity_errors`,
    `rest_framework/resolvers.py::_attempted_row_integrity_errors` (a caller the sweep missed), and
    `auth/mutations.py::_register_write_step`, which reads the user model's `password` column.
    `_decode_single_relation_id`'s null arm returns `_explicit_null_error` (`dry-0_0_15_3.md` item 17).
  - Upstream: `django/db/models/fields/__init__.py::Field.error_messages["null"]`, which the ModelForm flavor
    already reads in `forms/resolvers.py::_column_null_errors`.
  - Status: CONFIRMED. Four live cases (model and serializer, `itemId` omitted and `null`) and the package row failed
    on the old code.
  - Behaviour change: a custom or translated column `null` message now reaches the model, serializer and auth
    flavors as it already reached ModelForm. The wire `codes` stay `["null"]`.
  - Tests:
    - fakeshop `ItemHold.item` gets `error_messages={"null": "A hold needs an item."}` (migration
      `products/0004_item_hold_item_null_message.py`, state only);
    - live: `test_products_api.py::test_create_item_hold_null_item_is_a_field_error`, six cases that now agree;
    - `tests/utils/test_errors.py::test_null_field_error_and_empty_validation_error_leaf_shapes`.
  - Closes `dry-0_0_15_3.md` items 17 and 41.

- [x] 10. (WRT-2) The DRF non-field-errors key is captured once at import
  - Our code: the module constant `_DRF_NON_FIELD_KEY` was removed. `rest_framework/resolvers.py::_error_node_children`
    reads `api_settings.NON_FIELD_ERRORS_KEY` per dict node, as DRF's `as_serializer_error` does.
  - Upstream: `rest_framework/settings.py::api_settings` (public), reloaded on `setting_changed`.
  - Status: CONFIRMED. The live row failed on the old code at its second post (`field: "errors"` where `__all__` was
    expected). The capture happened at the lazy first import, so only a key changed after the first serializer
    request diverged.
  - Behaviour change: fixes the whole-object bucket being keyed as a field named after the reconfigured key.
  - Tests: live `test_products_api.py::test_create_item_via_serializer_object_validate_honours_a_reconfigured_non_field_key`
    over `ItemSerializer.validate()`, once under the default key and once under `override_settings`.

- [x] 11. (FLT-2) The FilterSet M2M sweep uses `isinstance(ManyToManyField)` over `get_fields()`
  - Our code: `filters/sets.py::FilterSet.get_fields #"m2m_names = {"` now reads `model._meta.many_to_many`.
  - Upstream: `django_filters/utils.py::get_all_model_fields` sweeps `opts.fields + opts.many_to_many`, and
    `Options.add_field` files every `many_to_many=True` field there.
  - Status: CONFIRMED. The new row failed on the old code: the third-party M2M field survived the removal and
    `get_fields` raised.
  - Behaviour change: fixes `Meta.fields = "__all__"` on a model with a third-party M2M field that does not subclass
    `ManyToManyField` (taggit's `TaggableManager` shape).
  - Tests: `tests/filters/test_sets.py::test_filterset_get_fields_excludes_an_m2m_field_outside_many_to_many_field`,
    over a taggit-shaped `ForeignObject` with `many_to_many=True`. No query reaches a FilterSet that fails to build.

- [ ] 34. (found landing item 1) The connection resolver serves a prefetched window without checking its bounds
  against its own arguments
  - Our code: the resolver's window probe (`connection.py::_resolve_from_window` and its prefetch read). Before item 1
    it consumed a window planned from different arguments and served wrong rows.
  - Upstream: none. This is package behaviour; the root cause (the planner reading wire names) is fixed by item 1.
  - Lines: small (a bounds-equality guard that falls back per parent on mismatch).
  - Status: CONFIRMED on the pre-item-1 code; no current input reaches it.
  - Reason to keep as is: none if the guard is cheap. Any future planner/resolver drift would serve wrong pages
    silently again.
  - Behaviour change: a drifted window falls back per parent (strictness-visible) instead of serving wrong rows.
  - Risk / blockers: robustness row, not a release blocker (GOAL.md trust boundary). It needs a way to make the
    planner drift in a test.

- [ ] 35. (found landing item 2) Strawberry decides whether to resolve a root `ListConnection`'s edges by wire name
  - Our code: `connection.py::DjangoConnection` calls `super().resolve_connection`, which reaches the upstream check.
  - Upstream: `strawberry/relay/utils.py::should_resolve_list_connection_edges` hardcodes `{"edges", "pageInfo"}` as
    wire names.
  - Lines: small (override or wrap the check with the Python-name read item 2 added).
  - Status: CONFIRMED by item 2's agent. A converter that renames both `edges` and `pageInfo` gets empty edges at the
    root. So does `auto_camel_case=False` with only `page_info { has_next_page }` selected: `hasNextPage` reads false.
  - Reason to keep as is: none. This is an upstream defect; report it upstream as well.
  - Behaviour change: fixes empty root edges and a wrong `hasNextPage` under those converters.
  - Risk / blockers: overriding upstream behaviour; it needs an origin comment if adapted. The item 2 vocabulary test
    keeps `pageInfo` unrenamed until this lands.

## Plain replacements (no behaviour change, no reason to keep)

- [x] 12. (NET-1) `_root_type` re-derives `GraphQLSchema.get_root_type`
  - Our code: `_root_type` was removed. `extensions/resource_policy.py::_DocumentWalk.operation` calls
    `graphql_schema.get_root_type(operation.operation)`.
  - Upstream: `graphql/type/schema.py::GraphQLSchema.get_root_type(operation)`. Public; the body
    `getattr(self, f"{operation.value}_type")` is the same at 3.2.0, 3.2.13 and 3.3.0a12.
  - Status: CONFIRMED (3 operation types on 6 schemas, 0 diffs; an absent root is `None` on both).
  - Behaviour change: none.
  - Tests: existing pins, `tests/test_resource_policy.py::test_an_operation_kind_the_schema_does_not_define_is_skipped`,
    `::test_the_streaming_path_carries_the_same_admission_verdict` and the mutation rows of
    `test_resource_policy_api.py`.

- [x] 13. (OPT-3, the plans.py half of O2) `_resolve_order_path_field` hand-walks order paths
  - Our code: `optimizer/plans.py::_resolve_order_path_field` now resolves the path through
    `utils/querysets.py::resolve_order_name`, the package's existing wrapper of `Query.names_to_path`, and refuses a
    leftover lookup or any hop that is many-to-many, reverse or nullable (`PathInfo.m2m`, `.direct`,
    `.join_field.null`). The terminal concrete non-relation check stays.
  - Upstream: `django/db/models/sql/query.py::Query.names_to_path`. Private, already pinned by `resolve_order_name`;
    the body is the same at 5.2.16, 6.0.9 and 6.1.2. No new private import.
  - Status: CONFIRMED (978 published OrderSet paths and 63,126 model-universe paths to depth 3, by identity of the
    returned field, 0 diffs; MTI parent-link, reverse O2O, M2M, GenericRelation and GenericForeignKey hops included).
  - Behaviour change: none.
  - Tests: existing pins, `tests/test_keyset_connection.py::test_resolve_order_path_field_arms`,
    `::test_resolve_order_path_field_accepts_mti_parent_link`, the `keyset_order_state` rows and the related-path rows
    of `test_keyset_api.py`.
  - Kept: `plans.py::_select_path_missing_connectors`. `PathInfo`s do not map one to one onto path segments (an MTI
    field adds a parent hop, an M2M segment is two), and its result names segments.

- [x] 14. (FLT-3) `_get_concrete_field_names_for_order` re-derives `Options.fields` and `Field.concrete`
  - Our code: `orders/inputs.py::_get_concrete_field_names_for_order` walks `_meta.fields` and keeps `Field.concrete`;
    the carrier-backed `ForeignObject` clause stays. The `column` / `many_to_many` predicate over `get_fields()` and
    its Django 5.2 M2M `column` paragraph are gone, since `Options.fields` holds no many-to-many field.
  - Upstream: `django/db/models/options.py::Options.fields` (documented private, like the `concrete_fields` the package
    already reads at about ten sites) and `Field.concrete` (public). Bare `concrete_fields` drops the carrier-backed
    link (6 diffs), so it is not the swap.
  - Status: CONFIRMED (287 models, fakeshop plus every module-level test model, content and order, 0 diffs at 5.2.16
    and 6.1.2).
  - Behaviour change: none. The non-model `ConfigurationError` names `'_meta.fields'`.
  - Tests: existing pins, `tests/orders/test_inputs.py::test_get_concrete_field_names_for_order_*`,
    `tests/orders/test_sets.py::test_orderset_all_excludes_virtual_generic_fields` and the live
    `test_library_inheritance_api.py::test_shelf_label_order_input_publishes_the_foreign_object_beside_its_carriers`.
  - Not in this change: `mutations/resolvers.py::_column_field_names` (the same seam changes the `exclude` it passes,
    46 of 287 models differ) and `forms/inputs.py::require_readable_choice_keys` (`dry-0_0_15_3.md` item 74).

- [x] 15. (WRT-3, the reducible part of F2) `_expression_references` hand-models `Model._get_expr_references`
  - Our code: `mutations/resolvers.py::_expression_references` takes the declarer model and reads the first segment
    of each path Django's walk yields; the hand-written `Q` / `F` / source-expression walk is gone.
  - Upstream: `django/db/models/base.py::Model._get_expr_references`, a private classmethod, byte-identical in
    5.2.16, 6.0.9 and 6.1.2; Django's constraint checks, `_get_field_expression_map` and the autodetector call it.
    Called through `utils/_narrowing.py::call_method`, so no suppression.
  - Status: CONFIRMED (46 expressions, 28 real across 155 models plus 18 synthetic trees, 0 multiset diffs;
    `_constraint_groups` for every model, 0 diffs).
  - Behaviour change: none.
  - Tests: existing pins, the `tests/mutations/test_resolvers.py` `unprovided_exclude_keeps_every_member`,
    check-constraint and unique-check rows. No fakeshop mutation reaches an expression or conditional constraint.

- [x] 16. (TYP-4) Choice-group flattening re-walks `Field.flatchoices`: kept, nothing to replace
  - Our code: the `flatten_groups` branch of `types/converters.py::_normalize_choice_pairs` is four lines inside the
    validating walk; `::choice_column_pairs` is a wrapper over it.
  - Upstream: `django/utils/choices.py::flatten_choices` (public; the same body at 5.2.16 and 6.1.2). It flattens one
    level and yields each inner entry raw, unvalidated.
  - Why it stays: our validation must unpack every top-level entry before Django's unpack runs (Django raises a raw
    `ValueError`/`TypeError` on a malformed entry and reads a two-character string as a pair), and every inner entry
    after it (Django yields `"bad"` or a nested group as is). Calling `flatten_choices` between the two passes saves
    about two lines, unpacks every flat entry twice, and trades the real-class group test for `isinstance`, which
    flattens a lazy-proxied list label.
  - Status: probed (7 fakeshop columns and 23 synthetic shapes, strict and blank). The only behaviour diff is the
    lazy-proxied list label.

- [x] 17. (TYP-8) The mutation-marker lookup indexes `parent_type.fields` by hand
  - Our code: `schema.py::DjangoMutationExecutionContext._marked_mutation_class` reads the root field through
    `get_field_def(self.schema, parent_type, field_nodes[0])`; the name guards and the `fields` dict read are gone.
  - Upstream: `graphql/utilities/type_info.py::get_field_def`, public at 3.2.x, the import
    `extensions/resource_policy.py` already uses. `docs/graphql-core-3_3-upgrade.md` names both sites for the 3.3
    swap to `GraphQLSchema.get_field`.
  - Status: CONFIRMED (135 fakeshop mutation fields plus `__typename`, `__schema`, `__type` and a missing name,
    plain and aliased, 0 diffs in the marker).
  - Behaviour change: none for any document. Root `__typename` now reads the meta-field, which has no backref, so it
    stays unmarked.
  - Tests: `tests/test_schema.py::test_marked_mutation_class_is_none_off_a_marked_root_mutation_field` (the rows for
    a nameless node, a `None` node list and a non-dict `fields`, inputs graphql-core never passes, are gone with their
    three suppressions); live `test_mutation_atomicity.py::test_mutation_root_typename_meta_field_resolves`.

- [ ] 18. (TYP-10) `unwrap_non_null` / `unwrap_graphql_type` re-derive graphql-core's peels
  - Our code: `utils/typing.py::unwrap_non_null` and `::unwrap_graphql_type` (~40 lines).
  - Upstream: `graphql/type/definition.py::get_nullable_type` and `::get_named_type`. Public, 3.2.0.
  - Lines: ~35.
  - Status: CONFIRMED (10,312 fakeshop field and argument types, 0 diffs).
  - Reason to keep ours: the bounded loop guards against cyclic chains. `GraphQLNonNull` refuses NonNull-of-NonNull at
    construction, so a real schema cannot produce one.
  - Behaviour change: none.
  - Risk / blockers: `unwrap_graphql_type` also peels Strawberry `of_type`, and no caller uses that.

- [ ] 19. (OPT-6) The GFK content-type carrier column is spelled as a string
  - Our code: `optimizer/plans.py::_prefetch_carrier_attnames #"f\"{ct_field}_id\""` (1 line).
  - Upstream: the same read `GenericForeignKeyDescriptor.get_prefetch_querysets` makes,
    `model._meta.get_field(ct_field).attname`.
  - Lines: 0.
  - Status: SUSPECTED.
  - Reason to keep ours: none (contenttypes.E004 forces a FK, so the attname is always `<name>_id` today).
  - Behaviour change: none.
  - Risk / blockers: none.

- [ ] 20. (WRT-5) The default write permission spells Django's codename grammar by hand
  - Our code: `mutations/permissions.py::DjangoModelPermission.has_permission #"codename = f"` (1 line).
  - Upstream: `django/contrib/auth/__init__.py::get_permission_codename` (public; admin uses it).
  - Lines: 0.
  - Status: CONFIRMED (0 diffs).
  - Reason to keep ours: none. It is low value: DRF's `DjangoModelPermissions.perms_map` spells the same grammar by
    hand.
  - Behaviour change: none.
  - Risk / blockers: none.

- [ ] 21. (ORM-2) `m2m_through_link_fields` re-reads through-FKs that `path_infos` already carries
  - Our code: `utils/relations.py::m2m_through_link_fields` (~25 lines).
  - Upstream: `ManyToManyField.path_infos` / `ManyToManyRel.path_infos`:
    - `[0].join_field`, or `.field` when the hop is not `direct`;
    - `[-1].join_field`.

    Public and cached.
  - Lines: ~15.
  - Status: CONFIRMED (36 M2M hops in both directions, 0 diffs).
  - Reason to keep ours: weak. It already composes Django's `m2m_field_name` / `m2m_reverse_field_name`. Optional.
  - Behaviour change: none.
  - Risk / blockers: none.

## Attribution (required either way; removes nothing)

- [ ] 22. (FLT-4, NET-4, TYP-11) Adapted upstream blocks lack origin comments, and no third-party license text ships
  - Our code. The release ships only `LICENSE` (`pyproject.toml` `license-files = ["LICENSE"]`; `git ls-files`
    tracks nothing else).
    - Blocks with no origin comment:
      - `filters/base.py::validate_range`: message and code verbatim from graphene-django.
      - `filters/base.py::_EmptyListAwareFilterMethod.__call__` and `_install_empty_list_aware_method`: graphene's
        `ListFilterMethod` / `ArrayFilterMethod` and the `.method` setters.
      - `templates/django_strawberry_framework/debug_toolbar.html`: a hardened rewrite of strawberry-django's
        template.
      - `management/commands/export_schema.py::Command`: strawberry-django's command.
    - Blocks named only in the module docstring: `filters/base.py::RangeField`, `RangeFilter` and
      `GlobalIDMultipleChoiceFilter`.
    - Blocks that name their origin but have no license file shipped:
      - `_django_patches.py::_patched_remove_databases_failures` (Django);
      - `_strawberry_patches.py::_patched_parse_query_params` (Strawberry);
      - `middleware/debug_toolbar.py` (strawberry-django, "upstream verbatim");
      - `extensions/debug.py` (graphene row shapes);
      - the `types/relay.py` ports (strawberry-django);
      - the `filters/sets.py` `_*_extra` builders (django-filter);
      - the attributed `TypedFilter` / `ArrayFilter` / `ListFilter` / `GlobalIDFilter` (graphene-django).
  - Upstream licenses owed:
    - Django: BSD;
    - django-filter: BSD;
    - Strawberry: MIT;
    - strawberry-graphql-django: MIT;
    - graphene-django: MIT.

    django-graphene-filters is the maintainer's own project and is excluded.
  - Lines: 0.
  - Status: CONFIRMED (both sides read).
  - Reason to keep ours: n/a.
  - Behaviour change: none.
  - Risk / blockers: none. AGENTS.md line 6 says the license text ships "added with its first adapted block", so this
    is overdue.

## Maintainer decisions (a reason to keep exists)

- [ ] 23. (OPT-4 = O5, with ORM-1) The lateral builder and relation-order expansion are a second compiler
  - Our code:
    - `optimizer/lateral_fetch.py::_select_columns` (~30 lines), `::_order_columns` (~40) and the raw SQL in
      `::build_lateral_sql` (~200).
    - The order expansion it reads: `utils/querysets.py::expand_relation_order`, `::_expanded_order_term`,
      `::_expanded_order_name`, `::resolve_order_name`, `::ResolvedOrderName`, `::take_order_expansion_step` and
      `::_UnexpandableOrderError` (~230).
  - Upstream:
    - `Query.get_select_mask()` with `get_default_columns(select_mask)`;
    - `SQLCompiler.get_order_by()` / `find_ordering_name`;
    - compile the child queryset via `qs.query.get_compiler(using).as_sql()`, and hand-write only the
      LATERAL/VALUES shell.
  - Lines: ~60–120 lateral, plus ~150 expansion.
  - Status:
    - Expansion: CONFIRMED faithful. 2,540 order terms, 0 diffs; the window OVER/JOIN was identical on 67/67 relations
      whose target has `Meta.ordering`.
    - Lateral: SUSPECTED.
  - Reason to keep ours:
    - The shell (the unnest/VALUES parent relation, in-branch `LIMIT`, the row-number range) has no Django
      equivalent.
    - The lateral column map, the random-order arm, the scalar-only projection, the index advisory and the keyset
      vocabulary read the expanded terms as names or `F`, and compiled `Col`s change that input.
    - `get_order_by()` adds joins to the query it compiles, so it must run on the executing queryset.
  - Behaviour change: none intended. It would accept the `defer()` shapes and relation-name orders that downgrade
    today.
  - Risk / blockers: an EXPLAIN re-check on the Postgres tier; private compiler APIs. The two halves are entangled and
    land together or not at all.

- [ ] 24. (OPT-5) `_correlation_steps` hand-builds the GenericRelation content-type restriction
  - Our code: the `kind == "generic"` arm of `optimizer/predicates.py::_correlation_steps` (~10 lines). It filters
    `content_type__app_label` / `content_type__model`, which joins `django_content_type`.
  - Upstream: `django/contrib/contenttypes/fields.py::GenericRelation.get_extra_restriction` /
    `::get_content_type`, which restrict on `content_type_id = <pk>` and honour `for_concrete_model`.
  - Lines: ~6.
  - Status: SUSPECTED.
  - Reason to keep ours: it avoids a `ContentType` lookup at predicate build and is multi-db neutral. That is arguably
    deliberate, but undocumented.
  - Behaviour change: none on rows; one join fewer per EXISTS.
  - Risk / blockers: the ContentType cache is per `using`. Either swap, or document the reason at the site.

- [ ] 25. (NET-2) The WebSocket Host projection re-derives `ASGIRequest.__init__`'s header-to-META mapping
  - Our code: `consumers.py::_host_validation_request` and `consumers.py #"_HOST_META_KEYS_BY_HEADER = "` (~16
    lines of code plus ~45 lines of justifying docstring).
  - Upstream: `django/core/handlers/asgi.py::ASGIRequest(scope, body_file)`, then `.get_host()`. Its host code is
    identical in 5.2.16 and 6.1.2.
  - Lines: ~50.
  - Status: CONFIRMED. 864 cases, 0 diffs, covering:
    - `ALLOWED_HOSTS` sets;
    - `USE_X_FORWARDED_HOST`;
    - duplicate, IPv6 and invalid hosts;
    - the underscore spoof header;
    - 3 server shapes.
  - Reason to keep ours: spec-046 Decision 19 rejected this on purpose.
    - `ASGIRequest` wants an HTTP scope, so `method` would be synthesized.
    - It parses cookies and content type for nothing.
    - A WebSocket scope with no `path` raises `KeyError`.
  - Behaviour change: none.
  - Risk / blockers: it feeds a synthesized HTTP-only key into a Django constructor. Revisit Decision 19, or close
    this as kept.

- [ ] 26. (NET-3) The Strawberry patch shields `parse_query_params` with a pinned copy of upstream's body
  - Our code: `_strawberry_patches.py::_patched_parse_query_params` (~17 lines), `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE`
    (~20) and the body-source pin in `_validate_upstream_shape` (~12).
  - Upstream: `strawberry/http/base.py::BaseView.parse_query_params`, unchanged from 0.322.2 to 0.327.7.
  - Lines: ~40.
  - Status: SUSPECTED.
  - Two ways to drop the copy:
    - a delegating wrapper that sets a ContextVar `_patched_parse_json` reads;
    - moving the gap-2 envelope guard off `parse_json` to a provenance-scoped translation around
      `parse_http_body`.
  - Reason to keep ours:
    - The origin is named, and the source pin already fails loud on drift.
    - The ContextVar adds hidden state.
    - The provenance option would turn a server-side `AttributeError` inside `parse_http_body` into a 400.
  - Behaviour change: none intended.
  - Risk / blockers: as above.

- [ ] 27. (TYP-3) Enum values `True` / `False` / `NULL` get a `MEMBER_` prefix that GraphQL does not require
  - Our code: `types/converters.py::_GRAPHQL_RESERVED_ENUM_VALUES` and the reserved arm of `::_sanitize_member_name`
    (~6 lines). The check casefolds.
  - Upstream: `graphql/type/assert_name.py::assert_enum_value_name` (public, 3.2.0+). It also covers the Name grammar
    that `_NON_IDENT` and the digit-prefix rule enforce.
  - Lines: ~4.
  - Status: CONFIRMED (11 names, 5 diffs). `True`, `False` and `NULL` are the real divergence. `__x` and `mro` belong
    to rules graphql-core has no callable for, and ours keeps them correctly.
  - Reason to keep ours: swapping changes the wire.
  - Behaviour change: changes the wire. Choice values `True`, `False` and `NULL` would publish without the prefix.
  - Risk / blockers: a schema break for any consumer with such a choice value.

- [ ] 28. (S12) `graphql_camel_name` pins input names instead of letting the `NameConverter` decide
  - Our code:
    - `utils/inputs.py::build_strawberry_input_class`;
    - `forms/inputs.py::_simple_triple` and `::_field_triple_and_spec`;
    - `rest_framework/serializer_converter.py::serializer_field_graphql_name` and `::resolve_serializer_field`;
    - `rest_framework/inputs.py::_resolve_nested_field`;
    - `mutations/inputs.py::relation_input_annotation` and `::model_column_input_annotation`.
    - About 40 lines.
  - Upstream: the schema's `NameConverter.from_field`.
  - Lines: ~40.
  - Status: still accurate (re-verified).
  - Reason to keep ours: swapping changes the wire.
  - Behaviour change: changes the wire. Input names would follow `auto_camel_case=False` and custom converters.
  - Risk / blockers: a schema break for consumers on a non-default converter.

- [ ] 29. (S6) Consumer per-frame masking → `SchemaExtension.on_stream_result`
  - Our code: `consumers.py::_stop_aware_results #"mask_execution_result(result, policy)"` (~3 lines plus the local
    import and docstring).
  - Upstream: `SchemaExtension.on_stream_result`. It is absent at 0.322.2 and present at 0.327.7; the exact release
    was not pinned.
  - Lines: ~5.
  - Status: re-verified.
  - Reason to keep ours:
    - It needs a floor raise.
    - The hook allows only in-place mutation of the yielded result. Ours returns a masked copy so `original_error`
      survives for `DjangoDebugExtension`, which moving would give up (or it would need in-place masking).
  - Behaviour change: none intended.
  - Risk / blockers: a floor raise, and losing the LIFO `original_error` contract.

- [ ] 30. (F5) The package `RangeField` / `_RangeWidget` / `validate_range` → django-filter's `RangeFilter` /
  `RangeField`
  - Our code: `filters/base.py::RangeField`, `_RangeWidget` and `validate_range` (~70 lines).
  - Upstream: `django_filters/fields.py::RangeField` (a `MultiValueField`, `_min`/`_max`, a `slice` value, Decimal
    sub-fields).
  - Lines: ~70.
  - Status: re-verified, still accurate.
  - Reason to keep ours:
    - The swap changes the wire keys and the value shape.
    - It loses per-column bound cleaning and the integer gte+lte split.
  - Behaviour change: changes the wire.
  - Risk / blockers: the attribution half is item 22.

- [ ] 31. (F8) `_PUBLIC_PACKAGE_FILTER_DEFAULTS` is a verbatim copy of `FILTER_FOR_DBFIELD_DEFAULTS`
  - Our code: `filters/sets.py::_PUBLIC_PACKAGE_FILTER_DEFAULTS` (~60 lines).
  - Upstream: `django_filters/filterset.py::FILTER_FOR_DBFIELD_DEFAULTS`.
  - Lines: ~60.
  - Status: CONFIRMED identical on django-filter 26.1: 0 key, class or extra diffs, and 286 extra-provider outputs with
    0 diffs.
  - Reason to keep ours: it anchors optimizer-eligibility ownership against a consumer mutating django-filter's
    global before import. That is a policy choice, not a missing seam.
  - Behaviour change: none.
  - Risk / blockers: keep and add a provenance check that the copy still matches upstream, or drop the anchor.

- [ ] 32. (O6) Seal-family spoof resistance → `qs.query`, `base_table`, `all()`/`_chain()`
  - Our code: `utils/querysets.py::_seal_or_defect`, `_base_table_defect`, `_query_genuineness_defect`,
    `_rebuild_query_payloads`, `_reconstructed_value` and the `_normalized_*` family (~2,000 lines).
  - Upstream: the plain queryset attributes.
  - Lines: ~2,000.
  - Status: re-verified; symbols unchanged.
  - Reason to keep ours: spec-045 trust boundary (a sealed-execution queryset). This is a policy question, not a seam.
  - Behaviour change: it would drop spoof resistance.
  - Risk / blockers: GOAL.md "Trust boundary"; a decision for spec-045, not a refactor.

- [ ] 33. (TYP-12) GIS/GEOS fields are unsupported; strawberry-django has a scalar block to adapt
  - Our code: `types/converters.py::SCALAR_MAP` / `FIELD_OUTPUT_TYPE_MAP` have no GEOS arm.
  - Upstream: the GEOS scalars and the `field_type_map.update` block in `strawberry_django/fields/types.py`. MIT,
    crib only: adapt with attribution.
  - Lines: adds code.
  - Status: SUSPECTED.
  - Reason to keep ours: n/a. This is a feature gap, not a copy.
  - Behaviour change: adds new scalars.
  - Risk / blockers: needs GDAL; it is a new KANBAN card, not a refactor. Item 22 covers the license.

## Closed by this sweep (kept, with the reason)

- [x] O2 walkers other than item 13 stay.
  - `utils/relations.py::classify_path`, `path_traverses_to_many` and `_lenient_traverses_to_many` stay. Over 4,171
    paths, the probe found 0 diffs in resolve-or-raise and cardinality.
  - The earlier 9 `GenericRelation__content_object` diffs are gone; both sides now raise.
  - The remaining 284 terminal diffs are by contract. Django returns the join field and flattens MTI hops, while we
    need the declared field and one hop per segment.
  - `utils/querysets.py::_prefetch_relation_target_or_none` stays: `get_prefetcher` needs a saved instance.
- [x] F1, filter side: what remains stays.
  - `binds_integer` stays: Django's `IntegerFieldOverflow` misses `in`, `range`, `RelatedExact` and duration
    microseconds.
  - `refuses_utc_offset` stays: PostgreSQL refuses on the server.
  - `psycopg_refuses_list_parameter` stays: it asks the driver.
  - The hand-walked gate is item 3.
- [x] F2, `_constraint_groups`, cannot be replaced.
  - `_get_unique_checks(include_meta_constraints=True)` adds a pk group on every model.
  - It misses the check, conditional and expression groups on 7 models.
  - `_expression_refs_exclude` changed between 5.2.16 and 6.1.
  - Only the walk (item 15) is reducible.
- [x] F3, `utils/widgets.py::multi_widget_keys` / `widget_keys` / `widget_entries`, stays.
  - Filter widgets: 0 diffs over 6,874.
  - A key recorder cannot pair keys with sub-widgets, misses `QueryArrayWidget`'s iteration reads, and adds harmless
    `x-clear` / `SelectDateWidget` part keys.
- [x] S2, `prime_selected_fields` → `convert_selections`, stays. Strawberry still dereferences
  `node.type_condition.name.value` in `InlineFragment.from_node` from 0.322.2 to 0.327.7, so no floor raise helps.
- [x] The four patch modules are all live at the ceiling.
  - Strawberry `parse_json` / `parse_http_body` / `replace_placeholders_with_files`;
  - cross_web `.body` decode;
  - graphql-core `complete_list_value`;
  - Django `_remove_databases_failures` (Trac #37064 wontfix).
- [x] The first sweep's keeps:
  - O4: the window row number on each row.
  - F11: one cleaned element's type.
  - S10: checks before names resolve.
  - S11: `execute_wrapper` misses COMMIT.
- [x] Docs drift, outside this list's scope. `docs/README.md` (the Relay `Meta.interfaces` paragraph) and specs
  001/015/019/029–032/036/048 say `id: GlobalID!`. The live fakeshop SDL publishes `id: ID!` 70 times and `GlobalID!`
  0 times. This is a spec-sweep item, not a seam.

## Dropped by the sweep

The candidates below were checked and thrown out, so the next sweep can skip them:
- **The filter side:** `filters/base.py::_filterset_resolved_field`, `_resolve_globalid_target`;
  `filters/sets.py::_TEXT_PATTERN_LOOKUPS` / `_lookups_for_field`, `_without_foreign_postgres_lookups`,
  `_MODEL_CHOICE_ONLY_EXTRAS`, `_runs_shipped_filter`.
- **Ordering:** the `orders/` `.asc()`/`.desc()` wrapper; `plans.py::_draws_at_random` (the Django `flatten` it would
  use skips `WhereNode`), `runtime_path_from_path`, `order_entry_name_and_direction` / `keyset.py::split_order_ref`,
  `_reverse_order_by`, `_diff_prefetch_related`, `_flatten_select_related`; `utils/querysets.py::default_order` /
  `selected_order`; `list_field.py`'s determinism classifiers and `_is_model_default_ordering_active`.
- **The optimizer extension:** `extension.py::_collect_reachable_fragment_definitions`, `_walk_cache_relevant_vars`,
  `_collect_schema_reachable_types`; `join_taxonomy.py::_partition_expr`.
- **Connections and pagination:** `connection.py::_resolve_from_window`, `_resolve_keyset_connection`,
  `_window_edge_class`; `utils/connections.py::page_arguments` and its neighbours.
- **Values and SQL:** `utils/querysets.py::binds_integer`, `_stored_decimal_or_none`;
  `relations.py::stored_value_column` (it matches `get_col` but returns more), `validate_lookup_expr`;
  `write_transaction.py::_sql_statement_token` (`sqlparse` fails open on a writable CTE).
- **Mutations, forms and DRF:** DRF field mapping (never re-derived); `serializer_errors_to_field_errors` (iterative
  on purpose); `writable_serializer_fields`; `input_field_required`; `adds_by_update_first`;
  `_reconstruct_partial_data`; `_coerced_null_fields`; `form_field_kind`.
- **Types and Relay:** `types/converters.py::_is_enum_reserved_member`, `_column_admits_empty_string`; `scalars.py`
  BigInt; `utils/strings.py::pascal_case`; `utils/lazy.py::unwrap_lazy_object`; `types/base.py::_NODEID_STRING_RE`;
  `relay.py::DjangoNodeField` / `_interleave`; `types/relay.py::node_definition_for_published_name`.
- **Schema execution:** `schema.py::_close_thread_connections`, `_execution_errors`, `_refuse_operation_document`.
- **Transport:** `routers.py`; `_request_body.py::body_exceeds_limit`; `views.py::_form_encoding_is_utf8` /
  `_declared_content_length` / `_evaluate_request_user` / `_RawBodyRequestAdapter`.
- **Resource policy and extensions:** `extensions/resource_policy.py::scan_document_text` (`max_tokens` is absent at
  3.2.0), `_variable_names`; the Strawberry depth and alias limiters; `MaskErrors`.
- **Auth and test tooling:** `auth/` (it already calls `authenticate`, `login`, `validate_password` and the channels
  helpers); `testing/client.py::_build_body`.
- **Context and execution utils:** `utils/context.py`, `directives.py`, `execution_mode.py`, `operation_lease.py`.
- **Thin wrappers and trust boundary:** the `_multipart.py` constants; `utils/permissions.py::resolve_auth_aliases`;
  the trust-boundary write code (`_merged_serializer_kwargs`, `_frozen_hook_view`, `_pin_validator_querysets`,
  `permissions.py::_validated_target_subquery`).

Adjacent, to look at next time: `filters/sets.py` hand-builds `{"message", "code"}` dicts where
`ErrorList.get_json_data` exists.

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
