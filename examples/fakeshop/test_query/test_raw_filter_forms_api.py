"""Consumer JSON and raw arguments preserve filter forms, widget keys and public primitive calls.

These consumers deliberately keep a django-filter FilterSet as well as the package's set.
Ordinary arguments feed the original public data/queryset/.qs seam, without publishing an
input factory or assigning an owner. QueryDict is built by Django from a real query-string
argument, retaining repeated SelectMultiple keys that a generated filter input cannot spell.
A declared list or lone range bound over a relation itself cleans each raw element as the
target column the relation compares on (its ``to_field``, else the primary key), as
``<relation>__<that column>`` cleans it; a ``method=`` filter on a relation cleans none.
"""

from collections.abc import Callable
from functools import wraps

import django_filters
import pytest
import strawberry
from apps.library import models as library_models
from apps.scalars import models
from django import forms
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import override_settings
from django.urls import path
from django_filters.filterset import BaseFilterSet
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload, json_object
from strawberry.scalars import JSON

from django_strawberry_framework import (
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import (
    ArrayFilter,
    FilterSet,
    ListFilter,
    RangeFilter,
    RelatedFilter,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._cleaned_filter_sets import (
    KEPT_EXTERNAL_ID,
    PackageCleanedScalarSet,
    PlainCleanedScalarSet,
    cleaned_specimen,
)
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-raw-filter-forms/", _graphql_view)]


def _filter_set(parent: str) -> type[BaseFilterSet]:
    return {"package": PackageCleanedScalarSet, "django-filter": PlainCleanedScalarSet}[parent]


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


def _schema() -> DjangoSchema:
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
    return DjangoSchema(query=Query, config=strawberry_config())


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
    """Create one matching and one other row per relation; answer each matching target's key."""
    branch = library_models.Branch.objects.create(name="Raw relations")
    shelf = library_models.Shelf.objects.create(branch=branch, code="A-1")
    other_shelf = library_models.Shelf.objects.create(branch=branch, code="B-1")
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
