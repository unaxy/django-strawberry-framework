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
it lands with its tick. An unticked item whose research note says "yours" waits on a maintainer decision.

Progress: 33 of 39 landed; 6 yours (25, 28, 29, 30, 32, 33).

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
    - Live: `examples/fakeshop/test_query/test_scalar_predicate_binding_api.py::test_a_temporal_primary_key_is_checked_through_its_pk_date_transform`,
      over a real test-local temporal-key table and native public type mounted on the HTTP holder.

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

- [x] 5. (TYP-2) A `GeneratedField` column has no conversion
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
  - Owner: spec-051 Slice 2. The maintainer left the conversion to the builder flow; it landed here as that slice
    (spec-051's Status line records it).
  - Landed: one computed column per `GeneratedField`, `utils/relations.py::generated_column`: a clone of
    `output_field` bound to the outer name, model and `db_column`, carrying the outer `choices`, `blank` and
    `help_text`, with `null = field.null or output_field.null` (the clone Django's own `GeneratedField.check`
    builds). It feeds classification and value coding only, never a query.
    - `types/converters.py::generated_output_field` wraps it with the three refusals (file / image output, an output
      no conversion publishes, an array output whose `base_field` declares choices), each naming the outer field.
      `scalar_route`, `convert_scalar`, `_scalar_map_entry` and `_column_admits_empty_string` read it.
    - Filters: `FilterSet._selected_column` keeps the `GeneratedField` when the merged `FILTER_DEFAULTS` +
      `Meta.filter_overrides` map has an entry for it (an override stays honoured) and selects the column otherwise;
      `_upstream_filter_for_lookup`, the origin oracle and `_lookups_for_field` read it, and
      `filters/base.py::_model_resolved_field` hands it to the request-time guards. Every lookup is read off the one
      registry Django's query resolves a generated column's lookups on, its `output_field` instance
      (`utils/relations.py::lookup_registry`), never the copy of the output class's lookups the generated field files
      on itself, and every walk starts from the generated field's own column (`utils/relations.py::lookup_operand`):
      the generated leaf's filter selection (`filters/sets.py::_generated_filter_field`, adapted into
      `FilterSet._upstream_filter_for_field`), the operand walk, the text-pattern test and the target-less GlobalID
      lookup test.
    - The identity codec (`utils/querysets.py::coerce_field_value_or_none` / `::column_python_value`) keeps the
      declared field's own `to_python` / `get_db_prep_value` (a consumer key subclass's hold) and codes a value stored
      in a generated column through its computed column after them (`::_value_codecs`; a lookup on that column is
      read off `utils/relations.py::lookup_registry`, never off the clone); `stored_value_column`, which now answers
      a generated column, feeds the storage-domain checks: a `relay.NodeID` over one refetched `null` for an
      existing row before. Keyset cursors, `orderBy:` cursor state, the array helpers and `inspect_django_type` read
      it too.
    - The research corrected two claims above: about 25 package lines, not 4, and nullability is the either-flag rule
      (strawberry-django reads `output_field.null` only).
    - Fixture: library `Shelf.code_length` (BigInteger output over `code`) and `Shelf.topic_length` (nullable integer
      over `NULLIF(topic, '')`), `db_persist=True`, migration `0020`; the tracked `db.sqlite3` is not migrated.
  - Tests: live `examples/fakeshop/test_query/test_library_generated_api.py` (44 rows: read, every filter lookup,
    the past-64-bit `in` / `range` guard, a nested `RelatedFilter`, order with nulls, the form update payload, an
    `"__all__"` type, a no-field-list mutation's input, the `relay.NodeID` refetch, and lookups registered on the
    `output_field` instance: a `Chr` operand, a text pattern, a target-less `GlobalIDFilter`, and a registration that
    replaces a name the generated field's copy holds, `Exact` or an equality named `contains` and `Chr` as
    `endswith`) and `examples/fakeshop/test_query/test_node_refetch_api.py` (a key subclass to a generated integer
    column refetched by `node` / `nodes`), plus package rows in
    `tests/types/test_converters.py`, `tests/filters/test_sets.py`, `tests/test_keyset.py`,
    `tests/utils/test_querysets.py` and `tests/mutations/test_resolvers.py`. Every fix row failed on the old code;
    the live module passes at Django 5.2.16 + django-filter 25.2. Postgres is Actions only.

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

- [x] 34. (found landing item 1) The connection resolver serves a prefetched window without checking its bounds
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
  - Landed: every planned window publishes `optimizer/plans.py::PlannedWindow` (its bounds and keyset cursor state)
    under its resolver key. `connection.py::_consume_window` serves the window only when the bounds its own arguments
    derive equal the planned ones; a mismatch or an unpublished window falls back per parent, and the fallback now
    reports itself to strictness (`types/resolvers.py::_check_n1` with `force_unplanned`), which no fallback did.
  - Tests: package tier, since no wire input makes the planner and resolver disagree:
    `tests/test_relay_connection.py::test_fast_path_refuses_a_window_planned_under_other_bounds[off|raise]`, which
    failed on the old code (decoy rows served; no strictness error).

- [x] 35. (found landing item 2) Strawberry decides whether to resolve a root `ListConnection`'s edges by wire name
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
  - Landed: `optimizer/selections.py::connection_page_selected` asks the same question by Python name, read through
    `connection.py::_page_requested`.
    - The keyset page (`_resolve_keyset_connection`), which called the check itself and was wrong on both executors,
      asks `_page_requested` alone.
    - The offset page's synchronous branch (`ListConnection.resolve_connection`, root and per-parent fallback) reaches
      it through `_strawberry_patches.py::_patched_should_resolve_list_connection_edges`, a gated rebind of the
      `strawberry.relay.types` global that answers by `_page_requested` alone; upstream is not asked, since it answers
      `True` for a fragment spread named `edges` and raises `AttributeError` on an anonymous inline fragment.
      `strawberry.relay.utils` keeps its own binding. `_strawberry_patches.py::_validate_relay_upstream_shape` refuses
      a release whose `resolve_connection` stops calling the global, naming the opt-out. The body is the same from
      0.322.2 to 0.339.0.
    - Not reported upstream yet.
  - Tests: live `test_library_api.py::test_snake_case_page_info_only_page_reports_has_next_page[root-offset|root-keyset|nested-per-parent]`
    and `::test_snake_case_page_info_only_keyset_page_reports_has_next_page_async`; the vocabulary row now renames
    `pageInfo` too. All five failed on the old code. Patch-shape rows in `tests/test_strawberry_patches.py`.

- [x] 36. (found landing item 23) The single-parent projection guard is blind for a multi-table child
  - Our code: `optimizer/single_parent_fetch.py` compares `lateral_fetch.py::_select_columns` at plan and fetch time.
  - Upstream: none; package behaviour.
  - Status: CONFIRMED by item 23's implementer. `_select_columns` answers `None` for any projection that selects a
    multi-table parent column (lateral cannot join it), so a full multi-table child load fingerprints `None` at both
    ends and a projection drift between plan and fetch goes unseen.
  - Fix: a single-parent fingerprint that keeps each column's alias instead of refusing parent-table columns.
  - Behaviour change: a drifted multi-table projection falls back instead of serving the planned columns.
  - Risk / blockers: robustness row, not a release blocker (GOAL.md trust boundary).
  - Landed: `lateral_fetch.py::_select_projection` keys each selected `Col` by its join alias's table
    (`(table, attname, column)`), and `single_parent_fetch.py` compares it at plan and fetch time.
    `_select_columns` stays the lateral builder's base-table-only refusal wrapper; both read `_selected_cols`.
  - Tests: package tier, since no GraphQL input alters a queryset after planning:
    `tests/optimizer/test_single_parent_fetch.py::test_fetch_returns_none_for_projection_drift_on_a_multi_table_parent_column`
    (failed on the old guard) and `::test_fast_path_serves_an_undrifted_multi_table_child`, over
    `Venue.lendingdesk`; two `_select_projection` rows in `tests/optimizer/test_lateral_fetch.py`.

- [x] 37. (found researching item 28) Form and serializer `FieldError` keys read the bind-time name, not the published
  one
  - Our code: `forms/resolvers.py` and `rest_framework/resolvers.py` key every error through the bind-time
    `InputFieldSpec.graphql_name` (`utils/errors.py::build_error_key_map`), nested serializer specs included. Only the
    model flavor re-read the executing schema (the former `mutations/resolvers.py` `_published_input_specs`).
  - Upstream: `strawberry/schema/name_converter.py::NameConverter.get_graphql_name` / `from_field`. A consumer
    converter overriding either respells even a pinned `name=`.
  - Status: SUSPECTED. Spec-versus-published comparison over fakeshop's 133 mutation classes: 0 mismatches by
    default; under a converter lower-casing every field, 224, of which the 54 model-flavor ones are repaired per
    request and 170 (102 form, 68 serializer) are not, so an error would be keyed `branchId` where the client sent
    `branchid`.
  - Behaviour change: fixes form and serializer errors keyed to a name the client never sent, under a custom
    `NameConverter`.
  - Landed: CONFIRMED live (all 6 cases of the new library row failed on the old code under an upper-casing
    converter). The model flavor's read-back moved into the shared `utils/inputs.py::published_input_specs`, which
    reads the executing schema's published `data` argument and recurses into `nested_specs` through `get_named_type`;
    the form (`forms/resolvers.py::_run_form_pipeline_sync`), serializer
    (`rest_framework/resolvers.py::_run_serializer_pipeline_sync`) and register (`auth/mutations.py`, through
    `_password_input_name`) pipelines read it once per request and pass `specs=` to their decode, error and write
    steps; a direct call with no executable schema keeps the bind specs. A second defect: DRF 3.18's
    `ListSerializer.to_internal_value` keys failing items by index (3.17 returns a list), so
    `rest_framework/resolvers.py::_error_node_children` dropped the child key map and a nested camelCase error was
    mis-keyed even under the default converter; an int key now keeps the level's map. Specs 036, 038, 039 and 040 are
    restated. Tests: live `test_library_api.py::test_form_and_serializer_errors_key_to_the_names_a_custom_converter_published`
    (model form, plain form, serializer, nested serializer) and
    `test_auth_api.py::test_register_errors_key_to_the_names_a_custom_converter_published`; package
    `tests/rest_framework/test_resolvers.py::test_flattener_rekeys_children_under_an_index_keyed_list_serializer_error`
    and `tests/auth/test_mutations.py::test_register_write_step_refuses_specs_without_a_password_field`. Verified
    (opus-high, two rounds) with eight failability mutations and the DRF 3.17.0, Django 5.2.16 and Strawberry 0.322.2
    floors.

- [x] 38. (found verifying item 37) The update / delete `id` argument's `FieldError` key is a literal, not the
  published argument name
  - Our code: `mutations/resolvers.py::not_found_error`, `::_invalid_lookup_id_error`, the
    `unstorable_text_error("id", pk)` call in `::coerce_lookup_id`, and `utils/write_transaction.py::conflict_error`
    key to the literal `"id"`. Model, form and serializer update / delete all reach them through the shared skeleton.
  - Upstream: `strawberry/schema/name_converter.py::NameConverter.from_argument` (calls `get_graphql_name`; the module
    is byte-identical at 0.322.2 and 0.327.7). The executing schema's published argument is the seam:
    `utils/typing.py::published_argument`.
  - Status: CONFIRMED live over fakeshop for eight cases (model update not-found, Relay invalid id, surrogate text id,
    delete not-found, form and serializer not-found, conflict): under an upper-casing converter, and under one that
    overrides `from_argument` alone, each answers `{"field": "id", "path": ["id"]}` where the client sent `ID`. Under
    the default converter the published name is `id`, so nothing changes on the wire. `login` is not affected: its
    `username` / `password` literals only feed an `is not None` test, and a failed login is always the `__all__`
    envelope.
  - Behaviour change: under a custom `NameConverter`, the `id` argument's not-found, invalid, unstorable-text and
    conflict errors key to the name the client sent.
  - Landed: `utils/typing.py::published_argument_wire_name` reads the published name (default on a direct-call stub);
    `list_field.py::_resolve_argument_wire_name` now delegates to it. The update / delete skeleton
    (`mutations/resolvers.py::run_write_pipeline_sync`) stores the `id` argument's published name on the request's
    `utils/write_transaction.py::WriteAliasContext` (`id_name`) before locating, and `not_found_error`,
    `_invalid_lookup_id_error`, `coerce_lookup_id` and `conflict_error` key through `::lookup_id_name` (`"id"`
    outside a pipeline). `docs/README.md` and the FieldError / DjangoMutation glossary bodies say so. Tests: live
    `test_library_api.py::test_lookup_id_errors_key_to_the_id_name_a_custom_converter_published` (8 rows: model,
    Relay, surrogate text, delete, form, serializer, conflict, and a `from_argument`-only converter; all failed on
    the old code); package `tests/mutations/test_write_transaction.py::test_lookup_id_name_is_the_pipelines_published_id_or_id_outside_one`.
    Verified (opus-high) with seven failability mutations, aliased and async documents, class reuse across schemas,
    and the Strawberry 0.322.2 and Django 5.2.16 floors.

- [x] 39. (found researching item 38) Relay pagination errors name `first` / `last` / `after` / `before` by literal
  - Our code: seven client-facing messages put a connection argument's Python name into the text:
    `utils/connections.py::decode_offset_cursor`, `::assert_relay_pagination_bound` (non-negative, cap),
    `keyset.py::_invalid_cursor_error`, `connection.py::_guard_first_and_last`, and the sliced-source and
    `filter:` / `orderBy:` refusals in `connection.py`. `list_field.py::_resolve_argument_wire_name` already reads
    the published name for `offset` / `limit` / `orderBy`.
  - Upstream: `strawberry/relay/utils.py::SliceMetadata.from_arguments` uses the same literals (byte-identical at
    0.322.2 and 0.327.7) but raises untyped `TypeError` / `ValueError`, and the package validates before the engine
    and runs a keyset fork the engine never sees, so the package owns the message; the name in it comes from the
    executing schema (`utils/typing.py::published_argument`). Upstream hazard:
    `strawberry/relay/fields.py::ConnectionExtension.apply` appends `before` / `after` / `first` / `last` to
    `field.arguments` on every schema build, so after a second build over the same types
    `Info.get_argument_definition` returns a stale argument and `published_argument`'s identity match raises
    `ConfigurationError` on a connection field.
  - Status: CONFIRMED live on root and nested offset and keyset connections at 0.322.2 and 0.327.7: under an
    upper-casing converter `FIRST: -1` answers "Argument 'first' must be a non-negative integer." (code
    `PAGINATION_INVALID` unchanged). Under the default converter the published names are the Python names, so the
    text does not change.
  - Behaviour change: message text only, under a custom `NameConverter`; `extensions.code` unchanged.
  - Landed: `utils/typing.py::published_argument` matches the published map by the back-referenced argument's
    Python name instead of identity, so it survives the rebuild append (items 37 and 38's readers inherit it). The
    pagination refusals read the published name through `utils/connections.py::published_page_argument_name` only
    when they reject (an accepted page does no lookup; plan-time and direct calls keep the Python name): the offset
    cursor and page-size bound (`utils/connections.py`), the keyset cursor (`keyset.py::_invalid_cursor_error`),
    `connection.py::_guard_first_and_last`, `::_guard_source_not_pre_sliced` and
    `::_guard_sidecar_input_against_non_queryset`. Specs 030, 047, 048 and 050 and the `PaginationArgumentError`
    glossary body are restated. Tests: live `test_connection_pagination_api.py::test_pagination_errors_name_the_arguments_the_schema_published`
    (48 rows: root and nested, offset and keyset, renaming and first/last-swapping converters),
    `::test_pagination_errors_follow_the_executing_schema_after_another_build` and
    `::test_resolver_contract_refusals_name_the_arguments_the_schema_published`; 43 of the 52 failed on the old code.
    Verified (opus-high) with 14 failability mutations, an optimizer-on / async / aliased probe (422 rows), and the
    Strawberry 0.322.2 and Django 5.2.16 floors; its three doc findings were applied as worded.

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

- [x] 18. (TYP-10) `unwrap_non_null` / `unwrap_graphql_type` re-derive graphql-core's peels
  - Our code: `unwrap_graphql_type` (and its `utils` re-export) was removed; `optimizer/extension.py` reads
    `get_named_type`, and its reachable-type walker takes a typed `GraphQLType`, reads `graphql_fields` on object and
    interface types and `GraphQLSchema.get_possible_types` for union members and interface implementations.
    `utils/typing.py::unwrap_non_null` stays as one `GraphQLNonNull` peel: `get_nullable_type`'s overloads reject a
    bare `GraphQLType` and its return reads partially Unknown, so calling it would grow suppressions.
  - Upstream: `graphql/type/definition.py::get_named_type` and `::get_nullable_type`, and
    `graphql/type/schema.py::GraphQLSchema.get_possible_types`. Public, the same at 3.2.0, 3.2.13 and 3.3.0a12.
  - Status: CONFIRMED (12,187 fakeshop schema values, both peels, 0 diffs; the reachable `DjangoType` set is the same
    91 types).
  - Behaviour change: none. The bounded loops and their cyclic-chain errors are gone: graphql-core refuses a
    `GraphQLNonNull` of a `GraphQLNonNull`, and a real schema holds no cyclic wrapper.
  - Tests: existing pins in `tests/optimizer/test_extension.py` (`resolve_model`, `check_schema` union and interface
    rows), `tests/utils/test_typing.py::test_unwrap_non_null_peels_only_non_null_layers` and
    `tests/test_resource_policy.py`. The rows that pinned hand-built `of_type` stacks and cyclic chains are gone.

- [x] 19. (OPT-6) The GFK content-type carrier column is spelled as a string
  - Our code: `optimizer/plans.py::_prefetch_carrier_attnames` reads the content-type key's own `attname`
    (`model._meta.get_field(ct_field)`); the object-id column stays the name `fk_field` gives.
  - Upstream: the read Django's generic prefetch makes, `GenericForeignKey.get_prefetch_queryset` on 5.2.16 and
    `GenericForeignKeyDescriptor.get_prefetch_querysets` on 6.1.2. `GenericForeignKey.ct_field_attname` is absent at
    the 5.2 floor, so it is not used.
  - Status: CONFIRMED (18 GFKs on fakeshop and module-level test models, identical attnames). contenttypes.E003/E004
    constrain the key's class and target, not its attname.
  - Behaviour change: fixes a content-type key that is a `ForeignKey` subclass overriding `get_attname`. The projection
    named `<ct_field>_id`, a column the model does not have, and the query failed when it compiled.
  - Tests: `tests/optimizer/test_plans.py::test_apply_projection_keeps_a_generic_foreign_key_carrier_by_its_key_attname`
    failed on the old code; the live
    `test_library_api.py::test_library_consumer_prefetch_keeps_its_link_columns[generic-foreign-key]` still pins the
    plain shape. Fakeshop has no renamed key, so the fix row is package-tier.

- [x] 20. (WRT-5) The default write permission spells Django's codename grammar by hand
  - Our code: `mutations/permissions.py::DjangoModelPermission.has_permission #"codename = f"` (1 line).
  - Upstream: `django/contrib/auth/__init__.py::get_permission_codename` (public; admin uses it).
  - Lines: 0.
  - Status: CONFIRMED (0 diffs).
  - Reason to keep ours: none. It is low value: DRF's `DjangoModelPermissions.perms_map` spells the same grammar by
    hand.
  - Behaviour change: none.
  - Risk / blockers: none.

- [x] 21. (ORM-2) `m2m_through_link_fields` re-reads through-FKs that `path_infos` already carries
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

## Attribution (extend upstream instead of shipping its license)

- [x] 22. (FLT-4, NET-4, TYP-11) Copied upstream blocks: extend upstream so no third-party license is owed
  - Rule. MIT and BSD attach only to copied or adapted upstream source. Importing, subclassing or calling upstream owes
    nothing, and neither does code that reproduces upstream behaviour in its own statements or shares a short
    functional string. A license file ships only for a project with at least one block still copied.
  - Audit at `339fdf91`, block against upstream source:
    - Copied:
      - Django: `_django_patches.py::_patched_remove_databases_failures` and its two pinned source strings;
      - Strawberry: `_strawberry_patches.py::_patched_parse_query_params` and its pinned source string;
      - strawberry-graphql-django: `templates/django_strawberry_framework/debug_toolbar.html`
        and `middleware/debug_toolbar.py`;
      - django-filter: `filters/sets.py::_PUBLIC_PACKAGE_FILTER_DEFAULTS`, the whole table in upstream's order.
    - Borderline: `_completion.py::_gather_with_cancel`, which has graphql-core 3.3's skeleton but the opposite
      cancel semantics, and `utils/errors.py::datetime_django_binds`, three lines of public calls.
    - Not copied (behaviour or name match only): every graphene-django "port", `extensions/debug.py`,
      `testing/client.py`, `types/relay.py::_order_nodes`, `optimizer/plans.py::apply_window_pagination`, the
      form and DRF converters, and `management/commands/export_schema.py::Command`, whose own argument handling
      shares only the `print_schema` call and Strawberry's "must be an instance of strawberry.Schema" message.
  - Extensions that keep behaviour (each lands with its own tick):
    - [x] 22a. `_django_patches.py::_patched_remove_databases_failures` re-wraps a foreign replacement in a
      `_DatabaseFailure` and then calls Django's own classmethod; both pinned Django bodies go.
    - [x] 22b. `_strawberry_patches.py::_patched_parse_query_params` delegates to upstream's own method under a
      ContextVar flag instead of a pinned copy.
    - [x] 22c. `filters/sets.py::_PUBLIC_PACKAGE_FILTER_DEFAULTS` is built from django-filter's
      `FILTER_FOR_DBFIELD_DEFAULTS` at import, with a provenance check for the baseline.
    - [x] 22d. `filters/base.py::ArrayFilter.filter` hands every value but `[]` to `Filter.filter`.
    - [x] 22e. `types/relay.py::_resolve_id_default` goes; the resolver table installs Strawberry's own `Node.resolve_id`.
    - [x] 22f. `utils/errors.py::datetime_django_binds` projects a date with `datetime.combine` and
      `timezone.make_aware`, and no longer claims to adapt Django's code.
  - After the extensions (landed): `LICENSE.django` and `LICENSE.graphql-core` are dropped, since no copied block backs
    them, and "port of" claims on blocks that copy nothing now read "same contract as".
  - Landed: the debug-toolbar pair is adapted code (65% of upstream's non-blank Python lines and 53% of its template
    lines survive verbatim), from strawberry-graphql-django 0.82.1, itself based on flavors/django-graphiql-debug-toolbar
    (MIT, not archived), so AGENTS.md line 6 decides it. `LICENSE.strawberry-django` and
    `LICENSE.django-graphiql-debug-toolbar` (byte copies) ship in the sdist and the wheel's `licenses/` through
    `pyproject.toml`'s `license-files` and sdist `include`; `middleware/debug_toolbar.py`'s docstring and a
    `{% comment %}` atop the template (stripped at render) name both origins and files; the glossary term and spec-042
    no longer call the project archived. Tests: `tests/middleware/test_debug_toolbar.py` and live
    `test_debug_toolbar_api.py` pass unchanged (the render is the old one plus one leading newline).
    - `_completion.py::_gather_with_cancel` is independent: no statement of graphql-core 3.3.0a12's
      `gather_with_cancel` survives, and its cancel semantics are the opposite. No license is owed.
    - The remaining "port of" claims name `django_graphene_filters`, the maintainer's own project; no third-party
      license applies.
  - The three remaining decisions copy nothing, so none is attribution work any more (yours):
    - Toolbar redesign onto the stock `djdt-request-id` header: recommend against. It drops the documented
      `debugToolbar` JSON key (a wire change), and the stock `fetch` patch loads after GraphiQL has captured
      `window.fetch` (graphiql 3.8.3, read statically, not run in a browser), so a bridge script is still needed and
      would have to reproduce the toolbar's module-private `replaceToolbarState`.
    - Moving the Strawberry and cross_web patches onto the package's views: every patched body delegates to the
      captured upstream method. Moving them drops the protection for consumers who mount Strawberry's own view and the
      `APPLY_UPSTREAM_PATCHES` `strawberry` / `cross_web` keys, and the Relay arm cannot move. Recommend not.
    - Moving the graphql-core list patch onto `CompletionExecutionContext`: a plain `strawberry.Schema` or a custom
      `execution_context_class` would lose the fix, and the `graphql_core` opt-out key goes. Recommend not.

## Maintainer decisions (a reason to keep exists)

- [x] 23. (OPT-4 = O5, with ORM-1) The lateral builder and relation-order expansion are a second compiler
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
  - Outcome: split; the "entangled" claim held only for the expansion and the branch compile.
    - Landed: `_select_columns` reads Django's `Query.get_select_mask` + `SQLCompiler.get_default_columns`, and
      `_order_columns` compiles the expanded order with `SQLCompiler.get_order_by`. `defer()` shapes, a multi-table
      child's own `.only()`, `F(...).asc()` / `.desc()` and trimmed relation-key orders now take the lateral path.
    - Kept: the order expansion (`expand_relation_order` and its helpers, ~120 lines). Window order terms must resolve
      against the window's own query, and Django's seam returns alias-bound `Col`s from a join-mutated query, so the
      swap would move the plan and four consumers (window, scalar projection, index advisory, lateral map) onto `Col`
      vocabulary for about -80 lines and change the Postgres ORDER BY text. The expansion is CONFIRMED faithful.
    - Maintainer decision: compiling the whole lateral branch with Django (`as_sql()` plus a hand-written
      LATERAL/VALUES shell, about -300 lines). It replaces the recognizer's plan-time WHERE proof, changes the emitted
      SQL text, and lets multi-table and `Exists` visibility scopes ride lateral.

- [x] 24. (OPT-5) `_correlation_steps` hand-builds the GenericRelation content-type restriction
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
  - Outcome: kept, with the reason at the site. `get_content_type()` / `get_extra_restriction` bake the default
    alias's ContentType pk (`get_for_model` caches per alias and ignores `using`), which matched the wrong rows on a
    shard with divergent content-type pks in 10 of 14 probe cases; the natural-key join resolves on the statement's
    alias. The arm also runs at declaration time, where a lookup would be database I/O. Pinned by
    `examples/fakeshop/test_query/test_multi_db.py::test_generic_relation_filter_matches_content_type_on_shard_b_alias`.

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
  - Research at `6fb82b7d` (maintainer decision, left open):
    - `ASGIRequest` on a copy of the handshake scope is unsafe. It parses `Content-Type` eagerly (`BadRequest` at
      6.1.2, `LookupError` at 5.2.16 on a crafted value) and decodes `query_string` as UTF-8 (`UnicodeDecodeError`),
      so a client-controlled handshake would raise past the `DisallowedHost`-only catch.
    - `ASGIRequest` on a fresh minimal scope (synthesized `method` and `path`, only the `host` / `x-forwarded-host`
      headers, the handshake's `server`) matches ours on a 16,512-case grid with 0 diffs at both versions. It saves
      about 10 code lines and 20 docstring lines, but it is still Decision 19's synthesized HTTP scope, fed to a
      constructor whose scope contract is undocumented.
    - No smaller seam exists. Channels' validators read `Origin` only, and calling `validate_host` directly would
      re-derive `_get_raw_host`.
  - Re-verified (yours, recommend keeping; Decision 19 stands):
    - Django's host code (`_get_raw_host`, `get_host`, `get_port`, `validate_host`, `split_domain_port`) hashes
      identical at 5.2.16 and 6.1.2; `ASGIRequest.__init__` drifts only outside the Host path (`HTTP_COOKIE`,
      `path_info`, the `Content-Type` `BadRequest` wrap). The header-to-META mapping is inline in the constructor at
      both; channels 4.3.2 and daphne have no `META` / `get_host` code; `AsyncRequestFactory` injects
      `host: testserver`. Ours vs the minimal-scope `ASGIRequest`: 0 diffs on 50,370 cases per version.
    - Corrected: the docstring called the two unprojected keys (`HTTP_X_FORWARDED_PORT`, the
      `SECURE_PROXY_SSL_HEADER` header) "provably verdict-neutral". They are only when a `Host` or
      `X-Forwarded-Host` header is present. On a hostless handshake under `USE_X_FORWARDED_PORT`, a malformed
      `X-Forwarded-Port` makes `example.com:abc`, which `get_host()` refuses and ours allows; a `SERVER_NAME` ending
      in `:<digits>` can flip either way. The authority is the server's own name in every case, so this is a
      robustness row (AGENTS.md line 39), not a spoof. `consumers.py::_host_validation_request` and the
      `tests/test_routers.py` subset row now state the exact condition.
    - Your options: keep (recommended), or project the two keys plus the scope `scheme` to agree with HTTP on a
      hostless handshake, which widens the hand-built `META`. The `ASGIRequest` seam has the same gap.

- [x] 26. (NET-3) The Strawberry patch shields `parse_query_params` with a pinned copy of upstream's body
  - Our code: `_strawberry_patches.py::_patched_parse_query_params` (~17 lines), `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE`
    (~20) and the body-source pin in `_validate_upstream_shape` (~12).
  - Upstream: `strawberry/http/base.py::BaseView.parse_query_params`, unchanged from 0.322.2 to 0.327.7.
  - Lines: ~40.
  - Status: landed as 22b (the ContextVar delegate).
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

- [x] 27. (TYP-3) Enum values `True` / `False` / `NULL` get a `MEMBER_` prefix that GraphQL does not require
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
  - Research (yours): the divergence is narrower than stated above, and no part of it is a defect.
    - `True`, `False` and `None` never reach the reserved arm: the Python-keyword step runs first and publishes
      `_True` / `_False` / `_None`, which a swap leaves alone. The real divergence is the casefold: `NULL`, `TRUE`,
      `FALSE` and any mixed case (`Null`) publish as `MEMBER_NULL` etc., where graphql-core accepts them bare.
    - Upstream: `assert_enum_value_name` refuses exactly `true` / `false` / `null`, case-sensitively, with the same
      body at 3.2.0, 3.2.8 and 3.3.0a12. graphql-core parses `NULL`, `TRUE`, `True` and `Null` as `EnumValueNode`
      at every version (only lower-case `true` / `null` are boolean / null literals), so no client ambiguity exists.
      Strawberry renames nothing; strawberry-django and graphene-django prefix nothing for case.
    - Every name we publish passes upstream's check, and lower-case `true` / `false` / `null` are prefixed by both.
      Fakeshop hits the reserved arm 0 times (its only `MEMBER_` names are the digit arm's `MEMBER_1/2/3`).
    - The casefold has no recorded reason beyond commit d3829b25's message; spec-051 calls it "a sanitizer choice,
      not a validity rule".
    - Recommendation: ask `assert_enum_value_name` on the exact name and drop the casefold (`NULL` / `TRUE` /
      `FALSE` / `Null` choices publish bare: a wire change for those values). The alternative keeps the wire and
      writes the casefold's reason into spec-001 and the glossary.
  - Landed (maintainer chose the swap): the reserved arm asks `assert_enum_value_name` through
    `types/converters.py::_graphql_refuses_enum_value` and `_GRAPHQL_RESERVED_ENUM_VALUES` is gone; spec-001 and
    spec-051 restated. Live row `test_converter_outputs_api.py::test_reserved_choice_values_publish_and_serialize_all_members`
    `[graphql-literal-case]` fails on the casefold; removing the arm fails it and `[graphql-reserved]`. The input
    side is `::test_a_literal_cased_choice_member_writes_its_stored_value` (a bare `NULL` / `Null` literal writes
    its value, `MEMBER_NULL` is refused); three of its four rows fail on the casefold.
    CHANGELOG: CHANGELOGTODO.md entry 902.

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
  - Research (yours): recommend keeping the pins as a wire contract.
    - `graphql_camel_name` is not a model of Strawberry's `to_camel_case`: it is injective on purpose (keeps `_`
      before a digit, leading and trailing underscores, `__x` for adjacent one-letter segments), so `field_2` and
      `field2` both publish. AGENTS.md line 6 has nothing to swap it for; the converter offers no injective seam.
    - Not wire-neutral even by default: on fakeshop, dropping the pins renames 31 input fields in 17 types under
      `auto_camel_case=True` (all digit boundaries: `isbn_10` → `isbn10`, `publisher_2Id` → `publisher2Id`) and
      3,528 under `auto_camel_case=False` (2,176 of them the `LOOKUP_NAME_MAP` pins, which stay under any swap).
      `field_2` beside `field2` would become a build-time collision refusal.
    - The listed sites are incomplete: `utils/inputs.py::emit_set_input_field_triples` and `::optional_input_field`
      pin too. The ~40 lines would not be saved: forms and serializers would need the model flavor's per-request
      published-name read-back (+45 to 70 lines).
    - Upstream (0.322.2 and 0.327.7 alike): an explicit `name=` bypasses only `apply_naming_config`; a converter
      overriding `get_graphql_name` / `from_field` still respells pinned names. That exposed item 37.
    - If you want parity (names matching the output types and `auto_camel_case=False`), item 37's read-back is the
      prerequisite; then the swap is a pure wire decision over about 10 to 15 test files.

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
  - Research (yours): recommend keeping the transport seam.
    - The hook is `SchemaExtension.on_stream_result`, first in strawberry-graphql 0.323.0 (0.322.2 has no hook, no
      runner method and no `StreamExecutionResult`; present and unchanged in every release from 0.323.0 to 0.339.0).
      Raising the floor drops exactly 0.322.2; the touch list is `pyproject.toml`, `utils/imports.py`'s
      `STRAWBERRY_FLOOR`, the `django.yml` floor cell, the floor literals in `tests/test_ci_governance.py` and
      `tests/test_routers.py`, BUILD.md "Floor verification" and two glossary bodies.
    - Contract: the hook wraps every frame of `schema.stream` / `schema.subscribe` (both WebSocket protocols, plus
      SSE and multipart); it cannot replace the frame (`async with ...: yield result` ignores its value), only
      mutate it in place before its `yield`; pre-yield runs in list order, so with the policy installed first every
      consumer extension's hook would see already-masked errors.
    - Why keep: at the 0.322.2 floor a moved mask is silently never called; the hook covers only schemas that carry
      `DjangoErrorPolicyExtension`, while today the consumer seam also masks a plain `strawberry.Schema` through
      `schema_error_policy`'s default; and the fail-closed whole-frame replacement (`degraded_result`) has no
      in-place equivalent. The saving is the two masking lines, one import and the `schema` parameter threading.
    - The tracker's stated `original_error` reason is overstated: the debug payload is built at `on_execute`
      teardown, before any frame exists, so an in-place masker leaves `debug.exceptions` intact in either order
      (probed on `DjangoSchema` at 0.323.0 and 0.327.7).
    - To move it anyway you decide three things: raise the floor to 0.323.0, drop or close the plain-Schema masking
      over WebSocket, and accept the ordering change.
    - Fixed in passing: `consumers.py`'s module docstring and `_stop_aware_results` claimed the masking import was
      function-local; it is module-level (the module stays `channels`-free).

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
  - Research (yours): recommend closing as kept; the reasons above need three corrections.
    - The GraphQL wire never changes: a declared range publishes `{start, end}` either way, and the generated
      `range` lookup is the `BaseRangeFilter` CSV list, which this item does not touch. Only the form keys
      (`_0`/`_1` vs `_min`/`_max`) and the list-vs-slice value differ, and both can be kept with a
      `RangeWidget(suffixes=["0", "1"])` subclass and a list-returning `compress`.
    - Per-column cleaning survives a swap through `RangeField(fields=(col, col))`; the integer gte+lte split lives in
      `RangeFilter.filter`, which a field swap never touches. A plain swap to the stock filter is not viable: its
      Decimal sub-fields refuse date bounds and accept a `1e60` price bound our column cleaning refuses.
    - Nothing is copied. `validate_range` shares only its message and code with graphene-django's; no license is
      owed, so the attribution half is empty.
    - The partial swap (subclass django-filter 25.2/26.1's `RangeField(MultiValueField)`, byte-identical at both)
      saves about 45 of 97 lines, but over 64 clean cases it differs twice: a non-pair is no longer refused by
      `validate_range` (no wire input sends one), and two bad bounds produce two `FILTER_INVALID` entries instead of
      one. The second is a wire delta, so the swap is your call; it also drops the public `validate_range` export.
      Fakeshop has 17 hand-declared range filters (12 package, 5 django-filter) and about 35 test lines pin `_0`/`_1`.

- [x] 31. (F8) `_PUBLIC_PACKAGE_FILTER_DEFAULTS` is a verbatim copy of `FILTER_FOR_DBFIELD_DEFAULTS`
  - Our code: `filters/sets.py::_PUBLIC_PACKAGE_FILTER_DEFAULTS` (~60 lines).
  - Upstream: `django_filters/filterset.py::FILTER_FOR_DBFIELD_DEFAULTS`.
  - Lines: ~60.
  - Status: CONFIRMED identical on django-filter 26.1: 0 key, class or extra diffs, and 286 extra-provider outputs with
    0 diffs. Landed as 22c (derived from upstream, provenance-checked baseline).
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
  - Research (yours): recommend closing as kept.
    - Measured: the family is 3,253 lines (1,386 code), 53% of `utils/querysets.py`; the item's contiguous block is
      1,982 lines, 775 of them code. `_seal_or_defect` has 6 call sites, all in that module; `list_field.py` imports
      `_type_is_genuinely_django` and `optimizer/walker.py` imports `_pk_membership_query_or_defect`.
    - No wire input reaches it: every input is a queryset an application hook or manager returned. spec-045
      Decision 8 scopes it to a mistaken hook and closes the dispatch-path expansion; START.md "Verified and
      rejected" bars reintroducing a blacklist.
    - No upstream seam keeps the guarantee. `QuerySet._chain()` / `_clone()` build `self.__class__` and dispatch on
      the candidate, and Django 6.1's `_chain` returns `self` when cloning is disabled; `Query.clone()` shares leaf
      lookups and `Query.__deepcopy__` is `clone()`. The two exact-seam fragments (the deferred-filter bake through
      the `QuerySet.query` getter, and `base_table` on the rebuilt query) total about 10 lines.
    - The plain-attributes swap (this item as worded) drops ownership, the plain-class rebuild and the alias,
      combinator and slicing policies built on it. Not recommended.
    - If you want it smaller, the option is "reconstruct first": rebuild the candidate's `sql.Query` straight from
      `__dict__` (as `_reconstructed_value` already does for an embedded query) instead of proving each node and then
      calling `Query.clone`. It removes about 1,050 lines (about 480 code): the graph walkers, the payload and
      container provers and the raw-SQL / template / metadata hardening. Scratch probes compiled identical SQL on 7
      shapes and refused 4 of 7 crafted shapes; a class-valued instance shadow and a self-referential list got
      through, so `_shadow_defect` and a cycle guard would stay. It changes defect wording, spec-045 Decision 2 and
      two glossary bodies, and rewrites about 70 of the 397 `tests/utils/test_querysets.py` rows. It needs your go
      and a spec-045 amendment.

- [ ] 33. (TYP-12) GIS/GEOS fields are unsupported; strawberry-django has a scalar block to adapt
  - Our code: `types/converters.py::SCALAR_MAP` / `FIELD_OUTPUT_TYPE_MAP` have no GEOS arm.
  - Upstream: the GEOS scalars and the `field_type_map.update` block in `strawberry_django/fields/types.py`. MIT,
    crib only: adapt with attribution.
  - Lines: adds code.
  - Status: SUSPECTED.
  - Reason to keep ours: n/a. This is a feature gap, not a copy.
  - Behaviour change: adds new scalars.
  - Risk / blockers: needs GDAL; it is a new KANBAN card, not a refactor. Item 22 covers the license.
  - Research (yours): a project, already owned by card `BACKLOG-STABLE-076-1.1.0` (GIS / GeoDjango geo scalars,
    Backlog, depends on card 054's pluggable field-conversion registry). Nothing lands in this sweep.
    - Upstream: `strawberry_django/fields/types.py`'s GEOS block is 105 lines: 8 coordinate-array scalars registered
      process-globally, 7 `field_type_map` rows, no geometry filter lookups. Its shape loses SRID and Z, its
      `Geometry` scalar cannot parse its own output, and its serializers pass wrong types through.
    - Today a spatial column fails closed (`Unsupported Django field type 'PointField'`), and the
      `SCALAR_MAP[GeometryField] = <scalar>` escape hatch already resolves through the MRO.
    - Blockers: this machine has no GDAL, GEOS or SpatiaLite; `django.contrib.gis.geos` and `.db.models` raise
      `ImproperlyConfigured` (not `ImportError`) without GDAL at 5.2.16 and 6.1.2, so the soft-dependency helpers and
      the `sys.modules` absence sentinel do not fit; a fakeshop model importing GIS breaks every GDAL-less run;
      Django 5.2.16 lacks 6.1's nested-geometry input guard, so a raw-string geometry input is a native-parser risk.
    - Plan if promoted: decide satellite package vs documented recipe (the card's open question; the recipe is the
      escape hatch plus `strawberry_config(extra_scalar_map=...)`, a guides-card page). An in-tree build lands after
      card 054 in three slices: strict read/write scalars (own statements, or an adapted block with
      `LICENSE.strawberry-django`, which item 22 now ships), geometry-operand filter lookups (about 24 of the 29
      Django GIS lookups), then distance / `relate` composite inputs. It needs an env-gated `FAKESHOP_GIS=1`
      SpatiaLite alias with its own app, a GDAL + SpatiaLite CI tier, and absence tested as `ImproperlyConfigured`.
      Roughly 1,500 to 2,000 lines for the first two slices.

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
