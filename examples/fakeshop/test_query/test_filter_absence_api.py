"""Live filtering contracts for optional child leaves whose absence would constrain their own form.

Rung 3: these consumer declarations give the same Issue leaf seven different absent-value
behaviors and let a parent override its form builder. A single shipped IssueFilter cannot
simultaneously carry those declarations. Each holder uses real library rows and the native
connection pipeline; its Issue type deliberately exposes both embargoed and open issues.
"""

from collections.abc import Mapping
from functools import wraps
from typing import TypeVar

import pytest
import strawberry
from apps.library import models as library_models
from django import forms
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter, ChoiceFilter, Filter, ModelChoiceFilter
from django_filters.filterset import BaseFilterSet
from graphql_client import JSONObject, graphql_payload, json_object
from strawberry import relay
from strawberry.scalars import JSON
from strawberry.types import Info
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_ModelT = TypeVar("_ModelT", bound=Model)
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-filter-absence/", _graphql_view)]


def _post(schema: DjangoSchema, query: str, variables: Mapping[str, object]) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                query,
                variables=variables,
                url="/graphql-filter-absence/",
            )
    finally:
        _CURRENT["schema"] = None


class _OpenIssuesCharFilter(CharFilter):
    """Consumer code which applies its own predicate even when a text value is absent."""

    @override
    def filter(self, qs: QuerySet[_ModelT], value: object) -> QuerySet[_ModelT]:
        return qs.filter(embargoed=False)


class _OpenIssuesBooleanFilter(BooleanFilter):
    """The Boolean declaration has a different cleaned empty value, and the same own predicate."""

    @override
    def filter(self, qs: QuerySet[_ModelT], value: object) -> QuerySet[_ModelT]:
        return qs.filter(embargoed=False)


class _AlwaysOpenWidget(forms.NullBooleanSelect):
    """A consumer single-key widget which reads an absent field as False."""

    @override
    def value_from_datadict(
        self,
        data: Mapping[str, object],
        files: object,
        name: str,
    ) -> bool | None:
        return False


_BEHAVIORS = (
    "checkbox",
    "disabled",
    "disabled-text",
    "consumer-filter",
    "consumer-boolean-filter",
    "null-model-choice",
    "consumer-widget",
)


def _absence_declaration(behavior: str) -> Filter:
    """Keep each consumer filter declaration identical at the native and raw argument surfaces."""
    declarations: dict[str, Filter] = {
        "checkbox": BooleanFilter(field_name="embargoed", widget=forms.CheckboxInput),
        "disabled": BooleanFilter(field_name="embargoed", disabled=True, initial=False),
        "disabled-text": CharFilter(field_name="title", disabled=True, initial="B"),
        "consumer-filter": _OpenIssuesCharFilter(field_name="title"),
        "consumer-boolean-filter": _OpenIssuesBooleanFilter(field_name="embargoed"),
        "null-choice": ChoiceFilter(field_name="title", choices=[("B", "B")], null_value=""),
        "null-model-choice": ModelChoiceFilter(
            field_name="periodical",
            queryset=library_models.Periodical.objects.all(),
            null_value=None,
        ),
        "consumer-widget": BooleanFilter(field_name="embargoed", widget=_AlwaysOpenWidget),
    }
    return declarations[behavior]


def _absence_schema(behavior: str, form_builder: str) -> DjangoSchema:
    """Publish one consumer declaration and choose the parent's real form-building seam."""

    class AbsenceIssueFilter(FilterSet):
        open_only = _absence_declaration(behavior)

        class Meta:
            model = library_models.Issue
            fields = {"title": ["exact"]}

    class AbsencePeriodicalFilter(FilterSet):
        issues = RelatedFilter(AbsenceIssueFilter, field_name="issues")

        class Meta:
            model = library_models.Periodical
            fields = {"name": ["exact"]}

        if form_builder == "django-filter":

            @override
            def get_form_class(self) -> type[forms.Form]:
                return BaseFilterSet.get_form_class(self)

    class AbsenceIssueType(DjangoType):
        class Meta:
            model = library_models.Issue
            fields = ("title", "embargoed")

    class AbsencePeriodicalType(DjangoType):
        class Meta:
            model = library_models.Periodical
            fields = ("name",)
            filterset_class = AbsencePeriodicalFilter
            interfaces = (relay.Node,)

    finalize_django_types()

    @strawberry.type
    class Query:
        def _periodicals(self, _info: Info) -> QuerySet[library_models.Periodical]:
            return library_models.Periodical.objects.order_by("pk")

        periodicals: DjangoConnection[AbsencePeriodicalType] = DjangoConnectionField(
            AbsencePeriodicalType,
            resolver=_periodicals,
        )

    return DjangoSchema(
        query=Query,
        types=[AbsenceIssueType],
        config=strawberry_config(),
    )


def _seed_periodicals() -> None:
    """The closed issue A and open issue B are both visible to every holder request."""
    closed = library_models.Periodical.objects.create(name="Closed Review")
    library_models.Issue.objects.create(periodical=closed, number=1, title="A", embargoed=True)
    open_ = library_models.Periodical.objects.create(name="Open Review")
    library_models.Issue.objects.create(periodical=open_, number=1, title="B", embargoed=False)


_PERIODICALS = """
query($filter: AbsencePeriodicalFilterInputType) {
  periodicals(filter: $filter) {
    edges {
      node {
        name
      }
    }
  }
}
"""


def _connection(names: list[str]) -> JSONObject:
    return {"edges": [{"node": {"name": name}} for name in names]}


@pytest.mark.django_db
@pytest.mark.parametrize("behavior", _BEHAVIORS)
def test_a_consumer_form_cannot_apply_an_unnamed_child_default_to_the_parent_over_http(
    behavior: str,
) -> None:
    """Every supported absent-value behavior stays inert on the parent's full consumer form.

    The upstream form builder includes all flat copies, so the applicator's independent
    unnamed-copy skip must protect Closed Review from a child default which would remove it.
    """
    _seed_periodicals()
    schema = _absence_schema(behavior, "django-filter")
    result = _post(schema, _PERIODICALS, {"filter": {"name": {"exact": "Closed Review"}}})
    assert result == {"data": {"periodicals": _connection(["Closed Review"])}}, result


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("form_builder", "filter_input", "names"),
    [
        pytest.param(
            "package",
            {},
            ["Closed Review", "Open Review"],
            id="package-empty-filter",
        ),
        pytest.param(
            "django-filter",
            {},
            ["Closed Review", "Open Review"],
            id="consumer-empty-filter",
        ),
        pytest.param(
            "package",
            {"name": {"exact": "Closed Review"}},
            ["Closed Review"],
            id="package-own-leaf",
        ),
        pytest.param(
            "django-filter",
            {"issuesTitle": {"exact": "A"}},
            ["Closed Review"],
            id="consumer-flat-sibling",
        ),
        pytest.param(
            "package",
            {"or": [{"issuesTitle": {"exact": "A"}}]},
            ["Closed Review"],
            id="package-or-arm",
        ),
        pytest.param(
            "django-filter",
            {"or": [{"issuesTitle": {"exact": "A"}}]},
            ["Closed Review"],
            id="consumer-or-arm",
        ),
        pytest.param(
            "package",
            {"not": {"issuesTitle": {"exact": "B"}}},
            ["Closed Review"],
            id="package-not-arm",
        ),
        pytest.param(
            "django-filter",
            {"not": {"issuesTitle": {"exact": "B"}}},
            ["Closed Review"],
            id="consumer-not-arm",
        ),
    ],
)
def test_an_unnamed_child_copy_stays_inert_in_each_parent_input_context_over_http(
    form_builder: str,
    filter_input: JSONObject,
    names: list[str],
) -> None:
    """Empty, own, sibling and logical input construct the right unnamed-copy scope.

    Every empty case explicitly sends filter:{}, which the native sidecar applies; omitting
    the argument would bypass filtering and could not prove the form-building contract.
    """
    _seed_periodicals()
    schema = _absence_schema("checkbox", form_builder)
    result = _post(schema, _PERIODICALS, {"filter": filter_input})
    assert result == {"data": {"periodicals": _connection(names)}}, result


@pytest.mark.django_db
@pytest.mark.parametrize("behavior", _BEHAVIORS)
def test_an_unnamed_parent_copy_does_not_disable_the_childs_own_form_default_over_http(
    behavior: str,
) -> None:
    """The flat parent copy stays inert while the same leaf still acts on its own nested form.

    The paired flat request proves A exists and is visible. The nested child's own form
    applies its absent-value behavior, which conflicts with A, so the nested branch matches
    nothing. The contrast cannot pass merely because the Issue type hides embargoed rows.
    """
    _seed_periodicals()
    schema = _absence_schema(behavior, "package")
    result = _post(
        schema,
        """
        query($flat: AbsencePeriodicalFilterInputType, $nested: AbsencePeriodicalFilterInputType) {
          flat: periodicals(filter: $flat) {
            edges {
              node {
                name
              }
            }
          }
          nested: periodicals(filter: $nested) {
            edges {
              node {
                name
              }
            }
          }
        }
        """,
        {"flat": {"issuesTitle": {"exact": "A"}}, "nested": {"issues": {"title": {"exact": "A"}}}},
    )
    assert result == {
        "data": {"flat": _connection(["Closed Review"]), "nested": _connection([])},
    }, result


def _raw_absence_schema(form_builder: str, behavior: str = "null-choice") -> DjangoSchema:
    """Keep the consumer's unbound set and ChoiceFilter form through an ordinary JSON argument.

    The title column has no model choices, so publishing FilterInput for this declaration is
    refused. The consumer resolver still legitimately accepts a JSON search object and calls
    the public FilterSet entry point, without inventing a choice enum or binding an owner.
    """

    class NullIssueFilter(FilterSet):
        open_only = _absence_declaration(behavior)

        class Meta:
            model = library_models.Issue
            fields = {"title": ["exact"]}

    class NullPeriodicalFilter(FilterSet):
        issues = RelatedFilter(NullIssueFilter, field_name="issues")

        class Meta:
            model = library_models.Periodical
            fields = {"name": ["exact"]}

        if form_builder == "django-filter":

            @override
            def get_form_class(self) -> type[forms.Form]:
                return BaseFilterSet.get_form_class(self)

    class NullIssueOutput(DjangoType):
        class Meta:
            model = library_models.Issue
            fields = ("title",)

    class NullPeriodicalOutput(DjangoType):
        class Meta:
            model = library_models.Periodical
            fields = ("name",)

    @strawberry.type
    class Query:
        def _periodicals(self, info: Info, where: JSON) -> QuerySet[library_models.Periodical]:
            return NullPeriodicalFilter.apply_sync(
                where,
                library_models.Periodical.objects.order_by("name"),
                info,
            )

        def _all_periodicals(self) -> QuerySet[library_models.Periodical]:
            return library_models.Periodical.objects.order_by("name")

        def _raw_issues(self, where: JSON) -> QuerySet[library_models.Issue]:
            return NullIssueFilter(
                data=json_object(where),
                queryset=library_models.Issue.objects.all(),
            ).qs

        periodicals: QuerySet[library_models.Periodical] = strawberry.field(
            resolver=_periodicals,
            graphql_type=list[NullPeriodicalOutput],
        )
        all_periodicals: QuerySet[library_models.Periodical] = strawberry.field(
            resolver=_all_periodicals,
            graphql_type=list[NullPeriodicalOutput],
        )
        raw_issues: QuerySet[library_models.Issue] = strawberry.field(
            resolver=_raw_issues,
            graphql_type=list[NullIssueOutput],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_NULL_CHOICE_PERIODICALS = """
query($where: JSON!) {
  periodicals(where: $where) {
    name
  }
  allPeriodicals {
    name
  }
}
"""


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("form_builder", "where", "names"),
    [
        pytest.param("package", {}, ["Closed Review", "Open Review"], id="package-empty"),
        pytest.param("django-filter", {}, ["Closed Review", "Open Review"], id="consumer-empty"),
        pytest.param(
            "django-filter",
            {"name": {"exact": "Closed Review"}},
            ["Closed Review"],
            id="consumer-own-leaf",
        ),
        pytest.param(
            "django-filter",
            {"issues__title": {"exact": "B"}},
            ["Open Review"],
            id="consumer-flat-sibling",
        ),
        pytest.param(
            "django-filter",
            {"or_": [{"issues__title": {"exact": "A"}}]},
            ["Closed Review"],
            id="consumer-or-arm",
        ),
        pytest.param(
            "django-filter",
            {"not_": {"issues__title": {"exact": "B"}}},
            ["Closed Review"],
            id="consumer-not-arm",
        ),
    ],
)
def test_an_unnamed_null_choice_copy_is_inert_in_each_parent_context_over_http(
    form_builder: str,
    where: JSONObject,
    names: list[str],
) -> None:
    """An absent title choice would constrain its own form to NULL, but no unnamed parent copy."""
    _seed_periodicals()
    schema = _raw_absence_schema(form_builder)
    result = _post(schema, _NULL_CHOICE_PERIODICALS, {"where": where})
    assert result == {
        "data": {
            "periodicals": [{"name": name} for name in names],
            "allPeriodicals": [{"name": name} for name in ("Closed Review", "Open Review")],
        },
    }, result


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("where", "names"),
    [
        pytest.param(
            {"issues__open_only": {"exact": "B"}},
            ["Open Review"],
            id="named-flat",
        ),
        pytest.param(
            {"issues": {"open_only": {"exact": "B"}}},
            ["Open Review"],
            id="named-nested",
        ),
        pytest.param(
            {"issues__open_only": {"exact": "B"}, "issues": {"open_only": {"exact": "B"}}},
            ["Open Review"],
            id="named-both",
        ),
        pytest.param(
            {"issues": {"title": {"exact": "B"}}},
            [],
            id="nested-sibling-keeps-child-default",
        ),
        pytest.param(
            {"issues__title": {"exact": "B"}},
            ["Open Review"],
            id="flat-sibling-skips-child-default",
        ),
    ],
)
def test_a_named_null_choice_copy_keeps_the_child_form_semantics_over_http(
    where: JSONObject,
    names: list[str],
) -> None:
    """A supplied choice matches B; an omitted choice acts only on the nested child's own form."""
    _seed_periodicals()
    schema = _raw_absence_schema("package")
    result = _post(schema, _NULL_CHOICE_PERIODICALS, {"where": where})
    assert result == {
        "data": {
            "periodicals": [{"name": name} for name in names],
            "allPeriodicals": [{"name": name} for name in ("Closed Review", "Open Review")],
        },
    }, result


@pytest.mark.django_db
def test_a_null_choice_default_still_constrains_the_childs_own_form_over_http() -> None:
    """A direct child form keeps the ChoiceFilter NULL default while its title sibling is supplied."""
    _seed_periodicals()
    schema = _raw_absence_schema("package")
    result = _post(
        schema,
        """
        query($where: JSON!) {
          rawIssues(where: $where) {
            title
          }
          allPeriodicals {
            name
          }
        }
        """,
        {"where": {"title": "B"}},
    )
    assert result == {
        "data": {
            "rawIssues": [],
            "allPeriodicals": [{"name": name} for name in ("Closed Review", "Open Review")],
        },
    }, result


@pytest.mark.django_db
@pytest.mark.parametrize("behavior", _BEHAVIORS)
@pytest.mark.parametrize("spelling", ["flat", "nested", "both"])
def test_a_named_child_default_leaf_matches_the_same_rows_in_each_spelling_over_http(
    behavior: str,
    spelling: str,
) -> None:
    """The original unbound declaration acts once supplied flat, nested, or in both positions."""
    _seed_periodicals()
    schema = _raw_absence_schema("package", behavior)
    values: dict[str, object] = {
        "checkbox": True,
        "disabled": True,
        "disabled-text": "A",
        "consumer-filter": "A",
        "consumer-boolean-filter": True,
        "null-model-choice": library_models.Periodical.objects.get(name="Closed Review").pk,
        "consumer-widget": True,
    }
    where: JSONObject = {}
    bag = {"exact": values[behavior]}
    if spelling in ("flat", "both"):
        where["issues__open_only"] = bag
    if spelling in ("nested", "both"):
        where["issues"] = {"open_only": bag}
    names = ["Closed Review"] if behavior in ("checkbox", "null-model-choice") else ["Open Review"]
    result = _post(schema, _NULL_CHOICE_PERIODICALS, {"where": where})
    assert result == {
        "data": {
            "periodicals": [{"name": name} for name in names],
            "allPeriodicals": [{"name": name} for name in ("Closed Review", "Open Review")],
        },
    }, result


@pytest.mark.django_db
@pytest.mark.parametrize("behavior", _BEHAVIORS)
@pytest.mark.parametrize("spelling", ["flat", "nested", "child-root"])
def test_a_child_default_belongs_to_the_form_on_which_the_sibling_is_read_over_http(
    behavior: str,
    spelling: str,
) -> None:
    """A child-root or nested sibling retains its own default; a flat sibling skips that copy."""
    _seed_periodicals()
    schema = _raw_absence_schema("package", behavior)
    if spelling == "child-root":
        result = _post(
            schema,
            """
            query($where: JSON!) {
              rawIssues(where: $where) {
                title
              }
              allPeriodicals {
                name
              }
            }
            """,
            {"where": {"title": "B"}},
        )
        assert result == {
            "data": {
                "rawIssues": [] if behavior == "null-model-choice" else [{"title": "B"}],
                "allPeriodicals": [{"name": name} for name in ("Closed Review", "Open Review")],
            },
        }, result
        return
    where: JSONObject = (
        {"issues__title": {"exact": "B"}}
        if spelling == "flat"
        else {"issues": {"title": {"exact": "B"}}}
    )
    names = [] if spelling == "nested" and behavior == "null-model-choice" else ["Open Review"]
    result = _post(schema, _NULL_CHOICE_PERIODICALS, {"where": where})
    assert result == {
        "data": {
            "periodicals": [{"name": name} for name in names],
            "allPeriodicals": [{"name": name} for name in ("Closed Review", "Open Review")],
        },
    }, result
