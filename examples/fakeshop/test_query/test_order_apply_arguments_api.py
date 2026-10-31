"""Unbound consumer ordering uses the queryset model to preserve one row per root.

Ordinary resolver arguments select a public Ordering value and call OrderSet.apply_sync.
The model-less and conflicting-Meta sets remain unbound to the native output type, as in
their programmatic use; no generated input factory or private owner assignment changes
their metadata before the request.
"""

from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, graphql_payload

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


urlpatterns = [path("graphql-order-arguments/", _graphql_view)]


def _schema(metadata: str) -> DjangoSchema:
    class ChildShelfOrder(OrderSet):
        class Meta:
            model = models.Shelf
            fields = ["code"]

    class ModellessBranchOrder(OrderSet):
        shelves = RelatedOrder(ChildShelfOrder, field_name="shelves")

    class ConflictingBranchOrder(OrderSet):
        shelves = RelatedOrder(ChildShelfOrder, field_name="shelves")

        class Meta:
            model = models.Book
            fields = ["title"]

    orders = {
        "model-less": ModellessBranchOrder,
        "conflicting-model": ConflictingBranchOrder,
    }[metadata]

    class BranchOutput(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("name",)

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            *,
            descending: bool = False,
        ) -> QuerySet[models.Branch]:
            return orders.apply_sync(
                [{"shelves": {"code": Ordering.DESC if descending else Ordering.ASC}}],
                models.Branch.objects.order_by("pk"),
                info,
            )

        def _all_rows(self) -> QuerySet[models.Branch]:
            return models.Branch.objects.order_by("pk")

        rows: QuerySet[models.Branch] = strawberry.field(
            resolver=_rows,
            graphql_type=list[BranchOutput],
        )
        all_rows: QuerySet[models.Branch] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[BranchOutput],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})


def _post(schema: DjangoSchema) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                """
                {
                  rows(descending: false) {
                    name
                  }
                  allRows {
                    name
                  }
                }
                """,
                url="/graphql-order-arguments/",
            )
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize("metadata", ["model-less", "conflicting-model"])
def test_an_unbound_order_aggregates_using_the_actual_root_queryset_model(metadata: str) -> None:
    """Each order uses a row-preserving MIN despite absent or conflicting model metadata."""
    alpha = models.Branch.objects.create(name="Alpha", city="X")
    models.Shelf.objects.create(code="z", branch=alpha)
    models.Shelf.objects.create(code="y", branch=alpha)
    beta = models.Branch.objects.create(name="Beta", city="Y")
    models.Shelf.objects.create(code="a", branch=beta)
    models.Shelf.objects.create(code="b", branch=beta)
    schema = _schema(metadata)

    with CaptureQueriesContext(connection) as captured:
        assert _post(schema) == {
            "data": {
                "rows": [{"name": "Beta"}, {"name": "Alpha"}],
                "allRows": [{"name": "Alpha"}, {"name": "Beta"}],
            },
        }

    ordered_statements = [
        row["sql"]
        for row in captured.captured_queries
        if 'FROM "library_branch"' in row["sql"] and "MIN(" in row["sql"].upper()
    ]
    assert len(ordered_statements) == 1, captured.captured_queries
