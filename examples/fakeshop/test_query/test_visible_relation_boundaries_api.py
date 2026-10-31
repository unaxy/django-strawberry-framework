"""Native HTTP visibility across async hops, multi-relation branches and bound re-entry.

These consumers distinguish hidden intermediate rows from hidden terminal rows,
exercise actual async-only queryset hooks, and bind secondary-type authority
through Meta. The re-entry consumer deliberately applies its public FilterInput
set to all Shelf roots and returns a separate plain output type: direct filter
application owns no root visibility, while a relation re-entering Shelf reads
the type the set is bound to.
"""

import asyncio
import datetime
from collections.abc import Awaitable, Mapping, Sequence
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.library import models
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter, ModelChoiceFilter, NumberFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import JSONObject, graphql_payload, response_json
from strategy_schemas import make_django_type
from strawberry.scalars import JSON
from strawberry.types.base import StrawberryObjectDefinition

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterInput, FilterSet, RelatedFilter
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-visible-boundaries/", _graphql_view),
    path("graphql-visible-boundaries-async/", _async_graphql_view),
]


async def _async_post(document: str, variables: Mapping[str, object]) -> JSONObject:
    result = await AsyncTestClient().query(
        document,
        variables,
        assert_no_errors=False,
        url="/graphql-visible-boundaries-async/",
    )
    assert result.response.status_code == 200
    return response_json(result.response)


def _post(
    schema: DjangoSchema,
    document: str,
    where: JSONObject,
    *,
    transport: str = "sync",
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            variables = {"where": where}
            if transport == "async":
                return asyncio.run(_async_post(document, variables))
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-visible-boundaries/",
            )
    finally:
        _CURRENT["schema"] = None


def _type(
    name: str,
    model: type[django_models.Model],
    fields: tuple[str, ...],
    *,
    filterset: type[FilterSet] | None = None,
    hides: Mapping[str, object] | None = None,
    async_hook: bool = False,
    primary: bool = True,
    node: bool = False,
) -> type[DjangoType]:
    meta: dict[str, object] = {"primary": primary}
    if filterset is not None:
        meta["filterset_class"] = filterset
    if node:
        meta["connection"] = {"total_count": True}
        if not primary:
            # The primary may be non-Relay; this output owns type-scoped IDs.
            meta["globalid_strategy"] = "type"
    namespace: dict[str, object] = {}
    if hides is not None:
        lookups = dict(hides)

        def visible(
            _cls: type[DjangoType],
            queryset: django_models.QuerySet[django_models.Model],
            _info: object,
            **_kwargs: object,
        ) -> django_models.QuerySet[django_models.Model]:
            return queryset.exclude(**lookups)

        async def visible_async(
            _cls: type[DjangoType],
            queryset: django_models.QuerySet[django_models.Model],
            _info: object,
            **_kwargs: object,
        ) -> django_models.QuerySet[django_models.Model]:
            await asyncio.sleep(0)
            return queryset.exclude(**lookups)

        namespace["get_queryset"] = classmethod(visible_async if async_hook else visible)
    return make_django_type(
        name,
        model,
        fields,
        node=node,
        meta_extra=meta,
        namespace_extra=namespace,
    )


def _schema(
    root: type[DjangoType],
    model: type[django_models.Model],
    targets: Sequence[type[DjangoType]],
) -> DjangoSchema:
    def resolve_rows(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> django_models.QuerySet[django_models.Model]:
        return model._default_manager.order_by("pk")

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(root, resolver=resolve_rows)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=targets,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _input(schema: DjangoSchema, *, argument: str = "filter") -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args[argument]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(
    schema: DjangoSchema,
    python_path: Sequence[str],
    value: object,
    *,
    argument: str = "filter",
) -> JSONObject:
    """Ask the actual definitions and configured converter, rather than guessing published names."""
    current = _input(schema, argument=argument)
    published: list[str] = []
    for index, name in enumerate(python_path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == name)
        wire = schema.config.name_converter.from_field(field)
        published.append(wire)
        if index < len(python_path) - 1:
            target = get_named_type(graphql_type_of(graphql_input_fields(current)[wire]))
            assert isinstance(target, GraphQLInputObjectType)
            current = target
    assert published
    result: JSONObject = {published[-1]: value}
    for wire in reversed(published[:-1]):
        result = {wire: result}
    return result


def _arm(
    schema: DjangoSchema,
    operator: str,
    values: object,
    *,
    argument: str = "filter",
) -> JSONObject:
    return _where(schema, (operator,), values, argument=argument)


def _document(schema: DjangoSchema, scalar: str) -> str:
    return (
        f"query($where: {_input(schema).name}!) {{ rows(filter: $where) {{ "
        f"totalCount edges {{ node {{ id name: {scalar} }} }} }} }}"
    )


def _expected(
    row_type: type[DjangoType],
    rows: Sequence[tuple[django_models.Model, str]],
) -> JSONObject:
    return {
        "data": {
            "rows": {
                "totalCount": len(rows),
                "edges": [
                    {"node": {"id": global_id_for(row_type, saved_pk(row)), "name": name}}
                    for row, name in rows
                ],
            },
        },
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "case",
    [
        "key-null",
        "key-membership",
        "exclude",
        "key-not",
    ],
)
def test_async_only_target_hook_is_awaited_for_relation_keys_exclusion_and_negation(
    case: str,
) -> None:
    """An actual async Book scope hides repair rows before every key/excluding/logical predicate."""

    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    class GenreParent(FilterSet):
        visible_books = RelatedFilter(BookChild, field_name="books")
        without_title = CharFilter(field_name="books__title", exclude=True)

        class Meta:
            model = models.Genre
            fields = {"books": ["exact", "isnull"]}

    target = _type(
        "AsyncVisibleBook",
        models.Book,
        ("title",),
        filterset=BookChild,
        hides={"circulation_status": "repair"},
        async_hook=True,
    )
    row_type = _type(
        "AsyncGenreRoot",
        models.Genre,
        ("id", "name"),
        filterset=GenreParent,
        node=True,
    )
    home = models.Branch.objects.create(name="Async target")
    shelf = models.Shelf.objects.create(branch=home, code="ASYNC")
    hidden_shelf = models.Shelf.objects.create(branch=home, code="HIDDEN")
    open_x = models.Book.objects.create(shelf=shelf, title="x")
    hidden_x = models.Book.objects.create(
        shelf=hidden_shelf,
        title="x",
        circulation_status="repair",
    )
    hidden_y = models.Book.objects.create(
        shelf=hidden_shelf,
        title="y",
        circulation_status="repair",
    )
    open_y = models.Book.objects.create(shelf=shelf, title="y")
    genres: dict[str, models.Genre] = {}
    for name, books in [
        ("mixed", [open_x, hidden_x]),
        ("hidden-only", [hidden_x, hidden_y]),
        ("empty", []),
        ("plain", [open_x, open_y]),
        ("only-y", [open_y]),
    ]:
        genre = models.Genre.objects.create(name=name)
        genre.books.set(books)
        genres[name] = genre
    schema = _schema(row_type, models.Genre, (target,))
    if case == "key-null":
        where = _where(schema, ("books", "is_null"), value=True)
        names = ["hidden-only", "empty"]
    elif case == "key-membership":
        where = _where(schema, ("books", "exact"), [saved_pk(open_x), saved_pk(hidden_x)])
        names = ["mixed", "plain"]
    elif case == "exclude":
        where = _where(schema, ("without_title", "exact"), "x")
        names = ["hidden-only", "empty", "only-y"]
    else:
        where = _arm(schema, "not_", _where(schema, ("books", "is_null"), value=False))
        names = ["hidden-only", "empty"]
    payload = _post(schema, _document(schema, "name"), where, transport="async")
    assert payload == _expected(row_type, [(genres[name], name) for name in names])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "case",
    [
        "key",
        "column",
        "column-or",
        "key-and-column",
    ],
)
def test_async_only_undeclared_target_hook_scopes_keys_and_columns_independently(
    case: str,
) -> None:
    """Await the undeclared Shelf hook; visible key-only and column-only controls stay distinct."""

    class BranchKeys(FilterSet):
        class Meta:
            model = models.Branch
            fields = {"alt_shelves": ["exact"], "alt_shelves__code": ["exact"]}

    target = _type(
        "AsyncAlternateShelf",
        models.Shelf,
        ("code",),
        hides={"topic": "secret"},
        async_hook=True,
    )
    row_type = _type(
        "AlternateBranchRoot",
        models.Branch,
        ("id", "name"),
        filterset=BranchKeys,
        node=True,
    )
    home = models.Branch.objects.create(name="home")
    alpha = models.Branch.objects.create(name="alpha")
    beta = models.Branch.objects.create(name="beta")
    gamma = models.Branch.objects.create(name="gamma")
    delta = models.Branch.objects.create(name="delta")
    models.Branch.objects.create(name="empty")
    open_shelf = models.Shelf.objects.create(branch=home, code="match", topic="open")
    away = models.Branch.objects.create(name="away")
    column_home = models.Branch.objects.create(name="column-home")
    secret = models.Shelf.objects.create(branch=away, code="match", topic="secret")
    key_only = models.Shelf.objects.create(branch=home, code="other", topic="open")
    column_only = models.Shelf.objects.create(branch=column_home, code="match", topic="open")
    for shelf, branch in [
        (open_shelf, alpha),
        (secret, beta),
        (key_only, gamma),
        (column_only, delta),
    ]:
        shelf.alt_branches.add(branch)
    schema = _schema(row_type, models.Branch, (target,))
    keys = [saved_pk(open_shelf), saved_pk(secret), saved_pk(key_only)]
    where = _where(schema, ("alt_shelves", "exact"), keys)
    names: list[tuple[models.Branch, str]]
    if case == "key":
        names = [(alpha, "alpha"), (gamma, "gamma")]
    elif case in {"column", "column-or"}:
        where = _where(schema, ("alt_shelves_code", "exact"), "match")
        if case == "column-or":
            where = _arm(schema, "or_", [where])
        names = [(alpha, "alpha"), (delta, "delta")]
    else:
        where.update(_where(schema, ("alt_shelves_code", "exact"), "match"))
        names = [(alpha, "alpha")]
    payload = _post(schema, _document(schema, "name"), where, transport="async")
    assert payload == _expected(row_type, names)


class _ShelfWorld(NamedTuple):
    """Rows and native type targets shared by the distinct declared branch shapes."""

    rows: dict[str, models.Book]
    shelves: dict[str, models.Shelf]
    branches: dict[str, models.Branch]
    branch_filter: type[FilterSet]
    shelf_filter: type[FilterSet]
    targets: tuple[type[DjangoType], ...]


def _shelf_world(*, async_shelf: bool = False) -> _ShelfWorld:
    class BranchChild(FilterSet):
        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    class ShelfChild(FilterSet):
        branch = RelatedFilter(BranchChild)

        class Meta:
            model = models.Shelf
            fields = {"topic": ["exact"]}

    branch_type = _type(
        "BoundaryBranch",
        models.Branch,
        ("name",),
        filterset=BranchChild,
        hides={"city": "restricted"},
    )
    shelf_type = _type(
        "BoundaryShelf",
        models.Shelf,
        ("code", "topic"),
        filterset=ShelfChild,
        hides={"topic": "secret"},
        async_hook=async_shelf,
    )
    open_branch = models.Branch.objects.create(name="open", city="here")
    restricted = models.Branch.objects.create(name="restricted", city="restricted")
    shelves = {
        "open": models.Shelf.objects.create(branch=open_branch, code="o", topic="t"),
        "secret": models.Shelf.objects.create(branch=open_branch, code="s", topic="secret"),
        "restricted": models.Shelf.objects.create(branch=restricted, code="r", topic="t"),
        "no_topic": models.Shelf.objects.create(branch=open_branch, code="n", topic=""),
    }
    rows = {
        "open": models.Book.objects.create(shelf=shelves["open"], title="open"),
        "on_secret": models.Book.objects.create(shelf=shelves["secret"], title="on_secret"),
        "on_restricted": models.Book.objects.create(
            shelf=shelves["restricted"],
            title="on_restricted",
        ),
        "no_topic": models.Book.objects.create(shelf=shelves["no_topic"], title="no_topic"),
    }
    return _ShelfWorld(
        rows,
        shelves,
        {"open": open_branch, "restricted": restricted},
        BranchChild,
        ShelfChild,
        (branch_type, shelf_type),
    )


def _multirelation_schema(world: _ShelfWorld) -> tuple[DjangoSchema, type[DjangoType]]:
    class BookParent(FilterSet):
        branch = RelatedFilter(world.branch_filter, field_name="shelf__branch")

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    root = _type(
        "MultirelationBook",
        models.Book,
        ("id", "title"),
        filterset=BookParent,
        node=True,
    )
    return _schema(root, models.Book, world.targets), root


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    "spelling",
    [
        "flat",
        "nested",
        "flat-or",
        "nested-or",
    ],
)
def test_one_declared_multirelation_branch_respects_its_intermediate_scope(
    spelling: str,
    transport: str,
) -> None:
    """A single shelf__branch declaration cannot reach the shared open Branch through a secret Shelf."""
    world = _shelf_world(async_shelf=transport == "async")
    schema, root = _multirelation_schema(world)
    path = (
        ("branch", "name", "exact") if spelling.startswith("nested") else ("branch_name", "exact")
    )
    where = _where(schema, path, "open")
    if spelling.endswith("-or"):
        where = _arm(schema, "or_", [where])
    payload = _post(schema, _document(schema, "title"), where, transport=transport)
    assert payload == _expected(root, [(world.rows[key], key) for key in ["open", "no_topic"]])


@pytest.mark.django_db
@pytest.mark.parametrize("target", ["restricted", "missing"])
def test_multirelation_branch_cannot_match_a_hidden_or_missing_terminal(target: str) -> None:
    """Visible intermediate shelves do not make a restricted Branch visible, and absent names stay empty."""
    world = _shelf_world()
    schema, root = _multirelation_schema(world)
    payload = _post(
        schema,
        _document(schema, "title"),
        _where(schema, ("branch_name", "exact"), target),
    )
    assert payload == _expected(root, [])


_TWO_HOP_CASES = [
    "open-shelf-key",
    "hidden-shelf-key",
    "open-branch-key",
    "hidden-branch-key",
    "exclude-open-branch",
    "branch-null",
    "branch-nonnull",
    "branch-name-null",
    "exclude-topic",
    "positive-topic",
    "not-topic",
]


@pytest.mark.django_db
@pytest.mark.parametrize("case", _TWO_HOP_CASES)
def test_two_declared_forward_hops_treat_each_hidden_link_as_absent(case: str) -> None:
    """Forward keys, null extension and negation read exactly the visibility of the hops they cross."""
    world = _shelf_world()

    class BookParent(FilterSet):
        shelf = RelatedFilter(world.shelf_filter)
        shelf_is = ModelChoiceFilter(field_name="shelf", queryset=models.Shelf.objects.all())
        # The public input types relation keys through ModelChoiceFilter.
        # Generic NumberFilter(ForeignKey) remains a raw-form compatibility case.
        branch_is = ModelChoiceFilter(
            field_name="shelf__branch",
            queryset=models.Branch.objects.all(),
        )
        not_branch = ModelChoiceFilter(
            field_name="shelf__branch",
            queryset=models.Branch.objects.all(),
            exclude=True,
        )
        branch_missing = BooleanFilter(field_name="shelf__branch", lookup_expr="isnull")
        name_missing = BooleanFilter(field_name="shelf__branch__name", lookup_expr="isnull")
        not_topic = CharFilter(field_name="shelf__topic", exclude=True)

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    root = _type("TwoHopBook", models.Book, ("id", "title"), filterset=BookParent, node=True)
    schema = _schema(root, models.Book, world.targets)
    if case in {"open-shelf-key", "hidden-shelf-key"}:
        name = "open" if case == "open-shelf-key" else "secret"
        where = _where(schema, ("shelf_is", "exact"), saved_pk(world.shelves[name]))
        expected = ["open"] if name == "open" else []
    elif case in {"open-branch-key", "hidden-branch-key", "exclude-open-branch"}:
        name = "restricted" if case == "hidden-branch-key" else "open"
        leaf = "not_branch" if case == "exclude-open-branch" else "branch_is"
        where = _where(schema, (leaf, "exact"), saved_pk(world.branches[name]))
        expected = {
            "open-branch-key": ["open", "no_topic"],
            "hidden-branch-key": [],
            "exclude-open-branch": ["on_secret", "on_restricted"],
        }[case]
    elif case in {"branch-null", "branch-nonnull", "branch-name-null"}:
        leaf = "name_missing" if case == "branch-name-null" else "branch_missing"
        null = case != "branch-nonnull"
        where = _where(schema, (leaf, "is_null"), null)
        expected = ["on_secret", "on_restricted"] if null else ["open", "no_topic"]
    else:
        leaf = "not_topic" if case == "exclude-topic" else "shelf_topic"
        where = _where(schema, (leaf, "exact"), "t")
        if case == "not-topic":
            where = _arm(schema, "not_", where)
        expected = (
            ["open", "on_restricted"] if case == "positive-topic" else ["on_secret", "no_topic"]
        )
    payload = _post(schema, _document(schema, "title"), where)
    assert payload == _expected(root, [(world.rows[key], key) for key in expected])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("lookup", "value"),
    [
        ("year", 2020),
        ("month", 6),
        ("year", 1999),
        ("month", 12),
    ],
    ids=[
        "year-matching",
        "month-matching",
        "year-missing",
        "month-missing",
    ],
)
def test_relation_before_date_transform_still_reads_the_target_scope(
    lookup: str,
    value: int,
) -> None:
    """A matching closed Venue cannot satisfy year/month; a visible different date also stays excluded."""

    class TicketPaths(FilterSet):
        opened_year = NumberFilter(field_name="venue__opened_on__year")
        opened_month = NumberFilter(field_name="venue__opened_on__month")

        class Meta:
            model = models.RepairTicket
            fields = []

    target = _type("TransformVenue", models.Venue, ("name",), hides={"name__startswith": "Closed"})
    row_type = _type(
        "TransformTicket",
        models.RepairTicket,
        ("id", "code"),
        filterset=TicketPaths,
        node=True,
    )
    open_venue = models.Venue.objects.create(name="Open", opened_on=datetime.date(2020, 6, 1))
    hidden_venue = models.Venue.objects.create(name="Closed", opened_on=datetime.date(2020, 6, 1))
    other_venue = models.Venue.objects.create(name="Other", opened_on=datetime.date(2021, 7, 1))
    first = models.RepairTicket.objects.create(code="open", venue=open_venue)
    models.RepairTicket.objects.create(code="hidden", venue=hidden_venue)
    models.RepairTicket.objects.create(code="other", venue=other_venue)
    schema = _schema(row_type, models.RepairTicket, (target,))
    payload = _post(
        schema,
        _document(schema, "code"),
        _where(schema, ("opened_" + lookup, "exact"), value),
    )
    expected = [(first, "open")] if value in {2020, 6} else []
    assert payload == _expected(row_type, expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        "column",
        "column-or",
        "key-secret",
        "key-private",
    ],
)
def test_meta_bound_secondary_reentry_scope_keeps_the_plain_consumers_root_universe(
    case: str,
) -> None:
    """Public FilterInput scopes re-entered Shelves by its Meta owner, preserving plain roots."""

    class SecondaryShelfKeys(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {
                "topic": ["exact"],
                "books__shelf__code": ["exact"],
                "books__shelf": ["exact"],
            }

    primary = _type(
        "PrimaryShelfScope",
        models.Shelf,
        ("code", "topic"),
        hides={"topic": "secret"},
    )
    secondary = _type(
        "SecondaryShelfScope",
        models.Shelf,
        ("code", "topic"),
        filterset=SecondaryShelfKeys,
        hides={"topic": "private"},
        primary=False,
    )
    output = _type(
        "PlainShelfOutput",
        models.Shelf,
        ("id", "code", "topic"),
        primary=False,
        node=True,
    )
    book_type = _type("ReentryBook", models.Book, ("title",))
    branch = models.Branch.objects.create(name="Reentry")
    secret = models.Shelf.objects.create(branch=branch, code="x", topic="secret")
    private_branch = models.Branch.objects.create(name="Private reentry")
    private = models.Shelf.objects.create(branch=private_branch, code="x", topic="private")
    adjacent = models.Shelf.objects.create(branch=branch, code="adjacent", topic="adjacent")
    models.Book.objects.create(shelf=secret, title="secret")
    models.Book.objects.create(shelf=private, title="private")

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: FilterInput[SecondaryShelfKeys] | None = None,
        ) -> django_models.QuerySet[models.Shelf]:
            # This consumer deliberately owns root visibility. Meta binds the set
            # to SecondaryShelfScope; its hook is read only by re-entered relations.
            queryset = models.Shelf.objects.order_by("pk")
            return (
                queryset if where is None else SecondaryShelfKeys.apply_sync(where, queryset, info)
            )

        rows: django_models.QuerySet[models.Shelf] = strawberry.field(
            resolver=_rows,
            graphql_type=list[output],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        types=(
            primary,
            secondary,
            output,
            book_type,
        ),
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    document = (
        f"query($where: {_input(schema, argument='where').name}!) {{ "
        "rows(where: $where) { id code topic } }"
    )

    def expected(rows: Sequence[models.Shelf]) -> JSONObject:
        return {
            "data": {
                "rows": [
                    {
                        "id": global_id_for(output, saved_pk(row)),
                        "code": row.code,
                        "topic": row.topic,
                    }
                    for row in rows
                ],
            },
        }

    # The private root really remains available: filtering through the secondary
    # type must not accidentally turn this plain consumer into a scoped root.
    assert _post(schema, document, {}) == expected([secret, private, adjacent])
    if case in {"column", "column-or"}:
        column = _where(schema, ("books_shelf_code", "exact"), "x", argument="where")
        if case == "column-or":
            sibling = _where(schema, ("topic", "exact"), "adjacent", argument="where")
            where = _arm(schema, "or_", [column, sibling], argument="where")
            kept = [secret, adjacent]
        else:
            where = column
            kept = [secret]
    else:
        target = secret if case == "key-secret" else private
        where = _where(schema, ("books_shelf", "exact"), saved_pk(target), argument="where")
        kept = [secret] if case == "key-secret" else []
    assert _post(schema, document, where) == expected(kept)


@pytest.mark.django_db(transaction=True)
def test_nested_or_prederives_its_async_only_terminal_target_for_the_unbound_consumer() -> None:
    """The nested branch uses its prederived terminal rows; a separate flat-hop cache cannot supply them."""
    alpha = models.Branch.objects.create(name="alpha")
    models.Shelf.objects.create(branch=alpha, code="match", topic="open")
    beta = models.Branch.objects.create(name="beta")
    models.Shelf.objects.create(branch=beta, code="other", topic="open")
    hidden = models.Branch.objects.create(name="hidden")
    models.Shelf.objects.create(branch=hidden, code="match", topic="secret")
    models.Branch.objects.create(name="empty")

    class ShelfChild(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class BranchParent(FilterSet):
        shelves = RelatedFilter(ShelfChild, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    target = _type(
        "NestedAsyncTerminalShelf",
        models.Shelf,
        ("code",),
        hides={"topic": "secret"},
        async_hook=True,
    )
    output = _type("UnboundNestedBranchOutput", models.Branch, ("name",))

    async def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> list[models.Branch]:
        del root
        rows = await BranchParent.apply_async(where, models.Branch.objects.order_by("name"), info)
        return [row async for row in rows]

    async def resolve_all(root: object) -> list[models.Branch]:
        del root
        return [row async for row in models.Branch.objects.order_by("name")]

    @strawberry.type
    class Query:
        rows: list[models.Branch] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[output],
        )
        all_rows: list[models.Branch] = strawberry.field(
            resolver=resolve_all,
            graphql_type=list[output],
        )

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        types=[target],
        config=strawberry_config(),
        extensions=[lambda: extension],
    )
    payload = _post(
        schema,
        "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
        {"or_": [{"shelves": {"code": "match"}}]},
        transport="async",
    )
    assert payload == {
        "data": {
            "rows": [{"name": "alpha"}],
            "allRows": [
                {"name": name}
                for name in (
                    "alpha",
                    "beta",
                    "empty",
                    "hidden",
                )
            ],
        },
    }, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("case", "transport"),
    [("key-or", "sync"), ("key-or", "async"), ("exclude-and-title", "async")],
    ids=["key-null-or-sync", "key-null-or-async", "exclude-and-title-async"],
)
def test_visible_relation_keys_and_exclusions_keep_their_logical_arm_verdicts(
    case: str,
    transport: str,
) -> None:
    """A key-null OR differs from nullable-terminal OR, and an excluding AND keeps only its witness."""
    branch = models.Branch.objects.create(name="key null OR")
    shelf = models.Shelf.objects.create(branch=branch, code="key null OR")
    visible_x = models.Book.objects.create(shelf=shelf, title="x")
    visible_y = models.Book.objects.create(shelf=shelf, title="y", subtitle="s")
    hidden_x_shelf = models.Shelf.objects.create(branch=branch, code="hidden x")
    hidden_y_shelf = models.Shelf.objects.create(branch=branch, code="hidden y")
    hidden_x = models.Book.objects.create(
        shelf=hidden_x_shelf,
        title="x",
        subtitle="s",
        circulation_status="repair",
    )
    hidden_y = models.Book.objects.create(
        shelf=hidden_y_shelf,
        title="y",
        circulation_status="repair",
    )
    models.Book.objects.create(shelf=shelf, title="unlinked", subtitle="s")
    for name, books in (
        ("mixed", [visible_x, hidden_x]),
        ("hidden_only", [hidden_y]),
        ("empty", []),
        ("other", [visible_y]),
        ("plain", [visible_x, visible_y]),
    ):
        genre = models.Genre.objects.create(name=name)
        genre.books.set(books)

    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"], "subtitle": ["exact", "isnull"]}

    class GenreParent(FilterSet):
        visible_books = RelatedFilter(BookChild, field_name="books")
        without_title = CharFilter(field_name="books__title", exclude=True)

        class Meta:
            model = models.Genre
            fields = {
                "name": ["exact"],
                "books": ["exact", "isnull"],
                "books__title": ["exact"],
                "books__subtitle": ["isnull"],
            }

    target = _type(
        "KeyNullOrBook",
        models.Book,
        ("title",),
        hides={"circulation_status": "repair"},
    )
    output = _type("KeyNullOrGenre", models.Genre, ("name",))

    def resolve_sync(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> django_models.QuerySet[models.Genre]:
        del root
        return GenreParent.apply_sync(where, models.Genre.objects.order_by("name"), info)

    async def resolve_async(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> list[models.Genre]:
        del root
        rows = await GenreParent.apply_async(where, models.Genre.objects.order_by("name"), info)
        return [row async for row in rows]

    def all_sync(root: object) -> django_models.QuerySet[models.Genre]:
        del root
        return models.Genre.objects.order_by("name")

    async def all_async(root: object) -> list[models.Genre]:
        del root
        return [row async for row in models.Genre.objects.order_by("name")]

    @strawberry.type
    class Query:
        rows: django_models.QuerySet[models.Genre] | Awaitable[list[models.Genre]] = (
            strawberry.field(
                resolver=resolve_async if transport == "async" else resolve_sync,
                graphql_type=list[output],
            )
        )
        all_rows: django_models.QuerySet[models.Genre] | Awaitable[list[models.Genre]] = (
            strawberry.field(
                resolver=all_async if transport == "async" else all_sync,
                graphql_type=list[output],
            )
        )

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        types=[target],
        config=strawberry_config(),
        extensions=[lambda: extension],
    )
    payload = _post(
        schema,
        "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
        (
            {"or_": [{"books": {"is_null": True}}, {"name": "other"}]}
            if case == "key-or"
            else {"and_": [{"without_title": "x"}, {"books__title": "y"}]}
        ),
        transport=transport,
    )
    assert payload == {
        "data": {
            "rows": [
                {"name": name}
                for name in (("empty", "hidden_only", "other") if case == "key-or" else ("other",))
            ],
            "allRows": [
                {"name": name}
                for name in (
                    "empty",
                    "hidden_only",
                    "mixed",
                    "other",
                    "plain",
                )
            ],
        },
    }, payload
