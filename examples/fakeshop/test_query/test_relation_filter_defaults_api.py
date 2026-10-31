"""Consumer relation forms apply defaults, await scoped methods and refuse unresolved active hops.

Ordinary JSON arguments reach unbound FilterSet apply methods or a consumer's direct
queryset property. Native output types preserve the whole root universe independently
of relation visibility. Explicit pass-through error policy exposes configuration refusals.
"""

import asyncio
from collections.abc import Awaitable, Mapping, Sequence
from functools import wraps
from typing import TypeVar

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django import forms
from django.db.models import F, Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter
from django_filters.filterset import BaseFilterSet
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    response_json,
)
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
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import read_attr, require_instance
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

_M = TypeVar("_M", bound=Model)
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
    path("graphql-relation-defaults/", _graphql_view),
    path("graphql-relation-defaults-async/", _async_view),
]


async def _async_post(document: str, variables: JSONObject) -> JSONObject:
    response = await AsyncTestClient().query(
        document,
        variables,
        url="/graphql-relation-defaults-async/",
        assert_no_errors=False,
    )
    assert response.response.status_code == 200
    return response_json(response.response)


def _post(
    schema: DjangoSchema,
    where: JSONObject,
    *,
    label: str = "name",
    transport: str = "sync",
) -> JSONObject:
    document = (
        f"query($where: JSON!) {{ rows(where: $where) {{ name: {label} }} "
        f"allRows {{ name: {label} }} }}"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if transport == "async":
                return asyncio.run(_async_post(document, {"where": where}))
            return graphql_payload(
                document,
                variables={"where": where},
                url="/graphql-relation-defaults/",
            )
    finally:
        _CURRENT["schema"] = None


def _holder(
    filterset: type[FilterSet],
    *,
    model: type[Model] = models.Branch,
    label: str = "name",
    targets: Sequence[type[DjangoType]] = (),
    direct: bool = False,
    prefix: str | None = None,
    transport: str = "sync",
) -> DjangoSchema:
    filterset.get_filters()
    output = type(
        "ConsumerRoot",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": (label,)})},
    )

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[Model]:
        del root
        queryset = model._default_manager.order_by(label)
        if direct:
            request = require_instance(read_attr(info.context, "request"), HttpRequest)
            return filterset(
                data=json_object(where),
                queryset=queryset,
                request=request,
                prefix=prefix,
            ).qs
        return filterset.apply_sync(where, queryset, info)

    async def resolve_async_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> list[Model]:
        del root
        queryset = await filterset.apply_async(where, model._default_manager.order_by(label), info)
        return await sync_to_async(list)(queryset)

    def resolve_all_rows(root: object) -> QuerySet[Model]:
        del root
        return model._default_manager.order_by(label)

    async def all_async_rows(root: object) -> list[Model]:
        del root
        return await sync_to_async(list)(model._default_manager.order_by(label))

    @strawberry.type
    class Query:
        rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=resolve_async_rows if transport == "async" else resolve_rows,
            graphql_type=list[output],
        )
        all_rows: QuerySet[Model] | Awaitable[list[Model]] = strawberry.field(
            resolver=all_async_rows if transport == "async" else resolve_all_rows,
            graphql_type=list[output],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=targets,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
        error_policy={"enabled": False},
    )


def _world() -> None:
    alpha = models.Branch.objects.create(name="alpha")
    alpha_shelf = models.Shelf.objects.create(branch=alpha, code="match", topic="open")
    beta = models.Branch.objects.create(name="beta")
    beta_shelf = models.Shelf.objects.create(branch=beta, code="match", topic="secret")
    models.Branch.objects.create(name="gamma")
    models.Book.objects.create(title="alpha", shelf=alpha_shelf)
    models.Book.objects.create(title="beta", shelf=beta_shelf)


def _expected(
    names: Sequence[str],
    *,
    universe: Sequence[str] = ("alpha", "beta", "gamma"),
) -> JSONObject:
    return {
        "data": {
            "rows": [{"name": name} for name in names],
            "allRows": [{"name": name} for name in universe],
        },
    }


def _target(*, annotated: bool = False, asynchronous: bool = False) -> type[DjangoType]:
    def scope(
        _cls: type[DjangoType],
        queryset: QuerySet[models.Shelf],
        _info: object,
    ) -> QuerySet[models.Shelf]:
        visible = queryset.exclude(topic="secret")
        return visible.annotate(label=F("code")) if annotated else visible

    async def async_scope(
        _cls: type[DjangoType],
        queryset: QuerySet[models.Shelf],
        _info: object,
    ) -> QuerySet[models.Shelf]:
        return await sync_to_async(lambda: queryset.exclude(topic="secret"))()

    return type(
        "ShelfScope",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": models.Shelf, "fields": ("code", "topic")}),
            "get_queryset": classmethod(async_scope if asynchronous else scope),
        },
    )


class _DefaultCode(CharFilter):
    """A consumer filter reading the form's empty value as the code ``match``."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return super().filter(qs, value or "match")


def _branch_filter(
    *,
    default: bool = False,
    customized: bool = False,
    reader: bool = False,
) -> type[FilterSet]:
    class ShelfChild(FilterSet):
        code_is = CharFilter(field_name="code", method="filter_code_is")
        if default:
            code_default = _DefaultCode(field_name="code")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"], "topic": ["exact"]}

        def filter_code_is(
            self,
            queryset: QuerySet[models.Shelf],
            _name: str,
            value: object,
        ) -> QuerySet[models.Shelf]:
            if reader:
                known = [shelf.code for shelf in models.Shelf.objects.filter(code=value)]
                return queryset.filter(code__in=known)
            return queryset.filter(code=value)

    child: type[FilterSet] = ShelfChild
    if customized:

        class OwnedShelf(ShelfChild):
            @override
            def __init__(
                self,
                data: Mapping[str, object] | None = None,
                queryset: QuerySet[Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        child = OwnedShelf

    class BranchParent(FilterSet):
        shelves = RelatedFilter(child, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    return BranchParent


def _placeholder(
    *,
    projected: bool = False,
    default: bool = False,
) -> tuple[type[FilterSet], type[FilterSet]]:
    class ShelfChild(FilterSet):
        branch = RelatedFilter(None, field_name="branch", queryset=models.Branch.objects.all())
        if default:
            branch_default = _DefaultCode(field_name="branch__name")

        class Meta:
            model = models.Shelf
            fields = {"branch__name": ["exact"]}

    child: type[FilterSet] = ShelfChild
    if projected:

        class OwnedShelf(ShelfChild):
            @override
            def __init__(
                self,
                data: Mapping[str, object] | None = None,
                queryset: QuerySet[Model] | None = None,
                *,
                request: HttpRequest | None = None,
                prefix: str | None = None,
            ) -> None:
                super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        child = OwnedShelf

    class BranchParent(FilterSet):
        shelves = RelatedFilter(child, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    return BranchParent, child


def _forward_placeholder() -> type[FilterSet]:
    class BookParent(FilterSet):
        shelf = RelatedFilter(None, field_name="shelf", queryset=models.Shelf.objects.all())

        class Meta:
            model = models.Book
            fields = {"title": ["exact"], "shelf__code": ["exact"]}

    return BookParent


def _message(owner: type[FilterSet], branch: str, *, missing_type: bool = False) -> str:
    reason = (
        "no DjangoType is registered for its target model Shelf"
        if missing_type
        else "its target FilterSet could not be resolved"
    )
    return (
        f"FilterSet {owner.__qualname__}: related filter branch {branch!r} is active in the "
        f"filter input (nested, or walked by a flat leaf) but {reason}. "
        "The branch's visibility scoping runs the target type's get_queryset "
        "(spec-027 Decision 8 step 3); skipping it would silently return unfiltered rows. "
        "Register a DjangoType for the target model or remove the RelatedFilter."
    )


def _refused(payload: JSONObject, message: str) -> None:
    assert json_at(payload, "data") is None, payload
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    assert json_at(errors[0], "message") == message, payload
    assert json_at(errors[0], "path") == ["rows"], payload


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["flat", "nested"])
def test_active_branch_requires_a_registered_target_type_over_http(spelling: str) -> None:
    """An unbound public consumer cannot silently skip the missing target scope in either spelling."""
    _world()
    filterset = _branch_filter()
    where: JSONObject = (
        {"shelves__code": "match"} if spelling == "flat" else {"shelves": {"code": "match"}}
    )
    _refused(_post(_holder(filterset), where), _message(filterset, "shelves", missing_type=True))


@pytest.mark.django_db
def test_forward_placeholder_refuses_its_supplied_raw_form_leaf_over_http() -> None:
    """A direct consumer form cannot filter through its unresolved forward branch."""
    _world()
    filterset = _forward_placeholder()
    schema = _holder(filterset, model=models.Book, label="title", direct=True)
    _refused(_post(schema, {"shelf__code": "match"}, label="title"), _message(filterset, "shelf"))


@pytest.mark.django_db
@pytest.mark.parametrize("projected", [False, True], ids=["plain-copy", "projected"])
def test_nested_placeholder_refuses_a_supplied_child_leaf_over_http(*, projected: bool) -> None:
    """Both expansion classes must refuse the same unresolved child branch."""
    _world()
    filterset, child = _placeholder(projected=projected)
    schema = _holder(filterset, targets=(_target(),))
    _refused(_post(schema, {"shelves__branch__name": "B"}), _message(child, "branch"))


@pytest.mark.django_db
@pytest.mark.parametrize("projected", [False, True], ids=["plain-copy", "projected"])
def test_raw_form_default_cannot_make_an_unresolved_child_branch_disappear(
    *,
    projected: bool,
) -> None:
    """An absent but constraining default derives the unresolved hop and refuses instead of recursing."""
    _world()
    filterset, child = _placeholder(projected=projected, default=True)
    schema = _holder(filterset, targets=(_target(),), direct=True)
    _refused(_post(schema, {}), _message(child, "branch"))


@pytest.mark.django_db
@pytest.mark.parametrize("projected", [False, True], ids=["plain-copy", "projected"])
def test_raw_form_inactive_copy_never_derives_its_unresolved_child_branch(
    *,
    projected: bool,
) -> None:
    """A direct form holds every copy but an empty no-op leaf still leaves all roots alone."""
    _world()
    filterset, _child = _placeholder(projected=projected)
    schema = _holder(filterset, targets=(_target(),), direct=True)
    payload = _post(schema, {})
    assert payload == _expected(["alpha", "beta", "gamma"]), payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    "shape",
    [
        "missing-type",
        "forward-placeholder",
        "plain-child",
        "projected-child",
    ],
)
def test_an_inactive_unresolved_relation_does_not_block_the_parents_own_leaf(shape: str) -> None:
    """A root's own scalar predicate stays usable without resolving an unrelated branch."""
    _world()
    if shape == "forward-placeholder":
        filterset = _forward_placeholder()
        schema = _holder(filterset, model=models.Book, label="title")
        payload = _post(schema, {"title": "alpha"}, label="title")
        assert payload == _expected(["alpha"], universe=["alpha", "beta"]), payload
    else:
        if shape == "missing-type":
            filterset = _branch_filter()
            targets: tuple[type[DjangoType], ...] = ()
        else:
            filterset, _child = _placeholder(projected=shape == "projected-child")
            targets = (_target(),)
        payload = _post(_holder(filterset, targets=targets), {"name": "alpha"})
        assert payload == _expected(["alpha"]), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "mode",
    [
        "walked-sync",
        "walked-async",
        "walked-direct",
        "projected-direct",
    ],
)
def test_a_consumer_class_default_constrains_the_form_that_actually_owns_it(mode: str) -> None:
    """An authored own default applies when omitted; a copied child default applies on its direct form."""
    _world()
    base = _branch_filter(default=True, customized=mode == "projected-direct")
    filterset = base
    if mode.startswith("walked-"):

        class WithOwnDefault(base):
            own = _DefaultCode(field_name="shelves__code")

        filterset = WithOwnDefault
    transport = "async" if mode == "walked-async" else "sync"
    schema = _holder(
        filterset,
        targets=(_target(),),
        direct=mode.endswith("direct"),
        transport=transport,
    )
    payload = _post(schema, {}, transport=transport)
    assert payload == _expected(["alpha"]), payload


@pytest.mark.django_db
def test_a_pipeline_request_does_not_run_an_unnamed_child_class_default() -> None:
    """The child's default cannot impose existence on a parent request that never names its copy."""
    _world()
    payload = _post(_holder(_branch_filter(default=True), targets=(_target(),)), {})
    assert payload == _expected(["alpha", "beta", "gamma"]), payload


@pytest.mark.django_db
def test_an_omitted_authored_default_reads_the_targets_runtime_annotation() -> None:
    """A column annotated only by the target hook constrains after that hook supplies it."""
    _world()
    base = _branch_filter()

    class AnnotatedDefault(base):
        own = _DefaultCode(field_name="shelves__label")

    payload = _post(_holder(AnnotatedDefault, targets=(_target(annotated=True),)), {})
    assert payload == _expected(["alpha"]), payload


@pytest.mark.django_db
def test_a_consumer_upstream_filter_loop_preserves_projected_target_visibility() -> None:
    """Calling django-filter's own loop still runs the projected child on its visible rows."""
    _world()
    base = _branch_filter()

    class UpstreamLoop(base):
        @override
        def filter_queryset(self, queryset: QuerySet[_M]) -> QuerySet[_M]:
            return BaseFilterSet.filter_queryset(self, queryset)

    payload = _post(
        _holder(UpstreamLoop, targets=(_target(),), direct=True),
        {"shelves__code_is": "match"},
    )
    assert payload == _expected(["alpha"]), payload


@pytest.mark.django_db
def test_a_consumer_form_prefix_reads_the_projected_leaf_under_its_prefixed_key(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The real prefixed form reads the key its method projection was given over JSON."""
    _world()
    schema = _holder(_branch_filter(reader=True), targets=(_target(),), direct=True, prefix="p")
    sql = record_compiled_sql()
    payload = _post(schema, {"p-shelves__code_is": "match"})
    assert payload == _expected(["alpha"]), payload
    assert len(_table_sql(sql, "library_shelf")) == 1, sql
    assert len(_table_sql(sql, "library_branch")) == 2, sql


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "case",
    [
        "flat",
        "flat-or",
        "method",
        "method-and-or",
    ],
)
def test_async_flat_scalar_and_projected_method_filters_await_their_target_hook(case: str) -> None:
    """An async-only target scope hides the otherwise matching second parent on each path."""
    _world()
    where: JSONObject
    if case == "flat":
        where = {"shelves__code": "match"}
    elif case == "flat-or":
        where = {"or_": [{"shelves__code": "match"}]}
    elif case == "method":
        where = {"shelves__code_is": "match"}
    else:
        where = {"and_": [{"or_": [{"shelves__code_is": "match"}]}]}
    schema = _holder(_branch_filter(), targets=(_target(asynchronous=True),), transport="async")
    payload = _post(schema, where, transport="async")
    assert payload == _expected(["alpha"]), payload


def _table_sql(statements: Sequence[str], table: str) -> list[str]:
    return [
        statement
        for statement in statements
        if statement.lstrip().startswith("SELECT ")
        and " FROM " in statement
        and statement.split(" FROM ", 1)[1].startswith(f'"{table}"')
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["flat", "nested"])
def test_a_projected_method_reading_the_database_costs_one_lookup_in_either_spelling(
    spelling: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The method's real Shelf lookup runs once, beside one filtered and one unfiltered root query."""
    _world()
    target = type(
        "PlainShelf",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": models.Shelf, "fields": ("code",)})},
    )
    schema = _holder(_branch_filter(reader=True), targets=(target,))
    where: JSONObject = (
        {"shelves__code_is": "match"} if spelling == "flat" else {"shelves": {"code_is": "match"}}
    )
    sql = record_compiled_sql()
    payload = _post(schema, where)
    assert payload == _expected(["alpha", "beta"]), payload
    assert len(_table_sql(sql, "library_shelf")) == 1, sql
    assert len(_table_sql(sql, "library_branch")) == 2, sql


@pytest.mark.django_db
@pytest.mark.parametrize("direct", [False, True], ids=["validated-apply", "consumer-qs"])
def test_a_full_consumer_form_keeps_its_required_copy_validation_contract(*, direct: bool) -> None:
    """Apply refuses the required unnamed field; a direct queryset preserves upstream invalid-form rows."""
    _world()

    class RequiredShelf(FilterSet):
        code_required = CharFilter(field_name="code", required=True)

        class Meta:
            model = models.Shelf
            fields = {"topic": ["exact"]}

    class FullConsumerForm(FilterSet):
        shelves = RelatedFilter(RequiredShelf, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

        @override
        def get_form_class(self) -> type[forms.Form]:
            return BaseFilterSet.get_form_class(self)

    payload = _post(_holder(FullConsumerForm, targets=(_target(),), direct=direct), {})
    if direct:
        assert payload == _expected(["alpha", "beta", "gamma"]), payload
    else:
        assert json_at(payload, "data") is None, payload
        errors = json_list(payload, "errors")
        assert len(errors) == 1, payload
        assert json_at(errors[0], "message") == "Invalid filter input", payload
        assert json_at(errors[0], "path") == ["rows"], payload
        assert json_at(errors[0], "extensions") == {
            "code": "FILTER_INVALID",
            "errors": {
                "shelves__code_required": [
                    {"message": "This field is required.", "code": "required"},
                ],
            },
        }, payload


@pytest.mark.django_db
def test_a_consumer_meta_form_reads_the_named_copy_without_binding_its_required_sibling() -> None:
    """A real form clean method consumes the named child value while the absent required copy stays absent."""
    _world()

    class ReadingForm(forms.Form):
        @override
        def clean(self) -> dict[str, object]:
            cleaned: dict[str, object] = self.cleaned_data
            if cleaned.get("shelves__code") != "MATCH" or "shelves__code_required" in cleaned:
                raise forms.ValidationError(
                    "The copied fields were not scoped to the supplied key.",
                )
            cleaned["shelves__code"] = "match"
            return cleaned

    class ShelfChild(FilterSet):
        code_required = CharFilter(field_name="code", required=True)

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class OwnForm(FilterSet):
        shelves = RelatedFilter(ShelfChild, field_name="shelves")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}
            form = ReadingForm

    payload = _post(_holder(OwnForm, targets=(_target(),)), {"shelves__code": "MATCH"})
    assert payload == _expected(["alpha"]), payload


def _desk_world() -> None:
    _world()
    for branch in models.Branch.objects.exclude(name="gamma"):
        models.CirculationDesk.objects.create(
            branch=branch,
            shelf=branch.shelves.get(),
            name=branch.name,
        )


@pytest.mark.django_db
@pytest.mark.parametrize("direct", [False, True], ids=["pipeline", "direct-form"])
@pytest.mark.parametrize("edit", [False, True], ids=["unchanged", "instance-edit"])
def test_a_consumer_constructor_edits_the_same_deferred_copy_the_request_runs(
    *,
    direct: bool,
    edit: bool,
) -> None:
    """An instance's iexact edit survives settlement; the unchanged sibling stays case sensitive."""
    _desk_world()

    class RingBranch(FilterSet):
        desks = RelatedFilter(lambda: RingDesk, field_name="circulation_desks")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    class RingDesk(FilterSet):
        shelf = RelatedFilter(lambda: RingShelf, field_name="shelf")

        class Meta:
            model = models.CirculationDesk
            fields = {"name": ["exact"]}

    class RingShelf(FilterSet):
        branch = RelatedFilter(RingBranch, field_name="branch")

        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class ConsumerConstructor(RingBranch):
        @override
        def __init__(
            self,
            data: Mapping[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)
            if edit:
                self.filters["desks__shelf__code"].lookup_expr = "iexact"

    desk = type(
        "PlainDesk",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": models.CirculationDesk, "fields": ("name",)})},
    )
    schema = _holder(ConsumerConstructor, targets=(_target(), desk), direct=direct)
    payload = _post(schema, {"desks__shelf__code": "MATCH"})
    assert payload == _expected(["alpha"] if edit else []), payload


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["field-empty-value", "checkbox-false"])
def test_an_omitted_parent_owned_walked_leaf_uses_its_actual_upstream_form_default(
    kind: str,
) -> None:
    """An own form default constrains visible shelves while the independent root field keeps all rows."""
    _world()
    base = _branch_filter()
    declaration = (
        CharFilter(field_name="shelves__code", empty_value="match")
        if kind == "field-empty-value"
        else BooleanFilter(
            field_name="shelves__topic",
            lookup_expr="isnull",
            widget=forms.CheckboxInput,
        )
    )
    parent = type("BranchOwnDefault", (base,), {"own": declaration})
    payload = _post(_holder(parent, targets=(_target(),)), {})
    assert payload == _expected(["alpha"]), payload
