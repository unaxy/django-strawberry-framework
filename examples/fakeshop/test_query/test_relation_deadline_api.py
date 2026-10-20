"""Live pins: the execution deadline stops nested single-object resolvers.

Contract: ``ResourcePolicy.execution_deadline_seconds`` - every seam about to
hand work to the database calls ``check_deadline`` first. The root connection,
root raw list, ``node`` / ``nodes``, and write-pipeline seams are pinned in
``test_resource_policy_api.py``; the rows here pin the nested relation seams
reached through hand-written roots (the documented ``all_library_books`` shape,
where the optimizer does not cover the root so nested resolvers lazy-load per row):

- nested forward FK / OneToOne (sync): rejects before its lazy load,
- nested reverse OneToOne (sync): rejects before its lazy load,
- nested forward FK (async): rejects (both async closure arms),
- unarmed control: the same roots serve nested rows cleanly.

A hand-written root runs no deadline check itself (hand resolvers never call
``check_deadline``), so with a 1us policy the armed budget is already past when
the nested resolver runs - deterministically, with no timing margin. Each
rejection asserts exactly one captured query (the root read), proving the
nested check runs ahead of the database.

The hand schema is built per view call with function-local type imports: the
acceptance-suite reload discipline rebuilds the app schema modules per module,
so only function-local references observe the current type classes.
"""

import importlib

import pytest
import strawberry
from apps.library import models as library_models
from apps.library.schema import VenueType
from apps.products.models import Item
from apps.products.schema import ItemType
from apps.products.services import seed_data
from asgiref.sync import sync_to_async
from django.db import connection
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphql_client import (
    JSONObject,
    json_list,
    json_object,
    post_graphql,
    response_json,
)

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    strawberry_config,
)
from django_strawberry_framework.testing import AsyncTestClient
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


urlpatterns = [
    path("rd-hand/", _hand_view),
    path("rd-hand-deadline/", _hand_deadline_view),
    path("rd-hand-deadline-async/", _hand_deadline_async_view),
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
