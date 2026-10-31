"""Consumer filters preserve queryset returns, distinctness and projected branch gates over HTTP.

Ordinary JSON reaches unbound public filtersets. A class-owned filter returning
an actual list is refused on each execution path. A customized projected child
walks its own related branch permission before returning any parent rows. A forward
relation choice keeps its authored DISTINCT on the parent query beside its visibility EXISTS.
An explicit related queryset must carry the target filterset's exact model whenever its branch
is active, including the distinction between a proxy and its concrete model.
"""

from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db import connection
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import CharFilter, Filter, ModelChoiceFilter
from graphql import GraphQLError
from graphql_client import JSONObject, graphql_payload, json_at, json_list
from strawberry.scalars import JSON

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.utils._narrowing import require
from django_strawberry_framework.utils.relations import is_model_class
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_ConsumerShelfProxy = type(
    "ConsumerShelfProxy",
    (models.Shelf,),
    {"__module__": __name__, "Meta": type("Meta", (), {"proxy": True, "app_label": "library"})},
)


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-filter-contracts/", _graphql_view)]


def _returns_a_list(_self: Filter, _queryset: object, _value: object) -> list[object]:
    return []


def _bad_return_parent(field_name: str) -> type[FilterSet]:
    class ShelfChild(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    probe = type("ListReturningFilter", (CharFilter,), {"filter": _returns_a_list})(
        field_name=field_name,
    )
    return type(
        "BookParent",
        (FilterSet,),
        {
            "shelf": RelatedFilter(ShelfChild, field_name="shelf"),
            "probe": probe,
            "Meta": type("Meta", (), {"model": models.Book, "fields": {"title": ["exact"]}}),
        },
    )


def _gated_parent() -> type[FilterSet]:
    class BookChild(FilterSet):
        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    class GenreChild(FilterSet):
        books = RelatedFilter(BookChild, field_name="books")
        named = CharFilter(field_name="books__title")

        class Meta:
            model = models.Genre
            fields = {"name": ["exact"]}

        def __init__(
            self,
            data: dict[str, object] | None = None,
            queryset: QuerySet[Model] | None = None,
            *,
            request: HttpRequest | None = None,
            prefix: str | None = None,
        ) -> None:
            super().__init__(data=data, queryset=queryset, request=request, prefix=prefix)

        def check_books_permission(self, request: HttpRequest) -> None:
            if request.headers.get("X-Refuse-Books") == "yes":
                raise GraphQLError("books denied")

    class BookParent(FilterSet):
        genres = RelatedFilter(GenreChild, field_name="genres")

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    return BookParent


def _schema(parent: type[FilterSet], *, hide_secret: bool = False) -> DjangoSchema:
    def visible_shelves(
        _cls: type[DjangoType],
        queryset: QuerySet[models.Shelf],
        _info: object,
    ) -> QuerySet[models.Shelf]:
        return queryset.exclude(topic="secret") if hide_secret else queryset

    shelf_output = type(
        "ShelfOutput",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": models.Shelf, "fields": ("code",)}),
            "get_queryset": classmethod(visible_shelves),
        },
    )

    class GenreOutput(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)

    class BookOutput(DjangoType):
        class Meta:
            model = models.Book
            fields = ("title",)

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[models.Book]:
        del root
        return parent.apply_sync(where, models.Book.objects.order_by("title"), info)

    def resolve_all(root: object) -> QuerySet[models.Book]:
        del root
        return models.Book.objects.order_by("title")

    @strawberry.type
    class Query:
        rows: QuerySet[models.Book] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[BookOutput],
        )
        all_rows: QuerySet[models.Book] = strawberry.field(
            resolver=resolve_all,
            graphql_type=list[BookOutput],
        )

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=[shelf_output, GenreOutput],
        config=strawberry_config(),
        extensions=[lambda: extension],
        error_policy={"enabled": False},
    )


def _world() -> None:
    branch = models.Branch.objects.create(name="contracts")
    shelf = models.Shelf.objects.create(branch=branch, code="match")
    genre = models.Genre.objects.create(name="shared")
    match = models.Book.objects.create(shelf=shelf, title="match")
    match.genres.add(genre)
    models.Book.objects.create(shelf=shelf, title="other")
    models.Book.objects.create(shelf=shelf, title="unlinked")


def _post(
    schema: DjangoSchema,
    where: JSONObject,
    *,
    denied: bool = False,
    label: str = "title",
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                "query($where: JSON!) { rows(where: $where) { "
                + label
                + " } allRows { "
                + label
                + " } }",
                variables={"where": where},
                client=Client(headers={"X-Refuse-Books": "yes" if denied else "no"}),
                url="/graphql-filter-contracts/",
            )
    finally:
        _CURRENT["schema"] = None


def _refusal(payload: JSONObject, message: str) -> None:
    assert json_at(payload, "data") is None, payload
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    assert json_at(errors[0], "path") == ["rows"], payload
    assert json_at(errors[0], "message") == message, payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field_name", "named"),
    [
        ("title", "'BookParent.probe'"),
        ("shelf", "'BookParent' filter 'shelf'"),
        ("shelf__code", "'BookParent' filter 'code'"),
    ],
    ids=["own-column", "relation-key", "through-branch"],
)
def test_class_owned_filter_returning_a_list_is_refused_on_each_public_leaf_path(
    field_name: str,
    named: str,
) -> None:
    """Each path reports its real production QuerySet assertion instead of accepting a consumer list."""
    _world()
    payload = _post(_schema(_bad_return_parent(field_name)), {"probe": "match"})
    _refusal(payload, f"Expected {named} to return a QuerySet, but got a list instead.")


@pytest.mark.django_db
@pytest.mark.parametrize("spelling", ["projected", "nested"])
@pytest.mark.parametrize("denied", [False, True], ids=["allowed", "denied"])
def test_customized_projected_child_walks_its_own_related_branch_permission(
    spelling: str,
    *,
    denied: bool,
) -> None:
    """The projected child and its nested twin honor the child gate, with ordinary allowed rows."""
    _world()
    where: JSONObject = (
        {"genres__named": "match"}
        if spelling == "projected"
        else {"genres": {"books": {"title": "match"}}}
    )
    payload = _post(_schema(_gated_parent()), where, denied=denied)
    if denied:
        _refusal(payload, "books denied")
    else:
        assert payload == {
            "data": {
                "rows": [{"title": "match"}],
                "allRows": [{"title": title} for title in ("match", "other", "unlinked")],
            },
        }, payload


@pytest.mark.django_db
@pytest.mark.parametrize("hidden", [False, True], ids=["visible-target", "hidden-target"])
def test_a_forward_model_choice_keeps_consumer_distinctness_on_the_parent_rows(
    *,
    hidden: bool,
) -> None:
    """The parent owns DISTINCT while one correlated EXISTS enforces the target visibility."""

    class ShelfChild(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class BookParent(FilterSet):
        shelf = RelatedFilter(ShelfChild, field_name="shelf")
        shelf_is = ModelChoiceFilter(
            field_name="shelf",
            queryset=models.Shelf.objects.all(),
            distinct=True,
        )

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    branch = models.Branch.objects.create(name="forward distinct")
    visible = models.Shelf.objects.create(branch=branch, code="visible", topic="open")
    secret = models.Shelf.objects.create(branch=branch, code="hidden", topic="secret")
    models.Book.objects.create(shelf=visible, title="visible")
    models.Book.objects.create(shelf=secret, title="hidden")
    schema = _schema(BookParent, hide_secret=True)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, {"shelf_is": saved_pk(secret if hidden else visible)})
    assert payload == {
        "data": {
            "rows": [] if hidden else [{"title": "visible"}],
            "allRows": [{"title": "hidden"}, {"title": "visible"}],
        },
    }, payload
    filtered = [
        entry["sql"]
        for entry in captured.captured_queries
        if 'FROM "library_book"' in entry["sql"] and "EXISTS" in entry["sql"].upper()
    ]
    assert len(filtered) == 1, captured.captured_queries
    assert filtered[0].upper().startswith("SELECT DISTINCT"), filtered
    assert filtered[0].upper().count("EXISTS") == 1, filtered


def _explicit_queryset_schema(queryset: QuerySet[Model]) -> DjangoSchema:
    class ShelfChild(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    parent = type(
        "ExplicitBranchParent",
        (FilterSet,),
        {
            "shelves": RelatedFilter(ShelfChild, field_name="shelves", queryset=queryset),
            "Meta": type("Meta", (), {"model": models.Branch, "fields": {"name": ["exact"]}}),
        },
    )

    class ShelfOutput(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("code",)

    class BranchOutput(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("name",)

    def resolve_rows(
        root: object,
        info: strawberry.Info[object, object],
        where: JSON,
    ) -> QuerySet[models.Branch]:
        del root
        return parent.apply_sync(where, models.Branch.objects.order_by("name"), info)

    def resolve_all(root: object) -> QuerySet[models.Branch]:
        del root
        return models.Branch.objects.order_by("name")

    @strawberry.type
    class Query:
        rows: QuerySet[models.Branch] = strawberry.field(
            resolver=resolve_rows,
            graphql_type=list[BranchOutput],
        )
        all_rows: QuerySet[models.Branch] = strawberry.field(
            resolver=resolve_all,
            graphql_type=list[BranchOutput],
        )

    finalize_django_types()
    return DjangoSchema(
        query=Query,
        types=[ShelfOutput],
        config=strawberry_config(),
        error_policy={"enabled": False},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["wrong-model", "proxy", "concrete"])
@pytest.mark.parametrize("active", [False, True], ids=["inactive", "active"])
def test_related_queryset_requires_the_exact_child_model_only_when_the_branch_is_active(
    kind: str,
    *,
    active: bool,
) -> None:
    """A real branch checks exact model identity; an inactive declaration leaves all roots alone."""
    first = models.Branch.objects.create(name="alpha")
    models.Shelf.objects.create(branch=first, code="match", topic="open")
    second = models.Branch.objects.create(name="beta")
    models.Shelf.objects.create(branch=second, code="match", topic="closed")
    models.Branch.objects.create(name="gamma")
    explicit: QuerySet[Model]
    if kind == "wrong-model":
        explicit = models.Book.objects.all()
        model_name = "Book"
    elif kind == "proxy":
        proxy_model = require(_ConsumerShelfProxy, is_model_class)
        explicit = proxy_model._default_manager.all()
        model_name = "ConsumerShelfProxy"
    else:
        explicit = models.Shelf.objects.filter(topic="open")
        model_name = "Shelf"
    where: JSONObject = {"shelves": {"code": "match"}} if active else {}
    payload = _post(_explicit_queryset_schema(explicit), where, label="name")
    if active and kind != "concrete":
        _refusal(
            payload,
            "RelatedFilter ExplicitBranchParent.shelves: the explicit ``queryset=`` is keyed on "
            f"{model_name} but the target filterset is keyed on Shelf. Pass a queryset of Shelf "
            "instances to ``RelatedFilter(queryset=...)``; proxy and multi-table-inheritance "
            "children are NOT accepted because Django's queryset ``&`` operator rejects mixed "
            "model classes.",
        )
    else:
        all_rows = [{"name": name} for name in ("alpha", "beta", "gamma")]
        assert payload == {
            "data": {"rows": [{"name": "alpha"}] if active else all_rows, "allRows": all_rows},
        }, payload
