"""A class-level ``filter`` override on a walked relation key runs as declared, over visible rows.

A consumer ``Filter`` subclass overriding ``filter`` on a relation key (a to-many key at
any hop count, a to-one key two or more hops away) receives the ``field_name`` it was
declared with, the value its form cleaned and the rows of the set declaring it, exactly
as when no hop is walked; a supplied value runs it once per request (a leaf the request
leaves out is first asked whether it constrains, then applied). The parents it keeps must
also reach, through each hop's visible rows, a visible last-hop row its value names, so a
row a target type's ``get_queryset`` hides matches nothing. A value naming no row of the
relation's target (an empty or absent choice, instances of another model, a value the key's
own comparison skips or refuses) runs as the related rows' own filter, over the rows the
walk keeps visible. Each request reaches the
leaf over HTTP through ``FilterSet.apply_sync`` / ``apply_async`` or the set's own form.
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import wraps
from typing import TypeVar

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy
from django_filters import CharFilter, Filter, ModelChoiceFilter, ModelMultipleChoiceFilter
from graphql import GraphQLError
from graphql_client import (
    JSONObject,
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
from django_strawberry_framework.filters import FilterSet, GlobalIDFilter, RelatedFilter
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import list_of, read_attr, require_instance
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

_M = TypeVar("_M", bound=Model)
pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_CALLS: list[tuple[str, str, str]] = []


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
    path("graphql-key-overrides/", _graphql_view),
    path("graphql-key-overrides-async/", _async_view),
]


def _record(field_name: object, value: object, qs: QuerySet[_M]) -> None:
    _CALLS.append((str(field_name), type(value).__name__, qs.model.__name__))


class _PkReader(ModelMultipleChoiceFilter):
    """Reads each chosen row's ``pk``, as a model-choice override may."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if not value:
            return qs
        pks = [read_attr(row, "pk") for row in list_of(value)]
        return qs.filter(**{f"{self.field_name}__pk__in": pks}).distinct()


class _Recorded(ModelMultipleChoiceFilter):
    """Records its call, then answers as django-filter does."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return super().filter(qs, value)


class _RecordedChoice(ModelChoiceFilter):
    """Records its call, then answers as django-filter's single-choice filter does."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return super().filter(qs, value)


class _RecordedGlobalID(GlobalIDFilter):
    """Records its call, then answers as the package's GlobalID filter does."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return super().filter(qs, value)


class _RecordedText(CharFilter):
    """Records its call, then compares the raw text as django-filter does."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return super().filter(qs, value)


@dataclass(frozen=True)
class _Key:
    """One relation key, the source model holding it and the walks that cross its hops."""

    model: type[Model]
    label: str
    first: str
    first_target: type[Model]
    hidden: Callable[[QuerySet[Model]], QuerySet[Model]]
    hidden_model: type[Model]


_SHELVES = _Key(
    models.Branch,
    "name",
    "shelves",
    models.Shelf,
    lambda rows: rows.exclude(topic="secret"),
    models.Shelf,
)
_GENRES = _Key(
    models.Book,
    "title",
    "genres",
    models.Genre,
    lambda rows: rows.exclude(name="secret"),
    models.Genre,
)
_SHELF_BRANCH = _Key(
    models.Book,
    "title",
    "shelf",
    models.Shelf,
    lambda rows: rows.exclude(topic="secret"),
    models.Shelf,
)
_FAVORITE_GENRE = _Key(
    models.Patron,
    "name",
    "profile",
    models.PatronProfile,
    lambda rows: rows.exclude(name="secret"),
    models.Genre,
)


@dataclass(frozen=True)
class _Case:
    """A declared override, its form value, the rows each walk answers and the statements run."""

    key: _Key
    declare: Callable[[], Filter]
    value: Callable[[], object]
    visible: Sequence[str]
    hiding: Sequence[str]
    received: tuple[str, str, str] | None
    queries: int


def _pks(model: type[Model], field: str, *names: str) -> list[str]:
    return [str(read_attr(model._default_manager.get(**{field: name}), "pk")) for name in names]


def _respelled(filter_instance: Filter, **values: object) -> Filter:
    """``filter_instance`` with each of ``values`` set on it as a consumer may set a lazy value.

    The stubs type ``field_name`` and ``lookup_expr`` as ``str``; a project hands Django's lazy
    text (``gettext_lazy``, ``SimpleLazyObject``) where a ``str`` is read.
    """
    for name, value in values.items():
        setattr(filter_instance, name, value)
    return filter_instance


def _shelf_gid(code: str) -> str:
    return str(relay.GlobalID("library.shelf", _pks(models.Shelf, "code", code)[0]))


def _genres() -> QuerySet[models.Genre]:
    return models.Genre.objects.all()


_CASES: dict[str, _Case] = {
    "reverse-fk-pk-reader": _Case(
        _SHELVES,
        lambda: _PkReader(field_name="shelves", queryset=models.Shelf.objects.all()),
        lambda: _pks(models.Shelf, "code", "open", "secret"),
        ["alpha", "beta"],
        ["alpha"],
        ("shelves", "list", "Branch"),
        2,
    ),
    "reverse-fk-super": _Case(
        _SHELVES,
        lambda: _Recorded(field_name="shelves", queryset=models.Shelf.objects.all()),
        lambda: _pks(models.Shelf, "code", "open", "secret"),
        ["alpha", "beta"],
        ["alpha"],
        ("shelves", "list", "Branch"),
        2,
    ),
    "reverse-fk-exclude": _Case(
        _SHELVES,
        lambda: _Recorded(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            exclude=True,
        ),
        lambda: _pks(models.Shelf, "code", "open", "secret"),
        ["delta", "gamma"],
        ["beta", "delta", "gamma"],
        ("shelves", "list", "Branch"),
        2,
    ),
    "reverse-fk-conjoined": _Case(
        _SHELVES,
        lambda: _Recorded(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            conjoined=True,
        ),
        lambda: _pks(models.Shelf, "code", "delta-open", "delta-secret"),
        ["delta"],
        [],
        ("shelves", "list", "Branch"),
        2,
    ),
    "reverse-fk-lazy-field-name": _Case(
        _SHELVES,
        lambda: _respelled(
            _PkReader(queryset=models.Shelf.objects.all()),
            field_name=SimpleLazyObject(lambda: "shelves"),
        ),
        lambda: _pks(models.Shelf, "code", "open", "secret"),
        ["alpha", "beta"],
        ["alpha"],
        ("shelves", "list", "Branch"),
        2,
    ),
    "reverse-fk-global-id": _Case(
        _SHELVES,
        lambda: _RecordedGlobalID(field_name="shelves"),
        lambda: _shelf_gid("secret"),
        ["beta"],
        [],
        ("shelves", "str", "Branch"),
        1,
    ),
    "m2m-super": _Case(
        _GENRES,
        lambda: _Recorded(field_name="genres", queryset=_genres()),
        lambda: _pks(models.Genre, "name", "drama", "secret"),
        ["mixed-book", "open-book", "secret-book"],
        ["mixed-book", "open-book"],
        ("genres", "list", "Book"),
        2,
    ),
    "m2m-conjoined": _Case(
        _GENRES,
        lambda: _Recorded(field_name="genres", queryset=_genres(), conjoined=True),
        lambda: _pks(models.Genre, "name", "drama", "secret"),
        ["mixed-book"],
        [],
        ("genres", "list", "Book"),
        2,
    ),
    "two-hop-to-many-pk-reader": _Case(
        _SHELVES,
        lambda: _PkReader(field_name="shelves__books", queryset=models.Book.objects.all()),
        lambda: _pks(models.Book, "title", "open-book", "secret-book"),
        ["alpha", "beta"],
        ["alpha"],
        ("shelves__books", "list", "Branch"),
        2,
    ),
    "two-hop-to-many-conjoined": _Case(
        _SHELVES,
        lambda: _Recorded(
            field_name="shelves__books",
            queryset=models.Book.objects.all(),
            conjoined=True,
        ),
        lambda: _pks(models.Book, "title", "delta-open-book", "delta-secret-book"),
        ["delta"],
        [],
        ("shelves__books", "list", "Branch"),
        2,
    ),
    "two-hop-to-one-pk-reader": _Case(
        _SHELF_BRANCH,
        lambda: _PkReader(field_name="shelf__branch", queryset=models.Branch.objects.all()),
        lambda: _pks(models.Branch, "name", "alpha", "beta"),
        ["mixed-book", "open-book", "secret-book"],
        ["mixed-book", "open-book"],
        ("shelf__branch", "list", "Book"),
        2,
    ),
    "two-hop-to-one-shipped": _Case(
        _SHELF_BRANCH,
        lambda: ModelMultipleChoiceFilter(
            field_name="shelf__branch",
            queryset=models.Branch.objects.all(),
        ),
        lambda: _pks(models.Branch, "name", "alpha", "beta"),
        ["mixed-book", "open-book", "secret-book"],
        ["mixed-book", "open-book"],
        None,
        2,
    ),
    "two-hop-to-one-single-choice": _Case(
        _SHELF_BRANCH,
        lambda: _RecordedChoice(field_name="shelf__branch", queryset=models.Branch.objects.all()),
        lambda: _pks(models.Branch, "name", "beta")[0],
        ["secret-book"],
        [],
        ("shelf__branch", "Branch", "Book"),
        2,
    ),
    "two-hop-to-field-raw-text": _Case(
        _FAVORITE_GENRE,
        lambda: _RecordedText(field_name="profile__favorite_genre"),
        lambda: "secret",
        ["bob"],
        [],
        ("profile__favorite_genre", "str", "Patron"),
        1,
    ),
    "two-hop-to-field-lazy-lookup": _Case(
        _FAVORITE_GENRE,
        lambda: _respelled(
            _RecordedText(field_name="profile__favorite_genre"),
            lookup_expr=gettext_lazy("exact"),
        ),
        lambda: "drama",
        ["ann"],
        ["ann"],
        ("profile__favorite_genre", "str", "Patron"),
        1,
    ),
}


def _world() -> None:
    alpha = models.Branch.objects.create(name="alpha")
    beta = models.Branch.objects.create(name="beta")
    delta = models.Branch.objects.create(name="delta")
    models.Branch.objects.create(name="gamma")
    open_shelf = models.Shelf.objects.create(branch=alpha, code="open", topic="open")
    secret_shelf = models.Shelf.objects.create(branch=beta, code="secret", topic="secret")
    models.Shelf.objects.create(branch=beta, code="beta-open", topic="open")
    delta_open = models.Shelf.objects.create(branch=delta, code="delta-open", topic="open")
    delta_secret = models.Shelf.objects.create(branch=delta, code="delta-secret", topic="secret")
    drama = models.Genre.objects.create(name="drama")
    secret = models.Genre.objects.create(name="secret")
    models.Book.objects.create(title="open-book", shelf=open_shelf).genres.add(drama)
    models.Book.objects.create(title="secret-book", shelf=secret_shelf).genres.add(secret)
    models.Book.objects.create(title="mixed-book", shelf=open_shelf).genres.add(drama, secret)
    models.Book.objects.create(title="delta-open-book", shelf=delta_open)
    models.Book.objects.create(title="delta-secret-book", shelf=delta_secret)
    for name, genre in (("ann", drama), ("bob", secret)):
        patron = models.Patron.objects.create(name=name)
        models.PatronProfile.objects.create(patron=patron, favorite_genre=genre)
    models.Patron.objects.create(name="cy")


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


def _filterset(case: _Case, walk: str) -> type[FilterSet]:
    key = case.key
    attrs: dict[str, object] = {
        "probe": case.declare(),
        "Meta": type("Meta", (), {"model": key.model, "fields": [key.label]}),
    }
    if walk == "related-filter":
        child = type(
            "HopChild",
            (FilterSet,),
            {"Meta": type("Meta", (), {"model": key.first_target, "fields": []})},
        )
        attrs["hop"] = RelatedFilter(child, field_name=key.first)
    filterset = type("KeyOverrides", (FilterSet,), attrs)
    if walk == "hiding":
        _node(key.hidden_model, key.hidden)
    else:
        _node(key.hidden_model)
    if walk == "related-filter" and key.first_target is not key.hidden_model:
        _node(key.first_target)
    return filterset


def _schema(
    filterset: type[FilterSet],
    model: type[Model],
    label: str,
    *,
    transport: str = "sync",
    direct: bool = False,
) -> DjangoSchema:
    filterset.get_filters()
    output = type(
        "KeyRoot",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": (label,)})},
    )

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[Model]:
        del root
        queryset = model._default_manager.order_by(label)
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
        url="/graphql-key-overrides-async/",
        assert_no_errors=False,
    )
    assert response.response.status_code == 200
    return response_json(response.response)


def _post(
    schema: DjangoSchema,
    label: str,
    variables: JSONObject,
    *,
    transport: str = "sync",
) -> JSONObject:
    document = f"query($where: JSON!) {{ rows(where: $where) {{ name: {label} }} }}"
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                return asyncio.run(_async_post(document, variables))
            return graphql_payload(document, variables=variables, url="/graphql-key-overrides/")
    finally:
        _CURRENT["schema"] = None


def _received(case: _Case) -> list[tuple[str, str, str]]:
    """The one call a consumer override records; a shipped filter records none."""
    return [] if case.received is None else [case.received]


def _rows(names: Sequence[str]) -> JSONObject:
    return {"data": {"rows": [{"name": name} for name in names]}}


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
@pytest.mark.parametrize("direct", [False, True], ids=["apply-sync", "form"])
@pytest.mark.parametrize("name", list(_CASES))
def test_a_key_override_runs_once_as_declared_and_matches_only_visible_named_rows(
    name: str,
    walk: str,
    *,
    direct: bool,
) -> None:
    """The override answers its unwalked rows, minus a parent reaching only a hidden named row.

    A shipped filter on the two-hop forward key, which keeps comparing the stored key, answers
    the same rows.
    """
    _world()
    case = _CASES[name]
    schema = _schema(_filterset(case, walk), case.key.model, case.key.label, direct=direct)
    variables: JSONObject = {"where": {"probe": case.value()}}
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, case.key.label, variables)
    expected = case.hiding if walk == "hiding" else case.visible
    assert payload == _rows(expected), payload
    assert _received(case) == _CALLS
    assert len(queries.captured_queries) == case.queries, queries.captured_queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
@pytest.mark.parametrize(
    "name",
    [
        "reverse-fk-pk-reader",
        "reverse-fk-conjoined",
        "two-hop-to-one-pk-reader",
        "two-hop-to-field-raw-text",
    ],
)
def test_an_async_key_override_runs_once_as_declared_and_matches_only_visible_named_rows(
    name: str,
    walk: str,
) -> None:
    """``apply_async`` answers as ``apply_sync`` does, the override called once."""
    _world()
    case = _CASES[name]
    schema = _schema(_filterset(case, walk), case.key.model, case.key.label, transport="async")
    variables: JSONObject = {"where": {"probe": case.value()}}
    _CALLS.clear()
    payload = _post(schema, case.key.label, variables, transport="async")
    assert payload == _rows(case.hiding if walk == "hiding" else case.visible), payload
    assert _received(case) == _CALLS


#: ``(spelling, value, walk) -> (rows, the call recorded)`` for a child set's override on
#: ``Shelf.books``: a value naming books runs as declared; an empty choice the override
#: reads as the hidden ``secret-book`` names no book and runs over the visible books. The
#: flat copy walks the declared ``shelves`` hop on every walk.
_CHILD_ANSWERS: dict[tuple[str, str, str], tuple[list[str], tuple[str, str, str]]] = {
    ("nested", "named", "unwalked"): (["alpha", "beta"], ("books", "list", "Shelf")),
    ("nested", "named", "hiding"): (["alpha"], ("books", "list", "Shelf")),
    ("flat", "named", "unwalked"): (["alpha", "beta"], ("shelves__books", "list", "Branch")),
    ("flat", "named", "hiding"): (["alpha"], ("shelves__books", "list", "Branch")),
    ("projected", "named", "unwalked"): (["alpha", "beta"], ("books", "list", "Shelf")),
    ("projected", "named", "hiding"): (["alpha"], ("books", "list", "Shelf")),
    ("nested", "hidden-default", "unwalked"): (["beta"], ("books", "QuerySet", "Shelf")),
    ("nested", "hidden-default", "hiding"): ([], ("id", "list", "Book")),
    ("flat", "hidden-default", "unwalked"): (["beta"], ("id", "list", "Book")),
    ("flat", "hidden-default", "hiding"): ([], ("id", "list", "Book")),
    ("projected", "hidden-default", "unwalked"): (["beta"], ("books", "QuerySet", "Shelf")),
    ("projected", "hidden-default", "hiding"): ([], ("id", "list", "Book")),
}


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["named", "hidden-default"])
@pytest.mark.parametrize("spelling", ["nested", "flat", "projected"])
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
def test_a_key_override_on_a_related_filter_child_runs_as_its_child_declares_it(
    walk: str,
    spelling: str,
    value: str,
) -> None:
    """The child's override runs once as its set declares it, or as its flat copy on the parent is.

    Nested, or projected (a child set with its own ``__init__``), it runs over the child
    set's rows; spelled flat, the parent's copy of it runs over the parent's rows with the
    path the copy carries there. Either way a parent reaching only a hidden named book
    matches nothing, and a value naming no book runs over the visible books.
    """
    _world()

    class ShelfChild(FilterSet):
        probe = (
            _PkReader(field_name="books", queryset=models.Book.objects.all())
            if value == "named"
            else _DefaultChoices(
                field_name="books",
                queryset=models.Book.objects.all(),
                default=(models.Book, "title", "secret-book"),
            )
        )

        class Meta:
            model = models.Shelf
            fields = ["code"]

    child: type[FilterSet] = ShelfChild
    if spelling == "projected":

        class OwnedShelf(ShelfChild):
            @override
            def __init__(
                self,
                data: Mapping[str, object] | None = None,
                queryset: QuerySet[Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        child = OwnedShelf

    class BranchParent(FilterSet):
        shelves = RelatedFilter(child, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = ["name"]

    _node(models.Shelf)
    _node(
        models.Book,
        (lambda rows: rows.exclude(title="secret-book")) if walk == "hiding" else None,
    )
    schema = _schema(BranchParent, models.Branch, "name")
    named = _pks(models.Book, "title", "open-book", "secret-book") if value == "named" else []
    where: JSONObject = (
        {"shelves": {"probe": named}} if spelling == "nested" else {"shelves__probe": named}
    )
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, "name", {"where": where})
    rows, received = _CHILD_ANSWERS[spelling, value, walk]
    assert payload == _rows(rows), payload
    assert [received] == _CALLS
    # A named value's choices are read while the form cleans; an empty one's default row is
    # read when the override runs. Then the root query.
    assert len(queries.captured_queries) == 2, queries.captured_queries


class _DefaultChoice(ModelChoiceFilter):
    """Reads an empty choice as the key of its ``default`` row, as a consumer default may."""

    def __init__(
        self,
        *,
        field_name: str,
        queryset: QuerySet[Model],
        default: tuple[type[Model], str, str],
    ) -> None:
        super().__init__(field_name=field_name, queryset=queryset)
        self.default = default

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if value is None:
            value = _default_pk(self.default)
        return super().filter(qs, value)


class _DefaultChoices(ModelMultipleChoiceFilter):
    """Reads an empty or absent selection as its ``default`` row's key, as a consumer may."""

    def __init__(
        self,
        *,
        field_name: str,
        queryset: QuerySet[Model],
        default: tuple[type[Model], str, str],
    ) -> None:
        super().__init__(field_name=field_name, queryset=queryset)
        self.default = default

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return super().filter(qs, value or [_default_pk(self.default)])


class _RawPkGlobalID(GlobalIDFilter):
    """Also reads a bare primary key, which the GlobalID comparison refuses."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if isinstance(value, str) and value.isdigit():
            return qs.filter(**{str(self.field_name): int(value)}).distinct()
        return super().filter(qs, value)


class _TolerantGlobalID(GlobalIDFilter):
    """Answers no row for an id the GlobalID comparison refuses."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        try:
            return super().filter(qs, value)
        except GraphQLError:
            return qs.none()


class _CodeText(CharFilter):
    """Reads its text as a shelf code, which the key column's comparison refuses."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if not value:
            return qs
        return qs.filter(**{f"{self.field_name}__code": value}).distinct()


class _BookPicker(ModelMultipleChoiceFilter):
    """Picks books on a shelves key: its instances are not rows of the relation's target."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if not value:
            return qs
        return qs.filter(**{f"{self.field_name}__books__in": list_of(value)}).distinct()


def _default_pk(default: tuple[type[Model], str, str]) -> object:
    model, field, name = default
    return read_attr(model._default_manager.get(**{field: name}), "pk")


#: The value a request leaves out of its input.
_ABSENT = object()


@dataclass(frozen=True)
class _Unnamed:
    """An override whose value names no row of the relation's target, and the parent's answer.

    ``walked`` is what the walked leaf answers (its rows, or the error its re-bound copy
    raises), as on the related rows' own filter; ``received`` / ``walked_received`` are the
    calls it records unwalked and walked. A request runs one statement per call when the
    override reads its default row (``reads``), ``cleans`` for its form's choices, and the
    root query unless the leaf raises; ``statements`` pins the unwalked, walked and
    hiding counts of an override answering no row by an empty queryset;
    ``related_received`` is the call of a value the walk's ``RelatedFilter`` target reads
    as naming a row, where the override runs as declared.
    """

    key: _Key
    declare: Callable[[], Filter]
    value: Callable[[], object]
    unwalked: Sequence[str]
    walked: Sequence[str] | str
    hiding: Sequence[str] | str
    received: tuple[str, str, str]
    walked_received: tuple[str, str, str]
    reads: int = 1
    cleans: int = 0
    statements: tuple[int, int, int] | None = None
    related_received: tuple[str, str, str] | None = None


_SHELF = (models.Shelf, "code", "open")
_HIDDEN_SHELF = (models.Shelf, "code", "secret")
_DRAMA = (models.Genre, "name", "drama")
_HIDDEN_GENRE = (models.Genre, "name", "secret")
_UNNAMED: dict[str, _Unnamed] = {
    "single-null-visible": _Unnamed(
        _SHELVES,
        lambda: _DefaultChoice(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_SHELF,
        ),
        lambda: None,
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "NoneType", "Branch"),
        ("id", "NoneType", "Shelf"),
    ),
    "single-null-hidden": _Unnamed(
        _SHELVES,
        lambda: _DefaultChoice(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        lambda: None,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "NoneType", "Branch"),
        ("id", "NoneType", "Shelf"),
    ),
    "multi-empty-visible": _Unnamed(
        _SHELVES,
        lambda: _DefaultChoices(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_SHELF,
        ),
        list,
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "QuerySet", "Branch"),
        ("id", "list", "Shelf"),
    ),
    "multi-empty-hidden": _Unnamed(
        _SHELVES,
        lambda: _DefaultChoices(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("id", "list", "Shelf"),
    ),
    "multi-absent-visible": _Unnamed(
        _SHELVES,
        lambda: _DefaultChoices(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_SHELF,
        ),
        lambda: _ABSENT,
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "QuerySet", "Branch"),
        ("id", "list", "Shelf"),
    ),
    "multi-absent-hidden": _Unnamed(
        _SHELVES,
        lambda: _DefaultChoices(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        lambda: _ABSENT,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("id", "list", "Shelf"),
    ),
    "m2m-empty-visible": _Unnamed(
        _GENRES,
        lambda: _DefaultChoices(field_name="genres", queryset=_genres(), default=_DRAMA),
        list,
        ["mixed-book", "open-book"],
        ["mixed-book", "open-book"],
        ["mixed-book", "open-book"],
        ("genres", "QuerySet", "Book"),
        ("id", "list", "Genre"),
    ),
    "m2m-empty-hidden": _Unnamed(
        _GENRES,
        lambda: _DefaultChoices(field_name="genres", queryset=_genres(), default=_HIDDEN_GENRE),
        list,
        ["mixed-book", "secret-book"],
        ["mixed-book", "secret-book"],
        [],
        ("genres", "QuerySet", "Book"),
        ("id", "list", "Genre"),
    ),
    "instances-of-another-model": _Unnamed(
        _SHELVES,
        lambda: _BookPicker(field_name="shelves", queryset=models.Book.objects.all()),
        lambda: _pks(models.Book, "title", "open-book"),
        ["alpha"],
        "Unsupported lookup 'books__in' for BigAutoField or join on the field not permitted.",
        "Unsupported lookup 'books__in' for BigAutoField or join on the field not permitted.",
        ("shelves", "list", "Branch"),
        ("id", "list", "Shelf"),
        reads=0,
        cleans=1,
    ),
    "raw-pk-the-global-id-refuses": _Unnamed(
        _SHELVES,
        lambda: _RawPkGlobalID(field_name="shelves"),
        lambda: _pks(models.Shelf, "code", "open")[0],
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "str", "Branch"),
        ("id", "str", "Shelf"),
        reads=0,
    ),
    "hidden-raw-pk-the-global-id-refuses": _Unnamed(
        _SHELVES,
        lambda: _RawPkGlobalID(field_name="shelves"),
        lambda: _pks(models.Shelf, "code", "secret")[0],
        ["beta"],
        ["beta"],
        [],
        ("shelves", "str", "Branch"),
        ("id", "str", "Shelf"),
        reads=0,
    ),
    "malformed-id-a-tolerant-override-reads": _Unnamed(
        _SHELVES,
        lambda: _TolerantGlobalID(field_name="shelves"),
        lambda: "garbage",
        [],
        [],
        [],
        ("shelves", "str", "Branch"),
        ("id", "str", "Shelf"),
        reads=0,
        statements=(0, 1, 1),
    ),
    "mistyped-id-a-tolerant-override-reads": _Unnamed(
        _SHELVES,
        lambda: _TolerantGlobalID(field_name="shelves"),
        lambda: str(relay.GlobalID("library.book", _pks(models.Shelf, "code", "open")[0])),
        [],
        [],
        [],
        ("shelves", "str", "Branch"),
        ("id", "str", "Shelf"),
        reads=0,
        statements=(0, 0, 1),
        related_received=("shelves", "str", "Branch"),
    ),
    "text-the-key-column-refuses": _Unnamed(
        _SHELVES,
        lambda: _CodeText(field_name="shelves"),
        lambda: "open",
        ["alpha"],
        "Unsupported lookup 'code' for BigAutoField or join on the field not permitted.",
        "Unsupported lookup 'code' for BigAutoField or join on the field not permitted.",
        ("shelves", "str", "Branch"),
        ("id", "str", "Shelf"),
        reads=0,
    ),
}


def _unnamed_case(shape: _Unnamed) -> _Case:
    return _Case(shape.key, shape.declare, shape.value, [], [], None, 0)


def _answer(payload: JSONObject) -> Sequence[str] | str:
    errors = payload.get("errors")
    if errors:
        return str(json_at(payload, "errors", 0, "message"))
    return [str(json_at(row, "name")) for row in json_list(payload, "data", "rows")]


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
@pytest.mark.parametrize("direct", [False, True], ids=["apply-sync", "form"])
@pytest.mark.parametrize("name", list(_UNNAMED))
def test_a_key_override_whose_value_names_no_row_runs_over_the_visible_related_rows(
    name: str,
    walk: str,
    *,
    direct: bool,
) -> None:
    """A value naming no row of the target runs as the related rows' own filter.

    An empty or absent choice the override reads as a default row, or instances of
    another model, name no row of the relation's target: walked, the leaf runs re-bound
    over the visible related rows, so a visible default answers its parents and a hidden
    one matches nothing.
    """
    _world()
    shape = _UNNAMED[name]
    schema = _schema(
        _filterset(_unnamed_case(shape), walk),
        shape.key.model,
        shape.key.label,
        direct=direct,
    )
    value = shape.value()
    where: JSONObject = {} if value is _ABSENT else {"probe": value}
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, shape.key.label, {"where": where})
    answer = {"unwalked": shape.unwalked, "related-filter": shape.walked, "hiding": shape.hiding}
    assert _answer(payload) == answer[walk], payload
    # A walked leaf the request leaves out is asked first whether it constrains
    # (``FilterSet._absent_leaf_applies``), then applied; ``apply_sync`` reads a ``null``
    # as left out.
    absent = value is _ABSENT or (value is None and not direct)
    received = shape.received if walk == "unwalked" else shape.walked_received
    if walk == "related-filter" and shape.related_received is not None:
        received = shape.related_received
    assert [received] * (2 if absent and walk != "unwalked" else 1) == _CALLS
    root = 0 if isinstance(answer[walk], str) else 1
    expected = shape.reads * len(_CALLS) + shape.cleans + root
    if shape.statements is not None:
        expected = shape.statements[["unwalked", "related-filter", "hiding"].index(walk)]
    assert len(queries.captured_queries) == expected, queries.captured_queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
@pytest.mark.parametrize(
    "name",
    [
        "single-null-hidden",
        "multi-absent-hidden",
        "multi-empty-visible",
        "hidden-raw-pk-the-global-id-refuses",
        "malformed-id-a-tolerant-override-reads",
        "mistyped-id-a-tolerant-override-reads",
    ],
)
def test_an_async_key_override_whose_value_names_no_row_runs_over_the_visible_related_rows(
    name: str,
    walk: str,
) -> None:
    """``apply_async`` runs a value naming no row as ``apply_sync`` does."""
    _world()
    shape = _UNNAMED[name]
    schema = _schema(
        _filterset(_unnamed_case(shape), walk),
        shape.key.model,
        shape.key.label,
        transport="async",
    )
    value = shape.value()
    where: JSONObject = {} if value is _ABSENT else {"probe": value}
    _CALLS.clear()
    payload = _post(schema, shape.key.label, {"where": where}, transport="async")
    assert _answer(payload) == (shape.unwalked if walk == "unwalked" else shape.hiding), payload
    absent = value is _ABSENT or value is None
    received = shape.received if walk == "unwalked" else shape.walked_received
    assert [received] * (2 if absent and walk != "unwalked" else 1) == _CALLS
