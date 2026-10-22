# django-strawberry-framework Kanban

Last refreshed: 2026-10-20

This board summarizes what is shipped, what has recently landed, and what remains to finish based on the current code, tests, docs, and release-readiness notes. It is intentionally written as a project-management view: each card has a status, priority, scope, and a practical definition of done.

Editing this board: `KANBAN.md` is a rendered artifact, not a source. The source of truth is the `kanban` Django app under [`examples/fakeshop/apps/kanban/`][kanban-app] — `BoardDoc` rows hold the prose sections (this preamble, the snapshot, the column intros, the footers), `Card` rows hold each card's identity / status / priority / dependencies, and `CardItem` / `CardReference` / `ParityClaim` rows hold the per-card bulleted body, blocking-or-related links between cards, and the parity claims against upstream packages. To change anything on the board, edit the relevant row(s) in the SQLite database at `examples/fakeshop/db.sqlite3` (Django admin or `manage.py shell`), then run `uv run python scripts/build_kanban_md.py` and `uv run python scripts/build_kanban_html.py` to regenerate `KANBAN.md` and `KANBAN.html`. Direct edits to `KANBAN.md` are overwritten on the next rebuild.

## Card ID format

Every card uses the form `<STATUS>[-<MILESTONE>]-NNN-X.Y.Z`:

- `<STATUS>` — the card workflow state: `BACKLOG` (unscheduled investigation / strategic-differentiation candidate), `TODO` (committed to a milestone, not yet active), `WIP` (actively being worked), or `DONE` (shipped). Updated when the card moves between workflow states. Blocking is not part of the workflow status; blocked cards render a derived `blocked` badge from unfinished `blocked_by` references and stay in their normal planning column.
- `<MILESTONE>` *(optional)* — the development phase the card lives in while it's still pre-shipping: `ALPHA` (pre-`0.1.0`), `BETA` (post-`0.1.0` / pre-`1.0.0`), or `STABLE` (post-`1.0.0`). Used on `BACKLOG`, `TODO`, and `WIP` cards. The two release cards themselves are tagged with the phase they usher in: `TODO-ALPHA-057-0.1.0` is the alpha → beta cut-over and `TODO-STABLE-073-1.0.0` is the beta → stable cut-over. **Dropped when the card ships** — `DONE` cards use the bare `DONE-NNN-X.Y.Z` form (no milestone segment). The card's version tag (`X.Y.Z`) already encodes which phase the shipment belongs to, and the bare form keeps the shipped-card cluster compact and uniform across the package's history.
- `NNN` — a 3-digit sequence number indicating the order the card was completed (`DONE` cards) or is being tracked (everything else; scheduled cards are ordered by planned ship version, and backlog cards sort after the scheduled board). **Unlike status, milestone, and version, this number is not stable** — it is recomputed whenever a card's position in the shipping sequence changes (reordered, new card inserted between two existing cards, version-tag bumped). Use the card title, not the NNN, when referencing a card from long-lived documents.
- `X.Y.Z` — the package version the card shipped in (`DONE` cards), is planned to ship in (scheduled cards), or is provisionally bucketed under (`BACKLOG` cards). Alpha cards span `0.0.6` through `0.0.15` leading up to `0.1.0`; Beta cards span `0.1.1` through `0.1.8` leading up to `1.0.0`. The `0.1.0` and `1.0.0` tags are reserved for the two release cards themselves. Backlog cards may use post-`1.0.0` buckets as ordering placeholders; they stay unscheduled until promoted to `TODO`.

For install, local development, testing, and the canonical documentation map, start from [`README.md`][readme].

## Relative size

A five-point T-shirt estimate of build effort — a planning estimate, not a commitment — anchored to the shipped Filtering subsystem (`DONE-027-0.0.8`) as XL:

- **XS** - trivial / mechanical; ≲½ day; one small module or a bookkeeping edit; no spec.
- **S** - small; ~1 day; one module + tests; light or no spec.
- **M** - moderate; a few days; multi-file, a real spec, a handful of design decisions.
- **L** - large subsystem; ~a week; new subpackage, full spec, broad integration.
- **XL** - very large subsystem at `DONE-027-0.0.8` scale.

## Progress to 1.0.0

**64.9% complete** toward `1.0.0` - 50 of 77 cards done (62.5% size-weighted). Across all non-backlog cards (incl. post-`1.0.0`), 50 of 78 (64.1%, 61.5% size-weighted). Past the 50% mark. Backlog excluded; size-weighted by relative size (XS=1 .. XL=5).

| Milestone | Cards done | Size-weighted |
| --- | --- | --- |
| Alpha (pre-0.1.0) | 50/60 (83.3%) | 81.2% |
| Beta (pre-1.0.0) | 0/16 (0.0%) | 0.0% |
| Stable (post-1.0.0) | 0/2 (0.0%) | 0.0% |

## Card index

Every card on the board, in board order. Links jump to the card.

| Card | Title | Column |
| --- | --- | --- |
| [`WIP-ALPHA-051-0.0.15`](#upstream_parity_gap_closure) | Upstream parity-gap closure | In progress |
| [`TODO-ALPHA-052-0.0.15`](#extract_djangodebugextension_into_the_standalone_django_strawberry_debug_package) | Extract DjangoDebugExtension into the standalone django-strawberry-debug package | In progress |
| [`TODO-ALPHA-053-0.0.15`](#boundary_hardening_and_system_wide_dry_squeeze) | Boundary hardening and system-wide DRY squeeze | In progress |
| [`TODO-ALPHA-054-0.0.16`](#pluggable_field_conversion_registry) | Pluggable field-conversion registry | To Do - Alpha (0.1.0) |
| [`TODO-ALPHA-055-0.0.16`](#apollo_federation_as_the_standalone_django_strawberry_federation_package) | Apollo Federation as the standalone django-strawberry-federation package | To Do - Alpha (0.1.0) |
| [`TODO-ALPHA-056-0.0.17`](#alpha_documentation_debt_discharge) | Alpha documentation-debt discharge | To Do - Alpha (0.1.0) |
| [`TODO-ALPHA-057-0.1.0`](#beta_release_cleanup_verification_alpha_beta) | Beta release (cleanup, verification, alpha → beta) | To Do - Alpha (0.1.0) |
| [`TODO-ALPHA-078-0.0.17`](#owning_spec_for_the_nested_connection_fetch_strategy_seam) | Owning spec for the nested-connection fetch-strategy seam | To Do - Alpha (0.1.0) |
| [`TODO-ALPHA-079-0.0.17`](#owning_spec_for_the_mutation_write_pipeline_transaction_locks_write_alias_authorization) | Owning spec for the mutation write pipeline (transaction, locks, write alias, authorization) | To Do - Alpha (0.1.0) |
| [`TODO-ALPHA-080-0.0.17`](#scriptsarchive_specpy_mechanize_the_spec_and_build_plan_archive_sweep) | `scripts/archive_spec.py`: mechanize the spec and build-plan archive sweep | To Do - Alpha (0.1.0) |
| [`TODO-BETA-058-0.1.1`](#graph_substrate_shared_graph_policy_and_dependency_planning) | Graph substrate: shared graph policy and dependency planning | To Do - Beta (1.0.0) |
| [`TODO-BETA-059-0.1.1`](#fieldset_declarative_field_level_behavior_metafields_class) | `FieldSet` declarative field-level behavior (`Meta.fields_class`) | To Do - Beta (1.0.0) |
| [`TODO-BETA-060-0.1.2`](#metasearch_fields_support) | `Meta.search_fields` support | To Do - Beta (1.0.0) |
| [`TODO-BETA-061-0.1.2`](#postgres_full_text_search_filter_primitives) | Postgres full-text search filter primitives | To Do - Beta (1.0.0) |
| [`TODO-BETA-062-0.1.3`](#aggregation_subsystem) | Aggregation subsystem | To Do - Beta (1.0.0) |
| [`TODO-BETA-063-0.1.3`](#mutation_idempotency_keys) | Mutation idempotency keys | To Do - Beta (1.0.0) |
| [`TODO-BETA-064-0.1.4`](#opt_in_node_sentinel_redaction_tier_metaredaction_mode) | Opt-in node-sentinel redaction tier (`Meta.redaction_mode`) | To Do - Beta (1.0.0) |
| [`TODO-BETA-065-0.1.4`](#stable_choice_enum_naming_override) | Stable choice enum naming override | To Do - Beta (1.0.0) |
| [`TODO-BETA-066-0.1.5`](#fakeshop_graphql_schema_activation) | Fakeshop GraphQL schema activation | To Do - Beta (1.0.0) |
| [`TODO-BETA-067-0.1.5`](#product_catalog_layer_3_http_graphql_tests) | Product-catalog Layer 3 HTTP GraphQL tests | To Do - Beta (1.0.0) |
| [`TODO-BETA-068-0.1.6`](#structural_optimization_templates_and_nested_sidecar_batching) | Structural optimization templates and nested sidecar batching | To Do - Beta (1.0.0) |
| [`TODO-BETA-069-0.1.6`](#optimizer_explain_mode) | Optimizer explain mode | To Do - Beta (1.0.0) |
| [`TODO-BETA-070-0.1.7`](#configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key) | Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`) | To Do - Beta (1.0.0) |
| [`TODO-BETA-071-0.1.8`](#migration_and_adoption_guides) | Migration and adoption guides | To Do - Beta (1.0.0) |
| [`TODO-BETA-072-0.1.8`](#adversarial_non_live_test_suite) | Adversarial non-live test suite | To Do - Beta (1.0.0) |
| [`TODO-STABLE-073-1.0.0`](#stable_release_api_freeze_cleanup_verification_beta_stable) | Stable release (API freeze, cleanup, verification, beta → stable) | To Do - Beta (1.0.0) |
| [`TODO-STABLE-074-1.1.0`](#dynamic_schemas_from_datatype_specs_synthetic_unmanaged_models) | Dynamic schemas from dataType specs (synthetic unmanaged models) | To Do - Beta (1.0.0) |
| [`TODO-BETA-077-0.1.7`](#generated_input_field_names_follow_the_schema_naming_config_auto_camel_case_nameconverter) | Generated input field names follow the schema naming config (`auto_camel_case`, `NameConverter`) | To Do - Beta (1.0.0) |
| [`DONE-050-0.0.15`](#djangolistfield_argument_surface_offset_limit_and_orderby) | `DjangoListField` argument surface: `offset` / `limit` and `orderBy` | Done |
| [`DONE-049-0.0.14`](#dependency_and_ci_hardening_refresh_django_locks_add_audit_automation_least_privilege_ci) | Dependency and CI hardening: refresh Django locks, add audit automation, least-privilege CI | Done |
| [`DONE-048-0.0.14`](#secure_output_and_error_defaults_drop_file_path_fail_closed_debug_prod_error_policy) | Secure output and error defaults: drop file path, fail-closed debug, prod error policy | Done |
| [`DONE-047-0.0.14`](#execution_resource_policy_central_budget_object_value_cardinality_walker) | Execution resource policy: central budget object + value-cardinality walker | Done |
| [`DONE-046-0.0.14`](#transport_security_django_owned_http_bounded_body_utf_8_wire_ws_revalidation) | Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation | Done |
| [`DONE-045-0.0.14`](#sealed_get_queryset_visibility_boundary_policy_artifacts) | Sealed get_queryset visibility-boundary policy artifacts | Done |
| [`DONE-044-0.0.14`](#response_extensions_debug_middleware) | Response-extensions debug middleware | Done |
| [`DONE-043-0.0.14`](#test_client_helper) | Test client helper | Done |
| [`DONE-042-0.0.14`](#debug_toolbar_middleware) | Debug-toolbar middleware | Done |
| [`DONE-041-0.0.14`](#channels_asgi_router_migration_aid) | Channels ASGI router (migration aid) | Done |
| [`DONE-040-0.0.13`](#auth_mutations_login_logout_register) | Auth mutations (login / logout / register) | Done |
| [`DONE-039-0.0.13`](#drf_serializer_mutations_serializermutation) | DRF serializer mutations (`SerializerMutation`) | Done |
| [`DONE-038-0.0.12`](#form_based_mutations_django_forms_modelforms) | Form-based mutations (Django Forms / ModelForms) | Done |
| [`DONE-037-0.0.11`](#upload_scalar_and_file_image_field_mapping) | Upload scalar and file / image field mapping | Done |
| [`DONE-036-0.0.11`](#mutations_auto_generated_input_types) | Mutations + auto-generated Input types | Done |
| [`DONE-035-0.0.10`](#optimizer_robustness_hardening_upstream_comparison_guards) | Optimizer robustness hardening (upstream-comparison guards) | Done |
| [`DONE-034-0.0.10`](#permissions_subsystem) | Permissions subsystem | Done |
| [`DONE-033-0.0.9`](#connection_aware_optimizer_planning) | Connection-aware optimizer planning | Done |
| [`DONE-032-0.0.9`](#full_relay_story_node_connection_root_validation) | Full Relay story (Node + Connection + Root + validation) | Done |
| [`DONE-031-0.0.9`](#django_model_based_globalid_encoding) | Django-model-based GlobalID encoding | Done |
| [`DONE-030-0.0.9`](#djangoconnectionfield_relay_connection_field) | `DjangoConnectionField` (Relay connection field) | Done |
| [`DONE-029-0.0.9`](#djangotype_consumer_dx_cleanup_pass) | `DjangoType` consumer-DX cleanup pass | Done |
| [`DONE-028-0.0.8`](#ordering_subsystem) | Ordering subsystem | Done |
| [`DONE-027-0.0.8`](#filtering_subsystem) | Filtering subsystem | Done |
| [`DONE-026-0.0.7`](#scalar_conversion_end_to_end_coverage_in_the_fakeshop_example) | Scalar conversion end-to-end coverage in the fakeshop example | Done |
| [`DONE-025-0.0.7`](#warning_free_scalar_registration_via_strawberryconfigscalar_map) | Warning-free scalar registration via `StrawberryConfig.scalar_map` | Done |
| [`DONE-024-0.0.7`](#django_trac_37064_hardening_safe_wrap_connection_method) | Django Trac #37064 hardening + `safe_wrap_connection_method` | Done |
| [`DONE-023-0.0.7`](#multi_database_cooperation_contract) | Multi-database cooperation contract | Done |
| [`DONE-022-0.0.7`](#schema_export_management_command) | Schema export management command | Done |
| [`DONE-021-0.0.7`](#appspy_and_django_app_config) | `apps.py` and Django app config | Done |
| [`DONE-020-0.0.7`](#djangolistfield_non_relay_list) | `DjangoListField` (non-Relay list) | Done |
| [`DONE-019-0.0.6`](#consumer_override_semantics_scalar_fields) | Consumer override semantics (scalar fields) | Done |
| [`DONE-018-0.0.6`](#multiple_djangotypes_per_model_with_metaprimary) | Multiple DjangoTypes per model with `Meta.primary` | Done |
| [`DONE-017-0.0.6`](#deferred_scalar_conversions) | Deferred scalar conversions | Done |
| [`DONE-016-0.0.6`](#fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement) | `FieldMeta` single-source-of-truth consolidation and mirror retirement | Done |
| [`DONE-015-0.0.5`](#005_relay_interfaces_and_node_foundation) | 0.0.5 Relay interfaces and Node foundation | Done |
| [`DONE-014-0.0.4`](#move_test_fixture_out_of_example_settings) | Move test fixture out of example settings | Done |
| [`DONE-013-0.0.4`](#real_m2m_coverage) | Real M2M coverage | Done |
| [`DONE-012-0.0.4`](#004_version_and_release_alignment) | 0.0.4 version and release alignment | Done |
| [`DONE-011-0.0.4`](#stale_placeholder_cleanup) | Stale placeholder cleanup | Done |
| [`DONE-010-0.0.4`](#004_foundation_slice_definition_order_independence) | 0.0.4 foundation slice (definition-order independence) | Done |
| [`DONE-009-0.0.4`](#rich_schema_architecture) | Rich schema architecture | Done |
| [`DONE-008-0.0.4`](#definition_order_independence_design) | Definition-order independence design | Done |
| [`DONE-007-0.0.4`](#004_onboarding_docs_and_spec_consolidation) | 0.0.4 onboarding docs and spec consolidation | Done |
| [`DONE-006-0.0.3`](#documentationstatus_positioning_for_shipped_layer_2) | Documentation/status positioning for shipped Layer 2 | Done |
| [`DONE-005-0.0.3`](#djangotype_contract_and_boundary) | DjangoType contract and boundary | Done |
| [`DONE-004-0.0.3`](#optimizer_beyond_slices_b1_b8) | Optimizer beyond slices B1-B8 | Done |
| [`DONE-003-0.0.2`](#optimizer_o4_nested_prefetch_chains) | Optimizer O4 nested prefetch chains | Done |
| [`DONE-002-0.0.2`](#optimizer_o1_o6_foundation) | Optimizer O1-O6 foundation | Done |
| [`DONE-001-0.0.1`](#djangotype_core_foundation) | DjangoType core foundation | Done |

## In progress

Cards actively being implemented — WIP is kept small (typically one or two) so work finishes before new work starts.

<a id="upstream_parity_gap_closure"></a>
### [WIP-ALPHA-051-0.0.15 - Upstream parity-gap closure](KANBAN.html#upstream_parity_gap_closure)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: WIP
- Relative size: M
- Labels: `mutations`, `public-api`, `scalars`, `types`
- Spec: [spec-051-parity_gap_closure-0_0_15.md](docs/spec-051-parity_gap_closure-0_0_15.md)

#### Planning note

The six code gaps left by the `0.1.0` parity audit after everything homeable was homed onto existing cards. All six are small, test-pinned items against a named upstream surface; none is a new subsystem. They are grouped because they share a charter — close every remaining build-side parity delta before the beta cut — not because they share a seam.

#### Scope

- A `through=` class-creation guard: reject at type creation a `through=`-declared M2M whose through model carries required extra columns (non-null, no default, beyond the two FKs) wherever the relation is writable through generated inputs, with a [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) naming the through model and the offending columns — today `django_strawberry_framework/mutations/resolvers.py::_assign_m2m` is a plain `.set()` and neither `django_strawberry_framework/mutations/inputs.py` nor `django_strawberry_framework/utils/relations.py` guards the declaration, so the failure happens at runtime inside Django's `.set()`, outside the `FieldError` envelope. Fail-loud is package doctrine; this guard is also what makes the `through_defaults` refusal homed on TODO-BETA-071-0.1.8 safe.
- `GeneratedField` support: resolve type and nullability from the field's `output_field` in `django_strawberry_framework/types/converters.py::convert_field_output` (the upstream answer — 🍓 `strawberry_django/fields/types.py` #"GeneratedField" — and a direct fit for our converter table), and exclude the column from generated write inputs since it is database-computed. Today a Django 5.0+ `GeneratedField` reached through `Meta.fields = "__all__"` raises `ConfigurationError "Unsupported Django field type 'GeneratedField'"` at type creation, [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) is the only escape, and nothing documents it — a migrating consumer with any generated column cannot declare the type at all.
- Model `help_text` as the SDL field description: thread the model column's `help_text` into the generated field's GraphQL description. Today no model-column path exists — the only `help_text` handling is on the DRF serializer-input side (`django_strawberry_framework/rest_framework/serializer_converter.py`) and `django_strawberry_framework/types/base.py` synthesizes bare annotations — so a ⚛️ migrant takes a silent whole-schema SDL regression on every documented model. The spec decides always-on (⚛️ threads `str(field.help_text)` unconditionally) versus opt-in (🍓 gates it behind `FIELD_DESCRIPTION_FROM_HELP_TEXT`); an explicit consumer-declared description wins over `help_text` either way.
- `django-choices-field` enum reuse: when a `TextChoicesField` / `IntegerChoicesField` declares a `choices_enum`, reuse the consumer's own enum instead of silently minting a second one from the raw choices (🍓 parity: `strawberry_django/fields/types.py` #"TextChoicesField"). Soft-dependency detection only — no hard dependency on `django-choices-field`; the `(model, field)` enum-reuse cache contract is unchanged. Coordinate with TODO-BETA-065-0.1.4, which owns `convert_choices_to_enum()` naming and that cache on the far side of the beta cut.
- `FieldError` keying: unify the key space of `FieldError.field` across every flavor — validator-origin errors (`full_clean()`, `form.errors`, a serializer save-time Django `ValidationError`) emit the model, form or serializer field name (`django_strawberry_framework/utils/errors.py::validation_error_to_field_errors` is an identity pass-through), relation-decode errors emit the GraphQL input name (`::relation_field_error`), and the serializer flavor re-keys recursively (`django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors`) — an FK suffix (`category` / `categoryId`) and a `Meta.input_class` rename have no casing relation, so the fix is a key map, not a casing function; pin the chosen keying with live tests including a multi-word snake_case field, which no test covers today (the divergence is invisible to the suite). ⚛️ context: `graphene_django/settings.py` #"CAMELCASE_ERRORS", default on, in the exact `ErrorType` our `FieldError` mirrors.
- Connection pagination rejections carry an audited `extensions.code`: every `django_strawberry_framework/utils/connections.py::PaginationArgumentError` carries `PAGINATION_INVALID` (`django_strawberry_framework/utils/errors.py::PAGINATION_INVALID_ERROR_CODE`), so a migrant's first contact reads as a policy. This discharges TODO-ALPHA-057-0.1.0's open question.

#### Definition of done

- [ ] A `through=` M2M with required extra columns fails at type creation with a `ConfigurationError` naming the through model and columns; an auto-created or fully-defaulted through model is unaffected; live coverage proves the runtime `.set()` path is never reached.
- [ ] A `GeneratedField` reached through `Meta.fields = "__all__"` or an explicit field list converts via its `output_field` type and nullability, is absent from generated write inputs, and is live-probed end-to-end.
- [ ] Model `help_text` appears as the SDL field description per the spec's on-by-default-or-opt-in decision; an explicit description wins; SDL snapshot coverage pins it.
- [ ] A `TextChoicesField` / `IntegerChoicesField` with a declared `choices_enum` publishes the consumer's enum (one enum type, not two); absence of `django-choices-field` changes nothing.
- [ ] `FieldError.field` keying is uniform across model, relation-decode, and serializer flavors; a live test pins a multi-word snake_case field on each flavor with a stock fakeshop shape (model `houseCode`, plain form `statusKey`, serializer `shelfCode`); `register` (the stock user model has no multi-word required field) and `ModelForm` (no stock form can fail validation on a multi-word field) are pinned at package tier.
- [x] Connection pagination rejections ([`PaginationArgumentError`](docs/GLOSSARY.md#paginationargumenterror)) carry the audited `extensions.code` `PAGINATION_INVALID` (`django_strawberry_framework/utils/errors.py::PAGINATION_INVALID_ERROR_CODE`); TODO-ALPHA-057-0.1.0's open question is closed against this card.
- [ ] TODO-BETA-071-0.1.8's upstream-settings disposition table gains its `CAMELCASE_ERRORS` row stating the keying story that ships (no toggle: keys are always the input name; `__all__` kept, not graphene's `_All__`) — ⚛️'s key is a toggle (`graphene_django/types.py` camelizes only when true, default on) and no equivalent knob exists here, so the row is owed under any outcome.
- [ ] TODO-ALPHA-053-0.0.15's Slice 5 joint-cut sentence and its GLOSSARY-flip DoD were amended for every card on the line, and the dependency edge sequencing it behind this card was added, at the 2026-08-29 board review; verify both still hold at wrap.
- [ ] Docs fold-in and card wrap: GLOSSARY terms via the DB, TREE regenerated, card flipped Done, KANBAN regenerated, `import_spec_terms` green.
- [ ] Full suite green under `fail_under = 100`; live-first placement respected. No version triplet, GLOSSARY status flip or CHANGELOG entry — all three ride TODO-ALPHA-053-0.0.15's joint `0.0.15` cut, which lands last on this line.

#### Files likely touched

- `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/utils/relations.py`
- `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/auth/mutations.py`
- `django_strawberry_framework/connection.py` and `django_strawberry_framework/error_policy.py` (argument-rejection surfacing: `connection.py` already raises `GraphQLError` for `first` + `last`, and the masking rule whose untouched branch the rejections must land in lives in `error_policy.py`)
- Mirrored `tests/` modules plus live coverage under `examples/fakeshop/test_query/`

#### Verified in upstream

- 🍓 `strawberry_django/fields/types.py` #"GeneratedField" resolves type and nullability from `output_field`.
- 🍓 `strawberry_django/fields/types.py` #"TextChoicesField" reuses the consumer's `choices_enum`.
- ⚛️ threads `str(field.help_text)` into every converter unconditionally; 🍓 ships the same behind `strawberry_django/settings.py` #"FIELD_DESCRIPTION_FROM_HELP_TEXT".
- ⚛️ `graphene_django/settings.py` #"CAMELCASE_ERRORS" (default on) camelizes `ErrorType` keys in `graphene_django/types.py`.

#### Why it matters

- The beta line is defined as feature parity with both upstreams. These six are the entire remaining build-side delta after the `0.1.0` parity audit homed everything else: two type-creation failures a migrant cannot work around (`through=`, `GeneratedField`), a whole-schema SDL regression (`help_text`), a duplicate-enum surprise, a mixed error wire format no test can see, and rejections that read as bugs. Closing them before `0.1.0` is what makes the parity claim on TODO-ALPHA-057-0.1.0 true rather than asserted.

#### Dependencies

- Nothing blocks this card. The sequencing runs the other way: TODO-ALPHA-053-0.0.15's four-DRY-axes file list covers `mutations/{sets,inputs,resolvers,permissions}.py`, `rest_framework/*`, `utils/*`, `connection.py` and `types/base.py` — every file this card touches except `types/converters.py` — so that card must be sequenced behind this one, exactly as it is already sequenced behind the debug extraction on the same line. That dependency edge and note are owed on that card, not this one.
- This card lands first on the shared `0.0.15` line; the debug extraction and the DRY squeeze follow, and the DRY squeeze still lands last and owns the joint cut.

#### Card references

- Related: Its masked-rejections open question is discharged by this card. -> `TODO-ALPHA-057-0.1.0` - Beta release (cleanup, verification, alpha → beta)
- Related: Owed the `CAMELCASE_ERRORS` row on its upstream-settings disposition table, and already carries the `through_defaults` refusal this card's `through=` guard is what makes safe. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides
- Related: Shares every file in this card's Files-likely-touched list except `types/converters.py`, so it is sequenced behind this card the same way it is sequenced behind the debug extraction. -> `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze
- Related: Owns `convert_choices_to_enum()` naming and the enum-reuse cache on the far side of the beta cut; this card lands the enum-reuse behaviour that card then names. -> `TODO-BETA-065-0.1.4` - Stable choice enum naming override

<a id="extract_djangodebugextension_into_the_standalone_django_strawberry_debug_package"></a>
### [TODO-ALPHA-052-0.0.15 - Extract DjangoDebugExtension into the standalone django-strawberry-debug package](KANBAN.html#extract_djangodebugextension_into_the_standalone_django_strawberry_debug_package)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `internal`
- Spec: [spec-052-debug_extraction-0_0_15.md](docs/SPECS/spec-052-debug_extraction-0_0_15.md)

#### Dependencies

- `DONE-044-0.0.14` - Response-extensions debug middleware

#### Scope

- Slice 1 - the new package: brand-new standalone repo unaxy/django-strawberry-debug; pyproject (deps Django>=5.2 + strawberry-graphql>=0.316.0, NO dependency on django-strawberry-framework), src layout, MIT, README ported from spec-044's user-facing API (posture, wire contract, graphene narrowing table, async boundary); debug.py moved VERBATIM except the single logger swap (logging.getLogger("django_strawberry_debug")); the 1,019-line suite moved onto a self-contained harness; CI matrix green; 0.1.0 published to PyPI.
- Slice 2 - the framework seam: delete extensions/debug.py + tests/extensions/test_debug.py; rewrite extensions/__init__.py as the require_optional_module-guarded PEP 562 lazy re-export; add [project.optional-dependencies] debug = ["django-strawberry-debug>=0.1.0"] (+ dev-group pin); absence test on the None-sentinel shape; ONE live-tier re-export + optimizer-composability proof; the probe scaffold slims to that seam test; fail_under = 100 re-verified.
- Slice 3 - docs fold-in (GLOSSARY via DB, README, TREE regen, dry-file doc retired) and card wrap; the 0.0.15 version-triplet cut and CHANGELOG entry belong to the boundary-hardening/DRY-squeeze card, which shares this patch line and lands last.

#### Definition of done

- [ ] django-strawberry-debug 0.1.0 on PyPI: verbatim-moved debug.py (logger swap only), moved suite green on its own harness, CI matrix green, README carrying posture + wire contract + async boundary.
- [ ] This repo: extensions/debug.py and its package-tier suite deleted; extensions/__init__.py is the guarded lazy re-export; [debug] extra added; absence sentinel test + one live seam/composability test in place; probe scaffold slimmed.
- [ ] pip install django-strawberry-framework[debug] resolves in an isolated venv and `from django_strawberry_framework.extensions import DjangoDebugExtension` works; with the extra absent, import-innocence + the install-hint error hold.
- [ ] Full suite green under fail_under = 100 after the deletion.
- [ ] Docs fold-in, card flipped Done, KANBAN regenerated, import_spec_terms green - no version triplet, GLOSSARY status flip or CHANGELOG entry, all of which ride the boundary-hardening/DRY-squeeze card's joint 0.0.15 cut.

#### Files likely touched

- New repo (unaxy/django-strawberry-debug): pyproject.toml, src/django_strawberry_debug/{__init__,debug}.py, tests/, CI workflows, README, CHANGELOG
- This repo: `django_strawberry_framework/extensions/{__init__,debug}.py`, `tests/extensions/test_debug.py`, `tests/_soft_dependency.py`, `examples/fakeshop/test_query/test_debug_extension_api.py`, `pyproject.toml` (extras + dev group), `uv.lock`
- Slice 3 docs: `docs/GLOSSARY.md` (DB + re-render), `README.md`, `docs/README.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`, KANBAN regen

#### Architectural posture

- Extraction, not the in-tree leaf: the split test applied to opposite facts. The optimizer split was rejected on bidirectional fusion; this module has zero reverse coupling, one trivial forward import, and a framework-independent audience - the one place extraction sheds weight without cutting a live seam.
- The name django-strawberry-debug is EARNED by generality (maintainer's rule: the generic family name only if it works beyond this framework; the import-surface proof settles it). Zero behavior change: the wire contract, capture mechanics, and developer-only posture move verbatim - the logger swap is the only code delta.
- The per-operation extension-isolation floor (strawberry-graphql>=0.316.0, subsumed by the framework's >=0.322.2) STAYS in the framework: per-operation extension isolation is a release-wide engine-lifecycle fix affecting every consumer schema, debug enabled or not. It was never debug-only; it does not travel with the feature.
- The shipped import path survives byte-for-byte via the guarded re-export - the extraction is invisible to any 0.0.14 consumer who installs the extra. No deprecation machinery at 0.0.x.

#### Why it matters

- A dead-weight review of the package found extensions/debug.py ([DjangoDebugExtension](docs/GLOSSARY.md#djangodebugextension), card 044's feature) is the one genuinely extractable module: its import surface is stdlib + Django + graphql-core + Strawberry plus exactly one package symbol (the root logger), nothing in the package imports it back, and it works against ANY strawberry-graphql + Django schema - no [DjangoType](docs/GLOSSARY.md#djangotype), registry, or optimizer required.
- Carrying it in-tree costs this distribution ~1,900 lines (472 impl + ~1,375 tests) for a feature with no in-package consumer, while a standalone package serves a real audience beyond the framework. The same evidence standard that rejected the optimizer split (bidirectional fusion) endorses this one (zero coupling).
- Sequenced BEFORE the boundary+DRY card deliberately: extraction shrinks that card's surface - extensions/ becomes a soft-dependency leaf (the rest_framework/ shape) before the import-linter contracts are authored, and the extras block gains its first member for the DRY card's four to join.

#### Dependencies

- Sequenced behind DONE-044-0.0.14: the extension must SHIP at 0.0.14 before it is extracted (extracting an unreleased feature would rewrite card 044 mid-flight). The whole card - not just the cut - waits for the 0.0.14 release. Within the card, Slice 2 is gated on Slice 1's published 0.1.0 artifact.

#### Card references

- Dependency: `DONE-044-0.0.14` - Response-extensions debug middleware

<a id="boundary_hardening_and_system_wide_dry_squeeze"></a>
### [TODO-ALPHA-053-0.0.15 - Boundary hardening and system-wide DRY squeeze](KANBAN.html#boundary_hardening_and_system_wide_dry_squeeze)

- Priority: High
- Status: To Do
- Relative size: XL
- Labels: `internal`
- Spec: [spec-053-boundary_dry_squeeze-0_0_15.md](docs/SPECS/spec-053-boundary_dry_squeeze-0_0_15.md)

#### Dependencies

- `DONE-044-0.0.14` - Response-extensions debug middleware
- `DONE-050-0.0.15` - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`
- `WIP-ALPHA-051-0.0.15` - Upstream parity-gap closure
- `TODO-ALPHA-052-0.0.15` - Extract DjangoDebugExtension into the standalone django-strawberry-debug package

#### Scope

- WP-A boundary hardening: promote the optimizer's inward-facing API (kill cross-boundary `_context` imports), enforce the dependency architecture with `import-linter` contracts in CI/pre-commit, declare packaging extras (`drf`, `channels`, `keyset-encryption`, `debug-toolbar`) over the existing soft-dependency seams.
- WP-B mechanical DRY batch (~450-550 lines): query-side delegate absorption into `sets_mixins.py`, write-side `PermissionClassesMixin` + metaclass merge, inputs micro-hoists, resolvers micro batch, root/optimizer/types small batch.
- WP-C structural DRY batch (~500-600 lines): fold `_run_delete` and the plain-form pipeline onto the shared write skeleton, filter converter/normalizer dispatch table, `install_input_namespace()`, bind-drain merge, connection dispatch tails, `slot_child_selections()`, `iter_relation_path()`, budgeted-walk primitive, column-backed conversion sharing (mutations+forms only), finalizer error formatters, underscore alias deletion, `editable_input_fields` onto `resolve_effective_fields`.
- WP-D contract-level DRY (~150 lines + doc debt): single-window planner scheme through `_divergent_key_windows`, walker `_resolve_field_map` dual-contract retirement (FieldMeta fallback), model relation decoder over the shared spine.
- Slice 5: docs fold-in, the joint `0.0.15` release cut (shared with the other three `0.0.15` cards; this card lands last so it owns the cut, and verifies the version triplet, which already reads `0.0.15`), CHANGELOG entry, card wrap.
- Widen `views.py::_canonicalizes_to_utf8` to catch `ValueError` and `UnicodeEncodeError` alongside `LookupError`. Pre-existing, fail-loud and not reachable from the wire, which is why it was left; a codec whose name canonicalizes but whose lookup raises escapes as an unrelated 500.
- A shared "is this one of our views?" recognizer with `middleware/debug_toolbar.py` is now a decidable question: the constraint that forced `middleware/request_body.py` to recognize by marker attribute (it must not import `views.py`) was removed when the ordering marks moved to `_boundary_ordering.py`. `debug_toolbar` recognizes a package view by class through an *upstream* `BaseView` import, so a narrower shared recognition needs no `views.py` import either. Revisit only when a third middleware needs the same recognition, or when two need to agree about one callback - not as a DRY sweep for its own sake.
- `middleware/request_body.py::_package_view_instance`'s docstring scopes its absolute to the outcomes the recognition decides: `None` means "not a callback this middleware can run a boundary for", a boundary the recognition accepted that raises anything but `HTTPException` leaves the hook uncaught, and no guard sits across the body cap's own errors.
- `docs/SPECS/spec-046-transport_security-0_0_14.md` Decision 7 and its `## Edge cases` capability bullet name every call the size probe guards (`seekable()`, the `tell()` that reads the starting position, the seek to the end, the restoring seek and the `tell()` that verifies it) and state that an answer that is not a built-in `int` is never used in arithmetic.
- `django_strawberry_framework/consumers.py::send_revalidated_operation_frame`'s docstring calls the derived adapter a thin delegation, with no statement count to drift from `_RevocationGatedWebSocketAdapter.send_json`'s body.
- `django_strawberry_framework/consumers.py::DjangoWebSocketHostValidator` logs a WebSocket `Host` denial on `django.security.DisallowedHost` at `ERROR` with the exception attached, the logger Django's HTTP handler uses for the same refusal; the wire is unchanged, and spec-046 records the logger.
- `django_strawberry_framework/conf.py #"POST-scoped"` states that the `MAX_REQUEST_BODY_BYTES` multipart carve-out is POST-scoped (`django_strawberry_framework/views.py::_is_multipart_form_post`): a multipart content type on any other method is counted like any other body.
- `auth/mutations.py` carries repeated literals - `password` seven times, `register` four, `current_user` three. Pre-existing rather than introduced by the transport work, which is why it was never folded into a security pass.
- spec-046's DRY `parse_json` bullet scopes the `UnicodeDecodeError` translation to the upstream-mounted path and states that `django_strawberry_framework/_strawberry_patches.py::_validate_upstream_shape` decides whether the patch installs at all, for every mount.
- `_optimizer_field_map` has zero occurrences in live code: the three `tests/optimizer/test_field_meta.py` test names and the `scripts/review_inspect.py` token are gone, and the walker reads `DjangoTypeDefinition.field_map` through `optimizer/walker.py::_resolve_field_map`. The prose survivals in `CHANGELOG.md` / `KANBAN.md` / `spec-010` / `spec-016` are correct as history and stay.
- Send a rejected subscription the `RESOURCE_LIMIT_EXCEEDED` envelope on both WebSocket protocols. Enforcement is not the gap: a subscription enters the extension runner's `operation()` and `executing()` exactly as a query does, so the document scan and the value walk both fire and a violating subscription IS refused. Upstream's non-streaming path converts a pre-execution exception into an `errors` entry and its streaming path does not, so the client sees a `complete` close instead of the code. Write the fix against that broad-versus-narrow `except` asymmetry, pin no private upstream symbol, and re-measure the asymmetry across the whole open-ended `strawberry-graphql>=0.322.2` range rather than the installed wheel (spec-047 Decision 13).
- Charge upload bytes before Django's upload handlers stream the body, through a package-owned upload handler or streaming body reader, so the upload bounds stop being post-materialization. Django has already streamed a multipart body by the time coerced values exist, so the seam sits beside the request-body cap rather than inside the value walker - which is why spec-047 narrows its own goal to "before any resolver, serializer, validator or storage backend touches the files" (spec-047 Decision 13).
- Refuse an oversized numeric literal as a typed resource rejection carrying `RESOURCE_LIMIT_EXCEEDED` rather than as the malformed-input failure CPython's `sys.get_int_max_str_digits` raises during JSON parsing or literal coercion. The request is already refused; only the envelope is wrong. A configured bound means a pre-coercion scan of the raw variables JSON, which is the body cap's layer rather than the walker's (spec-047 Decision 13).
- `optimizer/walker.py::_record_relation_access` must run before the FK-id-elision short-circuit in `optimizer/walker.py::_plan_select_relation` - it appends the FK `attname` the elided resolver reads (`types/resolvers.py::_build_fk_id_stub`), so reversing the order silently reintroduces the N+1 the elision exists to remove. The invariant is stated in the helper's docstring and in `spec-003-optimizer_nested_prefetch_chains-0_0_2.md`'s same-query-recursion contract, but no test or assertion pins the order. Add a guard: a call-site assertion or a walker test that fails when the two statements are swapped.
- `django_strawberry_framework/optimizer/plans.py::_prefetch_lookup_paths` recurses through nested `Prefetch` queryset lookups with no depth cap, and its docstring records why the asymmetry with `django_strawberry_framework/optimizer/plans.py::runtime_path_from_path` (bounded at `_MAX_PATH_DEPTH`) is deliberate: its input is the walker's own nested `Prefetch` chain, one level per selected relation, plus the lookups a consumer `get_queryset` attached, acyclic by construction and no deeper than the selection the walker already recursed through; the sibling's cap exists only to turn a cyclic or corrupt `prev` chain into a loud failure.
- `django_strawberry_framework/exceptions.py::ConfigurationError`'s docstring matches the runtime: registering several [`DjangoType`](docs/GLOSSARY.md#djangotype) subclasses against one model is documented as supported, and only a second [`Meta.primary`](docs/GLOSSARY.md#metaprimary) claim, a `primary` flag flipped on re-register, or finalization-time ambiguity (`django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity`) raises. Its deferred-key example says "feature", matching the runtime message.
- `django_strawberry_framework/types/base.py::_format_unknown_fields_error`'s docstring no longer enumerates its callers: it says the message serves every validator that points at a typo in a `Meta` key naming model fields, with `attr` naming the offending key, so a new caller cannot make it stale.
- `tests/types/test_base.py::test_meta_exclude_filters_concrete_fields` carries a comment naming `convert_relation`, a symbol with zero occurrences in `django_strawberry_framework/` - relation annotations resolve through `types/converters.py::resolved_relation_annotation`. Fold into whichever WP batch legitimately opens `test_base.py`; it is the same shape as the `_optimizer_field_map` item above and takes the same boundary - the present-tense survivals in shipped specs (`spec-009`, `spec-010` and `spec-019` all still name `convert_relation`; `spec-008` did until its 2026-08-14 residual reconciliation removed the last one, and it now greps 0, so do not re-add it on a later sweep) are correct as history and are not in the sweep. The same file carries a second, unrelated stale reference worth fixing in the same opening: `::test_meta_rejects_each_deferred_key`'s docstring reads "must raise until the spec that owns it ships", the last occurrence anywhere in the tree of the deferred-key vocabulary commit `83c25963` retired in favour of "feature". The package-side half of that correction landed at `65fd201e`, which is what leaves this one exposed - `grep -rn 'spec that owns' django_strawberry_framework/` now returns nothing while this line survives.
- Discharged: both dynamic-set factories were deleted - `get_orderset_class` / `get_filterset_class`, their caches, and the shared Layer-6 dynamic-set machinery in `utils/inputs.py` they alone reached. The auto-generation surface they were built ahead of is `spec-027`'s deferred non-goal, and GOAL.md's `astronomy` app declares every sidecar explicitly. The GLOSSARY [`OrderSet`](docs/GLOSSARY.md#orderset) entry's closing clause ("so no dynamic order factory is shipped") is accurate again, and `spec-027`'s auto-generation scrub (the beta-release card's deferral sweep) can state "no auto-generation ships" flatly.
- `django_strawberry_framework/orders/inputs.py` carries the retired reserved-slot rationale a third and fourth time in one module: `::_build_input_fields #"reserved -- see"` and `::_build_input_fields._leaf_of #"is a future-extension"`. Neither is false today - the first defers to `convert_order_field_to_input_annotation`'s docstring and the second describes a converter affordance that genuinely is unused - but they are the same sentence's third and fourth instances in one file, which is this card's DRY subject. The first two instances were rewritten at `f02dfda7` (the spec-028 DISTINCT ON retirement) and now read "kept for shape-symmetry"; these two were outside that commit's scope and still carry the older wording, so the module now states the same idea two different ways. Fold into whichever WP batch opens `orders/inputs.py`. Measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog item 19), re-verified 2026-08-16.
- Do NOT sweep the `docs/spec-NNN-...` spellings in `.py` files: every one is a decided non-edit, and an undifferentiated sweep breaks passing tests and destroys deliberate examples. `scripts/check_spec_glossary.py`'s 4 are usage examples in a docstring whose own prose then discusses what an archived spec keeps, so the pre-archive form is the point; `scripts/check_citations.py`'s 4 are the in-flight spec globs it resolves against (`docs/spec-*.md` beside `docs/SPECS/`); `examples/fakeshop/test_query/test_glossary_api.py`'s 2 (`spec_path=` and the `specPath: { exact: ... }` assertion), `examples/fakeshop/apps/glossary/tests/test_import_spec_terms.py`'s 3 and `tests/test_check_citations.py`'s 4 are fixture DATA the tests create and query; `tests/test_ci_governance.py`'s 2 are the message format the governance test reports. The edit half is DISCHARGED: the six test-module docstrings that genuinely made a stale path claim - `tests/test_connection.py`, `tests/test_list_field.py`, `tests/test_relay_node_field.py`, `tests/test_relay_connection.py`, `tests/optimizer/test_multi_db.py`, `tests/testing/test_relay.py` - all read `docs/SPECS/` (verified 2026-08-27: every rewritten target EXISTS at `docs/SPECS/` and is MISSING at `docs/`). The board-DB half is likewise discharged: `CardItem.text` carries 0 `docs/spec-NNN` tokens.
- `django_strawberry_framework/utils/inputs.py::promote_set_meta_fields #"source).fields = fields"` writes the `filter_fields` alias onto the **consumer's** `Meta` class in place (`django_strawberry_framework/filters/sets.py::FilterSetMetaclass` calls it from `__new__`), so a consumer `Meta` shared across two FilterSets has the first one's aliasing observed by the second; presence is read with `hasattr`, so a `Meta` that inherits `fields` skips the alias, the contract `django_strawberry_framework/utils/inputs.py::resolve_set_meta_fields` documents. Shipped and tested; recorded as a design question, not a defect claim - the fix direction (copy the Meta or resolve the alias into the new class's attrs rather than writing to the consumer's object) is a contract-level call that belongs with this card's boundary work.
- `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation`'s docstring points its end-to-end coverage at `examples/fakeshop/test_query/test_library_api.py::test_relay_genre_type_emits_node_interface_and_global_id_live` and `::test_mixed_relay_and_non_relay_no_interface_bleed_live`, the two live tests that exercise the id-suppression path.
- Decision 7's relation-traversal invariant is pinned against a non-Relay target at the package tier: `tests/optimizer/test_walker.py::test_plan_relay_target_relation_planning_matches_non_relay_target` builds two target types differing only in [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) and asserts equal `select_related`, `prefetch_related` and `only()` shapes, FK-id elisions and resolver keys. The live tier cannot carry the comparison because every `products` type declares a `get_queryset` and takes the windowed `Prefetch` downgrade.
- The `_resolve_field_map` dual contract is retired by deletion, not re-pointed: `optimizer/walker.py::_resolve_field_map` carries no `DUAL CONTRACT` paragraph, both of its paths stamp `FieldMeta` (the unregistered-model fallback through `FieldMeta.from_django_field`) so callers read every attribute directly and the `getattr(..., default)` read rule is gone with it, `types/resolvers.py::_field_meta_for_resolver` shares the same policy, and `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` #"Bounded exceptions to the single-source rule" keeps the one test-double exception and states that unregistered-model planning is not one. The rejected alternative (a walker-side `FieldMeta` so the resolver-side fallbacks can go) stays rejected in `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`.
- The three rule-27 source-reference spellings left by the spec-016 consolidation are gone. `django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation` cites `django_strawberry_framework/utils/relations.py::instance_accessor`; `django_strawberry_framework/optimizer/field_meta.py::_target_pk_name` spells `types/resolvers.py::_field_meta_for_resolver` the way `::_from_field_shape` in the same module does; and `tests/test_registry.py` no longer names the deleted `_record_pending_relation` helper. The present-tense survivals in shipped specs and in `CHANGELOG.md` are correct as history.
- The [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) ordering text states the [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) pk tiebreaker as conditional at every site: `docs/SPECS/spec-020-list_field-0_0_7.md` `### Decision 8`, the `Ordering contract` passage of `django_strawberry_framework/list_field.py::DjangoListField`'s docstring, and `docs/GLOSSARY.md`'s `DjangoListField` entry at #"**Ordering.**" say the pk is appended only when the order does not already end in a unique column, and that a keyset ([`Meta.cursor_field`](docs/GLOSSARY.md#metacursor_field)) connection appends none, matching `django_strawberry_framework/optimizer/plans.py::deterministic_order`. The `orderBy` recourse is accurate: spec-050 gives every `DjangoListField` published `offset` / `limit` / `orderBy` arguments.
- `django_strawberry_framework/list_field.py`'s comment above the consumer-wrapper branch no longer characterizes `is_async_callable`; it points at `utils/typing.py::is_async_callable`, whose docstring states the full contract (`functools.partial` and raw `staticmethod` layers peeled to any nesting, metaclass `async def __call__` read).
- `docs/GLOSSARY.md`'s [`SyncMisuseError`](docs/GLOSSARY.md#syncmisuseerror) entry (anchor `#syncmisuseerror`) names both `DjangoListField` raise paths: the sync default resolver among the surfaces where `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` raises on a coroutine-returning `get_queryset`, and `django_strawberry_framework/utils/querysets.py::reject_async_iterable_in_sync_context`, which raises the same error when a `DjangoListField` or `DjangoConnectionField` resolver returns an async-only iterable under synchronous execution.
- No build-phase name survives in shipped package source: the lead comment on `django_strawberry_framework/types/base.py` `_RELAY_NODE_GATE_INHERIT_TAIL` states the invariant (byte-identical at every compose site) without the pass name. `filters/sets.py` #"TODO(spec-060 Slice 1)" is a live staged-slice anchor, which AGENTS.md requires to name its doc and slice, and is not part of this vocabulary.
- No `workstream [A-D]` token survives in live `.py`: 0 occurrences across `django_strawberry_framework/`, `tests/` and `examples/`. Each former site states its invariant by content, the spec-033 partition-marker and conditional `_dst_total_count` sites under their real names and the walker's under its upstream ticket (`optimizer/walker.py` #"the strawberry-django #697 bug class").
- `tests/test_ci_governance.py`'s first docstring line names every corpus the module governs (CI workflows, Dependabot, install floors and first-party source), and `docs/TREE.md` renders that line under both render roots.
- Every multi-line schema construction example in package docstrings registers the package scalars with `config=strawberry_config()`: `optimizer/extension.py` (module docstring and the singleton-in-a-factory method docstring) and `extensions/debug.py` (module docstring) build `DjangoSchema(..., config=strawberry_config(), ...)`, the canonical form in `docs/README.md`, and `extensions/resource_policy.py::DjangoResourcePolicyExtension` carries it on both its `DjangoSchema(...)` example and the plain-schema fallback. Count on `config=strawberry_config`, never on `config=strawberry_config()`: the empty parens miss `extra_scalar_map=` call sites.
- Discharged: the window-partition shim in `optimizer/plans.py` was deleted with its six-row test family. Production derives the relation partition from the join descriptor (`classify_relation_join(...).partition_expr`), and `exceptions.py` no longer documents the `OptimizerError` only the shim could raise; the shared-child walker test reads `.partition_expr`.
- The `to_attr` grammar lives in `django_strawberry_framework/utils/connections.py::relation_connection_to_attr`, the neutral, cycle-safe module spec-033 Decision 11 created so the plan side and the resolve side share one source. `django_strawberry_framework/connection.py` imports it from there and `_extend_only_projection` from `django_strawberry_framework/optimizer/plans.py::_extend_only_projection`, so the resolver no longer imports from `optimizer/nested_planner.py`. A placement change with no behavior change; a cross-module `_`-private import is house convention, so the sibling `_active_strategy` import in `optimizer/extension.py` is not a defect.
- The `except (ValueError, TypeError, AttributeError, KeyError, IndexError)` tuple has zero occurrences in the package: `connection.py` and `auth/mutations.py` no longer catch it, so there is no population for a shared `_COERCION_ERRORS` constant. `utils/sessions.py` keeps its own six-member tuple (it adds `ImportError`) at its single site.
- The `_optimizer_runtime_prefixes` attribute name is one constant, `django_strawberry_framework/optimizer/selections.py::RUNTIME_PREFIXES_ATTR`: `django_strawberry_framework/optimizer/selections.py::with_runtime_prefix` writes through it, and `django_strawberry_framework/optimizer/walker.py::_selection_runtime_prefixes`, `django_strawberry_framework/optimizer/walker.py::_merge_runtime_prefixes` and `django_strawberry_framework/optimizer/walker.py::_merge_aliased_selections` read and write through it.
- `django_strawberry_framework/permissions.py::_is_unsupported_forward_edge` reads `field.is_relation` directly, like the two predicates beside it, so a field shape that cannot answer raises rather than being classified a non-relation. Its sole caller, `django_strawberry_framework/permissions.py::_edge_plan`, feeds it only `model._meta.get_fields()` members, all of which define `is_relation`.
- Discharged by path (b): both cascade-edge helpers in `permissions.py` were deleted, and the test sites read `_edge_plan(model).cascadable` directly, as every production path (`_validate_fields`, the preflight, `_walk`) already does.
- The live matching-type relation-planning anchor in `examples/fakeshop/test_query/test_library_api.py` #"TODO(BACKLOG polymorphic_interface_connections" carries the same head as its four siblings, and no `TODO(spec-035` remains in the tree. The anchor stays: it is the live-coverage half of the `BACKLOG.md` `polymorphic_interface_connections` R1 test plan.
- `FieldError` and `NON_FIELD_ERROR_KEY` are defined in `django_strawberry_framework/utils/errors.py::FieldError`'s module beside the shared write-error constructors, so `utils/` imports nothing from `mutations/`. `django_strawberry_framework/mutations/inputs.py` re-exports both, and the root `FieldError` export is unchanged.
- **Contract-level, and it is WP-B's `sets_mixins.py` question asked on the write side, settled:** the cross-flavor write substrate the three write flavors import lives in `django_strawberry_framework/write_mixins.py`, the write-side twin of `django_strawberry_framework/sets_mixins.py` and the destination spec-036 Decision 4 predicted; `django_strawberry_framework/mutations/sets.py` keeps only [`DjangoMutation`](docs/GLOSSARY.md#djangomutation)'s own class, metaclass, model ledger and bind.
- No stranded review-round label survives in this card's WP package modules: `optimizer/nested_planner.py` no longer cites `the P2-3 defect` and `orders/sets.py` no longer cites `spec-030-connection_field-0_0_9 P1-B`; each comment states its invariant by content.
- **Consolidate the `SerializerMutation ` message prefix, and fold the fourth provisional-name derivation into the same edit.** Measured 2026-09-10 by the spec-039 residual cycle in Python over the git-tracked package tree, counting occurrences and not lines: **73** occurrences of the source text `"SerializerMutation ` across five modules - `django_strawberry_framework/rest_framework/resolvers.py` 43, `django_strawberry_framework/rest_framework/inputs.py` 14, `django_strawberry_framework/rest_framework/sets.py` 14, `django_strawberry_framework/rest_framework/__init__.py` 1 (the djangorestframework-absent install hint) and `django_strawberry_framework/utils/inputs.py` 1 (a docstring naming the label as a `noun` parameter value, so the parameterized substrate this consolidation would target already exists) - of which **59** are `f"SerializerMutation {`, at 40 / 5 / 14 / 0 / 0. **State the five-module population:** an earlier reading of 71 globbed only the three `rest_framework/` modules and is the same too-narrow-population error this card's `"DjangoMutation"` sibling bullet warns about. A fourth spelling sits outside that literal - `django_strawberry_framework/utils/permissions.py::request_from_info` is called with `family_label="SerializerMutation"` from `django_strawberry_framework/rest_framework/resolvers.py`. Several occurrences are `pytest.raises(match=...)` anchors, so every message renders byte-identically under this card's existing error-string policy; this is a rename-the-literal change and never a reword. **Riding the same edit because it is another spelling of the same derivation:** `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` rebuilds the partial-input name inline from the runtime operation instead of from the `Meta` serializer class - a third spelling of the partial test and an inline rebuild of `NON_DELETE_OPERATION_INPUT_KIND` - and the correct fix needs an import edge that `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`'s `### Import manifest` does not grant `resolvers.py`, so the manifest row moves in the same change and this half is a contract change rather than a consolidation. The three other provisional-name sites were already re-pointed at `django_strawberry_framework/utils/inputs.py::generated_input_type_name`; this is the fourth. Homed here 2026-09-10 by the spec-039 residual cycle.
- **Contract-level, and the answer decides a WP-A `import-linter` contract: which population should the DRY import ratchet hold, and does the forms flavor get one?** `tests/rest_framework/test_dry_import_ratchet.py` pins by OBJECT IDENTITY that the serializer flavor imports its shared substrate rather than redefining it - the instrument is identity and not a source grep, so it catches the redefinition and the deletion alike - and it was built from imports measured at HEAD because `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`'s `### Import manifest` is stale in all four rows and a ratchet built from it would `AttributeError` on correct code. Three candidate populations, each losing something different: the spec's **named promotions** (what shipped, and what the file holds today), the **whole measured shared substrate**, or the `### Import manifest` population. Two concrete rows for the answer to weigh, neither added by the cycle that raised this: `django_strawberry_framework/utils/inputs.py::generated_input_type_name` is load-bearing at four `django_strawberry_framework/rest_framework/inputs.py` call sites and is absent from the ratchet's `SHARED_BINDINGS`, and the three `django_strawberry_framework/rest_framework/inputs.py` helpers that `django_strawberry_framework/rest_framework/sets.py` now imports are not named in that module's manifest column. **Second axis, and the reason it is a contract and not a test chore:** the forms flavor has no ratchet at all, while `django_strawberry_framework/forms/converter.py::FormFieldConversion` subclasses the same `django_strawberry_framework/utils/inputs.py::FieldConversionBase` the serializer ratchet pins - so whatever boundary WP-A declares for one flavor is owed to the other. Homed here 2026-09-10 by the spec-039 residual cycle; carried exactly, not re-decided.
- **Decide whether a duck-typed `_mutation_meta` is supported at the field-agreement seam.** `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` now raises [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) for both incoherent spellings of an absent mutation-meta snapshot (attribute missing, attribute `None`), replacing a fail-open `getattr` default that statement coverage could not see; that narrowing is shipped and correct, and its `operation` + `optional_fields` snapshot requirement is written into the spec as a contract sentence. What is still open is the tighter `isinstance(meta, _ValidatedMutationMeta)` form, which is a seam-support question rather than a hardening one: `django_strawberry_framework/auth/mutations.py::_AuthMutationMetaSnapshot` is deliberately a duck-typed snapshot, so an `isinstance` gate at that seam would decide for the whole write side whether the snapshot is a protocol or a class. WP-A owns the question because it is the same boundary the `import-linter` contracts formalize. Homed here 2026-09-10 by the spec-039 residual cycle.
- **Settle the owner-name asymmetry in the two `Meta.nested_fields` rejections BEFORE the WP-B consolidation opens those files, because this card's byte-preservation policy freezes whatever text it finds.** The same `SerializerMutation <name>` slot renders the MUTATION class name when `django_strawberry_framework/rest_framework/sets.py` rejects and the SERIALIZER class name when `django_strawberry_framework/rest_framework/inputs.py` rejects, so which name a consumer sees depends on which depth of the `django_strawberry_framework/rest_framework/inputs.py::NestedSerializerConfig` opt-in tree refused. It is pre-existing and was preserved byte-for-byte by the spec-039 residual cycle's consolidation, on the rule that changing a message inside a refactor is a behavior change wearing a refactor's diff - which is exactly this card's policy, and exactly why the decision has to precede the batch rather than ride it. Homed here 2026-09-10 by that cycle.
- **Two test-file items in the mirrored `tests/rest_framework/` tier, both for the pass that next opens those files - the same fold-in convention this card already uses for its `_optimizer_field_map` item.** (a) `tests/rest_framework/test_dry_import_ratchet.py`'s opening docstring wraps raggedly across its first lines; cosmetic, no gate sees it, and no consolidation pass remained in the cycle that wrote the file. (b) The inline-schema idiom in `tests/rest_framework/test_resolvers.py` is a consolidation candidate that was explicitly NOT held by the pass that raised it: re-measured 2026-09-10 with the instrument stated, **19** `class CategoryT` / `class ItemT` declarations, **12** `DjangoSchema(` calls and **14** `finalize_django_types()` calls. Both resolutions are legitimate - leave it (a test file where explicit local declaration aids readability) or extract a parametrizable schema builder - so this is a decision the batch makes when it is already in the file, never a defect to schedule on its own. Homed here 2026-09-10 by the spec-039 residual cycle.
- Slice 5 GLOSSARY flip - the three spec-050 anchors `#listargumenterror` ([`ListArgumentError`](docs/GLOSSARY.md#listargumenterror)), `#async-queryset-completion-adapter` ([Async queryset completion adapter](docs/GLOSSARY.md#async-queryset-completion-adapter)) and `#list-offset-order-precondition` ([List offset order precondition](docs/GLOSSARY.md#list-offset-order-precondition)) already read `shipped (0.0.15)` in `docs/GLOSSARY.md`; the cut verifies them and flips none of the three.
- **The subprocess-isolation idiom has one shared helper.** `tests/_subprocess.py::run_in_fresh_process` (the `tests/_soft_dependency.py` precedent: a non-conftest shared test module) runs a body in a fresh interpreter and asserts its exit status; one contract serves all three probe kinds through keyword parameters - `fakeshop` (the fakeshop `sys.path` + `DJANGO_SETTINGS_MODULE` + `django.setup()` prologue, on by default; off for the bare-interpreter import probe in `tests/base/test_init.py` and the soft-dependency probe in `tests/rest_framework/test_soft_dependency.py`), `interpreter_flags` (the `-W error::DeprecationWarning` warnings probe in `tests/test_scalars.py`), and `env` / `timeout`. Every former inline `sys.executable` call site in `tests/auth/`, `tests/base/`, `tests/filters/`, `tests/orders/`, `tests/rest_framework/` and `tests/test_scalars.py` calls it; the file-local prototype it grew from is gone.
- **The `django-debug-toolbar` floor's ungated restatements ride any floor bump, and the sweep that finds them is over the package NAME.** Measured 2026-09-12 by the spec-042 reconciliation cycle: `django-debug-toolbar>=7.0.0` is restated - correct today, gated by nothing - in `docs/GLOSSARY.md` #"django-debug-toolbar>=7.0.0" (DB-backed: an ORM edit plus a regenerate, never a hand-edit), `docs/README.md`, `CHANGELOG.md` #"Soft-dependency feature floors", the `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv` soft-dependency row, and the body of `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` itself. The terms.csv site is a **pair**: `import_spec_terms` loaded the same `notes` cell into `glossary_glossaryspecmention.notes` in `examples/fakeshop/db.sqlite3`, so fixing the CSV alone leaves the DB copy live. Sweep for the package name and read each hit rather than for the `django-debug-toolbar>=` specifier: the `CHANGELOG.md` site separates the name from the constraint with a space and a backtick, so the tight needle misses it. No absolute count is carried - it moves by more than twenty depending on whether `__pycache__`, the tracked DB and `temp-tests/` are inside the corpus, and the reproducible half is the delta between the two needles.
- The verified `django-debug-toolbar` and `djangorestframework` floors are constants, `django_strawberry_framework/utils/imports.py::DEBUG_TOOLBAR_FLOOR` and `django_strawberry_framework/utils/imports.py::DRF_FLOOR`, interpolated into each install hint. `tests/test_ci_governance.py::test_debug_toolbar_floor_constant_matches_the_pyproject_dependency_row` and `tests/test_ci_governance.py::test_drf_floor_constant_matches_the_pyproject_dependency_row` compare each to its `pyproject.toml` dependency row, beside the Channels and Strawberry rows. The `django_strawberry_framework/rest_framework/__init__.py` and `django_strawberry_framework/middleware/debug_toolbar.py` comments count only the three gated sites (the constant, the dependency row and the test's `_HINT_SUBSTRING` literal); spec-039 Decision 12 is named as the rationale, not a gated site.
- `tests/test_ci_governance.py::test_no_live_tier_module_posts_raw_without_a_declared_exemption` fails any `.post(` / `.generic(` call in `examples/fakeshop/test_query/` without a `# raw-envelope exemption: <reason>` comment directly above it (`docs/SPECS/spec-043-test_client-0_0_14.md` Decision 11); `.get(` stays out of the count. `examples/fakeshop/test_query/test_list_field_async_api.py` drives `AsyncTestClient` and posts raw nowhere.
- Decided: no shared async helper, and `examples/fakeshop/graphql_client.py` stays sync-only. The `examples/fakeshop/test_query/README.md` #"stays sync-only; no shared async helper" bullet states that async rows drive `django_strawberry_framework/testing/client.py::AsyncTestClient` against a module-owned `AsyncDjangoGraphQLView` mount.
- The package spells "a control signal is not a cleanup diagnostic" one way: every cleanup handler that may demote a failure to a note catches `Exception`, so `asyncio.CancelledError` / `KeyboardInterrupt` / `SystemExit` / `GeneratorExit` bypass it by inheritance and keep precedence (`django_strawberry_framework/resource_policy.py::_close_async_iterator`, and the `consumers.py` handlers alike); `scripts/check_truthful_reads.py` fails any `except BaseException` that does not re-raise, so a second spelling cannot return; no wire change.
- Seal the `FilterSet.apply_*` return the way the `OrderSet.apply_*` return is sealed: one shared post-sidecar helper pair (`django_strawberry_framework/utils/querysets.py::apply_filterset_sync` / `::apply_filterset_async`, `::apply_orderset_sync` / `::apply_orderset_async`, all over `::_apply_sidecar_sync` / `::_apply_sidecar_async`), the same frozen routing intent and the one `_SIDECAR_RESULT_POLICY` (lazy, model rows of the captured model, unsliced, same alias; a combined result is served as the set of primary keys it selects), called from both `connection.py` pipelines; the list field publishes no `filter:`. The spec-050 rationale's Decision 19 states the one-seal rule both fields share. A connection request seals `get_queryset` under the one default policy whether or not it carries a sidecar input, the same rule the list field applies with or without arguments. Package rows in `tests/test_connection.py`, live rows on the shipped genre connection in `examples/fakeshop/test_query/test_library_api.py`.
- Discharged: every relation an `OrderSet` term crosses, declared by a [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) or not, reads only rows its target type's `get_queryset` shows (`django_strawberry_framework/orders/sets.py::OrderSet._scoped_hops`, the hops `django_strawberry_framework/utils/relations.py::leading_relation_hops` reads, types resolved as `django_strawberry_framework/utils/querysets.py::relation_target_type` does, a declared hop through its target set's bound type); the term's value is `django_strawberry_framework/optimizer/predicates.py::visible_value`, `NULL` through a hidden row, and `django_strawberry_framework/orders/sets.py::OrderSet.apply_async` awaits each hop's visibility up front. A keyset `orderBy:` through such a relation is refused as nullable (`django_strawberry_framework/connection.py::_keyset_order_state`). Live rows in `examples/fakeshop/test_query/test_library_api.py`.
- Discharged for every relation a [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) declares: a relation-key filter leaf walks its last declared hop (`django_strawberry_framework/utils/permissions.py::walk_declared_relation_path` consumes that relation and leaves an empty remainder), and `django_strawberry_framework/filters/sets.py::FilterSet._leaf_chain` re-reads the key over the hop's visible rows: `isnull` tests whether a visible target row exists, a primary-key, GlobalID or model-choice value naming a hidden row matches nothing, a forward key also requires the stored key to reach a visible row, and the leaf fires exactly the gates its nested twin fires: the branch gate and the target's primary-key gate (`django_strawberry_framework/utils/permissions.py::relation_path_gates`, collected by `django_strawberry_framework/filters/sets.py::FilterSet._permission_walk_gates`). A key leaf over a relation a renamed `RelatedFilter` declares ([`Meta.fields`](docs/GLOSSARY.md#metafields) key `shelves` beside `visible_shelves = RelatedFilter(ShelfFilter, field_name="shelves")`) answers over the shelves `visibleShelves: { id: ... }` reads. Live rows in `examples/fakeshop/test_query/test_library_api.py` and `examples/fakeshop/test_query/test_products_api.py`, package rows in `tests/filters/test_sets.py`.
- Discharged: a relation no `RelatedFilter` declares reads the `get_queryset` of its model's registered type (`django_strawberry_framework/utils/querysets.py::relation_target_type`), relation keys, flat paths and multi-relation `field_name` intermediates alike; live rows in `examples/fakeshop/test_query/test_library_api.py` and `examples/fakeshop/test_query/test_products_api.py`, package rows in `tests/filters/test_sets.py`.
- Discharged: `django_strawberry_framework/utils/input_values.py::assert_set_traversal_depth` reads a set's `_MAX_LOGIC_DEPTH` knob once and names it as `_MAX_LOGIC_DEPTH=<n>` only when a declared int set the cap; a knobless, `None` or non-int knob is worded with the neutral default; pinned by `tests/filters/test_sets.py::test_evaluate_logic_tree_caps_a_non_int_knob_at_the_neutral_default`.
- Discharged: `django_strawberry_framework/utils/_queryset_private.py` reads no `_result_cache` slot, so its module docstring's claim that django-stubs declares none of the private `QuerySet` slots it spells holds; no change owed.
- Discharged: `django_strawberry_framework/optimizer/hints.py::_require_prefetch` reads the value's real class through `truth.is_instance`, so a value whose `__class__` read raises or claims `Prefetch` is the typed `ConfigurationError`; pinned by `tests/optimizer/test_hints.py::TestInvalidStatesRejected.test_prefetch_obj_rejects_raising_class_read`.
- Discharged: `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy` asks a selection's real type through `truth.is_instance` / `truth.is_type` and compares a name through the base `str` slot, so a hostile `__class__` can neither force a match nor replace the typed `ConfigurationError`; pinned by `tests/optimizer/test_nested_fetch.py::test_resolve_strategy_non_str_lookalikes_stay_typed` and `tests/optimizer/test_nested_fetch.py::test_resolve_strategy_class_test_reads_the_real_type`.
- Discharged: the gate rows stand verified; no package change owed.
- Robustness, not a defect: a wrong-table child can be served through a coinciding pk subquery; no contract row names it, so no change until one is filed.

#### Definition of done

- [ ] `lint-imports` green in CI and pre-commit with the four boundary contracts; no `optimizer._*` import outside `optimizer/`; the optimizer's package-internal contract is declared in `optimizer/__init__.py`.
- [ ] The four extras install and resolve in isolated venvs; runtime guards unchanged.
- [ ] Every WP-B/C/D candidate landed or recorded rejected-with-reason in the spec; the deliberate-duplication ledger preserved.
- [ ] Plain-form mutations run inside `pipeline_alias_guard` + `authorization_phase` with live coverage (approved behavior change); `editable_input_fields` strictness tightening covered (approved behavior change).
- [ ] Full suite green under `fail_under = 100`; zero error-string assertion edits outside the two approved behavior changes; optimizer bench deltas at noise level.
- [ ] Version triplet verified at `0.0.15`, GLOSSARY rows for every card on the line read `shipped (0.0.15)`, CHANGELOG entry, card flipped Done, KANBAN regenerated, `import_spec_terms` green.

#### Files likely touched

- `pyproject.toml` (import-linter config + extras), CI workflow, `.pre-commit-config.yaml`
- `django_strawberry_framework/optimizer/__init__.py` + its three cross-boundary consumers (`types/resolvers.py`, `mutations/resolvers.py`, `connection.py`)
- The four DRY axes: `filters/sets.py`, `orders/sets.py`, `sets_mixins.py`, `mutations/{sets,inputs,resolvers,permissions}.py`, `forms/{sets,inputs,resolvers}.py`, `rest_framework/{sets,inputs,resolvers,serializer_converter}.py`, `utils/*`, `connection.py`, `keyset.py`, `optimizer/*`, `types/{base,finalizer,resolvers,relay}.py`

#### Architectural posture

- No package split - the boundary becomes formal, not physical: `import-linter` contracts give ~90% of a split's discipline at ~2% of its cost, and are the prep work a real split would need anyway.
- Error-string byte-preservation policy: every consolidation renders existing messages byte-identically; family differences become parameters (noun, citation tail, accessor), never averaged prose. The pinned tests are the enforcement mechanism.
- Phase sequencing: mechanical -> structural -> contract-level. The per-family traversal descriptor (WP-B) is the substrate for WP-C's mixin work; the skeleton folds land before anyone touches the delete path again.
- Hot-path exclusions: nothing touches `_IndexedList.append_unique`, `included_field_selections`, `_merge_aliased_selections`, or resolver bodies. Expected measured perf cost ~zero despite the maintainer accepting a small cost.

#### Why it matters

- The maintainer's pain point: the package (~47.3k lines, ~19.7k code) has grown to the point of alignment fatigue. A pip-package split was investigated and rejected on evidence (the optimizer is bidirectionally fused to the type system; ecosystem precedent is uniformly against standalone framework-coupled optimizers).
- The split instinct pointed at real work: the optimizer/core boundary exists only by convention (private `optimizer._context` is imported from two subsystems; nothing enforces any seam), and four subsystem axes carry verified duplication.
- Four parallel audits (sets family, inputs/converters, resolvers, root+optimizer+utils) produced 32 verified consolidation candidates totaling ~1,100-1,300 lines, plus a do-not-touch ledger of deliberate duplication so future passes don't re-litigate.

#### Dependencies

- Sequenced behind DONE-044-0.0.14, whose `0.0.14` joint cut has landed; this card's Slice 5 owns the `0.0.15` release cut.
- Also sequenced behind TODO-ALPHA-052-0.0.15: the debug extraction lands first on this card's own `0.0.15` line and removes `extensions/debug.py`, so this card's import-linter leaf wording (contract 3) and its extras additions (Decision 5) build on the post-extraction tree - hold all slices until that card wraps.

#### Open question

- Two safe-direction costs in the middleware-ordering audit, deliberately left unpinned by any test so a contract sentence is not frozen before it is written. First, a chain spelled `[boundary, csrf, boundary]` is refused at startup, because the audit keeps the *last* boundary index and the *first* CSRF index. Second, two adjacent boundary entries measure the body twice, because `process_view` calls `view._enforce_request_boundary`, not `::_enforce_request_boundary_once`. Decide which is contract; only then does a row pin it.
- Whether the package owes a controlled response to a callback that forges the private boundary marker over a `view_class` carrying a *callable* of the probed name whose boundary then raises. Measured identically on Python 3.14/Django 6.0 and at the 3.10/5.2 floor: it passes the probe, is constructed, and a non-`HTTPException` leaves `process_view` uncaught. If taken, the change is `except Exception` around `view._enforce_request_boundary(request)` in `process_view`, and its cost is that the guard sits across the body cap's own errors and across a package mount's genuinely broken boundary - which is deliberately as loud with the middleware installed as without it. Three independent passes recommended against the code path. Until it is decided, no permanent test row may assert today's uncontrolled outcome as contract.

#### Card references

- Dependency: `DONE-044-0.0.14` - Response-extensions debug middleware
- Dependency: `TODO-ALPHA-052-0.0.15` - Extract DjangoDebugExtension into the standalone django-strawberry-debug package
- Dependency: The list-field card lands first on the shared `0.0.15` line; this card lands last and its Slice-5 version-triplet cut waits for every `0.0.15` card. -> `DONE-050-0.0.15` - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`
- Dependency: Shares every file in the parity-gap card's Files-likely-touched list except `types/converters.py`, so this card is sequenced behind it (the edge that card's DoD owed, landed at the 2026-08-29 board review). -> `WIP-ALPHA-051-0.0.15` - Upstream parity-gap closure

## To Do - Alpha (0.1.0)

Cards required to reach feature parity with both upstreams (`⚛️ graphene-django` and `🍓 strawberry-graphql-django`). Cards target `0.0.x` patches on the road to **0.1.0**; the remaining alpha work spans three joint-cut lines - `0.0.15` (050-053, DRY squeeze owns the cut), `0.0.16` (054-055, federation owns the cut), and `0.0.17` (056 solo). The final card in this column is the `0.1.0` release itself (cleanup, verification, alpha → beta cut-over). Cards in NNN order = planned ship order; dependency and parallelism notes live on each card.

<a id="pluggable_field_conversion_registry"></a>
### [TODO-ALPHA-054-0.0.16 - Pluggable field-conversion registry](KANBAN.html#pluggable_field_conversion_registry)

- Priority: Medium-high
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: To Do
- Relative size: M
- Labels: `converters`, `public-api`, `registry`, `scalar-map`, `scalars`, `types`

#### Planning note

Created 2026-08-29 from the DIV-033 discussion: turn the field-conversion escape hatch from process-global dict mutation into a scoped, bundle-shaped, callable-capable registry. Extensibility parity with graphene-django's public converter hook, and the prerequisite for the GIS backlog card and the dynamic-schemas card. No schema-visible change for existing consumers.

#### Dependencies

- `WIP-ALPHA-051-0.0.15` - Upstream parity-gap closure

#### Scope

- Class-attribute scoping: SCALAR_MAP / FIELD_OUTPUT_TYPE_MAP resolution moves from module-global-only to a layered lookup resolved at Meta-class creation time - per-type Meta override, then [DjangoType](docs/GLOSSARY.md#djangotype) base-class attribute (inherited via Python MRO, the DRF ModelSerializer.serializer_field_mapping shape), then the framework default maps. The module-level dicts remain the bottom layer so every existing registration keeps working; two apps in one process stop colliding because each app's base class carries its own map.
- Bundle-shaped entries: a registration value grows from a bare scalar to a bundle - scalar, optional read-output type, optional resolver-attach hook, optional filter-side scalar. The file family (FileField/ImageField -> DjangoFileType/DjangoImageType + resolvers._attach_file_resolvers) migrates onto it as the first in-tree registration, deleting its hard-coded special cases.
- Callable converters for structured/container fields: an entry value may be a callable converter(field, type_name, *, recurse) returning the annotation, with recurse a bound re-entry into convert_scalar. The hard-coded ArrayField/HStoreField branches in convert_scalar are deleted and re-registered as the first two callable entries; outer nullability widening stays framework-owned so converters cannot get it wrong; [ConfigurationError](docs/GLOSSARY.md#configurationerror) rejection of invalid shapes stays converter-raised.
- One registry, both sides: the filter-input converter (filters/inputs.py via scalar_for_field) resolves through the same registry so a registered type appears consistently on read output and filter arguments.
- The fail-closed contract is unchanged: an unregistered field class still raises ConfigurationError naming the registration hook; nothing silently degrades to str.
- No schema-visible change for existing consumers: fakeshop SDL is byte-identical before and after the refactor, asserted by a test.
- The file-column read-side selection is pinned before the file family migrates onto a bundle entry: `examples/fakeshop/test_query/test_uploads_api.py::test_file_and_image_columns_left_out_of_the_selection_are_absent_over_http` drops a `FileField` and an `ImageField` column by [`Meta.fields`](docs/GLOSSARY.md#metafields) (`MediaSpecimenType`) and by [`Meta.exclude`](docs/GLOSSARY.md#metaexclude) (`MediaSpecimenWithPathType`), and neither surfaces as an output field or a generated file resolver. This card's #"Fakeshop SDL byte-identity test" DoD item therefore measures the file family rather than assuming it.

#### Definition of done

- [ ] Registry resolution order (Meta override -> base-class attribute -> framework default) specified in the spec and pinned by tests, including the two-apps-one-process collision case.
- [ ] File family and postgres container fields migrated onto bundle/callable entries with their hard-coded branches deleted from convert_scalar and resolvers.
- [ ] Filter-input side resolves through the same registry, with a test pinning read/filter consistency for a consumer-registered type.
- [ ] Fakeshop SDL byte-identity test proves no schema-visible change for existing consumers.
- [ ] Escape-hatch documentation (converters.py docstring and any doc pages naming SCALAR_MAP registration) updated to the registry surface, with the old form still working and documented as the bottom layer.

#### Files likely touched

- `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/filters/inputs.py`
- `tests/types/test_converters.py`, `tests/filters/`

#### Verified in upstream

- graphene-django's convert_django_field is a @singledispatch callable registry (converter.py) and is the public hook third-party packages extend (graphene-gis adds GeoDjango support through it) - extensibility is itself a parity surface.
- DRF ModelSerializer.serializer_field_mapping (rest_framework/serializers.py) is the class-attribute scoping precedent: subclass-and-override, MRO-inherited - the DRF-idiom shape this framework follows.
- strawberry-graphql-django 0.82.1 ships geo scalars in-tree instead of a hook; the registry is how this package answers that surface without acquiring GDAL/GEOS system dependencies.

#### Why it matters

- The documented escape hatch (SCALAR_MAP[FieldCls] = <scalar>) is today raw process-global dict mutation: no scoping, no validation, no resolver or container story. Changing extension architecture after 0.1.0 means migrating consumers, so the reshape must land in alpha.
- Prerequisite for the GIS / GeoDjango backlog card (its recipe-vs-satellite open question is decided by how much this registry can carry) and for the dynamic-schemas card (dataType spec entries resolve through registered converters).

#### Card references

- Related: This registry decides how much of the GIS card a consumer-side recipe can cover. -> `BACKLOG-STABLE-076-1.1.0` - GIS / GeoDjango field-type support (geo scalars)
- Related: The doc-debt card documents the new registry surface from its own solo `0.0.17` line; the `0.0.16` release state is owned by the federation card's cut. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge
- Dependency: The parity-gap card's `GeneratedField` entry lands in the converter table this card migrates onto the registry; sequenced behind it. -> `WIP-ALPHA-051-0.0.15` - Upstream parity-gap closure
- Related: The file-column read-side `Meta.exclude` row is pinned before this card's bundle migration un-shares that path from the scalar case, so the migration is measured against it. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping

<a id="apollo_federation_as_the_standalone_django_strawberry_federation_package"></a>
### [TODO-ALPHA-055-0.0.16 - Apollo Federation as the standalone django-strawberry-federation package](KANBAN.html#apollo_federation_as_the_standalone_django_strawberry_federation_package)

- Priority: Medium-high
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: To Do
- Relative size: L
- Labels: `packaging`, `public-api`, `schema`

#### Planning note

Maintainer decision 2026-08-29 on the parity register's federation cut blocker: the Apollo Federation subgraph surface (🍓 ships it as the whole `strawberry_django/federation/` subpackage - `type.py`, `field.py`, `resolve.py`) lands as a standalone satellite package on the django-strawberry-debug pattern, never in core. Core-refused because federation couples the schema surface to a third-party protocol that evolves on Apollo's schedule and serves one deployment shape (a subgraph behind an Apollo gateway); the satellite gets its own release cadence for spec churn. Unlike the debug extraction this is greenfield-in-satellite, not a code move - and unlike django-strawberry-debug the satellite DOES depend on django-strawberry-framework, because entity resolution and the Meta surface build on core seams. Supersedes the retired BACKLOG `apollo_federation_meta_surface` row (its Meta sketch - `federation = {"keys": [...], "shareable": [...], "tag": ...}` - carries forward as the satellite's declaration shape).

#### Dependencies

- `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze

#### Scope

- Slice 1 - in-repo seams, the only slice that touches this repo's package source: pin [`DjangoSchema`](docs/GLOSSARY.md#djangoschema) as deliberately subclass-friendly (a stated contract with a test, not an accident), because a federated consumer needs `strawberry.federation.Schema`'s directive/entity machinery AND `DjangoSchema`'s transaction-spanning mutation context in one class, so the satellite must be able to build a `DjangoFederationSchema` on both; audit that everything entity resolution needs - registry lookup, finalizer participation, GlobalID/node identity - is reachable through public API under the import-linter boundary contracts the DRY-squeeze card lands, and add any missing public seam here rather than letting the satellite import `_private` internals.
- The pinned `DjangoSchema` subclass contract also states that every keyword argument `DjangoSchema.__init__` owns (today `resource_policy` and `error_policy`, and any later one) is consumed before delegation to the Strawberry base, and that a subclass forwards `**kwargs` unchanged, so a keyword added to `DjangoSchema` later reaches a `DjangoFederationSchema` without a satellite release.
- Slice 2 - the satellite: new repo unaxy/django-strawberry-federation depending on django-strawberry-framework and strawberry-graphql's federation support; `DjangoFederationSchema`; the DRF-idiom Meta surface (`Meta.federation = {"keys": [...], "shareable": [...], "tag": ...}`) emitting Federation 2 directives - Meta declarations, never decorators; `_entities` resolution routed through the target type's `get_queryset` so row visibility holds for gateway entity fetches exactly as it does for root fields; own suite, CI matrix, README; 0.1.0 published to PyPI.
- Slice 3 - framework docs fold-in: `[federation]` optional-dependencies extra pointing at the satellite; GLOSSARY entry via the DB; the migration-guides card's 🍓 guide maps `strawberry_django`'s federation subpackage to the satellite; the beta release card's parity carve-out cites the package; the BACKLOG `apollo_federation_meta_surface` row is retired (done at carding, recorded here).

#### Definition of done

- [ ] `DjangoSchema` subclass-friendliness is a pinned contract: a test constructs a subclass combining it with `strawberry.federation.Schema` machinery (or the seam equivalent) and the docstring states the contract.
- [ ] The satellite needs zero `_private` imports from django-strawberry-framework - verifiable under the import-linter contracts; any seam it needed was made public here first.
- [ ] django-strawberry-federation 0.1.0 on PyPI: `DjangoFederationSchema`, Meta-driven `@key` / `@shareable` / `@tag`, entity resolution through `get_queryset` (a hidden row is as unreachable via `_entities` as via a root field, proven by test), supergraph-composition + `_entities` round-trip integration coverage.
- [ ] `pip install django-strawberry-framework[federation]` resolves in an isolated venv; with the extra absent, nothing in core imports or references the satellite.
- [ ] Guides note and GLOSSARY entry land; the beta release card's parity claim cites the package for the federation carve-out.
- [ ] Full suite green under `fail_under = 100` for the in-repo slice. Version triplet at `0.0.16`, GLOSSARY status flips for the line, CHANGELOG entry - this card lands last on the `0.0.16` line (after the registry) and owns the joint cut.

#### Files likely touched

- `django_strawberry_framework/schema.py` (subclass-friendliness contract + docstring)
- Public seam additions only if the Slice 1 audit finds a gap (registry / finalizer / node identity access)
- `pyproject.toml` (`[federation]` extra), GLOSSARY via DB, guides fold-in
- Everything else lives in the new unaxy/django-strawberry-federation repo

#### Verified in upstream

- 🍓 ships federation as `strawberry_django/federation/` (`type.py`, `field.py`, `resolve.py`): Federation 2 directives and entity resolution. ⚛ ships none, so this is single-upstream parity.
- strawberry-graphql core ships `strawberry.federation` (federation-aware Schema, directive types), which is what the satellite composes rather than reimplements.

#### Dependencies

- Slice 1's public-seam audit runs against the import-linter boundary contracts this card lands.

#### Card references

- Dependency: Slice 1's public-seam audit runs against the import-linter boundary contracts this card lands. -> `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze
- Related: The satellite pattern this card follows - with the inverse dependency posture: debug has no core dependency, federation requires one. -> `TODO-ALPHA-052-0.0.15` - Extract DjangoDebugExtension into the standalone django-strawberry-debug package
- Related: Owes the federation note in the strawberry-graphql-django guide: upstream's federation subpackage maps to django-strawberry-federation. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides
- Related: The parity claim's federation carve-out cites this card's satellite package. -> `TODO-ALPHA-057-0.1.0` - Beta release (cleanup, verification, alpha → beta)

<a id="alpha_documentation_debt_discharge"></a>
### [TODO-ALPHA-056-0.0.17 - Alpha documentation-debt discharge](KANBAN.html#alpha_documentation_debt_discharge)

- Priority: Medium
- Status: To Do
- Relative size: XL
- Labels: `internal`

#### Planning note

Documentation-consistency debt accumulated across the alpha line, split off the beta release card so it has a definition of done that can fail.

#### Dependencies

- `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry
- `TODO-ALPHA-055-0.0.16` - Apollo Federation as the standalone django-strawberry-federation package

#### Scope

- `docs/GLOSSARY.md` carries a `## DjangoSchema` entry (anchor `#djangoschema`) describing the schema constructor, its two policy arguments and `DjangoMutationExecutionContext`, which is documented as a paragraph inside it rather than an entry of its own. The `## Public exports` [`DjangoSchema`](docs/GLOSSARY.md#djangoschema) bullet is one line linking that entry, and the `DjangoMutationExecutionContext` bullet links the same anchor. `## Public exports` also carries group bullets for the `views`, `routers` and `middleware.debug_toolbar` families, each stating that the dotted import path is the opt-in boundary and that the family is not root-exported.
- `README.md:62`'s `0.0.14` paragraph describes `main`'s router shape inside the released version's sentence. Chosen framing on record: lead with the marker, the shape `docs/README.md:128` and `TODAY.md:384` already use.
- `BACKLOG.md`'s two `Transport substrate: **shipped**` lines state that `django_strawberry_framework/routers.py::DjangoGraphQLProtocolRouter` owns only the WebSocket route and that HTTP stays the project's own Django view.
- Promote a spec/rationale consistency checker into `scripts/`. Nothing there matches `link|anchor|overlap` today, so every documentation pass hand-writes its own. The checks each spec-plus-rationale pair owes: link scaffold (defs / uses / undefined / orphan), the 10 canonical group headers in positional order, alphabetical order within group, on-disk resolution of every def target with the fragment stripped and URLs excluded, in-page anchors slugged by a markup-rendering slugger, an inline cross-file-link sweep, a rule-27 raw `path:NN` sweep, and a maximal-shared-shingle scan - the only thing that turns "it was a move, not a copy" into a measurement. Four slugger defects, each measured on an independent hand-roll of this checker, to encode as its regression tests. (a) A heading that is itself a reference link, slugged without rendering the markup out first: the link-definition key survives into the slug, so a correct in-page anchor reports as dangling. (b) Whitespace runs collapsed. GitHub replaces spaces one at a time, so a heading with a double space slugs to a double hyphen; a checker that collapses runs reports a false PASS - the only silent defect of the four, and so the most dangerous to leave unencoded. (c) Code spans deleted rather than masked before reference links are matched. A label spelled as a code span collapses to an empty label, which the usual bracket-capture pattern cannot match; one run reported 3 spec and 12 rationale false orphans from this alone. Mask span content to same-length filler instead, preserving the brackets. (d) `_` stripped as an emphasis marker before slugging. It destroys `django_types`, so the anchor for a heading naming `spec-001-django_types-0_0_1.md` reports unresolved against a correct link definition - a false positive whose natural fix is to corrupt a good link. Defect (d) is the argument for a tool rather than more prose: it was measured, written into a hand-off, and re-introduced from scratch two rounds later by a reader who had that hand-off. (e) Shingle tokenization, and it fails OPEN like defect (b) rather than loudly. A phrase-shaped duplicate check must tokenize on word characters (`[A-Za-z0-9_]+`) and case-fold, because Markdown emphasis and punctuation sit INSIDE the window and shift token positions without changing the words: the spec-006 residual cycle's first move-verification reported 0 non-scaffold overlaps where a word-character tokenizer finds 3, because `**all four**` and `**iff**` produce disjoint shingles from an identical word sequence. That is the second independent measurement of the rule this card's methodology note already carries out of the spec-005 cycle, arrived at without reference to it - which is the same argument defect (d) makes, and the argument for encoding the rule as a test rather than restating it in prose a third time. The scan also owes a control pair before any number it reports means anything: spec-006's companion measured 180 non-scaffold 8-word shingles against its sibling companions where the 006/005 control measured 247, so the higher-looking figure was the LESS coupled one and an unquoted overlap count is not a finding.
- `docs/SPECS/spec-002-optimizer-0_0_2.md` carries no status-shaped section any more. The spec-002 residual cycle discharged most of them - `## Open questions` and `## Current state` are gone, and `## Shipped slices` and `## Implementation checklist` survive the argument on their merits, since a past-tense fact about what shipped is not a promise about the present. The last one, `## Visibility status`, was retired by the spec-006 residual cycle as a cross-spec duplicate under the single-ownership law: the section existed because `spec-006-public_surface-0_0_3.md` asked for a copy, and both of spec-006's citing bullets were retired with it, so nothing in spec-006 names the section. The companion `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` no longer defines a `#visibility-status` link target either; its one remaining link into the spec, under `## Why a consumer-declared resolver wins`, reads "Bears on [Shipped slices][spec-002-shipped], O1." `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` no longer carries its when-O4-ships instruction at all - the 2026-08-07 reconciliation deleted the section - so nothing in spec-003 names these headings any more.
- `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` was reconciled on 2026-08-07 and three of the four stale sites this card carried are closed: the pre-reconciliation `plan_optimizations` arity and the present-tense `_collect_scalar_only_fields` are rewritten, and the discharged when-O4-ships instruction is deleted along with the parent-spec sweep item it carried. The fourth is a live DIVERGENCE this card must settle rather than sweep: this card's prescription was to replace the spec's opening claim so it states that O4 is shipped and that its record is this spec's, and the reconciliation deliberately rejected that disposition - a spec states its contract and never narrates its own shipping status - with the reasoning and the rejected alternative recorded in `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` under its `## Problem statement` entry. Neither surface has been partial-fixed toward the other; settling which one moves is this card's closeout call. The prior instruction not to sweep up spec-006's two citations of `## Visibility status` is spent: the spec-006 residual cycle retired both bullets with the heading they named, so nothing in spec-006 references the section.
- `DONE-003-0.0.2`'s `Verified in upstream` note is imprecise about which upstream function rebases: `strawberry_django/optimizer.py::_get_hints_from_django_relation`'s rebasing block moves entries out of its local store with the `path__` prefix STRIPPED (and is inert - that store is constructed empty), while the prefix-adding rebase lives in the sibling `::_get_hints_from_django_field`. The two sub-claims the parity argument rests on (`level=level + 1` recursion and `Prefetch(path, queryset=field_qs)` emission) are exact. Fold a one-clause correction into this card's closeout alongside its other spec-003 record work; a standalone edit of a shipped Done card's historical note buys no reader anything on its own.
- Decide whether `scripts/check_spec_glossary.py` should strip code spans in `REF_USE_PATTERN`. Today a glossary link whose only body carrier sits inside a code span still counts as a link; a checker that started stripping code spans would drop every such anchor and break the affected done cards' `import_spec_terms` chains. Run a repo-wide count of code-span-only carriers before changing anything - this is the same span-masking question as slugger defect (c) in this card's checker item, landing on the opposite answer (count them rather than drop them).
- Worker memory does not survive a concurrent build, and the loss is silent. `docs/builder/worker-memory/` is shared, gitignored, and reseeded empty by every build's pre-flight (`worker-0.md` step 5; `BUILD.md` `### Worker memory`), while `START.md` documents several sessions running builds on one checkout. So the second session to start a build destroys the first's memory before that build's closeout reads it - and `worker-0.md` `## Closeout job` step 2 is the only pass that ever reads all four. Measured on the spec-003 cycle: at closeout all four files read `# Worker N memory - build 004`, and the spec-003 entries were unrecoverable. Fix by namespacing the files per build, or by making pre-flight archive rather than delete, or by moving the closeout read earlier; whichever, pre-flight must stop being able to delete a build's memory that its own closeout has not harvested.
- `scripts/clean_up.py` has no concurrency guard and can destroy another session's live work. Its `('docs/builder', 'bld-*.md')` glob deletes every cycle's artifacts, not the caller's, and it also clears the shared `docs/builder/worker-memory/` and `docs/shadow/`. Running it at the close of the spec-003 cycle would have deleted two untracked spec-004 artifacts, one of them at `Status: planned` and written six minutes earlier - unrecoverable, since untracked files are not in git. It is the sanctioned way to end a cycle and the repo is documented as concurrently worked, so this will recur. Scope deletion to a caller-supplied cycle (`--card NNN`), or refuse when a targeted artifact is untracked or not `final-accepted`.
- The builder corpus states rules correctly and they still get missed, because they sit far from the point of use. Two measurements from the spec-003 cycle, one gap and one placement problem. (a) GAP: `worker-1.md` `### Performing the rationale move` decides what stays in a spec by asking whether a SENTENCE is deliberation or instruction - but a load-bearing rule can be an ordering constraint with no sentence form. Three of the six rules rescued out of spec-003's deleted pseudo-code fences existed only as the sequence of two lines (`_record_relation_access` before the elision short-circuit; the `only_fields` guard before connector injection; `cacheable = False` before the child build), and a seventh was missed on the first pass and caught only by review. Every rationale extraction that cuts pseudo-code hits this; five cycles have. (b) PLACEMENT: `BUILD.md` `## Claims are proven mechanically` already says to count occurrences rather than matching lines, and six of the cycle's thirteen findings were still miscounts, twice by exactly that `grep -c` mechanism. More prose is not the fix - the rule is right and unread. Both are corpus edits bound by `BUILD.md` `## The corpus ratchet`, so each needs the bytes it retires named before it lands. (c) A third measurement, from the spec-006 residual cycle, of (b)'s shape and pointing at (b)'s fix. Six instances in one cycle of RIGHT SUBSTANCE, LOOSE CITATION - a checklist box whose claim holds while the evidence it cites does not re-derive: an evidence formula requiring `git diff <spec>` to be empty, which was unsatisfiable from the moment that cycle's own reconciliation pass rewrote the spec uncommitted; a quoted heading carrying an ASCII hyphen where the heading on disk carries an em dash, so the quoted string greps to 0; marker occurrence counts measured over four docs and dispatched over five; and `CardItem.order` values checked as though they were rendered ordinals, which fails against a correct render because the order sequence is sparse. Four more were confined to a scratchpad, including a model cited as `GlossaryDocument` where the row is `apps.kanban.models.BoardDoc` with `namespace='glossary'`. The sharpest instance sat inside a sentence claiming re-derivation - the measurement had been re-derived and the attribution clause riding on it had not - so the countermeasure is that a re-derivation claim must scope to every clause it stands over, and an auditor re-derives the citation rather than only the substance. Converges from the other direction with this card's note-section quantifier rule; two cycles reaching one rule independently is the argument for stating it once in `BUILD.md` rather than a third time on a card. (d) Two rules measured by the spec-008 residual cycle, same ratchet bucket. First, the recurring pointer defect: a reference resolves and its destination does not carry the claim it was cited for. The two separating tests are subject match and explicit forwarding by name - a pointer landing on a section about the right subject is not thereby a pointer to the claim, and the only pointer that survives a later edit of its destination is one the destination names. This card's spec-010 rule-27 item is a population of exactly that defect, which is the argument for stating it in `BUILD.md` rather than once per spec. Second, its mechanical cousin, and the sharper of the two because it explains why gates miss it: before trusting a mechanical check, state what the tool actually reads. A line-oriented tool applied to a quantity that is not a line was that cycle's most repeated error, and the general form is that the tool's input is not the thing under test - `grep` sees source literals while the runtime sees their concatenation, so `testing/relay.py::global_id_for`'s message is split across adjacent string literals and a source grep returns 0 for text that is present in the raised string; a link audit reads a heading list while the claim lives in the body; and `cardinalit` appears only in prose while the code spells it `FieldMeta.is_many_side`, which is how a reported "9 occurrences, 0 validators" travelled three un-re-derived hops against a real 42 lines in 12 files. Converges with (b) from the opposite direction: (b) says count occurrences rather than matching lines, and this says a count means nothing until the population counted is the one the claim is about. (e) A placement defect in `ARTIFACT.md`, same bucket. `ARTIFACT.md:3` and `:181` make the top-level header `Status:` line canonical and `:187` makes the body append-only, and the spec-008 cycle still ran five state transitions with that header reading `planned`, because each pass appended a `## Status` section and none rewrote the header. Both rules are stated and both are correct; nothing sits at the point of use telling a pass writing its block that the header is what dispatch reads. The dispatcher's half of the same defect is that Worker-0 ticked two checklist boxes off a subagent's return message rather than the artifact, which `worker-0.md` already forbids - so the countermeasure is a placement edit at the write site, not a third statement of the rule.
- Add a source-symbol-citation check to the spec/rationale consistency checker this card already scopes: nothing in the repository verifies that a `path::Symbol` citation in a spec names a symbol that still exists. Measured instance: spec-005 cited `convert_relation` as the symbol a relation resolves through, and it is gone from the package entirely. It was found by a human-driven sweep and would have survived every automated gate that cycle ran - `check_spec_glossary` validates glossary anchors, not source symbols. The checker must distinguish a live spec's claim from a shipped spec's history: `spec-008`, `spec-009`, `spec-010` and `spec-019` all name `convert_relation` in the present tense and are correct as history, so a checker that flags them reproduces the documentation-sweep error this board has already ruled against twice.
- `CHANGELOG.md`'s `0.0.8` entry states the release's documentation context only as design-doc pointers: `CHANGELOG.md #"The documentation surface was synchronized for the 0.0.8 cycle"` cites `spec-027-filters-0_0_8.md` and `spec-028-orders-0_0_8.md` through reference links, so a reader of the release record has to leave it to learn what shipped. Decide whether that entry states the shipped surface itself or stays a pointer. Two measurements taken 2026-08-14 frame the decision: the file is 437 lines / 100,289 bytes, and the `0.0.4` onboarding-docs card's board claim that "`CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context" was true when it was written and describes neither property now. That row is correct history on a Done card and is NOT to be edited, which is precisely why the live decision needs a home here. Raised and deferred by the spec-007 residual cycle: `AGENTS.md` rule 21 closes `CHANGELOG.md` to a build cycle, and this card owns the CHANGELOG promotion.
- `scripts/check_trailing_commas.py` skips git-ignored and untracked paths on a sweep (a file named explicitly on the command line is still checked), so an unscoped `--check` no longer reads `.claude/` agent memory or any other ignored path; the `source-layout` pre-commit hook stays the gate on staged paths.
- `spec-009-rich_schema_architecture-0_0_4.md #"### Layer 3: Finalization trigger"` presented hybrid auto-finalization as the preferred direction after the spec-008 reconciliation established the direction was REJECTED; the Layer-3 text was corrected at `f3c94642` and the full spec-009 residual reconciliation cycle completed 2026-08-16 (`docs/builder/bld-009-final.md`) - Layer 3 now states the explicit `finalize_django_types()` call is the sole trigger and nothing auto-finalizes, and the whole spec was reconciled clause-by-clause against shipped code (no correctness defect, no silent omission; six never-built features adjudicated DROP AND SCRUB on parity grounds, with the reasoning in the spec's `-rationale.md` companion). The pointer half was discharged earlier by the spec-010 residual cycle (2026-08-15). Nothing remains for this card from the spec-009 side; the bullet stands as the record that the no-card-of-its-own residual-cycle disposition held here too.
- `spec-010-foundation-0_0_4.md`'s rule-27 debt is CLOSED - re-measured 2026-08-15 at the spec-010 residual cycle's wrap: zero in-repo raw `path:NN` citations remain, and the 20 occurrences on 14 lines that survive are all pinned third-party prior art at a named upstream version (`strawberry_django` / `graphene` / `graphene_django`), which `AGENTS.md` rule 27 does not reach and which keep their line numbers by design. `## Note on source line references`, the section that institutionalized the practice and was this bullet's stated blocker, was retired whole by an earlier rationale pass and no longer exists in the spec. Nothing is owed; the bullet stays as the record so a later sweep does not re-derive the 2026-08-14 measurement (42 occurrences, 20 in-repo) against a spec that no longer carries the debt.
- The `Verified in upstream` section's per-bullet completion state is unpopulated board-wide, which leaves this card's parity-audit definition-of-done box unmeasurable from the board. Measured 2026-08-14: 101 items across 43 cards, 87 of them `is_complete=False`, and `CardItem.verified_at` set on exactly ZERO - so the auditable half of the machinery (`verified_at` / `verified_by` / `verification_kind`, written by `services.verify_item`) has never been exercised for this section at all. The 14 ticked items sit entirely on cards 1 through 27 and only cards 24 and 25 are fully ticked, so the convention was followed early and then abandoned rather than never adopted - which is why the current state cannot be read as "nothing has been verified". Decide which it is before the parity audit runs: either a tick means an upstream claim was re-derived and 87 are owed, or the section is a prose record whose checkbox carries no contract and the flags should be normalized. Do not backfill ticks as tidy-up - a tick nobody re-derived is worse than an unticked bullet, and `verify_item` exists precisely so the difference is recorded. Raised by the spec-008 residual cycle against `DONE-008-0.0.4`'s two entries; the board-wide measurement is what turned a single-card observation into this card's.
- Add an unused-link-definition check to the spec/rationale consistency checker this card already scopes (the defs / uses / undefined / orphan scaffold check). Measured 2026-10-20 under a stated rule (corpus: git-tracked `.md` files; a definition is a line matching `^[ref]:`; a use is the full `[text][ref]`, collapsed `[ref][]` or shortcut `[ref]` form, link-definition lines and HTML comments excluded): **47 definitions across 8 files, none under `docs/SPECS/`** - `KANBAN.md` 36 (DB-generated scaffold), `CHANGELOG.md` 5, and one each in `BACKLOG.md`, `MUSE.md`, `docs/GLOSSARY.md`, `docs/bug_hunt/HUNT.md`, `docs/builder/DONE/build-033-connection_optimizer-0_0_9.md` and `docs/row-preserving-predicates-part1-plan.md`. The archived specs' unused `[backlog]` / `[relay]` definitions are gone. Neither existing checker sees these: `scripts/check_trailing_commas.py` enforces only the header scaffold and `scripts/check_spec_glossary.py` only glossary terms. The checker pins the use-detection rule and re-derives from it; a figure quoted without its rule is not comparable to this one.
- The boilerplate 'expand it into the full builder-format spec' preamble is **DISCHARGED board-wide**: re-derived 2026-08-19, **zero** files under `docs/SPECS/spec-*.md` carry it. This bullet previously stated the population as three - `spec-016`, `spec-024`, `spec-026` - and that figure was already stale when last read: measured at the parent commit of the spec-026 residual cycle, `spec-016` and `spec-024` were each **0** and only `spec-026` was **1**, so the true remaining figure was one, not three. Each of the three was retired by its own residual cycle MOVING the preamble into that spec's `docs/SPECS/appx/spec-NNN-...-rationale.md` companion, which is where the surviving occurrences legitimately live: a `grep -rl` across `docs/` now returns only those companions plus per-cycle `docs/builder/` artifacts quoting them, and **none of those is an edit**. Do not re-derive three, four, or five from an older reading of this bullet, and do not "fix" the companion copies - the move is the fix. What remains open on this card is unchanged and is the question this count was only ever a symptom of: whether a `-rationale.md` companion is owed by every shipped spec or only by one whose cycle produced it, which is this card's separate rationale-companion decision above.
- `AGENTS.md` rule 31's version-parity concern is **DISSOLVED**: the release is single-sourced in `django_strawberry_framework/__init__.py` `__version__`, and hatchling derives the pyproject packaging metadata from it via `[tool.hatch.version]`, so `pyproject.toml` carries `dynamic = ["version"]` and no second literal exists. The item as written asked for a gate pinning `pyproject.toml` `[project].version` against `__version__`; that literal is gone, so nothing remains to pin and no gate is owed. `tests/base/test_init.py::test_version` is the single pin on the one surviving literal. Recorded 2026-08-26, when the mechanical two-source comparison was removed from `scripts/bug_hunt.py::_package_release` together with the tests that pinned its bypass. `uv.lock`'s `django-strawberry-framework` root entry is the one remaining independent copy and stays out of scope here.
- ONE repo-wide sweep, in place of N one-clause fixes: does any archived spec's `0.0.X` deferral have a card? Sized by the spec-009 residual cycle at 56 archived specs, ~34 carrying a deferral-plus-version line, ~190-200 candidate lines (`docs/builder/bld-009-final.md` `### Deferred work catalog` items 5-11 carry the full grading). Folds in: `spec-034-permissions-0_0_10.md`'s four `TODO-BETA-046-0.1.1` citations - 3 live-claim sites (`:220`, `:224`, `:307`) to repoint at the [FieldSet](docs/GLOSSARY.md#fieldset) card, and 1 revision-log bullet (`:14`) that is a DECIDED NON-EDIT (true as history: `046` was the live id on 2026-06-14, before the 2026-07-30 renumber, so rewriting it would falsify a real record); `spec-028`'s two orphaned `0.0.9` deferrals - [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) orderBy-argument integration (`:195`/`:1191`, no card anywhere: needs the spec-009-style card-or-drop parity adjudication before the `1.0.0` freeze) and the position-side-channel leak-closing design (`:734`, verify first: the shipped [OrderSet](docs/GLOSSARY.md#orderset) per-field `check_<field>_permission` gates may already discharge it; if a real gap survives, the node-sentinel redaction card is the board's leak-posture home); `spec-027`'s "lands when [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) ships in `0.0.9`" auto-generation sentence (scrub to match `spec-028` Decision 12's standing-non-goal precedent; the wording depends on the dynamic-set-factories answer carried by the DRY-squeeze card's WP-D); `spec-028`'s 7 `WIP-ALPHA-*` citations and the `WIP-ALPHA-*` prefixes in `connection.py` / `types/finalizer.py` / `types/relay.py`; and the 8 raw `Decision N line NN` refs in package source violating AGENTS.md rule 27 (the live-code halves coordinate with the DRY-squeeze card's WP batches, which already own this shape). Two cautions: honour the spec-034 3+1 split, and do not mistake `orders/factories.py`'s "standing deferred Non-goal" wording for an orphaned deferral - it names no version and no owner. Two method rules the sweep inherits from the cycle that sized it. **State corpus exclusions by BASENAME, not by path prefix - a path prefix silently fails on an archived copy.** That cycle's two token sweeps measured over different permanent corpora without either noticing: a path-prefix reading excluded 137 files under `docs/builder/bld-`, `docs/builder/build-`, `docs/review/` and `docs/dry/` for 620 files, while a basename reading (per-cycle build documents excluded wherever they live) gave 606; **the 14-file difference is a directory, not a file** - every one sits under `docs/builder/DONE/`, whose paths begin `docs/builder/DONE/build-` and so escape the `docs/builder/build-` prefix. The recorded figures 15/5 for `TODO-BETA-046-0.1.1` and 27/9 for `DjangoModelType` are each correct under the rule they were computed with and **must not move**. The part worth carrying: **two independent agreeing re-derivations did not catch the mismatch**, because each instrument inherited the corpus definition from the thing it was checking; only running one population under both readings did. Second, when this sweep opens `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`, its `## Standing notes` "three sites" bullet is **DELIBERATELY stale and owed a correction** - the measured count is four (`filters/sets.py` is the fourth applier) and the spec's own opener was already corrected to "four sites"; it was left because that cycle held the rationale append-only, and the staleness is stated in-file five lines above it. Correct it in the first pass that has the rationale open without that constraint.
- Board-DB spec-path rot is discharged: `CardItem.text` carries 0 `docs/spec-NNN` tokens. (a) the 4 renumber residues on cards 057, 058 (two) and 060 named unwritten specs whose working location was `docs/` per `AGENTS.md` rule 26, and are gone with those specs' archiving; (b) the 3 occurrences on cards 055 and 056 were repointed to `docs/SPECS/` on 2026-08-19; (c) the 13 occurrences on 8 DONE cards (028 three, 029 / 030 / 032 two each, 033 / 034 / 035 / 045 one each) were repointed to `docs/SPECS/` on 2026-08-27, navigable over historical: the spec a DoD names is the file a reader opens today.
- `scripts/check_citations.py` reports a `#"substring"` pinpoint wrapped across a line break as a finding rather than skipping it, in every corpus the default run gates; it reports and does not repair. Pinned by `tests/test_check_citations.py::test_a_pinpoint_wrapped_across_a_line_break_is_a_finding` and `::test_a_wrapped_pinpoint_fails_the_default_run_in_every_corpus`.
- The rule-27 spellings left by the spec-016 consolidation outside the boundary-hardening WP files are converted to `path::Symbol`: `django_strawberry_framework/registry.py`'s module docstring cites `types/converters.py::resolved_relation_annotation` and `types/converters.py::convert_choices_to_enum`, `django_strawberry_framework/types/converters.py::convert_scalar` cites `types/base.py::_build_annotations`, and `django_strawberry_framework/filters/inputs.py` no longer carries the dotted `types.converters.convert_choices_to_enum` spelling.
- The `DONE-017-0.0.6` card body states the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppression in the past tense: `CardItem` 703 and 715 say it was suppressed at `0.0.6` and that `DONE-025-0.0.7` replaced it, `CardItem` 713 describes its guard test as pinning the warning-free import surface, and `CardReference` 62 matches 715 with its card-reference placeholder intact. `django_strawberry_framework/scalars.py` defines `BigInt` as a bare `NewType` registered through `_PACKAGE_SCALAR_MAP` behind `django_strawberry_framework/scalars.py::strawberry_config`.
- The `DONE-018-0.0.6` card body names the private symbol: `CardItem` 723 reads "`finalize_django_types()` runs `_audit_primary_ambiguity()` first", matching `django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity`.
- `DONE-020-0.0.7`'s `#### Package files` lists `django_strawberry_framework/__init__.py` and `django_strawberry_framework/list_field.py`; `django_strawberry_framework/apps.py` is no longer linked to this card and stays on `DONE-021-0.0.7` (its subject) and `DONE-024-0.0.7` (whose `ready()` installs the Trac #37064 patch). No card-files JSON is checked into the repo, so no stored input re-applies the old link; a future hand-authored JSON for card 20 must not list `apps.py`.
- `docs/GLOSSARY.md`'s `## Schema introspection management command` entry states its selector-rejection contract: an empty module path and a relative, leading-`.` module path are each rejected by the shared `_imports` selector validator (`django_strawberry_framework/management/commands/_imports.py::_validate_absolute_module_path`) on both import routes, labelled a schema selector for `--schema` and a dotted object path for a dotted `type` argument, in the same phrasing the `## Schema export management command` entry uses.
- `scripts/check_citations.py --substrings` is part of the gate: the `.pre-commit-config.yaml` `check-citations` hook and the `.github/workflows/django.yml` `--check` run both pass it, so a dead `#"substring"` pinpoint, including one into a script-rendered document (`docs/TREE.md`, `KANBAN.md`, `docs/GLOSSARY.md`), fails the build and an ambiguous one warns. Pinned by `tests/test_check_citations.py::test_substrings_flag_fails_the_run_and_warns_on_ambiguity`.
- `CHANGELOG.md`'s `[0.0.7]` entry for `DONE-026-0.0.7` carries no test counts: it names all six `tests/types/test_converters.py` tests commit `a5c89c98` removed (the three `big_integer` / `positive_big_integer` ones and the three `json_field` ones), its enumeration of `examples/fakeshop/test_query/test_scalars_api.py` lists all nine tests the ship commit `2701eb88` carried, including `test_scalar_specimen_introspects_json_scalar_in_both_shapes`, and it no longer claims the paired-model layout exercises surfaces no other example app touches.
- `docs/GLOSSARY.md`'s `DjangoConnectionField` entry states that `totalCount` selection-gating is directive-resolved: a `totalCount` that `@skip` / `@include` excludes, directly or through its fragment, issues no `COUNT` at the root or in a nested `<field>Connection` window, because the plan-time and resolve-time checks both run `django_strawberry_framework/optimizer/selections.py::should_include`. Live-pinned by `examples/fakeshop/test_query/test_library_api.py::test_genre_connection_total_count_skip_include_no_count`.
- `docs/GLOSSARY.md`'s `DjangoConnectionField` entry documents the already-sliced-`QuerySet` `GraphQLError`: a consumer `resolver=` returning an already-sliced `QuerySet` is rejected before visibility runs, on offset and keyset connections alike, by `django_strawberry_framework/connection.py::_guard_source_not_pre_sliced`, and the entry names the recourse (return an unsliced `QuerySet` or a `Manager`).
- The shipped keyset-cursor feature has its documentation homes without a spec of its own: `docs/SPECS/spec-030-connection_field-0_0_9.md` owns its contract in the `Keyset cursors` section, `docs/GLOSSARY.md` carries a `## Meta.cursor_field` heading, and `CHANGELOG.md` `[0.0.14]` records it. The surface: `cursor_field` sits in `django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`, is validated at class creation by `django_strawberry_framework/types/base.py::_validate_cursor_field` and at finalization, and runs through `django_strawberry_framework/keyset.py`.
- `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` #"the two milestone rows now cite board cards" claims `docs/README.md`'s two milestone rows cite board cards `052` and `067` through reference-style links. Measured 2026-08-25: `docs/README.md` cites NO card number at all - neither its `0.1.0` row (#"beta release: feature parity") nor its `1.0.0` row (#"stable release: full") carries a card reference in any form. Both digits are wrong and so is the claim's subject, which is why this is the ONE site the 2026-08-25 card-renumber sweep left deliberately unshifted: moving `052` to `053` would have produced a differently-false sentence while implying the claim had been verified. The same sentence's history half (the literal ids `BETA-033-0.1.0` and `STABLE-042-1.0.0` it says were replaced) is correct as history and is not in scope.
- `docs/SPECS/spec-058-graph_substrate-0_1_1.md` #"### Decision 10 - joint cut at" had a heading its own in-file links could not reach: the heading punctuates as "joint cut at `0.1.1`: release state" (colon) while both links to it spelled the slug `...-at-011--release-state-...` (the double hyphen a spaced em dash produces). Measured 2026-08-25 while re-syncing heading/anchor pairs through the card renumber. REPAIRED 2026-08-29 in the spec-stem rename sweep by moving the LINK side to match the heading, because the sweep changed the heading numeral and would otherwise have left the pair broken in a second way; the sibling `spec-060-search_fields-0_1_2.md` Decision 10 pair was repaired the same way. The general fix is still owed: this card scopes the spec-consistency checker, and `spec-060`'s Decision 11 heading/link pair (5 links) is the same defect, still open.
- Bare card numerals that were ALREADY stale before the insert-at-052 renumber, so the renumber's +1 does not repair them - each needs a read against its live referent (a +6 after the 2026-08-29 board inserts), not a shift. Measured 2026-08-25, eight sites in two surfaces the renumber deliberately left alone because a numeral wrong in BOTH numberings is a separate defect. (a) Board DB, `Card.planning_note` - a column no renumber has ever swept, on `TODO-BETA-060-0.1.2` (`card-054-owned completion bookkeeping`, `Spec-054: Decision 7`) and `TODO-BETA-061-0.1.2` (`card 054's Meta.search_fields surface`, `card 054's spec text`, `glossary promotion out of card 054's intermediate status`); every one names the SEARCH card, which was 054 only before the 2026-08-08 graph-substrate insert and is 060 today. (b) Board DB, `CardItem` text on `TODO-BETA-061-0.1.2` - scope items and one `definition_of_done` item reading `Card 054 deliberately ships only unprefixed OR-of-icontains search`, `Card 054 ships Meta.search_fields to main`, and `its card-054 intermediate status`, all three the same search-card referent. (c) Two spec-body label/target mismatches the renumber preserved verbatim rather than half-correcting: `docs/SPECS/spec-055-fieldset-0_1_1.md #"Meta.search_fields"` renders the link text `spec-055` over a target resolving to `spec-056-search_fields-0_1_2.md`, and `docs/SPECS/spec-056-search_fields-0_1_2.md` pairs `spec-054` with `TODO-BETA-058-0.1.1` for the same `FieldSet` referent - DISCHARGED 2026-08-29 by the spec-stem rename sweep, which set each link text from its ref-id target and repointed the pair onto `spec-059`/`spec-060`; parts (a) and (b) remain open - a spec stem and a card id one apart, so exactly one of the pair is wrong. Verify each referent before editing: a blanket +1 over this population would make (a) and (b) wrong in a new direction.
- Every `Decision N` reference in `tests/test_relay_connection.py` names its spec (`spec-032` or `spec-033`), so none falls back on the module docstring's `spec-032`.
- `scripts/check_citations.py` resolves `spec-<NNN> Decision <N>` (also `spec-<NNN>-<stem>` and `Decisions`, wrapped or not) in the gated corpus against the `Decision <N>` headings of the spec found by number, and fails the run when the heading is missing. Pinned by `tests/test_check_citations.py::test_a_spec_decision_citation_must_name_a_decision_heading`. The gate catches only a citation to a non-existent Decision: it does not see an ordinal inside a Decision's item list, a citation by heading text, or a citation to a Decision that exists but does not state the claim. The durable instrument for those is the spec-side convention in `spec-033` Decision 6's introduction, where a citation naming the arm by content carries its own claim.
- `docs/TREE.md` describes every post-ship optimizer module (`join_taxonomy`, `lateral_fetch`, `nested_fetch`, `nested_planner`, `predicates`, `selections`, `single_parent_fetch`) and `keyset.py` / `utils/connections.py` beside them, rendered by `scripts/build_tree_md.py` from each module's docstring; a docstring edit plus a regenerate is the only way the tail changes.
- Numbered-item citations in first-party `.py` are anchored. Every spaced `Decision N` in a file that names no spec carries its `spec-NNN` prefix (the former population was `django_strawberry_framework/permissions.py`, `tests/test_apps.py`, `django_strawberry_framework/optimizer/hints.py` and `django_strawberry_framework/management/commands/inspect_django_type.py`), the `Finding N` sites in `tests/forms/`, `tests/mutations/` and `tests/rest_framework/` and the `Revision N` sites in `examples/fakeshop/test_query/test_library_api.py` no longer point at nothing, and the lowercase `tests/types/test_resolvers.py #"per spec-023 Decision 5"` carries its stem. Sentence-initial capital-S `Spec-NNN` docstring openers resolve and are not rot. Card-id anchors are valid anchors, and a bare `Decision N` in a file naming exactly one spec follows the accepted convention. Census rules: count occurrences with `grep -oh | wc -l`, never `grep -c`; `\b` is PCRE only, so every command must be `-P` and paired with a positive control.
- No first-party `.py` cites a shipped spec by line number: the `tests/mutations/test_sets.py` (spec-036), `tests/optimizer/test_extension.py` (spec-033) and `examples/fakeshop/config/settings.py` (spec-039) sites name the owning `spec-0NN Decision N` or heading instead, as the `optimizer/walker.py` and `tests/optimizer/test_walker.py` spec-035 sites already did. Census instruments for this class: scan `edge case NNN` as well as `lines? NNN`, allow a comment-continuation `#` between the token and the number, and scan line pairs, since no single-line pattern sees a wrapped citation. The 12 live-source `(line NNN)` self-citations in `tests/types/test_resolvers.py` and `tests/test_exceptions.py` are a separate item. **One maintainer ruling is owed**, on `tests/orders/test_sets.py #"per cookbook line 280"` and `tests/orders/test_factories.py #"cookbook lines 124-130"`: the referent is `django-graphene-filters`' `examples/cookbook/` prior art, outside rule 27's reach only when pinned at a named upstream version, and neither names a file or a version, so either complete them to an upstream path plus pinned version and keep the line numbers, or drop the line numbers and cite the upstream symbol.
- `docs/SPECS/appx/spec-046-transport_security-0_0_14-terms.csv` lists the 8 `docs/GLOSSARY.md` entries the transport-security card authored (`djangographqlview`, `request-body-cap`, `utf-8-wire-contract`, `websocket-consumer-injection-seam`, `websocket-revalidation-window`, `connection-scoped-revocation`, `websocket-host-boundary`, `graphqlrequestbodyboundarymiddleware`), each with a distinct anchor and a reference-style link in spec-046, and `manage.py import_spec_terms` gives each a `spec-046` `GlossarySpecMention` row and a `CardGlossaryTerm` link to that card. `scripts/check_spec_glossary.py::load_terms` still validates CSV rows forward only, so a missing row stays invisible to it.
- `CHANGELOG.md`'s `[0.0.9]` entry for the two nullability-override `Meta` keys still describes the overrides as scalar-scoped: `CHANGELOG.md #"decouple a scalar field's GraphQL nullability"` and the same paragraph's "scalar-only, and the override flips". The shipped boundary is non-relation: `django_strawberry_framework/types/base.py::_validate_nullability_override_targets` rejects relation targets by name and `django_strawberry_framework/types/base.py::_build_annotations` threads the `force_nullable` tri-state into `convert_field_output`, which also covers the file/image output objects, so `required_overrides` can force a non-null `DjangoFileType!`. `docs/GLOSSARY.md #"**Non-relation scope.**"` carries the corrected wording and is a near-word-for-word twin of the CHANGELOG paragraph, so the replacement text does not have to be invented. **Do not sweep** the three `[0.0.6]` sites in the section beginning `CHANGELOG.md #"Annotation-only scalar field overrides on"`: they name the `Scalar field override semantics` contract, which is genuinely scalar-scoped.
- A maintainer ruling: whether `AGENTS.md` rule 27 governs `CHANGELOG.md` at all. Measured 2026-08-27 that file carries 0 raw `path:NN` references, 3 compliant `path::Symbol` citations, 14 dotted package import paths, and 33 bare `` `path.py` `` references with neither symbol nor `#"substring"` pinpoint. `scripts/check_citations.py` gates first-party `.py`, `KANBAN.md` (`MARKDOWN_SOURCES`) and the spec corpus, and no other markdown, so nothing checks `CHANGELOG.md` in either direction. The dotted forms are the crux and cannot be swept mechanically, because the same spelling means two different things: `django_strawberry_framework.testing` in a release note is a consumer import path that rule 27's `path::Symbol` shape would corrupt, while a private helper named inside `optimizer/plans.py` is a source reference rule 27 does cover. Option one, `CHANGELOG.md` joins the gate's markdown corpus under the same real-rot-only rule `KANBAN.md` gets, with dotted package paths declared user-facing API and exempt: 3 citations start being verified, the 33 bare file references need a decision of their own, and the exemption has to be expressed in the script rather than in prose. Option two, `CHANGELOG.md` stays out of scope as a release record rather than a source-reference surface: nothing changes today, and the question stops being re-raised each cycle only if the exclusion is written down. **Do not treat the 14 dotted import paths as violations** under either option without the exemption being settled first.
- Five Done cards carry 14 unticked `definition_of_done` items whose substance verifiably landed, so the boxes are bookkeeping rather than open obligations. Measured by ORM 2026-08-27 across every `done` card: card 35 (2 items), card 44 (6), card 46 (1), card 47 (3), card 49 (2). **Card 35's two must stay unticked** - both open "**[DEFERRED to the abstract-return optimizer entry card**" and are deliberate deferral markers, not incomplete work; the sweep population is the other 12. Card 46's single box is the one worth stating precisely, because it is the only one whose verification is split: it reads "Full suite green at 100% coverage (maintainer/CI gate); ruff + trailing-comma clean; manage.py check + makemigrations --check clean", and its first three clauses are gated on every push and PR by `.github/workflows/django.yml` (which runs `ruff check`, `ruff format --check`, `scripts/check_trailing_commas.py --check` and owns the `fail_under = 100` node) while its last two are gated by nothing - neither that workflow nor `.pre-commit-config.yaml` runs either Django management check. Re-derived rather than assumed: `manage.py makemigrations --check --dry-run` reports "No changes detected" and `manage.py check` reports "System check identified no issues (0 silenced)" at HEAD, so every clause holds. Fix is an ORM edit setting `is_complete=True` on the 12 non-deferral items plus `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py`; `CardItem` also carries `verified_at` / `verified_by` / `verification_kind`, all null on every one of the 14, so the tick should record which instrument established it rather than land as a bare boolean - and for card 46's box that instrument is CI for three clauses and a manual run for two, which is itself the argument for either adding the two management checks to the hygiene job or narrowing the box to what a gate can prove. Note the renderers do not read `is_complete` for these rows' display state, so the tick is a data correction rather than a visible one; this pairs with this card's existing item recording that the `Verified in upstream` section's per-bullet completion state is unpopulated board-wide.
- `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`'s `## Non-goals` never excludes PostgreSQL range fields, leaving the one spec that owned the deferred-scalar boundary silent on the field class an incoming `graphene-django` schema is most likely to carry across it. Re-derived 2026-08-28 rather than taken from the finding's own wording: that section carries **nine** bullets of which **four** are postgres-scoped (no multi-dimensional `ArrayField`; no outer `choices` on `ArrayField` / `HStoreField`; no dedicated `HStore` scalar; no postgres driver in dev dependencies), not the seven the finding claims, and `grep -c RangeField docs/SPECS/spec-017-deferred_scalars-0_0_6.md` returns 0 - the spec's four `range` hits are all the `BigInt` 32-bit / int64 sense. The behavior is already true in code and only the record is missing: `django_strawberry_framework/types/converters.py` soft-imports `ArrayField` and `HStoreField` only, and every other `django.contrib.postgres.fields` class falls through `django_strawberry_framework/types/converters.py::scalar_for_field` to `ConfigurationError`. The owed bullet states the exclusion and names the recourse - a consumer-registered scalar for the range type, the same escape hatch every other deferred scalar uses - and grounds it in the contract rather than in effort: `graphene-django` maps every range field to `List(base)`, and a two-element list cannot round-trip a two-ended interval's per-end inclusivity. Spell the postgres class by its full dotted path in the bullet, because the package already ships an unrelated `django_strawberry_framework/filters/base.py::RangeField` (the `django_filters` form field behind `RangeFilter`) and a bare `RangeField` greps to the filter surface instead. Text edit in one archived spec; no code, no glossary, no board row.
- No standing document says where dataloaders sit, so a migrant arriving from `graphene-django`'s N+1 chapter cannot tell whether they are supported here, discouraged, or replaced. Measured 2026-08-28: a case-insensitive `dataloader` grep returns 0 in `docs/GLOSSARY.md`, `README.md`, `docs/README.md`, `CHANGELOG.md`, `TODAY.md`, `BACKLOG.md`, `docs/TREE.md` and `KANBAN.md` - eight for eight - and the only occurrence anywhere in the tree is a one-clause follow-up aside in `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`. What is owed is two facts and not a recommendation: `strawberry.dataloader.DataLoader` ships with the engine and is available unchanged (nothing in this package wraps, patches or competes with it - import-checked in the project venv 2026-08-28), and this package's own answer to N+1 is the optimizer plus strictness, so a consumer reaches for a dataloader only where the optimizer has no plan to make. Two homes, one sentence each: a clause on the `docs/GLOSSARY.md` `## Strictness mode` entry, which already owns the N+1-detection vocabulary and is DB-generated - edit the fakeshop glossary app's `GlossaryTerm.body` and re-render with `scripts/build_glossary_md.py`, never hand-edit - and a line in `README.md`'s `## Is this for you?` section beside the existing `Strictness / N+1 detection` bullet, which is a plain text edit. Rides the same ORM edit and render as this card's other glossary items. The `0.1.8` migration guides get a one-line mention of the same fact, but that half is the migration-guides card's and explicitly not this one's.
- `README.md` never tells a migrant that unregistered relation targets fail loudly, and that is the first thing many of them will hit: `graphene-django` silently drops the field and `strawberry-graphql-django` falls back to a `DjangoModelType { pk }`, while this package raises at `finalize_django_types()` with an error naming source model, source field and target model (`django_strawberry_framework/types/finalizer.py::_format_unresolved_targets_error`). Re-derived 2026-08-28, and the finding narrows in the process: the FACT is already documented twice - `docs/GLOSSARY.md`'s `## Definition-order independence` entry states the error and its most common cause, and `docs/README.md` #"The most common failure mode is forgetting to import a module" states the same beside its finalization instruction - so what is missing is not the behavior but its MIGRATION framing, which exists in no file. The note is one or two sentences in `README.md`'s `## Is this for you?` section, where the two `Coming from ...?` paragraphs already address exactly this reader and neither mentions it. It has to name what each upstream does instead, because "we raise here" is only actionable to someone who knows their old schema was quietly dropping the field. Deliberately minimal and deliberately early: the full guides are the migration-and-adoption-guides card at `0.1.8` and are NOT this card's scope, and the beta-claim carve-out sentence belongs to the beta release card. Plain text edit, one file.
- `docs/GLOSSARY.md`'s `## Choice enum generation` entry understates a shipped capability: it opens "`CharField` / `TextField` with `choices=...` generates a Strawberry enum", while the code enums ANY field that declares choices. Verified 2026-08-28 in `django_strawberry_framework/types/converters.py::convert_scalar`, which resolves the column through `django_strawberry_framework/types/converters.py::scalar_for_field` and then substitutes `django_strawberry_framework/types/converters.py::convert_choices_to_enum` whenever the field's `choices` is truthy - there is no field-class test anywhere on that path. The corrected sentence needs the two real exclusions, which are rejections rather than pass-throughs: outer `choices` on an `ArrayField` and on an `HStoreField` each raise [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) (ambiguous at the GraphQL boundary; declare `choices` on `base_field` for an element-level enum). Integer choices work - `_sanitize_member_name` casts to `str`, so an `IntegerChoices` value becomes `MEMBER_1`, pinned at `tests/types/test_converters.py::test_choice_member_name_sanitization` - which makes us STRICTER than `strawberry-graphql-django`, which skips them, and the current wording surrenders that parity claim in the one document the `0.1.0` parity audit reads. Record the evidence boundary while correcting it: no example model carries an integer-choices column, so the live `/graphql/` tier does not pin this and the support rests on the package test plus the audit's live probe. DB-generated - edit the fakeshop glossary app's `GlossaryTerm.body` and re-render with `scripts/build_glossary_md.py`, never hand-edit; rides the same ORM edit and render as this card's other glossary items.
- `KANBAN.md`'s `### Still not implemented` list names `permissions.py` among the Layer 3 subsystems that are "still planned only", and it shipped at `0.0.10` (`DONE-034-0.0.10`, `docs/SPECS/spec-034-permissions-0_0_10.md`): `django_strawberry_framework/permissions.py` is on disk, root-exported and glossary-documented. Two corrections to the finding's own routing before it is actioned. FIRST, this is not a `CardItem`. Located 2026-08-28 by an ORM sweep over every text column in the kanban app, the sentence lives in `BoardDoc` pk 4 (`namespace="kanban"`, `key="snapshot"`, kind `Reference`, title `Snapshot`), so the edit is `BoardDoc.body` plus a `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` regenerate - a `CardItem`-scoped sweep returns nothing here and reads as already-fixed. SECOND, only ONE of that bullet's four entries is wrong: `aggregates/` and `fieldset.py` are genuinely absent, and `utils/queryset.py` is a deliberate near-miss a sweep must not "fix" - it is `BACKLOG.md`'s item-36 "promote embedded helpers to `utils/queryset.py` only when a second subsystem needs them", a planned singular module, NOT a typo for the shipped `django_strawberry_framework/utils/querysets.py`. Deleting the one line leaves the other three correct.
- `Meta.nested_fields` and `NestedSerializerConfig` are shipped, root-exported, live-tested surface with zero presence in any standing document. Measured 2026-08-28: a combined `nested_fields` / `NestedSerializerConfig` grep returns 0 in `docs/GLOSSARY.md`, `README.md`, `docs/README.md`, `CHANGELOG.md`, `TODAY.md`, `BACKLOG.md`, `docs/TREE.md` and `KANBAN.md` - eight for eight, so this is ABSENT rather than merely not-lookupable, which is the distinction this card's [`Meta.cursor_field`](docs/GLOSSARY.md#metacursor_field) bullet had to make and the reason that one is a decision and this one is not. The surface is real: `django_strawberry_framework/rest_framework/inputs.py::NestedSerializerConfig` is the explicit per-field opt-in for nested serializer inputs (`Meta.nested_fields = {"shelves": NestedSerializerConfig()}`), it is exported from the package root through the lazy attribute map in `django_strawberry_framework/__init__.py`, a nested field NOT named in the map still fails loud, and the whole path is pinned over `/graphql/` by `examples/fakeshop/test_query/test_library_api.py::test_create_branch_with_nested_shelves_over_http` beside its hidden-target and validation-path siblings. What is owed is a `## Meta.nested_fields` glossary heading - every other `Meta` key has one - covering the opt-in, the fail-loud default for an un-named nested field, and the contract that the consumer's own serializer `create()` performs the nested write (the framework never auto-saves the relation). DB-generated: add the `GlossaryTerm` row and re-render with `scripts/build_glossary_md.py`, never hand-edit. The changelog half is owed too and is not a judgement call - the feature shipped at `0.0.13` under `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`, and that release's `## [0.0.13]` entry describes [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) without mentioning nested inputs at all.
- `docs/SPECS/spec-034-permissions-0_0_10.md` routes a capability to a `BACKLOG.md` home that was never created, so the package's answer to object-level permission backends is recorded nowhere. That spec's out-of-scope entry #"Object-level permission backends (guardian-style) and per-field permission" says post-`1.0.0` differentiation would go through `BACKLOG.md`; measured 2026-08-28, a case-insensitive `guardian` grep over `BACKLOG.md` returns 0, so the pointer resolves to nothing. The missing record is a composition note rather than a refusal of the need: binding a specific third-party permission backend into framework queryset construction would couple the package to that backend's table layout, and the composition point is already public - a consumer calls `get_objects_for_user(info.context.request.user, "app.view_thing", queryset)` from the type's own `get_queryset`, which composes with filters, orders, connections, node refetch and the cascade because every one of them runs through the same hardened visibility boundary. Decide the home first, then write it once: either create the `BACKLOG.md` row that spec promises, or restate the spec entry so it stops pointing at a row that does not exist.
- `docs/SPECS/spec-038-form_mutations-0_0_12.md` #"### Reference-package parity checkpoint" carries no verdict on `graphene_django/forms/types.py::DjangoFormInputObjectType`, the one graphene-django forms surface that otherwise-thorough table omits. Measured 2026-08-28: `DjangoFormInputObjectType` greps to 0 in that spec, so the omission is silent rather than deferred, and a reader auditing forms parity against it finds a gap with no disposition. The verdict that belongs in the table is a refusal, and the card's own design already supplies the reasoning: a standalone form-derived input object exists upstream so a hand-written Relay mutation can borrow a form's shape as a nested `data:` argument, which is a workaround for not having a form mutation flavor rather than a capability of one. Here `Meta.form_class` on [`DjangoModelFormMutation`](docs/GLOSSARY.md#djangomodelformmutation) / [`DjangoFormMutation`](docs/GLOSSARY.md#djangoformmutation) generates inputs bound to the mutation that validates them. Add the row so the absence reads as decided rather than missed.
- The node-identity refusal is recorded for graphene-django's spelling and not for strawberry-graphql-django's, so half of it is invisible to a migrant searching the other name. Measured 2026-08-28: `lookup_field` resolves across `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` at five sites including its out-of-scope entry, while a combined `key_attr` / `DEFAULT_PK_FIELD_NAME` grep over `docs/`, `BACKLOG.md`, `KANBAN.md` and `README.md` returns 0. Those are strawberry-graphql-django's spelling of the same idea - `strawberry_django/settings.py` `DEFAULT_PK_FIELD_NAME` plus `key_attr` on the relay node - and one argument rejects both: resolving a global ID against a configurable non-pk column makes node identity a function of settings, so the same opaque ID then means different rows in two deployments of the same schema. The answer is the pk, with a consumer-authored resolver where a natural key must be addressable. Add the second spelling beside the recorded one; a verdict that names only one upstream's word for a surface both ship is a half-recorded verdict.
- BACKLOG.md's 'Moved out of this file' section states items 36/37/38 'move to `AGENTS.md` / `CONTRIBUTING.md`' (public-surface promotion discipline; shared queryset introspection helpers - note the shipped module is `utils/querysets.py`, plural, not the `utils/queryset.py` the note names; layered manual relation override test policy). Verified 2026-08-29: none of the three rules is present in either target file - the transfer never landed. Land the three rules (or record where each actually belongs) and correct the BACKLOG note.
- Twelve live-source `(line NNN)` self-citations and the two `cookbook line(s)` sites have no owning card, because this card's line-number-citation item explicitly routes them to "a live-code batch, not a documentation pass" and no batch names them. Measured 2026-09-01 by the spec-035 residual cycle over the 433-file `.py` corpus with a per-file `re.sub(r"\s+", " ", text)` flatten (the only instrument that survives both a wrap and a `#` comment-continuation): `grep -rnoE '\(lines? [0-9]+' --include='*.py'` returns **9 in `tests/types/test_resolvers.py`** (`:1797, :1802, :1808, :1817, :1828, :1908, :1915, :1920, :1931`) and **3 in `tests/test_exceptions.py`** (`:459, :464, :481`), plus `tests/orders/test_sets.py:169` #"per cookbook line 280" and `tests/orders/test_factories.py:250` #"cookbook lines 124-130" whose upstream-prior-art ruling this card already carries. These cite a live package source file's own line numbers, which `AGENTS.md` rule 27 wants as `path::Symbol` or `#"substring"`, and they are actively rotting: `types/resolvers.py` has moved under at least three of them. **Routing rule, not a sweep:** each site folds into whichever `TODO-ALPHA-053-0.0.15` WP batch legitimately opens its file, and only the residue no batch opens belongs to this card - the same boundary this card's spec-016 rule-27 item already draws. Precedent for the fix shape: the spec-035 residual cycle closed one citation of exactly this class in `tests/types/test_resolvers.py` (`git show 8c05f7fc:docs/builder/bld-035-final.md` D12) because that cycle already owned the file, replacing the line number with a `path::Symbol #"substring"` pair and proving the anchor resolves exactly once - do that, never a bare `path:NN` to `path::Symbol` mechanical rewrite, since three of these targets have moved and the symbol must be re-read against the live body first.
- The `0.0.14` mutation write hardening (the completion-spanning transaction, the `DjangoSchema` requirement, `Meta.select_for_update`'s lock semantics, single-write-alias pinning, the retryable `conflict` envelope, the immutable authorized-pk snapshot, the phased alias guard, the strict-`bool` authorization contract and the point-in-time authorization rule) gets its owning spec on TODO-ALPHA-079-0.0.17. `spec-036`'s corrected Decisions 8, 10 and 15 stay the boundary of what `spec-036` claims.
- **A failed generated mutation field nulls the whole response, hiding earlier fields that already committed.** Generated mutation payloads are non-null (`CreateItemPayload!`), so an error on a top-level generated mutation field - a completion failure, or a window whose connection was closed inside it (`django_strawberry_framework/schema.py::DjangoMutationExecutionContext._refuse_uncommitted_window`) - propagates to the `Mutation` root and the response carries `data: null`, although each serial field before it committed its own transaction. This is spec-correct non-null propagation, stated in `docs/README.md`'s `DjangoSchema` paragraph; the only fix is nullable generated payloads, a public-schema change for every consumer. Decide it with the owning spec for the `0.0.14` write hardening (the item above). Measured 2026-09-25.
- `tests/test_ci_governance.py::test_every_staged_todo_anchor_names_an_open_spec` fails any `TODO(spec-<NNN> ...)` anchor in first-party source whose spec has no card on the board or whose card is `Done`, so a staged anchor cannot outlive the spec that staged it.
- `docs/GLOSSARY.md`'s [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope) entry describes the 2-member shape and never mentions `FieldError.codes` or `FieldError.path`, the two additive client-ergonomics members shipped at `0.0.13`. They are the whole point of the envelope for a client that wants to branch without parsing localized human text or the dotted `field` string, so their absence from the glossary is an ABSENT-surface gap rather than a wording nit. Edit via the DB and re-render, never by hand. Measured 2026-09-01 by the spec-036 residual cycle.
- No stranded review-round label survives in `tests/` or `examples/`: `tests/mutations/test_resolvers.py` no longer cites `spec-036 FV-1`, `tests/test_relay_node_field.py` no longer names `the P1 bug` / `the P2 bug`, `examples/fakeshop/test_query/test_library_api.py` no longer says `the P0`, and `tests/test_connection.py` carries no `P3a` / `P3b` type names; each site states the invariant it pins by content. Count with a Python lookaround: a left-anchored `(^|[^A-Za-z0-9_-])TOKEN` alternation returns 0 under `ugrep` even where the token is live.
- **One instrument hazard left in the builder corpus, needing a corpus-ratchet edit that names the bytes it retires.** (a) is discharged: no recipe prescribes a bare `/tmp` - `docs/builder/BUILD.md`'s floor-venv recipe and `START.md`'s copy both build under `<scratch>/dsf-floor`, and `scripts/prove_failability.py` honours `TMPDIR` in code and docstring alike. (b) is half done: `docs/builder/BUILD.md` #"Prove the venv before trusting the run" forbids piping `uv venv` / `uv pip install` through `tail` or `head` (the pipeline reports the last command's status, so a refused venv followed by two refused installs reads as exit 0) and asks for `<scratch>/dsf-floor/bin/python --version` to report the floor interpreter before the focused tests; `START.md`'s copy of the same recipe carries neither sentence, so a reader following `START.md` alone still records an unproven floor. The confirming datum, measured 2026-09-10: the `dsf-floor` path two recorded floor runs name had lost its `pyvenv.cfg` while a sibling `dsf-floor-pass2` was intact, so the decay is real and a floor record naming only a scratch path is not auditable afterwards. No recorded floor claim is falsified by the hazard; it is a gap in what a later reader can audit.
- **`BACKLOG.md`'s error-envelope spec entry is the last `rev6`-vocabulary citer of `spec-039` in the tree, and it is a stranded ordinal.** It reads `BACKLOG.md` #"spec-036 Decision 7 + spec-039 rev6", naming a numbered revision vocabulary that the spec-039 residual cycle retired on 2026-09-10 - `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` now carries 0 occurrences of `rev6`, so both the token and the two ordinals behind it resolve to nothing. One substitution, recorded by that cycle so the next pass does not re-derive it: replace the parenthetical's `spec-039 rev6 #4/#13` with a content restatement - `spec-039`'s error-envelope `codes` / `path` improvements - which is the same restate-by-content remedy this card's stranded-ordinal bullets prescribe, and never a renumber. Homed here 2026-09-10 by that cycle; `BACKLOG.md` was outside its spec-and-`.py` fence.
- **`docs/GLOSSARY.md`'s [Debug-toolbar middleware](docs/GLOSSARY.md#debug-toolbar-middleware) entry enumerates two robustness divergences where the module names three, and the spec's `-terms.csv` row still describes the pre-flip status.** Measured 2026-09-12 by the spec-042 reconciliation cycle at `docs/GLOSSARY.md` #"Two deliberate robustness divergences": the entry names the `isinstance(view, type)` guard and the `_get_payload` response-shape bail, while `django_strawberry_framework/middleware/debug_toolbar.py` #"named here rather" names a third - `_postprocess` returns an already-encoded response untouched, since appending the bridge script to a compressed body corrupts it - and names them rather than counting them, which is the shape the entry should copy. The entry's status line already reads shipped (`0.0.14`) while `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv` still says the GLOSSARY status is planned for `0.0.14` until the joint cut flips it; that `notes` cell is checked by no gate against the spec (`import_spec_terms --check` only proves the DB copies it), so it is corrected here or not at all. DB-backed: an ORM edit plus a regenerate, never a hand-edit.
- Discharged: `django_strawberry_framework/filters/base.py::_materialize_list_shaped_values` no longer enumerates its consumers, and the one-caller GlobalID wrapper is inlined at `django_strawberry_framework/filters/base.py::GlobalIDMultipleChoiceFilter.filter`; the fail-closed list-shape contract is stated once at the owner.
- Discharged: `django_strawberry_framework/utils/permissions.py::_related_declarations` states the read its body makes (a real `dict` through the unbound `dict.items`, any other `Mapping` through its own `items()`), and `django_strawberry_framework/utils/input_values.py::related_declaration_mapping` points at it.

#### Definition of done

- [ ] Every `Scope` bullet on this card is either discharged in the tree or explicitly deferred onto a named card with a recorded reason. Modeled on the beta release card's parity-audit gate: `DONE` or explicitly deferred, never silently dropped.
- [ ] Each discharged bullet's claim is re-derived at close rather than trusted from the bullet text: a finding's grep vocabulary is not its population, and several bullets here record their own counting-basis traps.
- [ ] `docs/GLOSSARY.md` and `docs/TREE.md` are regenerated from their generators (never hand-edited) after the sweeps land, and `KANBAN.md` / `KANBAN.html` are regenerated from the board DB.
- [ ] `scripts/check_citations.py`, `scripts/check_spec_glossary.py`, and `scripts/check_trailing_commas.py --check` pass over every file the card touched.

#### Files likely touched

- `docs/SPECS/*.md` and `docs/SPECS/appx/*` - the archived-spec cohort carrying the stale claims
- `docs/GLOSSARY.md`, `docs/TREE.md` - both generated; regenerate, never hand-edit
- `CHANGELOG.md`, `README.md`, `docs/README.md`, `BACKLOG.md`, `CONTRIBUTING.md`
- `scripts/` - the spec/rationale consistency checker several bullets scope
- `examples/fakeshop/db.sqlite3` - the board-DB half of the card-text and spec-path sweeps

#### Why it matters

- The alpha line accumulated 48 documentation-consistency findings between 2026-08-05 and 2026-08-25, each one deferred onto the beta release card by a residual reconciliation cycle. That card's `Definition of done` is release mechanics - version bump, changelog promotion, matrix pass, tag, publish - and not one of its eight items gates a single finding, so at cut time the whole population would have been dropped silently rather than deferred deliberately.
- `AGENTS.md` rule 5 forbids defer-the-real-fix sequencing, and an ungated bullet parked on a release card is exactly that shape. Gating them from inside the release card would keep a documentation sweep inside a release cut; this card is the root-cause fix - the debt owns a card, owns a gate, and blocks the `0.1.0` cut through a dependency edge instead of through prose.

#### Open question

- Answered: `scripts/archive_spec.py` gets its own card, TODO-ALPHA-080-0.0.17, which scopes the three rewrite directions, the link-definition group relocation, the `SpecDoc` sync and a `--check` mode.

#### Card references

- Dependency: This card lands on its own `0.0.17` line after the `0.0.16` cut, owns the solo `0.0.17` cut, and documents the registry surface. -> `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry
- Dependency: This card lands on its own `0.0.17` line after the `0.0.16` cut; the federation `[federation]` extra and carve-out citation land before it. -> `TODO-ALPHA-055-0.0.16` - Apollo Federation as the standalone django-strawberry-federation package
- Related: Takes over this card's write-hardening owning-spec item. -> `TODO-ALPHA-079-0.0.17` - Owning spec for the mutation write pipeline (transaction, locks, write alias, authorization)
- Related: Takes over this card's `scripts/archive_spec.py` open question. -> `TODO-ALPHA-080-0.0.17` - `scripts/archive_spec.py`: mechanize the spec and build-plan archive sweep

<a id="beta_release_cleanup_verification_alpha_beta"></a>
### [TODO-ALPHA-057-0.1.0 - Beta release (cleanup, verification, alpha → beta)](KANBAN.html#beta_release_cleanup_verification_alpha_beta)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `cleanup`, `internal`, `release`, `tests`
- Spec: [spec-057-beta_release-0_1_0.md](docs/SPECS/spec-057-beta_release-0_1_0.md)

#### Predicted files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`tests/base/test_init.py`](tests/base/test_init.py)

#### Dependencies

- `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge

#### Scope

- Version bump to `0.1.0` across the single-sourced `__version__` and everything derived from it, plus `uv.lock`.
- A dated `## [0.1.0]` section atop the patch entries (the open line's `## [0.1.0] - Unreleased` heading is dated at the cut; no bare `[Unreleased]` block exists) with the cumulative Added / Changed / Fixed / Removed roll-up.
- Consumer-facing docs cross-checked against the actual shipped surface, with every "shipped" / "planned" label re-derived rather than trusted.
- The upstream-parity audit pass: every parity claim either `DONE` or explicitly deferred with a recorded reason.
- Full support-matrix test pass at 100% package coverage, then tag and publish.

#### Definition of done

- [ ] Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. The alpha documentation-debt card (`TODO-ALPHA-056-0.0.17`) is `DONE` as well: its own gate is that every bullet it carries is discharged or explicitly deferred onto a named card.
- [ ] Full test pass under each supported `(Python, Django, Strawberry)` combination.
- [ ] Coverage stays at 100% for the package source tree.
- [ ] Version bumped to `0.1.0` in `django_strawberry_framework/__init__.py` `__version__` (hatchling derives the packaging version from it), with `tests/base/test_init.py::test_version` and the `docs/GLOSSARY.md` package-version line in step.
- [ ] `CHANGELOG.md`'s `## [0.1.0]` section dated at the cut (`## [0.1.0] - YYYY-MM-DD`; the open development line carries a `## [<version>] - Unreleased` heading, never a bare `[Unreleased]` block) with a one-paragraph release summary plus the cumulative Added / Changed / Fixed / Removed sections covering `0.0.6` through the last shipped alpha patch.
- [ ] `README.md`, `docs/README.md`, `CONTRIBUTING.md`, `docs/GLOSSARY.md`, and `docs/TREE.md` cross-checked against the actual shipped surface; "shipped" / "planned" status markers updated.
- [ ] Audit pass against the parity findings: every ⚛️ and 🍓 card from the two upstream audits is either `DONE` or explicitly deferred with a recorded reason.
- [ ] The beta parity claim carries a carve-out sentence for per-field read permissions: `0.1.0` ships no per-field read permission at all, where strawberry-graphql-django ships `IsAuthenticated` / `HasPerm` / `HasRetvalPerm` / `HasSourcePerm` with SQL pre-filtering and schema directives. The raise-only `check_<field>_permission` gates arrive with the [`FieldSet`](docs/GLOSSARY.md#fieldset) card at `0.1.1` (spec-059), and the full declarative capability is the post-`1.0.0` `declarative_row_and_field_permissions` row in `BACKLOG.md`. The absence is a missing capability, not the refused `fail_silently` extension shape.
- [ ] The beta parity claim carries a carve-out sentence for model `@property` auto-binding: strawberry-graphql-django auto-types `@model_property` / `@model_cached_property` and plain `property` / `cached_property` from their return annotation, and `0.1.0` binds none of them. The `FieldSet` card delivers resolver-computed fields with `Meta.depends_on` at `0.1.1` but requires a paired `resolve_<field>`, so a migrant's `@property` fields do not auto-bind at `0.1.0` or `0.1.1` either; the owners are the post-`1.0.0` `computed_fields_binding` and `computed_field_optimizer_hints` rows in `BACKLOG.md`.
- [ ] The beta parity claim carries a carve-out sentence for the migration path itself: unregistered relation targets fail loudly at type finalization -- deliberate and argued in spec-009 as error-only, where graphene-django silently drops the field and strawberry-graphql-django falls back to a pk-only type -- and it is the first break many migrants hit, but the guides that would explain it are the Migration and adoption guides card at `0.1.8`. The `0.1.0` claim must state plainly that the migration path is documented later rather than reading as though the guides ship with the beta.
- [ ] Tag the release in git and publish to PyPI.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`

#### Why it matters

- This card is the formal cut-over from alpha (`0.0.x`) to beta (`0.1.0`). When every other Alpha card is in `DONE`, this card is the only thing left between the current state and the beta release. It exists to make the milestone explicit and to give the cleanup / verification work a place to live.
- Without a dedicated release card, the alpha → beta transition becomes an unstructured handful of doc tweaks and version bumps spread across the last few patches. Tracking it explicitly forces the parity audit and the full test pass to happen on a single named slice.
- release card.
- release-blocking.
- final card in the Alpha queue; gates the alpha → beta milestone.

#### Open question

- Answered: connection pagination rejections reach the client as `django_strawberry_framework/utils/connections.py::PaginationArgumentError` with Strawberry's own message and the audited `extensions.code` `PAGINATION_INVALID` (`django_strawberry_framework/utils/errors.py::PAGINATION_INVALID_ERROR_CODE`), set on the class so no raise site spells it.
- The debug extension's caps are not configurable, deliberately: `AGENTS.md` says add a settings key only when the feature that needs it lands, and a deployment wanting a different ceiling is a deployment running the extension in production. Revisit only if a real consumer need appears.

#### Card references

- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-013-0.0.4` - Real M2M coverage
- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-044-0.0.14` - Response-extensions debug middleware
- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-024-0.0.7` - Django Trac #37064 hardening + `safe_wrap_connection_method`
- Related: Every other Alpha card (`DONE-013-0.0.4` through `DONE-044-0.0.14` plus `DONE-024-0.0.7` and `DONE-045-0.0.14`) is in `DONE`. -> `DONE-045-0.0.14` - Sealed get_queryset visibility-boundary policy artifacts
- Dependency: The alpha documentation-debt card discharges before the 0.1.0 cut. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge

<a id="owning_spec_for_the_nested_connection_fetch_strategy_seam"></a>
### [TODO-ALPHA-078-0.0.17 - Owning spec for the nested-connection fetch-strategy seam](KANBAN.html#owning_spec_for_the_nested_connection_fetch_strategy_seam)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `connections`, `docs`, `internal`, `optimizer`, `query-planning`

#### Planning note

Goal: author one spec, through docs/SPECS/NEXT.md, whose subject is the pluggable nested-connection fetch-strategy seam. Today no spec owns it: its contracts are restated inside spec-033 Decision 4, spec-068 Decision 9 and the strategy-extension BACKLOG entries, so those documents describe a surface nothing defines. This card opens that spec; it does not change runtime behavior.

#### Dependencies

- `DONE-033-0.0.9` - Connection-aware optimizer planning

#### Scope

- The seam spans four modules: `django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionStrategy` with `django_strawberry_framework/optimizer/nested_fetch.py::NestedConnectionRequest`, `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`, `django_strawberry_framework/optimizer/nested_fetch.py::active_strategy` and the built-in `django_strawberry_framework/optimizer/nested_fetch.py::WindowedPrefetchStrategy` / `django_strawberry_framework/optimizer/nested_fetch.py::AutoNestedConnectionStrategy`; `django_strawberry_framework/optimizer/lateral_fetch.py::LateralPrefetchStrategy` with `django_strawberry_framework/optimizer/lateral_fetch.py::LateralWindowSpec` and `django_strawberry_framework/optimizer/lateral_fetch.py::build_lateral_sql`; `django_strawberry_framework/optimizer/single_parent_fetch.py::single_parent_spec` with `django_strawberry_framework/optimizer/single_parent_fetch.py::SingleParentWindowQuerySet`; and `django_strawberry_framework/optimizer/join_taxonomy.py::classify_relation_join` with `django_strawberry_framework/optimizer/join_taxonomy.py::RelationJoinDescriptor`.
- Selection surface the spec owns: the `nested_connection_strategy=` kwarg on `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension`, the setting read by `django_strawberry_framework/conf.py::nested_connection_strategy_setting`, and the per-field `django_strawberry_framework/optimizer/hints.py::OptimizerHint` `strategy(name)` hint, with their precedence.
- Take over from spec-033 Decision 4: the strategy roster (windowed, lateral, auto) and auto's choice by the nested queryset's effective alias; the single-parent fast path; the invariant that every backend lands rows under the same package-reserved `to_attr` consumed by the same resolver probe; the single-column `parent_link_field` refusal of the correlated strategies and lateral's downgrade to the windowed body on a non-local or raw order term; `django_strawberry_framework/optimizer/nested_fetch.py::unwindowable_child_queryset_reason` as one strategy-independent gate; and partitioning through the join taxonomy.
- Take over from spec-033 Decision 6 the refusal arm for a window the active strategy refused for every response key, and the hint-precedence paragraph for the strategy hint.
- Resolve spec-033 Decision 11's "Public surface: none" against the released acceptance of consumer-authored `NestedConnectionStrategy` instances, and own the module list for the four seam modules.
- Take over from spec-068 Decision 9 the strategy-interface contract: every strategy, built-in or BACKLOG candidate, consumes the sidecar normalization and the row-identity proof gate; spec-068 keeps the pipeline and cites this spec for the interface.
- Take over the strategy-extension rules restated by the BACKLOG entries `sqlite_correlated_json_nested_fetch`, `mti_aware_lateral_nested_fetch` and `backward_nested_keyset_pagination`: each extends this one seam and preserves its nested contracts rather than adding a parallel path.

#### Definition of done

- [ ] One spec under docs/SPECS has the fetch-strategy seam as its subject and states the contracts listed in Scope.
- [ ] spec-033 Decision 4, Decision 6 and Decision 11 and spec-068 Decision 9 cite the new spec instead of restating the strategy contracts.
- [ ] The BACKLOG strategy-extension entries point at the new spec as the owner of the interface they extend.
- [ ] The GLOSSARY strategy paragraph and its terms-CSV row cite the new spec.
- [ ] The public-versus-internal status of `NestedConnectionStrategy` is decided and matches the released notes.
- [ ] `uv run python scripts/check_citations.py --check --substrings` passes.

#### Files likely touched

- A new spec under docs/SPECS, numbered through docs/SPECS/NEXT.md.
- docs/SPECS/spec-033-connection_optimizer-0_0_9.md and docs/SPECS/spec-068-structural_templates-0_1_6.md (citations replace restatements).
- BACKLOG.md, docs/GLOSSARY.md and the glossary terms CSV.

#### Why it matters

- Three planned strategies and the structural-templates card all build on this seam. Without an owning spec each restates the contract in its own words, and the restatements drift from the code and from each other.

#### Dependencies

- The seam and its strategy contracts were introduced under spec-033; the new spec takes them over and spec-033 then cites it.

#### Open question

- Is `NestedConnectionStrategy` a public extension point (the released notes accept consumer-authored instances) or internal (spec-033 Decision 11)? The answer sets whether the spec carries a compatibility contract.

#### Card references

- Dependency: The seam and its strategy contracts were introduced under spec-033; the new spec takes them over and spec-033 then cites it. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Related: spec-068 Decision 9 (strategies consume the sidecar pipeline) is a constraint on this seam; the strategy-interface half moves onto this card's spec. -> `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching
- Related: Sibling Alpha documentation-debt card for surfaces without an owning spec. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge

<a id="owning_spec_for_the_mutation_write_pipeline_transaction_locks_write_alias_authorization"></a>
### [TODO-ALPHA-079-0.0.17 - Owning spec for the mutation write pipeline (transaction, locks, write alias, authorization)](KANBAN.html#owning_spec_for_the_mutation_write_pipeline_transaction_locks_write_alias_authorization)

- Priority: Medium
- Status: To Do
- Relative size: L
- Labels: `docs`, `internal`, `multi-db`, `mutations`, `permissions`

#### Planning note

Goal: author one spec, through docs/SPECS/NEXT.md, whose subject is the shared write pipeline every model-backed and form write flavor runs inside: its transaction, row locks, write alias, conflict envelope and authorization contract. That machinery shipped at 0.0.14 with no owning spec: none of the nine 0_0_14 specs scopes it, and its contracts are restated inside spec-036, spec-038, spec-039 and spec-040, so those documents describe a surface nothing defines. This card opens that spec; it does not change runtime behavior.

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Scope

- The completion-spanning transaction: `django_strawberry_framework/schema.py::DjangoMutationExecutionContext` opens `transaction.atomic(using=alias)` around each generated top-level mutation field and rolls it back when completion adds errors, and `django_strawberry_framework/utils/write_transaction.py::managed_write_transaction` marks it open; `django_strawberry_framework/utils/write_transaction.py::open_write_pipeline` nests every flavor's atomic block inside it.
- The [`DjangoSchema`](docs/GLOSSARY.md#djangoschema) requirement: `django_strawberry_framework/utils/write_transaction.py::require_managed_write` refuses a generated mutation reached through a plain `strawberry.Schema` with a [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) before any database work, and `django_strawberry_framework/schema.py::DjangoSchema` is the only schema that opens the managed transaction.
- `Meta.select_for_update` lock semantics: the shared validator `django_strawberry_framework/write_mixins.py::validate_select_for_update` (default `True`, opt-out), and the lock taken through the model base manager over a pk subquery by `django_strawberry_framework/utils/write_transaction.py::base_locked_queryset` and `django_strawberry_framework/utils/write_transaction.py::pipeline_scoped_queryset`, never by attaching `select_for_update()` to a consumer queryset; the clause is a no-op on backends without `FOR UPDATE`.
- Single-write-alias pinning: `django_strawberry_framework/utils/write_transaction.py::resolve_write_alias` asks the router once per operation, and `django_strawberry_framework/utils/write_transaction.py::pin_write_queryset`, `django_strawberry_framework/utils/write_transaction.py::check_instance_write_alias` and `django_strawberry_framework/utils/write_transaction.py::make_cross_alias_save_guard` pin every pipeline query to it; a `get_queryset` that re-routes to another alias fails closed with `ConfigurationError`.
- The retryable `conflict` envelope: `django_strawberry_framework/utils/write_transaction.py::conflict_error` on `id`, mapped from a zero-row forced update by `django_strawberry_framework/utils/write_transaction.py::forced_update_conflict_errors` (over the Django-version-sensitive `django_strawberry_framework/utils/write_transaction.py::not_updated_exceptions`) for the model and `ModelForm` flavors through `django_strawberry_framework/mutations/resolvers.py::save_located_row`, and from a witnessed INSERT under the authorized pk by `django_strawberry_framework/rest_framework/resolvers.py::_guarded_serializer_write` for the serializer flavor.
- The immutable authorized-pk snapshot: `authorized_pk` and `target_state` on `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext`, captured in `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync` right after the locate and before any consumer hook, compared by `django_strawberry_framework/utils/write_transaction.py::reject_substituted_row` (update and `django_strawberry_framework/mutations/resolvers.py::_delete_write_step`) and by `django_strawberry_framework/utils/write_transaction.py::assert_no_target_drift` over `django_strawberry_framework/utils/write_transaction.py::snapshot_target_state` (serializer flavor).
- The phased alias guard: `django_strawberry_framework/utils/write_transaction.py::pipeline_alias_guard` rejects every statement on a non-pinned connection and any non-read statement on the pinned one outside `django_strawberry_framework/utils/write_transaction.py::pipeline_write_phase`; `django_strawberry_framework/utils/write_transaction.py::authorization_phase` is the one narrow exception, permitting the aliases `django_strawberry_framework/utils/permissions.py::resolve_auth_aliases` names inside a database-enforced read-only, always-rolled-back transaction.
- The strict-`bool` authorization contract: `django_strawberry_framework/mutations/permissions.py::_require_sync_bool_auth_result` is the one result check `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` (`check_permission`), `django_strawberry_framework/mutations/permissions.py::run_permission_classes` (`has_permission`) and `django_strawberry_framework/mutations/permissions.py::DjangoModelPermission.has_permission` (`user.has_perm`) share; a coroutine or any non-`bool` return is refused, never read for truthiness.
- The point-in-time authorization rule: authorization runs exactly once per operation in `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise`, after the locate and lock and before decode; a revocation committed after the check is not re-observed, and `django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs` refuses a hook that supplies its own `instance` for the same reason.
- Take the restatements over: spec-036 Decision 8 (the transaction and async boundary paragraph and the `DjangoSchema` requirement), spec-036 Decision 15 and its Error shapes `DjangoSchema` row; spec-038 Decision 8 (the `conflict` mapping, the `authorized_pk` / `target_state` snapshot and the alias guard); spec-039 Decision 8 (the alias guard, the authorization phase, the snapshot and the witnessed-INSERT `conflict`) and its Row locking for model-backed write mutations section; spec-040 Decision 5 (the strict-`bool` result contract); and spec-047 Decision 9's account of the completion-spanning rollback. Each keeps its own flavor-specific rows and cites the new spec for the shared contract.

#### Definition of done

- [ ] One spec under docs/SPECS has the shared write pipeline as its subject and states the nine contracts listed in Scope, each citing its owning symbol.
- [ ] spec-036 Decisions 8 and 15, spec-038 Decision 8, spec-039 Decision 8 and its row-locking section, spec-040 Decision 5 and spec-047 Decision 9 cite the new spec instead of restating those contracts.
- [ ] The GLOSSARY [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) entry (row locking, single write alias, `conflict`, point-in-time authorization) and its terms-CSV row cite the new spec.
- [ ] The nullable-payload question below is decided and recorded in the new spec.
- [ ] `uv run python scripts/check_citations.py --check --substrings` passes.

#### Files likely touched

- A new spec under docs/SPECS, numbered through docs/SPECS/NEXT.md.
- docs/SPECS/spec-036-mutations-0_0_11.md, docs/SPECS/spec-038-form_mutations-0_0_12.md, docs/SPECS/spec-039-serializer_mutations-0_0_13.md, docs/SPECS/spec-040-auth_mutations-0_0_13.md and docs/SPECS/spec-047-resource_policy-0_0_14.md (citations replace restatements).
- docs/GLOSSARY.md (through the glossary app) and the glossary terms CSV.

#### Why it matters

- Every write flavor (model, `ModelForm`, plain form, serializer, auth) runs inside this pipeline and its security rests on these contracts. Without an owning spec each flavor spec restates them in its own words, and the restatements drift from the code and from each other.

#### Dependencies

- The write pipeline grew out of spec-036's resolver pipeline; spec-036 keeps Decisions 8, 10 and 15 as the boundary of what it claims and cites the new spec for the pipeline contracts.

#### Open question

- Should generated mutation payloads become nullable? Today a failed top-level generated mutation field nulls the whole `data` although earlier serial fields already committed; nullable payloads would fix that at the cost of a public-schema change for every consumer.

#### Card references

- Dependency: The write pipeline grew out of spec-036's resolver pipeline; spec-036 keeps Decisions 8, 10 and 15 as the boundary of what it claims and cites the new spec for the pipeline contracts. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: spec-038 Decision 8 restates the conflict mapping, the authorized-pk snapshot and the alias guard for the form flavors; it cites this card's spec instead. -> `DONE-038-0.0.12` - Form-based mutations (Django Forms / ModelForms)
- Related: spec-039 Decision 8 and its row-locking section restate the alias guard, authorization phase, snapshot and lock semantics for the serializer flavor; they cite this card's spec instead. -> `DONE-039-0.0.13` - DRF serializer mutations (`SerializerMutation`)
- Related: spec-040 Decision 5 restates the strict-bool authorization result contract the auth mutations share; it cites this card's spec instead. -> `DONE-040-0.0.13` - Auth mutations (login / logout / register)
- Related: spec-047 Decision 9 describes the completion-spanning rollback the execution deadline relies on; that account moves onto this card's spec. -> `DONE-047-0.0.14` - Execution resource policy: central budget object + value-cardinality walker
- Related: Its write-hardening item tracks this missing owning spec, and its nullable-payload item is decided with it. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge
- Related: Sibling owning-spec card for another shipped surface that no spec defines. -> `TODO-ALPHA-078-0.0.17` - Owning spec for the nested-connection fetch-strategy seam

<a id="scriptsarchive_specpy_mechanize_the_spec_and_build_plan_archive_sweep"></a>
### [TODO-ALPHA-080-0.0.17 - `scripts/archive_spec.py`: mechanize the spec and build-plan archive sweep](KANBAN.html#scriptsarchive_specpy_mechanize_the_spec_and_build_plan_archive_sweep)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `developer-tools`, `docs`, `internal`

#### Planning note

Goal: replace the hand-run archive procedure in docs/SPECS/NEXT.md Step 8 (and its Step 3 pre-write mode) and in docs/builder/BUILD.md "Archiving a plan" with one script, `scripts/archive_spec.py`, that performs every mechanical step, stops on the steps that need judgement, and carries a `--check` mode. This card ships tooling only; it does not change runtime behavior.

#### Scope

- File moves: list every `docs/spec-*.md` other than the active spec, move each to docs/SPECS/ and its `-terms.csv` and `-rationale.md` companions to docs/SPECS/appx/ only when they exist, with `git mv` for tracked files and a plain move for untracked ones, and refuse to overwrite an existing destination.
- Inbound rewrites (other files to a moved spec): every reference-style definition and legacy inline link target naming the old path, in each spelling (`spec-...`, `docs/spec-...`, `../spec-...`), across the citer set Step 8 sweeps (docs/, README.md, GOAL.md, TODAY.md, AGENTS.md), plus source-ref citations whose path is a moved spec. Link text that spells the old path verbatim is rewritten with its definition; other prose naming an old path is reported, not rewritten.
- Outbound rewrites (inside each moved file): every relative target gains one more `../` (two for a rationale moving to docs/SPECS/appx/), classified by Step 8's buckets: repo-root files, docs siblings, the `[next]` definition becoming `NEXT.md`, specs moved in the same sweep, the active spec, source, test, example and script files, and external sibling checkouts; anchors and URLs stay untouched. A spec's own companions gain `appx/`, and a rationale's back-links become `../spec-...md#decision-N`.
- Between moved specs: a definition from one moved spec to another resolves to the new sibling path in the same pass, so the sweep's order never matters.
- Link-definition group relocation: a rewritten definition whose target changes class moves under the matching one of the ten canonical group headers in the `<!-- LINK DEFINITIONS -->` block, an obligation no checker sees today.
- Terms CSVs: verify that the `notes` column of each moved CSV carries no paths, and report any it finds.
- DB sync in the same run as the move: repoint each archived spec's `examples/fakeshop/apps/kanban/models.py::SpecDoc` row through its writable `path` (never the read-only `url`), upsert the active spec's row on its WIP card, then run `manage.py import_spec_terms` so `GlossarySpecMention` rows re-key and old-path rows are reaped by `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::Command._orphan_mentions`.
- Re-renders: `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py` and `scripts/build_glossary_md.py`, so KANBAN.md, KANBAN.html and docs/GLOSSARY.md take the new paths from the DB rather than from hand edits.
- Build-plan archive (docs/builder/BUILD.md "Archiving a plan", restated by docs/builder/worker-0.md pre-flight): move each closed `docs/builder/build-*.md` plan to docs/builder/DONE/ without overwriting, rebase its link definitions one level, append one `git show <sha>:docs/builder/bld-<NNN>-<name>.md` line per artifact with the sha from `git log -1 --format=%h`, sweep inbound `build-<NNN>-` references outside DONE/, and delete that cycle's `bld-<NNN>-*.md` files by explicit path.
- Closing checks, each failing the run: every rewritten definition resolves on disk, `scripts/check_spec_glossary.py --spec <active spec>`, `manage.py import_spec_terms --check`, the three renderers' `--check`, `scripts/check_kanban_anchors.py` and `scripts/check_citations.py --check --substrings`.
- Modes: `--pre-write` runs Step 3's pre-write archive (no active spec yet, so the active-spec rewrites and the WIP `SpecDoc` upsert are skipped). `--check` is the dry run: it writes nothing, prints every planned move, link rewrite, group relocation, DB write and deletion, and exits nonzero while any is pending, so pre-flight can assert a completed sweep. A second writing run is a no-op.
- Stays manual, reported or refused by the script: CHANGELOG.md hits (maintainer owned, so listed and never rewritten); prose naming an old path where the wording needs judgement (listed); historical card-item text, which records the path of its day; choosing the active spec and normalizing the NEXT.md queue (authoring decisions); a build plan whose final box is open (a live cycle) or that lacks a `## Closing record`, and an untracked `bld-` artifact with no sha to cite (each stops the run for the maintainer); staging and committing.

#### Definition of done

- [ ] `scripts/archive_spec.py` exists with a module docstring stating the procedure and its modes, and `tests/test_archive_spec.py` covers the three rewrite directions, group relocation, the `SpecDoc` repoint, each refusal arm, and `--check` exiting nonzero on a pending sweep and zero on a completed one.
- [ ] docs/SPECS/NEXT.md Step 8 and its Step 3 pre-write mode, docs/builder/BUILD.md "Archiving a plan" and docs/builder/worker-0.md pre-flight invoke the script and keep only the manual residue listed in Scope.
- [ ] START.md's scripts table and docs/TREE.md carry the script.
- [ ] A writing run over an already-archived tree changes nothing, and `--check` passes on it.
- [ ] `uv run python scripts/check_citations.py --check --substrings` passes.

#### Files likely touched

- scripts/archive_spec.py and tests/test_archive_spec.py (new).
- docs/SPECS/NEXT.md, docs/builder/BUILD.md and docs/builder/worker-0.md (hand steps replaced by the script).
- START.md (by hand) and docs/TREE.md (through the kanban app).

#### Why it matters

- Step 8 is about 120 lines of hand-run steps, and its misses already stand in the record: the spec-005 documentation-and-archive audit (the three-direction cross-reference sweep and the `SpecDoc` path and terms-CSV verification) never ran; archived specs' inline link text kept naming pre-archival paths while their definitions resolved, because no checker reads link text; a done card's body carried a pre-archive spec path; the archive worked example wrote the read-only `SpecDoc.url` at nine sites; and an archive's glossary re-key left 14 orphaned spec-mention pairs behind.
- Every spec archive repeats the same sweep, so each class of miss recurs until the procedure is one checkable command.

#### Open question

- Should `scripts/archive_spec.py --check` run in pre-commit or CI, so a prior spec left in docs/ beside a new active spec fails the push rather than waiting for the next author's pre-flight?

#### Card references

- Related: Its documentation-debt item asks whether `scripts/archive_spec.py` should exist and whether it warrants its own card; this card is that card. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge
- Related: The closing gate of its build cycle named `scripts/archive_spec.py` as a future maintainer card. -> `DONE-044-0.0.14` - Response-extensions debug middleware

## To Do - Beta (1.0.0)

Cards that complete the django-graphene-filters Layer-3 richness on top of parity (`fields_class`, `aggregate_class`, `search_fields`, plus pre-stable cleanup). Each card targets its own `0.1.x` patch within the road to **1.0.0**. The final card in this column is the `1.0.0` release itself (API freeze, cleanup, verification, beta → stable cut-over). Cards in NNN order = planned ship order.

<a id="graph_substrate_shared_graph_policy_and_dependency_planning"></a>
### [TODO-BETA-058-0.1.1 - Graph substrate: shared graph policy and dependency planning](KANBAN.html#graph_substrate_shared_graph_policy_and_dependency_planning)

- Priority: High
- Status: To Do
- Relative size: L
- Labels: `internal`, `layer-3`, `optimizer`, `permissions`, `query-planning`
- Spec: [spec-058-graph_substrate-0_1_1.md](docs/SPECS/spec-058-graph_substrate-0_1_1.md)

#### Predicted files

- `django_strawberry_framework/extensions/graph.py` (planned)
- `django_strawberry_framework/graph/` (planned)
- `django_strawberry_framework/utils/predicates.py` (planned)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- `tests/graph/` (planned)

#### Planning note

The first of two graph foundation cards — the framework-internal graph-planning vocabulary (`GraphPathPlan`, `PredicatePlan`, `EdgeScope`, `FieldDependencyPlan`, `RowIdentityProof`) plus the operation-scoped dependency memo, extracted into one shared `django_strawberry_framework/graph/` package boundary **before** [`FieldSet`](docs/GLOSSARY.md#fieldset) (TODO-BETA-059-0.1.1), search (TODO-BETA-060-0.1.2), and [`AggregateSet`](docs/GLOSSARY.md#aggregateset) (TODO-BETA-062-0.1.3) freeze three private versions of the same machinery. Driven by a production audit of a five-root, graph-shaped schedule calendar; the general case is any multi-root dashboard whose roots traverse overlapping relation paths under per-viewer visibility. The consumer surface stays Meta-declared (`Meta.edge_scopes`; sidecar `Set` classes) — never stacked decorators, never a parallel imperative registration API; the plan objects themselves are internal vocabulary, not shipped API. The second foundation card (structural optimization templates + nested sidecar batching) is deliberately not this card.

#### Dependencies

- `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze

#### Scope

- Slice 1 — `graph/` package + operation dependency memo: `graph/memo.py` (`operation_scope()` bracket, `get_or_compute(info, key, factory)`, `graph.scope_key` pre-baking viewer identity and `queryset.db`), installed by both `DjangoOptimizerExtension.on_execute` and a new optimizer-independent `extensions/graph.py::GraphSubstrateExtension`; execution-scoped, immutable-values-only, async single-flight, exception-safe.
- Slice 2 — `graph/paths.py`: frozen `GraphPathPlan` over the shipped relation classifier, the longest-resolvable-prefix path/lookup splitter, `GraphPathPlanSet` grouping keyed on the complete relation chain plus a terminal-is-relation flag, exact owning-`DjangoTypeDefinition` identity with injected type references, and per-hop target-visibility metadata; `graph/proofs.py`: the `RowIdentityProof` lattice.
- Slice 3 — `PredicatePlan` compiler: first relocate `optimizer/predicates.py` whole (both `EXISTS` builders and the [`OrderSet`](docs/GLOSSARY.md#orderset) value helpers) to `utils/predicates.py` (`optimizer/predicates.py` stays as a re-export shim), then `any_of` / `all_of` / `not_` / `direct(Q)` (to-one paths only) / `related(path, Q)` / `same_related_row(path, conditions)`, every correlated branch compiled target-side through `related_rows_exist` over each hop's visible rows and the whole tree applied as one `Q` in one outer `.filter()` (no reserved alias), `graph.apply(plan, queryset, info, owner=...)` with its color twin `graph.apply_async` (hop hooks run through the shipped visibility runners with that `info`), a typed refusal of a hop whose hook the compiler is already running, no framework-introduced `DISTINCT`, and a `RowIdentityProof` on every compiled shape.
- Slice 4 — `graph/edges.py` `EdgeScope` (request-bound factories returning predicates, compiled narrow-only onto the child queryset at `_build_child_queryset` after target visibility) + `graph/dependencies.py` `FieldDependencyPlan(columns=...)` + `Meta.edge_scopes` as a net-new `ALLOWED_META_KEYS` entry + live fakeshop activation (`Loan.confidential`, the `LoanType` visibility hook with [`Meta.primary`](docs/GLOSSARY.md#metaprimary), the `BookType` hook rewrite, `edge_scopes` on `BookType.loans`, live HTTP tests with one-vs-one-hundred-parents query-count equality).
- Slice 5 — docs + card wrap: TREE / GLOSSARY / tracked-path constants regeneration, glossary entries for the five plan objects and the memo, record the amendment obligations on the five consumer cards, flip this card.
- Layering: `optimizer/`, `filters/`, and `types/` import `graph/`; `graph/` imports neither `optimizer/` nor the type registry — type references are injected by callers as opaque `DjangoTypeDefinition` handles.

#### Definition of done

- [ ] `graph/` package ships the plan objects and the memo as frozen dataclasses; no request value storable in any structural object; `graph/` imports neither `optimizer/` nor the type registry.
- [ ] `get_or_compute` proven live and in package tests: sync, async single-flight, both cancellation directions, exception-propagation-then-retry, absent-store degradation, request isolation, alias/viewer keying; works with and without the optimizer extension.
- [ ] `PredicatePlan` compiles every correlated branch target-side through `related_rows_exist` over each hop's visible rows, with the whole tree as one `Q` under one outer `.filter()` (N `EXISTS` terms for N branches, no annotation or reserved alias), typed input errors (including the re-entrant-hop refusal on both colors), `info` threaded to every hop hook with the `graph.apply_async` color twin, `direct` over a to-many path rejected, and no compiler-added multiplying outer join or `DISTINCT`.
- [ ] `Meta.edge_scopes` validates two-stage at type creation (a net-new `ALLOWED_META_KEYS` entry); factories return predicates compiled narrow-only via `graph.apply` after target visibility; strictness keys publish only after attachment; no fail-open path (prefetched, per-parent fallback, or optimizer-off).
- [ ] `FieldDependencyPlan(columns=...)` plus the shorthand normalizer shipped — only the members the `FieldSet` card consumes at `0.1.1`; no consumer-less vocabulary members.
- [ ] Live fakeshop activation landed (`Loan.confidential` + migration, the `LoanType` secondary type with `Meta.primary`, the `BookType` hook rewrite preserving the repair-exclusion contract) with parent-count-independent query counts on the windowed path; schema-module tuples swept.
- [ ] 100% package coverage; live-first placement respected; tracked-path constants regenerated; TREE / GLOSSARY / `test_query` README updated.
- [ ] Version triplet and `CHANGELOG.md` untouched — the `0.1.1` release state is owned by the `FieldSet` card's joint cut.

#### Architectural posture

- **Amendment obligation** — per the spec's Decision 1, TODO-BETA-059-0.1.1, TODO-BETA-060-0.1.2, TODO-BETA-062-0.1.3, TODO-BETA-069-0.1.6, and TODO-BETA-072-0.1.8 must be amended to consume the substrate rather than reimplement it, and the amendments must land on those cards before any of them starts — not at this card's Slice 5. `RowIdentityProof` ships as metadata only; the enforcement gate belongs to the sibling structural-templates / nested-sidecar-batching card (TODO-BETA-068-0.1.6).

#### Why it matters

- Five planned Layer 3 surfaces — `FieldSet` (TODO-BETA-059-0.1.1), search (TODO-BETA-060-0.1.2), aggregation (TODO-BETA-062-0.1.3), explain (TODO-BETA-069-0.1.6), and the adversarial suite (TODO-BETA-072-0.1.8) — each need path classification, row-preserving predicate composition, edge-scoped child visibility, or field-dependency vocabulary; without one substrate each ships a private twin and the divergent abstractions freeze at the `1.0.0` API surface.
- Row multiplication through to-many joins silently corrupts consumer permission filters today: a to-many hop inside an outer `Q` multiplies rows, and the audited production case hits it on every root. `PredicatePlan` makes correlated, row-preserving composition a public, refuse-on-misuse API.
- Query growth for every shipped shape is bounded by selection, never by parent row count: `queries(1 parent) == queries(100 parents)`.
- An operation-scoped dependency memo makes cross-root shared computation (viewer grants, audience sets) single-compute per request, with and without the optimizer extension.

#### Dependencies

- The boundary/DRY squeeze freezes optimizer subsystem boundaries; the `graph/` package must sit below them, and Slice 3's predicate relocation composes with the post-squeeze tree.

#### Open question

- How does the cascade cross a to-many edge - hide the parent, or narrow the list? `spec-034` shipped [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) over forward single-column FK / O2O edges only and left M2M and reverse relations out of scope, obligating a follow-up that was never carded. **This card is where the question is decided** rather than a card of its own: Slice 4's `graph/edges.py` `EdgeScope` already compiles child-visibility predicates narrow-only at `_build_child_queryset` after target visibility, and this card's own premise - that a to-many hop inside an outer `Q` multiplies rows - is the same hazard in a different dress. The two answers are not interchangeable and one must be chosen explicitly: **narrow the list** (the parent survives, its related list shows only visible targets) matches `EdgeScope`'s narrow-only compilation but leaks the parent's existence; **hide the parent** (a parent with any invisible target drops out) matches `spec-034` Decision 6's row-exclusion posture, which was chosen precisely to avoid an existence leak, but is not expressible as a narrow-only child predicate. Surfaced 2026-08-28 by the spec-034 residual cycle discharging that spec's Slice 5 obligation; the full deliberation is in `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` under `## Risks and open questions`.

#### Card references

- Dependency: The boundary/DRY squeeze freezes optimizer subsystem boundaries; the `graph/` package must sit below them, and Slice 3's predicate relocation composes with the post-squeeze tree. -> `TODO-ALPHA-053-0.0.15` - Boundary hardening and system-wide DRY squeeze
- Related: Amendment obligation: `FieldSet` normalizes `Meta.depends_on` into `FieldDependencyPlan` and consumes the substrate's field-dependency vocabulary instead of a private map shape. -> `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)
- Related: Amendment obligation: search path planning moves onto `GraphPathPlan` / `GraphPathPlanSet` (path classification + arm grouping); `LOOKUP_PREFIXES` rejection and permission dispatch stay card-local. -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Related: Amendment obligation: related / permissioned aggregation consumes `EdgeScope` for child visibility instead of a private child-visibility hook. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem
- Related: Amendment obligation: explain reads the substrate's plan objects (and the sibling card's operation plan map) rather than reconstructing plan state. -> `TODO-BETA-069-0.1.6` - Optimizer explain mode
- Related: Amendment obligation: the adversarial suite gains graph-substrate targets (memo isolation, predicate compilation, edge-scope fail-closed paths). -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite
- Related: The sibling foundation card: owns reproductions R1, R7, R8, and R10, the row-identity enforcement gate, and the structural/bound split this card's plan objects prepare. -> `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

<a id="fieldset_declarative_field_level_behavior_metafields_class"></a>
### [TODO-BETA-059-0.1.1 - `FieldSet` declarative field-level behavior (`Meta.fields_class`)](KANBAN.html#fieldset_declarative_field_level_behavior_metafields_class)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `fieldsets`, `layer-3`, `public-api`
- Spec: [spec-059-fieldset-0_1_1.md](docs/SPECS/spec-059-fieldset-0_1_1.md)

#### Predicted files

- `django_strawberry_framework/fieldset/` (planned)
- `tests/fieldset/` (planned)

#### Planning note

Strawberry port of django-graphene-filters' `AdvancedFieldSet` — the declarative field-level behavior layer that the cookbook drives via `Meta.fields_class`. The cookbook shape: a consumer-authored `class GalaxyFieldSet(FieldSet)` carries `resolve_<field>(self, root, info)` overrides for custom resolution, `check_<field>_permission(self, info)` denial gates that raise before resolve runs, and class-level annotations like `display_name: str | None = strawberry.field(description="...")` for computed fields the Django model does not have. Pointed at by `Meta.fields_class = GalaxyFieldSet` on the owning `DjangoType`. This is the smallest Layer-3 surface by file count but the most novel by semantic surface area — the resolver-override contract, the redaction-vs-denial split, and the computed-field annotation discipline all live here.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- Cookbook anchor: the `fields.py` example in `GOAL.md` and the `recipes/fields.py` in the django-graphene-filters cookbook are the canonical shapes. Tiered date visibility (staff → full datetime, perm-holder → day precision, authenticated → month precision, anonymous → year precision) plus redaction-vs-denial (`resolve_is_private` returns `False` for non-staff = redaction; `check_updated_date_permission` raises for anonymous = denial) plus computed-field annotations (`display_name: str | None = strawberry.field(...)` with `resolve_display_name`) are the three patterns the [FieldSet](docs/GLOSSARY.md#fieldset) contract must support cleanly.
- Class shape: `class FooFieldSet(FieldSet)` with `class Meta: model = Foo`. The body holds three flavors of declarations: `resolve_<field>(self, root, info)` (custom resolver, overrides the auto-generated one for `<field>`), `check_<field>_permission(self, info)` (denial gate; raises `GraphQLError` or returns silently — runs before `resolve_<field>` for this request), and class-level annotated attributes (computed fields the model does not have; paired with a `resolve_<field>` method).
- Wiring: `DjangoType.Meta.fields_class = FooFieldSet` binds the fieldset at finalizer phase 2.5 (the same seam `filterset_class` / `orderset_class` use). At type-creation time the framework wires each `resolve_<field>` / `check_<field>_permission` into the owning [`DjangoType`](docs/GLOSSARY.md#djangotype)'s resolver chain so consumers do not have to subclass the type or hand-attach decorators.
- Composes with `DjangoType.Meta.fields`: declaring `Meta.fields = ("id", "name", ...)` on the owning type stays the source of truth for which model fields surface; `FieldSet` only customizes resolution / permission for fields already in [`Meta.fields`](docs/GLOSSARY.md#metafields) AND declares any computed fields via class-level annotations.
- Optimizer cooperation: a `resolve_<field>` that touches ORM data (e.g. tiered date redaction reads `root.created_date`) must NOT defeat the optimizer's `only_fields` projection. The fieldset declares which model columns its resolvers depend on via `Meta.depends_on = {"resolve_created_date": ("created_date",), ...}` (or auto-introspection if reliably available); the optimizer adds those columns to the [`only()` projection](docs/GLOSSARY.md#only-projection) so the resolver does not trigger a deferred-field fetch.
- Composability with [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) (`DONE-034-0.0.10`): a `check_<field>_permission` gate that raises does NOT short-circuit cascade visibility; the cascade narrows the queryset first, then field-level gates run on whatever survives. A field denial does not leak existence — null fields and denials look identical to the client.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1): normalize `Meta.depends_on` into `FieldDependencyPlan` rather than a private map shape — the concrete column tuple stays as shorthand, and the expanded dependency kinds (relation traversals, annotations, contextual prefetches, batch assemblers, selection-sensitive activation, strictness metadata) ship here as the vocabulary's first consumer. The two-halves rule holds: relation traversals extend `select_related` / `prefetch_related` **and** column reads extend the `only()` projection. Strictness observes undeclared computed relation access where the selection makes it detectable. Without this, `FieldSet` optimizes a simple computed display name but cannot safely optimize a computed field over related rows.

#### Definition of done

- [ ] Add `docs/SPECS/spec-059-fieldset-0_1_1.md` covering the `resolve_<field>` override contract, the `check_<field>_permission` denial-vs-redaction guidance, the computed-field annotation discipline (`display_name: str | None = strawberry.field(...)`), and the optimizer `depends_on` contract.
- [ ] Implement `django_strawberry_framework/fieldset/` (package, mirroring the `filters/` shape) with `base.py` (FieldSet class + metaclass), `factories.py` (resolver-binding factory), and a per-fieldset finalizer hook in `types/finalizer.py` phase 2.5.
- [ ] `FieldSet` accepts `class Meta: model = Foo` only; field declarations are method-based (`resolve_<field>`, `check_<field>_permission`) plus class-level computed-field annotations. No `Meta.fields` on the FieldSet itself — the owning `DjangoType.Meta.fields` is the single source of truth for the model-field surface.
- [ ] Optimizer `Meta.depends_on` contract: when a `resolve_<field>` reads model columns the owning type's `Meta.fields` does not surface, the FieldSet declares them via `Meta.depends_on`; the optimizer adds those columns to the `only_fields` projection.
- [ ] Promote [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the resolver-binding pipeline applies end-to-end; this card owns the promotion (spec-059 Decision 8), and the table-driven binder generalization is owned by the aggregation card (`TODO-BETA-062-0.1.3`).
- [ ] Tests under `tests/fieldset/` mirror the source one-to-one. Live HTTP coverage under `examples/fakeshop/test_query/` exercises tiered visibility (staff vs perm-holder vs authenticated vs anonymous), redaction (non-staff sees `is_private = False`), denial (anonymous raises on `updated_date`), and a computed field (`display_name` resolves only for authenticated users).
- [ ] Composability tests: `FieldSet` + [`FilterSet`](docs/GLOSSARY.md#filterset) (a field with a `check_<field>_permission` gate is still filterable by an authorized user); `FieldSet` + [`OrderSet`](docs/GLOSSARY.md#orderset) (same for ordering); `FieldSet` + `apply_cascade_permissions` (cascade narrows first, then field gates run — no existence leak).

#### Foundation-slice seam

- `DjangoTypeDefinition.fields_class` is the forward-reserved slot the collection phase will populate.
- `Meta.fields_class` moves out of `DEFERRED_META_KEYS` only when the field-level permission / custom-resolver / computed-field machinery is applied end-to-end (no custom Strawberry field class is required for it; spec-059 Decision 11 pins resolver wrapping as the mechanism that carries the gate).
- Phase-2.5 finalizer wiring follows the shipped `_bind_filtersets` / `_bind_ordersets` pattern. New helper `_bind_fieldsets` (or the equivalent dispatched form when `TODO-BETA-062-0.1.3` lands) binds each `Meta.fields_class` to its owning `DjangoTypeDefinition` so resolvers and gates are wired before schema construction.
- Per-field resolver attachment: the existing `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; FieldSet-bound `resolve_<field>` extends that skip-set so the FieldSet's resolver wins over the auto-generated scalar resolver.
- Custom Strawberry field class — django-graphene-filters' `AdvancedFieldSet` works with a custom field type that carries the `check_<field>_permission` gate at resolve time. That question is settled without one: spec-059 pins **resolver wrapping** as the mechanism (Decision 11 — the wrapper captures the generated resolver and delegates to it as the cascade's step 3), upstream-parity and zero-config with zero overhead on unmanaged fields. Mapping the gate onto Strawberry's `strawberry.field(permission_classes=...)` is likewise rejected: `BasePermission.has_permission(source, info, **kwargs)` is class-per-policy with a fixed message contract, cannot host the gate-then-override cascade ordering, and would synthesize a permission class per managed field for no consumer benefit; a custom `DjangoModelField` field class is unnecessary machinery for the same reason.
- Slot realized in `DONE-034-0.0.10`: `DjangoTypeDefinition.fields_class` is now declared as an inert `type | None = None` sidecar (spec-034 Decision 2 — the structural mirror of the shipped `filterset_class` / `orderset_class` slots). It has no populator yet and stays `None`; `Meta.fields_class` remains in `DEFERRED_META_KEYS` (still rejected at validation). This card's `_bind_fieldsets` is what populates the slot and promotes the key end-to-end.

#### Architectural posture

- Non-goal — node-level sentinel redaction. The upstream `django_graphene_filters/object_type.py::AdvancedDjangoObjectType.get_node` / `_make_sentinel` (`is_redacted=True`) masks a hidden non-null FK target in place instead of dropping the row. The package deliberately did **not** adopt this tier (spec-034 Decision 6 chose row-exclusion), and `FieldSet` does **not** revive it. The redaction taxonomy is two-tier: relation/row visibility = queryset narrowing (`apply_cascade_permissions`, which is why the fakeshop `view_<model>` hooks cascade rather than keep a row with a sentinel FK), field visibility = `FieldSet` (redact value / deny). There is no third node-sentinel tier — `FieldSet` redaction runs only on fields of rows that already survived the cascade; it never masks a relation target to keep an otherwise-hidden row visible. It is now tracked as an explicit, opt-in tier — `TODO-BETA-064-0.1.4` (`Meta.redaction_mode`) — for consumers who explicitly want strict django-graphene-filters node-sentinel parity; it stays opt-in (not the default) because it conflicts with the row-narrowing model.

#### Why it matters

- `FieldSet` is the smallest Layer 3 surface and can define field-selection semantics used by `DjangoConnectionField`.
- It bridges the existing `DjangoType.Meta.fields` behavior and future connection/query APIs.
- Field-level visibility is the only cookbook surface where redaction (return a safe value) and denial (raise an error) need to be distinct. Filter / order / cascade all use queryset narrowing — they remove rows. FieldSet is the one place where a row stays visible but a field is either redacted or guarded behind an error. Without it, the cookbook's `is_private` and `description` patterns are not portable.
- Computed fields (annotations like `display_name: str | None = strawberry.field(...)` paired with `resolve_display_name`) are the cookbook's escape hatch for fields the Django model does not have. The framework currently has no declarative way to add them without subclassing `DjangoType`; the FieldSet is the home for that contract.

#### Dependencies

- [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) (`DONE-030-0.0.9`) - `FieldSet` composes on top of the shipped connection-field surface.

#### Open question

- Promotion-owner conflict RESOLVED at the 2026-08-29 board review, per the pinned preferred answer in `docs/SPECS/spec-059-fieldset-0_1_1.md` `## Risks and open questions` (Decision 8): this card owns the `Meta.fields_class` promotion, and the later table-driven dispatch generalization is owned by the aggregation card (the Layer-3 Meta key promotion card that briefly owned it was retired into the aggregation card at the same review). The `#### Definition of done` was reworded to match, and the spec text was reworded to name the aggregation card in the 2026-08-29 renumber sweep, so no residue remains. Originally measured by the spec-009 residual cycle (`docs/builder/bld-009-final.md` deferred-work catalog item 20).

#### Card references

- Dependency: `DjangoConnectionField` (`DONE-030-0.0.9`) - `FieldSet` composes on top of the shipped connection-field surface. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `DONE-034-0.0.10` - Permissions subsystem
- Related: The table-driven Meta-key binder generalization this card's `_bind_fieldsets` would otherwise hard-code a third helper for is owned by the aggregation card (absorbed from the retired promotion card). -> `TODO-BETA-062-0.1.3` - Aggregation subsystem
- Related: `TODO-BETA-064-0.1.4` - Opt-in node-sentinel redaction tier (`Meta.redaction_mode`)
- Dependency: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

<a id="metasearch_fields_support"></a>
### [TODO-BETA-060-0.1.2 - `Meta.search_fields` support](KANBAN.html#metasearch_fields_support)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `connections`, `filters`, `public-api`, `search`
- Spec: [spec-060-search_fields-0_1_2.md](docs/SPECS/spec-060-search_fields-0_1_2.md)

#### Predicted files

- [`django_strawberry_framework/filters/`](django_strawberry_framework/filters/)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- `tests/filters/test_search_fields.py` (planned)

#### Planning note

Strawberry analogue of django-graphene-filters' `Meta.search_fields`. The cookbook shape is a tuple of model-field paths including relation-traversal entries: `search_fields = ("name", "description", "object_type__name", "object_type__description")`. The framework adds a single `search: String` argument to [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) consumers; when supplied, the framework fans the input across every declared path as an OR'd `icontains` filter and joins the resulting Q-object into the queryset. Relation paths use Django's double-underscore spelling and run as the relation chain they spell, restricted through optimizer/predicates.py::related_rows_exist over each hop's visible rows, never in the root's join. Both dependencies have shipped (`DONE-027-0.0.8` Filtering and `DONE-030-0.0.9` `DjangoConnectionField`); the card is planned but unblocked. To-many relation paths compile row-preserving: the chain's correlated EXISTS through related_rows_exist (the restriction every filter relation hop uses), never a search-driven .distinct() — the root query keeps no membership join and totalCount stays a flat COUNT(*). Second adversarial review (2026-07-22) hardened the contracts: one strict finalize-time plan builder (the utils/relations.py classifier + lookup validator is the only path acceptance oracle; no get_model_field second oracle); the runtime entry point is a queryset compiler (apply_search_sync/_async), not a Q builder; relational search is visibility-aware (every hop, to-one or to-many, restricts over the rows its type's own get_queryset shows - declared hops with their queryset=, undeclared hops typed by relation_target_type, a root re-entry under both the resolved type's and the exact owner's hook - so a hidden related row never qualifies a visible root — the step is sync/async twinned, not colorless); search honors the declaring type's [FilterSet](docs/GLOSSARY.md#filterset) check_<field>_permission gates (a viewer may search a path exactly when they could filter by it — the fakeshop Category name gate is the live proof); a documented SEARCH_MAX_LENGTH=256 input cap with a typed error; duplicate/padded declarations rejected; Slice 4 adds the library to-many live surface (GenreType search_fields=("name", "books__title") over allLibraryGenresConnection) because all four staged products declarations are forward-only; Slice 5 moves the GLOSSARY entry to "implemented on main; release pending the joint 0.1.2 cut" instead of leaving it falsely planned.

Second Part 1 adversarial review (2026-07-22) formalized the groundwork as this spec's pre-card Slice 0 (docs/row-preserving-predicates-part1-plan.md Rev 4) with card-054-owned completion bookkeeping (GLOSSARY/TREE/KANBAN fold-in + OptimizerError raise-site docs), adopted the compositional multiset contract (framework predicates are pure selections: never multiply rows, never collapse consumer duplicates; global distinct removed), refined Decision 12 (direct relational branches carry per-branch hop visibility themselves, AND'd only into their own OR arm - never delegated to cascade) and Decision 13 (active search fires every APPLICABLE FilterSet gate; [Meta.search_fields](docs/GLOSSARY.md#metasearch_fields) is the grant for ungated paths; alias/prefix/HIDE_FLAT_FILTERS gate semantics pinned).

Cross-spec Medtrics-reproduction review (2026-07-22): part1-plan is Rev 5 and this spec gained Decision 14. Enacted: (a) the multiset contract is anchored to GOAL.md (predicates are selections over consumer-shaped querysets, never a normalization boundary; the DRF endpoint response is never the multiset oracle); (b) reverse-FK-after-to-one (forward FK -> reverse FK -> forward FK) is a named classifier/adapter category, separate from M2M; (c) one shared Medtrics reproduction fixture (Loan.book -> Book.loans -> Loan.patron -> Patron.email, four named loans, ordered-sequence oracle incl. the duplicated pre-rewrite sequence) consumed at three levels: Part 1 adapter test, this card's live LoanType search integration test (acceptance-only DjangoConnectionField(LoanType), search_fields = (note, book__loans__patron__email), exact ordered IDs + totalCount + page boundaries), and package SQL-shape tests (correlated EXISTS, not JOIN+DISTINCT or a scalar aggregate); (d) Decision 14: search scope is type-definition-wide and immutable (no request/resolver/connection mutation of the tuple; different surfaces use distinct DjangoTypes; no field-level override without a demonstrated use case); (e) row-boundary phrase oracle (red/dwarf vs red dwarf) making StringAgg observably wrong, live + SQL-shape; (f) borrowing/migration docs state both intentional DRF SearchFilter divergences together (phrase semantics, static scope). The Medtrics StringAgg patch is explicitly NOT prior art to adopt.

Critical-evaluation fixes (2026-07-22): part1-plan is Rev 6. Enacted after the post-anchor deep evaluation: (1) the LoanType search_fields declaration is permanent type-wide surface on the EXISTING LoanType (Decision 14 cross-ref); acceptance-only describes only the added DjangoConnectionField exposure, the existing list field gains nothing; (2) Decision 12 pins root-model-as-hop-target recursion (LoanType visibility composes into inner loan rows of book__loans; the same restriction the LoanFilter flat leaf runs) + a hidden-inner-loan live test; (3) dead C.5 fallback clause removed (LoanFilter exists); (4) same-table inner aliasing (library_loan re-entered inside EXISTS) is a named Slice B SQL-shape assertion; C.4 gains nullable-intermediate-to-one-hop and to_field rows; fixture oracles assert captured pks; three fixture levels tier-assigned; (5) Slice A note: legacy path_traverses_to_many is not the defect site, the category proves classify_path first_many_index; (6) live suites must use graphql_client.py helpers and route registry-mutating fixtures through schema_reload/project_schema_override (beyond settings-dependent); (7) test_query/README.md suite-description updates added to Slice D and Slice 5 bookkeeping; (8) confirmed no types/relay.py setting anchor exists, SEARCH_MAX_LENGTH stays a Decision 11 module constant. Code TODO anchors in utils/relations.py and optimizer/predicates.py synced.

Implementation-gate review enacted (2026-07-22): five blockers folded into the spec —
(1) P0-1 Decision 12 same-related-row rule carried by the target-side fold (the terminal filters the deepest hop's visible rows; leak counterexamples incl. book__loans re-entry);
(2) P0-2 exact-owner re-entry: build_search_path_plan(definition, paths) signature, frozen exact-owner reference, secondary-type regression;
(3) P1-3 async permission gates via run_in_one_sync_boundary (Decision 6), live async ORM-reading-gate regression;
(4) P1-4 named path-driven permission-plan helper in utils/permissions.py built post-_bind_filtersets, permission-plan test matrix, assign-after-both retry safety;
(5) P1-5 active_search canonical home moved to utils/connections.py with filters/search.py re-export, lazy-subpackage import pin extended.
Plus Decision 14 multi-type migration mechanics ([Meta.primary](docs/GLOSSARY.md#metaprimary), separate FilterSets, GlobalID strategy) and a DoD gate bullet. Part 1 plan unchanged (review: ready in principle).

Follow-up multiplicity review enacted (2026-07-22): five findings folded in. Part 1 plan bumped to Rev 7 — prior-art statement corrected (admin lookup_spawns_duplicates DOES detect reverse FK via PathInfo.m2m; old "misses reverse FK" reading was false), PathInfo named Slice A SQL-multiplicity authority beside relation_kind() semantic topology (many_side = any(path_info.m2m), target from path_infos[-1].to_opts; frozen plan keeps package-owned values only), admin helper banned from production (test differential oracle only, valid paths, never sole oracle), reverse-FK category rationale recast detection->compilation, exact acceptance floor Python 3.10 + Django==5.2.0 in sequencing steps 4/9. Spec-058: Decision 7 gains the finding-4 rationale (fixture exists because detection is insufficient; runtime consumes frozen plan, never calls admin helper, never a search_requires_distinct boolean); Test plan + DoD gain the exact-floor live reproduction requirement. Architecture unchanged per review verdict.

Coverage-gap audit (2026-07-31): a cross-check of the spec against the to-many search reproduction guide found two acceptance items with no home in the card -- consumer .only() / .defer() compatibility, and proof that selection-driven N+1 optimization is unchanged by the row-preserving predicate compiler (search + selected relations against a no-search control). Both are now scope + definition-of-done bullets here and Test-plan/DoD entries in the spec, and Slice 4 lists them among the composability cases. The spec's Slice 5 now enumerates the four Slice-0 fold-in obligations with their state (OptimizerError raise site, docs/TREE.md predicate modules, test_query/README.md paragraphs, and the GLOSSARY filterset multiset paragraph all landed with the Part 1 groundwork -- Slice 5 audits them present rather than rewriting them), leaving only the KANBAN fold-in outstanding. Same audit: this card's spec bullet named the pre-convention `docs/spec-search_fields.md`, which never existed; it now names the real spec. The stale-pointer sweep corrected the same defect on cards 34, 36, 39, 53, 55, 56, and 58.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- Cookbook anchor: the `recipes/schema.py` example shipped with django-graphene-filters declares `search_fields = ("name", "description", "object_type__name", "object_type__description")` — flat field names AND relation-traversal paths in the same tuple. The framework must accept both shapes identically; relation traversal is built on Django's standard `<rel>__<field>` lookup syntax.
- Argument shape: a single `search: String` argument on the connection field. Empty/null/whitespace-only input is a no-op (queryset passes through unchanged). Non-empty input produces a single Q-object that OR's `<path>__icontains=<input>` across every declared path. Relation paths (to-one and to-many) compile as their chain's correlated EXISTS over each hop's visible rows, OR'd with the direct-path predicates — one root row stays one SQL row through counting and pagination; JOIN-plus-DISTINCT is rejected as the implementation strategy.
- Composition with `filterset_class`: `search` and `filter` compose by intersection — the resulting queryset matches every declared filter AND the search OR-clause. The argument-factory machinery is shared between `filterset_class` and `search_fields`, so adding `search` does not duplicate the factory infrastructure.
- Composition with `get_queryset`: search runs against the post-visibility queryset (visibility narrows first), so a user cannot search for hidden rows by guessing field values. Relational search is additionally visibility-AWARE: every hop restricts through related_rows_exist over the rows its type's own get_queryset shows (and a walked [RelatedFilter](docs/GLOSSARY.md#relatedfilter)(queryset=...)), so a hidden related row behaves exactly like no related row, so a visible parent can never match through a related row hidden on its own GraphQL surface.
- Composition with the selection optimizer: search contributes NOTHING to the cached OptimizationPlan (no request value, no only/select_related/prefetch_related entry) and the plan contributes no predicate. An active search must leave selection-driven N+1 optimization observably unchanged (live search + selected-relations case paired against a no-search control on query count and select_related/prefetch_related work), and must compose onto a consumer .only() / .defer() queryset without widening or discarding the deferred field set or adding a selected column -- every arm's EXISTS is a WHERE condition, never an annotate()/alias() entry.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1): search path planning moves onto `GraphPathPlan` / `GraphPathPlanSet` (path classification plus chain-keyed arm grouping) ; relational arms restrict through the filter side's `related_rows_exist` over each hop's visible rows, not `PredicatePlan`; search must not own the only correct graph compiler. `LOOKUP_PREFIXES` prefix rejection and the permission-dispatch plan stay card-local — they are search policy, not substrate. **Deferred R3 arm recorded here:** a hidden related row must not be able to qualify a visible root through search (the substrate card proves the edge-selection half; this card owns the search-qualification half). **Fixture dependency:** the `LoanType` visibility hook with `Meta.primary` and the secondary-type root-model re-entry surface are created by the substrate card — consume them, do not duplicate them.
- A `search_fields` path and the flat `filter:` leaf over the same path answer the same rows: search reads the path through `django_strawberry_framework/utils/permissions.py::walk_declared_relation_path` with `undeclared=True` (the walk `django_strawberry_framework/filters/sets.py::FilterSet._flat_leaf_walk` reads), resolves each declared hop's type as `django_strawberry_framework/filters/sets.py::FilterSet._branch_visibility_seed` does and applies its explicit `queryset=`, types each undeclared hop with `django_strawberry_framework/utils/querysets.py::relation_target_type` (scoping only when that type has its own `get_queryset`), and restricts each hop through `django_strawberry_framework/optimizer/predicates.py::related_rows_exist`. A root re-entry whose exact owner differs from the hop's resolved type applies both hooks. Shape to pin: `search_fields = ("note", "book__loans__patron__email")` on `LoanType` and `filter: { bookLoansPatronEmail: { iContains: ... } }` return the same loans for a viewer who cannot see the only matching inner loan, book or patron.

#### Definition of done

- [ ] `docs/SPECS/spec-060-search_fields-0_1_2.md` is the card's spec of record (written).
- [ ] Search-fields argument generation lives in `django_strawberry_framework/filters/` and reuses the same DRF-style Meta surface and argument-factory machinery as `filterset_class`.
- [ ] Single `search: String` argument surfaces on `DjangoConnectionField` consumers and produces an OR'd `icontains` queryset filter across every declared field path, compiled row-preserving: direct paths as plain Q predicates, relation paths as their chain's correlated EXISTS through related_rows_exist over each hop's visible rows; no search-driven `.distinct()`; root `alias_map` free of membership joins; `totalCount` counts the row-preserving queryset directly.
- [ ] Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end; this card owns the promotion, and the table-driven binder generalization is owned by the aggregation card (`TODO-BETA-062-0.1.3`).
- [ ] Tests under `tests/filters/test_search_fields.py` covering single-field, relation-path, and combined-with-filterset cases.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a search across at least one relation path. Includes the library to-many proof: GenreType search over allLibraryGenresConnection (one genre, two matching books -> one edge, totalCount == 1, EXISTS in the emitted SQL, no search-driven SELECT DISTINCT).
- [ ] SQL-shape regression tests pin the row-preserving compilation: root query `alias_map` excludes membership/child tables, `query.distinct is False`, an EXISTS per relational arm (to-one and to-many) and none for a direct-only declaration, and the `totalCount` SQL has no distinct-wrapper subquery.
- [ ] Relational search is visibility-aware (every hop scoped by its type's own get_queryset via apply_type_visibility_sync/_async - declared hops with their queryset= and via= intermediates, undeclared hops typed by relation_target_type - restricted through related_rows_exist; hidden == absent and filter-twin parity live) and honors FilterSet check_<field>_permission gates for every declared path (shared utils/permissions.py machinery, loud raise) — proven live with anonymous/staff Category-name-gate tests and a hidden-related-row test.
- [ ] Input hygiene ships the shared active_search predicate (single definition consumed by the pipeline no-op gate AND the non-queryset sidecar guard, so whitespace input is never an observable error), the documented SEARCH_MAX_LENGTH=256 cap with a typed GraphQL error; a combined `get_queryset` result reaches search as its sealed primary-key set, so it needs no preflight.
- [ ] Predicate/selection independence is proven: with an active to-many search the built OptimizationPlan is identical to the no-search plan for the same selection and carries no request value; the live search + selected-relations case matches its no-search control on query count and select_related/prefetch_related work; and search composes onto consumer .only() / .defer() querysets without widening the deferred set or adding a selected column.

#### Files likely touched

- `django_strawberry_framework/filters/` (search support)
- `django_strawberry_framework/types/base.py` (Meta validation; promote key)
- `tests/filters/test_search_fields.py` (new)
- `examples/fakeshop/apps/products/schema.py` (activation)
- `django_strawberry_framework/connection.py` (synthesized `search:` argument; pipeline step)
- `django_strawberry_framework/optimizer/predicates.py` + `django_strawberry_framework/utils/relations.py` (consumed: pre-card row-preserving predicate compiler + structured path walker)
- examples/fakeshop/apps/library/schema.py (GenreType search_fields activation — the live to-many surface)

#### Verified in upstream

- `django-graphene-filters` exposes `Meta.search_fields = ("name", "description", "category__name")` — a tuple of model-field paths. The connection field gains a single `search: String` argument that fans out across the listed fields as an OR'd `icontains` filter, traversing relations through Django's standard ORM lookup syntax.

#### Why it matters

- `Meta.search_fields` is one of the five django-graphene-filters Layer-3 Meta keys explicitly listed in [`GOAL.md`][goal] alongside `filterset_class`, `orderset_class`, `aggregate_class`, and `fields_class`. Without it the package cannot claim full DGF parity at 1.0.0.
- Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. The fakeshop products schema stages four commented `search_fields` tuples awaiting this card's activation slice; `TODO-BETA-066-0.1.5` (Fakeshop GraphQL schema activation) is now scoped to the `node` / `nodes` entry points plus the `totalCount` opt-in and no longer gates them.

#### Dependencies

- `DONE-027-0.0.8` (Filtering subsystem) — the argument factory is shared.
- `DONE-030-0.0.9` (`DjangoConnectionField`) — the `search: String` argument surfaces on connection fields.

#### Card references

- Dependency: both dependencies have shipped: `DONE-027-0.0.8` (Filtering) and `DONE-030-0.0.9` (DjangoConnectionField) landed before this card. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: Promote `Meta.search_fields` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the pipeline applies it end-to-end; this card owns the promotion, and the table-driven binder generalization is owned by `TODO-BETA-062-0.1.3`. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem
- Dependency: both dependencies have shipped: `DONE-027-0.0.8` (Filtering) and `DONE-030-0.0.9` (DjangoConnectionField) landed before this card. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: Currently `search_fields` is in `DEFERRED_META_KEYS` and rejected at validation time. The fakeshop products schema stages four commented `search_fields` tuples awaiting this card's activation slice; `TODO-BETA-066-0.1.5` (Fakeshop GraphQL schema activation) is now scoped to the `node` / `nodes` entry points plus the `totalCount` opt-in and no longer gates them. -> `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation
- Related: a single `search: String` argument fanning out as an OR'd `icontains` across declared field paths; reuses `DONE-027-0.0.8`'s argument-factory machinery. Spec + tests + live HTTP + Meta-key promotion. -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

<a id="postgres_full_text_search_filter_primitives"></a>
### [TODO-BETA-061-0.1.2 - Postgres full-text search filter primitives](KANBAN.html#postgres_full_text_search_filter_primitives)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `filters`, `public-api`, `search`

#### Predicted files

- [`django_strawberry_framework/filters/base.py`](django_strawberry_framework/filters/base.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- `tests/filters/test_pg_full_text.py` (planned)

#### Planning note

Strawberry analogue of django-graphene-filters' Postgres full-text search family. The cookbook ships `AnnotatedFilter` (base) plus `SearchQueryFilter`, `SearchRankFilter`, and `TrigramFilter` in `django_graphene_filters/filters.py`, with matching `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType` input shapes in `django_graphene_filters/input_types.py`. These add Postgres-only `searchQuery` / `searchRank` / `trigram` filter inputs to FilterSets on Postgres-backed models, layered on `django.contrib.postgres.search`. Distinct from [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) (basic OR'd `icontains`); this is the ranked / weighted / similarity full-text surface. Planned; gated on `TODO-BETA-060-0.1.2` (basic search lands first) and shares `DONE-027-0.0.8`'s filter-argument-factory machinery.

Coverage-gap audit (2026-07-31): this card also owns the JOINT 0.1.2 release cut for the `Meta.search_fields` card's surface -- the version triplet, the CHANGELOG entry (explicit maintainer grant required), README / docs README shipped-surface wording, GOAL/TODAY release status, and the glossary promotion out of the search-fields card's intermediate status. That ownership previously lived only in the search-fields card's spec text, so it was invisible from this card; it is now a scope + definition-of-done bullet. Same audit: this card's spec bullet named the pre-convention `docs/spec-pg_full_text_search.md`; it now names the AGENTS.md spec-<NNN>-<topic>-<version> path.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `TODO-BETA-060-0.1.2` - `Meta.search_fields` support

#### Scope

- Cookbook anchor: `django_graphene_filters/filters.py` ships `AnnotatedFilter` -> `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter`; `django_graphene_filters/input_types.py` ships the paired `SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType`. Port the four filter classes plus their input shapes onto the Strawberry side.
- `AnnotatedFilter` base: annotate the queryset with a computed column (`SearchVector` / `SearchRank` / `TrigramSimilarity`) under a generated alias, then filter on that alias. The Strawberry-side annotation derives at materialization via the existing `convert_filter_to_input_annotation` path rather than a Graphene `input_type` constructor arg.
- `SearchQueryFilter`: `SearchVector` + `SearchQuery` full-text match with configurable search config, vector weights, and `search_type` (plain / phrase / raw / websearch).
- `SearchRankFilter`: `SearchRank` weighting with `weights` / `cover_density` / `normalization` options.
- `TrigramFilter`: `pg_trgm` `TrigramSimilarity` / `TrigramWordSimilarity` with a `kind` selector and a similarity threshold.
- Postgres-only: degrade with a clear [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) (or skip the filter) on non-Postgres backends; never emit a malformed query on SQLite.
- Prefix-shortcut operators are owned by this card. Card 054 deliberately ships only unprefixed OR-of-`icontains` search and rejects declarations beginning with `^`, `=`, `@`, or `$`. This card decides which shortcuts enter the ported surface and must pin a clear fail-closed non-Postgres contract for `@`; none of the four is considered shipped by card 054.
- Joint `0.1.2` release cut is owned by this card. The `Meta.search_fields` card ships that key to `main` but deliberately touches no release-state artifact, so this card carries them for BOTH cards: the `0.1.2` version triplet, the CHANGELOG entry (which needs the maintainer's explicit grant per AGENTS.md), README / docs README shipped-surface wording, GOAL/TODAY release status, and the promotion of the `Meta.search_fields` glossary entry from "implemented on main; release pending the joint 0.1.2 cut" to shipped.

#### Definition of done

- [ ] Add `docs/SPECS/spec-057-pg_full_text_search-0_1_2.md`.
- [ ] `AnnotatedFilter` + `SearchQueryFilter` / `SearchRankFilter` / `TrigramFilter` ship in `django_strawberry_framework/filters/` and reuse the shared DRF-style Meta surface + argument-factory machinery from `DONE-027-0.0.8`.
- [ ] Paired input types (`SearchQueryFilterInputType` / `SearchRankFilterInputType` / `TrigramFilterInputType`) generate with stable class-derived names.
- [ ] Backend guard: a clear typed error on non-Postgres backends rather than a malformed query.
- [ ] Tests under `tests/filters/test_pg_full_text.py` covering each filter, the weight/config options, and the non-Postgres guard.
- [ ] Live HTTP coverage under `examples/fakeshop/test_query/` against a Postgres-backed model (gated on a Postgres test backend; skipped under the default SQLite run).
- [ ] The joint `0.1.2` cut ships for both cards: the `0.1.2` version triplet is bumped, the CHANGELOG entry is written under the maintainer's explicit grant, README / docs README shipped-surface wording and GOAL/TODAY release status are moved for `Meta.search_fields` AND this card's full-text surface, and the `Meta.search_fields` glossary entry is promoted from its search-fields-card intermediate status to shipped.

#### Files likely touched

- `django_strawberry_framework/filters/base.py` (new filter classes)
- `django_strawberry_framework/filters/inputs.py` (new input types)
- `tests/filters/test_pg_full_text.py` (new)
- `examples/fakeshop/test_query/` (Postgres-gated HTTP coverage)

#### Verified in upstream

- The only cookbook filter-surface gap found in the 0.0.7 DRY-cycle kwarg-parity audit; every other `django_graphene_filters` filter primitive is already shipped in `DONE-027-0.0.8`.

#### Why it matters

- The Postgres full-text family is part of django-graphene-filters' shipped filter surface; recreating it is in scope for cookbook parity (`GOAL.md` "Working reference").
- `Meta.search_fields` (`TODO-BETA-060-0.1.2`) only covers OR'd `icontains`; ranked / weighted / similarity search is a distinct capability the cookbook ships and basic search does not.

#### Dependencies

- `TODO-BETA-060-0.1.2` (`Meta.search_fields`) -- basic search lands first; this is the advanced full-text surface.
- `DONE-027-0.0.8` (Filtering subsystem) -- the filter-argument-factory machinery is shared.

#### Card references

- Dependency: `TODO-BETA-060-0.1.2` (`Meta.search_fields`) -- basic search lands first; this is the advanced full-text surface. -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Related: `Meta.search_fields` (`TODO-BETA-060-0.1.2`) only covers OR'd `icontains`; ranked / weighted / similarity search is a distinct capability the cookbook ships and basic search does not. -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Dependency: `DONE-027-0.0.8` (Filtering subsystem) -- the filter-argument-factory machinery is shared. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: The only cookbook filter-surface gap found in the 0.0.7 DRY-cycle kwarg-parity audit; every other `django_graphene_filters` filter primitive is already shipped in `DONE-027-0.0.8`. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="aggregation_subsystem"></a>
### [TODO-BETA-062-0.1.3 - Aggregation subsystem](KANBAN.html#aggregation_subsystem)

- Priority: Medium-high
- Status: To Do
- Relative size: L
- Labels: `aggregations`, `filters`, `layer-3`, `public-api`

#### Predicted files

- `django_strawberry_framework/aggregates/` (planned)
- `tests/aggregates/` (planned)

#### Planning note

Strawberry port of django-graphene-filters' `AdvancedAggregateSet` — declarative per-type aggregation via `Meta.aggregate_class`. Mirrors the shipped Filtering and [Ordering](docs/GLOSSARY.md#ordering) architecture (six-layer lazy-resolution pipeline; finalizer phase-2.5 binding; per-module input-class namespace) but emits `strawberry.type` output types (not input) and adds a sync/async `compute` / `acompute` split. The cookbook shape: [`AggregateSet`](docs/GLOSSARY.md#aggregateset) subclasses declare `Meta.fields = {"name": ["count", "min", "max", "mode", "uniques"], ...}`, per-stat `check_<field>_<statname>_permission` gates, custom-stat `compute_<field>_<statname>` methods registered via `Meta.custom_stats = {...}`, [`RelatedAggregate`](docs/GLOSSARY.md#relatedaggregate) for cross-relation traversal, and a [`get_child_queryset`](docs/GLOSSARY.md#get_child_queryset) cascade hook for related aggregates.

#### Dependencies

- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`
- `AggregateSet`
- GraphQL argument/result factories
- [`Meta.aggregate_class`](docs/GLOSSARY.md#metaaggregate_class) promotion
- Cookbook anchor: django-graphene-filters' `recipes/aggregates.py` declares `class ObjectTypeAggregate(AggregateSet)` with `Meta.fields = {"name": ["count", "min", "max", "mode", "uniques"], "description": ["count", "min", "max"]}` and `Meta.custom_stats = {"centroid": graphene.String}` paired with a `compute_value_centroid(self, queryset)` method (`recipes/aggregates.py:73-90`). The Strawberry port carries this shape verbatim with [`OrderSet`](docs/GLOSSARY.md#orderset) → `AggregateSet` substitution and the `compute` / `acompute` sync/async split.
- Built-in stat surface: `count`, `min`, `max`, `mode`, `uniques`, plus the Django aggregate primitives `Sum`, `Count`, `Avg`, `Min`, `Max`, `GroupBy`. The cookbook ships every one as a per-field option on [`Meta.fields`](docs/GLOSSARY.md#metafields); this card pins the same surface.
- `RelatedAggregate("TargetAggregate", field_name="...")` for relation-traversed aggregates (e.g. `celestial_bodies = RelatedAggregate("CelestialBodyAggregate", field_name="galaxy")` on a `GalaxyAggregate`). Accepts a class reference, an absolute import path, or an unqualified name for circular references — the same lazy-resolution contract [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) and [`RelatedOrder`](docs/GLOSSARY.md#relatedorder) ship.
- `Meta.custom_stats = {"<statname>": <return_type>}` declares consumer-defined stats; the framework expects a paired `compute_<field>_<statname>(self, queryset)` method that returns a value matching the declared type. Cookbook example: `Meta.custom_stats = {"centroid": graphene.String}` paired with `compute_value_centroid(self, queryset)` returning the computed centroid string (`recipes/aggregates.py:73-90`).
- Per-stat permission: `check_<field>_<statname>_permission(self, request)` gates a specific (field, stat) pair (cookbook example: `check_name_uniques_permission` raises for non-staff so non-staff cannot see the unique-name distribution while still seeing `count` / `min` / `max`). Mirrors the per-field permission gate in [`FilterSet`](docs/GLOSSARY.md#filterset) / `OrderSet` but keyed on the (field, stat) tuple, not just the field.
- `get_child_queryset(self, rel_name, rel_agg)` cascade hook on `AggregateSet` lets a parent aggregate enforce a cascade rule on its children (cookbook example: a shared `_private_aware_child_qs` that filters out `is_private=True` rows when traversing through a `RelatedAggregate`). Composes with [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) (`DONE-034-0.0.10`).
- Sync / async `compute(self, info, queryset) -> <Output>` and `async def acompute(self, info, queryset) -> <Output>` — same dual-shape contract `FilterSet.apply_sync` / `apply_async` ships. Selection-set-aware: only the aggregate output fields the GraphQL query actually selects are computed; the optimizer plan-cache infrastructure drives the selected-fields detection so a 20-stat aggregate output type does not eagerly compute all 20 when the consumer asked for 3.
- Output-type emission: each `AggregateSet` emits a `@strawberry.type`-decorated output class named `<AggregateSet>OutputType` (e.g. `ObjectTypeAggregateOutputType`) materialized in a per-module `aggregates.outputs` namespace — disjoint from `filters.inputs` / `orders.inputs`, mirroring the per-module namespace pattern.
- Config knobs (parity watch-item, carried over from the django-graphene-filters parity review): DGF's aggregate subsystem ships tunable safety limits and an async opt-in as settings — `AGGREGATE_MAX_VALUES`, `AGGREGATE_MAX_UNIQUES`, and `ASYNC_AGGREGATES` (`django_graphene_filters/conf.py`). This card captures the `compute` / `acompute` split and the stat surface but not these config knobs; the spec must confirm they are in scope when `spec-aggregates` is authored, or consciously drop them.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1): related and permissioned aggregation consumes `EdgeScope` for child visibility, `GraphPathPlan` for relation-path classification, and `FieldDependencyPlan` for dependency declaration — no aggregate-private child-visibility abstraction beside `get_child_queryset`. Child aggregates must carry row-identity and cardinality semantics: aggregate fan-out across a many-join is a planner error by default, never a silently multiplied result. **Deferred R3 arm recorded here:** a hidden child must not contribute to a count or an aggregate.
- Optional (absorbed from the retired promotion card): fold the finalizer's per-key binding (`_bind_filtersets` / `_bind_ordersets` / `_bind_fieldsets`) into one dispatched, table-driven form so promoting a Meta key is a data change rather than a new helper per key.

#### Definition of done

- [ ] Add `django_strawberry_framework/aggregates/`.
- [ ] Add mirrored `tests/aggregates/`.
- [ ] Promote `Meta.aggregate_class` only when aggregation is applied end-to-end.
- [ ] Decide result type naming and grouping semantics.
- [ ] Validate generated queryset aggregation paths.
- [ ] Keep aggregation declarations composable with filters, ordering, and connection field behavior.
- [ ] Add `docs/SPECS/spec-058-aggregates-0_1_3.md` covering: `AggregateSet` / `RelatedAggregate` class shape; the `count`/`min`/`max`/`mode`/`uniques` built-in stat surface; `Meta.custom_stats` + `compute_<field>_<statname>` contract; per-stat `check_<field>_<statname>_permission` gating; `get_child_queryset` cascade hook; sync/async `compute` / `acompute` split; selection-set-aware computation; output-type emission and the `aggregates.outputs` namespace.
- [ ] Live HTTP coverage in `examples/fakeshop/test_query/` exercises a real cookbook-shaped aggregate: a parent type with `RelatedAggregate` traversal, a custom stat, a per-stat permission gate, and a selection-set test confirming only the selected stats are computed.
- [ ] Composability with the shipped sidecars: filter narrows first → order is a no-op for aggregate output → aggregate computes against the filtered + cascade-permissioned queryset. Pinned by a single test that exercises all three at once.

#### Foundation-slice seam

- `DjangoTypeDefinition.aggregate_class` is the populated slot.
- The cookbook reference (`AdvancedAggregateSet.compute` / `acompute`) splits sync and async paths; this lines up with the existing async-resolver support in the optimizer.
- Selection-set-aware aggregate computation will reuse the optimizer plan-cache infrastructure, since the aggregate output type's selected fields drive which annotations are computed.

#### Architectural posture

- Concurrency / scatter-gather seam (design guidance carried over from the django-graphene-filters parity review; net-new value, **not** a DGF-parity item). The package has zero query concurrency today, partly deliberate — `relay.py::DjangoNodesField` chooses sequential awaits over `asyncio.gather`, citing Django async-ORM connection safety. Parallelism only pays for genuinely independent queries on separate connections, never naive fan-out over one shared connection/cursor. Hard constraints any gather seam must respect: (1) each thread worker opens a thread-local connection it must close (`close_old_connections`), so the sync pool is small and bounded (≈2–3), NOT `max_workers=NUM_CORES` — except the independent-DB shard case, where core-scaling is correct; (2) the `chunk_size = ceil(count / NUM_CORES)` PK-range partition is a win ONLY when the reduction runs in Python (mode / uniques / percentile / `Counter`), never for a SQL-native aggregate (`Count`/`Sum`/`Min`/`Max`/`Avg`), which adds round-trips and loses index efficiency; (3) the example project runs on SQLite (serializes), so any speedup must be benchmarked on Postgres/MySQL — the 100%-coverage suite cannot prove it under the default runner.
- Where it pays to invest — the `AggregateSet` gather seam (this card). Independent stats that cannot fold into one `.aggregate()` (mode / uniques / percentile / the `Counter`-based custom `compute_*` stats above) are each their own scan, and the PK-range partition applies to their Python reduction; DB-native stats MUST stay single-query (let SQL do it). `acompute` already implies the async seam — build the gather seam (a sync bounded-pool plus the async `acompute` path) into this card from the start rather than retrofitting it. Design it once here: it is reused by the BACKLOG `matrix_dimensions_and_measures` (item 32 — per-measure fan-out + chunked-partition reduction over the heaviest 10M-row / percentile / pivot surface; design its executor with a parallel reduce from the start) and `sharding_aware_optimizer` (item 41 — multi-shard compose over independent DBs / connections: zero GIL contention, no shared-connection hazard, per-shard count/sum/min/max compose; the one place `max_workers=NUM_CORES` is literally correct) cards.
- Async-path constraint. Every async path today wraps its sync body in `sync_to_async(..., thread_sensitive=True)` — `FilterSet.apply_async`, `OrderSet.apply_async`, `aapply_cascade_permissions`, `resolve_mutation_async` — which serializes them onto the calling context's one thread-sensitive worker (asgiref's process-wide worker when no `ThreadSensitiveContext` is active). A generated mutation is the exception: `django_strawberry_framework/schema.py::DjangoMutationExecutionContext` gives each mutation field's transaction window a private thread and connection, so `resolve_mutation_async` runs there and never on the shared worker. That is a deliberate connection / consumer-hook safety choice, not a bug, but it is the constraint the async `acompute` gather must design around: the gather must run genuinely independent units on their own connections and never re-enter the shared sensitive thread.
- Adjacent optimizer seams investigated (non-aggregation, recorded here so they are not lost — both marginal / deferred): (a) root-connection `totalCount ∥ page slice` — when [`Meta.connection`](docs/GLOSSARY.md#metaconnection) opts into `totalCount`, the count runs serially after the slice via `count()` / `acount()` on the same filtered queryset (`connection.py::_attach_count_sync` / `_attach_count_async`); the two are independent and package-owned, but it is the smallest standalone win and marginal unless the count rivals the page cost, on a parallelizing backend only. (b) parallel independent top-level `prefetch_related` — plain to-many list / M2M siblings still issue N serial `WHERE parent_id IN (...)` scans inside Django's `prefetch_related_objects`; `OptimizationPlan.apply` returns a lazy queryset and Strawberry/Django owns materialization, so parallelizing means the package takes over materialization in the resolvers it controls (per the root-cause rule — NOT monkeypatching `prefetch_related_objects`). High risk; defer behind a Postgres benchmark.
- Ruled out, on the record: the single root list query (`list_field.py`, nothing to split); `resolve_nodes` (`relay.py`, already one `pk__in` per type — optimal within one DB, don't parallelize the single-DB case); `FilterSet` / `OrderSet` `apply_*` (queryset builders, no fan-out); the `0.0.11` mutations (single-row, single-transaction); `finalize_django_types()` (CPU/GIL-bound and contractually single-threaded); and DB-native aggregates. Do not retrofit concurrency onto shipped code without a Postgres benchmark.

#### Card references

- Related: full subsystem, parallel to Ordering: reuses `DONE-027-0.0.8`'s six-layer architecture but emits `strawberry.type` output types (not input) and adds the sync/async `compute` / `acompute` split. New `aggregates/` subpackage + `docs/SPECS/spec-058-aggregates-0_1_3.md` + tests. -> `DONE-027-0.0.8` - Filtering subsystem
- Related: `DONE-034-0.0.10` - Permissions subsystem
- Dependency: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

<a id="mutation_idempotency_keys"></a>
### [TODO-BETA-063-0.1.3 - Mutation idempotency keys](KANBAN.html#mutation_idempotency_keys)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `mutations`, `performance`, `security`

#### Predicted files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- [`tests/mutations/`](tests/mutations/)

#### Planning note

Promoted from BACKLOG.md item 23 as a Beta differentiator after the core mutation surface exists and before migration/adoption docs lock the pre-1.0 story.

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Scope

- Shipped baseline (given, commit 1b06c39e): every top-level mutation field already runs inside an always-on `transaction.atomic()` wrap, with `Meta.select_for_update` available to lock the affected rows. This card builds on that baseline and adds idempotency only — it introduces no new transaction opt-in.
- Add `Meta.idempotency_key = "request_id"` and `Meta.idempotency_ttl = 86400` backed by a durable package-owned idempotency record. A database uniqueness constraint over the fully scoped key serializes concurrent first attempts; the stored terminal response and status are the replay source of truth.
- Create the idempotency reservation and mutation side effects in the same database transaction, and persist the successful terminal response before that transaction commits. Validation, permission, completion, and database failures roll back both. `django.core.cache` may accelerate committed replays only; it is never the authority.
- Keep the surface DRF-shaped and mutation-local: declaration lives on each `DjangoMutation.Meta`, with safe defaults and no global setting required.

#### Definition of done

- [ ] New or amended mutation spec documents the idempotency Meta keys (`Meta.idempotency_key` / `Meta.idempotency_ttl`), durable-record schema and migration, canonical scope key, reservation state machine, TTL/reclamation behavior, terminal-response replay, concurrent retry semantics, and failure rollback rules.
- [ ] A unique durable reservation participates in the same always-on atomic boundary as the mutation write. The successful terminal response is stored before commit; a concurrent duplicate waits for or reads that committed outcome and never executes the mutation body twice. Any cache write is post-commit acceleration only.
- [ ] The durable idempotency key is scoped by mutation class, key value, authenticated principal or anonymous scope, and a canonical digest of operation arguments so unrelated calls cannot collide; reuse with a different digest fails loudly.
- [ ] Tests cover concurrent same-key submissions, a client retry after the database commit but before response receipt/cache fill, stale-reservation recovery and TTL expiry, successful replay, validation/completion/exception rollback, cache unavailability, and sync/async mutation paths where supported.
- [ ] Live `/graphql/` coverage exercises a real fakeshop mutation twice with the same idempotency key and proves the second response replays without a second write; a database-backed concurrency regression proves simultaneous duplicates also write once.

#### Foundation-slice seam

- `DONE-036-0.0.11` owns the base [`DjangoMutation`](docs/GLOSSARY.md#djangomutation) class, generated input types, and shared `errors: list[FieldError]` envelope; this card layers safety semantics onto that lifecycle instead of inventing a separate mutation primitive.
- DRF serializer and Form-based mutation cards inherit the same atomic/idempotency implementation through the shared mutation base once their adapters land.

#### Files likely touched

- `django_strawberry_framework/mutations/` plus the package-owned durable idempotency model and migration.
- `tests/mutations/` plus live fakeshop GraphQL mutation tests.
- `docs/GLOSSARY.md` and the mutation spec when the feature ships.

#### Verified in upstream

- Neither graphene-django nor strawberry-graphql-django ships mutation idempotency; this is a differentiator rather than an upstream-parity card.

#### Why it matters

- Stripe-style idempotency is production table stakes for payment, order, and inventory writes, but Django GraphQL packages leave it to each app.
- Combining the always-on transaction with a durable unique reservation and terminal-response replay makes generated mutations safe across retries, client timeouts, duplicate submissions, concurrent workers, and cache/process loss.

#### Dependencies

- Builds on the core DjangoMutation lifecycle and generated input envelope from DONE-036-0.0.11.

#### Card references

- Dependency: Builds on the core DjangoMutation lifecycle and generated input envelope from DONE-036-0.0.11. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="opt_in_node_sentinel_redaction_tier_metaredaction_mode"></a>
### [TODO-BETA-064-0.1.4 - Opt-in node-sentinel redaction tier (`Meta.redaction_mode`)](KANBAN.html#opt_in_node_sentinel_redaction_tier_metaredaction_mode)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required)
- Status: To Do
- Relative size: L
- Labels: `layer-3`, `permissions`, `public-api`, `security`

#### Predicted files

- `django_strawberry_framework/permissions/` (planned)
- [`django_strawberry_framework/types/`](django_strawberry_framework/types/)

#### Planning note

Strawberry port of django-graphene-filters' node-level sentinel redaction — the third redaction tier the package deferred in spec-034 Decision 6 (row-exclusion) and re-confirmed as a [`FieldSet`](docs/GLOSSARY.md#fieldset) Non-goal (`TODO-BETA-059-0.1.1`). Upstream `django_graphene_filters/object_type.py::AdvancedDjangoObjectType` exposes it as public SDL: `is_redacted = graphene.Boolean(...)` (`:137`), `resolve_is_redacted` (`:151`), `_make_sentinel` (`:200`), and a `get_node` (`:251`) that returns a `pk=0` sentinel in place of a hidden row so a non-null FK to a hidden target still resolves. This card recreates that surface behind an explicit per-`DjangoType` opt-in so a django-graphene-filters consumer relying on `isRedacted` / sentinel masking can port verbatim, without disturbing the default row-narrowing model.

#### Dependencies

- `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- `DONE-034-0.0.10` - Permissions subsystem

#### Scope

- Opt-in switch: introduce `Meta.redaction_mode` on [`DjangoType`](docs/GLOSSARY.md#djangotype) with `"exclude"` (default — the shipped row-narrowing behavior, unchanged) and `"sentinel"` (this tier). The two are mutually exclusive per type; the spec decides whether they may be mixed across a relation chain. The `"exclude"` default leaves every existing schema byte-for-byte unaffected.
- Sentinel chain: in `"sentinel"` mode, a parent row that references a hidden non-null target yields a `pk=0` sentinel object (a `_make_sentinel` analog) instead of excluding the parent row, so the non-null FK still resolves — matching upstream's existence-preserving semantics.
- SDL surface: expose `isRedacted: Boolean` on types in `"sentinel"` mode, resolving `True` for sentinel instances and `False` otherwise (the upstream `resolve_is_redacted` contract).
- Node resolution: override the Relay `get_node` seam (shipped in `DONE-032-0.0.9`) so resolving a hidden id yields the sentinel in `"sentinel"` mode rather than `None`.
- Reconcile with the cascade: in `"sentinel"` mode the masked relation targets must surface as sentinels rather than being narrowed out by [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions) (`DONE-034-0.0.10`). The spec resolves the tension — likely: the cascade narrows top-level rows as it does today, and sentinels appear only for non-null relation targets of rows that already survived the cascade. This is the core design decision.
- Existence-leak posture: state the trade-off explicitly — sentinel masking re-introduces the existence signal that row-exclusion (spec-034 Decision 6) was chosen to avoid. The opt-in default keeps the safe behavior; choosing `"sentinel"` is a conscious consumer acceptance of the leak in exchange for django-graphene-filters parity.

#### Definition of done

- [ ] Add `docs/SPECS/spec-060-node_sentinel-0_1_4.md` covering the `Meta.redaction_mode` switch, sentinel-chain semantics, the `isRedacted` SDL contract, the `get_node` override, and reconciliation with `apply_cascade_permissions`; state the existence-leak trade-off and why the tier is opt-in.
- [ ] Implement the sentinel-row factory and node-resolution hook (extending the `permissions/` surface) plus the `isRedacted` field and `Meta.redaction_mode` wiring on `DjangoType`.
- [ ] `Meta.redaction_mode` defaults to `"exclude"`; all existing schemas and tests stay unchanged under the default. The `"sentinel"` machinery is wired only when the mode is set.
- [ ] Tests mirror the source one-to-one; live HTTP coverage exercises a hidden non-null FK target resolving to a `pk=0` sentinel with `isRedacted = true`, a normal row reading `isRedacted = false`, and `get_node` on a hidden id returning the sentinel in `"sentinel"` mode vs `null` in `"exclude"` mode.
- [ ] Composability tests: `"sentinel"` mode + `apply_cascade_permissions` — the top-level cascade still narrows rows; sentinels appear only for relation targets of surviving rows (no row resurrection, no double counting).
- [ ] Amend the `FieldSet` (`TODO-BETA-059-0.1.1`) Architectural-posture note so its node-sentinel "Non-goal" cross-references this card as the realized opt-in tier.

#### Verified in upstream

- ⚛️ `graphene_django` — `django_graphene_filters/object_type.py::AdvancedDjangoObjectType` exposes node-sentinel redaction as public SDL: `is_redacted = graphene.Boolean(...)` (`:137`), `resolve_is_redacted` (`:151`), `_make_sentinel` (`:200`), and a `get_node` (`:251`) that returns a `pk=0` sentinel in place of a hidden non-null FK target. This card ports that surface behind an opt-in.

#### Architectural posture

- This card is the explicit, opt-in reversal of spec-034 Decision 6. The default stays row-exclusion — the existence-leak-free model; this tier exists only so the one public django-graphene-filters behavior with no analog (`isRedacted` / sentinel FK masking) is portable for consumers who explicitly choose it. It does not become the default and does not weaken the cascade for `"exclude"` schemas.

#### Why it matters

- Closes the single remaining django-graphene-filters public-surface gap recorded by the parity review (finding P2): node-sentinel redaction was the only public upstream behavior with no equivalent and no card — a deliberate non-goal under `spec-034-permissions-0_0_10` Decision 6's row-exclusion model. This converts a buried non-goal into a tracked, opt-in parity feature.
- Lets a django-graphene-filters consumer relying on `isRedacted` / sentinel FK masking migrate verbatim instead of re-architecting around row-exclusion.

#### Dependencies

- `DONE-034-0.0.10` (Permissions subsystem) — extends the `apply_cascade_permissions` / `get_queryset` cascade; this tier reconciles sentinels with cascade narrowing.
- `DONE-032-0.0.9` (Full Relay story) — overrides the shipped `get_node` node-resolution seam.

#### Card references

- Dependency: `DONE-034-0.0.10` (Permissions subsystem) — extends the `apply_cascade_permissions` / `get_queryset` cascade; this tier reconciles sentinels with cascade narrowing. -> `DONE-034-0.0.10` - Permissions subsystem
- Dependency: `DONE-032-0.0.9` (Full Relay story) — overrides the shipped `get_node` node-resolution seam. -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: Amends the `FieldSet` node-sentinel Non-goal note (`TODO-BETA-059-0.1.1`) — this card is the realized opt-in tier that note defers to. -> `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)

<a id="stable_choice_enum_naming_override"></a>
### [TODO-BETA-065-0.1.4 - Stable choice enum naming override](KANBAN.html#stable_choice_enum_naming_override)

- Priority: Low-medium
- Status: To Do
- Relative size: S
- Labels: `choice-enums`, `public-api`, `schema`, `stable-api`

#### Predicted files

- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`tests/types/test_converters.py`](tests/types/test_converters.py)

#### Dependencies

- `WIP-ALPHA-051-0.0.15` - Upstream parity-gap closure

#### Scope

- Add a stable override surface such as `Meta.choice_enum_names = {"status": "ItemStatusEnum"}`.

#### Definition of done

- [ ] New or amended spec documents the override key and ambiguity behavior.
- [ ] `_validate_meta` accepts the key only when the pipeline applies it end-to-end.
- [ ] `convert_choices_to_enum()` uses the explicit name when provided.
- [ ] Tests cover explicit naming, cache reuse, duplicate/conflicting names, and default first-reader behavior.

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_converters.py`

#### Verified in upstream

- Parity target - graphene-django's global choice-enum renaming, two settings in `graphene_django/settings.py`: `DJANGO_CHOICE_FIELD_ENUM_CUSTOM_NAME` takes an import-path string, resolved with `import_string` inside `converter.py`'s `generate_enum_name` and called with the model field, so one callable renames every generated enum process-wide; `DJANGO_CHOICE_FIELD_ENUM_V2_NAMING` is a second global flag selecting an alternate naming template (`ItemStatus` in place of the default `ShopItemStatusChoices`), and exists only to give the first shape a softer alternative. This card supersedes both rather than porting them: a process-wide callable makes the schema's type names a function of settings rather than of the declarations that produced them, so [`Meta.choice_enum_names`](docs/GLOSSARY.md#metachoice_enum_names) puts the name beside the declaration it names and leaves every field that does not set it on the generated default.

#### Open question

- Decide whether this belongs in the consumer-overrides spec or a small choice-enum follow-up spec.

#### Card references

- Dependency: The parity-gap card lands the `django-choices-field` enum-reuse behaviour whose naming surface and cache contract this card stabilizes. -> `WIP-ALPHA-051-0.0.15` - Upstream parity-gap closure

<a id="fakeshop_graphql_schema_activation"></a>
### [TODO-BETA-066-0.1.5 - Fakeshop GraphQL schema activation](KANBAN.html#fakeshop_graphql_schema_activation)

- Priority: Medium
- Status: To Do
- Relative size: M
- Labels: `example-app`, `graphql-api`, `relay`, `schema`

#### Planning note

The product-catalog root schema is already live: four [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) roots with their filtersets, ordersets, and mutations are wired and served (the Relay decisions in `DONE-032-0.0.9` shipped). The remaining unclaimed activation is the Relay `node` / `nodes` root entry points plus the connection `totalCount` opt-in; per-subsystem activation (fieldsets, search, aggregates) is owned by the Slice 4 of the respective Layer-3 subsystem cards, not here.

#### Dependencies

- `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)

#### Scope

- Add a subscription surface to the fakeshop example so subscription behaviour can be exercised at the live tier. Today there is no subscription app anywhere in `examples/fakeshop`, and `django.test.Client` cannot reach a WebSocket, so every subscription row in the suite is a consumer-tier substitution.
- Wire the Relay `node` (single refetch) and `nodes` (batch refetch) root entry points and the connection `totalCount` opt-in on the product-catalog roots, leaving non-opting connections unchanged - the activation half the DoD gates; previously the DoD stated it while Scope named only the subscription surface (scope/DoD mismatch closed at the 2026-08-29 board review).

#### Definition of done

- [ ] Wire the Relay `node` (single-object refetch) and `nodes` (batch refetch) root entry points into the fakeshop product-catalog schema, built on the shipped Relay story (`DONE-032-0.0.9`).
- [ ] Add the connection `totalCount` opt-in on the product-catalog `DjangoConnectionField` roots, leaving connections that do not opt in unchanged.
- [ ] Add in-process `schema.execute_sync` coverage under `examples/fakeshop/apps/products/tests/` for the `node` / `nodes` entry points and `totalCount`.
- [ ] Add live `/graphql/` coverage under `examples/fakeshop/test_query/` exercising a `node` refetch by GlobalID, a `nodes` batch refetch, and a `totalCount` query.
- [ ] The per-event error-policy masking rows run at the live tier against that surface, replacing the consumer-tier substitution in `tests/test_routers.py` that spec-048 carried forward: two events on both WebSocket protocols, each frame carrying the policy message and its own correlation id, plus the `error_policy={"enabled": False}` control row.

#### Card references

- Dependency: The product-catalog root schema is already live; the remaining node / nodes entry points and totalCount opt-in build on the shipped Relay story (`DONE-032-0.0.9`). -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: Historical gate, retyped related: the recut scope (node / nodes + totalCount) does not depend on the Meta-key promotion work, which the aggregation card absorbed at the 2026-08-29 board review. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem

<a id="product_catalog_layer_3_http_graphql_tests"></a>
### [TODO-BETA-067-0.1.5 - Product-catalog Layer 3 HTTP GraphQL tests](KANBAN.html#product_catalog_layer_3_http_graphql_tests)

- Priority: Medium
- Status: To Do
- Relative size: S
- Labels: `example-app`, `graphql-api`, `layer-3`, `tests`

#### Dependencies

- `TODO-BETA-062-0.1.3` - Aggregation subsystem
- `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation

#### Scope

- `examples/fakeshop/apps/products/tests/test_services.py::test_seed_cascade_split_builds_the_fixed_privacy_split` covers `examples/fakeshop/apps/products/services.py::seed_cascade_split` per app: the private category is the only private row and each entry's hops land where the cascade live tests read them.
- Four test-quality / DRY items in `examples/fakeshop/test_query/test_products_api.py`, all deliberately deferred by the spec-036 residual cycle (2026-09-01) to the pass that next opens that file for its own reasons - which is this card. **(a)** The denial assertion is spelled at **9** sites and wants an `_assert_denied(response)` helper; the existence challenge is clear on 9 callers, but **3** of those sites carry a site-specific comment explaining that the denial nulls the whole `data` rather than producing an in-band `FieldError` - the very distinction those rows exist to pin - so the item is not the helper, it is deciding where that explanation lives once the helper hides it. **(b)** The grant-a-codename block is a three-way near-copy; split `_grant_perms()` out of `::_login_with_perm` rather than adding a fourth copy. **(c)** GlobalID type-name literals are unnamed - `"products.category"` **46** times and `"products.item"` **32** - and want two module constants, not a factory. **(d)** `::test_create_item_via_serializer_multipart_upload_to_attachment` builds a local `createItemViaSerializer` document while the module-level `_CREATE_ITEM_VIA_SERIALIZER` already spells that field. The selections genuinely differ today so it is **not** a duplicate - recorded because the file's own convention is "each wire contract spelled once", and two spellings is how that convention erodes.

#### Definition of done

- [ ] Add live `/graphql/` acceptance tests under `examples/fakeshop/test_query/` for the activated product-catalog schema, reusing the library app's placement and schema-reload pattern.
- [ ] Cover the product-catalog connection / query fields and the other activated Layer 3 public surfaces end-to-end over HTTP.
- [ ] Keep per-app in-process `schema.execute_sync` tests under `examples/fakeshop/apps/products/tests/`; live HTTP tests stay under `examples/fakeshop/test_query/`.

#### Why it matters

- The library app already has live `/graphql/` acceptance tests under `examples/fakeshop/test_query/`.

#### Test plan

- bounded test suite: live `/graphql/` acceptance tests for the activated product-catalog schema, reusing the library app's placement + schema-reload pattern.

#### Open question

- Does the redundant `view_<model>` branch in the four fakeshop permission hooks stay? Each hook's `elif user and user.has_perm("products.view_<model>")` arm evaluates to the same expression as the fall-through it precedes, so it cannot change the result and costs a permission-table read per request per type. It is **spec-conformant** - `spec-034` Slice 4 and Decision 6's consumer-recipe divergence both demand it - so collapsing it is a contract change, not a cleanup. Paths: **(a)** keep it and record in the spec *why* a redundant branch is deliberate, **(b)** collapse each hook and add a spec sentence saying the grant is deliberately not a branch, or **(c)** give the branch different behaviour, which reverses Decision 6's recorded divergence and belongs to `TODO-BETA-064-0.1.4` rather than here. **A collapse is now safe to attempt**: the spec-034 residual cycle's R3 landed parametrized staff rows in `examples/fakeshop/test_query/test_products_api.py` that assert the `view_<model>` actor explicitly for all four models, so a mistake in the collapse fails loudly. Recorded 2026-08-28 (R1c finding M1, escalated as contract-level).

#### Card references

- Dependency: Depends on the activated product-catalog schema; these HTTP tests exercise the surface that card wires. -> `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation
- Dependency: The acceptance sweep lands after the Layer-3 trio so it sees every activated Layer-3 surface; the aggregation card is the last of the trio. -> `TODO-BETA-062-0.1.3` - Aggregation subsystem

<a id="structural_optimization_templates_and_nested_sidecar_batching"></a>
### [TODO-BETA-068-0.1.6 - Structural optimization templates and nested sidecar batching](KANBAN.html#structural_optimization_templates_and_nested_sidecar_batching)

- Priority: High
- Status: To Do
- Relative size: L
- Labels: `internal`, `optimizer`, `performance`, `query-planning`
- Spec: [spec-068-structural_templates-0_1_6.md](docs/SPECS/spec-068-structural_templates-0_1_6.md)

#### Predicted files

- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/optimizer/`](django_strawberry_framework/optimizer/)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- [`tests/optimizer/`](tests/optimizer/)

#### Planning note

The second of two graph foundation cards, sibling to the graph substrate (TODO-BETA-058-0.1.1). Where the substrate ships the shared planning vocabulary, this card ships the optimizer architecture that consumes it — four pillars: (1) the structural/bound plan split (`StructuralOptimizationTemplate` cacheable across requests, `BoundOptimizationPlan` request-local, `OptimizationPlan` produced by binding); (2) root-subtree structural cache keys replacing whole-operation AST keys; (3) nested sidecar batching — filtered/ordered/search-bearing nested connections stop executing per parent; (4) the operation plan map replacing last-wins introspection, plus `RowIdentityProof` enforcement at the window gate. Seated immediately ahead of explain (TODO-BETA-069-0.1.6), which renders the plan map and shares the `0.1.6` joint cut. No new consumer surface — every object is internal optimizer vocabulary; the observable contract is query counts, cache behavior, explain completeness, and strict-mode errors.

#### Dependencies

- `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning

#### Scope

- Slice 1 — template/bound core: `optimizer/templates.py` with frozen `StructuralOptimizationTemplate` (relative paths, field dependency graph, visibility binding slots, nested argument slots, row-identity proof recipe) and `BoundOptimizationPlan` (absolute paths, database alias, visibility querysets, concrete `Prefetch` objects, normalized argument values); the normalized root-subtree fingerprint builder; the binding pipeline producing today's `OptimizationPlan`; package tests proving bind-equivalence with directly-walked plans. Behavior-neutral by design.
- Slice 2 — cache rekey, response-path rebasing, operation plan map: `DjangoOptimizerExtension._build_cache_key` moves to the subtree fingerprint (exact owning type identity, root field/return type, normalized subtree selection, only the directive/pagination slots referenced inside the subtree, strategy config); templates store relative paths and binding rebases them under the actual alias; `_publish_plan_to_context` publishes the plan map keyed by root execution identity while the legacy `DST_OPTIMIZER_PLAN` last-wins key is retained for the explain card to retire.
- Slice 3 — nested sidecar batching: `optimizer/sidecar.py` with the eight-step normalization (edge-scoped child base -> [FilterSet](docs/GLOSSARY.md#filterset) once -> [OrderSet](docs/GLOSSARY.md#orderset) once -> deterministic order -> row-identity proof -> partition by parent join key -> window/lateral page -> attach per response-key `to_attr`); `_divergent_key_windows` plans argument-bearing response keys instead of abandoning them; `connection.py::_build_relation_connection_resolver` consumes the batched result attribute; the request-bound sidecar plan cache; per-alias batching.
- Slice 4 — row-identity enforcement + live activation: `unwindowable_child_queryset_reason` composes with the `RowIdentityProof` grades; strict targets raise a targeted unproven-row-identity error, non-strict targets fall back visibly, no automatic `DISTINCT`; the live fakeshop matrix (R1 five-root cache isolation, R7 ordered nested batching, R8 gate arms, R10 plan-map completeness, the R3 filtered arm promoted from characterized to asserted-equal query counts).
- Slice 5 — docs + card wrap: TREE / GLOSSARY / `test_query` README updates, audit the explain-card amendment is honored, flip this card. Version triplet, `CHANGELOG.md`, and release prose untouched — owned by the explain card's `0.1.6` joint cut.
- Changed seams: `optimizer/extension.py` (`_build_cache_key`, `_publish_plan_to_context`), `optimizer/walker.py` (`_plan_prefetch_relation` — visibility becomes a binding slot, not `cacheable = False`), `optimizer/nested_planner.py` (`_divergent_key_windows`), `optimizer/nested_fetch.py` (`unwindowable_child_queryset_reason`), `connection.py` (`_build_relation_connection_resolver`). New modules consume `graph/` and are not imported by it.

#### Definition of done

- [ ] `StructuralOptimizationTemplate` / `BoundOptimizationPlan` ship frozen; no request value storable in any structural object; the adversarial construction test raises.
- [ ] The plan cache keys by root-subtree fingerprint; the R1 matrix is green live (isolation, aliasing, re-embedding, full-hit repeat).
- [ ] Visibility-bearing relation templates are cross-request cacheable; `get_queryset` binds per request; one bound child recipe per relation/argument/scope key per request.
- [ ] Filtered/ordered/search-bearing nested connections batch with query counts independent of parent count (exact per-backend equalities, never inequalities); per-alias batching proven; the R3 filtered arm asserts equalities.
- [ ] Strict mode refuses unproven window shapes with a targeted error; non-strict falls back visibly; no code path injects `DISTINCT`.
- [ ] The operation plan map is complete and deterministic under reversed async completion order; the legacy key still serves existing readers.
- [ ] Sync and async agree across every arm; the no-extension and `OptimizerHint.SKIP` arms are unchanged; 100% package coverage; live-first placement respected.
- [ ] Version triplet and `CHANGELOG.md` untouched — the `0.1.6` release state is owned by the explain card's joint cut.

#### Architectural posture

- **Amendment obligations recorded at this card's creation** — explain (TODO-BETA-069-0.1.6) consumes the operation plan map and retires the legacy `DST_OPTIMIZER_PLAN` key; the adversarial suite (TODO-BETA-072-0.1.8) gains template-store, binding-boundary, and proof-gate targets. This card changes the introspection data, not its readers — the legacy key stays last-wins until explain rewires.
- No request value — user, tenant, queryset, database alias, or argument value — is storable in any structural object (the substrate card's posture, extended verbatim); enforced structurally and tested adversarially. Pluggable nested-fetch strategies must consume the sidecar normalization and the `RowIdentityProof` gate — a strategy that self-certifies child row identity would reopen the window-safety hole in a new backend. The framework never injects `DISTINCT` to launder an unproven shape.

#### Why it matters

- Whole-operation cache keys churn sibling plans: five roots across 32 combinations of five binary directive/pagination choices can occupy 160 entries of a 256-cap cache that evicts a quarter when full; toggling one root's `@include` variable invalidates every sibling's plan.
- Request-bound visibility poisons cacheability: one `get_queryset`-bearing child type marks the entire parent plan `cacheable = False`, so the most security-sensitive types are exactly the ones that replan on every request.
- Filtered/ordered nested connections execute per parent: one hundred parents with a filtered child connection issue one hundred (or, with `totalCount`, two hundred) child statements. The substrate card pinned this arm as characterized-only and assigned closing it here.
- Introspection is last-wins and windows are unproven: a five-root operation exposes only the last-published plan (completion-order dependent under async), and the window gate passes a consumer join that multiplies child rows — corrupting `totalCount`, page boundaries, and next-page flags.

#### Dependencies

- Gated on the substrate landing first: `EdgeScope` supplies the visibility-scoped child base the sidecar pipeline normalizes, `RowIdentityProof` is the vocabulary the window gate enforces, `FieldDependencyPlan` feeds the template's dependency graph, and the operation memo is the request-local tier the binding reuses.

#### Card references

- Dependency: Gated on the substrate landing first: `EdgeScope` supplies the visibility-scoped child base the sidecar pipeline normalizes, `RowIdentityProof` is the vocabulary the window gate enforces, `FieldDependencyPlan` feeds the template's dependency graph, and the operation memo is the request-local tier the binding reuses. -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Related: Amendment obligation: explain renders the operation plan map (every root exactly once, shared dependencies with hit counts, redacted scope values) and retires the legacy last-wins `DST_OPTIMIZER_PLAN` context key. -> `TODO-BETA-069-0.1.6` - Optimizer explain mode
- Related: Amendment obligation: the adversarial suite gains structural-template targets (template-store keying/under-keying, the structural/bound binding boundary, proof-gate refusal paths, sidecar cache isolation). -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite
- Related: Owns the fetch-strategy seam whose strategy interface this card's sidecar pipeline cites. -> `TODO-ALPHA-078-0.0.17` - Owning spec for the nested-connection fetch-strategy seam

<a id="optimizer_explain_mode"></a>
### [TODO-BETA-069-0.1.6 - Optimizer explain mode](KANBAN.html#optimizer_explain_mode)

- Priority: High
- Status: To Do
- Relative size: M
- Labels: `debugging`, `developer-tools`, `graphql-api`, `optimizer`, `performance`, `query-planning`

#### Predicted files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`examples/fakeshop/test_query/`](examples/fakeshop/test_query/)
- [`tests/optimizer/`](tests/optimizer/)

#### Planning note

Promoted from BACKLOG.md item 7 as a pre-1.0 differentiator: expose the optimizer plan already stashed on the GraphQL context as an opt-in response-extension payload so consumers can see exactly what the Django ORM optimizer planned for a request.

#### Dependencies

- `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

#### Scope

- Add an opt-in Strawberry response extension for optimizer explain output, exposed through the GraphQL response `extensions` map under a stable package-owned key.
- Serialize the existing `info.context.dst_optimizer_plan` data into a JSON-safe payload instead of re-planning the query.
- Include the ORM planning facts developers need to debug performance: `select_related`, `prefetch_related` / `Prefetch` chains, [`only()` projection](docs/GLOSSARY.md#only-projection), optimizer hints, FK-id elisions, and strictness decisions where available.
- Provide a request-level activation surface such as a header or context flag; keep explain output off by default.
- Guarantee explain mode is observational only: enabling it must not change SQL planning, resolver behavior, GraphQL data shape, or query results.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1, TODO-BETA-068-0.1.6): render the operation plan map instead of the single last-wins `info.context.dst_optimizer_plan`, and retire that legacy context key once this card lands (the sibling card publishes the map alongside it precisely so this card owns the cutover). Each entry exposes root field / type / model, structural template fingerprint and cache hit or miss, request binding identity without secret values, select / prefetch / computed dependencies, direct and correlated predicate branches, contextual edge scopes, nested strategy and sidecar plan, row-identity proof, fallback reasons, estimated query families, strictness keys, database alias, and whether total count and page share a statement. Shared operation dependencies appear once with redacted keys and hit / miss counts; the map stays complete and deterministic under any async completion order.
- **Visibility bindings in the plan map:** each rendered plan-map entry includes a "visibility bindings" field fed by the structural-template sibling card's visibility binding slots: per slot and per root base queryset, which hook or declared rule bound, at which site, whether a bypass or a restriction decided the verdict, which cascade edges ran, and hit counts, with actor values redacted; visibility explain is a row kind of this payload and never a second response extension.

#### Definition of done

- [ ] A new or amended spec documents the response-extension key, toggle surface, payload shape, privacy boundaries, and compatibility contract.
- [ ] Implementation reuses the existing optimizer plan metadata and does not duplicate the optimizer walker.
- [ ] Tests cover disabled-by-default behavior, enabled response-extension output, JSON-serializable payload shape, and no regression in normal query results.
- [ ] Live `/graphql/` coverage exercises a real fakeshop query and verifies the response carries normal `data` plus the explain extension only when requested.
- [ ] Documentation surfaces the feature as planned or shipped in `docs/GLOSSARY.md`, `docs/README.md`, and `KANBAN.md` as appropriate for the shipping slice.

#### Foundation-slice seam

- [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension) already stores the computed plan on `info.context.dst_optimizer_plan`; this card promotes that internal diagnostic seam into a documented consumer-facing debug payload.
- Pairs naturally with the backlog's query-time optimizer disable idea, but does not depend on it.

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/plans.py` or a new small explain serializer module if the payload needs normalization
- `tests/optimizer/`
- `examples/fakeshop/test_query/`
- `docs/GLOSSARY.md` and related standing docs when the feature ships

#### Why it matters

- This is GraphiQL-grade visibility for the Django ORM half of GraphQL requests. Consumers can answer `what did the optimizer do for this query?` without reading SQL logs or reverse-engineering the planner.
- Neither graphene-django nor strawberry-graphql-django ships this. It reinforces the package's optimizer-first mission at a low implementation cost.

#### Card references

- Related: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Dependency: Amendment source: the sibling foundation card ships the structural/bound plan split, the operation plan map, and the row-identity enforcement gate this card consumes. -> `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

<a id="configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key"></a>
### [TODO-BETA-070-0.1.7 - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)](KANBAN.html#configurable_filterlogic_key_namespace_filter_keyand_keyor_keynot_key)

- Priority: Low
- Parity: ⚛️ graphene-django (Required)
- Status: To Do
- Relative size: M
- Labels: `config`, `filters`, `public-api`

#### Predicted files

- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/filters/sets.py`](django_strawberry_framework/filters/sets.py)
- [`django_strawberry_framework/utils/connections.py`](django_strawberry_framework/utils/connections.py)

#### Planning note

Promoted from BACKLOG.md as the remaining django-graphene-filters configuration-parity gap: recreate the configurable filter-tree key namespace — `DJANGO_GRAPHENE_FILTERS` `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` (`django_graphene_filters/conf.py:13-16`, defaults `filter`/`and`/`or`/`not`). The package currently hardcodes the GraphQL names (`_LOGIC_KEYS` at `filters/inputs.py:131`, `CONNECTION_FILTER_KWARG` at `utils/connections.py:41`); this card makes them settings-driven while keeping the defaults and the default SDL byte-for-byte unchanged.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

#### Scope

- Settings surface: extend the `DJANGO_STRAWBERRY_FRAMEWORK` namespace (`conf.py`) with `FILTER_KEY` (default `"filter"`), `AND_KEY` (`"and"`), `OR_KEY` (`"or"`), and `NOT_KEY` (`"not"`), mirroring DGF's `DJANGO_GRAPHENE_FILTERS` keys and defaults, read through the existing `Settings` accessor so a host project renames them without touching package code.
- Logic-key rework: `_LOGIC_KEYS` (`filters/inputs.py:131`) and its import-time derivatives in `filters/sets.py` (`_LOGIC_PYTHON_ATTRS`, `_LOGIC_WIRE_BY_PYTHON_ATTR`, the `:1084` loop) are frozen module constants computed at import. Make the GraphQL wire names settings-derived and resolve the import-ordering tension — likely lazy resolution at schema-build time rather than at module import — so settings declared in the host `settings.py` are honored.
- Filter argument: the connection `filter` argument name (`CONNECTION_FILTER_KWARG = "filter"`, `utils/connections.py:41`) becomes `FILTER_KEY`-driven; the connection field signature, the resolver kwarg lookup, and any `kwargs.get("filter")` sites follow.
- Python-attr vs wire-name split: keep the Python-side attribute names (`and_`/`or_`/`not_`) stable — they are language-mandated keyword escapes, not parity surface. Only the GraphQL wire names are configurable; the spec pins which layer the rename applies to.
- Default parity: with no settings set, the generated SDL is byte-for-byte unchanged (`filter`/`and`/`or`/`not`), and the `conf.py` malformed/partial-mapping coercion contract still falls back to these defaults.

#### Definition of done

- [ ] Add a spec (or amend the filtering spec) covering the four settings keys and DGF-matching defaults, the import-time → schema-build-time resolution change, the Python-attr/wire-name split, and the default-unchanged guarantee.
- [ ] `conf.py` exposes `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` with DGF-matching defaults via the existing `Settings` accessor.
- [ ] `_LOGIC_KEYS` / its derived structures and `CONNECTION_FILTER_KWARG` resolve from settings at schema-build time (not import time); the spec documents the exact resolution point.
- [ ] Default (no settings) generated SDL is unchanged and existing filter tests pass untouched.
- [ ] Tests mirror upstream one-to-one: a host setting renames the operator keys and the `filter` argument in generated SDL and they filter correctly end-to-end (package + live HTTP); a malformed/partial settings dict falls back to defaults per the `conf.py` coercion contract.

#### Verified in upstream

- ⚛️ `graphene_django` — `django_graphene_filters/conf.py:13-16` defines `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` (defaults `filter`/`and`/`or`/`not`) under the `DJANGO_GRAPHENE_FILTERS` settings dict, letting the schema author rename the filter-tree operator keys. This package hardcodes them (`filters/inputs.py:131` `_LOGIC_KEYS`, `utils/connections.py:41` `CONNECTION_FILTER_KWARG`); this card ports the rename capability behind the same kind of settings dict.

#### Architectural posture

- This recreates the one DGF filtering configuration surface with no package analogue. The fixed wire names were a deliberate simplification; this card makes them configurable behind settings while keeping the defaults — and the byte-for-byte default SDL — unchanged. The cost is moving `_LOGIC_KEYS` off the import-time fast path to a settings-resolved value; the spec pins the resolution point so import ordering stays correct. It does not change the default schema and only the GraphQL wire names are configurable — the Python attribute names stay fixed.

#### Why it matters

- Closes the remaining django-graphene-filters configuration-surface gap: `DJANGO_GRAPHENE_FILTERS` `FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY` has no package analogue.
- Lets a django-graphene-filters consumer who renamed their filter-tree keys (e.g. to avoid clashing with an existing `filter`/`and`/`or`/`not` model field) migrate without a breaking schema rename.

#### Dependencies

- `DONE-027-0.0.8` (Filtering subsystem) — owns `_LOGIC_KEYS` and the filter-tree input-type generation whose wire names this card makes configurable.
- `DONE-030-0.0.9` ([`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield)) — owns the `filter` argument (`CONNECTION_FILTER_KWARG`) that `FILTER_KEY` renames.

#### Card references

- Dependency: `DONE-027-0.0.8` (Filtering subsystem) — owns `_LOGIC_KEYS` and the filter-tree input-type generation whose wire names this card makes configurable. -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: `DONE-030-0.0.9` (`DjangoConnectionField`) — owns the `filter` argument (`CONNECTION_FILTER_KWARG`) that `FILTER_KEY` renames. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

<a id="migration_and_adoption_guides"></a>
### [TODO-BETA-071-0.1.8 - Migration and adoption guides](KANBAN.html#migration_and_adoption_guides)

- Priority: Medium
- Status: To Do
- Relative size: L
- Labels: `docs`, `guides`, `public-api`

#### Dependencies

- `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)

#### Scope

- Add a `graphene-django` migration guide covering `DjangoObjectType` to [`DjangoType`](docs/GLOSSARY.md#djangotype), enum/field conversion differences, query optimizations, and Relay caveats.
- Add a `strawberry-graphql-django` migration guide covering decorator-to-`Meta` translation, optimizer differences, `get_queryset`, and optimizer hints.
- Add concise notes for DRF / django-filter users mapping serializers/filtersets/orders into the planned Layer 3 surfaces.
- Decide whether the cookbook migration recipe should name [`DjangoSchema`](docs/GLOSSARY.md#djangoschema) rather than plain `strawberry.Schema`. The cookbook port is query-only, so plain `Schema` is correct as written, but a reader who later adds a generated mutation hits the write pipeline refusing to run under it. Changing the recipe changes spec-044 migration story, which is why it was left.
- Document the choice-enum member-name collision as a hard build break in the `graphene-django` guide: upstream dedups two choice values that sanitize to the same enum member by appending a positional suffix derived from how many names it has already converted, so the client-visible member name is a function of `choices` declaration order; `django_strawberry_framework/types/converters.py::build_enum_from_choices` instead raises [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) naming both colliding values. A model that builds under `graphene-django` fails to build here, at type-creation time and before any query runs, so the guide must name the fix: rename one side or split the field.
- Document the choices-to-enum default in both guides: `graphene-django` converts choice columns to enums by default but ships the global `DJANGO_CHOICE_FIELD_ENUM_CONVERT` switch plus a per-type `convert_choices_to_enum` opt-out, and `strawberry-graphql-django` leaves choice columns as raw scalars by default behind `GENERATE_ENUMS_FROM_CHOICES`; here `django_strawberry_framework/types/converters.py::convert_choices_to_enum` always generates the enum and there is no global or per-type opt-out at all. For a `strawberry-graphql-django` migrant that is a whole-schema difference on every choice column; for a `graphene-django` migrant it hits every column the opt-out had covered. The only opt-out here is a consumer-authored annotation on that column, so the guide states the default once up front rather than field by field.
- Document the accepted request content types beside the UTF-8 wire-contract note: `graphene-django`'s view also parses `application/graphql` bodies and `application/x-www-form-urlencoded` / `multipart/form-data` form posts, and honours a `?pretty` query parameter on the response; this package accepts `application/json` only, plus `multipart/form-data` when the view is constructed with `multipart_uploads_enabled`. Anything else is a 400 'Unsupported content type' from the engine before the document is parsed, so a migrant reusing a `graphene-django` curl recipe or client sees the request rejected rather than executed, and response formatting is the client's job here.
- Document mutation atomicity in the `graphene-django` guide: upstream's `ATOMIC_MUTATIONS` is opt-in and off by default, settable globally or per database through the `DATABASES` entry, whereas `django_strawberry_framework/schema.py::DjangoMutationExecutionContext` holds every generated top-level mutation's transaction open through response completion unconditionally, with no setting that turns it off. Ours is the stronger guarantee, but the setting name and the opt-in to always-on flip are stated nowhere, so the migrant searching for `ATOMIC_MUTATIONS` needs one sentence saying it no longer exists and why.
- Map upstream's per-field manager and page-cap knobs onto their analogs here. `graphene-django`'s `on="manager"` (a [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) keyword) picks a named model manager; here the manager choice is a consumer resolver or `get_queryset` returning a `Manager`, which is coerced to a queryset. The per-field connection caps, `graphene-django`'s `max_limit=` and `strawberry-graphql-django`'s `max_results=`, map to the schema-wide `relay_max_results` passed through `strawberry_config`, under the request ceiling `max_page_size` on `django_strawberry_framework/resource_policy.py::ResourcePolicy`; an over-cap `first` / `last` raises, as upstream. `max_list_rows` bounds raw lists; its nearest upstream analog is `strawberry-graphql-django`'s `PAGINATION_MAX_LIMIT`. The note must say that an explicit over-ceiling `limit` on `django_strawberry_framework/list_field.py::DjangoListField` raises [`ListArgumentError`](docs/GLOSSARY.md#listargumenterror), while an omitted `limit`, the generated many-side relation lists and `django_strawberry_framework/resource_policy.py::bounded_rows` truncate silently to a short page with no error.
- Add a one-line dataloader note to both guides: `strawberry.dataloader` ships with the engine and is available unchanged, so a migrant's existing dataloaders keep working, but this package's own answer to N+1 is the query optimizer plus strictness rather than a dataloader layer. One line only here; the fuller GLOSSARY / README statement belongs to the alpha documentation-debt card.
- Document the unregistered relation target as the loudest migration break, because it is the first thing many migrants hit: `graphene-django` silently drops a relation whose target model has no registered type (its `dynamic_type` returns `None`) and `strawberry-graphql-django` falls back to a `pk`-only `DjangoModelType`, while `django_strawberry_framework/types/finalizer.py::_format_unresolved_targets_error` raises `ConfigurationError` at finalization listing every unresolved target. The guide must say the failure is deliberate, not a bug, and name the two fixes - declare a `DjangoType` for the target model, or exclude the field.
- Name `DurationField` as a graphene-django migration break: `graphene_django/converter.py::convert_field_to_float` registers `models.DurationField` alongside `models.FloatField`, so a migrant's duration column shipped as a `Float` of seconds, and here it raises `ConfigurationError` at type creation until the consumer registers a scalar through `django_strawberry_framework/types/converters.py` #"SCALAR_MAP". That is the deferred-scalar posture and it is deliberate - a bare `Float` loses the unit, and a consumer who needs a duration on the wire is better served choosing the representation than inheriting seconds-as-float by default - so the guide's job is to name `Float` as what they are replacing, which makes the fix mechanical. Verified against both reference trees 2026-08-28: this is single-upstream, `strawberry-graphql-django` has no `DurationField` handling at all. Do NOT extend the note to `BinaryField`: `graphene_django` has no `BinaryField` registration and no `Base64` reference anywhere in the package (`graphene.Base64` exists in graphene core, but nothing wires it to the field), so `BinaryField` raising here is not a divergence from either upstream.
- Give both guides an upstream-settings disposition table, because a migrant's first move is to search for the key they used to set and silence reads as a bug rather than a decision. Five config surfaces have no equivalent here and each owes one line saying so and why. (a) `strawberry-graphql-django`'s `TYPE_DESCRIPTION_FROM_MODEL_DOCSTRING` (`strawberry_django/settings.py`, default `False`) publishes the model docstring as the GraphQL type description; here it is [`Meta.description`](docs/GLOSSARY.md#metadescription), defaulting to the `DjangoType`'s own docstring, and the setting is not reproduced because Django synthesizes a `Model(field, field, ...)` docstring for every model that does not define one - so upstream's setting publishes a generated field list for exactly the models nobody documented. (b) `graphene-django`'s four GraphiQL knobs `SUBSCRIPTION_PATH`, `GRAPHIQL_HEADER_EDITOR_ENABLED`, `GRAPHIQL_SHOULD_PERSIST_HEADERS` and `GRAPHIQL_INPUT_VALUE_DEPRECATION` (`graphene_django/settings.py`) configure a development IDE the package does not own; here the engine's IDE is selected per mount with the inherited `graphql_ide=` keyword on `django_strawberry_framework/views.py::DjangoGraphQLView`, and `SUBSCRIPTION_PATH` is structurally moot because the WebSocket route is the router's `websocket_url_pattern`, not a hint rendered into HTML. (c) `graphene-django`'s `MAX_VALIDATION_ERRORS` caps how many validation errors a rejected document reports; here `django_strawberry_framework/resource_policy.py::ResourcePolicy` bounds the document BEFORE validation runs rather than truncating the report afterwards. (d) `strawberry_django/extensions/django_validation_cache.py::DjangoValidationCache` caches validation verdicts in a Django cache backend; there is no equivalent and it is refused rather than merely absent - a poisoned entry in a shared cross-process store is a schema-wide correctness failure rather than a slow request, and upstream documents its own default key function as unsafe for memcached. The in-process plan cache covers the performance need; document-level parse/validation reuse is the post-`1.0.0` `operation_document_and_plan_cache` row in `BACKLOG.md`, deliberately a bounded per-process LRU. (e) `graphene-django`'s `CAMELCASE_ERRORS` (`graphene_django/settings.py`, default on) camelizes `ErrorType` keys; there is no toggle here: every `FieldError` keys to the GraphQL input field the client sent (a camelized name is not always that name, given the `categoryId` FK suffix and `Meta.input_class` renames), and the non-field key stays `__all__`, not graphene's `_All__`. (a)-(d) verified against the reference trees 2026-08-28.
- Document the two `strawberry-graphql-django` mutation write surfaces that do not exist here, in that guide's write chapter. FIRST, filter-selected bulk update / delete: upstream's `strawberry_django/mutations/fields.py::DjangoUpdateMutation.instance_level_update` writes a predicate-selected row set, gated by `ALLOW_MUTATIONS_WITHOUT_FILTERS` (`strawberry_django/settings.py`, default `False`). Here the generated write pipeline's guarantee is locate-one then lock then authorize then attest, and a predicate-selected row set carries none of the four - which is why upstream needed a settings-level safety valve to make the shape survivable at all. The migration is one row per operation, located through the target type's `get_queryset`; a genuine bulk write becomes a consumer-authored mutation owning its own authorization story. SECOND, `through_defaults`: upstream's `strawberry_django/mutations/resolvers.py::update_m2m` writes intermediate-table columns through a relation input, which here would make a relation argument silently responsible for rows in a third table and contradicts the replace-only M2M contract. The migration is a consumer-authored mutation over the through model itself, an ordinary model with an ordinary write surface. Both verified against the reference checkout 2026-08-28.
- Document the per-field permission ladder as the largest single `strawberry-graphql-django` translation - it is that library's most-used surface and nothing here replaces it field-for-field. Upstream ships `strawberry_django/permissions.py::DjangoPermissionExtension` with `IsAuthenticated`, `HasPerm`, `HasSourcePerm` and `HasRetvalPerm` applied per field as Strawberry extensions. Here the read side is `get_queryset` for row visibility plus `django_strawberry_framework/permissions.py::apply_cascade_permissions` for its transitive closure, and the write side is `Meta.permission_classes`. The guide must say WHY the shape is not reproduced, not only that it is absent: upstream's `fail_silently` degradation chain resolves a denial to `None`, `[]`, an empty queryset or `OperationInfo` depending on the return type, so an authorization outcome depends on schema shape and a denial becomes indistinguishable from an empty result - the opposite of this package's fail-loud posture. Scope boundary for whoever writes this: the decorator SHAPE is refused permanently, but the read-side CAPABILITY is only deferred, and the beta parity claim's carve-out for it already lives on the beta release card. This guide item states the translation; it must not restate the carve-out.
- Document the mutation error-payload shape change in the `strawberry-graphql-django` guide, because it breaks client documents rather than server code. Upstream returns errors as a member of the payload union (`OperationInfo` in `strawberry_django/mutations/fields.py`), so every mutation's success type is conditional on the client selecting the right branch, and a client that omits the error branch silently receives an empty selection instead of a failure. Here the payload shape is fixed and errors arrive in the [`FieldError` envelope](docs/GLOSSARY.md#fielderror-envelope), always in the same place. The migration is mechanical but touches every mutation document a migrant ships: drop the `... on OperationInfo` inline fragment and select the `errors` field instead. The argument for the fixed shape is in `docs/SPECS/spec-036-mutations-0_0_11.md`.
- Document the batched-request response shape in the `graphene-django` guide: upstream's `graphene_django/views.py::GraphQLView.get_response` wraps each batched operation in a synthetic per-entry `id` / `status` envelope and collapses the HTTP status to the maximum across entries, so one failing operation changes the status seen for every sibling. Here batching is the engine's own, enabled per schema through Strawberry's `batching_config` and OFF by default, and an enabled batch returns a plain JSON array under one status with no synthetic envelope. The guide must name both halves - the response shape change AND that batching has to be turned on at all - because a migrant whose client batches gets a flat 400 "Batching is not enabled" on the first request rather than a shape difference to notice later.
- Document the Channels ASGI router migration row in the `strawberry-graphql-django` guide's symbol-equivalents table, with the three reasons it is not a drop-in rename. `strawberry_django.routers.AuthGraphQLProtocolTypeRouter` maps to `django_strawberry_framework/routers.py::DjangoGraphQLProtocolRouter`, but the constructor differs in ways a migrant hits on the first run: `django_application` is **required** here and second-positional, where upstream defaults it to `None` and builds its own; the websocket route argument is `websocket_url_pattern` with default `r"^graphql/?$"`, where upstream spells it `url_pattern` with default `"^graphql"`; and upstream's router also serves GraphQL over HTTP from the same object, while this one dispatches `"http"` straight to the project's own ASGI handler - so the HTTP half is a separate URLconf entry for `django_strawberry_framework/views.py::DjangoGraphQLView` rather than something the router provides. The card that shipped the router hands this card the row content rather than the symbol mapping alone; the mapping itself already arrives as that card's related reference.
- Carry the list-pagination mapping of `docs/SPECS/spec-050-list_field_arguments-0_0_15.md` Decision 11 into both guides: `strawberry-graphql-django`'s `pagination=True` / `OffsetPaginationInput` becomes flat `offset` / `limit` (and `orderBy`) on [`DjangoListField`](docs/GLOSSARY.md#djangolistfield), `OffsetPaginated` has no envelope equivalent (flat list, or a connection when count metadata is needed), nested `apply_window_pagination` becomes a nested connection, and a nonzero `offset` requires an active order; for `graphene-django`, a consumer resolver no longer receives the list arguments and a resolver returning `None` stays `None` instead of falling back to the default manager.

#### Definition of done

- [ ] New docs are added for the two major migration paths.
- [ ] README and `GLOSSARY.md` link to the migration docs.
- [ ] Guides distinguish shipped migration steps from planned Layer 3 migration targets.

#### Files likely touched

- future migration docs under `docs/`
- `docs/README.md`
- `docs/GLOSSARY.md`

#### Card references

- Dependency: The final configurable filter/logic key namespace (`TODO-BETA-070-0.1.7`) must ship first so both migration guides describe the released public surface. -> `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)

<a id="adversarial_non_live_test_suite"></a>
### [TODO-BETA-072-0.1.8 - Adversarial non-live test suite](KANBAN.html#adversarial_non_live_test_suite)

- Priority: Medium-high
- Status: To Do
- Relative size: L
- Labels: `adversarial-testing`, `hardening`, `tests`

#### Predicted files

- [`examples/fakeshop/test_query/README.md`](examples/fakeshop/test_query/README.md)
- [`tests/`](tests/)

#### Dependencies

- `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching
- `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)

#### Scope

- Hostile wire values: bad-base64 / wrong-`type_name` GlobalIDs, oversized `in` lists, unicode / emoji / null bytes, `strawberry.UNSET` / `None` across every operator-bag slot.
- Add a row distinguishing `consumers.py::_attempt_close`'s `ABANDONED` record from `settle`'s cancel-and-await. The two boundaries are currently jointly pinned - the same pair of rows fails for either mutation - so neither is independently proven.
- `tests/test_views.py::_strawberry_patch_opted_out` asserts `_patch_is_installed() is False` after restoring the originals, so the package-tier simulation is proven to un-install the patch.
- Re-anchor failability manifest entry 6 onto the middleware-ordering audit's decision expression rather than its initialization line, if the manifest is ever re-derived. Anchoring an aggregate inside the guard under test is the trap: one measured attempt reported four rows rather than zero, which would have passed the acceptance rule while measuring a third of its boundary. A zero gets graded; a plausible count gets graded by nobody.
- **Consume-the-substrate amendment** (TODO-BETA-058-0.1.1, TODO-BETA-068-0.1.6): add graph-substrate and structural-template attack targets — five-root operations; related-row existence leaks; selected-child leakage past a visible parent; same-related-row authorization false positives; custom-visibility outer fan-out; duplicate child rows under windows; whole-operation cache fragmentation; operation-memo scope isolation (viewer, tenant, database alias, cancellation); async plan-map ordering; structural-template under-keying (a referenced directive or pagination slot missing from the fingerprint must fail closed to a walk, never to a wrong reuse); the structural/bound binding boundary (no request value constructible into a structural object); proof-gate refusal paths; and snapshot consistency in the PostgreSQL tier.
- `tests/types/test_definition_order.py::test_filterset_class_resolves_across_module_boundary`'s module eviction is weaker than its comment claims. The row pops two fixture modules from `sys.modules` and re-imports them with `from tests.types.fixtures import branch_module, shelf_module`, under a comment asserting the pop makes the next import re-execute the module. Measured by the spec-010 residual cycle (2026-08-15): it does not - the parent package's still-set attribute satisfies the `from ... import`, so the stale module object comes back and `sys.modules` is never repopulated. The row passes today only because nothing imports those fixture modules first, a latent order dependence of exactly the class invisible below a full parallel run. The fix is one `importlib.import_module` per module plus a corrected comment - the same substitution that cycle's builder was forced into for its own rows, which is how the weakness was found.
- `tests/types/test_definition_order.py::test_annotation_only_relation_override_keeps_generated_resolver` does NOT pin the collection-phase consumer-authored short-circuit - never cite it as though it does. Measured twice in the spec-010 residual cycle, by the builder's and the reviewer's failability runs independently: with the relation branch of the short-circuit in `types/base.py::_build_annotations` deleted, every assertion in that row still passes, because the synthesized placeholder resolves back to the same class and the row's `consumer_*` set assertions read state computed in `__init_subclass__` rather than in `_build_annotations`. The short-circuit is pinned instead by the four override-shape rows that cycle landed in the same file. If a discriminating assertion is ever wanted, it must observe `_build_annotations`' own effect (pending-relation suppression), not the resolved schema, which is identical either way.
- `examples/fakeshop/test_query/test_multi_db.py::test_planned_prefetch_child_cascade_subquery_follows_a_routed_parent_onto_its_shard` (`FAKESHOP_SHARDED`-gated) pins the alias of a `Prefetch` child built under an active cascade. `django_strawberry_framework/permissions.py::apply_cascade_permissions` seeds every edge base on the root queryset's explicit alias, so under an unrouted root the cascade subqueries follow the outer query onto the parent's shard; `tests/test_permissions.py::test_unrouted_root_composes_unrouted_subqueries` and `tests/test_permissions.py::test_routed_hook_return_under_unrouted_root_fails_closed` pin the alias rule at the package tier.
- `scripts/prove_failability.py` has a row-isolation proof kind: a manifest entry declaring `isolates` (one node id, `scripts/prove_failability.py::ProofEntry`) is graded **row isolated** when that row is the only attributable failure and **ROW ISOLATION NOT MET** otherwise, instead of the boundary-proof `WEAKLY PINNED` arithmetic. `docs/builder/ARTIFACT.md` records the grading.
- `tests/base/test_conf.py::test_setting_reader_helpers_return_wrong_typed_values_verbatim` pins that `conf.py::testing_endpoint_setting` returns a non-`str` setting value verbatim (`TESTING_ENDPOINT: None` reads back as `None`), so the docstring's does-not-validate-or-coerce claim is executable.

#### Definition of done

- [ ] A dedicated adversarial suite under `tests/` exercises the categories above; every hostile input fails LOUDLY with a typed error rather than crashing.
- [ ] Root `tests/` holds only genuinely-unreachable-from-live cases plus the new adversarial ones; any remaining live-reachable duplicates are pruned (per `examples/fakeshop/test_query/README.md`).
- [ ] Coverage stays at 100% without relying on the pruned duplicates.

#### Files likely touched

- new adversarial test modules under `tests/`
- `examples/fakeshop/test_query/README.md` (cross-reference the adversarial-vs-unreachable split)

#### Why it matters

- `fail_under = 100` proves every LINE executes, not that the code is CORRECT under abuse. The failures that matter — deeply nested logic trees, malformed / wrong-`type_name` GlobalIDs, cyclic [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter) graphs, conflicting multi-owner reuse, UNSET/None permutations, oversized `Meta.fields = "__all__"` expansions, unicode / null-byte / oversized values — are exactly the ones a happy-path live query never exercises.

#### Card references

- Related: Root `tests/` historically mixed genuinely-unreachable-from-live cases with some that merely duplicated coverage already earned by the live `test_query/` suites (a first prune of redundant filter unit tests landed alongside `DONE-027-0.0.8`). -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: The final configurable filter/logic key namespace (`TODO-BETA-070-0.1.7`) must ship first so the adversarial suite exercises the released public surface before the stable gate. -> `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)
- Related: Amendment source: the graph substrate ships the shared planning vocabulary this card must consume instead of reimplementing (spec-058 Decision 1 — the amendment lands at the substrate card's creation, not at its Slice 5). -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Dependency: Amendment source: the sibling foundation card ships the structural/bound plan split, the operation plan map, and the row-identity enforcement gate this card consumes. -> `TODO-BETA-068-0.1.6` - Structural optimization templates and nested sidecar batching

<a id="stable_release_api_freeze_cleanup_verification_beta_stable"></a>
### [TODO-STABLE-073-1.0.0 - Stable release (API freeze, cleanup, verification, beta → stable)](KANBAN.html#stable_release_api_freeze_cleanup_verification_beta_stable)

- Priority: Critical
- Status: To Do
- Relative size: L
- Labels: `cleanup`, `release`, `stable-api`, `tests`

#### Predicted files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`tests/base/test_init.py`](tests/base/test_init.py)

#### Planning note

planned; this is the final card in the Beta queue and gates the beta → stable milestone

#### Dependencies

- `TODO-BETA-072-0.1.8` - Adversarial non-live test suite

#### Definition of done

- [ ] Every other Beta card (`TODO-BETA-058-0.1.1` through `TODO-BETA-072-0.1.8`) is in `DONE`.
- [ ] API surface audit: top-level `__all__` confirmed stable; every public symbol documented; no `# experimental` markers in shipped code; no `_private` symbols accidentally referenced from docs.
- [ ] SemVer policy committed in CHANGELOG header: every release after `1.0.0` follows MAJOR / MINOR / PATCH rules strictly; pre-`0.1.0` deprecation shims removed entirely.
- [ ] Full async + sync coverage matrix validated; no `sync_to_async` workarounds remain on any resolver path.
- [ ] Security review: input-validation surfaces (mutations, filters, GlobalID decoding) audited for injection / authorization gaps.
- [ ] Version bumped to `1.0.0` in `django_strawberry_framework/__init__.py` `__version__` (hatchling derives the packaging version from it), with `tests/base/test_init.py::test_version` and the `docs/GLOSSARY.md` package-version line in step.
- [ ] `CHANGELOG.md`'s open-line `## [1.0.0] - Unreleased` heading dated `## [1.0.0] - YYYY-MM-DD`. Release summary mentions the parity story (graphene-django + strawberry-graphql-django), the django-graphene-filters depth, and the SemVer policy switch.
- [ ] Final pass through `BACKLOG.md` to mark differentiators that landed and refresh the post-1.0 roadmap.
- [ ] Tag, publish to PyPI, write the 1.0 announcement.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`
- `BACKLOG.md`

#### Why it matters

- `1.0.0` is the API freeze. After this card lands, every public symbol — [`DjangoType`](docs/GLOSSARY.md#djangotype), [`DjangoOptimizerExtension`](docs/GLOSSARY.md#djangooptimizerextension), [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint), [`finalize_django_types`](docs/GLOSSARY.md#finalize_django_types), [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield), [`DjangoListField`](docs/GLOSSARY.md#djangolistfield), mutation classes, filter / order / aggregate / fieldset surfaces, and the Meta key vocabulary — is bound by strict SemVer. Breaking changes from this point forward require a major bump.
- The release card is where we audit, finalize, and commit to that contract. Without a dedicated card, "1.0 is stable" becomes a soft promise spread across N patches; making it a single card means the audit happens before the version tag goes out.

#### Card references

- Related: Every other Beta card (`TODO-BETA-058-0.1.1` through `TODO-BETA-072-0.1.8`) is in `DONE`. -> `TODO-BETA-058-0.1.1` - Graph substrate: shared graph policy and dependency planning
- Related: Every other Beta card (`TODO-BETA-058-0.1.1` through `TODO-BETA-072-0.1.8`) is in `DONE`. -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite
- Dependency: The final Beta card discharges before the `1.0.0` cut - the dependency edge replaces prose, mirroring the beta release card's edge on the doc-debt card. -> `TODO-BETA-072-0.1.8` - Adversarial non-live test suite

<a id="dynamic_schemas_from_datatype_specs_synthetic_unmanaged_models"></a>
### [TODO-STABLE-074-1.1.0 - Dynamic schemas from dataType specs (synthetic unmanaged models)](KANBAN.html#dynamic_schemas_from_datatype_specs_synthetic_unmanaged_models)

- Priority: Low-medium
- Status: To Do
- Relative size: L
- Labels: `metadata`, `public-api`, `schema`, `types`

#### Planning note

Created 2026-08-29 from the DIV-033 discussion. Post-1.0 greenfield: neither graphene-django nor strawberry-graphql-django has anything like it. Depends on the pluggable field-conversion registry; the chosen shape (compile specs into synthetic unmanaged Django models) was picked over a model-free converter path because it rides the entire existing pipeline instead of forking one.

#### Dependencies

- `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry

#### Scope

- A dataType-spec compiler: a declarative description of fields and relations (the 'set of dataTypes') is compiled at setup time into synthetic unmanaged Django model classes (type(name, (models.Model,), attrs) with Meta.managed = False and db_table pointed at an existing or external table), which then feed the unchanged [DjangoType](docs/GLOSSARY.md#djangotype) pipeline - converters, choice enums, FilterSets, ordering, optimizer, visibility, connections - so a dynamic schema gets every framework guarantee a hand-written model gets.
- Spec field entries resolve through the pluggable field-conversion registry, so consumer-registered and callable converters work identically for synthetic and hand-written models.
- Compiler discipline: a keyed cache so repeated compilation of the same spec returns the same model class (dynamic model creation registers in Django's app registry; per-request re-creation leaks), a stable dedicated app_label for synthetic models, and a defined error surface ([ConfigurationError](docs/GLOSSARY.md#configurationerror)) for invalid specs.
- Non-goal: schema mutation at request time. Specs are read at setup/import time; a changed spec is a process restart, exactly like an edited models.py.

#### Definition of done

- [ ] Compiler + keyed cache + stable app_label shipped with ConfigurationError coverage for invalid specs.
- [ ] A worked example against an external/unmanaged table (fakeshop or a docs recipe) proving filters, ordering, and the optimizer run unmodified over a synthetic model.
- [ ] Documentation of the setup-time-only contract and the spec format.

#### Why it matters

- The framework already reverse-engineers a GraphQL schema from model inputs; this closes the loop for sources that have a table shape but no models.py - external/legacy databases, inspectdb-style integration, multi-tenant column catalogs - without forking a second conversion path.

#### Dependencies

- Spec field entries resolve through the registry; the registry's callable-converter shape must be settled first.

#### Open question

- Ownership story: where dataType specs live (Python dicts, a settings entry, a file format), who validates them, and what the migration posture is when a spec changes shape against a live table.
- Relation entries between two synthetic models vs a synthetic model and a real one - the FK target resolution order needs a rule before the compiler exists.

#### Card references

- Dependency: Spec field entries resolve through the registry; the registry's callable-converter shape must be settled first. -> `TODO-ALPHA-054-0.0.16` - Pluggable field-conversion registry
- Related: Same DIV-033 discussion; a geo-bearing external table would exercise both cards. -> `BACKLOG-STABLE-076-1.1.0` - GIS / GeoDjango field-type support (geo scalars)

<a id="generated_input_field_names_follow_the_schema_naming_config_auto_camel_case_nameconverter"></a>
### [TODO-BETA-077-0.1.7 - Generated input field names follow the schema naming config (`auto_camel_case`, `NameConverter`)](KANBAN.html#generated_input_field_names_follow_the_schema_naming_config_auto_camel_case_nameconverter)

- Priority: Medium
- Status: To Do
- Relative size: L
- Labels: `config`, `filters`, `mutations`, `ordering`, `public-api`

#### Predicted files

- [`django_strawberry_framework/extensions/resource_policy.py`](django_strawberry_framework/extensions/resource_policy.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/forms/inputs.py`](django_strawberry_framework/forms/inputs.py)
- [`django_strawberry_framework/mutations/inputs.py`](django_strawberry_framework/mutations/inputs.py)
- [`django_strawberry_framework/orders/inputs.py`](django_strawberry_framework/orders/inputs.py)
- [`django_strawberry_framework/rest_framework/inputs.py`](django_strawberry_framework/rest_framework/inputs.py)
- [`django_strawberry_framework/rest_framework/serializer_converter.py`](django_strawberry_framework/rest_framework/serializer_converter.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)
- [`django_strawberry_framework/utils/inputs.py`](django_strawberry_framework/utils/inputs.py)
- [`django_strawberry_framework/utils/write_values.py`](django_strawberry_framework/utils/write_values.py)

#### Planning note

Under `StrawberryConfig(auto_camel_case=False)` or a custom `NameConverter`, output fields and list arguments follow the config (`order_by`, `page_info`) while every package-generated filter, order and mutation input field stays pinned camelCase (`createdDate`, `iContains`, `categoryId`), so one schema mixes both. Upstream strawberry-graphql-django leaves input fields unpinned (`fields/filter_types.py::BaseFilterLookup`, `ordering.py::OrderSequence.get_graphql_name`) and follows the config. Surfaced by the 0.0.15 REVIEW run (utils/strings.py, Mechanics); a probe under `auto_camel_case=False` over the products app printed the mixed SDL.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-028-0.0.8` - Ordering subsystem
- `DONE-050-0.0.15` - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`

#### Scope

- Stop pinning `name=` on package-generated input fields except where a Python keyword forces it (`in_`, `and_`, `or_`, `not_`); mark them so the schema's converter can name them.
- `django_strawberry_framework/scalars.py::strawberry_config` (and [`DjangoSchema`](docs/GLOSSARY.md#djangoschema)) install a converter wrapping the consumer's: for marked fields `django_strawberry_framework/utils/strings.py::graphql_camel_name` under the default config (keeps `field_2` and `field2` distinct), the consumer's `apply_naming_config` otherwise.
- `django_strawberry_framework/filters/inputs.py::LOOKUP_NAME_MAP` entries follow the config (`i_contains`, `is_null` under snake case).
- Runtime readers of the pinned name read the name the built schema published instead, the way `django_strawberry_framework/utils/typing.py::published_argument` does: `django_strawberry_framework/extensions/resource_policy.py::_nested_specs_map` (the resource budget; a wrong name silently skips the limit), the mutation, form and serializer resolvers, and `utils/write_values.py`.
- Decide a plain `strawberry.Schema` built without `strawberry_config`: document it or refuse it.

#### Definition of done

- [ ] Under `auto_camel_case=False` every package-generated input field, lookup and logic key is snake_case in SDL and filters, orders and mutates correctly end to end; under the default config the SDL is byte-for-byte unchanged.
- [ ] A custom `NameConverter` names generated input fields the way it names output fields.
- [ ] The resource budget and write-error field names match the published wire names under both configs (package tests building schemas with each config).
- [ ] `docs/README.md` and the filter, order and mutation glossary rows state that generated input names follow the schema naming config.

#### Why it matters

- `auto_camel_case=False` is a supported, documented knob (`docs/GLOSSARY.md` shows `strawberry_config(auto_camel_case=False, ...)`; list arguments already follow it), yet a client of such a schema must write `order_by: [{createdDate: ASC}]`: two naming conventions in one operation.

#### Dependencies

- Filtering subsystem: `LOOKUP_NAME_MAP` and the logic keys this card unpins.
- [Ordering](docs/GLOSSARY.md#ordering) subsystem: the order input fields this card unpins.
- [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) argument surface: list arguments already follow the naming config; this card brings the inputs in line.

#### Open question

- Input classes are process-global and built before any schema exists (`finalize_django_types()`, mutation binding), so one class can serve schemas with different configs; the wrapper must name per schema, not per class.

#### Card references

- Dependency: Filtering subsystem: `LOOKUP_NAME_MAP` and the logic keys this card unpins. -> `DONE-027-0.0.8` - Filtering subsystem
- Dependency: Ordering subsystem: the order input fields this card unpins. -> `DONE-028-0.0.8` - Ordering subsystem
- Dependency: `DjangoListField` argument surface: list arguments already follow the naming config; this card brings the inputs in line. -> `DONE-050-0.0.15` - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`
- Related: Configurable filter/logic key namespace also moves import-time wire names to schema-build time; land the two resolution points together. -> `TODO-BETA-070-0.1.7` - Configurable filter/logic key namespace (`FILTER_KEY`/`AND_KEY`/`OR_KEY`/`NOT_KEY`)

## Done

Shipped cards, newest first. Each retains its spec link, parity claims, and completion evidence.

<a id="djangolistfield_argument_surface_offset_limit_and_orderby"></a>
### [DONE-050-0.0.15 - `DjangoListField` argument surface: `offset` / `limit` and `orderBy`](KANBAN.html#djangolistfield_argument_surface_offset_limit_and_orderby)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `list-field`, `ordering`, `public-api`
- Spec: [spec-050-list_field_arguments-0_0_15.md](docs/SPECS/spec-050-list_field_arguments-0_0_15.md)

#### Planning note

Promoted from the 0.1.0 parity register's largest unaccounted finding (offset/limit pagination - both upstreams ship a client-facing offset surface) together with spec-028's orphaned orderBy deferral, taken as one card because both open the same list-field argument-factory seam and would otherwise open it twice. Maintainer decision 2026-08-29: build the minimal shape - bounded offset/limit on [`DjangoListField`](docs/GLOSSARY.md#djangolistfield) only, never on connections.

#### Scope

- Bounded `offset` / `limit` arguments on `DjangoListField` only. Connections are a permanent non-goal the spec must pin: grafting offset onto a connection reintroduces the skip-based instability keyset cursors exist to remove, and ⚛'s own `offset: Int`-on-every-connection is the shape being refused.
- Caps and hygiene: the effective row count is the minimum of the client `limit`, the field's `max_rows`, and the request `ResourcePolicy.max_list_rows` (the shipped bound; `trusted_max_rows` semantics unchanged); `offset` is bounded by a policy ceiling rather than unbounded skip; negative, non-integer, or over-ceiling values raise a typed `GraphQLError`, never a silent clamp in the error direction. With neither argument supplied, behavior and SQL are byte-for-byte today's.
- `orderBy` argument on `DjangoListField` through the shipped [OrderSet](docs/GLOSSARY.md#orderset) argument machinery (the target type's `orderset_class`, the same binding connections use) - this is spec-028's deferred orderBy-argument integration, orphaned since `0.0.9` and adjudicated onto this card by the doc-debt card's archived-spec deferral sweep. `django_strawberry_framework/list_field.py`'s ordering-contract docstring already promises order "unless the query supplies an `orderBy` argument" - an argument the field could not accept until this card, so the docstring becomes true rather than aspirational.
- Determinism interplay, a spec decision: an `offset` page without an active order (argument or `Meta.ordering`) is database-dependent and unstable across requests. Preferred answer: require an active order whenever `offset` is non-zero (typed error otherwise); the alternative - documenting the instability - must say why upstream's silent instability was kept.
- SDL consequence stated up front: nullable optional `offset` and `limit` surface on every `DjangoListField`, while `orderBy` surfaces conditionally only when the target type declares `Meta.orderset_class`. A published `offset` is a runtime-precondition coordinate rather than a per-field pagination claim.
- Migration mapping: ⚛'s connection `offset` and 🍓's `pagination=True` / `OffsetPaginationInput` / `OffsetPaginated[T]` / `offset_paginated()` all map onto this surface; the migration-guides card owes the note, including that nested/windowed offset pagination stays served by nested connections here.

#### Definition of done

- [x] A spec is written for the card covering the argument shapes, the caps table, the typed-error contract, the offset-requires-order decision, and the connections non-goal.
- [x] `offset` / `limit` / `orderBy` ship on `DjangoListField`; with none supplied, generated SDL for existing consumers is unchanged apart from the new optional `offset` / `limit` arguments, plus `orderBy` where the target declares [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class), and the emitted SQL is unchanged byte-for-byte.
- [x] SQL-shape tests pin that argument omission preserves the existing policy LIMIT unchanged, a smaller client limit lowers the high mark, a positive offset raises the low mark, and no code path injects DISTINCT.
- [x] `orderBy` composes with type visibility (`get_queryset` narrows first) and reuses the OrderSet pipeline end-to-end; the pk tiebreaker question is answered in the spec (lists have no cursors, so the connection tiebreaker is not blindly inherited).
- [x] Typed `GraphQLError` on negative / non-integer / over-ceiling `offset` or `limit`, live-tested on both values.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercises offset paging with an order, the cap interplay, and an orderBy'd list.
- [x] `django_strawberry_framework/list_field.py`'s ordering-contract docstring is updated to describe the shipped argument.
- [x] The migration-guides card gains the offset-mapping note (its upstream-settings/surface table).
- [x] Full suite green under `fail_under = 100`; live-first placement respected. No version triplet or CHANGELOG entry - the `0.0.15` release state is owned by the DRY-squeeze card's joint cut, which lands last on the line.

#### Files likely touched

- `django_strawberry_framework/list_field.py` (argument factory, caps, docstring)
- `django_strawberry_framework/orders/` argument machinery reused at the list-field seam
- `django_strawberry_framework/conf.py` only if the offset ceiling needs its own key (prefer deriving from `max_list_rows`)
- Mirrored `tests/` modules plus live coverage under `examples/fakeshop/test_query/`

#### Card references

- Related: Shares the `0.0.15` line; both are pre-beta parity work, this card lands first. -> `WIP-ALPHA-051-0.0.15` - Upstream parity-gap closure
- Related: Its archived-spec deferral sweep names spec-028's orphaned orderBy integration; adjudicated: carded here. -> `TODO-ALPHA-056-0.0.17` - Alpha documentation-debt discharge
- Related: Owes the offset-mapping migration note: upstream offset surfaces map to this card's `DjangoListField` arguments; nested offset pagination maps to nested connections. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides
- Related: The parity claim's offset/limit cut blocker is closed by this card. -> `TODO-ALPHA-057-0.1.0` - Beta release (cleanup, verification, alpha → beta)

<a id="dependency_and_ci_hardening_refresh_django_locks_add_audit_automation_least_privilege_ci"></a>
### [DONE-049-0.0.14 - Dependency and CI hardening: refresh Django locks, add audit automation, least-privilege CI](KANBAN.html#dependency_and_ci_hardening_refresh_django_locks_add_audit_automation_least_privilege_ci)

- Priority: High
- Status: Done
- Relative size: M
- Labels: `internal`
- Spec: [spec-049-dependency_ci_hardening-0_0_14.md](docs/SPECS/spec-049-dependency_ci_hardening-0_0_14.md)

#### Planning note

Security-audit remediation program, card 4 of 4. S6 is independently time-sensitive and may be expedited at maintainer discretion.

#### Dependencies

- `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

#### Scope

- uv.lock refresh (>=5.2.16 / >=6.0.7); keep + relabel the 5.2.0 compatibility cell.
- Dependency-audit + scheduled-security + auto-update workflows (pip-audit/dependabot shape).
- .github/workflows: least-privilege permissions, persist-credentials, SHA/digest pins, timeouts.
- Slice 5 doc fold-in landed DB-side at the release: the `Hard dependency` glossary entry now carries the secure-version statement - a declared floor is an API-compatibility bound frozen at release time, never advice about which version is safe to run - written into the fakeshop glossary DB and re-rendered with `scripts/build_glossary_md.py` rather than hand-edited into the generated file.
- The card shipped with no `SpecDoc` row, so `KANBAN.md` rendered it without a spec link. The row was seeded at the release, and the spec has since been archived, so the link resolves to `docs/SPECS/spec-049-dependency_ci_hardening-0_0_14.md` with its terms companion under `docs/SPECS/appx/`.
- `README.md`, `docs/README.md` and `TODAY.md` prose are hand-edited and were left for this card's DB-regeneration pass rather than done piecemeal.

#### Definition of done

- [x] Locks refreshed to the patched Django releases; audit + auto-update automation added; CI runs least-privilege with immutable action/image pins and job timeouts.
- [x] Governance files only (no package-source/SDL change, no coverage exposure); CI green.

#### Architectural posture

- Refresh uv.lock to at least Django 5.2.16 and 6.0.7 for their respective Python markers. KEEP the exact Django 5.2.0 compatibility CI cell but label it compatibility-only and never use it for deployment examples or security assertions -- compatibility support and secure-deployment support are different contracts.
- Add an automated dependency audit on pull requests and a scheduled run (audit the production resolution + optional extras; handle the intentional 5.2.0 compatibility environment separately); add automated update coverage for Python dependencies and GitHub Actions. State that production users must install the newest patch in their supported Django series; the Django>=5.2 floor is not a secure-version recommendation.
- CI least privilege: top-level permissions: contents: read, with only the exact additional grant to the one step/job that needs it; persist-credentials: false on every non-pushing checkout; pin every action to a reviewed full commit SHA (keep the readable version comment); pin the Postgres image by digest; add timeout-minutes to every networked/test job.

#### Why it matters

- S6 (High): uv.lock resolves Django 5.2.14 (py<3.12) and 6.0.5 (py>=3.12), but the Django project shipped security releases 5.2.16 and 6.0.7 (CVE-2026-48588, a shared-cache private-data exposure) plus 5.2.15/6.0.6 fixing five more issues in the currently locked versions. No dependency-audit command, scheduled security workflow, or update configuration exists.
- S7 (Medium): the test job grants contents: write though only the Coveralls upload consumes the token (which does not need repo-write); checkout persists its credential by default; first-party actions use mutable major tags and Postgres uses postgres:16; networked/test jobs have no timeout-minutes.

#### Dependencies

- Sequenced behind card 046 in the staged security program; S6 independently urgent.

#### Test plan

- The dependency audit runs on the production resolution + extras and handles the 5.2.0 environment separately; the refreshed lock still resolves the whole matrix.
- CI permission and pin assertions where mechanically testable; the exact 5.2.0 compatibility cell still proves API compatibility with the advertised floor.

#### Open question

- pip-audit vs safety vs osv for the audit step, and dependabot vs a scheduled uv upgrade job: the spec picks concrete tooling.
- Repository-level default token permissions (spec-049 Decision 3) is a GitHub settings change, not a file in the tree - maintainer action, and nothing in a build can verify it.
- `osv-scanner`'s inner image tag stays mutable (spec-049 Decision 4); pinning it would need a fork. Recorded in the spec's risks rather than fixed.
- The workflow `timeout-minutes` values are estimates, not measured p95s (spec-049 Decision 7).
- `CHANGELOG.md`'s `0.0.14` entry predates this program: it is dated 2026-07-20 and covers cards `DONE-041` through `DONE-044`, so none of the four security cards that target the same patch version appear in it. `AGENTS.md` reserves `CHANGELOG.md` to the maintainer, so closing that gap is maintainer action rather than a card task.

#### Card references

- Dependency: Sequenced behind card 046 in the staged security program; S6 independently urgent. -> `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

<a id="secure_output_and_error_defaults_drop_file_path_fail_closed_debug_prod_error_policy"></a>
### [DONE-048-0.0.14 - Secure output and error defaults: drop file path, fail-closed debug, prod error policy](KANBAN.html#secure_output_and_error_defaults_drop_file_path_fail_closed_debug_prod_error_policy)

- Priority: High
- Status: Done
- Relative size: M
- Labels: `internal`
- Spec: [spec-048-secure_output_defaults-0_0_14.md](docs/SPECS/spec-048-secure_output_defaults-0_0_14.md)

#### Planning note

Security-audit remediation program, card 3 of 4.

#### Dependencies

- `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

#### Scope

- converters.py: remove DjangoFileType.path from the default field set (name/size/url remain; opt-in path).
- extensions/debug.py: settings.DEBUG fail-closed gate + allow_unsafe_production ack + payload caps.
- schema.py: [DjangoSchema](docs/GLOSSARY.md#djangoschema) production error policy (log + correlation id + stable message under DEBUG=False).

#### Definition of done

- [x] path removed from the safe default; debug extension fails closed under DEBUG=False with an explicit ack; DjangoSchema has a production error policy.
- [x] Full suite green at 100% coverage; hygiene clean; migration note + docs fold-in.

#### Architectural posture

- Remove path from the public generated type's safe default (default output limited to name/size/url). A filesystem path requires an explicit server-owned field or a loud Meta opt-in; do not mask path failures while still exposing successful absolute paths. Justified pre-1.0 compatibility break + migration note.
- [DjangoDebugExtension](docs/GLOSSARY.md#djangodebugextension) fails closed when settings.DEBUG is false unless an explicit constructor acknowledgement (DjangoDebugExtension(allow_unsafe_production=True)); add the __init__ it currently lacks and preserve fresh-per-operation instances. Cap the number and serialized byte size of SQL and exception rows.
- DjangoSchema gets a first-class production error policy: under DEBUG=False, unexpected exceptions log server-side with a correlation identifier and return a stable, non-sensitive message; deliberate client-facing framework errors (validation envelopes, audited GraphQLError codes) retain their contract; consumer code may explicitly opt out.

#### Why it matters

- S5 (High): DjangoFileType.path returns FieldFile.path and its description says 'the absolute filesystem path'; [DjangoImageType](docs/GLOSSARY.md#djangoimagetype) inherits it. Every generated file/image output offers clients a server-internal path (usernames, release dirs, container mounts, tenant layout) whenever the storage backend supports one.
- S8 (Medium): DjangoDebugExtension returns interpolated SQL values, exception messages/types, and traceback paths, and operates independently of settings.DEBUG -- a single production schema-list entry silently activates the disclosure. It has no __init__ today.
- S10 (Medium): DjangoSchema centralizes mutation integrity but offers no production error policy; unhandled resolver/hook exceptions return their literal message to clients unless the consumer adds MaskErrors or overrides process_errors.

#### Dependencies

- Sequenced behind card 046 in the staged security program (independent code).

#### Test plan

- Default SDL lacks path; remote-storage failures still degrade safely for retained fields; any explicit path opt-in is absent unless deliberately declared.
- DEBUG=False rejects the debug extension by default; the explicit acknowledgement works; fresh-instance isolation intact; payload limits truncate deterministically; the aggregate fakeshop schema stays debug-free.
- Error policy distinguishes parse/validation errors, audited client-safe GraphQL errors, permission denials, and unexpected resolver/hook exceptions; sync/async parity; the correlation id (not the sensitive original message) reaches the client.

#### Open question

- The opt-in shape for an explicit filesystem-path field (Meta key vs server-only field): the spec decides.
- Correlation-id format + where it is logged, and whether the stable client message is configurable: the spec pins it.

#### Card references

- Dependency: Sequenced behind card 046 in the staged security program (independent code). -> `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

<a id="execution_resource_policy_central_budget_object_value_cardinality_walker"></a>
### [DONE-047-0.0.14 - Execution resource policy: central budget object + value-cardinality walker](KANBAN.html#execution_resource_policy_central_budget_object_value_cardinality_walker)

- Priority: High
- Status: Done
- Relative size: L
- Labels: `internal`
- Spec: [spec-047-resource_policy-0_0_14.md](docs/SPECS/spec-047-resource_policy-0_0_14.md)

#### Planning note

Security-audit remediation program, card 2 of 4.

#### Dependencies

- `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

#### Scope

- New immutable resource-policy object + schema-construction normalization + context threading.
- [Value-budget walker](docs/GLOSSARY.md#value-budget-walker) over coerced inputs (iterative, cycle-safe, py3.10).
- types/base.py DEFAULT_RELATION_SHAPE 'both' -> 'connection'; [DjangoListField](docs/GLOSSARY.md#djangolistfield) bound.

#### Definition of done

- [x] Immutable resource policy consumed by schema/fields/optimizer/transports; per-field narrowing only.
- [x] Value-budget walker rejects before ORM access; DEFAULT_RELATION_SHAPE default is 'connection'; raw lists bounded.
- [x] Full suite green at 100% coverage; hygiene clean; docs fold-in.

#### Architectural posture

- One immutable resource-policy object consumed by [DjangoSchema](docs/GLOSSARY.md#djangoschema), collection fields, the optimizer, and the transports: max document tokens, max selection/alias count after fragment expansion, max depth, max page size, max raw-list rows, max aggregate collection cost, optional execution deadline. Normalize and validate once at schema construction; thread the immutable result through request context (mirror the optimizer's DST_OPTIMIZER_* context seam). Per-field overrides may only narrow unless an explicit trusted-schema declaration widens.
- Extend the policy with one iterative, cycle-safe value-budget walker charging total input nodes, container width, membership-list items, node-refetch ids, relation ids per mutation and in aggregate, nested serializer rows, upload count / per-file bytes / aggregate bytes, and scalar byte size where a parser/validator is nonlinear. Stop before decoding ids or touching the ORM once the budget is exhausted.
- Change the secure default for many-side relations from 'both' to 'connection'. A raw list requires explicit opt-in and an enforced maximum; DjangoListField gets a required/effective bound (documenting it as dangerous is not enough).

#### Why it matters

- S3 (High): neither the package nor the example installs a token / query-depth / complexity / selection-count limiter, and there is no page-size / raw-list-row / aggregate-row budget. DjangoListField evaluates an unbounded queryset, and DEFAULT_RELATION_SHAPE='both' exposes a raw many-side list alongside the bounded connection, so a client bypasses the connection cap via the list sibling.
- S4 (High): document limits do not constrain variable-supplied values. A tiny query can carry an unlimited ids list ([DjangoNodesField](docs/GLOSSARY.md#djangonodesfield) preserves duplicates positionally), unlimited in-lookup values, an and/or filter tree of unbounded width/node count, unlimited M2M ids, wide nested serializer lists, and uploads with no aggregate byte / file-count / per-file cap.

#### Dependencies

- Depends on card 046: the resource policy is consumed by the transports fixed there, and the program is staged transport-first.

#### Test plan

- Token / expanded-selection / alias / depth / aggregate-cost boundaries; fragments and directives cannot evade accounting; the same field under many aliases is charged many times.
- A connection's relay_max_results cannot be bypassed through a generated list sibling; raw root and relation lists stop at the configured maximum.
- Each input family under/at/over boundary, including a tiny query with a large variable payload; duplicate ids; empty lists; multiple bounded fields whose aggregate exceeds the request budget; proof of zero ORM work after rejection; sync/async parity with one typed error code.

#### Open question

- Default budget values (token/selection/depth/page/rows/cost) and which are settings-overridable vs schema-construction-only: the spec pins concrete numbers.
- Whether 'both'->'connection' needs a one-release deprecation shim or is a clean alpha break like card 046: the spec decides.

#### Card references

- Dependency: Depends on card 046: the resource policy is consumed by the transports fixed there, and the program is staged transport-first. -> `DONE-046-0.0.14` - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation

<a id="transport_security_django_owned_http_bounded_body_utf_8_wire_ws_revalidation"></a>
### [DONE-046-0.0.14 - Transport security: Django-owned HTTP, bounded body, UTF-8 wire, WS revalidation](KANBAN.html#transport_security_django_owned_http_bounded_body_utf_8_wire_ws_revalidation)

- Priority: Critical
- Status: Done
- Relative size: L
- Labels: `internal`
- Spec: [spec-046-transport_security-0_0_14.md](docs/SPECS/spec-046-transport_security-0_0_14.md)

#### Planning note

Security-audit remediation program, card 1 of 4. Amends spec-041 (channels_router). Explicit 0.0.14 alpha breaking change.

#### Scope

- S1: redesign the router protocol split (required Django-ASGI HTTP ownership; remove direct Channels HTTP; exact WebSocket routing via websocket_url_pattern).
- S2: package-owned cumulative request-body cap on the GraphQL HTTP path + documented proxy/server cap.
- S9: strict UTF-8 wire decode before json.loads; translate UnicodeDecodeError to the controlled 400; invert UTF-16/32/BOM success tests to 400; decide and document the UTF-8-BOM policy; reconcile _cross_web_patches._patched_body against the new HTTP path.
- S11: WebSocket consumer-class/factory injection seam + actor revalidation at TWO checkpoints (operation admission and every information-bearing outbound operation frame), so a revoked actor can neither admit another operation nor emit another next/data/error frame; revocation is connection-scoped and closes the whole socket (4403 Forbidden); optional explicit bounded revalidation window.
- S12 (transport slice only): migration note (old vs new asgi.py + the required urlpatterns entry) + transport deployment guidance (CSRF, cache/Vary, security headers, IDE/GET controls). The broader S12 deployment-contract docs belong to the later cards' doc slices.

#### Definition of done

- [x] Router HTTP branch no longer instantiates GraphQLHTTPConsumer; django_application is required and omitting it fails at construction; websocket_url_pattern exact-matches; WebSocket Origin/auth wrappers + consumer injection seam in place.
- [x] Cumulative request-body cap enforced pre-parse on GraphQL HTTP + documented proxy/server cap.
- [x] Wire JSON is UTF-8-only; UTF-16/32 success tests inverted to 400.
- [x] WebSocket actor revalidation at both the admission and the outbound-frame checkpoint, with connection-scoped revocation, via the injection seam.
- [x] Migration note + transport deployment docs authored; spec-041 amended.
- [x] Full suite green at 100% coverage (maintainer/CI gate); ruff + trailing-comma clean; manage.py check + makemigrations --check clean.

#### Architectural posture

- RECOMMENDED DIRECTION (maintainer-pinned; the spec turns each bullet into a numbered Decision with alternatives-rejected rationale). Clean protocol split as an explicit alpha breaking change: the 0.0.14 byte-compatible upstream constructor contract is intentionally broken. The documented API freeze begins at 1.0.0, so correcting a confirmed security-boundary error during alpha is preferable to preserving an unsafe migration convenience.
- HTTP dispatches directly to a REQUIRED consumer-supplied Django ASGI application. The router must NOT instantiate or route to GraphQLHTTPConsumer. The GraphQL HTTP endpoint is declared in the consumer's Django URLconf using the normal Strawberry Django view, so it inherits the full MIDDLEWARE stack.
- Require django_application rather than deriving it internally; the consumer calls get_asgi_application() at the normal point in asgi.py (avoids Django init-order ambiguity). Omitting django_application must fail clearly at construction -- do not retain an unsafe compatibility fallback.
- WebSocket remains the package-owned Channels composition: exact GraphQL route -> DjangoWebSocketHostValidator (Host) -> AllowedHostsOriginValidator (Origin) -> AuthMiddlewareStack -> the GraphQL WebSocket consumer, with the Host validator outermost so Host and Origin are two separate checks in that order. Rename/narrow url_pattern to a WebSocket-only websocket_url_pattern with exact matching as the secure default; Django URLconf independently owns HTTP path matching.
- Add a WebSocket consumer-class/factory injection seam for S11 without implementing a second GraphQL protocol engine; the injected class must still sit inside the package's Host/Origin and authentication wrappers. Per-operation session revalidation is a WebSocket concern layered through that seam and must not delay or complicate the S1 HTTP correction.
- S1 does not dispose of S2: still define and test an explicit cumulative request-body limit (count received bytes, do not trust Content-Length; reject at the limit before JSON parse / schema execution) and document the reverse-proxy / ASGI-server limit. Routing through Django restores the authoritative middleware lifecycle but must not be represented as automatically providing every transport resource bound.

#### Why it matters

- S1 (Blocker): routers.py wires the HTTP branch as AuthMiddlewareStack(URLRouter([re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(...))])). That turns the session cookie into an authenticated actor but bypasses Django's MIDDLEWARE entirely -- SecurityMiddleware, CsrfViewMiddleware, CommonMiddleware / ALLOWED_HOSTS, and all consumer tenant/rate-limit/audit/cache/security-header middleware. Confirmed by source and a probe (POST Host: evil.example -> 200).
- S1 route overmatch: url_pattern default '^graphql' is a prefix regex, so /graphql-admin and /graphqlanything are claimed by the GraphQL consumer before the Django fallback -- a path the deployment believes Django owns.
- S2 (Blocker): the routed AsyncHttpConsumer buffers the whole body via b''.join(self.body) with no application cap; DATA_UPLOAD_MAX_MEMORY_SIZE is never consulted because Django's ASGI handler is bypassed. Unauthenticated memory amplification before JSON parsing or schema execution.
- S9 (Medium): _cross_web_patches._patched_body returns raw bytes so json.loads auto-detects UTF-16/32; RFC 8259 requires UTF-8 on the wire. Accepting other encodings creates a proxy/WAF/access-log parser differential.
- S11 (Medium): the WebSocket scope user is captured at handshake and never revalidated; a logout/password-reset/disable/revocation from another request or admin action is not reflected on the established connection.
- S1 and S2 block moving off the current 'not production' alpha posture; a framework's secure architecture cannot depend on every consumer independently discovering these gaps.

#### Test plan

- Django middleware / configured security headers execute on the GraphQL HTTP route; a project middleware sentinel runs; a hostile Host is rejected on HTTP (not only WebSocket).
- Cookie-authenticated mutations cover missing, wrong, and correct CSRF tokens (Client(enforce_csrf_checks=True)).
- An authenticated GET response is non-cacheable or varies on Cookie.
- /graphql and /graphql/ match per an explicit policy while /graphql-admin and /graphqlanything reach Django or 404.
- Body cap: no Content-Length; declared below/at/above; declared-small-but-streamed-over; multi-fragment crossing; JSON / malformed JSON / multipart; an early 413 proving neither JSON parse nor schema execution ran; parity across the py3.10 / Django 5.2.0 floor and the current stack.
- S9: UTF-16/32 (BOM and BOM-less) -> 400; ordinary UTF-8 preserved; malformed UTF-8 -> 400; the chosen UTF-8-BOM direction.
- S11: establish a socket, revoke/flush/disable via a separate request, prove the next operation is denied without reconnecting; existing WebSocket Origin/auth direction tests remain intact.

#### Open question

- Where the app-level body cap lives on the new Django-view HTTP path (a package GraphQL-view subclass vs. documented DATA_UPLOAD_MAX_MEMORY_SIZE + a thin wrapper): the spec decides.
- Whether the package ships a thin GraphQL HTTP view wrapper or points consumers directly at strawberry-django's GraphQLView: the spec decides and documents the exact urlpatterns entry.
- UTF-8 BOM: accept-and-strip vs reject (RFC 8259 permits either): the spec picks one and documents it.

<a id="sealed_get_queryset_visibility_boundary_policy_artifacts"></a>
### [DONE-045-0.0.14 - Sealed get_queryset visibility-boundary policy artifacts](KANBAN.html#sealed_get_queryset_visibility_boundary_policy_artifacts)

- Priority: High
- Status: Done
- Relative size: S
- Labels: `docs`, `internal`, `permissions`, `security`
- Spec: [spec-045-visibility_boundary-0_0_14.md](docs/SPECS/spec-045-visibility_boundary-0_0_14.md)

#### Scope

- Documentation-only slice over the already-landed sealed get_queryset visibility boundary (commit 60998b17). Authors the governing numbered security decisions, this card's spec, and the five new glossary terms.
- Depends on the sealed-boundary implementation commit 60998b17 (the code this card documents; already landed).

#### Definition of done

- [x] Numbered security decisions authored covering the changed contract: untrusted-object rebuild, prove-then-clone AST trust, identity-fast-path removal, Prefetch rebuild + alias threading, queryset-shape rejections, and the typed error contract.
- [x] Spec docs/SPECS/spec-045-visibility_boundary-0_0_14.md authored with its companion *-terms.csv.
- [x] GLOSSARY entries imported for the five new terms via the fakeshop glossary DB and docs/GLOSSARY.md regenerated.
- [x] KANBAN.md / KANBAN.html regenerated from the kanban DB with this card in Done.

#### Files likely touched

- `django_strawberry_framework/utils/querysets.py`
- `django_strawberry_framework/permissions.py`
- `django_strawberry_framework/optimizer/walker.py`

#### Why it matters

- The sealed boundary changed the accepted queryset shapes, identity/cache behavior, aliases, errors, and query execution of the framework's single data-leak-critical seam. Repository policy requires a governing numbered security decision, a KANBAN card, a spec, and a GLOSSARY update for exactly such a change; commit 60998b17 landed the correctness work without them, and this card authors them so the standing documentation matches the implemented security contract.

#### Decision

- **Threat model: a mistaken hook, not an in-process adversary.** The boundary defends against a `get_queryset` hook that returns wrong query state - a dropped predicate, a foreign or shadowed object, a wrong table, a sliced or projected shape, an injected cache, a re-routed alias, or AST the sealed query would share with the candidate. A consumer who deliberately crafts an object to reach a Django or adapter dispatch site is OUT of scope: they already execute code in the process, so no in-interpreter walk is a trust boundary against them (the same stance the framework takes on process-wide monkeypatching). Canonical reconstruction is the terminating mechanism - the sealed query is a framework-owned rebuild with every bound value normalized to an exact inert copy, not the candidate graph proven safe - so the boundary is CLOSED to further dispatch-path expansion. Decision 8 of `spec-045-visibility_boundary-0_0_14`.

<a id="response_extensions_debug_middleware"></a>
### [DONE-044-0.0.14 - Response-extensions debug middleware](KANBAN.html#response_extensions_debug_middleware)

- Priority: Low
- Parity: ⚛️ graphene-django (Required)
- Status: Done
- Relative size: M
- Labels: `debugging`, `graphql-api`, `middleware`
- Spec: [spec-044-debug_extension-0_0_14.md](docs/SPECS/spec-044-debug_extension-0_0_14.md)

#### Package files

- [`django_strawberry_framework/extensions/debug.py`](django_strawberry_framework/extensions/debug.py)
- [`tests/extensions/`](tests/extensions/)

#### Definition of done

- [x] Implement `django_strawberry_framework/extensions/debug.py` as a Strawberry `SchemaExtension` that captures SQL and exceptions for the in-flight operation and attaches them to the response `extensions` map (key: `debug`).
- [x] Pin the **exposure mechanism** (response-`extensions` map vs. schema-level `_debug` field) and the **fidelity choice** (cursor-wrap port vs. `connection.queries`) in the spec; default both to the simpler choice (response-`extensions` map + `connection.queries`) unless the spec authoring round chooses otherwise.
- [x] Output shape mirrors graphene's `DjangoDebugSQL` / `DjangoDebugException` field names where the chosen fidelity supports them; document any shape narrowing (e.g., omitted Postgres-specific fields) explicitly.
- [x] Off by default; opt-in via the extensions list passed to `strawberry.Schema(...)`.
- [x] Tests under `tests/extensions/test_debug.py` against a fakeshop request that emits SQL.
- [x] Documented as the response-side counterpart to `DONE-042-0.0.14`.

#### Files likely touched

- `django_strawberry_framework/extensions/` (new)
- `tests/extensions/` (new)

#### Architectural posture

- **"Middleware" is overloaded here**: graphene-django's `DjangoDebugMiddleware` is a **Graphene field-resolver middleware** (a callable invoked around each `resolve(root, info, **args)`), not a Django request/response middleware. The card title says "middleware" because that's what the graphene side calls the same idea; our Strawberry-native shape is a `SchemaExtension` (operation-scoped), not a Django middleware. The file name `middleware.py` is preserved on the graphene side for parity with their naming; ours lives under `extensions/`.
- **Exposure mechanism — pick one before writing the spec**:
- graphene-django: **schema-level**. Consumers add a `_debug: DjangoDebug` field to their query and selectively pull `{ _debug { sql { duration } } }`. Pay-for-what-you-select.
- Card's proposed Strawberry-native shape: **response-extensions-level**. Always emit the whole map under `extensions["debug"]` when the extension is enabled, or skip it entirely.
- Both end up "in the GraphQL response," but the graphene shape gives consumers per-query selectivity at the cost of needing a schema field. The Strawberry-extension shape is simpler to wire and skips schema surface entirely.
- **Fidelity tradeoff — pick one before writing the spec**:
- **Port graphene's cursor wrapping** (`sql/tracking.py`): wraps `connection.cursor` per-thread so the wrapper sees `start_time` before `execute()` and computes precise `duration`, captures Postgres-specific `iso_level` / `encoding`, surfaces `is_slow` / `is_select` flags. Higher fidelity; requires thread-local state management and `enable_instrumentation` / `disable_instrumentation` lifecycle hooks tied to the extension's operation begin / end.
- **Use `django.db.connection.queries`**: the SchemaExtension reads `connection.queries` at operation end and emits a smaller shape. Lower fidelity (relies on Django's existing logging — no Postgres-specific data, less precise timing). Trivially threadsafe; no cursor wrapping to manage.
- **Thread-local state** (if porting the cursor wrap): `sql/tracking.py::ThreadLocalState` plus `enable_instrumentation` / `disable_instrumentation` are the lifecycle hooks. The SchemaExtension's `on_operation` (or equivalent) wraps `wrap_cursor` for the request and `unwrap_cursor` on teardown. Exception capture wires through the corresponding execution hooks similarly.

#### Why it matters

- `graphene-django` ships a debug subsystem that exposes the executed SQL queries and raised exceptions for each GraphQL request via a `DjangoDebug` object. This is different from `DONE-042-0.0.14` (django-debug-toolbar SQL panel UI): graphene's mechanism is **inside the GraphQL response**, so frontend clients and Apollo DevTools can read it without the toolbar. Both mechanisms are useful and not mutually exclusive.
- A Strawberry-native equivalent is a small `SchemaExtension` that captures SQL (through `django.db.connection.queries` or via a port of graphene's cursor-wrap mechanism — see Architectural posture) and exceptions and attaches the result to the response's `extensions` map.
- `strawberry-graphql-django` ships **no** equivalent (no file references `connection.queries` and no `*debug*` module exists outside the toolbar middleware tracked by `DONE-042-0.0.14`); this card is graphene-django parity only.
- developer experience.

#### Card references

- Related: Documented as the response-side counterpart to `DONE-042-0.0.14`. -> `DONE-042-0.0.14` - Debug-toolbar middleware

<a id="test_client_helper"></a>
### [DONE-043-0.0.14 - Test client helper](KANBAN.html#test_client_helper)

- Priority: Low
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `graphql-api`, `test-client`, `tests`, `uploads`
- Spec: [spec-043-test_client-0_0_14.md](docs/SPECS/spec-043-test_client-0_0_14.md)

#### Package files

- [`django_strawberry_framework/testing/client.py`](django_strawberry_framework/testing/client.py)

#### Dependencies

- `DONE-037-0.0.11` - Upload scalar and file / image field mapping

#### Scope

- `test/client.py` (sync + async [`TestClient`](docs/GLOSSARY.md#testclient), a `GraphQLTestMixin`, two `(Mixin, TestCase)` combos), endpoint setting, multipart-upload support; several design decisions to pin; switch the fakeshop tests over.

#### Definition of done

- [x] Implement `django_strawberry_framework/testing/client.py` exposing `TestClient` / `AsyncTestClient` (per the inheritance shape pinned above) plus a `GraphQLTestMixin` and two concrete `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations for the unittest crowd.
- [x] Mixin carries `assertResponseNoErrors` / `assertResponseHasErrors` helpers (or the equivalent named for the chosen `.query()` return type).
- [x] Project-wide endpoint settings key (working name `GRAPHQL_TESTING_ENDPOINT`, final name pinned during implementation) under `DJANGO_STRAWBERRY_FRAMEWORK`, with constructor / per-call override.
- [x] Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `DONE-037-0.0.11` ships.
- [x] Live HTTP tests under `examples/fakeshop/test_query/` switch to the helper.
- [x] Tests under `tests/testing/test_client.py`.

#### Architectural posture

- **Mixin-first shape** (graphene-django convention): the reusable piece is `GraphQLTestMixin`; the concrete [`GraphQLTestCase`](docs/GLOSSARY.md#graphqltestcase) / `GraphQLTransactionTestCase` are two-line `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)` combinations so consumers with their own custom TestCase base can compose the mixin in directly. Our equivalent follows the same mixin-first shape rather than only shipping the concrete subclasses.
- **`.query()` return type — decide before writing the spec**: strawberry-django returns a typed `Response` dataclass (`data` / `errors` / `extensions`); graphene-django's `GraphQLTestMixin.query` returns a raw Django `HttpResponse` paired with `assertResponseNoErrors` / `assertResponseHasErrors` helpers that parse the body. The two flavors are not interchangeable — pick one and pin it (the typed-dataclass shape is the more DRF-shaped choice and composes better with future typed-error work).
- **Async**: strawberry-django's `AsyncTestClient` subclasses `TestClient` (not `BaseGraphQLTestClient` directly), takes a `django.test.client.AsyncClient`, and only overrides `.query()` + `.login()`. The sync `request()` is reused via `cast("Awaitable", ...)`. Our equivalent ports the same inheritance shape (or picks a flatter alternative explicitly in the spec).
- **Endpoint resolution**: project-wide default reads from `DJANGO_STRAWBERRY_FRAMEWORK["GRAPHQL_TESTING_ENDPOINT"]` (mirrors graphene's `TESTING_ENDPOINT` knob; final settings-key name pinned during implementation), with a per-instance / per-call override identical to strawberry-django's `path` constructor argument and graphene-django's `graphql_url` per-call argument.
- **File-upload coupling**: strawberry-django's `request()` switches to `format="multipart"` when `files=` is provided. Our helper must do the same so live HTTP tests for `DONE-037-0.0.11` ([Upload scalar](docs/GLOSSARY.md#upload-scalar)) can exercise multipart uploads through the helper rather than dropping back to raw `client.post(...)` calls.
- **Strawberry base-class reuse — decide before writing the spec**: subclass `strawberry.test.BaseGraphQLTestClient` (less code, couples our `.query()` / `.mutate()` shape to upstream Strawberry's choices) vs. roll our own base (more code, full control over the public surface). The strawberry-django decision was to subclass; the package's DRF-first stance argues for considering the from-scratch alternative.

#### Why it matters

- `strawberry-graphql-django` ships `strawberry_django.test.client.TestClient`, a thin wrapper around `django.test.Client` that posts GraphQL requests with the right content type, parses the response, and exposes `.query(...)` / `.mutate(...)`.
- `graphene-django` ships `graphene_django.utils.testing` with `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` / `graphql_query` helpers covering the same need.
- The fakeshop live tests already do this by hand; centralizing the pattern is a small win for consumers and keeps our HTTP tests crisp.
- developer experience.

#### Dependencies

- `DONE-037-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here.

#### Card references

- Dependency: `DONE-037-0.0.11` (Upload scalar) — the file-upload helper path lights up once Upload-scalar inputs exist; the helper itself ships without it but gains a tested path here. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping
- Related: Multipart file-upload support on `request()` so consumers can drive `Upload`-scalar mutations from the same helper once `DONE-037-0.0.11` ships. -> `DONE-037-0.0.11` - Upload scalar and file / image field mapping

<a id="debug_toolbar_middleware"></a>
### [DONE-042-0.0.14 - Debug-toolbar middleware](KANBAN.html#debug_toolbar_middleware)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `debugging`, `django-integration`, `middleware`
- Spec: [spec-042-debug_toolbar-0_0_14.md](docs/SPECS/spec-042-debug_toolbar-0_0_14.md)

#### Package files

- [`django_strawberry_framework/middleware/debug_toolbar.py`](django_strawberry_framework/middleware/debug_toolbar.py)

#### Definition of done

- [x] Implement `django_strawberry_framework/middleware/debug_toolbar.py` exposing a `DebugToolbarMiddleware` that **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` + `_postprocess` for the two injection paths above.
- [x] Ship the matching template asset at `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`; the middleware renders it via `render_to_string(...)` into HTML responses for the GraphiQL view.
- [x] Introspection-query skip behavior preserved (no payload injection when `operationName == "IntrospectionQuery"`).
- [x] `debug_toolbar` is a soft dependency: top-level package import must succeed without `django-debug-toolbar` installed; the middleware module raises `ImportError` with an install hint when actually imported.
- [x] In-process test against a fakeshop request that emits SQL, covering both the GraphiQL HTML path and the JSON operation path.

#### Architectural posture

- **Not a from-scratch middleware**: strawberry-django **subclasses** `debug_toolbar.middleware.DebugToolbarMiddleware` and overrides `process_view` (to tag GraphiQL requests) and `_postprocess` (to inject the toolbar payload into the response). Our equivalent follows the same subclass-and-override shape; we do not re-implement the panel-rendering logic that `django-debug-toolbar` already owns.
- **GraphiQL-view detection**: strawberry-django tags `request._is_graphiql = bool(view and issubclass(view, BaseView))` where `BaseView` is `strawberry.django.views.BaseView`. Our equivalent uses the same `issubclass` check against whichever view class the package settles on (working name [`DjangoGraphQLView`](docs/GLOSSARY.md#djangographqlview); pinned during implementation).
- **Two output paths, not one**:
- **HTML response** (the GraphiQL page itself): the middleware appends a rendered toolbar template to the response body and refreshes `Content-Length`.
- **JSON response** (a `/graphql/` operation result): the middleware parses the body, injects a `debugToolbar` key carrying per-panel `title` / `subtitle` metadata plus the toolbar's `requestId`, and re-encodes via `DjangoJSONEncoder`.
- **Introspection-query skip**: payload injection is suppressed when `operationName == "IntrospectionQuery"` so IDEs (Apollo Sandbox, etc.) that poll introspection on every keystroke don't flood their request history. Carry this behavior over.

#### Why it matters

- `strawberry-graphql-django` ships a `middlewares/debug_toolbar.py` so `django-debug-toolbar`'s SQL panel captures queries triggered by GraphQL resolvers. Without it, developers can't see the SQL hit by their queries during a `/graphql/` request.
- `graphene-django` ships **no** equivalent; this card is strawberry-graphql-django parity only.
- developer experience.

<a id="channels_asgi_router_migration_aid"></a>
### [DONE-041-0.0.14 - Channels ASGI router (migration aid)](KANBAN.html#channels_asgi_router_migration_aid)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: S
- Labels: `asgi`, `channels`, `django-integration`
- Spec: [spec-041-channels_router-0_0_14.md](docs/SPECS/spec-041-channels_router-0_0_14.md)

#### Package files

- [`django_strawberry_framework/routers.py`](django_strawberry_framework/routers.py)
- [`django_strawberry_framework/utils/imports.py`](django_strawberry_framework/utils/imports.py)
- [`django_strawberry_framework/utils/permissions.py`](django_strawberry_framework/utils/permissions.py)
- [`tests/test_routers.py`](tests/test_routers.py)
- [`tests/utils/test_imports.py`](tests/utils/test_imports.py)
- [`tests/utils/test_inputs.py`](tests/utils/test_inputs.py)
- [`tests/utils/test_permissions.py`](tests/utils/test_permissions.py)

#### Definition of done

- [x] Implement `django_strawberry_framework/routers.py` exposing `DjangoGraphQLProtocolRouter`.
- [x] `channels` is a soft dependency: top-level package import must not fail if `channels` is not installed. The helper wraps `channels` imports lazily and raises `ImportError` with an install hint when it is actually called.
- [x] Tests under `tests/test_routers.py` exercise both the channels-present and channels-absent paths.
- [x] Migration guide (`TODO-BETA-071-0.1.8`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → [`DjangoGraphQLProtocolRouter`](docs/GLOSSARY.md#djangographqlprotocolrouter), so the symbol rename is documented in one canonical location.

#### Architectural posture

- The router helper uses a **distinctly-ours symbol name**, `DjangoGraphQLProtocolRouter`, so the module is unambiguously ours and does not impersonate the upstream API. This respects the [`GOAL.md`][goal] non-goal "a thin wrapper around `strawberry-graphql-django`".
- Migration ergonomics are preserved by the upstream-equivalent mapping in the migration guide (`TODO-BETA-071-0.1.8`), not by copying the symbol name. A migrant changes the import (`from strawberry_django.routers import AuthGraphQLProtocolTypeRouter` → `from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter`) and passes the Django ASGI application the router requires (`django_application=get_asgi_application()`, called at the normal point in `asgi.py`; spec-046 Decision 3).

#### Why it matters

- `strawberry-graphql-django` ships a small `routers.py` that builds a `ProtocolTypeRouter` over `GraphQLHTTPConsumer` and `GraphQLWSConsumer` for consumers using Channels. The module is ~30 lines but is the single import that makes ASGI / WebSocket migration painless.
- Shipping a functionally-equivalent helper keeps a strawberry-graphql-django migrant's ASGI entrypoint change to the import plus the Django ASGI application the router requires. This card exists primarily to reduce migration friction, not to expand the API surface.
- small slice; explicit migration aid.

#### Card references

- Related: Migration guide (`TODO-BETA-071-0.1.8`) gains a one-row entry in its "symbol equivalents" table mapping `AuthGraphQLProtocolTypeRouter` → `DjangoGraphQLProtocolRouter`, so the symbol rename is documented in one canonical location. -> `TODO-BETA-071-0.1.8` - Migration and adoption guides

<a id="auth_mutations_login_logout_register"></a>
### [DONE-040-0.0.13 - Auth mutations (login / logout / register)](KANBAN.html#auth_mutations_login_logout_register)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `auth`, `mutations`, `public-api`
- Spec: [spec-040-auth_mutations-0_0_13.md](docs/SPECS/spec-040-auth_mutations-0_0_13.md)

#### Definition of done

- [x] Implement `django_strawberry_framework/auth/` with `login_mutation`, `logout_mutation`, `register_mutation`, and a `current_user` query helper, each composable with the existing permissions surface.
- [x] Mirrored tests under `tests/auth/`.
- [x] Documented as opt-in: consumers must import explicitly; auth mutations are not injected into every schema.

#### Why it matters

- `strawberry-graphql-django` ships a small auth-mutations module so consumers don't have to hand-wire the most common Django auth flows. Natural follow-on once general mutations land.

#### Dependencies

- depends on `DONE-036-0.0.11`.

#### Card references

- Related: depends on `DONE-036-0.0.11`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="drf_serializer_mutations_serializermutation"></a>
### [DONE-039-0.0.13 - DRF serializer mutations (`SerializerMutation`)](KANBAN.html#drf_serializer_mutations_serializermutation)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Status: Done
- Relative size: L
- Labels: `mutations`, `public-api`, `serializers`
- Spec: [spec-039-serializer_mutations-0_0_13.md](docs/SPECS/spec-039-serializer_mutations-0_0_13.md)

#### Package files

- [`django_strawberry_framework/rest_framework/`](django_strawberry_framework/rest_framework/)
- [`tests/rest_framework/`](tests/rest_framework/)

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Definition of done

- [x] Add `docs/SPECS/spec-039-serializer_mutations-0_0_13.md`.
- [x] Implement `django_strawberry_framework/rest_framework/` exposing [`SerializerMutation`](docs/GLOSSARY.md#serializermutation) (final name pinned during implementation) on the DRF-style Meta surface: `Meta.serializer_class`, `Meta.lookup_field`, `Meta.model_operations`, `Meta.optional_fields`.
- [x] Serializer-field → Strawberry input mapping lives in `rest_framework/serializer_converter.py`, dual-purposed for inputs and outputs (mirroring graphene's `is_input=True` flag).
- [x] `rest_framework` is a soft dependency: package import must succeed without DRF installed; the helper raises `ImportError` with an install hint when actually called.
- [x] Validation errors surface through the shared `errors: list[FieldError]` envelope from `DONE-036-0.0.11`, populated from `serializer.errors`.
- [x] Tests under `tests/rest_framework/`.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercising a `ModelSerializer` mutation.

#### Files likely touched

- `django_strawberry_framework/rest_framework/` (new)
- `tests/rest_framework/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Why it matters

- `graphene-django` ships `SerializerMutation`, which builds a mutation from a DRF `Serializer` / `ModelSerializer`. This is the highest-leverage write-side feature for DRF migrants — they already have serializers defined and want to reuse them in GraphQL.
- [`GOAL.md`][goal] explicitly names DRF as a target migration source ("keep the public API familiar to Django, DRF, and django-filter users"). Shipping `SerializerMutation` is on-mission, not just a parity item.

#### Dependencies

- `DONE-036-0.0.11` — general mutation infrastructure (including the shared `errors` envelope).

#### Card references

- Dependency: `DONE-036-0.0.11` — general mutation infrastructure (including the shared `errors` envelope). -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: Validation errors surface through the shared `errors: list[FieldError]` envelope from `DONE-036-0.0.11`, populated from `serializer.errors`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="form_based_mutations_django_forms_modelforms"></a>
### [DONE-038-0.0.12 - Form-based mutations (Django Forms / ModelForms)](KANBAN.html#form_based_mutations_django_forms_modelforms)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Status: Done
- Relative size: L
- Labels: `forms`, `mutations`, `public-api`
- Spec: [spec-038-form_mutations-0_0_12.md](docs/SPECS/spec-038-form_mutations-0_0_12.md)

#### Package files

- [`django_strawberry_framework/forms/`](django_strawberry_framework/forms/)
- [`tests/forms/`](tests/forms/)

#### Dependencies

- `DONE-036-0.0.11` - Mutations + auto-generated Input types

#### Definition of done

- [x] Add `docs/SPECS/spec-038-form_mutations-0_0_12.md`.
- [x] Implement `django_strawberry_framework/forms/` on the DRF-style Meta surface (`Meta.form_class`, `Meta.return_field_name`, etc.) rather than graphene's `MutationOptions` pattern.
- [x] Form-field → Strawberry input mapping lives in `forms/converter.py` and reuses the scalar conversion registry where field types overlap.
- [x] Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `DONE-036-0.0.11`, populated from `form.errors`.
- [x] Tests under `tests/forms/`.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercising both a plain `Form` mutation and a `ModelForm` mutation.

#### Files likely touched

- `django_strawberry_framework/forms/` (new)
- `tests/forms/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Why it matters

- `graphene-django` ships [`DjangoFormMutation`](docs/GLOSSARY.md#djangoformmutation) and `DjangoModelFormMutation`: mutation classes that consume a Django `Form` / `ModelForm` and translate field validation + `cleaned_data` into a GraphQL mutation surface. Many graphene-django consumers rely on this as their write-side abstraction because it reuses validation they already have.
- Without an equivalent, graphene-django migrants must rewrite every form-backed mutation against the lower-level mutation surface from `DONE-036-0.0.11`.

#### Dependencies

- `DONE-036-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to.

#### Card references

- Dependency: `DONE-036-0.0.11` — general mutation infrastructure (input-type generation, mutation-field plumbing) is the foundation form mutations attach to. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: Validation errors surface through the shared `errors: list[FieldError]` envelope defined in `DONE-036-0.0.11`, populated from `form.errors`. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="upload_scalar_and_file_image_field_mapping"></a>
### [DONE-037-0.0.11 - Upload scalar and file / image field mapping](KANBAN.html#upload_scalar_and_file_image_field_mapping)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `converters`, `mutations`, `scalars`, `uploads`
- Spec: [spec-037-upload_file_image_mapping-0_0_11.md](docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md)

#### Package files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`tests/types/test_converters.py`](tests/types/test_converters.py)

#### Definition of done

- [x] Scalar conversion in `types/converters.py` returns [`DjangoFileType`](docs/GLOSSARY.md#djangofiletype) / [`DjangoImageType`](docs/GLOSSARY.md#djangoimagetype) (or local equivalents) for `FileField` / `ImageField`.
- [x] Mutation input-type generation (`DONE-036-0.0.11`) maps the same fields to Strawberry's `Upload` scalar.
- [x] Synthetic-model tests cover both read and write paths.
- [x] `docs/GLOSSARY.md` documents the conversion table change.

#### Files likely touched

- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/mutations/` (input mapping)
- `tests/types/test_converters.py`

#### Why it matters

- `strawberry-graphql-django` maps `FileField` / `ImageField` to `Upload` on the input side and to `DjangoFileType` / `DjangoImageType` (with `name` / `path` / `size` / `url`) on the output side. Without it, every consumer that touches user uploads has to hand-roll the mapping.

#### Card references

- Related: Mutation input-type generation (`DONE-036-0.0.11`) maps the same fields to Strawberry's `Upload` scalar. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types

<a id="mutations_auto_generated_input_types"></a>
### [DONE-036-0.0.11 - Mutations + auto-generated Input types](KANBAN.html#mutations_auto_generated_input_types)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: XL
- Labels: `graphql-api`, `mutations`, `permissions`, `public-api`
- Spec: [spec-036-mutations-0_0_11.md](docs/SPECS/spec-036-mutations-0_0_11.md)

#### Package files

- [`django_strawberry_framework/mutations/`](django_strawberry_framework/mutations/)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`tests/mutations/`](tests/mutations/)

#### Dependencies

- `DONE-018-0.0.6` - Multiple DjangoTypes per model with `Meta.primary`
- `DONE-034-0.0.10` - Permissions subsystem

#### Definition of done

- [x] Add `docs/SPECS/spec-036-mutations-0_0_11.md`.
- [x] Implement `django_strawberry_framework/mutations/` (sets, fields, resolvers, input-type generation) on the DRF-style Meta surface (`Meta.input_class`, `Meta.partial_input_class`, etc.).
- [x] Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`.
- [x] Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; `DONE-038-0.0.12`, `DONE-039-0.0.13` and `DONE-040-0.0.13` return that same class rather than a per-flavor mirror, so a client's error branch is written once. Shape mirrors graphene-django's `ErrorType` - `field` (the GraphQL input field the client sent, or the `"__all__"` sentinel for a model-wide or multi-field-constraint error) plus `messages`. The type is ADDITIVE, not frozen: `codes` and `path` were added at `0.0.13` alongside `DONE-039-0.0.13` without disturbing the shared-return contract, so it carries **four** members today.
- [x] Tests under `tests/mutations/`.
- [x] Live HTTP coverage under `examples/fakeshop/test_query/` exercising the products write surface.

#### Files likely touched

- `django_strawberry_framework/mutations/` (new)
- `django_strawberry_framework/types/base.py`
- `tests/mutations/` (new)
- `examples/fakeshop/apps/products/schema.py`

#### Why it matters

- Mutations are the single largest unscoped gap against `strawberry-graphql-django`. Consumers migrating from strawberry-graphql-django will notice the missing write side immediately.
- `strawberry-django` exposes `create`, `update`, `delete`, custom mutations, and auto-generated `Input` / `PartialInput` types per model. These compose with permissions and the optimizer.

#### Dependencies

- `DONE-018-0.0.6` ([`Meta.primary`](docs/GLOSSARY.md#metaprimary)) — explicit primary type drives mutation target resolution.
- `DONE-034-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`.

#### Card references

- Dependency: `DONE-018-0.0.6` (`Meta.primary`) — explicit primary type drives mutation target resolution. -> `DONE-018-0.0.6` - Multiple DjangoTypes per model with `Meta.primary`
- Related: Auto-generated input types respect the relation-override contract pinned in `DONE-010-0.0.4`. -> `DONE-010-0.0.4` - 0.0.4 foundation slice (definition-order independence)
- Dependency: `DONE-034-0.0.10` (permissions) — write mutations need to compose with `apply_cascade_permissions`. -> `DONE-034-0.0.10` - Permissions subsystem
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; `DONE-038-0.0.12`, `DONE-039-0.0.13` and `DONE-040-0.0.13` return that same class rather than a per-flavor mirror, so a client's error branch is written once. Shape mirrors graphene-django's `ErrorType` - `field` (a model field name, or the `"__all__"` sentinel for a model-wide or multi-field-constraint error) plus `messages`. The type is ADDITIVE, not frozen: `codes` and `path` were added at `0.0.13` alongside `DONE-039-0.0.13` without disturbing the shared-return contract, so it carries **four** members today. -> `DONE-038-0.0.12` - Form-based mutations (Django Forms / ModelForms)
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; `DONE-038-0.0.12`, `DONE-039-0.0.13` and `DONE-040-0.0.13` return that same class rather than a per-flavor mirror, so a client's error branch is written once. Shape mirrors graphene-django's `ErrorType` - `field` (a model field name, or the `"__all__"` sentinel for a model-wide or multi-field-constraint error) plus `messages`. The type is ADDITIVE, not frozen: `codes` and `path` were added at `0.0.13` alongside `DONE-039-0.0.13` without disturbing the shared-return contract, so it carries **four** members today. -> `DONE-039-0.0.13` - DRF serializer mutations (`SerializerMutation`)
- Related: Define the shared `errors: list[FieldError]` envelope type for typed validation errors at the package boundary; `DONE-038-0.0.12`, `DONE-039-0.0.13` and `DONE-040-0.0.13` return that same class rather than a per-flavor mirror, so a client's error branch is written once. Shape mirrors graphene-django's `ErrorType` - `field` (a model field name, or the `"__all__"` sentinel for a model-wide or multi-field-constraint error) plus `messages`. The type is ADDITIVE, not frozen: `codes` and `path` were added at `0.0.13` alongside `DONE-039-0.0.13` without disturbing the shared-return contract, so it carries **four** members today. -> `DONE-040-0.0.13` - Auth mutations (login / logout / register)
- Related: `DONE-027-0.0.8`-scale. The single largest unscoped gap versus strawberry-graphql-django. New `mutations/` subpackage (sets / fields / resolvers / input-type generation) + spec + tests + live HTTP, plus the shared `errors: list[FieldError]` envelope reused by DONE-038-0.0.12 / DONE-039-0.0.13 / DONE-040-0.0.13. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="optimizer_robustness_hardening_upstream_comparison_guards"></a>
### [DONE-035-0.0.10 - Optimizer robustness hardening (upstream-comparison guards)](KANBAN.html#optimizer_robustness_hardening_upstream_comparison_guards)

- Priority: Medium-high
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `hardening`, `optimizer`, `performance`, `query-planning`
- Spec: [spec-035-optimizer_hardening-0_0_10.md](docs/SPECS/spec-035-optimizer_hardening-0_0_10.md)

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)
- [`tests/optimizer/test_extension.py`](tests/optimizer/test_extension.py)
- [`tests/optimizer/test_walker.py`](tests/optimizer/test_walker.py)
- [`tests/types/test_resolvers.py`](tests/types/test_resolvers.py)

#### Planning note

Source: 2026-06-11 comparative audit of `django_strawberry_framework/optimizer/` against `~/projects/strawberry-django-main/strawberry_django/optimizer.py` (1,823 lines, 36 capabilities inventoried). Three robustness gaps were verified absent in our source by direct inspection (grep + read, not inferred): no evaluated-queryset guard (zero `_result_cache` references package-wide), no operation-type gating of `.only()` (zero `OperationType` references), and no fragment `type_condition` narrowing (`type_condition` is only used as a fragment *marker* at `walker.py:845` and cloned at `extension.py:346`, never matched). Each guard exists upstream with a known mechanism and file:line anchor. The two big *performance* findings from the same audit — windowed nested-prefetch pagination and `totalCount` window-annotation reuse — are already owned by `Connection-aware optimizer planning` (WIP) and are explicitly NOT in this card. Ships in 0.0.10 because guard G2 must land before the 0.0.11 mutations cohort makes mutation root resolvers returning querysets a mainstream consumer path.

#### Dependencies

- `DONE-033-0.0.9` - Connection-aware optimizer planning

#### Scope

- G1 - evaluated-queryset guard. Today `DjangoOptimizerExtension._optimize` applies the plan to any root queryset; if the consumer's root resolver already evaluated it (a `len(qs)` guard, a `bool(qs)` branch, slicing for a log line), our `.only()` / `.select_related()` clone silently re-executes the SQL - a doubled query invisible to the consumer. Upstream guards this twice: the resolve hook only optimizes when `ret._result_cache is None` (`strawberry_django/optimizer.py:1781`) and `optimize()` re-checks `is_optimized(qs) or qs._result_cache is not None` (`optimizer.py:1628`). Implement: in `extension.py::_optimize`, AFTER the manager-to-`.all()` coercion at `extension.py:714` (a manager coercion always yields a fresh unevaluated queryset, so the guard must not fire before it) and BEFORE `diff_plan_for_queryset`, return the result unchanged when `getattr(queryset, "_result_cache", None) is not None`. Read defensively with `getattr` per the package posture pinned in `field_meta.py::_target_pk_name`.
- G1 non-goals: do NOT port upstream's `is_optimized()` flag, `CONFIG_KEY` queryset config, or the `QuerySet._clone` monkeypatch (`strawberry_django/queryset.py:50-62`) - those exist upstream because their optimizer can run at nested resolvers; our O3 root gate (`info.path.prev is None`, spec-002) already guarantees single application, so execution-state (`_result_cache`) is the only missing check.
- G2 - operation-type gating of `.only()`. We project `only_fields` onto mutation/subscription root querysets identically to queries; upstream disables `only` for non-QUERY operations (`enable_only and info.operation.operation == OperationType.QUERY`, `strawberry_django/optimizer.py:1784`, re-checked at `:1817`). Risk: a mutation resolver returning a queryset gets a selection-set-shaped `.only()`; post-mutation consumer code touching any unprojected field triggers one deferred-field refetch query per access, and `Model.save()` on a deferred instance writes only loaded fields (Django's documented deferred-save semantics) - a surprising interaction with signal handlers and downstream writes. Implement: suppress `only_fields` (keep `select_related` / `prefetch_related`) when `info.operation.operation is not OperationType.QUERY`, at plan-build time in the walker entry point.
- G2 cache-safety argument (spec-004 B1 grounding): gating at plan-build time is safe with ZERO cache-key change because the plan-cache key's first component is the printed operation AST (`_print_operation_with_reachable_fragments`, `extension.py:920-982`), and `print_ast(operation)` includes the `query` / `mutation` / `subscription` keyword - a query document and a mutation document can never collide on one cache entry.
- G2 FK-id-elision-under-non-`QUERY`-ops decision - **RESOLVED** (spec Decision 5): elision stays enabled, with a resolver-time loaded-check. With the optimizer's `only` suppressed the full source row loads, so the FK `attname` column the elision stub reads is normally present; but a consumer-returned `.only(...)` can still defer it, so `types/resolvers.py::_build_fk_id_stub` verifies the column is loaded and falls back **loudly** (strictness-visible) when it is not - never a silent per-row lazy load. Pinned by tests in `tests/types/test_resolvers.py`.
- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 - fragment type-condition narrowing. The walker treats `type_condition` purely as a fragment marker (`walker.py:845` is `hasattr(selection, "type_condition")`); `_included_field_selections` (`walker.py:733`) inlines every fragment body unconditionally. Two verified failure modes on interface/union queries: (a) fields from sibling concrete types miss the current `field_map` and fall through the unknown-name guard (`walker.py:203` `if django_field is None:` -> `continue`) - those branches are silently UNPLANNED, so every sibling-type relation selection is an N+1 the plan can never cover (B3 strictness fires at runtime, which is detection, not prevention); (b) a same-named relation existing on two members gets planned for the wrong branch - a spurious `select_related` join / over-projection (over-fetch, never wrong data).
- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 implementation (bounded, registry-only): when a fragment carries a non-None `type_condition`, inline its body only when the condition's type name matches the current planning type - the `type_cls` returned by `_resolve_field_map` (`walker.py:197`): its own GraphQL name, a name in its [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces), or the registered primary type name for the model; otherwise skip the fragment subtree. Resolve names through the registry/definition only - NO graphql-core schema lookups in the walk, preserving the B7 invariant (zero per-request Django/schema introspection). Upstream's heavier alternative for contrast: per-model concrete-type resolution via `get_possible_concrete_types` (`strawberry_django/utils/inspect.py:206-245`) with a per-concrete-type `ResolveInfo` re-walk (`optimizer.py:1492-1517`) - explicitly out of scope; we narrow, we do not multi-plan.
- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 cache-safety argument: narrowing is a pure function of (document, target_model, origin) - all three are already plan-cache key components (`extension.py:920-982`), so narrowed plans cache correctly with no key change.

#### Definition of done

- [x] Spec file added under `docs/` (numbered to the card at implementation time, suffix `optimizer_hardening-0_0_10`; it stays at the live working path until the next spec author's batched archive sweep relocates it to `docs/SPECS/`), recording all three guard mechanisms, the G2 elision decision, and the deferred-findings table from the 2026-06-11 audit with upstream file:line anchors.
- [x] G1: early-return lands in `extension.py::_optimize`; test pins the pass-through - root resolver evaluates the queryset (`len(qs)`) then returns it; assert exactly one SQL query total and that the returned object is the SAME queryset instance (not a re-executing clone). A second test pins that the manager-coercion path (`Model.objects`) still optimizes (the guard must sit after `extension.py:714`).
- [x] G2: a mutation operation whose root resolver returns a queryset produces a plan with empty `only_fields` while `select_related` / `prefetch_related` survive; a textually-identical selection set under a `query` operation still projects `only_fields`; both plans coexist in the cache (distinct printed-AST keys). Subscription operations covered by the same gate.
- [x] G2: the [FK-id elision](docs/GLOSSARY.md#fk-id-elision) under non-QUERY ops decision is pinned by a dedicated test matching whatever the spec records.
- [ ] **[DEFERRED to the abstract-return optimizer entry card — BACKLOG `polymorphic_interface_connections`; see spec-035 Decision 6/7 / Revision 3]** G3: union and interface fragment tests - sibling-type fragment bodies are excluded from the plan (no spurious `select_related` / `only` entries); matching-type and interface-implementor fragments still plan; the same-named-relation-on-two-members shape is a dedicated regression test; B3 strictness keys remain branch-sensitive after narrowing (no regression in `tests/optimizer/` strictness coverage).
- [ ] **[DEFERRED to the abstract-return optimizer entry card — BACKLOG `polymorphic_interface_connections`; see spec-035 Decision 6/7 / Revision 3]** Strictness `warn` no longer fires for relation selections inside correctly-narrowed sibling fragments that the resolver never executes (the old silent-N+1 signature is gone from that path).
- [x] No B1-B8 regressions: full suite green at the 100% coverage gate; the plan-cache hit path gains zero allocations (memoized id-resolver check stays ~40ns, cache-hit promotion unchanged); `ruff format` + `ruff check` clean.
- [x] Optimizer docs (`docs/` optimizer page or README optimizer section) gain a short 'what the optimizer will not touch' note covering evaluated querysets and non-query operations.

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py` - G1 `_result_cache` early return in `_optimize`; G2 operation-type read threaded to plan build.
- `django_strawberry_framework/optimizer/walker.py` - G2 `only_fields` suppression at `plan_optimizations` entry; G3 `type_condition` matching in `_included_field_selections` (and the extension-side fragment clone helpers `_named_children` / `_node_children_with_runtime_prefix` if connection extraction needs the same narrowing). **[As shipped: the G2 `enable_only` gate landed in `walker.py` threaded through every projection writer; G3 `type_condition` matching is DEFERRED (no code). The Decision 5 FK-id-elision loaded-check landed in `django_strawberry_framework/types/resolvers.py`, with tests in `tests/types/test_resolvers.py`.]**
- `django_strawberry_framework/optimizer/plans.py` - only if the G2 gate lands at apply-time instead of build-time (spec decides; build-time preferred for cacheability).
- `tests/optimizer/test_extension.py`, `tests/optimizer/test_walker.py` - mirrored guard tests.
- `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` - new (lives at the live working path; the `docs/SPECS/` archive move is the next spec author's batched sweep, never per-card).

#### Why it matters

- G2 is sequencing-critical: the 0.0.11 mutations cohort (`Mutations + auto-generated Input types` onward) makes mutation root resolvers returning querysets a mainstream path; shipping mutations on top of an ungated `.only()` bakes deferred-refetch storms and deferred-`save()` surprises into the first write-side release.
- G3 (**DEFERRED** - no runtime code in spec-035) targets the only known silent-N+1 class left in the walker: every interface/union sibling-type branch is unplanned, and B3 strictness only detects it at runtime in dev - the plan itself can never cover it. The narrowing that would close it is carried forward to the abstract-return optimizer entry card (motivation, not behavior shipped here).
- G1 protects consumer-evaluated querysets from invisible double execution - the exact 'respect what the consumer already did' posture spec-004 B8 pinned for optimization state, extended to execution state.
- All three are robustness parity items against `strawberry_django` (each verified at a specific upstream line) while preserving the four advantages the 2026-06-11 audit confirmed we hold over upstream: the global LRU plan cache (B1), FK-id elision (B2), strictness N+1 detection (B3), and class-creation-time `FieldMeta` precomputation (B7).

#### Dependencies

- **[DEFERRED - G3 ships no runtime code in spec-035; moved to the abstract-return optimizer entry card (BACKLOG `polymorphic_interface_connections`); see spec-035 Decision 6/7, Revision 3-4.]** G3 rewrites fragment inlining in the same `walker.py` selection-normalization seam (`_included_field_selections` / `_named_children`) that connection-aware planning extends; land after it to avoid concurrent walker churn, and so G3's union/interface tests can cover connection-wrapped fragments too.

#### Card references

- Dependency: G3 rewrites fragment inlining in the same `walker.py` selection-normalization seam (`_included_field_selections` / `_named_children`) that connection-aware planning extends; land after it to avoid concurrent walker churn, and so G3's union/interface tests can cover connection-wrapped fragments too. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Related: G2 (`.only()` gating by operation type) must land before the 0.0.11 mutations cohort makes mutation root querysets a mainstream consumer path. -> `DONE-036-0.0.11` - Mutations + auto-generated Input types
- Related: G1 extends spec-004 B8's consumer-state reconciliation from optimization state to execution state; G2's cache-safety argument rests on the spec-004 B1 printed-AST cache key. -> `DONE-004-0.0.3` - Optimizer beyond slices B1-B8
- Related: G1's minimal shape (no clone monkeypatch, no optimized flag) is justified by the O3 root gate; G3 lives in the O2 walker's selection-normalization seam. -> `DONE-002-0.0.2` - Optimizer O1-O6 foundation

<a id="permissions_subsystem"></a>
### [DONE-034-0.0.10 - Permissions subsystem](KANBAN.html#permissions_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Status: Done
- Relative size: L
- Labels: `optimizer`, `permissions`, `public-api`, `security`
- Spec: [spec-034-permissions-0_0_10.md](docs/SPECS/spec-034-permissions-0_0_10.md)

#### Package files

- [`django_strawberry_framework/permissions.py`](django_strawberry_framework/permissions.py)
- [`django_strawberry_framework/utils/permissions.py`](django_strawberry_framework/utils/permissions.py)
- [`examples/fakeshop/test_query/test_products_api.py`](examples/fakeshop/test_query/test_products_api.py)
- [`tests/optimizer/test_extension.py`](tests/optimizer/test_extension.py)
- [`tests/test_connection.py`](tests/test_connection.py)
- [`tests/test_list_field.py`](tests/test_list_field.py)
- [`tests/test_permissions.py`](tests/test_permissions.py)
- [`tests/test_relay_node_field.py`](tests/test_relay_node_field.py)

#### Planning note

Strawberry port of graphene-django's `apply_cascade_permissions(cls, queryset, info)` from `django_graphene_filters.permissions`. The cookbook line `return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)` is the canonical consumer surface — a single composable helper that walks the model graph at call time, runs each owner type's `get_queryset(qs, info)` against the related queryset, and returns a queryset that respects per-type row-level visibility across every traversed FK / OneToOne edge. Integrates with the optimizer's `Prefetch` downgrade so cascaded relations stay N+1-safe; per-field permission hooks via the reserved [`Meta.fields_class`](docs/GLOSSARY.md#metafields_class) slot are deferred to the later [FieldSet](docs/GLOSSARY.md#fieldset) work (`TODO-BETA-059-0.1.1`), not shipped in this card.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

#### Scope

- [`apply_cascade_permissions`](docs/GLOSSARY.md#apply_cascade_permissions)
- reserved `Meta.fields_class` slot for per-field permission hooks; the per-field read-gate itself ships with the later FieldSet work (`TODO-BETA-059-0.1.1`), not in this card
- Optimizer cooperation: cascaded relations downgrade to `Prefetch(queryset=...)` so visibility filters survive the join (carries the existing `get_queryset` → `Prefetch` downgrade contract across the cascade walk).
- composable permission rules that remain visible from the owning type/query surface
- Public callable surface: `apply_cascade_permissions(cls, queryset, info, fields=None)` returns a queryset; optional `fields=` argument scopes the cascade to specific FK names. Both sync and async variants ship; async variant uses `sync_to_async` around the cascade walker to stay event-loop-safe.
- Walks the model graph via `registry.iter_definitions()` (shipped 0.0.4) — for each FK / OneToOne whose target type has a `get_queryset`, build a subquery from that type's visibility and intersect into the caller's queryset.
- Cycle detection via a `ContextVar` "seen" set so self-referential or mutually-referential type graphs do not recurse infinitely; cycle break returns the partially-narrowed queryset without raising.
- Single-column FK / O2O scope only: relations without a single-column `column` attribute (composite FKs, generic relations) are skipped explicitly. M2M and reverse-FK visibility are out of scope for this card and tracked as deferred follow-ups.
- Nullable FK rows preserved — a `NULL` FK does not reference a hidden target so the parent row is not dropped from the result.
- Multi-DB / sharding safety: the per-edge target visibility subquery is pinned to the caller's database alias via `.using(qs._db)` so shard-aware querysets do not accidentally cross databases.

#### Definition of done

- [x] Add `docs/SPECS/spec-034-permissions-0_0_10.md`.
- [x] Implement `django_strawberry_framework/permissions.py` or a `permissions/` package if the surface grows.
- [x] Add `tests/test_permissions.py`.
- [x] Define the `Meta` surface for per-field permissions and promote keys only when applied end-to-end.
- [x] Use real fakeshop permission users through `services.create_users(1)` in example tests where the system-under-test is the example project.
- [x] Check all permission-related ORM paths for N+1 behavior.
- [x] `apply_cascade_permissions` exported from the public surface (`from django_strawberry_framework import apply_cascade_permissions`). Both sync and async-aware variants ship together.
- [x] The four upstream invariants are each pinned by a dedicated test: ContextVar cycle guard; single-column FK/O2O scope; multi-DB pinning to the caller's alias; nullable-FK rows preserved.
- [x] Reconcile open question: how the existing per-field FILTER-denial gate (`check_<field>_permission` on [`FilterSet`](docs/GLOSSARY.md#filterset) / [`OrderSet`](docs/GLOSSARY.md#orderset)) composes with the new cascade visibility. Decision recorded in `docs/SPECS/spec-034-permissions-0_0_10.md` before the implementation pass starts; tests pin both shapes.
- [x] Cascade composes with [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) (`DONE-030-0.0.9`): a connection field whose wrapped type's `get_queryset` calls `apply_cascade_permissions` produces a Relay connection where every edge's nested relations respect the same cascade rule.
- [x] Live HTTP coverage in `examples/fakeshop/test_query/` exercises real fakeshop permission users (via `services.create_users(1)`) across a 2-deep FK cascade. Real users, not mocked `info.context.user`.

#### Foundation-slice seam

- `apply_cascade_permissions(cls, queryset, info)` walks the model graph at call time; `registry.iter_definitions()` (shipped in 0.0.4) is the public iterator that walk uses to find each owner type's `get_queryset`.
- `_attach_relation_resolvers` already accepts a `skip_field_names` set so consumer-authored fields are not clobbered; field-level permission hooks (`fields_class`) extend the same skip-set semantics.

#### Why it matters

- for the fakeshop example and real usage.
- permissions/visibility is security-relevant and blocks the fakeshop real-usage story.

#### Dependencies

- `DjangoType.get_queryset`
- optimizer `Prefetch` downgrade
- future `DjangoConnectionField`

#### Open question

- Open question — hidden-FK semantics: when a parent row references a hidden target, choose between excluding the parent row, nulling the FK field, or returning a sentinel. The upstream uses sentinels; the Strawberry side has to pick before the cascade lands. Pinned in `docs/SPECS/spec-034-permissions-0_0_10.md`.
- Open question — cascade performance: subquery-per-FK (one extra round-trip per FK in the cascade) vs a single annotated pass (one query that joins every cascaded relation). The upstream is subquery-per-FK; benchmark both before committing.
- Open question — M2M / reverse-relation visibility: the upstream cascade explicitly skips M2M and reverse FK. Decide whether to extend coverage here or defer to a sibling card; if deferring, name the follow-up card in the spec.
- Open question — `check_permissions` API surface: does the existing per-field filter-denial `check_<field>_permission(self, request)` survive in its current form, get renamed to disambiguate from the new field-level read gate (`FieldSet.check_<field>_permission(info)` per `TODO-BETA-059-0.1.1`), or get deprecated in favor of a unified shape? Spec must answer before implementation.

#### Card references

- Dependency: future `DjangoConnectionField` -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)

<a id="connection_aware_optimizer_planning"></a>
### [DONE-033-0.0.9 - Connection-aware optimizer planning](KANBAN.html#connection_aware_optimizer_planning)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `connections`, `optimizer`, `query-planning`, `relay`
- Spec: [spec-033-connection_optimizer-0_0_9.md](docs/SPECS/spec-033-connection_optimizer-0_0_9.md)

#### Package files

- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`tests/optimizer/`](tests/optimizer/)

#### Definition of done

- [x] New spec at `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (the canonical structured filename).
- [x] Walker recognizes connection edge/node shapes without reaching into [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) internals.
- [x] Tests cover the cookbook-equivalent nested-connection shape against fakeshop or the cardinality fixture.
- [x] No regression on the existing B1-B8 plan-cache and queryset-diff coverage.

#### Files likely touched

- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `django_strawberry_framework/optimizer/extension.py`
- future `django_strawberry_framework/connection.py`
- mirrored optimizer tests

#### Dependencies

- gated on `DONE-030-0.0.9` / Relay decisions.

#### Card references

- Related: gated on `DONE-030-0.0.9` / Relay decisions. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

<a id="full_relay_story_node_connection_root_validation"></a>
### [DONE-032-0.0.9 - Full Relay story (Node + Connection + Root + validation)](KANBAN.html#full_relay_story_node_connection_root_validation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: XL
- Labels: `connections`, `graphql-api`, `permissions`, `public-api`, `relay`
- Spec: [spec-032-full_relay-0_0_9.md](docs/SPECS/spec-032-full_relay-0_0_9.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/relay.py`](django_strawberry_framework/relay.py)
- [`django_strawberry_framework/testing/__init__.py`](django_strawberry_framework/testing/__init__.py)
- [`django_strawberry_framework/testing/relay.py`](django_strawberry_framework/testing/relay.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)

#### Planning note

blocked on `DONE-030-0.0.9` ([`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield)). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, refetchable containers) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it.

#### Dependencies

- `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)

#### Scope

- **Required arguments**: `first: Int`, `after: String`, `last: Int`, `before: String`. Backward pagination (`last`/`before`) is required by the Relay spec.
- Reverse-FK and M2M relations on those types expose their Connection counterparts

#### Definition of done

- [x] New spec: `docs/SPECS/spec-032-full_relay-0_0_9.md` covering all eight goals above with worked examples and decision rationale.
- [x] [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield) and [`DjangoNodesField`](docs/GLOSSARY.md#djangonodesfield) exported from the package public surface; both wired through the registry's GlobalID decode path and the per-type `get_queryset`.
- [x] Reverse-FK and M2M relations on `relay.Node`-implementing types expose their Connection counterparts; [`Meta.relation_shapes`](docs/GLOSSARY.md#metarelation_shapes) opt-out documented.
- [x] Cursor pagination math passes the package's hand-authored Relay-spec conformance suite (the `first`/`after`/`last`/`before`/`pageInfo` edge cases), against both a root connection and a synthesized relation connection.
- [x] `Meta.connection = {"total_count": True}` adds a `totalCount` field that runs `qs.count()` on the unpaginated post-filter queryset.
- [x] Filter / order arguments accepted on Connection fields when the corresponding `*_class` is declared on the type.
- [x] Permission-aware Node lookup: `node(id:)` returns `null` for hidden rows; no existence leak via error timing.
- [x] Six schema-validation diagnostics from Goal 6 raise [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) with the documented messages.
- [x] `django_strawberry_framework.testing.relay` module exposes `global_id_for(type_cls, id, *, schema=None)` and `decode_global_id(gid, *, schema=None)`.
- [x] The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-066-0.1.5`.
- [x] 100% coverage across the new code paths; tests pin both happy paths and every validation failure.

#### Files likely touched

- `django_strawberry_framework/testing/relay.py` (new) — test helpers

#### Dependencies

- `DONE-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when DONE-030-0.0.9 lands.
- `DONE-027-0.0.8` (Filtering subsystem) — soft dependency for the filter argument on Connections.
- `DONE-028-0.0.8` ([Ordering](docs/GLOSSARY.md#ordering) subsystem) — soft dependency for the orderBy argument on Connections.
- `DONE-033-0.0.9` ([Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning)) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`.
- `DONE-034-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when DONE-034-0.0.10 lands.

#### Decision

- ~~`GlobalID` mapping decision~~ — Strawberry-supplied `id: GlobalID!` from the Relay interface replaces the synthesized `id: int!`; Django primary key remains projected as a connector column for the optimizer (Decision 2 of [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015]).
- Non-Strawberry-interface classes in [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) → rejected at validation with the offending class name.

#### Card references

- Dependency: blocked on `DONE-030-0.0.9` (`DjangoConnectionField`). When the connection field lands, this card unblocks and ships in the same release. The post-`1.0.0` "Relay magic" differentiators (type-rename GlobalID migrations, polymorphic connections, refetchable containers) live separately in [`BACKLOG.md`][backlog] item 39 — they extend this story rather than block it. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `filter: <Type>FilterInput` — generated from [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) (composes with `DONE-027-0.0.8`) -> `DONE-027-0.0.8` - Filtering subsystem
- Related: `orderBy: [<Type>OrderInput!]` — generated from [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) (composes with `DONE-028-0.0.8`) -> `DONE-028-0.0.8` - Ordering subsystem
- Related: `search: String` — generated from [`Meta.search_fields`](docs/GLOSSARY.md#metasearch_fields) (composes with `TODO-BETA-060-0.1.2` — note: search is `1.0.0` scope, ships after `0.1.0`; until then, search arg is absent) -> `TODO-BETA-060-0.1.2` - `Meta.search_fields` support
- Related: `DONE-030-0.0.9` (`DjangoConnectionField`) — **hard dependency**; this card unblocks when DONE-030-0.0.9 lands. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `DONE-033-0.0.9` (Connection-aware optimizer planning) — ships in parallel; the Node entry points and the relation-as-Connection upgrade both rely on the walker recognizing `edges { node { ... } }`. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Related: `DONE-034-0.0.10` (Permissions subsystem) — soft dependency; the Node entry points respect `get_queryset` immediately and integrate with declared permissions when DONE-034-0.0.10 lands. -> `DONE-034-0.0.10` - Permissions subsystem
- Related: The fakeshop `library` HTTP test suite gains Relay-shaped queries (refetch, paginated connection, cursor round-trip, `totalCount`). Fakeshop `products` activation lights up the full Relay surface as part of `TODO-BETA-066-0.1.5`. -> `TODO-BETA-066-0.1.5` - Fakeshop GraphQL schema activation

<a id="django_model_based_globalid_encoding"></a>
### [DONE-031-0.0.9 - Django-model-based GlobalID encoding](KANBAN.html#django_model_based_globalid_encoding)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
- Relative size: M
- Labels: `config`, `public-api`, `registry`, `relay`, `stable-api`, `types`, `versioning`
- Spec: [spec-031-globalid_encoding-0_0_9.md](docs/SPECS/spec-031-globalid_encoding-0_0_9.md)

#### Package files

- [`django_strawberry_framework/filters/base.py`](django_strawberry_framework/filters/base.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relay.py`](django_strawberry_framework/types/relay.py)
- [`django_strawberry_framework/utils/typing.py`](django_strawberry_framework/utils/typing.py)

#### Planning note

Promoted from BACKLOG.md item 40 and slotted after [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) but before the Full Relay story. This is the Relay identity-format decision: Django model identity should be the durable GlobalID anchor before root Node/refetch behavior and client-cache-facing Relay semantics harden.

#### Scope

- Switch the default Relay GlobalID payload for [`DjangoType`](docs/GLOSSARY.md#djangotype) rows from GraphQL type name + id to Django model label + id, e.g. `products.item:42`.
- Add a per-type [`Meta.globalid_strategy`](docs/GLOSSARY.md#metaglobalid_strategy) override and a schema-wide `DJANGO_STRAWBERRY_FRAMEWORK["RELAY_GLOBALID_STRATEGY"]` setting, with precedence `Meta` override, then setting, then package default.
- Support the planned strategies: `model` as the new default, `type` as an opt-in legacy/standard Relay convention, `type+model` as a transitional decoder/encoder mode, and callable strategies for fully custom encodings.
- Route decoded model-label IDs through Django's app registry and the framework registry so multiple `DjangoType`s for one model resolve through the primary type unless the consumer explicitly opts into type-scoped IDs.
- Document the edge cases: proxy models, multi-table inheritance, slug/custom `resolve_id_attr` values, composite-primary-key rejection, and rare Django model/app rename aliases.

#### Definition of done

- [x] A new or amended Relay spec records the GlobalID format decision before Full Relay root Node/refetch behavior ships.
- [x] Encoder and decoder tests cover `model`, `type`, `type+model`, and callable strategies.
- [x] Settings and `Meta.globalid_strategy` validation reject unknown strategy names loudly with `ConfigurationError`.
- [x] Multiple-`DjangoType` per model behavior is pinned: model-based IDs route through the primary type; type-scoped IDs remain available when consumers need disjoint auth/cache scopes.
- [x] Relay helper tests prove old type-name IDs can be accepted in transitional mode while new emitted IDs use the model-label strategy.
- [x] Standing docs describe the default, the opt-out path, and the pre-1.0 compatibility implications.

#### Foundation-slice seam

- Builds on the shipped Relay Node foundation (`Meta.interfaces = (relay.Node,)`, default `resolve_*` methods, and synthesized-id suppression).
- Must land before the Full Relay story mints durable root `node(id:)` and connection/refetch IDs into the public surface.
- The registry already knows the model-to-`DjangoType` mapping; this card changes what the encoded Relay ID points at, not how consumers declare Relay support.

#### Files likely touched

- `django_strawberry_framework/types/relay.py` or the local Relay helper module that owns encode/decode behavior
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/conf.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_relay_interfaces.py` and related Relay tests
- `docs/GLOSSARY.md`, `docs/README.md`, and the active Relay spec when the feature ships

#### Why it matters

- The standard Relay convention bakes the GraphQL type name into durable object identity. In Django apps the model is the durable thing; the GraphQL type is a refactor-friendly facade.
- Getting this right before `1.0.0` lets consumers rename GraphQL types without invalidating every cached GlobalID. Waiting until after Full Relay ships turns the same decision into migration work.

#### Card references

- Related: This card should land before Full Relay because root `node(id:)`, `nodes(ids:)`, and refetch helpers make GlobalID encoding a public durability contract. -> `DONE-032-0.0.9` - Full Relay story (Node + Connection + Root + validation)
- Related: `DjangoConnectionField` can land before this card because connection pagination does not require changing the Relay GlobalID payload. -> `DONE-030-0.0.9` - `DjangoConnectionField` (Relay connection field)
- Related: `DONE-015-0.0.5` - 0.0.5 Relay interfaces and Node foundation

<a id="djangoconnectionfield_relay_connection_field"></a>
### [DONE-030-0.0.9 - `DjangoConnectionField` (Relay connection field)](KANBAN.html#djangoconnectionfield_relay_connection_field)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: L
- Labels: `connections`, `filters`, `optimizer`, `ordering`, `public-api`, `relay`
- Spec: [spec-030-connection_field-0_0_9.md](docs/SPECS/spec-030-connection_field-0_0_9.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/connection.py`](django_strawberry_framework/connection.py)
- [`django_strawberry_framework/list_field.py`](django_strawberry_framework/list_field.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/orders/inputs.py`](django_strawberry_framework/orders/inputs.py)
- [`django_strawberry_framework/orders/sets.py`](django_strawberry_framework/orders/sets.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)

#### Planning note

Strawberry analogue of graphene-django's `AdvancedDjangoFilterConnectionField`. Wires the shipped Layer-3 sidecars into a Relay-shaped connection: accepts `filter:` from [`Meta.filterset_class`](docs/GLOSSARY.md#metafilterset_class) (`DONE-027-0.0.8`), `orderBy:` from [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) (`DONE-028-0.0.8`), plus `first`/`after`/`last`/`before` cursor pagination and opt-in `totalCount`. The `search:` arg activates when `TODO-BETA-060-0.1.2` lands; [`FieldSet`](docs/GLOSSARY.md#fieldset) selection composition is layered in by `TODO-BETA-059-0.1.1`. Central read-side primitive — every Layer-3 argument composes through this field.

#### Dependencies

- `DONE-027-0.0.8` - Filtering subsystem
- `DONE-028-0.0.8` - Ordering subsystem
- `DONE-029-0.0.9` - `DjangoType` consumer-DX cleanup pass

#### Scope

- Relay-style connection field
- composition of filtering, ordering, aggregation, field selection, and optimizer behavior
- Cookbook anchor: Strawberry analogue of graphene-django's `AdvancedDjangoFilterConnectionField`. Each `DjangoConnectionField(SomeType)` exposes the type's declared sidecars as connection arguments plus the standard Relay pagination args. The graphene cookbook line `all_object_types = AdvancedDjangoFilterConnectionField(ObjectTypeNode)` becomes `all_object_types: DjangoConnection[ObjectTypeNode] = DjangoConnectionField(ObjectTypeNode)` on the Strawberry side; the per-type `Meta.filterset_class` / `Meta.orderset_class` declarations drive argument generation identically.
- `filter: <Type>FilterInput` — auto-derived from `Meta.filterset_class` (`DONE-027-0.0.8`); absent when the type declares no filterset. Active-input gating and `check_*_permission` propagation carry over from the filter subsystem unchanged.
- `orderBy: [<Type>OrderInput!]` — auto-derived from `Meta.orderset_class` (`DONE-028-0.0.8`); absent when the type declares no orderset. List-shaped per the order spec's Decision 5.
- `first` / `after` / `last` / `before` — Relay cursor args; forward AND backward pagination per the Relay spec. Mutually-exclusive guard (`first` + `last` in one query) rejected as a typed error.
- `totalCount` — opt-in via `Meta.connection = {"total_count": True}`; runs `qs.count()` on the unpaginated post-filter queryset so paginated UIs can show "N of M" without a second round-trip.
- Composition order on the resolved queryset: `get_queryset(qs, info)` first (visibility), then `filter` (active-input gates), then `orderBy` (per-field gates), then cursor slice. The pre-pagination shape is what the optimizer plans against; the cursor slice runs last so totals stay correct.

#### Definition of done

- [x] Add `docs/SPECS/spec-030-connection_field-0_0_9.md`.
- [x] Implement `django_strawberry_framework/connection.py`.
- [x] Add `tests/test_connection.py`.
- [x] Decide whether full Relay support belongs here or a separate `relay/` subpackage.
- [x] Promote [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield) only when end-to-end schema usage is tested.
- [x] When the wrapped type declares `Meta.filterset_class`, the connection field exposes `filter: <Type>FilterInput` and routes input values through the filterset's `apply_sync` / `apply_async` pair.
- [x] When the wrapped type declares `Meta.orderset_class`, the connection field exposes `orderBy: [<Type>OrderInput!]` and routes through the orderset's `apply_sync` / `apply_async` pair.
- [x] Connection field composes with `cls.get_queryset(queryset, info)` — visibility scoping runs before any filter / order / cursor work.
- [x] Optimizer cooperation: the connection-aware planner (`DONE-033-0.0.9`) layers on without retrofit; this card ships against the existing flat-selection walker and the connection-aware walker takes over when DONE-033-0.0.9 lands.
- [x] Live HTTP coverage in `examples/fakeshop/test_query/` exercises a real round-trip with filter + orderBy + cursor + totalCount on a Relay-Node-shaped type.

#### Foundation-slice seam

- `finalize_django_types()` is the single architectural entry point that `DjangoConnectionField(DjangoType)` (and [`DjangoNodeField`](docs/GLOSSARY.md#djangonodefield)) will auto-trigger as their wrapper.
- An auto-trigger wrapper must respect the single-threaded-setup window: either be constrained to schema-construction time, or acquire a real lock around the finalizer.
- [Connection-aware optimizer planning](docs/GLOSSARY.md#connection-aware-optimizer-planning) is its own follow-up slice (`DONE-033-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes.

#### Dependencies

- [`FilterSet`](docs/GLOSSARY.md#filterset) (`DONE-027-0.0.8`)
- [`OrderSet`](docs/GLOSSARY.md#orderset) (`DONE-028-0.0.8`)
- Relay/interface decisions
- `FieldSet` — **deferred to `TODO-BETA-059-0.1.1`** (post-Alpha); field-selection composition is layered on after the connection field ships, not a 0.0.9 blocker.
- [`DjangoType`](docs/GLOSSARY.md#djangotype) consumer-DX cleanup pass (`DONE-029-0.0.9`) - schema-construction examples are current before `DjangoConnectionField` becomes the new consumer pattern.

#### Card references

- Dependency: `FilterSet` (`DONE-027-0.0.8`) -> `DONE-027-0.0.8` - Filtering subsystem
- Related: Connection-aware optimizer planning is its own follow-up slice (`DONE-033-0.0.9`); the foundation slice did not exercise nested connection prefetch shapes. -> `DONE-033-0.0.9` - Connection-aware optimizer planning
- Dependency: `OrderSet` (`DONE-028-0.0.8`) -> `DONE-028-0.0.8` - Ordering subsystem
- Related: once filters/orders are stable. FieldSet integration is deferred to `TODO-BETA-059-0.1.1` — `DjangoConnectionField` ships against the Layer-2 surface in 0.0.9 and gains field-selection composition when FieldSet lands. -> `TODO-BETA-059-0.1.1` - `FieldSet` declarative field-level behavior (`Meta.fields_class`)
- Dependency: `DjangoType` consumer-DX cleanup pass (`DONE-029-0.0.9`) - schema-construction examples are current before `DjangoConnectionField` becomes the new consumer pattern. -> `DONE-029-0.0.9` - `DjangoType` consumer-DX cleanup pass
- Related: `TODO-BETA-060-0.1.2` - `Meta.search_fields` support

<a id="djangotype_consumer_dx_cleanup_pass"></a>
### [DONE-029-0.0.9 - `DjangoType` consumer-DX cleanup pass](KANBAN.html#djangotype_consumer_dx_cleanup_pass)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `cleanup`, `developer-tools`, `public-api`, `types`
- Spec: [spec-029-consumer_dx_cleanup-0_0_9.md](docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md)

#### Package files

- [`django_strawberry_framework/management/commands/inspect_django_type.py`](django_strawberry_framework/management/commands/inspect_django_type.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)

#### Planning note

planned; three independent slices that ship in any order. Card body counts as complete when all three slices land; if the schedule forces Slice 3 to defer, the slice carves off as its own follow-up card without disrupting Slices 1 + 2.

#### Scope

- **Slice 1** — the singleton-factory `extensions=` construction form. Every optimizer `extensions=` entry is a factory over a singleton scoped to its construction site, `extensions=[lambda: <instance>]`: Strawberry calls the factory per operation and gets the same instance back, so the instance-bound plan cache survives, and a callable never trips Strawberry's instance-form `DeprecationWarning`. The bare class and a constructing `lambda: DjangoOptimizerExtension()` are rejected, since each hands every operation a fresh instance and the cache never hits (spec-029 Decision 3). Applies to every construction site in tests and examples and to the schema-construction snippets in `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, and `TODAY.md`.
- **Slice 2** — `manage.py inspect_django_type <Type>` diagnostic command at `django_strawberry_framework/management/commands/inspect_django_type.py`. It reads a finalized [`DjangoType`](docs/GLOSSARY.md#djangotype)'s `__django_strawberry_definition__` and prints per field: Django field name → Django field type → resolved GraphQL type → nullability → which converter row fired. Mirrors Django's `inspectdb` conceptually but scoped to the framework's type-definition surface. Tests: `examples/fakeshop/tests/test_inspect_django_type.py` (`call_command("inspect_django_type", "BookType", ...)`) and `tests/management/test_inspect_django_type.py`.
- **Slice 3** — [`Meta.nullable_overrides`](docs/GLOSSARY.md#metanullable_overrides) / [`Meta.required_overrides`](docs/GLOSSARY.md#metarequired_overrides) GraphQL-layer nullability overrides. Two public `Meta` keys let consumers decouple a non-relation field's GraphQL nullability from the underlying Django column without an `AlterField` migration or a custom resolver; they resolve at type-construction time in `django_strawberry_framework/types/base.py` through the `force_nullable` tri-state of `django_strawberry_framework/types/converters.py`, and relation targets are rejected. Tests in `tests/types/test_converters.py` (override + collision cases) plus a live HTTP test demonstrating the override flipping the GraphQL type's nullability without touching the model column. Spec: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`.

#### Definition of done

- [x] **Slice 1**: every optimizer `extensions=` entry uses the singleton-factory form in tests, examples, and consumer-facing docs. `uv run pytest` shows zero `DeprecationWarning` about Strawberry extension instances. `CHANGELOG.md` `## [0.0.9]` carries the `### Changed` bullet.
- [x] **Slice 2**: `django_strawberry_framework/management/commands/inspect_django_type.py` ships with module + class docstring, `add_arguments` registering a positional `type` argument plus `--schema <selector>`, and `handle` printing the resolved field table. Tests via `examples/fakeshop/tests/test_inspect_django_type.py` (`call_command`) and `tests/management/test_inspect_django_type.py`. `docs/GLOSSARY.md` carries the `Schema introspection management command` entry; `docs/TREE.md` lists the new module under `management/commands/`. `CHANGELOG.md` `## [0.0.9]` carries the `### Added` bullet.
- [x] **Slice 3**: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` written and reviewed; `Meta.nullable_overrides` and `Meta.required_overrides` implemented; tests cover override-applies, override-rejects-unknown-field, override-collides-with-other-direction error, and override-on-choice-field. `docs/GLOSSARY.md` carries an entry; a live HTTP test in `examples/fakeshop/test_query/` demonstrates the override flipping nullability for a real model field. `CHANGELOG.md` `## [0.0.9]` carries the `### Added` bullet.

#### Foundation-slice seam

- Slice 1 has no foundation interaction; it's a sweep across already-shipped surfaces.
- Slice 2 reads `DjangoTypeDefinition` populated by `finalize_django_types()`; the command is a strict consumer of the existing introspection surface.
- Slice 3 plugs into `DjangoType._build_annotations` (the converter loop in `django_strawberry_framework/types/base.py`) and the scalar-resolution path in `django_strawberry_framework/types/converters.py`. No finalizer changes — overrides apply at type-construction time, before finalization.

<a id="ordering_subsystem"></a>
### [DONE-028-0.0.8 - Ordering subsystem](KANBAN.html#ordering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: L
- Labels: `filters`, `graphql-api`, `layer-3`, `ordering`, `public-api`
- Spec: [spec-028-orders-0_0_8.md](docs/SPECS/spec-028-orders-0_0_8.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/orders/__init__.py`](django_strawberry_framework/orders/__init__.py)
- [`django_strawberry_framework/orders/base.py`](django_strawberry_framework/orders/base.py)
- [`django_strawberry_framework/orders/factories.py`](django_strawberry_framework/orders/factories.py)
- [`django_strawberry_framework/orders/inputs.py`](django_strawberry_framework/orders/inputs.py)
- [`django_strawberry_framework/orders/sets.py`](django_strawberry_framework/orders/sets.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)

#### Definition of done

- [x] Add `docs/SPECS/spec-028-orders-0_0_8.md`.
- [x] Add `django_strawberry_framework/orders/`.
- [x] Add mirrored `tests/orders/`.
- [x] Promote [`Meta.orderset_class`](docs/GLOSSARY.md#metaorderset_class) only when ordering is applied end-to-end.
- [x] Support simple fields and relation paths.
- [x] Define interaction with filters and connection field.
- [x] Keep ordering declarations introspectable from the owning type/query surface.

#### Card references

- Related: `~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/fields.py::DjangoFilterConnectionField #"order_by"` — connection field accepts an `order_by` argument that composes through `django_filters.OrderingFilter` declared on the FilterSet. Graphene has no separate ordering primitive; ⚛️ parity is met by the filter subsystem (`DONE-027-0.0.8`) rather than this card. -> `DONE-027-0.0.8` - Filtering subsystem

<a id="filtering_subsystem"></a>
### [DONE-027-0.0.8 - Filtering subsystem](KANBAN.html#filtering_subsystem)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: XL
- Labels: `example-app`, `filters`, `graphql-api`, `public-api`
- Spec: [spec-027-filters-0_0_8.md](docs/SPECS/spec-027-filters-0_0_8.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- [`django_strawberry_framework/exceptions.py`](django_strawberry_framework/exceptions.py)
- [`django_strawberry_framework/filters/__init__.py`](django_strawberry_framework/filters/__init__.py)
- [`django_strawberry_framework/filters/base.py`](django_strawberry_framework/filters/base.py)
- [`django_strawberry_framework/filters/factories.py`](django_strawberry_framework/filters/factories.py)
- [`django_strawberry_framework/filters/inputs.py`](django_strawberry_framework/filters/inputs.py)
- [`django_strawberry_framework/filters/sets.py`](django_strawberry_framework/filters/sets.py)
- [`django_strawberry_framework/list_field.py`](django_strawberry_framework/list_field.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)
- [`django_strawberry_framework/sets_mixins.py`](django_strawberry_framework/sets_mixins.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relay.py`](django_strawberry_framework/types/relay.py)

<a id="scalar_conversion_end_to_end_coverage_in_the_fakeshop_example"></a>
### [DONE-026-0.0.7 - Scalar conversion end-to-end coverage in the fakeshop example](KANBAN.html#scalar_conversion_end_to_end_coverage_in_the_fakeshop_example)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `example-app`, `graphql-api`, `scalars`, `tests`
- Spec: [spec-026-scalar_conversion_fakeshop-0_0_7.md](docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md)

#### Scope

- Full non-null wire-format sweep covering every field on `ScalarSpecimen`
- All-NULL nullable wire format covering every nullable converter branch

<a id="warning_free_scalar_registration_via_strawberryconfigscalar_map"></a>
### [DONE-025-0.0.7 - Warning-free scalar registration via `StrawberryConfig.scalar_map`](KANBAN.html#warning_free_scalar_registration_via_strawberryconfigscalar_map)

- Priority: Medium
- Status: Done
- Relative size: S
- Labels: `config`, `internal`, `public-api`, `scalar-map`, `scalars`
- Spec: [spec-025-scalar_map_helper-0_0_7.md](docs/SPECS/spec-025-scalar_map_helper-0_0_7.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)

<a id="django_trac_37064_hardening_safe_wrap_connection_method"></a>
### [DONE-024-0.0.7 - Django Trac #37064 hardening + `safe_wrap_connection_method`](KANBAN.html#django_trac_37064_hardening_safe_wrap_connection_method)

- Priority: Low
- Status: Done
- Relative size: S
- Labels: `django-integration`, `hardening`, `internal`
- Spec: [spec-024-django_trac_37064_hardening-0_0_7.md](docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md)

#### Package files

- [`django_strawberry_framework/_django_patches.py`](django_strawberry_framework/_django_patches.py)
- [`django_strawberry_framework/apps.py`](django_strawberry_framework/apps.py)
- `django_strawberry_framework/test/__init__.py` (historical)
- `django_strawberry_framework/test/_wrap.py` (historical)

<a id="multi_database_cooperation_contract"></a>
### [DONE-023-0.0.7 - Multi-database cooperation contract](KANBAN.html#multi_database_cooperation_contract)

- Priority: Low
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
- Relative size: S
- Labels: `multi-db`, `optimizer`, `tests`
- Spec: [spec-023-multi_db-0_0_7.md](docs/SPECS/spec-023-multi_db-0_0_7.md)

<a id="schema_export_management_command"></a>
### [DONE-022-0.0.7 - Schema export management command](KANBAN.html#schema_export_management_command)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: S
- Labels: `management-command`, `public-api`, `schema`
- Spec: [spec-022-export_schema-0_0_7.md](docs/SPECS/spec-022-export_schema-0_0_7.md)

#### Package files

- [`django_strawberry_framework/management/__init__.py`](django_strawberry_framework/management/__init__.py)
- [`django_strawberry_framework/management/commands/__init__.py`](django_strawberry_framework/management/commands/__init__.py)
- [`django_strawberry_framework/management/commands/export_schema.py`](django_strawberry_framework/management/commands/export_schema.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)

<a id="appspy_and_django_app_config"></a>
### [DONE-021-0.0.7 - `apps.py` and Django app config](KANBAN.html#appspy_and_django_app_config)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: XS
- Labels: `django-app`, `packaging`
- Spec: [spec-021-apps-0_0_7.md](docs/SPECS/spec-021-apps-0_0_7.md)

#### Package files

- [`django_strawberry_framework/apps.py`](django_strawberry_framework/apps.py)

<a id="djangolistfield_non_relay_list"></a>
### [DONE-020-0.0.7 - `DjangoListField` (non-Relay list)](KANBAN.html#djangolistfield_non_relay_list)

- Priority: High
- Parity: ⚛️ graphene-django (Required)
- Status: Done
- Relative size: M
- Labels: `graphql-api`, `list-field`, `optimizer`, `public-api`
- Spec: [spec-020-list_field-0_0_7.md](docs/SPECS/spec-020-list_field-0_0_7.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/list_field.py`](django_strawberry_framework/list_field.py)

<a id="consumer_override_semantics_scalar_fields"></a>
### [DONE-019-0.0.6 - Consumer override semantics (scalar fields)](KANBAN.html#consumer_override_semantics_scalar_fields)

- Priority: Medium
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: L
- Labels: `public-api`, `relay`, `scalars`, `types`
- Spec: [spec-019-consumer_overrides_scalar-0_0_6.md](docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md)

#### Package files

- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)

#### Test plan

- End-to-end test pinned the override surviving `strawberry.type(...)`
- 100% coverage was reached across `tests/types/test_definition_order.py`

#### Decision

- **`relay.Node` `id` collision rejected at type-creation time.** A consumer

<a id="multiple_djangotypes_per_model_with_metaprimary"></a>
### [DONE-018-0.0.6 - Multiple DjangoTypes per model with `Meta.primary`](KANBAN.html#multiple_djangotypes_per_model_with_metaprimary)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
- Relative size: L
- Labels: `optimizer`, `public-api`, `registry`, `types`
- Spec: [spec-018-meta_primary-0_0_6.md](docs/SPECS/spec-018-meta_primary-0_0_6.md)

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)

#### Test plan

- 100% coverage across `tests/test_registry.py`, `tests/types/test_base.py`,

#### Decision

- Two primary types for the same model: rejected at registration time

<a id="deferred_scalar_conversions"></a>
### [DONE-017-0.0.6 - Deferred scalar conversions](KANBAN.html#deferred_scalar_conversions)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `converters`, `public-api`, `scalars`
- Spec: [spec-017-deferred_scalars-0_0_6.md](docs/SPECS/spec-017-deferred_scalars-0_0_6.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/scalars.py`](django_strawberry_framework/scalars.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)

#### Test plan

- 100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the warning-free import surface are explicit.

#### Card references

- Related: `BigAutoField` preserved as `int` before scalar override recourse shipped in `DONE-019-0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)
- Related: The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` was suppressed at the definition site at `0.0.6` (tight `warnings.catch_warnings()` filter), keeping the package import surface clean. `DONE-025-0.0.7` replaced that suppression: `BigInt` is now a bare `NewType` bound to a `ScalarDefinition` built from Strawberry's no-warning `strawberry.scalar(name=...)` overload and registered through the package scalar map that the public `strawberry_config()` factory merges into a consumer's `strawberry.Schema(...)` — the real public-API change this note anticipated, not an internal-only refactor. -> `DONE-025-0.0.7` - Warning-free scalar registration via `StrawberryConfig.scalar_map`

<a id="fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement"></a>
### [DONE-016-0.0.6 - `FieldMeta` single-source-of-truth consolidation and mirror retirement](KANBAN.html#fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement)

- Priority: Medium
- Parity: 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
- Relative size: M
- Labels: `cleanup`, `field-meta`, `metadata`, `optimizer`, `types`
- Spec: [spec-016-fieldmeta_consolidation-0_0_6.md](docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md)

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Scope

- **SSoT consolidation.** Three reader sites now read `FieldMeta` from the canonical source on `DjangoTypeDefinition.field_map`:
- `django_strawberry_framework/types/base.py:_record_pending_relation`
- `django_strawberry_framework/types/converters.py:resolved_relation_annotation`
- `django_strawberry_framework/types/resolvers.py:_make_relation_resolver`
- **Mirror retirement.** `DjangoType.__init_subclass__` no longer writes the legacy class-attribute mirrors. The optimizer reads from `registry.get_definition(type_cls)` directly at all four former reader sites:
- `optimizer/walker.py:_resolve_field_map`
- `optimizer/walker.py:_walk_selections` (hints read)
- `optimizer/extension.py:_collect_schema_reachable_types`
- `optimizer/extension.py:check_schema`
- All `TODO(spec-fieldmeta-*)` source anchors removed.
- 100% package coverage maintained; no consumer-visible API change.
- internal metadata-architecture refactor; no consumer-visible API change.
- Internal refactor only; no `Meta` key changes, no public surface changes, no consumer-visible behavior changes. Existing tests pass without modification.

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/extension.py`

#### Why it matters

- Three reader sites were re-deriving relation shape via `relation_kind(field)` + raw `getattr(field, ...)` instead of reading the `FieldMeta` already on `DjangoTypeDefinition.field_map` — duplicating logic and creating drift surface for any future relation-flag addition.
- `DjangoType.__init_subclass__` was writing legacy class-attribute mirrors (`cls._optimizer_field_map`, `cls._optimizer_hints`) that survived `registry.clear()`, then four optimizer sites read those mirrors instead of the canonical `DjangoTypeDefinition`. Two parallel sources of field metadata with no enforced consistency.

<a id="005_relay_interfaces_and_node_foundation"></a>
### [DONE-015-0.0.5 - 0.0.5 Relay interfaces and Node foundation](KANBAN.html#005_relay_interfaces_and_node_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: L
- Labels: `public-api`, `relay`, `types`
- Spec: [spec-015-relay_interfaces-0_0_5.md](docs/SPECS/spec-015-relay_interfaces-0_0_5.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- [`django_strawberry_framework/optimizer/_context.py`](django_strawberry_framework/optimizer/_context.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relations.py`](django_strawberry_framework/types/relations.py)
- [`django_strawberry_framework/types/relay.py`](django_strawberry_framework/types/relay.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)
- [`django_strawberry_framework/utils/__init__.py`](django_strawberry_framework/utils/__init__.py)
- [`django_strawberry_framework/utils/relations.py`](django_strawberry_framework/utils/relations.py)
- [`django_strawberry_framework/utils/typing.py`](django_strawberry_framework/utils/typing.py)

#### Scope

- [`Meta.interfaces`](docs/GLOSSARY.md#metainterfaces) accepted end-to-end for any Strawberry interface.
- Four Relay node resolver defaults injected when `relay.Node` is declared (canonical order: `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`); consumer-declared overrides are preserved via Strawberry's `__func__` identity test.
- Automatic synthesized `id: int!` suppression when `relay.Node` is in `Meta.interfaces`; the Relay-supplied `id: GlobalID!` is used instead.
- `is_type_of` injection is unconditional for every [`DjangoType`](docs/GLOSSARY.md#djangotype) (Relay-declared or not); consumer-declared `is_type_of` is preserved.
- Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.
- Both sync and async paths for `_resolve_node_default` / `_resolve_nodes_default`; async `get_queryset` hooks are awaited on the async branch and rejected with `ConfigurationError` on the sync branch.
- `Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.
- Package version bumped to `0.0.5` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock`.

#### Foundation-slice seam

- `Meta.interfaces` is the first `0.0.4`-reserved `DjangoTypeDefinition` slot that ships end-to-end through finalizer phase 2.5; subsequent Layer 3 subsystems plug into the same architectural seam.

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/relay.py`
- `django_strawberry_framework/types/finalizer.py`
- `tests/types/test_relay_interfaces.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_relay_id_projection.py`
- `tests/test_registry.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `CHANGELOG.md`
- `docs/GLOSSARY.md`
- `docs/README.md`
- `TODAY.md`
- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`

#### Architectural posture

- Borrowed patterns from `strawberry-django` (spec "Borrowing posture", Decision 3). The override discriminator triad stays distinct across the three injection sites: `__dict__` membership for `is_type_of`, tuple membership for id suppression, `__func__` identity for the four `resolve_*` defaults.

<a id="move_test_fixture_out_of_example_settings"></a>
### [DONE-014-0.0.4 - Move test fixture out of example settings](KANBAN.html#move_test_fixture_out_of_example_settings)

- Priority: Low
- Status: Done
- Relative size: S
- Labels: `cleanup`, `example-app`, `internal`, `tests`
- Spec: [spec-014-testing_shift-0_0_4.md](docs/SPECS/spec-014-testing_shift-0_0_4.md)

#### Scope

- Removed `tests.fixtures.apps.TestsCardinalityConfig` from the example project.
- Removed the old unmanaged cardinality fixture files under `tests/fixtures/`.
- Package tests that need OneToOne / M2M / cardinality coverage now use real models from `examples/fakeshop/apps/library/`.

#### Files likely touched

- `examples/fakeshop/config/settings.py`
- `examples/fakeshop/apps/library/models.py`
- `docs/SPECS/spec-014-testing_shift-0_0_4.md`
- `AGENTS.md`
- `docs/TREE.md`

#### Why it matters

- test hygiene.

<a id="real_m2m_coverage"></a>
### [DONE-013-0.0.4 - Real M2M coverage](KANBAN.html#real_m2m_coverage)

- Priority: Medium
- Status: Done
- Relative size: S
- Labels: `example-app`, `internal`, `m2m`, `tests`
- Spec: [spec-013-real_m2m_coverage-0_0_4.md](docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md)

#### Package files

- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Scope

- Replaced test-only M2M/cardinality fixtures with real managed models in the `library` example app.
- Added package-level and HTTP-level coverage for M2M traversal and optimizer planning.

#### Files likely touched

- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `tests/types/test_definition_order.py`
- `tests/optimizer/test_definition_order.py`

#### Why it matters

- test hygiene.

<a id="004_version_and_release_alignment"></a>
### [DONE-012-0.0.4 - 0.0.4 version and release alignment](KANBAN.html#004_version_and_release_alignment)

- Priority: Low
- Status: Done
- Relative size: XS
- Labels: `internal`, `release`, `versioning`
- Spec: [spec-012-version_release_alignment-0_0_4.md](docs/SPECS/spec-012-version_release_alignment-0_0_4.md)

#### Scope

- Package metadata, runtime version, lockfile, tests, and changelog now agree on `0.0.4`.
- The changelog entry is condensed for the alpha release and covers the actual commit range through 2026-05-08.

#### Files likely touched

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`
- `CHANGELOG.md`

<a id="stale_placeholder_cleanup"></a>
### [DONE-011-0.0.4 - Stale placeholder cleanup](KANBAN.html#stale_placeholder_cleanup)

- Priority: Low
- Status: Done
- Relative size: XS
- Labels: `cleanup`, `docs`, `internal`, `tests`
- Spec: [spec-011-stale_placeholder_cleanup-0_0_4.md](docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md)

#### Scope

- Replaced stale M2M and forward-reference skips with definition-order tests.
- [Scalar field override semantics](docs/GLOSSARY.md#scalar-field-override-semantics) is a separate concern from definition order and is owned by `DONE-019-0.0.6`, which ships it at `0.0.6`.

#### Files likely touched

- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`

#### Why it matters

- internal test/doc cleanup.

#### Card references

- Related: Scalar field override semantics is a separate concern from definition order and ships at `0.0.6`. -> `DONE-019-0.0.6` - Consumer override semantics (scalar fields)

<a id="004_foundation_slice_definition_order_independence"></a>
### [DONE-010-0.0.4 - 0.0.4 foundation slice (definition-order independence)](KANBAN.html#004_foundation_slice_definition_order_independence)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
- Relative size: L
- Labels: `finalizer`, `registry`, `relations`, `types`
- Spec: [spec-010-foundation-0_0_4.md](docs/SPECS/spec-010-foundation-0_0_4.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/definition.py`](django_strawberry_framework/types/definition.py)
- [`django_strawberry_framework/types/finalizer.py`](django_strawberry_framework/types/finalizer.py)
- [`django_strawberry_framework/types/relations.py`](django_strawberry_framework/types/relations.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Scope

- `DjangoTypeDefinition` dataclass with forward-reserved slots for every Layer 3 subsystem.
- `PendingRelation` and pending-relation registry API (`add_pending_relation`, `iter_pending_relations`, `discard_pending`, `is_finalized`, `mark_finalized`, extended `clear`).
- `finalize_django_types()` three-phase finalizer (resolve pending → attach resolvers → `strawberry.type(cls)`), with phase-1 failure-atomicity and named-source-model error format.
- Manual relation override contract: split `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` so annotation-only overrides keep the generated resolver while assigned-field / decorator overrides suppress it. Class-attribute shadowing of relation fields raises `ConfigurationError`.
- `PendingRelationAnnotation` sentinel with metaclass `__repr__` that surfaces a useful `TypeError` body if `strawberry.Schema(...)` is constructed before finalization.
- MRO-aware `get_queryset` override detection (`django_strawberry_framework/utils/truth.py::overrides`) so abstract bases without `Meta` still flip the `has_custom_get_queryset` sentinel for downstream concrete subclasses.
- Real cardinality coverage through the `library` example app (`Patron`, `MembershipCard`, `Genre`, `Book`, `Shelf`, `Branch`, `Loan`) instead of test-only fixture models.
- Dedicated test files: `tests/types/test_definition_order.py`, `tests/types/test_definition_order_schema.py`, `tests/optimizer/test_definition_order.py`, plus `tests/test_registry.py` extensions for idempotency / phase-1 atomicity / phase-2/3 partial-mutation contract / pending-set cleanup / class-mutation residue.
- Documentation sweep: `README.md`, `docs/README.md`, `docs/GLOSSARY.md`, `TODAY.md`, and `CHANGELOG.md`.
- Version bump to `0.0.4` across `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock`.
- Deletion of `TypeRegistry.lazy_ref`; unsupported and unresolved relations now fail with explicit [`ConfigurationError`](docs/GLOSSARY.md#configurationerror) messages at annotation-building or finalization time.

#### Foundation-slice seam

- The forward-reserved slots on `DjangoTypeDefinition` are the architectural seam where the cookbook-shaped Layer 3 subsystems plug in (each subsystem moves its `Meta` key out of `DEFERRED_META_KEYS`, populates the matching slot in collection, and consumes it during finalization or in [`DjangoConnectionField`](docs/GLOSSARY.md#djangoconnectionfield)).
- The pending-resolution pattern (record at class creation, resolve at finalization, fail loud on missing target with named source model / field / target) generalizes directly to lazy related class references for [`RelatedFilter`](docs/GLOSSARY.md#relatedfilter), [`RelatedOrder`](docs/GLOSSARY.md#relatedorder), and `RelatedAggregate`.

#### Files likely touched

- `django_strawberry_framework/types/definition.py`
- `django_strawberry_framework/types/relations.py`
- `django_strawberry_framework/types/finalizer.py`
- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `django_strawberry_framework/registry.py`
- `tests/types/test_definition_order.py`
- `tests/types/test_definition_order_schema.py`
- `tests/optimizer/test_definition_order.py`
- `tests/test_registry.py`
- `examples/fakeshop/apps/library/models.py`
- `examples/fakeshop/apps/library/schema.py`
- `examples/fakeshop/test_query/test_library_api.py`
- `CHANGELOG.md`
- `docs/SPECS/spec-010-foundation-0_0_4.md`

<a id="rich_schema_architecture"></a>
### [DONE-009-0.0.4 - Rich schema architecture](KANBAN.html#rich_schema_architecture)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
- Relative size: L
- Labels: `layer-3`, `public-api`, `relations`, `types`
- Spec: [spec-009-rich_schema_architecture-0_0_4.md](docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md)

#### Scope

- Lay out the long-term architecture for filters, orders, aggregates, connections, permissions, and fieldsets.
- Compare Graphene, django-graphene-filters, and strawberry-graphql-django patterns against this package's DRF-shaped API.
- Define how the 0.0.4 foundation slice becomes the base for later Layer 3 subsystems.

<a id="definition_order_independence_design"></a>
### [DONE-008-0.0.4 - Definition-order independence design](KANBAN.html#definition_order_independence_design)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent), 🍓 strawberry-graphql-django (Parity-adjacent)
- Status: Done
- Relative size: M
- Labels: `finalizer`, `registry`, `relations`, `types`
- Spec: [spec-008-definition_order_independence-0_0_4.md](docs/SPECS/spec-008-definition_order_independence-0_0_4.md)

#### Scope

- Frame the class-definition-time relation-resolution problem.
- Compare options for preserving concrete related `DjangoType`s without import-order coupling.
- Set the failure-mode requirements that the 0.0.4 foundation slice implements.

<a id="004_onboarding_docs_and_spec_consolidation"></a>
### [DONE-007-0.0.4 - 0.0.4 onboarding docs and spec consolidation](KANBAN.html#004_onboarding_docs_and_spec_consolidation)

- Priority: Medium
- Status: Done
- Relative size: S
- Labels: `docs`, `internal`, `release`
- Spec: [spec-007-onboarding_docs_spec_consolidation-0_0_4.md](docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md)

#### Scope

- Root `README.md` is the canonical documentation map and operational entry point.
- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
- `docs/GLOSSARY.md` is the capability catalog with value-led optimizer language and comparison table.
- `docs/TREE.md` is the detailed layout/test-tree reference.
- `CHANGELOG.md` is condensed and no longer relies on design-doc pointers for release context.
- Completed design-doc content is folded into durable docs, while remaining specs preserve design history and follow-up work.

#### Files likely touched

- `README.md`
- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`
- `CHANGELOG.md`

#### Why it matters

- internal docs cleanup / spec consolidation — no upstream-parity surface.

<a id="documentationstatus_positioning_for_shipped_layer_2"></a>
### [DONE-006-0.0.3 - Documentation/status positioning for shipped Layer 2](KANBAN.html#documentationstatus_positioning_for_shipped_layer_2)

- Priority: Medium
- Status: Done
- Relative size: S
- Labels: `docs`, `internal`
- Spec: [spec-006-public_surface-0_0_3.md](docs/SPECS/spec-006-public_surface-0_0_3.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Scope

- `docs/README.md` gives a quickstart, package positioning, optimizer value, and status.
- `docs/GLOSSARY.md` describes shipped, planned, deferred, and alpha-constrained capabilities.
- `docs/TREE.md` preserves detailed package/test tree responsibilities.

#### Files likely touched

- `docs/README.md`
- `docs/GLOSSARY.md`
- `docs/TREE.md`

#### Why it matters

- internal docs / status-positioning card — no upstream-parity surface.

<a id="djangotype_contract_and_boundary"></a>
### [DONE-005-0.0.3 - DjangoType contract and boundary](KANBAN.html#djangotype_contract_and_boundary)

- Priority: High
- Parity: ⚛️ graphene-django (Parity-adjacent)
- Status: Done
- Relative size: M
- Labels: `docs`, `public-api`, `registry`, `types`
- Spec: [spec-005-django_type_contract-0_0_3.md](docs/SPECS/spec-005-django_type_contract-0_0_3.md)

#### Package files

- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)

#### Scope

- Document the alpha one-model-one-type registry constraint.
- Reject unsupported or deferred `Meta` keys instead of accepting unwired surface area.
- Remove consumer override promises that the implementation cannot honor yet.

<a id="optimizer_beyond_slices_b1_b8"></a>
### [DONE-004-0.0.3 - Optimizer beyond slices B1-B8](KANBAN.html#optimizer_beyond_slices_b1_b8)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: L
- Labels: `optimizer`, `performance`, `query-planning`, `schema-audit`
- Spec: [spec-004-optimizer_beyond-0_0_3.md](docs/SPECS/spec-004-optimizer_beyond-0_0_3.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Scope

- B1: plan cache keyed by selected operation AST, directive variables, model, root runtime path, and the resolver's origin Strawberry type
- B2: forward-FK-id elision
- B3: strictness mode (`off`, `warn`, `raise`)
- B4: [`Meta.optimizer_hints`](docs/GLOSSARY.md#metaoptimizer_hints) with [`OptimizerHint`](docs/GLOSSARY.md#optimizerhint)
- B5: plan introspection via context
- B6: schema-build-time audit
- B7: precomputed optimizer field metadata
- B8: queryset diffing against consumer-applied `select_related`, `prefetch_related`, and `Prefetch`

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/hints.py`
- `django_strawberry_framework/optimizer/field_meta.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_hints.py`
- `tests/optimizer/test_field_meta.py`
- `tests/optimizer/test_plans.py`

#### Card references

- Related: continuation of DONE-002-0.0.2's optimizer lineage (⚛️ parity-adjacent). -> `DONE-002-0.0.2` - Optimizer O1-O6 foundation

<a id="optimizer_o4_nested_prefetch_chains"></a>
### [DONE-003-0.0.2 - Optimizer O4 nested prefetch chains](KANBAN.html#optimizer_o4_nested_prefetch_chains)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: M
- Labels: `optimizer`, `performance`, `query-planning`, `relations`
- Spec: [spec-003-optimizer_nested_prefetch_chains-0_0_2.md](docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md)

#### Package files

- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/field_meta.py`](django_strawberry_framework/optimizer/field_meta.py)
- [`django_strawberry_framework/optimizer/hints.py`](django_strawberry_framework/optimizer/hints.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)

#### Scope

- Plan depth > 1 relation selections from the root optimizer pass.
- Emit nested `Prefetch` objects for many-side branches that need shaped child querysets.
- Recurse through single-valued relation chains with `select_related` and `only()` fields intact.

<a id="optimizer_o1_o6_foundation"></a>
### [DONE-002-0.0.2 - Optimizer O1-O6 foundation](KANBAN.html#optimizer_o1_o6_foundation)

- Priority: High
- Parity: 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: L
- Labels: `optimizer`, `performance`, `query-planning`, `relations`
- Spec: [spec-002-optimizer-0_0_2.md](docs/SPECS/spec-002-optimizer-0_0_2.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/optimizer/__init__.py`](django_strawberry_framework/optimizer/__init__.py)
- [`django_strawberry_framework/optimizer/extension.py`](django_strawberry_framework/optimizer/extension.py)
- [`django_strawberry_framework/optimizer/plans.py`](django_strawberry_framework/optimizer/plans.py)
- [`django_strawberry_framework/optimizer/walker.py`](django_strawberry_framework/optimizer/walker.py)
- [`django_strawberry_framework/types/__init__.py`](django_strawberry_framework/types/__init__.py)
- [`django_strawberry_framework/types/base.py`](django_strawberry_framework/types/base.py)
- [`django_strawberry_framework/types/converters.py`](django_strawberry_framework/types/converters.py)
- [`django_strawberry_framework/types/resolvers.py`](django_strawberry_framework/types/resolvers.py)
- [`django_strawberry_framework/utils/__init__.py`](django_strawberry_framework/utils/__init__.py)
- [`django_strawberry_framework/utils/strings.py`](django_strawberry_framework/utils/strings.py)
- [`django_strawberry_framework/utils/typing.py`](django_strawberry_framework/utils/typing.py)

#### Scope

- generated relation resolvers
- selection-tree walker
- root-gated optimizer extension
- nested `Prefetch` chains
- same-query `select_related` recursion
- [`only()` projection](docs/GLOSSARY.md#only-projection)
- custom `get_queryset` downgrade to `Prefetch`

#### Files likely touched

- `django_strawberry_framework/optimizer/extension.py`
- `django_strawberry_framework/optimizer/walker.py`
- `django_strawberry_framework/optimizer/plans.py`
- `tests/optimizer/test_extension.py`
- `tests/optimizer/test_walker.py`
- `tests/optimizer/test_plans.py`

<a id="djangotype_core_foundation"></a>
### [DONE-001-0.0.1 - DjangoType core foundation](KANBAN.html#djangotype_core_foundation)

- Priority: High
- Parity: ⚛️ graphene-django (Required), 🍓 strawberry-graphql-django (Required)
- Status: Done
- Relative size: L
- Labels: `public-api`, `registry`, `relations`, `scalars`, `types`
- Spec: [spec-001-django_types-0_0_1.md](docs/SPECS/spec-001-django_types-0_0_1.md)

#### Package files

- [`django_strawberry_framework/__init__.py`](django_strawberry_framework/__init__.py)
- [`django_strawberry_framework/conf.py`](django_strawberry_framework/conf.py)
- `django_strawberry_framework/converters.py` (historical)
- [`django_strawberry_framework/exceptions.py`](django_strawberry_framework/exceptions.py)
- `django_strawberry_framework/optimizer.py` (historical)
- [`django_strawberry_framework/registry.py`](django_strawberry_framework/registry.py)
- `django_strawberry_framework/types.py` (historical)

#### Scope

- [`DjangoType`](docs/GLOSSARY.md#djangotype) base class
- Meta validation
- scalar conversion
- relation conversion
- choice enums
- type registry
- relation resolvers
- `get_queryset` hook and `has_custom_get_queryset`

#### Files likely touched

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/types/resolvers.py`
- `tests/types/test_base.py`
- `tests/types/test_converters.py`
- `tests/types/test_resolvers.py`

#### Architectural posture

- The public shape is intentionally narrow and explicit.

#### Decision

- Deferred Meta keys are rejected, not silently accepted.

#### Card references

- Related: [Definition-order independence](docs/GLOSSARY.md#definition-order-independence) is now covered by `DONE-010-0.0.4`. -> `DONE-010-0.0.4` - 0.0.4 foundation slice (definition-order independence)

## Release readiness checklist

Before a release:

- `django_strawberry_framework/__init__.py` `__version__` (the single version literal; hatchling derives the packaging version from it) matches `tests/base/test_init.py::test_version` and the `docs/GLOSSARY.md` package-version line.
- README status matches actual top-level exports.
- `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, and any active design docs agree on shipped/planned state.
- No stale skipped tests refer to already-shipped slices.
- New source modules have mirrored tests in the correct tree.
- `uv run ruff check --fix .` passes.
- `uv run ruff format .` passes.
- The full `django.yml` matrix, dispatched with `gh workflow run django.yml` (every Python / Django cell, single-DB and `FAKESHOP_SHARDED=1`, plus the lint job), passes on the release commit, including the `fail_under = 100` package coverage gate on the latest single-DB cell.

## Notes for Kanban maintenance

- Treat this file as a living operational board, not a spec.
- When a card moves to Done, update the evidence and remove stale blocker language.
- When a future spec creates a new subsystem, add it here as a card with a definition of done.
- Keep `CHANGELOG.md` out of routine updates unless explicitly requested.
- Strategic differentiation candidates (features neither `graphene-django` nor `strawberry-graphql-django` ship cleanly) live in [`BACKLOG.md`][backlog] or the Backlog board section. When a backlog item is scheduled, promote it to a `TODO[-MILESTONE]-NNN-X.Y.Z` card here and cross-reference back.

## Decision: FilterSet subclassing unsupported

FilterSet / FilterArgumentsFactory subclassing is unsupported (decided 2026-05-30).

FilterArgumentsFactory raises TypeError on subclassing: its class-level input_object_types / _type_filterset_registry caches are shared mutable dicts a subclass would inherit rather than isolate, silently cross-contaminating builds.

Rationale: supporting subclassing would turn a currently-discouraged pattern into a real API commitment and pull in cache / lifecycle fixes that do not buy much without a concrete consumer need. Revisit if a real consumer need arises.

## Decision: Alpha cards must claim upstream parity

Every Alpha (`0.0.x`) card that ships a consumer-facing capability MUST carry at least one upstream parity link — a `ParityClaim` against `graphene_django` (⚛️) and/or `strawberry_django` (🍓), at `required` or `adjacent` level — AND at least one justification bullet in the card's `Verified in upstream` section grounding that link in a specific upstream `path::symbol` (decided 2026-06-09).

Rationale: Alpha is the road to `0.1.0` feature parity, so an Alpha *feature* card with no parity link is either mis-scoped (it belongs in Beta as a beyond-parity differentiator) or simply untracked. Requiring the link plus a grounded justification keeps the Alpha cut honestly parity-bearing and makes each card's placement auditable against the upstreams.

Exemption: pure-internal housekeeping cards — documentation, release / version alignment, cleanup, test-only coverage, and Django-core defensive hardening — have no upstream feature to match and are labeled `internal`; the rule does not apply to them. A parity link must NEVER be fabricated to satisfy the rule: if no honest upstream analog exists, the card is `internal` (or belongs in Beta), not parity-tagged.

Enforcement: `scripts/check_alpha_parity.py` fails if any non-`internal` Alpha card lacks a parity link or a `Verified in upstream` justification.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[backlog]: BACKLOG.md
[goal]: GOAL.md
[readme]: README.md

<!-- docs/ -->
[docs-readme]: docs/README.md
[glossary-bigint-scalar]: docs/GLOSSARY.md#bigint-scalar
[glossary-django-trac-37064-hardening]: docs/GLOSSARY.md#django-trac-37064-hardening
[glossary-filterset]: docs/GLOSSARY.md#filterset
[glossary-metafilterset_class]: docs/GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: docs/GLOSSARY.md#metaorderset_class
[glossary-multi-database-cooperation]: docs/GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: docs/GLOSSARY.md#optimizerhint
[glossary-orderset]: docs/GLOSSARY.md#orderset
[glossary-relatedfilter]: docs/GLOSSARY.md#relatedfilter
[glossary-relatedorder]: docs/GLOSSARY.md#relatedorder
[glossary-safe-wrap-connection-method]: docs/GLOSSARY.md#safe_wrap_connection_method
[glossary-strawberry-config]: docs/GLOSSARY.md#strawberry_config

<!-- docs/SPECS/ -->
[spec-015]: docs/SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-020]: docs/SPECS/spec-020-list_field-0_0_7.md
[spec-023]: docs/SPECS/spec-023-multi_db-0_0_7.md
[spec-027]: docs/SPECS/spec-027-filters-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[apps]: django_strawberry_framework/apps.py
[converters]: django_strawberry_framework/types/converters.py
[django-patches]: django_strawberry_framework/_django_patches.py
[filters]: django_strawberry_framework/filters/
[orders]: django_strawberry_framework/orders/
[plans]: django_strawberry_framework/optimizer/plans.py
[resolvers]: django_strawberry_framework/types/resolvers.py
[test-init]: django_strawberry_framework/testing/__init__.py
[wrap]: django_strawberry_framework/testing/_wrap.py

<!-- tests/ -->
[test-converters]: tests/types/test_converters.py
[test-multi-db]: tests/optimizer/test_multi_db.py
[test-resolvers]: tests/types/test_resolvers.py

<!-- examples/ -->
[db-shard-b.sqlite3]: examples/fakeshop/db_shard_b.sqlite3
[example-schema]: examples/fakeshop/config/schema.py
[fakeshop-library]: examples/fakeshop/apps/library/
[fakeshop-test-library]: examples/fakeshop/test_query/test_library_api.py
[kanban-app]: examples/fakeshop/apps/kanban/
[fakeshop-test-multi-db]: examples/fakeshop/test_query/test_multi_db.py
[settings]: examples/fakeshop/config/settings.py
[test-library-api]: examples/fakeshop/test_query/test_library_api.py
[test-scalars-api]: examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
