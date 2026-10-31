"""Copied filters bind by the exact keys their real widgets read without naming a prefix sibling.

Ordinary JSON reaches an unbound consumer FilterSet over Periodical and Issue.
The authored range widget asks for double-underscore suffixed keys. A required
probe stays outside the parent's form when only probe_min is named.
"""

from collections.abc import Mapping
from functools import wraps
from typing import TypeVar

import pytest
import strawberry
from apps.library import models
from django import forms
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter
from django_filters import RangeFilter as DjangoRangeFilter
from django_filters.widgets import SuffixedMultiWidget
from graphql_client import JSONObject, graphql_payload
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
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_Model = TypeVar("_Model", bound=Model)


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-copy-keys/", _graphql_view)]


class _DunderRangeWidget(SuffixedMultiWidget):
    """An authored two-box widget whose upstream suffix seam yields name__low and name__high."""

    suffixes: list[str] = ["_low", "_high"]

    def __init__(self, attrs: dict[str, object] | None = None) -> None:
        super().__init__((forms.TextInput, forms.TextInput), attrs)


class _TitlePairField(forms.MultiValueField):
    def __init__(self, *, required: bool = False, label: str | None = None) -> None:
        super().__init__(
            fields=[forms.CharField(required=False), forms.CharField(required=False)],
            widget=forms.MultiWidget([forms.TextInput(), forms.TextInput()]),
            required=required,
            label=label,
            require_all_fields=False,
        )

    @override
    def compress(self, data_list: list[object]) -> tuple[str, ...]:
        return tuple(str(value) for value in data_list if value)


def _schema(mode: str, calls: list[object] | None = None) -> DjangoSchema:
    class TitlePairFilter(CharFilter):
        @property
        @override
        def field(self) -> forms.Field:
            return _TitlePairField()

        @override
        def filter(self, qs: QuerySet[_Model], value: object) -> QuerySet[_Model]:
            if calls is not None:
                calls.append(value)
            return super().filter(qs, value)

    class IssueChild(FilterSet):
        if mode == "probe":
            probe = CharFilter(field_name="title", required=True)
            probe_min = CharFilter(field_name="title")
        elif mode in {"pair", "removed-pair"}:
            pick = TitlePairFilter(field_name="title", lookup_expr="in")
        else:
            span = DjangoRangeFilter(field_name="number", widget=_DunderRangeWidget)

        class Meta:
            model = models.Issue
            fields = {"number": ["exact"]} if mode == "probe" else {"title": ["exact"]}

    class PeriodicalParent(FilterSet):
        issues = RelatedFilter(IssueChild, field_name="issues")

        class Meta:
            model = models.Periodical
            fields = {"name": ["exact"]}

    parent: type[FilterSet] = PeriodicalParent
    if mode == "removed-pair":

        class RemovingParent(PeriodicalParent):
            def __init__(
                self,
                data: Mapping[str, object] | None = None,
                queryset: QuerySet[models.Periodical] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                copied = dict(data or {})
                copied.pop("issues__pick", None)
                super().__init__(copied, queryset, request=request, prefix=prefix)

        parent = RemovingParent

    class IssueOutput(DjangoType):
        class Meta:
            model = models.Issue
            fields = ("number", "title")

    class PeriodicalOutput(DjangoType):
        class Meta:
            model = models.Periodical
            fields = ("name",)

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[models.Periodical]:
        del root
        return parent.apply_sync(where, models.Periodical.objects.order_by("name"), info)

    def resolve_all(root: object) -> QuerySet[models.Periodical]:
        del root
        return models.Periodical.objects.order_by("name")

    @strawberry.type
    class Query:
        rows: QuerySet[models.Periodical] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[PeriodicalOutput],
        )
        all_rows: QuerySet[models.Periodical] = strawberry.field(
            resolver=resolve_all,
            graphql_type=list[PeriodicalOutput],
        )

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=[IssueOutput],
        config=strawberry_config(),
        extensions=[lambda: extension],
    )


def _world() -> None:
    closed = models.Periodical.objects.create(name="Closed Review")
    models.Issue.objects.create(periodical=closed, number=1, title="A", embargoed=False)
    open_ = models.Periodical.objects.create(name="Open Review")
    models.Issue.objects.create(periodical=open_, number=3, title="B", embargoed=False)
    models.Periodical.objects.create(name="Empty Review")


def _post(schema: DjangoSchema, where: JSONObject) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
                variables={"where": where},
                url="/graphql-copy-keys/",
            )
    finally:
        _CURRENT["schema"] = None


def _expected(names: list[str]) -> JSONObject:
    return {
        "data": {
            "rows": [{"name": name} for name in names],
            "allRows": [
                {"name": name} for name in ("Closed Review", "Empty Review", "Open Review")
            ],
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("where", "names"),
    [
        ({}, ["Closed Review", "Empty Review", "Open Review"]),
        ({"issues__span": {"exact": {"start": 2, "end": 3}}}, ["Open Review"]),
        ({"issues__span": {"exact": {"end": 1}}}, ["Closed Review"]),
        ({"issues": {"span": {"exact": {"start": 2}}}}, ["Open Review"]),
    ],
    ids=[
        "unnamed",
        "both-bounds",
        "end-only",
        "nested-start",
    ],
)
def test_copied_range_widget_reads_its_actual_double_underscore_suffixes(
    where: JSONObject,
    names: list[str],
) -> None:
    """Each named bound constrains its parent; an unnamed range keeps even the issue-less parent."""
    _world()
    payload = _post(_schema("range"), where)
    assert payload == _expected(names), payload


@pytest.mark.django_db
def test_naming_probe_min_does_not_bind_the_required_probe_prefix_sibling() -> None:
    """The exact supplied key binds probe_min alone, so the unnamed required probe cannot refuse it."""
    _world()
    payload = _post(_schema("probe"), {"issues__probe_min": {"exact": "B"}})
    assert payload == _expected(["Open Review"]), payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("where", "names", "invocations"),
    [
        ({"issues__pick": ["B", "Missing"]}, ["Open Review"], [("B", "Missing")]),
        ({}, ["Closed Review", "Empty Review", "Open Review"], []),
    ],
    ids=["supplied-pair", "unnamed-pair"],
)
def test_a_copied_non_range_multiwidget_binds_once_only_when_named(
    where: JSONObject,
    names: list[str],
    invocations: list[object],
) -> None:
    """A named two-box membership filter runs once; an unnamed copy never runs at all."""
    _world()
    calls: list[object] = []
    payload = _post(_schema("pair", calls), where)
    assert payload == _expected(names), payload
    assert calls == invocations


@pytest.mark.django_db
def test_a_constructor_removed_copy_never_dispatches_its_filter() -> None:
    """Removing a canonical copied input before binding leaves its consumer filter inactive."""
    _world()
    calls: list[object] = []
    payload = _post(_schema("removed-pair", calls), {"issues__pick": ["B", "Missing"]})
    assert payload == _expected(["Closed Review", "Empty Review", "Open Review"]), payload
    assert calls == []
