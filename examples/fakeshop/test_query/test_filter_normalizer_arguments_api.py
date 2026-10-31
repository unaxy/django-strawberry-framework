"""Ordinary JSON consumers retain each list normalizer arm's refusals and admitted forms.

The holder reuses the existing native public FilterSet apply root. No generated input
factory is bound to these declarations, so JSON can carry invalid containers while the
actual django-filter classes still clean and execute their admitted list forms.
"""

import django_filters
import pytest
from apps.library import models
from apps.products import models as product_models
from apps.products.services import seed_data
from django.db import models as django_models
from django_filters import (
    AllValuesMultipleFilter,
    BaseInFilter,
    BaseRangeFilter,
    CharFilter,
    NumberFilter,
)
from django_filters.filters import Filter
from graphql_client import JSONObject, json_list, json_object
from strawberry import relay
from test_filter_apply_arguments_api import _post, _refused, _schema

from django_strawberry_framework import DjangoType
from django_strawberry_framework.filters import FilterSet, GlobalIDMultipleChoiceFilter
from django_strawberry_framework.testing.relay import global_id_for
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")


class CharInFilter(BaseInFilter, CharFilter):
    """The original CSV membership class inherits django-filter's real form."""


class IntRange(BaseRangeFilter, NumberFilter):
    """The original CSV range class inherits django-filter's real form."""


def _multiple_choice_in_filter(choices: list[tuple[str, str]]) -> Filter:
    """Use the original dynamic wrapper django-filter builds around a multiple-choice filter."""
    wrapped: type[Filter] = type(
        "MultipleChoiceInFilter",
        (BaseInFilter, django_filters.MultipleChoiceFilter),
        {},
    )
    return wrapped(field_name="code", lookup_expr="in", choices=choices)


def _declaration(kind: str) -> Filter:
    choices = [("1", "1"), ("9", "9")]
    return {
        "csv-in": CharInFilter(field_name="code", lookup_expr="in"),
        "csv-range": IntRange(field_name="code", lookup_expr="range"),
        "typed-multiple": django_filters.TypedMultipleChoiceFilter(
            field_name="code",
            choices=choices,
        ),
        "all-values-multiple": AllValuesMultipleFilter(field_name="code"),
        "in-multiple": _multiple_choice_in_filter(choices),
        "globalid-multiple": GlobalIDMultipleChoiceFilter(field_name="pk", lookup_expr="in"),
    }[kind]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind",
    [
        "csv-in",
        "csv-range",
        "typed-multiple",
        "all-values-multiple",
        "in-multiple",
        "globalid-multiple",
    ],
)
@pytest.mark.parametrize("verdict", ["refused", "admitted"])
def test_each_original_list_normalizer_arm_keeps_its_container_contract(
    kind: str,
    verdict: str,
) -> None:
    """Each real filter rejects its malformed container and preserves its admitted list result."""
    branch = models.Branch.objects.create(name="Normalizer forms")
    first = models.Shelf.objects.create(branch=branch, code="1")
    models.Shelf.objects.create(branch=branch, code="9")
    declared = _declaration(kind)

    class ConsumerFilter(FilterSet):
        probe = declared

        class Meta:
            model = models.Shelf
            fields = []

    ConsumerFilter.get_filters()
    bad: JSONObject | str | int = (
        {"start": 1, "end": 5}
        if kind.startswith("csv-")
        else 42
        if kind == "globalid-multiple"
        else "abc"
    )
    good: object = [1, 5] if kind == "csv-range" else [] if kind == "in-multiple" else ["1"]
    operator = (
        "range"
        if kind == "csv-range"
        else "in_"
        if kind in {"csv-in", "in-multiple", "globalid-multiple"}
        else "exact"
    )
    targets: tuple[type[DjangoType], ...] = ()
    node_type: type[DjangoType] | None = None
    if kind == "globalid-multiple":

        class PrimitiveShelfNode(DjangoType):
            class Meta:
                model = models.Shelf
                fields = ("code",)
                interfaces = (relay.Node,)
                primary = True

        node_type = PrimitiveShelfNode
        targets = (PrimitiveShelfNode,)
    schema = _schema(
        ConsumerFilter,
        models.Shelf,
        transport="sync",
        fields=("code",),
        targets=targets,
    )
    if node_type is not None:
        good = [global_id_for(node_type, saved_pk(first), schema=schema)]
    where: JSONObject = {"probe": {operator: bad if verdict == "refused" else good}}
    payload = _post(
        schema,
        where,
        transport="sync",
        selection="code",
    )
    if verdict == "admitted":
        codes = ["1", "9"] if kind == "in-multiple" else ["1"]
        assert payload == {"data": {"rows": [{"code": code} for code in codes]}}, payload
    else:
        shape = (
            "CSV membership list"
            if kind in {"csv-in", "csv-range", "in-multiple"}
            else "GlobalID list"
            if kind == "globalid-multiple"
            else "multiple-choice list"
        )
        display = (
            "dict {'start': 1, 'end': 5}"
            if kind.startswith("csv-")
            else "int 42"
            if kind == "globalid-multiple"
            else "str 'abc'"
        )
        _refused(
            payload,
            f"{type(declared).__name__} consumes a list of values for its {declared.field_name!r} input, "
            f"but received a non-list container ({display}) for the {shape}; send a list "
            "(generated filter inputs deliver a list after GraphQL coercion).",
        )


@pytest.mark.django_db
@pytest.mark.parametrize("supplied", [False, True], ids=["omitted", "minted-list-control"])
def test_a_required_globalid_list_cleans_omission_as_a_required_field_error(
    *,
    supplied: bool,
) -> None:
    """An absent required list fails before filtering while a minted list selects its row."""
    branch = models.Branch.objects.create(name="Required global identifiers")
    first = models.Shelf.objects.create(branch=branch, code="1")
    models.Shelf.objects.create(branch=branch, code="9")

    class RequiredGlobalIdentifiers(FilterSet):
        probe = GlobalIDMultipleChoiceFilter(field_name="pk", lookup_expr="in", required=True)

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class RequiredShelfNode(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("code",)
            interfaces = (relay.Node,)
            primary = True

    schema = _schema(
        RequiredGlobalIdentifiers,
        models.Shelf,
        transport="sync",
        fields=("code",),
        targets=(RequiredShelfNode,),
    )
    where: JSONObject = {"code": {"exact": "1"}}
    if supplied:
        where["probe"] = {
            "in_": [global_id_for(RequiredShelfNode, saved_pk(first), schema=schema)],
        }
    payload = _post(schema, where, transport="sync", selection="code")
    if supplied:
        assert payload == {"data": {"rows": [{"code": "1"}]}}, payload
    else:
        assert payload["data"] is None, payload
        assert len(json_list(payload, "errors")) == 1, payload
        error = json_object(payload, "errors", 0)
        assert error["path"] == ["rows"], payload
        assert error["extensions"] == {
            "code": "FILTER_INVALID",
            "errors": {"probe": [{"message": "This field is required.", "code": "required"}]},
        }, payload


@pytest.mark.django_db
@pytest.mark.parametrize("verdict", ["admitted", "refused"])
def test_a_model_choice_membership_override_keeps_its_json_container_contract(
    verdict: str,
) -> None:
    """The generated model-choice wrapper cleans saved keys and refuses a scalar before form binding."""
    seed_data(1)
    categories = list(product_models.Category.objects.order_by("pk")[:2])
    assert len(categories) == 2
    category, other = categories

    def category_queryset(_field: object) -> dict[str, object]:
        return {"queryset": product_models.Category.objects.all()}

    class ItemChoiceFilter(FilterSet):
        class Meta:
            model = product_models.Item
            fields = {"category": ["exact", "in"]}
            filter_overrides = {
                django_models.ForeignKey: {
                    "filter_class": django_filters.ModelChoiceFilter,
                    "extra": category_queryset,
                },
            }

    expected = [
        item.name for item in product_models.Item.objects.filter(category=category).order_by("pk")
    ]
    assert expected
    assert product_models.Item.objects.filter(category=other).exists()
    key = saved_pk(category)
    value: object = [key] if verdict == "admitted" else key
    schema = _schema(ItemChoiceFilter, product_models.Item, transport="sync", fields=("name",))

    payload = _post(schema, {"category": {"in_": value}}, transport="sync")

    if verdict == "admitted":
        assert payload == {"data": {"rows": [{"name": name} for name in expected]}}, payload
    else:
        leaf = ItemChoiceFilter.get_filters()["category__in"]
        _refused(
            payload,
            f"{type(leaf).__name__} consumes a list of values for its 'category' input, "
            f"but received a non-list container (int {key}) for the model-choice list; send a list "
            "(generated filter inputs deliver a list after GraphQL coercion).",
        )
