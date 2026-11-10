"""Generated filter and write inputs keep their declared shapes over HTTP, shared names included.

Alternate cycle registration orders, per-instance field edits and unordered declarations
need separate consumer classes. Each holder declares native Meta types and exercises the
public generated input or FilterSet entry point through the package view.

Generated names: two operator bags of one name whose lookups are declared in opposite
orders share one input type, and two declarations deriving one generated input name with
different fields (set/member splits, two range axes of different types, a root beside a
bag, a filter beside an order root, a model input beside a form or serializer input) each
serve a schema of their own, two mounts side by side in one process.
"""

import asyncio
from collections import OrderedDict
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING, Annotated

import pytest
import strawberry
from apps.library import models
from apps.products import services
from apps.products.models import Category
from django import forms
from django.db.models import IntegerField, Model, QuerySet, TextField
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import AllValuesFilter, BooleanFilter, CharFilter, Filter
from graphql_client import (
    JSONObject,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    json_str,
    response_json,
)
from strategy_schemas import make_django_type
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import (
    FilterSet,
    RangeFilter,
    RelatedFilter,
    filter_input_type,
)
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import ModelSerializerBase, canonical_order, scrambled

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | strawberry.Schema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


#: The two schemas a generated-name clash is split across, one per mount.
_PAIR: dict[str, DjangoSchema | strawberry.Schema | None] = {"first": None, "second": None}


def _pair_view(side: str) -> Callable[[HttpRequest], HttpResponseBase]:
    @wraps(DjangoGraphQLView.as_view())
    def view(request: HttpRequest) -> HttpResponseBase:
        schema = _PAIR[side]
        assert schema is not None
        return DjangoGraphQLView.as_view(schema=schema)(request)

    return view


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-filter-publication/", _graphql_view),
    path("graphql-filter-publication-async/", _async_graphql_view),
    path("graphql-clash/first/", _pair_view("first")),
    path("graphql-clash/second/", _pair_view("second")),
]


async def _async_post(document: str, variables: Mapping[str, object] | None) -> JSONObject:
    result = await AsyncTestClient().query(
        document,
        variables,
        assert_no_errors=False,
        url="/graphql-filter-publication-async/",
    )
    assert result.response.status_code == 200
    return response_json(result.response)


def _post(
    schema: DjangoSchema | strawberry.Schema,
    document: str,
    where: JSONObject | None = None,
    *,
    transport: str = "sync",
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                return asyncio.run(
                    _async_post(document, {"where": where} if where is not None else None),
                )
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


def _ring(
    disabled: Collection[str] = (),
    fired: list[str] | None = None,
) -> dict[str, type[FilterSet]]:
    """The branch -> desk -> shelf -> branch cycle; each set named in ``disabled`` is ``flat=False``.

    The shelf set's ``check_branch_permission`` gate records into ``fired``.
    """

    class RingBranchFilter(FilterSet):
        desks = RelatedFilter(
            lambda: RingDeskFilter,
            field_name="circulation_desks",
            flat="branch" not in disabled,
        )

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"], "city": ["exact"]}

    class RingDeskFilter(FilterSet):
        shelf = RelatedFilter(
            lambda: RingShelfFilter,
            field_name="shelf",
            flat="desk" not in disabled,
        )

        class Meta:
            model = models.CirculationDesk
            fields = {"name": ["exact"]}

    class RingShelfFilter(FilterSet):
        branch = RelatedFilter(
            lambda: RingBranchFilter,
            field_name="branch",
            flat="shelf" not in disabled,
        )

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"], "topic": ["exact"]}

        def check_branch_permission(self, _request: object) -> None:
            if fired is not None:
                fired.append("branch")

    return {"branch": RingBranchFilter, "desk": RingDeskFilter, "shelf": RingShelfFilter}


def _ring_schema(first: str, disabled: Collection[str] = ()) -> DjangoSchema:
    sets = _ring(disabled)
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


_RING_COMMON = {"and", "or", "not"}

# The published input of each ring set with one set's declaration ``flat=False``:
# the declaration's nested branch stays, and no path copies through it.
_FLAT_FALSE_RING_INPUTS = {
    "branch": {
        "branch": {"name", "city", "desks"},
        "desk": {
            "name",
            "shelf",
            "shelfCode",
            "shelfTopic",
            "shelfBranchName",
            "shelfBranchCity",
        },
        "shelf": {
            "code",
            "topic",
            "branch",
            "branchName",
            "branchCity",
        },
    },
    "desk": {
        "branch": {
            "name",
            "city",
            "desks",
            "desksName",
        },
        "desk": {"name", "shelf"},
        "shelf": {
            "code",
            "topic",
            "branch",
            "branchName",
            "branchCity",
            "branchDesksName",
        },
    },
    "shelf": {
        "branch": {
            "name",
            "city",
            "desks",
            "desksName",
            "desksShelfCode",
            "desksShelfTopic",
        },
        "desk": {
            "name",
            "shelf",
            "shelfCode",
            "shelfTopic",
        },
        "shelf": {"code", "topic", "branch"},
    },
}


@pytest.mark.django_db
@pytest.mark.parametrize("disabled", sorted(_FLAT_FALSE_RING_INPUTS))
@pytest.mark.parametrize("first", ["branch", "desk", "shelf"])
def test_a_flat_false_ring_edge_publishes_no_copy_in_each_type_registration_order(
    first: str,
    disabled: str,
) -> None:
    """Disabling one ring declaration withdraws every flat key through it, whichever type registers first."""
    payload = _post(
        _ring_schema(first, (disabled,)),
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
        name: names | _RING_COMMON for name, names in _FLAT_FALSE_RING_INPUTS[disabled].items()
    }
    assert {
        name: {json_object(field)["name"] for field in json_list(data[name], "inputFields")}
        for name in expected
    } == expected, payload


def _hide_kyiv(
    _cls: type[DjangoType],
    queryset: QuerySet[models.Branch],
    _info: object,
    **_kwargs: object,
) -> QuerySet[models.Branch]:
    return queryset.exclude(city="Kyiv")


async def _hide_kyiv_async(
    _cls: type[DjangoType],
    queryset: QuerySet[models.Branch],
    _info: object,
    **_kwargs: object,
) -> QuerySet[models.Branch]:
    return queryset.exclude(city="Kyiv")


def _gated_ring_schema(
    transport: str,
    disabled: Collection[str],
    fired: list[str],
) -> DjangoSchema:
    """The ring's shelf set over a JSON argument; the branch type hides Kyiv (async-only on async)."""
    sets = _ring(disabled, fired)
    shelf_set = sets["shelf"]
    hook = _hide_kyiv_async if transport == "async" else _hide_kyiv
    branch = make_django_type(
        "GatedRingBranch",
        models.Branch,
        ("name",),
        node=False,
        namespace_extra={"get_queryset": classmethod(hook)},
    )
    desk = make_django_type("GatedRingDesk", models.CirculationDesk, ("name",), node=False)
    shelf = make_django_type("GatedRingShelf", models.Shelf, ("code",), node=False)
    finalize_django_types()

    def resolve_sync(info: strawberry.Info[object, object], where: JSON) -> QuerySet[Model]:
        return shelf_set.apply_sync(where, models.Shelf.objects.order_by("code"), info)

    async def resolve_async(info: strawberry.Info[object, object], where: JSON) -> list[Model]:
        rows = await shelf_set.apply_async(where, models.Shelf.objects.order_by("code"), info)
        return [row async for row in rows]

    resolver = resolve_async if transport == "async" else resolve_sync

    @strawberry.type
    class Query:
        rows: object = strawberry.field(resolver=resolver, graphql_type=list[shelf])

    return DjangoSchema(query=Query, types=[branch, desk], config=strawberry_config())


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("disabled", [(), ("shelf",)], ids=["enabled", "flat-false"])
@pytest.mark.parametrize(
    ("name", "codes"),
    [("North", ["N-1"]), ("East", [])],
    ids=["visible-branch", "hidden-branch"],
)
def test_a_nested_branch_across_a_flat_false_declaration_keeps_visibility_and_gates(
    name: str,
    codes: list[str],
    disabled: tuple[str, ...],
    transport: str,
) -> None:
    """A ``flat=False`` declaration's nested branch reads its target's visibility and fires its gate.

    The branch type hides the Kyiv branch (through an async-only hook on the async
    transport), so the East shelf never matches; the shelf set's
    ``check_branch_permission`` fires once, enabled or disabled.
    """
    north = models.Branch.objects.create(name="North", city="Oslo")
    east = models.Branch.objects.create(name="East", city="Kyiv")
    models.Shelf.objects.create(branch=north, code="N-1", topic="maps")
    models.Shelf.objects.create(branch=east, code="E-1", topic="art")
    fired: list[str] = []
    schema = _gated_ring_schema(transport, disabled, fired)
    payload = _post(
        schema,
        "query($where: JSON!) { rows(where: $where) { code } }",
        {"branch": {"name": name}},
        transport=transport,
    )
    assert payload == {"data": {"rows": [{"code": code} for code in codes]}}, payload
    assert fired == ["branch"]


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


def _connection(name: str, node: type[DjangoType]) -> dict[str, tuple[object, object]]:
    """One connection root field over ``node``, as an ``(annotation, field)`` pair."""
    return {name: (DjangoConnection[node], DjangoConnectionField(node))}


def _root(fields: Mapping[str, tuple[object, object]], name: str = "Query") -> type:
    """A Strawberry root built from ``(annotation, field)`` pairs."""
    return strawberry.type(
        type(
            name,
            (),
            {
                "__annotations__": {key: pair[0] for key, pair in fields.items()},
                **{key: pair[1] for key, pair in fields.items()},
            },
        ),
    )


@pytest.mark.django_db
@pytest.mark.parametrize("schema_class", [strawberry.Schema, DjangoSchema])
def test_two_bags_of_one_name_and_one_lookup_set_in_any_order_share_one_type(
    schema_class: type[strawberry.Schema],
) -> None:
    """Bags whose lookups match in another declaration order are one input type.

    ``BookFilter`` + ``shelf__code`` and ``BookFilterShelf`` + ``code`` both mint
    ``BookFilterShelfCodeFilterInputType`` with the same two lookups declared in
    opposite orders, so one schema serves both members through one type and a
    document filtering through each member runs.
    """
    branch = models.Branch.objects.create(name="Central", city="Boston")
    near = models.Shelf.objects.create(code="x", topic="Near", branch=branch)
    far = models.Shelf.objects.create(code="y", topic="Far", branch=branch)
    models.Book.objects.create(title="Kindred", shelf=near)
    models.Book.objects.create(title="Dune", shelf=far)

    class BookFilter(FilterSet):
        class Meta:
            model = models.Book
            fields = {"shelf__code": ["exact", "icontains"]}

    class BookFilterShelf(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["icontains", "exact"]}

    books = make_django_type(
        "BookNode",
        models.Book,
        ("id", "title"),
        meta_extra={"filterset_class": BookFilter},
    )
    shelves = make_django_type(
        "ShelfNode",
        models.Shelf,
        ("id", "code"),
        meta_extra={"filterset_class": BookFilterShelf},
    )
    finalize_django_types()
    query = _root({**_connection("books", books), **_connection("shelves", shelves)})
    schema = schema_class(query=query, config=strawberry_config())

    payload = _post(
        schema,
        """
        {
          bag: __type(name: "BookFilterShelfCodeFilterInputType") { inputFields { name } }
          books(filter: {shelfCode: {iContains: "x"}}) { edges { node { title } } }
          shelves(filter: {code: {exact: "x", iContains: "x"}}) { edges { node { code } } }
        }
        """,
    )

    assert "errors" not in payload, payload
    data = json_object(payload["data"])
    assert sorted(json_str(field, "name") for field in json_list(data, "bag", "inputFields")) == [
        "exact",
        "iContains",
    ]
    assert json_at(data, "books") == {"edges": [{"node": {"title": "Kindred"}}]}
    assert json_at(data, "shelves") == {"edges": [{"node": {"code": "x"}}]}


@dataclass
class _ClashSide:
    """One declaration's half of a generated input-name clash: its roots and a probe.

    ``query`` maps a root field name to its ``(annotation, field)`` pair;
    ``mutation`` maps a root mutation name to its field; ``operation`` is a
    document only this side's schema serves.
    """

    query: dict[str, tuple[object, object]]
    mutation: dict[str, object] = field(default_factory=dict[str, object])
    operation: str | None = None


def _set_member_split() -> tuple[_ClashSide, _ClashSide]:
    """``BookFilter`` + ``set_code`` and ``BookFilterSet`` + ``code`` spell one bag name."""

    class BookFilter(FilterSet):
        set_code = CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []

    class BookFilterSet(FilterSet):
        code = RangeFilter(field_name="topic")

        class Meta:
            model = models.Shelf
            fields = []

    branches = make_django_type(
        "BranchNode",
        models.Branch,
        ("id", "name"),
        meta_extra={"filterset_class": BookFilter},
    )
    shelves = make_django_type(
        "ShelfNode",
        models.Shelf,
        ("id", "code"),
        meta_extra={"filterset_class": BookFilterSet},
    )
    return (
        _ClashSide(
            _connection("branches", branches),
            operation='{ branches(filter: {setCode: {exact: "x"}}) { edges { node { id } } } }',
        ),
        _ClashSide(
            _connection("shelves", shelves),
            operation=(
                '{ shelves(filter: {code: {exact: {start: "a", end: "b"}}}) '
                "{ edges { node { id } } } }"
            ),
        ),
    )


def _root_and_bag() -> tuple[_ClashSide, _ClashSide]:
    """FilterSet ``BookFilterSetFilter``'s root and ``BookFilter.set``'s bag share a name."""

    class BookFilter(FilterSet):
        set = CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []

    class BookFilterSetFilter(FilterSet):
        code = CharFilter(field_name="code")

        class Meta:
            model = models.Shelf
            fields = []

    branches = make_django_type(
        "BranchNode",
        models.Branch,
        ("id", "name"),
        meta_extra={"filterset_class": BookFilter},
    )
    shelves = make_django_type(
        "ShelfNode",
        models.Shelf,
        ("id", "code"),
        meta_extra={"filterset_class": BookFilterSetFilter},
    )
    return (
        _ClashSide(
            _connection("branches", branches),
            operation='{ branches(filter: {set: {exact: "x"}}) { edges { node { id } } } }',
        ),
        _ClashSide(
            _connection("shelves", shelves),
            operation='{ shelves(filter: {code: {exact: "x"}}) { edges { node { id } } } }',
        ),
    )


def _range_split() -> tuple[_ClashSide, _ClashSide]:
    """``A`` over ``b_c`` and ``AB`` over ``c`` spell one range name, of two axis types.

    The two rows are unmanaged models no operation reads: the sides are compared
    by what each mount publishes under the shared name.
    """

    class _IntRangeRow(Model):
        b_c: "IntegerField[float | int | str | Combinable, int]" = IntegerField()

        class Meta:
            app_label = "library"
            managed = False

        @override
        def __str__(self) -> str:
            return str(self.b_c)

    class _TextRangeRow(Model):
        c: "TextField[str | Combinable, str]" = TextField()

        class Meta:
            app_label = "library"
            managed = False

        @override
        def __str__(self) -> str:
            return self.c

    class A(FilterSet):
        x = RangeFilter(field_name="b_c")

        class Meta:
            model = _IntRangeRow
            fields = []

    class AB(FilterSet):
        y = RangeFilter(field_name="c")

        class Meta:
            model = _TextRangeRow
            fields = []

    ints = make_django_type(
        "IntRangeNode",
        _IntRangeRow,
        ("id",),
        meta_extra={"filterset_class": A},
    )
    texts = make_django_type(
        "TextRangeNode",
        _TextRangeRow,
        ("id",),
        meta_extra={"filterset_class": AB},
    )
    return _ClashSide(_connection("ints", ints)), _ClashSide(_connection("texts", texts))


def _filter_and_order_root() -> tuple[_ClashSide, _ClashSide]:
    """A FilterSet and an OrderSet both named ``Foo`` both mint ``FooInputType``."""

    class Foo(FilterSet):
        name = CharFilter(field_name="name")

        class Meta:
            model = models.Branch
            fields = []

    # The order side's class is declared under the very name the filter side's holds.
    foo_order = type(
        "Foo",
        (OrderSet,),
        {
            "__module__": Foo.__module__,
            "__qualname__": Foo.__qualname__,
            "Meta": type("Meta", (), {"model": models.Shelf, "fields": ["code"]}),
        },
    )
    branches = make_django_type(
        "BranchNode",
        models.Branch,
        ("id", "name"),
        meta_extra={"filterset_class": Foo},
    )
    shelves = make_django_type(
        "ShelfNode",
        models.Shelf,
        ("id", "code"),
        meta_extra={"orderset_class": foo_order},
    )
    return (
        _ClashSide(
            _connection("branches", branches),
            operation='{ branches(filter: {name: {exact: "x"}}) { edges { node { id } } } }',
        ),
        _ClashSide(
            _connection("shelves", shelves),
            operation="{ shelves(orderBy: {code: ASC}) { edges { node { id } } } }",
        ),
    )


def _model_input_mutation() -> dict[str, object]:
    """A ``DjangoMutation`` creating a ``Shelf`` from ``code`` and ``topic``."""

    class CreateShelfFromCodeAndTopic(DjangoMutation):
        class Meta:
            model = models.Shelf
            operation = "create"
            fields = ("code", "topic")
            permission_classes = []

    return {"create_shelf": DjangoMutationField(CreateShelfFromCodeAndTopic)}


def _write_roots() -> dict[str, tuple[object, object]]:
    """Declare the primary types the write flavors resolve, and a query root over them."""
    shelves = make_django_type("ShelfNode", models.Shelf, ("id", "code", "topic"))
    make_django_type("BranchNode", models.Branch, ("id", "name", "city"))
    return _connection("shelves", shelves)


def _model_and_form_input() -> tuple[_ClashSide, _ClashSide]:
    """A model input narrowed to ``(code, topic)`` and a ``ModelForm`` named ``ShelfCodeTopic``."""
    query = _write_roots()

    class ShelfCodeTopic(forms.ModelForm[models.Branch]):
        class Meta:
            model = models.Branch
            fields = ("name", "city")

    class CreateBranchViaForm(DjangoModelFormMutation):
        class Meta:
            form_class = ShelfCodeTopic
            operation = "create"
            permission_classes = []

    return (
        _ClashSide(query, _model_input_mutation()),
        _ClashSide(query, {"create_branch": DjangoMutationField(CreateBranchViaForm)}),
    )


def _model_and_serializer_input() -> tuple[_ClashSide, _ClashSide]:
    """A model input narrowed to ``(code, topic)`` and a serializer named ``ShelfCodeTopic``."""
    query = _write_roots()

    class ShelfCodeTopic(ModelSerializerBase[models.Branch]):
        class Meta:
            model = models.Branch
            fields = ("name", "city")

    class CreateBranchViaSerializer(SerializerMutation):
        class Meta:
            serializer_class = ShelfCodeTopic
            operation = "create"
            permission_classes = []

    return (
        _ClashSide(query, _model_input_mutation()),
        _ClashSide(query, {"create_branch": DjangoMutationField(CreateBranchViaSerializer)}),
    )


def _clash_schema(side: _ClashSide, schema_class: type[strawberry.Schema]) -> strawberry.Schema:
    """A schema serving ``side`` alone, with a mutation root when the side declares one."""
    mutation = (
        strawberry.type(type("Mutation", (), dict(side.mutation))) if side.mutation else None
    )
    return schema_class(query=_root(side.query), mutation=mutation, config=strawberry_config())


def _type_shape(side: str, name: str) -> JSONObject:
    """Introspect ``name``'s input fields on one clash mount."""
    with override_settings(ROOT_URLCONF=__name__):
        payload = graphql_payload(
            '{ __type(name: "%s") { inputFields { name type { kind name ofType { name } } } } }'
            % name,
            url=f"/graphql-clash/{side}/",
        )
    assert "errors" not in payload, payload
    return json_object(payload, "data", "__type")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("build", "name"),
    [
        pytest.param(
            _set_member_split,
            "BookFilterSetCodeFilterInputType",
            id="set-member-split",
        ),
        pytest.param(_root_and_bag, "BookFilterSetFilterInputType", id="root-and-bag"),
        pytest.param(_range_split, "ABCRangeInputType", id="range-split"),
        pytest.param(_filter_and_order_root, "FooInputType", id="filter-and-order-root"),
        pytest.param(_model_and_form_input, "ShelfCodeTopicInput", id="model-and-form-input"),
        pytest.param(
            _model_and_serializer_input,
            "ShelfCodeTopicInput",
            id="model-and-serializer-input",
        ),
    ],
)
@pytest.mark.parametrize("schema_class", [strawberry.Schema, DjangoSchema])
def test_a_generated_name_clash_split_across_two_schemas_builds_and_executes(
    build: Callable[[], tuple[_ClashSide, _ClashSide]],
    name: str,
    schema_class: type[strawberry.Schema],
) -> None:
    """Two generated inputs of one name and different fields each serve a schema of their own.

    The clash is per schema: one process builds each declaration into its own
    schema, mounted side by side, and each mount publishes its own declaration's
    fields under the shared name and runs its own operation.
    """
    first, second = build()
    finalize_django_types()
    _PAIR["first"] = _clash_schema(first, schema_class)
    _PAIR["second"] = _clash_schema(second, schema_class)
    try:
        shapes = [_type_shape(side, name) for side in ("first", "second")]
        assert all(shapes), shapes
        assert shapes[0] != shapes[1], shapes
        for side, clash in (("first", first), ("second", second)):
            if clash.operation is None:
                continue
            with override_settings(ROOT_URLCONF=__name__):
                payload = graphql_payload(clash.operation, url=f"/graphql-clash/{side}/")
            assert "errors" not in payload, payload
    finally:
        _PAIR["first"] = None
        _PAIR["second"] = None
