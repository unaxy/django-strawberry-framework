"""Authored excluded-empty memberships and queryset overrides keep their logical-arm meaning.

Ordinary JSON reaches unbound public FilterSet apply consumers with native Meta output
and real target visibility. The relation-default holder preserves an independent root
universe, including a root with no shelf and one whose only shelf is hidden.
"""

import pytest
from apps.library import models
from django.db.models import QuerySet
from django_filters import CharFilter
from graphql_client import JSONObject
from test_relation_filter_defaults_api import _expected, _holder, _post
from typing_extensions import override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet, ListFilter, RelatedFilter

pytestmark = pytest.mark.usefixtures("private_registry")


def _where(value: JSONObject) -> JSONObject:
    """Give nested empty JSON lists their public argument type at table construction."""
    return value


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("where", "names"),
    [
        pytest.param({"code_out": []}, ["Empty", "Hidden", "North"], id="flat"),
        pytest.param({"not_": {"code_out": []}}, [], id="not"),
        pytest.param(
            _where({"or_": [{"code_out": []}, {"name": {"exact": "North"}}]}),
            ["Empty", "Hidden", "North"],
            id="or",
        ),
        pytest.param(
            _where({"and_": [{"code_out": []}, {"name": {"exact": "North"}}]}),
            ["North"],
            id="and",
        ),
        pytest.param({"codes_out": []}, ["Empty", "Hidden", "North"], id="walked-flat"),
        pytest.param({"not_": {"codes_out": []}}, [], id="walked-not"),
        pytest.param(
            _where({"or_": [{"codes_out": []}, {"name": {"exact": "North"}}]}),
            ["Empty", "Hidden", "North"],
            id="walked-or",
        ),
        pytest.param({"code_out": ["North"]}, ["Empty", "Hidden"], id="nonempty-own-control"),
        pytest.param({"codes_out": ["N-1"]}, ["Empty", "Hidden"], id="nonempty-walked-control"),
    ],
)
def test_an_authored_excluded_empty_membership_is_a_real_match_all_constraint(
    where: JSONObject,
    names: list[str],
) -> None:
    """Declared exclude=True with [] complements as a real constraint on root and visible child paths."""
    north = models.Branch.objects.create(name="North")
    hidden = models.Branch.objects.create(name="Hidden")
    models.Branch.objects.create(name="Empty")
    models.Shelf.objects.create(branch=north, code="N-1", topic="general")
    models.Shelf.objects.create(branch=hidden, code="H-1", topic="secret")

    class ShelfScope(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("code", "topic")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Shelf],
            info: object,
        ) -> QuerySet[models.Shelf]:
            del info
            return queryset.exclude(topic="secret")

    class ShelfChild(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class BranchParent(FilterSet):
        shelves = RelatedFilter(ShelfChild, field_name="shelves")
        code_out = ListFilter(field_name="name", lookup_expr="in", exclude=True)
        codes_out = ListFilter(field_name="shelves__code", lookup_expr="in", exclude=True)

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    payload = _post(_holder(BranchParent, targets=(ShelfScope,)), where)
    assert payload == _expected(names, universe=("Empty", "Hidden", "North")), payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("where", "codes"),
    [
        pytest.param({"worn_only": "y"}, ["W"], id="root"),
        pytest.param({"not_": {"worn_only": "y"}}, ["G"], id="not"),
        pytest.param({"or_": [{"worn_only": "y"}, {"code": {"exact": "G"}}]}, ["G", "W"], id="or"),
        pytest.param({"and_": [{"worn_only": "y"}, {"code": {"exact": "G"}}]}, [], id="and"),
        pytest.param({}, ["G", "W"], id="omitted"),
    ],
)
def test_a_consumers_queryset_override_shapes_each_logical_arm(
    where: JSONObject,
    codes: list[str],
) -> None:
    """The consumer qs property still restricts an arm even though its own filter method is identity."""
    branch = models.Branch.objects.create(name="Queryset override")
    models.Shelf.objects.create(branch=branch, code="G", condition="good")
    models.Shelf.objects.create(branch=branch, code="W", condition="worn")

    class WornOnlyShelfFilter(FilterSet):
        worn_only = CharFilter(method="keep_all")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

        def keep_all(
            self,
            queryset: QuerySet[models.Shelf],
            _name: str,
            _value: object,
        ) -> QuerySet[models.Shelf]:
            return queryset

        @property
        @override
        def qs(self) -> QuerySet[models.Shelf]:
            rows = super().qs
            if self.form.cleaned_data.get("worn_only"):
                rows = rows.filter(condition="worn")
            return rows

    payload = _post(
        _holder(WornOnlyShelfFilter, model=models.Shelf, label="code"),
        where,
        label="code",
    )
    assert payload == _expected(codes, universe=("G", "W")), payload
