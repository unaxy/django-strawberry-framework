"""Live HTTP relation filters and orders read their bound or registered target type.

``utils/querysets.py::relation_target_type`` answers a path re-entering the
table of the set it walks from with the type that set is bound to. Re-entry is
by table (``_meta.concrete_model``): a proxy reads its concrete model's table,
while a multi-table-inheritance parent and child are different tables. The
shipped fakeshop schema binds no set over a proxy type to a path that re-enters
its table (``OpenVenueFilter`` / ``OpenVenueOrder`` declare none), so these rows
build test-local types over the ``apps.library`` models and serve them on a
holder HTTP mount, sync and async.

Consumer order resolvers also preserve unfiltered roots while a publicly Meta-bound
secondary scopes only related values, and await async-only target hooks or refuse
their use from a synchronous resolver with the production diagnostic.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from functools import wraps

import pytest
import strawberry
from apps.library.models import (
    Book,
    Branch,
    BranchNote,
    Genre,
    LendingDesk,
    ProxyBranch,
    RepairTicket,
    Shelf,
    Venue,
    VisibleBranch,
)
from asgiref.sync import sync_to_async
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import (
    JSONObject,
    assert_graphql_success,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    response_json,
)
from strawberry import relay

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.connection import DjangoConnectionField, _connection_type_for
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.orders import Ordering, OrderSet, RelatedOrder
from django_strawberry_framework.schema import DjangoSchema
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import is_object_dict, is_object_list, saved_pk

# Every test declares fresh ``DjangoType`` classes over the library models.
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
    path("graphql-reentry/", _graphql_view),
    path("graphql-reentry-async/", _async_graphql_view),
]


async def _async_data(query: str) -> JSONObject:
    """Drive the async view with the package client, returning the successful data."""
    result = await AsyncTestClient(path="/graphql-reentry-async/").query(query)
    assert result.response.status_code == 200
    return json_object(response_json(result.response), "data")


def _hiding(field: str, value: str) -> classmethod[DjangoType, ..., QuerySet[Model]]:
    """Return a ``get_queryset`` hook hiding the rows whose ``field`` equals ``value``."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset.exclude(**{field: value})

    return classmethod(get_queryset)


def _node(
    name: str,
    model: type[Model],
    *,
    fields: tuple[str, ...] = ("id", "name"),
    filterset: type[FilterSet] | None = None,
    orderset: type[OrderSet] | None = None,
    hides: tuple[str, str] | None = None,
    primary: bool | None = None,
    relay_node: bool = True,
) -> type[DjangoType]:
    """Build a ``DjangoType`` over ``model``, hiding ``hides`` (``(field, value)``) if given."""
    meta: dict[str, object] = {"model": model, "fields": fields, "name": name}
    if relay_node:
        meta["interfaces"] = (relay.Node,)
    if filterset is not None:
        meta["filterset_class"] = filterset
    if orderset is not None:
        meta["orderset_class"] = orderset
    if primary is not None:
        meta["primary"] = primary
    namespace: dict[str, object] = {"Meta": type("Meta", (), meta)}
    if hides is not None:
        namespace["get_queryset"] = _hiding(*hides)
    return type(name, (DjangoType,), namespace)


def _schema(**fields: type[DjangoType]) -> DjangoSchema:
    """Finalize the declared types and expose one connection per ``fields`` entry."""
    finalize_django_types()
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    name: _connection_type_for(node, node.__django_strawberry_definition__)
                    for name, node in fields.items()
                },
                **{name: DjangoConnectionField(node) for name, node in fields.items()},
            },
        ),
    )
    return DjangoSchema(query=query)


def _names(
    schema: DjangoSchema,
    field: str,
    arguments: str,
    mode: str,
) -> list[str]:
    """Post ``field(arguments)`` to the sync or async view and return each node's label.

    A note's label is its ``body``; every other node's is its ``name``.
    """
    label = "body" if field == "notes" else "name"
    query = f"{{ {field}({arguments}) {{ edges {{ node {{ {label} }} }} }} }}"
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            data = (
                asyncio.run(_async_data(query))
                if mode == "async"
                else assert_graphql_success(query, url="/graphql-reentry/")
            )
    finally:
        _CURRENT["schema"] = None
    connection = data[field]
    assert is_object_dict(connection)
    edges = connection["edges"]
    assert is_object_list(edges)
    labels: list[str] = []
    for edge in edges:
        assert is_object_dict(edge)
        node = edge["node"]
        assert is_object_dict(node)
        value = node[label]
        assert isinstance(value, str)
        labels.append(value)
    return labels


def _branch_world() -> None:
    """Branches ``A``/``B``/``X``/``P`` (city = lowercase name), with two shelves alt-listing others.

    A shelf on ``A`` alt-lists ``P``, one on ``B`` ``X``. Each of ``A`` and ``B`` carries a
    ``BranchNote`` named after it.
    """
    rows = {city: Branch.objects.create(name=city.upper(), city=city) for city in "abxp"}
    for owner, alternate in (("a", "p"), ("b", "x")):
        shelf = Shelf.objects.create(branch=rows[owner], code=owner)
        shelf.alt_branches.add(rows[alternate])
        BranchNote.objects.create(branch_id=saved_pk(rows[owner]), body=owner.upper())


def _proxy_root_schema(set_model: type[Branch], *, hooked: bool) -> DjangoSchema:
    """The primary ``Branch`` type hides city ``p``; the ``ProxyBranch`` root hides ``x`` when ``hooked``.

    One filter set and one order set over ``set_model`` are bound to the proxy
    type; ``shelves__alt_branches`` re-enters the ``Branch`` table and reaches
    other rows. ``notes`` filters notes through a ``RelatedFilter`` on
    ``BranchNote.branch`` (declared to ``ProxyBranch``) whose target is that set.
    """
    _node("BranchPrimary", Branch, hides=("city", "p"), primary=True)

    class ReentrantBranchFilter(FilterSet):
        class Meta:
            model = set_model
            fields = {"name": ["exact"], "shelves__alt_branches__city": ["exact"]}

    class ReentrantBranchOrder(OrderSet):
        class Meta:
            model = set_model
            fields = ["name", "shelves__alt_branches__city"]

    class NoteFilter(FilterSet):
        branch = RelatedFilter(ReentrantBranchFilter, field_name="branch")

        class Meta:
            model = BranchNote
            fields = {"body": ["exact"]}

    root = _node(
        "ProxyBranchNode",
        ProxyBranch,
        filterset=ReentrantBranchFilter,
        orderset=ReentrantBranchOrder,
        hides=("city", "x") if hooked else None,
    )
    notes = _node("NoteNode", BranchNote, fields=("id", "body"), filterset=NoteFilter)
    return _schema(branches=root, notes=notes)


# ``(field, arguments, expected)`` per surface: the names the bound proxy type's own
# visibility answers with: the plain proxy hides nothing, the hooked one hides
# ``X``. The primary's hook (hiding ``P``) must never decide a re-entered row.
_PROXY_SURFACES = {
    "flat-hidden-by-bound": (
        "branches",
        'filter: {shelvesAltBranchesCity: {exact: "x"}}',
        {"plain": ["B"], "hooked": []},
    ),
    "flat-hidden-by-primary": (
        "branches",
        'filter: {shelvesAltBranchesCity: {exact: "p"}}',
        {"plain": ["A"], "hooked": ["A"]},
    ),
    "nested-hidden-by-bound": (
        "notes",
        'filter: {branch: {shelvesAltBranchesCity: {exact: "x"}}}',
        {"plain": ["B"], "hooked": []},
    ),
    "nested-hidden-by-primary": (
        "notes",
        'filter: {branch: {shelvesAltBranchesCity: {exact: "p"}}}',
        {"plain": ["A"], "hooked": ["A"]},
    ),
    "order": (
        "branches",
        "orderBy: [{shelvesAltBranchesCity: ASC_NULLS_LAST}, {name: ASC}]",
        {
            "plain": [
                "A",
                "B",
                "P",
                "X",
            ],
            "hooked": ["A", "B", "P"],
        },
    ),
}

_MODES = pytest.mark.parametrize("mode", ["sync", "async"])


@pytest.mark.django_db(transaction=True)
@_MODES
@pytest.mark.parametrize("surface", list(_PROXY_SURFACES))
@pytest.mark.parametrize("hooked", [False, True], ids=["plain-root", "hooked-root"])
@pytest.mark.parametrize(
    "set_model",
    [Branch, ProxyBranch],
    ids=["set-on-concrete", "set-on-proxy"],
)
def test_a_proxy_root_reads_its_own_visibility_on_a_path_re_entering_its_table(
    set_model: type[Branch],
    *,
    hooked: bool,
    surface: str,
    mode: str,
) -> None:
    """A set bound to a ``ProxyBranch`` type reads that type, not ``Branch``'s primary, on re-entry.

    The proxy reads the ``Branch`` table, so ``shelves__alt_branches`` re-enters
    it whichever model the set declares. Reading the primary instead would make a
    row the bound type hides an existence oracle (``x``) and hide a row it shows
    (``p``), in a flat leaf, through a ``RelatedFilter`` on ``BranchNote.branch``,
    and in ``orderBy``.
    """
    _branch_world()
    schema = _proxy_root_schema(set_model, hooked=hooked)
    field, arguments, expected = _PROXY_SURFACES[surface]
    assert _names(schema, field, arguments, mode) == expected["hooked" if hooked else "plain"]


@pytest.mark.django_db(transaction=True)
@_MODES
@pytest.mark.parametrize(
    "root_model",
    [Branch, VisibleBranch],
    ids=["concrete-root", "sibling-proxy-root"],
)
def test_a_relation_declared_to_a_proxy_of_the_roots_table_answers_with_the_root(
    root_model: type[Branch],
    mode: str,
) -> None:
    """``notes__branch`` reaches ``ProxyBranch``, which reads the root's table: the root answers.

    ``BranchNote.branch`` is declared to ``ProxyBranch``, whose registered type
    hides city ``x``. From a root over ``Branch`` (or its sibling proxy
    ``VisibleBranch``), the relation re-enters the root's own table, so the root's
    visibility decides, and the root shows ``X``.
    """
    rows = {city: Branch.objects.create(name=city.upper(), city=city) for city in "ax"}
    for row in rows.values():
        BranchNote.objects.create(branch_id=saved_pk(row), body=row.name)
    _node("ProxyBranchNode", ProxyBranch, hides=("city", "x"))

    class NoteBranchFilter(FilterSet):
        class Meta:
            model = root_model
            fields = {"name": ["exact"], "notes__branch__city": ["exact"]}

    root = _node("RootBranchNode", root_model, filterset=NoteBranchFilter)
    schema = _schema(branches=root)
    arguments = 'filter: {notesBranchCity: {exact: "x"}}'
    assert _names(schema, "branches", arguments, mode) == ["X"]


def _venue_world() -> None:
    """Desk ``D1``'s lead ticket is at desk ``H``; desk ``D2``'s at the plain venue ``Closed``."""
    hidden_desk = LendingDesk.objects.create(name="H")
    closed = Venue.objects.create(name="Closed")
    for desk_name, venue in (("D1", hidden_desk), ("D2", closed)):
        ticket = RepairTicket.objects.create(code=desk_name, venue=venue)
        LendingDesk.objects.create(name=desk_name, lead_ticket=ticket)


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "path",
        "argument",
        "name",
        "expected",
    ),
    [
        (
            "lead_ticket__venue__name",
            "leadTicketVenueName",
            "H",
            ["D1"],
        ),
        (
            "lead_ticket__venue__name",
            "leadTicketVenueName",
            "Closed",
            [],
        ),
        (
            "lead_ticket__venue__lendingdesk__name",
            "leadTicketVenueLendingdeskName",
            "H",
            [],
        ),
    ],
    ids=["parent-rows-shown-by-parent-type", "parent-rows-hidden-by-parent-type", "child-rows"],
)
def test_a_multi_table_child_root_reads_the_parents_type_for_parent_rows(
    path: str,
    argument: str,
    name: str,
    expected: list[str],
) -> None:
    """MTI parent and child are different tables: only a path reaching the child's own answers with the root.

    The set is keyed on ``Venue`` and bound to a ``LendingDesk`` type hiding desk
    ``H``; the primary ``Venue`` type hides ``Closed``. ``lead_ticket__venue``
    reaches ``Venue`` rows, a superset of desks the child type cannot scope, so
    the parent's type decides; ``...__lendingdesk`` reaches the root's own table.
    """
    _venue_world()
    _node("VenuePrimary", Venue, hides=("name", "Closed"), primary=True)

    class LeadVenueFilter(FilterSet):
        class Meta:
            model = Venue
            fields = {"name": ["exact"], path: ["exact"]}

    root = _node(
        "DeskNode",
        LendingDesk,
        fields=("name",),
        filterset=LeadVenueFilter,
        hides=("name", "H"),
    )
    schema = _schema(desks=root)
    arguments = f'filter: {{{argument}: {{exact: "{name}"}}}}'
    assert _names(schema, "desks", arguments, "sync") == expected


def _shared_set_schema(family: str, *, proxy_first: bool) -> DjangoSchema:
    """One ``family`` set over ``Branch`` shared by a plain ``Branch`` owner and a plain proxy owner.

    The primary ``Branch`` type hides city ``p``; neither owner hides anything.
    A shared filter set's owners keep the plain (non-Relay) identity its own-key
    axis requires, so the set is reached as the ``RelatedFilter`` target of
    ``notes``; a shared order set is reached through each owner's connection.
    """
    _node("BranchPrimary", Branch, hides=("city", "p"), primary=True)

    class SharedBranchFilter(FilterSet):
        class Meta:
            model = Branch
            fields = {"name": ["exact"], "shelves__alt_branches__city": ["exact"]}

    class SharedBranchOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["name", "shelves__alt_branches__city"]

    class NoteFilter(FilterSet):
        branch = RelatedFilter(SharedBranchFilter, field_name="branch")

        class Meta:
            model = BranchNote
            fields = {"body": ["exact"]}

    filtering = family == "filter"
    declare: dict[str, Callable[[], type[DjangoType]]] = {
        "proxy": lambda: _node(
            "ProxyOwner",
            ProxyBranch,
            filterset=SharedBranchFilter if filtering else None,
            orderset=None if filtering else SharedBranchOrder,
            relay_node=not filtering,
        ),
        "concrete": lambda: _node(
            "BranchOwner",
            Branch,
            filterset=SharedBranchFilter if filtering else None,
            orderset=None if filtering else SharedBranchOrder,
            primary=False,
            relay_node=not filtering,
        ),
    }
    order = ("proxy", "concrete") if proxy_first else ("concrete", "proxy")
    owners = {role: declare[role]() for role in order}
    if filtering:
        return _schema(
            notes=_node("NoteNode", BranchNote, fields=("id", "body"), filterset=NoteFilter),
        )
    return _schema(proxied=owners["proxy"], plain=owners["concrete"])


@pytest.mark.django_db
@pytest.mark.parametrize("proxy_first", [True, False], ids=["proxy-first", "concrete-first"])
@pytest.mark.parametrize(
    (
        "family",
        "field",
        "arguments",
        "expected",
    ),
    [
        (
            "filter",
            "notes",
            'filter: {branch: {shelvesAltBranchesCity: {exact: "p"}}}',
            ["A"],
        ),
        (
            "order",
            "proxied",
            "orderBy: [{shelvesAltBranchesCity: ASC_NULLS_LAST}, {name: ASC}]",
            [
                "A",
                "B",
                "P",
                "X",
            ],
        ),
        (
            "order",
            "plain",
            "orderBy: [{shelvesAltBranchesCity: ASC_NULLS_LAST}, {name: ASC}]",
            [
                "A",
                "B",
                "P",
                "X",
            ],
        ),
    ],
    ids=["filter", "order-through-proxy-owner", "order-through-concrete-owner"],
)
def test_two_plain_owners_on_one_table_share_a_set_in_either_declaration_order(
    *,
    proxy_first: bool,
    family: str,
    field: str,
    arguments: str,
    expected: list[str],
) -> None:
    """A plain ``Branch`` owner and a plain proxy owner both answer re-entry with the bound type.

    Each reads the ``Branch`` table, so whichever owner binds first, a re-entered
    row is read through an identity hook and the primary's hiding of ``p`` never
    applies.
    """
    _branch_world()
    schema = _shared_set_schema(family, proxy_first=proxy_first)
    assert _names(schema, field, arguments, "sync") == expected


def _order_world() -> None:
    branch = Branch.objects.create(name="home")
    secret = Shelf.objects.create(branch=branch, code="S1", topic="secret")
    middle = Shelf.objects.create(branch=branch, code="S2", topic="mmm")
    on_secret = Book.objects.create(title="on-secret", shelf=secret)
    on_middle = Book.objects.create(title="on-mmm", shelf=middle)
    Genre.objects.create(name="g-secret").books.add(on_secret)
    Genre.objects.create(name="g-mmm").books.add(on_middle)


def _ordering_holder(
    model: type[Model],
    label: str,
    orderset: type[OrderSet],
    targets: Sequence[type[DjangoType]],
    term: str,
    *,
    nested: bool = False,
    secondary_output: bool = False,
    mode: str = "sync",
) -> DjangoSchema:
    output = _node(
        "UnscopedOrderingOutput",
        model,
        fields=(label,),
        primary=not secondary_output,
        relay_node=False,
    )

    def terms(*, descending: bool) -> list[dict[str, object]]:
        direction = Ordering.DESC_NULLS_LAST if descending else Ordering.ASC_NULLS_LAST
        return [{term: {"topic": direction} if nested else direction}]

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        *,
        descending: bool,
    ) -> QuerySet[Model]:
        del root
        return orderset.apply_sync(
            terms(descending=descending),
            model._default_manager.all(),
            info,
        )

    async def resolve_async_rows(
        root: object,
        info: strawberry.Info[object, object],
        *,
        descending: bool,
    ) -> list[Model]:
        del root
        rows = await orderset.apply_async(
            terms(descending=descending),
            model._default_manager.all(),
            info,
        )
        return await sync_to_async(list)(rows)

    def resolve_all(root: object) -> QuerySet[Model]:
        del root
        return model._default_manager.order_by("pk")

    async def resolve_async_all(root: object) -> list[Model]:
        del root
        return await sync_to_async(list)(model._default_manager.order_by("pk"))

    @strawberry.type
    class Query:
        rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_rows if mode == "async" else resolve_rows,
            graphql_type=list[output],
        )
        all_rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_all if mode == "async" else resolve_all,
            graphql_type=list[output],
        )

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=targets,
        extensions=[lambda: extension],
        error_policy={"enabled": False},
    )


async def _async_ordering_payload(document: str) -> JSONObject:
    result = await AsyncTestClient(path="/graphql-reentry-async/").query(
        document,
        assert_no_errors=False,
    )
    assert result.response.status_code == 200
    return response_json(result.response)


def _ordering_payload(schema: DjangoSchema, label: str, mode: str) -> JSONObject:
    document = f"{{ rows(descending: true) {{ label: {label} }} allRows {{ label: {label} }} }}"
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if mode == "async":
                return asyncio.run(_async_ordering_payload(document))
            return graphql_payload(document, url="/graphql-reentry/")
    finally:
        _CURRENT["schema"] = None


def _ordered_expected(names: Sequence[str], universe: Sequence[str]) -> JSONObject:
    return {
        "data": {
            "rows": [{"label": name} for name in names],
            "allRows": [{"label": name} for name in universe],
        },
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["async", "sync"], ids=["awaited", "sync-refusal"])
@pytest.mark.parametrize("many", [False, True], ids=["to-one", "to-many"])
def test_consumer_related_order_awaits_an_async_only_target_or_refuses_the_sync_context(
    *,
    many: bool,
    mode: str,
) -> None:
    """The async target changes the order; the same wire request on a sync consumer names the misuse."""
    _order_world()

    async def hide_secret(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
    ) -> QuerySet[Model]:
        return await sync_to_async(lambda: queryset.exclude(topic="secret"))()

    target = type(
        "AsyncOrderShelf",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": Shelf, "fields": ("code", "topic")}),
            "get_queryset": classmethod(hide_secret),
        },
    )
    model, label, path = (
        (Genre, "name", "books__shelf__topic") if many else (Book, "title", "shelf__topic")
    )
    orderset = type(
        "AsyncRelatedOrder",
        (OrderSet,),
        {"Meta": type("Meta", (), {"model": model, "fields": [label, path]})},
    )
    schema = _ordering_holder(
        model,
        label,
        orderset,
        (target,),
        path.replace("__", "_"),
        mode=mode,
    )
    payload = _ordering_payload(schema, label, mode)
    if mode == "async":
        names = ["g-mmm", "g-secret"] if many else ["on-mmm", "on-secret"]
        assert payload == _ordered_expected(names, list(reversed(names))), payload
    else:
        assert json_at(payload, "data") is None, payload
        errors = json_list(payload, "errors")
        assert len(errors) == 1, payload
        assert json_at(errors[0], "path") == ["rows"], payload
        assert json_at(errors[0], "message") == (
            "AsyncOrderShelf.get_queryset returned a coroutine in a sync resolver context. "
            "A related order term reads its target type's get_queryset; await "
            "OrderSet.apply_async from an async resolver instead, or redefine get_queryset "
            "as a sync method."
        ), payload


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["declared-hop", "reentering"])
def test_public_secondary_order_binding_controls_related_values_without_scoping_the_root(
    shape: str,
) -> None:
    """The bound secondary hides secret related values while every plain consumer root stays available."""
    _order_world()

    class BoundShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"] if shape == "declared-hop" else ["code", "books__shelf__topic"]

    primary = _node(
        "PrimaryOrderShelf",
        Shelf,
        fields=("code", "topic"),
        hides=("topic", "mmm"),
        primary=True,
        relay_node=False,
    )
    secondary = _node(
        "SecondaryOrderShelf",
        Shelf,
        fields=("code", "topic"),
        hides=("topic", "secret"),
        orderset=BoundShelfOrder,
        primary=False,
        relay_node=False,
    )
    if shape == "declared-hop":

        class DeclaredBookOrder(OrderSet):
            shelf = RelatedOrder(BoundShelfOrder, field_name="shelf")

            class Meta:
                model = Book
                fields = ["title"]

        schema = _ordering_holder(
            Book,
            "title",
            DeclaredBookOrder,
            (primary, secondary),
            "shelf",
            nested=True,
        )
        payload = _ordering_payload(schema, "title", "sync")
        expected = _ordered_expected(["on-mmm", "on-secret"], ["on-secret", "on-mmm"])
    else:
        schema = _ordering_holder(
            Shelf,
            "code",
            BoundShelfOrder,
            (primary, secondary),
            "books_shelf_topic",
            secondary_output=True,
        )
        payload = _ordering_payload(schema, "code", "sync")
        expected = _ordered_expected(["S2", "S1"], ["S1", "S2"])
    assert payload == expected, payload
