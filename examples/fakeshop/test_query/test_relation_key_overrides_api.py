"""A class-level ``filter`` override on a walked relation key runs as declared, over visible rows.

A consumer ``Filter`` subclass overriding ``filter`` on a relation key (a to-many key at any
hop count, a to-one key two or more hops away) receives the ``field_name`` it was declared
with, the value its form cleaned and the rows of the set declaring it, exactly as when no
hop is walked; a supplied value runs it once per request (a leaf the request leaves out is
first asked whether it constrains, then applied). The parents it keeps must also reach,
through each hop's visible rows, a visible last-hop row (on a to-many key one its value
names), so a row a target type hides matches nothing. On a to-many key a value naming no row
of the relation's target (an empty or absent choice, instances or a key of another model, a
value the key's own comparison skips or refuses) runs the override as declared over the rows
of the set declaring it, its ``field_name`` an alias of its relation that joins only the
related rows the walk keeps visible (a many-to-many's through rows included; a first
non-null forward key the database enforces joined round its target, so a parent whose
related row is hidden is kept, any other first key joined as Django joins it) and its
``lookup_expr`` the walked lookup: a default it reads (a key, model instances, a queryset,
one instance, a GlobalID, through a crossing ``lookup_expr`` too), a path it continues past
the relation (``__pk__in``, ``__code``, ``__isnull``), ``exclude``, ``conjoined`` and
Django's own refusal answer as unwalked, over visible rows, through every relation a
declared hop crosses and its ``RelatedFilter(queryset=...)``, and under a connection's
count, order and pages; a relation the override's own Python names reads every row, its own
scoping. Each request reaches the leaf over HTTP through ``FilterSet.apply_sync`` /
``apply_async`` or the set's own form.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable, Generator, Mapping, Sequence
from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.db import connection
from django.db import models as db_models
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
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, GlobalIDFilter, RelatedFilter
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import list_of, read_attr, require_instance
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

_M = TypeVar("_M", bound=Model)
if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

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
_SHELF_ALT_BRANCHES = _Key(
    models.Book,
    "title",
    "shelf",
    models.Shelf,
    lambda rows: rows.exclude(topic="secret"),
    models.Shelf,
)
_SIGNAGE_SHELVES = _Key(
    models.BranchSignage,
    "code",
    "branch",
    models.VisibleBranch,
    lambda rows: rows.exclude(name="beta"),
    models.VisibleBranch,
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
    open_shelf.alt_branches.add(alpha)
    secret_shelf.alt_branches.add(beta)
    # Signage reaches its branch through the ``VisibleBranch`` proxy, whose manager keeps
    # only branches with a city.
    models.Branch.objects.update(city="here")
    for branch in (alpha, beta, models.Branch.objects.get(name="gamma")):
        models.BranchSignage.objects.create(code=f"s-{branch.name}", branch_id=branch.pk)
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
#: reads as the hidden ``secret-book`` names no book and runs as declared with its relation
#: joined to the visible books. The flat copy walks the declared ``shelves`` hop on every
#: walk.
_CHILD_ANSWERS: dict[tuple[str, str, str], tuple[list[str], tuple[str, str, str]]] = {
    ("nested", "named", "unwalked"): (["alpha", "beta"], ("books", "list", "Shelf")),
    ("nested", "named", "hiding"): (["alpha"], ("books", "list", "Shelf")),
    ("flat", "named", "unwalked"): (["alpha", "beta"], ("shelves__books", "list", "Branch")),
    ("flat", "named", "hiding"): (["alpha"], ("shelves__books", "list", "Branch")),
    ("projected", "named", "unwalked"): (["alpha", "beta"], ("books", "list", "Shelf")),
    ("projected", "named", "hiding"): (["alpha"], ("books", "list", "Shelf")),
    ("nested", "hidden-default", "unwalked"): (["beta"], ("books", "QuerySet", "Shelf")),
    ("nested", "hidden-default", "hiding"): ([], ("books_visible", "QuerySet", "Shelf")),
    ("flat", "hidden-default", "unwalked"): (["beta"], ("books_visible", "QuerySet", "Branch")),
    ("flat", "hidden-default", "hiding"): ([], ("books_visible", "QuerySet", "Branch")),
    ("projected", "hidden-default", "unwalked"): (["beta"], ("books", "QuerySet", "Shelf")),
    ("projected", "hidden-default", "hiding"): ([], ("books_visible", "QuerySet", "Shelf")),
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


def _default_rows(default: tuple[type[Model], str, str], *more: str) -> QuerySet[Model]:
    model, field, name = default
    return model._default_manager.filter(**{f"{field}__in": [name, *more]}).order_by("pk")


class _InstanceDefaults(ModelMultipleChoiceFilter):
    """Reads an empty or absent selection as its ``default`` rows, model instances."""

    def __init__(
        self,
        *,
        field_name: str,
        queryset: QuerySet[Model],
        default: tuple[type[Model], str, str],
        more: tuple[str, ...] = (),
        exclude: bool = False,
        conjoined: bool = False,
        lookup_expr: str = "exact",
    ) -> None:
        super().__init__(
            field_name=field_name,
            queryset=queryset,
            exclude=exclude,
            conjoined=conjoined,
            lookup_expr=lookup_expr,
        )
        self.default = default
        self.more = more

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return super().filter(qs, value or list(_default_rows(self.default, *self.more)))


class _PkDefaults(_InstanceDefaults):
    """Reads an empty or absent selection as its ``default`` rows' keys."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        pks = [read_attr(row, "pk") for row in _default_rows(self.default, *self.more)]
        return ModelMultipleChoiceFilter.filter(self, qs, value or pks)


class _QuerySetDefault(_InstanceDefaults):
    """Reads an empty selection as a queryset of its ``default`` rows."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return ModelMultipleChoiceFilter.filter(self, qs, value or _default_rows(self.default))


class _PkInDefault(_InstanceDefaults):
    """Compares its rows' keys past the relation, ``<field_name>__pk__in``, a default for none."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        rows = list_of(value) or list(_default_rows(self.default))
        pks = [read_attr(row, "pk") for row in rows]
        return qs.filter(**{f"{self.field_name}__pk__in": pks}).distinct()


class _DistinctWhenEmpty(ModelMultipleChoiceFilter):
    """Constrains nothing for an empty selection, returning a new queryset as it does so."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if not value:
            return qs.distinct()
        return super().filter(qs, value)


class _NoneRelatedWhenEmpty(ModelMultipleChoiceFilter):
    """Reads an empty selection as "no related row", ``<field_name>__isnull=True``."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if not value:
            return qs.filter(**{f"{self.field_name}__isnull": True}).distinct()
        return super().filter(qs, value)


class _NamesItsRelation(_InstanceDefaults):
    """Names ``shelves`` in its own Python, not through ``field_name``: its own scoping."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        rows = list_of(value) or list(_default_rows(self.default))
        return qs.filter(shelves__in=rows).distinct()


class _InstanceDefault(ModelChoiceFilter):
    """Reads an empty choice as its ``default`` row, one model instance."""

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
        return super().filter(qs, value or _default_rows(self.default).get())


class _GlobalIDDefault(GlobalIDFilter):
    """Reads an empty id as the GlobalID of its ``default`` shelf, as a consumer default may."""

    def __init__(self, *, field_name: str, node_id: Callable[[], str]) -> None:
        super().__init__(field_name=field_name)
        self.node_id = node_id

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        return super().filter(qs, value or str(relay.GlobalID("library.shelf", self.node_id())))


#: The value a request leaves out of its input.
_ABSENT = object()


@dataclass(frozen=True)
class _Unnamed:
    """An override whose value names no row of the relation's target, and the parent's answer.

    ``walked`` is what the walked leaf answers (its rows, or the error Django raises for its
    value), as unwalked over the visible related rows; ``received`` / ``walked_received`` are
    the calls it records unwalked and walked (walked, its ``field_name`` is the alias of its
    relation, ``<relation>_visible``). A request runs one statement per call when the
    override reads its default row (``reads``), ``cleans`` for its form's choices, and the
    root query unless the leaf raises; ``statements`` pins the unwalked, walked and
    hiding counts of an override answering no row by an empty queryset.
    """

    key: _Key
    declare: Callable[[], Filter]
    value: Callable[[], object]
    unwalked: Sequence[str] | str
    walked: Sequence[str] | str
    hiding: Sequence[str] | str
    received: tuple[str, str, str]
    walked_received: tuple[str, str, str]
    reads: int = 1
    cleans: int = 0
    statements: tuple[int, int, int] | None = None


_SHELF = (models.Shelf, "code", "open")
_HIDDEN_SHELF = (models.Shelf, "code", "secret")
_DRAMA = (models.Genre, "name", "drama")
_HIDDEN_GENRE = (models.Genre, "name", "secret")
_HIDDEN_BOOK = (models.Book, "title", "secret-book")
_DELTA_SHELF = (models.Shelf, "code", "delta-open")
_ALT_BETA = (models.Branch, "name", "beta")
#: Django's refusal of a book compared on the shelves relation, walked as unwalked.
_NOT_A_SHELF = 'Cannot query "open-book": Must be "Shelf" instance.'
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
        ("shelves_visible", "NoneType", "Branch"),
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
        ("shelves_visible", "NoneType", "Branch"),
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
        ("shelves_visible", "QuerySet", "Branch"),
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
        ("shelves_visible", "QuerySet", "Branch"),
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
        ("shelves_visible", "QuerySet", "Branch"),
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
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "m2m-empty-visible": _Unnamed(
        _GENRES,
        lambda: _DefaultChoices(field_name="genres", queryset=_genres(), default=_DRAMA),
        list,
        ["mixed-book", "open-book"],
        ["mixed-book", "open-book"],
        ["mixed-book", "open-book"],
        ("genres", "QuerySet", "Book"),
        ("genres_visible", "QuerySet", "Book"),
    ),
    "m2m-empty-hidden": _Unnamed(
        _GENRES,
        lambda: _DefaultChoices(field_name="genres", queryset=_genres(), default=_HIDDEN_GENRE),
        list,
        ["mixed-book", "secret-book"],
        ["mixed-book", "secret-book"],
        [],
        ("genres", "QuerySet", "Book"),
        ("genres_visible", "QuerySet", "Book"),
    ),
    "instances-of-another-model": _Unnamed(
        _SHELVES,
        lambda: _BookPicker(field_name="shelves", queryset=models.Book.objects.all()),
        lambda: _pks(models.Book, "title", "open-book"),
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "list", "Branch"),
        ("shelves_visible", "list", "Branch"),
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
        ("shelves_visible", "str", "Branch"),
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
        ("shelves_visible", "str", "Branch"),
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
        ("shelves_visible", "str", "Branch"),
        reads=0,
        statements=(0, 0, 0),
    ),
    "mistyped-id-a-tolerant-override-reads": _Unnamed(
        _SHELVES,
        lambda: _TolerantGlobalID(field_name="shelves"),
        lambda: str(relay.GlobalID("library.book", _pks(models.Shelf, "code", "open")[0])),
        [],
        [],
        [],
        ("shelves", "str", "Branch"),
        ("shelves_visible", "str", "Branch"),
        reads=0,
        statements=(0, 0, 0),
    ),
    "text-the-key-column-refuses": _Unnamed(
        _SHELVES,
        lambda: _CodeText(field_name="shelves"),
        lambda: "open",
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "str", "Branch"),
        ("shelves_visible", "str", "Branch"),
        reads=0,
    ),
    "instances-default-visible": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefaults(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_SHELF,
        ),
        list,
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "instances-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefaults(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "lazy-field-name-pk-in-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _respelled(
            _PkInDefault(
                field_name="shelves",
                queryset=models.Shelf.objects.all(),
                default=_HIDDEN_SHELF,
            ),
            field_name=SimpleLazyObject(lambda: "shelves"),
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "queryset-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _QuerySetDefault(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "instance-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefault(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        lambda: None,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "NoneType", "Branch"),
        ("shelves_visible", "NoneType", "Branch"),
    ),
    "pk-in-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _PkInDefault(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "hidden-text-the-key-column-refuses": _Unnamed(
        _SHELVES,
        lambda: _CodeText(field_name="shelves"),
        lambda: "secret",
        ["beta"],
        ["beta"],
        [],
        ("shelves", "str", "Branch"),
        ("shelves_visible", "str", "Branch"),
        reads=0,
    ),
    "exclude-instances-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefaults(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
            exclude=True,
        ),
        list,
        ["alpha", "delta", "gamma"],
        ["alpha", "delta", "gamma"],
        [
            "alpha",
            "beta",
            "delta",
            "gamma",
        ],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "conjoined-instances-default-hidden-member": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefaults(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_DELTA_SHELF,
            more=("delta-secret",),
            conjoined=True,
        ),
        list,
        ["delta"],
        ["delta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "m2m-instances-default-hidden": _Unnamed(
        _GENRES,
        lambda: _InstanceDefaults(
            field_name="genres",
            queryset=_genres(),
            default=_HIDDEN_GENRE,
        ),
        list,
        ["mixed-book", "secret-book"],
        ["mixed-book", "secret-book"],
        [],
        ("genres", "QuerySet", "Book"),
        ("genres_visible", "QuerySet", "Book"),
    ),
    "two-hop-instances-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefaults(
            field_name="shelves__books",
            queryset=models.Book.objects.all(),
            default=_HIDDEN_BOOK,
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves__books", "QuerySet", "Branch"),
        ("books_visible", "QuerySet", "Branch"),
    ),
    "global-id-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _GlobalIDDefault(
            field_name="shelves",
            node_id=lambda: str(_default_pk(_HIDDEN_SHELF)),
        ),
        lambda: "",
        ["beta"],
        ["beta"],
        [],
        ("shelves", "str", "Branch"),
        ("shelves_visible", "str", "Branch"),
    ),
    "empty-the-override-skips-by-a-new-queryset": _Unnamed(
        _SHELVES,
        lambda: _DistinctWhenEmpty(field_name="shelves", queryset=models.Shelf.objects.all()),
        list,
        [
            "alpha",
            "beta",
            "delta",
            "gamma",
        ],
        [
            "alpha",
            "beta",
            "delta",
            "gamma",
        ],
        [
            "alpha",
            "beta",
            "delta",
            "gamma",
        ],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
        reads=0,
    ),
    "crossing-lookup-pk-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _PkDefaults(
            field_name="shelves",
            lookup_expr="books",
            queryset=models.Book.objects.all(),
            default=_HIDDEN_BOOK,
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("books_visible", "QuerySet", "Branch"),
    ),
    "crossing-lookup-instances-default-visible": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefaults(
            field_name="shelves",
            lookup_expr="books",
            queryset=models.Book.objects.all(),
            default=(models.Book, "title", "open-book"),
        ),
        list,
        ["alpha"],
        ["alpha"],
        ["alpha"],
        ("shelves", "QuerySet", "Branch"),
        ("books_visible", "QuerySet", "Branch"),
    ),
    "crossing-lookup-instances-default-hidden": _Unnamed(
        _SHELVES,
        lambda: _InstanceDefaults(
            field_name="shelves",
            lookup_expr="books",
            queryset=models.Book.objects.all(),
            default=_HIDDEN_BOOK,
        ),
        list,
        ["beta"],
        ["beta"],
        [],
        ("shelves", "QuerySet", "Branch"),
        ("books_visible", "QuerySet", "Branch"),
    ),
    "m2m-no-related-row-when-empty": _Unnamed(
        _GENRES,
        lambda: _NoneRelatedWhenEmpty(field_name="genres", queryset=_genres()),
        list,
        ["delta-open-book", "delta-secret-book"],
        ["delta-open-book", "delta-secret-book"],
        ["delta-open-book", "delta-secret-book", "secret-book"],
        ("genres", "QuerySet", "Book"),
        ("genres_visible", "QuerySet", "Book"),
        reads=0,
    ),
    "forward-then-m2m-no-related-row-when-empty": _Unnamed(
        _SHELF_ALT_BRANCHES,
        lambda: _NoneRelatedWhenEmpty(
            field_name="shelf__alt_branches",
            queryset=models.Branch.objects.all(),
        ),
        list,
        ["delta-open-book", "delta-secret-book"],
        ["delta-open-book", "delta-secret-book"],
        ["delta-open-book", "delta-secret-book", "secret-book"],
        ("shelf__alt_branches", "QuerySet", "Book"),
        ("alt_branches_visible", "QuerySet", "Book"),
        reads=0,
    ),
    "proxy-then-to-many-no-related-row-when-empty": _Unnamed(
        _SIGNAGE_SHELVES,
        lambda: _NoneRelatedWhenEmpty(
            field_name="branch__shelves",
            queryset=models.Shelf.objects.all(),
        ),
        list,
        ["s-gamma"],
        ["s-gamma"],
        ["s-beta", "s-gamma"],
        ("branch__shelves", "QuerySet", "BranchSignage"),
        ("shelves_visible", "QuerySet", "BranchSignage"),
        reads=0,
    ),
    "forward-then-m2m-no-related-row-when-absent": _Unnamed(
        _SHELF_ALT_BRANCHES,
        lambda: _NoneRelatedWhenEmpty(
            field_name="shelf__alt_branches",
            queryset=models.Branch.objects.all(),
        ),
        lambda: _ABSENT,
        ["delta-open-book", "delta-secret-book"],
        ["delta-open-book", "delta-secret-book"],
        ["delta-open-book", "delta-secret-book", "secret-book"],
        ("shelf__alt_branches", "QuerySet", "Book"),
        ("alt_branches_visible", "QuerySet", "Book"),
        reads=0,
    ),
    "forward-then-m2m-instances-default-hidden": _Unnamed(
        _SHELF_ALT_BRANCHES,
        lambda: _InstanceDefaults(
            field_name="shelf__alt_branches",
            queryset=models.Branch.objects.all(),
            default=_ALT_BETA,
        ),
        list,
        ["secret-book"],
        ["secret-book"],
        [],
        ("shelf__alt_branches", "QuerySet", "Book"),
        ("alt_branches_visible", "QuerySet", "Book"),
    ),
    "forward-then-m2m-pk-in-default-hidden": _Unnamed(
        _SHELF_ALT_BRANCHES,
        lambda: _PkInDefault(
            field_name="shelf__alt_branches",
            queryset=models.Branch.objects.all(),
            default=_ALT_BETA,
        ),
        list,
        ["secret-book"],
        ["secret-book"],
        [],
        ("shelf__alt_branches", "QuerySet", "Book"),
        ("alt_branches_visible", "QuerySet", "Book"),
    ),
    "reverse-fk-no-related-row-when-empty": _Unnamed(
        _SHELVES,
        lambda: _NoneRelatedWhenEmpty(field_name="shelves", queryset=models.Shelf.objects.all()),
        list,
        ["gamma"],
        ["gamma"],
        ["gamma"],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
        reads=0,
    ),
    "a-relation-its-own-python-names-reads-every-row": _Unnamed(
        _SHELVES,
        lambda: _NamesItsRelation(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_HIDDEN_SHELF,
        ),
        list,
        ["beta"],
        ["beta"],
        ["beta"],
        ("shelves", "QuerySet", "Branch"),
        ("shelves_visible", "QuerySet", "Branch"),
    ),
    "a-key-of-another-model": _Unnamed(
        _SHELVES,
        lambda: _Recorded(field_name="shelves", queryset=models.Book.objects.all()),
        lambda: _pks(models.Book, "title", "open-book"),
        _NOT_A_SHELF,
        _NOT_A_SHELF,
        _NOT_A_SHELF,
        ("shelves", "list", "Branch"),
        ("shelves_visible", "list", "Branch"),
        reads=0,
        cleans=1,
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
    """A value naming no row of the target runs as declared through the visible related rows.

    An empty or absent choice the override reads as a default, or instances or a key of
    another model, name no row of the relation's target: walked, the override runs over its
    own set's rows with its relation joined only to the visible related rows, so a visible
    default answers its parents as unwalked, a hidden one matches nothing, and a value
    Django refuses raises Django's own error.
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
        "instances-default-hidden",
        "queryset-default-hidden",
        "exclude-instances-default-hidden",
        "m2m-instances-default-hidden",
        "two-hop-instances-default-hidden",
        "crossing-lookup-pk-default-hidden",
        "crossing-lookup-instances-default-hidden",
        "m2m-no-related-row-when-empty",
        "forward-then-m2m-no-related-row-when-empty",
        "forward-then-m2m-no-related-row-when-absent",
        "proxy-then-to-many-no-related-row-when-empty",
        "a-key-of-another-model",
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


def _visible_shelf_node(walk: str) -> None:
    """A ``Shelf`` Relay type whose GlobalID carries its ``code``, hiding secret shelves."""
    attrs: dict[str, object] = {
        "__annotations__": {"code": relay.NodeID[str]},
        "Meta": type(
            "Meta",
            (),
            {"model": models.Shelf, "fields": ("id", "code"), "interfaces": (relay.Node,)},
        ),
    }
    if walk == "hiding":

        def get_queryset(
            _cls: type[DjangoType],
            queryset: QuerySet[Model],
            _info: object,
        ) -> QuerySet[Model]:
            return queryset.exclude(topic="secret")

        attrs["get_queryset"] = classmethod(get_queryset)
    type("ShelfRows", (DjangoType,), attrs)


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "related-filter", "hiding"])
@pytest.mark.parametrize("direct", [False, True], ids=["apply-sync", "form"])
def test_a_global_id_default_compares_an_off_key_node_id_through_the_visible_relation(
    walk: str,
    *,
    direct: bool,
) -> None:
    """A default naming a shelf by the ``code`` its GlobalID carries compares through the relation.

    The shelves' type publishes ``code`` as its Relay ``NodeID``: walked, the override's own
    GlobalID default compares that column on the shelves its relation joins, visible only.
    """
    _world()
    attrs: dict[str, object] = {
        "probe": _GlobalIDDefault(field_name="shelves", node_id=lambda: "secret"),
        "Meta": type("Meta", (), {"model": models.Branch, "fields": ["name"]}),
    }
    if walk == "related-filter":
        child = type(
            "HopChild",
            (FilterSet,),
            {"Meta": type("Meta", (), {"model": models.Shelf, "fields": []})},
        )
        attrs["hop"] = RelatedFilter(child, field_name="shelves")
    _visible_shelf_node(walk)
    schema = _schema(type("Shelves", (FilterSet,), attrs), models.Branch, "name", direct=direct)
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, "name", {"where": {"probe": ""}})
    assert _answer(payload) == ([] if walk == "hiding" else ["beta"]), payload
    received = "shelves" if walk == "unwalked" else "shelves_visible"
    assert [(received, "str", "Branch")] == _CALLS
    assert len(queries.captured_queries) == 1, queries.captured_queries


#: ``scope -> rows`` a declared hop over two relations (``Branch`` through its shelves to
#: their books) answers for a book override reading an empty selection as the secret genre:
#: the mixed book (an open shelf) and the secret book (a secret shelf) carry it.
_THROUGH_SHELVES: dict[str, list[str]] = {
    "open": ["alpha", "beta"],
    "hidden-shelves": ["alpha"],
    "hidden-genres": [],
    "admitted-books": ["beta"],
}


@pytest.mark.django_db
@pytest.mark.parametrize("arm", [False, True], ids=["flat", "and-arm"])
@pytest.mark.parametrize("scope", list(_THROUGH_SHELVES))
def test_a_key_override_default_through_a_declared_hop_over_two_relations_reads_visible_rows(
    scope: str,
    *,
    arm: bool,
) -> None:
    """Every relation the walk crosses joins only the rows the request may see.

    The intermediate shelves its type hides, the genres its type hides and the books the
    ``RelatedFilter(queryset=...)`` leaves out each drop a parent the default reaches only
    through them. A second leaf in an ``and_`` arm joins the relation again under a name of
    its own.
    """
    _world()

    class BookChild(FilterSet):
        probe = _InstanceDefaults(
            field_name="genres",
            queryset=_genres(),
            default=_HIDDEN_GENRE,
        )

        class Meta:
            model = models.Book
            fields = ["title"]

    admitted = (
        models.Book.objects.exclude(title="mixed-book")
        if scope == "admitted-books"
        else models.Book.objects.all()
    )

    class Branches(FilterSet):
        books = RelatedFilter(BookChild, field_name="shelves__books", queryset=admitted)

        class Meta:
            model = models.Branch
            fields = ["name"]

    _node(
        models.Shelf,
        (lambda rows: rows.exclude(topic="secret")) if scope == "hidden-shelves" else None,
    )
    _node(models.Book)
    _node(
        models.Genre,
        (lambda rows: rows.exclude(name="secret")) if scope == "hidden-genres" else None,
    )
    schema = _schema(Branches, models.Branch, "name")
    where: JSONObject = {"books__probe": []}
    if arm:
        where["and_"] = [{"books__probe": []}]
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, "name", {"where": where})
    assert _answer(payload) == _THROUGH_SHELVES[scope], payload
    aliases = ["genres_visible", "genres_visible_2"] if arm else ["genres_visible"]
    assert [(alias, "QuerySet", "Branch") for alias in aliases] == _CALLS
    # Each call reads its default rows; then the root query.
    assert len(queries.captured_queries) == len(aliases) + 1, queries.captured_queries


@pytest.mark.django_db
@pytest.mark.parametrize("walk", ["unwalked", "hiding"])
def test_a_key_override_default_pages_counts_and_orders_its_visible_parents(walk: str) -> None:
    """A connection over the parents the override's default keeps counts and pages only them.

    The default names the open shelves and two secret ones; walked under a type hiding the
    secret shelves, the delta branch, reaching only a secret one, drops out of the count, the
    order and each page.
    """
    _world()

    class Shelves(FilterSet):
        probe = _InstanceDefaults(
            field_name="shelves",
            queryset=models.Shelf.objects.all(),
            default=_SHELF,
            more=("beta-open", "secret", "delta-secret"),
        )

        class Meta:
            model = models.Branch
            fields = ["name"]

    class Names(OrderSet):
        class Meta:
            model = models.Branch
            fields = ["name"]

    _node(models.Shelf, _SHELVES.hidden if walk == "hiding" else None)
    root = type(
        "BranchPages",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": models.Branch,
                    "fields": ("id", "name"),
                    "interfaces": (relay.Node,),
                    "filterset_class": Shelves,
                    "orderset_class": Names,
                    "connection": {"total_count": True},
                },
            ),
        },
    )

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(root)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    expected = ["delta", "beta", "alpha"] if walk == "unwalked" else ["beta", "alpha"]
    after = ""
    for index, name in enumerate(expected):
        document = (
            "query { rows(filter: {probe: {exact: []}}, orderBy: [{name: DESC}], "
            f"first: 1{after}) "
            "{ totalCount edges { cursor node { name } } pageInfo { hasNextPage } } }"
        )
        _CALLS.clear()
        _CURRENT["schema"] = schema
        try:
            with (
                override_settings(ROOT_URLCONF=__name__),
                CaptureQueriesContext(connection) as queries,
            ):
                payload = graphql_payload(document, url="/graphql-key-overrides/")
        finally:
            _CURRENT["schema"] = None
        page = json_object(json_at(payload, "data", "rows"))
        assert json_at(page, "totalCount") == len(expected), payload
        edge = json_object(json_at(page, "edges", 0))
        assert json_at(edge, "node", "name") == name, payload
        assert json_at(page, "pageInfo", "hasNextPage") == (index < len(expected) - 1), payload
        received = "shelves" if walk == "unwalked" else "shelves_visible"
        assert [(received, "QuerySet", "Branch")] == _CALLS
        # The default rows, the count and the page.
        assert len(queries.captured_queries) == 3, queries.captured_queries
        after = f', after: "{json_at(edge, "cursor")}"'


#: ``first hop -> (model, label, field_name, target, rows walked under a type hiding the
#: secret shelf or desk)`` for a to-many view whose first relation the round trip cannot reach.
_INNER_FIRST: dict[str, tuple[type[Model], str, str, type[Model], Sequence[str]]] = {
    "foreign-object": (
        models.ShelfLabel,
        "text",
        "shelf__books",
        models.Book,
        ["l-beta-open"],
    ),
    "inheritance-child": (
        models.KioskFault,
        "note",
        "kiosk__repairticket",
        models.RepairTicket,
        ["f-bare"],
    ),
}


def _inner_first_world() -> None:
    """``_world``, four shelf labels (one naming no shelf) and three faulted kiosk desks."""
    _world()
    branches = {branch.name: branch for branch in models.Branch.objects.all()}
    for text, branch, code in (
        ("l-open", "alpha", "open"),
        ("l-secret", "beta", "secret"),
        ("l-beta-open", "beta", "beta-open"),
        ("l-dangling", "gamma", "none"),
    ):
        models.ShelfLabel.objects.create(text=text, branch=branches[branch], shelf_code=code)
    for name in ("open", "secret", "bare"):
        desk = models.SelfServeDesk.objects.create(name=name, kiosk_code=name)
        models.KioskFault.objects.create(kiosk=desk, note=f"f-{name}")
        if name == "open":
            models.RepairTicket.objects.create(venue=desk, code="t-open")


@pytest.mark.django_db
@pytest.mark.parametrize("direct", [False, True], ids=["apply-sync", "form"])
@pytest.mark.parametrize("first", list(_INNER_FIRST))
def test_a_to_many_view_through_a_key_no_round_trip_reaches_keeps_its_inner_join(
    first: str,
    *,
    direct: bool,
) -> None:
    """A first key the view cannot join round its target keeps Django's inner join.

    A bare ``ForeignObject`` (``ShelfLabel.shelf``, whose key may name no shelf) and a key
    onto a multi-table-inheritance child (``KioskFault.kiosk``, whose parent tables Django
    would join ahead of the round trip's outer join) are joined as Django joins them: an
    override reading an empty choice as no related row keeps only the parents reaching a
    visible first row with none past it. The first alias is joined before any join that
    references it (the parent tables a later inherited hop crosses included), an order
    PostgreSQL requires.
    """
    _inner_first_world()
    model, label, field_name, target, rows = _INNER_FIRST[first]
    _node(models.Venue)
    _node(models.LendingDesk)
    _node(models.SelfServeDesk, lambda desks: desks.exclude(name="secret"))
    _node(models.Shelf, _SHELVES.hidden)
    _node(models.Book)
    _node(models.RepairTicket)

    inner = type(
        "Inner",
        (FilterSet,),
        {
            "probe": _NoneRelatedWhenEmpty(
                field_name=field_name,
                queryset=target._default_manager.all(),
            ),
            "Meta": type("Meta", (), {"model": model, "fields": [label]}),
        },
    )
    schema = _schema(inner, model, label, direct=direct)
    _CALLS.clear()
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, label, {"where": {"probe": []}})
    assert _answer(payload) == list(rows), payload
    segment = field_name.rsplit("__", 1)[-1]
    assert [(f"{segment}_visible", "QuerySet", model.__name__)] == _CALLS
    # Read the alias as the JOIN introducing it spells it: Django 5.2's compiler leaves a join
    # alias bare, Django 6.1's quotes it.
    alias = f"{field_name.split('__', 1)[0]}_visible"
    introduced = re.compile(rf'JOIN \S+ ("?{alias}"?) ON ')
    joined = [
        (query["sql"], match.group(1))
        for query in queries.captured_queries
        if (match := introduced.search(query["sql"])) is not None
    ]
    assert joined, queries.captured_queries
    for sql, spelled in joined:
        assert sql.index(f"{spelled} ON") < sql.index(f"{spelled}."), sql


def _round_trip_model_meta(table: str) -> type[object]:
    return type("Meta", (), {"app_label": "library", "managed": False, "db_table": table})


def _round_trip_source_models() -> dict[str, type[Model]]:
    """Register source models only while their test-local database tables exist."""
    linked = type(
        "RoundTripLinkedBook",
        (models.Book,),
        {"__module__": __name__, "Meta": _round_trip_model_meta("live_round_trip_linked_book")},
    )
    independent = type(
        "RoundTripIndependentBook",
        (models.Book,),
        {
            "__module__": __name__,
            "Meta": _round_trip_model_meta("live_round_trip_independent_book"),
            "catalog_number": db_models.IntegerField(primary_key=True),
        },
    )

    class RoundTripCompositeBook(db_models.Model):
        """Both source key columns identify the row reached by the reverse shelf join."""

        tenant: db_models.IntegerField["float | int | str | Combinable", int] = (
            db_models.IntegerField()
        )
        sequence: db_models.IntegerField["float | int | str | Combinable", int] = (
            db_models.IntegerField()
        )
        pk = db_models.CompositePrimaryKey("tenant", "sequence")
        title: db_models.TextField["str | Combinable", str] = db_models.TextField()
        shelf: db_models.ForeignKey["models.Shelf | Combinable", models.Shelf] = (
            db_models.ForeignKey(
                models.Shelf,
                related_name="round_trip_composite_books",
                on_delete=db_models.CASCADE,
            )
        )

        class Meta:
            app_label = "library"
            managed = False
            db_table = "live_round_trip_composite_book"

        @override
        def __str__(self) -> str:
            return self.title

    return {
        "parent-link-pk": linked,
        "independent-child-pk": independent,
        "composite-pk": RoundTripCompositeBook,
    }


@pytest.fixture
def round_trip_source_tables(transactional_db: None) -> Generator[dict[str, type[Model]]]:
    """Give the three native HTTP source shapes real tables for their relation joins."""
    _ = transactional_db
    source_models = _round_trip_source_models()
    with connection.schema_editor() as editor:
        for model in source_models.values():
            editor.create_model(model)
    try:
        yield source_models
    finally:
        with connection.schema_editor() as editor:
            for model in reversed(tuple(source_models.values())):
                editor.delete_model(model)


def _create_round_trip_row(
    model: type[Model],
    title: str,
    shelf: models.Shelf,
    key: dict[str, int],
) -> None:
    model._default_manager.create(title=title, shelf=shelf, **key)


def _round_trip_source_rows(model: type[Model], kind: str) -> None:
    """Put visible and hidden shelves behind every source key shape."""
    branch = models.Branch.objects.create(name="round-trip-branch")
    occupied = models.Shelf.objects.create(branch=branch, code="occupied", topic="open")
    empty = models.Shelf.objects.create(branch=branch, code="empty", topic="open")
    hidden = models.Shelf.objects.create(branch=branch, code="hidden", topic="secret")
    occupied.alt_branches.add(branch)
    hidden.alt_branches.add(branch)
    rows: list[tuple[str, models.Shelf, dict[str, int]]] = [
        ("visible-has", occupied, {"tenant": 1, "sequence": 1}),
        ("visible-none", empty, {"tenant": 1, "sequence": 2}),
        ("hidden-first", hidden, {"tenant": 2, "sequence": 1}),
    ]
    if kind == "composite-pk":
        rows.extend(
            [
                ("visible-has-peer-tenant", occupied, {"tenant": 1, "sequence": 3}),
                ("visible-has-peer-sequence", occupied, {"tenant": 3, "sequence": 1}),
            ],
        )
    for index, (title, shelf, composite_key) in enumerate(rows, start=1):
        key = (
            composite_key
            if kind == "composite-pk"
            else {"id": 10000 + index, "catalog_number": 1000 + index}
            if kind == "independent-child-pk"
            else {}
        )
        _create_round_trip_row(model, title, shelf, key)


class _HasRelatedWhenEmpty(ModelMultipleChoiceFilter):
    """Leave duplicates visible so a partial composite identity cannot look correct."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        _record(self.field_name, value, qs)
        if not value:
            return qs.filter(**{f"{self.field_name}__isnull": False})
        return super().filter(qs, value)


def _round_trip_visible_shelf_type() -> None:
    class ShelfRows(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("code",)

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Shelf],
            info: object,
        ) -> QuerySet[models.Shelf]:
            del cls, info
            return queryset.exclude(topic="secret")

    _ = ShelfRows


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("kind", ["parent-link-pk", "independent-child-pk", "composite-pk"])
@pytest.mark.parametrize("transport", ["sync", "form", "async"])
@pytest.mark.parametrize("supplied", [True, False], ids=["empty", "absent"])
@pytest.mark.parametrize("answer", ["none", "has"])
def test_a_round_trip_matches_the_declaring_sources_full_identity_over_http(
    round_trip_source_tables: dict[str, type[Model]],
    kind: str,
    transport: str,
    *,
    supplied: bool,
    answer: str,
) -> None:
    """An inherited or composite source sees the right visible first relation and no duplicates."""
    model = round_trip_source_tables[kind]
    _round_trip_source_rows(model, kind)
    _round_trip_visible_shelf_type()

    source_filter = type(
        "RoundTripSourceFilter",
        (FilterSet,),
        {
            "probe": (
                _NoneRelatedWhenEmpty(
                    field_name="shelf__alt_branches",
                    queryset=models.Branch.objects.all(),
                )
                if answer == "none"
                else _HasRelatedWhenEmpty(
                    field_name="shelf__alt_branches",
                    queryset=models.Branch.objects.all(),
                )
            ),
            "Meta": type("Meta", (), {"model": model, "fields": ["title"]}),
        },
    )

    where: JSONObject = {"probe": []} if supplied else {}
    schema = _schema(
        source_filter,
        model,
        "title",
        transport="async" if transport == "async" else "sync",
        direct=transport == "form",
    )
    _CALLS.clear()
    payload = _post(schema, "title", {"where": where}, transport=transport)
    expected = (
        ["hidden-first", "visible-none"]
        if answer == "none"
        else ["visible-has"]
        if kind != "composite-pk"
        else ["visible-has", "visible-has-peer-sequence", "visible-has-peer-tenant"]
    )
    assert _answer(payload) == expected, payload
    count = 1 if supplied else 2
    assert [("alt_branches_visible", "QuerySet", model.__name__)] * count == _CALLS


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("kind", ["independent-child-pk", "composite-pk"])
@pytest.mark.parametrize("mode", ["named", "default-path", "excluded-default"])
def test_a_round_trip_retains_named_and_default_relation_key_answers_over_http(
    round_trip_source_tables: dict[str, type[Model]],
    kind: str,
    mode: str,
) -> None:
    """The identity turn also leaves named choices and the override's own path/exclude intact."""
    model = round_trip_source_tables[kind]
    _round_trip_source_rows(model, kind)
    _round_trip_visible_shelf_type()
    field_name = "shelf__alt_branches"
    choice: ModelMultipleChoiceFilter = (
        _Recorded(field_name=field_name, queryset=models.Branch.objects.all())
        if mode == "named"
        else _PkInDefault(
            field_name=field_name,
            queryset=models.Branch.objects.all(),
            default=(models.Branch, "name", "round-trip-branch"),
            exclude=mode == "excluded-default",
        )
    )
    filterset = type(
        "RoundTripChoiceFilter",
        (FilterSet,),
        {"probe": choice, "Meta": type("Meta", (), {"model": model, "fields": ["title"]})},
    )
    values = _pks(models.Branch, "name", "round-trip-branch") if mode == "named" else []
    schema = _schema(filterset, model, "title")
    _CALLS.clear()
    payload = _post(schema, "title", {"where": {"probe": values}})
    visible = (
        ["visible-has"]
        if kind != "composite-pk"
        else ["visible-has", "visible-has-peer-sequence", "visible-has-peer-tenant"]
    )
    expected = ["hidden-first", "visible-none"] if mode == "excluded-default" else visible
    assert _answer(payload) == expected, payload
    received_name = field_name if mode == "named" else "alt_branches_visible"
    received_value = "list" if mode == "named" else "QuerySet"
    assert [(received_name, received_value, model.__name__)] == _CALLS
