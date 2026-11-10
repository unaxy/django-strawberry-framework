"""GlobalID filters accept only the target's configured emitted identifier spellings.

These native Relay types use real Meta strategies and emit identifiers over HTTP.
The JSON consumer applies its associated FilterSet; a typed GlobalID consumer uses
its bound public filter primitive to preserve Strawberry's already-decoded value.
A GlobalID filter into a model no type exposes compares the node id on the relation's
key, through a ``GenericRelation`` too; one on a ``GenericForeignKey`` is refused when
its set publishes its filters, served or applied unbound, unless a ``method`` filters it.
A relation key whose hops re-enter its own set's table takes the id the type registered
for the relation's target mints, under its published name, whichever type the set or the
walk's target rows answer for, and so does a consumer leaf ending on the re-entry's
primary key past an undeclared hop (``shelf__books__id``), served, applied sync or async,
and on the raw form. An id only a ``get_queryset`` annotation holds compares only over
rows its type answers for, and is refused over rows another type answers for.
"""

import asyncio
import functools
import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import wraps
from typing import NamedTuple

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db.models import CharField, Model, QuerySet, Value
from django.db.models.functions import Cast, Concat
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import Filter
from graphql import GraphQLError
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    json_str,
    response_json,
)
from strategy_schemas import make_django_type
from strawberry import relay
from strawberry.scalars import JSON
from strawberry.schema.name_converter import NameConverter
from strawberry.types import Info
from strawberry.types.base import StrawberryList, StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterSet,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    RelatedFilter,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import is_queryset, require, require_instance
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_URL = "/graphql-globalid-strategies/"
_ASYNC_URL = "/graphql-globalid-strategies-async/"


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-globalid-strategies/", _view),
    path("graphql-globalid-strategies-async/", _async_view),
]


def _branches() -> None:
    models.Branch.objects.create(name="Target", city="Boston")
    models.Branch.objects.create(name="Sibling", city="Boston")


def _schema(strategy: str | None) -> DjangoSchema:
    registry.clear()

    class BranchIdentityFilter(FilterSet):
        chosen = GlobalIDFilter(field_name="id")

        class Meta:
            model = models.Branch
            fields = []

    class BranchStrategyNode(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("id", "name")
            if strategy is not None:
                interfaces = (relay.Node,)
                globalid_strategy = strategy
            filterset_class = BranchIdentityFilter

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: Info[object, object],
            where: JSON | None = None,
        ) -> QuerySet[models.Branch]:
            rows = models.Branch.objects.order_by("pk")
            return rows if where is None else BranchIdentityFilter.apply_sync(where, rows, info)

        def _decoded(self, value: relay.GlobalID) -> QuerySet[models.Branch]:
            rows = models.Branch.objects.order_by("pk")
            filters = BranchIdentityFilter(queryset=rows)
            return filters.filters["chosen"].filter(rows, value)

        rows: QuerySet[models.Branch] = strawberry.field(
            resolver=_rows,
            graphql_type=StrawberryList(BranchStrategyNode),
        )
        decoded: QuerySet[models.Branch] = strawberry.field(
            resolver=_decoded,
            graphql_type=StrawberryList(BranchStrategyNode),
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _post(
    schema: DjangoSchema,
    query: str,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(query, variables=variables, url=_URL)
    finally:
        _CURRENT["schema"] = None


def _emitted_id(schema: DjangoSchema) -> str:
    payload = _post(schema, "{ rows { id name } }")
    assert "errors" not in payload, payload
    assert json_at(payload, "data", "rows", 0, "name") == "Target"
    assert json_at(payload, "data", "rows", 1, "name") == "Sibling"
    rows = json_list(json_object(payload, "data"), "rows")
    assert len(rows) == 2, payload
    value = json_at(payload, "data", "rows", 0, "id")
    assert isinstance(value, str), payload
    return value


def _filter(schema: DjangoSchema, value: object) -> JSONObject:
    return _post(
        schema,
        "query($where: JSON!) { rows(where: $where) { name } }",
        {"where": {"chosen": value}},
    )


def _accepts(payload: JSONObject, field: str = "rows") -> None:
    assert "errors" not in payload, payload
    assert payload["data"] == {field: [{"name": "Target"}]}, payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("emitter", "target", "accepted"),
    [
        pytest.param("type", "model", False, id="model-refuses-type-slot"),
        pytest.param("model", "type", False, id="type-refuses-model-slot"),
        pytest.param("model", "type+model", True, id="combined-accepts-model-slot"),
        pytest.param("type", "type+model", True, id="combined-accepts-type-slot"),
    ],
)
def test_globalid_filter_strategy_accepts_only_its_emitted_spellings(
    emitter: str,
    target: str,
    *,
    accepted: bool,
) -> None:
    """The same named Relay target accepts exactly its configured model/type spellings."""
    _branches()
    alternate_id = _emitted_id(_schema(emitter))
    receiving_schema = _schema(target)
    own_id = _emitted_id(receiving_schema)
    _accepts(_filter(receiving_schema, own_id))

    payload = _filter(receiving_schema, alternate_id)
    if accepted:
        _accepts(payload)
    else:
        assert payload["data"] is None, payload
        message = json_at(payload, "errors", 0, "message")
        assert isinstance(message, str), payload
        assert "GlobalID type mismatch" in message, payload


@pytest.mark.django_db
def test_global_id_for_mints_the_type_plus_model_id_the_type_emits() -> None:
    """Under ``globalid_strategy="type+model"`` the helper mints exactly the id the type emits.

    The emitted payload slot is the model label, not the type name.
    """
    _branches()
    schema = _schema("type+model")
    emitted = _emitted_id(schema)
    node_type = registry.get(models.Branch)
    assert node_type is not None
    target = models.Branch.objects.get(name="Target")
    assert emitted == global_id_for(node_type, saved_pk(target))
    assert relay.GlobalID.from_id(emitted).type_name == "library.branch"


@pytest.mark.django_db
def test_a_bound_globalid_filter_accepts_a_typed_globalid_argument() -> None:
    """A typed emitted ID works without apply context at its associated public filter."""
    _branches()
    schema = _schema("type")
    value = _emitted_id(schema)

    payload = _post(
        schema,
        "query($value: ID!) { decoded(value: $value) { name } }",
        {"value": value},
    )

    _accepts(payload, "decoded")


@pytest.mark.django_db
def test_default_globalid_form_field_refuses_a_json_integer_before_reading_rows(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The default noncoercive form field preserves a malformed JSON integer for refusal."""
    _branches()
    schema = _schema("model")
    _accepts(_filter(schema, _emitted_id(schema)))
    statements = record_compiled_sql(models.Branch._meta.db_table)

    payload = _filter(schema, 42)

    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_INVALID", payload
    assert statements == []


@pytest.mark.django_db
def test_a_nonrelay_target_refuses_a_globalid_with_a_typed_error(
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An associated non-Relay target refuses a real ID before it reads any branch rows."""
    _branches()
    emitting_schema = _schema("model")
    value = _emitted_id(emitting_schema)
    _accepts(_filter(emitting_schema, value))
    plain_schema = _schema(None)
    unfiltered = _post(plain_schema, "{ rows { name } }")
    assert "errors" not in unfiltered, unfiltered
    assert unfiltered["data"] == {"rows": [{"name": "Target"}, {"name": "Sibling"}]}
    statements = record_compiled_sql(models.Branch._meta.db_table)

    payload = _filter(plain_schema, value)

    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_UNVALIDATABLE", payload
    message = json_at(payload, "errors", 0, "message")
    assert isinstance(message, str), payload
    assert "no recorded globalid strategy" in message, payload
    assert statements == []


def _untyped_target_schema() -> DjangoSchema:
    """A Relay ``Shelf`` type filtering by a GlobalID of its ``branch``, which no type exposes."""
    registry.clear()

    class ShelfBranchFilter(FilterSet):
        branch_id = GlobalIDFilter(field_name="branch")

        class Meta:
            model = models.Shelf
            fields = []

    class UntypedBranchShelfNode(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("id", "code")
            interfaces = (relay.Node,)
            filterset_class = ShelfBranchFilter

    assert registry.get(models.Branch) is None

    @strawberry.type
    class Query:
        def _shelves(
            self,
            info: Info[object, object],
            where: JSON | None = None,
        ) -> QuerySet[models.Shelf]:
            rows = models.Shelf.objects.order_by("pk")
            return rows if where is None else ShelfBranchFilter.apply_sync(where, rows, info)

        shelves: QuerySet[models.Shelf] = strawberry.field(
            resolver=_shelves,
            graphql_type=StrawberryList(UntypedBranchShelfNode),
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.django_db
def test_a_globalid_filter_into_a_model_no_type_exposes_compares_the_node_id_alone() -> None:
    """A GlobalID leaf whose relation ends on an untyped model has no type to check its name by.

    ``Shelf.branch`` leads to ``Branch``, which no ``DjangoType`` exposes, so the walk
    from the Relay owner resolves no target definition: the schema builds, any type name
    is accepted, and the node id is compared on the branch key, a node id that key
    cannot hold answering ``GLOBALID_INVALID``.
    """
    target = models.Branch.objects.create(name="Target", city="Boston")
    sibling = models.Branch.objects.create(name="Sibling", city="Boston")
    models.Shelf.objects.create(code="T-1", branch=target)
    models.Shelf.objects.create(code="S-1", branch=sibling)
    schema = _untyped_target_schema()
    query = "query($where: JSON!) { shelves(where: $where) { code } }"

    for type_name in ("library.branch", "Unregistered"):
        value = str(relay.GlobalID(type_name=type_name, node_id=str(target.pk)))
        payload = _post(schema, query, {"where": {"branch_id": value}})
        assert payload == {"data": {"shelves": [{"code": "T-1"}]}}, payload

    malformed = str(relay.GlobalID(type_name="library.branch", node_id="abc"))
    payload = _post(schema, query, {"where": {"branch_id": malformed}})
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_INVALID", payload


_GlobalIDFilterClass = type[GlobalIDFilter | GlobalIDMultipleChoiceFilter]


def _tagged_object_filter(filter_class: _GlobalIDFilterClass) -> type[FilterSet]:
    """A set filtering ``TaggedItem`` rows by a GlobalID of its ``GenericForeignKey``."""

    class TaggedObjectFilter(FilterSet):
        tagged = filter_class(field_name="content_object")

        class Meta:
            model = models.TaggedItem
            fields = []

    return TaggedObjectFilter


def _tagged_item_schema(filterset: type[FilterSet], *, served: bool) -> DjangoSchema:
    """``TaggedItem`` rows, ``filterset`` served on their type or applied unbound."""
    registry.clear()

    class TaggedObjectNode(DjangoType):
        class Meta:
            model = models.TaggedItem
            fields = ("id", "tag")
            interfaces = (relay.Node,)
            if served:
                filterset_class = filterset

    @strawberry.type
    class Query:
        def _tags(
            self,
            info: Info[object, object],
            where: JSON | None = None,
        ) -> QuerySet[models.TaggedItem]:
            rows = models.TaggedItem.objects.order_by("pk")
            return rows if where is None else filterset.apply_sync(where, rows, info)

        tags: QuerySet[models.TaggedItem] = strawberry.field(
            resolver=_tags,
            graphql_type=StrawberryList(TaggedObjectNode),
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _generic_foreign_key_refusal(filter_class: _GlobalIDFilterClass) -> str:
    return (
        f"FilterSet _tagged_object_filter.<locals>.TaggedObjectFilter: {filter_class.__name__} "
        "'tagged' has field_name 'content_object', which names TaggedItem.content_object, a "
        "GenericForeignKey: Django filters no queryset through it"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("filter_class", [GlobalIDFilter, GlobalIDMultipleChoiceFilter])
def test_a_globalid_filter_on_a_generic_foreign_key_is_refused_when_the_schema_builds(
    filter_class: _GlobalIDFilterClass,
) -> None:
    """A ``GenericForeignKey`` stores no related row's identity a node id could be compared on.

    Django filters no queryset through one, so a GlobalID filter declared on it would
    answer every request with the ``FieldError`` its query raises. Serving the set
    refuses the declaration naming the set, the filter and the field.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        _ = _tagged_item_schema(_tagged_object_filter(filter_class), served=True)
    assert str(exc_info.value).startswith(_generic_foreign_key_refusal(filter_class)), exc_info


@pytest.mark.django_db
def test_an_unserved_globalid_filter_on_a_generic_foreign_key_is_refused_at_first_use(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A set no type serves publishes its filters at its first use: the same refusal, logged.

    The request answers the masked error and the server log carries the
    ``ConfigurationError``, never a ``FieldError`` from the query.
    """
    branch = models.Branch.objects.create(name="Target", city="Boston")
    _ = models.TaggedItem.objects.create(content_object=branch, tag="t")
    schema = _tagged_item_schema(_tagged_object_filter(GlobalIDFilter), served=False)
    unfiltered = _post(schema, "{ tags { tag } }")
    assert unfiltered == {"data": {"tags": [{"tag": "t"}]}}, unfiltered
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    value = str(relay.GlobalID(type_name="BranchNode", node_id=str(branch.pk)))

    payload = _post(
        schema,
        "query($where: JSON!) { tags(where: $where) { tag } }",
        {"where": {"tagged": value}},
    )

    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "message") == "An unexpected error occurred.", payload
    records = [
        record
        for record in caplog.records
        if record.name == "django_strawberry_framework" and record.exc_info is not None
    ]
    assert len(records) == 1, caplog.records
    exc_info = records[0].exc_info
    assert exc_info is not None
    assert type(exc_info[1]) is ConfigurationError, exc_info[1]
    assert str(exc_info[1]).startswith(_generic_foreign_key_refusal(GlobalIDFilter)), exc_info[1]


def _generic_relation_schema() -> DjangoSchema:
    """A Relay ``Branch`` type filtering by a GlobalID of one of its ``tags``.

    ``Branch.tags`` is a ``GenericRelation`` (the reverse of ``TaggedItem.content_object``)
    and no type exposes ``TaggedItem``, so the node id is compared on the tag's key.
    """
    registry.clear()

    class BranchTagFilter(FilterSet):
        tagged = GlobalIDFilter(field_name="tags")

        class Meta:
            model = models.Branch
            fields = []

    class TaggedBranchNode(DjangoType):
        class Meta:
            model = models.Branch
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = BranchTagFilter

    @strawberry.type
    class Query:
        def _branches(
            self,
            info: Info[object, object],
            where: JSON | None = None,
        ) -> QuerySet[models.Branch]:
            rows = models.Branch.objects.order_by("pk")
            return rows if where is None else BranchTagFilter.apply_sync(where, rows, info)

        branches: QuerySet[models.Branch] = strawberry.field(
            resolver=_branches,
            graphql_type=StrawberryList(TaggedBranchNode),
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


@pytest.mark.django_db
def test_a_globalid_filter_through_a_generic_relation_compares_the_tag_key() -> None:
    """The reverse of a ``GenericForeignKey`` is a relation Django joins, so it stays filterable.

    A ``TaggedItem`` node id keeps the branch that tag is attached to; a node id the
    tag's key cannot hold answers ``GLOBALID_INVALID``.
    """
    target = models.Branch.objects.create(name="Target", city="Boston")
    sibling = models.Branch.objects.create(name="Sibling", city="Boston")
    tag = models.TaggedItem.objects.create(content_object=target, tag="t")
    models.TaggedItem.objects.create(content_object=sibling, tag="s")
    schema = _generic_relation_schema()
    query = "query($where: JSON!) { branches(where: $where) { name } }"

    value = str(relay.GlobalID(type_name="library.taggeditem", node_id=str(tag.pk)))
    payload = _post(schema, query, {"where": {"tagged": value}})
    assert payload == {"data": {"branches": [{"name": "Target"}]}}, payload

    malformed = str(relay.GlobalID(type_name="library.taggeditem", node_id="abc"))
    payload = _post(schema, query, {"where": {"tagged": malformed}})
    assert payload["data"] is None, payload
    assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_INVALID", payload


def _tagged_object_method_filter() -> type[FilterSet]:
    """A set whose GlobalID filter on the ``GenericForeignKey`` filters through a ``method``."""

    class TaggedObjectMethodFilter(FilterSet):
        tagged = GlobalIDFilter(field_name="content_object", method="by_target")

        class Meta:
            model = models.TaggedItem
            fields = []

        def by_target(
            self,
            queryset: QuerySet[models.TaggedItem],
            name: str,
            value: str,
        ) -> QuerySet[models.TaggedItem]:
            del name
            return queryset.filter(
                content_type=ContentType.objects.get_for_model(models.Branch),
                object_id=relay.GlobalID.from_id(value).node_id,
            )

    return TaggedObjectMethodFilter


@pytest.mark.django_db
@pytest.mark.parametrize("served", [True, False], ids=["served", "unserved"])
def test_a_globalid_filter_on_a_generic_foreign_key_filters_through_its_method(
    *,
    served: bool,
) -> None:
    """A ``method`` filters as it chooses, so the refusal leaves the filter to it.

    django-filter dispatches the filter to its method, never through the relation its
    ``field_name`` names: this one keeps the tags whose content type and object id the
    node id names.
    """
    target = models.Branch.objects.create(name="Target", city="Boston")
    sibling = models.Branch.objects.create(name="Sibling", city="Boston")
    _ = models.TaggedItem.objects.create(content_object=target, tag="t")
    _ = models.TaggedItem.objects.create(content_object=sibling, tag="s")
    schema = _tagged_item_schema(_tagged_object_method_filter(), served=served)
    value = str(relay.GlobalID(type_name="BranchNode", node_id=str(target.pk)))

    payload = _post(
        schema,
        "query($where: JSON!) { tags(where: $where) { tag } }",
        {"where": {"tagged": value}},
    )

    assert payload == {"data": {"tags": [{"tag": "t"}]}}, payload


class _ApiPrefix(NameConverter):
    """Publish every output object type as ``Api<name>``; inputs keep theirs."""

    @override
    def from_object(self, object_type: StrawberryObjectDefinition) -> str:
        name = super().from_object(object_type)
        return name if object_type.is_input else f"Api{name}"


def _encode_by_name(type_cls: type[DjangoType], _model: type[Model], _root: Model) -> str:
    """A ``callable`` strategy: the type's class name, encode-only."""
    return type_cls.__name__


def _hiding(*pks: int) -> "classmethod[DjangoType, ..., QuerySet[Model]]":
    """Return a ``get_queryset`` hook scoping a type's rows to those outside ``pks``."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset.exclude(pk__in=pks)

    return classmethod(get_queryset)


#: The text the keyed worlds' ``node_key`` annotation puts before a row's key.
_KEY_PREFIX = "k"


def _keyed() -> "classmethod[DjangoType, ..., QuerySet[Model]]":
    """A ``get_queryset`` hook annotating ``node_key`` (``k<pk>``), which no column holds."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset.annotate(node_key=Concat(Value(_KEY_PREFIX), Cast("id", CharField())))

    return classmethod(get_queryset)


def _custom_typename() -> "classmethod[DjangoType, ..., str]":
    """Return a consumer ``resolve_typename``, which classifies its type ``custom``."""

    def resolve_typename(cls: type[DjangoType], _root: object, _info: object) -> str:
        return cls.__name__

    return classmethod(resolve_typename)


class _Library(NamedTuple):
    """The library rows every re-entry world reads, by name."""

    branches: dict[str, models.Branch]
    shelves: dict[str, models.Shelf]
    genres: dict[str, models.Genre]
    books: dict[str, models.Book]
    loans: dict[str, models.Loan]
    publishers: dict[str, models.Publisher]


def _library() -> _Library:
    """Two branches, three shelves, two genres, four books, three loans and three publishers.

    ``s1`` and ``s2`` stand on ``b1``, ``s3`` on ``b2``; ``s1`` and ``s2`` also list ``b2``
    as an alternate branch. ``bk1`` / ``bk2`` stand on ``s1``, ``bk3`` on ``s2``, ``bk4``
    on ``s3``; ``bk1`` / ``bk3`` are ``g1``, ``bk2`` / ``bk4`` ``g2``. ``bk1`` is lent
    twice, ``bk2`` once. ``h1`` prints a run co-published by ``h2``, ``h3`` one
    co-published by ``h1``.
    """
    branches = {name: models.Branch.objects.create(name=name) for name in ("b1", "b2")}
    shelves = {
        code: models.Shelf.objects.create(code=code, branch=branches[branch])
        for code, branch in (("s1", "b1"), ("s2", "b1"), ("s3", "b2"))
    }
    shelves["s1"].alt_branches.add(branches["b2"])
    shelves["s2"].alt_branches.add(branches["b2"])
    genres = {name: models.Genre.objects.create(name=name) for name in ("g1", "g2")}
    books: dict[str, models.Book] = {}
    for title, shelf, genre in (
        ("bk1", "s1", "g1"),
        ("bk2", "s1", "g2"),
        ("bk3", "s2", "g1"),
        ("bk4", "s3", "g2"),
    ):
        books[title] = models.Book.objects.create(title=title, shelf=shelves[shelf])
        books[title].genres.add(genres[genre])
    patrons = [models.Patron.objects.create(name=name) for name in ("p1", "p2")]
    loans = {
        name: models.Loan.objects.create(book=books[book], patron=patron)
        for name, book, patron in (
            ("l1", "bk1", patrons[0]),
            ("l2", "bk1", patrons[1]),
            ("l3", "bk2", patrons[0]),
        )
    }
    publishers = {
        name: models.Publisher.objects.create(name=name, house_code=name.upper())
        for name in ("h1", "h2", "h3")
    }
    edition = models.Edition.objects.create(isbn_13="9780000000001", publisher=publishers["h1"])
    for printer, co_publisher in (("h1", "h2"), ("h3", "h1")):
        printing = models.Printing.objects.create(edition=edition, publisher_2=publishers[printer])
        printing.co_publishers.add(publishers[co_publisher])
    return _Library(branches, shelves, genres, books, loans, publishers)


@dataclass(frozen=True)
class _Reentry:
    """A filter set wired to a type, whose GlobalID relation key a request walks hop by hop.

    ``filterset`` serves ``root`` (its rows' type) beside ``types`` under ``converter``;
    ``path`` is the leaf's input path (Python names, the last one the lookup), ``wire``
    its published spelling, ``listed`` whether the lookup takes a list and ``form_key``
    the raw form's key. ``accepted`` names a row as the type registered for the
    relation's target names it, which answers ``expected``; a re-entry world's
    ``refused`` names it another way, answered by ``refusal``.
    """

    filterset: type[FilterSet]
    root: type[DjangoType]
    types: tuple[type[DjangoType], ...]
    path: tuple[str, ...]
    wire: tuple[str, ...]
    form_key: str | None
    accepted: str
    expected: list[int]
    refused: str = ""
    refusal: str = ""
    listed: bool = True
    converter: NameConverter | None = None

    def value(self, global_id: str) -> str | list[str]:
        """The input value naming ``global_id``, a list where the lookup takes one."""
        return [global_id] if self.listed else global_id


def _gid(type_name: str, row: Model | str) -> str:
    """Encode ``row`` (or the node id itself) under ``type_name``."""
    node_id = row if isinstance(row, str) else str(saved_pk(row))
    return str(relay.GlobalID(type_name=type_name, node_id=node_id))


def _pks(*rows: Model) -> list[int]:
    return sorted(saved_pk(row) for row in rows)


def _mismatch(expected: str, received: str, *, listed: bool = True) -> str:
    """Strategy validation's refusal of a type name the target does not accept."""
    index = " at index 0" if listed else ""
    return f"GlobalID type mismatch: filter expects {expected} but received {received}{index}"


def _pair(
    model: type[Model],
    filterset: type[FilterSet],
    *,
    primary: str = "model",
    secondary: object = "type",
    hidden: tuple[int, ...] = (0,),
    hook: bool = True,
    node_id: str | None = None,
) -> tuple[type[DjangoType], type[DjangoType]]:
    """A ``primary``-strategy primary type over ``model`` and a secondary serving ``filterset``.

    ``secondary`` is the secondary's ``globalid_strategy`` (``"custom"`` overrides its
    ``resolve_typename`` instead); with ``hook`` its ``get_queryset`` hides ``hidden``.
    ``node_id`` names the column the primary's ``NodeID`` reads, its key by default.
    """
    stem = f"Reentry{model.__name__}"
    fields = ("id",) if node_id is None else ("id", node_id)
    namespace: dict[str, object] = {}
    meta: dict[str, object] = {
        "primary": False,
        "filterset_class": filterset,
        "connection": {"total_count": True},
    }
    if secondary == "custom":
        namespace["resolve_typename"] = _custom_typename()
    else:
        meta["globalid_strategy"] = secondary
    if hook:
        namespace["get_queryset"] = _hiding(*hidden)
    primary_type = make_django_type(
        f"{stem}Primary",
        model,
        fields,
        meta_extra={"primary": True, "globalid_strategy": primary},
        namespace_extra=None
        if node_id is None
        else {"__annotations__": {node_id: relay.NodeID[str]}},
    )
    secondary_type = make_django_type(
        f"{stem}Secondary",
        model,
        ("id",),
        meta_extra=meta,
        namespace_extra=namespace,
    )
    return primary_type, secondary_type


def _flat_set(model: type[Model], key: str, lookups: list[str]) -> type[FilterSet]:
    meta = type("Meta", (), {"model": model, "fields": {key: lookups}})
    return type("ReentryFilter", (FilterSet,), {"Meta": meta})


def _declared_set(model: type[Model], leaf: Filter) -> type[FilterSet]:
    meta = type("Meta", (), {"model": model, "fields": []})
    return type("ReentryFilter", (FilterSet,), {"leaf": leaf, "Meta": meta})


def _book_key(rows: _Library, shape: str) -> _Reentry:
    """``shelf__books`` / ``genres__books`` on a ``Book`` set wired to a scoping ``type`` secondary."""
    key = "genres__books" if shape == "genres" else "shelf__books"
    lookup = "in" if shape == "in" else "exact"
    if shape == "single":
        filterset = _declared_set(models.Book, GlobalIDFilter(field_name=key))
    elif shape == "multi":
        filterset = _declared_set(models.Book, GlobalIDMultipleChoiceFilter(field_name=key))
    else:
        filterset = _flat_set(models.Book, key, ["exact", "in"] if shape == "in" else [lookup])
    primary, secondary = _pair(models.Book, filterset)
    books = rows.books
    declared = shape in {"single", "multi"}
    listed = shape != "single"
    named = "leaf" if declared else key.replace("__", "_")
    return _Reentry(
        filterset,
        secondary,
        (primary,),
        (named, "in_" if shape == "in" else lookup),
        ("leaf" if declared else "genresBooks" if shape == "genres" else "shelfBooks", lookup),
        "leaf" if declared else f"{key}__in" if shape == "in" else key,
        _gid("library.book", books["bk1"]),
        _pks(books["bk1"], books["bk3"])
        if shape == "genres"
        else _pks(books["bk1"], books["bk2"]),
        _gid("ReentryBookSecondary", books["bk1"]),
        _mismatch("library.book", "ReentryBookSecondary", listed=listed),
        listed=listed,
    )


def _loan_key(rows: _Library) -> _Reentry:
    """``book__loans`` on a ``Loan`` set: a forward key, then its reverse back to ``Loan``."""
    filterset = _flat_set(models.Loan, "book__loans", ["exact"])
    primary, secondary = _pair(models.Loan, filterset)
    return _Reentry(
        filterset,
        secondary,
        (primary, make_django_type("ReentryLoanBook", models.Book, ("id",))),
        ("book_loans", "exact"),
        ("bookLoans", "exact"),
        "book__loans",
        _gid("library.loan", rows.loans["l1"]),
        _pks(rows.loans["l1"], rows.loans["l2"]),
        _gid("ReentryLoanSecondary", rows.loans["l1"]),
        _mismatch("library.loan", "ReentryLoanSecondary"),
    )


def _shelf_key(rows: _Library) -> _Reentry:
    """``alt_branches__alt_shelves`` on a ``Shelf`` set: a many-to-many and its reverse."""
    filterset = _flat_set(models.Shelf, "alt_branches__alt_shelves", ["exact"])
    primary, secondary = _pair(models.Shelf, filterset)
    shelves = rows.shelves
    return _Reentry(
        filterset,
        secondary,
        (primary, make_django_type("ReentryShelfBranch", models.Branch, ("id",))),
        ("alt_branches_alt_shelves", "exact"),
        ("altBranchesAltShelves", "exact"),
        "alt_branches__alt_shelves",
        _gid("library.shelf", shelves["s1"]),
        _pks(shelves["s1"], shelves["s2"]),
        _gid("ReentryShelfSecondary", shelves["s1"]),
        _mismatch("library.shelf", "ReentryShelfSecondary"),
    )


def _proxy_key(rows: _Library) -> _Reentry:
    """``shelves__alt_branches`` on a ``ProxyBranch`` set: the path re-enters the proxy's table."""
    filterset = _flat_set(models.ProxyBranch, "shelves__alt_branches", ["exact"])
    concrete = make_django_type(
        "ReentryBranch",
        models.Branch,
        ("id",),
        meta_extra={"globalid_strategy": "model"},
    )
    proxy = make_django_type(
        "ReentryProxyBranch",
        models.ProxyBranch,
        ("id",),
        meta_extra={
            "globalid_strategy": "model",
            "filterset_class": filterset,
            "connection": {"total_count": True},
        },
        namespace_extra={"get_queryset": _hiding(0)},
    )
    branches = rows.branches
    return _Reentry(
        filterset,
        proxy,
        (concrete, make_django_type("ReentryProxyShelf", models.Shelf, ("id",))),
        ("shelves_alt_branches", "exact"),
        ("shelvesAltBranches", "exact"),
        "shelves__alt_branches",
        _gid("library.branch", branches["b2"]),
        _pks(branches["b1"]),
        _gid("library.proxybranch", branches["b2"]),
        _mismatch("library.branch", "library.proxybranch"),
    )


def _declared_last_hop(rows: _Library) -> _Reentry:
    """``shelf__books`` walking ``shelf`` and ``books``, both declared, into the set itself.

    No type scopes the walk: the last hop's target set is the walking set, bound to the
    ``type`` secondary.
    """

    class ReentryShelfFilter(FilterSet):
        books = RelatedFilter(lambda: ReentryBookFilter, field_name="books")

        class Meta:
            model = models.Shelf
            fields = []

    class ReentryBookFilter(FilterSet):
        shelf = RelatedFilter(ReentryShelfFilter, field_name="shelf")
        leaf = GlobalIDFilter(field_name="shelf__books")

        class Meta:
            model = models.Book
            fields = []

    primary, secondary = _pair(models.Book, ReentryBookFilter, hook=False)
    books = rows.books
    return _Reentry(
        ReentryBookFilter,
        secondary,
        (primary, make_django_type("ReentryBookShelf", models.Shelf, ("id",))),
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("library.book", books["bk1"]),
        _pks(books["bk1"], books["bk2"]),
        _gid("ReentryBookSecondary", books["bk1"]),
        _mismatch("library.book", "ReentryBookSecondary", listed=False),
        listed=False,
    )


def _renamed_key(rows: _Library) -> _Reentry:
    """A ``type`` primary under a renaming converter: its published spelling, never its own."""
    filterset = _flat_set(models.Book, "shelf__books", ["exact"])
    primary, secondary = _pair(models.Book, filterset, primary="type")
    books = rows.books
    return _Reentry(
        filterset,
        secondary,
        (primary,),
        ("shelf_books", "exact"),
        ("shelfBooks", "exact"),
        None,
        _gid("ApiReentryBookPrimary", books["bk1"]),
        _pks(books["bk1"], books["bk2"]),
        _gid("ReentryBookPrimary", books["bk1"]),
        _mismatch("ApiReentryBookPrimary", "ReentryBookPrimary"),
        converter=_ApiPrefix(),
    )


def _renamed_forward_key(rows: _Library) -> _Reentry:
    """``shelf__branch`` past a ``Shelf`` hop a scoping type walks, into a renamed ``type`` branch."""
    filterset = _flat_set(models.Book, "shelf__branch", ["exact"])
    branch = make_django_type(
        "ReentryBranch",
        models.Branch,
        ("id",),
        meta_extra={"globalid_strategy": "type"},
    )
    shelf = make_django_type(
        "ReentryBookShelf",
        models.Shelf,
        ("id",),
        namespace_extra={"get_queryset": _hiding(0)},
    )
    book = make_django_type(
        "ReentryBook",
        models.Book,
        ("id",),
        meta_extra={"filterset_class": filterset, "connection": {"total_count": True}},
    )
    books = rows.books
    return _Reentry(
        filterset,
        book,
        (branch, shelf),
        ("shelf_branch", "exact"),
        ("shelfBranch", "exact"),
        None,
        _gid("ApiReentryBranch", rows.branches["b1"]),
        _pks(books["bk1"], books["bk2"], books["bk3"]),
        _gid("ReentryBranch", rows.branches["b1"]),
        _mismatch("ApiReentryBranch", "ReentryBranch", listed=False),
        listed=False,
        converter=_ApiPrefix(),
    )


def _off_pk_key(rows: _Library, model_name: str) -> _Reentry:
    """A ``model`` primary whose ``NodeID`` is a unique text column, not its key.

    ``printings_2__co_publishers`` on ``Publisher`` (its house code) or
    ``shelves__alt_branches`` on ``Branch`` (its name): the target rows compare that column
    on themselves.
    """
    if model_name == "publisher":
        filterset = _flat_set(models.Publisher, "printings_2__co_publishers", ["exact"])
        primary, secondary = _pair(models.Publisher, filterset, node_id="house_code")
        named, kept = rows.publishers["h2"], [rows.publishers["h1"]]
        extra = (
            make_django_type("ReentryPrinting", models.Printing, ("id",)),
            make_django_type("ReentryEdition", models.Edition, ("isbn_13",)),
        )
        path, wire, key = (
            "printings_2_co_publishers",
            "printings2CoPublishers",
            "printings_2__co_publishers",
        )
        node_id = named.house_code
    else:
        filterset = _flat_set(models.Branch, "shelves__alt_branches", ["exact"])
        primary, secondary = _pair(models.Branch, filterset, node_id="name")
        named, kept = rows.branches["b2"], [rows.branches["b1"]]
        extra = (make_django_type("ReentryBranchShelf", models.Shelf, ("id",)),)
        path, wire, key = "shelves_alt_branches", "shelvesAltBranches", "shelves__alt_branches"
        node_id = named.name
    stem = f"Reentry{type(named).__name__}"
    return _Reentry(
        filterset,
        secondary,
        (primary, *extra),
        (path, "exact"),
        (wire, "exact"),
        key,
        _gid(type(named)._meta.label_lower, node_id),
        _pks(*kept),
        _gid(f"{stem}Secondary", named),
        _mismatch(type(named)._meta.label_lower, f"{stem}Secondary"),
    )


def _encode_only_secondary(rows: _Library, strategy: str) -> _Reentry:
    """A ``callable`` or ``custom`` secondary, which mints ids no filter decodes, serves the set."""
    filterset = _flat_set(models.Book, "shelf__books", ["exact"])
    primary, secondary = _pair(
        models.Book,
        filterset,
        secondary=_encode_by_name if strategy == "callable" else "custom",
    )
    books = rows.books
    return _Reentry(
        filterset,
        secondary,
        (primary,),
        ("shelf_books", "exact"),
        ("shelfBooks", "exact"),
        "shelf__books",
        _gid("library.book", books["bk1"]),
        _pks(books["bk1"], books["bk2"]),
        _gid("ReentryBookSecondary", books["bk1"]),
        _mismatch("library.book", "ReentryBookSecondary"),
    )


def _hidden_named_row(rows: _Library) -> _Reentry:
    """The secondary's ``get_queryset`` hides the book the id names: no parent reaches it."""
    filterset = _flat_set(models.Book, "shelf__books", ["exact"])
    books = rows.books
    primary, secondary = _pair(models.Book, filterset, hidden=(saved_pk(books["bk2"]),))
    return _Reentry(
        filterset,
        secondary,
        (primary,),
        ("shelf_books", "exact"),
        ("shelfBooks", "exact"),
        "shelf__books",
        _gid("library.book", books["bk2"]),
        [],
        _gid("ReentryBookSecondary", books["bk2"]),
        _mismatch("library.book", "ReentryBookSecondary"),
    )


def _trailing_pk_leaf(
    rows: _Library,
    key: str,
    *,
    secondary: object = "type",
    exclude: bool = False,
    hop_hook: bool = False,
) -> _Reentry:
    """A consumer ``GlobalIDFilter`` on ``key``, ending on a re-entry's primary key.

    ``shelf__books__id`` / ``__pk`` or ``genres__books__id`` on a ``Book`` set wired to a
    ``secondary`` whose ``get_queryset`` scopes the walk's hops back to ``Book``; with
    ``hop_hook`` the secondary declares none and a ``Shelf`` type scopes the earlier
    hop. The id names the target row as the type registered for ``Book`` does, as the
    unscoped leaf and the bare key's do; with ``exclude`` the filter excludes the rows.
    """
    filterset = _declared_set(models.Book, GlobalIDFilter(field_name=key, exclude=exclude))
    primary, secondary_type = _pair(
        models.Book,
        filterset,
        secondary=secondary,
        hook=not hop_hook,
    )
    extra = (
        (
            make_django_type(
                "ReentryBookShelf",
                models.Shelf,
                ("id",),
                namespace_extra={"get_queryset": _hiding(0)},
            ),
        )
        if hop_hook
        else ()
    )
    books = rows.books
    named = {
        saved_pk(books[title])
        for title in (("bk1", "bk3") if key.startswith("genres") else ("bk1", "bk2"))
    }
    every = {saved_pk(book) for book in books.values()}
    return _Reentry(
        filterset,
        secondary_type,
        (primary, *extra),
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("library.book", books["bk1"]),
        sorted(every - named if exclude else named),
        _gid("ReentryBookSecondary", books["bk1"]),
        _mismatch("library.book", "ReentryBookSecondary", listed=False),
        listed=False,
    )


def _patron_trailing_pk_leaf(_rows: _Library) -> _Reentry:
    """``card__patron__id`` on a ``Patron`` set: a reverse one-to-one, then back forward."""
    patrons = {patron.name: patron for patron in models.Patron.objects.all()}
    for name, patron in patrons.items():
        models.MembershipCard.objects.create(patron=patron, barcode=name)
    filterset = _declared_set(models.Patron, GlobalIDFilter(field_name="card__patron__id"))
    primary, secondary = _pair(models.Patron, filterset)
    return _Reentry(
        filterset,
        secondary,
        (primary, make_django_type("ReentryPatronCard", models.MembershipCard, ("id",))),
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("library.patron", patrons["p1"]),
        _pks(patrons["p1"]),
        _gid("ReentryPatronSecondary", patrons["p1"]),
        _mismatch("library.patron", "ReentryPatronSecondary", listed=False),
        listed=False,
    )


def _off_pk_trailing_pk_leaf(rows: _Library) -> _Reentry:
    """``printings_2__co_publishers__id`` on ``Publisher``: its primary's id is its house code."""
    filterset = _declared_set(
        models.Publisher,
        GlobalIDFilter(field_name="printings_2__co_publishers__id"),
    )
    primary, secondary = _pair(models.Publisher, filterset, node_id="house_code")
    named = rows.publishers["h2"]
    return _Reentry(
        filterset,
        secondary,
        (
            primary,
            make_django_type("ReentryPrinting", models.Printing, ("id",)),
            make_django_type("ReentryEdition", models.Edition, ("isbn_13",)),
        ),
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("library.publisher", named.house_code),
        _pks(rows.publishers["h1"]),
        _gid("ReentryPublisherSecondary", named),
        _mismatch("library.publisher", "ReentryPublisherSecondary", listed=False),
        listed=False,
    )


_REENTRIES: dict[str, Callable[[_Library], _Reentry]] = {
    "generated-key": functools.partial(_book_key, shape="generated"),
    "declared-key": functools.partial(_book_key, shape="single"),
    "declared-multiple-key": functools.partial(_book_key, shape="multi"),
    "in-lookup": functools.partial(_book_key, shape="in"),
    "many-to-many-key": functools.partial(_book_key, shape="genres"),
    "forward-then-reverse-key": _loan_key,
    "many-to-many-then-reverse-key": _shelf_key,
    "proxy-root": _proxy_key,
    "declared-last-hop": _declared_last_hop,
    "renamed-primary": _renamed_key,
    "renamed-forward-key-past-a-scoped-hop": _renamed_forward_key,
    "off-key-node-id-publisher": functools.partial(_off_pk_key, model_name="publisher"),
    "off-key-node-id-branch": functools.partial(_off_pk_key, model_name="branch"),
    "callable-secondary": functools.partial(_encode_only_secondary, strategy="callable"),
    "custom-secondary": functools.partial(_encode_only_secondary, strategy="custom"),
    "hidden-named-row": _hidden_named_row,
    "trailing-id": functools.partial(_trailing_pk_leaf, key="shelf__books__id"),
    "trailing-pk": functools.partial(_trailing_pk_leaf, key="shelf__books__pk"),
    "many-to-many-trailing-id": functools.partial(_trailing_pk_leaf, key="genres__books__id"),
    "to-one-trailing-id": _patron_trailing_pk_leaf,
    "trailing-id-past-a-scoped-hop": functools.partial(
        _trailing_pk_leaf,
        key="shelf__books__id",
        hop_hook=True,
    ),
    "off-key-node-id-trailing-id": _off_pk_trailing_pk_leaf,
    "callable-secondary-trailing-id": functools.partial(
        _trailing_pk_leaf,
        key="shelf__books__id",
        secondary=_encode_by_name,
    ),
    "custom-secondary-trailing-id": functools.partial(
        _trailing_pk_leaf,
        key="shelf__books__id",
        secondary="custom",
    ),
    "excluded-trailing-id": functools.partial(
        _trailing_pk_leaf,
        key="shelf__books__id",
        exclude=True,
    ),
}


def _reentry_schema(world: _Reentry) -> DjangoSchema:
    """Serve ``world.root`` as a filtered connection and through ``apply_sync``."""
    model = world.filterset._meta.model
    assert model is not None

    def _all_rows(_root: object, _info: object) -> QuerySet[Model]:
        return model._default_manager.order_by("pk")

    def _applied(info: Info[object, object], where: JSON) -> QuerySet[Model]:
        return world.filterset.apply_sync(where, model._default_manager.order_by("pk"), info)

    async def _applied_async(info: Info[object, object], where: JSON) -> list[Model]:
        rows = await world.filterset.apply_async(
            where,
            model._default_manager.order_by("pk"),
            info,
        )
        return await sync_to_async(list)(rows)

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(world.root, resolver=_all_rows)
        applied: QuerySet[Model] = strawberry.field(
            resolver=_applied,
            graphql_type=StrawberryList(world.root),
        )
        applied_async: list[Model] = strawberry.field(
            resolver=_applied_async,
            graphql_type=StrawberryList(world.root),
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=Query,
        types=world.types,
        config=strawberry_config()
        if world.converter is None
        else strawberry_config(name_converter=world.converter),
        extensions=[lambda: optimizer],
    )


def _nested(names: tuple[str, ...], value: str | list[str]) -> JSONObject:
    """``value`` under the input ``names``, outermost first."""
    nested: JSONObject = {names[-1]: value}
    for name in reversed(names[:-1]):
        nested = {name: nested}
    return nested


def _wire_literal(names: tuple[str, ...], value: str | list[str]) -> str:
    """``value`` under the published input ``names``, spelled as a GraphQL object literal."""
    literal = json.dumps(value)
    for name in reversed(names):
        literal = f"{{{name}: {literal}}}"
    return literal


async def _async_post(
    schema: DjangoSchema,
    query: str,
    variables: Mapping[str, object],
) -> JSONObject:
    """Post ``query`` to the async view serving ``schema`` and return the parsed payload."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            result = await AsyncTestClient(path=_ASYNC_URL).query(
                query,
                variables,
                assert_no_errors=False,
            )
    finally:
        _CURRENT["schema"] = None
    assert result.response.status_code == 200
    return response_json(result.response)


def _reentry_answer(world: _Reentry, global_id: str, driver: str) -> list[int] | str:
    """The pks ``driver`` answers for ``global_id`` in ``world``, or its error message."""
    value = world.value(global_id)
    schema = _reentry_schema(world)
    if driver == "form":
        assert world.form_key is not None
        model = world.filterset._meta.model
        assert model is not None
        bound = world.filterset(
            data={world.form_key: value},
            queryset=model._default_manager.all(),
        )
        try:
            rows = require(bound.qs, is_queryset)
        except GraphQLError as exc:
            return exc.message
        return sorted(saved_pk(require_instance(row, Model)) for row in rows)
    if driver == "live":
        query = f"{{ rows(filter: {_wire_literal(world.wire, value)}) {{ edges {{ node {{ id }} }} }} }}"
        payload = _post(schema, query)
        path: tuple[str, ...] = ("rows", "edges")
    elif driver == "apply-async":
        payload = asyncio.run(
            _async_post(
                schema,
                "query($where: JSON!) { appliedAsync(where: $where) { id } }",
                {"where": _nested(world.path, value)},
            ),
        )
        path = ("appliedAsync",)
    else:
        payload = _post(
            schema,
            "query($where: JSON!) { applied(where: $where) { id } }",
            {"where": _nested(world.path, value)},
        )
        path = ("applied",)
    if payload.get("errors"):
        return json_str(payload, "errors", 0, "message")
    rows_out = json_list(payload, "data", *path)
    node_ids = [
        json_str(row, "node", "id") if driver == "live" else json_str(row, "id")
        for row in rows_out
    ]
    return sorted(
        int(relay.GlobalID.from_id(node_id).node_id.removeprefix(_KEY_PREFIX))
        for node_id in node_ids
    )


#: The worlds whose answer reads the executing schema's published names, which a raw form lacks.
_SCHEMA_NAMED = {"renamed-primary", "renamed-forward-key-past-a-scoped-hop"}
_REENTRY_ROWS = [
    pytest.param(name, driver, id=f"{name}-{driver}")
    for name in _REENTRIES
    for driver in ("live", "apply-sync", "form")
    if driver != "form" or name not in _SCHEMA_NAMED
]


@pytest.mark.django_db
@pytest.mark.parametrize(("name", "driver"), _REENTRY_ROWS)
def test_a_reentry_key_serves_the_id_its_relation_target_type_mints(
    name: str,
    driver: str,
) -> None:
    """A GlobalID relation key whose hops re-enter its set's table names a row as its relation's type.

    Whichever type the walk's target rows answer for (a secondary the set is bound to,
    scoping the walk or not, a proxy root's type), the key's id is the one the type
    registered for the relation's target mints, under the name the executing schema
    published for it and in its ``NodeID`` column, as an unscoped key's is: it answers
    the exact rows reaching the row it names over the visible target rows. A leaf
    ending on the re-entry's primary key (``shelf__books__id``, ``__pk``) names it so
    too, an encode-only secondary's set included, and excludes those rows under
    ``exclude=True``.
    """
    world = _REENTRIES[name](_library())

    assert _reentry_answer(world, world.accepted, driver) == world.expected


@pytest.mark.django_db
@pytest.mark.parametrize(("name", "driver"), _REENTRY_ROWS)
def test_a_reentry_key_refuses_an_id_its_relation_target_type_does_not_mint(
    name: str,
    driver: str,
) -> None:
    """The id the set's own type mints, or an unpublished spelling, is a type mismatch."""
    world = _REENTRIES[name](_library())

    assert _reentry_answer(world, world.refused, driver) == world.refusal


_ASYNC_ROWS = ["trailing-id", "many-to-many-trailing-id"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("name", _ASYNC_ROWS)
def test_a_reentry_leaf_applied_async_serves_the_id_its_relation_target_type_mints(
    name: str,
) -> None:
    """``apply_async`` names the re-entry's row as the type registered for its relation does."""
    world = _REENTRIES[name](_library())

    assert _reentry_answer(world, world.accepted, "apply-async") == world.expected


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("name", _ASYNC_ROWS)
def test_a_reentry_leaf_applied_async_refuses_the_id_its_set_type_mints(name: str) -> None:
    """``apply_async`` refuses the id the secondary the set is bound to mints."""
    world = _REENTRIES[name](_library())

    assert _reentry_answer(world, world.refused, "apply-async") == world.refusal


def _keyed_leaf(rows: _Library, shape: str) -> _Reentry:
    """A GlobalID leaf ending on ``Book``'s key, whose primary's ``NodeID`` is ``node_key``.

    ``node_key`` is an annotation the primary's ``get_queryset`` adds, so only rows the
    primary answers for carry it. ``foreign-*`` shapes walk ``shelf__books__id`` or
    ``genres__books__id`` on a ``Book`` set wired to a scoping ``type`` secondary, whose
    rows lack it; ``owned-reentry`` walks ``shelf__books__id`` on a ``Book`` set wired to
    the primary itself, and ``owned-relation`` ``books__id`` on a ``Shelf`` set, both over
    rows the primary answers for.
    """
    key = {
        "foreign-reverse-foreign-key": "shelf__books__id",
        "foreign-many-to-many": "genres__books__id",
        "owned-reentry": "shelf__books__id",
        "owned-relation": "books__id",
    }[shape]
    model = models.Shelf if shape == "owned-relation" else models.Book
    filterset = _declared_set(model, GlobalIDFilter(field_name=key))
    wired = {"filterset_class": filterset, "connection": {"total_count": True}}
    primary = make_django_type(
        "ReentryKeyedBook",
        models.Book,
        ("id",),
        meta_extra={
            "primary": True,
            "globalid_strategy": "model",
            **(wired if shape == "owned-reentry" else {}),
        },
        namespace_extra={
            "__annotations__": {"node_key": relay.NodeID[str]},
            "get_queryset": _keyed(),
        },
    )
    if shape == "owned-reentry":
        root, types = primary, ()
    elif shape == "owned-relation":
        shelf = make_django_type("ReentryKeyedShelf", models.Shelf, ("id",), meta_extra=wired)
        root, types = shelf, (primary,)
    else:
        root = make_django_type(
            "ReentryKeyedSecondary",
            models.Book,
            ("id",),
            meta_extra={"primary": False, "globalid_strategy": "type", **wired},
            namespace_extra={"get_queryset": _hiding(0)},
        )
        types = (primary,)
    books = rows.books
    # A ``foreign-*`` shape answers no rows: the id is refused.
    expected = (
        _pks(rows.shelves["s1"])
        if shape == "owned-relation"
        else _pks(books["bk1"], books["bk2"])
        if shape == "owned-reentry"
        else []
    )
    return _Reentry(
        filterset,
        root,
        types,
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("library.book", f"{_KEY_PREFIX}{saved_pk(books['bk1'])}"),
        expected,
        listed=False,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("driver", ["live", "apply-sync", "form"])
@pytest.mark.parametrize("shape", ["foreign-reverse-foreign-key", "foreign-many-to-many"])
def test_a_reentry_leaf_refuses_an_id_an_annotation_holds_over_rows_another_type_scopes(
    shape: str,
    driver: str,
) -> None:
    """The primary's ``node_key`` is not on rows the secondary answers for: a coded refusal.

    The leaf's unscoped twin and the bare key refuse it alike, never compare it on the
    walk's rows.
    """
    world = _keyed_leaf(_library(), shape)

    assert _reentry_answer(world, world.accepted, driver) == (
        "GlobalID filter target ReentryKeyedBook carries its id in 'node_key', which no "
        "model column holds, so a filter across a relation cannot compare it."
    )


#: ``applied`` serves the model's own rows, which lack the ``node_key`` the keyed primary's
#: ``id`` reads, so the set wired to that primary answers live and on the raw form.
_OWNED_KEYED_ROWS = [
    pytest.param(shape, driver, id=f"{shape}-{driver}")
    for shape in ("owned-reentry", "owned-relation")
    for driver in ("live", "apply-sync", "form")
    if shape != "owned-reentry" or driver != "apply-sync"
]


@pytest.mark.django_db
@pytest.mark.parametrize(("shape", "driver"), _OWNED_KEYED_ROWS)
def test_a_leaf_compares_an_id_an_annotation_holds_over_rows_its_type_scopes(
    shape: str,
    driver: str,
) -> None:
    """Over rows the primary answers for, its ``node_key`` annotation is compared there."""
    world = _keyed_leaf(_library(), shape)

    assert _reentry_answer(world, world.accepted, driver) == world.expected


def _untyped_walk(rows: _Library, shape: str) -> _Reentry:
    """A to-many GlobalID key walking a declared hop into a model no type exposes.

    ``shelves__books`` on ``Branch`` past its declared ``shelves`` (no ``Book`` type), or
    ``books__loans`` on ``Genre`` past its declared ``books`` (no ``Loan`` type): no type
    names the key's rows, so any type name is accepted and the node id compared alone.
    """
    if shape == "reverse-foreign-key":
        root_model, hop_model, hop, key = models.Branch, models.Shelf, "shelves", "shelves__books"
        named, expected = rows.books["bk1"], _pks(rows.branches["b1"])
    else:
        root_model, hop_model, hop, key = models.Genre, models.Book, "books", "books__loans"
        named, expected = rows.loans["l1"], _pks(rows.genres["g1"])
    hop_set = type(
        "UntypedHopFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": hop_model, "fields": []})},
    )
    filterset = type(
        "UntypedWalkFilter",
        (FilterSet,),
        {
            hop: RelatedFilter(hop_set, field_name=hop),
            "leaf": GlobalIDFilter(field_name=key),
            "Meta": type("Meta", (), {"model": root_model, "fields": []}),
        },
    )
    root = make_django_type(
        "UntypedWalkRoot",
        root_model,
        ("id",),
        meta_extra={"filterset_class": filterset, "connection": {"total_count": True}},
    )
    return _Reentry(
        filterset,
        root,
        (make_django_type("UntypedWalkHop", hop_model, ("id",)),),
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("Unregistered", named),
        expected,
        listed=False,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("driver", ["live", "apply-sync", "form"])
@pytest.mark.parametrize("shape", ["reverse-foreign-key", "forward-then-reverse"])
def test_a_walked_to_many_key_into_a_model_no_type_exposes_compares_the_node_id_alone(
    shape: str,
    driver: str,
) -> None:
    """No type answers for the key's target, so neither of its decodes checks a type name."""
    world = _untyped_walk(_library(), shape)

    assert _reentry_answer(world, world.accepted, driver) == world.expected
