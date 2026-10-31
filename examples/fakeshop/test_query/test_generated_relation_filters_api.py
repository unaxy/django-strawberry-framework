"""Native HTTP generated relation filters over Relay keys, ForeignObject and to_field links.

The shipped Book filter declares Shelf as a RelatedFilter and publishes Shelf as
non-Relay. These holders preserve the distinct generated forward-GlobalID leaf.
The existing Lnk models supply scalar-carried ForeignObject links onto a slug,
two non-PK columns, or a primary key, including ordinary non-Relay targets.

Genre/Profile holders distinguish direct generated traversal from a declared
RelatedFilter branch. Genre.name is the stored favorite_genre key, while Relay
IDs carry Genre.pk. One genre is named as another's PK to make a raw stored-key
comparison return the wrong row. Published input names come from the executing
schema's Strawberry definitions and configured NameConverter.
"""

from collections.abc import Mapping, Sequence
from functools import wraps
from typing import TypeVar

import pytest
import strawberry
from apps.library import models as library_models
from django.db import connection, models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql import GraphQLInputObjectType, get_named_type
from graphql_client import JSONObject, graphql_payload, json_at, json_list, json_str
from strategy_schemas import make_django_type
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.typing import (
    graphql_fields,
    graphql_input_fields,
    graphql_type_of,
)
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk
from tests.optimizer import _link_models

pytestmark = pytest.mark.usefixtures("private_registry")
_ModelT = TypeVar("_ModelT", bound=models.Model)
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-generated-relations/", _graphql_view)]


def _post(schema: DjangoSchema, document: str, *, variables: Mapping[str, object]) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-generated-relations/",
            )
    finally:
        _CURRENT["schema"] = None


def _schema(
    node_type: type[DjangoType],
    model: type[models.Model],
    *,
    extra_types: Sequence[type[DjangoType]] = (),
) -> DjangoSchema:
    def resolve_rows(
        _root: object,
        _info: strawberry.Info[object, object],
    ) -> models.QuerySet[models.Model]:
        return model._default_manager.order_by("pk")

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(node_type, resolver=resolve_rows)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=extra_types,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _filter_input(schema: DjangoSchema) -> GraphQLInputObjectType:
    query = schema._schema.query_type
    assert query is not None
    named = get_named_type(graphql_type_of(graphql_fields(query)["rows"].args["filter"]))
    assert isinstance(named, GraphQLInputObjectType)
    return named


def _published_path(schema: DjangoSchema, python_path: Sequence[str]) -> tuple[str, ...]:
    """Ask Strawberry's definitions/converter for every actual input field spelling."""
    current = _filter_input(schema)
    published: list[str] = []
    for index, python_name in enumerate(python_path):
        definition = schema.get_type_by_name(current.name)
        assert isinstance(definition, StrawberryObjectDefinition)
        field = next(field for field in definition.fields if field.python_name == python_name)
        wire_name = schema.config.name_converter.from_field(field)
        published.append(wire_name)
        named = get_named_type(graphql_type_of(graphql_input_fields(current)[wire_name]))
        if index < len(python_path) - 1:
            assert isinstance(named, GraphQLInputObjectType)
            current = named
    return tuple(published)


def _where(schema: DjangoSchema, python_path: Sequence[str], value: object) -> JSONObject:
    names = _published_path(schema, python_path)
    assert names
    bag: JSONObject = {names[-1]: value}
    for wire_name in reversed(names[:-1]):
        bag = {wire_name: bag}
    return bag


def _document(schema: DjangoSchema, selection: str) -> str:
    return (
        f"query($where: {_filter_input(schema).name}!) {{ rows(filter: $where) {{ "
        f"edges {{ node {{ {selection} }} }} }} }}"
    )


def _root_sql(captured: CaptureQueriesContext, table: str) -> list[str]:
    return [
        query["sql"]
        for query in captured.captured_queries
        if query["sql"].lstrip().upper().startswith("SELECT ")
        and " FROM " in query["sql"]
        and query["sql"].split(" FROM ", 1)[1].startswith(f'"{table}"')
    ]


def _filter_class(name: str, model: type[models.Model], fields: object) -> type[FilterSet]:
    declared = type(
        name,
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": model, "fields": fields})},
    )
    assert issubclass(declared, FilterSet)
    return declared


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        "union",
        "empty",
        "missing",
        "mixed",
        "malformed-index",
    ],
)
def test_generated_forward_fk_membership_decodes_the_whole_requested_list(case: str) -> None:
    """A generated Relay Shelf membership unions whole IDs, while empty/missing inputs stay restrictive."""
    branch = library_models.Branch.objects.create(name="Forward Membership")
    shelves = [
        library_models.Shelf.objects.create(code=code, branch=branch) for code in ("A", "B", "C")
    ]
    for shelf, title in zip(shelves, ("book-a", "book-b", "book-c"), strict=True):
        library_models.Book.objects.create(title=title, shelf=shelf)
    absent = library_models.Shelf.objects.create(code="absent", branch=branch)
    shelf_type = make_django_type("GeneratedShelfNode", library_models.Shelf, ("id", "code"))
    filters = _filter_class("GeneratedBookMembership", library_models.Book, {"shelf": ["in"]})
    book_type = make_django_type(
        "GeneratedBookNode",
        library_models.Book,
        ("id", "title"),
        meta_extra={"filterset_class": filters},
    )
    schema = _schema(book_type, library_models.Book)
    first = global_id_for(shelf_type, shelves[0].pk)
    second = global_id_for(shelf_type, shelves[1].pk)
    missing = global_id_for(shelf_type, absent.pk)
    absent.delete()
    values: dict[str, list[str]] = {
        "union": [first, second],
        "empty": [],
        "missing": [missing],
        "mixed": [first, missing],
        "malformed-index": [first, "not-a-globalid"],
    }
    expected = {
        "union": ["book-a", "book-b"],
        "empty": [],
        "missing": [],
        "mixed": ["book-a"],
    }
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            _document(schema, "title"),
            variables={
                "where": _where(schema, ("shelf", "in_"), values[case]),
            },
        )
    if case == "malformed-index":
        assert payload["data"] is None
        assert len(json_list(payload, "errors")) == 1
        assert json_at(payload, "errors", 0, "path") == ["rows"]
        assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_INVALID"
        assert json_str(payload, "errors", 0, "message") == (
            "Invalid GlobalID: 'not-a-globalid' is not a valid GlobalID (malformed "
            "base64 or not a 'type_name:node_id' shape) at index 1."
        )
        assert _root_sql(captured, "library_book") == []
    else:
        assert payload == {
            "data": {"rows": {"edges": [{"node": {"title": title}} for title in expected[case]]}},
        }
        if expected[case]:
            assert len(_root_sql(captured, "library_book")) == 1


def _foreign_object_schema(
    child_model: type[models.Model],
    *,
    node: bool,
    all_fields: bool,
) -> tuple[DjangoSchema, type[DjangoType]]:
    parent_type = make_django_type(
        "GeneratedLinkParent",
        _link_models.LnkParent,
        ("id", "label"),
        node=node,
    )
    filters = _filter_class(
        "GeneratedLinkFilter",
        child_model,
        "__all__" if all_fields else {"parent": ["exact"]},
    )
    child_type = make_django_type(
        "GeneratedLinkChild",
        child_model,
        ("id", "name", "parent"),
        meta_extra={"filterset_class": filters},
    )
    return _schema(child_type, child_model), parent_type


def _add_partial_pair_rows() -> None:
    """A same-tenant/different-code row and an orphan catch either missing join carrier."""
    _link_models.LnkPairChild.objects.create(p_tenant=1, p_code="B", name="code-only")
    _link_models.LnkPairChild.objects.create(p_tenant=2, p_code="B", name="partial-orphan")


def _assert_pair_carriers(statements: list[str]) -> None:
    assert len(statements) == 1, statements
    sql = statements[0]
    join = sql[sql.index(" JOIN ") :]
    assert '"p_tenant"' in join, sql
    assert '"tenant"' in join, sql
    assert '"p_code"' in join, sql
    assert '"code"' in join, sql


def _foreign_object_request(
    child_model: type[models.Model],
    *,
    node: bool,
    all_fields: bool,
    target: str,
) -> None:
    with _link_models.link_fixture_tables(connection):
        _add_partial_pair_rows()
        schema, parent_type = _foreign_object_schema(child_model, node=node, all_fields=all_fields)
        gone = _link_models.LnkParent.objects.create(
            tenant=9,
            code="gone",
            slug="gone",
            label="gone",
        )
        parent = gone if target == "missing" else _link_models.LnkParent.objects.get(label=target)
        value = global_id_for(parent_type, saved_pk(parent)) if node else saved_pk(parent)
        if target == "missing":
            gone.delete()
        names = {"pa": ["a1", "a2", "a3"], "pb": ["b1"], "missing": []}[target]
        with CaptureQueriesContext(connection) as captured:
            payload = _post(
                schema,
                _document(schema, "name parent { label }"),
                variables={
                    "where": _where(schema, ("parent", "exact"), value),
                },
            )
        assert payload == {
            "data": {
                "rows": {
                    "edges": [
                        {"node": {"name": name, "parent": {"label": target}}} for name in names
                    ],
                },
            },
        }
        statements = _root_sql(captured, child_model._meta.db_table)
        assert len(statements) == 1, captured.captured_queries
        if child_model is _link_models.LnkPairChild:
            _assert_pair_carriers(statements)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("target", ["pa", "pb", "missing"])
@pytest.mark.parametrize(
    "child_model",
    [_link_models.LnkSlugObjectChild, _link_models.LnkPairChild, _link_models.LnkColumnChild],
    ids=["slug-target", "pair-target", "pk-target"],
)
def test_generated_foreign_object_globalid_filters_decode_the_parent_primary_key(
    child_model: type[models.Model],
    target: str,
) -> None:
    """Each ForeignObject shape selects the encoded parent, excluding other and partial carriers."""
    _foreign_object_request(child_model, node=True, all_fields=False, target=target)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("node", [True, False], ids=["relay-target", "plain-target"])
@pytest.mark.parametrize("target", ["pa", "pb", "missing"])
def test_all_fields_pair_filter_uses_both_carriers_for_relay_and_plain_targets(
    target: str,
    *,
    node: bool,
) -> None:
    """The __all__ parent.exact leaf keeps both carriers for GlobalIDs and raw parent keys."""
    _foreign_object_request(_link_models.LnkPairChild, node=node, all_fields=True, target=target)


def _profile(genre: library_models.Genre, code: str) -> None:
    patron = library_models.Patron.objects.create(name="Patron " + code)
    library_models.PatronProfile.objects.create(
        patron=patron,
        postal_code=code,
        favorite_genre=genre,
    )


def _to_field_rows() -> tuple[library_models.Genre, library_models.Genre, library_models.Genre]:
    first = library_models.Genre.objects.create(name="C1")
    decoy = library_models.Genre.objects.create(name=str(first.pk))
    library_models.Genre.objects.create(name="C3")
    unrelated = library_models.Genre.objects.create(name="C4")
    _profile(first, "one")
    _profile(decoy, "two")
    _profile(unrelated, "unrelated")
    assert first.name != str(first.pk)
    gone = library_models.Genre.objects.create(name="gone")
    return first, decoy, gone


def _to_field_schema(mode: str) -> tuple[DjangoSchema, type[DjangoType]]:
    class ProfileFilter(FilterSet):
        class Meta:
            model = library_models.PatronProfile
            fields = {"favorite_genre": ["exact", "in"]}

    genre_filters: type[FilterSet]
    if mode == "generated":

        class GeneratedGenreFilter(FilterSet):
            class Meta:
                model = library_models.Genre
                fields = {"favoring_profiles__favorite_genre": ["exact", "in"]}

        genre_filters = GeneratedGenreFilter
    elif mode == "postal":

        class PostalGenreFilter(FilterSet):
            class Meta:
                model = library_models.Genre
                fields = {"favoring_profiles__postal_code": ["icontains"]}

        genre_filters = PostalGenreFilter
    else:

        class DeclaredGenreFilter(FilterSet):
            favoring_profiles = RelatedFilter(ProfileFilter)

            class Meta:
                model = library_models.Genre
                fields = {"name": ["exact"]}

        if mode == "direct-rebased":

            class RebasedGenreFilter(DeclaredGenreFilter):
                @override
                def filter_queryset(
                    self,
                    queryset: models.QuerySet[_ModelT],
                ) -> models.QuerySet[_ModelT]:
                    # This supported consumer override applies the copied filter to
                    # the outer Genre query, so its complete rebased path is exercised.
                    cleaned: dict[str, object] = self.form.cleaned_data
                    return self.filters["favoring_profiles__favorite_genre"].filter(
                        queryset,
                        cleaned.get("favoring_profiles__favorite_genre"),
                    )

            genre_filters = RebasedGenreFilter
        else:
            genre_filters = DeclaredGenreFilter

    profile_type = make_django_type(
        "GeneratedProfile",
        library_models.PatronProfile,
        ("postal_code", "favorite_genre"),
        node=False,
        meta_extra={"filterset_class": ProfileFilter},
    )
    genre_type = make_django_type(
        "GeneratedGenre",
        library_models.Genre,
        ("id", "name"),
        meta_extra={"filterset_class": genre_filters},
    )
    return _schema(genre_type, library_models.Genre, extra_types=(profile_type,)), genre_type


def _to_field_inputs(
    schema: DjangoSchema,
    genre_type: type[DjangoType],
    first: library_models.Genre,
    second: library_models.Genre,
    gone: library_models.Genre,
    case: str,
    *,
    nested: bool,
) -> tuple[JSONObject, list[library_models.Genre]]:
    encoded_first = global_id_for(genre_type, first.pk)
    encoded_second = global_id_for(genre_type, second.pk)
    missing = global_id_for(genre_type, gone.pk)
    gone.delete()
    lookup = "exact" if case in {"exact", "missing"} else "in_"
    values: dict[str, object] = {
        "exact": encoded_first,
        "membership": [encoded_first, encoded_second],
        "empty": [],
        "missing": missing,
        "mixed": [encoded_first, missing],
    }
    expected = {
        "exact": [first],
        "membership": [first, second],
        "empty": [],
        "missing": [],
        "mixed": [first],
    }
    path = (
        ("favoring_profiles", "favorite_genre", lookup)
        if nested
        else ("favoring_profiles_favorite_genre", lookup)
    )
    return _where(schema, path, values[case]), expected[case]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        "exact",
        "membership",
        "empty",
        "missing",
        "mixed",
    ],
)
def test_generated_to_field_traversal_uses_pk_qualified_correlated_predicates(case: str) -> None:
    """Decode Genre.pk across the stored Genre.name link inside one row-preserving predicate."""
    first, second, gone = _to_field_rows()
    schema, genre_type = _to_field_schema("generated")
    where, expected = _to_field_inputs(schema, genre_type, first, second, gone, case, nested=False)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, _document(schema, "id name"), variables={"where": where})
    assert payload == {
        "data": {
            "rows": {
                "edges": [
                    {"node": {"id": global_id_for(genre_type, genre.pk), "name": genre.name}}
                    for genre in expected
                ],
            },
        },
    }
    if expected:
        sql = _root_sql(captured, "library_genre")
        assert len(sql) == 1, captured.captured_queries
        # These hook-free, undeclared hops stay on the generated candidate adapter.
        # Registration alone does not add the scoped branch visibility pipeline.
        assert sql[0].upper().count("EXISTS") == 1, sql
        assert "DISTINCT" not in sql[0].upper(), sql
        predicate = sql[0].split(" WHERE ", 1)[1]
        assert '"favorite_genre_id"' in predicate, sql
        assert '"name"' in predicate, sql
        assert '"library_genre"."id"' in predicate, sql
        outer = sql[0].split(" WHERE ", 1)[0]
        assert " JOIN " not in outer.upper(), sql


@pytest.mark.django_db
@pytest.mark.parametrize("nested", [False, True], ids=["flat-expanded", "nested-branch"])
@pytest.mark.parametrize("case", ["exact", "membership", "empty"])
def test_declared_to_field_branch_keeps_the_child_primary_key_comparison(
    case: str,
    *,
    nested: bool,
) -> None:
    """The declared RelatedFilter runs its child leaf with the same decoded-pk verdict in both spellings."""
    first, second, gone = _to_field_rows()
    schema, genre_type = _to_field_schema("declared")
    where, expected = _to_field_inputs(
        schema,
        genre_type,
        first,
        second,
        gone,
        case,
        nested=nested,
    )
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, _document(schema, "id name"), variables={"where": where})
    assert payload == {
        "data": {
            "rows": {
                "edges": [
                    {"node": {"id": global_id_for(genre_type, genre.pk), "name": genre.name}}
                    for genre in expected
                ],
            },
        },
    }
    if expected:
        assert len(_root_sql(captured, "library_genre")) == 1


@pytest.mark.django_db
def test_generated_reverse_to_field_text_leaf_preserves_each_matching_root_once() -> None:
    """Two matching profiles keep one Genre, with one EXISTS joined on the stored non-PK name."""
    matched = library_models.Genre.objects.create(name="T1")
    decoy = library_models.Genre.objects.create(name=str(matched.pk))
    library_models.Genre.objects.create(name="Empty")
    _profile(matched, "cardio one")
    _profile(matched, "cardio two")
    _profile(decoy, "neuro")
    schema, genre_type = _to_field_schema("postal")
    where = _where(schema, ("favoring_profiles_postal_code", "i_contains"), "cardio")
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, _document(schema, "id name"), variables={"where": where})
    assert payload == {
        "data": {
            "rows": {
                "edges": [
                    {
                        "node": {"id": global_id_for(genre_type, matched.pk), "name": "T1"},
                    },
                ],
            },
        },
    }
    sql = _root_sql(captured, "library_genre")
    assert len(sql) == 1, captured.captured_queries
    assert sql[0].upper().count("EXISTS") == 1, sql
    assert "DISTINCT" not in sql[0].upper(), sql
    predicate = sql[0].split(" WHERE ", 1)[1]
    assert '"favorite_genre_id"' in predicate, sql
    assert '"name"' in predicate, sql
    assert '"library_genre"."id"' in predicate, sql
    assert " JOIN " not in sql[0].split(" WHERE ", 1)[0].upper(), sql


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["exact", "missing"])
def test_a_consumer_applies_the_expanded_globalid_leaf_to_its_rebased_outer_model(
    case: str,
) -> None:
    """A normal filter_queryset override uses the full rebased path while decoding the target PK.

    This consumer owns its loop, so it calls the public copied leaf directly
    over Genre rows. The standard declared branch test instead rebinds its
    terminal to Profile rows; both supported usages keep their own verdict.
    """
    first, second, gone = _to_field_rows()
    schema, genre_type = _to_field_schema("direct-rebased")
    where, expected = _to_field_inputs(
        schema,
        genre_type,
        first,
        second,
        gone,
        case,
        nested=False,
    )
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, _document(schema, "id name"), variables={"where": where})
    assert payload == {
        "data": {
            "rows": {
                "edges": [
                    {"node": {"id": global_id_for(genre_type, genre.pk), "name": genre.name}}
                    for genre in expected
                ],
            },
        },
    }
    assert len(_root_sql(captured, "library_genre")) == 1
