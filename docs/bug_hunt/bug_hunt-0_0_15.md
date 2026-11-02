# Bug hunt 0.0.15: to-do list

Every finding from both 0.0.15 hunts, checked against main on 2026-11-01. The Sep-3 hunt landed its fixes on main at
the time. The Sep-19 hunt ran in the t3 worktree and was never merged; its findings were re-done on main one by one in
[`bug_hunt-0_0_15_2.md`](bug_hunt-0_0_15_2.md), whose item numbers the entries below cite. A package file with no
finding in either hunt has one entry saying so.

Progress: 229 done, 10 to do.

## To do

- [ ] 84. Live rows for the composite-index advisory over an M2M window: the hunt asked for a fakeshop M2M-ordering
  fixture so a live `/graphql` test tells the silent M2M window from a wrongly advised one (deep dive 1 promotion P2, a
  nested M2M connection with a non-pk order and no covering index, is the same row). The fix has package pins only
  (`tests/optimizer/test_nested_index_advisory.py`, `269b80c0`, bug_hunt-0_0_15_2.md item 3);
  `examples/fakeshop/test_query/test_library_shapes_api.py::test_to_many_relation_name_book_order_pages_genre_books_connection_like_the_pipeline`
  pages an M2M connection by a non-pk order live but asserts no advisory. Add the live advisory row, or rule the package
  pins enough. Found hunting `optimizer/nested_planner.py` and in deep dive 1 (Sep-19)
- [ ] 102. Decide: the write side passes a `relay.NodeID` over a non-column attribute (one the type's `get_queryset`
  annotates) through as the raw primary key (`relay.py::_resolve_real_pk`), so a relation write naming such a type
  stores whichever row's pk equals the id's text, while the filter side refuses that slot. Refuse it on writes too, or
  keep the pass-through? Tracked as bug_hunt-0_0_15_2.md item 321, still open. Found hunting `relay.py` (Sep-3)
- [ ] 144. A set subclass used only as a related-set target and never wired to a type binds the base's owner, silently,
  in a cross-model FilterSet inheritance; the hunt judged it benign in every reachable shape and fixed nothing.
  bug_hunt-0_0_15_2.md item 73 asks whether to keep it or fall back to the target model's registered type, and is
  unanswered. Found hunting `types/finalizer.py` (Sep-19)
- [ ] 205. Final test gate: never run for the Sep-19 campaign (it waited on the naming decision), so its Postgres,
  sharded and async-transport cells stayed unverified there; the Sep-3 full run passed (7306 passed, 100% coverage). On
  main the gate is the maintainer's full Actions run on a green HEAD: the latest `django.yml` run (`34f34860`) failed
  its Coverage job, the one before (`b8eda47d`) passed. Tracked as bug_hunt-0_0_15_2.md item 29 (with CI rows 415 and
  417: no Postgres x sharded cell, no Postgres coverage diff). Found at the final gate (Sep-3, Sep-19)
- [ ] 219. Mutation naming posture. A mutation class whose `__name__` raises, is not a `str`, is a format-hostile `str`
  subclass or is not a GraphQL name: t3 published a degraded `<MetaclassName>Payload` type (the error-label renderer
  reaching type naming at `mutations/sets.py` / `mutations/fields.py`, pinned by `tests/mutations/test_fields.py`) and,
  after the `types/base.py` guard, rejected a `DjangoType` whose `__name__` is not an exact `str` at class creation; the
  second-reader challenge ended in a maintainer decision request: (A) publish the degraded name or (B) reject at
  definition with a typed `ConfigurationError`. Unanswered. On main the model and form flavors fail raw at declaration,
  a non-identifier name raises a raw `SyntaxError` at `DjangoMutationField`, and `"Create-Item"` fails only at schema
  build. Open as `bug_hunt-0_0_15_2.md` item 26 (also items 220 and 229: raising `Meta.permission_classes` name,
  identifier-but-not-GraphQL input names). Covers the Sep-3 lead that `mutations/fields.py::_validate_mutation_target`
  renders `__name__` unguarded. Found in review 5c / 5d (Sep-19) and as an open lead of the Sep-3 campaign
- [ ] 224. Dive 3 HIGH (disclosure and handling). A consumer `Prefetch` hint over a type whose `get_queryset` hides rows
  bypassed that hook: `optimizer/walker.py::_apply_hint` installed the consumer queryset and marked the relation
  planned, so a documented `Meta.optimizer_hints` plus an ordinary anonymous nested query served hidden rows; 0.0.14 is
  affected. The defect is fixed on main (`5d4cdb3b`, plus `00563dd0` for a consumer `select_related` outranking a
  planned visibility `Prefetch`; `bug_hunt-0_0_15_2.md` item 13). Left open: the maintainer decision on disclosure
  (advisory, release note) and a `SECURITY.md` path for a maintainer-found finding; `SECURITY.md` on main still
  describes only outside reporters (`bug_hunt-0_0_15_2.md` item 204). Found in deep dive 3 (Sep-19)
- [ ] 226. Dive 5 (error reporting) found 25 test sites whose assertions check only the `FieldError` key, so they would
  pass under the counterfactual payload (the R2(c) lesson: a key-only body passed under its own counterfactual);
  proposed as a test-hardening card. No tracker row in `bug_hunt-0_0_15_2.md`. Unverified on main: the 25-site census
  was t3's; main's FieldError wire-name re-key landed through item 11 (`7517eab2`) and its tests were not re-censused
  here. Left: re-census assertions that name only the key, tighten them to the full payload. Found in deep dive 5
  (Sep-19)
- [ ] 227. Dive 5 could not exercise the async nested-body error row on the hunting interpreter (5 definitions / 6
  items; the sync twins carry the erratum-corrected pins). Unverified on main whether a fixture exists that drives the
  async nested path to that row; no tracker row in `bug_hunt-0_0_15_2.md`. Found in deep dive 5 (Sep-19)
- [ ] 228. Malformed `BigInt` literal: graphql-core reports a custom scalar's literal rejection as an error carrying its
  originating exception, so the production error policy masks it (`unexpected error` + `correlationId`) instead of the
  clean scalar message; `examples/fakeshop/test_query/test_scalars_api.py` documents the behaviour and opens the
  pass-through gate (`DEBUG=True`) to assert the reason. Not tracked in `bug_hunt-0_0_15_2.md`. Unverified at runtime
  (not executed here): whether a client under the default policy still gets only the masked message for a bad `BigInt`
  argument; decision needed whether scalar parse/literal rejections should pass the policy like validation errors.
  Owners `scalars.py` / `extensions/error_policy.py`. Found as an open lead of the Sep-3 campaign (batch-17 residue
  triage for `filters/inputs.py`)
- [ ] 233. `pbugs.md` tranche 2 (items 11-20): classes a single-cell hunt (Python 3.14 / Django 6.1 / SQLite / single
  DB) cannot reach, never hunted in either campaign: Django-metadata divergence 5.2 to 6.1, environment-conditional
  branches, Postgres-only `lateral_fetch` SQL, the three monkeypatch modules against a one-dimensional version matrix,
  PEP 649, fixture-shape gaps, migration drift, settings-module split, scheduler-dependent isolation, vendor-divergent
  SQL. On main they are tracked as open CI/tooling rows (`bug_hunt-0_0_15_2.md` items 413 migration drift, 414 settings
  split, 415 Postgres x sharded cell, 416 strawberry pin cell, 417 Postgres coverage diff, 418 randomized-order run, 419
  Postgres keyset round trip), with item 150 done (NULL placement doc). No row covers metadata divergence (11),
  environment-conditional branches (12) or PEP 649 (15) beyond the CI floor and latest cells. Found as the structural
  open lead of the Sep-3 campaign

## Done

- [x] 1. `_boundary_ordering.py`: no bugs in either campaign. Found hunting `_boundary_ordering.py` (Sep-3, Sep-19)
- [x] 2. `_cross_web_patches.py`: no bugs in either campaign. Found hunting `_cross_web_patches.py` (Sep-3, Sep-19)
- [x] 3. Medium. `_django_patches.py`: `importlib.reload()` re-executed the module-level validated-source global while
  the previous patch generation stayed installed on `SimpleTestCase`, so every later `tearDownClass` raised
  `RuntimeError` until the next `apply()` (for good when patches were disabled at that moment). Fixed (`a8f31a2d`): the
  module now recovers Django's descriptor from the installed patch's stamp (`_captured_upstream_descriptor`), so the
  running generation keeps its teardown and the next `apply()` revalidates; test
  `tests/test_django_patches.py::test_reload_preserves_the_installed_patch_teardown`. The Sep-19 hunt found nothing more
  (a `__class__`-liar re-examined and judged not a defect). Found hunting `_django_patches.py` (Sep-3, Sep-19)
- [x] 4. `_graphql_core_patches.py`: no bugs (the file is not in the Sep-3 campaign). Found hunting
  `_graphql_core_patches.py` (Sep-19)
- [x] 5. `_request_body.py`: no bugs in either campaign. Found hunting `_request_body.py` (Sep-3, Sep-19)
- [x] 6. `_strawberry_patches.py`: no bugs in either campaign. Found hunting `_strawberry_patches.py` (Sep-3, Sep-19)
- [x] 7. `apps.py`: no bugs in either campaign. Found hunting `apps.py` (Sep-3, Sep-19)
- [x] 8. Low. `auth/mutations.py::_authenticated_actor_or_none`: a hostile `is_authenticated` value whose `__bool__` /
  `__len__` raises escaped the final truthiness test as a top-level error. Sep-3 contained it to anonymous (`a8f31a2d`);
  superseded: `73a190b6` removed that containment family on purpose, so a consumer's raising `is_authenticated`
  (attribute read, legacy call or truthiness test) now propagates to the schema's error policy and never classifies the
  request as anonymous (`tests/auth/test_queries.py::test_a_raising_is_authenticated_propagates_to_the_error_policy`).
  Found hunting `auth/mutations.py` (Sep-3)
- [x] 9. (robustness) A hostile `__name__` on a user model, mutation holder or payload class (seal rebind / delete,
  declared / new conflict, register-exclusion model, bind ambiguity / no-type model: seven label sites) escaped the
  typed error as a raw exception, and a `str`-subclass `USERNAME_FIELD` entry whose `__format__` raises did the same
  through the seal label. Already fixed on main: every class label reads through `utils/truth.py::name` (`73a190b6`).
  Whether a hostile class name should fail at declaration is the open question of bug_hunt-0_0_15_2.md item 26. Found
  hunting `auth/mutations.py` (Sep-19)
- [x] 10. (robustness) `auth/mutations.py::derive_register_fields` rendered `{protected!r}` over producer-controlled
  `USERNAME_FIELD` / `REQUIRED_FIELDS` values, so a `str` subclass with a raising `__repr__` escaped as a raw
  `RuntimeError`. Done as bug_hunt-0_0_15_2.md item 17 (`b4d6e06a`): every entry is read as plain text and the label
  names it by value
  (`tests/auth/test_mutations.py::test_derive_register_fields_names_a_protected_str_subclass_by_value`). Found hunting
  `auth/mutations.py` (Sep-19)
- [x] 11. `auth/queries.py`: no bugs in either campaign. The Sep-3 hunt reproduced the `is_authenticated` truthiness
  escape recorded under `auth/mutations.py` and added an async-parity test for it; that contract has since changed to
  propagate (see that entry). Found hunting `auth/queries.py` (Sep-3, Sep-19)
- [x] 12. `auth/sessions.py`: no bugs in either campaign. Found hunting `auth/sessions.py` (Sep-3, Sep-19)
- [x] 13. Low. `conf.py`: six message sites interpolated `{type(value).__name__}` at the raise, so a value whose
  metaclass has a raising `__name__` made `_normalize_user_settings` and `upstream_patches_enabled` raise a raw
  `RuntimeError` instead of `ConfigurationError`. Fixed (`a8f31a2d`); the messages now render through `utils/truth.py`
  (`kind`, `render`), pinned by `tests/base/test_conf.py::test_normalize_rejection_skips_raising_metaclass_name`,
  `test_upstream_patches_toggle_rejection_skips_raising_metaclass_name` and
  `test_upstream_patches_mapping_value_rejection_skips_raising_metaclass_name`. The Sep-19 hunt found nothing more.
  Found hunting `conf.py` (Sep-3, Sep-19)
- [x] 14. Low. `connection.py::_attach_count_sync` / `_attach_count_async` read `.count` on a non-queryset resolver
  result (set, frozenset, generator, one-shot iterator) even when `totalCount` was not selected, raising a raw
  `AttributeError`. Fixed (`a8f31a2d`): the source is read only when the count is wanted
  (`_guard_total_count_countable`, `_set_total_count`); live rows
  `examples/fakeshop/test_query/test_connection_fields_api.py::test_consumer_resolver_generator_paginates_without_total_count`
  and `test_async_consumer_resolver_set_source_paginates_without_total_count`. Found hunting `connection.py` (Sep-3)
- [x] 15. Low. A connection resolver returning a scalar (`None`, an `int`) leaked a blank `AssertionError` from
  Strawberry's slicer at the GraphQL boundary. Fixed (`a8f31a2d`): `connection.py::_guard_non_queryset_iterable` runs
  first and raises a `GraphQLError` naming the resolver contract
  (`tests/test_connection.py::test_guard_non_queryset_iterable_admits_getitem_only_sequence`, live
  `test_connection_fields_api.py` message row). Found hunting `connection.py` (Sep-3)
- [x] 16. Low. `connection.py::_consume_fallback`: a list, tuple or generator consumer resolver served a negative offset
  `after` cursor as a wrapped slice instead of a cursor error. Done as bug_hunt-0_0_15_2.md item 2 (`a57bd826`, every
  offset cursor through one decoder; live rows
  `test_connection_pagination_api.py::test_negative_offset_cursor_on_a_sequence_resolver_is_a_cursor_error` and the
  async, generator and queryset twins). The Sep-19 stale re-pass over the sealed pipelines found nothing else. Found
  hunting `connection.py` (Sep-19)
- [x] 17. High. `consumers.py`: a non-object JSON frame, an unhashable operation id, a non-dict or missing subscribe
  payload, an unknown legacy `stop` id or a deeply nested document escaped the generated handlers' message loop as a raw
  exception, killing the connection task while the socket stayed open (a per-connection denial of service). Fixed
  (`a8f31a2d`): `_contain_message_loop_failure` closes `4400` "Failed to parse message" for client frame-shape escapes
  (`TypeError`, `KeyError`, `RecursionError`) and `1011` "Internal error" for anything else, logging both server-side;
  tests `tests/test_routers.py::test_the_containment_close_names_whose_fault_the_escape_was` and
  `test_a_non_dispatchable_frame_is_refused_and_the_connection_ends`. The Sep-19 re-pass of the 6-line docstring delta
  found no bug. Found hunting `consumers.py` (Sep-3, Sep-19)
- [x] 18. Low. `utils/policies.py::resolve_policy` (owner of `error_policy.py`'s override ladder, shared with
  `ResourcePolicy`) validated the override mapping over one iteration and built the policy over a second, so a divergent
  one-shot mapping or an unhashable key leaked a raw `TypeError` instead of `ConfigurationError`. Fixed (`a8f31a2d`):
  the mapping is materialized once and read as a plain dict, with a key-type guard before set membership
  (`tests/utils/test_policies.py::test_a_divergent_one_shot_mapping_resolves_from_one_consumed_pass`,
  `test_a_hashable_non_string_key_is_typed_rejected_at_the_key_guard`). A raising iterator now propagates its own error
  by design (`73a190b6`). The Sep-19 re-pass of the canonical-copy default path found no bug. Found hunting
  `error_policy.py` (Sep-3, Sep-19)
- [x] 19. Low. `exceptions.py::_safe_text` let a `str` subclass returned by a message object's `__str__` through the
  `rendered or fallback` check, so its `__len__` raised during error-envelope assembly. Fixed Sep-3 (`a8f31a2d`), then
  superseded: `73a190b6` removed the `_safe_*` containment family; framework messages are exact `str` built at the raise
  site and a consumer object raised as a message renders through its own dunders
  (`tests/test_exceptions.py::test_consumer_message_arg_renders_through_its_own_dunders`). The Sep-19 hunt found no bug
  in the earlier layout. Found hunting `exceptions.py` (Sep-3, Sep-19)
- [x] 20. Medium. `extensions/debug.py`: `Schema.stream()` snapshots extension results inside the still-open operation,
  before `on_operation` teardown, so the debug payload was never published on the streaming / WebSocket seam while its
  capture cost was paid. Fixed (`a8f31a2d`): `on_execute` stashes right after graphql-core returns, `on_operation` still
  rebuilds at teardown (`tests/extensions/test_debug.py::test_streaming_seam_publishes_the_payload_the_engine_reads`).
  Found hunting `extensions/debug.py` (Sep-3)
- [x] 21. Low. `extensions/debug.py::_serialize_sql_row` let NaN / Infinity SQL durations into payload rows, which a
  strict JSON encoder then rejects for the whole debug payload. Fixed (`a8f31a2d`): a non-finite duration is refused and
  only that row is dropped
  (`tests/extensions/test_debug.py::test_a_nan_duration_costs_only_its_own_row_and_the_rest_keep_their_order`). Found
  hunting `extensions/debug.py` (Sep-3)
- [x] 22. Low. Deleting `settings.DEBUG` crashed `extensions/debug.py`'s disclosure gate. Fixed (`a8f31a2d`): an
  unreadable `DEBUG` answers inert, only `debug is True` discloses
  (`tests/extensions/test_debug.py::test_deleted_debug_setting_is_an_inert_refusal`). The Sep-19 hunt found no further
  bug. Found hunting `extensions/debug.py` (Sep-3, Sep-19)
- [x] 23. Low. `extensions/error_policy.py::masking_is_active` read `settings.DEBUG` bare, so with `DEBUG` absent the
  `AttributeError` escaped the gate, the teardown floor destroyed healthy `data` beside the errors it should have
  masked, and the subscription seam raised mid-stream. Fixed (`a8f31a2d`): an unreadable `DEBUG` reads as not exactly
  `True`, so masking stays on
  (`tests/test_error_policy.py::test_the_masking_gate_stays_active_when_debug_cannot_be_read`,
  `test_a_teardown_with_unreadable_debug_masks_normally_and_keeps_data`). Found hunting `extensions/error_policy.py`
  (Sep-3)
- [x] 24. Low. A hostile `ErrorPolicy` (isinstance-valid via `object.__new__`, validation skipped) with a raising
  `message` or `enabled` property escaped `_degraded` and the gate, leaving the original sensitive message on the wire.
  Fixed (`a8f31a2d`), and closed at the root by `9350eb8d`: the schema stores a validated copy of the policy built from
  its field values (`utils/policies.py::canonical_policy`), so no seam reads a consumer object
  (`tests/test_error_policy.py::test_a_str_subclass_cannot_survive_into_the_private_record`). Found hunting
  `extensions/error_policy.py` (Sep-3)
- [x] 25. Low. `extensions/error_policy.py::mask_execution_result` trusted `if not errors`, so a falsy-but-populated
  error container skipped classification and unmasked errors reached the client. Fixed (`a8f31a2d`): the list is
  materialized before the emptiness check
  (`tests/test_error_policy.py::test_a_falsy_but_populated_errors_container_is_still_masked`). Found hunting
  `extensions/error_policy.py` (Sep-3)
- [x] 26. Low. `extensions/error_policy.py::_is_unexpected` read `original_error` through a defaulted `getattr`, so a
  raising property was answered as absent, taking the deliberate-delivery branch and shipping the error's own message.
  Fixed (`a8f31a2d`): a direct read whose raise `_replacement_for` degrades to the policy message
  (`tests/test_error_policy.py::test_an_original_error_read_that_raises_is_masked_not_trusted`). The Sep-19 re-pass of
  the `9350eb8d` rewrite found no bug. Found hunting `extensions/error_policy.py` (Sep-3, Sep-19)
- [x] 27. `extensions/operation_state.py`: no bugs (the file is not in the Sep-3 campaign). Found hunting
  `extensions/operation_state.py` (Sep-19)
- [x] 28. (robustness) `extensions/resource_policy.py`: `max_nested_rows` had no behavioral coverage anywhere. Closed
  (`a8f31a2d`) with live rows
  `examples/fakeshop/test_query/test_resource_policy_api.py::test_a_nested_row_list_over_the_bound_is_rejected`,
  `test_a_nested_row_list_at_the_bound_is_not_rejected` and `test_a_nested_row_list_rides_in_through_one_variable`.
  Found hunting `extensions/resource_policy.py` (Sep-3)
- [x] 29. Low. `extensions/resource_policy.py::scan_document_text` raised raw `TypeError` / `AttributeError` /
  `KeyError` on a non-string `query`, which the WebSocket transport delivers unchecked. Fixed (`a8f31a2d`): a non-string
  document is declined before the lexer
  (`tests/test_resource_policy.py::test_a_non_string_query_is_declined_not_scanned`). Found hunting
  `extensions/resource_policy.py` (Sep-3)
- [x] 30. Medium. `extensions/resource_policy.py::_ValueBudget._charge_list_family` classified a mutation list by its
  item type name, so a raw-pk relation list (`[Int!]`, model, form and serializer flavors) got the looser membership
  bound and never fed the request-wide relation-id aggregate. Fixed (`a8f31a2d`): it keys on the bind-time
  `RELATION_MULTI` spec, the `ID`-name rule stays only as the plain-schema fallback
  (`examples/fakeshop/test_query/test_resource_policy_api.py::test_a_raw_pk_model_relation_list_over_the_bound_is_rejected`
  and the form, serializer, nested and aggregate rows). Found hunting `extensions/resource_policy.py` (Sep-3)
- [x] 31. Low. `extensions/resource_policy.py`: directive argument values and unread variable defaults were never
  charged though validation converts them before execution. Already fixed on main (`0c0537e2`; bug_hunt-0_0_15_2.md
  items 7 and 193; `test_resource_policy_api.py::test_field_directive_values_are_charged_as_input_nodes`). Found hunting
  `extensions/resource_policy.py` (Sep-19)
- [x] 32. Low. `extensions/resource_policy.py`: a spread's own directive values on an unknown or cyclic fragment escaped
  charging because the spread charge ran below the unresolvable / cyclic guard. Already fixed on main (`0c0537e2`;
  bug_hunt-0_0_15_2.md item 8;
  `test_resource_policy_api.py::test_a_directive_value_on_a_spread_of_an_unknown_fragment_is_charged`). Found hunting
  `extensions/resource_policy.py` (Sep-19)
- [x] 33. Medium. `filters/base.py`: a `RelatedFilter` target resolving to a non-`FilterSet` (plain class, a
  cross-family `OrderSet`, a factory returning a non-class) passed the `.filterset` read and failed later as a raw
  `AttributeError` in the BFS enqueue or `_expand_related_filter`. Fixed (`a8f31a2d`): `RelatedFilter._validate_target`
  is the family's target-type gate, a typed `ConfigurationError` naming owner, field and target
  (`tests/filters/test_base.py::test_related_filter_gate_rejects_plain_class_target`,
  `test_related_filter_gate_rejects_cross_family_orderset_target`). Found hunting `filters/base.py` (Sep-3)
- [x] 34. Low. `filters/base.py`: a scalar, one-shot iterator or generator passed to `ListFilter.filter` /
  `IntegerInFilter.filter` leaked a raw `TypeError`, a string `in` value iterated per character, and a lying `list`
  subclass, hostile `__repr__` or hostile `__eq__` escaped the GlobalID and `ArrayFilter` paths in place of the coded
  GraphQL error. Fixed (`a8f31a2d`): `_materialize_list_shaped_values` gates the list-shaped filters fail-closed
  (`tests/filters/test_base.py::test_list_filter_one_shot_iterator_is_a_coded_reject`). Found hunting `filters/base.py`
  (Sep-3)
- [x] 35. Medium. `filters/sets.py::FilterSet.get_fields`: a one-shot iterator or generator `Meta.fields` was consumed
  once and re-expanded to an empty field map on every later pass (the lazy-`RelatedFilter` re-expansion), the
  filter-side twin of the order family's gate. Fixed (`a8f31a2d`): the declaration shape is gated before the first
  consumption with a typed `ConfigurationError`
  (`tests/filters/test_sets.py::test_filterset_get_fields_rejects_one_shot_iterator_at_class_creation`). Found hunting
  `filters/base.py` (Sep-3)
- [x] 36. (robustness) Low. `filters/base.py::RelatedFilter._validate_target`'s owner-label line did an unguarded
  `isinstance(owner, type)`, so a bound owner with a raising `__class__` escaped the typed rejection as a raw
  `RuntimeError`. Already fixed on main: owner and target identity read through `utils/truth.py` (`is_type`, `qualname`,
  `kind`; `73a190b6`), which never asks the value. No test pins this exact shape; the truthful-reads gate
  (`scripts/check_truthful_reads.py`) bans the unguarded read. Found hunting `filters/base.py` (Sep-19)
- [x] 37. Medium. `filters/factories.py` (owner `utils/inputs.py::normalize_set_meta_for_factory`): a falsy `exclude`
  (`None`, `[]`, `()`, `set()`) stayed a cache-key discriminator although django-filter reads `exclude or []`, so one
  declaration minted two `CategoryAutoFilter` classes and `ConfigurationError: input type name ... claimed by two
  distinct FilterSet classes`. Fixed Sep-3 (`a8f31a2d`); the dynamic-set factory (`get_filterset_class`,
  `create_dynamic_set_class`, `normalize_set_meta_for_factory`) was later deleted as test-only package code
  (`899cb35b`), so the defect no longer exists. Found hunting `filters/factories.py` (Sep-3)
- [x] 38. Low. `get_filterset_class(None, model=...)` with no `fields` / `exclude` hit django-filter's metaclass
  assertion as a raw `AssertionError`. Fixed Sep-3 (`a8f31a2d`) with a `require_fields_or_exclude` flag; that factory
  was deleted with the rest of the dynamic-set code (`899cb35b`), so the defect no longer exists. The Sep-19 hunt found
  no bug in the file. Found hunting `filters/factories.py` (Sep-3, Sep-19)
- [x] 39. Medium. `utils/strings.py::pascal_case` collapsed leading and trailing underscore runs, so filter members
  whose names differ only at the edges (`price` / `price_` / `_price`) minted one operator-bag / range type name and
  Strawberry silently dropped the second member's lookups from the SDL. Fixed (`a8f31a2d`): edge runs are kept verbatim,
  interior runs still collapse (`tests/utils/test_strings.py::test_pascal_case_handles_snake_case_inputs`, `"_price_"`
  row). Found hunting `filters/inputs.py` (Sep-3)
- [x] 40. (robustness) Low. `filters/inputs.py::_normalize_range_value`: a hand-built range value it could not read (a
  list, a scalar, an object, a mapping with a key other than `start` / `end`) dropped the constraint and returned every
  row. Done as bug_hunt-0_0_15_2.md item 15 (`a54ad7c8`): it raises `ConfigurationError`
  (`tests/filters/test_inputs.py::test_range_filters_reject_python_values_without_mapping_or_input_protocol`). Found
  hunting `filters/inputs.py` (Sep-19)
- [x] 41. Medium. `filters/sets.py::FilterSet.filter_for_field` dereferenced `default.distinct` unconditionally, so a
  model field with no `FILTER_DEFAULTS` entry (`FileField`, `ImageField`, `BinaryField`) under
  `Meta.unknown_field_behavior` WARN / IGNORE raised a raw `AttributeError` at class creation instead of upstream's
  `None` skip. Fixed (`a8f31a2d`): it returns `None` early
  (`tests/filters/test_sets.py::test_filter_for_field_preserves_upstream_none_contract_for_unrecognized_field`). Found
  hunting `filters/sets.py` (Sep-3)
- [x] 42. (robustness) Low. `filters/sets.py::FilterSet._normalize_input`: a multi-entry operator bag over a declared
  filter silently kept only the last lookup. Done as bug_hunt-0_0_15_2.md item 4 (`754ed263`, `9f7ea5dd`): each lookup
  binds to its own filter and two lookups on one key both apply, replacing the Sep-19 raise
  (`tests/filters/test_sets.py::test_normalize_input_overlap_head_binds_each_lookup_to_its_own_filter`). Found hunting
  `filters/sets.py` (Sep-19)
- [x] 43. Low. `filters/sets.py::FilterSet._normalize_input`: on an overlap head a single foreign lookup bound the
  generated form key instead of the declared one, so the filter silently returned wrong rows. Done as
  bug_hunt-0_0_15_2.md item 4 (`754ed263`; item 189 re-checked it; test
  `tests/filters/test_sets.py::test_normalize_input_overlap_head_binds_each_lookup_to_its_own_filter`). Found in deep
  dive 4 (Sep-19)
- [x] 44. (robustness) Nineteen error-label reads in `filters/sets.py` (`__name__` / `__qualname__` of a hostile
  metaclass) and a `!=` against a custom `Collection` at the `get_fields` `"__all__"` check escaped raw. Already fixed
  on main: labels read through `utils/truth.py` (`73a190b6`, 41 reads) and the narrowing check is a plain `==` as
  upstream's; no `!=` against `"__all__"` remains in `filters/` or `sets_mixins.py`. No test pins the raising-`__ne__`
  shape. Declaration-time typing of hostile set class names is the open question of bug_hunt-0_0_15_2.md item 26. Found
  hunting `filters/sets.py` (Sep-19)
- [x] 45. `forms/converter.py`: no bugs in either campaign (Sep-3 ran 43 probes, Sep-19 41; the Sep-19 control that
  flipped JSON to str failed for the intended reason). Found hunting `forms/converter.py` (Sep-3, Sep-19)
- [x] 46. (robustness) `forms/inputs.py::_form_field_basis` classified each `get_form_fields` / `base_fields` value with
  a bare `isinstance`, so a value whose `__class__` read raises escaped raw instead of being listed as an invalid field
  in the typed `ConfigurationError`. Fixed (`32b66897`, test
  `tests/forms/test_inputs.py::test_basis_diagnostic_typed_for_hostile_class_value`; bug_hunt-0_0_15_2.md item 16).
  Found hunting `forms/inputs.py` (Sep-19)
- [x] 47. (robustness) Low. `forms/inputs.py::_form_field_basis` ran the identifier / keyword walk over hook-supplied
  names outside the typed error, so a `str` subclass whose `isidentifier` or `__hash__` raised escaped raw. Fixed
  (`a8f31a2d`) and still held: `utils/inputs.py::is_input_attribute_name` reads the exact `str` through base slots
  (tests `tests/utils/test_inputs.py::test_is_input_attribute_name`,
  `tests/forms/test_inputs.py::test_honest_str_subclass_basis_name_still_builds`). Found hunting `forms/inputs.py`
  (Sep-3)
- [x] 48. (robustness) Low. `forms/inputs.py`: a hook key with a raising `__repr__` detonated inside the invalid-names
  message, and `_model_column_for` let a raising `_meta.model` read or a `get_field` error other than
  `FieldDoesNotExist` escape raw instead of typed. Fixed in `a8f31a2d`, then superseded: `73a190b6` removed that
  containment family so a consumer's own exception propagates (names render through `utils/truth.py::render`, the model
  through `truth.static_attr`); item 16 classes the remaining hostile-input shapes as no-contract robustness rows. Found
  hunting `forms/inputs.py` (Sep-3)
- [x] 49. `forms/resolvers.py`: no bugs in either campaign. Sep-3 verified a lost session's candidate fix, now
  `utils/write_values.py::materialize_relation_id_container` (atom tuple rejected before iteration, container
  materialized before any visibility query; tests
  `tests/utils/test_write_values.py::test_materialize_relation_id_container_materializes_once`,
  `::test_materialize_relation_id_container_rejects_text_mapping_and_non_iterable_atoms`). Found hunting
  `forms/resolvers.py` (Sep-3, Sep-19)
- [x] 50. Medium. `forms/sets.py::_cached_build_form_input` keyed shared-basis siblings by per-mutation-class identity,
  so two mutations producing the same form basis through one shared `get_form_fields` hook (or two hooks with identical
  content) got two distinct same-named input classes and tripped the "materialized by two distinct" collision on a legal
  declaration, while a stateful hook stayed content-blind. Fixed (`a8f31a2d`): the key's fourth component is
  `forms/inputs.py::_form_basis_content_identity` (tests
  `tests/forms/test_sets.py::test_shared_hook_intermediate_base_siblings_dedupe`,
  `::test_stateful_shared_hook_requiredness_drift_is_loud`). Found hunting `forms/sets.py` (Sep-3)
- [x] 51. (robustness) Eight raw `__name__` reads in `forms/sets.py` (validation labels, hook labels, exception name,
  form class and permission entry names) raised raw for a class whose `__name__` raises. Already fixed on main
  (`73a190b6`): every read goes through `utils/truth.py::name`, a type-slot read, and only `module=__name__` remains;
  item 16 closes the rest, and item 26 (open) asks only whether a hostile class name should fail at declaration. Found
  hunting `forms/sets.py` (Sep-19)
- [x] 52. `keyset.py`: no bugs in either campaign. Sep-19 assessed one lead as a robustness row, not a defect: a
  `Meta.cursor_field` entry that is a hostile `str` subclass passes validation and detonates only at the seek `Q` at
  execution; the actor is the schema author, no wire input reaches it, and the owner would be
  `types/base.py::_validate_cursor_field`. Found hunting `keyset.py` (Sep-3, Sep-19)
- [x] 53. (robustness) Low. `list_field.py::_validate_djangotype_target` (shared by all four field factories) formatted
  and interrogated its target raw: `{target_type!r}`, `__name__` twice, `getattr(target, name, None)` (suppresses only
  `AttributeError`), and later `isclass` / `issubclass` / the registry lookup / `origin`, so a hostile target escaped
  raw instead of the typed `ConfigurationError`; the Relay validator also re-read the definition a second time. Fixed
  (`a8f31a2d`, reworked by `f9ac71bf` and `73a190b6`; bug_hunt-0_0_15_2.md item 21): the guard asks the real type
  through `utils/truth.py`, renders through `truth.render` / `truth.name`, and returns the one definition read that
  `_validate_relay_djangotype_target` consumes (tests
  `tests/test_list_field.py::test_djangolistfield_rejects_a_target_whose_class_cannot_be_trusted`,
  `::test_every_field_factory_shares_the_class_test_of_the_target_guard`). Found hunting `list_field.py` (Sep-3, Sep-19)
- [x] 54. (robustness) Low-Medium. `list_field.py::DjangoListField` forwarded `directives` to `strawberry.field`
  unvalidated: a non-iterable escaped as a raw `TypeError`, a midway-raising iterator as `ValueError`, and a bare `str`
  / `bytes` silently built element-wise garbage. Fixed (`a8f31a2d`): `utils/directives.py::validated_field_directives`
  is the shared check (tests `tests/test_list_field.py::test_djangolistfield_rejects_bare_string_directives`,
  `::test_djangolistfield_rejects_bare_bytes_directives`, `::test_djangolistfield_rejects_non_iterable_directives`).
  Found hunting `list_field.py` (Sep-3)
- [x] 55. (robustness) Hostile `__mro__` read at class creation inside `types/base.py` / `registry.py`, outside the
  list-field validator, escaping raw. Closed as no code: bug_hunt-0_0_15_2.md item 22 classes `__mro__` reads as
  no-contract robustness rows. Found hunting `list_field.py` (Sep-19)
- [x] 56. `management/commands/_imports.py`: no bugs in either campaign (Sep-3 85-row battery, Sep-19 13-probe battery
  plus a narrowed-catch control; hostile `__str__` on an `ImportError` deliberately passes through as
  operator-pointed-module behaviour). Found hunting `management/commands/_imports.py` (Sep-3, Sep-19)
- [x] 57. `management/commands/export_schema.py`: no bugs in either campaign (exported SDL byte-identical to
  `print_schema` of the live schema on stdout and file output; weakened blank-guard control reproduced the long-fixed
  whitespace bug and failed as intended). Found hunting `management/commands/export_schema.py` (Sep-3, Sep-19)
- [x] 58. Low. `management/commands/inspect_django_type.py` assumed every pk on a Relay-shaped type is suppressed to the
  interface `id: GlobalID!`, so a relation pk (`OneToOneField(primary_key=True)`, an MTI parent link) printed a
  `GlobalID! relay.Node id` row the schema never emits (it exposes the resolved relation type), and two docstrings said
  the opposite. Fixed (`a8f31a2d`): the predicate is now the shared `types/base.py::_is_suppressed_relay_pk`,
  relation-first, read by both `_build_annotations` and the command (tests
  `tests/management/test_inspect_django_type.py::test_inspect_one_to_one_pk_on_relay_type_reports_relation_row`,
  `::test_inspect_mti_parent_link_pk_on_relay_type_reports_relation_row`). Sep-19 found nothing further (a later DRY
  docstring edit re-verified as no behaviour change). Found hunting `management/commands/inspect_django_type.py` (Sep-3)
- [x] 59. `middleware/debug_toolbar.py`: no bugs in either campaign. Sep-3's one candidate (a UTF-16 / declared-charset
  corruption in `_get_payload`) was disproved: the decode and re-encode key off the same parsed charset, so the round
  trip is consistent. Found hunting `middleware/debug_toolbar.py` (Sep-3, Sep-19)
- [x] 60. `middleware/request_body.py`: no bugs in either campaign (over-limit multipart refused with 413 before any
  parse or CSRF check on both transports; fail-closed streams, exemption stamp and misordering audit all held). Found
  hunting `middleware/request_body.py` (Sep-3, Sep-19)
- [x] 61. (robustness) Low. `mutations/fields.py::DjangoMutationField` forwarded `directives` to `strawberry.field`
  unvalidated, so a bare `str` / `bytes`, a hostile iterator or a non-iterable escaped as a raw `AttributeError` /
  `ValueError` / `TypeError` at schema build or SDL render. Fixed (`a8f31a2d`):
  `utils/directives.py::validated_field_directives` is the shared check and `auth/mutations.py::_make_auth_field` uses
  it too (tests `tests/mutations/test_fields.py::test_bare_string_or_bytes_directives_raise_at_construction`,
  `::test_non_iterable_directives_raise_configuration_error`). Found hunting `mutations/fields.py` (Sep-3)
- [x] 62. (robustness) Low. `mutations/fields.py`'s target guard used a bare `isinstance`, a raw protocol probe, a raw
  own-`__dict__` read and ledger membership by `==`, so a class with a hostile `__class__`, `__dict__` or `__eq__`
  escaped raw, and a drained class equal to its redeclaration built a schema whose requests failed. Fixed (`b4d6e06a`
  binds the target by identity; `73a190b6` reads the class through `utils/truth.py`: `truth.is_type`,
  `truth.class_dict`, `truth.is_among`; bug_hunt-0_0_15_2.md item 17; tests
  `tests/mutations/test_fields.py::test_stale_target_equal_to_its_redeclaration_rejected_at_construction`,
  `::test_registered_target_with_raising_metaclass_eq_constructs`). Found hunting `mutations/fields.py` (Sep-19)
- [x] 63. (robustness) Low. `mutations/inputs.py::build_mutation_input(overrides=)` and
  `mutation_input_field_specs(excluded_attrs=)` frozenset-split a bare `str` into per-character names (a `bytes` into
  integers): an override silently did nothing, `excluded_attrs="name"` left the spec scalar, and a garbage string
  satisfied the empty-input guard so a no-editable-column model built a zero-field input instead of the fail-loud
  reject. Fixed (`a8f31a2d`): `_frozenset_of_attr_names` rejects a bare `str` / `bytes` at both sites (tests
  `tests/mutations/test_inputs.py::test_build_mutation_input_rejects_bare_string_overrides`,
  `::test_mutation_input_field_specs_rejects_bare_string_excluded_attrs`). Found hunting `mutations/inputs.py` (Sep-3)
- [x] 64. (robustness) Low-Medium. `mutations/inputs.py::build_payload_type(object_slot=)` collapsed a slot of
  `"errors"` / `"ok"` onto the duplicate namespace key and built a payload with no object field, and a non-identifier
  slot exploded later as a cryptic `SyntaxError`. Fixed (`a8f31a2d`), then made inexpressible: the parameter no longer
  exists, the slot is always `payload_object_slot(primary_type)` (`"node"` or `"result"`). Found hunting
  `mutations/inputs.py` (Sep-3)
- [x] 65. `mutations/operations.py`: no bugs in either campaign. Sep-3's two observations (a `Meta.operation` `str`
  subclass with a raising `__hash__` escaping the metaclass, and the delete `input_type_name` `KeyError`) were closed
  under `mutations/sets.py`. Found hunting `mutations/operations.py` (Sep-3, Sep-19)
- [x] 66. Medium. `mutations/permissions.py::run_permission_classes` walked a mutable validated-meta slot, so a hostile
  `has_permission` hook could rebind `permission_classes` to the empty allow-any posture (or swap `_mutation_meta`) and
  every later request was authorized: a persistent cross-request authorization bypass (trigger is developer-authored
  in-request class mutation, not client input). Fixed (`a8f31a2d`): the walk iterates `tuple(meta.permission_classes)`,
  `write_mixins.py::_ValidatedMutationMeta` is sealed after `__init__`, the metaclass makes `_mutation_meta` write-once,
  and `auth/mutations.py` mirrors both (tests
  `tests/mutations/test_permissions.py::test_permission_slot_refusal_preserves_snapshot_and_original_error`,
  `tests/auth/test_mutations.py::test_auth_permission_holder_snapshot_is_sealed`, live
  `examples/fakeshop/test_query/test_mutation_permissions_api.py::test_hook_rebinding_the_validated_permission_slot_fails_closed`).
  Found hunting `mutations/permissions.py` (Sep-3)
- [x] 67. (robustness) Seven raw `mutation_cls.__name__` / `model.__name__` reads, plus an eager `getattr(primary,
  "__name__", ...)` default that escaped even for honest primaries, in `mutations/resolvers.py` request-time messages
  (guard owner, pk-drift, write-step drift, auth owner). Already fixed on main (`73a190b6`): every label is
  `truth.name(...)` and no `__name__` read remains; bug_hunt-0_0_15_2.md item 17 closes the rest as no-contract rows,
  item 26 is the open naming question. Found hunting `mutations/resolvers.py` (Sep-19)
- [x] 68. High. `mutations/sets.py`: a `Meta.operation` that is a `str` subclass with a raising `__hash__` escaped
  `DjangoMutationMetaclass` as a raw `RuntimeError` through frozenset membership, and the same shape through
  `NON_DELETE_WRITE_OPERATIONS` shared by the form and serializer flavors. Fixed (`a8f31a2d`): the operation is read as
  its exact text before membership (`truth.text(raw_operation)` in `mutations/sets.py` and `write_mixins.py`; tests
  `tests/mutations/test_sets.py::test_django_mutation_validate_meta_reads_a_hostile_hash_operation_as_its_text`,
  `tests/test_write_mixins.py::test_require_non_delete_operation_reads_a_hostile_hash_operation_as_its_text`). Found
  hunting `mutations/sets.py` (Sep-3)
- [x] 69. Medium. `mutations/sets.py::DjangoMutation.input_type_name` on a validated `delete` raised a raw `KeyError:
  'delete'` from a direct index (unreachable in-framework). Fixed (`a8f31a2d`): `.get()` plus a typed
  `ConfigurationError` saying delete is id-only and materializes no input (test
  `tests/mutations/test_sets.py::test_django_mutation_input_type_name_delete_operation_raises_typed_reject`). Found
  hunting `mutations/sets.py` (Sep-3)
- [x] 70. High. `make_declaration_registry.register` dedupe used `declaration_cls not in store`, which dispatches each
  stored class's `__eq__`, so a consumer metaclass with a hostile `__eq__` escaped raw on a second registration. Fixed
  (`a8f31a2d`): identity scan, same semantics for honest classes; now `truth.is_among` in `write_mixins.py` (test
  `tests/test_write_mixins.py::test_make_declaration_registry_identity_dedup_hostile_eq_safe_containment`). Found
  hunting `mutations/sets.py` (Sep-3)
- [x] 71. (robustness) Low. Six raw `__name__` reads in `mutations/sets.py` (validation labels and the `<Name>Payload` /
  input naming sites) escaped raw for a registered class whose `__name__` raises. Already fixed on main (`73a190b6`):
  labels and names read through `truth.name`; bug_hunt-0_0_15_2.md item 17 closes the label rows as needing no code, and
  the publish-or-reject naming decision is the open item 26 recorded under `mutations/fields.py`. Found hunting
  `mutations/sets.py` (Sep-19)
- [x] 72. `optimizer/_context.py`: no bugs in either campaign (the documented armed-context-copied-into-a-spawned-task
  hazard is ContextVar semantics, not a defect). Found hunting `optimizer/_context.py` (Sep-3, Sep-19)
- [x] 73. (robustness) Low. `optimizer/extension.py::DjangoOptimizerExtension.__init__` validated `strictness not in
  ("off", "warn", "raise")` and formatted it with `!r`, so a hostile `str` subclass or object replaced the promised
  `ValueError` with its own raw exception. Fixed (`a8f31a2d`), extended by `f788edcf` to a `__class__` that raises or
  claims `str` (bug_hunt-0_0_15_2.md item 18): `_matched_strictness` compares through the base `str` slot after asking
  the real type, so a content-equal `str` subclass is still accepted (tests
  `tests/optimizer/test_extension.py::test_strictness_hostile_dunder_values_raise_typed_valueerror`,
  `::test_strictness_accepts_content_equal_str_subclass`). Found hunting `optimizer/extension.py` (Sep-3)
- [x] 74. Low. `optimizer/extension.py::_get_or_build_plan` LRU sweep called `popitem(last=False)` unguarded, so a
  concurrent request's sweep draining the shared cache between the length read and the pop raised a raw `KeyError` into
  the request building a plan, while every other cache mutation in the module suppresses it. Fixed (`a8f31a2d`): the
  sweep pop is wrapped in `suppress(KeyError)` (test
  `tests/optimizer/test_extension.py::test_plan_cache_eviction_survives_concurrent_drain`). Found hunting
  `optimizer/extension.py` (Sep-3)
- [x] 75. (robustness) `optimizer/extension.py::check_schema`'s warning read `type_cls.__name__` raw (a consumer
  sabotaging its own class; fails loud at build, no client path); recorded not fixed in Sep-3. Closed: extension.py no
  longer reads `__name__` anywhere. Found hunting `optimizer/extension.py` (Sep-3)
- [x] 76. Low. `optimizer/field_meta.py::FieldMeta.attname` documents the DB column name, but Django fills `attname`
  with the relation name on fields that store no column (forward `ManyToManyField`, `GenericRelation`,
  `GenericForeignKey`), so `_from_field_shape` stamped a non-column name and the walker appended it to
  `plan.only_fields` (`Book { genres { ... } }` gave `only_fields=('genres',)`; Django silently drops it from `.only()`,
  so dead plan metadata plus a portability hazard). Fixed (`a8f31a2d`): `_from_field_shape` stamps `attname` None for
  non-concrete relations (tests
  `tests/optimizer/test_field_meta.py::test_from_django_field_non_column_relations_stamp_attname_none`,
  `::test_walker_plan_never_projects_non_column_relation_names`). Sep-19 found no bugs. Found hunting
  `optimizer/field_meta.py` (Sep-3)
- [x] 77. (robustness) Low. `optimizer/hints.py::_require_prefetch` checked the value with a bare `isinstance`, so a
  `prefetch_obj` whose `__class__` raises escaped raw from both `OptimizerHint.prefetch` and direct construction. Fixed
  (`f788edcf`, bug_hunt-0_0_15_2.md item 18): the check is `truth.is_instance`, subclasses still pass (test
  `tests/optimizer/test_hints.py::TestInvalidStatesRejected::test_prefetch_obj_rejects_raising_class_read`). Found
  hunting `optimizer/hints.py` (Sep-19)
- [x] 78. (robustness) Low. `optimizer/hints.py::_require_strategy` delegated unguarded to
  `nested_fetch.resolve_strategy`, whose dispatch let a `str` subclass with raising `__eq__` / `__hash__` / `__repr__`,
  or a non-`str` with raising `__getattr__`, escape as its own raw exception; the hunt's shim in `hints.py` was removed
  once the root cause was fixed in the owner. Already fixed on main (`a8f31a2d`):
  `optimizer/nested_fetch.py::resolve_strategy` compares through the base `str` slot and renders through `truth.render`
  (hardened again by `f788edcf`; tests in `tests/optimizer/test_nested_fetch.py`). Found hunting `optimizer/hints.py`
  (Sep-3)
- [x] 79. Medium. `optimizer/join_taxonomy.py` classified a reverse hop over a multi-column `ForeignObject` as
  `windowable=True` with the relation name as the partition column, so a queryset-rooted nested connection died with
  `data=None` where the per-parent fallback returns exact rows. Done as bug_hunt-0_0_15_2.md item 1 (`fe6a6df0`): every
  relation link column derives from one reader and a multi-column reverse link is unwindowable (tests
  `tests/optimizer/test_join_taxonomy.py::test_two_column_foreign_object_reverse_is_unwindowable_and_attaches_on_every_carrier`,
  live `examples/fakeshop/test_query/test_relation_link_api.py::test_two_column_link_connection_resolves_per_parent`;
  the live fixture Sep-19 left to the maintainer now exists as the library `ForeignObject` models). Sep-3 found no bugs.
  Found hunting `optimizer/join_taxonomy.py` (Sep-19)
- [x] 80. Low. `optimizer/lateral_fetch.py::_order_columns` accepted an empty order tuple and returned `()`, so a
  hand-built `NestedConnectionRequest` with `order_by=()` rendered invalid Postgres SQL (`ROW_NUMBER() OVER (ORDER BY
  )`, `ORDER BY  LIMIT %s`) at fetch time, while the windowed body renders a valid orderless window. Fixed (`a8f31a2d`):
  an empty order returns `None` and the strategy downgrades to the windowed plan (test
  `tests/optimizer/test_lateral_fetch.py::test_order_columns_reject_an_empty_order`). Sep-19 found no bugs (Postgres
  execution of the lateral path was not exercised in that campaign). Found hunting `optimizer/lateral_fetch.py` (Sep-3)
- [x] 81. (robustness) `optimizer/nested_fetch.py::resolve_strategy` promised a typed `ConfigurationError` on a bad
  strategy but dispatched into consumer dunders at four points: `value == "auto"`, the registry `dict` lookup (raising
  `__hash__`, reflected `__eq__`), the message `repr`, and the `plan` read, so a hostile `str` subclass escaped raw.
  Fixed (`a8f31a2d`): names match by content through the base `str` slot with a linear scan of the two-key registry, and
  `hints.py::_require_strategy` lost its containment shim (tests
  `tests/optimizer/test_nested_fetch.py::test_resolve_strategy_str_subclass_matches_by_content_and_renders_by_its_repr`,
  `tests/optimizer/test_hints.py`). The later truthful-reads refactor (`73a190b6`) deliberately lets the consumer's own
  `__repr__` / `plan` exception propagate instead of being rewrapped, and pins that. Found hunting
  `optimizer/nested_fetch.py` (Sep-3)
- [x] 82. (robustness) Low. `optimizer/nested_fetch.py::resolve_strategy`: a strategy value whose `__class__` raised, or
  that claimed `str` (and a lazy proxy of a name), passed the `isinstance(value, str)` gate and escaped as a raw
  `RuntimeError` / `TypeError` instead of the typed rejection. Done as bug_hunt-0_0_15_2.md item 18 (`f788edcf`): the
  class tests ask the real type and never read `__class__` (now `truth.is_instance` / `truth.is_type`); tests
  `tests/optimizer/test_nested_fetch.py::test_resolve_strategy_non_str_lookalikes_stay_typed`,
  `test_resolve_strategy_class_test_reads_the_real_type`. Found hunting `optimizer/nested_fetch.py` (Sep-19)
- [x] 83. Low. `optimizer/nested_planner.py::_advise_composite_index` advised an index such as `(id, name)` on the
  related model for a many-to-many window, which partitions by the through table's parent key, so no database uses it.
  Done as bug_hunt-0_0_15_2.md item 3 (`269b80c0`): the advisory resolves the partition column the way
  `Window(partition_by=...)` does and stays silent when it lives off the child's table (M2M through table,
  multi-table-inheritance parent link); tests
  `tests/optimizer/test_nested_index_advisory.py::TestAdvisoryReadsThePartitionColumn::test_cross_table_partition_is_silent`
  (forward, reverse, explicit-through, self and to-field M2M; `8de57e4a` later extended it to every child-table column).
  Found hunting `optimizer/nested_planner.py` (Sep-19)
- [x] 85. `optimizer/nested_planner.py`: the Sep-3 hunt classified an uncommitted mechanical refactor
  (`ConnectionWindowBounds` replacing an anonymous 3-tuple) as behavior-preserving and found no bug; its one residual,
  the stale return annotation on `_keyset_window_slice_from_arguments`, now reads `tuple[ConnectionWindowBounds,
  KeysetSeek | None] | None`. The Sep-19 re-pass over the sliced-child refusal (`44712901`) found no bug either. Found
  hunting `optimizer/nested_planner.py` (Sep-3, Sep-19)
- [x] 86. `optimizer/plans.py`: no bugs in either campaign. Found hunting `optimizer/plans.py` (Sep-3, Sep-19)
- [x] 87. (robustness) Low. `optimizer/predicates.py::attach_exists` re-read both querysets' `.db` inside the
  alias-mismatch f-string after the guard comparison; on a hint-less queryset each read re-resolves through the router,
  so a stateful router made the message name aliases that were never the compared pair. Fixed (`a8f31a2d`): both aliases
  are snapshotted before the comparison and the message formats the snapshots; test
  `tests/optimizer/test_predicates.py::test_alias_mismatch_message_reports_the_compared_values`. The Sep-19 hunt found
  no further bug. Found hunting `optimizer/predicates.py` (Sep-3, Sep-19)
- [x] 88. Low. `optimizer/selections.py::included_field_selections` iterated its input twice (fast-path probe, then
  rebuild), so a one-shot iterable lost fields before a fragment, the fragment itself, or a whole fragment body,
  silently skipping prefetch planning. Fixed (`a8f31a2d`): non-list/tuple iterables are materialized once at entry and
  list/tuple keep the identity passthrough; test
  `tests/optimizer/test_selections.py::test_included_field_selections_materializes_one_shot_iterables`. The Sep-19 hunt
  found no further bug. Found hunting `optimizer/selections.py` (Sep-3, Sep-19)
- [x] 89. `optimizer/single_parent_fetch.py`: no bugs in either campaign. Found hunting
  `optimizer/single_parent_fetch.py` (Sep-3, Sep-19)
- [x] 90. `optimizer/walker.py`: no bugs in either campaign inside the file (plan-cache identity, FK elision,
  multi-alias routing, hostile selection shapes, absent-vs-empty settings, the sliced-child refusal at `44712901`).
  Found hunting `optimizer/walker.py` (Sep-3, Sep-19)
- [x] 91. Low. A hook returning `union()` / `intersection()` / `difference()` on a plain-list relation passed the
  list-relation child seal (`_LIST_RELATION_CHILD_POLICY`, `reject_combined=False`) and escaped as a raw
  `NotSupportedError` at plan apply or fetch-time refilter instead of the typed `ConfigurationError`; the same class on
  the default seal. Done as bug_hunt-0_0_15_2.md item 6 (`5c5e32c5`): a combined result is rebuilt as
  `Model.filter(pk__in=<combined>.order_by().values("pk"))` or fails closed with a verbose `ConfigurationError`; live
  rows in `examples/fakeshop/test_query/test_combined_visibility_api.py`. Found hunting `optimizer/walker.py` (Sep-19)
- [x] 92. Medium. `orders/base.py::RelatedOrder`: a target resolving to a non-`OrderSet` (plain class, the cross-family
  `FilterSet`, a factory returning a non-class) survived declaration, binding and expansion, then leaked a raw
  `AttributeError` from `finalize_django_types()` or silently walked the filter family through the order input builder.
  Fixed (`a8f31a2d`): the `.orderset` read seam runs `_validate_target`, a typed `ConfigurationError` naming owner,
  field and target (placeholder `None` passes, an unresolvable string still raises `ImportError`); tests
  `tests/orders/test_base.py::test_related_order_rejects_plain_class_target_with_typed_error`,
  `test_related_order_rejects_filterset_target`, `test_related_order_rejects_factory_returning_non_class`. Found hunting
  `orders/base.py` (Sep-3)
- [x] 93. (robustness) Low. `orders/base.py::RelatedOrder._validate_target` and `bind_orderset`: an owner whose
  `__class__` read raised, with a non-family target, escaped the typed rejection as a raw `RuntimeError` from an
  unguarded `isinstance(owner, type)`. Already fixed on main (`73a190b6`): the owner and target are read through
  `utils/truth.py` (`truth.is_type`, `truth.is_subclass`, `truth.qualname`), which never reads `__class__`.
  `tests/orders/test_base.py` has no row for the raising-`__class__` owner itself; `bug_hunt-0_0_15_2.md` item 20 closes
  the robustness class. Found hunting `orders/base.py` (Sep-19)
- [x] 94. `orders/factories.py`: no bugs in either campaign. The Sep-19 lead that `Meta.exclude` is accepted but ignored
  at the factory was judged correct deferral (no caller reads it; exclude-distinct metas fail loud). Found hunting
  `orders/factories.py` (Sep-3, Sep-19)
- [x] 95. (robustness) Docs gap. `orders/inputs.py`: `OrderSet` `Meta.fields = "__all__"` expands to every column-backed
  field independent of the owning type's field surface, so a client can infer a hidden column's relative values from row
  order; the glossary warned only about related branches, not the type's own hidden columns. Fixed: the `OrderSet` entry
  in `docs/GLOSSARY.md` carries a "Hidden-column warning" (rendered from the glossary DB, `7426e7e7`). No code change.
  Found hunting `orders/inputs.py` (Sep-3)
- [x] 96. (robustness) Low. `orders/inputs.py` leaf-direction rejection interpolated `orderset_cls.__qualname__` raw, so
  a raising `__qualname__` or a `str` subclass that cannot format escaped instead of the typed rejection. Already fixed
  on main (`73a190b6`): the label reads `truth.qualname(orderset_cls)` (`bug_hunt-0_0_15_2.md` item 26 stays open only
  as the separate question of rejecting such names at declaration); no `tests/orders/test_inputs.py` row names a raising
  `__qualname__`. Found hunting `orders/inputs.py` (Sep-19)
- [x] 97. Medium. `orders/sets.py::OrderSet._expand_meta_fields`: the no-model arm skipped entry validation
  (`fields=[None]`, `[b"title"]` expanded to junk keys; an unhashable entry raised raw `TypeError`), a hostile iterable
  raised raw mid-iteration, and a one-shot iterator `Meta.fields` expanded once then silently rebuilt to an empty or
  partial field set on every later rebuild. Fixed (`a8f31a2d`): a re-readable-container gate
  (`require_re_readable_field_declaration`) rejects one-shot iterators loudly and an unconditional entry-type gate
  (`require_field_name`) runs before the path walk; tests
  `tests/orders/test_sets.py::test_orderset_expand_meta_fields_rejects_one_shot_iterator_fields` and the shape table
  around it. Found hunting `orders/sets.py` (Sep-3)
- [x] 98. (robustness) Low. `orders/sets.py`: eleven sites (the normalization ledger and purity-check `__name__` reads,
  six `__qualname__` labels, and `_expand_meta_fields` `== "__all__"`) raised raw for a hostile class name or a
  `Meta.fields` with a hostile `__eq__`. Labels already fixed on main (`73a190b6`): every label reads `truth.name` /
  `truth.qualname`. The hostile `__eq__` arm is closed by bug_hunt-0_0_15_2.md item 20 as a robustness row with no
  contract row (django-filter reads it the same way); item 26 holds the open declaration-time question. Found hunting
  `orders/sets.py` (Sep-19)
- [x] 99. `permissions.py`: no bugs in either campaign. The Sep-3 "Fixed Low" (sliced and combined cascade targets
  escaping raw) was regraded: `_validated_target_subquery` already raised `ConfigurationError` at HEAD and
  `tests/test_permissions.py` already pinned it, so the move onto `utils/querysets.py::_CASCADE_SEAL_POLICY` was
  behavior-preserving. Found hunting `permissions.py` (Sep-3, Sep-19)
- [x] 100. `registry.py`: no bugs in either campaign. Found hunting `registry.py` (Sep-3, Sep-19)
- [x] 101. `relay.py`: no bugs in either campaign. Sep-3 leads: consumer `resolve_node(s)` override shapes (not client
  input) and the `nodes(ids:)` width bound (now `ResourcePolicy.max_node_ids`) need no code; a non-unique `NodeID`
  column is documented at `types/relay.py`; the Sep-19 hostile-`__mro__` Node lead was judged no standing (loud in both
  eras). Found hunting `relay.py` (Sep-3, Sep-19)
- [x] 103. Medium. `resource_policy.py::_is_valid_deadline`: a deployment-supplied numeric subclass whose comparison
  dunder raised leaked a raw `RuntimeError` out of `ResourcePolicy.__post_init__`, and a huge int overflowed
  `math.isfinite`. Fixed (`a8f31a2d`, later tightened to exact built-in numbers by `fb6ccdb6`): a non-built-in number is
  the typed `ConfigurationError` and an overflow answers False; test
  `tests/test_resource_policy.py::test_a_hostile_numeric_deadline_subclass_is_typed_rejected`. The Sep-19 re-pass at the
  canonical-copy bytes found no further bug. Found hunting `resource_policy.py` (Sep-3, Sep-19)
- [x] 104. Medium. `resource_policy.py::check_deadline`: a hostile numeric stashed under the consumer-owned
  `DST_RESOURCE_DEADLINE` key leaked raw comparison errors out of a collection resolver. Fixed (`a8f31a2d`): the
  deadline answer is judged on the built-in domain and anything not placeable on the clock fails closed with the typed
  `ResourceLimitExceeded`. Found hunting `resource_policy.py` (Sep-3)
- [x] 105. Medium. `resource_policy.py::bounded_rows`: a mapping-shaped resolver result raised raw `KeyError` from the
  slice where slices hash. Fixed (`a8f31a2d`): only an exact list, tuple, str, bytes, bytearray or `QuerySet` is sliced
  and every other shape is counted into a fresh list; tests
  `tests/test_resource_policy.py::test_bounded_rows_bounds_a_mapping_shaped_result`,
  `test_bounded_rows_bounds_a_hostile_mapping_subclass`. Found hunting `resource_policy.py` (Sep-3)
- [x] 106. Medium. `resource_policy.py::bounded_rows_async`: a hostile note surface on the source error (non-iterable or
  raising `__notes__`) let the diagnostic-attachment `TypeError` replace the source error inside the cleanup `finally`.
  Fixed (`a8f31a2d`): the note write is contained; test
  `tests/test_resource_policy.py::test_bounded_rows_async_hostile_notes_property_getter_does_not_mask_the_source`. Found
  hunting `resource_policy.py` (Sep-3)
- [x] 107. Medium. `utils/policies.py::resolve_policy`: a validated policy instance behind the `RESOURCE_POLICY` setting
  slot was rejected with a self-contradictory typed message (it named the received type while demanding one). Fixed
  (`a8f31a2d`): the setting slot and the explicit argument are one ladder, so a validated instance from either passes;
  test `tests/test_resource_policy.py::test_an_instance_through_the_setting_slot_resolves_on_the_same_terms`. Found
  hunting `resource_policy.py` (Sep-3)
- [x] 108. Low. `rest_framework/hook_context.py` boundary, `rest_framework/resolvers.py::_hook_mapping`: the typed
  boundary guarded only `dict(value)`, so a hook mapping with non-string keys escaped as a raw `TypeError: keywords must
  be strings` at `serializer_class(**kwargs)` / `serializer.save(**save_kwargs)` for both the kwargs and the save-kwargs
  hooks. Fixed (`a8f31a2d`): the materialized keys are gated and a non-string key is a `ConfigurationError` naming the
  hook; test `tests/rest_framework/test_resolvers.py::test_hook_mapping_rejects_non_string_keys`. The Sep-19 hunt of
  `hook_context.py` itself found no bug. Found hunting `rest_framework/hook_context.py` (Sep-3, Sep-19)
- [x] 109. Medium. `rest_framework/inputs.py` via `utils/inputs.py::normalize_field_name_sequence`: a `set` /
  `frozenset` serializer `Meta.fields` / `Meta.exclude` iterated in hash order and `serializer_input_type_name` folds
  that walk order into the generated input class name, so one declaration produced different type names and SDL field
  orders per `PYTHONHASHSEED`. Fixed (`a8f31a2d`): the shared shape gate rejects an unordered set for an ordered key
  with a typed `ConfigurationError`; test
  `tests/utils/test_inputs.py::test_normalize_field_name_sequence_rejects_unordered_sets_for_an_ordered_key`. The Sep-19
  hunt found no bug in the file; its two leads went to `rest_framework/sets.py`. Found hunting
  `rest_framework/inputs.py` (Sep-3, Sep-19)
- [x] 110. Medium. `rest_framework/resolvers.py` / `rest_framework/inputs.py::resolve_injected_field_specs`: an injected
  serializer-only `ChoiceField` / `MultipleChoiceField` resolved its schema-time spec under the create provisional while
  the runtime agreement guard re-derived under the update provisional, so every call of a valid `Meta.injected_fields`
  update raised a spurious "align the runtime serializer" `ConfigurationError`. Fixed (`a8f31a2d`):
  `resolve_injected_field_specs` takes a required keyword-only `operation_kind` and `SerializerMutation.build_input`
  threads it; test
  `tests/rest_framework/test_resolvers.py::test_injected_serializer_choice_field_agrees_on_update_operation`. Found
  hunting `rest_framework/resolvers.py` (Sep-3)
- [x] 111. (robustness) Low. `rest_framework/resolvers.py` hook boundaries with typed contracts: a hook mapping or
  `Field` / `Mapping` value whose `__class__` raised, a hostile freeze leaf, a hostile `write_alias` context or
  `__repr__`, and a hostile-`__repr__` key escaped raw. Done as bug_hunt-0_0_15_2.md item 19 (`5cbe15de`): the class
  tests are guarded `isinstance` (proxies still pass), the freeze, alias and saved result ask the real type, renders use
  `truth.render`. Found hunting `rest_framework/resolvers.py` (Sep-19)
- [x] 112. (robustness) Low. `rest_framework/resolvers.py`: about 53 runtime labels read `mutation_cls.__name__` /
  `type(serializer).__name__` raw, so a registered class with a raising `__name__` escaped from inside already-typed
  paths. Already fixed on main (`73a190b6`): labels read `truth.name` (no raw `__name__` read remains in
  `rest_framework/`); `bug_hunt-0_0_15_2.md` item 19 calls the labels item 26's question, which is still open as a
  declaration-time rejection decision. Found hunting `rest_framework/resolvers.py` (Sep-19)
- [x] 113. Medium. `rest_framework/serializer_converter.py::resolve_serializer_field`: the relation cardinality guard
  (`many_to_many or one_to_many`) and the emitted kind (`many_to_many` only) disagreed, so a
  `PrimaryKeyRelatedField(many=True)` over a reverse-FK or `GenericRelation` column compiled to a single-id input while
  the runtime validated a list, killing every call. Fixed (`a8f31a2d`): the emitted kind follows the serializer field's
  cardinality (`RELATION_MULTI`); tests
  `tests/rest_framework/test_converter.py::test_many_pk_related_field_over_generic_relation_column_emits_multi` and the
  reverse-FK / reverse-O2O rows. Found hunting `rest_framework/serializer_converter.py` (Sep-3)
- [x] 114. Low. `rest_framework/serializer_converter.py`: a `ListField` whose child had `allow_null=True` lost the
  nullable element, and a `ChoiceField(allow_blank=True)` lost its `""` value (the hunt's fix swapped the enum for
  `String` and asked for sign-off). Done as bug_hunt-0_0_15_2.md item 5 (`a5dc6ea3`) with a better design: choice enums
  carry a `BLANK` member and list elements follow the child's `allow_null`; the published-schema decision is moot and
  the blocked live rows now exist (`ShelfMetadataSerializer` `tags` / `priority` / `labels` / `flags` in
  `examples/fakeshop/apps/library/serializers.py`, live rows in `examples/fakeshop/test_query/test_library_api.py`);
  tests
  `tests/rest_framework/test_converter.py::test_serializer_only_multiple_choicefield_allow_blank_enum_has_blank_member`,
  `test_listfield_choice_child_allow_null_makes_the_enum_element_nullable`. Found hunting
  `rest_framework/serializer_converter.py` (Sep-19)
- [x] 115. (robustness) Low. `rest_framework/serializer_converter.py`: four typed raises interpolated a hostile
  `__name__` raw. Already fixed on main (`73a190b6`): the file reads names through `truth` (no raw `__name__` read of a
  field or serializer class remains). Found hunting `rest_framework/serializer_converter.py` (Sep-19)
- [x] 116. Medium. `rest_framework/sets.py` Meta validators: `_validate_schema_field_map` let a hostile `__ne__`
  bound-name value and a `str` subclass key with hostile `__hash__` escape raw; `_validate_serializer_nested_fields`
  used a bare `.items()`, crashed on wrong-arity entries, unhashable keys and hostile-`__repr__` keys while assembling
  its own error, and `Meta.nested_fields = {}` spuriously demanded a `create()` / `update()` override. Fixed
  (`a8f31a2d`): keys read as text (`truth.plain_str`) or refused, the map copied by `dict_of`, an empty declaration
  demands no override; tests `tests/rest_framework/test_sets.py` and
  `::test_validate_nested_fields_empty_mapping_requires_no_write_override`. Found hunting `rest_framework/sets.py`
  (Sep-3)
- [x] 117. (robustness) Low. `rest_framework/sets.py`: six `__name__` sites and two class tests escaped raw for a
  hostile class, and a kept serializer field named by a non-identifier or keyword passed class creation then raised an
  unnamed `SyntaxError` at finalize. Done as bug_hunt-0_0_15_2.md item 19 (`5cbe15de`): kept input names are checked at
  class creation (root and nested), tests are guarded `isinstance`, labels read through `truth`; the rejection of
  non-identifier keys stands as a recorded behavior change. Found hunting `rest_framework/sets.py` (Sep-19)
- [x] 118. `routers.py`: the Sep-3 hunt found no bug and flagged the `strawberry-graphql>=0.316.0` literal in
  `_STRAWBERRY_CHANNELS_BROKEN_HINT` as the same drift hazard `CHANNELS_FLOOR` removed; the hint now interpolates
  `STRAWBERRY_FLOOR` (`a8f31a2d`). Found hunting `routers.py` (Sep-3)
- [x] 119. (robustness) Low. `routers.py::_factory_application`: a factory return whose `__class__` raised, or hostile
  consumer-injection interrogations (`callable`, coroutine test), escaped raw against spec-046 Decision 11. Done as
  bug_hunt-0_0_15_2.md item 21 (`f9ac71bf`): the coroutine test is a guarded `isinstance` (a lazy-proxied coroutine is
  still closed) and the interrogations ask the real type; `tests/test_routers.py` carries the hostile-class doubles.
  Found hunting `routers.py` (Sep-19)
- [x] 120. (robustness) Low. `scalars.py::strawberry_config`: the containment guard covered only
  `dict(extra_scalar_map)`, so a hostile key's `__eq__` (reached on a hash collision in the collision check and the
  merge) escaped as a raw `RuntimeError` instead of the documented `ValueError`. Fixed (`a8f31a2d`) with an extended
  guard, then superseded by design in `73a190b6`: containment of a consumer's own dunder exceptions was retired
  package-wide, so the mapping's and keys' own exception now propagates; test
  `tests/test_scalars.py::test_strawberry_config_hostile_key_eq_error_propagates`. The Sep-19 hunt found no bug. Found
  hunting `scalars.py` (Sep-3, Sep-19)
- [x] 121. Medium. `schema.py::DjangoMutationExecutionContext._rollback_for_new_errors` ran unguarded between the atomic
  enter and exit on both execution paths, so a raising `errors` container or `__len__` skipped `atomic.__exit__` and
  left the transaction open (async: the alias lock released over it). Fixed (`a8f31a2d`): an unreadable container marks
  `set_rollback(True)`, re-raises, and both callers exit the atomic in a `finally`; tests
  `tests/test_schema.py::test_sync_window_hostile_error_container_rolls_back_and_leaks_no_transaction` and the async
  twin. Found hunting `schema.py` (Sep-3)
- [x] 122. (robustness) `DjangoSchema(...)` construction escaped a raw `RuntimeError` for a hostile policy value (an
  unguarded `isinstance` in `resource_policy.py::_require_positive_int`, `_is_valid_deadline` and
  `error_policy.py::ErrorPolicy.__post_init__`) through both the explicit argument and the setting slot. Already fixed
  on main: every type test is exact (`type(value) is not int`; `246d1dad`, `fb6ccdb6`, `9350eb8d` for `ErrorPolicy`), so
  a subclass is the typed `ConfigurationError` and no consumer dunder runs; tests
  `tests/test_resource_policy.py::test_a_hostile_int_subclass_narrowing_a_bound_is_typed_rejected`,
  `test_a_policy_argument_whose_class_read_raises_is_rejected`. Found hunting `schema.py` (Sep-3)
- [x] 123. High. `schema.py::_execute_mutation_field_async`: cancelling an async mutation during the window-enter left
  the boundary thread finishing `atomic.__enter__` while the task abandoned the bare await, so the alias lock released
  over an open transaction on the shared worker connection and later mutations nested inside it (success payloads for
  writes that never commit). Done as bug_hunt-0_0_15_2.md item 194 (`1b6a09b1`), replacing the hunt's shield-handoff
  with a better design: each async window runs on a private single-thread executor and its own connection, and the final
  transition is driven to completion across repeated cancellation; tests in `tests/mutations/test_write_transaction.py`
  and `tests/test_schema.py`. Found in scenario txn and hunting `schema.py` (Sep-19)
- [x] 124. `schema.py`: the Sep-19 stale re-passes over the canonical-copy enforcement record (`9350eb8d`) and the async
  handoff delta found no further bug. Found hunting `schema.py` (Sep-19)
- [x] 125. Low. `sets_mixins.py::RelatedSetTargetMixin` had no family hook for the resolved-target type gate, so a
  future set family could lose the gate by writing its property getter as a bare `_resolved_target()` read (lead handed
  over from the `filters/base.py` hunt). `_validate_target` is now the family gate, fired at the one shared seam after
  the re-store on every resolved read; the base raises `NotImplementedError` so a hookless subclass fails loud, and
  `RelatedFilter` / `RelatedOrder` carry the former inline gates verbatim. Fixed (`a8f31a2d`, tests
  `tests/test_sets_mixins.py::test_related_set_target_mixin_hook_is_abstract_without_a_family_validator`,
  `test_both_families_supply_their_own_target_validator`). Found hunting `sets_mixins.py` (Sep-3)
- [x] 126. (robustness) A hostile owner or declaration reached `sets_mixins.py` raw:
  `require_re_readable_field_declaration` let a raising-`__class__` `Meta.fields` generator escape, `resolve_lazy_class`
  ran a raising `__bool__` on `bound_class`, and the class labels interpolated `__qualname__` unguarded (nine sites
  across `sets_mixins.py`, `filters/base.py`, `orders/base.py`). Done as bug_hunt-0_0_15_2.md items 20 and 23
  (`f9ac71bf`); since `73a190b6` `resolve_lazy_class` asks `truth.is_type(bound_class)` and reads the owner module
  through `utils/truth.py`, so no consumer dunder runs
  (`tests/test_sets_mixins.py::test_resolve_lazy_class_owner_scope_matrix`). Found hunting `sets_mixins.py` (Sep-19)
- [x] 127. (robustness) `sets_mixins.py::resolve_lazy_class` attempt 2 interpolated a hostile `bound_class.__module__`,
  so a raw `RuntimeError` replaced the attempt-2 `ImportError`. Closed as not a bug: bug_hunt-0_0_15_2.md item 27 (no
  contract row; the module read now goes through `truth.module`). Found hunting `sets_mixins.py` (Sep-19)
- [x] 128. (lint) `sets_mixins.py::should_cache_expansion` carried one misaligned docstring line. Already fixed on main:
  the docstring reads aligned (landing commit not identified). Found hunting `sets_mixins.py` (Sep-19)
- [x] 129. `testing/_wrap.py`: no bugs in either campaign. `safe_wrap_connection_method`'s decline and unwrap protocols
  are disjoint and share one predicate, and every hostile-shape exception is propagation matching its developer-facing
  contract. Found hunting `testing/_wrap.py` (Sep-3, Sep-19)
- [x] 130. Low. `testing/client.py::_assert_file_placeholders` accepted an empty dotted segment in a `files=` path
  (`files={"": ...}`, `"data."`), emitting the spec-invalid map `{"": ["variables."]}` that the guard promises never to
  emit; the server answered an opaque 400 naming no path. The walk now rejects an empty segment. Fixed (`a8f31a2d`, test
  `tests/testing/test_client.py::test_files_placeholder_empty_segment_raises_instead_of_emitting`). Found hunting
  `testing/client.py` (Sep-3)
- [x] 131. Low. `testing/client.py::_assert_file_placeholders` rejected a tuple of placeholders ("cannot descend into
  '0'") although `json.dumps` writes a tuple as a JSON array. The walker now treats list and tuple as the array family.
  Fixed (`a8f31a2d`, test `tests/testing/test_client.py::test_files_placeholder_tuple_arrays_walk_and_map_like_lists`).
  Found hunting `testing/client.py` (Sep-3)
- [x] 132. Low. `testing/client.py::_assert_file_placeholders`: a list or tuple container whose `__len__` raises escaped
  the walker as a raw `RuntimeError`. Sep-3 contained it as an `AssertionError`; `73a190b6` reversed that on purpose
  (the container's own exception propagates) and pins it with
  `tests/testing/test_client.py::test_files_placeholder_hostile_len_container_propagates`. Closed as not a bug: a
  consumer container's own behaviour. The Sep-19 re-hunt found nothing further. Found hunting `testing/client.py`
  (Sep-3, Sep-19)
- [x] 133. `testing/relay.py`: no bugs in either campaign. The identity triple-check repels definition laundering, a
  hostile id object's `__str__` propagates by design, and node-id round trips match the wire. Found hunting
  `testing/relay.py` (Sep-3, Sep-19)
- [x] 134. Medium. `types/base.py::DjangoType.__init_subclass__`: under `from __future__ import annotations` a `field:
  auto` annotation arrives as the string "auto" and the `StrawberryAuto` isinstance test missed it, so nothing was
  synthesized, a relation `items: auto` registered no `PendingRelation`, and the unselected-auto `ConfigurationError`
  was bypassed. `_is_auto_annotation` now accepts the instance and the string spellings ("auto", "strawberry.auto").
  Fixed (`a8f31a2d`, tests `tests/types/test_base.py::test_pep563_auto_annotation_synthesizes_model_inferred_type`,
  `test_pep563_dotted_auto_annotation_synthesizes_model_inferred_type`). Aliased spellings (`import strawberry as sb`)
  stay a design call, bug_hunt-0_0_15_2.md item 411. Found hunting `types/base.py` (Sep-3)
- [x] 135. Low. `types/base.py`: a metaclass can inject non-string keys into the class namespace, and mixed-type
  auto-name sets then hit `sorted({1, "zz"})` and escaped `__init_subclass__` as a raw `TypeError`. The string-keys
  contract is now checked once at the collection boundary. Fixed (`a8f31a2d`, test
  `tests/types/test_base.py::test_non_string_annotation_keys_raise_configuration_error`). Found hunting `types/base.py`
  (Sep-3)
- [x] 136. Low. `types/base.py::_validate_meta`: `getattr(meta, key, default)` swallows only `AttributeError`, so a
  hostile `Meta` metaclass `__getattr__` leaked raw. Every `Meta` read now goes through `_meta_attr`, which reads the
  real MRO namespaces (`truth.static_attr`) so no metaclass hook runs. Fixed (`a8f31a2d`). Found hunting `types/base.py`
  (Sep-3)
- [x] 137. (robustness) `types/base.py` collection seam: a `Meta` value or entry whose `__class__` raised or lied
  (`model`, `name`, `primary`, `connection`, `cursor_field`, `relation_shapes`, `interfaces`, `fields` / `exclude`,
  `optimizer_hints`), a non-string annotation key whose `__repr__` raised, and a raising-named `interfaces` value
  escaped raw (about 20 gates). Done as bug_hunt-0_0_15_2.md item 22 (`f9ac71bf`); since `73a190b6` identity facts are
  read through `utils/truth.py` and `scripts/check_truthful_reads.py` enforces it, so none of these needs a handler
  (`tests/types/test_base.py::test_non_string_annotation_key_is_rejected_whatever_its_class_or_repr`). Found hunting
  `types/base.py` (Sep-19)
- [x] 138. (robustness) `types/base.py::_detect_custom_get_queryset` read `cls.__mro__` outside its guard, so a
  raising-`__mro__` metaclass broke class creation. The function is gone: `__init_subclass__` asks `truth.overrides(cls,
  DjangoType, "get_queryset")` (`02c575ee`, `73a190b6`), which reads the real MRO
  (`tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_abstract_base_without_meta`). Found hunting
  `types/base.py` (Sep-19)
- [x] 139. (lint) Four hunt-added `except BaseException` arms in `types/base.py` were reached by no test and blocked
  `fail_under = 100` (review 5c), plus a false "`bool` subclass" comment and two stray docstring spaces. Closed: main
  has no `except BaseException` in `types/base.py` (the package-wide policy forbids one outside cleanup-and-re-raise)
  and the comment is gone. Found in review 5c (Sep-19)
- [x] 140. (robustness) `types/converters.py`: a field or column whose `__class__` raised or lied escaped raw at five
  declaration seams (`ArrayField` dispatch, `base_field` fetch, nested-array check, `HStoreField` dispatch, enum entry
  and grouped-choices prechecks); the Sep-3 hunt found no bug. Done as bug_hunt-0_0_15_2.md item 22 / 23 (`73a190b6`):
  dispatch now reads `truth.is_instance`, `truth.kind` and `truth.mro_entry`, so a lying class changes nothing
  (`tests/types/test_converters.py::test_scalar_for_field_label_runs_a_hostile_field_name_str` pins the one
  consumer-code read left, and propagation). No per-file liar test survives; `tests/utils/test_truth.py` and the
  truthful-reads gate carry it. Found hunting `types/converters.py` (Sep-19)
- [x] 141. (robustness) `types/definition.py`: a liar `Meta.name` / field name / pk name / id attribute escaped raw at
  four seams (`graphql_type_name`, `related_target_for`, `_normalize_pk_name`, `_resolves_id_off_pk`); the Sep-3 hunt
  found no bug. Done as bug_hunt-0_0_15_2.md item 22 (`f9ac71bf`, then `73a190b6`): names and pk names are read through
  `utils/truth.py`
  (`tests/types/test_definition_relations.py::test_graphql_type_name_reads_the_origin_name_past_a_hostile_metaclass`,
  `test_custom_id_detection_reads_hostile_class_metadata_truthfully`). Found hunting `types/definition.py` (Sep-19)
- [x] 142. Low. `types/finalizer.py::_bind_set_owner_common`: an `OrderSet.Meta.model` given as the Django lazy-ref
  string (`"library.Genre"`) reached `issubclass(definition.model, set_model)` and escaped `finalize_django_types()` as
  a raw `TypeError`. A non-class model now raises the family model-mismatch `ConfigurationError`, rendering the declared
  value. Fixed (`a8f31a2d`, test
  `tests/types/test_finalizer.py::test_orderset_non_class_meta_model_is_typed_at_finalize`). Found hunting
  `types/finalizer.py` (Sep-3)
- [x] 143. (robustness) `types/finalizer.py::_field_surface_names` read a liar `__class__` attribute and the inherited
  surface (`type_cls.__mro__`, each base's `__strawberry_definition__`) raw, so a hostile class escaped as a raw
  `RuntimeError`; the relay seams' `__mro__` pre-scans (`types/relay.py` `apply_interfaces`) behave the same. Done as
  bug_hunt-0_0_15_2.md item 22 and item 27 (`73a190b6`): the surface is built from `truth.mro` / `truth.static_attr` /
  `truth.class_dict`, and the relay-seam rows need no code (no contract row). Found hunting `types/finalizer.py`
  (Sep-19)
- [x] 145. `types/relations.py`: no bugs in either campaign. `discard_pending` is strictly identity-based, sentinel
  annotation keys match Django's field names, and failure keeps the pending records. Found hunting `types/relations.py`
  (Sep-3, Sep-19)
- [x] 146. A `DjangoType` with two `relay.NodeID[...]` annotations silently stamped `"pk"`, so the schema emitted
  pk-based GlobalIDs (plain Strawberry raises `NodeIDAnnotationError`; strawberry-django swallows it to `"pk"`, and
  Sep-3 left it as upstream parity). `types/relay.py::_stamp_relay_id_attr` now raises a `ConfigurationError` at
  finalize. Fixed (`ca30de22`, test
  `tests/types/test_relay_interfaces.py::test_two_node_id_annotations_are_refused_not_read_as_pk`). Found hunting
  `types/relay.py` (Sep-3)
- [x] 147. A `relay.NodeID` over an attribute that is no model column stamps literally and fails raw at `resolve_id`
  (`AttributeError`) or refetch (`FieldError`); Sep-3 recorded it as upstream parity and a possible finalize-time
  concreteness gate. Closed as not a bug: a NodeID over a `get_queryset` annotation is a supported shape
  (`relay.py::_node_id_slot` passes the raw literal on), and the write-side question is bug_hunt-0_0_15_2.md item 321,
  still open. Found hunting `types/relay.py` (Sep-3)
- [x] 148. `types/relay.py`: no further bugs in the Sep-19 re-hunt. Hostile-`__mro__` reads at the relay seams and the
  raw `__str__` of a hostile id object are robustness rows, closed by bug_hunt-0_0_15_2.md items 27 and 168. Found
  hunting `types/relay.py` (Sep-19)
- [x] 149. Low. `types/resolvers.py::_make_relation_resolver`: the forward FK / OneToOne resolver leaked the
  `DoesNotExist` family (a dangling FK, an unsaved instance's unset non-null FK) at all four read sites (sync / async,
  fast / planned), where the reverse one-to-one branch already contained it to `None`. Every read site now catches the
  target's `DoesNotExist` (`_absence_catch_spec`); a non-nullable wire field still surfaces the `None` through
  graphql-core. Fixed (`a8f31a2d`, tests
  `tests/types/test_resolvers.py::test_forward_resolver_contains_unsaved_instance_does_not_exist`,
  `test_forward_resolver_nullable_dangling_fk_resolves_to_none`). Found hunting `types/resolvers.py` (Sep-3)
- [x] 150. Low. `types/resolvers.py` reverse one-to-one: Sep-3 widened the catch so a plain `AttributeError` from a
  hostile descriptor also became `None`. Closed as not a bug: main catches the target's `DoesNotExist` only, so a
  consumer's own `AttributeError` keeps raising (`test_reverse_one_to_one_propagates_plain_attribute_error`). Found
  hunting `types/resolvers.py` (Sep-3)
- [x] 151. Low. Nested forward FK / OneToOne resolvers (and the other relation resolvers) never called `check_deadline`
  before touching the database. Done as bug_hunt-0_0_15_2.md item 12 (`8d4f66bd`): every package seam that reaches the
  database checks the request deadline first; live rows in `examples/fakeshop/test_query/test_relation_deadline_api.py`.
  Found in deep dive 3 (Sep-19)
- [x] 152. `utils/canonical.py`: no bugs. `base_container_values` and `canonical_sort_key` read base slots exactly and
  hostile reprs / huge ints are safe; a liar `__class__` fails closed through both consumers together, a robustness row.
  Sep-3 had no item of its own (the file arrived with the `a8f31a2d` hardening set and was verified through its
  `utils/inputs.py` item). Found hunting `utils/canonical.py` (Sep-19)
- [x] 153. Low. `utils/connections.py`: the nested-window planner read cursor presence by `is_supplied` (so `before: ""`
  counted as present) while the offset engine reads `if before:`, so `last: N, before: ""` planned a forward window
  while the engine served the backward tail. Cursor presence is now `bool(before)` / `bool(after)` with a parity
  comment. Already fixed on main (`193f9946`; bug_hunt-0_0_15_2.md item 9; live test
  `examples/fakeshop/test_query/test_library_api.py::test_genre_books_connection_last_with_empty_cursor_is_the_planned_tail`).
  The Sep-3 hunt found no bug here. Found hunting `utils/connections.py` (Sep-19)
- [x] 154. `utils/context.py`: no bugs in either campaign. The `MISSING` sentinel and `restored_context_keys` extraction
  preserve the old round trip including failure paths, and the permanent pins exist
  (`tests/utils/test_context.py::test_restored_context_keys_round_trips_absent_present_and_none`). Found hunting
  `utils/context.py` (Sep-3, Sep-19)
- [x] 155. Low. `utils/converters.py::convert_with_mro` read the field class's MRO through `type.__getattribute__`,
  which still honours a data descriptor on the metaclass, so a raising `__mro__` property escaped as a raw
  `RuntimeError` and a lying one resolved the wrong registry entry. The walk now reads the real MRO from the
  interpreter. Fixed (`a8f31a2d`; now `utils/truth.py::mro_entry`, `cac08a48`; tests
  `tests/utils/test_converters.py::test_mro_walk_bypasses_a_hostile_metaclass_mro_property`,
  `test_mro_walk_ignores_a_fake_mro_claiming_a_registered_class`). Found hunting `utils/converters.py` (Sep-3)
- [x] 156. Low. `utils/converters.py::convert_with_mro` iterated the live serializer registry, so a
  `register_serializer_field_converter` call on another thread during a schema build raised "dictionary changed size
  during iteration". The scan now copies the registry once. Fixed (`a8f31a2d`; now `truth.mro_entry`'s one
  `dict(mapping)` copy; test
  `tests/utils/test_converters.py::test_registry_walk_scans_a_snapshot_not_a_live_items_view`). The Sep-19 re-hunt found
  no further bug. Found hunting `utils/converters.py` (Sep-3, Sep-19)
- [x] 157. (robustness) Low. `utils/directives.py::validated_field_directives`: a raising-`__class__` value escaped the
  char-wise text-atom `isinstance` raw because it sat before the `try`. Done as bug_hunt-0_0_15_2.md items 22 and 23
  (`f9ac71bf`, `73a190b6`): the atom is judged by its real class (`is_text_atom`), never a `__class__` read
  (`tests/utils/test_directives.py::test_value_claiming_text_through_its_class_is_judged_by_its_real_class`). Found
  hunting `utils/directives.py` (Sep-19)
- [x] 158. Decision request 5c: `utils/directives.py` documented that `BaseException` is deliberately not caught while
  hunt arms elsewhere swallowed `KeyboardInterrupt` / `SystemExit` into typed errors; one policy, or narrow the
  hostile-value arms to `Exception`? Decided in code: the module docstring states one package-wide policy (control
  signals always propagate; no handler catches `BaseException` except to clean up and re-raise),
  `scripts/check_truthful_reads.py` TR002 enforces it, and 11 re-raising sites remain (`73a190b6`). bug_hunt-0_0_15_2.md
  item 94 still reads open and is stale. Found in review 5c (Sep-19)
- [x] 159. (robustness) Low. `utils/errors.py::validation_error_to_field_errors`: a raising-`__class__` value escaped
  the per-field atom interrogation raw. Done as bug_hunt-0_0_15_2.md item 23 (`f9ac71bf`); `73a190b6` rewrote the mapper
  to `require` / `require_instance` / `truth.text` with no atom interrogation left (a planted leaf or map is the typed
  refusal, `tests/utils/test_errors.py::test_validation_error_leaves_must_be_validation_errors`). The Sep-3 hunt found
  no bug in the error-envelope candidate set. Found hunting `utils/errors.py` (Sep-19)
- [x] 160. `utils/execution_mode.py`: no bugs. The mode is bound per operation with a nesting matrix both directions,
  close-then-rebind and bind/unbind restore all hold, and the upstream Strawberry seam was audited at the runtime and
  floor versions. Sep-3 had no record (the file arrived 2026-09-17). Found hunting `utils/execution_mode.py` (Sep-19)
- [x] 161. `utils/imports.py`: no bugs in either campaign. `CHANNELS_FLOOR` is single-sourced into every install hint
  and pinned to the pyproject dev-group row by a governance test; hostile str-subclass names are normalized at all four
  entry points. Found hunting `utils/imports.py` (Sep-3, Sep-19)
- [x] 162. Low. `utils/input_values.py::iter_active_fields`: after the related-declaration refactor, a raising
  `config.related_attr` read escaped the walker raw where HEAD had contained it. Sep-3 added an `except BaseException`
  arm; `73a190b6` reversed it on purpose (a consumer property's exception propagates) and pins it with
  `tests/utils/test_input_values.py::test_iter_active_fields_propagates_a_hostile_config_related_attr_read`. Closed as
  not a bug. Found hunting `utils/input_values.py` (Sep-3)
- [x] 163. (robustness) Low. `utils/input_values.py::raise_set_traversal_depth_exceeded` interpolated a `str`-subclass
  `__qualname__`, running its hostile `__str__` / `__format__` while the depth-cap failure assembled. Done (`f9ac71bf`,
  then `7532ab43`: the label reads `truth.qualname` bare; tests
  `tests/utils/test_input_values.py::test_depth_cap_error_label_survives_a_qualname_whose_class_read_raises`,
  `test_depth_cap_error_label_reads_qualname_defensively`). Found hunting `utils/input_values.py` (Sep-19)
- [x] 164. (robustness) Low. `utils/inputs.py`: eight loud-but-untyped escapes at declaration seams when a value's
  `__class__` raised or lied: `canonicalize_set_meta_fields`, the factory mapping gate, `_hashable_meta_value`, the
  field-name-sequence dispatches, the dynamic-class model gate, the lazy-annotation subclass check, six label sites, and
  the `FilterSet.get_fields` pre-check (`filters/sets.py`). Done as bug_hunt-0_0_15_2.md item 23 (`f9ac71bf`,
  `53001bdd`, `73a190b6`): a raising `Meta.fields` gets the typed re-readable rejection on both families
  (`tests/utils/test_inputs.py::test_meta_fields_canonicalization_passes_a_value_whose_class_read_raises_through`,
  `test_normalize_field_name_sequence_rejects_a_value_whose_class_read_raises`), and the label reads need no code (items
  20 and 23). The Sep-3 hunt found no bug (its six pins stay). Found hunting `utils/inputs.py` (Sep-19)
- [x] 165. `utils/operation_lease.py`: no bugs. `close()` leaves outstanding handles valid, the five construction sites
  never hold a `None` payload, and `held()` is read by identity everywhere. Sep-3 had no record (the file arrived
  2026-09-16). Found hunting `utils/operation_lease.py` (Sep-19)
- [x] 166. Medium. `utils/permissions.py::invoke_permission_method`: a declared non-callable `check_<field>_permission`
  slot (`= 42`) was silently skipped by a bare `callable()` probe, an intended authorization gate that never runs. A
  non-callable, non-`None` slot is now a `ConfigurationError`; `None` stays a no-op. Fixed (`a8f31a2d`, test
  `tests/utils/test_permissions.py::test_invoke_permission_method_rejects_a_non_callable_gate_slot`; re-confirmed as
  bug_hunt-0_0_15_2.md item 409). Found hunting `utils/permissions.py` (Sep-3)
- [x] 167. Low. `utils/permissions.py::invoke_permission_method`: a gate slot whose read raises (a raising descriptor)
  escaped as a raw `RuntimeError`; Sep-3 wrapped it in the typed error. Closed as not a bug: main lets the consumer
  descriptor's own error propagate
  (`tests/utils/test_permissions.py::test_invoke_permission_method_propagates_a_gate_descriptor_error`). The Sep-19
  re-hunt found no further bug. Found hunting `utils/permissions.py` (Sep-3, Sep-19)
- [x] 168. (robustness) `utils/policies.py::resolve_policy` leaked raw exceptions for a hostile override mapping (a
  one-shot mapping that diverges between passes, an unhashable key, a raising iterator) instead of the typed
  `ConfigurationError`. Fixed (`a8f31a2d`): the mapping is materialized once and the key-type guard runs first; a
  raising iterator now propagates its own error. Pinned by
  `tests/utils/test_policies.py::test_a_divergent_one_shot_mapping_resolves_from_one_consumed_pass` and
  `::test_a_hashable_non_string_key_is_typed_rejected_at_the_key_guard`. Found hunting `utils/policies.py` (Sep-3)
- [x] 169. (robustness) Low. `utils/policies.py::resolve_policy` escaped raw `RuntimeError` / `TypeError` for an
  override whose `__class__` raises or lies, a key whose `__eq__` raises, and keys whose `__lt__` raises inside
  `sorted()`, against the typed-error promise. Done as `bug_hunt-0_0_15_2.md` item 23 (`f9ac71bf`, reworked onto
  `utils/truth.py` in `73a190b6`); tests
  `tests/utils/test_policies.py::test_a_policy_value_whose_class_read_raises_is_typed_rejected`,
  `::test_a_key_that_is_not_really_a_string_is_typed_rejected`,
  `::test_comparison_hostile_unknown_keys_are_named_in_the_typed_rejection`. Found hunting `utils/policies.py` (Sep-19)
- [x] 170. `utils/private_state.py`: no bugs (not in the Sep-3 campaign). Found hunting `utils/private_state.py`
  (Sep-19)
- [x] 171. High. `utils/querysets.py::_sealed_prefetch_related_lookups`: a `Prefetch("items", queryset=<unrelated
  model>)` over a coincidentally same-named relation sealed clean, so Django (#37267) filled the relation with the
  foreign table's rows and they reached GraphQL without the related type's `get_queryset` running. Fixed (`a8f31a2d`):
  the lookup path is resolved to its relation target (new `_prefetch_relation_target_or_none`, including the default
  `<model>_set` accessor spelling) and a child of another model fails the seal closed. Tests
  `tests/utils/test_querysets.py::test_prefetch_child_default_accessor_wrong_model_fails_closed` and
  `::test_prefetch_relation_target_resolves_every_installed_default_accessor`. Found hunting `utils/querysets.py`
  (Sep-3)
- [x] 172. (robustness) Low. `utils/querysets.py::_apply_sidecar_sync` / `_apply_sidecar_async` built the sidecar method
  label from a raw `set_class.__name__`, so a raising metaclass `__name__` or a hostile `str` subclass escaped raw.
  Closed: `bug_hunt-0_0_15_2.md` item 23 records the `__name__` labels as needing no code (no contract row), and both
  reads now go through `truth.name` (`73a190b6`, `utils/querysets.py::_apply_sidecar_sync`); no sidecar-specific test
  found, the read itself is pinned by `tests/utils/test_truth.py::test_a_str_subclass_name_reads_as_an_exact_str`. Found
  hunting `utils/querysets.py` (Sep-19)
- [x] 173. Low. `utils/querysets.py`: a hook that returned a `union()` / `intersection()` / `difference()` queryset
  escaped the list-relation child seal as a raw `NotSupportedError` (plan time through `.only()`, or fetch time through
  Django's refilter), and the same class was live on the default-seal surfaces (node refetch, related-filter derive,
  mutation locate, write decode); the Sep-19 fix (`reject_combined=True` on the list-relation child policy) was never
  merged. Done as `bug_hunt-0_0_15_2.md` item 6 (`5c5e32c5`): a combined result is rebuilt as its primary-key set on
  every surface and shapes it cannot represent are refused with a typed error (the `reject_combined` axis is gone), live
  rows in `examples/fakeshop/test_query/test_combined_visibility_api.py`. Found hunting `utils/querysets.py` (Sep-19)
- [x] 174. Low. `utils/querysets.py`: a combinator hook result that carried its own ordering by an expression (`Lower`,
  `Case`) raised a raw `TypeError` inside Django when the seal rebuilt the query. Done as `bug_hunt-0_0_15_2.md` item 37
  (`22900492`: a combined hook queryset keeps an `F()` / `OrderBy` ordering). Found hunting `utils/querysets.py`
  (Sep-19)
- [x] 175. (stale-row) `utils/relations.py::path_traverses_to_many.cache_clear` cleared only the outer `lru_cache`, so
  after an explicit clear a warm `(model, field_path)` key kept serving the stale `ClassifiedPath`. Fixed (`a8f31a2d`):
  a new `_path_traverses_to_many_cache_clear` clears the inner classification cache, then the outer, and is bound onto
  the handle. Test
  `tests/utils/test_relations.py::test_path_traverses_to_many_cache_clear_reaches_the_classification_cache`. Found
  hunting `utils/relations.py` (Sep-3)
- [x] 176. `utils/relations.py`: no bugs in the Sep-19 campaign (185-probe battery, both Python cells, unique-reverse-FK
  and cache bound confirmed; a later docstring-only drift was re-verified as behaviour-neutral). Found hunting
  `utils/relations.py` (Sep-19)
- [x] 177. (robustness) Low. `utils/sessions.py::session_store_class` leaked a raw `RuntimeError` for a `SESSION_ENGINE`
  that is a hostile `str` subclass (raising `__format__` in the import-path f-string, raising `__repr__` in the
  rejection message). Fixed (`a8f31a2d`): the engine is copied to an exact `str` before use. Tests
  `tests/utils/test_sessions.py::test_session_store_class_format_hostile_engine_raises_configuration_error` and
  `::test_session_store_class_repr_hostile_engine_raises_configuration_error`. Found hunting `utils/sessions.py` (Sep-3)
- [x] 178. (robustness) Low. `utils/sessions.py::session_store_class` still escaped raw for a `SESSION_ENGINE` with a
  raising `__bool__` / `__len__`, a lying or raising `__class__`, or a lying-`True` empty subclass, against the
  typed-error contract. Done as `bug_hunt-0_0_15_2.md` item 23 (`f9ac71bf`, `73a190b6`: the engine is accepted by its
  real class and flattened before the emptiness check); tests
  `tests/utils/test_sessions.py::test_session_store_class_rejects_an_engine_that_is_not_really_a_string`,
  `::test_session_store_class_resolves_a_truthiness_hostile_engine`. Found hunting `utils/sessions.py` (Sep-19)
- [x] 179. `utils/strings.py`: no bugs in the Sep-3 string-helper battery (hostile `str` subclasses, snake/camel round
  trip, non-string inputs all typed). The `pascal_case` leading and trailing underscore change that campaign noted
  belongs to `filters/inputs.py`. Found hunting `utils/strings.py` (Sep-3)
- [x] 180. (robustness) Low. `utils/strings.py::_plain_text` ran an unguarded `isinstance` and `str.__str__`
  normalization, so a `__class__` spoof or raising `__class__` escaped every string helper raw instead of the typed
  `ConfigurationError`. Done as `bug_hunt-0_0_15_2.md` item 23 (`f9ac71bf`, `73a190b6`: the test is `truth.is_instance`,
  the copy `truth.text`); tests
  `tests/utils/test_strings.py::test_string_helpers_reject_a_value_that_is_not_really_a_string` and
  `::test_string_helpers_normalize_hostile_string_subclasses`. Found hunting `utils/strings.py` (Sep-19)
- [x] 181. Low. `utils/typing.py::is_async_callable` returned False for every class, so a class whose metaclass defines
  `async def __call__` passed as a `globalid_strategy` encoder slipped past the build-time sync-ness gate and failed per
  request. Fixed (`a8f31a2d`): a class is classified by `type(target).__call__`. Test
  `tests/utils/test_typing.py::test_is_async_callable_sees_through_an_async_call_metaclass`. Found hunting
  `utils/typing.py` (Sep-3)
- [x] 182. `utils/typing.py`: no bugs in the Sep-19 campaign (71-node battery on Python 3.10 to 3.14; the one real
  divergence, `partialmethod` reading async on 3.13+, is unreachable because every seam rejects it typed first). Found
  hunting `utils/typing.py` (Sep-19)
- [x] 183. (robustness) Low. `utils/write_transaction.py`: the write fingerprint and phase guard trusted consumer code
  in ten places (scalar leaves rendered through a subclass's lying `__repr__`, dict keys repr'd wholesale, `bytes(item)`
  calling a raising `__bytes__`, opaque objects with a constant `__repr__` collapsing to one fingerprint, a hostile
  `__eq__` escaping `assert_no_target_drift`, a non-string statement reaching `is_read_only_sql`'s `str()`). Fixed
  (`a8f31a2d`): base-slot `_leaf_token`, keys walked as nodes, byte strings read through their base buffer, id-tagged
  opaque leaves, unreadable comparison failing closed as typed drift, non-string SQL unclassifiable. Tests
  `tests/mutations/test_write_transaction.py::test_field_fingerprint_reads_hostile_containers_through_their_base_slots`,
  `::test_field_fingerprint_reads_bytes_through_their_base_buffer`,
  `::test_assert_no_target_drift_propagates_a_planted_eq_error` and
  `::test_is_read_only_sql_fails_closed_on_a_non_string_statement`. Found hunting `utils/write_transaction.py` (Sep-3)
- [x] 184. (robustness) Low. `utils/write_transaction.py` read raw `__name__` for five message labels (mutation class,
  signal sender, queryset model, model, instance type), so a hostile name escaped raw. Done as `bug_hunt-0_0_15_2.md`
  item 23 (no contract row, label question is item 26); the five sites now read `truth.name` (`73a190b6`, pinned by
  `tests/utils/test_truth.py::test_a_str_subclass_name_reads_as_an_exact_str`, no write_transaction-specific test
  found). Found hunting `utils/write_transaction.py` (Sep-19)
- [x] 185. `utils/write_values.py`: no bugs in either campaign (hidden and missing relation rows give identical
  envelopes at the batch and single seams, coercion matrix never raw, one query for duplicates and generators). Found
  hunting `utils/write_values.py` (Sep-3, Sep-19)
- [x] 186. `views.py`: no bugs in either campaign (413 before parse, bounded body read, UTF-8 wire contract, CSRF
  carve-outs, absent settings fail closed to the 1 MiB default). Found hunting `views.py` (Sep-3, Sep-19)
- [x] 187. (stale-row) Baseline failure: collection-time model fixture isolation. `tests/utils/test_querysets.py`
  proxy-target fixtures registered models in the global app registry, polluting finalization and missing-table tests.
  Already fixed on main (`a01a2ab8`: the fixtures carry a private `Meta.apps` registry, `_proxy_target_apps`). Found in
  the baseline failure item (Sep-19)
- [x] 188. Scenario pagination window semantics: no bugs (offset, keyset and nested walks exact, backward walks,
  tampered and cross-vocabulary cursors rejected, charge monotonic); the negative-offset cursor found elsewhere is item
  2 of `bug_hunt-0_0_15_2.md` (`a57bd826`). Found in scenario pagination window semantics (Sep-19)
- [x] 189. Scenario authorization and visibility across actors: no bugs (57 probes: actor rotation, no-`related_name`
  reverse relations, awaitable truthiness, cross-execution sentinels, plan-cache actor isolation). Two robustness rows
  carried no fix: a consumer-authored relation resolver owns its own scoping; and a field gate returning `False` without
  raising did not deny, which main now closes (`fc46ba10`: a gate returning anything but `None` or `True` denies, stated
  in `docs/README.md`). Found in scenario authorization and visibility across actors (Sep-19)
- [x] 190. High (WebSocket tier; HTTP low at most). Scenario transaction and session lifecycle under interruption: a
  cancellation arriving while the async mutation window opens its transaction left the atomic block open on the shared
  worker connection, so later mutations nested inside it and reported success for writes that never committed. Already
  fixed on main (`bug_hunt-0_0_15_2.md` item 10, `316b06a8`): the window enters, runs and exits its atomic in one thread
  call and a cancelled task waits for that thread across repeated cancellation before re-raising, pinned by
  `tests/mutations/test_write_transaction.py::test_a_cancelled_window_ends_after_its_thread_and_the_next_mutation_commits`
  and `::test_a_client_complete_mid_window_never_strands_its_transaction`. The Sep-19 opener and teardown hardening
  (`_drive_window_transition`, `_cancel_all_but_current`) was never merged and its separate opener does not exist on
  main. Found in scenario transaction and session lifecycle under interruption (Sep-19)
- [x] 191. Deep dive 1 (nested read execution): no bugs. Live rows were exact for text-pk, O2O-pk, `to_field`, MTI,
  proxy, no-`related_name`, cycle and self-M2M nested reads, window-versus-fallback agreement and FK-id elision. Found
  in deep dive 1 (Sep-19)
- [x] 192. Deep dive 1 promotion P1: a composite-primary-key parent with a multi-column `ForeignObject` reverse as a
  nested connection had only a unit pin and no live row. Live rows now exist in
  `examples/fakeshop/test_query/test_relation_link_api.py` after `bug_hunt-0_0_15_2.md` item 1 (`fe6a6df0`, `337b3317`).
  Found in deep dive 1 (Sep-19)
- [x] 193. Deep dive 1 promotion P3: a root connection field whose consumer resolver returns a plain sequence had no
  live row. Done:
  `examples/fakeshop/test_query/test_connection_fields_api.py::test_consumer_resolver_iterable_without_sidecar_input_paginates`
  posts it through the package's HTTP view. Found in deep dive 1 (Sep-19)
- [x] 194. Deep dive 2 (write-input parity across mutation flavors): no bugs. Seven wire-differential splits (form
  scalar null as `""`, form M2M null clears, subtitle NULL versus `""`, required M2M `[]`, whitespace, custom-input
  partial required, coercion versus envelope) were each validator-inherent or documented. Found in deep dive 2 (Sep-19)
- [x] 195. Deep dive 2 live rows D1 and D2 (serializer `ListField` null child and `allow_blank` `ChoiceField`) had no
  fixture. Fixed through `bug_hunt-0_0_15_2.md` items 5 and 43 (`a5dc6ea3`, `a9dec21d`): live rows
  `examples/fakeshop/test_query/test_library_api.py::test_serializer_only_choice_allow_blank_writes_blank_over_http` and
  `::test_serializer_list_field_nullable_child_round_trips_null_element_over_http` over new library serializer fields.
  Found in deep dive 2 (Sep-19)
- [x] 196. High, client-reachable visibility defect on the consumer-hint nested-read path (surface, rows, location and
  legs are recorded only abstractly; the evidence was sealed and never executed or reproduced here). Already fixed on
  main as `bug_hunt-0_0_15_2.md` item 13 (`5d4cdb3b`, `00563dd0`), live pin
  `examples/fakeshop/test_query/test_library_api.py::test_library_prefetch_object_book_hint_is_scoped_by_book_type_get_queryset`.
  Found in deep dive 3 (Sep-19)
- [x] 197. Low. Nested forward-FK, forward and reverse one-to-one resolvers never called `check_deadline`, so lazy loads
  proceeded past an expired request deadline (sibling seams rejected the same shape). Done as `bug_hunt-0_0_15_2.md`
  item 12 (`8d4f66bd`: every package seam that reaches the database checks the deadline first), live rows in
  `examples/fakeshop/test_query/test_resource_policy_api.py::test_a_passed_deadline_stops_a_nested_forward_fk_before_its_lazy_load`
  and siblings. Found in deep dive 3 (Sep-19)
- [x] 198. Deep dive 3 follow-ups: the `ResourcePolicy` seam list gains the new seam (done in `8d4f66bd`, which rewrote
  `resource_policy.py`), and the hiding-hook fixture lead is done (`16a8c179`: `VenueBadgeType` and `VenueSponsorType`
  hide marked rows, live rows over the no-`related_name` reverse accessors; `bug_hunt-0_0_15_2.md` item 28). Found in
  deep dive 3 (Sep-19)
- [x] 199. Deep dive 4 (sidecar merge and normalization): an overlap head (declared and generated filter on one name)
  bound a named generated lookup to the declared form key, so the filter silently returned wrong rows. Done as
  `bug_hunt-0_0_15_2.md` item 4 (`754ed263`, `9f7ea5dd`: each lookup binds to its own filter); tests
  `tests/filters/test_sets.py::test_normalize_input_overlap_head_binds_each_lookup_to_its_own_filter` and
  `tests/filters/test_inputs.py::test_overlap_head_emits_one_bag_with_each_lookup_keeping_its_own_form_key`. Found in
  deep dive 4 (Sep-19)
- [x] 200. Deep dive 4 other results: no further defect. The five wire-unreachable silences were re-derived, the gate
  matrix (including permission-first ordering) is complete, the orders twin is clean, and the filters-loud /
  orders-silent unknown-key divergence needs no code (`bug_hunt-0_0_15_2.md` item 27). The README line over-generalizing
  `in: []` is moot after item 14 (`e09b5ef1`). Found in deep dive 4 (Sep-19)
- [x] 201. Deep dive 5 (error reporting contract): no bugs. The five-row production error table, hook-seam ownership,
  rejection codes, `ListArgumentError` vocabulary, transport rejections and per-event subscription masking were proven
  live, and the six permanent pins live on main in `examples/fakeshop/test_query/test_error_policy_api.py` (for example
  `::test_a_plain_schema_leaves_a_hook_failure_unmasked`,
  `::test_two_unexpected_errors_in_one_response_carry_two_different_ids`,
  `::test_a_refused_schema_still_bounds_an_over_budget_document_live`). Found in deep dive 5 (Sep-19)
- [x] 202. Deep dive 5 ride-in: a malformed relation GlobalID was judged conformant as a masked top-level error with a
  correlation id (byte-identical on six legs). Main later made it the relation's `FieldError` instead (`0100f26d`, test
  `examples/fakeshop/test_query/test_error_policy_api.py::test_a_malformed_relation_id_is_the_relation_field_error_never_a_masked_error`).
  Found in deep dive 5 (Sep-19)
- [x] 203. Low. Package integration: the root `__getattr__` hook was annotated `-> type` although two of its soft
  exports are functions, so the shipped `py.typed` handed type-checking consumers a false `type`. Fixed (`a8f31a2d`):
  `-> Any`. Test
  `tests/rest_framework/test_soft_dependency.py::test_getattr_return_annotation_admits_function_valued_exports`. Found
  in package integration (Sep-3)
- [x] 204. Package integration: model and form flavors keyed validator `FieldError.field` by the Django snake_case name
  while the serializer flavor and relation and null errors keyed by the GraphQL input name. Done as
  `bug_hunt-0_0_15_2.md` item 11 (`7517eab2`: every flavor keys to the input field the client sent), with live and
  package rows including `tests/utils/test_error_keys.py` and
  `examples/fakeshop/test_query/test_library_api.py::test_create_publisher_errors_key_to_the_input_fields_sent`. Found
  in package integration (Sep-19)
- [x] 206. (lint) `tests/rest_framework/test_sets.py` carried two 4-element parametrize lists that were not exploded and
  `tests/types/test_base.py` one over-exploded 3-element dict, so `scripts/check_trailing_commas.py --check` failed.
  Both were in the unmerged branch's own hunks; main passes the check. Done as bug_hunt-0_0_15_2.md item 24. Found in
  the trailing-comma lint ledger item (Sep-19)
- [x] 207. `optimizer/join_taxonomy.py::_child_link_is_virtual`: the fix's live-tier row needed a composite-PK /
  `ForeignObject` fakeshop fixture and was left to the maintainer. Fixed as bug_hunt-0_0_15_2.md item 1 (`fe6a6df0`,
  `337b3317`); live rows over `ForeignObject` links (one or two carrier columns) exist on main in
  `examples/fakeshop/test_query/test_relation_link_api.py` and `test_mti_composite_relations_api.py`. Found hunting
  `optimizer/join_taxonomy.py` (Sep-19)
- [x] 208. `rest_framework/serializer_converter.py`: the live-tier rows for the nullable-element widening and the
  `allow_blank` exclusion needed fakeshop serializer fixtures, left to the maintainer. Fixed as bug_hunt-0_0_15_2.md
  item 5 (`a5dc6ea3`), which added the fixtures (`examples/fakeshop/apps/library/serializers.py`, `schema.py`, the
  `Shelf.condition` column) and live rows in `examples/fakeshop/test_query/test_library_api.py`. Found hunting
  `rest_framework/serializer_converter.py` (Sep-19)
- [x] 209. (robustness) `rest_framework/resolvers.py::_error_node_children` (`str(key)` of a hostile-`__str__` dict key)
  and the `{saved!r}` render of a hostile-`__repr__` custom `save()` return were routed out of slice as new-card
  candidates. The `save()` return now asks the real type and renders through the guarded repr; `str(key)` needs no code
  (DRF keeps detail keys as given, no contract row). Done as bug_hunt-0_0_15_2.md items 19 and 27 (`5cbe15de`). Found
  hunting `rest_framework/resolvers.py` (Sep-19)
- [x] 210. (robustness) `optimizer/hints.py` forwarded two leads to other files: the bare `isinstance` trio in
  `types/base.py`, and a `strategy` value whose `__class__` lies escaping raw at `optimizer/nested_fetch.py`. Both
  fixed: the strategy, strictness and `Meta.optimizer_hints` gates now ask the real type through
  `utils/_narrowing.py::is_str` / `is_class` and a guarded `isinstance`. Done as bug_hunt-0_0_15_2.md items 18 and 22
  (`f788edcf`, `f9ac71bf`). Found hunting `optimizer/hints.py` (Sep-19)
- [x] 211. (robustness) `types/base.py` robustness rows noted as card fodder: a non-string annotation key whose
  `__repr__` raises at the string-keys gate, a keyset `cursor_field` value with an evil `str`, the adjacent-gate liar
  shapes (N1-N5), and a lying non-raising `__mro__` (O2); plus the raw `__mro__` reads in `types/finalizer.py` and the
  relay-owned seams (`types/relay.py` `apply_interfaces` pre-scan and upstream scan). The `Meta` gates, annotation keys
  and `cursor_field` now use guarded `isinstance` / real-type asks; the `__mro__` reads need no code (no contract row).
  Done as bug_hunt-0_0_15_2.md items 22 and 27 (`f9ac71bf`). Found hunting `types/base.py` and `types/finalizer.py`
  (Sep-19)
- [x] 212. (robustness) `sets_mixins.py` residual lead: a raising-liar `Meta.fields` reaching
  `filters/sets.py::get_fields`, `utils/inputs.py::canonicalize_set_meta_fields` and upstream `django_filters` end to
  end. A `Meta.fields` whose `__class__` raises is now the typed re-readable rejection on both set families
  (`canonicalize_set_meta_fields`, `FilterSet.get_fields`, `is_re_readable_field_declaration`). Done as
  bug_hunt-0_0_15_2.md item 23 (`f9ac71bf`). Found hunting `sets_mixins.py` (Sep-19)
- [x] 213. (stale-row) `tests/types/test_converters.py::test_convert_scalar_class_liar_at_hstore_dispatch_stays_typed`
  passed only when `django.contrib.postgres.fields` is unimportable; with psycopg v3 installed the `ArrayField` arm
  fired first and the pin was red. The maintainer was to decide whether to harden the pin. The test (with the
  hostile-class dispatch guards it pinned) is no longer on main (removed by `73a190b6`), so the question is moot. Found
  hunting `types/converters.py` (Sep-19)
- [x] 214. Decision request:
  `tests/test_list_field.py::test_djangolistfield_unregistered_guard_survives_a_hostile_metaclass_name` was red because
  the `types/base.py::DjangoType.__init_subclass__` unreadable-`__name__` guard rejected the test's class at creation,
  outside its `pytest.raises`; the guard stood or the test was retired. Neither the test nor the guard
  (`_safe_class_name` in `types/base.py`) is on main (both gone in `73a190b6`), so nothing remains to decide. Found in
  the Sep-19 gate review
- [x] 215. A `get_queryset` hook returning a combinator (`union()` / `intersection()` / `difference()`) escaped the
  list-relation seal raw (`NotSupportedError` at plan or fetch time), and the other surfaces of the `utils/querysets.py`
  `_DEFAULT` policy (9-surface census) were left unflipped for a maintainer decision, with a raw `TypeError` for an
  order-by expression extending the census. The hunt's `reject_combined=True` fix is superseded: a combined hook result
  is now rebuilt as a primary-key set on every surface, `reject_combined` and the list-argument policy are removed, and
  `F()` / `OrderBy` column ordering is carried. Done as bug_hunt-0_0_15_2.md items 6 and 37 (`5c5e32c5`, `22900492`).
  Found hunting `optimizer/walker.py` and `utils/querysets.py` (Sep-19)
- [x] 216. The Sep-3 campaign's closeout record (Status complete, +463/-2) survived only as an uncommitted scratch patch
  and needed a commit. Committed as `bug_hunt-0_0_15-historical.md` (`73a190b6`) and now folded into this list. Found in
  the Sep-19 migration record
- [x] 217. High. `schema.py::DjangoMutationExecutionContext._execute_mutation_field_async` (t3 design: a bare `await` of
  the enter, `_exit_with_error` and `_exit_clean` sync-boundary calls): a client cancel or `complete` while the exit sat
  queued behind another socket's call made asgiref drop the queued exit, stranding the row in an open atomic after the
  lock was released; the enter-side shield-handoff also swallowed the `CancelledError` (the enter error replaced
  `opener_cancelled`, a failed handoff exit replaced the cancel) and an opener self-cancel left a completed enter open.
  Main has no such seams: the whole window (enter, completion, exit) is one sync call on its own thread and connection,
  a cancelled private window waits for its thread across repeated cancels and then re-raises the `CancelledError`
  unchanged. Already fixed on main (`1b6a09b1`, `316b06a8`; tests
  `tests/mutations/test_write_transaction.py::test_a_window_cancelled_during_its_enter_still_exits_the_transaction_it_opened`
  and `::test_a_cancelled_window_ends_after_its_thread_and_the_next_mutation_commits`; `bug_hunt-0_0_15_2.md` item 10).
  The review's test errata (T1-T4) and record corrections (R1-R3) described t3-only tests and prose. Found in review 5a
  (Sep-19, scenario Transaction and session lifecycle; the scenario's own result belongs to that slice)
- [x] 218. Rule-35 classification of the t3 ledger: 8 rows met the three legs (defect), 37 rows were robustness rows
  (hostile `__class__`, metaclass `__name__`/`__mro__`/`__hash__`/`__getattr__`, `str` subclasses with raising dunders;
  no wire or settings input), 2 lint rows, 1 stale row; the open question was whether guards for the robustness rows
  stay. Answered in practice: main kept hostile-metadata guards and re-based them on guarded `isinstance` / `is_str` /
  `is_class` helpers (`bug_hunt-0_0_15_2.md` items 16-23 done, e.g. `f788edcf`, `5cbe15de`, `32b66897`); the one
  remaining policy question is the separate `BaseException` entry. No explicit maintainer ruling text was found, only
  the landed behaviour. Found in review 5b (Sep-19)
- [x] 220. Review 5d, `rest_framework/sets.py` (~:196): `get_serializer_for_schema` keys that are not identifiers were
  newly rejected, a behaviour change the second reader concurred with. On main a kept serializer field named by a
  non-identifier or keyword is refused at class creation, root and nested, instead of raising an unnamed `SyntaxError`
  at finalize. Done as `bug_hunt-0_0_15_2.md` item 19 (`5cbe15de`). Whether the identifier-only rule should become a
  GraphQL-name check is item 229 (open, separate entry in the mutation-naming family). Found in review 5d (Sep-19)
- [x] 221. Review 5d, `filters/inputs.py::_normalize_range_value` (~:807) and
  `filters/sets.py::FilterSet._normalize_input` (~:2403): t3 raised where the old code silently did nothing (an
  unreadable hand-built range value; two active lookups on one declared+generated form key, reach corrected to
  "direct-Python + overlap-wire"). Main covers both by other means: an unreadable range value raises
  `ConfigurationError` (`a54ad7c8`, item 15) and each lookup is bound once to its own form key so two lookups on one key
  both apply and a hand-built mapping naming an unknown field or lookup raises (`754ed263`, `9f7ea5dd`, item 4; tests
  `tests/filters/test_sets.py::test_normalize_input_overlap_head_binds_each_lookup_to_its_own_filter`,
  `tests/filters/test_inputs.py::test_overlap_head_emits_one_bag_with_each_lookup_keeping_its_own_form_key`, live rows
  in `examples/fakeshop/test_query/test_library_api.py`). The t3 raise itself does not exist on main. Found in review 5d
  (Sep-19)
- [x] 222. Review 5d, `rest_framework/serializer_converter.py`: the `allow_blank` fix changed the published schema (enum
  to `String`) and needed maintainer sign-off before the gate. Resolved differently on main: an `allow_blank` serializer
  `ChoiceField` publishes its generated enum with a `BLANK` member that writes `""`, no `String` fallback (`a5dc6ea3`,
  `bug_hunt-0_0_15_2.md` items 5 and 192; list and multiple-choice forms `a9dec21d`, item 43; live row
  `examples/fakeshop/test_query/test_library_api.py::test_serializer_only_choice_allow_blank_writes_blank_over_http`).
  Found in review 5d (Sep-19)
- [x] 223. Review 5e prose rows: `filters/inputs.py` docstring "the previous arms SPLATTED" (process provenance),
  `tests/test_resource_policy.py` test docstring "proves the fix reaches a real request", mis-indented renumbered list
  in `routers.py` (~:256) and a misaligned docstring line in `sets_mixins.py` (~:466). All four were t3-only text that
  never reached main; `rg` finds none of the phrases in the package or tests. Closed as not a bug on main. Found in
  review 5e (Sep-19)
- [x] 225. Dive 4 new-card candidates and docs lead: (a) B21 corollary, a foreign single lookup on a declared-only head
  (misbinding unsafely versus the ignore-safely family posture); (b) filters raise on unknown hand-built keys while
  orders skip them (harmonization question); (c) README over-generalized integer `in: []` (executed: every row, sentence
  said none). (a) is covered by binding each lookup to its own form key once and raising on an unknown field or lookup
  in a hand-built mapping (`754ed263`, item 4); (b) was ruled no code (no contract row, hand-built input only; item 27);
  (c) fixed with the `in: []` rework (`e09b5ef1`, item 14; `docs/README.md` states an empty list matches no rows). Found
  in deep dive 4 (Sep-19)
- [x] 229. Sep-3 lead: the read-side twin of a hostile `__eq__` at the `mutations/fields.py` mutation-registry
  membership (the write side was fixed there). Fixed: `DjangoMutationField` no longer checks ledger membership by
  equality, so a drained class equal to its redeclaration cannot build a schema whose requests fail (`b4d6e06a`,
  `bug_hunt-0_0_15_2.md` item 17). Found as an open lead of the Sep-3 campaign (`mutations/sets.py` observations)
- [x] 230. Sep-3 lead: `optimizer/nested_planner.py` stale return annotation (recorded for the ConnectionWindowBounds
  owner). Already correct on main: `_connection_window_slice_from_arguments` returns `ConnectionWindowBounds | None` and
  `_keyset_window_slice_from_arguments` returns `tuple[ConnectionWindowBounds, KeysetSeek | None] | None`, and
  basedpyright (`all` mode) gates return annotations. Found as an open lead of the Sep-3 campaign
  (`optimizer/nested_planner.py` item)
- [x] 231. Sep-3 lead: `utils/context.py::get_context_value` ran its `isinstance` outside the guarded region, so a
  hostile context class could escape raw. No contract row and no wire input (robustness class, items 22-23); main reads
  the dispatch through the guarded `utils/_narrowing.py::is_dict` and documents which exceptions an absent key means.
  Closed as a robustness row, no further code. Found as an open lead of the Sep-3 campaign (`utils/context.py` item)
- [x] 232. Sep-3 cross-file leads from the `schema.py` / `types/resolvers.py` items:
  `resource_policy.py::_require_positive_int` and `_is_valid_deadline` bool pre-check, `ErrorPolicy.__post_init__` and
  `bounded_rows` each let a hostile value escape as a raw error at `DjangoSchema` construction or on the first request.
  Fixed for the policies: the type tests are EXACT (`type(value) is not int`, `_is_builtin_number`, `type(self.enabled)
  is not bool`; `fb6ccdb6`; `resource_policy.py::_require_positive_int`, `error_policy.py::ErrorPolicy.__post_init__`).
  `bounded_rows` still raises the same `TypeError` `islice` would for a non-iterable consumer result, by documented
  design (`resource_policy.py::_consumer_rows`): application error, not a wire input. Found as open leads of the Sep-3
  campaign (`schema.py`, `types/resolvers.py`)
- [x] 234. Sep-3 unexamined scope: the parked single-item querysets run (`bug_hunt-0_0_15-querysets.md`: every item but
  `utils/querysets.py`, plus its integration and gate) and scenario items never existed in the Sep-3 format. Superseded:
  the Sep-19 campaign re-hunted all 104 file items plus scenarios and deep dives (`bug_hunt-0_0_15_2.md` re-verified
  each on main); the Sep-3 fixes landed on main at the time, and their per-fix survival was spot-checked only (five pins
  at closeout), not individually re-proven. Found in the Sep-3 Outcomes (Unexamined scope)
- [x] 235. Regrade (Sep-3 independent review): `permissions.py` Fixed Low is a refactor, not a fix; the sliced and
  combined queryset rejections were consolidated into `_CASCADE_SEAL_POLICY` in `utils/querysets.py`. No open work.
  Found hunting `permissions.py` (Sep-3)
- [x] 236. Regrade (Sep-3 independent review): `optimizer/hints.py` Fixed Low is docstring-only after the
  `nested_fetch.py` root fix removed its `_require_strategy` shim. No open work. Found hunting `optimizer/hints.py`
  (Sep-3)
- [x] 237. Regrade (Sep-3 independent review): `utils/strings.py` No bugs stands; the `pascal_case` edge-underscore
  behaviour change belongs to the `filters/inputs.py` item (Fixed Medium). No open work. Found hunting
  `utils/strings.py` (Sep-3)
- [x] 238. Regrade (Sep-3 independent review): `mutations/resolvers.py` No bugs, DRY-only changes;
  `optimizer/extension.py` Fixed Low x2 reduced to two cosmetic hunks. No open work. Found hunting
  `mutations/resolvers.py` and `optimizer/extension.py` (Sep-3)
- [x] 239. Regrade (Sep-3 independent review): `consumers.py` Fixed High keeps its headline, with its tests named (12
  containment rows and the close-code test in `tests/test_routers.py`) and the close code split `4400` (client
  frame-shape escapes) versus `1011` (server-side). No open work. Found hunting `consumers.py` (Sep-3)
