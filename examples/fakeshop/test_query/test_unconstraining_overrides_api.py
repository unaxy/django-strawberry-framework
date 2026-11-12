"""A walked filter override answering a value with every row it was given keeps every parent.

A consumer ``filter`` override that answers an empty or left-out value with a new queryset
keeping every row it was given (``qs.distinct()``, ``qs.all()``, ``qs.order_by()``,
``qs.filter(Q())``, ``qs.exclude(Q())``, ``qs.select_related(None)``) constrains nothing, as
django-filter reads it and as the identity ``qs`` does: on a forward relation key (a nullable
one, and one two hops long, too), on a path into a target column through a forward key and
through a to-many hop, walked through a declared ``RelatedFilter`` or through a relation whose
target type's ``get_queryset`` hides rows, every parent is kept, a ``NULL`` key, a hidden
related row and no related row at all included, as unwalked; with ``exclude=True`` too. A
logical arm holding only such a leaf is Django's ``Q()`` identity: ``or: [{leaf}, real]`` is
the real arm and ``not: {leaf}`` keeps every row, walked and unwalked. Each request reaches the
leaf over HTTP through ``FilterSet.apply_sync`` / ``apply_async`` or the set's own form, and
runs one statement.
"""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from functools import wraps
from typing import ClassVar, TypeVar

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import Model, Q, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import CharFilter, Filter, ModelChoiceFilter
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    response_json,
)
from strawberry import relay
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import read_attr, require_instance
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

_M = TypeVar("_M", bound=Model)
pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_CALLS: list[tuple[str, str]] = []


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-unconstraining/", _graphql_view),
    path("graphql-unconstraining-async/", _async_view),
]

#: Each way an override hands back every row it was given, as a new queryset.
_BODIES = (
    "distinct",
    "all",
    "order-by",
    "empty-q",
    "exclude-empty-q",
    "select-related-none",
)


def _every_row(body: str, rows: QuerySet[_M]) -> QuerySet[_M]:
    """``rows`` again, as a new queryset built the way ``body`` names."""
    if body == "distinct":
        return rows.distinct()
    if body == "all":
        return rows.all()
    if body == "order-by":
        return rows.order_by()
    if body == "empty-q":
        return rows.filter(Q())
    if body == "exclude-empty-q":
        return rows.exclude(Q())
    assert body == "select-related-none", body
    return rows.select_related(None)


class _EveryRowWhenEmptyChoice(ModelChoiceFilter):
    """Answers an empty choice with every row it was given; a choice as django-filter does."""

    body: str = "distinct"

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _CALLS.append((str(self.field_name), qs.model.__name__))
        if not value:
            return _every_row(self.body, qs)
        return super().filter(qs, value)


class _EveryRowWhenEmptyText(CharFilter):
    """Answers empty text with every row it was given; text as django-filter does."""

    body: str = "distinct"

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _CALLS.append((str(self.field_name), qs.model.__name__))
        if not value:
            return _every_row(self.body, qs)
        return super().filter(qs, value)


@dataclass(frozen=True)
class _Shape:
    """A leaf walking a relation: the set's model, its labelling column, the leaf and its hop.

    ``rows`` is every row of ``model`` by ``label``; ``named`` is the row a sibling arm names.
    """

    model: type[Model]
    label: str
    field_name: str
    choice_of: type[Model] | None
    first: str
    first_target: type[Model]
    hidden: Callable[[QuerySet[Model]], QuerySet[Model]]
    rows: Sequence[str]
    named: str


_SHAPES: dict[str, _Shape] = {
    "forward-key": _Shape(
        models.Book,
        "title",
        "shelf",
        models.Shelf,
        "shelf",
        models.Shelf,
        lambda rows: rows.exclude(topic="secret"),
        ["open-book", "secret-book"],
        "open-book",
    ),
    "nullable-forward-key": _Shape(
        models.PatronProfile,
        "postal_code",
        "favorite_genre",
        models.Genre,
        "favorite_genre",
        models.Genre,
        lambda rows: rows.exclude(name="secret"),
        ["ann", "bob", "cy"],
        "ann",
    ),
    "two-hop-forward-key": _Shape(
        models.Book,
        "title",
        "shelf__branch",
        models.Branch,
        "shelf",
        models.Shelf,
        lambda rows: rows.exclude(topic="secret"),
        ["open-book", "secret-book"],
        "open-book",
    ),
    "column-through-forward-key": _Shape(
        models.Book,
        "title",
        "shelf__code",
        None,
        "shelf",
        models.Shelf,
        lambda rows: rows.exclude(topic="secret"),
        ["open-book", "secret-book"],
        "open-book",
    ),
    "column-through-to-many": _Shape(
        models.Branch,
        "name",
        "shelves__code",
        None,
        "shelves",
        models.Shelf,
        lambda rows: rows.exclude(topic="secret"),
        ["alpha", "beta", "gamma"],
        "alpha",
    ),
}
_WALKS = ("unwalked", "related-filter", "hiding")


def _world() -> None:
    """Rows a walk can drop: a hidden related row, a ``NULL`` key and no related row at all."""
    alpha = models.Branch.objects.create(name="alpha")
    beta = models.Branch.objects.create(name="beta")
    models.Branch.objects.create(name="gamma")
    open_shelf = models.Shelf.objects.create(branch=alpha, code="open", topic="open")
    secret_shelf = models.Shelf.objects.create(branch=beta, code="secret", topic="secret")
    drama = models.Genre.objects.create(name="drama")
    secret = models.Genre.objects.create(name="secret")
    models.Book.objects.create(title="open-book", shelf=open_shelf).genres.add(drama, secret)
    models.Book.objects.create(title="secret-book", shelf=secret_shelf)
    for name, genre in (("ann", drama), ("bob", secret), ("cy", None)):
        patron = models.Patron.objects.create(name=name)
        profile = models.PatronProfile.objects.create(
            patron=patron,
            postal_code=name,
            favorite_genre=genre,
        )
        if name == "ann":
            models.Annotation.objects.create(profile=profile, body="first")
            models.Annotation.objects.create(profile=profile, body="second")


def _repeating(model: type[Model]) -> QuerySet[Model]:
    """Every row of ``model``, one repeated per row its to-many join meets.

    ``open-book`` comes back once per genre and ann's profile once per annotation, as a
    resolver joining a to-many relation without ``distinct()`` hands them over.
    """
    if model is models.Book:
        return model._default_manager.filter(
            Q(genres__isnull=True) | Q(genres__name__gte=""),
        )
    assert model is models.PatronProfile, model
    return model._default_manager.filter(
        Q(annotations__isnull=True) | Q(annotations__body__gte=""),
    )


def _node(
    model: type[Model],
    scope: Callable[[QuerySet[Model]], QuerySet[Model]] | None = None,
) -> None:
    attrs: dict[str, object] = {
        "Meta": type(
            "Meta",
            (),
            {"model": model, "fields": (model._meta.pk.name,), "interfaces": (relay.Node,)},
        ),
    }
    if scope is not None:

        def get_queryset(
            _cls: type[DjangoType],
            queryset: QuerySet[Model],
            _info: object,
        ) -> QuerySet[Model]:
            return scope(queryset)

        attrs["get_queryset"] = classmethod(get_queryset)
    type(f"{model.__name__}Rows", (DjangoType,), attrs)


def _declare(shape: _Shape, body: str, *, exclude: bool) -> Filter:
    if shape.choice_of is None:
        text = _EveryRowWhenEmptyText(field_name=shape.field_name, exclude=exclude)
        text.body = body
        return text
    choice = _EveryRowWhenEmptyChoice(
        field_name=shape.field_name,
        queryset=shape.choice_of._default_manager.all(),
        exclude=exclude,
    )
    choice.body = body
    return choice


def _filterset(
    shape: _Shape,
    body: str,
    walk: str,
    *,
    exclude: bool = False,
) -> type[FilterSet]:
    attrs: dict[str, object] = {
        "probe": _declare(shape, body, exclude=exclude),
        "named": CharFilter(field_name=shape.label),
        "Meta": type("Meta", (), {"model": shape.model, "fields": []}),
    }
    if walk == "related-filter":
        child = type(
            "HopChild",
            (FilterSet,),
            {"Meta": type("Meta", (), {"model": shape.first_target, "fields": []})},
        )
        attrs["hop"] = RelatedFilter(child, field_name=shape.first)
    filterset = type("EveryRowOverrides", (FilterSet,), attrs)
    if walk == "hiding":
        _node(shape.first_target, shape.hidden)
    elif walk == "related-filter":
        _node(shape.first_target)
    return filterset


def _schema(
    filterset: type[FilterSet],
    shape: _Shape,
    *,
    transport: str = "sync",
    direct: bool = False,
    repeating: bool = False,
    across: str | None = None,
) -> DjangoSchema:
    filterset.get_filters()
    model, label = shape.model, shape.label
    output = type(
        "EveryRowRoot",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": (label,)})},
    )

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[Model]:
        del root
        rows = _repeating(model) if repeating else model._default_manager.all()
        queryset = rows.order_by(label) if across is None else rows.order_by(across, label)
        if direct:
            request = require_instance(read_attr(info.context, "request"), HttpRequest)
            return filterset(data=json_object(where), queryset=queryset, request=request).qs
        return filterset.apply_sync(where, queryset, info)

    async def resolve_async_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> list[Model]:
        del root
        queryset = await filterset.apply_async(where, model._default_manager.order_by(label), info)
        return await sync_to_async(list)(queryset)

    @strawberry.type
    class Query:
        rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_rows if transport == "async" else resolve_rows,
            graphql_type=list[output],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
        error_policy={"enabled": False},
    )


async def _async_post(document: str, variables: JSONObject) -> JSONObject:
    response = await AsyncTestClient().query(
        document,
        variables,
        url="/graphql-unconstraining-async/",
        assert_no_errors=False,
    )
    assert response.response.status_code == 200
    return response_json(response.response)


def _names(
    schema: DjangoSchema,
    shape: _Shape,
    where: JSONObject,
    *,
    transport: str = "sync",
) -> list[str]:
    selected = "".join(
        part.capitalize() if index else part for index, part in enumerate(shape.label.split("_"))
    )
    document = f"query($where: JSON!) {{ rows(where: $where) {{ name: {selected} }} }}"
    variables: JSONObject = {"where": where}
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                payload = asyncio.run(_async_post(document, variables))
            else:
                payload = graphql_payload(
                    document,
                    variables=variables,
                    url="/graphql-unconstraining/",
                )
    finally:
        _CURRENT["schema"] = None
    assert "errors" not in payload, payload
    return [str(json_at(row, "name")) for row in json_list(payload, "data", "rows")]


def _where(value: str) -> JSONObject:
    """The request's input: the leaf supplied empty, or left out."""
    return {"probe": ""} if value == "empty" else {}


def _calls(shape: _Shape, walk: str, value: str) -> list[tuple[str, str]]:
    """The override's calls: once over the set's rows unwalked, or as a walk runs it.

    A walked leaf the request leaves out is first asked whether it constrains
    (``FilterSet._absent_leaf_applies``), then applied, each over the rows its chain reads:
    a forward key's leaf compares the key its own rows hold, a path into a column runs over
    the target's rows.
    """
    if walk == "unwalked":
        return [(shape.field_name, shape.model.__name__)]
    if shape.choice_of is not None:
        call = (shape.field_name, shape.model.__name__)
    else:
        call = (shape.field_name.partition("__")[2], shape.first_target.__name__)
    return [call] * (2 if value == "absent" else 1)


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _WALKS)
@pytest.mark.parametrize("value", ["empty", "absent"])
@pytest.mark.parametrize("direct", [False, True], ids=["apply-sync", "form"])
@pytest.mark.parametrize("body", _BODIES)
@pytest.mark.parametrize("name", list(_SHAPES))
def test_an_override_keeping_every_row_it_was_given_keeps_every_parent(
    name: str,
    body: str,
    value: str,
    walk: str,
    *,
    direct: bool,
) -> None:
    """Every parent stays, walked as unwalked: a ``NULL`` key, a hidden row and none at all."""
    _world()
    shape = _SHAPES[name]
    schema = _schema(_filterset(shape, body, walk), shape, direct=direct)
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        names = _names(schema, shape, _where(value))
    assert names == list(shape.rows)
    assert _calls(shape, walk, value) == _CALLS
    assert len(queries.captured_queries) == 1, queries.captured_queries


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _WALKS)
@pytest.mark.parametrize("value", ["empty", "absent"])
@pytest.mark.parametrize("direct", [False, True], ids=["apply-sync", "form"])
@pytest.mark.parametrize("body", ["distinct", "all"])
@pytest.mark.parametrize("name", list(_SHAPES))
def test_an_excluding_override_keeping_every_row_it_was_given_keeps_every_parent(
    name: str,
    body: str,
    value: str,
    walk: str,
    *,
    direct: bool,
) -> None:
    """``exclude=True`` negates no constraint: every parent stays, as django-filter keeps it."""
    _world()
    shape = _SHAPES[name]
    schema = _schema(_filterset(shape, body, walk, exclude=True), shape, direct=direct)
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        names = _names(schema, shape, _where(value))
    assert names == list(shape.rows)
    assert _calls(shape, walk, value) == _CALLS
    assert len(queries.captured_queries) == 1, queries.captured_queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
@pytest.mark.parametrize("value", ["empty", "absent"])
@pytest.mark.parametrize("exclude", [False, True], ids=["positive", "exclude"])
@pytest.mark.parametrize("name", list(_SHAPES))
def test_an_async_override_keeping_every_row_it_was_given_keeps_every_parent(
    name: str,
    value: str,
    walk: str,
    record_compiled_sql: RecordCompiledSql,
    *,
    exclude: bool,
) -> None:
    """``apply_async`` keeps every parent as ``apply_sync`` does, in one statement."""
    _world()
    shape = _SHAPES[name]
    schema = _schema(
        _filterset(shape, "distinct", walk, exclude=exclude),
        shape,
        transport="async",
    )
    _CALLS.clear()
    statements = record_compiled_sql()
    assert _names(schema, shape, _where(value), transport="async") == list(shape.rows)
    assert _calls(shape, walk, value) == _CALLS
    assert len(statements) == 1, statements


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _WALKS)
@pytest.mark.parametrize("arm", ["or", "not"])
@pytest.mark.parametrize("body", ["distinct", "all"])
@pytest.mark.parametrize("name", list(_SHAPES))
def test_a_logical_arm_holding_only_an_override_keeping_every_row_is_the_identity(
    name: str,
    body: str,
    arm: str,
    walk: str,
) -> None:
    """The arm composes as ``Q()``: ``or`` is its real sibling arm, ``not`` keeps every row."""
    _world()
    shape = _SHAPES[name]
    schema = _schema(_filterset(shape, body, walk), shape)
    where: JSONObject = (
        {"or_": [{"probe": ""}, {"named": shape.named}]}
        if arm == "or"
        else {"not_": {"probe": ""}}
    )
    with CaptureQueriesContext(connection) as queries:
        names = _names(schema, shape, where)
    assert names == ([shape.named] if arm == "or" else list(shape.rows))
    assert len(queries.captured_queries) == 1, queries.captured_queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
@pytest.mark.parametrize("arm", ["or", "not"])
@pytest.mark.parametrize("name", list(_SHAPES))
def test_an_async_logical_arm_holding_only_an_override_keeping_every_row_is_the_identity(
    name: str,
    arm: str,
    walk: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """``apply_async`` composes the arm as ``apply_sync`` does, in one statement."""
    _world()
    shape = _SHAPES[name]
    schema = _schema(_filterset(shape, "distinct", walk), shape, transport="async")
    where: JSONObject = (
        {"or_": [{"probe": ""}, {"named": shape.named}]}
        if arm == "or"
        else {"not_": {"probe": ""}}
    )
    statements = record_compiled_sql()
    names = _names(schema, shape, where, transport="async")
    assert names == ([shape.named] if arm == "or" else list(shape.rows))
    assert len(statements) == 1, statements


@pytest.mark.django_db
@pytest.mark.parametrize("walk", _WALKS)
@pytest.mark.parametrize("value", ["empty", "absent"])
@pytest.mark.parametrize("direct", [False, True], ids=["apply-sync", "form"])
@pytest.mark.parametrize("name", ["forward-key", "nullable-forward-key", "two-hop-forward-key"])
def test_a_key_override_answering_with_distinct_rows_collapses_a_repeated_parent(
    name: str,
    value: str,
    walk: str,
    *,
    direct: bool,
) -> None:
    """The override's own rows are the answer: its ``distinct()`` collapses a repeated parent.

    A resolver handing over rows a to-many join repeats gets each parent once, as
    django-filter's ``qs.distinct()`` gives it unwalked, never the repeated rows it was given.
    """
    _world()
    shape = _SHAPES[name]
    schema = _schema(_filterset(shape, "distinct", walk), shape, direct=direct, repeating=True)
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        names = _names(schema, shape, _where(value))
    assert names == list(shape.rows)
    assert _calls(shape, walk, value) == _CALLS
    assert len(queries.captured_queries) == 1, queries.captured_queries


#: The ``method=`` calls of ``_AnyByMethod``, one value each.
_METHOD_CALLS: list[object] = []


class _AnyByMethod(FilterSet):
    """A ``method=`` answering ``"any"`` with every row it was given, as a new queryset."""

    probe = CharFilter(field_name="shelves__code", method="any_or_code")
    named = CharFilter(field_name="name")

    class Meta:
        model = models.Branch
        fields: ClassVar[list[str]] = []

    def any_or_code(
        self,
        queryset: QuerySet[_M],
        name: str,
        value: object,
    ) -> QuerySet[_M]:
        _METHOD_CALLS.append(value)
        if value == "any":
            return queryset.distinct()
        return queryset.filter(**{name: value})


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
@pytest.mark.parametrize("arm", ["or", "not", "flat"])
def test_a_method_answering_with_every_row_it_was_given_constrains_nothing(
    arm: str,
    walk: str,
) -> None:
    """The ``method=`` runs once and keeps every row: a logical arm holding it is ``Q()``.

    ``or: [{probe}, real]`` is the real arm, ``not: {probe}`` keeps every row, and the flat
    leaf keeps every row, unwalked and with the shelves' type hiding a shelf.
    """
    _world()
    shape = _SHAPES["column-through-to-many"]
    if walk == "hiding":
        _node(shape.first_target, shape.hidden)
    schema = _schema(_AnyByMethod, shape)
    where: JSONObject = (
        {"or_": [{"probe": "any"}, {"named": shape.named}]}
        if arm == "or"
        else {"not_": {"probe": "any"}}
        if arm == "not"
        else {"probe": "any"}
    )
    _METHOD_CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        names = _names(schema, shape, where)
    assert _METHOD_CALLS == ["any"]
    assert names == ([shape.named] if arm == "or" else list(shape.rows))
    assert len(queries.captured_queries) == 1, queries.captured_queries


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["related-filter", "hiding"])
@pytest.mark.parametrize("where", ["empty", "absent", "not"])
@pytest.mark.parametrize("name", ["forward-key", "two-hop-forward-key"])
def test_an_override_dropping_the_resolvers_own_join_keeps_every_parent(
    name: str,
    where: str,
    walk: str,
) -> None:
    """``qs.order_by()`` over rows a resolver ordered across ``shelf`` keeps every row.

    The resolver's ordering joins each book's shelf (an inner join); the override's
    ``order_by()`` drops that join and every predicate stays the input's, so it constrains
    nothing: the flat leaf, supplied empty or left out, keeps every book, a hidden shelf's
    included, and ``not: {leaf}`` composes as ``Q()``.
    """
    _world()
    shape = _SHAPES[name]
    schema = _schema(_filterset(shape, "order-by", walk), shape, across="shelf__code")
    request: JSONObject = {"not_": {"probe": ""}} if where == "not" else _where(where)
    with CaptureQueriesContext(connection) as queries:
        names = _names(schema, shape, request)
    assert sorted(names) == sorted(shape.rows)
    assert len(queries.captured_queries) == 1, queries.captured_queries
