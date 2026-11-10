"""A declared order hop is scoped by its target set's bound type only where its rows are the reached rows.

Ordinary resolvers call ``OrderSet.apply_sync`` on sets no type is wired to, so no
finalize audit reads them: a ``RelatedOrder`` whose target set is bound to a type of a
model the relation does not reach is refused when a term crosses it, naming the
declaration, whether the set declares that model or no model at all. A target bound to a
multi-table-inheritance parent or child of the reached model, keyed by the same column,
scopes the hop: a related row its type hides from the anonymous actor orders its parent
as a missing one, and staff sees it.
"""

from functools import wraps

import pytest
import strawberry
from apps.library import models
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import Client, override_settings
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_list, json_str
from strawberry.types import Info
from typing_extensions import override

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.orders import Ordering, OrderSet, RelatedOrder
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-order-target-scope/", _graphql_view)]


def _user_is_staff(info: object) -> bool:
    """Unwrap ``info.context`` -> request -> user and report ``is_staff``."""
    context = getattr(info, "context", None)
    request = getattr(context, "request", None) or context
    user = getattr(request, "user", None)
    return isinstance(user, AbstractUser) and user.is_staff


def _schema() -> DjangoSchema:
    class DeskOrder(OrderSet):
        class Meta:
            model = models.DeskProfile
            fields = ["code"]

    class ModellessDeskOrder(OrderSet):
        class Meta:
            fields = ["code"]

    class ShelfDeskOrder(OrderSet):
        shelf = RelatedOrder(DeskOrder, field_name="shelf")

        class Meta:
            model = models.Book
            fields = ["title"]

    class ShelfModellessOrder(OrderSet):
        shelf = RelatedOrder(ModellessDeskOrder, field_name="shelf")

        class Meta:
            model = models.Book
            fields = ["title"]

    class VenueScopeOrder(OrderSet):
        class Meta:
            model = models.Venue
            fields = ["name"]

    class DeskScopeOrder(OrderSet):
        class Meta:
            model = models.LendingDesk
            fields = ["name"]

    class VenueOrder(OrderSet):
        lendingdesk = RelatedOrder(VenueScopeOrder, field_name="lendingdesk")

        class Meta:
            model = models.Venue
            fields = ["name"]

    class TicketOrder(OrderSet):
        venue = RelatedOrder(DeskScopeOrder, field_name="venue")

        class Meta:
            model = models.RepairTicket
            fields = ["code"]

    class DeskProfileType(DjangoType):
        class Meta:
            model = models.DeskProfile
            fields = ("code",)
            primary = True
            orderset_class = DeskOrder

    class ModellessDeskProfileType(DjangoType):
        class Meta:
            model = models.DeskProfile
            fields = ("code",)
            primary = False
            orderset_class = ModellessDeskOrder

    class HidingVenueType(DjangoType):
        class Meta:
            model = models.Venue
            fields = ("name",)
            primary = False
            orderset_class = VenueScopeOrder

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Venue],
            info: Info,
            **kwargs: object,
        ) -> QuerySet[models.Venue]:
            return queryset if _user_is_staff(info) else queryset.exclude(name="hidden")

    class HidingLendingDeskType(DjangoType):
        class Meta:
            model = models.LendingDesk
            fields = ("name",)
            orderset_class = DeskScopeOrder

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.LendingDesk],
            info: Info,
            **kwargs: object,
        ) -> QuerySet[models.LendingDesk]:
            return queryset if _user_is_staff(info) else queryset.exclude(name="hidden")

    class BookOutput(DjangoType):
        class Meta:
            model = models.Book
            fields = ("title",)

    class VenueOutput(DjangoType):
        class Meta:
            model = models.Venue
            fields = ("name",)
            primary = True

    class TicketOutput(DjangoType):
        class Meta:
            model = models.RepairTicket
            fields = ("code",)

    @strawberry.type
    class Query:
        def _refused_forward(self, info: strawberry.Info[object, object]) -> QuerySet[models.Book]:
            return ShelfDeskOrder.apply_sync(
                [{"shelf": {"code": Ordering.ASC}}],
                models.Book.objects.all(),
                info,
            )

        def _refused_model_less(
            self,
            info: strawberry.Info[object, object],
        ) -> QuerySet[models.Book]:
            return ShelfModellessOrder.apply_sync(
                [{"shelf": {"code": Ordering.ASC}}],
                models.Book.objects.all(),
                info,
            )

        def _venues(self, info: strawberry.Info[object, object]) -> QuerySet[models.Venue]:
            return VenueOrder.apply_sync(
                [{"lendingdesk": {"name": Ordering.ASC_NULLS_LAST}}, {"name": Ordering.ASC}],
                models.Venue.objects.all(),
                info,
            )

        def _tickets(self, info: strawberry.Info[object, object]) -> QuerySet[models.RepairTicket]:
            return TicketOrder.apply_sync(
                [{"venue": {"name": Ordering.ASC_NULLS_LAST}}, {"code": Ordering.ASC}],
                models.RepairTicket.objects.all(),
                info,
            )

        refused_forward: QuerySet[models.Book] = strawberry.field(
            resolver=_refused_forward,
            graphql_type=list[BookOutput],
        )
        refused_model_less: QuerySet[models.Book] = strawberry.field(
            resolver=_refused_model_less,
            graphql_type=list[BookOutput],
        )
        venues: QuerySet[models.Venue] = strawberry.field(
            resolver=_venues,
            graphql_type=list[VenueOutput],
        )
        tickets: QuerySet[models.RepairTicket] = strawberry.field(
            resolver=_tickets,
            graphql_type=list[TicketOutput],
        )

    finalize_django_types()
    return DjangoSchema(
        query=Query,
        types=[
            DeskProfileType,
            ModellessDeskProfileType,
            HidingVenueType,
            HidingLendingDeskType,
        ],
        config=strawberry_config(),
        error_policy={"enabled": False},
    )


def _post(schema: DjangoSchema, query: str, client: Client | None = None) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, client=client, url="/graphql-order-target-scope/")
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "target"),
    [("refusedForward", "DeskOrder"), ("refusedModelLess", "ModellessDeskOrder")],
    ids=["set-declaring-an-unrelated-model", "model-less-set-served-by-an-unrelated-type"],
)
def test_a_direct_order_whose_target_type_is_unrelated_is_refused_naming_the_declaration(
    field: str,
    target: str,
) -> None:
    """``Book.shelf`` ordered through a set bound to a ``DeskProfile`` type is refused.

    The comparison reads the type the target is bound to, so a model-less set served
    by a ``DeskProfile`` type is refused as a set declaring ``DeskProfile`` is.
    """
    create_users(1)
    owner = {"refusedForward": "ShelfDeskOrder", "refusedModelLess": "ShelfModellessOrder"}[field]
    bound = {"refusedForward": "DeskProfileType", "refusedModelLess": "ModellessDeskProfileType"}
    payload = _post(_schema(), f"{{ {field} {{ title }} }}")
    assert payload["data"] is None
    expected = (
        f"OrderSet _schema.<locals>.{owner}: RelatedOrder 'shelf' has field_name 'shelf', which "
        f"reaches Shelf, but its target OrderSet _schema.<locals>.{target} is bound to "
        f"_schema.<locals>.{bound[field]}, whose model is DeskProfile. A RelatedOrder's target "
        "OrderSet must be bound to a type of Shelf, a proxy of it, or a "
        "multi-table-inheritance parent or child of it keyed by the same column."
    )
    assert [json_str(error, "message") for error in json_list(payload, "errors")] == [expected]


def _seed_venues() -> None:
    plain = models.Venue.objects.create(name="aa-plain")
    hidden = models.LendingDesk.objects.create(name="hidden")
    second = models.LendingDesk.objects.create(name="b")
    first = models.LendingDesk.objects.create(name="a")
    for code, venue in (
        ("c1", plain),
        ("c2", hidden),
        ("c3", second),
        ("c4", first),
    ):
        _ = models.RepairTicket.objects.create(code=code, venue=venue)


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "query",
        "field",
        "key",
        "staff",
        "anonymous",
    ),
    [
        (
            "{ venues { name } }",
            "venues",
            "name",
            [
                "a",
                "b",
                "hidden",
                "aa-plain",
            ],
            [
                "a",
                "b",
                "aa-plain",
                "hidden",
            ],
        ),
        (
            "{ tickets { code } }",
            "tickets",
            "code",
            [
                "c4",
                "c3",
                "c2",
                "c1",
            ],
            [
                "c4",
                "c3",
                "c1",
                "c2",
            ],
        ),
    ],
    ids=["parent-set-across-a-reverse-one-to-one", "child-set-across-a-forward-foreign-key"],
)
def test_a_direct_order_through_an_mti_relative_hides_the_rows_its_type_hides(
    query: str,
    field: str,
    key: str,
    staff: list[str],
    anonymous: list[str],
) -> None:
    """A hidden lending desk orders its venue or ticket as a missing one for the anonymous actor.

    ``Venue.lendingdesk`` is scoped by a ``Venue`` type (the parent of the reached
    ``LendingDesk``), ``RepairTicket.venue`` by a ``LendingDesk`` type (a child of the
    reached ``Venue``: a venue that is no lending desk reads as missing for everyone).
    """
    create_users(1)
    _seed_venues()
    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))
    schema = _schema()
    for client, expected in ((staff_client, staff), (Client(), anonymous)):
        assert _post(schema, query, client) == {
            "data": {field: [{key: value} for value in expected]},
        }
