"""A served set with a ``required`` own filter refuses a request that supplies no filter input.

A root connection and a nested ``<relation>Connection`` over such a set bind its form
when ``filter:`` is omitted, ``null`` or an unset variable, so the form refuses the
request with the ``FILTER_INVALID`` envelope ``filter: {}`` answers; the nested
relation is never window-planned. A required flag whose form field never refuses
binds the set all the same, so an omitted ``filter:`` answers what ``filter: {}``
answers. A set with no required own filter keeps its unbound reading and its query
counts (a child's required leaf copied flat included), an iterable ``resolver=``
return passes through, and an enabled flat copy that takes the own required key stays
the copy.
"""

import asyncio
import logging
from collections.abc import Mapping
from functools import wraps

import pytest
import strawberry
from apps.library import models as library_models
from django import forms
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import BooleanFilter, CharFilter
from graphql_client import (
    JSONObject,
    graphql_payload,
    json_list,
    json_object,
    json_str,
    response_json,
)
from strawberry import relay
from strawberry.types import Info

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-required-omission/", _graphql_view),
    path("graphql-required-omission-async/", _async_view),
]


async def _async_post(document: str, variables: Mapping[str, object]) -> JSONObject:
    response = await AsyncTestClient().query(
        document,
        variables,
        url="/graphql-required-omission-async/",
        assert_no_errors=False,
    )
    assert response.response.status_code == 200
    return response_json(response.response)


def _post(
    schema: DjangoSchema,
    document: str,
    variables: Mapping[str, object] | None = None,
    *,
    transport: str = "sync",
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                return asyncio.run(_async_post(document, variables or {}))
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-required-omission/",
            )
    finally:
        _CURRENT["schema"] = None


def _periodical_set(*, required: bool) -> type[FilterSet]:
    """A Periodical set whose own ``name_req`` leaf is ``required`` or not."""

    class OmissionPeriodicalFilter(FilterSet):
        name_req = CharFilter(field_name="name", required=required)

        class Meta:
            model = library_models.Periodical
            fields = {"name": ["exact"]}

    return OmissionPeriodicalFilter


def _issue_set(*, required: bool) -> type[FilterSet]:
    """An Issue set whose own ``title_req`` leaf is ``required`` or not."""

    class OmissionIssueFilter(FilterSet):
        title_req = CharFilter(field_name="title", required=required)

        class Meta:
            model = library_models.Issue
            fields = {"title": ["exact"]}

    return OmissionIssueFilter


def _schema(
    periodical_filter: type[FilterSet] | None,
    issue_filter: type[FilterSet] | None = None,
    *,
    strictness: str = "off",
    iterable: bool = False,
) -> DjangoSchema:
    """Serve ``periodicals`` (over ``periodical_filter``), its nested ``issuesConnection`` and ``issues``."""

    class OmissionIssueType(DjangoType):
        class Meta:
            model = library_models.Issue
            fields = ("title",)
            interfaces = (relay.Node,)
            if issue_filter is not None:
                filterset_class = issue_filter

    class OmissionPeriodicalType(DjangoType):
        class Meta:
            model = library_models.Periodical
            fields = ("name", "issues")
            interfaces = (relay.Node,)
            relation_shapes = {"issues": "connection"}
            if periodical_filter is not None:
                filterset_class = periodical_filter

    finalize_django_types()
    optimizer = DjangoOptimizerExtension(strictness=strictness)

    @strawberry.type
    class Query:
        def _periodicals(self, _info: Info) -> object:
            rows = library_models.Periodical.objects.order_by("pk")
            return list(rows) if iterable else rows

        periodicals: DjangoConnection[OmissionPeriodicalType] = DjangoConnectionField(
            OmissionPeriodicalType,
            resolver=_periodicals,
        )

        def _issues(self, _info: Info) -> QuerySet[library_models.Issue]:
            return library_models.Issue.objects.order_by("pk")

        issues: DjangoConnection[OmissionIssueType] = DjangoConnectionField(
            OmissionIssueType,
            resolver=_issues,
        )

    return DjangoSchema(
        query=Query,
        types=[OmissionIssueType],
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _seed() -> None:
    closed = library_models.Periodical.objects.create(name="Closed Review")
    library_models.Issue.objects.create(periodical=closed, number=1, title="A", embargoed=True)
    open_ = library_models.Periodical.objects.create(name="Open Review")
    library_models.Issue.objects.create(periodical=open_, number=1, title="B", embargoed=False)
    library_models.Periodical.objects.create(name="Empty Review")


_ALL = ["Closed Review", "Open Review", "Empty Review"]
_EVERY_ISSUE = {"Closed Review": ["A"], "Open Review": ["B"], "Empty Review": []}

_ROOT_WITH_VARIABLE = """
query($f: OmissionPeriodicalFilterInputType) {
  periodicals(filter: $f) { edges { node { name } } }
}
"""

#: The root document per spelling of "no filter input"; ``{}`` is the bound control.
_ROOT_DOCUMENTS: dict[str, tuple[str, dict[str, object]]] = {
    "omitted": ("query { periodicals { edges { node { name } } } }", {}),
    "inline-null": ("query { periodicals(filter: null) { edges { node { name } } } }", {}),
    "unset-variable": (_ROOT_WITH_VARIABLE, {}),
    "empty": ("query { periodicals(filter: {}) { edges { node { name } } } }", {}),
}

_NESTED = """
query($f: OmissionIssueFilterInputType) {
  periodicals {
    edges { node { name issuesConnection(filter: $f) { edges { node { title } } } } }
  }
}
"""
_NESTED_OMITTED = """
query {
  periodicals {
    edges { node { name issuesConnection { edges { node { title } } } } }
  }
}
"""


#: The nested document's variables per spelling; ``None`` posts the document with no ``filter:``.
_NESTED_VARIABLES: dict[str, dict[str, object] | None] = {
    "omitted": None,
    "null-variable": {"f": None},
    "empty": {"f": {}},
}


def _required_refusal(key: str, path: list[str | int]) -> JSONObject:
    return {
        "message": "Invalid filter input",
        "path": path,
        "extensions": {
            "code": "FILTER_INVALID",
            "errors": {key: [{"message": "This field is required.", "code": "required"}]},
        },
    }


def _refused(payload: JSONObject, key: str, path: list[str | int]) -> None:
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    error = json_object(errors[0])
    expected = _required_refusal(key, path)
    assert {k: error.get(k) for k in ("message", "path", "extensions")} == expected, payload


def _edges(payload: JSONObject) -> list[object]:
    assert "errors" not in payload, payload
    return json_list(payload, "data", "periodicals", "edges")


def _names(payload: JSONObject) -> list[str]:
    return [json_str(edge, "node", "name") for edge in _edges(payload)]


def _nested(payload: JSONObject) -> dict[str, list[str]]:
    return {
        json_str(edge, "node", "name"): [
            json_str(issue, "node", "title")
            for issue in json_list(edge, "node", "issuesConnection", "edges")
        ]
        for edge in _edges(payload)
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "spelling",
    [
        "omitted",
        "inline-null",
        "unset-variable",
        "empty",
    ],
)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_required_own_filter_refuses_a_root_request_with_no_filter_input_over_http(
    spelling: str,
    transport: str,
) -> None:
    """``filter:`` omitted, ``null`` or an unset variable is refused as ``filter: {}`` is."""
    _seed()
    schema = _schema(_periodical_set(required=True))
    document, variables = _ROOT_DOCUMENTS[spelling]
    payload = _post(schema, document, variables, transport=transport)
    _refused(payload, "name_req", ["periodicals"])
    assert payload.get("data") is None, payload


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["omitted", "inline-null", "unset-variable"])
def test_a_required_root_refusal_reads_no_row(spelling: str) -> None:
    """The form refuses before the connection reads a row."""
    _seed()
    schema = _schema(_periodical_set(required=True))
    document, variables = _ROOT_DOCUMENTS[spelling]
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, document, variables)
    _refused(payload, "name_req", ["periodicals"])
    assert queries.captured_queries == [], queries.captured_queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_required_own_filter_given_its_key_answers_rows_over_http(transport: str) -> None:
    """The same set answers the matching rows once the request names the required key."""
    _seed()
    schema = _schema(_periodical_set(required=True))
    payload = _post(
        schema,
        _ROOT_WITH_VARIABLE,
        {"f": {"nameReq": {"exact": "Closed Review"}}},
        transport=transport,
    )
    assert _names(payload) == ["Closed Review"]


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["omitted", "inline-null", "unset-variable"])
def test_a_set_with_no_required_filter_answers_every_row_in_one_query(spelling: str) -> None:
    """A set with no required own filter runs no filter step when ``filter:`` is absent."""
    _seed()
    schema = _schema(_periodical_set(required=False))
    document, variables = _ROOT_DOCUMENTS[spelling]
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, document, variables)
    assert _names(payload) == _ALL
    assert len(queries.captured_queries) == 1, queries.captured_queries


@pytest.mark.django_db
def test_an_iterable_resolver_over_a_required_set_passes_through_with_no_filter_input() -> None:
    """An iterable ``resolver=`` return cannot be filtered; with no ``filter:`` it is served."""
    _seed()
    schema = _schema(_periodical_set(required=True), iterable=True)
    assert _names(_post(schema, _ROOT_DOCUMENTS["omitted"][0])) == _ALL


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "required",
        "variables",
        "answer",
        "query_count",
    ),
    [
        pytest.param(
            False,
            None,
            {"Closed Review": ["A"], "Open Review": ["B"], "Empty Review": []},
            2,
            id="optional-omitted",
        ),
        pytest.param(
            False,
            {"f": {}},
            {"Closed Review": ["A"], "Open Review": ["B"], "Empty Review": []},
            4,
            id="optional-empty",
        ),
        pytest.param(
            True,
            {"f": {"titleReq": {"exact": "A"}}},
            {"Closed Review": ["A"], "Open Review": [], "Empty Review": []},
            4,
            id="required-given",
        ),
    ],
)
def test_a_nested_connection_answers_rows_with_its_query_count(
    variables: dict[str, object] | None,
    answer: dict[str, list[str]],
    query_count: int,
    *,
    required: bool,
) -> None:
    """An optional nested set stays window-planned when omitted; a filtered one runs per parent."""
    _seed()
    schema = _schema(None, _issue_set(required=required))
    document = _NESTED_OMITTED if variables is None else _NESTED
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, document, variables)
    assert _nested(payload) == answer
    assert len(queries.captured_queries) == query_count, queries.captured_queries


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["omitted", "null-variable", "empty"])
def test_a_required_nested_set_refuses_a_request_with_no_filter_input_over_http(
    spelling: str,
) -> None:
    """The nested relation is not window-planned: the first parent's form refuses the request."""
    _seed()
    schema = _schema(None, _issue_set(required=True))
    document = _NESTED_OMITTED if spelling == "omitted" else _NESTED
    variables = _NESTED_VARIABLES[spelling]
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, document, variables)
    _refused(
        payload,
        "title_req",
        [
            "periodicals",
            "edges",
            0,
            "node",
            "issuesConnection",
        ],
    )
    assert len(queries.captured_queries) == 1, queries.captured_queries


@pytest.mark.django_db
def test_strictness_names_a_required_nested_set_as_the_reason_it_runs_per_parent(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The planner and the resolver each name the required filter as the window's loss."""
    _seed()
    schema = _schema(
        None,
        _issue_set(required=True),
        strictness="warn",
    )
    caplog.set_level(logging.DEBUG, logger="django_strawberry_framework")
    payload = _post(schema, _NESTED_OMITTED)
    _refused(
        payload,
        "title_req",
        [
            "periodicals",
            "edges",
            0,
            "node",
            "issuesConnection",
        ],
    )
    messages = [
        r.getMessage() for r in caplog.records if r.name.startswith("django_strawberry_framework")
    ]
    assert (
        "Optimizer: nested connection issues response key 'issuesConnection' falls back "
        "to per-parent resolution (target filter set has a required filter)."
    ) in messages, messages
    assert (
        "Potential N+1 on issues (not window-planned: target filter set has a required "
        "filter; resolving per-parent)"
    ) in messages, messages


def _shadowed_set(*, flat: bool) -> type[FilterSet]:
    """An own required ``issues__title_req`` beside a branch whose enabled copy takes that key."""
    child = _issue_set(required=False)

    class OmissionPeriodicalFilter(FilterSet):
        issues = RelatedFilter(child, field_name="issues", flat=flat)
        issues__title_req = CharFilter(field_name="issues__title", required=True)

        class Meta:
            model = library_models.Periodical
            fields = {"name": ["exact"]}

    return OmissionPeriodicalFilter


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["omitted", "empty"])
@pytest.mark.parametrize("flat", [True, False])
def test_an_enabled_flat_copy_takes_the_own_required_key_over_http(
    spelling: str,
    *,
    flat: bool,
) -> None:
    """An enabled copy holds the key, so the own ``required`` is gone; ``flat=False`` restores it."""
    _seed()
    schema = _schema(_shadowed_set(flat=flat))
    document, variables = _ROOT_DOCUMENTS[spelling]
    payload = _post(schema, document, variables)
    if flat:
        assert _names(payload) == _ALL
    else:
        _refused(payload, "issues__title_req", ["periodicals"])


@pytest.mark.django_db
def test_a_nested_set_whose_required_leaf_is_only_a_flat_copy_keeps_its_window() -> None:
    """A child set's required leaf copied flat onto the target set is no own required filter.

    The copy acts only when a request names it, so an omitted ``filter:`` leaves the
    target set unbound and the nested page is served from the window.
    """
    _seed()
    child = _periodical_set(required=True)

    class OmissionIssueFilter(FilterSet):
        periodical = RelatedFilter(child, field_name="periodical", flat=True)

        class Meta:
            model = library_models.Issue
            fields = {"title": ["exact"]}

    schema = _schema(None, OmissionIssueFilter)
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, _NESTED_OMITTED)
    assert _nested(payload) == _EVERY_ISSUE
    assert len(queries.captured_queries) == 2, queries.captured_queries


def _required_boolean_set(*, checkbox: bool) -> type[FilterSet]:
    """An Issue set flagging a ``BooleanFilter`` required, whose ``NullBooleanField`` never refuses."""

    class OmissionIssueFilter(FilterSet):
        embargoed_req = BooleanFilter(field_name="embargoed", required=True)
        if checkbox:
            open_only = BooleanFilter(field_name="embargoed", widget=forms.CheckboxInput)

        class Meta:
            model = library_models.Issue
            fields = {"title": ["exact"]}

    return OmissionIssueFilter


@pytest.mark.django_db
def test_a_required_flag_whose_field_never_refuses_answers_as_an_empty_filter_nested() -> None:
    """The flag binds the nested set, so its page is read per parent; no field refuses it."""
    _seed()
    schema = _schema(None, _required_boolean_set(checkbox=False))
    with CaptureQueriesContext(connection) as queries:
        payload = _post(schema, _NESTED_OMITTED)
    assert _nested(payload) == _EVERY_ISSUE
    assert len(queries.captured_queries) == 4, queries.captured_queries


_ISSUES_OMITTED = "query { issues { edges { node { title } } } }"
_ISSUES_EMPTY = "query { issues(filter: {}) { edges { node { title } } } }"


@pytest.mark.django_db
@pytest.mark.parametrize("document", [_ISSUES_OMITTED, _ISSUES_EMPTY], ids=["omitted", "empty"])
def test_an_omitted_filter_on_a_required_set_answers_what_an_empty_filter_answers(
    document: str,
) -> None:
    """Beside the required flag, a checkbox reads its absent value as ``False`` either way."""
    _seed()
    schema = _schema(None, _required_boolean_set(checkbox=True))
    payload = _post(schema, document)
    assert "errors" not in payload, payload
    titles = [
        json_str(edge, "node", "title") for edge in json_list(payload, "data", "issues", "edges")
    ]
    assert titles == ["B"]
