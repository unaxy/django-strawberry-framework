# Spec: Generated input field names follow the schema's naming config

Target card: [`DONE-051-0.0.15`][kanban]
Status: **Shipped** in the `0.0.15` line; it ships in the `0.0.15` release. This `Status:`
line is the lifecycle source of truth; the Slice checklist is the contract ledger and its
boxes stay unticked by repository convention.

Predecessors: [`spec-027`][spec-027] (the filter input pipeline and `LOOKUP_NAME_MAP`),
[`spec-028`][spec-028] (the order inputs), [`spec-036`][spec-036],
[`spec-038`][spec-038] and [`spec-039`][spec-039] (the model, form and serializer write
inputs), and [`spec-050`][spec-050] (the `DjangoListField` arguments, which already followed
the naming config).

Release: [`django_strawberry_framework.__version__`][package-init] reads `"0.0.15"`, the open
`0.0.15` development line. [`TODO-ALPHA-055-0.0.15`][kanban] cuts the `0.0.15` release
([Decision 7](#decision-7--joint-0015-cut--this-card-bumps-nothing)).

## Key glossary references

- [`DjangoSchema`][glossary-djangoschema] - the schema class whose construction refuses two
  fields its converter names alike.
- [`strawberry_config`][glossary-strawberry_config] - the config whose `auto_camel_case` and
  `name_converter` now name every generated input field.
- [Input type generation][glossary-input-type-generation] - the write-input generator for
  model, form and serializer mutations.
- [`FilterSet`][glossary-filterset], [`RelatedFilter`][glossary-relatedfilter],
  [`OrderSet`][glossary-orderset] and [`RelatedOrder`][glossary-relatedorder] - the read-side
  sets whose generated input fields follow the config.
- [`DjangoMutation`][glossary-djangomutation],
  [`DjangoFormMutation`][glossary-djangoformmutation],
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] and
  [`SerializerMutation`][glossary-serializermutation] - the write flavors whose errors key to
  the published names.
- [`FieldError` envelope][glossary-fielderror-envelope] - the error shape whose `field` is the
  name the executing schema published.
- [Execution resource policy][glossary-execution-resource-policy] - the budget that charges a
  generated relation list by its input attr.
- [`DjangoListField`][glossary-djangolistfield] - the list arguments that already followed the
  config before this card.
- [`ConfigurationError`][glossary-configurationerror] - the refusal type for a collision.
- [`Meta.fields`][glossary-metafields] and [`Meta.exclude`][glossary-metaexclude] - the levers
  the collision remedy names.
- [Joint version cut][glossary-joint-version-cut] - the `0.0.15` release rule.

## Slice checklist

- [ ] Slice 1 - every generated filter, order, model-mutation, form and serializer input
      field is built with no `name=`; only the Python-keyword escapes (`in_`, `and_`, `or_`,
      `not_`, and a transform registered under a keyword) keep one
      ([Decision 1](#decision-1--the-executing-schemas-nameconverter-names-every-generated-input-field),
      [Decision 2](#decision-2--only-a-python-keyword-escape-keeps-name)).
- [ ] Slice 2 - the bind-time name is the default converter's prediction and every request
      reads the executing schema's own names
      ([Decision 3](#decision-3--a-bind-time-prediction-a-per-request-read-back)).
- [ ] Slice 3 - the four bind-time GraphQL-name collision guards give way to one per-schema
      refusal in `DjangoSchema`, worded with what the consumer can change
      ([Decision 4](#decision-4--djangoschema-refuses-a-pair-its-converter-names-alike)); a
      plain `strawberry.Schema` publishes one of the pair, documented
      ([Decision 5](#decision-5--a-plain-strawberryschema-publishes-one-of-the-pair)).
- [ ] Slice 4 - `LOOKUP_NAME_MAP` holds python attrs only, and no package casing helper names
      an input field.
- [ ] Slice 5 - `docs/README.md`, the glossary rows, the predecessor specs and the board state
      the contract.

## Problem statement

Under `StrawberryConfig(auto_camel_case=False)` or a custom `NameConverter`, output fields and
list arguments followed the config while every package-generated filter, order and mutation
input field kept a pinned camelCase `name=` (`createdDate`, `iContains`, `categoryId`). One
schema mixed both conventions, so a client of a snake-case schema wrote
`order_by: [{createdDate: ASC}]`. The pin also differed from the output type's own field at a
digit boundary: the output field `isbn_13` published `isbn13`, the generated input field
`isbn_13` (the pinned caser kept the `_` before a digit). Upstream strawberry-graphql-django
pins no input name and follows the config.

## Current state

- `django_strawberry_framework/utils/inputs.py::build_strawberry_input_class` builds every generated
  input class; no field it receives carries `name=` unless a keyword forces it.
- `django_strawberry_framework/utils/inputs.py::optional_field_kwargs` is the one place a filter or
  order field gets a `name=`: only for a keyword escape.
- `django_strawberry_framework/filters/inputs.py::lookup_leaf_names` maps a lookup to its python attr
  through `LOOKUP_NAME_MAP` (`icontains` -> `i_contains`); the converter names the field
  (`iContains` by default, `i_contains` under `auto_camel_case=False`).
- `django_strawberry_framework/utils/inputs.py::predicted_input_field_name` is the bind-time name;
  `django_strawberry_framework/utils/inputs.py::published_input_specs` is the per-request one.
- `django_strawberry_framework/schema.py::_refuse_field_name_collisions` refuses, per schema, two fields one
  published type's converter names alike.

## Goals

- One naming rule per schema: every generated input field is named by the executing schema's
  `NameConverter`, exactly as its output fields and list arguments are.
- Every runtime reader of a published name agrees with what the executing schema published,
  under every config: a write mutation's error keys key to the published names, and the
  resource budget and the filter and order decode read no wire name at all (Decision 3).
- A pair the converter names alike fails the deployment at construction, naming what the
  consumer can change.

## Non-goals

- Configurable logic keys (`FILTER_KEY` / `AND_KEY` / `OR_KEY` / `NOT_KEY`): card
  [`TODO-BETA-072-0.1.7`][kanban].
- Renaming generated input TYPES. Type names stay the package's own grammar
  (`generated_input_type_name`, `name_set_input_type_name`), which no converter rewrites.
- An injective naming seam. Strawberry's converter has none, and the package adds none
  ([Decision 6](#decision-6--no-converter-wrapper)).

## Borrowing posture

Upstream strawberry-graphql-django builds its filter and order input fields with no pinned
name (`fields/filter_types.py::BaseFilterLookup`, `ordering.py::OrderSequence`), so the
schema's converter names them. This card adopts that shape. Strawberry's own
`NameConverter.from_field` is the one source of every published name; the package asks it and
never models it.

## Architectural decisions

### Decision 1 — The executing schema's `NameConverter` names every generated input field

Every generated input field is built with no `name=`. Strawberry keys an input type's fields
by `config.name_converter.from_field` at schema build, so the field publishes under the
schema's own rule: `createdDate` / `isbn13` under the default config, `created_date` /
`isbn_13` under `auto_camel_case=False`, a custom converter's spelling otherwise. The output
field over the same column publishes the same name, so a client reads and writes one spelling.

**Rationale**: a pinned name is a second naming authority beside the schema's. It cannot
follow `auto_camel_case`, and even by default it diverged from Strawberry's converter on
several shapes (`isbn_13` -> `isbn_13` vs `isbn13`, `a_b_c` -> `aB__xC` vs `aBC`,
`URL_name` -> `URL__xName` vs `URLName`). The schema is the only object that knows its config,
and it names the fields when it is built.

**Wire change under the default config**: every input field whose name the package caser
spelled differently from Strawberry's converter renames to the converter's spelling. An
underscore before a digit is dropped (`isbn_13` -> `isbn13`, `x_1_y` -> `x1Y`); the `__x`
marker the caser put before a segment following a one-letter or upper-case one is gone
(`a_b_c` -> `aBC`, `URL_name` -> `URLName`, `API_key` -> `APIKey`); a leading underscore is
dropped (`_legacy_id` -> `LegacyId`). Every other default-config name is unchanged. On
fakeshop that is 31 input fields, all at digit boundaries (`isbn_13` -> `isbn13`, `address_2`
-> `address2`), and one hashed serializer input type, which renames because its shape token
hashes the predicted name
(`PatronProfileSerializerAddress_u2b828be281257a1c0Favorite_ugenre982b97c775a8d68dPartialInput`
-> `PatronProfileSerializerAddress_u235621b729422e33eFavorite_ugenre982b97c775a8d68dPartialInput`).

**Alternative rejected**: keep the pins as a wire contract. That keeps the default SDL
byte-for-byte, but leaves every snake-case schema mixing two conventions and every
digit-boundary input disagreeing with its output field.

### Decision 2 — Only a Python-keyword escape keeps `name=`

`in`, `and`, `or` and `not` cannot be dataclass attributes, so the attr is escaped (`in_`,
`and_`, `or_`, `not_`) and the field carries `name="in"` (and so on) through
`django_strawberry_framework/utils/inputs.py::optional_field_kwargs`; a transform registered under a
keyword (`from`) escapes the same way in
`django_strawberry_framework/filters/inputs.py::lookup_leaf_names`. These spellings hold under the
default config and under `auto_camel_case=False`. A converter that overrides
`get_graphql_name` respells an explicit name too (`IN`, `OR` under one that upper-cases every
name), and a filter under it still decodes: graphql-core coerces each published name to the
input dataclass's Python attr, the decode reads only those attrs, and
`django_strawberry_framework/filters/sets.py::FilterSet._normalize_input` writes the literal
django-filter form keys the lookup table records
(`django_strawberry_framework/filters/inputs.py::filter_lookup_table`). A filter error keys
to those form paths, with the logic arms' literal names (`or_0__title`;
`django_strawberry_framework/filters/inputs.py::LogicOperatorDescriptor.arm_key`), under every
config.

**Rationale**: the escape is the one name the package must supply, since the attr cannot be
the wire name. Everything else is the converter's.

### Decision 3 — A bind-time prediction, a per-request read-back

Input classes are process-global and built before any schema exists
(`finalize_django_types()`, mutation binding), and one class can serve schemas of different
configs. So no class carries a final name:

- At bind, a `django_strawberry_framework/utils/inputs.py::InputFieldSpec`'s `graphql_name` is
  `django_strawberry_framework/utils/inputs.py::predicted_input_field_name`, Strawberry's default
  converter's answer (or a `Meta.input_class` field's explicit `name=`). It feeds what has no
  schema to ask: generated type-name hashing, and a direct-call stub with no executable
  schema.
- Per request, `django_strawberry_framework/utils/inputs.py::published_input_specs` renames the specs to
  the names the executing schema published, read through
  `django_strawberry_framework/utils/typing.py::published_argument` and
  `django_strawberry_framework/utils/typing.py::published_python_name`; every write flavor keys its
  decode, validator and save-time errors through it.
- The resource budget charges a generated relation list by its input attr, which the published
  field back-references
  (`django_strawberry_framework/extensions/resource_policy.py::_mutation_input_specs`), so it needs
  no name at all.

**Rationale**: the name is a property of the schema, not of the class, so the class records
the attr and the schema answers the name.

### Decision 4 — `DjangoSchema` refuses a pair its converter names alike

Strawberry keeps one of two distinct fields its converter gives one GraphQL name and silently
drops the other. `django_strawberry_framework/schema.py::_refuse_field_name_collisions` walks every published
object, interface and input type of a `DjangoSchema` at construction and raises
`ConfigurationError` naming the type and both fields. A generated field takes no `name=`, so
the remedy names what the consumer can change
(`django_strawberry_framework/utils/inputs.py::field_name_collision_remedy`, fed by the
`django_strawberry_framework/utils/inputs.py::GeneratedFieldSources` that
`build_strawberry_input_class` records): for two generated fields, the set, model, form or
serializer and the two members they are generated from, with the levers the flavor has
(`Meta.fields` / `Meta.exclude`, and a model mutation's `Meta.input_class` field with an
explicit `name=`). A filter or order set names each member's own lever, since
`Meta.exclude` refuses a declared name
(`django_strawberry_framework/sets_mixins.py::reject_unknown_exclude_names`): a declaration is
renamed or removed (an inherited one disabled with `name = None`), a `Meta.fields` entry is
dropped through `Meta.fields` / `Meta.exclude`, a `RelatedFilter` flat copy goes through its
`RelatedFilter` or `HIDE_FLAT_FILTERS`, an operator-bag lookup is dropped from its
`Meta.fields` lookup list, and a logic key (`and_`, `or_`, `not_`) is named as reserved, so
only the other member's lever is offered. For a generated field beside a declared one, the
declared field's `name=` or the member to drop; for two declared fields, Strawberry's own
levers. The check is the schema's: `field_2` beside `field2` is refused under the default
config and served as two fields under `auto_camel_case=False`.

**Rationale**: the collision is a fact about one schema's converter, so it is decided when
that schema is built. This replaces the four bind-time guards, which judged a name before any
converter existed.

### Decision 5 — A plain `strawberry.Schema` publishes one of the pair

The card asked to document or refuse a plain `strawberry.Schema` built over generated inputs.
It is documented: a plain schema runs no collision check, so it publishes one of two fields
its converter names alike and drops the other. A write mutation whose input lost a field that
way refuses before any write: `django_strawberry_framework/utils/inputs.py::published_input_specs`
finds no published field for the dropped one and raises `ConfigurationError` naming it and
pointing at `DjangoSchema`. `docs/README.md` and the
[`FilterSet`][glossary-filterset], [`OrderSet`][glossary-orderset],
[Input type generation][glossary-input-type-generation],
[`strawberry_config`][glossary-strawberry_config] and [`DjangoSchema`][glossary-djangoschema]
glossary rows say so.

**Rationale**: the read surface builds and resolves under a plain schema by design, and
refusing there needs a hook into a class the package does not own. Generated mutations
already refuse to write under a plain schema.

### Decision 6 — No converter wrapper

The card prescribed a wrapper converter that names generated input fields per schema while
keeping them distinct. It is not built.

**Rationale**: names already resolve per schema at build (Decision 1), so the wrapper would add
nothing but a second naming rule. Keeping `field_2` and `field2` distinct means a naming
function that differs from the schema's own converter, which re-derives upstream behaviour
instead of asking it, and Strawberry offers no injective seam to adapt. The per-schema refusal
(Decision 4) names the pair and the lever instead.

### Decision 7 — Joint `0.0.15` cut — this card bumps nothing

This card ships in the `0.0.15` line beside `DONE-050-0.0.15`, `WIP-ALPHA-052-0.0.15`,
`TODO-ALPHA-053-0.0.15`, `TODO-ALPHA-054-0.0.15` and `TODO-ALPHA-055-0.0.15`, six cards in all, so
the line is a [joint version cut][glossary-joint-version-cut]: card `055` lands last and owns the version
triplet, the release-status flips and the `CHANGELOG.md` entry. This card's change notes ride
`CHANGELOGTODO.md` for that cut.

## Edge cases and constraints

- **Digit boundaries.** `isbn_10` and `isbn_13` publish `isbn10` / `isbn13` by default, as the
  output fields do; `publisher_2` beside `publisher2` on one model is refused at
  `DjangoSchema` construction and published as two fields under `auto_camel_case=False`.
- **A path member beside a declared filter.** A `Meta.fields` path the converter names like a
  declared filter is refused, naming the path member.
- **`RelatedOrder` members.** Two related-order members the converter names alike are refused
  the same way, and order apart under `auto_camel_case=False`.
- **Operator-bag lookups** carry `GeneratedFieldSources` too: only a converter that names two
  lookups alike reaches them (`gt` / `gte` under one that drops a trailing `e`), and the
  refusal names the head's `Meta.fields` lookup list (the child set's, for a flat copy).
  Range inputs carry none; their bounds are the package's own names.
- **A logic key.** A member the converter names like `and` / `or` / `not` is refused, naming
  the key reserved and the member's own lever.
- **A Python-keyword column.** A model field named `from` is no dataclass attribute; the
  generated input refuses it with a `ConfigurationError` naming it, and `Meta.fields` /
  `Meta.exclude` leaves it out.
- **A direct-call stub** with no executable schema keeps the bind-time names
  (`published_input_specs` returns the bind tuple).
- **One class, several schemas.** The same input class served by a default schema and a
  snake-case schema publishes under each schema's names, and each request reads its own.
- **Type names** never follow the converter: `generated_input_type_name` and
  `name_set_input_type_name` stay the package grammar, so a hashed serializer type (Decision 1's
  fakeshop one) is the only kind of type that renames.

## Test plan

Live tier (`/graphql/` over HTTP):

- `examples/fakeshop/test_query/test_library_api.py::test_snake_case_schema_names_generated_filter_and_order_fields_in_snake_case`
- `examples/fakeshop/test_query/test_library_api.py::test_snake_case_schema_keeps_the_keyword_lookup_and_logic_key_spellings`
- `examples/fakeshop/test_query/test_library_api.py::test_snake_case_schema_writes_a_generated_relation_under_its_snake_name`
- `examples/fakeshop/test_query/test_library_api.py::test_custom_converter_names_generated_filter_and_order_fields_end_to_end`
- `examples/fakeshop/test_query/test_library_api.py::test_related_order_members_the_default_converter_names_alike_refuse_the_schema`
- `examples/fakeshop/test_query/test_library_api.py::test_related_order_members_publish_and_order_apart_without_auto_camel_case_over_http`
- `examples/fakeshop/test_query/test_input_shapes_api.py::test_digit_boundary_columns_the_default_converter_names_alike_refuse_the_schema`
- `examples/fakeshop/test_query/test_input_shapes_api.py::test_digit_boundary_columns_publish_and_write_both_without_auto_camel_case_over_http`
- `examples/fakeshop/test_query/test_input_shapes_api.py::test_a_plain_schema_refuses_a_write_through_the_field_its_converter_dropped_over_http`
- `examples/fakeshop/test_query/test_library_api.py::test_a_declared_member_beside_a_listed_one_names_each_members_own_lever`
- `examples/fakeshop/test_query/test_filter_declarations_api.py::test_a_member_the_converter_names_like_a_logic_key_names_the_key_reserved`
- `examples/fakeshop/test_query/test_filter_declarations_api.py::test_operator_bag_lookups_the_converter_names_alike_name_the_lookup_list`
- `examples/fakeshop/test_query/test_filter_declarations_api.py::test_a_flat_copy_the_converter_names_like_a_declared_filter_names_its_relatedfilter`
- `examples/fakeshop/test_query/test_filter_declarations_api.py::test_flat_copy_lookups_the_converter_names_alike_name_the_child_lookup_list`
- `examples/fakeshop/test_query/test_filter_declarations_api.py::test_filter_members_the_default_converter_names_alike_refuse_the_schema`
- `examples/fakeshop/test_query/test_filter_declarations_api.py::test_a_path_member_beside_a_declared_filter_the_converter_names_alike_names_the_path`
- `examples/fakeshop/test_query/test_model_mutation_flows_api.py::test_consumer_and_generated_fields_key_each_refusal_to_the_executing_schema`
- `examples/fakeshop/test_query/test_model_mutation_flows_api.py::test_unnamed_raw_relation_list_is_charged_before_any_write`

Package tier (lines no real query reaches):

- `tests/utils/test_inputs.py::test_predicted_input_field_name_is_the_default_converters_name`
- `tests/utils/test_inputs.py::test_optional_field_kwargs_defaults_none_and_names_only_a_keyword_escape`
- `tests/mutations/test_inputs.py::test_mutation_input_field_specs_record_the_bind_time_wire_name`
- `tests/mutations/test_inputs.py::test_generated_write_input_pair_is_refused_only_where_the_schema_names_it_alike`
- `tests/mutations/test_inputs.py::test_a_python_keyword_column_is_refused_naming_the_column`
- `tests/types/test_definition_order.py::test_generated_set_input_pair_is_refused_only_where_the_schema_names_it_alike`
- `tests/types/test_definition_order.py::test_custom_name_converter_collision_raises_at_schema_build`
- `tests/types/test_definition_order.py::test_camel_case_field_pair_is_two_fields_without_auto_camel_case`

## Doc updates

- `docs/README.md`: generated filter, order and mutation input fields follow the naming config;
  the keyword names and their `get_graphql_name` respelling; the per-schema refusal and the
  plain-schema drop.
- `docs/GLOSSARY.md`: the `filterset`, `orderset`, `input-type-generation`, `strawberry_config`
  and `djangoschema` rows.
- [`spec-027`][spec-027], [`spec-028`][spec-028], [`spec-036`][spec-036],
  [`spec-038`][spec-038] and [`spec-039`][spec-039] restate their naming sentences and point
  here.
- `CHANGELOGTODO.md` carries the change notes for the joint cut (Decision 7).

## Risks and open questions

- **Wire break for default-config consumers at digit boundaries.** Accepted: the rename makes
  each input field match its output field. The `0.0.15` release notes name the 31 fakeshop
  fields' shape and the hashed serializer type.
- **Answered: per schema or per class?** Names resolve per schema at build, never per class
  (Decision 3); the open question the card carried is closed.

## Out of scope (explicitly tracked elsewhere)

- Configurable logic keys - [`TODO-BETA-072-0.1.7`][kanban].

## Definition of done

- [ ] Under `auto_camel_case=False` every generated input field and lookup is snake case in
      SDL, and filters, orders and mutations work end to end under it; the keyword names keep
      their spelling.
- [ ] Under the default config the SDL changes only where Decision 1 says: the input fields the
      package caser spelled differently and the hashed serializer input types over them.
- [ ] A custom `NameConverter` names generated input fields as it names output fields.
- [ ] Write-error keys and the resource budget agree with the published names under every
      config.
- [ ] `DjangoSchema` refuses a pair its converter names alike, naming the declaration and the
      members; a plain `strawberry.Schema` publishes one, documented.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangoformmutation]: ../GLOSSARY.md#djangoformmutation
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangomodelformmutation]: ../GLOSSARY.md#djangomodelformmutation
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangoschema]: ../GLOSSARY.md#djangoschema
[glossary-execution-resource-policy]: ../GLOSSARY.md#execution-resource-policy
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-input-type-generation]: ../GLOSSARY.md#input-type-generation
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-orderset]: ../GLOSSARY.md#orderset
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-relatedorder]: ../GLOSSARY.md#relatedorder
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation
[glossary-strawberry_config]: ../GLOSSARY.md#strawberry_config

<!-- docs/SPECS/ -->
[spec-027]: spec-027-filters-0_0_8.md
[spec-028]: spec-028-orders-0_0_8.md
[spec-036]: spec-036-mutations-0_0_11.md
[spec-038]: spec-038-form_mutations-0_0_12.md
[spec-039]: spec-039-serializer_mutations-0_0_13.md
[spec-050]: spec-050-list_field_arguments-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[package-init]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
