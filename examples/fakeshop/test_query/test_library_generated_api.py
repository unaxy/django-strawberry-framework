"""Live GraphQL HTTP tests for the library ``Shelf``'s database-computed (``GeneratedField``) columns.

``Shelf.code_length`` computes ``LENGTH(code)`` into a ``BigIntegerField`` and
``Shelf.topic_length`` computes ``LENGTH(NULLIF(topic, ''))`` into a nullable
``IntegerField``. Each reads, filters and orders as the column it computes (its
``output_field``): ``codeLength: BigInt!`` and ``topicLength: Int`` on ``ShelfType``'s
explicit field list and on a private ``fields = "__all__"`` type, integer lookups on
``ShelfFilter`` (nested through ``BookFilter.shelf`` too), the integer ``in`` dropping a
member past the column's 64-bit range and the integer ``range`` applying a bound past it
as Django's range-aware ``gte`` / ``lte``, and ordering with nulls placed as asked. Both are
absent from every generated write input (Django forces ``editable=False``), a form
update returns the value the database recomputed, and a ``relay.NodeID`` over
``code_length`` refetches its row by the integer it computes. A lookup or transform
registered on ``code_length``'s ``output_field`` instance, where Django's query resolves
the column's lookups, is the generated column's: Django's ``Chr`` types its operand
``String`` and matches, a text pattern takes a ``String``, a per-field ``"__all__"``
publishes it (and a class registration made after the model was built), and a
target-less ``GlobalIDFilter`` codes its node id through the column. A registration
there (or on the output class after the model was built) that replaces a name the
generated field's own copy of its output class's lookups holds is the one the leaf
publishes: ``Exact`` as ``contains`` takes the column's ``BigInt``, ``Chr`` as
``endswith`` a ``String`` on a generated or declared leaf, and a ``GlobalIDFilter``
hands that transform its node id uncoded.
"""

import contextlib
from collections.abc import Generator, Iterator
from typing import ClassVar

import pytest
import strawberry
from apps.library import models
from django.db import models as django_models
from django.db.models.functions import Chr
from django.db.models.lookups import Contains, Exact, Lookup, Transform
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import override_settings
from django.test.utils import register_lookup
from django.urls import path
from django_filters import CharFilter, Filter, NumberFilter
from graphql_client import (
    JSONObject,
    json_at,
    json_list,
    response_json,
)
from graphql_client import assert_graphql_success as _assert_graphql_success
from graphql_client import post_graphql as _post_graphql
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoListField,
    DjangoMutation,
    DjangoMutationField,
    DjangoNodeField,
    DjangoNodesField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, GlobalIDFilter
from django_strawberry_framework.filters.base import _lookup_operand, _model_lookup_operand
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import DjangoGraphQLView

#: One past the largest value a signed 64-bit column stores.
_PAST_BIGINT = 2**63

_SHELF_ROWS = (("A", ""), ("CC", "abcd"), ("BBB", "xy"))


def _seed_shelves(rows: tuple[tuple[str, str], ...] = _SHELF_ROWS) -> None:
    """Shelves ``A`` (topic ``""``), ``CC`` (topic ``abcd``) and ``BBB`` (topic ``xy``), in ``rows`` order."""
    branch = models.Branch.objects.create(name="Generated", city="open")
    for code, topic in rows:
        _ = models.Shelf.objects.create(code=code, topic=topic, branch=branch)


def _codes(query: str, variables: dict[str, object] | None = None) -> list[str]:
    """Return the ``code`` of every shelf ``allLibraryShelves`` answers, in order."""
    data = _assert_graphql_success(query, variables=variables)
    return [str(json_at(row, "code")) for row in json_list(data, "allLibraryShelves")]


def _field_types(type_name: str) -> dict[str, str]:
    """Return ``{field: rendered type}`` for an object type, ``!`` marking a non-null one."""
    data = _assert_graphql_success(
        f'{{ __type(name: "{type_name}") {{ fields {{ name type {{ kind name ofType {{ name }} }} }} }} }}',
    )
    rendered: dict[str, str] = {}
    for field in json_list(data, "__type", "fields"):
        kind = json_at(field, "type", "kind")
        if kind == "NON_NULL":
            rendered[str(json_at(field, "name"))] = f"{json_at(field, 'type', 'ofType', 'name')}!"
        else:
            rendered[str(json_at(field, "name"))] = str(json_at(field, "type", "name"))
    return rendered


@pytest.mark.django_db
def test_generated_columns_read_as_their_output_columns_over_http() -> None:
    """``codeLength`` is ``BigInt!`` and ``topicLength`` ``Int``, ``null`` for an empty topic."""
    _seed_shelves()

    types = _field_types("ShelfType")
    assert (types["codeLength"], types["topicLength"]) == ("BigInt!", "Int")
    data = _assert_graphql_success("{ allLibraryShelves { code codeLength topicLength } }")
    assert json_list(data, "allLibraryShelves") == [
        {"code": "A", "codeLength": "1", "topicLength": None},
        {"code": "CC", "codeLength": "2", "topicLength": 4},
        {"code": "BBB", "codeLength": "3", "topicLength": 2},
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("leaf", "expected"),
    [
        pytest.param("codeLength: {exact: 2}", ["CC"], id="code-exact"),
        pytest.param("codeLength: {gt: 1}", ["CC", "BBB"], id="code-gt"),
        pytest.param("codeLength: {lt: 3}", ["A", "CC"], id="code-lt"),
        pytest.param("codeLength: {in: [1, 3]}", ["A", "BBB"], id="code-in"),
        pytest.param("codeLength: {range: [2, 3]}", ["CC", "BBB"], id="code-range"),
        pytest.param("codeLength: {isNull: true}", [], id="code-isnull"),
        pytest.param("topicLength: {exact: 4}", ["CC"], id="topic-exact"),
        pytest.param("topicLength: {gt: 2}", ["CC"], id="topic-gt"),
        pytest.param("topicLength: {lt: 4}", ["BBB"], id="topic-lt"),
        pytest.param("topicLength: {in: [2, 4]}", ["CC", "BBB"], id="topic-in"),
        pytest.param("topicLength: {range: [1, 3]}", ["BBB"], id="topic-range"),
        pytest.param("topicLength: {isNull: true}", ["A"], id="topic-isnull"),
        pytest.param("topicLength: {isNull: false}", ["CC", "BBB"], id="topic-not-null"),
    ],
)
def test_generated_columns_filter_as_their_output_columns_over_http(
    leaf: str,
    expected: list[str],
) -> None:
    """Every generated integer lookup filters the computed column."""
    _seed_shelves()

    assert _codes(f"{{ allLibraryShelves(filter: {{{leaf}}}) {{ code }} }}") == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("leaf", "expected"),
    [
        pytest.param({"in": [_PAST_BIGINT]}, [], id="in-all-out-of-range"),
        pytest.param({"in": [_PAST_BIGINT, 3]}, ["BBB"], id="in-mixed"),
        pytest.param({"range": [2, _PAST_BIGINT]}, ["CC", "BBB"], id="range-upper-past"),
        pytest.param({"range": [_PAST_BIGINT, _PAST_BIGINT + 1]}, [], id="range-lower-past"),
    ],
)
def test_generated_bigint_lookups_hold_values_past_the_column_range_over_http(
    leaf: dict[str, object],
    expected: list[str],
) -> None:
    """A ``codeLength`` value past 64 bits never reaches the database as a raw bind.

    The ``in`` member is dropped (a list whose every member drops matches no row) and a
    ``range`` bound applies as Django's range-aware ``gte`` / ``lte``: the guards read the
    column the generated field computes (a ``BigIntegerField``), never the error a raw
    ``OverflowError`` would mask.
    """
    _seed_shelves()

    assert (
        _codes(
            "query ($f: ShelfFilterInputType) { allLibraryShelves(filter: $f) { code } }",
            variables={"f": {"codeLength": leaf}},
        )
        == expected
    )


@pytest.mark.django_db
def test_generated_column_filters_through_a_related_filter_over_http() -> None:
    """``BookFilter.shelf`` reaches ``ShelfFilter``'s generated leaves, nested."""
    _seed_shelves()
    for shelf in models.Shelf.objects.all():
        _ = models.Book.objects.create(shelf=shelf, title=f"On {shelf.code}")

    data = _assert_graphql_success(
        "{ allLibraryBooks(filter: {shelf: {codeLength: {gt: 1}, topicLength: {lt: 4}}}) "
        "{ title } }",
    )
    assert json_list(data, "allLibraryBooks") == [{"title": "On BBB"}]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("order", "expected"),
    [
        pytest.param("{codeLength: ASC}", ["A", "CC", "BBB"], id="code-asc"),
        pytest.param("{codeLength: DESC}", ["BBB", "CC", "A"], id="code-desc"),
        pytest.param("{topicLength: ASC_NULLS_LAST}", ["BBB", "CC", "A"], id="topic-asc"),
        pytest.param("{topicLength: DESC_NULLS_FIRST}", ["A", "CC", "BBB"], id="topic-desc"),
    ],
)
def test_generated_columns_order_over_http(order: str, expected: list[str]) -> None:
    """Both generated columns order, the nullable one with its nulls placed as asked.

    The shelves are stored ``BBB``, ``A``, ``CC``, an order no expected answer shares, so
    every row tells an applied order from the primary-key order.
    """
    _seed_shelves((_SHELF_ROWS[2], _SHELF_ROWS[0], _SHELF_ROWS[1]))

    assert _codes(f"{{ allLibraryShelves(orderBy: [{order}]) {{ code }} }}") == expected


@pytest.mark.django_db
def test_form_update_returns_the_recomputed_generated_column_over_http() -> None:
    """``updateShelfViaForm`` answers the ``codeLength`` the database computed for the new code."""
    _seed_shelves()
    shelf = models.Shelf.objects.get(code="A")

    data = _assert_graphql_success(
        "mutation ($id: ID!, $d: ShelfRelationsFormPartialInput!) "
        "{ updateShelfViaForm(id: $id, data: $d) { result { code codeLength } errors { field } } }",
        variables={"id": shelf.pk, "d": {"code": "EEEEE"}},
    )
    assert json_at(data, "updateShelfViaForm") == {
        "result": {"code": "EEEEE", "codeLength": "5"},
        "errors": [],
    }


_HOLDER: dict[str, DjangoSchema | None] = {"schema": None}


def _holder_view(request: HttpRequest) -> HttpResponseBase:
    schema = _HOLDER["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _holder_view)]


@pytest.fixture
def all_fields_shelf_schema(private_registry: None) -> Iterator[DjangoSchema]:
    """Serve a ``fields = "__all__"`` shelf type and a mutation that names no field list.

    ``GeneratedShelfType`` selects every column and relation, the two generated columns
    included (each relation target gets a minimal type), and
    ``CreateGeneratedShelf`` writes every editable one, which leaves both out.
    """
    del private_registry

    class GeneratedBranchType(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("id", "name")

    class GeneratedBookType(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")

    class GeneratedDeskType(DjangoType):
        class Meta:
            model = models.CirculationDesk
            fields = ("id",)

    class GeneratedLabelType(DjangoType):
        class Meta:
            model = models.ShelfLabel
            fields = ("id",)

    class GeneratedShelfType(DjangoType):
        class Meta:
            model = models.Shelf
            fields = "__all__"

    class CreateGeneratedShelf(DjangoMutation):
        class Meta:
            model = models.Shelf
            operation = "create"
            permission_classes = []

    @strawberry.type
    class Query:
        shelves: list[GeneratedShelfType] = DjangoListField(GeneratedShelfType)

    @strawberry.type
    class Mutation:
        create_generated_shelf = DjangoMutationField(CreateGeneratedShelf)

    del GeneratedBranchType, GeneratedBookType, GeneratedDeskType, GeneratedLabelType
    finalize_django_types()
    schema = DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config())
    _HOLDER["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            yield schema
    finally:
        _HOLDER["schema"] = None


def _holder_payload(query: str, variables: dict[str, object] | None = None) -> JSONObject:
    response = _post_graphql(query, variables=variables, url="/graphql-test/")
    assert response.status_code == 200
    payload = response_json(response)
    assert "errors" not in payload, payload
    return payload


@pytest.mark.django_db
@pytest.mark.usefixtures("all_fields_shelf_schema")
def test_all_fields_type_reads_generated_columns_over_http() -> None:
    """``fields = "__all__"`` selects both generated columns with their output types."""
    _seed_shelves()

    payload = _holder_payload(
        '{ __type(name: "GeneratedShelfType") { fields { name type { kind name ofType { name } } } } '
        "shelves { code codeLength topicLength } }",
    )
    fields = {
        str(json_at(field, "name")): json_at(field, "type")
        for field in json_list(payload, "data", "__type", "fields")
    }
    assert fields["codeLength"] == {"kind": "NON_NULL", "name": None, "ofType": {"name": "BigInt"}}
    assert fields["topicLength"] == {"kind": "SCALAR", "name": "Int", "ofType": None}
    rows = sorted(
        (str(json_at(row, "code")), json_at(row, "codeLength"), json_at(row, "topicLength"))
        for row in json_list(payload, "data", "shelves")
    )
    assert rows == [("A", "1", None), ("BBB", "3", 2), ("CC", "2", 4)]


@pytest.mark.django_db
@pytest.mark.usefixtures("all_fields_shelf_schema")
def test_no_field_list_mutation_input_omits_generated_columns_over_http() -> None:
    """A model mutation over every editable column publishes neither generated column."""
    payload = _holder_payload(
        "{ __schema { mutationType { fields { name args { name type { ofType { name } } } } } } }",
    )
    (mutation,) = json_list(payload, "data", "__schema", "mutationType", "fields")
    (data_arg,) = (arg for arg in json_list(mutation, "args") if json_at(arg, "name") == "data")
    input_name = str(json_at(data_arg, "type", "ofType", "name"))
    input_fields = _holder_payload(
        f'{{ __type(name: "{input_name}") {{ inputFields {{ name }} }} }}',
    )
    names = {
        str(json_at(field, "name"))
        for field in json_list(input_fields, "data", "__type", "inputFields")
    }
    assert "code" in names
    assert not names & {"codeLength", "topicLength"}, names


@pytest.fixture
def generated_node_id_schema(private_registry: None) -> Iterator[DjangoSchema]:
    """Serve a Relay shelf type whose GlobalID carries the generated ``code_length``.

    ``GeneratedNodeShelfType`` declares ``code_length: relay.NodeID[int]``, so a node id
    names a shelf by the length its database computes; the root ``node`` / ``nodes`` fields
    refetch by it.
    """
    del private_registry

    class GeneratedNodeShelfType(DjangoType):
        code_length: relay.NodeID[int]

        class Meta:
            model = models.Shelf
            fields = ("code", "code_length")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=[GeneratedNodeShelfType],
        config=strawberry_config(),
    )
    _HOLDER["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            yield schema
    finally:
        _HOLDER["schema"] = None


def _shelf_node_id(code_length: object) -> str:
    """The GlobalID the registered shelf type answers for a shelf of ``code_length``."""
    shelf_type = registry.get(models.Shelf)
    assert shelf_type is not None
    return global_id_for(shelf_type, code_length)


@pytest.mark.django_db
@pytest.mark.usefixtures("generated_node_id_schema")
def test_node_id_over_a_generated_column_refetches_its_row_over_http() -> None:
    """A ``NodeID`` over ``code_length`` is coded as the ``BigIntegerField`` it computes.

    The decoded id text is cast to the column's integer before the lookup, so ``node`` and
    ``nodes`` answer the shelf whose computed length it names, and an id past 64 bits
    identifies no row (``null``, no error), never a raw bind the backend refuses.
    """
    _seed_shelves()

    payload = _holder_payload(
        "query ($one: ID!, $many: [ID!]!) { node(id: $one) { id ... on GeneratedNodeShelfType "
        "{ code } } nodes(ids: $many) { ... on GeneratedNodeShelfType { code } } }",
        variables={
            "one": _shelf_node_id(2),
            "many": [_shelf_node_id(3), _shelf_node_id(_PAST_BIGINT * 128), _shelf_node_id(1)],
        },
    )
    assert json_at(payload, "data") == {
        "node": {"id": _shelf_node_id(2), "code": "CC"},
        "nodes": [{"code": "BBB"}, None, {"code": "A"}],
    }
    past = _holder_payload(
        "query ($one: ID!) { node(id: $one) { id } }",
        variables={"one": _shelf_node_id(_PAST_BIGINT * 128)},
    )
    assert json_at(past, "data") == {"node": None}


class _Has(Contains):
    """``contains`` under a project's own name, a text pattern over the column's rendering."""

    lookup_name = "has"


@contextlib.contextmanager
def _instance_lookup(
    field: django_models.Field[object, object],
    lookup: type[Lookup] | type[Transform],
    lookup_name: str | None,
) -> Generator[None]:
    """Register ``lookup`` on the ``field`` instance alone (``Field.register_lookup``) while open."""
    name = lookup_name or lookup.lookup_name
    _ = field.register_instance_lookup(lookup, name)
    try:
        yield
    finally:
        del vars(field)["instance_lookups"][name]
        _clear_operand_caches()


@contextlib.contextmanager
def _class_lookup(
    field_class: type[django_models.Field[object, object]],
    lookup: type[Lookup] | type[Transform],
    lookup_name: str,
) -> Generator[None]:
    """Register ``lookup`` as ``lookup_name`` on ``field_class`` (``register_lookup``) while open."""
    try:
        with register_lookup(field_class, lookup, lookup_name=lookup_name):
            yield
    finally:
        _clear_operand_caches()


def _clear_operand_caches() -> None:
    """Drop the filter operands resolved while a test's lookup registration was live.

    ``filters/base.py`` caches each column's resolved lookup operand for the process; an
    entry written under a registration would outlive it into the next test on the worker.
    """
    _lookup_operand.cache_clear()
    _model_lookup_operand.cache_clear()


@contextlib.contextmanager
def _output_lookup_schema(
    owners: tuple[str, ...],
    lookup: type[Lookup] | type[Transform],
    lookup_expr: str,
    *,
    lookup_name: str | None = None,
    declared: dict[str, Filter] | None = None,
) -> Generator[DjangoSchema]:
    """Serve ``rows``, a shelf connection filtering ``code_length__<lookup_expr>``.

    ``lookup`` is registered (as ``lookup_name`` when given) on ``Shelf.code_length``'s
    ``output_field`` instance (where Django's query resolves the generated column's
    lookups) and, when ``owners`` names it, on the generated field instance too, for the
    schema's lifetime only. ``lookup_expr`` ``"__all__"`` is the per-field shorthand, every
    other value one lookup. ``declared`` adds filters to the set.
    """
    generated = models.Shelf._meta.get_field("code_length")
    assert isinstance(generated, django_models.GeneratedField)
    output = generated.output_field
    assert output is not None
    instances: dict[str, django_models.Field[object, object]] = {
        "generated": generated,
        "output": output,
    }
    with contextlib.ExitStack() as registrations:
        for owner in owners:
            registrations.enter_context(_instance_lookup(instances[owner], lookup, lookup_name))
        lookups: object = lookup_expr if lookup_expr == "__all__" else [lookup_expr]
        meta = type("Meta", (), {"model": models.Shelf, "fields": {"code_length": lookups}})
        lookup_filter = type(
            "LookupShelfFilter",
            (FilterSet,),
            {"Meta": meta, **(declared or {})},
        )
        assert issubclass(lookup_filter, FilterSet)
        with _rows_schema(models.Shelf, lookup_filter, ("id", "code")) as schema:
            yield schema


@contextlib.contextmanager
def _rows_schema(
    row_model: type[django_models.Model],
    filter_class: type[FilterSet],
    selected: tuple[str, ...],
) -> Generator[DjangoSchema]:
    """Serve ``rows``, a ``row_model`` connection selecting ``selected``, filtered by ``filter_class``."""

    class RowsType(DjangoType):
        class Meta:
            model = row_model
            fields = selected
            interfaces = (relay.Node,)
            filterset_class = filter_class

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(RowsType)

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config())
    _HOLDER["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            yield schema
    finally:
        _HOLDER["schema"] = None


def _operand_types(head: str) -> dict[str, str]:
    """Return ``{operand: input type}`` of ``LookupShelfFilter``'s ``head`` leaf."""
    heads = _holder_payload(
        '{ __type(name: "LookupShelfFilterInputType") { inputFields { name type { name } } } }',
    )
    (bag,) = (
        json_at(field, "type", "name")
        for field in json_list(heads, "data", "__type", "inputFields")
        if json_at(field, "name") == head
    )
    payload = _holder_payload(
        f'{{ __type(name: "{bag}") {{ inputFields {{ name type {{ name }} }} }} }}',
    )
    return {
        str(json_at(field, "name")): str(json_at(field, "type", "name"))
        for field in json_list(payload, "data", "__type", "inputFields")
    }


def _row_codes(where: str) -> list[str]:
    """Return the ``code`` of every row ``rows(filter: {where})`` answers."""
    payload = _holder_payload(f"{{ rows(filter: {{{where}}}) {{ edges {{ node {{ code }} }} }} }}")
    return [
        str(json_at(edge, "node", "code")) for edge in json_list(payload, "data", "rows", "edges")
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("owners", [("output",), ("generated", "output")], ids=["output", "both"])
def test_transform_registered_on_the_generated_output_types_its_operand_over_http(
    owners: tuple[str, ...],
    private_registry: None,
) -> None:
    """``codeLength`` through Django's ``Chr`` publishes and filters a ``String`` operand.

    Django resolves a generated column's lookups on its ``output_field`` instance, where
    ``Chr`` is registered, and the transform's output is a ``CharField``: the leaf is
    ``String``, ``"A"`` matches the shelf whose code is 65 characters long, and the
    integer ``65`` is refused as the wrong type.
    """
    del private_registry
    _seed_shelves((("A" * 65, ""), ("B" * 66, "")))

    with _output_lookup_schema(owners, Chr, "chr__exact"):
        assert _operand_types("codeLengthChr") == {"chr_Exact": "String"}
        assert _row_codes('codeLengthChr: {chr_Exact: "A"}') == ["A" * 65]
        refused = _post_graphql(
            "{ rows(filter: {codeLengthChr: {chr_Exact: 65}}) { edges { node { code } } } }",
            url="/graphql-test/",
        )
        assert "errors" in response_json(refused)


@pytest.mark.django_db
def test_text_pattern_registered_on_the_generated_output_takes_a_string_over_http(
    private_registry: None,
) -> None:
    """A text-pattern lookup registered on the generated output publishes a ``String`` operand.

    ``has`` (a ``contains``) is registered on ``Shelf.code_length``'s ``output_field``
    instance only, the registry Django's query reads it from: the leaf takes the text
    pattern it compares the column's rendering against, never a ``BigInt``.
    """
    del private_registry

    with _output_lookup_schema(("output",), _Has, "has"):
        assert _operand_types("codeLength") == {"has": "String"}


@pytest.mark.django_db
@pytest.mark.parametrize("registration", ["output-instance", "late-class"])
def test_all_lookups_on_a_generated_column_read_the_registry_its_query_resolves_over_http(
    registration: str,
    private_registry: None,
) -> None:
    """Per-field ``"__all__"`` on ``code_length`` publishes a lookup Django's query resolves.

    ``same`` (Django's ``Exact``) is registered on ``Shelf.code_length``'s ``output_field``
    instance, or on ``BigIntegerField`` after the model class was built (as an
    ``AppConfig.ready()`` would): ``Shelf.objects.filter(code_length__same=2)`` resolves it
    either way, so the expanded set carries ``same`` and it filters.
    """
    del private_registry
    _seed_shelves()

    with contextlib.ExitStack() as stack:
        if registration == "late-class":
            stack.enter_context(_class_lookup(django_models.BigIntegerField, Exact, "same"))
            owners: tuple[str, ...] = ()
        else:
            owners = ("output",)
        with _output_lookup_schema(owners, Exact, "__all__", lookup_name="same"):
            orm = models.Shelf.objects.filter(code_length__same=2)
            assert [shelf.code for shelf in orm] == ["CC"]
            assert _operand_types("codeLength")["same"] == "BigInt"
            assert _row_codes('codeLength: {same: "2"}') == ["CC"]


class _ContainsAsExact(Exact):
    """Django's ``Exact`` under its own ``lookup_name`` ``contains``, an equality."""

    lookup_name = "contains"


def _replace_contains(registration: str, lookup: type[Lookup]) -> contextlib.ExitStack:
    """Register ``lookup`` as ``contains`` on ``BigIntegerField`` for ``"late-class"``, else nothing.

    The ``"output-instance"`` registration is ``_output_lookup_schema``'s ``owners``.
    """
    stack = contextlib.ExitStack()
    if registration == "late-class":
        stack.enter_context(_class_lookup(django_models.BigIntegerField, lookup, "contains"))
    return stack


@pytest.mark.django_db
@pytest.mark.parametrize("lookup_expr", ["contains", "__all__"], ids=["declared", "all"])
@pytest.mark.parametrize("registration", ["output-instance", "late-class"])
def test_a_lookup_replaced_on_the_generated_output_is_the_one_its_query_resolves_over_http(
    registration: str,
    lookup_expr: str,
    private_registry: None,
) -> None:
    """``contains`` replaced by Django's ``Exact`` on the generated output compares the integer.

    ``Exact`` is registered as ``contains`` on ``Shelf.code_length``'s ``output_field``
    instance, or on ``BigIntegerField`` after the model class was built, where the generated
    field's own copy of its output class's lookups still holds the text pattern:
    ``Shelf.objects.filter(code_length__contains=1)`` resolves ``Exact``, so the declared and
    the ``"__all__"`` leaf both take the column's ``BigInt`` and ``1`` matches.
    """
    del private_registry
    _seed_shelves()

    owners = ("output",) if registration == "output-instance" else ()
    with (
        _replace_contains(registration, Exact),
        _output_lookup_schema(owners, Exact, lookup_expr, lookup_name="contains"),
    ):
        orm = models.Shelf.objects.filter(code_length__contains=1)
        assert [shelf.code for shelf in orm] == ["A"]
        assert _operand_types("codeLength")["contains"] == "BigInt"
        assert _row_codes("codeLength: {contains: 1}") == ["A"]


@pytest.mark.django_db
@pytest.mark.parametrize("lookup_expr", ["contains", "__all__"], ids=["declared", "all"])
@pytest.mark.parametrize("registration", ["output-instance", "late-class"])
def test_a_lookup_named_like_a_text_pattern_on_the_generated_output_takes_the_column_over_http(
    registration: str,
    lookup_expr: str,
    private_registry: None,
) -> None:
    """An equality whose own ``lookup_name`` is ``contains`` publishes the column's ``BigInt``.

    Registered as ``contains`` on ``Shelf.code_length``'s ``output_field`` instance, or on
    ``BigIntegerField`` after the model class was built, it is the lookup Django's query
    resolves for ``code_length__contains``, never the text pattern the generated field's
    own copy of its output class's lookups holds under that name.
    """
    del private_registry

    owners = ("output",) if registration == "output-instance" else ()
    with (
        _replace_contains(registration, _ContainsAsExact),
        _output_lookup_schema(owners, _ContainsAsExact, lookup_expr),
    ):
        assert _operand_types("codeLength")["contains"] == "BigInt"


@pytest.mark.django_db
@pytest.mark.parametrize("leaf", ["generated", "declared"])
def test_a_transform_replacing_a_lookup_on_the_generated_output_types_its_operand_over_http(
    leaf: str,
    private_registry: None,
) -> None:
    """Django's ``Chr`` registered as ``endswith`` on the generated output takes a ``String``.

    The generated field's own copy of its output class's lookups holds the text pattern
    ``endswith``, but Django's query resolves ``code_length__endswith`` on the
    ``output_field`` instance: ``Chr`` and an implicit ``exact``. The generated leaf and a
    declared ``CharFilter`` both take the character ``Chr`` computes, and ``"A"`` matches
    the shelf whose code is 65 characters long.
    """
    del private_registry
    _seed_shelves((("A" * 65, ""), ("B" * 66, "")))
    declared = leaf == "declared"
    filters: dict[str, Filter] = {
        "length_ends": CharFilter(field_name="code_length", lookup_expr="endswith"),
    }
    head = "lengthEnds" if declared else "codeLength"

    with _output_lookup_schema(
        ("output",),
        Chr,
        "exact" if declared else "endswith",
        lookup_name="endswith",
        declared=filters if declared else None,
    ):
        orm = models.Shelf.objects.filter(code_length__endswith="A")
        assert [shelf.code for shelf in orm] == ["A" * 65]
        assert _operand_types(head)["endsWith"] == "String"
        assert _row_codes(f'{head}: {{endsWith: "A"}}') == ["A" * 65]


@pytest.mark.django_db
def test_globalid_filter_codes_its_node_id_through_a_lookup_registered_on_the_generated_output(
    private_registry: None,
) -> None:
    """A target-less ``GlobalIDFilter`` over ``code_length`` codes its node id as the column.

    ``same`` (Django's ``Exact``) is registered on ``Shelf.code_length``'s ``output_field``
    instance only, so it is a lookup of the generated column: the node id ``65`` is the
    integer the column computes and matches the 65-character code, and a node id the
    column cannot hold answers ``GLOBALID_INVALID``, never a raw database error.
    """
    del private_registry
    _seed_shelves((("A" * 65, ""), ("B" * 66, "")))

    with _output_lookup_schema(
        ("output",),
        Exact,
        "exact",
        lookup_name="same",
        declared={"length_id": GlobalIDFilter(field_name="code_length", lookup_expr="same")},
    ):
        assert _row_codes(f'lengthId: {{same: "{relay.to_base64("Anything", "65")}"}}') == [
            "A" * 65,
        ]
        payload = response_json(
            _post_graphql(
                f'{{ rows(filter: {{lengthId: {{same: "{relay.to_base64("Anything", "abc")}"}}}}) '
                "{ edges { node { code } } } }",
                url="/graphql-test/",
            ),
        )
        (error,) = json_list(payload, "errors")
        assert json_at(error, "extensions", "code") == "GLOBALID_INVALID", payload


@pytest.mark.django_db
def test_globalid_filter_passes_its_node_id_to_a_transform_replacing_a_lookup_on_the_generated_output(
    private_registry: None,
) -> None:
    """A target-less ``GlobalIDFilter`` hands a transform's operand its node id uncoded.

    Django's ``Chr`` is registered as ``endswith`` on ``Shelf.code_length``'s ``output_field``
    instance, replacing the text pattern the generated field's own copy holds: the filter's
    lookup is no lookup of the column but a transform, so the node id ``"A"`` reaches
    ``Chr``'s implicit ``exact`` as given and matches the 65-character code, never refused
    as an integer the column cannot hold.
    """
    del private_registry
    _seed_shelves((("A" * 65, ""), ("B" * 66, "")))

    with _output_lookup_schema(
        ("output",),
        Chr,
        "exact",
        lookup_name="endswith",
        declared={"length_id": GlobalIDFilter(field_name="code_length", lookup_expr="endswith")},
    ):
        gid = relay.to_base64("Anything", "A")
        assert _row_codes(f'lengthId: {{endsWith: "{gid}"}}') == ["A" * 65]


def _gte_extra(field: object) -> dict[str, object]:
    """A ``filter_overrides`` ``extra`` making every leaf it selects a ``gte`` filter."""
    del field
    return {"lookup_expr": "gte"}


def _non_distinct_extra(field: object) -> dict[str, object]:
    """A ``filter_overrides`` ``extra`` building every filter it selects with ``distinct=False``."""
    del field
    return {"distinct": False}


@pytest.mark.django_db
def test_override_extra_lookup_expr_replaces_the_generated_leaf_lookup_over_http(
    private_registry: None,
) -> None:
    """A ``filter_overrides`` ``extra`` naming ``lookup_expr`` applies it to a generated leaf.

    ``topic_length`` computes an ``IntegerField``; the override's ``extra`` hands its
    ``NumberFilter`` ``lookup_expr="gte"``, which replaces the leaf's own ``exact`` as
    django-filter's ``filter_for_field`` lets a params entry replace a default, so the
    leaf publishes ``gte`` and answers every shelf whose topic is at least that long.
    """
    del private_registry
    _seed_shelves()

    class GteTopicFilter(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"topic_length": ["exact"]}
            filter_overrides: ClassVar[dict[type[django_models.Field[object, object]], object]] = {
                django_models.IntegerField: {"filter_class": NumberFilter, "extra": _gte_extra},
            }

    with _rows_schema(models.Shelf, GteTopicFilter, ("id", "code")):
        assert _row_codes("topicLength: {gte: 2}") == ["CC", "BBB"]


@pytest.mark.django_db
def test_consumer_override_on_a_generated_leaf_across_a_to_many_keeps_its_distinct_over_http(
    private_registry: None,
) -> None:
    """A consumer-selected filter on a generated leaf past a to-many keeps ``distinct=False``.

    Django's ``Chr`` is registered as ``endswith`` on ``BigIntegerField`` after the model was
    built, so ``shelves__code_length__endswith`` resolves to ``Chr``'s ``CharField`` output,
    which the consumer's ``CharField`` override selects with ``distinct=False``. That
    filter is the consumer's, never the framework's to-many policy, so a branch with two
    matching shelves answers once per shelf.
    """
    del private_registry
    branch = models.Branch.objects.create(name="Twice", city="open")
    for code in ("A" * 65, "C" * 65):
        _ = models.Shelf.objects.create(code=code, branch=branch)

    class NonDistinctBranchFilter(FilterSet):
        class Meta:
            model = models.Branch
            fields = {"shelves__code_length": ["endswith"]}
            filter_overrides: ClassVar[dict[type[django_models.Field[object, object]], object]] = {
                django_models.CharField: {
                    "filter_class": CharFilter,
                    "extra": _non_distinct_extra,
                },
            }

    with (
        _class_lookup(django_models.BigIntegerField, Chr, "endswith"),
        _rows_schema(models.Branch, NonDistinctBranchFilter, ("id", "name")),
    ):
        payload = _holder_payload(
            '{ rows(filter: {shelvesCodeLength: {endsWith: "A"}}) { edges { node { name } } } }',
        )
        names = [
            str(json_at(edge, "node", "name"))
            for edge in json_list(payload, "data", "rows", "edges")
        ]
        assert names == ["Twice", "Twice"]
