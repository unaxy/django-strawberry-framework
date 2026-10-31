"""Published filter cycles and deferred consumer fields preserve their declared inputs over HTTP.

Alternate cycle registration orders, per-instance field edits and unordered declarations
need separate consumer classes. Each holder declares native Meta types and exercises the
public generated input or FilterSet entry point through the package view.
"""

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Annotated

import pytest
import strawberry
from apps.library import models
from apps.products import services
from apps.products.models import Category
from django import forms
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import AllValuesFilter, BooleanFilter, CharFilter, Filter
from graphql_client import JSONObject, graphql_payload, json_list, json_object
from strategy_schemas import make_django_type
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter, filter_input_type
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import canonical_order, scrambled

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-filter-publication/", _graphql_view)]


def _post(schema: DjangoSchema, document: str, where: JSONObject | None = None) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables={"where": where} if where is not None else None,
                url="/graphql-filter-publication/",
            )
    finally:
        _CURRENT["schema"] = None


def _raw_schema(
    filterset: type[FilterSet],
    model: type[Model],
    label: str,
    targets: Sequence[tuple[type[Model], tuple[str, ...]]],
) -> DjangoSchema:
    output = make_django_type("PublicationOutput", model, (label,), node=False)
    types = [
        make_django_type(f"PublicationTarget{index}", target, fields, node=False)
        for index, (target, fields) in enumerate(targets)
    ]

    def resolve_rows(info: strawberry.Info[object, object], where: JSON) -> QuerySet[Model]:
        return filterset.apply_sync(where, model._default_manager.order_by(label), info)

    @strawberry.type
    class Query:
        rows: QuerySet[Model] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[output],
        )

    finalize_django_types()
    return DjangoSchema(
        query=Query,
        types=types,
        config=strawberry_config(),
        error_policy={"enabled": False},
    )


def _rows(schema: DjangoSchema, where: JSONObject, label: str) -> JSONObject:
    return _post(
        schema,
        "query($where: JSON!) { rows(where: $where) { " + label + " } }",
        where,
    )


def _published_field(
    output: type[DjangoType],
    filterset: type[FilterSet],
    model: type[Model],
) -> object:
    argument = filter_input_type(filterset)

    def resolve(
        info: strawberry.Info[object, object],
        criteria: Annotated[
            object,
            strawberry.argument(name="filter", graphql_type=argument),
        ],
    ) -> QuerySet[Model]:
        return filterset.apply_sync(criteria, model._default_manager.all(), info)

    return strawberry.field(resolver=resolve, graphql_type=list[output])


def _ring() -> dict[str, type[FilterSet]]:
    class RingBranchFilter(FilterSet):
        desks = RelatedFilter(lambda: RingDeskFilter, field_name="circulation_desks")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"], "city": ["exact"]}

    class RingDeskFilter(FilterSet):
        shelf = RelatedFilter(lambda: RingShelfFilter, field_name="shelf")

        class Meta:
            model = models.CirculationDesk
            fields = {"name": ["exact"]}

    class RingShelfFilter(FilterSet):
        branch = RelatedFilter(lambda: RingBranchFilter, field_name="branch")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"], "topic": ["exact"]}

    return {"branch": RingBranchFilter, "desk": RingDeskFilter, "shelf": RingShelfFilter}


def _ring_schema(first: str) -> DjangoSchema:
    sets = _ring()
    root_models = {"branch": models.Branch, "desk": models.CirculationDesk, "shelf": models.Shelf}
    outputs = {
        name: make_django_type(
            "Published" + name.title(),
            root_models[name],
            ("id",),
            node=False,
            meta_extra={"filterset_class": sets[name]},
        )
        for name in sorted(sets, key=lambda name: name != first)
    }
    branch, desk, shelf = outputs["branch"], outputs["desk"], outputs["shelf"]
    finalize_django_types()

    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "branches": list[branch],
                    "desks": list[desk],
                    "shelves": list[shelf],
                },
                "branches": _published_field(branch, sets["branch"], models.Branch),
                "desks": _published_field(desk, sets["desk"], models.CirculationDesk),
                "shelves": _published_field(shelf, sets["shelf"], models.Shelf),
            },
        ),
    )
    return DjangoSchema(query=query, config=strawberry_config())


@pytest.mark.django_db
@pytest.mark.parametrize("first", ["branch", "desk", "shelf"])
def test_a_cycle_publishes_its_complete_input_surface_in_each_type_registration_order(
    first: str,
) -> None:
    """Every root exposes the same finite cycle lap whichever model type registers first."""
    payload = _post(
        _ring_schema(first),
        """
        {
          branch: __type(name: "RingBranchFilterInputType") { inputFields { name } }
          desk: __type(name: "RingDeskFilterInputType") { inputFields { name } }
          shelf: __type(name: "RingShelfFilterInputType") { inputFields { name } }
        }
        """,
    )
    assert "errors" not in payload, payload
    data = json_object(payload["data"])
    expected = {
        "branch": {
            "name",
            "city",
            "desks",
            "desksName",
            "desksShelfCode",
            "desksShelfTopic",
            "desksShelfBranchName",
            "desksShelfBranchCity",
            "and",
            "or",
            "not",
        },
        "desk": {
            "name",
            "shelf",
            "shelfCode",
            "shelfTopic",
            "shelfBranchName",
            "shelfBranchCity",
            "shelfBranchDesksName",
            "and",
            "or",
            "not",
        },
        "shelf": {
            "code",
            "topic",
            "branch",
            "branchName",
            "branchCity",
            "branchDesksName",
            "branchDesksShelfCode",
            "branchDesksShelfTopic",
            "and",
            "or",
            "not",
        },
    }
    assert {
        name: {json_object(field)["name"] for field in json_list(data[name], "inputFields")}
        for name in expected
    } == expected, payload


def _cycle_override(shape: str, *, customize: bool) -> type[FilterSet]:
    resolved: dict[str, type[FilterSet]] = {}

    class CycleBranchFilter(FilterSet):
        shelves = RelatedFilter(lambda: resolved["shelf"], field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    class CycleShelfFilter(FilterSet):
        branch = RelatedFilter(CycleBranchFilter, field_name="branch")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

        @classmethod
        @override
        def get_filters(cls) -> OrderedDict[str, Filter]:
            table = OrderedDict(super().get_filters())
            if shape == "rename":
                return OrderedDict(
                    ("kode" if key == "code" else key, f) for key, f in table.items()
                )
            table["extra"] = CharFilter(field_name="topic", lookup_expr="icontains")
            return table

    shelf: type[FilterSet] = CycleShelfFilter
    if customize:

        class CustomizedCycleShelfFilter(CycleShelfFilter):
            def __init__(
                self,
                data: Mapping[str, object] | None = None,
                queryset: QuerySet[Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        shelf = CustomizedCycleShelfFilter
    resolved["shelf"] = shelf
    return CycleBranchFilter


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["rename", "add-in-place"])
@pytest.mark.parametrize("customize", [False, True], ids=["expanded", "projected"])
@pytest.mark.parametrize("spelling", ["flat", "nested"])
def test_a_cyclic_override_keeps_its_renamed_or_added_filter_on_flat_and_nested_requests(
    shape: str,
    spelling: str,
    *,
    customize: bool,
) -> None:
    """A cyclic child's public override contributes its actual key on both consumer input paths."""
    first = models.Branch.objects.create(name="B1")
    second = models.Branch.objects.create(name="B2")
    models.Shelf.objects.create(branch=first, code="S1", topic="alpha")
    models.Shelf.objects.create(branch=second, code="S2", topic="beta")
    parent = _cycle_override(shape, customize=customize)
    schema = _raw_schema(parent, models.Branch, "name", [(models.Shelf, ("code",))])
    key, value = ("kode", "S1") if shape == "rename" else ("extra", "alp")
    where: JSONObject = (
        {f"shelves__{key}": value} if spelling == "flat" else {"shelves": {key: value}}
    )
    assert _rows(schema, where, "name") == {
        "data": {"rows": [{"name": "B1"}]},
    }


@pytest.mark.django_db
def test_a_prefixed_consumer_form_filters_its_two_hop_flat_copy() -> None:
    """The consumer's prefix applies to the named desk-to-shelf copy on the actual bound form."""
    north = models.Branch.objects.create(name="North", city="Oslo")
    south = models.Branch.objects.create(name="South", city="Rome")
    northern = models.Shelf.objects.create(branch=north, code="N-1", topic="maps")
    southern = models.Shelf.objects.create(branch=south, code="S-1", topic="law")
    models.CirculationDesk.objects.create(branch=north, shelf=northern, name="Front")
    models.CirculationDesk.objects.create(branch=south, shelf=southern, name="Back")
    branch = _ring()["branch"]

    class PrefixedBranchFilter(branch):
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            del prefix
            super().__init__(data=data, queryset=queryset, request=request, prefix="p")

    schema = _raw_schema(
        PrefixedBranchFilter,
        models.Branch,
        "name",
        [(models.CirculationDesk, ("name",)), (models.Shelf, ("code",))],
    )
    assert _rows(schema, {"desks__shelf__code": "S-1"}, "name") == {
        "data": {"rows": [{"name": "South"}]},
    }


def _edited_issue_parent(edit: str) -> type[FilterSet]:
    class EditedIssueFilter(FilterSet):
        open_only = BooleanFilter(field_name="embargoed")
        title_required = CharFilter(field_name="title")

        class Meta:
            model = models.Issue
            fields = {"title": ["exact"]}

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            if edit == "required":
                self.filters["title_required"].extra["required"] = True
            else:
                self.filters["open_only"].extra["widget"] = forms.CheckboxInput

    class EditedPeriodicalFilter(FilterSet):
        issues = RelatedFilter(EditedIssueFilter, field_name="issues")

        class Meta:
            model = models.Periodical
            fields = {"name": ["exact"]}

    return EditedPeriodicalFilter


def _periodical_rows() -> None:
    closed = models.Periodical.objects.create(name="Closed Review")
    models.Issue.objects.create(periodical=closed, number=1, title="A", embargoed=True)
    open_ = models.Periodical.objects.create(name="Open Review")
    models.Issue.objects.create(periodical=open_, number=1, title="B", embargoed=False)


@pytest.mark.django_db
@pytest.mark.parametrize("edit", ["required", "checkbox"])
@pytest.mark.parametrize("named", [False, True], ids=["unnamed", "named"])
def test_a_childs_constructor_field_edit_affects_only_its_named_flat_copy(
    edit: str,
    *,
    named: bool,
) -> None:
    """Required and checkbox edits keep omitted copies inert and clean the named copy's real value."""
    _periodical_rows()
    where: JSONObject = {}
    if named:
        where = (
            {"issues__title_required": "B"} if edit == "required" else {"issues__open_only": ""}
        )
    schema = _raw_schema(
        _edited_issue_parent(edit),
        models.Periodical,
        "name",
        [(models.Issue, ("title",))],
    )
    names = ["Open Review"] if named else ["Closed Review", "Open Review"]
    assert _rows(schema, where, "name") == {
        "data": {"rows": [{"name": name} for name in names]},
    }


@pytest.mark.django_db
def test_a_named_child_constructor_required_field_refuses_an_empty_string() -> None:
    """A required flag authored by the child constructor reaches the actual projected form field."""
    _periodical_rows()
    schema = _raw_schema(
        _edited_issue_parent("required"),
        models.Periodical,
        "name",
        [(models.Issue, ("title",))],
    )
    payload = _rows(schema, {"issues__title_required": ""}, "name")
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "Invalid filter input",
                "locations": [{"line": 1, "column": 24}],
                "path": ["rows"],
                "extensions": {
                    "code": "FILTER_INVALID",
                    "errors": {
                        "issues__title_required": [
                            {"message": "This field is required.", "code": "required"},
                        ],
                    },
                },
            },
        ],
    }, payload


def _all_values_parent() -> type[FilterSet]:
    class TitlesIssueFilter(FilterSet):
        any_title = AllValuesFilter(field_name="title")

        class Meta:
            model = models.Issue
            fields = {"number": ["exact"]}

    class TitlesPeriodicalFilter(FilterSet):
        issues = RelatedFilter(TitlesIssueFilter, field_name="issues")
        title_available = CharFilter(method="filter_title_available")

        class Meta:
            model = models.Periodical
            fields = {"name": ["exact"]}

        def filter_title_available(
            self,
            queryset: QuerySet[models.Periodical],
            _name: str,
            value: str,
        ) -> QuerySet[models.Periodical]:
            field = self.filters["issues__any_title"].field
            assert isinstance(field, forms.ChoiceField)
            return (
                queryset.filter(issues__title=value)
                if field.valid_value(value)
                else queryset.none()
            )

    return TitlesPeriodicalFilter


@pytest.mark.django_db
@pytest.mark.parametrize("title", ["A", "missing"], ids=["available", "unavailable"])
def test_a_consumer_can_read_choices_from_a_deferred_all_values_copy(title: str) -> None:
    """A public filters read binds the late copy to its parent model before its real choices query."""
    review = models.Periodical.objects.create(name="Review")
    models.Issue.objects.create(periodical=review, number=1, title="B", embargoed=False)
    models.Issue.objects.create(periodical=review, number=2, title="A", embargoed=False)
    schema = _raw_schema(
        _all_values_parent(),
        models.Periodical,
        "name",
        [(models.Issue, ("title",))],
    )
    assert _rows(schema, {"title_available": title}, "name") == {
        "data": {"rows": [{"name": "Review"}] if title == "A" else []},
    }


_CATEGORY_COLUMNS = (
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
    "id",
)
_GRAPHQL_NAMES = {
    "is_private": "isPrivate",
    "created_date": "createdDate",
    "updated_date": "updatedDate",
}
_GRAPHQL_LOOKUPS = {
    "exact": "exact",
    "icontains": "iContains",
    "istartswith": "iStartsWith",
    "iendswith": "iEndsWith",
}


def _unordered_declaration(row: str) -> tuple[dict[str, object], list[tuple[str, list[str]]]]:
    if row == "lookup-set":
        lookups = scrambled(set, tuple(_GRAPHQL_LOOKUPS))
        return {"fields": {"name": lookups, "description": ["exact"]}}, [
            ("name", canonical_order(lookups)),
            ("description", ["exact"]),
        ]
    kind = frozenset if row.endswith("frozenset") else set
    names = scrambled(kind, _CATEGORY_COLUMNS)
    key = "filter_fields" if row.startswith("filter-fields") else "fields"
    meta: dict[str, object] = {key: names}
    kept = canonical_order(names)
    if row == "exclude":
        meta["exclude"] = {"updated_date"}
        kept.remove("updated_date")
    return meta, [(name, ["exact"]) for name in kept]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "row",
    [
        "fields-set",
        "fields-frozenset",
        "filter-fields-set",
        "filter-fields-frozenset",
        "exclude",
        "lookup-set",
    ],
)
def test_unordered_meta_declarations_publish_canonical_field_and_lookup_order(row: str) -> None:
    """The actual input type orders sets canonically while preserving the ordered neighbor in a dict."""
    services.seed_data(0)
    declared, expected = _unordered_declaration(row)
    filterset = type(
        "PublishedCanonicalFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": Category, **declared})},
    )
    output = make_django_type(
        "CanonicalCategory",
        Category,
        ("name",),
        node=False,
        meta_extra={"filterset_class": filterset},
    )
    finalize_django_types()

    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"categories": list[output]},
                "categories": _published_field(output, filterset, Category),
            },
        ),
    )
    schema = DjangoSchema(query=query, config=strawberry_config())
    payload = _post(
        schema,
        """
        {
          __type(name: "PublishedCanonicalFilterInputType") {
            inputFields {
              name
              type { name ofType { name } }
            }
          }
        }
        """,
    )
    assert "errors" not in payload, payload
    fields = [json_object(field) for field in json_list(payload, "data", "__type", "inputFields")]
    actual = [field for field in fields if field["name"] not in ("and", "or", "not")]
    assert [field["name"] for field in actual] == [
        _GRAPHQL_NAMES.get(name, name) for name, _ in expected
    ], payload
    named_types = [json_object(field["type"]) for field in actual]
    type_names = [
        str(type_["name"] or json_object(type_["ofType"])["name"]) for type_ in named_types
    ]
    document = (
        "{ "
        + " ".join(
            f'field{index}: __type(name: "{name}") {{ inputFields {{ name }} }}'
            for index, name in enumerate(type_names)
        )
        + " }"
    )
    lookups = _post(schema, document)
    assert "errors" not in lookups, lookups
    assert [
        [
            json_object(field)["name"]
            for field in json_list(lookups, "data", f"field{index}", "inputFields")
        ]
        for index in range(len(expected))
    ] == [[_GRAPHQL_LOOKUPS[lookup] for lookup in lookups] for _, lookups in expected], lookups
