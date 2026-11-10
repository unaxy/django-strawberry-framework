"""Consumer JSON arguments preserve filtering, inactive logic and malformed-value refusals.

These consumers deliberately accept ordinary JSON instead of generated FilterInput types.
Their resolvers pass request values to public FilterSet apply methods or construction/.qs. Invalid
shapes therefore reach the same supported apply seam as a consumer's assembled criteria;
they are not private-validator wrappers. Native Meta output types remain unbound to the
sets. Explicit pass-through policy lets refusal rows read the production diagnostics.
A JSON number past an integer column's range answers from the end it lies past without
being converted, and past an integer transform's range it keeps its ``FILTER_INVALID``.
A set declaring no ``Meta.model`` refuses a leaf by naming the missing model, masked
under the default error policy, while its ``RelatedFilter`` branches still apply.
A list or range criterion over a duration or integer annotation of the queryset handed to
the set, or of a branch's target type's ``get_queryset``, is cleaned and compared as the
annotation's output field under ``apply_sync`` and ``apply_async`` alike. Complete fields
and values added by consumer cleaning acquire bind-only owners after the whole native
logical domain succeeds; only missing package inner parsers prepare before cleaning.
Raw ``.qs`` keeps safe sibling filtering on the same form when native errors suppress
uncached bind-only hooks. Permission gates precede annotation parser and bind preparation;
each owner is cached.
A leaf whose path starts at a ``FilteredRelation`` alias of the queryset the set filters, handed
to it or added by its ``filter_queryset``, walks the alias as a hop over the relations it joins
and reads each relation's visibility, its condition held by Django's own join; an alias only
``filter_queryset`` adds is not awaited before an async-only hook, which raises, and one joining
no relation is refused. A condition may read the queryset's annotations, but one reading a table
the alias's own joins would rebind is refused; a to-many alias key whose ``filter`` override
reads its own path, supplied or absent, answers over the visible rows.
"""

import asyncio
import copy
import datetime
import logging
import os
from collections.abc import Awaitable, Callable, Mapping
from functools import partial, wraps
from typing import TYPE_CHECKING, Annotated, ClassVar, NamedTuple, NoReturn

import pytest
import strawberry
from apps.library import models
from apps.library.filters import _validate_email_must_have_at_sign
from apps.products.services import create_users
from apps.scalars import models as scalar_models
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection
from django.db import models as django_models
from django.db.models import Lookup, Model, QuerySet
from django.db.models.functions import Abs, ExtractIsoYear, ExtractMonth, ExtractYear, Length
from django.forms import DurationField as FormDurationField
from django.forms import Field as FormField
from django.forms import Form, TextInput, Widget
from django.forms.utils import ErrorDict
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import AsyncClient, Client, override_settings
from django.test.utils import isolate_apps, register_lookup
from django.urls import path
from django_filters import (
    BaseInFilter,
    BaseRangeFilter,
    BooleanFilter,
    CharFilter,
    DateTimeFilter,
    DurationFilter,
    Filter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    NumberFilter,
)
from django_filters import RangeFilter as UpstreamRangeFilter
from graphql import GraphQLError
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_object,
    response_json,
)
from strategy_schemas import make_django_type
from typing_extensions import override

from django_strawberry_framework import DjangoSchema, finalize_django_types, strawberry_config
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    ArrayFilter,
    FilterSet,
    ListFilter,
    RangeField,
    RangeFilter,
    RelatedFilter,
)
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import (
    is_list_or_tuple,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._cleaned_filter_sets import cleaned_specimen
from tests._idioms import saved_pk

if TYPE_CHECKING:
    from django_strawberry_framework import DjangoType

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-apply-arguments/", _graphql_view),
    path("graphql-apply-arguments-async/", _async_graphql_view),
]


async def _async_post(
    document: str,
    variables: Mapping[str, object],
    client: AsyncClient | None,
) -> JSONObject:
    result = await AsyncTestClient(client=client).query(
        document,
        variables,
        assert_no_errors=False,
        url="/graphql-apply-arguments-async/",
    )
    assert result.response.status_code == 200
    return response_json(result.response)


def _post(
    schema: DjangoSchema,
    where: object,
    *,
    transport: str,
    selection: str = "name",
    optional: object = UNSET,
    optional_root: bool = False,
    client: Client | AsyncClient | None = None,
) -> JSONObject:
    root = "optionalRows" if optional_root else "rows"
    extra_declaration = ", $optional: JSON" if optional_root else ""
    extra_argument = ", optional: $optional" if optional_root else ""
    document = (
        f"query($where: JSON!{extra_declaration}) {{ "
        f"{root}(where: $where{extra_argument}) {{ {selection} }} }}"
    )
    variables: JSONObject = {"where": where}
    if optional is not UNSET:
        variables["optional"] = optional
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                assert client is None or isinstance(client, AsyncClient)
                return asyncio.run(_async_post(document, variables, client))
            assert client is None or isinstance(client, Client)
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-apply-arguments/",
                client=client,
            )
    finally:
        _CURRENT["schema"] = None


def _schema(
    filterset: type[FilterSet],
    model: type[Model],
    *,
    transport: str,
    fields: tuple[str, ...] = ("name",),
    targets: tuple[type["DjangoType"], ...] = (),
    resource_policy: Mapping[str, object] | None = None,
    direct: bool = False,
    masked: bool = False,
    annotated: Callable[[QuerySet[Model]], QuerySet[Model]] | None = None,
) -> DjangoSchema:
    output = make_django_type("RawCriteriaOutput", model, fields, node=False)

    def handed() -> QuerySet[Model]:
        queryset = model._default_manager.order_by("pk")
        return queryset if annotated is None else annotated(queryset)

    def resolve_rows(
        info: strawberry.Info[object, object],
        where: strawberry.scalars.JSON,
    ) -> QuerySet[Model]:
        queryset = handed()
        if direct:
            return filterset(data=json_object(where), queryset=queryset).qs
        return filterset.apply_sync(where, queryset, info)

    async def resolve_async_rows(
        info: strawberry.Info[object, object],
        where: strawberry.scalars.JSON,
    ) -> list[Model]:
        queryset = await filterset.apply_async(where, handed(), info)
        return await sync_to_async(list)(queryset)

    def resolve_optional_rows(
        info: strawberry.Info[object, object],
        where: strawberry.scalars.JSON,
        optional: Annotated[
            object,
            strawberry.argument(graphql_type=strawberry.scalars.JSON | None),
        ] = UNSET,
    ) -> QuerySet[Model]:
        return filterset.apply_sync(
            {"or_": [where, optional]},
            model._default_manager.order_by("pk"),
            info,
        )

    async def resolve_async_optional_rows(
        info: strawberry.Info[object, object],
        where: strawberry.scalars.JSON,
        optional: Annotated[
            object,
            strawberry.argument(graphql_type=strawberry.scalars.JSON | None),
        ] = UNSET,
    ) -> list[Model]:
        queryset = await filterset.apply_async(
            {"or_": [where, optional]},
            model._default_manager.order_by("pk"),
            info,
        )
        return await sync_to_async(list)(queryset)

    @strawberry.type
    class Query:
        rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_rows if transport == "async" else resolve_rows,
            graphql_type=list[output],
        )
        optional_rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_optional_rows
            if transport == "async"
            else resolve_optional_rows,
            graphql_type=list[output],
        )

    finalize_django_types()
    return DjangoSchema(
        query=Query,
        types=targets,
        config=strawberry_config(),
        error_policy=None if masked else {"enabled": False},
        resource_policy=resource_policy,
    )


def _refused(
    payload: JSONObject,
    message: str,
    *,
    root: str = "rows",
    extensions: JSONObject | None = None,
) -> None:
    error: JSONObject = {
        "message": message,
        "locations": [{"line": 1, "column": 24}],
        "path": [root],
    }
    if extensions is not None:
        error["extensions"] = extensions
    assert payload == {"data": None, "errors": [error]}, payload


def _generated_raw_filter() -> tuple[type[Model], type[FilterSet]]:
    """An unserved set with generated unsupported outputs and an ordinary duration column."""
    meta = type("Meta", (), {"app_label": "scalars", "managed": False})
    row = type(
        "GeneratedRawRow",
        (Model,),
        {
            "__module__": __name__,
            "name": django_models.TextField(),
            "plain": django_models.DurationField(),
            "starts_at": django_models.DateTimeField(),
            "ends_at": django_models.DateTimeField(),
            "elapsed": django_models.GeneratedField(
                expression=django_models.F("ends_at") - django_models.F("starts_at"),
                output_field=django_models.DurationField(),
                db_persist=True,
            ),
            "file": django_models.GeneratedField(
                expression=django_models.Value("file"),
                output_field=django_models.FileField(),
                db_persist=True,
            ),
            "Meta": meta,
        },
    )
    filter_meta = type("Meta", (), {"model": row, "fields": []})
    filterset = type(
        "GeneratedRawFilter",
        (FilterSet,),
        {
            "elapsed": DurationFilter(field_name="elapsed"),
            "file": CharFilter(field_name="file"),
            "null_elapsed": BooleanFilter(field_name="elapsed", lookup_expr="isnull"),
            "plain": DurationFilter(field_name="plain"),
            "Meta": filter_meta,
        },
    )
    return row, filterset


@pytest.mark.django_db
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("where", "field"),
    [
        ({"elapsed": {"exact": "00:00:01"}}, "DurationField"),
        ({"file": {"exact": {"x": 1}}}, "FileField"),
        ({"null_elapsed": {"isnull": True}}, "DurationField"),
    ],
    ids=["scalar", "object", "null-test"],
)
@isolate_apps("apps.scalars")
def test_unserved_generated_source_policy_refuses_json_over_http(
    where: JSONObject,
    field: str,
    transport: str,
) -> None:
    """An active raw JSON leaf gets its declaring FilterSet refusal before form dispatch."""
    row, filterset = _generated_raw_filter()
    schema = _schema(
        filterset,
        row,
        transport=transport,
        fields=("name",),
        annotated=lambda qs: qs.none(),
    )
    ordinary = _post(schema, {"plain": {"exact": "00:00:01"}}, transport=transport)
    assert ordinary == {"data": {"rows": []}}, ordinary
    payload = _post(schema, where, transport=transport)
    assert payload["data"] is None, payload
    message = json_at(payload, "errors", 0, "message")
    assert isinstance(message, str)
    assert message.startswith("GeneratedRawFilter: "), message
    assert f"GeneratedRawRow.{'file' if field == 'FileField' else 'elapsed'}, a {field}" in message
    assert "Meta.exclude" not in message


@pytest.mark.django_db
@isolate_apps("apps.scalars")
def test_direct_raw_generated_filter_refuses_and_ordinary_duration_still_builds() -> None:
    """Direct ``FilterSet(data=...).qs`` applies the same generated-only policy."""
    row, filterset = _generated_raw_filter()
    schema = _schema(
        filterset,
        row,
        transport="sync",
        fields=("name",),
        direct=True,
        annotated=lambda qs: qs.none(),
    )
    ordinary = _post(schema, {"plain": "00:00:01"}, transport="sync")
    assert ordinary == {"data": {"rows": []}}, ordinary
    refused = _post(schema, {"elapsed": "00:00:01"}, transport="sync")
    assert refused["data"] is None, refused
    message = json_at(refused, "errors", 0, "message")
    assert isinstance(message, str)
    assert "GeneratedRawFilter: DurationFilter on 'elapsed'" in message
    assert "register DurationField" in message


def _branch_filter() -> type[FilterSet]:
    class CriteriaBranchFilter(FilterSet):
        class Meta:
            model = models.Branch
            fields = {"name": ["exact", "icontains"]}

    return CriteriaBranchFilter


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_consumer_dict_operator_bag_narrows_the_root_rows(transport: str) -> None:
    models.Branch.objects.create(name="alpha-match")
    models.Branch.objects.create(name="beta")
    schema = _schema(_branch_filter(), models.Branch, transport=transport)
    assert _post(schema, {"name": {"i_contains": "match"}}, transport=transport) == {
        "data": {"rows": [{"name": "alpha-match"}]},
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("inactive", [None, UNSET], ids=["null", "omitted"])
def test_an_inactive_optional_or_arm_does_not_widen_its_real_sibling(
    transport: str,
    inactive: object,
) -> None:
    models.Branch.objects.create(name="alpha")
    models.Branch.objects.create(name="beta")
    schema = _schema(_branch_filter(), models.Branch, transport=transport)
    assert _post(
        schema,
        {"name": {"exact": "alpha"}},
        transport=transport,
        optional=inactive,
        optional_root=True,
    ) == {"data": {"optionalRows": [{"name": "alpha"}]}}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_present_optional_or_arm_still_contributes_its_matching_rows(transport: str) -> None:
    models.Branch.objects.create(name="alpha")
    models.Branch.objects.create(name="beta")
    schema = _schema(_branch_filter(), models.Branch, transport=transport)
    assert _post(
        schema,
        {"name": {"exact": "alpha"}},
        transport=transport,
        optional={"name": {"exact": "beta"}},
        optional_root=True,
    ) == {"data": {"optionalRows": [{"name": "alpha"}, {"name": "beta"}]}}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("depth", ["root", "and"], ids=["root", "logical-arm"])
def test_an_unknown_json_filter_key_is_refused_at_each_input_depth(
    transport: str,
    depth: str,
) -> None:
    models.Branch.objects.create(name="must not be returned")
    filterset = _branch_filter()
    value: JSONObject = {"nope": "x"}
    if depth == "and":
        value = {"and_": [value]}
    schema = _schema(filterset, models.Branch, transport=transport)
    _refused(
        _post(schema, value, transport=transport),
        f"FilterSet {filterset.__qualname__}: 'nope' is not a filter input field; "
        "it would apply nothing.",
    )


def _model_less_branch_filter() -> type[FilterSet]:
    class ChildShelfCodeFilter(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class ModelLessBranchFilter(FilterSet):
        name = CharFilter(field_name="name")
        shelves = RelatedFilter(ChildShelfCodeFilter, field_name="shelves")

    return ModelLessBranchFilter


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("masked", [False, True], ids=["pass-through", "masked"])
def test_a_leaf_of_an_unbound_set_declaring_no_meta_model_is_refused_by_its_missing_model(
    *,
    transport: str,
    masked: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A leaf resolves against the set's ``Meta.model``, so a model-less set applies none.

    The refusal names the missing ``Meta.model`` rather than calling a declared filter
    unknown. A pass-through error policy puts it on the wire; the default policy without
    ``DEBUG`` answers the masked message and its correlation id while the log keeps the
    refusal.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    models.Branch.objects.create(name="must not be returned")
    filterset = _model_less_branch_filter()
    schema = _schema(filterset, models.Branch, transport=transport, masked=masked)
    message = (
        f"FilterSet {filterset.__qualname__}: 'name' cannot apply: the set declares no "
        "Meta.model, which every leaf filter resolves against. Declare Meta.model on the "
        "set, or apply a subclass that declares it."
    )
    payload = _post(schema, {"name": "must not be returned"}, transport=transport)
    if not masked:
        _refused(payload, message)
        return
    correlation_id = json_at(payload, "errors", 0, "extensions", "correlationId")
    assert isinstance(correlation_id, str), payload
    _refused(
        payload,
        "An unexpected error occurred.",
        extensions={"correlationId": correlation_id},
    )
    [logged] = [
        record.exc_info
        for record in caplog.records
        if record.name == "django_strawberry_framework" and record.exc_info is not None
    ]
    assert isinstance(logged[1], ConfigurationError), logged
    assert str(logged[1]) == message


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_branch_of_an_unbound_set_declaring_no_meta_model_still_narrows_the_rows(
    transport: str,
) -> None:
    """A ``RelatedFilter`` branch resolves on its child set's model, so it applies."""
    alpha = models.Branch.objects.create(name="alpha")
    models.Shelf.objects.create(code="a1", branch=alpha)
    beta = models.Branch.objects.create(name="beta")
    models.Shelf.objects.create(code="b1", branch=beta)
    schema = _schema(
        _model_less_branch_filter(),
        models.Branch,
        transport=transport,
        targets=(make_django_type("ShelfTarget", models.Shelf, ("code",), node=False),),
    )
    assert _post(schema, {"shelves": {"code": {"exact": "b1"}}}, transport=transport) == {
        "data": {"rows": [{"name": "beta"}]},
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("value", "description"),
    [("name", "str ('name')"), ([{"name": "foo"}], "list ([{'name': 'foo'}])")],
    ids=["scalar", "top-level-list"],
)
def test_a_scalar_json_filter_input_is_refused_before_any_row_is_served(
    transport: str,
    value: object,
    description: str,
) -> None:
    models.Branch.objects.create(name="must not be returned")
    filterset = _branch_filter()
    schema = _schema(filterset, models.Branch, transport=transport)
    _refused(
        _post(schema, value, transport=transport),
        f"FilterSet {filterset.__qualname__}: the filter input must be a mapping or a "
        f"filter-input object, got a {description}. A non-walkable input would silently "
        "drop every predicate and skip every check_* permission gate.",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("value", "rendered"),
    [
        ({"exact": {"k": "v"}}, "{'k': 'v'}"),
        ({"nope": "x"}, "{'nope': 'x'}"),
        ({"in": ["foo"]}, "{'in': ['foo']}"),
    ],
    ids=["dict-under-exact", "unknown-bag-key", "wire-in-is-not-python-key"],
)
def test_a_dict_under_a_scalar_lookup_is_refused_without_losing_its_field(
    transport: str,
    value: JSONObject,
    rendered: str,
) -> None:
    models.Branch.objects.create(name="must not be returned")
    filterset = _branch_filter()
    schema = _schema(filterset, models.Branch, transport=transport)
    _refused(
        _post(schema, {"name": value}, transport=transport),
        f"FilterSet {filterset.__qualname__}: filter 'name' received a dict value "
        f"({rendered}) but CharFilter consumes a single scalar form key. A dict value here "
        "would be splatted into unknown form-data keys the form silently ignores, dropping "
        "the filter. Pass the schema value shape for this filter (a scalar, a list, or a "
        "range {start, end} input on a RangeFilter primitive).",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_dict_under_a_choice_lookup_is_refused_without_losing_its_field(transport: str) -> None:
    """A leaf whose input is no ``JSON`` value refuses an object, as a ``CharFilter`` does.

    ``condition`` is a choices column, so its ``exact`` leaf is an ``EnumChoiceFilter``,
    published as the column's enum: an object reaching it through a consumer ``JSON``
    argument is never one value to bind whole.
    """

    class CriteriaShelfFilter(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"condition": ["exact"]}

    branch = models.Branch.objects.create(name="east")
    models.Shelf.objects.create(code="must not be returned", branch=branch)
    schema = _schema(CriteriaShelfFilter, models.Shelf, transport=transport, fields=("code",))
    _refused(
        _post(schema, {"condition": {"exact": {"k": "v"}}}, transport=transport, selection="code"),
        f"FilterSet {CriteriaShelfFilter.__qualname__}: filter 'condition' received a dict value "
        "({'k': 'v'}) but EnumChoiceFilter consumes a single scalar form key. A dict value here "
        "would be splatted into unknown form-data keys the form silently ignores, dropping "
        "the filter. Pass the schema value shape for this filter (a scalar, a list, or a "
        "range {start, end} input on a RangeFilter primitive).",
    )


def _fines_sets() -> tuple[type[FilterSet], type[FilterSet]]:
    class FinesWindowFilter(FilterSet):
        fines = RangeFilter(field_name="lifetime_fines_cents", lookup_expr="range")

        class Meta:
            model = models.Patron
            fields = []

    class FinesWindowLoanFilter(FilterSet):
        patron = RelatedFilter(FinesWindowFilter, field_name="patron")

        class Meta:
            model = models.Loan
            fields = []

    return FinesWindowFilter, FinesWindowLoanFilter


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    "depth",
    ["root", "and", "patron"],
    ids=["root", "logical-arm", "related"],
)
@pytest.mark.parametrize(
    ("value", "received"),
    [
        ({"rnage": {"start": 1, "end": 5}}, "dict {'rnage': {'start': 1, 'end': 5}}"),
        ({"range": [1, 5]}, "list [1, 5]"),
        ([1, 5], "list [1, 5]"),
        ({"start": 1, "zzz": 5}, "dict {'start': 1, 'zzz': 5}"),
    ],
    ids=[
        "misspelled-lookup",
        "list-in-lookup",
        "bare-list",
        "mixed-known-unknown-axis",
    ],
)
def test_a_malformed_range_argument_is_refused_at_every_public_input_depth(
    transport: str,
    depth: str,
    value: object,
    received: str,
) -> None:
    models.Patron.objects.create(name="must not be returned", email="p@example.test")
    patron_filter, loan_filter = _fines_sets()
    target = patron_filter
    root_model: type[Model] = models.Patron
    selection = "name"
    where: JSONObject = {"fines": value}
    targets: tuple[type[DjangoType], ...] = ()
    if depth == "and":
        where = {"and_": [where]}
    elif depth == "patron":
        target = loan_filter
        root_model = models.Loan
        selection = "id"
        targets = (make_django_type("PatronTarget", models.Patron, ("name",), node=False),)
        where = {"patron": where}
    schema = _schema(target, root_model, transport=transport, fields=(selection,), targets=targets)
    _refused(
        _post(schema, where, transport=transport, selection=selection),
        "RangeFilter consumes a range input with only 'start' / 'end' axes for its 'fines' "
        f"input, but received {received}; send a mapping or input object with 'start' / 'end' "
        "(generated filter inputs reject this shape during GraphQL validation).",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_valid_range_argument_keeps_only_the_admitted_patron(transport: str) -> None:
    models.Patron.objects.create(name="inside", email="in@example.test", lifetime_fines_cents=3)
    models.Patron.objects.create(name="outside", email="out@example.test", lifetime_fines_cents=9)
    patron_filter, _loan_filter = _fines_sets()
    schema = _schema(patron_filter, models.Patron, transport=transport)
    assert _post(
        schema,
        {"fines": {"start": 1, "end": 5}},
        transport=transport,
    ) == {"data": {"rows": [{"name": "inside"}]}}


_PAST_ANY_INTEGER = "-1e999999999999999999"


class _SignedBigCriteriaSet(FilterSet):
    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = {"signed_big": ["gte", "in"], "occurred_on": ["year__gt"]}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("where", "labels"),
    [
        pytest.param(
            {"signed_big": {"gte": _PAST_ANY_INTEGER}},
            ["kept", "other"],
            id="gte-below",
        ),
        pytest.param(
            {"signed_big": {"in_": [_PAST_ANY_INTEGER, "7"]}},
            ["kept"],
            id="in-member-below",
        ),
    ],
)
def test_a_json_number_past_an_integer_column_answers_without_being_converted(
    transport: str,
    where: JSONObject,
    labels: list[str],
) -> None:
    """``-1e999999999999999999`` cleans to a decimal no ``int()`` finishes; it is read by its side."""
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    schema = _schema(
        _SignedBigCriteriaSet,
        scalar_models.ScalarSpecimen,
        transport=transport,
        fields=("label",),
    )
    assert _post(schema, where, transport=transport, selection="label") == {
        "data": {"rows": [{"label": label} for label in labels]},
    }


class _CustomizedSignedBigCriteriaSet(_SignedBigCriteriaSet):
    """A child whose ``__init__`` override projects its leaves onto a parent as owned copies."""

    parent_year_after = NumberFilter(field_name="parent__occurred_on", lookup_expr="year__gt")

    @override
    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)


class _PartnerSignedBigCriteriaSet(FilterSet):
    partner = RelatedFilter(_CustomizedSignedBigCriteriaSet, field_name="partner")

    class Meta:
        model = scalar_models.NullableScalarSpecimen
        fields = []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("where", "labels"),
    [
        pytest.param(
            {"partner__signed_big": {"in_": [_PAST_ANY_INTEGER, "7"]}},
            ["with-kept"],
            id="column",
        ),
    ],
)
def test_a_json_number_past_a_projected_integer_leaf_answers_without_being_converted(
    transport: str,
    where: JSONObject,
    labels: list[str],
) -> None:
    """A projected ``partner__signed_big`` copy is held to its column's range on the child's queryset."""
    kept = cleaned_specimen("kept", kept=True)
    other = cleaned_specimen("other", kept=False)
    scalar_models.NullableScalarSpecimen.objects.create(label="with-kept", partner=kept)
    scalar_models.NullableScalarSpecimen.objects.create(label="with-other", partner=other)
    scalar_models.NullableScalarSpecimen.objects.create(label="without-partner", partner=None)
    schema = _schema(
        _PartnerSignedBigCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(
            make_django_type(
                "PartnerTarget",
                scalar_models.ScalarSpecimen,
                ("label",),
                node=False,
            ),
        ),
    )
    assert _post(schema, where, transport=transport, selection="label") == {
        "data": {"rows": [{"label": label} for label in labels]},
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_json_year_past_a_projected_leafs_range_is_refused_over_the_childs_queryset(
    transport: str,
) -> None:
    """A projected ``year`` across the child's own ``parent`` hop is asked on the child's queryset.

    ``parent`` is no relation of the parent set's model, so the copy is held and asked
    only where its path resolves; past the transform's range it is ``FILTER_INVALID``.
    """
    scalar_models.NullableScalarSpecimen.objects.create(
        label="with-kept",
        partner=cleaned_specimen("kept", kept=True),
    )
    schema = _schema(
        _PartnerSignedBigCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(
            make_django_type(
                "PartnerTarget",
                scalar_models.ScalarSpecimen,
                ("label",),
                node=False,
            ),
        ),
    )
    _refused(
        _post(
            schema,
            {"partner__parent_year_after": {"year_gt": _PAST_ANY_INTEGER}},
            transport=transport,
            selection="label",
        ),
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {
                "partner__parent_year_after": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
        },
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_json_year_past_the_transforms_range_keeps_its_refusal(transport: str) -> None:
    """A ``year`` bound past its integer range is refused as the database cannot bind it, at once."""
    cleaned_specimen("kept", kept=True)
    schema = _schema(
        _SignedBigCriteriaSet,
        scalar_models.ScalarSpecimen,
        transport=transport,
        fields=("label",),
    )
    _refused(
        _post(
            schema,
            {"occurred_on": {"year_gt": _PAST_ANY_INTEGER}},
            transport=transport,
            selection="label",
        ),
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {
                "occurred_on__year__gt": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
        },
    )


class _AnnotationCriteriaSet(FilterSet):
    lag_among = ListFilter(field_name="lag", lookup_expr="in")
    lag_span = RangeFilter(field_name="lag", lookup_expr="range")
    kids_among = ListFilter(field_name="kids", lookup_expr="in")
    kids_span = RangeFilter(field_name="kids", lookup_expr="range")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    (
        "source_kind",
        "where",
        "labels",
        "invalid_field",
    ),
    [
        (
            "year-annotate",
            {"after": {"gte": 99999}},
            None,
            "after",
        ),
        (
            "year-alias",
            {"at": {"exact": 99999}},
            None,
            "at",
        ),
        (
            "year-alias",
            {"span": {"start": 2000, "end": 99999}},
            None,
            "span",
        ),
        (
            "year-alias",
            {"span": {"start": 99999}},
            None,
            "span",
        ),
        (
            "year-alias",
            {"span": {"end": 99999}},
            None,
            "span",
        ),
        (
            "iso-alias",
            {"span": {"start": 2000, "end": 99999}},
            None,
            "span",
        ),
        (
            "year-alias",
            {"span": {"start": 2000, "end": 2026}},
            ["kept"],
            None,
        ),
        (
            "year-alias",
            {"members": {"in_": [2026, 99999]}},
            ["kept"],
            None,
        ),
        (
            "month-alias",
            {"span": {"start": 0, "end": 99999}},
            ["kept"],
            None,
        ),
        (
            "month-alias",
            {"members": {"in_": [1]}},
            ["kept"],
            None,
        ),
        (
            "month-alias",
            {"members": {"in_": [999999999999999999999]}},
            None,
            "members",
        ),
        (
            "month-alias",
            {"members": {"in_": [1, 999999999999999999999]}},
            None,
            "members",
        ),
        (
            "month-alias",
            {"array_members": {"in_": [999999999999999999999]}},
            None,
            "array_members",
        ),
        (
            "month-alias",
            {"array_members": {"in_": [1, 999999999999999999999]}},
            None,
            "array_members",
        ),
        (
            "month-alias",
            {"array_members": {"in_": [1]}},
            ["kept"],
            None,
        ),
        (
            "integer-alias",
            {"members": {"in_": [999999999999999999999]}},
            [],
            None,
        ),
        (
            "integer-alias",
            {"span": {"start": 0, "end": 99999}},
            ["kept"],
            None,
        ),
        (
            "count-alias",
            {"members": {"in_": [999999999999999999999]}},
            [],
            None,
        ),
    ],
)
def test_expression_alias_bind_asks_follow_the_actual_shipped_predicate(
    transport: str,
    source_kind: str,
    where: JSONObject,
    labels: list[str] | None,
    invalid_field: str | None,
) -> None:
    cleaned_specimen("kept", kept=True)

    class AliasSet(FilterSet):
        after = NumberFilter(field_name="stamp_value", lookup_expr="gte")
        at = NumberFilter(field_name="stamp_value", lookup_expr="exact")
        span = RangeFilter(field_name="stamp_value", lookup_expr="range")
        members = ListFilter(field_name="stamp_value", lookup_expr="in")
        array_members = ArrayFilter(field_name="stamp_value", lookup_expr="in")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    def with_alias(rows: QuerySet[Model]) -> QuerySet[Model]:
        expression = (
            ExtractYear("occurred_on")
            if source_kind.startswith("year")
            else ExtractIsoYear("occurred_on")
            if source_kind == "iso-alias"
            else ExtractMonth("occurred_on")
            if source_kind == "month-alias"
            else django_models.Count("children")
            if source_kind == "count-alias"
            else django_models.F("signed_big")
        )
        if source_kind == "year-annotate":
            return rows.annotate(stamp_value=expression)
        return rows.alias(stamp_value=expression)

    schema = _schema(
        AliasSet,
        scalar_models.ScalarSpecimen,
        transport=transport,
        fields=("label",),
        annotated=with_alias,
    )
    payload = _post(schema, where, transport=transport, selection="label")
    if invalid_field is None:
        assert payload == {"data": {"rows": [{"label": label} for label in labels or []]}}, payload
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    invalid_field: [
                        {
                            "message": "Enter a value the database can represent.",
                            "code": "invalid",
                        },
                    ],
                },
            },
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "source_kind",
        "query_string",
        "invalid_field",
        "ordinary_error",
        "labels",
    ),
    [
        (
            "year",
            "p-after=99999&p-label=kept&p-bad_number=abc",
            "after",
            True,
            ["kept"],
        ),
        (
            "year",
            "p-at=99999&p-label=kept",
            "at",
            False,
            ["kept"],
        ),
        (
            "year",
            "p-span_0=2000&p-span_1=99999&p-label=kept",
            "span",
            False,
            ["kept"],
        ),
        (
            "year",
            "p-span_0=99999&p-label=kept",
            "span",
            False,
            ["kept"],
        ),
        (
            "year",
            "p-span_1=99999&p-label=kept",
            "span",
            False,
            ["kept"],
        ),
        (
            "iso",
            "p-span_0=2000&p-span_1=99999&p-label=kept",
            "span",
            False,
            ["kept"],
        ),
        (
            "year",
            "p-native_span=2000,99999&p-label=kept",
            None,
            False,
            ["kept"],
        ),
        (
            "year",
            "p-members=2026,99999&p-label=kept",
            None,
            False,
            ["kept"],
        ),
        (
            "month",
            "p-span_0=0&p-span_1=99999&p-label=kept",
            None,
            False,
            ["kept"],
        ),
        (
            "month",
            "p-members=999999999999999999999&p-label=kept",
            "members",
            False,
            ["kept"],
        ),
        (
            "month",
            "p-members=1,999999999999999999999&p-label=kept",
            "members",
            False,
            ["kept"],
        ),
        (
            "month",
            "p-array_members=999999999999999999999&p-label=kept",
            "array_members",
            False,
            ["kept"],
        ),
        (
            "month",
            "p-array_members=1,999999999999999999999&p-label=kept",
            "array_members",
            False,
            ["kept"],
        ),
        (
            "month",
            "p-array_members=1&p-label=kept",
            None,
            False,
            ["kept"],
        ),
        (
            "month",
            "p-native_members=999999999999999999999&p-label=kept",
            "native_members",
            False,
            ["kept"],
        ),
        (
            "integer",
            "p-members=999999999999999999999&p-label=kept",
            None,
            False,
            [],
        ),
        (
            "count",
            "p-members=999999999999999999999&p-label=kept",
            None,
            False,
            [],
        ),
    ],
)
def test_raw_expression_alias_bind_errors_preserve_good_siblings(
    source_kind: str,
    query_string: str,
    invalid_field: str | None,
    *,
    ordinary_error: bool,
    labels: list[str],
) -> None:
    cleaned_specimen("kept", kept=True)

    class NativeNumberRange(BaseRangeFilter, NumberFilter):
        """django-filter's CSV range keeps its one native numeric predicate."""

    class NativeNumberIn(BaseInFilter, NumberFilter):
        """django-filter's CSV membership binds each numeric transform member."""

    class AliasSet(FilterSet):
        after = NumberFilter(field_name="stamp_value", lookup_expr="gte")
        at = NumberFilter(field_name="stamp_value", lookup_expr="exact")
        span = RangeFilter(field_name="stamp_value", lookup_expr="range")
        native_span = NativeNumberRange(field_name="stamp_value", lookup_expr="range")
        native_members = NativeNumberIn(field_name="stamp_value", lookup_expr="in")
        members = ListFilter(field_name="stamp_value", lookup_expr="in")
        array_members = ArrayFilter(field_name="stamp_value", lookup_expr="in")
        label = CharFilter(field_name="label")
        bad_number = NumberFilter(field_name="signed_big")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            rows = scalar_models.ScalarSpecimen.objects.order_by("label")
            expression = (
                ExtractYear("occurred_on")
                if source_kind == "year"
                else ExtractIsoYear("occurred_on")
                if source_kind == "iso"
                else ExtractMonth("occurred_on")
                if source_kind == "month"
                else django_models.Count("children")
                if source_kind == "count"
                else django_models.F("signed_big")
            )
            instance = AliasSet(
                data=QueryDict(query_string),
                queryset=rows.alias(stamp_value=expression),
                prefix="p",
            )
            errors = require_instance(instance.errors, ErrorDict).get_json_data()
            valid = instance.is_valid()
            return {
                "errors": errors,
                "valid": valid,
                "labels": list(instance.qs.values_list("label", flat=True)),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    errors: JSONObject = {}
    if invalid_field is not None:
        errors[invalid_field] = [
            {"message": "Enter a value the database can represent.", "code": "invalid"},
        ]
    if ordinary_error:
        errors["bad_number"] = [{"message": "Enter a number.", "code": "invalid"}]
    assert payload == {
        "data": {
            "answer": {"errors": errors, "valid": not errors, "labels": labels},
        },
    }, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    (
        "source_kind",
        "where",
        "labels",
        "invalid_field",
    ),
    [
        (
            "year",
            {"after": {"gte": 99999}},
            None,
            "after",
        ),
        (
            "year",
            {"span": {"start": 2000, "end": 99999}},
            None,
            "span",
        ),
        (
            "year",
            {"span": {"end": 99999}},
            None,
            "span",
        ),
        (
            "year",
            {"span": {"start": 2000, "end": 2026}},
            ["of-child"],
            None,
        ),
        (
            "month",
            {"members": {"in_": [999999999999999999999]}},
            None,
            "members",
        ),
        (
            "month",
            {"members": {"in_": [1]}},
            ["of-child"],
            None,
        ),
        (
            "integer",
            {"span": {"start": 0, "end": 999999999999999999999}},
            ["of-child"],
            None,
        ),
        (
            "integer",
            {"span": {"start": 999999999999999999999, "end": 999999999999999999999}},
            [],
            None,
        ),
    ],
)
def test_scoped_integer_expression_uses_its_actual_source_for_bind_and_range(
    transport: str,
    source_kind: str,
    where: JSONObject,
    labels: list[str] | None,
    invalid_field: str | None,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class ScopedSet(FilterSet):
        after = NumberFilter(field_name="partner__stamp_value", lookup_expr="gte")
        span = RangeFilter(field_name="partner__stamp_value", lookup_expr="range")
        members = ListFilter(field_name="partner__stamp_value", lookup_expr="in")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        expression = (
            ExtractYear("occurred_on")
            if source_kind == "year"
            else ExtractMonth("occurred_on")
            if source_kind == "month"
            else django_models.F("signed_big")
        )
        return rows.alias(stamp_value=expression)

    target = make_django_type(
        "ScopedIntegerExpressionTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )
    schema = _schema(
        ScopedSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    recorded = record_compiled_sql()
    payload = _post(schema, where, transport=transport, selection="label")
    if invalid_field is None:
        assert payload == {"data": {"rows": [{"label": label} for label in labels or []]}}, payload
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    invalid_field: [
                        {
                            "message": "Enter a value the database can represent.",
                            "code": "invalid",
                        },
                    ],
                },
            },
        )
        assert recorded == [], recorded
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "source_kind",
        "query_string",
        "invalid_field",
        "labels",
    ),
    [
        (
            "year",
            "p-after=99999&p-label=of-child",
            "after",
            ["of-child"],
        ),
        (
            "year",
            "p-span_0=2000&p-span_1=99999&p-label=of-child",
            "span",
            ["of-child"],
        ),
        (
            "year",
            "p-span_1=99999&p-label=of-child",
            "span",
            ["of-child"],
        ),
        (
            "year",
            "p-native_span=2000,99999&p-label=of-child",
            None,
            ["of-child"],
        ),
        (
            "month",
            "p-members=999999999999999999999&p-label=of-child",
            "members",
            ["of-child"],
        ),
        (
            "month",
            "p-array_members=999999999999999999999&p-label=of-child",
            "array_members",
            ["of-child"],
        ),
        (
            "month",
            "p-native_members=999999999999999999999&p-label=of-child",
            "native_members",
            ["of-child"],
        ),
        (
            "month",
            "p-members=1&p-label=of-child",
            None,
            ["of-child"],
        ),
        (
            "integer",
            "p-span_0=0&p-span_1=999999999999999999999&p-label=of-child",
            None,
            ["of-child"],
        ),
        (
            "integer",
            "p-span_0=999999999999999999999&p-span_1=999999999999999999999&p-label=of-child",
            None,
            [],
        ),
        (
            "integer",
            "p-members=999999999999999999999&p-label=of-child",
            None,
            [],
        ),
    ],
)
def test_raw_scoped_integer_expression_reuses_the_source_for_errors_and_qs(
    source_kind: str,
    query_string: str,
    invalid_field: str | None,
    labels: list[str],
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class NativeNumberRange(BaseRangeFilter, NumberFilter):
        """Keep the shipped CSV range as one numeric predicate."""

    class NativeNumberIn(BaseInFilter, NumberFilter):
        """Keep the shipped CSV membership parser."""

    class ScopedSet(FilterSet):
        after = NumberFilter(field_name="partner__stamp_value", lookup_expr="gte")
        span = RangeFilter(field_name="partner__stamp_value", lookup_expr="range")
        native_span = NativeNumberRange(field_name="partner__stamp_value", lookup_expr="range")
        members = ListFilter(field_name="partner__stamp_value", lookup_expr="in")
        array_members = ArrayFilter(field_name="partner__stamp_value", lookup_expr="in")
        native_members = NativeNumberIn(field_name="partner__stamp_value", lookup_expr="in")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        expression = (
            ExtractYear("occurred_on")
            if source_kind == "year"
            else ExtractMonth("occurred_on")
            if source_kind == "month"
            else django_models.F("signed_big")
        )
        return rows.alias(stamp_value=expression)

    target = make_django_type(
        "RawScopedIntegerExpressionTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            rows = scalar_models.NullableScalarSpecimen.objects.order_by("label")
            instance = ScopedSet(data=QueryDict(query_string), queryset=rows, prefix="p")
            errors = require_instance(instance.errors, ErrorDict).get_json_data()
            valid = instance.is_valid()
            return {
                "errors": errors,
                "valid": valid,
                "labels": list(instance.qs.values_list("label", flat=True)),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    errors: JSONObject = {}
    if invalid_field is not None:
        errors[invalid_field] = [
            {"message": "Enter a value the database can represent.", "code": "invalid"},
        ]
    assert payload == {
        "data": {
            "answer": {"errors": errors, "valid": not errors, "labels": labels},
        },
    }, payload
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("family", ["package-list", "native-csv"])
def test_registered_integer_transform_with_same_output_field_asks_its_member_bind(
    transport: str,
    family: str,
) -> None:
    cleaned_specimen("kept", kept=True)

    class NativeNumberIn(BaseInFilter, NumberFilter):
        """Keep django-filter's native CSV member preparation."""

    with register_lookup(django_models.BigIntegerField, Abs):

        class AbsSet(FilterSet):
            magnitude_members = (
                ListFilter(field_name="signed_big", lookup_expr="abs__in")
                if family == "package-list"
                else NativeNumberIn(field_name="signed_big", lookup_expr="abs__in")
            )

            class Meta:
                model = scalar_models.ScalarSpecimen
                fields = []

        schema = _schema(
            AbsSet,
            scalar_models.ScalarSpecimen,
            transport=transport,
            fields=("label",),
        )
        refused = _post(
            schema,
            {"magnitude_members": [999999999999999999999]},
            transport=transport,
            selection="label",
        )
        _refused(
            refused,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "magnitude_members": [
                        {
                            "message": "Enter a value the database can represent.",
                            "code": "invalid",
                        },
                    ],
                },
            },
        )
        accepted = _post(
            schema,
            {"magnitude_members": [7]},
            transport=transport,
            selection="label",
        )
        assert accepted == {"data": {"rows": [{"label": "kept"}]}}, accepted


def _with_annotations(rows: QuerySet[Model]) -> QuerySet[Model]:
    """The duration since the parent's stamp and the count of children, as a resolver adds them."""
    return rows.annotate(
        lag=django_models.ExpressionWrapper(
            django_models.F("occurred_at") - django_models.F("parent__occurred_at"),
            output_field=django_models.DurationField(),
        ),
        kids=django_models.Count("children"),
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("where", "answer"),
    [
        pytest.param({"lag_among": {"in_": ["1 00:00:00"]}}, ["child"], id="duration-member"),
        pytest.param(
            {"lag_span": {"start": "12:00:00", "end": "2 00:00:00"}},
            ["child"],
            id="duration-range",
        ),
        pytest.param({"kids_among": {"in_": ["1", "1.5", str(2**63)]}}, ["kept"], id="integer"),
        pytest.param(
            {"kids_span": {"start": str(-(2**63) - 1), "end": "0"}},
            ["child"],
            id="integer-range-below-the-column",
        ),
        pytest.param(
            {"lag_among": {"in_": ["abc"]}},
            {"lag_among": [{"message": "Enter a valid duration.", "code": "invalid"}]},
            id="duration-junk",
        ),
        pytest.param(
            {"lag_span": {"end": "1000000000 00:00:00"}},
            {
                "lag_span": [
                    {
                        "message": "The number of days must be between -999999999 and 999999999.",
                        "code": "overflow",
                    },
                ],
            },
            id="duration-past-timedelta",
        ),
        pytest.param(
            {"kids_span": {"start": "abc"}},
            {"kids_span": [{"message": "Enter a number.", "code": "invalid"}]},
            id="integer-junk",
        ),
    ],
)
def test_a_criterion_over_a_queryset_annotation_is_cleaned_as_the_annotation_compares(
    transport: str,
    where: JSONObject,
    answer: list[str] | JSONObject,
) -> None:
    """``apply_sync`` and ``apply_async`` clean a value over an annotation as its output field.

    ``lag`` is a ``DurationField`` expression and ``kids`` a ``Count`` the resolver adds to
    the queryset it hands the set: a duration member compares as one, an integer member
    naming no row drops, a range bound past the column widens, and junk or a duration past
    ``timedelta`` is ``FILTER_INVALID`` keyed to the filter, on either executor.
    """
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    schema = _schema(
        _AnnotationCriteriaSet,
        scalar_models.ScalarSpecimen,
        transport=transport,
        fields=("label",),
        annotated=_with_annotations,
    )
    payload = _post(schema, where, transport=transport, selection="label")
    if isinstance(answer, list):
        assert payload == {"data": {"rows": [{"label": label} for label in answer]}}, payload
        return
    _refused(
        payload,
        "Invalid filter input",
        extensions={"code": "FILTER_INVALID", "errors": answer},
    )


class _PartnerAnnotationCriteriaSet(FilterSet):
    partner = RelatedFilter(_AnnotationCriteriaSet, field_name="partner")

    class Meta:
        model = scalar_models.NullableScalarSpecimen
        fields = []


class _DurationMembersFromScopedTarget(BaseInFilter, DurationFilter):
    """An ordinary django-filter CSV class whose own field cleans duration members."""


class _UndeclaredAnnotationCriteriaSet(FilterSet):
    lag_among = _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")

    class Meta:
        model = scalar_models.NullableScalarSpecimen
        fields = []


class _CustomizedAnnotationCriteriaSet(_AnnotationCriteriaSet):
    """A child whose per-request constructor owns its member validator."""

    constructor_calls: ClassVar[list[str]] = []
    inner_installations: ClassVar[list[str]] = []
    outer_installations: ClassVar[list[str]] = []

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        rows = self.queryset
        assert rows is not None
        cloned = rows.all()
        self.queryset = cloned
        type(self).constructor_calls.append(cloned.db)
        field = self.filters["lag_among"].field
        element = read_attr(field, "element_field", None)
        if isinstance(element, FormField):
            element.validators.append(_reject_one_day)
            type(self).inner_installations.append(cloned.db)
        else:
            # Sync flat preparation follows permission checks, so constructor-time
            # base rows cannot yet supply the annotation's inner field.
            field.validators.append(_reject_one_day_list)
            type(self).outer_installations.append(cloned.db)


def _reject_one_day(value: object) -> None:
    """A real form validator that proves the child field owns flat cleaning."""
    if value == datetime.timedelta(days=1):
        raise ValidationError("One day is reserved.", code="reserved")


def _reject_one_day_list(value: object) -> None:
    if value == [datetime.timedelta(days=1)]:
        raise ValidationError("One day is reserved.", code="reserved")


class _CustomizedPartnerAnnotationCriteriaSet(FilterSet):
    partner = RelatedFilter(_CustomizedAnnotationCriteriaSet, field_name="partner")

    class Meta:
        model = scalar_models.NullableScalarSpecimen
        fields = []


class _AliasDurationWidget(TextInput):
    """Read a consumer's form spelling before the annotation member cleaner runs."""

    @override
    def value_from_datadict(
        self,
        data: Mapping[str, object],
        files: object,
        name: str,
    ) -> object:
        del files
        value = data.get(name)
        if value == ["one-day"]:
            return ["1 00:00:00"]
        if value == ["two-days"]:
            return ["2 00:00:00"]
        return value


class _WholeDurationField(FormField):
    """A consumer field whose complete clean owns duration member interpretation."""

    @override
    def clean(self, value: object) -> object:
        cleaned = object_result(super().clean, value)
        if cleaned == ["one-day"]:
            return [datetime.timedelta(days=1)]
        if cleaned == ["two-days"]:
            return [datetime.timedelta(days=2)]
        raise ValidationError("Use one-day or two-days.", code="whole_duration")


class _WholeDurationListFilter(ListFilter):
    field_class = _WholeDurationField


class _WholeDurationChildSet(FilterSet):
    lag_among = _WholeDurationListFilter(field_name="lag", lookup_expr="in")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = []


class _WholeDurationParentSet(FilterSet):
    partner = RelatedFilter(_WholeDurationChildSet, field_name="partner")

    class Meta:
        model = scalar_models.NullableScalarSpecimen
        fields = []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("member", "labels"),
    [
        pytest.param("one-day", ["of-child"], id="consumer-field-accepts"),
        pytest.param("not-a-day", None, id="consumer-field-refuses"),
    ],
)
def test_a_whole_consumer_field_keeps_its_clean_over_a_child_annotation(
    member: str,
    labels: list[str] | None,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    target = make_django_type(
        "WholeDurationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_annotating_target)},
    )
    schema = _schema(
        _WholeDurationParentSet,
        scalar_models.NullableScalarSpecimen,
        transport="async",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": [member]}},
        transport="async",
        selection="label",
    )
    if labels is not None:
        assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "partner__lag_among": [
                        {"message": "Use one-day or two-days.", "code": "whole_duration"},
                    ],
                },
            },
        )


class _GenericOutputChildSet(FilterSet):
    opaque_among = ListFilter(field_name="opaque", lookup_expr="in")
    opaque_span = RangeFilter(field_name="opaque", lookup_expr="range")

    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = []


class _GenericOutputParentSet(FilterSet):
    partner = RelatedFilter(_GenericOutputChildSet, field_name="partner")

    class Meta:
        model = scalar_models.NullableScalarSpecimen
        fields = []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("where", "labels"),
    [
        pytest.param(
            {"partner__opaque_among": {"in_": ["kept"]}},
            ["of-child"],
            id="generic-output-list-match",
        ),
        pytest.param(
            {"partner__opaque_among": {"in_": ["missing"]}},
            [],
            id="generic-output-list-miss",
        ),
        pytest.param(
            {"partner__opaque_span": {"start": "kept", "end": "kept"}},
            ["of-child"],
            id="generic-output-range-match",
        ),
        pytest.param(
            {"partner__opaque_span": {"start": "missing", "end": "z"}},
            [],
            id="generic-output-range-miss",
        ),
    ],
)
def test_a_target_output_without_a_django_filter_comparison_field_keeps_its_outer_value(
    where: JSONObject,
    labels: list[str],
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)

    def generic_target(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        return rows.annotate(
            opaque=django_models.Value("kept", output_field=django_models.Field()),
        )

    target = make_django_type(
        "GenericOutputTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(generic_target)},
    )
    schema = _schema(
        _GenericOutputParentSet,
        scalar_models.NullableScalarSpecimen,
        transport="async",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(schema, where, transport="async", selection="label")
    assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload


def _reject_parent_one_day(value: object) -> None:
    if value == [datetime.timedelta(days=1)]:
        raise ValidationError("Parent reserved one day.", code="parent_reserved")


class _ParentEditedAnnotationCriteriaSet(_PartnerAnnotationCriteriaSet):
    """The rebound field's outer validator and widget belong to the parent copy."""

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        field = self.filters["partner__lag_among"].field
        field.validators.append(_reject_parent_one_day)
        field.widget = _AliasDurationWidget()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("member", "answer"),
    [
        pytest.param(
            "one-day",
            {
                "partner__lag_among": [
                    {"message": "Parent reserved one day.", "code": "parent_reserved"},
                ],
            },
            id="parent-validator-and-widget",
        ),
        pytest.param("two-days", ["of-two-days"], id="widget-accepted"),
    ],
)
def test_parent_rebound_field_keeps_its_widget_and_outer_validator_with_annotation_cleaning(
    transport: str,
    member: str,
    answer: JSONObject | list[str],
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    for days in (1, 2):
        child = cleaned_specimen(f"child-{days}", kept=True)
        child.parent = kept
        child.occurred_at = kept.occurred_at + datetime.timedelta(days=days)
        child.save(update_fields=["parent", "occurred_at"])
        scalar_models.NullableScalarSpecimen.objects.create(
            label=f"of-{['one', 'two'][days - 1]}-day{'s' if days == 2 else ''}",
            partner=child,
        )
    target = make_django_type(
        "ParentEditedAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_annotating_target)},
    )
    schema = _schema(
        _ParentEditedAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": [member]}},
        transport=transport,
        selection="label",
    )
    if isinstance(answer, list):
        assert payload == {"data": {"rows": [{"label": label} for label in answer]}}, payload
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={"code": "FILTER_INVALID", "errors": answer},
        )


class _ReadOmittedProjectedCriteriaSet(_AnnotationCriteriaSet):
    named = CharFilter(method="filter_named")

    def filter_named(
        self,
        queryset: QuerySet[Model],
        name: str,
        value: str,
    ) -> QuerySet[Model]:
        del name
        return queryset.filter(label=value)


class _ReadingOmittedProjectedSet(FilterSet):
    partner = RelatedFilter(_ReadOmittedProjectedCriteriaSet, field_name="partner")

    class Meta:
        model = scalar_models.NullableScalarSpecimen
        fields = {"label": ["exact"]}

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        widget = read_attr(self.filters["partner__named"].field, "widget")
        assert isinstance(widget, Widget)
        widget.attrs["data-inspected"] = "yes"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    "where",
    [
        pytest.param({"label": {"exact": "of-child"}}, id="omitted"),
        pytest.param(
            {"label": {"exact": "of-child"}, "partner__named": None},
            id="null",
        ),
        pytest.param(
            {"label": {"exact": "of-child"}, "partner__lag_span": {"start": None, "end": None}},
            id="empty-range",
        ),
    ],
)
def test_reading_an_omitted_projected_field_does_not_derive_its_target(
    transport: str,
    where: JSONObject,
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    async def async_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        return rows

    def sync_target(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        return rows

    target = make_django_type(
        "UnreadProjectedTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(async_target if transport == "async" else sync_target),
        },
    )
    schema = _schema(
        _ReadingOmittedProjectedSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    assert calls == []
    assert _post(schema, where, transport=transport, selection="label") == {
        "data": {"rows": [{"label": "of-child"}]},
    }
    assert calls == []


@pytest.mark.django_db(transaction=True)
def test_reading_a_projected_field_reuses_the_active_siblings_awaited_annotation() -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "ReadThenAnnotatedTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_async)},
    )
    schema = _schema(
        _ReadingOmittedProjectedSet,
        scalar_models.NullableScalarSpecimen,
        transport="async",
        fields=("label",),
        targets=(target,),
    )
    assert calls == []
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": ["1 00:00:00"]}},
        transport="async",
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert calls == ["default"]


def _annotating_target(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
    """A target type's ``get_queryset`` adding the annotations its branch's filters name."""
    del cls, info
    return _with_annotations(rows)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("where", "answer"),
    [
        pytest.param(
            {"partner": {"lag_among": {"in_": ["1 00:00:00"]}}},
            ["of-child"],
            id="duration-member",
        ),
        pytest.param(
            {"partner__lag_among": {"in_": ["1 00:00:00"]}},
            ["of-child"],
            id="flat-duration-member",
        ),
        pytest.param(
            {"partner__lag_span": {"start": "12:00:00", "end": "2 00:00:00"}},
            ["of-child"],
            id="flat-duration-range",
        ),
        pytest.param(
            {"partner__kids_among": {"in_": ["1", "1.5", str(2**63)]}},
            ["of-kept"],
            id="flat-integer-members",
        ),
        pytest.param(
            {"partner": {"kids_span": {"start": "1", "end": str(2**63)}}},
            ["of-kept"],
            id="integer-range-past-the-column",
        ),
        pytest.param(
            {"partner__kids_span": {"start": "1", "end": str(2**63)}},
            ["of-kept"],
            id="flat-integer-range-past-the-column",
        ),
        pytest.param(
            {"partner": {"lag_among": {"in_": ["abc"]}}},
            {"partner__lag_among": [{"message": "Enter a valid duration.", "code": "invalid"}]},
            id="duration-junk",
        ),
        pytest.param(
            {"partner__lag_among": {"in_": ["abc"]}},
            {"partner__lag_among": [{"message": "Enter a valid duration.", "code": "invalid"}]},
            id="flat-duration-junk",
        ),
    ],
)
def test_a_branch_criterion_over_its_target_types_annotation_is_cleaned_as_it_compares(
    transport: str,
    where: JSONObject,
    answer: list[str] | JSONObject,
) -> None:
    """A ``RelatedFilter`` branch reads the annotations its target type's ``get_queryset`` adds.

    The branch's set is handed the target type's rows, which carry ``lag`` and ``kids``, so a
    member or bound over either is cleaned and compared as the annotation's output field.
    """
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-kept", partner=kept)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    target = make_django_type(
        "AnnotatedPartnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_annotating_target)},
    )
    schema = _schema(
        _PartnerAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(schema, where, transport=transport, selection="label")
    if isinstance(answer, list):
        assert payload == {"data": {"rows": [{"label": label} for label in answer]}}, payload
        return
    _refused(
        payload,
        "Invalid filter input",
        extensions={"code": "FILTER_INVALID", "errors": answer},
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("spelling", ["flat", "nested", "logical"])
@pytest.mark.parametrize("lookup", ["member", "range"])
@pytest.mark.parametrize("customized", [False, True], ids=["plain", "projected-consumer"])
def test_child_annotation_bind_ask_reads_the_actual_terminal_rows(
    transport: str,
    spelling: str,
    lookup: str,
    record_compiled_sql: RecordCompiledSql,
    *,
    customized: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    target = make_django_type(
        "OverflowAnnotatedPartnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_annotating_target)},
    )
    schema = _schema(
        _CustomizedPartnerAnnotationCriteriaSet if customized else _PartnerAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    huge = "999999999 00:00:00"
    name = "lag_among" if lookup == "member" else "lag_span"
    value: JSONObject = (
        {"in_": [huge] if customized else ["1 00:00:00", huge]}
        if lookup == "member"
        else {"start": "1 00:00:00", "end": huge}
    )
    leaf: JSONObject = {name: value} if spelling == "nested" else {f"partner__{name}": value}
    where: JSONObject = {"partner": leaf} if spelling == "nested" else leaf
    if spelling == "logical":
        where = {"or_": [leaf]}
    _CustomizedAnnotationCriteriaSet.constructor_calls.clear()
    _CustomizedAnnotationCriteriaSet.inner_installations.clear()
    _CustomizedAnnotationCriteriaSet.outer_installations.clear()
    recorded = record_compiled_sql()
    payload = _post(schema, where, transport=transport, selection="label")
    if connection.features.has_native_duration_field:
        native_labels = [] if customized and lookup == "member" else ["of-child"]
        assert payload == {"data": {"rows": [{"label": label} for label in native_labels]}}, (
            payload
        )
        return
    _refused(
        payload,
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {
                f"{'or_0__' if spelling == 'logical' else ''}partner__{name}": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
        },
    )
    assert recorded == [], recorded
    if customized:
        assert _CustomizedAnnotationCriteriaSet.constructor_calls == ["default"]
        assert _CustomizedAnnotationCriteriaSet.inner_installations == (
            ["default"] if spelling == "nested" else []
        )
        assert _CustomizedAnnotationCriteriaSet.outer_installations == (
            [] if spelling == "nested" else ["default"]
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("member", ["999999999 00:00:00", "not-a-duration"])
def test_undeclared_scoped_target_annotation_uses_its_visible_query_to_ask_the_bind(
    transport: str,
    member: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    def annotated_once(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "UndeclaredAnnotatedPartnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_once)},
    )
    schema = _schema(
        _UndeclaredAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    recorded = record_compiled_sql()
    payload = _post(
        schema,
        {"lag_among": {"in_": [member]}},
        transport=transport,
        selection="label",
    )
    if member == "not-a-duration":
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "lag_among": [{"message": "Enter a valid duration.", "code": "invalid"}],
                },
            },
        )
        assert recorded == [], recorded
        assert calls == []
        return
    if connection.features.has_native_duration_field:
        assert payload == {"data": {"rows": []}}, payload
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "lag_among": [
                        {
                            "message": "Enter a value the database can represent.",
                            "code": "invalid",
                        },
                    ],
                },
            },
        )
        assert recorded == [], recorded
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("deny", "member"),
    [
        pytest.param(True, "1 00:00:00", id="denied"),
        pytest.param(False, "not-a-duration", id="invalid-before-owner"),
        pytest.param(False, "1 00:00:00", id="valid-owner-once"),
    ],
)
def test_complete_undeclared_annotation_owner_runs_after_consumer_form(
    member: str,
    *,
    deny: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class RecordingForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class OrderedSet(_UndeclaredAnnotationCriteriaSet):
        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = RecordingForm

        def check_lag_among_permission(self, request: object) -> None:
            del request
            events.append("gate")
            if deny:
                raise GraphQLError("denied-undeclared-annotation")

    def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "OrderedUndeclaredAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        OrderedSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"lag_among": {"in_": [member]}},
        transport="sync",
        selection="label",
    )
    if deny:
        _refused(payload, "denied-undeclared-annotation")
        assert events == ["gate"]
    elif member == "not-a-duration":
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "lag_among": [{"message": "Enter a valid duration.", "code": "invalid"}],
                },
            },
        )
        assert events == ["gate", "form.clean"]
    else:
        assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
        assert events == ["gate", "form.clean", "hook"]


@pytest.mark.django_db(transaction=True)
def test_undeclared_complete_invalid_member_wins_async_only_owner() -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    async def async_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "UndeclaredAsyncOnlyAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(async_target)},
    )
    schema = _schema(
        _UndeclaredAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"lag_among": {"in_": ["not-a-duration"]}},
        transport="sync",
        selection="label",
    )
    _refused(
        payload,
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {"lag_among": [{"message": "Enter a valid duration.", "code": "invalid"}]},
        },
    )
    assert calls == []


@pytest.mark.django_db(transaction=True)
def test_unrelated_form_error_precedes_uncached_complete_async_owner() -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class Criteria(_UndeclaredAnnotationCriteriaSet):
        bad_number = NumberFilter(field_name="signed_big")

    async def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "UnrelatedErrorBeforeCompleteOwnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"lag_among": {"in_": ["1 00:00:00"]}, "bad_number": "abc"},
        transport="sync",
        selection="label",
    )
    _refused(
        payload,
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {"bad_number": [{"message": "Enter a number.", "code": "invalid"}]},
        },
    )
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("operator", ["or_", "and_"])
@pytest.mark.parametrize("invalid_first", [False, True])
def test_logical_native_error_precedes_complete_annotation_owner_in_both_arm_orders(
    transport: str,
    operator: str,
    *,
    invalid_first: bool,
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class Criteria(_UndeclaredAnnotationCriteriaSet):
        bad_number = NumberFilter(field_name="signed_big")

    def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "LogicalNativeErrorBeforeCompleteOwnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    bad = {"bad_number": "abc"}
    lag = {"lag_among": {"in_": ["1 00:00:00"]}}
    payload = _post(
        schema,
        {operator: [bad, lag] if invalid_first else [lag, bad]},
        transport=transport,
        selection="label",
    )
    index = 0 if invalid_first else 1
    _refused(
        payload,
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {
                f"{operator}{index}__bad_number": [
                    {"message": "Enter a number.", "code": "invalid"},
                ],
            },
        },
    )
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("deep", [False, True])
def test_root_clean_created_annotation_waits_for_later_logical_native_error(
    transport: str,
    *,
    deep: bool,
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class DefaultsForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            cleaned = super().clean()
            if self.cleaned_data.get("label") == "of-child":
                self.cleaned_data["lag_among"] = [datetime.timedelta(days=1)]
            return cleaned

    class Criteria(_UndeclaredAnnotationCriteriaSet):
        bad_number = NumberFilter(field_name="signed_big")
        label = CharFilter(field_name="label")

        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = DefaultsForm

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "RootDefaultWaitsForLogicalNativeErrorTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    bad: dict[str, object] = {"bad_number": "abc"}
    if deep:
        bad = {"not_": {"and_": [bad]}}
    payload = _post(
        schema,
        {"label": {"exact": "of-child"}, "or_": [bad]},
        transport=transport,
        selection="label",
    )
    key = "or_0__not__and_0__bad_number" if deep else "or_0__bad_number"
    _refused(
        payload,
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {key: [{"message": "Enter a number.", "code": "invalid"}]},
        },
    )
    assert calls == []


@pytest.mark.django_db(transaction=True)
def test_valid_complete_value_reports_sync_misuse_after_actual_form_clean() -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class RecordingForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class Criteria(_UndeclaredAnnotationCriteriaSet):
        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = RecordingForm

    async def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "ValidCompleteAsyncOnlyTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"lag_among": {"in_": ["1 00:00:00"]}},
        transport="sync",
        selection="label",
    )
    assert payload["data"] is None, payload
    message = json_at(payload, "errors", 0, "message")
    assert isinstance(message, str)
    assert "FilterSet.apply_async" in message
    assert events == ["form.clean"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "query",
        "errors",
        "valid",
        "labels",
        "disabled_initial",
    ),
    [
        pytest.param(
            "p-lag_among=999999999+00%3A00%3A00&p-label=of-child",
            {
                "lag_among": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
            False,
            ["of-child"],
            False,
            id="refused-member-keeps-valid-sibling",
        ),
        pytest.param(
            "p-lag_among=1+00%3A00%3A00&p-label=of-child",
            {},
            True,
            ["of-child"],
            False,
            id="valid-member",
        ),
        pytest.param(
            "p-lag_list=999999999+00%3A00%3A00&p-label=of-child",
            {
                "lag_list": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
            False,
            ["of-child"],
            False,
            id="refused-package-list-keeps-valid-sibling",
        ),
        pytest.param(
            "p-lag_list=1+00%3A00%3A00&p-label=of-child",
            {},
            True,
            ["of-child"],
            False,
            id="valid-package-list-uses-actual-duration-cleaner",
        ),
        pytest.param(
            "p-lag_span_0=999999999+00%3A00%3A00&p-lag_span_1=999999999+00%3A00%3A00&p-label=of-child",
            {
                "lag_span": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
            False,
            ["of-child"],
            False,
            id="refused-range-keeps-valid-sibling",
        ),
        pytest.param(
            "p-lag_span_0=1+00%3A00%3A00&p-lag_span_1=1+00%3A00%3A00&p-label=of-child",
            {},
            True,
            ["of-child"],
            False,
            id="valid-range-uses-actual-duration-cleaner",
        ),
        pytest.param("p-label=other", {}, True, ["other"], False, id="inactive-annotation"),
        pytest.param(
            "p-lag_among=&p-label=other",
            {},
            True,
            ["other"],
            False,
            id="empty-raw-member",
        ),
        pytest.param("__null__", {}, True, ["other"], False, id="raw-null-member"),
        pytest.param("__unbound__", {}, False, ["of-child", "other"], False, id="unbound"),
        pytest.param(
            "p-lag_among_csv=999999999+00%3A00%3A00&p-label=of-child",
            {
                "lag_among": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
            False,
            ["of-child"],
            False,
            id="actual-alternate-widget-key-refused",
        ),
        pytest.param(
            "p-lag_among_csv=1+00%3A00%3A00&p-label=of-child",
            {},
            True,
            ["of-child"],
            False,
            id="actual-alternate-widget-key-valid",
        ),
        pytest.param(
            "p-lag_among_csv=&p-label=other",
            {},
            True,
            ["other"],
            False,
            id="actual-alternate-widget-key-empty",
        ),
        pytest.param(
            "__custom_absent__",
            {},
            True,
            ["other"],
            False,
            id="actual-alternate-widget-key-absent",
        ),
        pytest.param(
            "p-label=of-child",
            {
                "lag_among": [
                    {"message": "Enter a value the database can represent.", "code": "invalid"},
                ],
            },
            False,
            ["of-child"],
            True,
            id="disabled-initial-annotation",
        ),
    ],
)
def test_raw_scoped_annotation_form_asks_before_bare_qs(
    query: str,
    errors: dict[str, object],
    labels: list[str],
    *,
    valid: bool,
    disabled_initial: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    scalar_models.NullableScalarSpecimen.objects.create(label="other")
    calls: list[str] = []
    custom_widget = "lag_among_csv" in query or query == "__custom_absent__"

    class PostedDurationInput(TextInput):
        @override
        def value_from_datadict(
            self,
            data: Mapping[str, object],
            files: object,
            name: str,
        ) -> object:
            return object_result(super().value_from_datadict, data, files, f"{name}_csv")

    class RawForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            if disabled_initial:
                field = self.fields["lag_among"]
                field.disabled = True
                field.initial = [datetime.timedelta(days=999999999)]

    class RawSet(FilterSet):
        lag_among = (
            _DurationMembersFromScopedTarget(
                field_name="partner__lag",
                lookup_expr="in",
                widget=PostedDurationInput,
            )
            if custom_widget
            else _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
        )
        lag_list = ListFilter(field_name="partner__lag", lookup_expr="in")
        lag_span = RangeFilter(field_name="partner__lag", lookup_expr="range")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = RawForm

    def annotated_once(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "RawScopedAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_once)},
    )

    @strawberry.type
    class Query:
        def _answer(self, query: str) -> dict[str, object]:
            data: dict[str, object] | QueryDict | None
            if query == "__unbound__":
                data = None
            elif query == "__null__":
                data = {"p-lag_among": None, "p-label": "other"}
            elif query == "__custom_absent__":
                data = QueryDict("p-label=other")
            else:
                data = QueryDict(query)
            instance = RawSet(
                data=data,
                queryset=scalar_models.NullableScalarSpecimen.objects.order_by("label"),
                prefix="p",
            )
            errors = require_instance(instance.errors, ErrorDict).get_json_data()
            valid = instance.is_valid()
            preclean_calls = list(calls)
            return {
                "errors": errors,
                "valid": valid,
                "preclean_calls": preclean_calls,
                "labels": list(instance.qs.values_list("label", flat=True)),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(
                "query($query: String!) { answer(query: $query) }",
                variables={"query": query},
                url="/graphql-apply-arguments/",
            )
    finally:
        _CURRENT["schema"] = None
    if connection.features.has_native_duration_field:
        errors = {}
        valid = query != "__unbound__"
        labels = [] if "999999999" in query or disabled_initial else labels
    preclean_calls = (
        []
        if query
        in {
            "p-label=other",
            "p-lag_among=&p-label=other",
            "p-lag_among_csv=&p-label=other",
            "__null__",
            "__unbound__",
            "__custom_absent__",
        }
        else ["default"]
    )
    assert payload == {
        "data": {
            "answer": {
                "errors": errors,
                "valid": valid,
                "preclean_calls": preclean_calls,
                "labels": labels,
            },
        },
    }, payload
    assert calls == preclean_calls


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("cached_owner", [False, True], ids=["uncached", "parser-sibling-cached"])
def test_raw_invalid_form_skips_only_uncached_bind_source_and_keeps_partial_qs(
    record_compiled_sql: RecordCompiledSql,
    *,
    cached_owner: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class RawSet(FilterSet):
        lag_among = _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
        lag_list = ListFilter(field_name="partner__lag", lookup_expr="in")
        bad_number = NumberFilter(field_name="signed_big")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "RawInvalidPostcleanTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )
    recorded = record_compiled_sql()

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            sibling = "&p-lag_list=1+00%3A00%3A00" if cached_owner else ""
            data = QueryDict(
                f"p-lag_among=999999999+00%3A00%3A00{sibling}&p-bad_number=abc&p-label=of-child",
            )
            instance = RawSet(
                data=data,
                queryset=scalar_models.NullableScalarSpecimen.objects.order_by("label"),
                prefix="p",
            )
            errors = require_instance(instance.errors, ErrorDict).get_json_data()
            valid = instance.is_valid()
            before_qs = list(calls)
            before_sql = list(recorded)
            return {
                "errors": errors,
                "valid": valid,
                "before_qs": before_qs,
                "before_sql": before_sql,
                "labels": list(instance.qs.values_list("label", flat=True)),
                "after_qs": list(calls),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    errors: JSONObject = {"bad_number": [{"message": "Enter a number.", "code": "invalid"}]}
    if cached_owner and not connection.features.has_native_duration_field:
        errors["lag_among"] = [
            {"message": "Enter a value the database can represent.", "code": "invalid"},
        ]
    expected_calls = ["default"] if cached_owner else []
    expected_labels = (
        []
        if cached_owner and connection.features.has_native_duration_field
        else [
            "of-child",
        ]
    )
    assert payload == {
        "data": {
            "answer": {
                "errors": errors,
                "valid": False,
                "before_qs": expected_calls,
                "before_sql": [],
                "labels": expected_labels,
                "after_qs": expected_calls,
            },
        },
    }, payload


@pytest.mark.django_db(transaction=True)
def test_complete_disabled_initial_binds_after_form_clean() -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class InitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            field = self.fields["lag_among"]
            field.disabled = True
            field.initial = [datetime.timedelta(days=999999999)]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class InitialSet(FilterSet):
        lag_among = _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = InitialForm

        def check_label_permission(self, request: object) -> None:
            del request
            events.append("gate")

    def annotated_once(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "InitialAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_once)},
    )
    schema = _schema(
        InitialSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"label": {"exact": "of-child"}},
        transport="sync",
        selection="label",
    )
    if connection.features.has_native_duration_field:
        assert payload == {"data": {"rows": []}}, payload
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "lag_among": [
                        {
                            "message": "Enter a value the database can represent.",
                            "code": "invalid",
                        },
                    ],
                },
            },
        )
    assert events == ["gate", "form.clean", "hook"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("family", "member", "expected"),
    [
        pytest.param("native", "1 00:00:00", "row", id="native-valid"),
        pytest.param("native", "999999999 00:00:00", "bind", id="native-huge"),
        pytest.param("list", "1 00:00:00", "row", id="package-list-valid-string"),
        pytest.param("list", "junk", "parse", id="package-list-malformed"),
        pytest.param("list", "999999999 00:00:00", "bind", id="package-list-huge"),
        pytest.param("range", "1 00:00:00", "row", id="package-range-valid-string"),
        pytest.param("range", "junk", "parse", id="package-range-malformed"),
        pytest.param("range", "999999999 00:00:00", "bind", id="package-range-huge"),
        pytest.param("list-policy", "1 00:00:00", "policy", id="declaring-list-policy"),
        pytest.param("range-policy", "1 00:00:00", "policy", id="declaring-range-policy"),
        pytest.param("native-denied", "1 00:00:00", "denied", id="denied-zero-hook"),
    ],
)
def test_disabled_initial_uses_actual_owner_and_cleaner_on_both_colors(
    transport: str,
    family: str,
    member: str,
    expected: str,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []
    is_range = family.startswith("range")
    is_native = family.startswith("native")
    policy = family.endswith("policy")

    class InitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            field = self.fields["lag_initial"]
            field.disabled = True
            value: object = (
                datetime.timedelta(days=1 if member == "1 00:00:00" else 999999999)
                if is_native
                else member
            )
            field.initial = [value, value] if is_range else [value]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class PolicyDurationFilter(DurationFilter):
        @property
        @override
        def field(self) -> FormField:
            field = super().field
            if policy and _reject_one_day not in field.validators:
                field.validators.append(_reject_one_day)
            return field

    class InitialSet(FilterSet):
        lag_initial = (
            _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
            if is_native
            else RangeFilter(field_name="partner__lag", lookup_expr="range")
            if is_range
            else ListFilter(field_name="partner__lag", lookup_expr="in")
        )
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = InitialForm
            filter_overrides = {
                django_models.DurationField: {"filter_class": PolicyDurationFilter},
            }

        def check_label_permission(self, request: object) -> None:
            del request
            events.append("gate")
            if expected == "denied":
                raise GraphQLError("denied-initial")

    def annotated_sync(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "BothColorInitialAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                annotated_async if transport == "async" else annotated_sync,
            ),
        },
    )
    schema = _schema(
        InitialSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"label": {"exact": "of-child"}},
        transport=transport,
        selection="label",
    )
    if expected == "denied":
        _refused(payload, "denied-initial")
        assert events == ["gate"]
        return
    if expected == "bind" and connection.features.has_native_duration_field:
        assert payload == {"data": {"rows": []}}, payload
    elif expected == "row":
        assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    else:
        message, code = {
            "bind": ("Enter a value the database can represent.", "invalid"),
            "parse": ("Enter a valid duration.", "invalid"),
            "policy": ("One day is reserved.", "reserved"),
        }[expected]
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {"lag_initial": [{"message": message, "code": code}]},
            },
        )
    assert events == (
        ["gate", "form.clean", "hook"] if is_native else ["gate", "hook", "form.clean"]
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("family", ["list", "range"])
@pytest.mark.parametrize(
    ("scenario", "preinspect"),
    [
        ("valid", False),
        ("valid", True),
        ("malformed", False),
        ("huge", False),
        ("policy", False),
        ("owned", True),
    ],
)
def test_cached_declared_child_enriches_own_disabled_initial_field(
    transport: str,
    family: str,
    scenario: str,
    *,
    preinspect: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []
    member = (
        "junk"
        if scenario == "malformed"
        else "999999999 00:00:00"
        if scenario == "huge"
        else "1 00:00:00"
    )

    class InitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            field = self.fields["lag_initial"]
            field.disabled = True
            field.initial = [member, member] if family == "range" else [member]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class PolicyDurationFilter(DurationFilter):
        @property
        @override
        def field(self) -> FormField:
            field = super().field
            if scenario == "policy" and _reject_one_day not in field.validators:
                field.validators.append(_reject_one_day)
            return field

    inner_cleaner = (
        FormDurationField(validators=[_reject_one_day]) if scenario == "owned" else None
    )

    class RootSet(FilterSet):
        partner = RelatedFilter(_AnnotationCriteriaSet, field_name="partner")
        lag_initial = (
            RangeFilter(field_name="partner__lag", lookup_expr="range", bound_field=inner_cleaner)
            if family == "range"
            else ListFilter(
                field_name="partner__lag",
                lookup_expr="in",
                element_field=inner_cleaner,
            )
        )

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = InitialForm
            filter_overrides = {
                django_models.DurationField: {"filter_class": PolicyDurationFilter},
            }

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            if preinspect:
                _ = self.form

    def annotated_sync(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "CachedDeclaredInitialTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                annotated_async if transport == "async" else annotated_sync,
            ),
        },
    )
    schema = _schema(
        RootSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"partner__kids_among": {"in_": [0]}},
        transport=transport,
        selection="label",
    )
    if scenario == "valid":
        assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    elif scenario == "huge" and connection.features.has_native_duration_field:
        assert payload == {"data": {"rows": []}}, payload
    else:
        message, code = {
            "malformed": ("Enter a valid duration.", "invalid"),
            "huge": ("Enter a value the database can represent.", "invalid"),
            "policy": ("One day is reserved.", "reserved"),
            "owned": ("One day is reserved.", "reserved"),
        }[scenario]
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {"lag_initial": [{"message": message, "code": code}]},
            },
        )
    assert events == ["hook", "form.clean"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("family", ["list", "range"])
@pytest.mark.parametrize("member", ["1 00:00:00", "999999999 00:00:00"])
def test_raw_cached_declared_sibling_enriches_own_initial_before_clean(
    family: str,
    member: str,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class InitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            field = self.fields["lag_initial"]
            field.disabled = True
            field.initial = [member, member] if family == "range" else [member]
            self.order_fields(["partner__kids_among", "lag_initial"])

    class RawSet(FilterSet):
        partner = RelatedFilter(_AnnotationCriteriaSet, field_name="partner")
        lag_initial = (
            RangeFilter(field_name="partner__lag", lookup_expr="range")
            if family == "range"
            else ListFilter(field_name="partner__lag", lookup_expr="in")
        )

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = InitialForm

    def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        del cls, info
        calls.append("hook")
        return _with_annotations(rows)

    target = make_django_type(
        "RawCachedDeclaredInitialTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            instance = RawSet(
                data=QueryDict("p-partner__kids_among=0"),
                queryset=scalar_models.NullableScalarSpecimen.objects.order_by("label"),
                prefix="p",
            )
            errors = require_instance(instance.errors, ErrorDict).get_json_data()
            valid = instance.is_valid()
            return {
                "errors": errors,
                "valid": valid,
                "labels": list(instance.qs.values_list("label", flat=True)),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    huge = member.startswith("999999999")
    bind_error = huge and not connection.features.has_native_duration_field
    expected_errors: JSONObject = (
        {
            "lag_initial": [
                {"message": "Enter a value the database can represent.", "code": "invalid"},
            ],
        }
        if bind_error
        else {}
    )
    assert payload == {
        "data": {
            "answer": {
                "errors": expected_errors,
                "valid": not bind_error,
                "labels": [] if huge and not bind_error else ["of-child"],
            },
        },
    }, payload
    assert calls == ["hook"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("transport", "changed"),
    [
        ("sync", False),
        ("async", False),
        ("sync", True),
        ("async", True),
    ],
)
def test_unchanged_empty_permitted_initial_skips_its_annotation_owner(
    transport: str,
    *,
    changed: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class EmptyInitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(
                data=data,
                prefix=prefix,
                empty_permitted=True,
                use_required_attribute=False,
            )
            field = self.fields["lag_initial"]
            field.disabled = True
            field.initial = [datetime.timedelta(days=1)]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class InitialSet(FilterSet):
        lag_initial = _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = EmptyInitialForm

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    def annotated_sync(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "EmptyPermittedInitialTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                annotated_async if transport == "async" or not changed else annotated_sync,
            ),
        },
    )
    schema = _schema(
        InitialSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"label": {"exact": "of-child"}} if changed else {},
        transport=transport,
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert events == (["form.clean", "hook"] if changed else [])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("added", [False, True])
def test_unchanged_form_post_super_active_value_joins_postclean_bind_phase(
    transport: str,
    *,
    added: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class PostSuperForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(
                data=data,
                prefix=prefix,
                empty_permitted=True,
                use_required_attribute=False,
            )

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

        @override
        def full_clean(self) -> None:
            super().full_clean()
            events.append("post.super")
            if added:
                self.cleaned_data["lag_among"] = [datetime.timedelta(days=1)]

    class Criteria(_UndeclaredAnnotationCriteriaSet):
        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = PostSuperForm

    def annotated_sync(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "UnchangedPostSuperAddedAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                annotated_async if transport == "async" else annotated_sync,
            ),
        },
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(schema, {}, transport=transport, selection="label")
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert events == ["post.super", *(["hook"] if added else [])]


@pytest.mark.django_db(transaction=True)
def test_async_logical_arm_awaits_its_own_disabled_initial_on_the_same_form() -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class InitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            if "label" in self.data:
                field = self.fields["lag_initial"]
                field.disabled = True
                field.initial = ["1 00:00:00"]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class InitialSet(FilterSet):
        lag_initial = ListFilter(field_name="partner__lag", lookup_expr="in")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = InitialForm

        def check_label_permission(self, request: object) -> None:
            del request
            events.append("gate")

    async def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "LogicalInitialAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        InitialSet,
        scalar_models.NullableScalarSpecimen,
        transport="async",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"or_": [{"label": {"exact": "of-child"}}]},
        transport="async",
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert events == [
        "gate",
        "form.clean",
        "hook",
        "form.clean",
    ]


@pytest.mark.django_db(transaction=True)
def test_async_nested_child_awaits_its_disabled_initial_before_clean() -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class InitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            field = self.fields["lag_initial"]
            field.disabled = True
            field.initial = ["1 00:00:00"]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class ChildSet(FilterSet):
        lag_initial = ListFilter(field_name="partner__lag", lookup_expr="in")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = InitialForm

        def check_label_permission(self, request: object) -> None:
            del request
            events.append("gate")

    class OuterSet(FilterSet):
        siblings = RelatedFilter(ChildSet, field_name="partner__nullable_partners")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    async def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "NestedInitialAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        OuterSet,
        scalar_models.NullableScalarSpecimen,
        transport="async",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"siblings": {"label": {"exact": "of-child"}}},
        transport="async",
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert events == ["hook", "form.clean", "gate"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("spelling", ["flat", "nested", "logical"])
@pytest.mark.parametrize("projected", [False, True], ids=["plain", "constructor-projected"])
@pytest.mark.parametrize("lookup", ["member", "package-list", "range"])
@pytest.mark.parametrize("member", ["1 00:00:00", "999999999 00:00:00"])
def test_projected_child_to_undeclared_annotation_asks_final_source(
    transport: str,
    spelling: str,
    lookup: str,
    member: str,
    record_compiled_sql: RecordCompiledSql,
    *,
    projected: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class ChildSet(FilterSet):
        lag_among = _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
        lag_list = ListFilter(field_name="partner__lag", lookup_expr="in")
        lag_span = RangeFilter(field_name="partner__lag", lookup_expr="range")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    class ProjectedChildSet(ChildSet):
        constructor_calls: ClassVar[list[str]] = []

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            rows = self.queryset
            assert rows is not None
            self.queryset = rows.filter(label="of-child")
            type(self).constructor_calls.append(rows.db)

    class OuterSet(FilterSet):
        siblings = RelatedFilter(
            ProjectedChildSet if projected else ChildSet,
            field_name="partner__nullable_partners",
        )

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    def annotated_once(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "ProjectedUndeclaredAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_once)},
    )
    schema = _schema(
        OuterSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    name = (
        "lag_span"
        if lookup == "range"
        else "lag_list"
        if lookup == "package-list"
        else "lag_among"
    )
    key = f"siblings__{name}"
    value: JSONObject = (
        {"in_": ["1 00:00:00", member]}
        if lookup != "range"
        else {"start": "1 00:00:00", "end": member}
    )
    leaf: JSONObject = {key: value}
    where: JSONObject = leaf
    if spelling == "nested":
        where = {"siblings": {name: value}}
    elif spelling == "logical":
        where = {"or_": [leaf]}
    ProjectedChildSet.constructor_calls.clear()
    recorded = record_compiled_sql()
    payload = _post(schema, where, transport=transport, selection="label")
    if member == "1 00:00:00" or connection.features.has_native_duration_field:
        assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    f"{'or_0__' if spelling == 'logical' else ''}{key}": [
                        {
                            "message": "Enter a value the database can represent.",
                            "code": "invalid",
                        },
                    ],
                },
            },
        )
        assert recorded == [], recorded
    assert calls == ["default"]
    if projected:
        assert ProjectedChildSet.constructor_calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("member", "labels"),
    [
        pytest.param("1 00:00:00", None, id="declaring-child-policy-refuses"),
        pytest.param("2 00:00:00", ["of-child"], id="declaring-child-policy-accepts"),
    ],
)
def test_undeclared_annotation_comparison_uses_declaring_child_filter_policy(
    member: str,
    labels: list[str] | None,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=2)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)

    class PolicyDurationFilter(DurationFilter):
        @property
        @override
        def field(self) -> FormField:
            field = super().field
            if _reject_one_day not in field.validators:
                field.validators.append(_reject_one_day)
            return field

    class ChildSet(FilterSet):
        lag_span = RangeFilter(field_name="partner__lag", lookup_expr="range")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            filter_overrides = {
                django_models.DurationField: {"filter_class": PolicyDurationFilter},
            }

    class OuterSet(FilterSet):
        siblings = RelatedFilter(ChildSet, field_name="partner__nullable_partners")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    target = make_django_type(
        "PolicyUndeclaredAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_annotating_target)},
    )
    schema = _schema(
        OuterSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"siblings__lag_span": {"start": member, "end": "2 00:00:00"}},
        transport="sync",
        selection="label",
    )
    if labels is None:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "siblings__lag_span": [
                        {"message": "One day is reserved.", "code": "reserved"},
                    ],
                },
            },
        )
    else:
        assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_projected_flat_child_keeps_its_constructor_validator_on_target_annotations(
    transport: str,
) -> None:
    """The child instance owns a flat member's validator and its annotated cleaner."""
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    target = make_django_type(
        "CustomizedAnnotatedPartnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(_annotating_target)},
    )
    schema = _schema(
        _CustomizedPartnerAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    _CustomizedAnnotationCriteriaSet.inner_installations.clear()
    _CustomizedAnnotationCriteriaSet.outer_installations.clear()
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": ["1 00:00:00"]}},
        transport=transport,
        selection="label",
    )
    _refused(
        payload,
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {
                "partner__lag_among": [{"message": "One day is reserved.", "code": "reserved"}],
            },
        },
    )
    assert _CustomizedAnnotationCriteriaSet.inner_installations == []
    assert _CustomizedAnnotationCriteriaSet.outer_installations == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("spelling", "member", "labels"),
    [
        pytest.param("flat", "1 00:00:00", None, id="flat-reserved"),
        pytest.param("nested", "1 00:00:00", None, id="nested-reserved"),
        pytest.param("flat", "2 00:00:00", ["of-two"], id="flat-allowed"),
        pytest.param("nested", "2 00:00:00", ["of-two"], id="nested-allowed"),
        pytest.param("flat-multi", "2 00:00:00", ["of-two"], id="two-fields-one-child"),
        pytest.param("logical", "2 00:00:00", ["of-two"], id="logical-arm"),
    ],
)
def test_child_queryset_clone_keeps_its_inner_validator_and_one_installed_context(
    spelling: str,
    member: str,
    labels: list[str] | None,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    for days in (1, 2):
        child = cleaned_specimen(f"child-{days}", kept=True)
        child.parent = kept
        child.occurred_at = kept.occurred_at + datetime.timedelta(days=days)
        child.save(update_fields=["parent", "occurred_at"])
        scalar_models.NullableScalarSpecimen.objects.create(
            label=f"of-{'one' if days == 1 else 'two'}",
            partner=child,
        )
    calls: list[str] = []

    async def annotated_once(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "ClonedAnnotatedPartnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_once)},
    )
    schema = _schema(
        _CustomizedPartnerAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport="async",
        fields=("label",),
        targets=(target,),
    )
    _CustomizedAnnotationCriteriaSet.constructor_calls.clear()
    _CustomizedAnnotationCriteriaSet.inner_installations.clear()
    _CustomizedAnnotationCriteriaSet.outer_installations.clear()
    leaf: JSONObject = {"lag_among": {"in_": [member]}}
    if spelling == "nested":
        where: JSONObject = {"partner": leaf}
    elif spelling == "logical":
        where = {"or_": [{"partner__lag_among": {"in_": [member]}}]}
    else:
        where = {"partner__lag_among": {"in_": [member]}}
        if spelling == "flat-multi":
            where["partner__kids_among"] = {"in_": ["0"]}
    payload = _post(schema, where, transport="async", selection="label")
    if labels is None:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "partner__lag_among": [
                        {"message": "One day is reserved.", "code": "reserved"},
                    ],
                },
            },
        )
    else:
        assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
    assert calls == ["default"]
    assert _CustomizedAnnotationCriteriaSet.constructor_calls == ["default"]
    assert _CustomizedAnnotationCriteriaSet.inner_installations == (
        ["default"] if spelling == "nested" else []
    )
    assert _CustomizedAnnotationCriteriaSet.outer_installations == (
        [] if spelling == "nested" else ["default"]
    )


class _FlatOrderChildSet(FilterSet):
    class Meta:
        model = scalar_models.ScalarSpecimen
        fields = {"label": ["exact"]}


def _flat_order_parent_set(*, deny: bool) -> type[FilterSet]:
    class FlatOrderParentSet(FilterSet):
        partner = RelatedFilter(_FlatOrderChildSet, field_name="partner")
        own_number = NumberFilter(field_name="signed_big")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

        def check_partner_permission(self, request: object) -> None:
            del request
            if deny:
                raise GraphQLError("denied-flat-partner")

    return FlatOrderParentSet


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("where", "denied", "error_key"),
    [
        pytest.param(
            {"partner__label": {"exact": "child"}},
            True,
            None,
            id="denied-before-flat-hook",
        ),
        pytest.param(
            {"own_number": "abc", "partner__label": {"exact": "child"}},
            False,
            "own_number",
            id="form-error-before-flat-hook",
        ),
        pytest.param(
            {"or_": [{"own_number": "abc", "partner__label": {"exact": "child"}}]},
            False,
            "or_0__own_number",
            id="logical-form-error-before-flat-hook",
        ),
    ],
)
def test_sync_flat_permission_and_ordinary_form_errors_precede_async_only_target(
    where: JSONObject,
    error_key: str | None,
    *,
    denied: bool,
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    async def async_only_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        return rows

    target = make_django_type(
        "FlatOrderAsyncTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(async_only_target)},
    )
    schema = _schema(
        _flat_order_parent_set(deny=denied),
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    assert calls == []
    payload = _post(schema, where, transport="sync", selection="label")
    if error_key is None:
        _refused(payload, "denied-flat-partner")
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    error_key: [{"message": "Enter a number.", "code": "invalid"}],
                },
            },
        )
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("deny", "member", "labels"),
    [
        pytest.param(True, "two-days", None, id="denied-before-annotation"),
        pytest.param(False, "one-day", None, id="form-owned-validator"),
        pytest.param(False, "two-days", ["of-two-days"], id="one-hook-through-query"),
    ],
)
def test_sync_flat_annotation_runs_after_gate_and_before_the_actual_form_clean(
    member: str,
    labels: list[str] | None,
    *,
    deny: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    for days in (1, 2):
        child = cleaned_specimen(f"child-{days}", kept=True)
        child.parent = kept
        child.occurred_at = kept.occurred_at + datetime.timedelta(days=days)
        child.save(update_fields=["parent", "occurred_at"])
        scalar_models.NullableScalarSpecimen.objects.create(
            label=f"of-{'one-day' if days == 1 else 'two-days'}",
            partner=child,
        )
    events: list[str] = []

    class RecordingForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class OrderedAnnotationSet(FilterSet):
        partner = RelatedFilter(_AnnotationCriteriaSet, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = RecordingForm

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            field = self.form.fields["partner__lag_among"]
            field.widget = _AliasDurationWidget()
            field.validators.append(_reject_parent_one_day)

        def check_partner_permission(self, request: object) -> None:
            del request
            events.append("gate")
            if deny:
                raise GraphQLError("denied-annotation-partner")

    def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "OrderedAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        OrderedAnnotationSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": [member]}},
        transport="sync",
        selection="label",
    )
    if deny:
        _refused(payload, "denied-annotation-partner")
        assert events == ["gate"]
    elif labels is None:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "partner__lag_among": [
                        {"message": "Parent reserved one day.", "code": "parent_reserved"},
                    ],
                },
            },
        )
        assert events == ["gate", "hook", "form.clean"]
    else:
        assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
        assert events == ["gate", "hook", "form.clean"]


@pytest.mark.django_db(transaction=True)
def test_sync_invalid_annotation_input_reaches_async_hook_before_form_errors() -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "InvalidSyncAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_async)},
    )
    schema = _schema(
        _PartnerAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": ["not-a-duration"]}},
        transport="sync",
        selection="label",
    )
    assert payload["data"] is None, payload
    message = json_at(payload, "errors", 0, "message")
    assert isinstance(message, str)
    assert "FilterSet.apply_async" in message
    assert "FILTER_INVALID" not in str(payload)
    assert calls == []


@pytest.mark.django_db(transaction=True)
def test_whole_consumer_invalid_value_precedes_unresolved_annotation_owner() -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class RuntimeWholeChildSet(_AnnotationCriteriaSet):
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            self.filters["lag_among"].field_class = _WholeDurationField

    class RuntimeWholeParentSet(FilterSet):
        partner = RelatedFilter(RuntimeWholeChildSet, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "WholeFieldAsyncTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_async)},
    )
    schema = _schema(
        RuntimeWholeParentSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": ["not-a-day"]}},
        transport="sync",
        selection="label",
    )
    _refused(
        payload,
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {
                "partner__lag_among": [
                    {"message": "Use one-day or two-days.", "code": "whole_duration"},
                ],
            },
        },
    )
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("insertion", ["clean", "post-super"])
@pytest.mark.parametrize(
    "scenario",
    [
        "valid",
        "huge",
        "inactive",
        "removed",
        "repaired",
    ],
)
def test_clean_created_complete_annotation_binds_after_the_whole_actual_form(
    transport: str,
    insertion: str,
    scenario: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    scalar_models.NullableScalarSpecimen.objects.create(label="other")
    events: list[str] = []

    class DefaultsForm(Form):
        def add_default(self) -> None:
            if scenario == "removed":
                self.cleaned_data.pop("lag_among", None)
                return
            if self.cleaned_data.get("label") == "of-child":
                days = 999999999 if scenario == "huge" else 1
                self.cleaned_data["lag_among"] = [datetime.timedelta(days=days)]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            cleaned = super().clean()
            if insertion == "clean":
                self.add_default()
            return cleaned

        @override
        def full_clean(self) -> None:
            super().full_clean()
            if insertion == "post-super":
                events.append("post.super")
                self.add_default()

    class DefaultsSet(FilterSet):
        lag_among = _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = DefaultsForm

        def check_label_permission(self, request: object) -> None:
            del request
            events.append("gate")

    def annotated_sync(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "CleanCreatedAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                annotated_async if transport == "async" else annotated_sync,
            ),
        },
    )
    schema = _schema(
        DefaultsSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    recorded = record_compiled_sql()
    label = "other" if scenario == "inactive" else "of-child"
    where: dict[str, object] = {"label": {"exact": label}}
    if scenario in {"removed", "repaired"}:
        where["lag_among"] = {
            "in_": ["1 00:00:00" if scenario == "removed" else "2 00:00:00"],
        }
    payload = _post(
        schema,
        where,
        transport=transport,
        selection="label",
    )
    if scenario == "huge" and not connection.features.has_native_duration_field:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "lag_among": [
                        {
                            "message": "Enter a value the database can represent.",
                            "code": "invalid",
                        },
                    ],
                },
            },
        )
        assert recorded == [], recorded
    else:
        labels = [] if scenario == "huge" else [label]
        assert payload == {"data": {"rows": [{"label": value} for value in labels]}}, payload
    assert events == [
        "gate",
        "form.clean",
        *(["post.super"] if insertion == "post-super" else []),
        *([] if scenario in {"inactive", "removed"} else ["hook"]),
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("insertion", ["clean", "post-super"])
@pytest.mark.parametrize("scenario", ["valid", "huge", "inactive"])
def test_raw_clean_created_complete_annotation_uses_one_form_and_source(
    insertion: str,
    scenario: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    scalar_models.NullableScalarSpecimen.objects.create(label="other")
    events: list[str] = []

    class DefaultsForm(Form):
        def add_default(self) -> None:
            if self.cleaned_data.get("label") == "of-child":
                days = 999999999 if scenario == "huge" else 1
                self.cleaned_data["lag_among"] = [datetime.timedelta(days=days)]

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            cleaned = super().clean()
            if insertion == "clean":
                self.add_default()
            return cleaned

        @override
        def full_clean(self) -> None:
            super().full_clean()
            if insertion == "post-super":
                events.append("post.super")
                self.add_default()

    class RawSet(FilterSet):
        lag_among = _DurationMembersFromScopedTarget(field_name="partner__lag", lookup_expr="in")
        label = CharFilter(field_name="label")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = DefaultsForm

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "RawCleanCreatedAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )
    recorded = record_compiled_sql()

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            label = "other" if scenario == "inactive" else "of-child"
            instance = RawSet(
                data=QueryDict(f"p-label={label}"),
                queryset=scalar_models.NullableScalarSpecimen.objects.order_by("label"),
                prefix="p",
            )
            errors = require_instance(instance.errors, ErrorDict).get_json_data()
            valid = instance.is_valid()
            before_qs = list(events)
            before_sql = list(recorded)
            return {
                "errors": errors,
                "valid": valid,
                "before_qs": before_qs,
                "before_sql": before_sql,
                "labels": list(instance.qs.values_list("label", flat=True)),
                "after_qs": list(events),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    label = "other" if scenario == "inactive" else "of-child"
    errors: JSONObject = {}
    if scenario == "huge" and not connection.features.has_native_duration_field:
        errors["lag_among"] = [
            {"message": "Enter a value the database can represent.", "code": "invalid"},
        ]
    expected_events = [
        "form.clean",
        *(["post.super"] if insertion == "post-super" else []),
        *([] if scenario == "inactive" else ["hook"]),
    ]
    expected_labels = [label] if scenario != "huge" or errors else []
    assert payload == {
        "data": {
            "answer": {
                "errors": errors,
                "valid": not errors,
                "before_qs": expected_events,
                "before_sql": [],
                "labels": expected_labels,
                "after_qs": expected_events,
            },
        },
    }, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("added", [False, True])
def test_raw_unchanged_form_post_super_value_is_bound_on_the_same_instance(
    *,
    added: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class PostSuperForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(
                data=data,
                prefix=prefix,
                empty_permitted=True,
                use_required_attribute=False,
            )

        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

        @override
        def full_clean(self) -> None:
            super().full_clean()
            events.append("post.super")
            if added:
                self.cleaned_data["lag_among"] = [datetime.timedelta(days=1)]

    class RawSet(_UndeclaredAnnotationCriteriaSet):
        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = PostSuperForm

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "RawUnchangedPostSuperAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            instance = RawSet(
                data=QueryDict(""),
                queryset=scalar_models.NullableScalarSpecimen.objects.order_by("label"),
            )
            form = instance.form
            return {
                "errors": require_instance(instance.errors, ErrorDict).get_json_data(),
                "valid": instance.is_valid(),
                "same_form": instance.form is form,
                "before_qs": list(events),
                "labels": list(instance.qs.values_list("label", flat=True)),
                "after_qs": list(events),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    expected_events = ["post.super", *(["hook"] if added else [])]
    assert payload == {
        "data": {
            "answer": {
                "errors": {},
                "valid": True,
                "same_form": True,
                "before_qs": expected_events,
                "labels": ["of-child"],
                "after_qs": expected_events,
            },
        },
    }, payload


@pytest.mark.django_db(transaction=True)
def test_raw_logical_domain_error_suppresses_new_bind_owner_and_keeps_safe_sibling() -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class RawSet(_UndeclaredAnnotationCriteriaSet):
        bad_number = NumberFilter(field_name="signed_big")
        label = CharFilter(field_name="label")

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "RawLogicalErrorSuppressesBindOwnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            instance = RawSet(
                data={
                    "label": "of-child",
                    "bad_number": "abc",
                    "or_": [{"lag_among": {"in_": ["1 00:00:00"]}}],
                },
                queryset=scalar_models.NullableScalarSpecimen.objects.order_by("label"),
            )
            return {
                "errors": require_instance(instance.errors, ErrorDict).get_json_data(),
                "valid": instance.is_valid(),
                "before_qs": list(calls),
                "labels": list(instance.qs.values_list("label", flat=True)),
                "after_qs": list(calls),
            }

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    assert payload == {
        "data": {
            "answer": {
                "errors": {"bad_number": [{"message": "Enter a number.", "code": "invalid"}]},
                "valid": False,
                "before_qs": [],
                "labels": ["of-child"],
                "after_qs": [],
            },
        },
    }, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operator", ["or_", "and_"])
@pytest.mark.parametrize("invalid_first", [False, True])
def test_raw_logical_child_error_wins_complete_owner_in_both_arm_orders(
    operator: str,
    *,
    invalid_first: bool,
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class RawSet(_UndeclaredAnnotationCriteriaSet):
        bad_number = NumberFilter(field_name="signed_big")

    def annotated(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "RawLogicalChildErrorBeforeBindOwnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated)},
    )

    @strawberry.type
    class Query:
        def _answer(self) -> dict[str, object]:
            bad = {"bad_number": "abc"}
            lag = {"lag_among": {"in_": ["1 00:00:00"]}}
            instance = RawSet(
                data={operator: [bad, lag] if invalid_first else [lag, bad]},
                queryset=scalar_models.NullableScalarSpecimen.objects.order_by("pk"),
            )
            root_errors = require_instance(instance.errors, ErrorDict).get_json_data()
            root_valid = instance.is_valid()
            try:
                _ = instance.qs
            except GraphQLError as error:
                return {
                    "root_errors": root_errors,
                    "root_valid": root_valid,
                    "error": str(error),
                    "extensions": error.extensions,
                    "calls": list(calls),
                }
            raise AssertionError("The logical child must report its native form error")

        answer: dict[str, object] = strawberry.field(
            resolver=_answer,
            graphql_type=strawberry.scalars.JSON,
        )

    finalize_django_types()
    schema = DjangoSchema(
        query=Query,
        types=(target,),
        config=strawberry_config(),
        error_policy={"enabled": False},
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload("query { answer }", url="/graphql-apply-arguments/")
    finally:
        _CURRENT["schema"] = None
    index = 0 if invalid_first else 1
    assert payload == {
        "data": {
            "answer": {
                "root_errors": {},
                "root_valid": True,
                "error": "Invalid filter input",
                "extensions": {
                    "code": "FILTER_INVALID",
                    "errors": {
                        f"{operator}{index}__bad_number": [
                            {"message": "Enter a number.", "code": "invalid"},
                        ],
                    },
                },
                "calls": [],
            },
        },
    }, payload


@pytest.mark.django_db(transaction=True)
def test_whole_consumer_field_on_resolved_flat_column_cleans_before_async_target() -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class WholeResolvedSet(FilterSet):
        occurred_among = _WholeDurationListFilter(
            field_name="partner__occurred_at",
            lookup_expr="in",
        )

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    async def target_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "WholeResolvedAsyncTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(target_async)},
    )
    schema = _schema(
        WholeResolvedSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    _refused(
        _post(
            schema,
            {"occurred_among": {"in_": ["not-a-day"]}},
            transport="sync",
            selection="label",
        ),
        "Invalid filter input",
        extensions={
            "code": "FILTER_INVALID",
            "errors": {
                "occurred_among": [
                    {"message": "Use one-day or two-days.", "code": "whole_duration"},
                ],
            },
        },
    )
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "leaf",
    ["stamp_year_path", "stamp_year_lookup", "stamp_alias_year"],
)
def test_sync_flat_annotation_transform_spelling_uses_the_hook_output_field(leaf: str) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    class StampChildSet(FilterSet):
        stamp_year_path = RangeFilter(field_name="stamp__year", lookup_expr="range")
        stamp_year_lookup = RangeFilter(field_name="stamp", lookup_expr="year__range")
        stamp_alias_year = RangeFilter(field_name="stamp__at", lookup_expr="year__range")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    class StampParentSet(FilterSet):
        partner = RelatedFilter(StampChildSet, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        return rows.annotate(
            **{
                ("stamp__at" if leaf == "stamp_alias_year" else "stamp"): django_models.F(
                    "occurred_at",
                ),
            },
        )

    target = make_django_type(
        "StampYearTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        StampParentSet,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {f"partner__{leaf}": {"start": str(child.occurred_at.year)}},
        transport="sync",
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("member", "constructor_label", "labels"),
    [
        pytest.param("1 00:00:00", "child-1", None, id="owned-validator"),
        pytest.param("2 00:00:00", "child-1", [], id="constructor-excludes"),
        pytest.param("2 00:00:00", "child-2", ["of-child-2"], id="constructor-allows"),
    ],
)
def test_preinspected_projected_child_is_promoted_without_losing_constructor_validator(
    member: str,
    constructor_label: str,
    labels: list[str] | None,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    for days in (1, 2):
        child = cleaned_specimen(f"child-{days}", kept=True)
        child.parent = kept
        child.occurred_at = kept.occurred_at + datetime.timedelta(days=days)
        child.save(update_fields=["parent", "occurred_at"])
        scalar_models.NullableScalarSpecimen.objects.create(
            label=f"of-child-{days}",
            partner=child,
        )
    calls: list[str] = []

    class PreinspectedChild(_AnnotationCriteriaSet):
        constructor_calls: ClassVar[list[str]] = []

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            rows = self.queryset
            assert rows is not None
            self.queryset = (
                rows.all()
                .annotate(constructor_label=django_models.F("label"))
                .filter(
                    constructor_label=constructor_label,
                )
            )
            type(self).constructor_calls.append(rows.db)
            self.filters["lag_among"].field.validators.append(_reject_parent_one_day)

    class PreinspectingParent(FilterSet):
        partner = RelatedFilter(PreinspectedChild, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            _ = self.filters["partner__lag_among"].field

    def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "PreinspectedAnnotationTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        PreinspectingParent,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": [member]}},
        transport="sync",
        selection="label",
    )
    if labels is None:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "partner__lag_among": [
                        {"message": "Parent reserved one day.", "code": "parent_reserved"},
                    ],
                },
            },
        )
    else:
        assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
    assert calls == ["default"]
    assert PreinspectedChild.constructor_calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("family", ["list", "range"])
@pytest.mark.parametrize(
    "spelling",
    [
        "direct",
        "logical",
        "valid",
        "async-valid",
        "sibling-valid",
    ],
)
def test_projected_method_values_keep_ordinary_sync_flat_hook_timing(
    family: str,
    spelling: str,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []
    received: list[object] = []
    filter_class = ListFilter if family == "list" else RangeFilter
    lookup = "in" if family == "list" else "range"

    class MethodChild(FilterSet):
        lag_sent = filter_class(field_name="lag", lookup_expr=lookup, method="filter_lag_sent")
        lag_among = ListFilter(field_name="lag", lookup_expr="in")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

        def filter_lag_sent(
            self,
            queryset: QuerySet[Model],
            name: str,
            value: object,
        ) -> QuerySet[Model]:
            del name
            received.append(value)
            events.append("method")
            return queryset.filter(label="child")

    class RecordingForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class MethodParent(FilterSet):
        partner = RelatedFilter(MethodChild, field_name="partner")
        own_number = NumberFilter(field_name="signed_big")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = RecordingForm

    async def async_only_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        del cls, info
        events.append("hook")
        return rows

    def recording_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def async_annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "MethodTimingTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                async_annotated_target
                if spelling == "async-valid"
                else recording_target
                if spelling in {"valid", "sibling-valid"}
                else async_only_target,
            ),
        },
    )
    schema = _schema(
        MethodParent,
        scalar_models.NullableScalarSpecimen,
        transport="async" if spelling == "async-valid" else "sync",
        fields=("label",),
        targets=(target,),
    )
    criterion: JSONObject = (
        {"in_": ["sent"]} if family == "list" else {"start": "sent", "end": "sent"}
    )
    where: JSONObject = {"partner__lag_sent": criterion}
    if spelling in {"valid", "async-valid", "sibling-valid"}:
        if spelling == "sibling-valid":
            where["partner__lag_among"] = {"in_": ["1 00:00:00"]}
        payload = _post(
            schema,
            where,
            transport="async" if spelling == "async-valid" else "sync",
            selection="label",
        )
        assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
        assert events == (
            ["form.clean", "hook", "method"]
            if spelling == "valid"
            else ["hook", "form.clean", "method"]
        )
        assert received == ([["sent"]] if family == "list" else [["sent", "sent"]])
    else:
        where["own_number"] = "abc"
        if spelling == "logical":
            where = {"or_": [where]}
        payload = _post(schema, where, transport="sync", selection="label")
        key = "or_0__own_number" if spelling == "logical" else "own_number"
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {key: [{"message": "Enter a number.", "code": "invalid"}]},
            },
        )
        assert events == ["form.clean"] * (2 if spelling == "logical" else 1)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("days", "labels"),
    [
        pytest.param(1, None, id="consumer-inner-validator"),
        pytest.param(2, ["of-two-days"], id="consumer-inner-accepts"),
    ],
)
@pytest.mark.parametrize("owner", ["form", "filter"])
@pytest.mark.parametrize("transport", ["async", "sync"])
def test_filter_or_materialized_form_keeps_its_owned_range_bound_validator(
    days: int,
    labels: list[str] | None,
    owner: str,
    transport: str,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    for child_days in (1, 2):
        child = cleaned_specimen(f"child-{child_days}", kept=True)
        child.parent = kept
        child.occurred_at = kept.occurred_at + datetime.timedelta(days=child_days)
        child.save(update_fields=["parent", "occurred_at"])
        scalar_models.NullableScalarSpecimen.objects.create(
            label=f"of-{'one' if child_days == 1 else 'two'}-days",
            partner=child,
        )
    events: list[str] = []

    class RecordingForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class MaterializedRangeParent(FilterSet):
        partner = RelatedFilter(_AnnotationCriteriaSet, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = RecordingForm

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            if owner == "filter":
                field = self.filters["partner__lag_span"].field
                assert isinstance(field, RangeField)
                field.bound_field = FormDurationField()
            else:
                field = self.form.fields["partner__lag_span"]
                assert isinstance(field, RangeField)
                field.bound_field = FormDurationField()
            assert isinstance(field, RangeField)
            bound = field.bound_field
            assert isinstance(bound, FormField)
            bound.validators.append(_reject_one_day)
            _ = self.form

    def annotated_sync(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "MaterializedRangeTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                annotated_async if transport == "async" else annotated_sync,
            ),
        },
    )
    schema = _schema(
        MaterializedRangeParent,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    bound = f"{days} 00:00:00"
    payload = _post(
        schema,
        {"partner__lag_span": {"start": bound, "end": bound}},
        transport=transport,
        selection="label",
    )
    if labels is None:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "partner__lag_span": [
                        {"message": "One day is reserved.", "code": "reserved"},
                    ],
                },
            },
        )
    else:
        assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
    assert events == (["form.clean"] if labels is None else ["form.clean", "hook"])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("member", "with_sibling", "labels"),
    [
        pytest.param("1 00:00:00", True, None, id="owned-inner-survives-promotion"),
        pytest.param("2 00:00:00", True, ["of-two"], id="allowed-inner-and-sibling"),
        pytest.param("1 00:00:00", False, None, id="owned-inner-keeps-necessary-owner"),
    ],
)
def test_projected_child_inner_range_validator_survives_sibling_promotion(
    member: str,
    labels: list[str] | None,
    *,
    with_sibling: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    for days in (1, 2):
        child = cleaned_specimen(f"child-{days}", kept=True)
        child.parent = kept
        child.occurred_at = kept.occurred_at + datetime.timedelta(days=days)
        child.save(update_fields=["parent", "occurred_at"])
        scalar_models.NullableScalarSpecimen.objects.create(
            label=f"of-{'one' if days == 1 else 'two'}",
            partner=child,
        )
    events: list[str] = []

    class OwnedChild(_AnnotationCriteriaSet):
        constructor_calls: ClassVar[list[str]] = []

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            rows = self.queryset
            assert rows is not None
            type(self).constructor_calls.append(rows.db)
            field = self.filters["lag_span"].field
            assert isinstance(field, RangeField)
            field.bound_field = FormDurationField(validators=[_reject_one_day])

    class RecordingForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class OwnedParent(FilterSet):
        partner = RelatedFilter(OwnedChild, field_name="partner")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = RecordingForm

    def annotated_target(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "OwnedChildPromotionTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_target)},
    )
    schema = _schema(
        OwnedParent,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
    )
    where: JSONObject = {"partner__lag_span": {"start": member, "end": member}}
    if with_sibling:
        where["partner__kids_among"] = {"in_": ["0"]}
    payload = _post(schema, where, transport="sync", selection="label")
    if labels is None:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "partner__lag_span": [
                        {"message": "One day is reserved.", "code": "reserved"},
                    ],
                },
            },
        )
    else:
        assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
    assert OwnedChild.constructor_calls == ["default"]
    assert events == (
        ["hook", "form.clean"]
        if with_sibling
        else ["form.clean"]
        if labels is None
        else ["form.clean", "hook"]
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("member", "labels", "events_after"),
    [
        pytest.param(
            "junk",
            None,
            ["branch-hook", "form.clean"],
            id="owner-before-invalid-form",
        ),
        pytest.param(
            "4",
            ["matching-book"],
            ["branch-hook", "form.clean", "shelf-hook"],
            id="earlier-hop-at-application",
        ),
    ],
)
def test_multihop_flat_annotation_prepares_only_its_owning_hop(
    member: str,
    labels: list[str] | None,
    events_after: list[str],
) -> None:
    branch = models.Branch.objects.create(name="West")
    shelf = models.Shelf.objects.create(branch=branch, code="west")
    models.Book.objects.create(shelf=shelf, title="matching-book")
    events: list[str] = []

    class BranchCriteria(FilterSet):
        name_lengths = ListFilter(field_name="name_len", lookup_expr="in")

        class Meta:
            model = models.Branch
            fields = []

    class ShelfCriteria(FilterSet):
        branch = RelatedFilter(BranchCriteria, field_name="branch")

        class Meta:
            model = models.Shelf
            fields = []

    class RecordingForm(Form):
        @override
        def clean(self) -> dict[str, object] | None:
            events.append("form.clean")
            return super().clean()

    class BookCriteria(FilterSet):
        shelf = RelatedFilter(ShelfCriteria, field_name="shelf")
        branch_name_lengths = ListFilter(field_name="shelf__branch__name_len", lookup_expr="in")

        class Meta:
            model = models.Book
            fields = []
            form = RecordingForm

    def shelf_hook(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        events.append("shelf-hook")
        return rows

    def branch_hook(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        events.append("branch-hook")
        return rows.annotate(name_len=Length("name"))

    shelf_type = make_django_type(
        "OwnedAnnotationShelf",
        models.Shelf,
        ("code",),
        node=False,
        namespace_extra={"get_queryset": classmethod(shelf_hook)},
    )
    branch_type = make_django_type(
        "OwnedAnnotationBranch",
        models.Branch,
        ("name",),
        node=False,
        namespace_extra={"get_queryset": classmethod(branch_hook)},
    )
    schema = _schema(
        BookCriteria,
        models.Book,
        transport="sync",
        fields=("title",),
        targets=(shelf_type, branch_type),
    )
    payload = _post(
        schema,
        {"branch_name_lengths": {"in_": [member]}},
        transport="sync",
        selection="title",
    )
    if labels is None:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "branch_name_lengths": [
                        {"message": "Enter a number.", "code": "invalid"},
                    ],
                },
            },
        )
    else:
        assert payload == {"data": {"rows": [{"title": label} for label in labels]}}, payload
    assert events == events_after


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_flat_nested_and_logical_annotation_leaves_share_one_target_hook(
    transport: str,
) -> None:
    """One declared hop supplies every active spelling's annotated form field."""
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    def annotated_once(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "OnceAnnotatedPartnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_once)},
    )
    schema = _schema(
        _PartnerAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    assert calls == []
    payload = _post(
        schema,
        {
            "or_": [
                {
                    "partner": {"lag_among": {"in_": ["1 00:00:00"]}},
                    "partner__kids_among": {"in_": ["0"]},
                },
                {"partner__lag_span": {"start": "1 00:00:00"}},
            ],
        },
        transport=transport,
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
def test_a_flat_annotation_field_awaits_its_async_only_target_hook() -> None:
    """Flat form cleaning uses the target rows awaited by the async apply path."""
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    calls: list[str] = []

    async def annotated_async(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "AsyncAnnotatedPartnerTarget",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(annotated_async)},
    )
    schema = _schema(
        _PartnerAnnotationCriteriaSet,
        scalar_models.NullableScalarSpecimen,
        transport="async",
        fields=("label",),
        targets=(target,),
    )
    assert calls == []
    payload = _post(
        schema,
        {"partner__lag_among": {"in_": ["1 00:00:00"]}},
        transport="async",
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert calls == ["default"]


class _ReadingFiltersSet(FilterSet):
    """A consumer constructor that materializes the filters it inspects."""

    def __init__(
        self,
        data: Mapping[str, object] | None = None,
        queryset: QuerySet[Model] | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        assert self.filters


def _expanded_set(base: type[FilterSet]) -> type[FilterSet]:

    class FinesEmailPatronFilter(base):
        fines = RangeFilter(field_name="lifetime_fines_cents", lookup_expr="range")
        emails = ListFilter(field_name="email", lookup_expr="in")
        picks = MultipleChoiceFilter(field_name="email", choices=[("a@x.test", "a@x.test")])
        name = CharFilter(field_name="name")

        class Meta:
            model = models.Patron
            fields = []

    class FinesEmailLoanFilter(FilterSet):
        patron = RelatedFilter(FinesEmailPatronFilter, field_name="patron")

        class Meta:
            model = models.Loan
            fields = []

    return FinesEmailLoanFilter


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("settled", [False, True], ids=["plain-child", "child-init"])
@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            {"patron__fines": [1, 5]},
            (
                "RangeFilter consumes a range input with only 'start' / 'end' axes for its "
                "'patron__fines' input, but received list [1, 5]; send a mapping or input object "
                "with 'start' / 'end' (generated filter inputs reject this shape during GraphQL validation)."
            ),
        ),
        (
            {"patron__emails": "abc"},
            (
                "ListFilter consumes a list of values for its 'patron__email' input, but received a "
                "non-list container (str 'abc') for the list input; send a list (generated "
                "filter inputs deliver a list after GraphQL coercion)."
            ),
        ),
        (
            {"patron__picks": "abc"},
            (
                "MultipleChoiceFilter consumes a list of values for its 'patron__email' input, but "
                "received a non-list container (str 'abc') for the multiple-choice list; send a list "
                "(generated filter inputs deliver a list after GraphQL coercion)."
            ),
        ),
        (
            {"patron__name": {"exact": {"k": "v"}}},
            (
                "FilterSet {owner}: filter 'patron__name' received a dict value ({{'k': 'v'}}) but "
                "CharFilter consumes a single scalar form key. A dict value here would be splatted "
                "into unknown form-data keys the form silently ignores, dropping the filter. Pass "
                "the schema value shape for this filter (a scalar, a list, or a range {{start, end}} "
                "input on a RangeFilter primitive)."
            ),
        ),
    ],
    ids=[
        "range",
        "list",
        "multiple-choice",
        "dict",
    ],
)
def test_an_expanded_malformed_argument_names_the_consumers_original_filter_class(
    transport: str,
    *,
    settled: bool,
    value: JSONObject,
    message: str,
) -> None:
    target = _expanded_set(_ReadingFiltersSet if settled else FilterSet)
    patron_type = make_django_type("ExpandedPatronTarget", models.Patron, ("name",), node=False)
    schema = _schema(
        target,
        models.Loan,
        transport=transport,
        fields=("id",),
        targets=(patron_type,),
    )
    expected = message.format(owner=target.__qualname__) if "{owner}" in message else message
    _refused(_post(schema, value, transport=transport, selection="id"), expected)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("cap", "nesting", "refused"),
    [(8, 8, False), (8, 12, True), (32, 12, False)],
    ids=["default-boundary", "over-default", "raised-consumer-budget"],
)
def test_the_consumer_depth_budget_applies_to_json_criteria_before_rows_are_served(
    transport: str,
    cap: int,
    nesting: int,
    *,
    refused: bool,
) -> None:
    models.Branch.objects.create(name="match")
    models.Branch.objects.create(name="decoy")

    class BudgetedBranchFilter(FilterSet):
        _MAX_LOGIC_DEPTH = cap

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    criteria: JSONObject = {"name": "match"}
    for _ in range(nesting):
        criteria = {"and_": [criteria]}
    schema = _schema(
        BudgetedBranchFilter,
        models.Branch,
        transport=transport,
        resource_policy={"max_value_depth": 64},
    )
    payload = _post(schema, criteria, transport=transport)
    if refused:
        _refused(
            payload,
            f"FilterSet {BudgetedBranchFilter.__qualname__}: logical-branch nesting exceeded "
            f"_MAX_LOGIC_DEPTH={cap}. Flatten the filter input or split into multiple queries.",
        )
    else:
        assert payload == {"data": {"rows": [{"name": "match"}]}}


class _RefusingSqlLookup(Lookup[object]):
    """An installed consumer lookup whose own SQL compiler raises a TypeError."""

    lookup_name = "refuses_sql"

    @override
    def as_sql(self, compiler: object, connection: object) -> NoReturn:
        raise TypeError("consumer lookup")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_consumer_lookup_compiler_type_error_keeps_its_own_verdict(transport: str) -> None:
    with register_lookup(django_models.DateTimeField, _RefusingSqlLookup):

        class RefusingSqlFilter(FilterSet):
            stamped = DateTimeFilter(field_name="occurred_at", lookup_expr="refuses_sql")

            class Meta:
                model = scalar_models.ScalarSpecimen
                fields = []

        schema = _schema(
            RefusingSqlFilter,
            scalar_models.ScalarSpecimen,
            transport=transport,
            fields=("label",),
        )
        assert _post(schema, {}, transport=transport, selection="label") == {"data": {"rows": []}}
        _refused(
            _post(
                schema,
                {
                    "stamped": datetime.datetime(
                        2021,
                        1,
                        1,
                        tzinfo=datetime.timezone.utc,
                    ).isoformat(),
                },
                transport=transport,
                selection="label",
            ),
            "consumer lookup",
        )


def _gate_first_set() -> type[FilterSet]:
    class GateFirstFilter(FilterSet):
        email_must_have_at_sign = CharFilter(field_name="email", method="filter_email")

        class Meta:
            model = models.Patron
            fields = {"name": ["exact"]}

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            email_filter = self.filters["email_must_have_at_sign"]
            email_filter.field.validators.append(_validate_email_must_have_at_sign)

        def filter_email(
            self,
            queryset: QuerySet[models.Patron],
            _name: str,
            value: str,
        ) -> QuerySet[models.Patron]:
            return queryset.filter(email=value)

        def check_name_permission(self, request: object) -> None:
            user = read_attr(request, "user", None)
            if not user or not read_attr(user, "is_staff", None):
                raise GraphQLError("gate-first-nope")

    return GateFirstFilter


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
def test_permission_verdict_precedes_form_validation_for_the_same_invalid_input(
    transport: str,
    viewer: str,
) -> None:
    create_users(1)
    models.Patron.objects.create(name="P", email="p@x.io")
    client = AsyncClient() if transport == "async" else Client()
    if viewer == "staff":
        client.force_login(User.objects.get(username="staff_1"))
    schema = _schema(_gate_first_set(), models.Patron, transport=transport)
    payload = _post(
        schema,
        {"name": {"exact": "P"}, "email_must_have_at_sign": "no-at-sign"},
        transport=transport,
        client=client,
    )
    if viewer == "anonymous":
        _refused(payload, "gate-first-nope")
    else:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {
                    "email_must_have_at_sign": [
                        {"message": "missing @", "code": "missing_at_sign"},
                    ],
                },
            },
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("operator", "value", "detail"),
    [
        (
            "or_",
            {"name": {"exact": "x"}},
            (
                "logical branch 'or' takes a list of filter inputs, got a dict. Wrap the "
                "clauses as 'or: [{...}]'."
            ),
        ),
        (
            "not_",
            [{"name": {"exact": "x"}}],
            (
                "logical branch 'not' takes a single filter input, got a list. Wrap the "
                "clause as 'not: {...}', not a list."
            ),
        ),
        (
            "not_",
            "name",
            (
                "logical branch 'not' takes filter inputs, got a str ('name'). Each clause "
                "must be a mapping or filter-input object, not a scalar."
            ),
        ),
        (
            "or_",
            ["name"],
            (
                "logical branch 'or' takes filter inputs, got a str ('name'). Each clause "
                "must be a mapping or filter-input object, not a scalar."
            ),
        ),
        (
            "and_",
            [42],
            (
                "logical branch 'and' takes filter inputs, got a int (42). Each clause must "
                "be a mapping or filter-input object, not a scalar."
            ),
        ),
    ],
    ids=[
        "or-container",
        "not-container",
        "not-element",
        "or-element",
        "and-element",
    ],
)
def test_malformed_json_logical_criteria_refuse_the_container_or_element_that_was_sent(
    transport: str,
    operator: str,
    value: object,
    detail: str,
) -> None:
    models.Branch.objects.create(name="must not be returned")
    filterset = _branch_filter()
    schema = _schema(filterset, models.Branch, transport=transport)
    _refused(
        _post(schema, {operator: value}, transport=transport),
        f"FilterSet {filterset.__qualname__}: {detail}",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    ("value", "detail"),
    [
        (
            "match",
            (
                "filter input field 'name' has no exact lookup to take a bare value (lookups:"
                " ['i_contains', 'i_starts_with']); pass an operator bag."
            ),
        ),
        (
            {"gt": "match"},
            (
                "filter input field 'name' has no 'gt' lookup (lookups: ['i_contains', "
                "'i_starts_with']); it would apply nothing."
            ),
        ),
    ],
    ids=["no-bare-exact", "no-requested-lookup"],
)
def test_an_explicit_pattern_only_head_refuses_an_unpublished_lookup(
    transport: str,
    value: object,
    detail: str,
) -> None:
    models.Branch.objects.create(name="alpha-match")
    models.Branch.objects.create(name="other")

    class PatternBranchFilter(FilterSet):
        class Meta:
            model = models.Branch
            fields = {"name": ["icontains", "istartswith"]}

    schema = _schema(PatternBranchFilter, models.Branch, transport=transport)
    assert _post(schema, {"name": {"i_contains": "match"}}, transport=transport) == {
        "data": {"rows": [{"name": "alpha-match"}]},
    }
    _refused(
        _post(schema, {"name": value}, transport=transport),
        f"FilterSet {PatternBranchFilter.__qualname__}: {detail}",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_nested_logic_and_real_related_hops_share_the_same_depth_budget(transport: str) -> None:
    from apps.kanban import filters as kanban_filters  # noqa: PLC0415 - reloaded declarations
    from apps.kanban import models as kanban_models  # noqa: PLC0415 - reloaded declarations

    filterset = kanban_filters.CardFilter
    criteria: JSONObject = {"number": {"exact": 21}}
    for _ in range(filterset._MAX_LOGIC_DEPTH + 2):
        criteria = {"or_": [{"dependencies": criteria}]}
    schema = _schema(
        filterset,
        kanban_models.Card,
        transport=transport,
        fields=("number",),
        resource_policy={"max_value_depth": 64},
    )
    assert _post(schema, {}, transport=transport, selection="number") == {
        "data": {
            "rows": [
                {"number": card.number} for card in kanban_models.Card.objects.order_by("pk")
            ],
        },
    }
    _refused(
        _post(schema, criteria, transport=transport, selection="number"),
        f"FilterSet {filterset.__qualname__}: logical-branch nesting exceeded "
        f"_MAX_LOGIC_DEPTH={filterset._MAX_LOGIC_DEPTH}. Flatten the filter input or split "
        "into multiple queries.",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("criteria", "detail"),
    [
        (
            {"or": {"name": {"exact": "match"}}},
            (
                "logical branch 'or' takes a list of filter inputs, got a dict. Wrap the "
                "clauses as 'or: [{...}]'."
            ),
        ),
        (
            {"not": "name"},
            (
                "logical branch 'not' takes filter inputs, got a str ('name'). Each clause "
                "must be a mapping or filter-input object, not a scalar."
            ),
        ),
        (
            {"or": ["name"]},
            (
                "logical branch 'or' takes filter inputs, got a str ('name'). Each clause "
                "must be a mapping or filter-input object, not a scalar."
            ),
        ),
        (
            {"and": [42]},
            (
                "logical branch 'and' takes filter inputs, got a int (42). Each clause must "
                "be a mapping or filter-input object, not a scalar."
            ),
        ),
    ],
    ids=[
        "container",
        "not-element",
        "or-element",
        "and-element",
    ],
)
def test_a_directly_constructed_set_refuses_malformed_logic_over_http(
    criteria: JSONObject,
    detail: str,
) -> None:
    """The public constructor/.qs path validates a raw logical tree before returning rows."""
    models.Branch.objects.create(name="match")
    models.Branch.objects.create(name="decoy")
    filterset = _branch_filter()
    schema = _schema(filterset, models.Branch, transport="sync", direct=True)
    assert _post(schema, {"name": "match"}, transport="sync") == {
        "data": {"rows": [{"name": "match"}]},
    }
    _refused(
        _post(schema, criteria, transport="sync"),
        f"FilterSet {filterset.__qualname__}: {detail}",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("value", "refused"),
    [({"start": 1, "end": 5}, False), ({"end": 5}, True), ({}, True)],
    ids=["both-bounds", "end-only", "no-bound"],
)
def test_a_required_upstream_range_reads_the_keys_its_real_widget_requires(
    value: JSONObject,
    *,
    refused: bool,
) -> None:
    """Upstream RangeField accepts both supplied bounds and rejects an absent required bound."""
    models.Patron.objects.create(name="inside", email="in@example.test", lifetime_fines_cents=3)
    models.Patron.objects.create(name="outside", email="out@example.test", lifetime_fines_cents=9)

    class RequiredRangeFilter(FilterSet):
        fines = UpstreamRangeFilter(field_name="lifetime_fines_cents", required=True)

        class Meta:
            model = models.Patron
            fields = []

    payload = _post(
        _schema(RequiredRangeFilter, models.Patron, transport="sync"),
        {"fines": value},
        transport="sync",
    )
    if refused:
        _refused(
            payload,
            "Invalid filter input",
            extensions={
                "code": "FILTER_INVALID",
                "errors": {"fines": [{"message": "This field is required.", "code": "required"}]},
            },
        )
    else:
        assert payload == {"data": {"rows": [{"name": "inside"}]}}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_declared_head_refuses_an_extra_lookup_after_an_active_valid_lookup(
    transport: str,
) -> None:
    """A consumer-declared head cannot quietly drop its second, unpublished lookup."""
    models.Branch.objects.create(name="alpha-match")
    models.Branch.objects.create(name="other")

    class DeclaredBranchFilter(FilterSet):
        custom = CharFilter(field_name="name", lookup_expr="icontains")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    schema = _schema(DeclaredBranchFilter, models.Branch, transport=transport)
    assert _post(schema, {"custom": {"i_contains": "match"}}, transport=transport) == {
        "data": {"rows": [{"name": "alpha-match"}]},
    }
    _refused(
        _post(
            schema,
            {"custom": {"i_contains": "match", "starts_with": "m"}},
            transport=transport,
        ),
        f"FilterSet {DeclaredBranchFilter.__qualname__}: filter input field 'custom' has no "
        "'starts_with' lookup (lookups: ['i_contains']); it would apply nothing.",
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize(
    "scenario",
    [
        "valid",
        "year",
        "text",
        "arm",
    ],
)
def test_plain_cached_consumer_form_uses_the_complete_apply_protocol(
    transport: str,
    scenario: str,
) -> None:
    cleaned_specimen("kept", kept=True)
    models.Branch.objects.create(name="choice")
    forms_built: list[Form] = []
    cleans: list[Form] = []

    class ConsumerForm(Form):
        @override
        def full_clean(self) -> None:
            cleans.append(self)
            super().full_clean()

    class Criteria(FilterSet):
        pick = ModelMultipleChoiceFilter(
            field_name="label",
            queryset=models.Branch.objects.all(),
            to_field_name="name",
        )

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = {"occurred_on": ["year__gt"], "signed_big": ["exact"]}
            form = ConsumerForm

        @property
        @override
        def form(self) -> Form:
            if not hasattr(self, "_consumer_form"):
                self._consumer_form = self.get_form_class()(self.data, prefix=self.form_prefix)
                forms_built.append(self._consumer_form)
            return self._consumer_form

    scenarios: dict[str, JSONObject] = {
        "valid": {"occurred_on": {"year_gt": "2000"}, "or_": [{"signed_big": "7"}]},
        "year": {"occurred_on": {"year_gt": "99999"}},
        "text": {"pick": ["\ud800"]},
        "arm": {"or_": [{"signed_big": "abc"}]},
    }
    criteria = scenarios[scenario]
    schema = _schema(
        Criteria,
        scalar_models.ScalarSpecimen,
        transport=transport,
        fields=("label",),
    )
    payload = _post(schema, criteria, transport=transport, selection="label")
    if scenario == "valid":
        assert payload == {"data": {"rows": [{"label": "kept"}]}}, payload
    else:
        key = {"year": "occurred_on__year__gt", "text": "pick", "arm": "or_0__signed_big"}[
            scenario
        ]
        code = "invalid"
        if scenario == "text":
            assert json_at(payload, "errors", 0, "extensions", "errors", key, 0, "message") == (
                "Text contains invalid Unicode (unpaired surrogate code points)."
            )
        assert json_at(payload, "errors", 0, "extensions", "code") == "FILTER_INVALID", payload
        assert json_at(payload, "errors", 0, "extensions", "errors", key, 0, "code") == code
    assert len(forms_built) == (2 if scenario in {"valid", "arm"} else 1)
    assert len(cleans) == (0 if scenario == "text" else len(forms_built))
    assert all(any(form is owned for owned in forms_built) for form in cleans)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("invalid", [False, True])
def test_consumer_range_parser_owns_native_validation_before_annotation_hook(
    transport: str,
    *,
    invalid: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    events: list[str] = []

    class CompleteRangeField(RangeField):
        @override
        def to_python(self, value: object) -> object:
            events.append("parser")
            if value in self.empty_values:
                return None
            values = require(value, is_list_or_tuple)
            return [
                None if bound is None else FormDurationField().clean(bound) for bound in values
            ]

    class CompleteRangeFilter(RangeFilter):
        field_class = CompleteRangeField

    class Criteria(FilterSet):
        lag = CompleteRangeFilter(field_name="partner__lag", lookup_expr="range")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

    async def async_owner(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    def sync_owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "CompleteRangeParserOwner",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                async_owner if invalid or transport == "async" else sync_owner,
            ),
        },
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"lag": {"start": "not-a-duration" if invalid else "1 00:00:00"}},
        transport=transport,
        selection="label",
    )
    if invalid:
        assert json_at(payload, "errors", 0, "extensions", "code") == "FILTER_INVALID", payload
        assert json_at(payload, "errors", 0, "extensions", "errors", "lag", 0, "code") == "invalid"
        assert events == ["parser"]
    else:
        assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
        assert events == ["parser", "hook"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("empty", ["list", "disabled", "unchanged"])
def test_inactive_missing_inner_parser_never_acquires_annotation_owner(
    transport: str,
    empty: str,
) -> None:
    scalar_models.NullableScalarSpecimen.objects.create(label="kept")
    calls: list[str] = []

    class EmptyForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(
                data=data,
                prefix=prefix,
                empty_permitted=empty == "unchanged",
                use_required_attribute=False,
            )
            if empty == "disabled":
                self.fields["lag"].disabled = True
                self.fields["lag"].initial = []

    class Criteria(FilterSet):
        lag = ListFilter(field_name="partner__lag", lookup_expr="in")
        amount = NumberFilter(field_name="signed_big", lookup_expr="gt")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = EmptyForm

    async def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "InactiveMissingParserOwner",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(owner)},
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    where: JSONObject = (
        {} if empty == "unchanged" else {"lag": {"in_": []}, "amount": {"gt": "1e51"}}
    )
    payload = _post(schema, where, transport=transport, selection="label")
    if empty == "unchanged":
        assert payload == {"data": {"rows": [{"label": "kept"}]}}, payload
    else:
        assert json_at(payload, "errors", 0, "extensions", "code") == "FILTER_INVALID", payload
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_invalid_root_stops_logical_construction_before_missing_parser_owner(
    transport: str,
) -> None:
    scalar_models.NullableScalarSpecimen.objects.create(label="kept")
    constructed: list[FilterSet] = []
    calls: list[str] = []

    class Criteria(FilterSet):
        lag = ListFilter(field_name="partner__lag", lookup_expr="in")
        amount = NumberFilter(field_name="signed_big", lookup_expr="gt")

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            constructed.append(self)

    async def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "InvalidRootParserOwner",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={"get_queryset": classmethod(owner)},
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(
        schema,
        {"amount": {"gt": "1e51"}, "or_": [{"lag": {"in_": ["1 00:00:00"]}}]},
        transport=transport,
        selection="label",
    )
    assert json_at(payload, "errors", 0, "extensions", "code") == "FILTER_INVALID", payload
    assert len(constructed) == 1
    assert calls == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", ["repair", "pop", "pop-async"])
def test_raw_reused_generated_form_binds_only_after_outer_full_clean(mode: str) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    scalar_models.NullableScalarSpecimen.objects.create(label="unrelated")
    events: list[str] = []

    class InnerForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(
                data=data,
                prefix=prefix,
                empty_permitted=True,
                use_required_attribute=False,
            )

        @override
        def full_clean(self) -> None:
            super().full_clean()
            events.append("inner")
            self.cleaned_data["lag_among"] = [datetime.timedelta(days=999999999)]

    class Source(_UndeclaredAnnotationCriteriaSet):
        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = InnerForm

    generated = type(
        Source(data={}, queryset=scalar_models.NullableScalarSpecimen.objects.all()).form,
    )

    class OuterForm(generated):
        @override
        def full_clean(self) -> None:
            super().full_clean()
            events.append("outer")
            if mode == "repair":
                self.cleaned_data["lag_among"] = [datetime.timedelta(days=1)]
            else:
                self.cleaned_data.pop("lag_among", None)

    class Criteria(_UndeclaredAnnotationCriteriaSet):
        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = OuterForm

    def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def async_owner(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "ReusedOuterFormOwner",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(async_owner if mode == "pop-async" else owner),
        },
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport="sync",
        fields=("label",),
        targets=(target,),
        direct=True,
    )
    payload = _post(schema, {}, transport="sync", selection="label")
    labels = ["of-child"] if mode == "repair" else ["of-child", "unrelated"]
    assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
    assert events == ["inner", "outer", *(["hook"] if mode == "repair" else [])]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("always", [False, True])
def test_absent_disabled_multiple_choice_initial_obeys_native_noop_before_owner(
    transport: str,
    *,
    always: bool,
) -> None:
    child = cleaned_specimen("child", kept=True)
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    scalar_models.NullableScalarSpecimen.objects.create(label="unrelated")
    calls: list[str] = []

    class InitialForm(Form):
        def __init__(
            self,
            data: dict[str, object] | QueryDict | None = None,
            *,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, prefix=prefix)
            self.fields["kids"].disabled = True
            self.fields["kids"].initial = ["0", "1"]

    class ChoicesFilter(MultipleChoiceFilter):
        always_filter = always

    class Criteria(FilterSet):
        kids = ChoicesFilter(
            field_name="partner__kids",
            choices=[("0", "None"), ("1", "One")],
            required=True,
        )

        class Meta:
            model = scalar_models.NullableScalarSpecimen
            fields = []
            form = InitialForm

    def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    async def async_owner(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        calls.append(rows.db)
        return _annotating_target(cls, rows, info)

    target = make_django_type(
        "AbsentMultipleChoiceOwner",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(
                async_owner if transport == "async" or not always else owner,
            ),
        },
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    payload = _post(schema, {}, transport=transport, selection="label")
    labels = ["of-child"] if always else ["of-child", "unrelated"]
    assert payload == {"data": {"rows": [{"label": label} for label in labels]}}, payload
    assert calls == (["default"] if always else [])


@pytest.mark.skipif(
    os.environ.get("FAKESHOP_SHARDED") != "1",
    reason="requires FAKESHOP_SHARDED=1",
)
@pytest.mark.django_db(transaction=True, databases=["default", "shard_b"])
@pytest.mark.parametrize("family", ["complete", "missing-parser"])
def test_async_annotation_readiness_uses_constructor_selected_shard(family: str) -> None:
    branch = models.Branch.objects.using("shard_b").create(name="remote")
    models.Shelf.objects.using("shard_b").create(branch=branch, code="remote")
    models.Shelf.objects.create(branch=models.Branch.objects.create(name="local"), code="local")
    calls: list[str] = []

    class Criteria(FilterSet):
        rank = (
            NumberFilter(field_name="branch__rank")
            if family == "complete"
            else ListFilter(field_name="branch__rank", lookup_expr="in")
        )

        class Meta:
            model = models.Shelf
            fields = []

        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data, queryset, request=request, prefix=prefix)
            assert self.queryset is not None
            self.queryset = self.queryset.using("shard_b")

    async def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        return rows.annotate(
            rank=django_models.Value(1, output_field=django_models.IntegerField()),
        )

    target = make_django_type(
        "ConstructorShardAnnotationOwner",
        models.Branch,
        ("name",),
        node=False,
        namespace_extra={"get_queryset": classmethod(owner)},
    )
    schema = _schema(
        Criteria,
        models.Shelf,
        transport="async",
        fields=("code",),
        targets=(target,),
    )
    where: JSONObject = {"rank": "1" if family == "complete" else {"in_": ["1"]}}

    async def bounded_request() -> JSONObject:
        return await asyncio.wait_for(
            _async_post(
                "query($where: JSON!) { rows(where: $where) { code } }",
                {"where": where},
                None,
            ),
            timeout=5,
        )

    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = asyncio.run(bounded_request())
    finally:
        _CURRENT["schema"] = None
    assert payload == {"data": {"rows": [{"code": "remote"}]}}, payload
    assert calls == ["shard_b"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("policy", ["form", "filterset"])
def test_consumer_form_validation_policy_keeps_accepted_root_logical_arms(
    transport: str,
    policy: str,
) -> None:
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)

    class AcceptingForm(Form):
        @override
        def is_valid(self) -> bool:
            return True if policy == "form" else super().is_valid()

    class Criteria(FilterSet):
        label = CharFilter(field_name="label")
        bad = NumberFilter(field_name="signed_big")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []
            form = AcceptingForm

        @classmethod
        @override
        def _validate_form_or_raise(cls, filterset_instance: FilterSet) -> None:
            if policy != "filterset":
                super()._validate_form_or_raise(filterset_instance)

    schema = _schema(
        Criteria,
        scalar_models.ScalarSpecimen,
        transport=transport,
        fields=("label",),
    )
    payload = _post(
        schema,
        {"bad": "abc", "or_": [{"label": "kept"}]},
        transport=transport,
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "kept"}]}}, payload


@pytest.mark.django_db(transaction=True)
def test_raw_native_root_error_preserves_safe_logical_sibling_filters() -> None:
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)

    class Criteria(FilterSet):
        label = CharFilter(field_name="label")
        bad = NumberFilter(field_name="signed_big")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    schema = _schema(
        Criteria,
        scalar_models.ScalarSpecimen,
        transport="sync",
        fields=("label",),
        direct=True,
    )
    payload = _post(
        schema,
        {"bad": "abc", "or_": [{"label": "kept"}]},
        transport="sync",
        selection="label",
    )
    assert payload == {"data": {"rows": [{"label": "kept"}]}}, payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("family", ["list", "range"])
def test_plain_cached_consumer_form_receives_its_missing_annotation_parser(
    transport: str,
    family: str,
) -> None:
    branch = models.Branch.objects.create(name="branch")
    models.Shelf.objects.create(branch=branch, code="kept")
    events: list[str] = []

    class ConsumerForm(Form):
        @override
        def full_clean(self) -> None:
            events.append("clean")
            super().full_clean()

    class Criteria(FilterSet):
        rank = (
            ListFilter(field_name="branch__rank", lookup_expr="in")
            if family == "list"
            else RangeFilter(field_name="branch__rank", lookup_expr="range")
        )

        class Meta:
            model = models.Shelf
            fields = []
            form = ConsumerForm

        @property
        @override
        def form(self) -> Form:
            if not hasattr(self, "_consumer_form"):
                self._consumer_form = self.get_form_class()(self.data, prefix=self.form_prefix)
            return self._consumer_form

    def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        events.append("hook")
        return rows.annotate(
            rank=django_models.Value(1, output_field=django_models.IntegerField()),
        )

    async def async_owner(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        return owner(cls, rows, info)

    target = make_django_type(
        "PlainFormMissingParserOwner",
        models.Branch,
        ("name",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(async_owner if transport == "async" else owner),
        },
    )
    schema = _schema(
        Criteria,
        models.Shelf,
        transport=transport,
        fields=("code",),
        targets=(target,),
    )
    value: JSONObject = {"in_": ["1"]} if family == "list" else {"start": "1", "end": "1"}
    payload = _post(schema, {"rank": value}, transport=transport, selection="code")
    assert payload == {"data": {"rows": [{"code": "kept"}]}}, payload
    assert events == ["hook", "clean"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("logical", [False, True])
@pytest.mark.parametrize("policy", ["form", "filterset"])
def test_accepted_native_field_error_keeps_active_annotation_binding(
    transport: str,
    policy: str,
    *,
    logical: bool,
) -> None:
    kept = cleaned_specimen("kept", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = kept
    child.occurred_at = kept.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])
    scalar_models.NullableScalarSpecimen.objects.create(label="of-child", partner=child)
    scalar_models.NullableScalarSpecimen.objects.create(label="unrelated")
    events: list[str] = []

    class AcceptingForm(Form):
        @override
        def full_clean(self) -> None:
            events.append("clean")
            super().full_clean()

        @override
        def is_valid(self) -> bool:
            return set(self.errors).issubset({"bad"}) if policy == "form" else super().is_valid()

    class Criteria(_UndeclaredAnnotationCriteriaSet):
        bad = NumberFilter(field_name="signed_big")

        class Meta(_UndeclaredAnnotationCriteriaSet.Meta):
            form = AcceptingForm

        @classmethod
        @override
        def _validate_form_or_raise(cls, filterset_instance: FilterSet) -> None:
            if policy != "filterset":
                super()._validate_form_or_raise(filterset_instance)

    def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        events.append("hook")
        return _annotating_target(cls, rows, info)

    async def async_owner(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        return owner(cls, rows, info)

    target = make_django_type(
        "AcceptedNativeErrorAnnotationOwner",
        scalar_models.ScalarSpecimen,
        ("label",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(async_owner if transport == "async" else owner),
        },
    )
    schema = _schema(
        Criteria,
        scalar_models.NullableScalarSpecimen,
        transport=transport,
        fields=("label",),
        targets=(target,),
    )
    leaf: JSONObject = {"lag_among": {"in_": ["1 00:00:00"]}}
    where: JSONObject = {"bad": "abc", "or_": [leaf]} if logical else {"bad": "abc", **leaf}
    payload = _post(schema, where, transport=transport, selection="label")
    assert payload == {"data": {"rows": [{"label": "of-child"}]}}, payload
    assert events == ["clean", *(["clean"] if logical else []), "hook"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_supplied_empty_resolved_flat_leaf_keeps_ordinary_owner_acquisition(
    transport: str,
) -> None:
    models.Branch.objects.create(name="empty")
    calls: list[str] = []

    class Criteria(FilterSet):
        code = CharFilter(field_name="shelves__code")

        class Meta:
            model = models.Branch
            fields = []

    def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        return rows.exclude(topic="hidden")

    async def async_owner(
        cls: type[object],
        rows: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        return owner(cls, rows, info)

    target = make_django_type(
        "OrdinaryEmptyFlatOwner",
        models.Shelf,
        ("code",),
        node=False,
        namespace_extra={
            "get_queryset": classmethod(async_owner if transport == "async" else owner),
        },
    )
    schema = _schema(Criteria, models.Branch, transport=transport, targets=(target,))
    payload = _post(schema, {"code": ""}, transport=transport)
    assert payload == {"data": {"rows": [{"name": "empty"}]}}, payload
    assert calls == ["default"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "scenario",
    [
        "key-null",
        "key-membership",
        "exclude",
        "logical",
    ],
)
def test_async_resolved_relation_leaf_awaits_its_actual_terminal_owner(scenario: str) -> None:
    models.Genre.objects.create(name="empty")
    calls: list[str] = []

    class Child(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    class Criteria(FilterSet):
        visible_books = RelatedFilter(Child, field_name="books")
        without_title = CharFilter(field_name="books__title", exclude=True)

        class Meta:
            model = models.Genre
            fields = {"books": ["exact", "isnull"]}

    async def owner(cls: type[object], rows: QuerySet[Model], info: object) -> QuerySet[Model]:
        del cls, info
        calls.append(rows.db)
        return rows.exclude(circulation_status="repair")

    target = make_django_type(
        "ResolvedRelatedTerminalOwner",
        models.Book,
        ("title",),
        node=False,
        namespace_extra={"get_queryset": classmethod(owner)},
    )
    schema = _schema(Criteria, models.Genre, transport="async", targets=(target,))
    scenarios: dict[str, JSONObject] = {
        "key-null": {"books": {"is_null": True}},
        "key-membership": {"books": {"exact": [0]}},
        "exclude": {"without_title": "x"},
        "logical": {"not_": {"books": {"is_null": False}}},
    }
    payload = _post(schema, scenarios[scenario], transport="async")
    assert payload == {
        "data": {"rows": [] if scenario == "key-membership" else [{"name": "empty"}]},
    }, payload
    assert calls == ["default"]


def _alias_hook(hide: Mapping[str, object], *, awaited: bool = False) -> object:
    """A ``get_queryset`` hiding the rows ``hide`` matches from every viewer but staff."""

    def visible(queryset: QuerySet[Model], info: object) -> QuerySet[Model]:
        user = read_attr(read_attr(read_attr(info, "context"), "request"), "user", None)
        return queryset if read_attr(user, "is_staff", None) is True else queryset.exclude(**hide)

    def get_queryset(
        cls: type[object],
        queryset: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        del cls
        return visible(queryset, info)

    async def aget_queryset(
        cls: type[object],
        queryset: QuerySet[Model],
        info: object,
    ) -> QuerySet[Model]:
        del cls
        return visible(queryset, info)

    return classmethod(aget_queryset if awaited else get_queryset)


def _alias_targets(*, awaited_shelf: bool = False) -> tuple["type[DjangoType]", ...]:
    """Types hiding a secret shelf, a restricted branch, a book in repair and a hidden genre."""
    return tuple(
        make_django_type(
            name,
            model,
            (column,),
            node=False,
            meta_extra={"primary": True},
            namespace_extra={
                "get_queryset": _alias_hook(hide, awaited=awaited_shelf and model is models.Shelf),
            },
        )
        for name, model, column, hide in (
            (
                "AliasShelfTarget",
                models.Shelf,
                "code",
                {"topic": "secret"},
            ),
            (
                "AliasBranchTarget",
                models.Branch,
                "name",
                {"city": "restricted"},
            ),
            (
                "AliasBookTarget",
                models.Book,
                "title",
                {"circulation_status": "repair"},
            ),
            (
                "AliasGenreTarget",
                models.Genre,
                "name",
                {"name": "hidden"},
            ),
        )
    )


def _alias_world() -> dict[str, int]:
    """Shelves ``A-1`` (open), ``B-2`` (secret, tier 3), ``C-3`` (restricted branch) and a book on each.

    ``bk3`` is in repair; ``bk1`` is in the open genre, ``bk2`` in the hidden one, ``bk3`` in
    both. Each book's ``subtitle`` names a shelf topic: ``bk1`` and ``bk2`` their own shelf's.
    ``A-1`` and ``B-2`` each hold a circulation desk, a model no type here exposes, and one
    patron borrows each book (``loan-bk1``, ...).
    """
    open_branch = models.Branch.objects.create(name="b-open", city="x")
    restricted = models.Branch.objects.create(name="b-restr", city="restricted")
    shelves = {
        code: models.Shelf.objects.create(branch=branch, code=code, topic=topic, tier=tier)
        for code, branch, topic, tier in (
            (
                "A-1",
                open_branch,
                "open",
                1,
            ),
            (
                "B-2",
                open_branch,
                "secret",
                3,
            ),
            (
                "C-3",
                restricted,
                "open",
                2,
            ),
        )
    }
    for code in ("A-1", "B-2"):
        models.CirculationDesk.objects.create(
            name=f"desk-{code}",
            branch=open_branch,
            shelf=shelves[code],
        )
    open_genre = models.Genre.objects.create(name="open")
    hidden_genre = models.Genre.objects.create(name="hidden")
    books = {
        title: models.Book.objects.create(
            shelf=shelves[code],
            title=title,
            subtitle=subtitle,
            circulation_status=status,
        )
        for title, code, subtitle, status in (
            (
                "bk1",
                "A-1",
                "open",
                "available",
            ),
            (
                "bk2",
                "B-2",
                "secret",
                "available",
            ),
            (
                "bk3",
                "C-3",
                "x",
                "repair",
            ),
        )
    }
    patron = models.Patron.objects.create(name="reader")
    for title in ("bk1", "bk2", "bk3"):
        models.Loan.objects.create(book=books[title], patron=patron, note=f"loan-{title}")
    books["bk1"].genres.set([open_genre])
    books["bk2"].genres.set([hidden_genre])
    books["bk3"].genres.set([open_genre, hidden_genre])
    return {
        **{code: saved_pk(shelf) for code, shelf in shelves.items()},
        **{title: saved_pk(book) for title, book in books.items()},
    }


class _OverridingAliasKey(ListFilter):
    """A list filter overriding ``filter``, so a to-many key runs it as declared."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return super().filter(qs, value)


class _JoinedAliasKey(ListFilter):
    """A list filter overriding ``filter`` to keep the rows its path joins, whatever its value."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        del value
        return qs.filter(**{f"{self.field_name}__isnull": False}).distinct()


def _aliased(
    **relations: django_models.FilteredRelation,
) -> Callable[[QuerySet[Model]], QuerySet[Model]]:
    """Return a queryset hook adding a copy of each of ``relations`` as an alias, in order.

    Django's ``Query.add_filtered_relation`` rewrites the instance it is handed, so each
    queryset gets its own.
    """

    def alias(rows: QuerySet[Model]) -> QuerySet[Model]:
        return rows.alias(
            **{name: copy.deepcopy(relation) for name, relation in relations.items()},
        )

    return alias


def _shelf_reading(
    condition: django_models.Q,
    **annotations: django_models.Expression | django_models.F | django_models.Subquery,
) -> Callable[[QuerySet[Model]], QuerySet[Model]]:
    """Return a hook annotating ``annotations``, then aliasing ``vshelf`` under ``condition``.

    A ``vs0`` alias of the shelf is added first, so an annotation may read it.
    """

    def alias(rows: QuerySet[Model]) -> QuerySet[Model]:
        return (
            rows.alias(vs0=django_models.FilteredRelation("shelf"))
            .annotate(**copy.deepcopy(annotations))
            .alias(vshelf=django_models.FilteredRelation("shelf", condition=condition))
        )

    return alias


def _book_branch_reading_its_shelf(rows: QuerySet[Model]) -> QuerySet[Model]:
    """Alias each book's shelf's branch under a condition reading its shelf's topic."""
    return rows.annotate(want=django_models.F("shelf__topic")).alias(
        vb=django_models.FilteredRelation(
            "shelf__branch",
            condition=~django_models.Q(shelf__branch__city=django_models.F("want")),
        ),
    )


def _loan_branch_reading_its_shelf(rows: QuerySet[Model]) -> QuerySet[Model]:
    """Alias each loan's book's shelf's branch under a condition reading the shelf's topic."""
    return rows.annotate(want=django_models.F("book__shelf__topic")).alias(
        vb=django_models.FilteredRelation(
            "book__shelf__branch",
            condition=~django_models.Q(book__shelf__branch__city=django_models.F("want")),
        ),
    )


def _first_genre() -> django_models.Subquery:
    return django_models.Subquery(
        models.Genre.objects.filter(books=django_models.OuterRef("pk"))
        .order_by("name")
        .values("name")[:1],
    )


def _shelf(condition: django_models.Q | None = None) -> django_models.FilteredRelation:
    if condition is None:
        return django_models.FilteredRelation("shelf")
    return django_models.FilteredRelation("shelf", condition=condition)


_TIER_TWO = django_models.Q(shelf__tier__gte=2)
_OWN_TOPIC = django_models.Q(shelf__topic=django_models.F("subtitle"))


class _InRows(NamedTuple):
    """An ``in`` value naming world rows by label, read as their keys."""

    labels: tuple[str, ...]


class _AliasCase(NamedTuple):
    """A leaf over an alias, its JSON value, and the rows each viewer reads."""

    model: type[Model]
    alias: Callable[[QuerySet[Model]], QuerySet[Model]]
    leaf: Callable[[], Filter]
    value: object
    anonymous: list[str]
    staff: list[str]


_ALIAS_CASES: dict[str, _AliasCase] = {
    "forward-column": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf()),
        partial(CharFilter, field_name="vshelf__code"),
        "B-2",
        [],
        ["bk2"],
    ),
    "forward-key": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf()),
        partial(ListFilter, field_name="vshelf", lookup_expr="in"),
        _InRows(("B-2",)),
        [],
        ["bk2"],
    ),
    "reverse-column": _AliasCase(
        models.Shelf,
        _aliased(vbooks=django_models.FilteredRelation("books")),
        partial(CharFilter, field_name="vbooks__title"),
        "bk3",
        [],
        ["C-3"],
    ),
    "reverse-key": _AliasCase(
        models.Shelf,
        _aliased(vbooks=django_models.FilteredRelation("books")),
        partial(ListFilter, field_name="vbooks", lookup_expr="in"),
        _InRows(("bk3",)),
        [],
        ["C-3"],
    ),
    "many-to-many-column": _AliasCase(
        models.Book,
        _aliased(vgenres=django_models.FilteredRelation("genres")),
        partial(CharFilter, field_name="vgenres__name"),
        "hidden",
        [],
        ["bk2", "bk3"],
    ),
    "past-the-alias": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf()),
        partial(CharFilter, field_name="vshelf__branch__name"),
        "b-restr",
        [],
        ["bk3"],
    ),
    "alias-of-two-relations": _AliasCase(
        models.Book,
        _aliased(vbranch=django_models.FilteredRelation("shelf__branch")),
        partial(CharFilter, field_name="vbranch__name"),
        "b-open",
        ["bk1"],
        ["bk1", "bk2"],
    ),
    "alias-into-a-model-no-type-exposes": _AliasCase(
        models.Book,
        _aliased(vdesk=django_models.FilteredRelation("shelf__circulation_desk")),
        partial(CharFilter, field_name="vdesk__name"),
        "desk-B-2",
        [],
        ["bk2"],
    ),
    "alias-over-an-alias": _AliasCase(
        models.Book,
        _aliased(
            vshelf=_shelf(_TIER_TWO),
            vbranch=django_models.FilteredRelation("vshelf__branch"),
        ),
        partial(CharFilter, field_name="vbranch__name"),
        "b-open",
        [],
        ["bk2"],
    ),
    "condition-reading-the-row": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf(_OWN_TOPIC)),
        partial(CharFilter, field_name="vshelf__code"),
        "B-2",
        [],
        ["bk2"],
    ),
    "condition-reading-a-value-annotation": _AliasCase(
        models.Book,
        _shelf_reading(
            django_models.Q(shelf__code=django_models.F("want")),
            want=django_models.Value("B-2"),
        ),
        partial(CharFilter, field_name="vshelf__code"),
        "B-2",
        [],
        ["bk2"],
    ),
    "condition-reading-a-joined-annotation": _AliasCase(
        models.Book,
        _shelf_reading(
            django_models.Q(shelf__code=django_models.F("want")),
            want=django_models.F("shelf__code"),
        ),
        partial(CharFilter, field_name="vshelf__code"),
        "B-2",
        [],
        ["bk2"],
    ),
    "condition-reading-a-to-many-annotation": _AliasCase(
        models.Book,
        _shelf_reading(
            ~django_models.Q(shelf__topic=django_models.F("want")),
            want=django_models.F("genres__name"),
        ),
        partial(CharFilter, field_name="vshelf__code"),
        "B-2",
        [],
        ["bk2"],
    ),
    "condition-reading-a-subquery-annotation": _AliasCase(
        models.Book,
        _shelf_reading(
            ~django_models.Q(shelf__topic=django_models.F("want")),
            want=_first_genre(),
        ),
        partial(CharFilter, field_name="vshelf__code"),
        "B-2",
        [],
        ["bk2"],
    ),
    "condition-reading-an-annotation-over-another-alias": _AliasCase(
        models.Book,
        _shelf_reading(
            django_models.Q(shelf__code=django_models.F("want")),
            want=django_models.F("vs0__code"),
        ),
        partial(CharFilter, field_name="vshelf__code"),
        "B-2",
        [],
        ["bk2"],
    ),
    "forward-chain-reading-a-joined-annotation": _AliasCase(
        models.Book,
        _book_branch_reading_its_shelf,
        partial(CharFilter, field_name="vb__name"),
        "b-open",
        ["bk1"],
        ["bk1", "bk2"],
    ),
    "two-step-forward-chain-reading-a-joined-annotation": _AliasCase(
        models.Loan,
        _loan_branch_reading_its_shelf,
        partial(CharFilter, field_name="vb__name"),
        "b-open",
        ["loan-bk1"],
        ["loan-bk1", "loan-bk2"],
    ),
    "null-alias": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf(_OWN_TOPIC)),
        partial(BooleanFilter, field_name="vshelf", lookup_expr="isnull"),
        value=True,
        anonymous=["bk2"],
        staff=[],
    ),
    "non-null-alias": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf(_OWN_TOPIC)),
        partial(BooleanFilter, field_name="vshelf", lookup_expr="isnull"),
        value=False,
        anonymous=["bk1"],
        staff=["bk1", "bk2"],
    ),
    "excluded-column": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf()),
        partial(CharFilter, field_name="vshelf__code", exclude=True),
        "B-2",
        ["bk1", "bk2", "bk3"],
        ["bk1", "bk3"],
    ),
    "excluded-key": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf()),
        partial(ListFilter, field_name="vshelf", lookup_expr="in", exclude=True),
        _InRows(("B-2",)),
        ["bk1", "bk2", "bk3"],
        ["bk1", "bk3"],
    ),
    "excluded-key-past-a-condition": _AliasCase(
        models.Book,
        _aliased(vshelf=_shelf(_TIER_TWO)),
        partial(ListFilter, field_name="vshelf", lookup_expr="in", exclude=True),
        _InRows(("B-2",)),
        ["bk2", "bk3"],
        ["bk3"],
    ),
    "overriding-to-many-key": _AliasCase(
        models.Shelf,
        _aliased(vbooks=django_models.FilteredRelation("books")),
        partial(_OverridingAliasKey, field_name="vbooks", lookup_expr="in"),
        _InRows(("bk3",)),
        [],
        ["C-3"],
    ),
    "overriding-to-many-key-past-a-condition": _AliasCase(
        models.Shelf,
        _aliased(
            vbooks=django_models.FilteredRelation(
                "books",
                condition=django_models.Q(books__title="bk1"),
            ),
        ),
        partial(_OverridingAliasKey, field_name="vbooks", lookup_expr="in"),
        _InRows(("bk2",)),
        [],
        [],
    ),
    "overriding-to-many-key-naming-no-row": _AliasCase(
        models.Shelf,
        _aliased(
            vbooks=django_models.FilteredRelation(
                "books",
                condition=django_models.Q(books__title="bk1"),
            ),
        ),
        partial(_OverridingAliasKey, field_name="vbooks", lookup_expr="in"),
        {"in_": [999999]},
        [],
        [],
    ),
    "overriding-to-many-key-reading-its-path": _AliasCase(
        models.Shelf,
        _aliased(
            vbooks=django_models.FilteredRelation(
                "books",
                condition=django_models.Q(books__title="bk1"),
            ),
        ),
        partial(_JoinedAliasKey, field_name="vbooks", lookup_expr="in"),
        {"in_": []},
        ["A-1"],
        ["A-1"],
    ),
    "overriding-to-many-key-reading-its-path-to-a-hidden-row": _AliasCase(
        models.Shelf,
        _aliased(
            vbooks=django_models.FilteredRelation(
                "books",
                condition=django_models.Q(books__title="bk3"),
            ),
        ),
        partial(_JoinedAliasKey, field_name="vbooks", lookup_expr="in"),
        {"in_": []},
        [],
        ["C-3"],
    ),
    "overriding-many-to-many-key-reading-its-path": _AliasCase(
        models.Genre,
        _aliased(
            vbooks=django_models.FilteredRelation(
                "books",
                condition=django_models.Q(books__title__in=["bk2", "bk3"]),
            ),
        ),
        partial(_JoinedAliasKey, field_name="vbooks", lookup_expr="in"),
        {"in_": []},
        ["hidden"],
        ["open", "hidden"],
    ),
}


def _alias_value(value: object, world: Mapping[str, int]) -> object:
    if isinstance(value, _InRows):
        return {"in_": [world[label] for label in value.labels]}
    return value


def _alias_set(case: _AliasCase, *, placed_by_set: bool) -> type[FilterSet]:
    """A set declaring ``case``'s leaf; with ``placed_by_set`` its ``filter_queryset`` adds the alias."""
    meta = type("Meta", (), {"model": case.model, "fields": []})
    namespace: dict[str, object] = {"leaf": case.leaf(), "Meta": meta}
    if placed_by_set:

        def filter_queryset(self: FilterSet, queryset: QuerySet[Model]) -> QuerySet[Model]:
            return FilterSet.filter_queryset(self, case.alias(queryset))

        namespace["filter_queryset"] = filter_queryset
    return type("AliasCriteria", (FilterSet,), namespace)


def _alias_client(transport: str, viewer: str) -> Client | AsyncClient:
    client = AsyncClient() if transport == "async" else Client()
    if viewer == "staff":
        client.force_login(User.objects.get(username="staff_1"))
    return client


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("placement", ["handed-queryset", "filter-queryset"])
@pytest.mark.parametrize("case", sorted(_ALIAS_CASES))
def test_a_flat_path_starting_at_a_filtered_relation_alias_reads_each_relations_visibility(
    case: str,
    placement: str,
    transport: str,
    viewer: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A leaf over a ``FilteredRelation`` alias answers as Django does over the rows each type shows.

    The alias walks as a hop over the relations it joins, forward, reverse, many-to-many, past
    the alias, over two relations and over another alias, its condition (an ``F()`` reading the
    book included) holding through Django's own join: the anonymous viewer never matches through
    a secret shelf, a restricted branch, a book in repair or a hidden genre, and reads an alias
    whose joined shelf is hidden as ``NULL``, while Django's ``INNER`` join of a non-null forward
    key drops a book whose shelf the condition leaves out under ``isNull`` and ``exclude`` alike.
    Staff read Django's literal rows. The alias is on the queryset handed to the set or added by
    the set's ``filter_queryset``, under ``apply_sync`` and ``apply_async``, in one statement.
    """
    create_users(1)
    selected = _ALIAS_CASES[case]
    world = _alias_world()
    columns: dict[type[Model], str] = {
        models.Book: "title",
        models.Shelf: "code",
        models.Loan: "note",
    }
    column = columns.get(selected.model, "name")
    schema = _schema(
        _alias_set(selected, placed_by_set=placement == "filter-queryset"),
        selected.model,
        transport=transport,
        fields=(column,),
        targets=_alias_targets(),
        annotated=selected.alias if placement == "handed-queryset" else None,
    )
    client = _alias_client(transport, viewer)
    recorded = record_compiled_sql("library_")
    payload = _post(
        schema,
        {"leaf": _alias_value(selected.value, world)},
        transport=transport,
        selection=column,
        client=client,
    )
    expected = selected.staff if viewer == "staff" else selected.anonymous
    assert payload == {"data": {"rows": [{column: row} for row in expected]}}, payload
    assert len(recorded) == 1, recorded


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("placement", ["handed-queryset", "filter-queryset"])
@pytest.mark.parametrize(
    ("case", "rows"),
    [("forward-column", []), ("alias-of-two-relations", ["bk1"])],
)
def test_an_alias_only_filter_queryset_adds_is_not_awaited_before_an_async_only_hook(
    case: str,
    rows: list[str],
    placement: str,
) -> None:
    """``apply_async`` awaits an async-only target hook for an alias on the queryset it is handed.

    The shelf hook is async-only, for the shelf the alias joins and for the shelf an alias of
    two relations passes through. An alias the set's ``filter_queryset`` adds exists only once
    the set filters, after every hook the handed queryset names was awaited, so the async-only
    shelf hook it reaches raises ``SyncMisuseError`` rather than reading the shelf unscoped.
    """
    create_users(1)
    selected = _ALIAS_CASES[case]
    _alias_world()
    schema = _schema(
        _alias_set(selected, placed_by_set=placement == "filter-queryset"),
        models.Book,
        transport="async",
        fields=("title",),
        targets=_alias_targets(awaited_shelf=True),
        annotated=selected.alias if placement == "handed-queryset" else None,
    )
    payload = _post(schema, {"leaf": selected.value}, transport="async", selection="title")
    if placement == "handed-queryset":
        assert payload == {"data": {"rows": [{"title": title} for title in rows]}}, payload
    else:
        _refused(
            payload,
            (
                "AliasShelfTarget.get_queryset returned a coroutine in a sync resolver context. "
                "A related filter reads its target type's get_queryset; await "
                "FilterSet.apply_async from an async resolver (a connection field does under "
                "await schema.execute() or the async view) instead, or redefine get_queryset "
                "as a sync method."
            ),
        )


@pytest.mark.django_db
@pytest.mark.parametrize("transport", ["sync", "async"])
def test_a_filtered_relation_alias_joining_no_relation_is_refused_when_a_leaf_walks_it(
    transport: str,
) -> None:
    """An alias whose ``relation_name`` names a column, which Django accepts, scopes no hop.

    A leaf starting at it is refused naming the alias and the path it joins, rather than
    compiled over rows no type was asked about.
    """
    create_users(1)
    _alias_world()
    selected = _AliasCase(
        models.Book,
        _aliased(vtitle=django_models.FilteredRelation("title")),
        partial(CharFilter, field_name="vtitle"),
        "bk1",
        [],
        [],
    )
    schema = _schema(
        _alias_set(selected, placed_by_set=False),
        models.Book,
        transport=transport,
        fields=("title",),
        targets=_alias_targets(),
        annotated=selected.alias,
    )
    _refused(
        _post(schema, {"leaf": "bk1"}, transport=transport, selection="title"),
        (
            "FilteredRelation alias 'vtitle' joins 'title', which is not a path of relations "
            "of Book a filter can scope."
        ),
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("placement", ["handed-queryset", "filter-queryset"])
def test_an_absent_alias_key_whose_filter_reads_its_path_answers_over_the_visible_rows(
    placement: str,
    transport: str,
    viewer: str,
) -> None:
    """A to-many alias key overriding ``filter`` acts though the request names no key.

    Its override keeps the shelves its path joins, whatever its value, so asked whether it
    constrains it does, over the set's own rows too (where an alias ``filter_queryset`` adds
    is not yet joined), and it answers over the alias's books its type lets the viewer see.
    """
    create_users(1)
    selected = _ALIAS_CASES["overriding-to-many-key-reading-its-path-to-a-hidden-row"]
    _alias_world()
    schema = _schema(
        _alias_set(selected, placed_by_set=placement == "filter-queryset"),
        models.Shelf,
        transport=transport,
        fields=("code",),
        targets=_alias_targets(),
        annotated=selected.alias if placement == "handed-queryset" else None,
    )
    payload = _post(
        schema,
        {},
        transport=transport,
        selection="code",
        client=_alias_client(transport, viewer),
    )
    expected = selected.staff if viewer == "staff" else selected.anonymous
    assert payload == {"data": {"rows": [{"code": row} for row in expected]}}, payload


def _genre_shelf_reading_its_book(rows: QuerySet[Model]) -> QuerySet[Model]:
    """Alias each genre's books' shelf under a condition reading a book column annotation."""
    return rows.annotate(want=django_models.F("books__title")).alias(
        vb=django_models.FilteredRelation(
            "books__shelf",
            condition=django_models.Q(books__shelf__code=django_models.F("want")),
        ),
    )


def _branch_books_reading_their_shelf(rows: QuerySet[Model]) -> QuerySet[Model]:
    """Alias each branch's shelves, then their books under a condition reading the shelf alias."""
    return (
        rows.alias(vs=django_models.FilteredRelation("shelves"))
        .annotate(want=django_models.F("vs__code"))
        .alias(
            vbk=django_models.FilteredRelation(
                "vs__books",
                condition=django_models.Q(vs__books__subtitle=django_models.F("want")),
            ),
        )
    )


def _book_genres_reading_a_numbered_join(rows: QuerySet[Model]) -> QuerySet[Model]:
    """Alias the genres of a book's shelf-mates under a condition reading a shelf-mate's title."""
    return rows.annotate(want=django_models.F("shelf__books__title")).alias(
        vg=django_models.FilteredRelation(
            "shelf__books__genres",
            condition=django_models.Q(shelf__books__genres__name=django_models.F("want")),
        ),
    )


class _ReboundCase(NamedTuple):
    """An alias whose condition reads an annotation the filter's own joins would rebind."""

    model: type[Model]
    alias: Callable[[QuerySet[Model]], QuerySet[Model]]
    leaf: str
    column: str
    message: str


_REBOUND_CASES: dict[str, _ReboundCase] = {
    "a-table-the-relations-cross": _ReboundCase(
        models.Genre,
        _genre_shelf_reading_its_book,
        "vb__code",
        "name",
        (
            "FilteredRelation alias 'vb' reads annotation 'want', which reads 'library_book'; a "
            "filter over the alias joins 'library_book' again to reach 'books__shelf', which "
            "would rebind the annotation to that join, so no filter can scope the alias."
        ),
    ),
    "the-alias-it-starts-at": _ReboundCase(
        models.Branch,
        _branch_books_reading_their_shelf,
        "vbk__title",
        "name",
        (
            "FilteredRelation alias 'vbk' reads annotation 'want', which reads 'vs'; a filter "
            "over the alias joins 'vs' again to reach 'vs__books', which would rebind the "
            "annotation to that join, so no filter can scope the alias."
        ),
    ),
    "a-numbered-join": _ReboundCase(
        models.Book,
        _book_genres_reading_a_numbered_join,
        "vg__name",
        "title",
        (
            "FilteredRelation alias 'vg' reads annotation 'want', which reads 'T3'; a filter "
            "over the alias joins 'T3' again to reach 'shelf__books__genres', which would "
            "rebind the annotation to that join, so no filter can scope the alias."
        ),
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("transport", ["sync", "async"])
@pytest.mark.parametrize("case", sorted(_REBOUND_CASES))
def test_an_alias_condition_reading_an_annotation_its_joins_would_rebind_is_refused(
    case: str,
    transport: str,
) -> None:
    """An alias whose condition reads an annotation over a table alias its filter joins again.

    Django renames the filter's own joins when it nests them, the annotation's included, so
    the annotation would read the filter's row of that table: the leaf is refused naming the
    alias, the annotation and the table alias, never answered over another row's value.
    """
    create_users(1)
    _alias_world()
    selected = _REBOUND_CASES[case]
    schema = _schema(
        _alias_set(
            _AliasCase(
                selected.model,
                selected.alias,
                partial(CharFilter, field_name=selected.leaf),
                "bk2",
                [],
                [],
            ),
            placed_by_set=False,
        ),
        selected.model,
        transport=transport,
        fields=(selected.column,),
        targets=_alias_targets(),
        annotated=selected.alias,
    )
    _refused(
        _post(schema, {"leaf": "bk2"}, transport=transport, selection=selected.column),
        selected.message,
    )
