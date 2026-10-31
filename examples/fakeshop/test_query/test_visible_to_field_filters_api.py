"""Native nullable to_field visibility, with raw PK and stored-name carriers distinguished.

Profile requests publish the actual generated relation key and authored
ModelChoiceFilter carriers. A saved Genre named as another Genre's primary key
makes comparing the stored name to a requested PK observably wrong. Hidden and
deleted targets remain distinct fixture causes of absent related rows.

The reverse stored-name request uses the supported ModelChoiceFilter name
carrier. The request names the stored key through the filter's own form field.
The plain reverse output deliberately preserves every Genre root while the
Meta-bound set controls visibility only on its re-entered target.
"""

from collections.abc import Sequence
from functools import wraps
from typing import Annotated, NamedTuple

import pytest
import strawberry
from apps.library import models
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import CharFilter, ModelChoiceFilter
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterInput, FilterSet, RelatedFilter
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-visible-to-field/", _graphql_view)]


def _input(schema: DjangoSchema) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _where(schema: DjangoSchema, path: Sequence[str], value: object) -> JSONObject:
    """Ask the actual schema definitions and configured NameConverter at each input level."""
    current = _input(schema)
    names: list[str] = []
    for index, name in enumerate(path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == name)
        wire = schema.config.name_converter.from_field(field)
        names.append(wire)
        if index < len(path) - 1:
            nested = get_named_type(graphql_type_of(graphql_input_fields(current)[wire]))
            assert isinstance(nested, GraphQLInputObjectType)
            current = nested
    assert names
    result: JSONObject = {names[-1]: value}
    for name in reversed(names[:-1]):
        result = {name: result}
    return result


def _post(schema: DjangoSchema, where: JSONObject, selection: str) -> JSONObject:
    query = f"query($where: {_input(schema).name}!) {{ rows(filter: $where) {{ {selection} }} }}"
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                query,
                variables={"where": where},
                url="/graphql-visible-to-field/",
            )
    finally:
        _CURRENT["schema"] = None


class _World(NamedTuple):
    """Saved Profile labels and the different raw identity/storage Genre columns."""

    genres: dict[str, models.Genre]
    profiles: dict[str, models.PatronProfile]


def _world() -> _World:
    opened = models.Genre.objects.create(name="open")
    secret = models.Genre.objects.create(name="secret")
    decoy = models.Genre.objects.create(name=str(saved_pk(opened)))
    gone = models.Genre.objects.create(name="gone")
    profiles: dict[str, models.PatronProfile] = {}
    for name, genre in [
        ("open", opened),
        ("secret", secret),
        ("none", gone),
        ("decoy", decoy),
    ]:
        patron = models.Patron.objects.create(name="patron-" + name, email=name + "@x")
        profiles[name] = models.PatronProfile.objects.create(
            patron=patron,
            favorite_genre=genre,
            postal_code=name,
        )
    # A genuinely missing former target uses the model's SET_NULL behavior,
    # without disabling constraints or constructing a dangling FK.
    gone.delete()
    profiles["none"].refresh_from_db(fields=["favorite_genre"])
    assert profiles["none"].favorite_genre is None
    return _World({"open": opened, "secret": secret, "decoy": decoy}, profiles)


def _profile_schema(*, declared: bool) -> DjangoSchema:
    class GenreChild(FilterSet):
        class Meta:
            model = models.Genre
            fields = {"name": ["exact", "isnull"]}

    class ProfileParent(FilterSet):
        if declared:
            favorite = RelatedFilter(GenreChild, field_name="favorite_genre")
        favored = ModelChoiceFilter(
            field_name="favorite_genre",
            queryset=models.Genre.objects.all(),
        )
        not_favored = ModelChoiceFilter(
            field_name="favorite_genre",
            queryset=models.Genre.objects.all(),
            exclude=True,
        )
        favorite_not_named = CharFilter(field_name="favorite_genre__name", exclude=True)

        class Meta:
            model = models.PatronProfile
            fields = {"favorite_genre": ["exact", "isnull"], "favorite_genre__name": ["isnull"]}

    class ScopedGenre(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)
            filterset_class = GenreChild

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.Genre],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.Genre]:
            del info
            return queryset.exclude(name__startswith="secret")

    class ProfileOutput(DjangoType):
        class Meta:
            model = models.PatronProfile
            fields = ("postal_code",)
            filterset_class = ProfileParent

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: Annotated[
                FilterInput[ProfileParent] | None,
                strawberry.argument(name="filter"),
            ] = None,
        ) -> django_models.QuerySet[models.PatronProfile]:
            queryset = models.PatronProfile.objects.order_by("pk")
            return queryset if where is None else ProfileParent.apply_sync(where, queryset, info)

        rows: django_models.QuerySet[models.PatronProfile] = strawberry.field(
            resolver=_rows,
            graphql_type=list[ProfileOutput],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=(ScopedGenre,),
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _profiles(world: _World, *names: str) -> JSONObject:
    return {"data": {"rows": [{"postalCode": world.profiles[name].postal_code} for name in names]}}


def _root_sql(sqls: Sequence[str], model: type[django_models.Model]) -> list[str]:
    return [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith(f'"{model._meta.db_table}"')
    ]


def _assert_profile_request_sql(sqls: Sequence[str]) -> None:
    root = _root_sql(sqls, models.PatronProfile)
    assert len(root) == 1, sqls
    assert '"favorite_genre_id"' in root[0], root
    assert "EXISTS" in root[0].upper(), root
    assert "DISTINCT" not in root[0].upper(), root
    # A forward FK whose stored key is Genre.name may legitimately JOIN
    # Genre to compare its requested PK; the target is unique, so it cannot fan out.


_NULL_CASES = [
    "terminal-null",
    "key-null",
    "key-nonnull",
    "exclude-open",
    "exclude-secret",
]


@pytest.mark.django_db
@pytest.mark.parametrize("declared", [True, False], ids=["declared", "undeclared"])
@pytest.mark.parametrize("case", _NULL_CASES)
def test_nullable_to_field_columns_and_keys_use_the_hidden_absent_world(
    case: str,
    record_compiled_sql: RecordCompiledSql,
    *,
    declared: bool,
) -> None:
    """Hidden and deleted targets count as absent; the visible numeric-name decoy stays nonnull."""
    world = _world()
    schema = _profile_schema(declared=declared)
    if case in {"terminal-null", "key-null", "key-nonnull"}:
        leaf = "favorite_genre_name" if case == "terminal-null" else "favorite_genre"
        null = case != "key-nonnull"
        where = _where(schema, (leaf, "is_null"), null)
        names = ["secret", "none"] if null else ["open", "decoy"]
    else:
        name = "open" if case == "exclude-open" else "secret"
        where = _where(schema, ("favorite_not_named", "exact"), name)
        names = (
            ["secret", "none", "decoy"]
            if name == "open"
            else [
                "open",
                "secret",
                "none",
                "decoy",
            ]
        )
    sqls = record_compiled_sql()
    assert _post(schema, where, "postalCode") == _profiles(world, *names)
    _assert_profile_request_sql(sqls)


@pytest.mark.django_db
@pytest.mark.parametrize("declared", [True, False], ids=["declared", "undeclared"])
@pytest.mark.parametrize("target", ["open", "secret"])
@pytest.mark.parametrize("carrier", ["generated", "model-choice", "excluding-choice"])
def test_to_field_raw_pk_and_model_choice_carriers_do_not_compare_the_stored_name(
    carrier: str,
    target: str,
    record_compiled_sql: RecordCompiledSql,
    *,
    declared: bool,
) -> None:
    """Actual Genre PK input selects open, never the Profile whose stored Genre name equals that number."""
    world = _world()
    schema = _profile_schema(declared=declared)
    leaf = {
        "generated": "favorite_genre",
        "model-choice": "favored",
        "excluding-choice": "not_favored",
    }[carrier]
    if carrier == "excluding-choice":
        names = (
            ["secret", "none", "decoy"]
            if target == "open"
            else [
                "open",
                "secret",
                "none",
                "decoy",
            ]
        )
    else:
        names = ["open"] if target == "open" else []
    sqls = record_compiled_sql()
    where = _where(schema, (leaf, "exact"), saved_pk(world.genres[target]))
    assert _post(schema, where, "postalCode") == _profiles(world, *names)
    _assert_profile_request_sql(sqls)


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["open", "secret"])
def test_reverse_to_field_name_carrier_scopes_targets_without_scoping_plain_roots(
    name: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The supported name carrier compares Genre.name while hidden roots remain separately observable."""
    world = _world()

    class GenreChild(FilterSet):
        class Meta:
            model = models.Genre
            fields = {"name": ["exact"]}

    class GenreParent(FilterSet):
        fans_favorite = RelatedFilter(GenreChild, field_name="favoring_profiles__favorite_genre")
        favored_as = ModelChoiceFilter(
            field_name="favoring_profiles__favorite_genre",
            queryset=models.Genre.objects.all(),
            to_field_name="name",
        )

        class Meta:
            model = models.Genre
            fields = {"name": ["exact"]}

    class PrimaryGenre(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)
            filterset_class = GenreChild
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

    class BoundGenre(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("name",)
            filterset_class = GenreParent
            primary = False

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.Genre],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.Genre]:
            del info
            return queryset.exclude(name__startswith="secret")

    class PlainGenre(DjangoType):
        class Meta:
            model = models.Genre
            fields = ("id", "name")
            primary = False

    class PlainProfile(DjangoType):
        class Meta:
            model = models.PatronProfile
            fields = ("postal_code",)

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: Annotated[
                FilterInput[GenreParent] | None,
                strawberry.argument(name="filter"),
            ] = None,
        ) -> django_models.QuerySet[models.Genre]:
            queryset = models.Genre.objects.order_by("pk")
            return queryset if where is None else GenreParent.apply_sync(where, queryset, info)

        rows: django_models.QuerySet[models.Genre] = strawberry.field(
            resolver=_rows,
            graphql_type=list[PlainGenre],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        types=(PrimaryGenre, BoundGenre, PlainProfile),
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )

    def expected(names: Sequence[str]) -> JSONObject:
        return {
            "data": {
                "rows": [
                    {"id": saved_pk(world.genres[key]), "name": world.genres[key].name}
                    for key in names
                ],
            },
        }

    # Plain consumer roots include the hidden Genre and numeric-name decoy.
    # Neither can vanish as an accidental substitute for target visibility.
    assert _post(schema, {}, "id name") == expected(["open", "secret", "decoy"])
    open_where = _where(schema, ("favored_as", "exact"), world.genres["open"].name)
    assert _post(schema, open_where, "id name") == expected(["open"])
    sqls = record_compiled_sql()
    where = _where(schema, ("favored_as", "exact"), world.genres[name].name)
    assert _post(schema, where, "id name") == expected(["open"] if name == "open" else [])
    # ModelChoiceField.clean performs its own Genre lookup. The explicit
    # ordered consumer query is the root scan, separate from that preparation.
    roots = [
        sql for sql in _root_sql(sqls, models.Genre) if 'ORDER BY "library_genre"."id"' in sql
    ]
    assert len(roots) == 1, sqls
    assert "EXISTS" in roots[0].upper(), roots
    assert '"favorite_genre_id"' in roots[0], roots
    assert "DISTINCT" not in roots[0].upper(), roots
