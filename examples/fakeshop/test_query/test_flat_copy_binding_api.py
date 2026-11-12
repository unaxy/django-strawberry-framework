"""A walked flat copy filters as a filter of the hop's target set, model included.

A ``RelatedFilter`` child's filter served flat on the parent (``shelfCodeValues`` for
``code_values`` through ``shelf``) runs, when no owner binds it, as a copy bound to the last hop's
target set: its ``parent`` that set, its ``field_name`` the path left on the target and its
``model`` the target's model, as django-filter binds every filter of a set. So a filter that
resolves its ``field_name`` against ``self.model`` while it filters answers its nested twin's rows:
django-filter's ``AllValuesMultipleFilter`` (whose ``field``, re-read by
``MultipleChoiceFilter.filter``, lists the model's column values), a consumer
``MultipleChoiceFilter`` labelling its form field from ``get_model_field(self.model,
self.field_name)``, a consumer ``CharFilter`` re-cleaning its value with that field and one
checking its column on its owner's ``queryset`` (its ``parent``), through a forward key, a reverse
key, a many-to-many, two hops and a relation no ``RelatedFilter`` declares past a declared one, and
a consumer ``ModelMultipleChoiceFilter`` labelling its field from its relation through a forward
relation key folded onto the hop before it and a to-many relation key under a parent keyed by
``isbn_13``, on the sync and async views and through a raw ``FilterSet(data, queryset,
request=...).qs`` a consumer resolver reads. The flat copy's form field, which cleans the value, is
the parent's own copy's; the owner-bound twins (a ``method=``, a child set ``__init__``) answer as
their nested twins do. A set's own leaf whose path walks a relation no ``RelatedFilter`` declares,
scoped by its target type's ``get_queryset``, runs bound to that relation's model the same way.

A declared branch's explicit ``queryset=`` admits the child rows among the rows it holds however
either side reads ``distinct()``: child filters django-filter runs ``distinct()`` for
(``AllValuesMultipleFilter``, a consumer ``MultipleChoiceFilter`` and
``ModelMultipleChoiceFilter``), a callable, ``distinct()`` or combined (``union()``) ``queryset=``
and a target type's ``get_queryset`` returning ``distinct()`` rows, through a forward key, a
reverse key, a many-to-many and a scoped second hop, flat, nested, under ``not``, ``and`` and
``or``, in pinned statement counts, on the sync and async views and through a raw ``FilterSet(data,
queryset, request=...).qs``. One pinned by ``.using()`` to an alias the request does not read is
refused with a ``ConfigurationError`` naming the declaration and both aliases, flat, nested, under
``not``, on the sync and async views and through a raw ``.qs``, before any book row is read.
"""

from collections.abc import Mapping
from functools import wraps
from typing import TypeAlias

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django import forms
from django.db import connection
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase, QueryDict
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import (
    AllValuesMultipleFilter,
    CharFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
)
from django_filters.utils import get_model_field
from graphql_client import (
    JSONObject,
    graphql_payload,
    json_list,
    json_str,
    middleware_without_debug_toolbar,
    response_json,
)
from strawberry import relay
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
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.utils._narrowing import (
    is_queryset,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}

#: The shelf codes ``_LabelledPicks`` offers.
_CODES = (
    ("A-1", "A-1"),
    ("B-2", "B-2"),
    ("C-3", "C-3"),
    ("D-4", "D-4"),
)


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
    path("graphql-flat-binding/", _graphql_view),
    path("graphql-flat-binding-async/", _async_graphql_view),
]


def _column_label(model: type[Model], field_name: str | None) -> str:
    """The verbose name of the column ``field_name`` reaches from ``model``."""
    # django-filter's ``get_model_field`` returns ``None`` for a path that ends at no column.
    label = read_attr(get_model_field(model, str(field_name)), "verbose_name", None)
    if label is None:
        raise LookupError(f"{model.__name__} has no column {field_name!r}")
    return str(label)


class _LabelledPicks(MultipleChoiceFilter):
    """A consumer ``MultipleChoiceFilter`` whose form field is labelled from the column it filters.

    ``field`` resolves ``field_name`` on ``model`` on every read, as django-filter's
    ``AllValuesMultipleFilter`` does; ``MultipleChoiceFilter.filter`` reads it per value.
    """

    # Annotated only: the FilterSet instance binding the filter sets it.
    model: type[Model]

    @property
    @override
    def field(self) -> forms.Field:
        self.extra["help_text"] = _column_label(self.model, self.field_name)
        return super().field


class _RecleanedText(CharFilter):
    """A consumer ``CharFilter`` labelled from its column; ``filter`` re-cleans with ``field``."""

    # Annotated only: the FilterSet instance binding the filter sets it.
    model: type[Model]

    @property
    @override
    def field(self) -> forms.Field:
        self.extra["help_text"] = _column_label(self.model, self.field_name)
        return super().field

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        return super().filter(qs, self.field.clean(value))


class _OwnerColumnText(CharFilter):
    """A consumer ``CharFilter`` whose ``filter`` checks its column on its owner's rows."""

    @override
    def filter(self, qs: QuerySet[Model], value: object) -> QuerySet[Model]:
        owner = require_instance(read_attr(self, "parent"), FilterSet)
        _ = _column_label(require(owner.queryset, is_queryset).model, self.field_name)
        return super().filter(qs, value)


class _LabelledRows(ModelMultipleChoiceFilter):
    """A consumer ``ModelMultipleChoiceFilter`` whose form field is labelled from its relation.

    ``field`` resolves ``field_name`` on ``model`` on every read; ``MultipleChoiceFilter.filter``
    reads it per value.
    """

    # Annotated only: the FilterSet instance binding the filter sets it.
    model: type[Model]

    @property
    @override
    def field(self) -> forms.Field:
        self.extra["help_text"] = _column_label(self.model, self.field_name)
        return super().field


class FlatBindBranchFilter(FilterSet):
    """The branch a shelf stands in: django-filter's ``AllValuesMultipleFilter`` over ``name``."""

    name_values = AllValuesMultipleFilter(field_name="name")

    class Meta:
        model = models.Branch
        fields = ()


class FlatBindGenreFilter(FilterSet):
    """A book's genres: django-filter's ``AllValuesMultipleFilter`` over ``name``."""

    name_values = AllValuesMultipleFilter(field_name="name")

    class Meta:
        model = models.Genre
        fields = ()


class FlatBindShelfFilter(FilterSet):
    """Shelf filters reading their model while they filter, a ``method=`` twin and a branch hop."""

    code_values = AllValuesMultipleFilter(field_name="code")
    code_labelled = _LabelledPicks(field_name="code", choices=_CODES)
    code_recleaned = _RecleanedText(field_name="code")
    code_owner_checked = _OwnerColumnText(field_name="code")
    # A relation key on the declared ``branch`` hop: walked flat, it folds onto the shelf rows.
    branch_labelled = _LabelledRows(
        field_name="branch",
        queryset=models.Branch.objects.all(),
    )
    code_values_method = AllValuesMultipleFilter(field_name="code", method="filter_code_values")
    # ``alt_branches`` is a relation no ``RelatedFilter`` declares; ``FlatBindBranch`` scopes it.
    alt_branch_names = AllValuesMultipleFilter(field_name="alt_branches__name")
    branch = RelatedFilter(FlatBindBranchFilter, field_name="branch")

    class Meta:
        model = models.Shelf
        fields = ()

    def filter_code_values(
        self,
        queryset: QuerySet[models.Shelf],
        name: str,
        value: list[str],
    ) -> QuerySet[models.Shelf]:
        """Keep the shelves whose ``name`` column holds a listed value."""
        return queryset.filter(**{f"{name}__in": value})


class FlatBindInitBookFilter(FilterSet):
    """A book set overriding ``__init__``, so the filter set owns its flat copies."""

    title_values = AllValuesMultipleFilter(field_name="title")

    class Meta:
        model = models.Book
        fields = ()

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


class FlatBindPublisherFilter(FilterSet):
    """A printing's co-publishers, reached as a declared to-many hop."""

    class Meta:
        model = models.Publisher
        fields = ()


class FlatBindPrintingFilter(FilterSet):
    """A printing's to-many relation key ``co_publishers``, over its declared hop."""

    co_publishers_labelled = _LabelledRows(
        field_name="co_publishers",
        queryset=models.Publisher.objects.all(),
    )
    co_publishers = RelatedFilter(FlatBindPublisherFilter, field_name="co_publishers")

    class Meta:
        model = models.Printing
        fields = ()


class FlatBindEditionFilter(FilterSet):
    """Editions, keyed by ``isbn_13``, through the reverse key ``printings``."""

    printings = RelatedFilter(FlatBindPrintingFilter, field_name="printings")

    class Meta:
        model = models.Edition
        fields = ()


class FlatBindBookFilter(FilterSet):
    """Books through a forward key, a many-to-many and, past the shelf, two hops."""

    shelf = RelatedFilter(FlatBindShelfFilter, field_name="shelf")
    genres = RelatedFilter(FlatBindGenreFilter, field_name="genres")

    class Meta:
        model = models.Book
        fields = ()


class FlatBindBranchRootFilter(FilterSet):
    """Branches through the reverse key ``shelves``."""

    shelves = RelatedFilter(FlatBindShelfFilter, field_name="shelves")

    class Meta:
        model = models.Branch
        fields = ()


class FlatBindGenreRootFilter(FilterSet):
    """Genres through the reverse many-to-many ``books`` into a set that owns its flat copies."""

    books = RelatedFilter(FlatBindInitBookFilter, field_name="books")

    class Meta:
        model = models.Genre
        fields = ()


def _raw_titles(query: str, request: HttpRequest) -> list[str]:
    """A consumer's own construction: ``FlatBindBookFilter(data, queryset, request=...).qs``.

    ``data`` is the ``QueryDict`` Django builds from the query string ``query``.
    """
    filterset = FlatBindBookFilter(
        data=QueryDict(query),
        queryset=models.Book.objects.order_by("title"),
        request=request,
    )
    assert filterset.is_valid(), filterset.errors
    matched: QuerySet[Model] = filterset.qs
    return [require_instance(read_attr(book, "title"), str) for book in matched]


def _schema() -> DjangoSchema:
    class FlatBindBook(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            filterset_class = FlatBindBookFilter

    class FlatBindBranch(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = FlatBindBranchRootFilter

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Branch],
            info: strawberry.Info[object, object],
        ) -> QuerySet[models.Branch]:
            return queryset.exclude(city="restricted")

    class FlatBindShelf(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("id", "code")
            interfaces = (relay.Node,)
            filterset_class = FlatBindShelfFilter

    class FlatBindGenre(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = FlatBindGenreRootFilter

    class FlatBindPublisher(DjangoType):
        class Meta:
            model = models.Publisher
            fields = ("id", "name")
            filterset_class = FlatBindPublisherFilter

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Publisher],
            info: strawberry.Info[object, object],
        ) -> QuerySet[models.Publisher]:
            return queryset.exclude(name="restricted")

    class FlatBindPrinting(DjangoType):
        class Meta:
            model = models.Printing
            fields = ("id", "run_size")
            filterset_class = FlatBindPrintingFilter

    class FlatBindEdition(DjangoType):
        class Meta:
            model = models.Edition
            fields = ("isbn_13", "imprint")
            interfaces = (relay.Node,)
            filterset_class = FlatBindEditionFilter

    @strawberry.type
    class Query:
        books: DjangoConnection[FlatBindBook] = DjangoConnectionField(FlatBindBook)
        branches: DjangoConnection[FlatBindBranch] = DjangoConnectionField(FlatBindBranch)
        shelves: DjangoConnection[FlatBindShelf] = DjangoConnectionField(FlatBindShelf)
        genres: DjangoConnection[FlatBindGenre] = DjangoConnectionField(FlatBindGenre)
        editions: DjangoConnection[FlatBindEdition] = DjangoConnectionField(FlatBindEdition)

        @strawberry.field
        def raw_books(self, info: strawberry.Info[object, object], query: str) -> list[str]:
            del self
            return _raw_titles(
                query,
                require_instance(read_attr(info.context, "request"), HttpRequest),
            )

    # Registered for their filter sets' hops; no root field reads them.
    del FlatBindPublisher, FlatBindPrinting
    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_NORTH, _SOUTH, _ORBIT, _TOR = 701, 702, 801, 802


def _world() -> None:
    """Two branches, four shelves (``D-4`` holds no book, ``A-1`` lists ``South``), two books."""
    # Explicit keys: the relation-key rows name a branch and a publisher by key.
    north = models.Branch.objects.create(pk=_NORTH, name="North", city="Boston")
    south = models.Branch.objects.create(pk=_SOUTH, name="South", city="Boston")
    shelves = {
        code: models.Shelf.objects.create(code=code, branch=branch, tier=1)
        for code, branch in (
            ("A-1", north),
            ("B-2", north),
            ("C-3", south),
            ("D-4", south),
        )
    }
    dune = models.Book.objects.create(title="Dune", shelf=shelves["A-1"])
    emma = models.Book.objects.create(title="Emma", shelf=shelves["C-3"])
    models.Genre.objects.create(name="Fiction").books.add(dune)
    models.Genre.objects.create(name="Poetry").books.add(emma)
    shelves["A-1"].alt_branches.add(south)
    orbit = models.Publisher.objects.create(pk=_ORBIT, name="Orbit", house_code="ORB")
    tor = models.Publisher.objects.create(pk=_TOR, name="Tor", house_code="TOR")
    first = models.Edition.objects.create(
        isbn_13="9780000000001",
        imprint="First",
        publisher=orbit,
    )
    second = models.Edition.objects.create(
        isbn_13="9780000000002",
        imprint="Second",
        publisher=tor,
    )
    models.Printing.objects.create(edition=first).co_publishers.add(tor)
    models.Printing.objects.create(edition=second).co_publishers.add(orbit)


_ROOTS = {
    "books": ("FlatBindBookFilterInputType", "title"),
    "editions": ("FlatBindEditionFilterInputType", "imprint"),
    "branches": ("FlatBindBranchRootFilterInputType", "name"),
    "genres": ("FlatBindGenreRootFilterInputType", "name"),
    "shelves": ("FlatBindShelfFilterInputType", "code"),
}

#: ``(root, flat input, nested input, expected labels, (flat, nested) statements)`` per leaf.
#: A flat request builds only its named copy's form field and the nested one every child
#: filter's, so an ``AllValuesMultipleFilter`` child (``code_values``, ``code_values_method``,
#: ``alt_branch_names``) costs the nested branch one ``SELECT DISTINCT`` each; every walked
#: ``AllValuesMultipleFilter`` terminal reads its target model's values once per value it
#: compares (``MultipleChoiceFilter.get_filter_predicate``), as its nested twin does.
_Case: TypeAlias = tuple[
    str,
    Mapping[str, object],
    Mapping[str, object],
    list[str],
    tuple[int, int],
]

_CASES: dict[str, _Case] = {
    "forward-all-values": (
        "books",
        {"shelfCodeValues": {"exact": ["A-1"]}},
        {"shelf": {"codeValues": {"exact": ["A-1"]}}},
        ["Dune"],
        (3, 5),
    ),
    "forward-all-values-two-values": (
        "books",
        {"shelfCodeValues": {"exact": ["A-1", "C-3"]}},
        {"shelf": {"codeValues": {"exact": ["A-1", "C-3"]}}},
        ["Dune", "Emma"],
        (4, 6),
    ),
    "forward-consumer-multiple-choice": (
        "books",
        {"shelfCodeLabelled": {"exact": ["C-3"]}},
        {"shelf": {"codeLabelled": {"exact": ["C-3"]}}},
        ["Emma"],
        (1, 4),
    ),
    "forward-consumer-recleaned": (
        "books",
        {"shelfCodeRecleaned": {"exact": "C-3"}},
        {"shelf": {"codeRecleaned": {"exact": "C-3"}}},
        ["Emma"],
        (1, 4),
    ),
    "forward-consumer-owner-checked": (
        "books",
        {"shelfCodeOwnerChecked": {"exact": "C-3"}},
        {"shelf": {"codeOwnerChecked": {"exact": "C-3"}}},
        ["Emma"],
        (1, 4),
    ),
    "forward-key-folded": (
        "books",
        {"shelfBranchLabelled": {"exact": [_SOUTH]}},
        {"shelf": {"branchLabelled": {"exact": [_SOUTH]}}},
        ["Emma"],
        (2, 5),
    ),
    "to-many-key": (
        "editions",
        {"printingsCoPublishersLabelled": {"exact": [_TOR]}},
        {"printings": {"coPublishersLabelled": {"exact": [_TOR]}}},
        ["First"],
        (2, 2),
    ),
    "many-to-many-all-values": (
        "books",
        {"genresNameValues": {"exact": ["Poetry"]}},
        {"genres": {"nameValues": {"exact": ["Poetry"]}}},
        ["Emma"],
        (3, 3),
    ),
    "two-hops-all-values": (
        "books",
        {"shelfBranchNameValues": {"exact": ["South"]}},
        {"shelf": {"branch": {"nameValues": {"exact": ["South"]}}}},
        ["Emma"],
        (3, 6),
    ),
    "reverse-all-values": (
        "branches",
        {"shelvesCodeValues": {"exact": ["C-3"]}},
        {"shelves": {"codeValues": {"exact": ["C-3"]}}},
        ["South"],
        (3, 5),
    ),
    "reverse-consumer-multiple-choice": (
        "branches",
        {"shelvesCodeLabelled": {"exact": ["A-1"]}},
        {"shelves": {"codeLabelled": {"exact": ["A-1"]}}},
        ["North"],
        (1, 4),
    ),
    "declared-then-undeclared-all-values": (
        "books",
        {"shelfAltBranchNames": {"exact": ["South"]}},
        {"shelf": {"altBranchNames": {"exact": ["South"]}}},
        ["Dune"],
        (3, 5),
    ),
    "method-twin": (
        "books",
        {"shelfCodeValuesMethod": {"exact": ["A-1"]}},
        {"shelf": {"codeValuesMethod": {"exact": ["A-1"]}}},
        ["Dune"],
        (2, 4),
    ),
    "init-twin": (
        "genres",
        {"booksTitleValues": {"exact": ["Emma"]}},
        {"books": {"titleValues": {"exact": ["Emma"]}}},
        ["Poetry"],
        (3, 3),
    ),
}


def _document(root: str) -> str:
    input_type, label = _ROOTS[root]
    return (
        f"query ($filter: {input_type}) "
        f"{{ {root}(filter: $filter) {{ edges {{ node {{ {label} }} }} }} }}"
    )


def _labels(root: str, labels: list[str]) -> JSONObject:
    label = _ROOTS[root][1]
    return {"data": {root: {"edges": [{"node": {label: value}} for value in labels]}}}


def _post(
    schema: DjangoSchema,
    root: str,
    filter_input: Mapping[str, object],
) -> tuple[JSONObject, int]:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__), CaptureQueriesContext(connection) as sql:
            payload = graphql_payload(
                _document(root),
                variables={"filter": filter_input},
                url="/graphql-flat-binding/",
            )
    finally:
        _CURRENT["schema"] = None
    return payload, len(sql)


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(_CASES))
def test_a_walked_flat_copy_answers_its_nested_twins_rows_with_its_queries(case: str) -> None:
    """The flat leaf answers the nested branch's rows, each in its pinned statement count."""
    root, flat, nested, expected, statements = _CASES[case]
    _world()
    schema = _schema()

    flat_payload, flat_queries = _post(schema, root, flat)
    nested_payload, nested_queries = _post(schema, root, nested)

    assert flat_payload == _labels(root, expected), flat_payload
    assert nested_payload == flat_payload
    assert (flat_queries, nested_queries) == statements


@pytest.mark.django_db
def test_a_sets_own_leaf_walking_a_scoped_undeclared_relation_reads_the_relations_model() -> None:
    """``alt_branch_names`` at the shelves root walks ``alt_branches`` as an undeclared hop.

    ``FlatBindBranch.get_queryset`` scopes the relation, so the leaf walks it and runs bound
    to the face the hop's rows offer (``_UndeclaredHopSet``), its model ``Branch``.
    """
    _world()

    payload, _queries = _post(_schema(), "shelves", {"altBranchNames": {"exact": ["South"]}})

    assert payload == _labels("shelves", ["A-1"]), payload


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("case", sorted(_CASES))
async def test_a_walked_flat_copy_answers_its_nested_twins_rows_async(case: str) -> None:
    """Under the async view (``apply_async``) the flat leaf answers the same rows."""
    root, flat, nested, expected, _statements = _CASES[case]
    await sync_to_async(_world)()
    schema = _schema()
    _CURRENT["schema"] = schema
    payloads: list[JSONObject] = []
    try:
        with override_settings(ROOT_URLCONF=__name__):
            for filter_input in (flat, nested):
                result = await AsyncTestClient().query(
                    _document(root),
                    variables={"filter": filter_input},
                    assert_no_errors=False,
                    url="/graphql-flat-binding-async/",
                )
                payloads.append(response_json(result.response))
    finally:
        _CURRENT["schema"] = None

    assert payloads == [_labels(root, expected)] * 2, payloads


_RAW_CASES = {
    "forward-all-values": ("shelf__code_values=A-1&shelf__code_values=C-3", ["Dune", "Emma"]),
    "forward-consumer-multiple-choice": ("shelf__code_labelled=C-3", ["Emma"]),
    "forward-consumer-recleaned": ("shelf__code_recleaned=C-3", ["Emma"]),
    "many-to-many-all-values": ("genres__name_values=Fiction", ["Dune"]),
    "two-hops-all-values": ("shelf__branch__name_values=South", ["Emma"]),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(_RAW_CASES))
def test_a_raw_filterset_walks_a_flat_copy_on_its_target_model(case: str) -> None:
    """A resolver's own ``FilterSet(data, queryset, request=...).qs`` reads the same rows."""
    query, expected = _RAW_CASES[case]
    _world()
    _CURRENT["schema"] = _schema()
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(
                "query ($query: String!) { rawBooks(query: $query) }",
                variables={"query": query},
                url="/graphql-flat-binding/",
            )
    finally:
        _CURRENT["schema"] = None

    assert payload == {"data": {"rawBooks": expected}}, payload


# --- A declared branch's explicit ``queryset=`` over distinct child rows ---------------------


def _shelves_for_request(request: HttpRequest | None) -> QuerySet[models.Shelf]:
    """django-filter's request-aware ``queryset=`` form: every shelf but ``A-1``."""
    del request
    return models.Shelf.objects.exclude(code="A-1")


class ScopedBranchFilter(FilterSet):
    """The branch a shelf stands in: a distinct ``name_values`` and a plain ``name_text``."""

    name_values = AllValuesMultipleFilter(field_name="name")
    name_text = CharFilter(field_name="name")

    class Meta:
        model = models.Branch
        fields = ()


class ScopedGenreFilter(FilterSet):
    """A book's genres: django-filter's ``AllValuesMultipleFilter`` over ``name``."""

    name_values = AllValuesMultipleFilter(field_name="name")

    class Meta:
        model = models.Genre
        fields = ()


class ScopedShelfFilter(FilterSet):
    """Shelf leaves django-filter runs ``distinct()`` for, a plain one, and a scoped branch hop."""

    code_values = AllValuesMultipleFilter(field_name="code")
    code_labelled = _LabelledPicks(field_name="code", choices=_CODES)
    branch_labelled = _LabelledRows(field_name="branch", queryset=models.Branch.objects.all())
    code_contains = CharFilter(field_name="code", lookup_expr="icontains")
    branch = RelatedFilter(
        ScopedBranchFilter,
        field_name="branch",
        queryset=models.Branch.objects.exclude(name="North"),
    )

    class Meta:
        model = models.Shelf
        fields = ()


def _scoped_book_filter(name: str, queryset: object) -> type[FilterSet]:
    """A ``Book`` set whose ``shelf`` branch declares ``queryset`` (none for ``None``)."""
    shelf = (
        RelatedFilter(ScopedShelfFilter, field_name="shelf")
        if queryset is None
        else RelatedFilter(ScopedShelfFilter, field_name="shelf", queryset=queryset)
    )
    genres = RelatedFilter(
        ScopedGenreFilter,
        field_name="genres",
        queryset=models.Genre.objects.exclude(name="Fiction"),
    )
    meta = type("Meta", (), {"model": models.Book, "fields": ()})
    namespace = {
        "__module__": __name__,
        "shelf": shelf,
        "genres": genres,
        "Meta": meta,
    }
    return type(name, (FilterSet,), namespace)


#: The ``Book`` sets, by the ``queryset=`` their ``shelf`` branch declares.
_SCOPED_BOOK_SETS = {
    "plain": _scoped_book_filter(
        "ScopedPlainBookFilter",
        models.Shelf.objects.exclude(code="A-1"),
    ),
    "callable": _scoped_book_filter("ScopedCallableBookFilter", _shelves_for_request),
    "distinct": _scoped_book_filter(
        "ScopedDistinctBookFilter",
        models.Shelf.objects.exclude(code="A-1").distinct(),
    ),
    "combined": _scoped_book_filter(
        "ScopedCombinedBookFilter",
        models.Shelf.objects.filter(code="C-3").union(models.Shelf.objects.filter(code="D-4")),
    ),
    "open": _scoped_book_filter("ScopedOpenBookFilter", None),
    # Pinned to an alias the settings never configure: the refusal reads the pin alone.
    "pinned": _scoped_book_filter(
        "ScopedPinnedBookFilter",
        models.Shelf.objects.using("elsewhere").exclude(code="A-1"),
    ),
}


class ScopedBranchRootFilter(FilterSet):
    """Branches through the reverse key ``shelves``, every shelf but ``C-3``."""

    shelves = RelatedFilter(
        ScopedShelfFilter,
        field_name="shelves",
        queryset=models.Shelf.objects.exclude(code="C-3"),
    )

    class Meta:
        model = models.Branch
        fields = ()


def _scoped_raw_titles(variant: str, query: str, request: HttpRequest) -> list[str]:
    """A consumer's own ``<book set>(data, queryset, request=...).qs``."""
    filterset = _SCOPED_BOOK_SETS[variant](
        data=QueryDict(query),
        queryset=models.Book.objects.order_by("title"),
        request=request,
    )
    assert filterset.is_valid(), filterset.errors
    matched: QuerySet[Model] = filterset.qs
    return [require_instance(read_attr(book, "title"), str) for book in matched]


def _scoped_schema(variant: str) -> DjangoSchema:
    book_set = _SCOPED_BOOK_SETS[variant]

    class ScopedBook(DjangoType):
        class Meta:
            model = models.Book
            fields = ("id", "title")
            interfaces = (relay.Node,)
            filterset_class = book_set

    class ScopedBranch(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = ScopedBranchRootFilter

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[models.Branch],
            info: strawberry.Info[object, object],
        ) -> QuerySet[models.Branch]:
            # A visibility hook reading its rows ``distinct()``.
            return queryset.exclude(city="restricted").distinct()

    class ScopedShelf(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("id", "code")
            filterset_class = ScopedShelfFilter

    class ScopedGenre(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            filterset_class = ScopedGenreFilter

    @strawberry.type
    class Query:
        books: DjangoConnection[ScopedBook] = DjangoConnectionField(ScopedBook)
        branches: DjangoConnection[ScopedBranch] = DjangoConnectionField(ScopedBranch)

        @strawberry.field
        def raw_books(self, info: strawberry.Info[object, object], query: str) -> list[str]:
            del self
            return _scoped_raw_titles(
                variant,
                query,
                require_instance(read_attr(info.context, "request"), HttpRequest),
            )

    del ScopedShelf, ScopedGenre
    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


_SCOPED_ROOTS = {"books": "title", "branches": "name"}
#: Every label each root lists unfiltered.
_SCOPED_EVERYONE = {"books": ["Dune", "Emma"], "branches": ["North", "South"]}

#: ``(book set, root, flat input, nested input, expected labels, (flat, nested) statements)``:
#: each child leaf admits a row the branch's ``queryset=`` leaves out, so only the rows the
#: queryset holds answer.
_ScopedCase: TypeAlias = tuple[
    str,
    str,
    Mapping[str, object],
    Mapping[str, object],
    list[str],
    tuple[int, int],
]

_SCOPED_CASES: dict[str, _ScopedCase] = {
    "forward-all-values": (
        "plain",
        "books",
        {"shelfCodeValues": {"exact": ["A-1", "C-3"]}},
        {"shelf": {"codeValues": {"exact": ["A-1", "C-3"]}}},
        ["Emma"],
        (4, 4),
    ),
    "forward-consumer-multiple-choice": (
        "plain",
        "books",
        {"shelfCodeLabelled": {"exact": ["A-1", "C-3"]}},
        {"shelf": {"codeLabelled": {"exact": ["A-1", "C-3"]}}},
        ["Emma"],
        (1, 2),
    ),
    "forward-key": (
        "plain",
        "books",
        {"shelfBranchLabelled": {"exact": [_NORTH, _SOUTH]}},
        {"shelf": {"branchLabelled": {"exact": [_NORTH, _SOUTH]}}},
        ["Emma"],
        (2, 3),
    ),
    "callable-queryset": (
        "callable",
        "books",
        {"shelfCodeValues": {"exact": ["A-1", "C-3"]}},
        {"shelf": {"codeValues": {"exact": ["A-1", "C-3"]}}},
        ["Emma"],
        (4, 4),
    ),
    "distinct-queryset-plain-leaf": (
        "distinct",
        "books",
        {"shelfCodeContains": {"iContains": "-"}},
        {"shelf": {"codeContains": {"iContains": "-"}}},
        ["Emma"],
        (1, 2),
    ),
    "combined-queryset": (
        "combined",
        "books",
        {"shelfCodeValues": {"exact": ["A-1", "C-3"]}},
        {"shelf": {"codeValues": {"exact": ["A-1", "C-3"]}}},
        ["Emma"],
        (4, 4),
    ),
    "many-to-many": (
        "open",
        "books",
        {"genresNameValues": {"exact": ["Fiction", "Poetry"]}},
        {"genres": {"nameValues": {"exact": ["Fiction", "Poetry"]}}},
        ["Emma"],
        (4, 4),
    ),
    "reverse": (
        "open",
        "branches",
        {"shelvesCodeValues": {"exact": ["A-1", "C-3"]}},
        {"shelves": {"codeValues": {"exact": ["A-1", "C-3"]}}},
        ["North"],
        (4, 4),
    ),
    "second-hop-scoped": (
        "open",
        "books",
        {"shelfBranchNameValues": {"exact": ["North", "South"]}},
        {"shelf": {"branch": {"nameValues": {"exact": ["North", "South"]}}}},
        ["Emma"],
        (4, 5),
    ),
    "second-hop-distinct-hook-plain-leaf": (
        "open",
        "books",
        {"shelfBranchNameText": {"exact": "South"}},
        {"shelf": {"branch": {"nameText": {"exact": "South"}}}},
        ["Emma"],
        (1, 3),
    ),
}


def _scoped_document(variant: str, root: str) -> str:
    label = _SCOPED_ROOTS[root]
    input_type = (
        f"{_SCOPED_BOOK_SETS[variant].__name__}InputType"
        if root == "books"
        else "ScopedBranchRootFilterInputType"
    )
    return (
        f"query ($filter: {input_type}) "
        f"{{ {root}(filter: $filter) {{ edges {{ node {{ {label} }} }} }} }}"
    )


def _scoped_post(
    schema: DjangoSchema,
    variant: str,
    root: str,
    filter_input: Mapping[str, object],
) -> tuple[JSONObject, int]:
    document = _scoped_document(variant, root)
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__), CaptureQueriesContext(connection) as sql:
            payload = graphql_payload(
                document,
                variables={"filter": filter_input},
                url="/graphql-flat-binding/",
            )
    finally:
        _CURRENT["schema"] = None
    return payload, len(sql)


def _scoped_labels(root: str, labels: list[str]) -> JSONObject:
    label = _SCOPED_ROOTS[root]
    return {"data": {root: {"edges": [{"node": {label: value}} for value in labels]}}}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(_SCOPED_CASES))
def test_a_scoped_branch_admits_its_child_rows_the_queryset_holds(case: str) -> None:
    """A branch's ``queryset=`` bounds its child rows however either side reads ``distinct()``."""
    variant, root, flat, nested, expected, statements = _SCOPED_CASES[case]
    _world()
    schema = _scoped_schema(variant)

    flat_payload, flat_queries = _scoped_post(schema, variant, root, flat)
    nested_payload, nested_queries = _scoped_post(schema, variant, root, nested)
    negated_payload, _negated_queries = _scoped_post(schema, variant, root, {"not": nested})
    both_payload, _both_queries = _scoped_post(schema, variant, root, {"and": [nested, nested]})
    either_payload, _either_queries = _scoped_post(
        schema,
        variant,
        root,
        {"or": [nested, nested]},
    )

    assert flat_payload == _scoped_labels(root, expected), flat_payload
    assert nested_payload == flat_payload
    assert both_payload == flat_payload
    assert either_payload == flat_payload
    everyone = _SCOPED_EVERYONE[root]
    assert negated_payload == _scoped_labels(
        root,
        [label for label in everyone if label not in expected],
    ), negated_payload
    assert (flat_queries, nested_queries) == statements


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("case", sorted(_SCOPED_CASES))
async def test_a_scoped_branch_admits_its_child_rows_the_queryset_holds_async(case: str) -> None:
    """Under the async view (``apply_async``) each spelling answers the same rows."""
    variant, root, flat, nested, expected, _statements = _SCOPED_CASES[case]
    await sync_to_async(_world)()
    schema = _scoped_schema(variant)
    document = _scoped_document(variant, root)
    everyone = _SCOPED_EVERYONE[root]
    spellings = (
        (flat, expected),
        (nested, expected),
        ({"not": nested}, [value for value in everyone if value not in expected]),
        ({"and": [nested, nested]}, expected),
        ({"or": [nested, nested]}, expected),
    )
    _CURRENT["schema"] = schema
    payloads: list[JSONObject] = []
    try:
        with override_settings(ROOT_URLCONF=__name__):
            for filter_input, _expected in spellings:
                result = await AsyncTestClient().query(
                    document,
                    variables={"filter": filter_input},
                    assert_no_errors=False,
                    url="/graphql-flat-binding-async/",
                )
                payloads.append(response_json(result.response))
    finally:
        _CURRENT["schema"] = None

    assert payloads == [_scoped_labels(root, labels) for _input, labels in spellings], payloads


_SCOPED_RAW_CASES = {
    "forward-all-values": ("plain", "shelf__code_values=A-1&shelf__code_values=C-3", ["Emma"]),
    "distinct-queryset-plain-leaf": ("distinct", "shelf__code_contains=-", ["Emma"]),
    "combined-queryset": ("combined", "shelf__code_values=A-1&shelf__code_values=C-3", ["Emma"]),
    "second-hop-distinct-hook-plain-leaf": ("open", "shelf__branch__name_text=South", ["Emma"]),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(_SCOPED_RAW_CASES))
def test_a_raw_filterset_walks_a_scoped_branch_to_the_rows_its_queryset_holds(case: str) -> None:
    """A resolver's own scoped book set's ``(data, queryset, request=...).qs`` reads these rows."""
    variant, query, expected = _SCOPED_RAW_CASES[case]
    _world()
    _CURRENT["schema"] = _scoped_schema(variant)
    try:
        with override_settings(ROOT_URLCONF=__name__):
            payload = graphql_payload(
                "query ($query: String!) { rawBooks(query: $query) }",
                variables={"query": query},
                url="/graphql-flat-binding/",
            )
    finally:
        _CURRENT["schema"] = None

    assert payload == {"data": {"rawBooks": expected}}, payload


_PINNED_REFUSAL = (
    "RelatedFilter ScopedPinnedBookFilter.shelf: the explicit ``queryset=`` is pinned with "
    "``.using()`` to database alias 'elsewhere', but this request reads alias 'default'; one "
    "resolution never spans two database connections. Remove the ``.using(...)`` call so the "
    "queryset follows the request's alias."
)


@pytest.mark.django_db
def test_a_scoped_branch_pinned_to_an_alias_the_request_does_not_read_is_refused() -> None:
    """A ``queryset=`` pinned by ``.using`` to another alias is the typed refusal, each spelling."""
    _world()
    schema = _scoped_schema("pinned")
    nested = {"shelf": {"codeContains": {"iContains": "-"}}}
    _CURRENT["schema"] = schema
    try:
        with (
            override_settings(
                ROOT_URLCONF=__name__,
                DEBUG=True,
                MIDDLEWARE=middleware_without_debug_toolbar(),
            ),
            CaptureQueriesContext(connection) as sql,
        ):
            payloads = [
                graphql_payload(
                    _scoped_document("pinned", "books"),
                    variables={"filter": filter_input},
                    url="/graphql-flat-binding/",
                )
                for filter_input in (
                    {"shelfCodeContains": {"iContains": "-"}},
                    nested,
                    {"not": nested},
                )
            ]
            payloads.append(
                graphql_payload(
                    "query ($query: String!) { rawBooks(query: $query) }",
                    variables={"query": "shelf__code_contains=-"},
                    url="/graphql-flat-binding/",
                ),
            )
    finally:
        _CURRENT["schema"] = None

    assert [len(json_list(payload, "errors")) for payload in payloads] == [1] * 4, payloads
    assert [json_str(payload, "errors", 0, "message") for payload in payloads] == [
        _PINNED_REFUSAL,
    ] * 4
    # No book row is read: the refusal comes before the request's query runs.
    assert [q["sql"] for q in sql.captured_queries if '"library_book"."title"' in q["sql"]] == []


@pytest.mark.django_db(transaction=True)
async def test_a_scoped_branch_pinned_to_an_alias_the_request_does_not_read_is_refused_async() -> (
    None
):
    """Under the async view (``apply_async``) each spelling answers the same typed refusal."""
    await sync_to_async(_world)()
    schema = _scoped_schema("pinned")
    nested = {"shelf": {"codeContains": {"iContains": "-"}}}
    _CURRENT["schema"] = schema
    payloads: list[JSONObject] = []
    try:
        with override_settings(
            ROOT_URLCONF=__name__,
            DEBUG=True,
            MIDDLEWARE=middleware_without_debug_toolbar(),
        ):
            for filter_input in (
                {"shelfCodeContains": {"iContains": "-"}},
                nested,
                {"not": nested},
            ):
                result = await AsyncTestClient().query(
                    _scoped_document("pinned", "books"),
                    variables={"filter": filter_input},
                    assert_no_errors=False,
                    url="/graphql-flat-binding-async/",
                )
                payloads.append(response_json(result.response))
    finally:
        _CURRENT["schema"] = None

    assert [len(json_list(payload, "errors")) for payload in payloads] == [1] * 3, payloads
    assert [json_str(payload, "errors", 0, "message") for payload in payloads] == [
        _PINNED_REFUSAL,
    ] * 3
