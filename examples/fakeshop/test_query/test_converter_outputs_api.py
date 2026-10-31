"""Native HTTP converter verdicts requiring consumer scalar or column declarations.

Shipped scalar and library suites own ordinary scalar values, nullable outputs,
choice blanks and the non-null Shelf condition enum. These holders add nullable
choice columns with empty-option labels, reserved choice spellings, nullable
BigInt arguments, an invalid outbound BigInt, and real PostgreSQL container fields.

Container rows are unsaved model instances, so the HTTP serialization and SDL
checks work on SQLite too. Only importing Django's real ArrayField/HStoreField
needs the optional PostgreSQL driver. These requests exercise the published scalar
types and their serialized values.
"""

from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from functools import wraps
from types import ModuleType
from typing import TYPE_CHECKING, Annotated

import pytest
import strawberry
from apps.library import models as library_models
from django.db import connection, models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql import GraphQLEnumType, GraphQLInputObjectType, get_named_type
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_str,
    read_attr,
)
from strategy_schemas import make_django_type
from typing_extensions import override

from django_strawberry_framework import (
    BigInt,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterInput, FilterSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils._narrowing import (
    is_concrete_field,
    require,
    require_instance,
)
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
    object_result,
)
from django_strawberry_framework.views import DjangoGraphQLView

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-converter/", _graphql_view)]


def _post(
    schema: DjangoSchema,
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables=variables, url="/graphql-converter/")
    finally:
        _CURRENT["schema"] = None


_EMPTY_LABEL_CHOICES: list[tuple[str | None, str]] = [
    (None, "Unassessed"),
    ("good", "Good"),
    ("worn", "Worn"),
]


def _choice_model(
    choices: list[tuple[str | None, str]],
    *,
    blank: bool = False,
) -> type[models.Model]:
    class ChoiceCarrier(models.Model):
        status: "models.TextField[str | Combinable | None, str | None]" = models.TextField(  # noqa: DJ001 - NULL is the fixture input
            choices=choices,
            blank=blank,
            null=True,
        )

        class Meta:
            app_label = "scalars"
            managed = False
            db_table = "converter_choice_carrier"

        @override
        def __str__(self) -> str:
            return str(self.status)

    return ChoiceCarrier


def _choice_schema(model: type[models.Model], values: list[str | None]) -> DjangoSchema:
    type_cls = make_django_type("FixtureType", model, ("status",), node=False)

    def _owners() -> list[models.Model]:
        return [model(status=value) for value in values]

    @strawberry.type
    class Query:
        owners: list[models.Model] = strawberry.field(
            resolver=_owners,
            graphql_type=list[type_cls],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.parametrize("wire", ["null", "0"], ids=["explicit-null", "present-zero"])
def test_a_nullable_bigint_argument_distinguishes_null_from_a_present_integer(wire: str) -> None:
    """A nullable argument delivers None for null and still parses a present zero as an integer."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt | None = None) -> str:
            return "null" if val is None else str(val + 1)

    schema = DjangoSchema(query=Query, config=strawberry_config())
    payload = _post(schema, "{ echo(val: " + wire + ") }")
    assert payload == {"data": {"echo": "null" if wire == "null" else "1"}}


@pytest.mark.parametrize("raw_value", [True, 7], ids=["refuse-bool", "accept-integer"])
def test_an_outbound_bigint_rejects_bool_beside_its_integer_control(raw_value: int) -> None:
    """Bool never serializes as a BigInt even though Python admits it to the int-shaped NewType."""

    @strawberry.type
    class Query:
        @strawberry.field
        def value(self) -> BigInt:
            return BigInt(raw_value)

    schema = DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})
    payload = _post(schema, "{ value }")
    if type(raw_value) is bool:
        assert payload["data"] is None, payload
        assert len(json_list(payload, "errors")) == 1
        assert json_at(payload, "errors", 0, "path") == ["value"]
        assert (
            json_str(payload, "errors", 0, "message") == "BigInt cannot serialize bool value True"
        )
    else:
        assert payload == {"data": {"value": "7"}}


def test_a_nullable_empty_label_choice_reads_null_blank_and_a_declared_member() -> None:
    """The empty-option label is not an enum value; null, BLANK and good stay distinct on the wire."""
    model = _choice_model(_EMPTY_LABEL_CHOICES, blank=True)
    schema = _choice_schema(model, [None, "", "good"])
    payload = _post(
        schema,
        '{ owners { status } __type(name: "FixtureTypeStatusEnum") { enumValues { name } } }',
    )
    assert payload == {
        "data": {
            "owners": [{"status": None}, {"status": "BLANK"}, {"status": "good"}],
            "__type": {"enumValues": [{"name": "BLANK"}, {"name": "good"}, {"name": "worn"}]},
        },
    }


@contextmanager
def _choice_table(model: type[models.Model]) -> Generator[None, None, None]:
    with connection.schema_editor() as editor:
        editor.create_model(model)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("wire", "stored"),
    [
        (None, None),
        ("BLANK", ""),
        ("good", "good"),
        ("_None", "refused"),
    ],
    ids=[
        "null",
        "blank",
        "declared-member",
        "empty-label-is-not-a-member",
    ],
)
def test_a_nullable_empty_label_choice_write_preserves_the_three_stored_values(
    wire: str | None,
    stored: str | None,
) -> None:
    """Valid nullable/blank/member values persist exactly; the empty-option spelling stores no row."""
    owner_model = _choice_model(_EMPTY_LABEL_CHOICES, blank=True)

    class NullableChoiceType(DjangoType):
        class Meta:
            model = owner_model
            fields = ("id", "status")
            primary = True

    class CreateNullableChoice(DjangoMutation):
        class Meta:
            model = owner_model
            operation = "create"
            fields = ("status",)
            permission_classes = []

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        create_owner = DjangoMutationField(CreateNullableChoice)

    finalize_django_types()
    assert registry.get(owner_model) is NullableChoiceType
    schema = DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config())
    document = """
    mutation ($status: NullableChoiceTypeStatusEnum) {
      createOwner(data: { status: $status }) {
        result { status }
        errors { field messages }
      }
    }
    """
    with _choice_table(owner_model):
        payload = _post(schema, document, variables={"status": wire})
        if stored == "refused":
            assert payload["data"] is None, payload
            assert len(json_list(payload, "errors")) == 1
            assert (
                "Value '_None' does not exist in 'NullableChoiceTypeStatusEnum' enum."
                in json_str(
                    payload,
                    "errors",
                    0,
                    "message",
                )
            )
            assert owner_model._default_manager.count() == 0
        else:
            assert payload == {"data": {"createOwner": {"result": {"status": wire}, "errors": []}}}
            rows = list(owner_model._default_manager.all())
            assert len(rows) == 1
            assert read_attr(rows[0], "status") == stored


_CHOICE_CASES: dict[str, tuple[list[tuple[str | None, str]], list[str]]] = {
    "graphql-reserved": (
        [
            ("true", "True"),
            ("FALSE", "False"),
            ("null", "Null"),
            ("caf\u00e9", "Cafe"),
            ("__private", "Private"),
            ("active", "Active"),
        ],
        [
            "MEMBER_true",
            "MEMBER_FALSE",
            "MEMBER_null",
            "caf_",
            "MEMBER___private",
            "active",
        ],
    ),
    "python-reserved": (
        [
            ("-x-", "Dash X"),
            ("mro", "Method Resolution Order"),
            ("_ignore_", "Ignore Directive"),
            ("_FixtureTypeStatusEnum__hidden", "Private Namespace"),
            ("active", "Active"),
        ],
        [
            "MEMBER__x_",
            "MEMBER_mro",
            "MEMBER__ignore_",
            "MEMBER__FixtureTypeStatusEnum__hidden",
            "active",
        ],
    ),
}


@pytest.mark.parametrize("case", ["graphql-reserved", "python-reserved"])
def test_reserved_choice_values_publish_and_serialize_all_members(case: str) -> None:
    """Reserved values survive as safe distinct members, while an ordinary value stays unchanged."""
    choices, names = _CHOICE_CASES[case]
    model = _choice_model(choices)
    schema = _choice_schema(model, [value for value, _label in choices])
    payload = _post(
        schema,
        '{ owners { status } __type(name: "FixtureTypeStatusEnum") { enumValues { name } } }',
    )
    assert payload == {
        "data": {
            "owners": [{"status": name} for name in names],
            "__type": {"enumValues": [{"name": name} for name in names]},
        },
    }


def _container_field(kind: str, *, nullable: bool) -> models.Field[object, object]:
    module = require_instance(
        object_result(pytest.importorskip, "django.contrib.postgres.fields", exc_type=ImportError),
        ModuleType,
    )
    constructor = read_attr(module, "ArrayField" if kind == "array" else "HStoreField")
    assert callable(constructor)
    if kind == "array":
        integer_field: models.IntegerField[float | int | str | Combinable, int] = (
            models.IntegerField()
        )
        field = object_result(constructor, integer_field, null=nullable)
    else:
        field = object_result(constructor, null=nullable)
    return require(field, is_concrete_field)


def _container_model(field: models.Field[object, object]) -> type[models.Model]:
    class ContainerCarrier(models.Model):
        value = field

        class Meta:
            app_label = "scalars"
            managed = False

        @override
        def __str__(self) -> str:
            return "container"

    return ContainerCarrier


def _container_schema(model: type[models.Model], payload: object) -> DjangoSchema:
    type_cls = make_django_type("ContainerType", model, ("value",), node=False)

    def _owner() -> models.Model:
        return model(value=payload)

    @strawberry.type
    class Query:
        owner: models.Model = strawberry.field(resolver=_owner, graphql_type=type_cls)

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_CONTAINER_QUERY = """
{
  owner { value }
  __type(name: "ContainerType") {
    fields {
      name
      type {
        kind name
        ofType {
          kind name
          ofType {
            kind name
            ofType {
              kind name
              ofType { kind name }
            }
          }
        }
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    ("nullable", "payload"),
    [(False, [1, 2, 3]), (False, []), (True, None)],
    ids=["integer-members", "empty-list", "nullable-outer"],
)
def test_real_array_field_publishes_and_serializes_its_integer_element_type(
    *,
    nullable: bool,
    payload: list[int] | None,
) -> None:
    """Real ArrayField publishes each wrapper and preserves integer members, [] and outer null."""
    model = _container_model(_container_field("array", nullable=nullable))
    schema = _container_schema(model, payload)
    integer: JSONObject = {"kind": "SCALAR", "name": "Int", "ofType": None}
    members: JSONObject = {"kind": "NON_NULL", "name": None, "ofType": integer}
    array: JSONObject = {"kind": "LIST", "name": None, "ofType": members}
    expected_type: JSONObject = (
        array if nullable else {"kind": "NON_NULL", "name": None, "ofType": array}
    )
    result = _post(schema, _CONTAINER_QUERY)
    assert result == {
        "data": {
            "owner": {"value": payload},
            "__type": {"fields": [{"name": "value", "type": expected_type}]},
        },
    }


@pytest.mark.parametrize(
    ("nullable", "payload"),
    [
        (False, {"k1": "v1"}),
        (False, {"k1": "v", "k2": None}),
        (False, {}),
        (True, None),
    ],
    ids=[
        "string-values",
        "null-member",
        "empty-map",
        "nullable-outer",
    ],
)
def test_real_hstore_field_publishes_json_and_preserves_each_member(
    *,
    nullable: bool,
    payload: dict[str, str | None] | None,
) -> None:
    """Real HStoreField publishes JSON and preserves string/null members, empty maps and outer null."""
    model = _container_model(_container_field("hstore", nullable=nullable))
    schema = _container_schema(model, payload)
    scalar: JSONObject = {"kind": "SCALAR", "name": "JSON", "ofType": None}
    expected_type: JSONObject = (
        scalar if nullable else {"kind": "NON_NULL", "name": None, "ofType": scalar}
    )
    result = _post(schema, _CONTAINER_QUERY)
    assert result == {
        "data": {
            "owner": {"value": payload},
            "__type": {"fields": [{"name": "value", "type": expected_type}]},
        },
    }


_CHOICE_FILTER_LOOKUPS = (
    ("exact", "exact", ("",)),
    ("iexact", "iExact", ("",)),
    ("lte", "lte", ("",)),
    ("lt", "lt", ()),
    ("gt", "gt", ("good", "worn")),
    ("gte", "gte", ("", "good", "worn")),
    ("contains", "contains", ("", "good", "worn")),
    ("icontains", "iContains", ("", "good", "worn")),
    ("startswith", "startsWith", ("", "good", "worn")),
    ("istartswith", "iStartsWith", ("", "good", "worn")),
    ("endswith", "endsWith", ("", "good", "worn")),
    ("iendswith", "iEndsWith", ("", "good", "worn")),
    ("regex", "regex", ("", "good", "worn")),
    ("iregex", "iRegex", ("", "good", "worn")),
)


def _filtered_choice_schema(owner_model: type[models.Model], lookups: list[str]) -> DjangoSchema:
    class ChoiceOwnerFilter(FilterSet):
        class Meta:
            model = owner_model
            fields = {"status": lookups}

    owner_type = make_django_type(
        "FilteredChoiceOwner",
        owner_model,
        ("status",),
        node=False,
        meta_extra={"filterset_class": ChoiceOwnerFilter},
    )

    @strawberry.type
    class Query:
        def _owners(
            self,
            info: strawberry.Info[object, object],
            where: Annotated[
                FilterInput[ChoiceOwnerFilter] | None,
                strawberry.argument(name="filter"),
            ] = None,
        ) -> models.QuerySet[models.Model]:
            return ChoiceOwnerFilter.apply_sync(
                where,
                owner_model._default_manager.order_by("pk"),
                info,
            )

        owners: models.QuerySet[models.Model] = strawberry.field(
            resolver=_owners,
            graphql_type=list[owner_type],
        )

        def _raw_owners(self, value: str) -> models.QuerySet[models.Model]:
            form_key = ChoiceOwnerFilter.get_filter_name("status", lookups[0])
            return ChoiceOwnerFilter(
                data={form_key: value},
                queryset=owner_model._default_manager.order_by("pk"),
            ).qs

        raw_owners: models.QuerySet[models.Model] = strawberry.field(
            resolver=_raw_owners,
            graphql_type=list[owner_type],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _choice_filter_types(
    schema: DjangoSchema,
    wire_lookup: str,
    *,
    head: str = "status",
) -> tuple[str, GraphQLEnumType]:
    query = schema._schema.query_type
    assert query is not None
    where = get_named_type(graphql_type_of(graphql_fields(query)["owners"].args["filter"]))
    assert isinstance(where, GraphQLInputObjectType)
    status = get_named_type(graphql_type_of(graphql_input_fields(where)[head]))
    assert isinstance(status, GraphQLInputObjectType)
    member = get_named_type(graphql_type_of(graphql_input_fields(status)[wire_lookup]))
    assert isinstance(member, GraphQLEnumType)
    return where.name, member


def _filter_choices(schema: DjangoSchema, where_type: str, where: JSONObject) -> JSONObject:
    return _post(
        schema,
        f"query($where: {where_type}!) {{ owners(filter: $where) {{ status }} }}",
        variables={"where": where},
    )


def _choice_members_payload(
    enum_type: GraphQLEnumType,
    values: Sequence[object],
    *,
    root: str = "owners",
) -> JSONObject:
    return {
        "data": {
            root: [
                {"status": None if value is None else enum_type.serialize(value)}
                for value in values
            ],
        },
    }


def _store_choice_values(owner_model: type[models.Model], values: Sequence[object]) -> None:
    for value in values:
        owner_model._default_manager.create(status=value)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("lookup", "wire_lookup", "expected"),
    _CHOICE_FILTER_LOOKUPS,
    ids=[case[0] for case in _CHOICE_FILTER_LOOKUPS],
)
def test_a_blank_enum_member_applies_its_predicate_and_excludes_null_on_every_text_lookup(
    lookup: str,
    wire_lookup: str,
    expected: tuple[str, ...],
) -> None:
    """BLANK applies the chosen lookup to an empty string; the NULL row distinguishes it from omission."""
    model = _choice_model(_EMPTY_LABEL_CHOICES, blank=True)
    schema = _filtered_choice_schema(model, [lookup])
    where_type, enum_type = _choice_filter_types(schema, wire_lookup)
    with _choice_table(model):
        _store_choice_values(
            model,
            [
                "",
                "good",
                "worn",
                None,
            ],
        )
        assert _filter_choices(schema, where_type, {}) == _choice_members_payload(
            enum_type,
            [
                "",
                "good",
                "worn",
                None,
            ],
        )
        assert _filter_choices(
            schema,
            where_type,
            {"status": {wire_lookup: enum_type.serialize("")}},
        ) == _choice_members_payload(enum_type, list(expected))


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("lookup", "wire_lookup"),
    [("exact", "exact"), ("iexact", "iExact")],
    ids=["exact", "i-exact"],
)
def test_a_null_spelled_enum_member_selects_the_literal_value_instead_of_sql_null(
    lookup: str,
    wire_lookup: str,
) -> None:
    """The enum's literal null spelling selects that stored text while the SQL NULL row stays out."""
    model = _choice_model([("null", "Null"), ("other", "Other")])
    schema = _filtered_choice_schema(model, [lookup])
    where_type, enum_type = _choice_filter_types(schema, wire_lookup)
    with _choice_table(model):
        _store_choice_values(model, [None, "null", "other"])
        assert _filter_choices(schema, where_type, {}) == _choice_members_payload(
            enum_type,
            [None, "null", "other"],
        )
        assert _filter_choices(
            schema,
            where_type,
            {"status": {wire_lookup: enum_type.serialize("null")}},
        ) == _choice_members_payload(enum_type, ["null"])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("lookup", "wire_lookup"),
    [("exact", "exact"), ("iexact", "iExact")],
    ids=["exact", "i-exact"],
)
def test_a_padded_enum_member_selects_its_untrimmed_value_over_the_trimmed_decoy(
    lookup: str,
    wire_lookup: str,
) -> None:
    """A whitespace-bearing enum member selects its complete stored value, never its stripped decoy."""
    model = _choice_model([(" padded ", "Padded"), ("padded", "Trimmed")])
    schema = _filtered_choice_schema(model, [lookup])
    where_type, enum_type = _choice_filter_types(schema, wire_lookup)
    with _choice_table(model):
        _store_choice_values(model, [None, " padded ", "padded"])
        assert _filter_choices(schema, where_type, {}) == _choice_members_payload(
            enum_type,
            [None, " padded ", "padded"],
        )
        assert _filter_choices(
            schema,
            where_type,
            {"status": {wire_lookup: enum_type.serialize(" padded ")}},
        ) == _choice_members_payload(enum_type, [" padded "])


def _raw_filter_choices(schema: DjangoSchema, value: str) -> JSONObject:
    return _post(
        schema,
        "query($value: String!) { rawOwners(value: $value) { status } }",
        variables={"value": value},
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("lookup", "wire_lookup"),
    [(lookup, wire) for lookup, wire, _expected in _CHOICE_FILTER_LOOKUPS],
    ids=[case[0] for case in _CHOICE_FILTER_LOOKUPS],
)
def test_a_raw_empty_form_string_keeps_the_upstream_skip_on_every_text_choice_lookup(
    lookup: str,
    wire_lookup: str,
) -> None:
    """A consumer String argument keeps raw empty form data distinct from the BLANK enum member."""
    model = _choice_model(_EMPTY_LABEL_CHOICES, blank=True)
    schema = _filtered_choice_schema(model, [lookup])
    _where_type, enum_type = _choice_filter_types(schema, wire_lookup)
    with _choice_table(model):
        _store_choice_values(
            model,
            [
                "",
                "good",
                "worn",
                None,
            ],
        )
        assert _raw_filter_choices(schema, "") == _choice_members_payload(
            enum_type,
            [
                "",
                "good",
                "worn",
                None,
            ],
            root="rawOwners",
        )


@pytest.mark.django_db(transaction=True)
def test_a_raw_null_form_string_keeps_the_upstream_null_choice_meaning() -> None:
    """A consumer's raw null sentinel selects SQL NULL while the literal text remains a decoy."""
    model = _choice_model([("null", "Null"), ("other", "Other")])
    schema = _filtered_choice_schema(model, ["exact"])
    _where_type, enum_type = _choice_filter_types(schema, "exact")
    with _choice_table(model):
        _store_choice_values(model, [None, "null", "other"])
        assert _raw_filter_choices(schema, "other") == _choice_members_payload(
            enum_type,
            ["other"],
            root="rawOwners",
        )
        assert _raw_filter_choices(schema, "null") == _choice_members_payload(
            enum_type,
            [None],
            root="rawOwners",
        )


@pytest.mark.django_db(transaction=True)
def test_a_raw_text_choice_pattern_accepts_text_outside_the_enum_members() -> None:
    """A consumer String argument can search a choice column by a partial raw form value."""
    model = _choice_model(_EMPTY_LABEL_CHOICES, blank=True)
    schema = _filtered_choice_schema(model, ["icontains"])
    _where_type, enum_type = _choice_filter_types(schema, "iContains")
    with _choice_table(model):
        _store_choice_values(model, [None, "good", "worn"])
        assert _raw_filter_choices(schema, "wo") == _choice_members_payload(
            enum_type,
            ["worn"],
            root="rawOwners",
        )


@pytest.mark.django_db(transaction=True)
def test_a_raw_empty_integer_choice_argument_keeps_the_unfiltered_rows() -> None:
    """An empty raw String skips an integer-choice predicate instead of binding an empty integer."""

    class IntegerChoiceCarrier(models.Model):
        status: "models.IntegerField[float | int | str | Combinable | None, int | None]" = (
            models.IntegerField(
                choices=[(1, "Low"), (2, "High")],
                blank=True,
                null=True,
            )
        )

        class Meta:
            app_label = "scalars"
            managed = False
            db_table = "converter_integer_choice_carrier"

        @override
        def __str__(self) -> str:
            return str(self.status)

    schema = _filtered_choice_schema(IntegerChoiceCarrier, ["exact"])
    _where_type, enum_type = _choice_filter_types(schema, "exact")
    with _choice_table(IntegerChoiceCarrier):
        _store_choice_values(IntegerChoiceCarrier, [1, 2, None])
        assert _raw_filter_choices(schema, "1") == _choice_members_payload(
            enum_type,
            [1],
            root="rawOwners",
        )
        assert _raw_filter_choices(schema, "") == _choice_members_payload(
            enum_type,
            [1, 2, None],
            root="rawOwners",
        )


@pytest.mark.django_db
def test_a_to_many_blank_choice_search_uses_exists_without_duplicating_its_parent(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The generated choice leaf constrains the parent through one EXISTS and keeps its multiplicity."""
    blank = library_models.Branch.objects.create(name="blank")
    graded = library_models.Branch.objects.create(name="graded")
    library_models.Branch.objects.create(name="empty")
    library_models.Shelf.objects.create(code="b1", branch=blank)
    library_models.Shelf.objects.create(code="b2", branch=blank)
    library_models.Shelf.objects.create(code="g", branch=graded, condition="good")

    class BranchConditionFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"shelves__condition": ["iexact"]}

    class BranchChoiceOwner(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("name",)
            filterset_class = BranchConditionFilter

    @strawberry.type
    class Query:
        def _owners(
            self,
            info: strawberry.Info[object, object],
            where: Annotated[
                FilterInput[BranchConditionFilter],
                strawberry.argument(name="filter"),
            ],
        ) -> models.QuerySet[library_models.Branch]:
            return BranchConditionFilter.apply_sync(
                where,
                library_models.Branch.objects.order_by("pk"),
                info,
            )

        owners: models.QuerySet[library_models.Branch] = strawberry.field(
            resolver=_owners,
            graphql_type=list[BranchChoiceOwner],
        )

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config())
    where_type, enum_type = _choice_filter_types(schema, "iExact", head="shelvesCondition")
    sql = record_compiled_sql()
    assert _post(
        schema,
        f"query($where: {where_type}!) {{ owners(filter: $where) {{ name }} }}",
        variables={"where": {"shelvesCondition": {"iExact": enum_type.serialize("")}}},
    ) == {"data": {"owners": [{"name": "blank"}]}}
    roots = [statement for statement in sql if 'FROM "library_branch"' in statement]
    assert len(roots) == 1, sql
    assert roots[0].upper().count("EXISTS") == 1, roots
    assert "DISTINCT" not in roots[0].upper(), roots
