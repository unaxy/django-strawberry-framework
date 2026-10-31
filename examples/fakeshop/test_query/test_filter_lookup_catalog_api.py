"""Consumer filter overrides retain usable text-pattern lookups in the all-lookup catalog.

Ordinary string arguments feed the original unbound FilterSet's public data/queryset/.qs
interface. A partial datetime string and a JSON text pattern deliberately use that consumer
interface rather than pretending their column-typed generated inputs accept those strings.
"""

import datetime
import uuid
from functools import wraps
from typing import TYPE_CHECKING

import pytest
import strawberry
from apps.scalars import models as scalar_models
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter
from graphql_client import assert_graphql_data

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.views import DjangoGraphQLView

if TYPE_CHECKING:
    from graphql_client import JSONValue

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-filter-lookup-catalog/", _graphql_view)]


def _schema() -> DjangoSchema:
    class OverriddenSpecimenFilter(FilterSet):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"payload": "__all__", "occurred_at": "__all__"}
            filter_overrides = {
                models.JSONField: {"filter_class": CharFilter},
                models.DateTimeField: {"filter_class": CharFilter},
            }

    class MediaFilter(FilterSet):
        class Meta:
            model = scalar_models.MediaSpecimen
            fields = {"attachment": "__all__"}
            filter_overrides = {models.FileField: {"filter_class": CharFilter}}

    class ScalarOutput(DjangoType):
        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = ("label",)

    class MediaOutput(DjangoType):
        class Meta:
            model = scalar_models.MediaSpecimen
            fields = ("label",)

    @strawberry.type
    class Query:
        def _specimens(self, column: str, needle: str) -> QuerySet[scalar_models.ScalarSpecimen]:
            return OverriddenSpecimenFilter(
                data={f"{column}__icontains": needle},
                queryset=scalar_models.ScalarSpecimen.objects.order_by("id"),
            ).qs

        def _media(self, needle: str) -> QuerySet[scalar_models.MediaSpecimen]:
            return MediaFilter(
                data={"attachment__icontains": needle},
                queryset=scalar_models.MediaSpecimen.objects.order_by("id"),
            ).qs

        specimens: QuerySet[scalar_models.ScalarSpecimen] = strawberry.field(
            resolver=_specimens,
            graphql_type=list[ScalarOutput],
        )
        media: QuerySet[scalar_models.MediaSpecimen] = strawberry.field(
            resolver=_media,
            graphql_type=list[MediaOutput],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _assert_data(schema: DjangoSchema, query: str, expected: dict[str, "JSONValue"]) -> None:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            assert_graphql_data(query, expected, url="/graphql-filter-lookup-catalog/")
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize(("column", "needle"), [("occurred_at", "2021-06"), ("payload", "needle")])
def test_an_overridden_non_text_column_keeps_its_all_catalog_pattern_filter(
    column: str,
    needle: str,
) -> None:
    """The consumer's CharFilter narrows real rows for either overridden non-text column."""
    moment = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc)
    later = datetime.datetime(2022, 3, 1, 18, 0, tzinfo=datetime.timezone.utc)
    for label, when, note in [("june", moment, "Needle"), ("march", later, "hay")]:
        scalar_models.ScalarSpecimen.objects.create(
            label=label,
            flag=False,
            score=1.0,
            occurred_on=moment.date(),
            occurred_at=when,
            occurred_time=when.time(),
            payload={"note": note},
            external_id=uuid.uuid4(),
        )
    _assert_data(
        _schema(),
        '{ specimens(column: "' + column + '", needle: "' + needle + '") { label } }',
        {"specimens": [{"label": "june"}]},
    )


@pytest.mark.django_db
def test_an_overridden_file_column_keeps_its_all_catalog_pattern_filter() -> None:
    """The FileField override matches its stored path without returning the nonmatching file."""
    for label, file_path in [
        ("report", "scalar_media/files/report.txt"),
        ("photo", "x/photo.png"),
    ]:
        scalar_models.MediaSpecimen.objects.create(
            label=label,
            attachment=file_path,
            image="scalar_media/images/blank.png",
        )
    _assert_data(
        _schema(),
        '{ media(needle: "REPORT") { label } }',
        {"media": [{"label": "report"}]},
    )
