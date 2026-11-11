"""Consumer JSON and raw arguments preserve filter forms, widget keys and public primitive calls.

These consumers deliberately keep a django-filter FilterSet as well as the package's set.
Ordinary arguments feed the original public data/queryset/.qs seam, without publishing an
input factory or assigning an owner. QueryDict is built by Django from a real query-string
argument, retaining repeated SelectMultiple keys that a generated filter input cannot spell.
A declared list or lone range bound over a relation itself cleans each raw element as the
target column the relation compares on (its ``to_field``, else the primary key), as
``<relation>__<that column>`` cleans it, and one whose ``lookup_expr`` crosses the relation
cleans each as the column the crossing reaches; a ``method=`` filter on a relation cleans
none.
A number past an integer column's range, which django-filter's ``NumberFilter`` caps only
from above (``-1e999999999999999999`` cleans to a decimal whose ``int()`` cannot finish),
answers from the end it lies past without converting it, on both parents and on every
generated and declared integer lookup; a fraction short of one past an end keeps the
truncated value's verdict.
Raw members and bounds over a duration or integer annotation of the queryset handed to the set
clean as that annotation's output field under both parents, a ``method=`` twin receiving them
as sent, and a set handed no queryset leaves the path to Django's ``FieldError``.
Under the package's set the same values over an annotation its own ``filter_queryset`` adds
before ``super()`` clean and are bind-asked over the queryset the override passes on:
``is_valid()`` and ``errors`` build ``qs`` to report a refusal (DRF's 400 body, the strict
``FilterView``'s empty answer), a bare ``.qs`` applies the leaves that cleaned (running the
override twice where ``is_valid()`` first runs it once), the bare
``form.is_valid()`` sees the refusal only once ``.qs`` ran, under ``is_valid()`` a model
field's own form error answers alone beside it, an override replacing a handed annotation is
cleaned as its replacement compares, a set overriding no ``filter_queryset`` builds no ``qs``
to validate, and a path the override does not add is Django's ``FieldError``.
Under the package's set the raw form runs the bind ask the typed input runs, as its own
errors: a year comparison past 9999, a duration past the backend's range on every lookup
and text the package refuses are refused with the typed input's messages, and the bare ``.qs``
applies the leaves that cleaned.
A set no type names (a plain subclass of ``BookFilter``, a set of the test's own) publishes
its filter table at its first construction, under a consumer's own call, DRF's
``DjangoFilterBackend`` and django-filter's ``FilterView`` alike: a walked key one or two hops
deep answers ``BookFilter``'s rows as each viewer sees them, and a declaration Django answers
no request for (a ``range`` over a relation, a GlobalID, model-choice, column-typed, choice or
null-test filter over a ``GenericForeignKey``, a model-choice filter with no queryset, declared
or selected by ``Meta.filter_overrides``) is refused at every construction, while a filter on
the content type key beside a ``GenericForeignKey`` or on the ``GenericRelation`` reversing it
answers its rows.
A raw key starting at a ``FilteredRelation`` alias the set's ``filter_queryset`` adds reads
the visibility of the shelf the alias joins and of the branch past it, under every driver.
A raw key past a self relation reads the parent type's annotation of its name while the set's
``filter_queryset`` annotates the same name on the rows it filters, under every driver.
"""

import contextlib
import datetime
from collections.abc import Callable, Generator, Iterable, Mapping
from decimal import Decimal
from functools import wraps
from typing import TYPE_CHECKING, ClassVar, NamedTuple

import django_filters
import pytest
import strawberry
from apps.library import models as library_models
from apps.library.filters import BookFilter, ReadingListEntryFilter, ReadingListFilter
from apps.products.services import create_users
from apps.scalars import models
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db import connection
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import (
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    Field,
    FilteredRelation,
    ForeignKey,
    IntegerField,
    Lookup,
    Model,
    QuerySet,
)
from django.db.models.functions import Upper
from django.db.models.sql.compiler import SQLCompiler
from django.forms.utils import ErrorDict
from django.http import HttpRequest, HttpResponseBase, JsonResponse, QueryDict
from django.test import Client, override_settings
from django.test.utils import register_lookup
from django.urls import path
from django_filters import CharFilter
from django_filters.filterset import BaseFilterSet
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterView
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    assert_database_answer,
    database_answer,
    graphql_payload,
    json_int,
    json_list,
    json_loads,
    json_object,
    read_attr,
)
from rest_framework import generics, serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.renderers import JSONRenderer
from strawberry.scalars import JSON
from strawberry.types import Info
from typing_extensions import override

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    ArrayFilter,
    FilterSet,
    GlobalIDFilter,
    ListFilter,
    RangeFilter,
    RelatedFilter,
)
from django_strawberry_framework.filters.base import _lookup_operand, _model_lookup_operand
from django_strawberry_framework.utils._narrowing import (
    is_list_or_tuple,
    is_queryset,
    require,
    require_instance,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._cleaned_filter_sets import (
    KEPT_EXTERNAL_ID,
    PackageCleanedScalarSet,
    PlainCleanedScalarSet,
    cleaned_specimen,
)
from tests._idioms import saved_pk

if TYPE_CHECKING:
    from django.db.models.sql.compiler import _AsSqlType

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


class _PlainBookFilter(BookFilter):
    """A plain subclass of the set ``BookType`` serves, which no type names."""


class _UnservedBranchSet(FilterSet):
    class Meta:
        model = library_models.Branch
        fields = {"name": ["exact"], "city": ["exact"]}


class _UnservedShelfSet(FilterSet):
    branch = RelatedFilter(_UnservedBranchSet, field_name="branch")

    class Meta:
        model = library_models.Shelf
        fields = {"topic": ["exact"]}


class _UnservedBookSet(FilterSet):
    """A set no type names, walking ``shelf`` and ``shelf__branch`` through its declarations."""

    shelf = RelatedFilter(_UnservedShelfSet, field_name="shelf")

    class Meta:
        model = library_models.Book
        fields = {"title": ["exact"]}


class _UnservedFlatOffBookSet(FilterSet):
    """A set no type names whose ``shelf`` is ``flat=False``, beside its own ``iexact`` topic key.

    The enabled twin (``_UnservedBookSet``) copies ``shelf__topic`` (``exact``) and
    ``shelf__branch__city``; this set copies neither, so its own ``shelf__topic`` holds
    the key and walks ``shelf`` as the request's actor sees it.
    """

    shelf = RelatedFilter(_UnservedShelfSet, field_name="shelf", flat=False)
    shelf__topic = CharFilter(field_name="shelf__topic", lookup_expr="iexact")

    class Meta:
        model = library_models.Book
        fields = {"title": ["exact"]}


class _RangeIssueChild(FilterSet):
    """An ``Issue`` set whose django-filter ``RangeWidget`` reads ``number_min`` / ``number_max``."""

    number = django_filters.RangeFilter(field_name="number")

    class Meta:
        model = library_models.Issue
        fields = {"title": ["exact"]}


def _range_own_parent(*, flat: bool) -> type[FilterSet]:
    """A ``Periodical`` set with its own ``issues__number`` range beside ``issues`` (``flat``)."""

    class RangeOwnPeriodicalSet(FilterSet):
        issues = RelatedFilter(_RangeIssueChild, field_name="issues", flat=flat)
        issues__number = django_filters.RangeFilter(field_name="issues__number")

        class Meta:
            model = library_models.Periodical
            fields = {"name": ["exact"]}

    return RangeOwnPeriodicalSet


class _RangeOverRelationSet(FilterSet):
    """A ``range`` over a relation: Django registers no ``range`` lookup on one."""

    branch_span = RangeFilter(field_name="branch", lookup_expr="range")

    class Meta:
        model = library_models.Shelf
        fields = ("code",)


class _GlobalIDOverGenericSet(FilterSet):
    """A GlobalID filter over a ``GenericForeignKey``, which compares no row identity."""

    content_object = GlobalIDFilter(field_name="content_object")

    class Meta:
        model = library_models.TaggedItem
        fields = ("tag",)


class _ModelChoiceOverGenericSet(FilterSet):
    """A model-choice filter over a ``GenericForeignKey``, which holds no chosen row."""

    content_object = django_filters.ModelChoiceFilter(
        field_name="content_object",
        queryset=library_models.Branch.objects.all(),
    )

    class Meta:
        model = library_models.TaggedItem
        fields = ("tag",)


class _ModelMultipleChoicePastKeySet(FilterSet):
    """A model-multiple-choice filter past a key onto the desk's ``GenericForeignKey``."""

    desk_object = django_filters.ModelMultipleChoiceFilter(
        field_name="desk__content_object",
        queryset=library_models.Branch.objects.all(),
    )

    class Meta:
        model = library_models.DeskShift
        fields = ("name",)


class _CharOverGenericSet(FilterSet):
    """A ``CharFilter`` over a ``GenericForeignKey``: no column holds a value it compares."""

    content_object = django_filters.CharFilter(field_name="content_object")

    class Meta:
        model = library_models.TaggedItem
        fields = ("tag",)


class _NullTestOverGenericSet(FilterSet):
    """An ``isnull`` test over a ``GenericForeignKey``, which Django filters no queryset through."""

    content_object = django_filters.BooleanFilter(
        field_name="content_object",
        lookup_expr="isnull",
    )

    class Meta:
        model = library_models.CirculationDesk
        fields = ("name",)


class _RangePastKeyOntoGenericSet(FilterSet):
    """A ``range`` past a key onto the desk's ``GenericForeignKey``."""

    desk_object = RangeFilter(field_name="desk__content_object")

    class Meta:
        model = library_models.DeskShift
        fields = ("name",)


class _ChoicePastKeyOntoGenericSet(FilterSet):
    """A ``ChoiceFilter`` past a key onto the desk's ``GenericForeignKey``."""

    desk_object = django_filters.ChoiceFilter(
        choices=[("a", "a")],
        field_name="desk__content_object",
    )

    class Meta:
        model = library_models.DeskShift
        fields = ("name",)


class _ContentTypeColumnSet(FilterSet):
    """A ``NumberFilter`` on the content type key a ``GenericForeignKey`` reads: a column."""

    kind = django_filters.NumberFilter(field_name="content_type")

    class Meta:
        model = library_models.TaggedItem
        fields = ("tag",)


class _GenericRelationSet(FilterSet):
    """A ``NumberFilter`` on the ``GenericRelation`` reversing a ``GenericForeignKey``."""

    tagged = django_filters.NumberFilter(field_name="tags")

    class Meta:
        model = library_models.Branch
        fields = ("name",)


class _QuerysetlessChoiceSet(FilterSet):
    """A ``ModelChoiceFilter`` with no ``queryset=``: its form field has no rows to look in."""

    branch_is = django_filters.ModelChoiceFilter(field_name="branch")

    class Meta:
        model = library_models.Shelf
        fields = ("code",)


class _QuerysetlessOverrideSet(FilterSet):
    """A ``Meta.filter_overrides`` entry selecting a ``ModelChoiceFilter`` with no ``extra``."""

    class Meta:
        model = library_models.Shelf
        fields = {"branch": ["exact"]}
        filter_overrides = {ForeignKey: {"filter_class": django_filters.ModelChoiceFilter}}


class _AliasedShelfBookSet(FilterSet):
    """Book filters over a ``FilteredRelation`` alias the set's own ``filter_queryset`` adds."""

    shelf_code = CharFilter(field_name="vshelf__code")
    shelf_branch = CharFilter(field_name="vshelf__branch__name")

    class Meta:
        model = library_models.Book
        fields = ("title",)

    @override
    def filter_queryset(self, queryset: QuerySet[Model]) -> QuerySet[Model]:
        return super().filter_queryset(queryset.alias(vshelf=FilteredRelation("shelf")))


def _kids_as_sent(
    _filterset: BaseFilterSet,
    queryset: QuerySet[Model],
    name: str,
    value: list[object],
) -> QuerySet[Model]:
    """A consumer method keeping ``parent`` only when every member arrives as the text sent."""
    del name
    return queryset.filter(label="parent" if all(isinstance(v, str) for v in value) else "child")


def _annotated_set(parent: str) -> type[BaseFilterSet]:
    """A set whose list and range filters name two annotations of the queryset it is handed."""
    base = {"package": FilterSet, "django-filter": django_filters.FilterSet}[parent]
    declared = type(
        "RawAnnotationSet",
        (base,),
        {
            "lag_among": ListFilter(field_name="lag", lookup_expr="in"),
            "lag_span": RangeFilter(field_name="lag", lookup_expr="range"),
            "kids_among": ListFilter(field_name="kids", lookup_expr="in"),
            "kids_span": RangeFilter(field_name="kids", lookup_expr="range"),
            "kids_pair": ListFilter(field_name="kids", lookup_expr="range"),
            "up_among": ListFilter(field_name="up", lookup_expr="in"),
            "kids_sent": ListFilter(field_name="kids", lookup_expr="in", method="kids_as_sent"),
            "par_span": RangeFilter(field_name="par", lookup_expr="signed_big__range"),
            "par_among": ListFilter(field_name="par", lookup_expr="signed_big__in"),
            "offspring_among": ListFilter(field_name="offspring", lookup_expr="in"),
            "offspring_array": ArrayFilter(field_name="offspring", lookup_expr="in"),
            "signed_among": ListFilter(field_name="signed_big", lookup_expr="in"),
            "kids_as_sent": _kids_as_sent,
            "Meta": type("Meta", (), {"model": models.ScalarSpecimen, "fields": ()}),
        },
    )
    assert issubclass(declared, BaseFilterSet)
    return declared


def _annotated_rows(rows: QuerySet[Model]) -> QuerySet[Model]:
    """``rows`` annotated with the ``lag``, ``kids`` and ``up`` outputs ``_annotated_set`` names."""
    return rows.annotate(
        lag=ExpressionWrapper(
            F("occurred_at") - F("parent__occurred_at"),
            output_field=DurationField(),
        ),
        kids=Count("children"),
        up=Upper("label"),
    )


class _HandedJsonSet(FilterSet):
    """A list over ``pj``, a ``JSONField`` annotation of the handed queryset; no ``filter_queryset``.

    The handed queryset resolves ``pj`` and its output gives the list no cleaner, so the value
    is applied as sent.
    """

    pj_among = ListFilter(field_name="pj", lookup_expr="in")

    class Meta:
        model = models.ScalarSpecimen
        fields = ()


class _ShadowedAnnotationSet(FilterSet):
    """A list over ``n``, handed as ``payload`` and replaced by a ``Count`` in ``filter_queryset``."""

    n_among = ListFilter(field_name="n", lookup_expr="in")

    class Meta:
        model = models.ScalarSpecimen
        fields = ()

    @override
    def filter_queryset(self, queryset: QuerySet[Model]) -> QuerySet[Model]:
        return super().filter_queryset(queryset.annotate(n=Count("children")))


def _shadowed_rows() -> QuerySet[Model]:
    """Every specimen with ``n`` a ``JSONField`` annotation, as handed to the shadowing set."""
    return models.ScalarSpecimen.objects.annotate(n=F("payload")).order_by("pk")


#: One entry per run of the late set's own ``filter_queryset`` (``_late_annotated_set``).
_LATE_FILTER_QUERYSET_RUNS: list[None] = []


def _late_annotated_set() -> type[FilterSet]:
    """``_annotated_set("package")`` whose own ``filter_queryset`` annotates before ``super()``.

    Handed unannotated rows, the set's form reads no field for ``lag`` or ``kids``: each such
    value is cleaned over the queryset the override passes on. Each run of the override is
    recorded in ``_LATE_FILTER_QUERYSET_RUNS``.
    """
    handed = _annotated_set("package")
    assert issubclass(handed, FilterSet)

    class LateAnnotationSet(handed):
        @override
        def filter_queryset(self, queryset: QuerySet[Model]) -> QuerySet[Model]:
            _LATE_FILTER_QUERYSET_RUNS.append(None)
            return super().filter_queryset(_annotated_rows(queryset))

    return LateAnnotationSet


class _LateParentTwiceSet(FilterSet):
    """Members and a bound over ``parent__twice``; its ``filter_queryset`` annotates ``twice``.

    The rows it filters name their own tripled ``signed_big`` ``twice``, the name the parent's
    type annotates (``_register_doubling_type``).
    """

    twice_among = ListFilter(field_name="parent__twice", lookup_expr="in")
    twice_below = django_filters.NumberFilter(field_name="parent__twice", lookup_expr="lt")

    class Meta:
        model = models.ScalarSpecimen
        fields = ()

    @override
    def filter_queryset(self, queryset: QuerySet[Model]) -> QuerySet[Model]:
        return super().filter_queryset(queryset.annotate(twice=F("signed_big") * 3))


#: The raw sets the driver routes build, by route name.
_RAW_SETS: dict[str, type[FilterSet]] = {
    "book-filter": BookFilter,
    "plain-subclass": _PlainBookFilter,
    "unserved": _UnservedBookSet,
    "aliased-shelf": _AliasedShelfBookSet,
    "unserved-flat-off": _UnservedFlatOffBookSet,
    "reading-list-entry-filter": ReadingListEntryFilter,
    "reading-list-filter": ReadingListFilter,
    "range-own-flat-on": _range_own_parent(flat=True),
    "range-own-flat-off": _range_own_parent(flat=False),
    "range-over-a-relation": _RangeOverRelationSet,
    "global-id-over-a-generic-key": _GlobalIDOverGenericSet,
    "model-choice-over-a-generic-key": _ModelChoiceOverGenericSet,
    "model-multiple-choice-past-a-key-onto-a-generic-key": _ModelMultipleChoicePastKeySet,
    "char-over-a-generic-key": _CharOverGenericSet,
    "null-test-over-a-generic-key": _NullTestOverGenericSet,
    "range-past-a-key-onto-a-generic-key": _RangePastKeyOntoGenericSet,
    "choice-past-a-key-onto-a-generic-key": _ChoicePastKeyOntoGenericSet,
    "content-type-column": _ContentTypeColumnSet,
    "generic-relation": _GenericRelationSet,
    "model-choice-with-no-queryset": _QuerysetlessChoiceSet,
    "filter-override-with-no-queryset": _QuerysetlessOverrideSet,
    "late-annotation": _late_annotated_set(),
    "late-parent-twice": _LateParentTwiceSet,
}


def _raw_set_rows(filterset_class: type[FilterSet]) -> QuerySet[Model]:
    model = filterset_class._meta.model
    assert model is not None
    return model._default_manager.order_by("pk")


def _row_ids(rows: Iterable[object]) -> JsonResponse:
    return JsonResponse([saved_pk(require_instance(row, Model)) for row in rows], safe=False)


def _direct_rows(request: HttpRequest, name: str) -> JsonResponse:
    """A consumer view building the set itself over the query string, with the request."""
    filterset_class = _RAW_SETS[name]
    filterset = filterset_class(
        data=request.GET,
        queryset=_raw_set_rows(filterset_class),
        request=request,
    )
    return _row_ids(require(filterset.qs, is_queryset))


class _IdSerializer(serializers.Serializer[Model]):
    id = serializers.IntegerField(source="pk")


class _BackendRowsView(generics.ListAPIView[Model]):
    """A session-authenticated DRF list filtered through ``DjangoFilterBackend``."""

    serializer_class = _IdSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class: ClassVar[type[BaseFilterSet] | None] = None
    authentication_classes = (SessionAuthentication,)
    permission_classes = ()
    renderer_classes = (JSONRenderer,)
    pagination_class = None


class _ListedRowsView(FilterView):
    """django-filter's ``FilterView`` answering its filtered rows' ids as JSON."""

    @override
    def render_to_response(
        self,
        context: dict[str, object],
        **response_kwargs: object,
    ) -> JsonResponse:
        return _row_ids(self.object_list)


urlpatterns = [
    path("graphql-raw-filter-forms/", _graphql_view),
    *(
        route
        for name, filterset_class in _RAW_SETS.items()
        for route in (
            path(f"raw-sets/direct/{name}/", _direct_rows, {"name": name}),
            path(
                f"raw-sets/backend/{name}/",
                _BackendRowsView.as_view(
                    filterset_class=filterset_class,
                    queryset=_raw_set_rows(filterset_class),
                ),
            ),
            path(
                f"raw-sets/filter-view/{name}/",
                _ListedRowsView.as_view(
                    filterset_class=filterset_class,
                    queryset=_raw_set_rows(filterset_class),
                ),
            ),
        )
    ),
    path(
        "raw-sets/backend/shadowed-annotation/",
        _BackendRowsView.as_view(
            filterset_class=_ShadowedAnnotationSet,
            queryset=_shadowed_rows(),
        ),
    ),
    path(
        "raw-sets/filter-view/shadowed-annotation/",
        _ListedRowsView.as_view(filterset_class=_ShadowedAnnotationSet, queryset=_shadowed_rows()),
    ),
]


class _DecimalSeeingFilter(django_filters.NumberFilter):
    """A consumer ``filter`` override that keeps ``kept`` only when it receives a decimal."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        if value is None:
            return qs
        return qs.filter(label="kept" if isinstance(value, Decimal) else "other")


class _SignedBigComparisonSet(FilterSet):
    signed_big_overridden = _DecimalSeeingFilter(field_name="signed_big", lookup_expr="exact")
    signed_big_at_most = django_filters.NumberFilter(field_name="signed_big", lookup_expr="lte")
    signed_big_array_among = ArrayFilter(field_name="signed_big", lookup_expr="in")
    signed_big_containing = django_filters.NumberFilter(
        field_name="signed_big",
        lookup_expr="contains",
    )
    signed_big_ending = django_filters.NumberFilter(
        field_name="signed_big",
        lookup_expr="endswith",
    )
    signed_big_matching = django_filters.NumberFilter(field_name="signed_big", lookup_expr="regex")
    signed_big_as_sent = django_filters.NumberFilter(
        field_name="signed_big",
        method="_kept_for_a_decimal",
    )

    def _kept_for_a_decimal(
        self,
        queryset: QuerySet[models.ScalarSpecimen],
        name: str,
        value: object,
    ) -> QuerySet[models.ScalarSpecimen]:
        del name
        return queryset.filter(label="kept" if isinstance(value, Decimal) else "other")

    class Meta:
        model = models.ScalarSpecimen
        fields = {
            "signed_big": [
                "exact",
                "gte",
                "lt",
                "in",
                "range",
            ],
        }


class _PlainYearSpanSet(django_filters.FilterSet):
    occurred_year_span = RangeFilter(field_name="occurred_on", lookup_expr="year__range")

    class Meta:
        model = models.ScalarSpecimen
        fields = ("label",)


#: Sets a test declares while a project lookup it registers is in place, by parent name.
_TEST_LOCAL_SETS: dict[str, type[BaseFilterSet]] = {}


def _filter_set(parent: str) -> type[BaseFilterSet]:
    shipped: dict[str, type[BaseFilterSet]] = {
        "package": PackageCleanedScalarSet,
        "django-filter": PlainCleanedScalarSet,
        "generated": _SignedBigComparisonSet,
        "plain-year": _PlainYearSpanSet,
    }
    return shipped[parent] if parent in shipped else _TEST_LOCAL_SETS[parent]


def _repeated_set(parent: str) -> type[BaseFilterSet]:
    base = {"package": FilterSet, "django-filter": django_filters.FilterSet}[parent]
    declared = type(
        "RepeatedChoiceSet",
        (base,),
        {
            "signed_big_in": ListFilter(
                field_name="signed_big",
                lookup_expr="in",
                widget=forms.SelectMultiple,
            ),
            "Meta": type("Meta", (), {"model": models.ScalarSpecimen, "fields": ()}),
        },
    )
    assert issubclass(declared, BaseFilterSet)
    return declared


def _schema(*, error_policy: dict[str, object] | None = None) -> DjangoSchema:
    class ScalarOutput(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("label",)

    @strawberry.type
    class Query:
        def _rows(self, parent: str, where: JSON) -> QuerySet[models.ScalarSpecimen]:
            return _filter_set(parent)(
                data=json_object(where),
                queryset=models.ScalarSpecimen.objects.order_by("label"),
            ).qs

        def _raw_rows(self, parent: str, query: str) -> QuerySet[models.ScalarSpecimen]:
            return _filter_set(parent)(
                data=QueryDict(query),
                queryset=models.ScalarSpecimen.objects.order_by("label"),
            ).qs

        def _repeated_rows(self, parent: str, query: str) -> QuerySet[models.ScalarSpecimen]:
            return _repeated_set(parent)(
                data=QueryDict(query),
                queryset=models.ScalarSpecimen.objects.order_by("label"),
            ).qs

        rows: QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=list[ScalarOutput],
        )
        raw_rows: QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_raw_rows,
            graphql_type=list[ScalarOutput],
        )
        repeated_rows: QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_repeated_rows,
            graphql_type=list[ScalarOutput],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config(), error_policy=error_policy)


def _post(schema: DjangoSchema, query: str, variables: JSONObject) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables=variables, url="/graphql-raw-filter-forms/")
    finally:
        _CURRENT["schema"] = None


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize(
    "where",
    [
        pytest.param({"price_span_0": "10", "price_span_1": "11"}, id="decimal-range"),
        pytest.param(
            {
                "occurred_at_span_0": "2026-01-01 00:00:00",
                "occurred_at_span_1": "2026-12-31 00:00:00",
            },
            id="datetime-range",
        ),
        pytest.param(
            {
                "external_id_span_0": str(KEPT_EXTERNAL_ID),
                "external_id_span_1": str(KEPT_EXTERNAL_ID),
            },
            id="uuid-range",
        ),
        pytest.param({"signed_big_span_0": "5", "signed_big_span_1": "8"}, id="integer-range"),
        pytest.param({"price_in": ["10.5"]}, id="decimal-list"),
        pytest.param({"occurred_at_in": ["2026-01-02 03:04:05"]}, id="datetime-list"),
        pytest.param({"external_id_in": [str(KEPT_EXTERNAL_ID)]}, id="uuid-list"),
        pytest.param({"signed_big_in": ["7"]}, id="integer-list"),
    ],
)
def test_declared_scalar_ranges_and_lists_match_the_rows_their_forms_clean(
    parent: str,
    where: JSONObject,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Each real scalar range or list applies its declared form under both supported parent sets."""
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    schema = _schema()
    statements = record_compiled_sql("scalars_scalarspecimen")
    result = _post(
        schema,
        "query($parent: String!, $where: JSON!) { rows(parent: $parent, where: $where) { label } }",
        {"parent": parent, "where": where},
    )
    assert result == {"data": {"rows": [{"label": "kept"}]}}, result
    assert len(statements) == 1, statements


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize(
    ("query_string", "labels"),
    [
        pytest.param("signed_big_in=7,900", ["kept", "other"], id="comma-separated"),
        pytest.param("signed_big_in=7", ["kept"], id="one-member"),
        pytest.param("signed_big_in=", ["kept", "other", "unselected"], id="empty"),
        pytest.param("", ["kept", "other", "unselected"], id="absent"),
    ],
)
def test_django_query_dict_arguments_keep_csv_emptiness_and_membership(
    parent: str,
    query_string: str,
    labels: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Django reads comma-separated members and retains upstream omission and empty-string skips."""
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    unselected = cleaned_specimen("unselected", kept=False)
    unselected.signed_big = 1001
    unselected.save(update_fields=["signed_big"])
    schema = _schema()
    statements = record_compiled_sql("scalars_scalarspecimen")
    result = _post(
        schema,
        "query($parent: String!, $query: String!) { rawRows(parent: $parent, query: $query) { label } }",
        {"parent": parent, "query": query_string},
    )
    assert result == {"data": {"rawRows": [{"label": label} for label in labels]}}, result
    assert len(statements) == 1, statements


_PAST_ANY_INTEGER = "-1e999999999999999999"
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1


def _raw_labels(parent: str, query_string: str, schema: DjangoSchema | None = None) -> JSONObject:
    return _post(
        schema or _schema(),
        "query($parent: String!, $query: String!) { rawRows(parent: $parent, query: $query) { label } }",
        {"parent": parent, "query": query_string},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize(
    ("query_string", "labels", "statements"),
    [
        pytest.param(
            f"signed_big_span_0={_PAST_ANY_INTEGER}&signed_big_span_1=8",
            ["kept"],
            1,
            id="range-start-below",
        ),
        pytest.param(
            f"signed_big_span_0={_PAST_ANY_INTEGER}",
            ["kept", "other"],
            1,
            id="lone-start-below",
        ),
        pytest.param(f"signed_big_span_1={_PAST_ANY_INTEGER}", [], 0, id="lone-end-below"),
        pytest.param(f"signed_big_in={_PAST_ANY_INTEGER},7", ["kept"], 1, id="in-member-below"),
        pytest.param(f"signed_big_in={_PAST_ANY_INTEGER}", [], 0, id="in-every-member-below"),
    ],
)
def test_a_declared_integer_range_or_list_answers_a_number_past_the_column_without_converting_it(
    parent: str,
    query_string: str,
    labels: list[str],
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A bound or member past ``signed_big``'s range answers from the end it lies past.

    django-filter's ``NumberFilter`` caps a decimal only from above, so the raw form
    cleans ``-1e999999999999999999``; ``int()`` of it cannot finish, and the package's
    ``RangeFilter`` and ``ListFilter`` compare it without one, under either parent.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    recorded = record_compiled_sql("scalars_scalarspecimen")
    result = _raw_labels(parent, query_string)
    assert result == {"data": {"rawRows": [{"label": label} for label in labels]}}, result
    assert len(recorded) == statements, recorded


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query_string", "labels", "statements"),
    [
        pytest.param(f"signed_big={_PAST_ANY_INTEGER}", [], 0, id="exact-below"),
        pytest.param(
            f"signed_big__gte={_PAST_ANY_INTEGER}",
            [
                "kept",
                "max",
                "min",
                "other",
            ],
            1,
            id="gte-below",
        ),
        pytest.param(f"signed_big__lt={_PAST_ANY_INTEGER}", [], 0, id="lt-below"),
        pytest.param(f"signed_big__in={_PAST_ANY_INTEGER},7", ["kept"], 1, id="in-member-below"),
        pytest.param(
            f"signed_big__range={_PAST_ANY_INTEGER},7",
            ["kept", "min"],
            1,
            id="range-start-below",
        ),
        pytest.param(f"signed_big_at_most={_PAST_ANY_INTEGER}", [], 0, id="declared-lte-below"),
        pytest.param(
            f"signed_big_array_among={_PAST_ANY_INTEGER},7",
            ["kept"],
            1,
            id="declared-array-in-member-below",
        ),
        pytest.param(
            f"signed_big_overridden={_PAST_ANY_INTEGER}",
            ["kept"],
            1,
            id="filter-override-receives-the-decimal-parity",
        ),
        pytest.param(
            f"signed_big_as_sent={_PAST_ANY_INTEGER}",
            ["kept"],
            1,
            id="method-receives-the-decimal-parity",
        ),
        pytest.param(
            "signed_big__lt=-1e1000000",
            [],
            0,
            id="lt-below-million-exponent-18s-at-parent",
        ),
        pytest.param("signed_big=1e40", [], 0, id="exact-above-parity"),
        pytest.param("signed_big_containing=1e40", [], 1, id="declared-contains-above-parity"),
        pytest.param("signed_big_ending=1e40", [], 1, id="declared-endswith-above-parity"),
        pytest.param(
            f"signed_big_containing={_PAST_ANY_INTEGER}",
            [],
            1,
            id="declared-contains-below-parity",
        ),
        pytest.param(f"signed_big={_INT64_MAX}.5", ["max"], 1, id="exact-fraction-short-parity"),
        pytest.param(
            f"signed_big__lt={_INT64_MAX}.5",
            ["kept", "min", "other"],
            1,
            id="lt-fraction-short-parity",
        ),
    ],
)
def test_a_generated_or_declared_integer_comparison_answers_a_number_past_the_column_without_converting_it(
    query_string: str,
    labels: list[str],
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Each generated ``signed_big`` lookup and a declared ``NumberFilter`` read the side, not the number.

    A number past the column's 64-bit range answers as Django's range-aware comparison
    reads one past that end (matching nothing or everything), an ``in`` member drops and a
    ``range`` bound widens; ``-2**63`` stays the lowest value the column stores, ``1e40``
    lies past the top under django-filter's cap, and a fraction short of one past an end
    is compared as Django truncates it. A ``method=`` filter and a class-level ``filter``
    override receive the decimal their form cleaned, and a text-pattern lookup
    (``contains``, ``endswith``), which Django never converts to an integer, compares the
    decimal's own spelling.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    for label, stored in (("min", _INT64_MIN), ("max", _INT64_MAX)):
        bound = cleaned_specimen(label, kept=False)
        bound.signed_big = stored
        bound.save(update_fields=["signed_big"])
    recorded = record_compiled_sql("scalars_scalarspecimen")
    result = _raw_labels("generated", query_string)
    assert result == {"data": {"rawRows": [{"label": label} for label in labels]}}, result
    assert len(recorded) == statements, recorded


@pytest.mark.django_db
def test_a_declared_regex_over_an_integer_column_answers_as_djangos_own_regex(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A declared ``regex`` over ``signed_big`` receives ``1e40`` as its form cleaned it.

    Django's ``Regex`` never converts its value to an integer (``Lookup.prepare_rhs``
    false), so nothing is held and the one statement answers as the backend answers
    Django's own ``signed_big__regex`` with the decimal: SQLite matches its spelling and
    finds no row, PostgreSQL has no ``text ~ numeric`` operator and refuses it.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    answer = database_answer(
        models.ScalarSpecimen.objects.filter(signed_big__regex=Decimal("1e40"))
        .order_by("label")
        .values_list("label", flat=True),
    )
    schema = _schema(error_policy={"enabled": False})
    recorded = record_compiled_sql("scalars_scalarspecimen")
    result = _raw_labels("generated", "signed_big_matching=1e40", schema)
    assert_database_answer(result, "rawRows", answer)
    assert len(recorded) == 1, recorded


@contextlib.contextmanager
def _registered_lookup(
    field_class: type[Field[object, object]],
    lookup: type[Lookup],
) -> Generator[None]:
    """Register ``lookup`` on ``field_class`` while open, then drop the operands it resolved.

    ``filters/base.py`` caches each column's resolved lookup operand for the process; an
    entry written under the registration would outlive it into the next test on the
    worker.
    """
    try:
        with register_lookup(field_class, lookup):
            yield
    finally:
        _lookup_operand.cache_clear()
        _model_lookup_operand.cache_clear()


class _DivisibleBy(Lookup):
    """A project lookup on integer columns, as Django's custom-lookup guide writes one."""

    lookup_name = "divisible_by"

    @override
    def as_sql(self, compiler: SQLCompiler, connection: BaseDatabaseWrapper) -> "_AsSqlType":
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} %% {rhs} = 0", (*lhs_params, *rhs_params)


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
def test_a_project_lookup_receives_the_number_its_form_cleaned(
    parent: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``register_lookup`` lookup owns what its value means, so nothing is held for it.

    ``divisible_by`` prepares ``-5`` through ``unsigned_big`` (``prepare_rhs`` true by
    default) but reads more than which side of the column's range ``-5`` lies on: held to
    ``-1``, every row would divide by it. It answers as Django prepares ``-5``, under
    both parents.
    """
    for label, stored in (
        ("a", 10),
        ("b", 7),
        ("c", 0),
        ("d", 15),
    ):
        row = cleaned_specimen(label, kept=False)
        row.unsigned_big = stored
        row.save(update_fields=["unsigned_big"])
    base = {"package": FilterSet, "django-filter": django_filters.FilterSet}[parent]
    with _registered_lookup(IntegerField, _DivisibleBy):
        declared = type(
            "DivisibleBySet",
            (base,),
            {
                "divisible": django_filters.NumberFilter(
                    field_name="unsigned_big",
                    lookup_expr="divisible_by",
                ),
                "Meta": type("Meta", (), {"model": models.ScalarSpecimen, "fields": ()}),
            },
        )
        assert issubclass(declared, BaseFilterSet)
        monkeypatch.setitem(_TEST_LOCAL_SETS, "divisible", declared)
        result = _raw_labels("divisible", "divisible=-5")
    assert result == {"data": {"rawRows": [{"label": "a"}, {"label": "c"}, {"label": "d"}]}}, (
        result
    )


@pytest.mark.django_db
def test_a_plain_parents_two_bound_year_range_past_the_range_answers_as_one_past_it() -> None:
    """Both bounds of a ``year__range`` under a plain django-filter parent are held first.

    ``-1e999999999999999999`` answers exactly as ``-9223372036854775809``, one past the
    year output's 64-bit range, never with the ``MemoryError`` its ``int()`` raises. A
    plain parent's form runs no bind ask, so that integer answers as the backend answers
    Django's own ``occurred_on__year__range``: SQLite's driver cannot bind it,
    PostgreSQL compares it and matches no row.
    """
    cleaned_specimen("kept", kept=True)
    one_past = _INT64_MIN - 1
    answer = database_answer(
        models.ScalarSpecimen.objects.filter(occurred_on__year__range=(one_past, one_past))
        .order_by("label")
        .values_list("label", flat=True),
    )
    query = "occurred_year_span_0={0}&occurred_year_span_1={0}"
    schema = _schema(error_policy={"enabled": False})
    past = _raw_labels("plain-year", query.format(_PAST_ANY_INTEGER), schema)
    assert_database_answer(past, "rawRows", answer)
    assert past == _raw_labels("plain-year", query.format(one_past), schema), past


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
def test_a_consumer_select_multiple_widget_reads_each_repeated_query_key(
    parent: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Replacing the widget changes raw input decoding to repeated-key membership on both parents."""
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    unselected = cleaned_specimen("unselected", kept=False)
    unselected.signed_big = 1001
    unselected.save(update_fields=["signed_big"])
    schema = _schema()
    statements = record_compiled_sql("scalars_scalarspecimen")
    result = _post(
        schema,
        "query($parent: String!, $query: String!) { repeatedRows(parent: $parent, query: $query) { label } }",
        {"parent": parent, "query": "signed_big_in=7&signed_big_in=900"},
    )
    assert result == {"data": {"repeatedRows": [{"label": "kept"}, {"label": "other"}]}}, result
    assert len(statements) == 1, statements


def _split_widget_schema(mode: str) -> DjangoSchema:
    from django.contrib.postgres.forms import SplitArrayWidget  # noqa: PLC0415

    class SplitShelfChild(FilterSet):
        arr = django_filters.Filter(
            field_name="code",
            lookup_expr="in",
            widget=SplitArrayWidget(forms.TextInput(), size=2),
        )

        class Meta:
            model = library_models.Shelf
            fields = {"topic": ["exact"]}

    class SplitBranch(FilterSet):
        shelves = RelatedFilter(SplitShelfChild, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class SplitShelfOutput(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("code",)

    class SplitBranchOutput(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("name",)

    SplitBranch.get_filters()

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: JSON,
        ) -> QuerySet[library_models.Branch]:
            queryset = library_models.Branch.objects.order_by("name")
            if mode == "apply":
                return SplitBranch.apply_sync(where, queryset, info)
            return SplitBranch(
                data=json_object(where),
                queryset=queryset,
                prefix="p" if mode == "direct-prefixed" else None,
            ).qs

        def _all_rows(self) -> QuerySet[library_models.Branch]:
            return library_models.Branch.objects.order_by("name")

        rows: QuerySet[library_models.Branch] = strawberry.field(
            resolver=_rows,
            graphql_type=list[SplitBranchOutput],
        )
        all_rows: QuerySet[library_models.Branch] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[SplitBranchOutput],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, types=[SplitShelfOutput], config=strawberry_config())


@pytest.mark.pg
@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["apply", "direct", "direct-prefixed"])
@pytest.mark.parametrize(
    ("values", "names"),
    [
        pytest.param(["A-1", "Z-9"], ["alpha"], id="first-index-matches"),
        pytest.param(["Z-9", "B-1"], ["beta"], id="second-index-matches"),
        pytest.param(["X-1", "Z-9"], [], id="neither-index-matches"),
    ],
)
def test_a_real_split_array_widget_filters_under_its_actual_index_keys(
    mode: str,
    values: list[str],
    names: list[str],
) -> None:
    """A genuine widget binds both indices through apply and raw forms, including prefixed forms."""
    alpha = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=alpha, code="A-1", topic="maps")
    beta = library_models.Branch.objects.create(name="beta")
    library_models.Shelf.objects.create(branch=beta, code="B-1", topic="law")
    library_models.Branch.objects.create(name="gamma")
    lead = "p-" if mode == "direct-prefixed" else ""
    where: JSONObject = (
        {"shelves__arr": values}
        if mode == "apply"
        else {f"{lead}shelves__arr_{index}": value for index, value in enumerate(values)}
    )
    payload = _post(
        _split_widget_schema(mode),
        "query($where: JSON!) { rows(where: $where) { name } allRows { name } }",
        {"where": where},
    )
    assert payload == {
        "data": {
            "rows": [{"name": name} for name in names],
            "allRows": [{"name": name} for name in ("alpha", "beta", "gamma")],
        },
    }, payload


def _raw_integer_membership_schema() -> DjangoSchema:
    class BookGenreInFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__id": ["in"]}

    class MultiBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres__name": ["icontains"], "loans__note": ["icontains"]}

    class ManyInactiveBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {
                path: [
                    "icontains",
                    "exact",
                    "iexact",
                    "startswith",
                ]
                for path in (
                    "genres__name",
                    "loans__note",
                    "loans__patron__email",
                    "loans__patron__name",
                )
            }

    class NoLeafBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields: dict[str, list[str]] = {}

    declarations = {
        "membership": BookGenreInFilter,
        "one-active": MultiBookFilter,
        "many-inactive": ManyInactiveBookFilter,
        "leafless": NoLeafBookFilter,
    }
    for declaration in declarations.values():
        declaration.get_filters()

    class RawMembershipBook(DjangoType):
        class Meta:
            model = library_models.Book
            fields = ("title",)

    BookGenreInFilter.get_filters()

    @strawberry.type
    class Query:
        def _rows(self, where: JSON, mode: str = "membership") -> QuerySet[library_models.Book]:
            selected = declarations[mode]
            selected.get_filters()
            return selected(
                data=json_object(where),
                queryset=library_models.Book.objects.order_by("title"),
            ).qs

        def _all_rows(self) -> QuerySet[library_models.Book]:
            return library_models.Book.objects.order_by("title")

        rows: QuerySet[library_models.Book] = strawberry.field(
            resolver=_rows,
            graphql_type=list[RawMembershipBook],
        )
        all_rows: QuerySet[library_models.Book] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[RawMembershipBook],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "shape",
    [
        "oversized",
        "mixed",
        "matching",
        "empty",
        "omitted",
    ],
)
def test_raw_generated_integer_membership_remains_restrictive_when_every_member_drops(
    shape: str,
) -> None:
    """A raw overflowing member is discarded without widening an empty routed membership."""
    branch = library_models.Branch.objects.create(name="Raw membership")
    shelf = library_models.Shelf.objects.create(branch=branch, code="RAW-1")
    first = library_models.Book.objects.create(shelf=shelf, title="First")
    second = library_models.Book.objects.create(shelf=shelf, title="Second")
    library_models.Book.objects.create(shelf=shelf, title="Unlinked")
    genre = library_models.Genre.objects.create(name="matching")
    other = library_models.Genre.objects.create(name="other")
    first.genres.add(genre, other)
    second.genres.add(other)
    oversized = 99999999999999999999999
    inputs: dict[str, JSONObject] = {
        "oversized": {"genres__id__in": [oversized]},
        "mixed": {"genres__id__in": [genre.pk, oversized]},
        "matching": {"genres__id__in": [genre.pk]},
        "empty": {"genres__id__in": []},
        "omitted": {},
    }
    names = (
        ["First"]
        if shape in {"mixed", "matching"}
        else ["First", "Second", "Unlinked"]
        if shape == "omitted"
        else []
    )
    payload = _post(
        _raw_integer_membership_schema(),
        "query($where: JSON!) { rows(where: $where) { title } allRows { title } }",
        {"where": inputs[shape]},
    )
    assert payload == {
        "data": {
            "rows": [{"title": title} for title in names],
            "allRows": [{"title": title} for title in ("First", "Second", "Unlinked")],
        },
    }, payload


def _routing_world() -> None:
    branch = library_models.Branch.objects.create(name="Inactive candidates")
    shelf = library_models.Shelf.objects.create(branch=branch, code="INACTIVE-1")
    first = library_models.Book.objects.create(shelf=shelf, title="First")
    second = library_models.Book.objects.create(shelf=shelf, title="Second")
    library_models.Book.objects.create(shelf=shelf, title="Unlinked")
    first.genres.add(
        library_models.Genre.objects.create(name="cardio-a"),
        library_models.Genre.objects.create(name="cardio-b"),
    )
    second.genres.add(library_models.Genre.objects.create(name="other"))
    for index in (1, 2):
        patron = library_models.Patron.objects.create(
            name=f"Loan patron {index}",
            email=f"loan-{index}@example.test",
        )
        library_models.Loan.objects.create(book=second, patron=patron, note=f"Cardio {index}")


@pytest.mark.django_db
def test_sixteen_inactive_generated_candidates_keep_the_leafless_statement(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Sixteen eligible generated no-ops keep every root and the leafless SQL verbatim."""
    _routing_world()
    statements = record_compiled_sql()
    payload = _post(
        _raw_integer_membership_schema(),
        '{ manyRows: rows(mode: "many-inactive", where: {}) { title } '
        'emptyRows: rows(mode: "leafless", where: {}) { title } allRows { title } }',
        {},
    )
    roots = [{"title": title} for title in ("First", "Second", "Unlinked")]
    assert payload == {"data": {"manyRows": roots, "emptyRows": roots, "allRows": roots}}, payload
    book_sql = [statement for statement in statements if 'FROM "library_book"' in statement]
    assert len(book_sql) == 3, statements
    assert book_sql[0] == book_sql[1] == book_sql[2], book_sql
    assert "EXISTS" not in book_sql[0].upper(), book_sql


@pytest.mark.django_db
@pytest.mark.parametrize("active", ["genres", "loans"])
def test_one_active_generated_candidate_attaches_no_inactive_sibling_predicate(
    active: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Either active generated path attaches one EXISTS and leaves its inactive sibling alone."""
    _routing_world()
    statements = record_compiled_sql()
    payload = _post(
        _raw_integer_membership_schema(),
        'query($where: JSON!) { rows(mode: "one-active", where: $where) { title } allRows { title } }',
        {
            "where": {
                "genres__name__icontains"
                if active == "genres"
                else "loans__note__icontains": "cardio",
            },
        },
    )
    assert payload == {
        "data": {
            "rows": [{"title": "First" if active == "genres" else "Second"}],
            "allRows": [{"title": title} for title in ("First", "Second", "Unlinked")],
        },
    }, payload
    book_sql = [statement for statement in statements if 'FROM "library_book"' in statement]
    assert len(book_sql) == 2, statements
    assert [sql.upper().count("EXISTS") for sql in book_sql] == [1, 0], book_sql
    inactive_table = '"library_loan"' if active == "genres" else '"library_genre"'
    assert all(inactive_table not in sql for sql in book_sql), book_sql
    assert all("DISTINCT" not in sql.upper() for sql in book_sql), book_sql


def _direct_integer_list_schema() -> DjangoSchema:
    class DirectCountSet(FilterSet):
        count_among = ListFilter(field_name="quantity", lookup_expr="in")
        count_outside = ListFilter(field_name="quantity", lookup_expr="in", exclude=True)
        count_array = ArrayFilter(field_name="quantity", lookup_expr="in")

        class Meta:
            model = models.OverrideSpecimen
            fields = ("quantity",)

    class DirectCountOutput(DjangoType):
        class Meta:
            model = models.OverrideSpecimen
            fields = ("label",)

    def queryset() -> QuerySet[models.OverrideSpecimen]:
        return models.OverrideSpecimen.objects.order_by("label")

    @strawberry.type
    class Query:
        def _rows(self, name: str, members: JSON) -> QuerySet[models.OverrideSpecimen]:
            rows = queryset()
            bound = DirectCountSet(data={}, queryset=rows).filters[name]
            return bound.filter(rows, members)

        def _all_rows(self) -> QuerySet[models.OverrideSpecimen]:
            return queryset()

        rows: QuerySet[models.OverrideSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=list[DirectCountOutput],
        )
        all_rows: QuerySet[models.OverrideSpecimen] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[DirectCountOutput],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("name", "members", "labels"),
    [
        pytest.param("count_among", ["abc", 12], ["high"], id="unconvertible-member-dropped"),
        pytest.param("count_among", ["abc"], [], id="every-member-dropped"),
        pytest.param(
            "count_outside",
            ["abc"],
            ["high", "low"],
            id="every-member-dropped-excluded",
        ),
        pytest.param("count_among", [12], ["high"], id="admitted-member"),
        pytest.param("count_outside", [12], ["low"], id="admitted-member-excluded"),
        pytest.param("count_array", [12.5], [], id="array-fractional-member-dropped"),
        pytest.param("count_array", [10**20], [], id="array-overflowing-member-dropped"),
        pytest.param("count_array", [12, 10**20], ["high"], id="array-overflow-beside-member"),
    ],
)
def test_a_public_integer_list_primitive_drops_members_the_column_cannot_convert(
    name: str,
    members: list[object],
    labels: list[str],
) -> None:
    """A consumer's direct public filter call drops an invalid integer instead of widening or failing."""
    models.OverrideSpecimen.objects.create(label="low", quantity=5, token="A")
    models.OverrideSpecimen.objects.create(label="high", quantity=12, token="B")
    payload = _post(
        _direct_integer_list_schema(),
        "query($name: String!, $members: JSON!) { "
        "rows(name: $name, members: $members) { label } allRows { label } }",
        {"name": name, "members": members},
    )
    assert payload == {
        "data": {
            "rows": [{"label": label} for label in labels],
            "allRows": [{"label": label} for label in ("high", "low")],
        },
    }, payload


_OVERFLOW = "99999999999999999999"

#: The owner model and relation each raw relation row filters, by row id.
_RELATIONS: dict[str, tuple[type[Model], str]] = {
    "foreign-key": (library_models.Book, "shelf"),
    "many-to-many": (library_models.Book, "genres"),
    "reverse-foreign-key": (library_models.Shelf, "books"),
    "one-to-one": (library_models.MembershipCard, "patron"),
    "reverse-one-to-one": (library_models.Patron, "card"),
    "text-primary-key": (library_models.Printing, "edition"),
    "text-to-field": (library_models.Printing, "licensor"),
}

#: The declarations each raw relation row binds as ``f``, by row id.
_RELATION_FILTERS: dict[str, Callable[[str], django_filters.Filter]] = {
    "list": lambda field_name: ListFilter(field_name=field_name, lookup_expr="in"),
    "array": lambda field_name: ArrayFilter(field_name=field_name, lookup_expr="in"),
    "lone-bound": lambda field_name: RangeFilter(field_name=field_name, lookup_expr="gte"),
    "crossing": lambda field_name: ListFilter(field_name=field_name, lookup_expr="code__in"),
    "crossing-integer": lambda field_name: ListFilter(
        field_name=field_name,
        lookup_expr="tier__in",
    ),
    "crossing-integer-array": lambda field_name: ArrayFilter(
        field_name=field_name,
        lookup_expr="tier__in",
    ),
    "crossing-integer-control": lambda field_name: ListFilter(
        field_name=f"{field_name}__tier",
        lookup_expr="in",
    ),
    "list-method": lambda field_name: ListFilter(
        field_name=field_name,
        lookup_expr="in",
        method="by_target_code",
    ),
    "array-method": lambda field_name: ArrayFilter(
        field_name=field_name,
        lookup_expr="in",
        method="by_target_code",
    ),
}


def _by_target_code(
    _filterset: BaseFilterSet,
    queryset: QuerySet[Model],
    name: str,
    value: list[str],
) -> QuerySet[Model]:
    """A consumer method filtering on the relation's target ``code``, not its key."""
    return queryset.filter(**{f"{name}__code__in": value})


@strawberry.type
class _RelationAnswer:
    errors: list[str]
    rows: list[str]


def _relation_set(parent: str, kind: str, relation: str) -> type[BaseFilterSet]:
    model, field_name = _RELATIONS[relation]
    base = {"package": FilterSet, "django-filter": django_filters.FilterSet}[parent]
    declared = type(
        "RawRelationSet",
        (base,),
        {
            "f": _RELATION_FILTERS[kind](field_name),
            "by_target_code": _by_target_code,
            "Meta": type("Meta", (), {"model": model, "fields": ()}),
        },
    )
    assert issubclass(declared, BaseFilterSet)
    return declared


def _relation_schema() -> DjangoSchema:
    @strawberry.type
    class Query:
        def _relation_rows(
            self,
            parent: str,
            kind: str,
            relation: str,
            query: str,
        ) -> _RelationAnswer:
            model = _RELATIONS[relation][0]
            filterset = _relation_set(parent, kind, relation)(
                data=QueryDict(query),
                queryset=model._default_manager.order_by("pk"),
            )
            if not filterset.is_valid():
                errors = [
                    f"{name}: {message}"
                    for name, messages in filterset.errors.items()
                    for message in messages
                ]
                return _RelationAnswer(errors=errors, rows=[])
            matched: QuerySet[Model] = filterset.qs
            return _RelationAnswer(errors=[], rows=[str(row) for row in matched])

        relation_rows: _RelationAnswer = strawberry.field(resolver=_relation_rows)

    return DjangoSchema(query=Query, config=strawberry_config())


def _relation_world() -> dict[str, str]:
    """Create one matching and one other row per relation; answer each matching target's key.

    Each shelf's ``tier`` differs from its key, so a tier compared as a key answers other rows.
    """
    branch = library_models.Branch.objects.create(name="Raw relations")
    shelf = library_models.Shelf.objects.create(
        branch=branch,
        code="A-1",
        tier=library_models.Shelf.Tier.UPPER,
    )
    other_shelf = library_models.Shelf.objects.create(
        branch=branch,
        code="B-1",
        tier=library_models.Shelf.Tier.LOWER,
    )
    first = library_models.Book.objects.create(shelf=shelf, title="First")
    second = library_models.Book.objects.create(shelf=other_shelf, title="Second")
    genre = library_models.Genre.objects.create(name="matching")
    first.genres.add(genre)
    second.genres.add(library_models.Genre.objects.create(name="other"))
    patron = library_models.Patron.objects.create(name="Ada")
    card = library_models.MembershipCard.objects.create(patron=patron, barcode="CARD-1")
    other_patron = library_models.Patron.objects.create(name="Bo")
    library_models.MembershipCard.objects.create(patron=other_patron, barcode="CARD-2")
    house = library_models.Publisher.objects.create(name="Kept House", house_code="KH")
    other_house = library_models.Publisher.objects.create(name="Other House", house_code="OH")
    edition = library_models.Edition.objects.create(isbn_13="9780000000001", publisher=house)
    other_edition = library_models.Edition.objects.create(
        isbn_13="9780000000002",
        publisher=other_house,
    )
    library_models.Printing.objects.create(edition=edition, licensor=house, run_size=1)
    library_models.Printing.objects.create(edition=other_edition, licensor=other_house, run_size=2)
    return {
        "foreign-key": str(saved_pk(shelf)),
        "many-to-many": str(saved_pk(genre)),
        "reverse-foreign-key": str(saved_pk(first)),
        "one-to-one": str(saved_pk(patron)),
        "reverse-one-to-one": str(saved_pk(card)),
        "text-primary-key": edition.isbn_13,
        "text-to-field": house.name,
    }


#: The row each relation's matching key selects, as ``str(row)``.
_MATCHED = {
    "foreign-key": ["First"],
    "many-to-many": ["First"],
    "reverse-foreign-key": ["A-1"],
    "one-to-one": ["CARD-1"],
    "reverse-one-to-one": ["Ada"],
    "text-primary-key": ["9780000000001 x1"],
    "text-to-field": ["9780000000001 x1"],
}


def _post_relation(
    parent: str,
    kind: str,
    relation: str,
    query: str,
) -> JSONObject:
    return _post(
        _relation_schema(),
        "query($parent: String!, $kind: String!, $relation: String!, $query: String!) { "
        "relationRows(parent: $parent, kind: $kind, relation: $relation, query: $query) "
        "{ errors rows } }",
        {
            "parent": parent,
            "kind": kind,
            "relation": relation,
            "query": query,
        },
    )


def _relation_answer(errors: list[str], rows: list[str]) -> JSONObject:
    return {"data": {"relationRows": {"errors": list(errors), "rows": list(rows)}}}


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize("kind", ["list", "array"])
@pytest.mark.parametrize(
    "relation",
    [
        "foreign-key",
        "many-to-many",
        "reverse-foreign-key",
        "one-to-one",
        "reverse-one-to-one",
    ],
)
@pytest.mark.parametrize(
    ("wire", "verdict"),
    [
        pytest.param("{key}", "matched", id="key"),
        pytest.param("{key}.0", "matched", id="integral-decimal"),
        pytest.param(f"{{key}},{_OVERFLOW}", "matched", id="overflow-beside-key"),
        pytest.param("x", "refused", id="junk"),
        pytest.param("{key},x", "refused", id="junk-beside-key"),
        pytest.param(_OVERFLOW, "none", id="overflow"),
        pytest.param("{key}.5", "none", id="fractional"),
        pytest.param("2147483000", "unmatched", id="no-such-row"),
    ],
)
def test_a_declared_list_over_an_integer_keyed_relation_cleans_each_raw_element_as_its_key(
    parent: str,
    kind: str,
    relation: str,
    wire: str,
    verdict: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """``?f=`` over a relation itself reads each element as ``<relation>__<target key>`` does.

    An element the key column cannot hold is the form's error (the 400 a
    ``DjangoFilterBackend`` answers), never a value handed to Django's related lookup,
    which raises; an ``in`` drops an element past the column's integer range or
    fractional, which names no row, so a list left empty matches nothing without a query,
    while a key no row holds is compared like any other.
    """
    keys = _relation_world()
    model, _field_name = _RELATIONS[relation]
    statements = record_compiled_sql(model._meta.db_table)
    result = _post_relation(parent, kind, relation, f"f={wire.format(key=keys[relation])}")
    expected = {
        "matched": _relation_answer([], _MATCHED[relation]),
        "refused": _relation_answer(["f: Enter a number."], []),
        "none": _relation_answer([], []),
        "unmatched": _relation_answer([], []),
    }[verdict]
    assert result == expected, result
    assert len(statements) == (1 if verdict in {"matched", "unmatched"} else 0), statements


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize("kind", ["list", "array"])
@pytest.mark.parametrize("relation", ["text-primary-key", "text-to-field"])
@pytest.mark.parametrize("wire", ["{key}", " {key} "], ids=["key", "padded-key"])
def test_a_declared_list_over_a_text_keyed_relation_strips_each_raw_element_as_its_key(
    parent: str,
    kind: str,
    relation: str,
    wire: str,
) -> None:
    """A text key element is stripped as the key column's own form strips it, ``to_field`` too."""
    keys = _relation_world()
    result = _post_relation(parent, kind, relation, f"f={wire.format(key=keys[relation])}")
    assert result == _relation_answer([], _MATCHED[relation]), result


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize(
    (
        "kind",
        "query",
        "errors",
        "rows",
    ),
    [
        pytest.param("lone-bound", "f_0=x", ["f: Enter a number."], [], id="lone-bound-junk"),
        pytest.param("lone-bound", "f_0={key}", [], ["First", "Second"], id="lone-bound-key"),
        pytest.param("crossing", "f=A-1", [], ["First"], id="crossing-lookup-text"),
        pytest.param("crossing", "f={key}", [], [], id="crossing-lookup-key-as-text"),
    ],
)
def test_a_declared_filter_over_a_relation_cleans_only_where_its_lookup_compares_the_relation(
    parent: str,
    kind: str,
    query: str,
    errors: list[str],
    rows: list[str],
) -> None:
    """A lone bound under a lookup Django applies to the relation is cleaned as its key.

    A ``lookup_expr`` continuing across the relation (``code__in``) compares the crossed
    column, so its element is that column's text, never read as the relation's key.
    """
    keys = _relation_world()
    query = query.format(key=keys["foreign-key"])
    result = _post_relation(parent, kind, "foreign-key", query)
    assert result == _relation_answer(errors, rows), result


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize(
    "kind",
    ["crossing-integer", "crossing-integer-array", "crossing-integer-control"],
)
@pytest.mark.parametrize(
    ("wire", "errors", "rows"),
    [
        pytest.param("3", [], ["First"], id="member"),
        pytest.param("1", [], ["Second"], id="member-equal-to-another-shelfs-key"),
        pytest.param("x", ["f: Enter a number."], [], id="junk"),
        pytest.param(_OVERFLOW, [], [], id="overflow"),
        pytest.param(f"3,{_OVERFLOW}", [], ["First"], id="overflow-beside-member"),
    ],
)
def test_a_declared_list_crossing_a_relation_cleans_each_raw_element_as_the_crossed_column(
    parent: str,
    kind: str,
    wire: str,
    errors: list[str],
    rows: list[str],
) -> None:
    """``?f=`` on ``shelf`` + ``tier__in`` reads each element as ``shelf__tier`` + ``in`` does.

    On the first instance of a fresh package set and under a stock django-filter parent
    alike, an element the ``tier`` column cannot hold is the form's error and one past
    its integer range names no row, never Django's ``ValueError`` or ``OverflowError``.
    """
    _relation_world()
    result = _post_relation(parent, kind, "foreign-key", f"f={wire}")
    assert result == _relation_answer(errors, rows), result


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize("kind", ["list-method", "array-method"])
@pytest.mark.parametrize(
    ("wire", "rows"),
    [
        pytest.param("A-1", ["First"], id="one-code"),
        pytest.param("A-1,B-1", ["First", "Second"], id="two-codes"),
    ],
)
def test_a_method_filter_over_a_relation_receives_each_raw_element_as_sent(
    parent: str,
    kind: str,
    wire: str,
    rows: list[str],
) -> None:
    """A ``method=`` filter on a relation cleans no element: its method, not a lookup, reads it.

    The method filters on the target's ``code``, so a code is never refused as a key.
    """
    _relation_world()
    result = _post_relation(parent, kind, "foreign-key", f"f={wire}")
    assert result == _relation_answer([], rows), result


_UNBINDABLE = [{"message": "Enter a value the database can represent.", "code": "invalid"}]
_SURROGATE = [
    {
        "message": "Text contains invalid Unicode (unpaired surrogate code points).",
        "code": "invalid",
    },
]
_NULL_CHARACTER = [
    {"message": "Null characters are not allowed.", "code": "null_characters_not_allowed"},
]


def _annotation_set(parent: str, query: str, mode: str) -> BaseFilterSet:
    """The annotation set over ``query`` as ``mode`` builds it.

    ``handed``: the queryset handed to the set holds both annotations (and, for a ``par_`` or
    ``offspring_`` key, both ``FilteredRelation`` aliases); ``late``: the set is handed
    unannotated rows and its own ``filter_queryset`` annotates (``_late_annotated_set``);
    ``unhanded``: no queryset is handed, so the set reads the model's default rows, which
    hold no annotation.
    """
    data = QueryDict(query)
    rows = models.ScalarSpecimen.objects.order_by("label")
    if mode == "unhanded":
        return _annotated_set(parent)(data=data)
    if mode == "late":
        assert parent == "package"
        return _late_annotated_set()(data=data, queryset=rows)
    queryset = _annotated_rows(rows)
    if query.startswith(("par_", "offspring_")):
        queryset = queryset.alias(
            par=FilteredRelation("parent"),
            offspring=FilteredRelation("children"),
        )
    return _annotated_set(parent)(data=data, queryset=queryset)


def _error_lines(filterset: BaseFilterSet) -> list[str]:
    return [
        f"{name}: {message}" for name, messages in filterset.errors.items() for message in messages
    ]


@strawberry.type
class _AnnotationRead:
    """What a set reports read in one order: ``form.is_valid()`` before and after ``.qs``."""

    valid_before: bool | None
    valid_after: bool
    errors: list[str]
    rows: list[str]


#: The parent set and the way it is given the annotations, by id: handed under both parents,
#: or added by the package set's own ``filter_queryset`` (``_late_annotated_set``).
_ANNOTATION_MODES = [
    pytest.param("package", "handed", id="package"),
    pytest.param("django-filter", "handed", id="django-filter"),
    pytest.param("package", "late", id="package-filter-queryset"),
]


def _annotation_family() -> None:
    """A ``parent`` specimen (``kids`` 1) and its ``child`` (``kids`` 0, ``lag`` one day)."""
    parent_row = cleaned_specimen("parent", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = parent_row
    child.occurred_at = parent_row.occurred_at + datetime.timedelta(days=1)
    child.save(update_fields=["parent", "occurred_at"])


_ANNOTATION_ROWS = (
    "query($parent: String!, $query: String!, $mode: String!) { "
    "annotationRows(parent: $parent, query: $query, mode: $mode) { errors rows } }"
)


def _annotation_schema() -> DjangoSchema:
    @strawberry.type
    class Query:
        def _annotation_rows(
            self,
            parent: str,
            query: str,
            mode: str,
        ) -> _RelationAnswer:
            filterset = _annotation_set(parent, query, mode)
            try:
                if not filterset.is_valid():
                    return _RelationAnswer(errors=_error_lines(filterset), rows=[])
                matched: QuerySet[Model] = filterset.qs
                return _RelationAnswer(errors=[], rows=[str(row) for row in matched])
            except FieldError as error:
                # A path no queryset holds: Django refuses it when the form or ``.qs`` reads it.
                return _RelationAnswer(errors=[str(error).partition(".")[0]], rows=[])

        def _annotation_read(
            self,
            query: str,
            mode: str,
            order: str,
        ) -> _AnnotationRead:
            """Read the set in ``order``: ``qs``, ``form`` or ``valid`` first.

            ``qs`` reads ``.qs`` first, ``form`` the bare ``form.is_valid()``, ``valid`` the
            set's own ``is_valid()``, which reads no ``.qs`` for an invalid set.
            """
            filterset = _annotation_set("package", query, mode)
            if order == "valid" and not filterset.is_valid():
                return _AnnotationRead(
                    valid_before=None,
                    valid_after=False,
                    errors=_error_lines(filterset),
                    rows=[],
                )
            valid_before = filterset.form.is_valid() if order == "form" else None
            matched: QuerySet[Model] = filterset.qs
            rows = [str(row) for row in matched]
            return _AnnotationRead(
                valid_before=valid_before,
                valid_after=filterset.form.is_valid(),
                errors=_error_lines(filterset),
                rows=rows,
            )

        def _handed_json_builds(self, query: str) -> list[bool]:
            """Whether ``_HandedJsonSet``'s ``qs`` is built after ``is_valid()``, then after ``.qs``.

            django-filter keeps a built ``qs`` as ``_qs``.
            """
            filterset = _HandedJsonSet(
                data=QueryDict(query),
                queryset=models.ScalarSpecimen.objects.annotate(pj=F("payload")),
            )
            _ = filterset.is_valid()
            after_is_valid = hasattr(filterset, "_qs")
            _ = list(filterset.qs)
            return [after_is_valid, hasattr(filterset, "_qs")]

        def _late_filter_queryset_runs(self, query: str, order: str) -> int:
            """How often the late set's ``filter_queryset`` runs for ``.qs`` read in ``order``.

            ``qs``: ``.qs`` read first; ``valid``: ``is_valid()`` asked first, then ``.qs``.
            """
            filterset = _annotation_set("package", query, "late")
            _LATE_FILTER_QUERYSET_RUNS.clear()
            if order == "valid":
                _ = filterset.is_valid()
            _ = list(filterset.qs)
            return len(_LATE_FILTER_QUERYSET_RUNS)

        annotation_rows: _RelationAnswer = strawberry.field(resolver=_annotation_rows)
        annotation_read: _AnnotationRead = strawberry.field(resolver=_annotation_read)
        late_filter_queryset_runs: int = strawberry.field(resolver=_late_filter_queryset_runs)
        handed_json_builds: list[bool] = strawberry.field(resolver=_handed_json_builds)

    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.django_db
@pytest.mark.parametrize(("parent", "mode"), _ANNOTATION_MODES)
@pytest.mark.parametrize(
    ("query", "errors", "rows"),
    [
        pytest.param("lag_among=1 00:00:00", [], ["child"], id="duration-member"),
        pytest.param(
            "lag_among=abc",
            ["lag_among: Enter a valid duration."],
            [],
            id="duration-junk",
        ),
        pytest.param(
            "lag_span_0=0&lag_span_1=1 00:00:00",
            [],
            ["child"],
            id="duration-range",
        ),
        pytest.param(
            "lag_span_0=abc",
            ["lag_span: Enter a valid duration."],
            [],
            id="duration-bound-junk",
        ),
        pytest.param("kids_among=1", [], ["parent"], id="integer-member"),
        pytest.param("kids_among=abc", ["kids_among: Enter a number."], [], id="integer-junk"),
        pytest.param(f"kids_among=0,1.5,{2**63}", [], ["child"], id="integer-members-drop"),
        pytest.param(
            f"kids_span_0=1&kids_span_1={2**63}",
            [],
            ["parent"],
            id="integer-range-past-the-column",
        ),
        pytest.param(
            "kids_span_1=abc",
            ["kids_span: Enter a number."],
            [],
            id="integer-bound-junk",
        ),
        pytest.param("kids_sent=1,abc", [], ["parent"], id="method-receives-the-text-sent"),
        pytest.param("kids_span_0=1&kids_span_1=", [], ["parent"], id="integer-range-empty-box"),
        pytest.param(
            f"kids_span_0={_PAST_ANY_INTEGER}&kids_span_1=1",
            [],
            ["child", "parent"],
            id="integer-bound-past-any-integer",
        ),
        pytest.param(
            f"kids_among={_PAST_ANY_INTEGER},1",
            [],
            ["parent"],
            id="integer-member-past-any-integer",
        ),
        pytest.param("kids_pair=0,1", [], ["child", "parent"], id="integer-range-list"),
        pytest.param(
            "kids_pair=1",
            ["kids_pair: Range query expects two values."],
            [],
            id="integer-range-list-of-one",
        ),
        pytest.param("up_among= PARENT ", [], ["parent"], id="text-member-stripped"),
        pytest.param(
            "kids_pair=0,1,2",
            ["kids_pair: Range query expects two values."],
            [],
            id="integer-range-list-of-three",
        ),
    ],
)
def test_a_raw_value_over_a_queryset_annotation_is_cleaned_as_the_queryset_compares_it(
    parent: str,
    mode: str,
    query: str,
    errors: list[str],
    rows: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Raw members and bounds over annotations clean as the queryset's output fields.

    ``lag`` is a ``DurationField`` expression and ``kids`` a ``Count``, neither a field of
    the model: each value is cleaned by the form field django-filter's ``gte`` filter
    builds for that output, under the package's set and a plain django-filter one alike,
    so junk is the form's error, an empty box leaves its side open, an integer member
    naming no row or past any integer drops and a range bound past the column widens, never
    Django's ``ValueError``, ``ValidationError`` or ``AttributeError``. The package's set
    answers alike when its own ``filter_queryset`` adds the annotations to unannotated rows
    before it calls ``super()`` (``late``): each value is cleaned over the queryset the
    override passes on, its refusal read by ``is_valid()``. A ``method=`` filter over an
    annotation receives each member as sent: its method, not a lookup of the filter's, reads
    the value. A refused value runs no statement; rows run one.
    """
    _annotation_family()
    statements = record_compiled_sql(models.ScalarSpecimen._meta.db_table)
    assert _post(
        _annotation_schema(),
        _ANNOTATION_ROWS,
        {"parent": parent, "query": query, "mode": mode},
    ) == {"data": {"annotationRows": {"errors": errors, "rows": rows}}}
    assert len(statements) == (0 if errors else 1), statements


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize(
    ("query", "rows"),
    [
        pytest.param(
            f"par_span_0=7&par_span_1={2**63}",
            ["child"],
            id="continued-alias-range",
        ),
        pytest.param("par_among=7.5", [], id="continued-alias-fraction"),
        pytest.param(
            "offspring_among=-1e999999999999999999",
            [],
            id="reverse-alias-extreme-list",
        ),
        pytest.param(
            "offspring_among={child},-1e999999999999999999",
            ["parent"],
            id="reverse-alias-mixed-list",
        ),
        pytest.param(
            "offspring_array=-1e999999999999999999",
            [],
            id="reverse-alias-extreme-array",
        ),
        pytest.param(
            "offspring_array={child},-1e999999999999999999",
            ["parent"],
            id="reverse-alias-mixed-array",
        ),
    ],
)
def test_raw_filters_under_both_parents_clean_continued_and_reverse_alias_values(
    parent: str,
    query: str,
    rows: list[str],
) -> None:
    """Raw QueryDict paths use the handed alias and hold before target-key coercion."""
    parent_row = cleaned_specimen("parent", kept=True)
    child = cleaned_specimen("child", kept=True)
    child.parent = parent_row
    child.save(update_fields=["parent"])
    payload = _post(
        _annotation_schema(),
        _ANNOTATION_ROWS,
        {"parent": parent, "query": query.format(child=saved_pk(child)), "mode": "handed"},
    )
    assert payload == {"data": {"annotationRows": {"errors": [], "rows": rows}}}, payload


@pytest.mark.django_db
@pytest.mark.parametrize("parent", ["package", "django-filter"])
@pytest.mark.parametrize("query", ["kids_among=1", "kids_among=abc", "kids_span_0=1"])
def test_a_raw_set_handed_no_queryset_leaves_an_annotation_path_to_django(
    parent: str,
    query: str,
) -> None:
    """With no queryset handed, no queryset holds the annotation: Django refuses the path.

    The set's rows are its model's default ones, so nothing cleans the value as an
    annotation, and the path is Django's ``FieldError`` wherever the form or ``.qs`` reads
    it, the answer a filter naming an unknown path gives.
    """
    cleaned_specimen("parent", kept=True)
    assert _post(
        _annotation_schema(),
        _ANNOTATION_ROWS,
        {"parent": parent, "query": query, "mode": "unhanded"},
    ) == {
        "data": {
            "annotationRows": {"errors": ["Cannot resolve keyword 'kids' into field"], "rows": []},
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "path"),
    [
        pytest.param("par_among=7", "par", id="alias-list"),
        pytest.param("par_span_0=7", "par", id="alias-range"),
        pytest.param("offspring_array=1", "offspring", id="reverse-alias-array"),
    ],
)
def test_a_path_the_filter_queryset_override_does_not_add_is_left_to_django(
    query: str,
    path: str,
) -> None:
    """A path no queryset holds, the one ``filter_queryset`` passes on included, is Django's.

    The late set's override adds ``lag`` and ``kids`` only, so nothing cleans a value over
    the ``par`` or ``offspring`` alias and the path is Django's ``FieldError`` when the
    leaf applies, as it is for a set handed no queryset.
    """
    cleaned_specimen("parent", kept=True)
    assert _post(
        _annotation_schema(),
        _ANNOTATION_ROWS,
        {"parent": "package", "query": query, "mode": "late"},
    ) == {
        "data": {
            "annotationRows": {
                "errors": [f"Cannot resolve keyword '{path}' into field"],
                "rows": [],
            },
        },
    }


_ANNOTATION_READ = (
    "query($query: String!, $mode: String!, $order: String!) { "
    "annotationRead(query: $query, mode: $mode, order: $order) "
    "{ validBefore validAfter errors rows } }"
)


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["handed", "late"])
@pytest.mark.parametrize(
    ("query", "errors"),
    [
        pytest.param(
            "lag_span_0=999999999 00:00:00",
            ["lag_span: Enter a value the database can represent."],
            id="duration-bound-past-sqlite",
        ),
        pytest.param(
            "lag_among=999999999 00:00:00",
            ["lag_among: Enter a value the database can represent."],
            id="duration-member-past-sqlite",
        ),
    ],
)
def test_a_package_set_asks_the_database_about_an_annotation_value(
    mode: str,
    query: str,
    errors: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The package's set asks the bind question of a value over an annotation, late or handed.

    The value is cleaned as a duration, then bind-asked over the queryset that compares it: the
    handed one, or the one the set's own ``filter_queryset`` passes on. SQLite stores a duration
    as integer microseconds, so the database refuses the value and no statement runs.
    PostgreSQL's ``interval`` holds every ``timedelta``, so there the value binds and filters,
    matching no row.
    """
    _annotation_family()
    statements = record_compiled_sql(models.ScalarSpecimen._meta.db_table)
    sqlite = connection.vendor == "sqlite"
    assert _post(
        _annotation_schema(),
        _ANNOTATION_ROWS,
        {"parent": "package", "query": query, "mode": mode},
    ) == {"data": {"annotationRows": {"errors": errors if sqlite else [], "rows": []}}}
    assert len(statements) == (0 if sqlite else 1)


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["handed", "late"])
@pytest.mark.parametrize(
    ("query", "order", "expected"),
    [
        pytest.param(
            "kids_span_0=abc",
            "qs",
            {
                "validBefore": None,
                "validAfter": False,
                "errors": ["kids_span: Enter a number."],
                "rows": ["child", "parent"],
            },
            id="qs-before-errors",
        ),
        pytest.param(
            "kids_among=1,abc&signed_among=7",
            "qs",
            {
                "validBefore": None,
                "validAfter": False,
                "errors": ["kids_among: Enter a number."],
                "rows": ["child", "parent"],
            },
            id="qs-applies-the-leaves-that-cleaned",
        ),
        pytest.param(
            "kids_span_0=1",
            "qs",
            {
                "validBefore": None,
                "validAfter": True,
                "errors": [],
                "rows": ["parent"],
            },
            id="qs-of-a-valid-bound",
        ),
    ],
)
def test_a_bare_qs_read_applies_the_leaves_that_clean_and_reports_the_rest(
    mode: str,
    query: str,
    order: str,
    expected: JSONObject,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """``.qs`` read before ``is_valid()`` applies the leaves that clean and drops a refused one.

    django-filter's own ``qs`` filters whatever ``errors`` holds, so a junk bound or member
    over an annotation is the form's error afterwards and its leaf applies nothing, never
    Django's ``ValueError``: handed, or added by the set's own ``filter_queryset``, in one
    statement.
    """
    _annotation_family()
    statements = record_compiled_sql(models.ScalarSpecimen._meta.db_table)
    assert _post(
        _annotation_schema(),
        _ANNOTATION_READ,
        {"query": query, "mode": mode, "order": order},
    ) == {"data": {"annotationRead": expected}}
    assert len(statements) == 1, statements


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("order", "runs"),
    [pytest.param("qs", 2, id="qs-first"), pytest.param("valid", 1, id="is-valid-first")],
)
@pytest.mark.parametrize("query", ["kids_span_0=1", "kids_span_0=abc"])
def test_a_bare_qs_read_runs_the_sets_filter_queryset_once_more_than_is_valid_first(
    query: str,
    order: str,
    runs: int,
) -> None:
    """``.qs`` read first runs the set's own ``filter_queryset`` twice, ``is_valid()`` first once.

    django-filter's ``qs`` reads ``errors`` before it filters, and the set's ``errors``
    builds ``qs`` to clean a value waiting for the queryset ``filter_queryset`` passes on;
    django-filter then filters again, with the same rows. Asked first, ``is_valid()`` builds
    ``qs`` once and django-filter keeps it for the read that follows.
    """
    _annotation_family()
    assert _post(
        _annotation_schema(),
        "query($query: String!, $order: String!) "
        "{ lateFilterQuerysetRuns(query: $query, order: $order) }",
        {"query": query, "order": order},
    ) == {"data": {"lateFilterQuerysetRuns": runs}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        pytest.param(
            "handed",
            {
                "validBefore": False,
                "validAfter": False,
                "errors": ["kids_span: Enter a number."],
                "rows": ["child", "parent"],
            },
            id="handed",
        ),
        pytest.param(
            "late",
            {
                "validBefore": True,
                "validAfter": False,
                "errors": ["kids_span: Enter a number."],
                "rows": ["child", "parent"],
            },
            id="late",
        ),
    ],
)
def test_the_bare_form_sees_a_late_refusal_only_once_qs_is_built(
    mode: str,
    expected: JSONObject,
) -> None:
    """``form.is_valid()`` asked directly sees a value ``filter_queryset`` refuses only at ``.qs``.

    The set's ``is_valid()`` and ``errors`` build ``qs`` to clean a value only the queryset
    the set's own ``filter_queryset`` passes on resolves; the bare form django-filter builds
    knows no such queryset, so it is valid until ``.qs`` runs and invalid after it. A value
    the handed queryset resolves is the bare form's error from the start.
    """
    _annotation_family()
    assert _post(
        _annotation_schema(),
        _ANNOTATION_READ,
        {"query": "kids_span_0=abc", "mode": mode, "order": "form"},
    ) == {"data": {"annotationRead": expected}}


@pytest.mark.django_db
def test_a_set_with_no_filter_queryset_override_builds_no_qs_to_validate() -> None:
    """A set overriding no ``filter_queryset`` adds no path, so ``is_valid()`` builds no ``qs``.

    ``pj`` is a ``JSONField`` annotation of the queryset handed to the set, so the list is
    applied as sent: its form lists it as uncleaned, yet nothing a ``filter_queryset`` override
    could add awaits it, so ``is_valid()`` leaves ``qs`` unbuilt and the ``.qs`` read that
    follows builds it.
    """
    _annotation_family()
    assert _post(
        _annotation_schema(),
        "query($query: String!) { handedJsonBuilds(query: $query) }",
        {"query": "pj_among=1"},
    ) == {"data": {"handedJsonBuilds": [False, True]}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "driver",
        "query",
        "refusal",
        "labels",
    ),
    [
        pytest.param("backend", "1,abc", {"n_among": ["Enter a number."]}, [], id="backend-junk"),
        pytest.param("filter-view", "1,abc", None, [], id="filter-view-junk"),
        pytest.param("backend", "1", None, ["parent"], id="backend-member"),
        pytest.param("filter-view", "1", None, ["parent"], id="filter-view-member"),
    ],
)
def test_an_override_replacing_a_handed_annotation_cleans_the_value_it_compares(
    driver: str,
    query: str,
    refusal: JSONObject | None,
    labels: list[str],
) -> None:
    """A ``filter_queryset`` override shadowing a handed annotation's name is cleaned over it.

    ``n`` is handed as a ``JSONField`` annotation, whose output gives the list no cleaner,
    and the override replaces it with a ``Count`` before ``super()``: the set's
    ``is_valid()`` builds ``qs`` and cleans each member as the ``Count`` compares it, so a
    junk member is refused (DRF's 400 body, the strict ``FilterView``'s empty answer) and a
    count matches its row.
    """
    _annotation_family()
    status, body = _raw_set_answer(Client(), driver, "shadowed-annotation", {"n_among": query})
    if refusal is not None:
        assert (status, body) == (400, refusal)
        return
    assert status == 200, body
    ids = [
        json_int(row, "id") if driver == "backend" else json_int(row) for row in json_list(body)
    ]
    assert ids == [saved_pk(models.ScalarSpecimen.objects.get(label=label)) for label in labels]


_NATIVE_BESIDE_LATE = "signed_among=abc&kids_span_0=abc"


_BOTH_REFUSALS = ["kids_span: Enter a number.", "signed_among: Enter a number."]


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "mode",
        "order",
        "errors",
        "rows",
        "statements",
    ),
    [
        pytest.param("handed", "valid", _BOTH_REFUSALS, [], 0, id="handed-is-valid-first"),
        pytest.param(
            "late",
            "valid",
            ["signed_among: Enter a number."],
            [],
            0,
            id="late-is-valid-first",
        ),
        pytest.param("handed", "qs", _BOTH_REFUSALS, ["child", "parent"], 1, id="handed-qs-first"),
        pytest.param("late", "qs", _BOTH_REFUSALS, ["child", "parent"], 1, id="late-qs-first"),
    ],
)
def test_a_native_form_error_answers_alone_beside_a_late_refusal(
    mode: str,
    order: str,
    errors: list[str],
    rows: list[str],
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Under ``is_valid()`` a form a field of the model refuses is not handed to ``filter_queryset``.

    ``signed_among`` cleans as the model's ``signed_big`` column; with its junk member
    ``is_valid()`` refuses the form before any queryset is built, so a junk bound over an
    annotation the set's own ``filter_queryset`` adds is not asked and the refusal is the
    model field's alone, where a handed annotation's bound is refused beside it; no
    statement runs. A bare ``.qs`` read first filters whatever ``errors`` holds, as
    django-filter's ``qs`` does, so ``filter_queryset`` runs: the late bound is refused there
    beside the model field's error, neither leaf applies, in one statement.
    """
    _annotation_family()
    recorded = record_compiled_sql(models.ScalarSpecimen._meta.db_table)
    payload = _post(
        _annotation_schema(),
        _ANNOTATION_READ,
        {"query": _NATIVE_BESIDE_LATE, "mode": mode, "order": order},
    )
    answer = json_object(payload, "data", "annotationRead")
    assert sorted(map(str, json_list(answer, "errors"))) == errors, payload
    assert answer["rows"] == rows, payload
    assert len(recorded) == statements, recorded


class _PackageYearSet(FilterSet):
    occurred_years_among = ListFilter(field_name="occurred_on__year", lookup_expr="in")
    occurred_year_span = RangeFilter(field_name="occurred_on", lookup_expr="year__range")
    occurred_year_after = django_filters.NumberFilter(
        field_name="occurred_on__year",
        lookup_expr="gt",
    )

    class Meta:
        model = models.ScalarSpecimen
        fields = {"occurred_on": ["year__gt"], "label": ["exact"]}


def _raw_answer_schema() -> DjangoSchema:
    """A raw ``QueryDict`` set answering both raw verdicts: the form's errors and the bare ``.qs``."""
    sets: dict[str, type[BaseFilterSet]] = {
        "package": PackageCleanedScalarSet,
        "package-year": _PackageYearSet,
    }

    class RawAnswerSpecimen(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("label",)

    def _bound(parent: str, query: str) -> BaseFilterSet:
        return sets[parent](
            data=QueryDict(query),
            queryset=models.ScalarSpecimen.objects.order_by("label"),
        )

    @strawberry.type
    class Query:
        def _raw_errors(self, parent: str, query: str) -> dict[str, object]:
            return require_instance(_bound(parent, query).errors, ErrorDict).get_json_data()

        raw_errors: dict[str, object] = strawberry.field(resolver=_raw_errors, graphql_type=JSON)

        def _raw_rows(self, parent: str, query: str) -> QuerySet[models.ScalarSpecimen]:
            return _bound(parent, query).qs

        raw_rows: QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_raw_rows,
            graphql_type=list[RawAnswerSpecimen],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})


def _raw_answer(parent: str, query_string: str) -> JSONObject:
    return _post(
        _raw_answer_schema(),
        "query($parent: String!, $query: String!) { "
        "rawErrors(parent: $parent, query: $query) "
        "rawRows(parent: $parent, query: $query) { label } }",
        {"parent": parent, "query": query_string},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "parent",
        "query_string",
        "errors",
        "labels",
    ),
    [
        pytest.param(
            "package-year",
            "occurred_on__year__gt=99999",
            {"occurred_on__year__gt": _UNBINDABLE},
            ["kept", "other"],
            id="generated-year-past-9999",
        ),
        pytest.param(
            "package-year",
            "occurred_year_after=99999",
            {"occurred_year_after": _UNBINDABLE},
            ["kept", "other"],
            id="declared-year-past-9999",
        ),
        pytest.param(
            "package-year",
            "occurred_years_among=2026,99999",
            {},
            ["kept", "other"],
            id="declared-year-list-member-past-9999-compares-as-an-integer",
        ),
        pytest.param(
            "package-year",
            "occurred_year_span_0=2000&occurred_year_span_1=99999",
            {},
            ["kept", "other"],
            id="declared-year-range-bound-past-9999-compares-as-an-integer",
        ),
        pytest.param(
            "package-year",
            "occurred_on__year__gt=99999&label=kept",
            {"occurred_on__year__gt": _UNBINDABLE},
            ["kept"],
            id="the-bare-qs-applies-the-leaves-that-cleaned",
        ),
        pytest.param(
            "package-year",
            "occurred_on__year__gt=2000&label=kept",
            {},
            ["kept"],
            id="year-in-range",
        ),
        pytest.param(
            "package",
            "label=\ud800",
            {"label": _SURROGATE},
            ["kept", "other"],
            id="lone-surrogate",
        ),
        pytest.param(
            "package-year",
            "occurred_on__year__gt=2%00",
            {"occurred_on__year__gt": _NULL_CHARACTER},
            ["kept", "other"],
            id="nul-on-a-number",
        ),
        pytest.param(
            "package",
            "label=\ud800&signed_big_span_0=NaN",
            {"label": _SURROGATE},
            ["kept", "other"],
            id="refused-text-skips-cleaning",
        ),
    ],
)
def test_a_raw_form_refuses_what_its_typed_input_refuses(
    parent: str,
    query_string: str,
    errors: JSONObject,
    labels: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Raw form data runs the bind ask the typed input runs, as the form's own errors.

    ``errors`` answers the GraphQL input's ``FILTER_INVALID`` payload for the same value:
    a year no database binds, and text the package refuses (a refused text skips cleaning, so
    only its refusals are reported). django-filter's bare ``.qs`` applies the leaves that
    cleaned, as it does for any invalid form: none once text is refused.
    """
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)
    recorded = record_compiled_sql("scalars_scalarspecimen")
    result = _raw_answer(parent, query_string)
    assert result == {
        "data": {"rawErrors": errors, "rawRows": [{"label": label} for label in labels]},
    }, result
    assert len(recorded) == 1, recorded


@pytest.mark.django_db
def test_reused_generated_meta_forms_keep_one_current_owner_around_consumer_clean() -> None:
    """A generated form may be reused twice; the final set owns the entire clean."""
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)

    class SourceSet(FilterSet):
        after = django_filters.NumberFilter(field_name="signed_big", lookup_expr="gt")

        class Meta:
            model = models.ScalarSpecimen
            fields = []

    source_form = type(SourceSet(queryset=models.ScalarSpecimen.objects.all()).form)

    class MiddleSet(SourceSet):
        class Meta(SourceSet.Meta):
            form: type[forms.Form] = source_form

    middle_form = type(MiddleSet(queryset=models.ScalarSpecimen.objects.all()).form)
    calls: list[str] = []

    def consumer_full_clean(self: forms.Form) -> None:
        calls.append("before")
        middle_form.full_clean(self)
        if self.cleaned_data.get("after") == Decimal(99999):
            self.cleaned_data["after"] = Decimal(2000)
        calls.append("after")

    def consumer_clean(self: forms.Form) -> dict[str, object]:
        calls.append("clean")
        return middle_form.clean(self) or {}

    consumer_form = type(
        "ConsumerForm",
        (middle_form,),
        {"full_clean": consumer_full_clean, "clean": consumer_clean},
    )

    class CurrentSet(MiddleSet):
        after = django_filters.NumberFilter(field_name="occurred_on__year", lookup_expr="gt")

        class Meta(MiddleSet.Meta):
            form: type[forms.Form] = consumer_form

    class RawRow(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("label",)

    def bound(query: str) -> CurrentSet:
        return CurrentSet(
            data=QueryDict(query),
            queryset=models.ScalarSpecimen.objects.order_by("label"),
        )

    @strawberry.type
    class Query:
        def _raw_errors(self, query: str) -> dict[str, object]:
            return require_instance(bound(query).errors, ErrorDict).get_json_data()

        raw_errors: dict[str, object] = strawberry.field(resolver=_raw_errors, graphql_type=JSON)

        def _raw_rows(self, query: str) -> QuerySet[models.ScalarSpecimen]:
            return bound(query).qs

        raw_rows: QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_raw_rows,
            graphql_type=list[RawRow],
        )

        def _typed_rows(
            self,
            info: strawberry.Info[object, object],
            where: JSON,
        ) -> QuerySet[models.ScalarSpecimen]:
            return CurrentSet.apply_sync(
                json_object(where),
                models.ScalarSpecimen.objects.order_by("label"),
                info,
            )

        typed_rows: QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_typed_rows,
            graphql_type=list[RawRow],
        )

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})
    assert _post(
        schema,
        "query($query: String!) { rawErrors(query: $query) }",
        {"query": "after=99999"},
    ) == {"data": {"rawErrors": {}}}
    assert calls == ["before", "clean", "after"]
    calls.clear()
    assert _post(
        schema,
        "query($query: String!) { rawErrors(query: $query) }",
        {"query": "after=88888"},
    ) == {"data": {"rawErrors": {"after": _UNBINDABLE}}}
    assert calls == ["before", "clean", "after"]
    calls.clear()
    assert _post(
        schema,
        "query($query: String!) { rawErrors(query: $query) }",
        {"query": "after=\ud800"},
    ) == {"data": {"rawErrors": {"after": _SURROGATE}}}
    assert calls == []
    assert _post(
        schema,
        "query($where: JSON!) { typedRows(where: $where) { label } }",
        {"where": {"after": {"gt": 99999}}},
    ) == {"data": {"typedRows": [{"label": "kept"}, {"label": "other"}]}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("where", "errors", "labels"),
    [
        pytest.param({"names": ["kept", "\ud800"]}, {"names": _SURROGATE}, ["kept", "other"]),
        pytest.param({"names": ["kept", ["\ud800"]]}, {"names": _SURROGATE}, ["kept", "other"]),
        pytest.param(
            {"names": ["kept", "bad\x00text"]},
            {"names": _NULL_CHARACTER},
            ["kept", "other"],
        ),
        pytest.param({"names": ["kept", "other"]}, {}, ["kept", "other"]),
        pytest.param({"names": ["kept"]}, {}, ["kept"]),
        pytest.param({"names": []}, {}, []),
        pytest.param({"names": None}, {}, ["kept", "other"]),
        pytest.param({}, {}, ["kept", "other"]),
    ],
)
def test_raw_tuple_membership_text_is_refused_before_element_clean(
    where: JSONObject,
    errors: JSONObject,
    labels: list[str],
) -> None:
    cleaned_specimen("kept", kept=True)
    cleaned_specimen("other", kept=False)

    class NameSet(FilterSet):
        names = ListFilter(field_name="label", lookup_expr="in")

        class Meta:
            model = models.ScalarSpecimen
            fields = []

    class RawRow(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("label",)

    def bound(raw: Mapping[str, object]) -> NameSet:
        data: dict[str, object] = {}
        if "names" in raw:
            value = raw["names"]
            data["names"] = None if value is None else tuple(require(value, is_list_or_tuple))
        return NameSet(
            data=data,
            queryset=models.ScalarSpecimen.objects.order_by("label"),
        )

    @strawberry.type
    class Query:
        def _errors(self, where: JSON) -> dict[str, object]:
            return require_instance(bound(json_object(where)).errors, ErrorDict).get_json_data()

        errors: dict[str, object] = strawberry.field(resolver=_errors, graphql_type=JSON)

        def _rows(self, where: JSON) -> QuerySet[models.ScalarSpecimen]:
            return bound(json_object(where)).qs

        rows: QuerySet[models.ScalarSpecimen] = strawberry.field(
            resolver=_rows,
            graphql_type=list[RawRow],
        )

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})
    payload = _post(
        schema,
        "query($where: JSON!) { errors(where: $where) rows(where: $where) { label } }",
        {"where": where},
    )
    assert payload == {
        "data": {"errors": errors, "rows": [{"label": label} for label in labels]},
    }, payload


class _RawElapsedProbe(Model):
    """A duration column on a consumer model; the temporary real table exists only for its rows."""

    elapsed: DurationField[object, datetime.timedelta] = DurationField()

    class Meta:
        managed = False
        app_label = "library"

    @override
    def __str__(self) -> str:
        return str(self.elapsed)


class _DurationsInFilter(django_filters.BaseInFilter, django_filters.DurationFilter):
    """A consumer CSV filter whose form cleans each member as a duration, as django-filter documents."""


class _RawElapsedSet(FilterSet):
    elapsed_among = ListFilter(field_name="elapsed", lookup_expr="in")
    elapsed_excluded = ListFilter(field_name="elapsed", lookup_expr="in", exclude=True)
    elapsed_array_among = ArrayFilter(field_name="elapsed", lookup_expr="in")
    elapsed_span = RangeFilter(field_name="elapsed", lookup_expr="range")
    elapsed_after = django_filters.DurationFilter(field_name="elapsed", lookup_expr="gt")
    elapsed_csv_among = _DurationsInFilter(field_name="elapsed", lookup_expr="in")

    class Meta:
        model = _RawElapsedProbe
        fields = {
            "elapsed": [
                "exact",
                "gt",
                "gte",
                "lt",
                "lte",
                "in",
                "range",
            ],
        }


@pytest.fixture
def raw_elapsed_table(transactional_db: None) -> Generator[None]:
    """Create the duration consumer's table without changing a shipped model."""
    _ = transactional_db
    with connection.schema_editor() as editor:
        editor.create_model(_RawElapsedProbe)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(_RawElapsedProbe)


def _raw_elapsed_schema() -> DjangoSchema:
    class RawElapsedRow(DjangoType):
        class Meta:
            model = _RawElapsedProbe
            fields = ("id",)

    def _bound(query: str) -> _RawElapsedSet:
        return _RawElapsedSet(
            data=QueryDict(query),
            queryset=_RawElapsedProbe.objects.order_by("pk"),
        )

    @strawberry.type
    class Query:
        def _raw_errors(self, query: str) -> dict[str, object]:
            return require_instance(_bound(query).errors, ErrorDict).get_json_data()

        raw_errors: dict[str, object] = strawberry.field(resolver=_raw_errors, graphql_type=JSON)

        def _raw_rows(self, query: str) -> QuerySet[_RawElapsedProbe]:
            return _bound(query).qs

        raw_rows: QuerySet[_RawElapsedProbe] = strawberry.field(
            resolver=_raw_rows,
            graphql_type=list[RawElapsedRow],
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config(), error_policy={"enabled": False})


_PAST_MICROSECONDS = "999999999 00:00:00"
_BELOW_MICROSECONDS = "-999999999 00:00:00"
_ONE_DAY = "1 00:00:00"


class _RawDurationCase(NamedTuple):
    """One raw duration request: the key the bind ask refuses, the rows each backend answers.

    ``refused`` is ``None`` for a request no backend refuses. ``bare_rows`` is what the bare
    ``.qs`` lists where the value is refused (the leaves that cleaned), ``native_rows`` what
    the request selects on a backend binding a native interval, which takes every timedelta.
    """

    query: str
    refused: str | None
    bare_rows: tuple[str, ...]
    native_rows: tuple[str, ...]


_BOTH = ("one-day", "two-days")
_RAW_DURATION_CASES = {
    "exact": _RawDurationCase(f"elapsed={_PAST_MICROSECONDS}", "elapsed", _BOTH, ()),
    "gt": _RawDurationCase(f"elapsed__gt={_BELOW_MICROSECONDS}", "elapsed__gt", _BOTH, _BOTH),
    "gte": _RawDurationCase(f"elapsed__gte={_BELOW_MICROSECONDS}", "elapsed__gte", _BOTH, _BOTH),
    "lt": _RawDurationCase(f"elapsed__lt={_PAST_MICROSECONDS}", "elapsed__lt", _BOTH, _BOTH),
    "lte": _RawDurationCase(f"elapsed__lte={_PAST_MICROSECONDS}", "elapsed__lte", _BOTH, _BOTH),
    "generated-in-mixed": _RawDurationCase(
        f"elapsed__in={_ONE_DAY},{_PAST_MICROSECONDS}",
        "elapsed__in",
        _BOTH,
        ("one-day",),
    ),
    "generated-in-every-member": _RawDurationCase(
        f"elapsed__in={_PAST_MICROSECONDS}",
        "elapsed__in",
        _BOTH,
        (),
    ),
    "generated-range": _RawDurationCase(
        f"elapsed__range={_ONE_DAY},{_PAST_MICROSECONDS}",
        "elapsed__range",
        _BOTH,
        _BOTH,
    ),
    "declared-list-mixed": _RawDurationCase(
        f"elapsed_among={_ONE_DAY},{_PAST_MICROSECONDS}",
        "elapsed_among",
        _BOTH,
        ("one-day",),
    ),
    "declared-list-exclude": _RawDurationCase(
        f"elapsed_excluded={_ONE_DAY},{_PAST_MICROSECONDS}",
        "elapsed_excluded",
        _BOTH,
        ("two-days",),
    ),
    "declared-array": _RawDurationCase(
        f"elapsed_array_among={_ONE_DAY},{_PAST_MICROSECONDS}",
        "elapsed_array_among",
        _BOTH,
        ("one-day",),
    ),
    "declared-range-bound": _RawDurationCase(
        f"elapsed_span_0={_BELOW_MICROSECONDS}&elapsed_span_1={_ONE_DAY}",
        "elapsed_span",
        _BOTH,
        ("one-day",),
    ),
    "declared-comparison": _RawDurationCase(
        f"elapsed_after={_BELOW_MICROSECONDS}",
        "elapsed_after",
        _BOTH,
        _BOTH,
    ),
    "django-filter-csv": _RawDurationCase(
        f"elapsed_csv_among={_ONE_DAY},{_PAST_MICROSECONDS}",
        "elapsed_csv_among",
        _BOTH,
        ("one-day",),
    ),
    "the-bare-qs-applies-the-leaves-that-cleaned": _RawDurationCase(
        f"elapsed_among={_PAST_MICROSECONDS}&elapsed={_ONE_DAY}",
        "elapsed_among",
        ("one-day",),
        (),
    ),
    "in-range": _RawDurationCase(f"elapsed_among={_ONE_DAY}", None, (), ("one-day",)),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("raw_elapsed_table")
@pytest.mark.parametrize("case", _RAW_DURATION_CASES)
def test_a_raw_duration_past_the_backends_range_is_refused_by_the_form(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A duration whose microsecond count lies past 64 bits is the raw form's refusal.

    On SQLite and MySQL, which bind a duration as its microsecond count, every lookup and
    every member or bound of every generated, declared and django-filter duration filter is
    refused with the message the typed input answers, include and exclude alike; the bare
    ``.qs`` applies the leaves that cleaned. A native interval takes the value.
    """
    rows = {
        label: _RawElapsedProbe.objects.create(elapsed=datetime.timedelta(days=days))
        for label, days in (("one-day", 1), ("two-days", 2))
    }
    selected = _RAW_DURATION_CASES[case]
    refused = selected.refused is not None and not connection.features.has_native_duration_field
    errors = {selected.refused: _UNBINDABLE} if refused and selected.refused else {}
    labels = selected.bare_rows if refused else selected.native_rows
    recorded = record_compiled_sql(_RawElapsedProbe._meta.db_table)
    result = _post(
        _raw_elapsed_schema(),
        "query($query: String!) { rawErrors(query: $query) rawRows(query: $query) { id } }",
        {"query": selected.query},
    )
    assert result == {
        "data": {
            "rawErrors": errors,
            "rawRows": [{"id": saved_pk(rows[label])} for label in labels],
        },
    }, result
    assert len(recorded) == 1, recorded


def _actor_is_staff(info: Info) -> bool:
    user = read_attr(read_attr(read_attr(info, "context"), "request"), "user")
    return read_attr(user, "is_staff") is True


def _register_hiding_types() -> None:
    """Serve Shelf and Branch through types hiding a secret shelf and a restricted branch.

    Each walked key's hop reads its target type's ``get_queryset`` as the request's actor:
    the anonymous viewer never matches through a ``topic="secret"`` shelf or a
    ``city="restricted"`` branch, staff do.
    """

    class HidingShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code", "topic")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Shelf],
            info: Info,
        ) -> QuerySet[library_models.Shelf]:
            return queryset if _actor_is_staff(info) else queryset.exclude(topic="secret")

    class HidingBranchType(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name", "city")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[library_models.Branch],
            info: Info,
        ) -> QuerySet[library_models.Branch]:
            return queryset if _actor_is_staff(info) else queryset.exclude(city="restricted")

    del HidingShelfType, HidingBranchType
    finalize_django_types()


def _shelved_world() -> dict[str, int]:
    """An open shelf's book, a secret shelf's book and a restricted branch's book, by title."""
    home = library_models.Branch.objects.create(name="Home", city="Boston")
    vault = library_models.Branch.objects.create(name="Vault", city="restricted")
    shelves = {
        "b-open": library_models.Shelf.objects.create(code="S-open", topic="general", branch=home),
        "b-secret": library_models.Shelf.objects.create(
            code="S-secret",
            topic="secret",
            branch=home,
        ),
        "b-vault": library_models.Shelf.objects.create(
            code="S-vault",
            topic="general",
            branch=vault,
        ),
    }
    return {
        title: saved_pk(library_models.Book.objects.create(title=title, shelf=shelf))
        for title, shelf in shelves.items()
    }


def _raw_set_client(viewer: str) -> Client:
    client = Client()
    if viewer == "staff":
        client.force_login(get_user_model().objects.get(username="staff_1"))
    return client


def _raw_set_answer(
    client: Client,
    driver: str,
    name: str,
    query: dict[str, str],
) -> tuple[int, object]:
    """The status code and JSON body one driver route answers for ``query``."""
    data = QueryDict(mutable=True)
    data.update(query)
    with override_settings(ROOT_URLCONF=__name__):
        response = client.get(f"/raw-sets/{driver}/{name}/?{data.urlencode()}")
    return response.status_code, json_loads(response.content)


def _raw_set_ids(
    client: Client,
    driver: str,
    name: str,
    query: dict[str, str],
) -> list[int]:
    status, body = _raw_set_answer(client, driver, name, query)
    assert status == 200, body
    rows = json_list(body)
    return [json_int(row, "id") if driver == "backend" else json_int(row) for row in rows]


#: (walked key and value, the titles each viewer's request answers)
_WALKED_KEYS: dict[str, tuple[dict[str, str], list[str], list[str]]] = {
    "walked-column-on-a-hidden-shelf": ({"shelf__topic": "secret"}, [], ["b-secret"]),
    "two-hop-column-past-a-hidden-shelf": (
        {"shelf__branch__city": "Boston"},
        ["b-open"],
        ["b-open", "b-secret"],
    ),
    "two-hop-column-on-a-hidden-branch": ({"shelf__branch__name": "Vault"}, [], ["b-vault"]),
}

_RAW_DRIVERS = ["direct", "backend", "filter-view"]


@pytest.mark.django_db
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("key", sorted(_WALKED_KEYS))
@pytest.mark.parametrize("name", ["plain-subclass", "unserved"])
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
def test_a_raw_set_no_type_names_answers_a_walked_key_as_book_filter(
    driver: str,
    name: str,
    key: str,
    viewer: str,
) -> None:
    """A set no type names, built raw, answers a walked key with ``BookFilter``'s rows.

    ``BookFilter`` is built raw in the same request (no type names it in this registry).

    Its first construction publishes its filter table, so the flat copies its
    ``RelatedFilter`` declarations expand to are fields of its form and each walks its hop
    as the request's actor sees it, under a consumer's own construction, DRF's
    ``DjangoFilterBackend`` and django-filter's ``FilterView`` alike: never the view's
    unfiltered rows.
    """
    create_users(1)
    _register_hiding_types()
    books = _shelved_world()
    client = _raw_set_client(viewer)
    query, anonymous, staff = _WALKED_KEYS[key]
    expected = [books[title] for title in (staff if viewer == "staff" else anonymous)]

    assert _raw_set_ids(client, driver, name, query) == expected
    assert _raw_set_ids(client, driver, "book-filter", query) == expected


def _register_doubling_type() -> None:
    """Register the specimen type whose ``get_queryset`` doubles ``signed_big`` as ``twice``."""

    class DoublingSpecimenType(DjangoType):
        class Meta:
            model = models.ScalarSpecimen
            fields = ("id", "label")
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.ScalarSpecimen],
            info: object,
            **kwargs: object,
        ) -> QuerySet[models.ScalarSpecimen]:
            del info, kwargs
            return queryset.annotate(twice=F("signed_big") * 2)

    del DoublingSpecimenType
    finalize_django_types()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "labels"),
    [
        pytest.param({"twice_among": "14,21"}, ["kept-child"], id="members"),
        pytest.param({"twice_among": f"14,{2**63}"}, ["kept-child"], id="member-past-range"),
        pytest.param(
            {"twice_below": str(2**63)},
            ["kept-child", "gone-child"],
            id="bound-past-range",
        ),
    ],
)
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
def test_a_raw_name_past_a_self_relation_reads_the_parent_types_annotation(
    driver: str,
    query: dict[str, str],
    labels: list[str],
) -> None:
    """``parent__twice`` reads the parent type's ``twice``, never the rows' own ``twice``.

    The set's ``filter_queryset`` annotates ``twice`` (triple ``signed_big``) on the rows it
    filters, and the specimen type's ``get_queryset`` annotates it double: past the
    ``parent`` hop the name is the parent's, so ``14`` matches the kept parent's child and a
    number past any integer is held past the column's range, under a consumer's own
    construction, DRF's ``DjangoFilterBackend`` and django-filter's ``FilterView`` alike.
    """
    kept = cleaned_specimen("kept", kept=True)
    gone = cleaned_specimen("gone", kept=False)
    for label, parent in (("kept-child", kept), ("gone-child", gone)):
        child = cleaned_specimen(label, kept=True)
        child.parent = parent
        child.save(update_fields=["parent"])
    _register_doubling_type()
    expected = [saved_pk(models.ScalarSpecimen.objects.get(label=label)) for label in labels]
    assert _raw_set_ids(Client(), driver, "late-parent-twice", query) == expected


#: (raw key over the alias and value, the titles each viewer's request answers)
_ALIASED_KEYS: dict[str, tuple[dict[str, str], list[str], list[str]]] = {
    "alias-column-on-a-hidden-shelf": ({"shelf_code": "S-secret"}, [], ["b-secret"]),
    "past-the-alias-on-a-hidden-branch": ({"shelf_branch": "Vault"}, [], ["b-vault"]),
    "past-the-alias-through-a-hidden-shelf": (
        {"shelf_branch": "Home"},
        ["b-open"],
        ["b-open", "b-secret"],
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("key", sorted(_ALIASED_KEYS))
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
def test_a_raw_key_over_a_filtered_relation_alias_reads_the_shelfs_visibility(
    driver: str,
    key: str,
    viewer: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A raw key starting at an alias the set's ``filter_queryset`` adds walks the alias as a hop.

    ``vshelf`` joins ``Book.shelf``: under a consumer's own construction, DRF's
    ``DjangoFilterBackend`` and django-filter's ``FilterView``, the anonymous viewer never
    matches a book through the secret shelf or the restricted branch past it, and staff read
    every row, in one statement.
    """
    create_users(1)
    _register_hiding_types()
    books = _shelved_world()
    client = _raw_set_client(viewer)
    query, anonymous, staff = _ALIASED_KEYS[key]
    recorded = record_compiled_sql(library_models.Book._meta.db_table)

    assert _raw_set_ids(client, driver, "aliased-shelf", query) == [
        books[title] for title in (staff if viewer == "staff" else anonymous)
    ]
    assert len(recorded) == 1, recorded


#: (raw key, the refusal ``DjangoFilterBackend`` answers with its 400, else ``None``, and the
#: specimens every driver answers: the bare ``.qs`` of a consumer's own construction applies
#: no refused leaf, and django-filter's strict ``FilterView`` answers no row for a refused form)
_LATE_ANNOTATION_KEYS: dict[str, tuple[dict[str, str], JSONObject | None, list[str]]] = {
    "junk-bound": (
        {"kids_span_0": "abc"},
        {"kids_span": ["Enter a number."]},
        ["parent", "child"],
    ),
    "junk-member": (
        {"kids_among": "1,abc"},
        {"kids_among": ["Enter a number."]},
        ["parent", "child"],
    ),
    "bound": ({"kids_span_0": "1"}, None, ["parent"]),
    "member": ({"kids_among": "0"}, None, ["child"]),
}


@pytest.mark.django_db
@pytest.mark.parametrize("key", sorted(_LATE_ANNOTATION_KEYS))
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
def test_a_raw_value_over_an_annotation_filter_queryset_adds_is_cleaned_by_every_driver(
    driver: str,
    key: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A value over an annotation the set's own ``filter_queryset`` adds is cleaned per driver.

    The set is handed its model's unannotated rows (``_late_annotated_set``); each junk bound
    or member is cleaned over the queryset the override passes on and refused as the form's
    error: DRF's ``DjangoFilterBackend`` answers its 400 body and django-filter's strict
    ``FilterView`` no row, without a statement, while a consumer's bare ``.qs`` applies the
    leaves that cleaned in one; never Django's ``ValueError``.
    """
    family = {"parent": cleaned_specimen("parent", kept=True)}
    family["child"] = cleaned_specimen("child", kept=True)
    family["child"].parent = family["parent"]
    family["child"].save(update_fields=["parent"])
    query, refusal, labels = _LATE_ANNOTATION_KEYS[key]
    statements = record_compiled_sql(models.ScalarSpecimen._meta.db_table)

    status, body = _raw_set_answer(Client(), driver, "late-annotation", query)

    rows = [saved_pk(family[label]) for label in labels]
    if refusal is not None and driver == "backend":
        assert (status, body) == (400, refusal)
    elif refusal is not None and driver == "filter-view":
        assert (status, body) == (200, [])
    else:
        assert status == 200, body
        ids = [
            json_int(row, "id") if driver == "backend" else json_int(row)
            for row in json_list(body)
        ]
        assert ids == rows
    assert len(statements) == (0 if refusal is not None and driver != "direct" else 1), statements


#: (the set, the refusal its first construction raises)
_REFUSED_SETS = {
    "range-over-a-relation": (
        "FilterSet _RangeOverRelationSet: RangeFilter 'branch_span' has field_name 'branch' and "
        "lookup_expr 'range', but Django resolves no transform or lookup 'range' on "
        "Shelf.branch (ForeignKey), so every request naming the filter would be refused."
    ),
    "global-id-over-a-generic-key": (
        "FilterSet _GlobalIDOverGenericSet: GlobalIDFilter 'content_object' has field_name "
        "'content_object', which names TaggedItem.content_object, a GenericForeignKey: Django "
        "filters no queryset through it, so no related row's identity can be compared on it."
    ),
    "model-choice-over-a-generic-key": (
        "FilterSet _ModelChoiceOverGenericSet: ModelChoiceFilter 'content_object' has "
        "field_name 'content_object', which names TaggedItem.content_object, a "
        "GenericForeignKey: Django filters no queryset through it, so no related row's "
        "identity can be compared on it."
    ),
    "model-multiple-choice-past-a-key-onto-a-generic-key": (
        "FilterSet _ModelMultipleChoicePastKeySet: ModelMultipleChoiceFilter 'desk_object' has "
        "field_name 'desk__content_object', which names CirculationDesk.content_object, a "
        "GenericForeignKey: Django filters no queryset through it, so no related row's "
        "identity can be compared on it."
    ),
    "char-over-a-generic-key": (
        "_CharOverGenericSet: CharFilter on 'content_object' reads TaggedItem.content_object, a "
        "GenericForeignKey: Django filters no queryset through it, so no input can carry its "
        "value"
    ),
    "null-test-over-a-generic-key": (
        "_NullTestOverGenericSet: BooleanFilter on 'content_object' reads "
        "CirculationDesk.content_object, a GenericForeignKey: Django filters no queryset "
        "through it, so no input can carry its value"
    ),
    "range-past-a-key-onto-a-generic-key": (
        "_RangePastKeyOntoGenericSet: RangeFilter on 'desk__content_object' reads "
        "CirculationDesk.content_object, a GenericForeignKey: Django filters no queryset "
        "through it, so no input can carry its value"
    ),
    "choice-past-a-key-onto-a-generic-key": (
        "_ChoicePastKeyOntoGenericSet: ChoiceFilter on 'desk__content_object' reads "
        "CirculationDesk.content_object, a GenericForeignKey: Django filters no queryset "
        "through it, so no input can carry its value"
    ),
    "model-choice-with-no-queryset": (
        "FilterSet _QuerysetlessChoiceSet: ModelChoiceFilter 'branch_is' has field_name 'branch' "
        "and no queryset, so the model-choice form field it builds has no rows to look a value "
        "up in, and every request building the set's form would fail. Pass queryset= (a model "
        "queryset, or a callable taking the request), override the filter's "
        "get_queryset(request), or give a Meta.filter_overrides entry an `extra` returning "
        '{"queryset": ...}.'
    ),
    "filter-override-with-no-queryset": (
        "FilterSet _QuerysetlessOverrideSet: ModelChoiceFilter 'branch' has field_name 'branch' "
        "and no queryset, so the model-choice form field it builds has no rows to look a value "
        "up in, and every request building the set's form would fail. Pass queryset= (a model "
        "queryset, or a callable taking the request), override the filter's "
        "get_queryset(request), or give a Meta.filter_overrides entry an `extra` returning "
        '{"queryset": ...}.'
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("name", sorted(_REFUSED_SETS))
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
def test_a_raw_set_declaring_a_refused_filter_is_refused_at_its_first_construction(
    driver: str,
    name: str,
) -> None:
    """A set no type names is refused at its first construction, its first use, by every driver.

    Its publication refuses the declaration Django can answer no request for, so the
    request building it raises ``ConfigurationError`` naming the set and the filter whatever
    data it sends, and every later request does too until the declaration is fixed.
    """
    create_users(1)
    client = _raw_set_client("anonymous")
    for _ in range(2):
        with pytest.raises(ConfigurationError) as refused:
            _ = _raw_set_ids(client, driver, name, {})
        assert str(refused.value).startswith(_REFUSED_SETS[name])
    assert _RAW_SETS[name]._expansion_snapshot() is None


@pytest.mark.django_db
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
def test_a_raw_set_filtering_the_columns_beside_a_generic_key_answers_their_rows(
    driver: str,
) -> None:
    """The content type key a ``GenericForeignKey`` reads and its ``GenericRelation`` filter rows.

    Only a leaf ending on the ``GenericForeignKey`` itself is refused when its set
    publishes: a column-typed filter on the content type key, and one on the
    ``GenericRelation`` reversing the relation on the tagged model, are joined as any
    relation is and answer their rows on every driver.
    """
    create_users(1)
    branch = library_models.Branch.objects.create(name="tagged-branch")
    other = library_models.Branch.objects.create(name="untagged-branch")
    desk = library_models.CirculationDesk.objects.create(
        name="tagged-desk",
        branch=branch,
        shelf=library_models.Shelf.objects.create(code="s-tagged", branch=branch),
    )
    branch_type = ContentType.objects.get_for_model(library_models.Branch)
    desk_type = ContentType.objects.get_for_model(library_models.CirculationDesk)
    on_branch = library_models.TaggedItem.objects.create(
        tag="b",
        content_type=branch_type,
        object_id=saved_pk(branch),
    )
    on_desk = library_models.TaggedItem.objects.create(
        tag="d",
        content_type=desk_type,
        object_id=saved_pk(desk),
    )
    client = _raw_set_client("anonymous")

    by_kind = {"kind": str(saved_pk(branch_type))}
    assert _raw_set_ids(client, driver, "content-type-column", by_kind) == [saved_pk(on_branch)]
    by_desk_kind = {"kind": str(saved_pk(desk_type))}
    assert _raw_set_ids(client, driver, "content-type-column", by_desk_kind) == [
        saved_pk(on_desk),
    ]
    by_tag = {"tagged": str(saved_pk(on_branch))}
    assert _raw_set_ids(client, driver, "generic-relation", by_tag) == [saved_pk(branch)]
    assert _raw_set_ids(client, driver, "generic-relation", {}) == [
        saved_pk(branch),
        saved_pk(other),
    ]


#: (raw key and value, the titles each viewer's request answers, by set)
_FLAT_OFF_KEYS: dict[str, tuple[dict[str, str], dict[str, tuple[list[str], list[str]]]]] = {
    "withdrawn-copy-is-ignored": (
        {"shelf__branch__city": "Boston"},
        {
            "unserved": (["b-open"], ["b-open", "b-secret"]),
            "unserved-flat-off": (
                ["b-open", "b-secret", "b-vault"],
                ["b-open", "b-secret", "b-vault"],
            ),
        },
    ),
    "restored-own-key-keeps-its-lookup-and-hop": (
        {"shelf__topic": "SECRET"},
        {"unserved": ([], []), "unserved-flat-off": ([], ["b-secret"])},
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("viewer", ["anonymous", "staff"])
@pytest.mark.parametrize("key", sorted(_FLAT_OFF_KEYS))
@pytest.mark.parametrize("name", ["unserved", "unserved-flat-off"])
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
def test_a_raw_set_ignores_a_flat_false_copy_and_restores_its_own_key(
    driver: str,
    name: str,
    key: str,
    viewer: str,
) -> None:
    """On a set no type names, a ``flat=False`` declaration's generated key is ignored.

    django-filter ignores a key no filter registers, so the view's rows return; the
    set's own ``iexact`` key an enabled copy would replace holds it again and walks
    ``shelf`` as the actor sees it. The enabled twin answers both keys through its
    copies. Every driver alike.
    """
    create_users(1)
    _register_hiding_types()
    books = _shelved_world()
    client = _raw_set_client(viewer)
    query, by_set = _FLAT_OFF_KEYS[key]
    anonymous, staff = by_set[name]
    expected = [books[title] for title in (staff if viewer == "staff" else anonymous)]

    assert _raw_set_ids(client, driver, name, query) == expected


def _reading_lists() -> dict[str, int]:
    """Classics holds Beloved and Middlemarch; Anthology holds Kindred. Pks by title."""
    classics = library_models.ReadingList.objects.create(title="Classics")
    anthology = library_models.ReadingList.objects.create(title="Anthology")
    rows: dict[str, int] = {"Classics": saved_pk(classics), "Anthology": saved_pk(anthology)}
    for title, reading_list in (
        ("Beloved", classics),
        ("Middlemarch", classics),
        ("Kindred", anthology),
    ):
        entry = library_models.ReadingListEntry.objects.create(
            reading_list=reading_list,
            title=title,
        )
        rows[title] = saved_pk(entry)
    return rows


@pytest.mark.django_db
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
@pytest.mark.parametrize(
    (
        "name",
        "key",
        "value",
        "titles",
    ),
    [
        pytest.param(
            "reading-list-entry-filter",
            "reading_list__id",
            "Anthology",
            ["Beloved", "Middlemarch", "Kindred"],
            id="disabled-copy-key-ignored",
        ),
        pytest.param(
            "reading-list-entry-filter",
            "reading_list",
            "Anthology",
            ["Kindred"],
            id="disabled-declarations-own-head",
        ),
        pytest.param(
            "reading-list-filter",
            "entries__reading_list",
            "Classics",
            ["Classics"],
            id="enabled-copied-terminal-head",
        ),
        pytest.param(
            "reading-list-filter",
            "entries__title",
            "Kindred",
            ["Anthology"],
            id="enabled-copy",
        ),
    ],
)
def test_the_shipped_reading_list_cycle_answers_raw_form_keys(
    driver: str,
    name: str,
    key: str,
    value: str,
    titles: list[str],
) -> None:
    """A raw key only the disabled copy registers is ignored; the head and enabled copies filter.

    Every row is one every viewer sees.
    """
    create_users(1)
    for model in (library_models.ReadingList, library_models.ReadingListEntry):
        meta = {"model": model, "fields": ("id", "title")}
        type(f"Raw{model.__name__}Type", (DjangoType,), {"Meta": type("Meta", (), meta)})
    finalize_django_types()
    rows = _reading_lists()
    client = _raw_set_client("anonymous")
    sent = str(rows[value]) if key != "entries__title" else value
    assert _raw_set_ids(client, driver, name, {key: sent}) == [rows[title] for title in titles]


@pytest.mark.django_db
@pytest.mark.parametrize("driver", _RAW_DRIVERS)
@pytest.mark.parametrize("name", ["range-own-flat-on", "range-own-flat-off"])
@pytest.mark.parametrize(
    ("query", "names"),
    [
        pytest.param(
            {"issues__number_min": "2", "issues__number_max": "2"},
            ["Second"],
            id="suffixed-keys-bind",
        ),
        pytest.param({"issues__number": "2"}, ["First", "Second", "Empty"], id="bare-key-ignored"),
    ],
)
def test_a_multi_key_range_widget_binds_its_suffixed_keys_whoever_holds_the_key(
    driver: str,
    name: str,
    query: dict[str, str],
    names: list[str],
) -> None:
    """The key ``issues__number`` is a ``RangeWidget`` whether the copy or the own filter holds it.

    Enabled, the child's range copy holds it; ``flat=False``, the parent's own range.
    Either way only ``issues__number_min`` / ``_max`` bind, and a bare
    ``issues__number`` names no widget key, so django-filter ignores it.
    """
    create_users(1)
    for model in (library_models.Periodical, library_models.Issue):
        meta = {"model": model, "fields": ("id",)}
        type(f"Range{model.__name__}Type", (DjangoType,), {"Meta": type("Meta", (), meta)})
    finalize_django_types()
    rows: dict[str, int] = {}
    for title, number in (("First", 1), ("Second", 2), ("Empty", None)):
        periodical = library_models.Periodical.objects.create(name=title)
        rows[title] = saved_pk(periodical)
        if number is not None:
            library_models.Issue.objects.create(periodical=periodical, number=number, title=title)
    client = _raw_set_client("anonymous")
    assert _raw_set_ids(client, driver, name, query) == [rows[title] for title in names]
