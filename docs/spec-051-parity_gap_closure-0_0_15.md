# Spec: Upstream parity-gap closure — close the six build-side deltas the `0.1.0` parity audit left, before the beta cut

Planned for `0.0.15` (card `WIP-ALPHA-051-0.0.15`); **this card shares the
`0.0.15` line with three others (`DONE-050-0.0.15` list-field arguments;
`TODO-ALPHA-052-0.0.15` debug extraction; `TODO-ALPHA-053-0.0.15` boundary
hardening + DRY squeeze), so it owns no version bump** — card `053` lands
last and carries the joint cut
([Decision 9](#decision-9--joint-0015-cut--this-card-bumps-nothing)).
This card is a **parity card**: six small, test-pinned items against a named
⚛️ graphene-django or 🍓 strawberry-graphql-django surface, grouped because
they share one charter — every build-side parity delta the `0.1.0` audit could
not home onto an existing card closes here — not because they share a seam.
None is a new subsystem; each lands as a predicate, a converter arm, a
description thread, a soft-dependency reuse, or (for the two already in the
tree) a verification pass.

The six items (items 1–4 are Slices 1–4; Slice 5 verifies items 5 and 6):

1. **A `through=` guard** ([Decision 2](#decision-2--the-through-guard-is-a-write-side-predicate-raised-before-any-request)):
   a `through=`-declared many-to-many whose through model carries required
   extra columns is refused with a
   [`ConfigurationError`][glossary-configurationerror] naming the through model
   and the columns, wherever a generated write would reach `.set()`. Today
   `django_strawberry_framework/mutations/resolvers.py::_assign_m2m` is a plain
   `.set()`, so every write that sends the relation a non-empty list returns
   the generic `"__all__"` constraint error of the
   [`FieldError` envelope][glossary-fielderror-envelope]
   (`django_strawberry_framework/utils/errors.py::integrity_error_field_errors`)
   — a schema misdeclaration reported to the client as a data error, whatever
   the rows hold (an omitted relation or `[]` inserts no through row).
2. **`GeneratedField` support** ([Decision 3](#decision-3--a-generatedfield-converts-through-its-output_field-and-never-enters-a-write-input)):
   a Django `GeneratedField` converts via its `output_field`, is nullable when
   either it or its `output_field` declares `null`, and stays out of every
   generated write input. **Built** (Slice 2):
   `django_strawberry_framework/types/converters.py::generated_output_field`
   unwraps the field to the column it computes, so the scalar route, the
   `SCALAR_MAP` walk, nullability and the choice enum all read that column.
   The `SCALAR_MAP` walk is keyed on the **output field's** class (MRO
   walked, read live), so a project maps an unsupported output class by
   registering that class, and a `SCALAR_MAP[models.GeneratedField]` entry
   is never consulted. The unwrap refuses three outputs at type or
   `FilterSet` creation (a file output; an output class with no `SCALAR_MAP`
   ancestor that is no `ArrayField` / `HStoreField`, whose message offers
   `django_strawberry_framework/types/converters.py::generated_output_field #"Add an entry to SCALAR_MAP or exclude this field via"`;
   an `ArrayField` output whose `base_field` declares choices). The
   per-field escapes are exclusion
   ([`Meta.exclude`][glossary-metaexclude]) and, on the type, an
   annotation-only override
   (`django_strawberry_framework/types/base.py::_build_annotations #"wins over the auto-synthesized annotation"`
   skips conversion for a consumer-authored name); nullability is
   overridden per field by `Meta.nullable_overrides` /
   `Meta.required_overrides`.
3. **Model `help_text` as the SDL description** ([Decision 4](#decision-4--help_text-is-always-on-no-setting) and
   [Decision 5](#decision-5--the-description-is-attached-where-each-field-object-is-built)):
   always on, no setting; an explicit consumer description wins.
4. **`django-choices-field` enum reuse** ([Decision 6](#decision-6--a-declared-choices_enum-is-reused-through-soft-dependency-detection)):
   a `TextChoicesField` / `IntegerChoicesField` publishes the consumer's own
   `choices_enum` instead of a second enum minted from the raw choices; soft
   detection only, no hard dependency.
5. **`FieldError` keying** ([Decision 7](#decision-7--fielderror-keying-is-the-shipped-key-map-contract-no-toggle)):
   **built.** Every flavor keys through
   `django_strawberry_framework/utils/errors.py::build_error_key_map`, and the
   card's Scope row already describes the shipped key map, its matrix and its
   live rows.
6. **`PAGINATION_INVALID`** ([Decision 8](#decision-8--pagination-rejections-carry-pagination_invalid-shipped)):
   **built and ticked on the card.** Every
   [`PaginationArgumentError`][glossary-paginationargumenterror] carries the
   audited `extensions.code`.

Status: **PARTIALLY BUILT** (the checklist boxes stay unticked; this line is
the truth). Built: item 2, Slice 2 (`GeneratedField`: the computed column
`django_strawberry_framework/utils/relations.py::generated_column`, the
conversion unwrap and its three refusals
`django_strawberry_framework/types/converters.py::generated_output_field`
read by the scalar route, the scalar-map walk, nullability and blank
admission, the filter side's selection column
`django_strawberry_framework/filters/sets.py::FilterSet._selected_column`
and resolved column `django_strawberry_framework/filters/base.py::_model_resolved_field`,
the array helpers, the keyset cursor reads, the identity codec
(`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`)
and the inspection label; library
`Shelf.code_length` / `Shelf.topic_length` with migration
`0020_shelf_code_length_topic_length`, pinned live in
`examples/fakeshop/test_query/test_library_generated_api.py`); item 5 (the key map in `utils/errors.py`, its matrix in
`examples/fakeshop/test_query/test_mutation_error_keys_api.py`, and the live rows the card's DoD names —
library `createPublisher` for the model flavor, kanban `setCardStatus` for the
plain form, library `createShelfViaSubclassedSerializer` for the serializer)
and item 6 (`django_strawberry_framework/utils/errors.py::PAGINATION_INVALID_ERROR_CODE`
on every `django_strawberry_framework/utils/connections.py::PaginationArgumentError`,
pinned live in `examples/fakeshop/test_query/test_connection_pagination_api.py`).
The cross-card rows the DoD owes are also already on the board: card
`TODO-BETA-071-0.1.8`'s upstream-settings table carries the `CAMELCASE_ERRORS`
row and its write-surface row carries the `through_defaults` refusal, and card
`053`'s Slice 5 sentence, GLOSSARY-flip DoD and dependency edge on this card
are in place (placed at the 2026-08-29 board review, the date this card's own
DoD row records), though the edge's note repeats a false file-overlap claim
Slice 5 amends. Item 5's card row is current: its Scope row already describes
the shipped key map. Outstanding (absent from the tree): items 1, 3 and 4,
each a slice below, and the card-row amendments Slice 5 owes
([Decision 11](#decision-11--board-rows-cross-card-rows-are-verified-the-cards-own-stale-rows-are-amended)).
Five slices: Slice 1 (**the `through=` guard**), Slice 2
(**`GeneratedField`**), Slice 3 (**`help_text` descriptions**), Slice 4
(**`choices_enum` reuse**), Slice 5 (**verification of the shipped items and
the cross-card rows, card amendments, docs fold-in, card wrap — no version
cut**).

Permission caveat: `AGENTS.md` prohibits `CHANGELOG.md` edits without
explicit permission; **this spec grants none.** The `0.0.15` release entry
covering this card is written by card `053`'s Slice 5
([`spec-053`][spec-053] Decision 11), which owns the joint cut for the line.

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`DjangoType`][glossary-djangotype],
  [`finalize_django_types`][glossary-finalize_django_types],
  [`Meta.model`][glossary-metamodel],
  [`Meta.fields`][glossary-metafields], [`Meta.exclude`][glossary-metaexclude],
  [`Meta.description`][glossary-metadescription] — the type system every
  read-side item (items 2–4) lands in; `Meta.description` is the precedent
  for how a lazy translation string is accepted.
- [Scalar field conversion][glossary-scalar-field-conversion],
  [Specialized scalar conversions][glossary-specialized-scalar-conversions],
  [Choice enum generation][glossary-choice-enum-generation],
  [`Meta.choice_enum_names`][glossary-metachoice_enum_names] — the converter
  table a `GeneratedField` routes through and the enum pipeline a
  `choices_enum` short-circuits.
- [`Meta.nullable_overrides`][glossary-metanullable_overrides],
  [`Meta.required_overrides`][glossary-metarequired_overrides] — the
  per-field nullability assertions a `GeneratedField` honors like any column.
- [Scalar field override semantics][glossary-scalar-field-override-semantics]
  — the four-corner `consumer_authored_fields` contract whose annotation-only
  corner is the per-field `help_text` opt-out.
- [`DjangoFileType`][glossary-djangofiletype],
  [`DjangoImageType`][glossary-djangoimagetype],
  [`Meta.filesystem_path_fields`][glossary-metafilesystem_path_fields] — the
  file/image output wrappers whose generated resolvers gain a description, the
  one `output_field` family a `GeneratedField` may not carry, and the opt-in
  that therefore never targets a generated column.
- [Relation handling][glossary-relation-handling],
  [`DjangoConnectionField`][glossary-djangoconnectionfield],
  [`Meta.relation_shapes`][glossary-metarelation_shapes] — the forward
  relation fields and the synthesized connection siblings a `help_text`
  also describes.
- [Relay Node integration][glossary-relay-node-integration] — the pk
  suppression the scalar description attach must respect.
- [Input type generation][glossary-input-type-generation],
  [`DjangoMutation`][glossary-djangomutation],
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation],
  [`DjangoFormMutation`][glossary-djangoformmutation],
  [`SerializerMutation`][glossary-serializermutation],
  [Auth mutations][glossary-auth-mutations] — the write flavors the
  `through=` guard protects and the key map already serves.
- [`FieldError` envelope][glossary-fielderror-envelope] — the error contract
  item 5 keys and whose generic `"__all__"` constraint leaf item 1 stops a
  misdeclared through model from reaching.
- [`PaginationArgumentError`][glossary-paginationargumenterror],
  [Production error policy][glossary-production-error-policy],
  [Structural error classification][glossary-structural-error-classification]
  — the rejection item 6 codes, the masking rule it lands outside of, and the
  shape rule (a `GraphQLError` travels untouched) that keeps it readable.
- [`ConfigurationError`][glossary-configurationerror] — the raise type of
  every declaration-time refusal here; the package's fail-loud doctrine puts
  a misdeclared schema at import or schema build, never in a response.
- [Soft dependency][glossary-soft-dependency],
  [Hard dependency][glossary-hard-dependency],
  [`require_optional_module`][glossary-require_optional_module],
  [Eviction-simulated absence][glossary-eviction-simulated-absence] — the
  detection discipline `django-choices-field` joins (in an observation-only
  variant), and the absence idiom its package-tier test reuses.
- [`FilterSet`][glossary-filterset], [`OrderSet`][glossary-orderset],
  [`auto`-typed annotations][glossary-auto-typed-annotations] — surfaces
  that ride the same scalar route (filters/orders over a `GeneratedField`)
  or route through synthesis (an `auto` field still gets its description).
- [Schema introspection management command][glossary-schema-introspection-management-command],
  [Schema export management command][glossary-schema-export-management-command]
  — the inspection label that gains a `GeneratedField` row and the SDL
  export Slice 3's description check runs through.
- [Joint version cut][glossary-joint-version-cut],
  [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  release discipline Slice 5 defers to and the test discipline every slice
  follows.

## Slice checklist

Each top-level item maps to one commit / PR. **Five slices.** The card is an
M: four small builds in four seams plus a verification wrap. No slice depends
on another's code, but Slices 2, 3 and 4 each add a library migration and
migrations chain, so each takes the next free number and depends on
whichever library migration is newest when it is built (Slice 2 took
`examples/fakeshop/apps/library/migrations/0020_shelf_code_length_topic_length.py`,
after `0019_distributor_display_name`). Slice 1 adds no migration and goes first (it is the only item that
changes what a write path accepts); Slice 5 lands last. Each slice rebases
onto whatever card `053` has landed
on the shared seams by then ([Risks](#risks-and-open-questions)).

- [ ] **Slice 1 — The `through=` guard**
  - [ ] `required_through_columns(field)` in
        `django_strawberry_framework/utils/relations.py`, beside
        `django_strawberry_framework/utils/relations.py::m2m_through_link_fields`:
        the through model's concrete columns that are not the two link
        foreign keys, not the auto primary key, not a `GeneratedField`, not a
        `DateField` / `DateTimeField` / `TimeField` with `auto_now` /
        `auto_now_add` (Django's `pre_save` fills them on the bulk insert),
        and that Django cannot otherwise fill on a bare `through(source,
        target)` insert ([Decision 2](#decision-2--the-through-guard-is-a-write-side-predicate-raised-before-any-request)
        defines "required"). The generator
        `django_strawberry_framework/mutations/inputs.py::editable_input_fields`
        gains no through raise (its existing narrowing refusals stay as they
        are).
  - [ ] One shared message formatter (owner label, owning model field,
        through model, columns, three remedies — exclude the relation, give
        the column a default, write the through rows from a consumer-authored
        mutation over the through model) and three raise sites, each over
        the already-narrowed field set: the model flavor in
        `django_strawberry_framework/mutations/sets.py::DjangoMutation._validate_meta`
        over its `selected` list (auth `register` rides it, being a
        `DjangoMutation`); the form flavor in
        `django_strawberry_framework/forms/inputs.py::build_form_input_class`
        over `effective`, skipped when the form class overrides
        `_save_m2m`; the serializer flavor in the build walk,
        `django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields`
        for an input field and
        `django_strawberry_framework/rest_framework/inputs.py::resolve_injected_field_specs`
        for a `Meta.injected_fields` name, over each model-backed
        `RELATION_MULTI` spec
        `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field`
        returns, resolving the column through `source`, skipped when the
        serializer class overrides the `create()` / `update()` the operation
        reaches (never inside `resolve_serializer_field`, which receives
        neither the serializer class nor the operation).
  - [ ] Package tier: rejection over the glossary app's `GlossaryTermLink`
        (required `kind`; its `created_date` / `updated_date` not listed) per
        flavor; acceptance over kanban `CardGlossaryTerm` (every extra
        defaulted, timestamps not listed); the narrowing escape; the override
        skips; an injected-field relation; unmanaged throughs for the
        predicate's edge rows. Live: library
        `Shelf.alt_branches` (auto-created through) still reaches `.set()`
        through `createShelf` and `createShelfViaForm`.
- [ ] **Slice 2 — `GeneratedField`**
  - [ ] `django_strawberry_framework/utils/relations.py::generated_column`
        builds the column a `GeneratedField` computes: a clone of its
        `output_field` bound under the generated field's model, `db_column`
        and name (an `ArrayField` output binds its `base_field` with it),
        carrying the generated field's `choices`, `blank` and `help_text`,
        with `null = GeneratedField.null or output_field.null`; one column is
        filed per field (`dict.setdefault`), so two reads are one object. It
        answers classification reads only: it never builds a query and no
        lookup is read off it, since a clone carries none of the lookups a
        project registers on the `output_field` instance; every lookup is read
        off that instance's registry
        (`django_strawberry_framework/utils/relations.py::lookup_registry`) and
        every walk starts from the generated field's own column
        (`django_strawberry_framework/utils/relations.py::lookup_operand`), and
        `django_strawberry_framework/utils/relations.py::generated_column_source`
        reads the generated field back from the clone.
        `django_strawberry_framework/types/converters.py::generated_output_field`
        is the conversion unwrap over it and owns the three refusals, each a
        `ConfigurationError` whose label (`_field_label` of the bound column)
        names the generated field: a `FileField` / `ImageField` output, an
        output class with no `SCALAR_MAP` ancestor that is no
        `ArrayField` / `HStoreField`, and an `ArrayField` output whose
        `base_field` declares choices
        ([Decision 3](#decision-3--a-generatedfield-converts-through-its-output_field-and-never-enters-a-write-input)).
  - [ ] `django_strawberry_framework/types/converters.py::scalar_route`
        routes a `GeneratedField` first, as its computed column (so an
        `ArrayField` / `HStoreField` output lands in the arm it would land in
        as a plain column; the column carries the outer `choices`, so the map
        arm's `choices` flag needs no re-stamp);
        `django_strawberry_framework/types/converters.py::convert_scalar`
        converts the computed column (nullability, `force_nullable` and the
        choice enum keyed on the generated field's own model and name);
        `django_strawberry_framework/types/converters.py::_scalar_map_entry`
        walks it, so the filter-side
        `django_strawberry_framework/filters/inputs.py::_scalar_from_model_field`
        agrees; `django_strawberry_framework/types/converters.py::_column_admits_empty_string`
        reads the generated field's forced `blank=True` with the output's
        `empty_strings_allowed`. `Meta.required_overrides` asserts non-null.
  - [ ] `django_strawberry_framework/filters/sets.py`:
        `FilterSet._selected_column` names the field django-filter
        classifies, selected off the same merged map upstream's `try_dbfield`
        walks (`FilterSet._merged_filter_defaults`, read through
        `_entry_by_mro`): the `GeneratedField` itself when the merged
        `FILTER_DEFAULTS` plus `Meta.filter_overrides` map holds an entry for
        its class (a consumer override stays reachable), else its computed
        column (upstream's `try_dbfield` walk has no `GeneratedField` row and
        `BaseFilterSet.filter_for_lookup` answers `(None, {})`, after which
        `handle_unrecognized_field` raises). `FilterSet._upstream_filter_for_lookup`
        (which `django_strawberry_framework/filters/base.py::_column_form_field`
        also calls) asks upstream about it, and the ownership oracle
        (`FilterSet._generation_origin_for_field`, the per-field `"__all__"`
        origin read) classifies it; `filter_for_field` runs it through
        `FilterSet._upstream_filter_for_field`'s adapted branch, upstream's
        body over `_generated_filter_field`'s resolution. The class tests
        of `FilterSet.filter_for_lookup` (the text-pattern, choice, integer
        `in` and integer `range` reroutes) and
        `django_strawberry_framework/filters/sets.py::_lookups_for_field` read
        the computed column, so outer choices give the enum filters and two
        generated columns of different output types publish their outputs'
        lookups. `django_strawberry_framework/filters/base.py::_model_resolved_field`
        answers a path naming a `GeneratedField` with its computed column, so
        the input type, the form field that cleans a value and the
        request-time integer guards (`IntegerInFilter`, `IntegerRangeFilter`)
        see the output class; the path still names the generated field.
        `django_strawberry_framework/utils/_array_field.py::array_element_field`
        and `django_strawberry_framework/utils/_array_field.py::array_leaf_field`
        read a `GeneratedField` as its computed column (the filter bind ask
        classifies its leaf by the output class).
  - [ ] Keyset: `django_strawberry_framework/keyset.py::validate_cursor_field_columns`,
        `django_strawberry_framework/keyset.py::cursor_columns_for` and
        `django_strawberry_framework/optimizer/plans.py::effective_cursor_state`
        read a generated cursor column as its computed column (nullable by the
        either-flag rule, JSON by the output class, coded by the output's
        codec).
  - [ ] Identity codec: `django_strawberry_framework/utils/relations.py::stored_value_link`
        answers a reached `GeneratedField` with its computed column, and
        `django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`
        and `django_strawberry_framework/utils/querysets.py::column_python_value`
        (under `identity_key`) cast and prepare through the declared field's
        own `to_python` / `get_db_prep_value` (a consumer key subclass's
        methods hold; Django's `ForeignKey` methods delegate to the column it
        references); a value stored in a `GeneratedField`, whose own methods
        end that delegation as the identity, then codes through the column it
        computes too (`django_strawberry_framework/utils/querysets.py::_value_codecs`),
        so a key subclass's cast and the computed column's both apply.
        So a `relay.NodeID` over a generated column refetches through `node` /
        `nodes` and their reorder, and a key whose `to_field` is a unique
        generated column codes through it too; the storage-domain checks read
        the column `stored_value_column` answers.
  - [ ] The write-side exclusion pinned (Django forces `editable=False`, so
        `django_strawberry_framework/mutations/inputs.py::editable_input_fields`
        already drops it — a test, not code).
  - [ ] `django_strawberry_framework/management/commands/inspect_django_type.py::_scalar_route_label`
        renders `GeneratedField -> <output label>`.
  - [ ] Fixture: two generated columns on library `Shelf` with migration
        `0020_shelf_code_length_topic_length` — `code_length` (`BigIntegerField`
        output over the non-null `code`, so the GraphQL input is `BigInt` and a
        member past 64 bits reaches the package's range guard) and
        `topic_length` (`IntegerField(null=True)` output over a
        `NULLIF(topic, '')` expression), on `ShelfType`'s field list,
        `ShelfFilter` and `ShelfOrder`; live coverage
        (`examples/fakeshop/test_query/test_library_generated_api.py`) reads
        both through an explicit list and a holder `Meta.fields = "__all__"`
        type, filters (flat and through `BookFilter.shelf`) and orders them,
        proves them absent from a holder model mutation that names no field
        list, reads `codeLength` back from an `updateShelfViaForm` payload, and
        types and applies lookups registered on the `output_field` instance.
- [ ] **Slice 3 — `help_text` descriptions**
  - [ ] One `help_text` accessor (falsy → no description; `str` kept as
        text; a lazy `Promise` rendered by `str()` at the attach site; a
        truthy non-text value refused), read at every site below.
  - [ ] Type creation: `django_strawberry_framework/types/base.py`'s
        `DjangoType.__init_subclass__` runs the accessor's refusal over every
        selected column that will receive a synthesized description, so a
        non-text `help_text` fails at class creation.
  - [ ] Output side, Phase 2 of
        `django_strawberry_framework/types/finalizer.py::finalize_django_types`:
        a synthesized scalar gets `strawberry.field(description=...)` only for
        a name `django_strawberry_framework/types/base.py::_build_annotations`
        synthesized (never a consumer-authored name, never the Relay pk
        `django_strawberry_framework/types/base.py::_is_suppressed_relay_pk`
        drops); relations and file/image columns through a `description=`
        parameter on
        `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`
        (whose description skip set is `consumer_authored_fields`, while its
        resolver skip set stays `consumer_assigned_relation_fields`) and
        `django_strawberry_framework/types/resolvers.py::_attach_file_resolvers`.
        Phase 2.5: the synthesized `<field>Connection` sibling in
        `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`
        takes the same column's text
        ([Decision 5](#decision-5--the-description-is-attached-where-each-field-object-is-built)).
  - [ ] Input side, at bind: the model flavor's
        `django_strawberry_framework/mutations/inputs.py::build_mutation_input`
        adds `description` to the per-field kwargs it already builds through
        `django_strawberry_framework/utils/inputs.py::optional_input_field`;
        the form flavor adds it in
        `django_strawberry_framework/forms/inputs.py::build_form_input_class`
        after `optional_input_field` (`_field_triple_and_spec` builds no
        kwargs), from the **form field's** `help_text`, and
        `django_strawberry_framework/forms/inputs.py::_form_basis_content_identity`
        gains the text so two bases differing only in `help_text` do not
        dedupe onto one input; the serializer flavor's
        `django_strawberry_framework/rest_framework/serializer_converter.py::serializer_field_description`
        routes its `help_text` through the same accessor.
  - [ ] A library migration (the next free number) adding a `help_text` to `Shelf.code` and
        to `Book.genres` (no fakeshop relation column carries a `help_text`
        today; `BookType` declares `relation_shapes = {"genres": "both"}`, so
        `Book.genres` publishes both the list field and the
        `genresConnection` sibling); live introspection rows over both, over
        `auth.User.username` (`UserType.username`, `RegisterInput.username`)
        and over an explicit-description override; an `export_schema` SDL
        check.
- [ ] **Slice 4 — `choices_enum` reuse**
  - [ ] `django_strawberry_framework/types/converters.py::convert_choices_to_enum`
        detects a `TextChoicesField` / `IntegerChoicesField` through
        `django_strawberry_framework/utils/imports.py::loaded_attr` (never an
        import) and reuses its `choices_enum`, wrapping with
        `strawberry.enum` only when the class carries no
        `__strawberry_definition__`; the result enters the same
        `(model, field)` registry cache
        ([Decision 6](#decision-6--a-declared-choices_enum-is-reused-through-soft-dependency-detection)).
  - [ ] A package-applied `strawberry.enum` (which decorates the consumer
        class in place) registers its inverse through
        `django_strawberry_framework/registry.py::register_subsystem_clear`,
        so `django_strawberry_framework/registry.py::TypeRegistry.clear`
        removes exactly the definitions the package added and never a
        consumer's own.
  - [ ] The two consumer-enum refusals, each a `ConfigurationError` at type
        creation: a column that admits `""` whose enum has no `""`-valued
        member; a member name that is not publishable as a GraphQL enum value
        (not a GraphQL Name, `__`-prefixed, or exactly `true` / `false` /
        `null`).
  - [ ] `django-choices-field` joins `[dependency-groups].dev` in
        `pyproject.toml` (with `uv.lock`), as the other soft dependencies
        do; **no** `[project.optional-dependencies]` extra.
  - [ ] A library migration (the next free number) adding a `TextChoicesField` column to
        `Shelf`; present-path live coverage over it; absence at package tier
        through `tests/_soft_dependency.py::simulated_absence`.
- [ ] **Slice 5 — Verification, card amendments, docs fold-in, card wrap (no version cut)**
  - [ ] Re-run and re-read the shipped items against the tree: the key-map
        matrix and its three live rows (item 5), the `PAGINATION_INVALID`
        live pin (item 6); add nothing unless a row is missing.
  - [ ] Verify the cross-card rows still hold: card `071`'s
        `CAMELCASE_ERRORS` row and `through_defaults` refusal; card `053`'s
        Slice 5 joint-cut sentence, its GLOSSARY-flip DoD, and its
        dependency edge on this card
        ([Decision 11](#decision-11--board-rows-cross-card-rows-are-verified-the-cards-own-stale-rows-are-amended)).
  - [ ] Amend in the kanban DB, then re-render, each card row
        [Risks](#risks-and-open-questions) names: `CardItem` 1475, 1476,
        1477, 1481, 1482, 1483, 1484, 1491, 1492, 1496, 1500, 1501, 1502 and
        1504 on this card, and the `CardReference` note on each side of the
        `051` / `053` dependency edge (129 on this card, 146 on card `053`);
        append to card `053` the row flagging the SDL-visible `help_text`
        change for its `CHANGELOG.md` bullet; correct [`spec-053`][spec-053]
        Decision 11's "`051` touches every file in this card's WP list except
        `types/converters.py`" clause and its "so it cannot precede them"
        scope (its own Risks entry gates only Slice 5 on this card).
  - [ ] Verify the version triplet reads `0.0.15` and move nothing
        ([Decision 9](#decision-9--joint-0015-cut--this-card-bumps-nothing)).
  - [ ] `docs/GLOSSARY.md` rows via the glossary DB + re-render (new rows
        for the guard, `GeneratedField`, `help_text`, `choices_enum`; **no
        status flips**); append each new anchor to this spec's
        `-terms.csv`, re-run `scripts/check_spec_glossary.py`, then run
        `manage.py import_spec_terms`; `docs/README.md`, `docs/TREE.md`
        regenerated.
  - [ ] Card flip to Done + `KANBAN.md` / `KANBAN.html` regeneration from
        the DB; `scripts/check_kanban_anchors.py` green. **No version triplet
        move, no GLOSSARY status flip, no `CHANGELOG.md` entry.**

## Problem statement

The beta line is defined as feature parity with both upstreams. After the
`0.1.0` parity audit homed every other delta onto an existing card, six
build-side gaps remained with no home: two declarations that fail as written
(`through=` with required extras fails every write that sends the relation a
non-empty list, `GeneratedField` fails type creation), one
whole-schema SDL regression (`help_text`), one duplicate-enum surprise
(`choices_enum`), one mixed error wire format no test could see (`FieldError`
keying), and rejections that read as bugs (`PAGINATION_INVALID`). Two of the
six have since been built under other work; the other four are each a few
dozen lines in one or two seams. Closing them is what makes the parity claim
on card `TODO-ALPHA-057-0.1.0` (the beta cut) true rather than asserted.

## Current state

- **`through=`**: `django_strawberry_framework/mutations/inputs.py::editable_input_fields`
  keeps every forward, editable many-to-many (`is_forward_many_to_many` +
  `editable`), `django_strawberry_framework/mutations/inputs.py::model_column_write_kind`
  classifies it `RELATION_MULTI`, and
  `django_strawberry_framework/mutations/resolvers.py::_assign_m2m` calls
  `.set(keys)` with no `through_defaults`. Django's `.set()` bulk-creates
  `through(source=…, target=…)` rows, so a required extra column raises an
  `IntegrityError` that
  `django_strawberry_framework/mutations/resolvers.py::save_or_field_errors`
  maps to the generic `"__all__"` constraint leaf. The generator is called in
  more places than the input build:
  `django_strawberry_framework/mutations/inputs.py::mutation_input_shape`
  calls it twice (narrowed, then un-narrowed for the full name set),
  `django_strawberry_framework/mutations/sets.py::_expected_input_attr_names`
  (with `fields=` / `exclude=`) and
  `django_strawberry_framework/auth/mutations.py::derive_register_fields`
  (with `fields=`) call it narrowed for validation, and `django_strawberry_framework/mutations/sets.py::DjangoMutation._validate_meta`
  calls it narrowed at class creation, where the mutation's name is known.
  `django_strawberry_framework/utils/relations.py::m2m_through_model`
  and `::m2m_through_link_fields` already resolve the through model and its
  two link fields (honoring `through_fields`); nothing reads the remaining
  columns. The form flavor admits the column through
  `django_strawberry_framework/forms/inputs.py::_model_column_for`, a
  pre-narrowing lookup also used by content-identity hashing,
  `django_strawberry_framework/forms/inputs.py::relation_target_model` and
  the partial-required guards; the input itself is built over the narrowed
  `effective` set in
  `django_strawberry_framework/forms/inputs.py::build_form_input_class`, and
  the write runs `form.save()` / `form.save_m2m()`. The serializer flavor
  writes through `serializer.save()`; DRF's own `get_relation_kwargs`
  makes every custom-through many-to-many `read_only`, so only an explicitly
  declared `PrimaryKeyRelatedField(many=True, queryset=…)` reaches
  `resolve_serializer_field`'s relation arm, and the canonical DRF pattern
  pairs that declaration with an overridden `create()` / `update()`.
  Fakeshop shapes: library `Shelf.alt_branches` and `Book.genres` are
  auto-created throughs, `Shelf.alt_branches` written live by `createShelf`
  and `createShelfViaForm`, `Book.genres` by `updateBookViaForm` and
  `updateBookGenresViaSerializer`; kanban `Card.labels` is auto-created too,
  with no timestamps; every custom through model inherits
  `created_date` (`auto_now_add`) and `updated_date` (`auto_now`) from its
  app's `TimeStampedModel` — kanban `Card.glossary_terms`
  (`CardGlossaryTerm`: `raw_text` and `order` defaulted, unique on
  `(card, order)`), `Card.parity` (`ParityClaim`: required `level` foreign
  key), `Card.changed_files` (`CardPathLink`: `kind` defaulted), glossary
  `GlossaryTerm.related_terms` (`GlossaryTermLink`: required `kind` foreign
  key, `raw_label` and `order` defaulted, unique on
  `(source_term, kind, order)`) and `GlossaryTerm.categories`
  (`GlossaryCategoryMembership`: `order` defaulted, unique on
  `(category, order)`). No generated mutation writes any of the five: the
  kanban surface is plain `DjangoFormMutation`s over services, and the
  glossary app has no mutations — which is why nothing has failed.
- **`GeneratedField`** (built, Slice 2): Django's `GeneratedField.__init__`
  forces `editable=False` and `blank=True` and refuses `default` /
  `db_default`; the class inherits `Field.empty_strings_allowed = True`;
  `contribute_to_class` registers the output field's class lookups on the
  instance; and the schema editor emits the generated clause in place of
  `NULL` / `NOT NULL`, so neither `null` flag is enforced by the database.
  django-filter's `FILTER_DEFAULTS` walk has no `GeneratedField` row. The
  package reads the column it computes
  (`django_strawberry_framework/utils/relations.py::generated_column`,
  refused or admitted by
  `django_strawberry_framework/types/converters.py::generated_output_field`)
  wherever it classifies the column: the scalar route, the filter selection
  and request-time guards, the array helpers and the keyset cursor reads.
  Every write flavor drops it (the `editable=False` branch of
  `editable_input_fields`, a `ModelForm`'s field discovery, DRF's read-only
  mapping). The order side
  (`django_strawberry_framework/orders/inputs.py::_get_concrete_field_names_for_order`)
  requires a real database column, which a generated column is. Library
  `Shelf` declares two (`code_length`, `topic_length`);
  `tests/mutations/test_resolvers.py::LinkedDesk` declares an unmanaged one
  (`db_persist=True`) for the package-tier write-side test.
- **`help_text`**: `django_strawberry_framework/types/base.py::_build_annotations`
  synthesizes bare annotations; no description reaches a generated output
  field. The only description threading is the serializer input side
  (`django_strawberry_framework/rest_framework/serializer_converter.py::serializer_field_description`,
  a bare `str(help_text)` plus a constraint summary) and the `description`
  key `django_strawberry_framework/utils/inputs.py::build_strawberry_input_class`
  reads from each field's kwargs, which the model and form flavors never set.
  `Meta.description` (`django_strawberry_framework/types/base.py::_ValidatedMeta`)
  is the precedent: `str` is kept as text, a `Promise` stays lazy and is
  rendered once by `str()` in Phase 3 of `finalize_django_types`, anything
  else is a `ConfigurationError`. Django accepts `help_text=None` and stores
  it. No fakeshop app model carries a `help_text`, but the schema exposes
  `auth.User.username` (lazy `help_text`) on `UserType` and on
  `RegisterInput` (`examples/fakeshop/apps/accounts/schema.py`), so this
  item changes live SDL the day it lands.
- **`choices_enum`**: `django_strawberry_framework/types/converters.py::convert_choices_to_enum`
  checks the `(model, field_name)` registry cache
  (`django_strawberry_framework/registry.py::TypeRegistry`), then mints an
  enum through `django_strawberry_framework/types/converters.py::build_enum_from_choices`
  (the `BLANK` member when
  `django_strawberry_framework/types/converters.py::_column_admits_empty_string`,
  value sanitization including the Python-`enum` reservation check
  `django_strawberry_framework/types/converters.py::_is_enum_reserved_member`,
  the sanitize-collision guard). `django-choices-field` is not installed and
  nothing in the package names it. Library `Shelf.condition` (a
  blank-admitting `TextChoices` `CharField`, whose enum carries `BLANK`) and
  `Shelf.tier` (`IntegerChoices`) are the stock choice columns.
- **`FieldError` keying** — built. `django_strawberry_framework/utils/errors.py::build_error_key_map`
  is the one key map; `django_strawberry_framework/utils/errors.py::validation_error_to_field_errors`
  takes it (no longer an identity pass-through);
  `django_strawberry_framework/utils/errors.py::relation_field_error` keys
  decode errors; `django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors`
  re-keys recursively through the same map; the model flavor's map comes
  from `django_strawberry_framework/mutations/resolvers.py::_model_error_key_map`.
  `examples/fakeshop/test_query/test_mutation_error_keys_api.py` is the flavor × key-shape matrix, with
  `register` and `ModelForm` through native holder HTTP mounts,
  and the three live rows the DoD names exist in
  `examples/fakeshop/test_query/`. `docs/README.md` documents the contract in
  the `## Writing data` keying paragraph ("There is no casing setting: the
  key is always the input name, and `"__all__"` stays as written").
- **`PAGINATION_INVALID`** — built and ticked. Every
  `PaginationArgumentError` sets `extensions.code` to
  `PAGINATION_INVALID_ERROR_CODE`; the production error policy's table in
  `docs/README.md` lists it among the framework-raised codes that pass the
  masking rule unchanged; the live pin sits in
  `examples/fakeshop/test_query/test_connection_pagination_api.py`. The
  card's `connection.py` / `error_policy.py` file rows belong to this item
  and are spent.
- **Cross-card rows** — present. Card `071`'s upstream-settings disposition
  table carries the `CAMELCASE_ERRORS` row (no toggle; keys are always the
  input name; `__all__` kept) and its write-surface row the
  `through_defaults` refusal, whose migration is "a consumer-authored
  mutation over the through model itself"; card `053`'s Slice 5 sentence
  counts the line ("shared with the other three `0.0.15` cards"), its
  GLOSSARY-flip DoD covers them, and its dependency list carries this card
  (the edge's note repeats the false file-overlap claim; Slice 5 amends it).

## Goals

- A `through=` relation with required extra columns fails before any request
  runs, by name, on the class that would write it; every auto-created or
  fully-filled through is untouched and still reaches `.set()`.
- A `GeneratedField` converts, filters, orders and inspects like the column
  its `output_field` describes, is nullable whenever either field says so,
  and never appears in a write input.
- Every column `help_text` appears as the SDL description of the field the
  package synthesizes for it — output and input alike — with no setting to
  find, an explicit consumer description always winning, and an
  annotation-only override as the per-field opt-out.
- A `choices_enum` publishes once, under the consumer's enum, and the
  package's choice-enum invariants (blank admission, publishable member
  names, the registry cache) still hold for it.
- The two shipped items are verified rather than rebuilt, and the card body
  stops contradicting the tree.

## Non-goals

- **No `through_defaults` support.** A write that supplies through-row
  extras is the refusal homed on card `071`, which stands on the replace-only
  many-to-many contract; this card's guard does not change it. The guard
  turns one failure shape (a required column no insert can fill) into a
  declaration-time refusal; a through that passes the guard can still fail a
  write on a unique set that a constant fill collides on
  ([Edge cases](#edge-cases-and-constraints)), which stays the `"__all__"`
  constraint envelope.
- **No `FIELD_DESCRIPTION_FROM_HELP_TEXT`-style setting**
  ([Decision 4](#decision-4--help_text-is-always-on-no-setting)).
- **No description threading into filter or order inputs.** A
  [`FilterSet`][glossary-filterset] input field is lookup-shaped (`name:
  {exact, in}`); a column `help_text` describes the column, not a lookup
  object. ⚛️ describes a filter argument with the filter's `label`
  ([`graphene_django/filter/utils.py`][upstream-graphene-filter-utils] #"description=filter_field.label"),
  not the column text; 🍓 threads `help_text` into filter types too, under
  its opt-in (`_process_type` in [`strawberry_django/type.py`][upstream-strawberry-type] #"description_from_doc = settings"
  runs over every processed type and has no `is_filter` exclusion). This
  card declines it either way.
- **No reverse-relation descriptions.** Both upstreams describe a reverse
  relation with the forward field's `help_text` (⚛️ unconditionally, 🍓
  under its opt-in; [Borrowing posture](#borrowing-posture)); this package
  does not.
- **No `GeneratedField` write path.** The column is database-computed;
  Django forbids writing it and so does this package.
- **No enum naming changes.** Card `TODO-BETA-065-0.1.4` owns
  `convert_choices_to_enum` naming and the cache on the far side of the beta
  cut; this card lands the reuse behavior that card then names.
- **No version triplet move, no GLOSSARY status flip, no `CHANGELOG.md`
  entry** ([Decision 9](#decision-9--joint-0015-cut--this-card-bumps-nothing)).

## Borrowing posture

Every item was grounded in the named upstream source before any decision was
pinned (the card's `Verified in upstream` list, re-read for this spec):

- 🍓 [`strawberry_django/fields/types.py`][upstream-strawberry-field-types] #"GeneratedField":
  `resolve_model_field_type` maps `type(model_field.output_field)` through the
  field map — adopted as the type-routing rule
  ([Decision 3](#decision-3--a-generatedfield-converts-through-its-output_field-and-never-enters-a-write-input)),
  extended to recurse through the package's own container arms. 🍓's
  read-side nullability (`strawberry_django/fields/base.py`, its
  `field_to_check`) hands `is_optional` the `output_field` of a
  `GeneratedField`, so it reads `output_field.null` alone; this package also
  honors the `GeneratedField`'s own `null`, because the schema editor
  enforces neither and either flag is the consumer saying the expression can
  be null.
  🍓's auto-enum arm, which tests `model_field.choices` (the
  `GeneratedField`'s own) before its `GeneratedField` arm, runs only under
  `GENERATE_ENUMS_FROM_CHOICES` (default `False`) and only when the first
  choice is not an `int`; only its `TextChoicesField` arm is unconditional.
  Where that arm runs, both libraries read the outer field's choices; with
  it off, 🍓 publishes the output field's scalar, so a default-on enum for a
  choice-bearing generated column is this package's existing choice-enum
  rule, not 🍓 parity. ⚛️ has no `GeneratedField` handling at all.
- 🍓 [`strawberry_django/fields/types.py`][upstream-strawberry-field-types] #"TextChoicesField":
  imports `django_choices_field` under `try` / `except`, reuses
  `model_field.choices_enum`, and wraps it with `strawberry.enum` only when
  it carries no `__strawberry_definition__` — adopted
  ([Decision 6](#decision-6--a-declared-choices_enum-is-reused-through-soft-dependency-detection)),
  with the import replaced by the package's `sys.modules`-only detection
  and two refusals applied on top that 🍓 does not apply (a blank-admitting
  column whose enum has no `""` member; an unpublishable member name).
  Accepted widening ([Risks](#risks-and-open-questions)).
- ⚛️ [`graphene_django/converter.py`][upstream-graphene-converter] #"get_django_field_description":
  `str(field.help_text) if field.help_text else None`, threaded
  unconditionally into every converter, forward relations and connections
  included; ⚛️ [`graphene_django/forms/converter.py`][upstream-graphene-form-converter]
  does the same from the form field. 🍓 ships the equivalent behind
  [`strawberry_django/settings.py`][upstream-strawberry-settings] #"FIELD_DESCRIPTION_FROM_HELP_TEXT"
  (default `False`). ⚛️'s always-on shape and falsy test are adopted
  ([Decision 4](#decision-4--help_text-is-always-on-no-setting)); its bare
  `str()` of a truthy non-text value is not (the package refuses, as it does
  for `Meta.description`).
- **Deliberate divergence**: ⚛️ `convert_field_to_list_or_connection` in
  [`graphene_django/converter.py`][upstream-graphene-converter] describes a
  reverse relation with `field.field.help_text`, the forward foreign key's
  text. That text describes the forward side ("the shelf's home branch")
  and reads wrong on the reverse list, so reverse relations here stay
  undescribed. 🍓's `_process_type` in
  [`strawberry_django/type.py`][upstream-strawberry-type] #"f_description = model_attr.field.help_text"
  does the same for a `ManyToOneRel` / `ManyToManyRel` under its opt-in, so
  the divergence is from both upstreams.
- ⚛️ [`graphene_django/settings.py`][upstream-graphene-settings] #"CAMELCASE_ERRORS"
  (default on) with [`graphene_django/types.py`][upstream-graphene-types] #"ErrorType":
  a casing toggle over the key the `FieldError` envelope mirrors. Rejected
  as a shape: an FK suffix (`category` / `categoryId`) and a
  `Meta.input_class` rename have no casing relation, so the shipped fix is a
  key map ([Decision 7](#decision-7--fielderror-keying-is-the-shipped-key-map-contract-no-toggle)).
- **Deliberate divergence on `through=`**: ⚛️ guards nothing and fails inside
  Django's `.set()` as this package does today. 🍓 does not fail there when
  the client supplies the extras: `update_m2m` in
  [`strawberry_django/mutations/resolvers.py`][upstream-strawberry-mutation-resolvers]
  pops a per-row `through_defaults` from each relation input item, builds or
  fetches the through row, sets the extras on it and saves it; without them
  its `im.full_clean()` / `im.save()` hits the same required column. That per-row
  input shape is exactly what card `071` refuses and documents
  (its remedy: a consumer-authored mutation over the through model); the
  guard is the package's own fail-loud doctrine applied to the shape the
  refusal leaves unwritable.

## User-facing API

No new `Meta` key, setting, or export. The consumer-visible changes are:

```python
class Shelf(models.Model):
    code = models.TextField(help_text="Printed on the shelf's end panel.")
    code_length = models.GeneratedField(
        expression=Length("code"), output_field=models.IntegerField(), db_persist=True,
    )
    grade = TextChoicesField(choices_enum=ShelfGrade, default=ShelfGrade.STANDARD)


class ShelfType(DjangoType):
    class Meta:
        model = Shelf
        fields = "__all__"   # no longer raises on code_length
```

- The SDL for `ShelfType.code` (and the create input's `code`) carries
  `"""Printed on the shelf's end panel."""`; a consumer-authored
  `code: str = strawberry.field(description="…")` wins unchanged, and an
  annotation-only `code: str` publishes no description.
- `codeLength: Int!` is read-only: present on the type, filterable and
  orderable, absent from every generated create / update input.
- `grade` publishes the consumer's `ShelfGrade` enum, once.
- A `ManyToManyField(through=Link)` whose `Link` has a required extra column
  raises on the mutation class that would write it — the model flavor at
  class creation, the form and serializer flavors when their input binds,
  before the schema serves a request:

  ```
  ConfigurationError: CreateTerm.Meta.model GlossaryTerm.related_terms is a
  many-to-many through GlossaryTermLink, whose required column(s) 'kind' a
  generated write cannot supply; the package writes a many-to-many with
  .set() and sends no through_defaults. Exclude the relation from this
  mutation (Meta.exclude / Meta.fields), give the column(s) a default, or
  write the through rows from a consumer-authored mutation over
  GlossaryTermLink.
  ```

  (Final wording is pinned by the Slice 1 test; the five facts — owner
  label, owning field, through model, column names, remedies — are the
  contract. The form and serializer flavors name their form / serializer
  class as the owner label. `created_date` / `updated_date` are not listed:
  `pre_save` fills them.)

## Architectural decisions

### Decision 1 — Card scope: six items, one charter; the two shipped items are verified, not rebuilt

**Decision**: the card closes exactly the six audit leftovers. Items 5 and 6
are already in the tree under other work; this card's obligation to them is
a Slice 5 verification pass (re-run the matrix and the live rows, re-read the
docs) and the card-body amendments that stop the Scope prose from
contradicting the code. Anything discovered mid-slice that is not one of the
six is carded separately.

**Alternative rejected**: dropping items 5 and 6 from the card as "done
elsewhere" — the card's DoD rows for them (including the two cross-card
rows) are the only place the parity audit's closure is recorded; the
verification pass is cheap and the audit trail is the point.

### Decision 2 — The `through=` guard is a write-side predicate, raised before any request

**Decision**: a new helper `required_through_columns(field)` in
`django_strawberry_framework/utils/relations.py` (beside
`django_strawberry_framework/utils/relations.py::m2m_through_link_fields`,
which already resolves the two link fields, `through_fields` included)
returns, in declaration order, the through model's concrete columns that are
**required**: not one of the two link foreign keys, not the auto-assigned
primary key, not a `GeneratedField`, not a `DateField` / `DateTimeField` /
`TimeField` with `auto_now` or `auto_now_add` (the bulk insert's
`SQLInsertCompiler.pre_save_val` calls `pre_save(obj, add=True)`, which fills
them), and such that a bare `through(source, target)` insert would fail —
`null=False`, no `default`, no `db_default`, and not a column whose
`empty_strings_allowed` lets Django's `Field._get_default` fill `""` (a
`TextField()` with no default is *not* required: Django inserts `""`; an
`IntegerField(blank=True, null=False)` with no default *is*: `blank` plays no
part, only what the insert can fill). A non-empty result is a
`ConfigurationError` built by one formatter naming the owner label, the
owning model field, the through model, the columns, and the remedies.

The predicate stays out of the generator.
`django_strawberry_framework/mutations/inputs.py::editable_input_fields` is
called un-narrowed by
`django_strawberry_framework/mutations/inputs.py::mutation_input_shape #"editable_input_fields(model, operation_kind=operation_kind)"`
(the full name set), so a raise there would fire for a relation
`Meta.exclude` removed; its narrowed validation callers,
`django_strawberry_framework/mutations/sets.py::_expected_input_attr_names`
(`fields=` / `exclude=`) and
`django_strawberry_framework/auth/mutations.py::derive_register_fields`
(`fields=`), have no mutation name to report. The guard runs at three sites,
each over the already-narrowed set:

- model flavor: `django_strawberry_framework/mutations/sets.py::DjangoMutation._validate_meta`,
  over the `selected` list it already computes at class creation for create
  and update operations — so `Meta.exclude` / `Meta.fields` on the mutation
  is the documented escape, and the message names the mutation class. Auth
  `register` is a `DjangoMutation` and rides the same check.
- form flavor: `django_strawberry_framework/forms/inputs.py::build_form_input_class`,
  over `effective` (never
  `django_strawberry_framework/forms/inputs.py::_model_column_for`, a
  pre-narrowing lookup shared by content-identity hashing, relation-target
  resolution and the partial-required guards). The guard is skipped when the
  form class's `_save_m2m` is not Django's own: a `ModelForm` that overrides
  it writes the relation itself, the form analogue of the DRF pattern below.
  A plain `Form` has no model column and no `.set()` path.
- serializer flavor: the build walk in
  `django_strawberry_framework/rest_framework/inputs.py`, where the
  serializer class and the operation are both known:
  `django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields`
  (`serializer_class=`, `is_partial=`) for an input field and
  `django_strawberry_framework/rest_framework/inputs.py::resolve_injected_field_specs`
  (`serializer_class`, `operation_kind=`) for a `Meta.injected_fields` name,
  each over the model-backed `RELATION_MULTI` spec
  `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field`
  returns, with the column resolved through the field's `source`. The guard
  cannot live inside `resolve_serializer_field`, whose parameters are
  `(field, model, type_name)`: no serializer class, no operation. Only an
  explicit `PrimaryKeyRelatedField(many=True, queryset=…)` reaches the
  relation arm (DRF marks every custom-through many-to-many `read_only`),
  and DRF's documented pattern pairs that declaration with an overridden
  `create()` / `update()`; the guard therefore fires only when the method
  the operation reaches (`create` for a create, `update` for an update) is
  `ModelSerializer`'s own, whose body calls `field.set(value)`. The guard is
  not re-run per request: the runtime serializer is the same
  `Meta.serializer_class` whose `create()` / `update()` the build read, and
  `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`
  (which re-calls `resolve_serializer_field` per request only when
  `spec.required` or `spec.annotation_repr` is set) holds every exposed
  relation to its schema-time `source` and related model on every request,
  so the column written is the column the build checked even when the
  runtime field set differs from `get_serializer_for_schema()`'s; a
  runtime-only field outside that map receives no client value.

The model flavor raises at class creation; the form and serializer flavors
raise when their input binds inside `finalize_django_types`. Both precede the
first request.

**Reconciling the card's wording**: the card says "reject at type creation"
and its DoD "fails at type creation … live coverage proves the runtime
`.set()` path is never reached". The class whose creation the guard belongs
to is the **mutation** that would write the relation; the input type itself
materializes at bind. A `DjangoType` over the same model is read-only
exposure: it has no through row to write, and refusing it would force
`Meta.exclude` on the read side too, hiding a readable relation. A live test
cannot observe an import-time refusal (the fakeshop schema would not load),
so the refusal is pinned at package tier and the live rows prove the
opposite verdict: a stock auto-created through still reaches `.set()`. Both
card rows are amended in Slice 5 ([Risks](#risks-and-open-questions)).

**Why these columns and not others**: Django's `.set()` → `_add_items` →
`through._default_manager.bulk_create(...)` constructs each row from the two
link keys plus `through_defaults` (which this package never sends), then
lets `Field.get_default()` and `pre_save` fill the rest. The predicate is
exactly "what neither can fill". It does **not** cover a filled column that
sits in a unique set (a constant `default` or `""` inside a `UniqueConstraint`
or `unique=True`): whether such a fill collides depends on the default's
kind (a callable such as `uuid4` yields distinct values), on which side of
the relation the set keys (kanban `CardGlossaryTerm`'s `(card, order)` fails
any two-target `.set()`; glossary `GlossaryCategoryMembership`'s
`(category, order)` fails only when a second term joins one category), and
on rows already stored. That collision is data-dependent and stays the
`"__all__"` constraint envelope, which is the envelope's job.

**Alternatives rejected**:

- *Raise at `DjangoType` creation* (the card's literal wording) — refuses
  read-only exposure that works, and `DjangoType` cannot know whether any
  mutation will ever write the relation.
- *Raise inside `editable_input_fields`* — breaks `Meta.exclude` (the
  un-narrowed full-set call raises anyway) and has no mutation name.
- *Leave the request-time `"__all__"` constraint error* — a misdeclared
  schema is a configuration error, not a client error;
  [`ConfigurationError`][glossary-configurationerror] at declaration is the
  package's fail-loud doctrine, and the envelope must not carry a failure
  every write sending the relation a non-empty list would hit, whatever the
  rows hold.
- *Accept a per-row `through_defaults` input* (🍓's `update_m2m` shape) —
  homed as a refusal on card `071`: it makes a relation argument responsible
  for rows in a third table and contradicts the replace-only many-to-many
  contract; a static per-mutation default cannot express per-row data either.
- *Extend the predicate to unique-set collisions* — rejected above: the
  verdict depends on default kind, relation side and stored data, so a
  schema-time rule either over-refuses (callable defaults) or under-refuses
  (target-side sets).
- *The serializer guard inside `resolve_serializer_field`* (beside
  `_reject_relation_cardinality_mismatch`) — the converter receives neither
  the serializer class nor the operation, so it cannot tell which of
  `create()` / `update()` the write reaches or whether it is overridden;
  threading both in would widen a per-field converter that the runtime
  agreement pass also calls, for a check only the build walk needs.
- *Guard only the model flavor* — the form and serializer flavors reach the
  same `.set()` (Django's `_save_m2m()` and `ModelSerializer.create` /
  `update`) when not overridden, so a single-flavor guard leaves two silent
  paths.
- *Guard the form / serializer flavors regardless of overrides* — refuses
  the canonical DRF and Django patterns for writing a custom through, which
  never call `.set()`.

### Decision 3 — A `GeneratedField` converts through its `output_field` and never enters a write input

**Decision**: a `GeneratedField` is read as the column it computes:
`django_strawberry_framework/utils/relations.py::generated_column` clones its
`output_field` (the idiom Django's own `GeneratedField.check` uses to
validate the output) and binds the clone under the generated field's model,
`db_column` and name, carrying the facts below; one clone is filed per field.
It answers classification reads only: it is not in
`Options.concrete_fields`, and a query, ordering or projection names the
generated field by its path. No lookup is read off it: Django's query
resolves a generated column's lookups and transforms on the `output_field`
instance (the `Col` it builds carries that instance), where a project may
register its own (`Field.register_lookup` on an instance), and a clone keeps
only its class's. Every lookup the package reads for a generated column comes
from that one registry
(`django_strawberry_framework/utils/relations.py::lookup_registry`), never from
the copy of the output class's lookups `GeneratedField.contribute_to_class`
files on the generated field. The generated field's own `get_lookup` /
`get_transform` (Django's `RegisterLookupMixin`) fall back to the
`output_field` for a name the copy lacks, so the copy diverges from the query
in two places only: a name a later registration replaces (Django's `Exact` as
`contains`, `Chr` as `endswith`) it answers with the class's original, and its
`get_lookups()` enumeration lists no registration made after the model was
built, on the class or on the `output_field` instance. Every
walk starts from the generated field's own column
(`django_strawberry_framework/utils/relations.py::lookup_operand`, the walk
`validate_lookup_expr` runs from `Field.cached_col`;
`django_strawberry_framework/utils/relations.py::generated_column_source`
reads the generated field back from the clone): the generated leaf's filter
selection (`FilterSet._upstream_filter_for_field` and the ownership oracle
`FilterSet._generation_origin_for_field`, through
`django_strawberry_framework/filters/sets.py::_generated_filter_field`), the
filter operand walk
(`django_strawberry_framework/filters/base.py::_lookup_operand`, which answers
an output that is the `output_field` instance as the computed column), the
text-pattern test of `FilterSet.filter_for_lookup`
(`django_strawberry_framework/filters/sets.py::_is_text_pattern_on_non_text`)
and the target-less GlobalID filter's lookup test
(`django_strawberry_framework/filters/base.py::_unresolved_target_node_id`).
A registration on the `GeneratedField` class or instance reaches neither
those reads nor Django's query: a generated leaf naming it is upstream's
`FieldLookupError` when the set is defined, and a declared filter naming it is
refused at execution as Django refuses `Model.objects.filter(...)` with it.
`django_strawberry_framework/types/converters.py::scalar_route` routes a
`GeneratedField` **first**, as that column — so an `ArrayField` output takes
the array arm, an `HStoreField` output the hstore arm, and any other output
the `SCALAR_MAP` arm keyed on the output field's class (🍓's rule, extended
through the package's container arms). The column carries the generated
field's `choices`, so the map arm's `choices` flag and `convert_scalar`'s
enum (keyed on the generated field's own model and name) need no re-stamp.
`django_strawberry_framework/types/converters.py::_scalar_map_entry` unwraps
the same way, so `django_strawberry_framework/types/converters.py::scalar_for_field`
— and through it the filter-side
`django_strawberry_framework/filters/inputs.py::_scalar_from_model_field` —
resolves a `GeneratedField` to the scalar the selected-field side publishes.
The card names `django_strawberry_framework/types/converters.py::convert_field_output`
as the seam; the arm sits one level down in `scalar_route` because
`convert_field_output` is read-side only and the filter side would otherwise
publish a different scalar.

Facts read off the **`GeneratedField` itself**: `choices` (a
`GeneratedField` that declares choices takes the choice enum like any
column; choices on the `output_field` are a type-carrier detail Django never
validates and are ignored) and `help_text`. Two facts need a rule of their
own, because Django forces or bypasses them:

- **Nullability**: `GeneratedField.null or output_field.null`. The schema
  editor (`BaseDatabaseSchemaEditor._iter_column_sql`) emits the generated
  clause *instead of* `NULL` / `NOT NULL`, so the database enforces neither
  flag; an expression over a nullable column yields `NULL` whatever the
  `GeneratedField` says. Either flag is the consumer's statement that the
  expression can be null; with neither, the SDL is non-null and a `NULL`
  row is a resolver error. `Meta.required_overrides` asserts non-null over a
  nullable declaration; [`Meta.nullable_overrides`][glossary-metanullable_overrides]
  widens a non-null one.
- **Blank admission** for a choice-bearing `GeneratedField`: Django forces
  `blank=True` and the class inherits `empty_strings_allowed = True`, so
  `django_strawberry_framework/types/converters.py::_column_admits_empty_string`
  read off the `GeneratedField` would mint a `BLANK` member even for an
  integer output. It reads the computed column, whose `blank` is the forced
  `True` and whose `empty_strings_allowed` is the output class's: a text
  expression can compute `""`, an integer one cannot.

`django_strawberry_framework/types/converters.py::generated_output_field`,
the conversion unwrap every type-side and filter-side read goes through,
owns three refusals, each a `ConfigurationError` at type or `FilterSet`
creation labelled with the **outer** field (the computed column is bound
under its model and name, so
`django_strawberry_framework/types/converters.py::_field_label` of the
column reads `Model.<generated field>`, where the raw `output_field` would
read `<unbound>.None`): a `FileField` /
`ImageField` output (the file
wrappers resolve storage-backed values and a database expression has none;
the refusal sits in the unwrap so the filter side cannot publish `String`
for it, and `Meta.filesystem_path_fields` therefore never sees a generated
column — its validator's non-file refusal would name it too); an output
class with no `SCALAR_MAP` ancestor; and an `ArrayField` output whose
`base_field` declares choices (choices on the output, its `base_field`'s
included, are a detail Django never validates or reads for the generated
column, and outer choices on an array are refused by `convert_scalar`
already, so a generated array has no enum). The refusals are re-read on
every call, so a `SCALAR_MAP` entry registered later is seen. The order side needs nothing (a generated column is a real column).
`django_strawberry_framework/management/commands/inspect_django_type.py::_scalar_route_label`
renders `GeneratedField -> <label of the output route>`.

The filter side selects off the same merged map upstream's `try_dbfield`
walks (`FilterSet._merged_filter_defaults`, read through `_entry_by_mro`):
`django_strawberry_framework/filters/sets.py::FilterSet._selected_column`
answers the `GeneratedField` itself when the merged `FILTER_DEFAULTS` plus
`Meta.filter_overrides` map holds an entry for its class (a consumer's
`filter_overrides[GeneratedField]` is reached as written), else its computed
column, the one upstream's `try_dbfield` walk can classify (it has no
`GeneratedField` row, so `BaseFilterSet.filter_for_lookup` answers
`(None, {})` and `handle_unrecognized_field` raises). `FilterSet._upstream_filter_for_lookup`
asks upstream about that field and the ownership oracle classifies the same
one, so they cannot disagree. Upstream's `filter_for_field` body runs for a
`GeneratedField` with one change (`FilterSet._upstream_filter_for_field`,
adapted from django-filter): the field and terminal lookup it hands
`filter_for_lookup` come from
`django_strawberry_framework/filters/sets.py::_generated_filter_field`, the
`resolve_field` answer walked on the registry Django's query reads, which is
the `GeneratedField` itself for a lookup on the computed column and the
transform's output past a transform. The class tests of
`FilterSet.filter_for_lookup` and
`django_strawberry_framework/filters/sets.py::_lookups_for_field`
(`_is_text_column`, `_without_foreign_postgres_lookups`) read the computed
column, so a choice-bearing generated column gets the enum filters a choice
column gets (`exact` is `EnumChoiceFilter`, never django-filter's
empty-value skip that would widen `BLANK` to every row). Its per-field
`"__all__"` set is read off the `output_field` instance's registry
(`django_strawberry_framework/utils/relations.py::lookup_registry`), where
Django's query resolves a generated column's lookups (`GeneratedField.cached_col`
hands the query a `Col` over it): an instance registration there and a class
registration made after the model was built both publish, which the
`get_lookups()` of the copy `contribute_to_class` files on the generated field
would miss, and two
generated columns of different output types publish their own sets. At
request time `django_strawberry_framework/filters/base.py::_model_resolved_field`
answers a path naming a `GeneratedField` with its computed column, so the
input type, the form field cleaning a value and the integer `in` / `range`
range guards read the output class, while the predicate still names the
generated field and a transform between the column and the lookup is
resolved on the `output_field` instance's registry (a `Chr` registered there,
under a new name or one the generated field's copy holds, types its operand
`String`). The array helpers
(`django_strawberry_framework/utils/_array_field.py::array_element_field`,
`django_strawberry_framework/utils/_array_field.py::array_leaf_field`) read
it the same way, so the filter bind ask classifies its leaf by the output
class, and the keyset cursor reads
(`django_strawberry_framework/keyset.py::validate_cursor_field_columns`,
`django_strawberry_framework/keyset.py::cursor_columns_for`,
`django_strawberry_framework/optimizer/plans.py::effective_cursor_state`)
hold a generated cursor column to the either-flag nullability and code it
with the output's codec. The identity codec reads it too:
`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`
and `identity_key` cast through the declared field's own codec and, for a
value stored in a generated column, then through its computed column
(`django_strawberry_framework/utils/querysets.py::_value_codecs`;
`django_strawberry_framework/utils/relations.py::stored_value_link` answers a
generated column with its computed column for the storage-domain checks), so
for a `relay.NodeID` over a
generated column a decoded id `"2"` is the integer the rows hold and one
past the column's range names no row. Any error names the outer field.

The write side changes nothing and pins everything: Django's
`GeneratedField.__init__` forces `editable=False`, so
`django_strawberry_framework/mutations/inputs.py::editable_input_fields`,
the form flavor (a `ModelForm` never builds a field for a non-editable
column) and the serializer flavor (DRF marks it `read_only`) all already
exclude it. Slice 2 adds the tests that would catch a regression on each
flavor; `tests/mutations/test_resolvers.py::LinkedDesk` is the existing
unmanaged fixture. Whether a saved instance carries the recomputed value
after an update depends on the backend and the Django version (the installed
6.1 `Model._save_table` returns it through `RETURNING` where supported and
otherwise defers it so the next read queries it); the live update-then-read
row pins that the payload is current on every supported cell.

**Alternatives rejected**:

- *A `SCALAR_MAP` row for `GeneratedField`* — there is no single scalar; the
  row would have to be a sentinel the map walk special-cases, which is the
  arm by another name with the filter side left behind.
- *The arm in `convert_field_output`* (the card's seam) — the filter side
  reads `scalar_for_field`, not the read-output entry point, and would
  publish a different scalar.
- *Nullability from one flag alone* (🍓 reads `output_field.null` only) —
  the database enforces neither, and a consumer who wrote
  `GeneratedField(null=True)` or `output_field=IntegerField(null=True)` has
  said the expression can be null.
- *Unwrapping in `filter_for_field`* — the override would hide a consumer's
  `Meta.filter_overrides[GeneratedField]`; selecting off the merged map
  upstream's `try_dbfield` walks, and taking the computed column only where
  that map has no entry for the `GeneratedField`'s class, keeps it reachable.
- *Nullability always on* — makes every generated column optional in the
  SDL, though most expressions over non-null columns cannot be null; the
  declared flags carry the information.
- *Honoring `output_field.choices`* — Django does not validate them and
  never consults them for the generated column; publishing an enum the
  database does not enforce would be a lie in the SDL.
- *Allowing a file `output_field` and resolving it as a bare path string* —
  silently degrades a wrapper type the rest of the schema publishes as
  `DjangoFileType`; refuse loud, the consumer can expose the path through
  a plain annotated column of their own.

### Decision 4 — `help_text` is always on; no setting

**Decision**: a column `help_text` becomes the GraphQL description of every
field the package synthesizes for that column, unconditionally. There is no
`DJANGO_STRAWBERRY_FRAMEWORK` key for it. The precedence is: an explicit
description on a consumer-authored field (a `strawberry.field(description=…)`
assignment or a `@strawberry.field` resolver) is untouched by the package; an
annotation-only override (`code: str`) is consumer-authored too and gets no
description — the per-field opt-out ([Scalar field override
semantics][glossary-scalar-field-override-semantics]); an
[`auto`-typed annotation][glossary-auto-typed-annotations] routes through
synthesis and therefore gets the `help_text`; a package-synthesized field
gets the `help_text` or nothing.

Value handling, in one accessor read by every site: a falsy value (`""`,
`None` — Django accepts and stores `help_text=None`, so a third-party model
may carry it) is no description (⚛️'s `if field.help_text`); a `str` (any
subclass, read as plain text through
`django_strawberry_framework/utils/truth.py::text`) is kept; a lazy
translation `Promise` is rendered by `str()` at the site that builds the
field object, in the active language of the `finalize_django_types` call
that builds it (graphql-core's `GraphQLField` refuses a non-`str`
description, so nothing lazy may reach Strawberry); a truthy non-text value
is a `ConfigurationError` naming the column. The refusal fires at class
creation: `DjangoType.__init_subclass__` in
`django_strawberry_framework/types/base.py` runs the accessor over every
selected column that will receive a synthesized description (a
consumer-authored name is skipped, so the annotation-only override is also
the escape from the refusal); an input build over a column no type selects
reaches the same accessor and raises the same error at bind.

**Rationale**: ⚛️ threads it unconditionally and a ⚛️ migrant otherwise takes
a silent whole-schema SDL regression on every documented model; a setting
whose only sane value is "on" is the preemptive-settings anti-pattern
`AGENTS.md` names; and the package already treats the model as the source
of truth for everything else the SDL says about a column (type, nullability,
choices). An opt-in would protect an installed base's existing SDL; this
package has no such base to protect before the beta cut. The change is SDL-visible on any
schema exposing a documented column, `auth.User.username` included, so card
`053`'s `CHANGELOG.md` entry names it (Slice 5 cross-card row).

**Alternatives rejected**: 🍓's `FIELD_DESCRIPTION_FROM_HELP_TEXT` opt-in
(a knob with one right value); ⚛️'s bare `str()` of whatever `help_text`
holds (a truthy non-text value would publish its `repr`); refusing `None`
(a third-party model's `help_text=None` would fail the consumer's import
with no opt-out); opt-out per type through a new `Meta` key (no use case
was named; the annotation-only override already opts a field out).

### Decision 5 — The description is attached where each field object is built

**Decision**: each description attaches in the window where the package
already builds that field object, never by editing Strawberry's definition
after Phase 3:

- **Phase 2** of `django_strawberry_framework/types/finalizer.py::finalize_django_types`
  (output scalars, relations, file/image columns). For a scalar column the
  package sets `strawberry.field(description=…)` beside the synthesized
  annotation, only for a name
  `django_strawberry_framework/types/base.py::_build_annotations`
  synthesized: never a consumer-authored name, and never a Relay-Node type's
  pk, which `django_strawberry_framework/types/base.py::_is_suppressed_relay_pk`
  drops in favor of the `id` the [Relay Node integration][glossary-relay-node-integration]
  supplies (assigning a field object there would re-publish the suppressed
  column). For a forward relation and a file/image column the existing
  attachers `django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`
  and `django_strawberry_framework/types/resolvers.py::_attach_file_resolvers`
  grow a per-field `description=` they pass into the `strawberry.field(...)`
  they already construct. The relation attacher keeps
  `consumer_assigned_relation_fields` as its *resolver* skip set (an
  annotation-only relation override still gets the package resolver) and
  uses `consumer_authored_fields` as its *description* skip set, so the
  annotation-only opt-out behaves the same on relations as on scalars.
- **Phase 2.5**: the synthesized `<field>Connection` sibling
  ([`Meta.relation_shapes`][glossary-metarelation_shapes]) in
  `django_strawberry_framework/types/finalizer.py::_synthesize_relation_connections`
  takes the same column's text under the same skip set.
- **Bind** (the input builders): the model flavor's
  `django_strawberry_framework/mutations/inputs.py::build_mutation_input`
  adds `description` to the kwargs
  `django_strawberry_framework/utils/inputs.py::optional_input_field`
  returns, which `django_strawberry_framework/utils/inputs.py::build_strawberry_input_class`
  already reads; the form flavor does the same in
  `django_strawberry_framework/forms/inputs.py::build_form_input_class`
  after `optional_input_field` (its
  `django_strawberry_framework/forms/inputs.py::_field_triple_and_spec`
  builds no kwargs) from the **form field's** `help_text` (⚛️'s rule: a
  `ModelForm` copies the column's text onto its field, and a plain `Form`
  field's own `help_text` is the only text it has), and
  `django_strawberry_framework/forms/inputs.py::_form_basis_content_identity`
  includes the rendered text so the per-shape build cache never dedupes two
  bases whose descriptions differ. The serializer flavor's
  `django_strawberry_framework/rest_framework/serializer_converter.py::serializer_field_description`
  replaces its bare `str(help_text)` with the shared accessor; its
  constraint summary stays a serializer-only extra.

Reverse relations get no description ([Borrowing posture](#borrowing-posture)).
The skip sets are the existing ones, so consumer precedence costs no new
bookkeeping: `django_strawberry_framework/types/base.py::_consumer_assigned_fields`
is computed at `__init_subclass__`, before Phase 2 runs, and never sees the
package's own assignments. The inspection command keeps reading
`origin.__annotations__` for synthesized fields; the description is
Strawberry metadata, not a type change.

**Alternatives rejected**:

- *Keep the `Promise` lazy until Phase 3, like `Meta.description`* — the
  field objects are built in Phase 2, 2.5 and at bind, and graphql-core
  refuses a non-`str` description; rendering at each build site is the only
  point that exists.
- *A new `DjangoTypeDefinition` slot carrying per-field descriptions* —
  one more thing the finalizer and the inspection command must agree on,
  for data each build site can read straight off the column.
- *Rewriting `__strawberry_definition__.fields[].description` after
  Phase 3* — edits Strawberry's frozen definition; the attach windows exist
  precisely so the package never does that.
- *Threading the description through `_build_annotations` at class
  creation* — a bare annotation has nowhere to carry text; the field object
  must exist, and the package deliberately creates field objects only in
  Phase 2.
- *Reusing the resolver skip set for relation descriptions* — an
  annotation-only relation override would publish the column text while
  the same override on a scalar publishes none.

### Decision 6 — A declared `choices_enum` is reused through soft-dependency detection

**Decision**: `django_strawberry_framework/types/converters.py::convert_choices_to_enum`
checks, after the cache and before minting, whether the column is a
`django_choices_field` `TextChoicesField` / `IntegerChoicesField`. Detection
is `django_strawberry_framework/utils/imports.py::loaded_attr` (a
`sys.modules`-only read that never imports) for each class name, then
`django_strawberry_framework/utils/truth.py::is_instance`; when
`django-choices-field` is not loaded the branch is dead and nothing changes.
On a hit the field's `choices_enum` is the enum: wrapped with
`strawberry.enum` when it carries no `__strawberry_definition__` (🍓's rule;
a consumer who already decorated it keeps their name and description), then
registered in the same `(model, field_name)` cache through
`django_strawberry_framework/registry.py::TypeRegistry` so sibling types see
one enum and the card-`065` cache contract is unchanged.

`strawberry.enum` decorates the consumer's class **in place**, so a
package-applied definition would survive `TypeRegistry.clear()` and a rebuild
would read it as consumer decoration. The wrap therefore records each class
it decorated, with the definition object it set, and registers one teardown
through `django_strawberry_framework/registry.py::register_subsystem_clear`
that deletes `__strawberry_definition__` from exactly those classes when the
attribute is still that recorded object — never a definition the consumer
applied or re-applied.

Two package refusals apply on top of 🍓, each a `ConfigurationError` at type
creation naming the column and the enum:

- a column that admits `""`
  (`django_strawberry_framework/types/converters.py::_column_admits_empty_string`)
  whose enum has no `""`-valued member — the generated path would have
  minted a `BLANK` member, and a consumer enum cannot be extended without
  publishing something the consumer did not declare;
- a member name GraphQL cannot publish as an enum value: not a GraphQL Name
  (`[_A-Za-z][_0-9A-Za-z]*`; a Python identifier may carry non-ASCII
  letters), `__`-prefixed (reserved for introspection), or exactly `true`,
  `false` or `null` (the spellings the GraphQL grammar excludes, as
  graphql-core's `assert_enum_value_name` refuses them; the generated path
  asks the same check through
  `django_strawberry_framework/types/converters.py::_graphql_refuses_enum_value`).
  The generated path renames
  such members; a consumer enum cannot be renamed, so it is refused.
  `django_strawberry_framework/types/converters.py::_is_enum_reserved_member`
  is not reused: it tests the names Python's `enum` reserves, which a built
  `Enum` class can never contain as members.

The serializer-side
`django_strawberry_framework/rest_framework/serializer_converter.py::_serializer_choice_enum`
is untouched: a DRF `ChoiceField` carries choices, not a `choices_enum`, and
its name-keyed cache is a documented separate key space (`spec-053`
Decision 8).

`django-choices-field` joins `[dependency-groups].dev` in `pyproject.toml`
(and `uv.lock`) beside the other soft dependencies, with a comment naming
the present-path tests it serves; it never enters `[project].dependencies`,
gets no `require_optional_module` guard (there is nothing to require —
absence is the plain generated path, not an error), and gets **no**
`[project.optional-dependencies]` extra: a consumer has the package installed
by the time a model declares the field, so an extra would advertise an
install the package never needs, and card `053`'s four-extra count stands.

**Alternatives rejected**:

- *`import django_choices_field` under `try` / `except` at module load*
  (🍓's shape) — the package's soft-dependency doctrine forbids importing an
  optional package the consumer did not reach for; `loaded_attr` observes
  what the consumer already imported to declare the field.
- *Minting the package's enum and publishing both* — the duplicate-enum
  surprise is the gap.
- *Letting the consumer enum through without the blank check* (🍓) — a
  `TextChoicesField(blank=True)` whose enum lacks a `""` member would read
  `""` rows as a value the SDL does not admit; fail loud at type creation.
- *Running `_is_enum_reserved_member` over the consumer members* — dead
  under the coverage gate (no built enum can trip it) and blind to the names
  GraphQL actually refuses.
- *Leaving the package-applied `strawberry.enum` in place across
  `registry.clear()`* — the next build cannot tell package from consumer
  decoration, and a leaked artifact is the order-dependence the registry's
  teardown contract exists to prevent.
- *Adding a `choices` extra* — see above.
- *Resolving GraphQL name collisions between a consumer enum and a generated
  one* — card `065` owns naming; a collision is Strawberry's own duplicate
  type error today and stays so.

### Decision 7 — `FieldError` keying is the shipped key-map contract; no toggle

**Decision** (built): every flavor keys a `FieldError` to the GraphQL input
field the client sent, through
`django_strawberry_framework/utils/errors.py::build_error_key_map`: a
forward key reports as `categoryId` whether the validator says `category`
or `category_id`, a multi-word `house_code` as `houseCode`, a
`Meta.input_class` rename as the renamed field; a non-field error is
`"__all__"` with an empty `path`; a name the input does not expose keeps
its validator-side name; a dotted name arrives verbatim with `path` split
at the dots. There is no casing setting. This spec pins the contract as the
answer to the card's open item; the card's Scope row already describes the
shipped key map, its matrix and its live rows, so Slice 5 re-reads it and
amends nothing.

**Alternative rejected**: ⚛️'s `CAMELCASE_ERRORS` toggle — a casing
function cannot express the FK-suffix or rename cases; a key map can, and a
toggle over it would be a second wire format for one envelope.

### Decision 8 — Pagination rejections carry `PAGINATION_INVALID` (shipped)

**Decision** (built, ticked on the card): every
`django_strawberry_framework/utils/connections.py::PaginationArgumentError`
carries `extensions.code = "PAGINATION_INVALID"`
(`django_strawberry_framework/utils/errors.py::PAGINATION_INVALID_ERROR_CODE`),
listed in the production error policy's pass-through table; as a
`GraphQLError` it passes the [structural error
classification][glossary-structural-error-classification] untouched. Card
`057`'s open question is closed against this card. Slice 5 re-reads the live
pin and the policy row; no code.

### Decision 9 — Joint `0.0.15` cut — this card bumps nothing

This card shares `0.0.15` with cards `050` (Done), `052`
([`spec-052`][spec-052]) and `053` ([`spec-053`][spec-053]), so the line is a
[joint version cut][glossary-joint-version-cut] and the **last** card to
land owns the bump. That is card `053`, by its own declared dependency on
this card and on `052` (`spec-053` Decision 11); its Risks entry gates its
Slice 5 on both. The
version triplet (`django_strawberry_framework/__init__.py::__version__`,
`tests/base/test_init.py`, the GLOSSARY package-version row) already reads
`0.0.15` for the open line; this card's Slice 5 verifies it and moves
nothing, writes no `CHANGELOG.md` entry, and flips no GLOSSARY status. New
rows this card adds carry the planned-for-`0.0.15` status: card `050`
flipped its own rows to `shipped (0.0.15)` at its wrap, but `spec-053`'s
Slice 5 DoD already owns the flip for every row on the line that does not
yet read shipped, and the flip belongs to the cut that releases the version,
so a second owner here would only make the flip order-dependent.

**Alternative rejected**: cutting `0.0.15` here — would leave `052` and
`053` shipping under a version already released, the exact failure the
joint-cut rule exists to prevent.

### Decision 10 — TODO anchors stage the unbuilt slices

Per the repo's staging discipline, a staged-but-unbuilt slice carries
`TODO(spec-051 slice N)` source anchors at the sites it will change, removed
in the change that ships the slice. This authoring pass modifies no source
file, so none are placed by the spec; the builder places them in a slice's
first commit when the slice lands in more than one, and omits them when the
slice lands whole. The sites are named in the
[Slice checklist](#slice-checklist).

### Decision 11 — Board rows: cross-card rows are verified, the card's own stale rows are amended

The card's DoD owes two rows on other cards: card `071`'s `CAMELCASE_ERRORS`
disposition row and card `053`'s amended Slice 5 sentence, GLOSSARY-flip DoD
and dependency edge. Both are already on the board (placed at the
2026-08-29 board review, the date this card's own DoD row records). Slice 5
re-reads them against the final shape of this card and edits only on a
mismatch; the dependency edge's note is one (its file-overlap claim is
false; [Risks](#risks-and-open-questions)).

This spec also departs from the card's own text in named places (the guard's
raise point and its live proof, the `GeneratedField` seam, nullability rule
and escapes, the `help_text` scope, the `choices_enum` refusals, the
"cannot work around" framing of the why-it-matters row, the files-touched
rows, the sequencing notes, the spec path). Each departure is a scheduled
amendment of a named `CardItem` or `CardReference`, listed with its reason
in [Risks](#risks-and-open-questions) and owed by Slice 5 and the DoD; none
is left for the spec to reinterpret silently. Card `053` gains one row
flagging the SDL-visible `help_text` change for its `CHANGELOG.md` bullet,
and `spec-053` Decision 11's file-overlap clause and "cannot precede them"
scope are corrected. Every card-body
edit is made in the kanban DB and re-rendered, never in the generated
exports.

## Implementation plan

| Slice | Seam | Change | Risk profile |
|---|---|---|---|
| 1 | `utils/relations.py`, `mutations/sets.py`, `forms/inputs.py`, `rest_framework/inputs.py` | one predicate, one formatter, three raise sites, two override checks | MEDIUM — three flavors with different raise moments; the override checks decide which canonical patterns stay legal |
| 2 | `utils/relations.py`, `types/converters.py`, `filters/sets.py`, `filters/base.py`, `utils/_array_field.py`, `keyset.py`, `optimizer/plans.py`, `utils/querysets.py`, `management/commands/inspect_django_type.py`, library models + migration | one computed column per generated field, a conversion unwrap with three refusals, the filter column selected off upstream's merged `try_dbfield` map and output-class reads, the request-time and keyset reads, a label row, two fixture columns | MEDIUM — the filter side has its own field-class dispatch that the scalar route does not reach |
| 3 | `types/base.py`, `types/finalizer.py`, `types/resolvers.py`, `mutations/inputs.py`, `forms/inputs.py`, `rest_framework/serializer_converter.py`, library models + migration | one accessor, a type-creation check, `description=` threaded into the Phase-2 attachers, the Phase-2.5 sibling and three input builders | MEDIUM — the scalar `strawberry.field(description=…)` assignment is the one new shape, and live SDL changes ([Risks](#risks-and-open-questions)) |
| 4 | `types/converters.py`, `pyproject.toml` / `uv.lock`, library models + migration | a detection branch, two refusals, a registry teardown, a dev pin, a fixture column | LOW — dead branch when the package is absent |
| 5 | docs, DB, board, `spec-053` | verification, card amendments, fold-in | mechanical |

Parameterize-don't-average obligations:

- Slice 1: the three flavors share the formatter and the predicate; what
  differs (how the column is found — the mutation's `selected` list, the
  `ModelForm`'s `effective` set, the serializer field's `source`; which
  override exempts it — none, `_save_m2m`, `create` / `update`) stays at
  each call site.
- Slice 2: the scalar route, the scalar-map walk, the filter selection and
  the request-time filter reads read one conversion unwrap
  (`generated_output_field`) over one computed column (`generated_column`,
  which the array helpers and the keyset reads take directly); the label rule
  (outer field) is part of the column.
- Slice 3: the scalar / relation / file / connection attachers and the three
  input builders read one `help_text` accessor; the sites differ only in
  which `strawberry.field(...)` or kwargs dict receives it.
- Slice 4: the `BLANK`-admission rule is the same predicate the generated
  path uses (`_column_admits_empty_string`); the consumer path checks it
  instead of acting on it.

## Helper-reuse obligations (DRY)

New helpers this card introduces become canonical owners; the executing
slices retarget every call site, not just the ones named here:
`required_through_columns` (`django_strawberry_framework/utils/relations.py`),
the through-guard message formatter (one home, three callers), the
`help_text` accessor (one reader of the column text with the falsy / `str` /
`Promise` / refuse rule, consumed by the type-creation check, the Phase-2
attachers, the Phase-2.5 sibling and all three input builders), the
`GeneratedField` computed column (`utils/relations.py::generated_column`) and
its conversion unwrap (`types/converters.py::generated_output_field`, read by
`scalar_route`, `convert_scalar`, `_scalar_map_entry`,
`_column_admits_empty_string`, `filters/sets.py` and `filters/base.py`,
never re-spelled), and the consumer-enum member-name
validator. Existing owners that must not be duplicated:
`django_strawberry_framework/utils/relations.py::m2m_through_link_fields`
(the link-field resolution), `django_strawberry_framework/utils/imports.py::loaded_attr`
(the no-import detection), `django_strawberry_framework/types/converters.py::_column_admits_empty_string`
(the blank-admission rule), `django_strawberry_framework/registry.py::register_subsystem_clear`
(the teardown hook), `django_strawberry_framework/utils/inputs.py::optional_input_field`
(the per-field kwargs the input-side description joins).

## Edge cases and constraints

- **A relation the mutation narrows away** — the model flavor's guard runs
  over `selected`, so `Meta.exclude = ["related_terms"]` builds without
  raising, and a `Meta.fields` list that omits it never consults the through
  model.
- **Timestamped throughs** — `auto_now` / `auto_now_add` columns are filled
  by `pre_save` on the bulk insert and never listed; every custom kanban
  and glossary through carries both (the auto-created `Card.labels` through
  carries neither and needs neither).
- **Through model with a required column that is itself a `GeneratedField`
  or has a `db_default`** — not required; the database fills it. The
  predicate reads `db_default` as a default.
- **A through model whose extra column is a required `ForeignKey`** (the
  glossary `GlossaryTermLink.kind` and kanban `ParityClaim.level` shape) —
  required; a foreign key column has no `empty_strings_allowed`.
- **`TextField()` with no default on the through** — not required (Django
  fills `""`); **`IntegerField(blank=True, null=False)` with no default** —
  required (`blank` plays no part).
- **A filled column inside a unique set** (kanban `CardGlossaryTerm`'s
  `(card, order)`, glossary `GlossaryCategoryMembership`'s
  `(category, order)`, a `unique=True` text column filled with `""`) — not
  covered; a colliding write is the `"__all__"` constraint envelope
  ([Decision 2](#decision-2--the-through-guard-is-a-write-side-predicate-raised-before-any-request)).
- **A consumer field whose own `pre_save` fills it** — not recognized (only
  the `auto_now` family is); the guard lists it, and a `default=` clears it.
- **Symmetrical self-referential through** (Django no longer restricts
  symmetrical intermediate models; verified on the installed Django 6.1.2)
  — a required extra on it is
  refused like any other; `.set()` would insert both directions without it.
- **`through_fields` with a third foreign key to the same model** —
  `m2m_through_link_fields` resolves the two named link fields, so the third
  foreign key is an extra column and is counted when required.
- **A `ModelForm` overriding `_save_m2m`, a serializer overriding the
  `create()` / `update()` its operation reaches** — the guard does not fire;
  the override owns the through rows.
- **A through relation named in a serializer mutation's `Meta.injected_fields`**
  — guarded like an input field (`resolve_injected_field_specs`); the
  injected value reaches the same `.set()`.
- **The read-side `DjangoType`** over the same model is never refused
  (Decision 2); its relation field and connection sibling work as today.
- **`GeneratedField` over a nullable source with neither `null` flag** —
  publishes non-null; a `NULL` row is a resolver error. The consumer
  declares `null=True` on either field (or `Meta.nullable_overrides`).
- **`GeneratedField` with `null=True` or `output_field.null=True`** —
  publishes the optional scalar; `Meta.required_overrides` asserts non-null.
- **Choice-bearing `GeneratedField`** — the enum comes from the outer
  `choices`; `BLANK` only for a text-like output (`empty_strings_allowed`),
  never for an integer one, despite Django's forced `blank=True`.
- **`GeneratedField` with a file / image `output_field`, an unsupported
  output class, or an `ArrayField` output whose `base_field` has choices** —
  refused at type creation, labelled with the outer field; the refusal is in
  the shared unwrap, so the filter side refuses it too.
- **Two `GeneratedField`s of different output types in one `FilterSet` with
  `"__all__"`** — each gets its own output class's lookups.
- **A lookup or transform registered on a `GeneratedField`'s `output_field`
  instance** — reached as Django's query reaches it: the leaf's operand is the
  transform's output (`Chr` publishes `String`), a text pattern publishes
  `String`, and a target-less GlobalID filter codes its node id through the
  column; one registered only on the `GeneratedField` is upstream's
  `FieldLookupError` for a generated leaf when the set is defined, and a
  declared filter naming it builds and is refused at execution by Django.
- **A mutation payload read after an update of a generated column's source**
  — carries the recomputed value whether the backend refreshed it through
  `RETURNING` or deferred it.
- **`GeneratedField` whose `output_field` is a consumer `SCALAR_MAP`
  subclass** — the recursive route walks the output field's MRO exactly as
  a plain column's.
- **`GeneratedField` in [`Meta.nullable_overrides`][glossary-metanullable_overrides]**
  — applies as to any column. `convert_scalar` computes `effective_null`
  from the `force_nullable` tri-state before it calls `scalar_route`; for a
  `GeneratedField` the either-flag rule (`GeneratedField.null or
  output_field.null`) takes the place of `field.null` only when
  `force_nullable` is `None`, and an override replaces the rule's result
  outright, so the order of the two reads does not matter.
- **`help_text` on a column the consumer re-annotates** (`code: str`, or a
  relation `items: list["AdminItemType"]`) — consumer-authored; no
  description on either kind, and the type-creation refusal skips it.
- **`help_text` on a Relay-Node type's pk** — the pk is suppressed in favor
  of the Node `id`; no field object is attached for it.
- **`help_text=None` or `""`** — no description.
- **Two `ModelForm` bases differing only in a field's `help_text`** — two
  inputs; the per-shape build cache keys on the rendered text.
- **A serializer field's `help_text`** — read through the same accessor, so a
  truthy non-text value is refused there too; the constraint summary is
  appended as today.
- **A truthy non-text `help_text`** — refused at class creation for a
  selected output column, at bind for an input-only column; an
  annotation-only override of a selected column is the escape.
- **`help_text` on a `GeneratedField`** — threaded like any column (the
  field is the column the type reads).
- **Lazy `help_text` under `USE_I18N`** — rendered by `str()` at each field
  build site in the active language of the finalize call; a schema built per
  language is the consumer's existing responsibility.
- **A `ModelForm` field whose `help_text` differs from its column's** — the
  form field's text is published.
- **`auth.User.username`** — its lazy `help_text` describes `UserType.username`
  and `RegisterInput.username` on the live schema.
- **`TextChoicesField` with `blank=True`** — refused unless the enum
  declares a `""`-valued member; the `BLANK` member is never minted onto a
  consumer enum.
- **A consumer enum member GraphQL cannot publish** (non-ASCII name,
  `__`-prefixed, `true` / `false` / `null`) — refused at type creation.
- **An already-`strawberry.enum`-decorated `choices_enum`** — kept as
  decorated; `registry.clear()` leaves the consumer's definition alone and
  removes only a package-applied one, so a clear-and-rebuild re-wraps it.
- **`django-choices-field` installed but the field class never imported** —
  `loaded_attr` reads `sys.modules`; a model that declares the field has
  imported it, so the only way to miss is a consumer who never declared one,
  where the generated path is correct.
- **A card row the build falsifies** — amended in the kanban DB in Slice 5
  (Decision 11), never reinterpreted in the spec.
- **Concurrent sessions and card `053`**: `spec-053`'s Risks entry gates
  only its Slice 5 on this card (its Decision 11's "cannot precede them"
  reads as whole-card; Slice 5 corrects that scope), and its Status already
  shows C13, B3, C11 and D1–D3 landed
  on shared seams, so each slice re-verifies its target files against `HEAD`
  and rebases onto what `053` has landed (collisions in
  [Risks](#risks-and-open-questions)).
- **ASCII-only in `.py`**; trailing-comma layout; ruff format + check after
  every edit (maintainer-invoked gates only); symbol-qualified doc references
  re-swept for every renamed symbol.

## Test plan

Live-first ([Live-first coverage mandate][glossary-live-first-coverage-mandate]):
every reachable behavior is pinned through the fakeshop schema in
`examples/fakeshop/test_query/`; package tier only for shapes the stock
schema cannot express or an import-time refusal the live schema cannot load.

- **Slice 1** — live: `Shelf.alt_branches` (auto-created through) still
  writes through `.set()` via `createShelf` (model) and `createShelfViaForm`
  (form) — the opposite verdict of the refusal, which no live test can load.
  Package tier: `required_through_columns` over `GlossaryTerm.related_terms`
  returns `("kind",)` and over `Card.glossary_terms` returns `()` — neither
  lists `created_date` / `updated_date`; a `DjangoMutation`, a
  `DjangoModelFormMutation` and a `SerializerMutation` (declaring
  `related_terms = PrimaryKeyRelatedField(many=True, queryset=…)`
  explicitly, since DRF would otherwise make it read-only) over
  `GlossaryTerm` each raise with the owner label, the through model and
  `kind` in the message; the same `DjangoMutation` with
  `Meta.exclude = ["related_terms"]` builds without raising; a `ModelForm`
  overriding `_save_m2m` and a serializer overriding `create()` do not raise;
  the same serializer relation named in `Meta.injected_fields` raises;
  unmanaged throughs: a `TextField()` extra, a `db_default` extra and an
  `auto_now_add` extra do **not** raise, an `IntegerField(blank=True,
  null=False)` extra **does**, a symmetrical self-through with a required
  extra raises, a `through_fields` through with a third foreign key to the
  same model counts the third when required; a read-side `DjangoType` over
  `GlossaryTerm` finalizes.
- **Slice 2** — live
  (`examples/fakeshop/test_query/test_library_generated_api.py`):
  `codeLength` and `topicLength` appear in the SDL with the output scalar
  (`BigInt!` and `Int`) under both a holder `Meta.fields = "__all__"` type
  and `ShelfType`'s explicit list; a shelf with an empty `topic` reads
  `topicLength: null`; `exact` / `gt` / `lt` / `in` / `range` / `isNull`
  filter both, flat and through `BookFilter.shelf`; a `codeLength` `in`
  member past 64 bits is dropped (all of them: no row) and a `range` bound
  past it applies as `gte` / `lte`, never a raw bind; both order, nulls
  placed as asked; a holder Relay type declaring `code_length:
  relay.NodeID[int]` refetches through `node` and `nodes` and answers `null`
  with no error for an id past 64 bits; a holder model mutation naming no
  field list omits both
  from its input; an update of `code` through `updateShelfViaForm` returns
  the recomputed `codeLength` in its payload; with Django's `Chr` registered
  on `code_length`'s `output_field` instance (alone or with the generated
  field's), `chr__exact` is a `String` leaf, `"A"` matches the 65-character
  code and `65` is refused; a `contains` registered there as `has` is a
  `String` leaf; and a target-less `GlobalIDFilter` over `code_length` with
  `Exact` registered there as `same` matches by node id `65` and answers
  `GLOBALID_INVALID` for `abc`; a `Meta.filter_overrides` `IntegerField`
  entry whose `extra` names `lookup_expr="gte"` makes the `topic_length`
  leaf a `gte` filter, as on a plain column; and with `Chr` registered as
  `endswith` on `BigIntegerField`, a branch set's `shelves__code_length`
  `endswith` leaf selected by a consumer `CharField` override keeps its
  `distinct=False`, a branch with two matching shelves answering twice.
  In-process
  (`examples/fakeshop/tests/test_inspect_django_type.py`, `call_command`):
  the inspection command prints the `GeneratedField -> …` label. Package
  tier: a `GeneratedField(null=True)` over a non-null output publishes the
  optional scalar; `Meta.required_overrides` asserts it non-null; an
  integer-output choice `GeneratedField` has no `BLANK` member and a
  text-output one has; a file `output_field`, an unsupported output class
  and an `ArrayField` output with a choice-bearing `base_field` are refused
  with the outer field's label (type and filter side); two `GeneratedField`s
  of different output types in one `FilterSet` with `"__all__"` get their
  own lookups; a choice-bearing text output's `exact` / `iexact` leaves are
  `EnumChoiceFilter` / `EnumLookupFilter`; a `Meta.filter_overrides`
  `GeneratedField` entry is honoured; a `""` lookup is upstream's
  `FieldLookupError` on a generated column as on a plain one; an `ArrayField` output routes to the
  array arm (the array helpers read its element), an `HStoreField` output to
  the hstore arm; the keyset cursor validation and an `orderBy:` cursor
  refuse `Shelf.topic_length` as nullable and code `Shelf.code_length` as a
  `BigIntegerField`; `coerce_field_value_or_none` casts a decoded id through
  a generated column and through a key whose `to_field` is one;
  `LinkedDesk` stays out of every flavor's input
  (`editable_input_fields`, a `ModelForm` and a `ModelSerializer` input).
- **Slice 3** — live introspection: `Shelf.code`'s `help_text` describes
  `ShelfType.code` and the model-flavor and form-flavor input fields;
  `Book.genres`'s `help_text` (Slice 3's migration) describes
  `BookType.genres` and its `genresConnection` sibling; a consumer sibling
  with an explicit description keeps
  it; an annotation-only override publishes none; an `auto` annotation gets
  the column text; `UserType.username` and `RegisterInput.username` carry
  Django's username `help_text` (`examples/fakeshop/test_query/test_auth_api.py`).
  In-process: `export_schema` (`examples/fakeshop/tests/test_export_schema.py`)
  prints the `Shelf.code` description in the SDL. Package tier: a lazy
  `help_text` renders in the active language; `help_text=None` and `""`
  yield no description; a truthy non-text `help_text` is refused at class
  creation on a selected column, is not refused under an annotation-only
  override, and is refused at bind on an input-only column; a
  Relay-Node type whose pk carries a `help_text` finalizes with the Node `id`
  and no re-published pk; two `ModelForm` bases differing only in a field's
  `help_text` build two inputs; the serializer description routes through
  the accessor.
- **Slice 4** — present path, live: a library `TextChoicesField` column
  publishes one enum (the consumer's name; introspection shows no second
  type) and round-trips through a query, a filter and a write; an
  already-`strawberry.enum`-decorated `choices_enum` keeps its decoration.
  Package tier: `tests/_soft_dependency.py::simulated_absence` over
  `django_choices_field` proves the generated path is unchanged; a
  `blank=True` column with no `""` member is refused; a consumer member
  named `true`, a `__`-prefixed member and a non-ASCII member are each
  refused; `registry.clear()` then a rebuild re-wraps a package-decorated
  enum and leaves a consumer-decorated one untouched.
- **Slice 5** — re-run `examples/fakeshop/test_query/test_mutation_error_keys_api.py` and the three live
  key rows; re-run the `PAGINATION_INVALID` pin; nothing new unless a row
  is missing. The amended card rows pass `scripts/check_kanban_anchors.py`
  and `scripts/check_citations.py --substrings`; `import_spec_terms --check`
  is green after the CSV append.
- **Gate**: full suite green under `fail_under = 100` at every slice
  boundary, run only at maintainer-invoked gates per `AGENTS.md`.

## Doc updates

- Slice 1: `docs/README.md` `### Model mutations` — one sentence in the
  paragraph that states M2M inputs are replacements, naming the guard, the
  `Meta.exclude` escape and the consumer-authored through-model mutation;
  `docs/GLOSSARY.md` gains a row for the through-column guard via the
  glossary DB.
- Slice 2 (README built): `docs/README.md` `## Reading data` →
  `### Database-computed columns` — `GeneratedField` converts via its
  `output_field`, is read-only, is nullable when either field says so, and
  its three refusals; GLOSSARY row under Specialized scalar conversions
  (Slice 5's fold-in).
- Slice 3: `docs/README.md` `## What just happened?` — column `help_text` is
  the field description, an explicit description wins, an annotation-only
  override opts out; GLOSSARY row.
- Slice 4: `docs/README.md` `## Installation` gains a sentence that a
  `django-choices-field` column's `choices_enum` is reused when the consumer
  declares one (the section has no soft-dependency list to extend);
  `START.md`'s "Soft deps" line gains `django-choices-field` (observation
  only, no guard); the GLOSSARY "Soft dependency" body gains the
  observation-only variant (`loaded_attr`, no `require_*` guard, no install
  hint, no extra); GLOSSARY row under Choice enum generation.
- Slice 5: `docs/TREE.md` regenerated (module docstrings change);
  `KANBAN.md` / `KANBAN.html` from the DB after the card amendments;
  [`spec-053`][spec-053] Decision 11's file-overlap clause and "cannot
  precede them" scope corrected. **Not touched**: `CHANGELOG.md`, the version
  triplet, GLOSSARY statuses,
  `README.md` / `GOAL.md` / `TODAY.md` release-status prose (all ride
  `spec-053` Slice 5).

## Risks and open questions

- **Card rows the spec departs from — scheduled amendments.** Slice 5 amends
  each of these rows in the kanban DB (on card `051` unless marked), then
  re-renders, and corrects the `spec-053` sentence listed last. Preferred
  answer: amend all fourteen `CardItem` rows and both `CardReference` notes
  at wrap, each to the wording this spec ships. Fallback: if a row's text moved concurrently,
  amend the current text to the same facts and record the re-read in the
  wrap commit; the fallback is never "leave the prose and let the spec carry
  the truth".
  - 1475 (scope): "reject at type creation" → reject on the mutation class
    (model flavor at class creation, form / serializer at bind); "outside
    the `FieldError` envelope" is false (the failure is the generic
    `"__all__"` constraint leaf); "makes the `through_defaults` refusal …
    safe" overstates (the guard does not cover unique-set collisions).
  - 1476 (scope): "resolve type and nullability from the field's
    `output_field` in `convert_field_output`" → type from the
    `output_field` through `scalar_route` (seam relocated so filters agree),
    nullability `GeneratedField.null or output_field.null`; "`Meta.exclude`
    is the only escape" is false today → the escapes are exclusion, an
    annotation-only override, or a consumer `SCALAR_MAP` entry (the raise
    text itself offers the last).
  - 1477 (scope): the description also lands on the model and form input
    fields (accepted widening) and a truthy non-text `help_text` is refused.
  - 1481 (DoD): "fails at type creation" and "live coverage proves the
    runtime `.set()` path is never reached" → fails on the mutation class
    before any request; package tier pins the refusal (a live test cannot
    load it), live coverage proves `.set()` is still reached on the stock
    auto-created through.
  - 1482 (DoD): "converts via its `output_field` type and nullability" →
    type via `output_field`, nullability by the either-flag rule, file
    outputs refused.
  - 1483 (DoD): "per the spec's on-by-default-or-opt-in decision" → always
    on, inputs included, annotation-only override opts out.
  - 1484 (DoD): add the two consumer-enum refusals (blank admission,
    unpublishable member names) — accepted widening against 🍓.
  - 1491 and 1492 (files_touched): 1492 names `mutations/resolvers.py`,
    which no slice changes (the guard fires before `_assign_m2m` is ever
    reached), and omit most of what the four open slices change. Amend to
    `utils/relations.py`, `mutations/sets.py`, `forms/inputs.py`,
    `rest_framework/inputs.py` (Slice 1); `utils/relations.py`,
    `types/converters.py`, `filters/sets.py`, `filters/base.py`,
    `utils/_array_field.py`, `keyset.py`, `optimizer/plans.py`,
    `utils/querysets.py`, `management/commands/inspect_django_type.py`
    (Slice 2); `types/base.py`, `types/finalizer.py`, `types/resolvers.py`,
    `mutations/inputs.py`, `rest_framework/serializer_converter.py`
    (Slice 3); `pyproject.toml` and `uv.lock` (Slice 4), each under its
    full `django_strawberry_framework/` path as the rows spell them. 1493
    and 1494 name the built items' files and stay.
  - 1496 (verified_upstream): "resolves type and nullability from
    `output_field`" is right for 🍓 (its `field_to_check` hands
    `is_optional` the `output_field`) but not for this package, which also
    honors the `GeneratedField`'s own `null` (the either-flag rule).
  - 1500 (why_it_matters): "two type-creation failures a migrant cannot
    work around (`through=`, `GeneratedField`)" → the `through=` failure is
    request-time (the `"__all__"` leaf on a write that sends the relation a
    non-empty list; excluding the relation from the mutation avoids it),
    and a `GeneratedField` has three escapes (exclusion, an annotation-only
    override, a `SCALAR_MAP` entry); restate as two declarations that fail
    as written.
  - 1501 (dependencies_note): "card `053`'s four-DRY-axes file list covers …
    every file this card touches except `types/converters.py`" is false:
    beyond `types/converters.py`, this card touches
    `management/commands/inspect_django_type.py`, `pyproject.toml` and
    `uv.lock`, and its own files-touched rows name `auth/mutations.py` and
    `error_policy.py`, none of them on that list (`CardItem` 1090).
    `pyproject.toml` is in card `053`'s files (`CardItem` 1088 names it for
    the import-linter config and extras), but not in the four-axes list the
    row quotes. "must be sequenced behind this one" overstates:
    `spec-053`'s Risks entry gates only its Slice 5 on this card.
  - 1502 (dependencies_note): "This card lands first" overstates for the
    same reason; only card `053`'s Slice 5 waits for this card.
  - `CardReference` 129 (this card → `053`) and 146 (`053` → this card),
    the dependency edge's notes: both say card `053` shares every file in
    this card's files-likely-touched list except `types/converters.py`,
    false for the files named under 1501; restate the edge as "card `053`'s
    Slice 5 cut waits for this card", with no overlap claim.
  - `spec-053` Decision 11 (not a board row, corrected in the same pass):
    "`051` touches every file in this card's WP list except
    `types/converters.py`" is quantified over card `053`'s list and false
    both ways (`types/converters.py` is not on that list and is the file
    this card changes most; most of the list, such as `orders/sets.py`,
    `sets_mixins.py`, `keyset.py`, `optimizer/*` and `types/relay.py`, this
    card never touches), and its "so it cannot precede them" reads as
    whole-card where its own Risks entry gates only Slice 5 on this card
    (card `052` alone holds all of card `053`'s slices, per `CardItem`
    1111).
  - 1504 (note): names `docs/SPECS/spec-051-parity_gaps-0_0_15.md`; the spec
    is `docs/spec-051-parity_gap_closure-0_0_15.md` (until the next spec's
    archive step moves it).
- **Accepted widenings beyond the card's text.** The `help_text` on input
  fields (⚛️ does it on both sides; the card names only "the generated
  field") and the blank-admission / member-name refusals of a consumer enum
  (🍓 accepts both). Preferred answer: ship both and amend 1477, 1483 and
  1484 as above. Fallback: if the maintainer narrows, drop the input-side
  description (one kwargs line per builder) and keep the refusals, which
  guard a wire contract rather than add surface.
- **Sequencing and collisions with card `053`.** `spec-053`'s Risks entry
  gates only its Slice 5 on this card, and its Status shows C13, B3, C11
  and D1–D3 already landed on shared seams. Preferred answer: each slice of this card rebases
  onto whatever `053` has landed when it starts; the later of two colliding
  items carries the other's change: whatever B5 folds into
  `_attach_generated_resolvers` (053 Slice 2) must carry the `description=`
  parameter both attachers gain (this card's Slice 3) if they are among
  what it folds, or this card threads it through the fold if the fold
  lands first; C10's column-conversion sharing (053 Slice 3) and the
  description kwargs in `build_mutation_input` / `forms/inputs.py` (this
  card's Slice 3) likewise; C8's `iter_relation_path` in
  `utils/relations.py` (053 Slice 3) shares a module with
  `required_through_columns` (this card's Slice 1) but no function;
  `spec-053` Decision 11's file-overlap clause is corrected in Slice 5
  (first bullet). Fallback: if the maintainer re-orders so `053` wraps
  first, the joint-cut ownership follows whichever card lands last and this card's Slice 5 takes the version
  verification `053` would have done.
- **The fifth soft dependency against card `053`'s "four extras" DoD.**
  Preferred answer: no extra for `django-choices-field` (Decision 6), so
  `053`'s count stands and no cross-card row is owed for it. Fallback: if the
  maintainer wants the extra, it lands in `053`'s A3 block and this card's
  Slice 5 appends a row to card `053` changing "four extras" to five.
- **SDL-visible change on the live schema.** Slice 3 adds descriptions to
  `UserType.username` and `RegisterInput.username` (Django's lazy
  `help_text`) and to every documented column a consumer schema exposes.
  Preferred answer: card `053`'s `CHANGELOG.md` entry names it, through a
  row Slice 5 appends to card `053`. Fallback: if card `053` has already cut,
  the maintainer adds the bullet to the released entry by hand (this spec
  grants no `CHANGELOG.md` permission).
- **The scalar `strawberry.field(description=…)` assignment** (Decision 5)
  is the one shape the Phase-2 window has not carried before: a field object
  with no resolver and no default beside a synthesized annotation.
  Strawberry builds its dataclass keyword-only, and the package is not
  known to construct `DjangoType` instances (unproven; the consistent
  evidence is
  `django_strawberry_framework/types/relay.py::install_is_type_of`, which
  maps a returned model instance, not a type instance, to its type), so no
  ordering or default problem is expected. Preferred answer: assign it and pin with the live
  introspection rows. Fallback: attach a trivial attribute resolver the way
  the file attacher does, which costs one function per described scalar.
- **Which library columns carry the fixtures.** Preferred: `Shelf` (it
  already hosts the choice and M2M fixtures and has the richest live
  coverage): `code_length` and `topic_length` generated columns (Slice 2,
  built, migration `0020_shelf_code_length_topic_length`), a `help_text` on
  `code` plus one on `Book.genres` (Slice 3, the next free migration
  number; no fakeshop relation column carries a
  `help_text` today, and `Book.genres` is the forward relation whose
  `relation_shapes = {"genres": "both"}` publishes a connection sibling),
  and a new `grade` `TextChoicesField` column rather than converting
  `condition`, whose `BLANK`-member behavior is pinned and must stay
  (Slice 4, the number after Slice 3's). Each slice takes the next free
  number when it lands.
  Fallback: `Book` for the scalar and choice fixtures, same three
  migrations.
- **`django-choices-field` floor.** The dev pin needs a release that ships
  `choices_enum` on both field classes and installs on the supported Django
  range. Preferred answer: the builder checks PyPI at Slice 4 and records the
  reason beside the pin, as the other soft-dependency pins do. Fallback: if
  no release installs on the newest supported Django, the present-path
  fixture moves off the fakeshop schema to a package-tier model under
  `tests/` and the live rows become package-tier rows with the gap recorded
  beside the pin.
- **`help_text` on the form flavor when the form field and the column
  disagree.** Preferred answer: the form field wins (it is the input's
  source of truth, and ⚛️'s rule); a `ModelForm` that overrides a field's
  `help_text` publishes the override. Fallback: if the maintainer wants
  model-side consistency, read the backing column's text when one exists
  and the form field's only for a column-less field — one branch in the
  form builder.

## Out of scope (explicitly tracked elsewhere)

- `through_defaults` support — refused on card `071` (migration and
  adoption guides); its remedy is a consumer-authored mutation over the
  through model.
- `convert_choices_to_enum` naming and the enum-reuse cache contract — card
  `065`.
- The `0.0.15` version cut, `CHANGELOG.md` entry and GLOSSARY status flips —
  card `053` ([`spec-053`][spec-053]).
- The debug-extension extraction on the same line — card `052`
  ([`spec-052`][spec-052]).
- The beta cut and the parity claim it asserts — card `057`; this card is
  what makes the claim true.

## Definition of done

- [ ] A `through=` many-to-many with required extra columns (`auto_now`
      family, `db_default`, `GeneratedField` and `""`-fillable columns
      exempt) fails on the mutation class that would write it in every
      model-backed flavor, before any request, with a `ConfigurationError`
      naming the owner, the through model, the columns and the remedies;
      `Meta.exclude` of the relation builds; a serializer's
      `Meta.injected_fields` relation is guarded too; a `_save_m2m` / `create()` /
      `update()` override exempts its flavor; an auto-created or fully-filled
      through is unaffected; live coverage proves `.set()` is still reached
      on the stock auto-created through.
- [ ] A `GeneratedField` reached through `Meta.fields = "__all__"` or an
      explicit list converts via its `output_field`, is nullable when either
      field declares `null`, takes choices and blank admission by the
      Decision 3 rules, filters (two output types in one `FilterSet`) and
      orders, is absent from every generated write input, is refused with
      the outer field's label for a file / image output, an unsupported
      output class or a choice-bearing array element, and is live-probed
      end-to-end through two fakeshop columns.
- [ ] Column `help_text` is the SDL description of every package-synthesized
      output field, connection sibling and model/form input field, always on;
      an explicit description wins; an annotation-only override publishes
      none; the Relay-suppressed pk gets no field object; a lazy string
      renders at its build site; `None` / `""` publish none; a truthy
      non-text value is refused at class creation for a selected output
      column and at bind for an input-only column; the form build cache keys
      on the text; live
      introspection and the `export_schema` check pin it, `Book.genres` and
      `auth.User.username` included.
- [ ] A `TextChoicesField` / `IntegerChoicesField` with a `choices_enum`
      publishes the consumer's enum (one enum type, not two); a blank-admitting
      column without a `""` member and an unpublishable member name are
      refused; a package-applied `strawberry.enum` is removed by
      `registry.clear()` and a consumer's is not; absence of
      `django-choices-field` changes nothing, proven at package tier; no
      packaging extra.
- [ ] Items 5 and 6 verified against the tree: the key-map matrix, its three
      live rows and the `PAGINATION_INVALID` pin all pass.
- [ ] `CardItem` 1475, 1476, 1477, 1481, 1482, 1483, 1484, 1491, 1492,
      1496, 1500, 1501, 1502 and 1504 and `CardReference` 129 and 146
      amended in the kanban DB to the shipped wording and re-rendered; card
      `053` carries the row flagging the SDL-visible `help_text` change;
      `spec-053` Decision 11's file-overlap clause and "cannot precede them"
      scope corrected.
- [ ] Card `071`'s `CAMELCASE_ERRORS` row and card `053`'s amended Slice 5
      sentence, GLOSSARY-flip DoD and dependency edge re-read and confirmed
      at wrap.
- [ ] Version triplet verified at `0.0.15`, unmoved.
- [ ] Docs fold-in: GLOSSARY rows via the DB (no status flips), each new
      anchor appended to this spec's `-terms.csv` with
      `scripts/check_spec_glossary.py` re-run green and `import_spec_terms`
      run; `docs/README.md`, `START.md`'s soft-deps line, `docs/TREE.md`
      regenerated; card flipped Done; `KANBAN.md` / `KANBAN.html`
      regenerated; `import_spec_terms --check` green.
- [ ] Full suite green under `fail_under = 100`; live-first placement
      respected. No version triplet move, GLOSSARY status flip or
      `CHANGELOG.md` entry — all three ride card `053`'s joint `0.0.15` cut.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: GLOSSARY.md
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-auto-typed-annotations]: GLOSSARY.md#auto-typed-annotations
[glossary-choice-enum-generation]: GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangofiletype]: GLOSSARY.md#djangofiletype
[glossary-djangoformmutation]: GLOSSARY.md#djangoformmutation
[glossary-djangoimagetype]: GLOSSARY.md#djangoimagetype
[glossary-djangomodelformmutation]: GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-eviction-simulated-absence]: GLOSSARY.md#eviction-simulated-absence
[glossary-fielderror-envelope]: GLOSSARY.md#fielderror-envelope
[glossary-filterset]: GLOSSARY.md#filterset
[glossary-finalize_django_types]: GLOSSARY.md#finalize_django_types
[glossary-hard-dependency]: GLOSSARY.md#hard-dependency
[glossary-input-type-generation]: GLOSSARY.md#input-type-generation
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-metachoice_enum_names]: GLOSSARY.md#metachoice_enum_names
[glossary-metadescription]: GLOSSARY.md#metadescription
[glossary-metaexclude]: GLOSSARY.md#metaexclude
[glossary-metafields]: GLOSSARY.md#metafields
[glossary-metafilesystem_path_fields]: GLOSSARY.md#metafilesystem_path_fields
[glossary-metamodel]: GLOSSARY.md#metamodel
[glossary-metanullable_overrides]: GLOSSARY.md#metanullable_overrides
[glossary-metarelation_shapes]: GLOSSARY.md#metarelation_shapes
[glossary-metarequired_overrides]: GLOSSARY.md#metarequired_overrides
[glossary-orderset]: GLOSSARY.md#orderset
[glossary-paginationargumenterror]: GLOSSARY.md#paginationargumenterror
[glossary-production-error-policy]: GLOSSARY.md#production-error-policy
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-require_optional_module]: GLOSSARY.md#require_optional_module
[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: GLOSSARY.md#scalar-field-override-semantics
[glossary-schema-export-management-command]: GLOSSARY.md#schema-export-management-command
[glossary-schema-introspection-management-command]: GLOSSARY.md#schema-introspection-management-command
[glossary-serializermutation]: GLOSSARY.md#serializermutation
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-specialized-scalar-conversions]: GLOSSARY.md#specialized-scalar-conversions
[glossary-structural-error-classification]: GLOSSARY.md#structural-error-classification

<!-- docs/SPECS/ -->
[spec-052]: SPECS/spec-052-debug_extraction-0_0_15.md
[spec-053]: SPECS/spec-053-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-graphene-converter]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/converter.py
[upstream-graphene-filter-utils]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/filter/utils.py
[upstream-graphene-form-converter]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/forms/converter.py
[upstream-graphene-settings]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/settings.py
[upstream-graphene-types]: ../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/types.py
[upstream-strawberry-field-types]: ../../strawberry-django-main/strawberry_django/fields/types.py
[upstream-strawberry-mutation-resolvers]: ../../strawberry-django-main/strawberry_django/mutations/resolvers.py
[upstream-strawberry-settings]: ../../strawberry-django-main/strawberry_django/settings.py
[upstream-strawberry-type]: ../../strawberry-django-main/strawberry_django/type.py
