"""Live pins: the execution deadline stops nested relation resolvers.

Contract: ``ResourcePolicy.execution_deadline_seconds`` - every seam about to
hand work to the database calls ``check_deadline`` first. The root connection,
root raw list, ``node`` / ``nodes``, and write-pipeline seams are pinned in
``test_resource_policy_api.py``; the rows here pin the nested relation seams
reached through hand-written roots (the documented ``all_library_books`` shape,
where the optimizer does not cover the root so nested resolvers lazy-load per row):

- nested forward FK / OneToOne (sync): rejects before its lazy load,
- nested reverse OneToOne (sync): rejects before its lazy load,
- nested forward FK (async): rejects (both async closure arms),
- nested forward and reverse OneToOne already loaded by ``select_related``
  (async): rejects at the resolver head, where no lazy-load coroutine exists,
- unarmed control: the same roots serve nested rows cleanly,
- a generated mutation whose budget ends after its write (sync and async): a
  payload with no relation hop commits, while a forward FK or many-side payload
  hop rejects and the write rolls back; the same selection on an unspent mount
  commits whole.

A hand-written root runs no deadline check itself (hand resolvers never call
``check_deadline``), so with a 1us policy the armed budget is already past when
the nested resolver runs - deterministically, with no timing margin. Each
sync lazy-load rejection asserts exactly one captured query (the root read),
proving the nested check runs ahead of the database. The mutation rows run the
fakeshop schema under a generous budget and end it with an extension that
stashes a past instant once the write's resolver has returned, the one write a
resolver may make to the budget.

The hand schema is built per view call with function-local type imports: the
acceptance-suite reload discipline rebuilds the app schema modules per module,
so only function-local references observe the current type classes.
"""

import importlib
import inspect
import time
from collections.abc import Awaitable, Callable

import pytest
import strawberry
from apps.library import models as library_models
from apps.library.schema import VenueType
from apps.products.models import Item
from apps.products.schema import ItemType
from apps.products.services import seed_data
from asgiref.sync import sync_to_async
from config import schema as config_schema
from django.db import connection
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphql import GraphQLResolveInfo
from graphql_client import (
    JSONObject,
    json_list,
    json_object,
    post_graphql,
    response_json,
)
from strawberry.extensions import SchemaExtension
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    strawberry_config,
)
from django_strawberry_framework.resource_policy import DST_RESOURCE_DEADLINE
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils.context import stash_on_context
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

importlib.import_module("config.schema")  # finalizes DjangoTypes for the hand roots

pytestmark = pytest.mark.urls(__name__)

_DEADLINE_SECONDS = 0.000_001


def _hand_schema(deadline: float | None) -> DjangoSchema:

    @strawberry.type
    class DeadlineHandQuery:
        def _hand_items(self, info: strawberry.Info) -> list[Item]:
            return list(ItemType.get_queryset(Item.objects.order_by("id"), info)[:3])

        hand_items: list[Item] = strawberry.field(
            resolver=_hand_items,
            graphql_type=list[ItemType],
        )

        def _hand_venues(self, info: strawberry.Info) -> list[library_models.Venue]:
            return list(
                VenueType.get_queryset(
                    library_models.Venue.objects.order_by("id"),
                    info,
                )[:3],
            )

        hand_venues: list[library_models.Venue] = strawberry.field(
            resolver=_hand_venues,
            graphql_type=list[VenueType],
        )

        async def _hand_items_async(self, info: strawberry.Info) -> list[Item]:
            return await sync_to_async(
                lambda: list(ItemType.get_queryset(Item.objects.order_by("id"), info)[:3]),
            )()

        hand_items_async: list[Item] = strawberry.field(
            resolver=_hand_items_async,
            graphql_type=list[ItemType],
        )

    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=DeadlineHandQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
        resource_policy={"execution_deadline_seconds": deadline},
    )


@csrf_exempt
def _hand_view(request: HttpRequest) -> HttpResponseBase:
    return DjangoGraphQLView.as_view(schema=_hand_schema(None))(request)


@csrf_exempt
def _hand_deadline_view(request: HttpRequest) -> HttpResponseBase:
    return DjangoGraphQLView.as_view(schema=_hand_schema(_DEADLINE_SECONDS))(request)


@csrf_exempt
async def _hand_deadline_async_view(request: HttpRequest) -> HttpResponseBase:
    return await AsyncDjangoGraphQLView.as_view(schema=_hand_schema(_DEADLINE_SECONDS))(
        request,
    )


class _ExpireAfterWrite(SchemaExtension):
    """Spend the budget the moment the generated write's resolver returns.

    The write pipeline's own check has passed and the row is written; the
    deadline then ends before the payload is completed, with no sleep and no
    timing margin. An EARLIER instant under ``DST_RESOURCE_DEADLINE`` is the one
    write a resolver may make to the budget (spec-047 Decision 2).
    """

    @override
    def resolve(
        self,
        _next: Callable[..., object],
        root: object,
        info: GraphQLResolveInfo,
        *args: object,
        **kwargs: object,
    ) -> object:
        """Narrow the deadline to a past instant once the write field has resolved."""
        result = _next(root, info, *args, **kwargs)
        if info.field_name != "createBookViaCustomInput":
            return result
        context = object_result(getattr, info, "context")
        if inspect.isawaitable(result):

            async def _after(pending: Awaitable[object]) -> object:
                value = await pending
                stash_on_context(context, DST_RESOURCE_DEADLINE, time.monotonic() - 1.0)
                return value

            return _after(result)
        stash_on_context(context, DST_RESOURCE_DEADLINE, time.monotonic() - 1.0)
        return result


def _write_schema(extensions: list[type[SchemaExtension]]) -> DjangoSchema:
    """The fakeshop schema under a generous budget, with ``extensions`` spending it."""
    return DjangoSchema(
        query=config_schema.Query,
        mutation=config_schema.Mutation,
        config=strawberry_config(),
        extensions=extensions,
        resource_policy={"execution_deadline_seconds": 60},
    )


@csrf_exempt
def _write_unspent_view(request: HttpRequest) -> HttpResponseBase:
    return DjangoGraphQLView.as_view(schema=_write_schema([]))(request)


@csrf_exempt
def _write_spent_view(request: HttpRequest) -> HttpResponseBase:
    return DjangoGraphQLView.as_view(schema=_write_schema([_ExpireAfterWrite]))(request)


@csrf_exempt
async def _write_spent_async_view(request: HttpRequest) -> HttpResponseBase:
    return await AsyncDjangoGraphQLView.as_view(schema=_write_schema([_ExpireAfterWrite]))(request)


def _hand_loaded_schema() -> DjangoSchema:
    """Async roots whose single-valued relations are fetched with the rows, so no hop lazy-loads."""
    library_schema = importlib.import_module("apps.library.schema")
    card_type = object_result(getattr, library_schema, "MembershipCardType")
    venue_type = object_result(getattr, library_schema, "VenueType")

    @strawberry.type
    class LoadedQuery:
        async def _cards(self) -> list[library_models.MembershipCard]:
            return await sync_to_async(list)(
                library_models.MembershipCard.objects.select_related("patron").order_by("id"),
            )

        cards: list[library_models.MembershipCard] = strawberry.field(
            resolver=_cards,
            graphql_type=list[card_type],
        )

        async def _venues(self) -> list[library_models.Venue]:
            return await sync_to_async(list)(
                library_models.Venue.objects.select_related("venuebadge").order_by("id"),
            )

        venues: list[library_models.Venue] = strawberry.field(
            resolver=_venues,
            graphql_type=list[venue_type],
        )

    return DjangoSchema(
        query=LoadedQuery,
        config=strawberry_config(),
        resource_policy={"execution_deadline_seconds": _DEADLINE_SECONDS},
    )


@csrf_exempt
async def _hand_loaded_async_view(request: HttpRequest) -> HttpResponseBase:
    return await AsyncDjangoGraphQLView.as_view(schema=_hand_loaded_schema())(request)


urlpatterns = [
    path("rd-hand/", _hand_view),
    path("rd-hand-deadline/", _hand_deadline_view),
    path("rd-hand-deadline-async/", _hand_deadline_async_view),
    path("rd-write-unspent/", _write_unspent_view),
    path("rd-write-spent/", _write_spent_view),
    path("rd-write-spent-async/", _write_spent_async_view),
    path("rd-hand-loaded-async/", _hand_loaded_async_view),
]


def _deadline_rejection(payload: JSONObject) -> None:
    errors = json_list(payload, "errors")
    assert len(errors) == 1, errors
    extensions = json_object(payload, "errors", 0, "extensions")
    assert extensions["code"] == "RESOURCE_LIMIT_EXCEEDED", extensions
    assert extensions["bound"] == "execution_deadline_seconds", extensions


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_nested_forward_single_before_its_lazy_load() -> None:
    seed_data(1)
    with CaptureQueriesContext(connection) as captured:
        payload = response_json(
            post_graphql("{ handItems { name category { name } } }", url="/rd-hand-deadline/"),
        )
    _deadline_rejection(payload)
    assert len(captured.captured_queries) == 1, [q["sql"] for q in captured.captured_queries]


@pytest.mark.django_db
def test_a_passed_deadline_stops_a_nested_reverse_o2o_before_its_lazy_load() -> None:
    seed_data(1)
    venue = library_models.Venue.objects.create(name="Badge Hall Deadline")
    library_models.VenueBadge.objects.create(code="B-RD", venue=venue)
    with CaptureQueriesContext(connection) as captured:
        payload = response_json(
            post_graphql("{ handVenues { name venuebadge { code } } }", url="/rd-hand-deadline/"),
        )
    _deadline_rejection(payload)
    assert len(captured.captured_queries) == 1, [q["sql"] for q in captured.captured_queries]


@pytest.mark.django_db(transaction=True)
async def test_a_passed_deadline_stops_an_async_nested_forward_single() -> None:
    await sync_to_async(seed_data)(1)

    res = await AsyncTestClient().query(
        "{ handItemsAsync { name category { name } } }",
        assert_no_errors=False,
        url="/rd-hand-deadline-async/",
    )
    assert res.response.status_code == 200
    _deadline_rejection(response_json(res.response))


@pytest.mark.django_db
def test_an_unarmed_deadline_leaves_nested_singles_alone() -> None:
    seed_data(1)
    venue = library_models.Venue.objects.create(name="Badge Hall Control")
    library_models.VenueBadge.objects.create(code="B-CTL", venue=venue)
    payload = response_json(
        post_graphql(
            "{ handItems { name category { name } } handVenues { name venuebadge { code } } }",
            url="/rd-hand/",
        ),
    )
    assert "errors" not in payload, payload
    assert len(json_list(payload, "data", "handItems")) == 3
    assert json_object(payload, "data", "handVenues", 0, "venuebadge") == {"code": "B-CTL"}


_CREATE_BOOK = (
    "mutation($d: BookInput!){ createBookViaCustomInput(data: $d){ "
    "node{ title %s } errors{ field messages } } }"
)


def _book_input() -> JSONObject:
    branch = library_models.Branch.objects.create(name="rd-write", city="Boston")
    shelf = library_models.Shelf.objects.create(code="RD-W", topic="Fiction", branch=branch)
    return {"title": "rd-write-book", "subtitle": "s", "shelfId": shelf.pk}


def _written_books() -> int:
    return library_models.Book.objects.filter(title="rd-write-book").count()


@pytest.mark.parametrize(
    ("selection", "hop"),
    [("", None), ("shelf { code }", "shelf"), ("genres { name }", "genres")],
    ids=["no-hop-commits", "forward-fk-rolls-back", "many-side-rolls-back"],
)
@pytest.mark.django_db
def test_a_deadline_that_ends_after_the_write_fails_the_payload_hop_and_rolls_the_write_back(
    selection: str,
    hop: str | None,
) -> None:
    """A relation hop in a generated mutation's payload checks the budget too.

    The write pipeline's check passes and the row is written; the budget then ends
    before the payload is completed. A payload with no relation hop has nothing
    left to check and commits. A forward FK hop and a many-side hop each reject at
    the hop's own path, past the written node, and the mutation's new error rolls
    the write back. ``rd-write-unspent`` is the
    control: the same selection with nothing spending the budget commits whole.
    """
    variables = {"d": _book_input()}
    unspent = response_json(
        post_graphql(_CREATE_BOOK % selection, variables=variables, url="/rd-write-unspent/"),
    )
    assert "errors" not in unspent, unspent
    assert _written_books() == 1
    library_models.Book.objects.filter(title="rd-write-book").delete()

    payload = response_json(
        post_graphql(_CREATE_BOOK % selection, variables=variables, url="/rd-write-spent/"),
    )
    if hop is None:
        assert "errors" not in payload, payload
        assert json_object(payload, "data", "createBookViaCustomInput", "node") == {
            "title": "rd-write-book",
        }
        assert _written_books() == 1
    else:
        _deadline_rejection(payload)
        assert json_list(payload, "errors", 0, "path") == ["createBookViaCustomInput", "node", hop]
        assert _written_books() == 0


@pytest.mark.django_db(transaction=True)
async def test_a_deadline_that_ends_after_an_async_write_rolls_the_write_back() -> None:
    """The async executor rolls the write back on the same forward FK payload rejection."""
    variables = {"d": await sync_to_async(_book_input)()}
    res = await AsyncTestClient().query(
        _CREATE_BOOK % "shelf { code }",
        variables,
        assert_no_errors=False,
        url="/rd-write-spent-async/",
    )
    payload = response_json(res.response)
    _deadline_rejection(payload)
    assert json_list(payload, "errors", 0, "path") == ["createBookViaCustomInput", "node", "shelf"]
    assert await sync_to_async(_written_books)() == 0


def _seed_loaded_relations() -> None:
    patron = library_models.Patron.objects.create(name="rd-loaded")
    library_models.MembershipCard.objects.create(patron=patron, barcode="rd-loaded-card")
    venue = library_models.Venue.objects.create(name="rd-loaded-hall")
    library_models.VenueBadge.objects.create(code="B-LOADED", venue=venue)


@pytest.mark.parametrize(
    ("query", "path"),
    [
        ("{ cards { barcode patron { name } } }", ["cards", 0, "patron"]),
        ("{ venues { name venuebadge { code } } }", ["venues", 0, "venuebadge"]),
    ],
    ids=["forward-one-to-one", "reverse-one-to-one"],
)
@pytest.mark.django_db(transaction=True)
async def test_a_passed_deadline_stops_a_single_relation_already_loaded_under_async_execution(
    query: str,
    path: list[object],
) -> None:
    """The resolver-head check, not a check in the lazy-load coroutine, stops this hop.

    ``select_related`` loads the relation with the row, so the resolver builds no
    lazy-load coroutine: only the check at the resolver head rejects. The unloaded
    async row above cannot tell the two placements apart.
    """
    await sync_to_async(_seed_loaded_relations)()
    res = await AsyncTestClient().query(
        query,
        assert_no_errors=False,
        url="/rd-hand-loaded-async/",
    )
    payload = response_json(res.response)
    _deadline_rejection(payload)
    assert json_list(payload, "errors", 0, "path") == path
