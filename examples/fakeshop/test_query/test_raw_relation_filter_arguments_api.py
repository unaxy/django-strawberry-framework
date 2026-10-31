"""Raw relation filters reached through ordinary public scalar Query arguments.

The consumer chooses Int/String arguments, passes their values to the original
unbound FilterSets through apply_sync, and returns plain Meta output types.
No generated FilterInput annotation is required for NumberFilter(ForeignKey)
or CharFilter(ForeignKey). Separate scoped target types supply relation
visibility while an unfiltered sibling proves the roots themselves remain
available.
"""

from collections.abc import Sequence
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter, ModelChoiceFilter, NumberFilter
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-raw-relation-arguments/", _graphql_view)]


def _post(schema: DjangoSchema, document: str, variables: JSONObject) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-raw-relation-arguments/",
            )
    finally:
        _CURRENT["schema"] = None


def _schema(query: type[object], types: Sequence[type[DjangoType]]) -> DjangoSchema:
    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=query,
        types=types,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _assert_root_sql(sqls: Sequence[str], model: type[django_models.Model]) -> None:
    roots = [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith(f'"{model._meta.db_table}"')
    ]
    # One result list and one all-roots sibling; these raw Number/Char fields
    # have no ModelChoice form-cleaning query to confuse with root execution.
    assert len(roots) == 2, sqls
    filtered = [sql for sql in roots if "EXISTS" in sql.upper()]
    assert len(filtered) == 1, roots
    assert all("DISTINCT" not in sql.upper() for sql in roots), roots


def _book_schema() -> DjangoSchema:
    # Preserve the original declarations, including their distinct child sets,
    # without binding any set to an output type or materializing FilterInput.
    class BranchChild(FilterSet):
        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    class ShelfChild(FilterSet):
        branch = RelatedFilter(BranchChild, field_name="branch")

        class Meta:
            model = models.Shelf
            fields = {"topic": ["exact"]}

    class BookParent(FilterSet):
        shelf = RelatedFilter(ShelfChild, field_name="shelf")
        shelf_is = ModelChoiceFilter(field_name="shelf", queryset=models.Shelf.objects.all())
        branch_is = NumberFilter(field_name="shelf__branch")
        not_branch = NumberFilter(field_name="shelf__branch", exclude=True)
        branch_missing = BooleanFilter(field_name="shelf__branch", lookup_expr="isnull")
        name_missing = BooleanFilter(field_name="shelf__branch__name", lookup_expr="isnull")
        not_topic = CharFilter(field_name="shelf__topic", exclude=True)

        class Meta:
            model = models.Book
            fields = {"title": ["exact"]}

    class ScopedBranch(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("name", "city")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.Branch],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.Branch]:
            del info
            return queryset.exclude(city="restricted")

    class ScopedShelf(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("code", "topic")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.Shelf],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.Shelf]:
            del info
            return queryset.exclude(topic="secret")

    class BookOutput(DjangoType):
        class Meta:
            model = models.Book
            fields = ("title",)

    @strawberry.type
    class Query:
        def _books_by_branch(
            self,
            info: strawberry.Info[object, object],
            branch_id: int,
        ) -> django_models.QuerySet[models.Book]:
            return BookParent.apply_sync(
                {"branch_is": branch_id},
                models.Book.objects.order_by("pk"),
                info,
            )

        def _books_not_in_branch(
            self,
            info: strawberry.Info[object, object],
            branch_id: int,
        ) -> django_models.QuerySet[models.Book]:
            return BookParent.apply_sync(
                {"not_branch": branch_id},
                models.Book.objects.order_by("pk"),
                info,
            )

        def _all_books(self) -> django_models.QuerySet[models.Book]:
            return models.Book.objects.order_by("pk")

        books_by_branch: django_models.QuerySet[models.Book] = strawberry.field(
            resolver=_books_by_branch,
            graphql_type=list[BookOutput],
        )
        books_not_in_branch: django_models.QuerySet[models.Book] = strawberry.field(
            resolver=_books_not_in_branch,
            graphql_type=list[BookOutput],
        )
        all_books: django_models.QuerySet[models.Book] = strawberry.field(
            resolver=_all_books,
            graphql_type=list[BookOutput],
        )

    return _schema(Query, (ScopedBranch, ScopedShelf))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "branch", "expected"),
    [
        ("booksByBranch", "open", ["open", "no_topic"]),
        ("booksByBranch", "restricted", []),
        ("booksNotInBranch", "open", ["on_secret", "on_restricted"]),
        (
            "booksNotInBranch",
            "restricted",
            [
                "open",
                "on_secret",
                "on_restricted",
                "no_topic",
            ],
        ),
    ],
    ids=[
        "open-key",
        "hidden-key",
        "exclude-open-key",
        "exclude-hidden-key",
    ],
)
def test_raw_number_fk_argument_walks_both_target_scopes_without_hiding_roots(
    field: str,
    branch: str,
    expected: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Raw NumberFilter keys see no relation through either hidden hop; exclusion keeps absence."""
    branches = {
        name: models.Branch.objects.create(name=name, city="here" if name == "open" else name)
        for name in ("open", "restricted")
    }
    fixtures = [
        (
            "open",
            "open",
            "o",
            "t",
        ),
        (
            "on_secret",
            "open",
            "s",
            "secret",
        ),
        (
            "on_restricted",
            "restricted",
            "r",
            "t",
        ),
        (
            "no_topic",
            "open",
            "n",
            "",
        ),
    ]
    for title, parent, code, topic in fixtures:
        shelf = models.Shelf.objects.create(branch=branches[parent], code=code, topic=topic)
        models.Book.objects.create(title=title, shelf=shelf)
    schema = _book_schema()
    document = (
        "query($branch: Int!) { "
        f"rows: {field}(branchId: $branch) {{ title }} "
        "allBooks { title } }"
    )
    sql = record_compiled_sql()
    assert _post(schema, document, {"branch": saved_pk(branches[branch])}) == {
        "data": {
            "rows": [{"title": title} for title in expected],
            "allBooks": [{"title": title} for title, _, _, _ in fixtures],
        },
    }
    _assert_root_sql(sql, models.Book)
    filtered = next(statement for statement in sql if "EXISTS" in statement.upper())
    assert '"library_shelf"' in filtered, filtered
    assert '"library_branch"' in filtered, filtered


def _profile_schema() -> DjangoSchema:
    class ProfileKeys(FilterSet):
        by_pk = NumberFilter(field_name="pk")

        class Meta:
            model = models.PatronProfile
            fields = {"postal_code": ["exact"]}

    class ScopedPatron(DjangoType):
        class Meta:
            model = models.Patron
            fields = ("name",)

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.Patron],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.Patron]:
            del info
            return queryset.exclude(name="secret")

    class ProfileOutput(DjangoType):
        class Meta:
            model = models.PatronProfile
            fields = ("postal_code",)

    @strawberry.type
    class Query:
        def _profiles_by_patron(
            self,
            info: strawberry.Info[object, object],
            patron_id: int,
        ) -> django_models.QuerySet[models.PatronProfile]:
            return ProfileKeys.apply_sync(
                {"by_pk": patron_id},
                models.PatronProfile.objects.order_by("pk"),
                info,
            )

        def _all_profiles(self) -> django_models.QuerySet[models.PatronProfile]:
            return models.PatronProfile.objects.order_by("pk")

        profiles_by_patron: django_models.QuerySet[models.PatronProfile] = strawberry.field(
            resolver=_profiles_by_patron,
            graphql_type=list[ProfileOutput],
        )
        all_profiles: django_models.QuerySet[models.PatronProfile] = strawberry.field(
            resolver=_all_profiles,
            graphql_type=list[ProfileOutput],
        )

    return _schema(Query, (ScopedPatron,))


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["open", "secret"])
def test_raw_number_pk_argument_uses_the_patron_relation_of_a_profile(
    name: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A relation-valued model PK follows Patron visibility without filtering Profile roots."""
    patrons = {
        name: models.Patron.objects.create(name=name, email=name + "@x")
        for name in ("open", "secret")
    }
    for label, patron in patrons.items():
        models.PatronProfile.objects.create(patron=patron, postal_code=label)
    schema = _profile_schema()
    document = """
        query($patron: Int!) {
            rows: profilesByPatron(patronId: $patron) { postalCode }
            allProfiles { postalCode }
        }
    """
    sql = record_compiled_sql()
    assert _post(schema, document, {"patron": saved_pk(patrons[name])}) == {
        "data": {
            "rows": [{"postalCode": "open"}] if name == "open" else [],
            "allProfiles": [{"postalCode": "open"}, {"postalCode": "secret"}],
        },
    }
    _assert_root_sql(sql, models.PatronProfile)
    filtered = next(statement for statement in sql if "EXISTS" in statement.upper())
    assert '"library_patron"' in filtered, filtered
    assert '"patron_id"' in filtered, filtered


def _genre_schema() -> DjangoSchema:
    class GenreChild(FilterSet):
        class Meta:
            model = models.Genre
            fields = {"name": ["exact"]}

    class GenreParent(FilterSet):
        fans_favorite = RelatedFilter(GenreChild, field_name="favoring_profiles__favorite_genre")
        favored_as = CharFilter(field_name="favoring_profiles__favorite_genre")

        class Meta:
            model = models.Genre
            fields = {"name": ["exact"]}

    class ScopedGenre(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)
            primary = True

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.Genre],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.Genre]:
            del info
            return queryset.exclude(name__startswith="secret")

    class GenreOutput(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)
            primary = False

    class ProfileOutput(DjangoType):
        class Meta:
            model = models.PatronProfile
            fields = ("postal_code",)

    @strawberry.type
    class Query:
        def _genres_favored_as(
            self,
            info: strawberry.Info[object, object],
            name: str,
        ) -> django_models.QuerySet[models.Genre]:
            return GenreParent.apply_sync(
                {"favored_as": name},
                models.Genre.objects.order_by("pk"),
                info,
            )

        def _all_genres(self) -> django_models.QuerySet[models.Genre]:
            return models.Genre.objects.order_by("pk")

        genres_favored_as: django_models.QuerySet[models.Genre] = strawberry.field(
            resolver=_genres_favored_as,
            graphql_type=list[GenreOutput],
        )
        all_genres: django_models.QuerySet[models.Genre] = strawberry.field(
            resolver=_all_genres,
            graphql_type=list[GenreOutput],
        )

    return _schema(Query, (ScopedGenre, ProfileOutput))


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["open", "secret"])
def test_raw_char_fk_argument_compares_the_stored_to_field_name_over_a_reverse_hop(
    name: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Raw CharFilter uses Genre.name, hides the terminal target, and preserves all Genre roots."""
    opened = models.Genre.objects.create(name="open")
    secret = models.Genre.objects.create(name="secret")
    decoy = models.Genre.objects.create(name=str(saved_pk(opened)))
    for label, genre in [
        ("open", opened),
        ("secret", secret),
        ("decoy", decoy),
        ("none", None),
    ]:
        patron = models.Patron.objects.create(name=label, email=label + "@x")
        models.PatronProfile.objects.create(patron=patron, favorite_genre=genre, postal_code=label)
    schema = _genre_schema()
    document = """
        query($name: String!) {
            rows: genresFavoredAs(name: $name) { name }
            allGenres { name }
        }
    """
    sql = record_compiled_sql()
    assert _post(schema, document, {"name": name}) == {
        "data": {
            "rows": [{"name": "open"}] if name == "open" else [],
            "allGenres": [{"name": genre.name} for genre in (opened, secret, decoy)],
        },
    }
    _assert_root_sql(sql, models.Genre)
    filtered = next(statement for statement in sql if "EXISTS" in statement.upper())
    assert '"library_patronprofile"' in filtered, filtered
    assert '"favorite_genre_id"' in filtered, filtered
