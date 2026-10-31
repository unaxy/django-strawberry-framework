"""Consumer JSON arguments preserve filtering, inactive logic and malformed-value refusals.

These consumers deliberately accept ordinary JSON instead of generated FilterInput types.
Their resolvers pass request values to public FilterSet apply methods or construction/.qs. Invalid
shapes therefore reach the same supported apply seam as a consumer's assembled criteria;
they are not private-validator wrappers. Native Meta output types remain unbound to the
sets. Explicit pass-through policy lets refusal rows read the production diagnostics.
"""

import asyncio
import datetime
from collections.abc import Awaitable, Mapping
from functools import wraps
from typing import TYPE_CHECKING, Annotated, NoReturn

import pytest
import strawberry
from apps.library import models
from apps.library.filters import _validate_email_must_have_at_sign
from apps.products.services import create_users
from apps.scalars import models as scalar_models
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db import models as django_models
from django.db.models import Lookup, Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import AsyncClient, Client, override_settings
from django.test.utils import register_lookup
from django.urls import path
from django_filters import CharFilter, DateTimeFilter, MultipleChoiceFilter
from django_filters import RangeFilter as UpstreamRangeFilter
from graphql import GraphQLError
from graphql_client import JSONObject, graphql_payload, json_object, response_json
from strategy_schemas import make_django_type
from typing_extensions import override

from django_strawberry_framework import DjangoSchema, finalize_django_types, strawberry_config
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter, RelatedFilter
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

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
) -> DjangoSchema:
    output = make_django_type("RawCriteriaOutput", model, fields, node=False)

    def resolve_rows(
        info: strawberry.Info[object, object],
        where: strawberry.scalars.JSON,
    ) -> QuerySet[Model]:
        queryset = model._default_manager.order_by("pk")
        if direct:
            return filterset(data=json_object(where), queryset=queryset).qs
        return filterset.apply_sync(where, queryset, info)

    async def resolve_async_rows(
        info: strawberry.Info[object, object],
        where: strawberry.scalars.JSON,
    ) -> list[Model]:
        queryset = await filterset.apply_async(where, model._default_manager.order_by("pk"), info)
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
        error_policy={"enabled": False},
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
        emails = ListFilter(field_name="email")
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
