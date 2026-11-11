"""GlobalID filters accept only the target's configured emitted identifier spellings.

These native Relay types use real Meta strategies and emit identifiers over HTTP.
The JSON consumer applies its associated FilterSet; a typed GlobalID consumer uses
its bound public filter primitive to preserve Strawberry's already-decoded value.
A GlobalID filter into a model no type exposes compares the node id on the relation's
key, through a ``GenericRelation`` too; one on a ``GenericForeignKey`` is refused when
its set publishes its filters, served or applied unbound, unless a ``method`` filters it.
So is a model-choice filter on one, whatever its ``queryset``, unless a ``method`` or a
``filter`` override of its own filters it; through a ``GenericRelation`` it keeps the
tagged rows, and on a name only the type's queryset holds (a ``FilteredRelation`` alias,
a text annotation) it serves rows. So is any other filter running shipped code on one (a
column-typed, choice or null-test filter, a ``RelatedFilter`` child's naming the child),
while a ``method`` or a ``filter`` override of its own answers rows unserved and, served,
is refused by the input build no scalar types. A shipped filter whose path continues past
one (``content_object__name``, past a ``GenericRelation`` or from a ``RelatedFilter``
child) is refused alike, naming the key it continues past, while a ``method`` or a
``filter`` override over such a path answers rows served and unserved.
A relation key whose hops re-enter its own set's table takes the id the type registered
for the relation's target mints, under its published name, whichever type the set or the
walk's target rows answer for, and so does a consumer leaf ending on the re-entry's
primary key past an undeclared hop (``shelf__books__id``), served, applied sync or async,
and on the raw form. An id only a ``get_queryset`` annotation holds compares only over
rows its type answers for, and is refused over rows another type answers for. A leaf
ending on a relation target's key past a declared hop into a set no type wires names a
row as the type registered for the target does; past a hop into a set a secondary wires,
as that secondary. A GlobalID filter whose path starts at a ``FilteredRelation`` alias
(bare, ``__id``, ``__pk``) decodes, validates and refuses as the same filter over the
relation the alias joins does, over the rows Django's join of the alias reads (its
condition applied), on every placement and driver; the build cannot see the alias, so an
encode-only target through one is refused per request.
"""

import asyncio
import functools
import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import wraps
from typing import NamedTuple, TypeVar

import pytest
import strawberry
from apps.library import models
from apps.library.filters import ModelChoiceInFilter
from asgiref.sync import sync_to_async
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import CharField, F, FilteredRelation, Model, Q, QuerySet, Value
from django.db.models.functions import Cast, Concat
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    Filter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    NumberFilter,
)
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
from django_strawberry_framework.utils._narrowing import (
    is_list_or_tuple,
    is_queryset,
    require,
    require_instance,
)
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_M = TypeVar("_M", bound=Model)
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


class _SuperGlobalIDFilter(GlobalIDFilter):
    """A consumer ``filter`` override that still compares the node id through ``super()``."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return super().filter(qs, value)


class _OwnGlobalIDMultipleChoiceFilter(GlobalIDMultipleChoiceFilter):
    """A consumer ``filter`` override that filters nothing, never calling ``super()``."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        del value
        return qs


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
@pytest.mark.parametrize(
    "filter_class",
    [
        GlobalIDFilter,
        GlobalIDMultipleChoiceFilter,
        _SuperGlobalIDFilter,
        _OwnGlobalIDMultipleChoiceFilter,
    ],
)
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


def _generic_relation_schema(leaf: Filter) -> DjangoSchema:
    """A Relay ``Branch`` type filtering by ``leaf``, one of its ``tags``.

    ``Branch.tags`` is a ``GenericRelation`` (the reverse of ``TaggedItem.content_object``)
    and no type exposes ``TaggedItem``, so a GlobalID ``leaf``'s node id is compared on the
    tag's key.
    """
    registry.clear()

    class BranchTagFilter(FilterSet):
        tagged = leaf

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
    schema = _generic_relation_schema(GlobalIDFilter(field_name="tags"))
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


def _branch_rows(_request: object = None) -> QuerySet[models.Branch]:
    """Every branch: a model-choice filter's ``queryset``, or the callable returning it."""
    return models.Branch.objects.order_by("pk")


class _ContentObjectChoiceFilter(ModelChoiceFilter):
    """A ``filter`` override keeping the tags whose content type and object id name the branch."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        if not isinstance(value, models.Branch):
            return qs
        content_type = ContentType.objects.get_for_model(models.Branch)
        return qs.filter(content_type=content_type, object_id=value.pk)


class _ContentObjectMultipleChoiceFilter(ModelMultipleChoiceFilter):
    """A ``filter`` override keeping the tags whose object id names one of the branches."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        if not is_list_or_tuple(value) or not value:
            return qs
        content_type = ContentType.objects.get_for_model(models.Branch)
        return qs.filter(
            content_type=content_type,
            object_id__in=[saved_pk(row) for row in value if isinstance(row, Model)],
        )


def _model_choice_set(
    model: type[Model],
    leaf: Filter | None,
    queryset: object = None,
    lookup: str = "exact",
) -> type[FilterSet]:
    """A set on ``model`` declaring ``leaf`` as ``chosen``, or selecting a model choice.

    With no ``leaf``, ``Meta.filter_overrides`` selects a ``ModelChoiceFilter`` over
    ``queryset`` (every branch for ``None``; a callable returning them is passed uncalled)
    for the ``GenericForeignKey`` ``Meta.fields`` names with ``lookup``: for ``in``,
    django-filter generates its CSV wrapper around the selected class.
    """
    meta: dict[str, object] = {"model": model, "fields": []}
    attrs: dict[str, object] = {}
    if leaf is None:
        chosen_rows = _branch_rows() if queryset is None else queryset

        def extra(_field: object) -> dict[str, object]:
            return {"queryset": chosen_rows}

        meta["fields"] = {"content_object": [lookup]}
        meta["filter_overrides"] = {
            GenericForeignKey: {"filter_class": ModelChoiceFilter, "extra": extra},
        }
    else:
        attrs["chosen"] = leaf
    attrs["Meta"] = type("Meta", (), meta)
    filterset = type("ModelChoiceGenericSet", (FilterSet,), attrs)
    assert issubclass(filterset, FilterSet)
    return filterset


def _served_schema(filterset: type[FilterSet]) -> DjangoSchema:
    """``filterset``'s model on a type serving it, so the schema build publishes the set."""
    model = filterset._meta.model
    assert model is not None
    registry.clear()

    @strawberry.type
    class Query:
        rows = DjangoConnectionField(
            make_django_type(
                "ServedRowsNode",
                model,
                ("id",),
                meta_extra={"filterset_class": filterset},
            ),
        )

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


class _GenericChoice(NamedTuple):
    """A model-choice shape on a ``GenericForeignKey`` and the words its refusal names."""

    model: type[Model]
    #: Builds the declared leaf; ``None`` selects one through ``Meta.filter_overrides``.
    leaf: Callable[[], Filter] | None
    #: The refused filter's class, published name and ``field_name``.
    kind: str
    name: str
    field_name: str
    #: The ``GenericForeignKey`` the path ends on.
    relation: str
    #: The ``queryset`` a ``Meta.filter_overrides`` selection is handed (``None``: every
    #: branch).
    queryset: object = None
    #: The lookup ``Meta.fields`` names for a ``Meta.filter_overrides`` selection.
    lookup: str = "exact"


_GENERIC_CHOICES: dict[str, _GenericChoice] = {
    "model-choice": _GenericChoice(
        models.TaggedItem,
        lambda: ModelChoiceFilter(field_name="content_object", queryset=_branch_rows()),
        "ModelChoiceFilter",
        "chosen",
        "content_object",
        "TaggedItem.content_object",
    ),
    "model-multiple-choice": _GenericChoice(
        models.TaggedItem,
        lambda: ModelMultipleChoiceFilter(field_name="content_object", queryset=_branch_rows()),
        "ModelMultipleChoiceFilter",
        "chosen",
        "content_object",
        "TaggedItem.content_object",
    ),
    "model-choice-past-a-forward-key": _GenericChoice(
        models.DeskShift,
        lambda: ModelChoiceFilter(field_name="desk__content_object", queryset=_branch_rows()),
        "ModelChoiceFilter",
        "chosen",
        "desk__content_object",
        "CirculationDesk.content_object",
    ),
    "model-multiple-choice-past-a-reverse-relation": _GenericChoice(
        models.Branch,
        lambda: ModelMultipleChoiceFilter(
            field_name="circulation_desks__content_object",
            queryset=_branch_rows(),
        ),
        "ModelMultipleChoiceFilter",
        "chosen",
        "circulation_desks__content_object",
        "CirculationDesk.content_object",
    ),
    "declared-csv-model-choice": _GenericChoice(
        models.TaggedItem,
        lambda: ModelChoiceInFilter(
            field_name="content_object",
            lookup_expr="in",
            queryset=_branch_rows(),
        ),
        "ModelChoiceInFilter",
        "chosen",
        "content_object",
        "TaggedItem.content_object",
    ),
    "filter-overrides-model-choice": _GenericChoice(
        models.TaggedItem,
        None,
        "ModelChoiceFilter",
        "content_object",
        "content_object",
        "TaggedItem.content_object",
    ),
    "filter-overrides-generated-csv-model-choice": _GenericChoice(
        models.TaggedItem,
        None,
        "ModelChoiceInFilter",
        "content_object__in",
        "content_object",
        "TaggedItem.content_object",
        lookup="in",
    ),
    "callable-queryset-model-choice": _GenericChoice(
        models.TaggedItem,
        None,
        "ModelChoiceFilter",
        "content_object",
        "content_object",
        "TaggedItem.content_object",
        _branch_rows,
    ),
}


def _generic_choice_refusal(shape: _GenericChoice) -> str:
    return (
        f"FilterSet ModelChoiceGenericSet: {shape.kind} "
        f"{shape.name!r} has field_name {shape.field_name!r}, which names {shape.relation}, a "
        "GenericForeignKey: Django filters no queryset through it, so no related row's "
        "identity can be compared on it. Filter through the GenericRelation that reverses it "
        "on the related model, or on the content type and object id columns it reads."
    )


@pytest.mark.django_db
@pytest.mark.parametrize("name", sorted(_GENERIC_CHOICES))
def test_a_model_choice_filter_on_a_generic_foreign_key_is_refused_when_the_schema_builds(
    name: str,
) -> None:
    """A model-choice filter compares the row it looks up on its path, which a GFK cannot hold.

    Whatever its ``queryset`` (a model's rows, a callable returning them), past a forward
    key or a reverse relation, as django-filter's CSV wrapper or a ``Meta.filter_overrides``
    selection, it would answer every request with the ``FieldError`` Django's query raises:
    serving the set refuses it in the GlobalID filter's words.
    """
    shape = _GENERIC_CHOICES[name]
    leaf = None if shape.leaf is None else shape.leaf()
    filterset = _model_choice_set(shape.model, leaf, shape.queryset, shape.lookup)

    with pytest.raises(ConfigurationError) as exc_info:
        _ = _served_schema(filterset)

    assert str(exc_info.value) == _generic_choice_refusal(shape), exc_info


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["model-choice", "model-multiple-choice"])
def test_an_unserved_model_choice_filter_on_a_generic_foreign_key_is_refused_at_first_use(
    caplog: pytest.LogCaptureFixture,
    name: str,
) -> None:
    """Applied unbound, the set publishes at its first use: the same refusal, logged.

    The request answers the masked error and the server log carries the
    ``ConfigurationError``, never a ``FieldError`` from the query.
    """
    shape = _GENERIC_CHOICES[name]
    assert shape.leaf is not None
    branch = models.Branch.objects.create(name="Target", city="Boston")
    _ = models.TaggedItem.objects.create(content_object=branch, tag="t")
    schema = _tagged_item_schema(_model_choice_set(shape.model, shape.leaf()), served=False)
    unfiltered = _post(schema, "{ tags { tag } }")
    assert unfiltered == {"data": {"tags": [{"tag": "t"}]}}, unfiltered
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    value = saved_pk(branch) if name == "model-choice" else [saved_pk(branch)]

    payload = _post(
        schema,
        "query($where: JSON!) { tags(where: $where) { tag } }",
        {"where": {"chosen": value}},
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
    assert str(exc_info[1]) == _generic_choice_refusal(shape), exc_info[1]


def _content_object_method_set(leaf: Filter) -> type[FilterSet]:
    """A set whose model-choice ``leaf`` on the ``GenericForeignKey`` runs ``by_branches``."""

    class ContentObjectMethodSet(FilterSet):
        chosen = leaf

        class Meta:
            model = models.TaggedItem
            fields = []

        def by_branches(
            self,
            queryset: QuerySet[models.TaggedItem],
            name: str,
            value: object,
        ) -> QuerySet[models.TaggedItem]:
            del name
            chosen = value if is_list_or_tuple(value) else [value]
            return queryset.filter(
                content_type=ContentType.objects.get_for_model(models.Branch),
                object_id__in=[saved_pk(row) for row in chosen if isinstance(row, Model)],
            )

    return ContentObjectMethodSet


def _own_filter_set(leaf: Filter) -> type[FilterSet]:
    """A set whose model-choice ``leaf`` on the ``GenericForeignKey`` runs its own ``filter``."""

    class ContentObjectOwnFilterSet(FilterSet):
        chosen = leaf

        class Meta:
            model = models.TaggedItem
            fields = []

    return ContentObjectOwnFilterSet


#: Each model-choice leaf the refusal leaves to consumer code, its set builder, and whether
#: it takes a list of branches.
_CONSUMER_GENERIC_CHOICES: dict[str, tuple[Callable[[], type[FilterSet]], bool]] = {
    "model-choice-method": (
        lambda: _content_object_method_set(
            ModelChoiceFilter(
                field_name="content_object",
                queryset=_branch_rows(),
                method="by_branches",
            ),
        ),
        False,
    ),
    "model-multiple-choice-method": (
        lambda: _content_object_method_set(
            ModelMultipleChoiceFilter(
                field_name="content_object",
                queryset=_branch_rows(),
                method="by_branches",
            ),
        ),
        True,
    ),
    "model-choice-filter-override": (
        lambda: _own_filter_set(
            _ContentObjectChoiceFilter(field_name="content_object", queryset=_branch_rows()),
        ),
        False,
    ),
    "model-multiple-choice-filter-override": (
        lambda: _own_filter_set(
            _ContentObjectMultipleChoiceFilter(
                field_name="content_object",
                queryset=_branch_rows(),
            ),
        ),
        True,
    ),
}


def _node_pks(payload: JSONObject, field: str) -> list[int]:
    """The primary keys the node ids of ``payload``'s ``field`` rows name, in order."""
    assert "errors" not in payload, payload
    rows = json_list(json_object(payload, "data"), field)
    return [int(relay.GlobalID.from_id(json_str(row, "id")).node_id) for row in rows]


@pytest.mark.django_db
@pytest.mark.parametrize("served", [True, False], ids=["served", "unserved"])
@pytest.mark.parametrize("name", sorted(_CONSUMER_GENERIC_CHOICES))
def test_a_model_choice_filter_on_a_generic_foreign_key_filters_through_consumer_code(
    name: str,
    *,
    served: bool,
) -> None:
    """A ``method`` or a ``filter`` override filters as it chooses, so the refusal leaves it.

    Neither compares through the relation the ``field_name`` names: these keep the tags
    whose content type and object id name the chosen branches.
    """
    target = models.Branch.objects.create(name="Target", city="Boston")
    sibling = models.Branch.objects.create(name="Sibling", city="Boston")
    other = models.Branch.objects.create(name="Other", city="Boston")
    tags = [
        saved_pk(models.TaggedItem.objects.create(content_object=branch, tag=branch.name.lower()))
        for branch in (target, sibling, other)
    ]
    build, listed = _CONSUMER_GENERIC_CHOICES[name]
    schema = _tagged_item_schema(build(), served=served)
    value = [saved_pk(target), saved_pk(sibling)] if listed else saved_pk(target)

    payload = _post(
        schema,
        "query($where: JSON!) { tags(where: $where) { id } }",
        {"where": {"chosen": value}},
    )

    assert _node_pks(payload, "tags") == (tags[:2] if listed else tags[:1]), payload


@pytest.mark.django_db
@pytest.mark.parametrize("listed", [False, True], ids=["model-choice", "model-multiple-choice"])
def test_a_model_choice_filter_through_a_generic_relation_keeps_the_tagged_rows(
    *,
    listed: bool,
) -> None:
    """The reverse of a ``GenericForeignKey`` is a relation Django joins, so it stays filterable.

    A tag chosen from ``TaggedItem``'s rows keeps the branch it is attached to.
    """
    target = models.Branch.objects.create(name="Target", city="Boston")
    sibling = models.Branch.objects.create(name="Sibling", city="Boston")
    _ = models.Branch.objects.create(name="Other", city="Boston")
    target_tag = models.TaggedItem.objects.create(content_object=target, tag="t")
    sibling_tag = models.TaggedItem.objects.create(content_object=sibling, tag="s")
    tags = models.TaggedItem.objects.order_by("pk")
    leaf = (
        ModelMultipleChoiceFilter(field_name="tags", queryset=tags)
        if listed
        else ModelChoiceFilter(field_name="tags", queryset=tags)
    )
    schema = _generic_relation_schema(leaf)
    value = [saved_pk(target_tag), saved_pk(sibling_tag)] if listed else saved_pk(target_tag)

    payload = _post(
        schema,
        "query($where: JSON!) { branches(where: $where) { id } }",
        {"where": {"tagged": value}},
    )

    expected = [saved_pk(target), saved_pk(sibling)] if listed else [saved_pk(target)]
    assert _node_pks(payload, "branches") == expected, payload


class _ObjectIdNumberFilter(NumberFilter):
    """A ``filter`` override keeping the tags whose object id is the number sent."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        if value is None:
            return qs
        return qs.filter(object_id=value)


def _column_generic_set(leaf: Filter) -> type[FilterSet]:
    """A ``TaggedItem`` set whose column-typed ``leaf`` names the ``GenericForeignKey``."""

    class ColumnGenericSet(FilterSet):
        tagged = leaf

        class Meta:
            model = models.TaggedItem
            fields = []

        def by_object(
            self,
            queryset: QuerySet[models.TaggedItem],
            name: str,
            value: object,
        ) -> QuerySet[models.TaggedItem]:
            del name
            return queryset.filter(object_id=value)

    return ColumnGenericSet


_COLUMN_GENERIC_SUBJECT = (
    "ColumnGenericSet: {kind} on 'content_object' reads "
    "TaggedItem.content_object, a GenericForeignKey: Django filters no queryset through it, so "
    "no input can carry its value"
)


_PAST_GENERIC_SUBJECT = (
    "ColumnGenericSet: {kind} on 'content_object__name' continues past "
    "TaggedItem.content_object, a GenericForeignKey: Django filters no queryset through it, so "
    "no input can carry its value"
)


#: Each column-typed leaf on the ``GenericForeignKey`` consumer code filters.
_CONSUMER_GENERIC_COLUMNS: dict[str, Callable[[], Filter]] = {
    "number-method": lambda: NumberFilter(field_name="content_object", method="by_object"),
    "number-filter-override": lambda: _ObjectIdNumberFilter(field_name="content_object"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("name", sorted(_CONSUMER_GENERIC_COLUMNS))
def test_an_unserved_column_filter_on_a_generic_foreign_key_filters_through_consumer_code(
    name: str,
) -> None:
    """A ``method`` or a ``filter`` override filters as it chooses: unserved, it answers rows.

    Neither runs the shipped comparison through the relation its ``field_name`` names,
    so publishing the set leaves it to its own code: these keep the tags whose object id
    is the number sent.
    """
    target = models.Branch.objects.create(name="Target", city="Boston")
    sibling = models.Branch.objects.create(name="Sibling", city="Boston")
    tags = [
        saved_pk(models.TaggedItem.objects.create(content_object=branch, tag=branch.name.lower()))
        for branch in (target, sibling)
    ]
    schema = _tagged_item_schema(
        _column_generic_set(_CONSUMER_GENERIC_COLUMNS[name]()),
        served=False,
    )

    payload = _post(
        schema,
        "query($where: JSON!) { tags(where: $where) { id } }",
        {"where": {"tagged": saved_pk(sibling)}},
    )

    assert _node_pks(payload, "tags") == tags[1:], payload


@pytest.mark.django_db
@pytest.mark.parametrize("name", sorted(_CONSUMER_GENERIC_COLUMNS))
def test_a_served_column_filter_on_a_generic_foreign_key_is_refused_by_its_input_build(
    name: str,
) -> None:
    """Served, consumer code still needs an input its value travels in: none types it.

    The set publishes the leaf (its own code filters it), and the input build refuses it,
    since no scalar types a ``GenericForeignKey``.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        _ = _tagged_item_schema(
            _column_generic_set(_CONSUMER_GENERIC_COLUMNS[name]()),
            served=True,
        )

    kind = "NumberFilter" if name == "number-method" else "_ObjectIdNumberFilter"
    expected = _COLUMN_GENERIC_SUBJECT.format(kind=kind)
    assert str(exc_info.value).startswith(expected), exc_info


#: Each column-typed leaf past the ``GenericForeignKey`` consumer code filters.
_CONSUMER_PAST_GENERIC_COLUMNS: dict[str, Callable[[], Filter]] = {
    "number-method": lambda: NumberFilter(field_name="content_object__id", method="by_object"),
    "number-filter-override": lambda: _ObjectIdNumberFilter(field_name="content_object__id"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("served", [True, False], ids=["served", "unserved"])
@pytest.mark.parametrize("name", sorted(_CONSUMER_PAST_GENERIC_COLUMNS))
def test_a_column_filter_past_a_generic_foreign_key_filters_through_consumer_code(
    name: str,
    *,
    served: bool,
) -> None:
    """A ``method`` or a ``filter`` override past the key filters as it chooses: rows.

    Neither hands Django the path its ``field_name`` spells, so the set publishes it served
    or unserved, and each keeps the tags whose object id is the number sent.
    """
    target = models.Branch.objects.create(name="Target", city="Boston")
    sibling = models.Branch.objects.create(name="Sibling", city="Boston")
    tags = [
        saved_pk(models.TaggedItem.objects.create(content_object=branch, tag=branch.name.lower()))
        for branch in (target, sibling)
    ]
    schema = _tagged_item_schema(
        _column_generic_set(_CONSUMER_PAST_GENERIC_COLUMNS[name]()),
        served=served,
    )

    payload = _post(
        schema,
        "query($where: JSON!) { tags(where: $where) { id } }",
        {"where": {"tagged": saved_pk(sibling)}},
    )

    assert _node_pks(payload, "tags") == tags[1:], payload


def _desk_route_parent(field_name: str = "content_object") -> type[FilterSet]:
    """A ``Branch`` set reaching a desk set's ``CharFilter`` on or past its ``GenericForeignKey``."""

    class DeskGenericChild(FilterSet):
        held = CharFilter(field_name=field_name)

        class Meta:
            model = models.CirculationDesk
            fields = []

    class DeskRouteParent(FilterSet):
        circulation_desks = RelatedFilter(DeskGenericChild, field_name="circulation_desks")

        class Meta:
            model = models.Branch
            fields = []

    return DeskRouteParent


def _with_callable_queryset(leaf: ModelChoiceFilter) -> ModelChoiceFilter:
    """``leaf`` holding ``_branch_rows`` uncalled, as django-filter's callable ``queryset``.

    The stubs type ``queryset`` as a ``QuerySet``; django-filter calls a callable one with the
    request when it builds the form field.
    """
    vars(leaf)["queryset"] = _branch_rows
    return leaf


def _tags_past_generic_set() -> type[FilterSet]:
    """A ``Branch`` set past its ``GenericRelation``, then past the key it reverses."""

    class BranchTagsPastSet(FilterSet):
        tag_object = NumberFilter(field_name="tags__content_object__id")

        class Meta:
            model = models.Branch
            fields = []

    return BranchTagsPastSet


#: Each shipped leaf ending on, or continuing past, a ``GenericForeignKey`` a served set
#: publishes, and the words its refusal starts with.
_SERVED_GENERIC_COLUMNS: dict[str, tuple[Callable[[], type[FilterSet]], str]] = {
    "choice": (
        lambda: _column_generic_set(
            ChoiceFilter(choices=[("a", "a")], field_name="content_object"),
        ),
        _COLUMN_GENERIC_SUBJECT.format(kind="ChoiceFilter"),
    ),
    "null-test": (
        lambda: _column_generic_set(
            BooleanFilter(field_name="content_object", lookup_expr="isnull"),
        ),
        _COLUMN_GENERIC_SUBJECT.format(kind="BooleanFilter"),
    ),
    "choice-past": (
        lambda: _column_generic_set(
            ChoiceFilter(choices=[("a", "a")], field_name="content_object__name"),
        ),
        _PAST_GENERIC_SUBJECT.format(kind="ChoiceFilter"),
    ),
    "callable-model-choice-past": (
        lambda: _column_generic_set(
            _with_callable_queryset(
                ModelChoiceFilter(field_name="content_object__name", queryset=_branch_rows()),
            ),
        ),
        _PAST_GENERIC_SUBJECT.format(kind="ModelChoiceFilter"),
    ),
    "past-a-generic-relation": (
        _tags_past_generic_set,
        (
            "BranchTagsPastSet: NumberFilter on 'tags__content_object__id' continues past "
            "TaggedItem.content_object, a GenericForeignKey: Django filters no queryset "
            "through it, so no input can carry its value"
        ),
    ),
    "related-filter-route-past": (
        lambda: _desk_route_parent("content_object__name"),
        (
            "DeskGenericChild: CharFilter on 'content_object__name' continues past "
            "CirculationDesk.content_object, a GenericForeignKey: Django filters no queryset "
            "through it, so no input can carry its value"
        ),
    ),
    "related-filter-route": (
        _desk_route_parent,
        (
            "DeskGenericChild: CharFilter on 'content_object' reads "
            "CirculationDesk.content_object, a GenericForeignKey: Django filters no queryset "
            "through it, so no input can carry its value"
        ),
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("name", sorted(_SERVED_GENERIC_COLUMNS))
def test_a_shipped_filter_on_a_generic_foreign_key_is_refused_when_the_schema_builds(
    name: str,
) -> None:
    """Whatever its class or lookup, a shipped leaf on a ``GenericForeignKey`` is refused.

    Django filters no queryset through one, so a choice filter or a null test there would
    answer every request with Django's ``FieldError``: the set refuses it when it
    publishes, naming the set that declares it (a ``RelatedFilter`` child's leaf names the
    child, with no route).
    """
    build, expected = _SERVED_GENERIC_COLUMNS[name]

    with pytest.raises(ConfigurationError) as exc_info:
        _ = _served_schema(build())

    assert str(exc_info.value).startswith(expected), exc_info
    assert "(reached through" not in str(exc_info.value), exc_info


@pytest.mark.django_db
@pytest.mark.parametrize("field_name", ["content_object", "content_object__name"])
def test_an_unserved_column_filter_on_a_generic_foreign_key_is_refused_at_first_use(
    caplog: pytest.LogCaptureFixture,
    field_name: str,
) -> None:
    """Applied unbound, the set publishes at its first use: the input build's refusal, logged.

    The request answers the masked error and the server log carries the
    ``ConfigurationError``, never a ``FieldError`` from the query.
    """
    branch = models.Branch.objects.create(name="Target", city="Boston")
    _ = models.TaggedItem.objects.create(content_object=branch, tag="t")
    schema = _tagged_item_schema(
        _column_generic_set(CharFilter(field_name=field_name)),
        served=False,
    )
    unfiltered = _post(schema, "{ tags { tag } }")
    assert unfiltered == {"data": {"tags": [{"tag": "t"}]}}, unfiltered
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")

    payload = _post(
        schema,
        "query($where: JSON!) { tags(where: $where) { tag } }",
        {"where": {"tagged": "x"}},
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
    subject = _COLUMN_GENERIC_SUBJECT if field_name == "content_object" else _PAST_GENERIC_SUBJECT
    assert str(exc_info[1]).startswith(subject.format(kind="CharFilter")), exc_info[1]


def _annotated_desks(
    _cls: type[DjangoType],
    queryset: QuerySet[Model],
    _info: object,
    **_kwargs: object,
) -> QuerySet[Model]:
    """The desks with their branch as a ``FilteredRelation`` alias and its name as text."""
    return queryset.annotate(
        on_branch=FilteredRelation("branch"),
        branch_label=F("branch__name"),
    )


@pytest.mark.django_db
@pytest.mark.parametrize("listed", [False, True], ids=["model-choice", "model-multiple-choice"])
@pytest.mark.parametrize("field_name", ["on_branch", "branch_label"])
def test_a_model_choice_filter_on_a_name_only_the_served_queryset_holds_serves_rows(
    field_name: str,
    *,
    listed: bool,
) -> None:
    """A path the model lacks is left to the request: the type's queryset may hold it.

    A ``FilteredRelation`` alias and a text annotation of the type's ``get_queryset`` are
    no field of ``CirculationDesk``, yet the input typed from the filter's ``queryset``
    keeps the desk on the chosen branch (the text compared as the branch's ``str``).
    """
    first = models.Branch.objects.create(name="First", city="Boston")
    second = models.Branch.objects.create(name="Second", city="Boston")
    content_type = ContentType.objects.get_for_model(models.Branch)
    desks = [
        saved_pk(
            models.CirculationDesk.objects.create(
                name=f"desk-{branch.name}",
                branch=branch,
                shelf=models.Shelf.objects.create(code=branch.name, branch=branch),
                content_type=content_type,
                object_id=branch.pk,
            ),
        )
        for branch in (first, second)
    ]
    leaf = (
        ModelMultipleChoiceFilter(field_name=field_name, queryset=_branch_rows())
        if listed
        else ModelChoiceFilter(field_name=field_name, queryset=_branch_rows())
    )

    class AnnotatedDeskSet(FilterSet):
        chosen = leaf

        class Meta:
            model = models.CirculationDesk
            fields = []

    registry.clear()

    @strawberry.type
    class Query:
        desks = DjangoConnectionField(
            make_django_type(
                "AnnotatedDeskNode",
                models.CirculationDesk,
                ("id", "name"),
                meta_extra={"filterset_class": AnnotatedDeskSet},
                namespace_extra={"get_queryset": classmethod(_annotated_desks)},
            ),
        )

    finalize_django_types()
    schema = DjangoSchema(query=Query, config=strawberry_config())
    value = f"[{saved_pk(first)}]" if listed else str(saved_pk(first))

    payload = _post(
        schema,
        f"{{ desks(filter: {{ chosen: {{ exact: {value} }} }}) {{ edges {{ node {{ id }} }} }} }}",
    )

    assert "errors" not in payload, payload
    edges = json_list(json_object(payload, "data", "desks"), "edges")
    found = [int(relay.GlobalID.from_id(json_str(edge, "node", "id")).node_id) for edge in edges]
    assert found == desks[:1], payload


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


class _OverridingGlobalIDFilter(GlobalIDFilter):
    """A consumer ``filter`` override that answers as the package's GlobalID filter does."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        return super().filter(qs, value)


#: Each keyed shape's walking model and leaf path: a ``*-key`` shape spells the relation
#: key, the others a leaf ending on ``Book``'s key (``__id``, or ``__pk`` for a ``*-pk``
#: shape).
_KEYED_PATHS: dict[str, tuple[type[Model], str]] = {
    "foreign-reverse-foreign-key": (models.Book, "shelf__books__id"),
    "foreign-many-to-many": (models.Book, "genres__books__id"),
    "foreign-reverse-foreign-key-key": (models.Book, "shelf__books"),
    "foreign-many-to-many-key": (models.Book, "genres__books"),
    "foreign-declared-hop-key": (models.Shelf, "books"),
    "foreign-declared-last-hop-key": (models.Book, "shelf__books"),
    "owned-reentry": (models.Book, "shelf__books__id"),
    "owned-relation": (models.Shelf, "books__id"),
    "owned-reentry-key": (models.Book, "shelf__books"),
    "owned-relation-key": (models.Shelf, "books"),
    "owned-forward-key": (models.Loan, "book"),
    "owned-unbound-hop-key": (models.Shelf, "books"),
    "owned-unbound-forward-hop-key": (models.Loan, "book"),
    "owned-unbound-hop": (models.Shelf, "books__id"),
    "owned-unbound-hop-pk": (models.Shelf, "books__pk"),
    "owned-unbound-forward-hop": (models.Loan, "book__id"),
    "owned-unbound-forward-hop-pk": (models.Loan, "book__pk"),
    "override-relation-key": (models.Shelf, "books"),
    "override-forward-key": (models.Loan, "book"),
}


def _keyed_set(shape: str) -> tuple[type[FilterSet], tuple[type[DjangoType], ...]]:
    """The walking set of a keyed ``shape``, and the types its declared hops read.

    A ``*-hop*`` shape declares its relation as a ``RelatedFilter`` hop into a ``Book``
    set that no type wires, or (``foreign-*``) that a scoping ``type`` secondary wires; a
    leaf ending on ``Book``'s key walks that hop. The declared last hop walks a declared
    ``shelf`` hop, then its ``books`` hop back into the walking set.
    """
    model, key = _KEYED_PATHS[shape]
    leaf_filter = (_OverridingGlobalIDFilter if shape.startswith("override-") else GlobalIDFilter)(
        field_name=key,
    )
    if shape == "foreign-declared-last-hop-key":

        class KeyedShelfFilter(FilterSet):
            books = RelatedFilter(lambda: KeyedBookFilter, field_name="books")

            class Meta:
                model = models.Shelf
                fields = []

        class KeyedBookFilter(FilterSet):
            shelf = RelatedFilter(KeyedShelfFilter, field_name="shelf")
            leaf = leaf_filter

            class Meta:
                model = models.Book
                fields = []

        return KeyedBookFilter, (make_django_type("ReentryKeyedShelf", models.Shelf, ("id",)),)
    if "-hop" not in shape:
        return _declared_set(model, leaf_filter), ()
    child = type(
        "KeyedHopBookFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": models.Book, "fields": []})},
    )
    hop_types = (
        (
            make_django_type(
                "ReentryKeyedHopBook",
                models.Book,
                ("id",),
                meta_extra={
                    "primary": False,
                    "globalid_strategy": "type",
                    "filterset_class": child,
                },
                namespace_extra={"get_queryset": _hiding(0)},
            ),
        )
        if shape.startswith("foreign-")
        else ()
    )
    filterset = type(
        "ReentryFilter",
        (FilterSet,),
        {
            "hop": RelatedFilter(child, field_name=key.removesuffix("__id").removesuffix("__pk")),
            "leaf": leaf_filter,
            "Meta": type("Meta", (), {"model": model, "fields": []}),
        },
    )
    return filterset, hop_types


def _keyed_leaf(rows: _Library, shape: str) -> _Reentry:
    """A GlobalID leaf or relation key into ``Book``, whose primary's ``NodeID`` is ``node_key``.

    ``node_key`` is an annotation the primary's ``get_queryset`` adds, so only rows the
    primary answers for carry it. ``foreign-*`` shapes walk ``shelf__books`` or
    ``genres__books`` (the key, or its leaf ending on ``__id``) on a ``Book`` set wired to
    a scoping ``type`` secondary, whose rows lack it, the declared last hop back into
    that set, or ``books`` on a ``Shelf`` set through a declared hop into a set another
    secondary wires. ``owned-reentry*`` walks ``shelf__books`` on a ``Book`` set wired to
    the primary itself, ``owned-relation*`` ``books`` on a ``Shelf`` set and
    ``owned-forward-key`` ``book`` on a ``Loan`` set, all over rows the primary answers
    for, as do the ``owned-unbound-*`` keys and leaves through a declared hop into a set no
    type wires. An ``override-*`` key's class overrides ``filter``. ``refused`` names
    ``bk1``'s handle as a ``library.shelf`` id.
    """
    model, _key = _KEYED_PATHS[shape]
    filterset, hop_types = _keyed_set(shape)
    wired = {"filterset_class": filterset, "connection": {"total_count": True}}
    reentry = shape.startswith("owned-reentry")
    primary = make_django_type(
        "ReentryKeyedBook",
        models.Book,
        ("id",),
        meta_extra={"primary": True, "globalid_strategy": "model", **(wired if reentry else {})},
        namespace_extra={
            "__annotations__": {"node_key": relay.NodeID[str]},
            "get_queryset": _keyed(),
        },
    )
    if reentry:
        root, types = primary, hop_types
    elif model is models.Book:
        root = make_django_type(
            "ReentryKeyedSecondary",
            models.Book,
            ("id",),
            meta_extra={"primary": False, "globalid_strategy": "type", **wired},
            namespace_extra={"get_queryset": _hiding(0)},
        )
        types = (primary, *hop_types)
    else:
        root = make_django_type(f"ReentryKeyed{model.__name__}", model, ("id",), meta_extra=wired)
        types = (primary, *hop_types)
    books = rows.books
    # A ``foreign-*`` or ``override-*`` shape answers no rows: the id is refused.
    expected = (
        []
        if shape.startswith(("foreign-", "override-"))
        else _pks(books["bk1"], books["bk2"])
        if reentry
        else _pks(rows.loans["l1"], rows.loans["l2"])
        if model is models.Loan
        else _pks(rows.shelves["s1"])
    )
    handle = f"{_KEY_PREFIX}{saved_pk(books['bk1'])}"
    return _Reentry(
        filterset,
        root,
        types,
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("library.book", handle),
        expected,
        _gid("library.shelf", handle),
        _mismatch("library.book", "library.shelf", listed=False),
        listed=False,
    )


#: The coded refusal of ``node_key`` over rows its type does not answer for.
_KEYED_REFUSAL = (
    "GlobalID filter target ReentryKeyedBook carries its id in 'node_key', which no "
    "model column holds, so a filter across a relation cannot compare it."
)
_REFUSED_KEYED = [
    *(shape for shape in _KEYED_PATHS if shape.startswith("foreign-")),
    "override-relation-key",
    "override-forward-key",
]


def _keyed_answer(world: _Reentry, global_id: str, driver: str) -> tuple[list[int] | str, int]:
    """``_reentry_answer`` and the number of statements the request ran."""
    with CaptureQueriesContext(connection) as captured:
        answer = _reentry_answer(world, global_id, driver)
    return answer, len(captured.captured_queries)


@pytest.mark.django_db
@pytest.mark.parametrize("driver", ["live", "apply-sync", "form"])
@pytest.mark.parametrize("shape", _REFUSED_KEYED)
def test_a_reentry_leaf_refuses_an_id_an_annotation_holds_over_rows_another_type_scopes(
    shape: str,
    driver: str,
) -> None:
    """The primary's ``node_key`` is not on rows a secondary answers for: a coded refusal.

    The leaf ending on the key and the bare key refuse it alike, through undeclared or
    declared hops, before any statement runs, never comparing it on the walk's rows. A
    key whose class overrides ``filter`` runs as declared across the relation, on the
    walking set's own rows, which the primary's hook never touched, and refuses it too.
    """
    world = _keyed_leaf(_library(), shape)

    assert _keyed_answer(world, world.accepted, driver) == (_KEYED_REFUSAL, 0)


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["foreign-reverse-foreign-key-key", "override-relation-key"])
def test_an_annotation_id_refused_over_another_types_rows_is_coded_unvalidatable(
    shape: str,
) -> None:
    """The refusal of ``node_key`` carries ``GLOBALID_UNVALIDATABLE`` on the wire."""
    world = _keyed_leaf(_library(), shape)
    literal = _wire_literal(world.wire, world.value(world.accepted))

    payload = _post(
        _reentry_schema(world),
        f"{{ rows(filter: {literal}) {{ edges {{ node {{ id }} }} }} }}",
    )

    assert json_str(payload, "errors", 0, "message") == _KEYED_REFUSAL
    assert json_at(payload, "errors", 0, "extensions", "code") == "GLOBALID_UNVALIDATABLE"


#: ``applied`` serves the model's own rows, which lack the ``node_key`` the keyed primary's
#: ``id`` reads, so the set wired to that primary answers live and on the raw form.
_OWNED_KEYED_ROWS = [
    pytest.param(shape, driver, id=f"{shape}-{driver}")
    for shape in _KEYED_PATHS
    if shape.startswith("owned-")
    for driver in ("live", "apply-sync", "form")
    if not shape.startswith("owned-reentry") or driver != "apply-sync"
]


@pytest.mark.django_db
@pytest.mark.parametrize(("shape", "driver"), _OWNED_KEYED_ROWS)
def test_a_leaf_compares_an_id_an_annotation_holds_over_rows_its_type_scopes(
    shape: str,
    driver: str,
) -> None:
    """Over rows the primary answers for, its ``node_key`` annotation is compared there.

    The relation key compares it as its leaf ending on the key does, forward or to-many,
    through undeclared hops or a declared hop into a set no type wires (where the leaf,
    ``__id`` or ``__pk``, names a row of the type registered for ``Book``, as the key
    does, never the unwired set's own scalar key), in one statement.
    """
    world = _keyed_leaf(_library(), shape)

    assert _keyed_answer(world, world.accepted, driver) == (world.expected, 1)


@pytest.mark.django_db
@pytest.mark.parametrize(("shape", "driver"), _OWNED_KEYED_ROWS)
def test_a_leaf_over_rows_an_annotation_id_type_scopes_refuses_another_types_id(
    shape: str,
    driver: str,
) -> None:
    """An id of another type is a type mismatch, on the key as on its leaf ending on the key."""
    world = _keyed_leaf(_library(), shape)

    assert _keyed_answer(world, world.refused, driver) == (world.refusal, 0)


_ASYNC_KEYED = ["owned-relation-key", "owned-unbound-hop", "foreign-reverse-foreign-key-key"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("shape", _ASYNC_KEYED)
def test_a_relation_key_applied_async_compares_an_annotation_id_only_over_its_types_rows(
    shape: str,
) -> None:
    """``apply_async`` compares ``node_key`` over the primary's rows and refuses it elsewhere.

    So does a leaf ending on ``Book``'s key past a declared hop into a set no type wires.
    """
    rows = _library()
    world = _keyed_leaf(rows, shape)

    assert _reentry_answer(world, world.accepted, "apply-async") == (
        _pks(rows.shelves["s1"]) if shape.startswith("owned-") else _KEYED_REFUSAL
    )


def _secondary_hop_leaf(rows: _Library, shape: str) -> _Reentry:
    """A leaf ending on ``Book``'s key past a declared hop into a set a ``type`` secondary wires.

    ``books__id`` on a ``Shelf`` set (``reverse-foreign-key``) or ``book__id`` on a ``Loan``
    set (``forward``) walks its declared hop into ``SecondaryHopBookFilter``, which the
    secondary ``SecondaryHopBook`` wires beside the primary ``SecondaryHopBookPrimary``:
    the leaf decodes against the secondary that set is bound to, while the relation's key
    validates against the primary, so the secondary's id names ``bk1`` and the primary's
    is a type mismatch.
    """
    model, key = (
        (models.Shelf, "books__id")
        if shape == "reverse-foreign-key"
        else (models.Loan, "book__id")
    )
    child = type(
        "SecondaryHopBookFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": models.Book, "fields": []})},
    )
    filterset = type(
        "ReentryFilter",
        (FilterSet,),
        {
            "hop": RelatedFilter(child, field_name=key.removesuffix("__id")),
            "leaf": GlobalIDFilter(field_name=key),
            "Meta": type("Meta", (), {"model": model, "fields": []}),
        },
    )
    primary = make_django_type(
        "SecondaryHopBookPrimary",
        models.Book,
        ("id",),
        meta_extra={"primary": True, "globalid_strategy": "type"},
    )
    secondary = make_django_type(
        "SecondaryHopBook",
        models.Book,
        ("id",),
        meta_extra={"primary": False, "globalid_strategy": "type", "filterset_class": child},
    )
    root = make_django_type(
        f"SecondaryHop{model.__name__}",
        model,
        ("id",),
        meta_extra={"filterset_class": filterset, "connection": {"total_count": True}},
    )
    book = rows.books["bk1"]
    return _Reentry(
        filterset,
        root,
        (primary, secondary),
        ("leaf", "exact"),
        ("leaf", "exact"),
        "leaf",
        _gid("SecondaryHopBook", book),
        _pks(rows.loans["l1"], rows.loans["l2"])
        if model is models.Loan
        else _pks(rows.shelves["s1"]),
        _gid("SecondaryHopBookPrimary", book),
        _mismatch("SecondaryHopBook", "SecondaryHopBookPrimary", listed=False),
        listed=False,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("driver", ["live", "apply-sync", "form"])
@pytest.mark.parametrize("shape", ["reverse-foreign-key", "forward"])
def test_a_leaf_past_a_hop_into_a_secondary_wired_set_decodes_against_that_secondary(
    shape: str,
    driver: str,
) -> None:
    """The secondary the hop's set is bound to names the leaf's row; the primary's id is refused.

    Only a hop into a set no type wires reads the leaf as the type registered for the
    relation's target.
    """
    world = _secondary_hop_leaf(_library(), shape)

    assert _reentry_answer(world, world.accepted, driver) == world.expected
    assert _reentry_answer(world, world.refused, driver) == world.refusal


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


class _AliasShape(NamedTuple):
    """A ``FilteredRelation`` alias of the rows a GlobalID filter runs over, and its relation.

    ``alias`` joins ``relation`` (its twin, the same Python path over the model's own
    relations) from ``model``'s rows into ``target``'s; ``add`` adds it to a queryset.
    ``own`` and ``hidden`` name the target rows a request sends by ``_library`` name.
    """

    model: type[Model]
    relation: str
    alias: str
    target: type[Model]
    add: Callable[[QuerySet[Model]], QuerySet[Model]]
    own: str
    hidden: str


def _vshelf(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(vshelf=FilteredRelation("shelf"))


def _vbooks(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(vbooks=FilteredRelation("books"))


def _vgenres(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(vgenres=FilteredRelation("genres"))


def _vbranch(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(vshelf=FilteredRelation("shelf"), vbranch=FilteredRelation("vshelf__branch"))


def _vshelf_past_s1(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(vshelf=FilteredRelation("shelf", condition=~Q(shelf__code="s1")))


def _vbooks_past_bk1(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(vbooks=FilteredRelation("books", condition=~Q(books__title="bk1")))


def _vgenres_past_first_genre(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(vgenres=FilteredRelation("genres", condition=~Q(genres__name="g1")))


def _vbranch_past_s1(rows: QuerySet[Model]) -> QuerySet[Model]:
    return rows.alias(
        vshelf=FilteredRelation("shelf", condition=~Q(shelf__code="s1")),
        vbranch=FilteredRelation("vshelf__branch"),
    )


_ALIAS_SHAPES: dict[str, _AliasShape] = {
    "forward": _AliasShape(
        models.Book,
        "shelf",
        "vshelf",
        models.Shelf,
        _vshelf,
        "s1",
        "s2",
    ),
    "reverse": _AliasShape(
        models.Shelf,
        "books",
        "vbooks",
        models.Book,
        _vbooks,
        "bk1",
        "bk3",
    ),
    "many-to-many": _AliasShape(
        models.Book,
        "genres",
        "vgenres",
        models.Genre,
        _vgenres,
        "g1",
        "g2",
    ),
    "alias-over-alias": _AliasShape(
        models.Book,
        "shelf__branch",
        "vbranch",
        models.Branch,
        _vbranch,
        "b1",
        "b2",
    ),
}


def _named_row(rows: _Library, name: str) -> Model:
    """The ``_library`` row named ``name``, whichever table holds it."""
    tables: tuple[Mapping[str, Model], ...] = (
        rows.branches,
        rows.shelves,
        rows.genres,
        rows.books,
    )
    return next(table[name] for table in tables if name in table)


def _joined_pks(shape: _AliasShape, target: Model) -> list[int]:
    """The rows of ``shape.model`` whose ``relation`` reaches ``target``, as Django joins it."""
    joined = shape.model._default_manager.filter(**{shape.relation: saved_pk(target)})
    return sorted({saved_pk(row) for row in joined})


def _gid_leaf(field_name: str, *, listed: bool) -> Filter:
    """A ``GlobalIDFilter`` over ``field_name``, or its multiple-choice ``in`` sibling."""
    if listed:
        return GlobalIDMultipleChoiceFilter(field_name=field_name, lookup_expr="in")
    return GlobalIDFilter(field_name=field_name)


def _aliasing(
    add: Callable[[QuerySet[Model]], QuerySet[Model]],
) -> "classmethod[DjangoType, ..., QuerySet[Model]]":
    """A ``get_queryset`` hook adding ``add``'s ``FilteredRelation`` alias to the type's rows."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return add(queryset)

    return classmethod(get_queryset)


def _alias_target(
    model: type[Model],
    strategy: object = "model",
    *,
    hidden: Model | None = None,
    node: bool = True,
    namespace: Mapping[str, object] | None = None,
    fields: tuple[str, ...] = ("id",),
) -> type[DjangoType]:
    """``AliasTarget``, the primary over ``model`` the alias and its twin decode against.

    ``strategy`` is its ``globalid_strategy`` (``None`` for none); with ``hidden`` its
    ``get_queryset`` hides that row.
    """
    meta: dict[str, object] = {"primary": True}
    if strategy is not None:
        meta["globalid_strategy"] = strategy
    extra: dict[str, object] = dict(namespace or {})
    if hidden is not None:
        extra["get_queryset"] = _hiding(saved_pk(hidden))
    return make_django_type(
        "AliasTarget",
        model,
        fields,
        node=node,
        meta_extra=meta,
        namespace_extra=extra,
    )


#: Where a world's alias is added: on the queryset handed to the set, by the rows type's
#: ``get_queryset``, or by the set's own ``filter_queryset`` override.
_HANDED = "handed"
_TYPE_HOOK = "get_queryset"
_FILTER_QUERYSET = "filter_queryset"


@dataclass(frozen=True)
class _AliasWorld:
    """A set over ``model`` declaring ``leaves`` and the rows each driver hands it.

    ``rows`` is the queryset the resolvers and the raw form hand the set (the alias added
    where ``placement`` adds it); with ``served`` the rows type serves the set as a
    filtered connection.
    """

    schema: DjangoSchema
    filterset: type[FilterSet]
    rows: Callable[[], QuerySet[Model]]
    served: bool


def _alias_world(
    shape: _AliasShape,
    leaves: Mapping[str, Callable[[], Filter]],
    target_types: Callable[[], tuple[type[DjangoType], ...]],
    *,
    placement: str = _HANDED,
    served: bool = True,
    methods: Mapping[str, object] | None = None,
) -> _AliasWorld:
    """Serve a set declaring ``leaves`` (and ``methods``) over ``shape``'s rows beside ``target_types``.

    The rows type ``AliasRows`` mints ``model`` ids for ``shape.model``; ``applied`` /
    ``appliedAsync`` hand the set its rows through that type's ``get_queryset``, as a
    resolver reading the type's rows does.
    """
    registry.clear()
    namespace: dict[str, object] = {name: leaf() for name, leaf in leaves.items()}
    namespace.update(methods or {})
    namespace["Meta"] = type("Meta", (), {"model": shape.model, "fields": []})
    if placement == _FILTER_QUERYSET:

        def filter_queryset(self: FilterSet, queryset: QuerySet[Model]) -> QuerySet[Model]:
            return FilterSet.filter_queryset(self, shape.add(queryset))

        namespace["filter_queryset"] = filter_queryset
    filterset = type("AliasFilter", (FilterSet,), namespace)
    types = target_types()
    meta: dict[str, object] = {"primary": True, "globalid_strategy": "model"}
    if served:
        meta.update(filterset_class=filterset, connection={"total_count": True})
    root = make_django_type(
        "AliasRows",
        shape.model,
        ("id",),
        meta_extra=meta,
        namespace_extra={"get_queryset": _aliasing(shape.add)}
        if placement == _TYPE_HOOK
        else None,
    )

    def handed() -> QuerySet[Model]:
        rows = shape.model._default_manager.order_by("pk")
        return shape.add(rows) if placement == _HANDED else rows

    def typed_rows(info: object) -> QuerySet[Model]:
        typed: QuerySet[Model] = root.get_queryset(handed(), info)
        return typed

    def _all_rows(_root: object, _info: object) -> QuerySet[Model]:
        return handed()

    def _applied(info: Info[object, object], where: JSON) -> QuerySet[Model]:
        return filterset.apply_sync(where, typed_rows(info), info)

    async def _applied_async(info: Info[object, object], where: JSON) -> list[Model]:
        rows = await filterset.apply_async(where, typed_rows(info), info)
        return await sync_to_async(list)(rows)

    applied_type = StrawberryList(root)
    if served:

        @strawberry.type
        class ServedQuery:
            rows = DjangoConnectionField(root, resolver=_all_rows)
            applied: QuerySet[Model] = strawberry.field(
                resolver=_applied,
                graphql_type=applied_type,
            )
            applied_async: list[Model] = strawberry.field(
                resolver=_applied_async,
                graphql_type=applied_type,
            )

        query: type[object] = ServedQuery
    else:

        @strawberry.type
        class UnservedQuery:
            applied: QuerySet[Model] = strawberry.field(
                resolver=_applied,
                graphql_type=applied_type,
            )
            applied_async: list[Model] = strawberry.field(
                resolver=_applied_async,
                graphql_type=applied_type,
            )

        query = UnservedQuery
    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(query=query, types=types, extensions=[lambda: optimizer])
    return _AliasWorld(schema, filterset, functools.partial(typed_rows, None), served)


class _Said(NamedTuple):
    """What one request answers: the rows' keys or an error's message, its code, its statements."""

    answer: list[int] | str
    code: object
    statements: int


#: Every driver a served world answers through; an unserved world has no connection.
_ALIAS_DRIVERS = (
    "live",
    "apply-sync",
    "apply-async",
    "form",
)


def _alias_said(
    world: _AliasWorld,
    leaf: str,
    value: str | list[str] | None,
    driver: str,
    recorded: list[str],
) -> _Said:
    """What ``driver`` answers for ``value`` sent to ``world``'s ``leaf``.

    A list value (or ``None`` for a listed leaf) is sent to the ``in`` lookup, any other
    to ``exact``; ``recorded`` is the statement recorder the count is read from.
    """
    listed = isinstance(world.filterset.base_filters[leaf], GlobalIDMultipleChoiceFilter)
    lookup = "in" if listed else "exact"
    before = len(recorded)
    if driver == "form":
        bound = world.filterset(data={leaf: value}, queryset=world.rows())
        try:
            found = sorted(
                saved_pk(require_instance(row, Model)) for row in require(bound.qs, is_queryset)
            )
        except GraphQLError as exc:
            code = None if exc.extensions is None else exc.extensions.get("code")
            return _Said(exc.message, code, len(recorded) - before)
        return _Said(found, None, len(recorded) - before)
    if driver == "live":
        literal = _wire_literal((leaf, lookup), value) if value is not None else None
        literal = literal or f"{{{leaf}: {{{lookup}: null}}}}"
        payload = _post(
            world.schema,
            f"{{ rows(filter: {literal}) {{ edges {{ node {{ id }} }} }} }}",
        )
        path: tuple[str, ...] = ("rows", "edges")
    else:
        where: JSONObject = {leaf: {"in_" if listed else lookup: value}}
        field = "appliedAsync" if driver == "apply-async" else "applied"
        document = f"query($where: JSON!) {{ {field}(where: $where) {{ id }} }}"
        payload = (
            asyncio.run(_async_post(world.schema, document, {"where": where}))
            if driver == "apply-async"
            else _post(world.schema, document, {"where": where})
        )
        path = (field,)
    statements = len(recorded) - before
    if payload.get("errors"):
        extensions = json_object(payload, "errors", 0).get("extensions")
        return _Said(
            json_str(payload, "errors", 0, "message"),
            json_object(extensions).get("code") if extensions is not None else None,
            statements,
        )
    node_ids = [
        json_str(row, "node", "id") if driver == "live" else json_str(row, "id")
        for row in json_list(payload, "data", *path)
    ]
    return _Said(
        sorted(int(relay.GlobalID.from_id(node_id).node_id) for node_id in node_ids),
        None,
        statements,
    )


class _AliasValue(NamedTuple):
    """A value sent to the alias and to its twin, and what both answer for it.

    ``twin_statements``, when given, is the twin's own statement count where its route
    runs a different number of statements to the same answer.
    """

    name: str
    value: str | list[str] | None
    expected: _Said
    twin_statements: int | None = None


def _sent(type_name: str, row: Model | str, *, listed: bool) -> str | list[str]:
    """``row`` encoded under ``type_name``, in a list where the leaf takes one."""
    global_id = _gid(type_name, row)
    return [global_id] if listed else global_id


def _every_pk(shape: _AliasShape) -> list[int]:
    return sorted(saved_pk(row) for row in shape.model._default_manager.all())


def _assert_alias_answers_as_its_twin(
    world: _AliasWorld,
    values: list[_AliasValue],
    recorded: list[str],
) -> None:
    """Each value answers ``expected`` through the alias leaf and its twin, on every driver."""
    drivers = _ALIAS_DRIVERS if world.served else _ALIAS_DRIVERS[1:]
    for value in values:
        for driver in drivers:
            said = _alias_said(world, "alias", value.value, driver, recorded)
            twin = _alias_said(world, "twin", value.value, driver, recorded)
            assert said == value.expected, (value.name, driver, said)
            if value.twin_statements is not None:
                assert twin.statements == value.twin_statements, (value.name, driver, twin)
                twin = twin._replace(statements=said.statements)
            assert twin == said, (value.name, driver, twin)


def _twin_leaves(
    shape: _AliasShape,
    suffix: str,
    *,
    listed: bool,
) -> dict[str, Callable[[], Filter]]:
    """``alias`` over the alias spelled with ``suffix`` and ``twin`` over its relation."""
    return {
        "alias": functools.partial(_gid_leaf, f"{shape.alias}{suffix}", listed=listed),
        "twin": functools.partial(_gid_leaf, f"{shape.relation}{suffix}", listed=listed),
    }


#: Each leaf spelling: the bare alias, or its target's key past it.
_ALIAS_FORMS = {"bare": "", "id": "__id", "pk": "__pk"}
_ALIAS_WORLDS = [
    *(
        pytest.param(
            shape,
            form,
            scoped,
            listed,
            id=f"{shape}-{form}-{'scoped' if scoped else 'unscoped'}-"
            f"{'multiple' if listed else 'single'}",
        )
        for shape in _ALIAS_SHAPES
        for form in ("bare", "id")
        for scoped in (True, False)
        for listed in (False, True)
    ),
    pytest.param("forward", "pk", False, False, id="forward-pk-unscoped-single"),
    pytest.param("reverse", "pk", False, False, id="reverse-pk-unscoped-single"),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "shape_name",
        "form",
        "scoped",
        "listed",
    ),
    _ALIAS_WORLDS,
)
def test_a_global_id_filter_over_a_filtered_relation_alias_answers_as_over_its_relation(
    shape_name: str,
    form: str,
    *,
    scoped: bool,
    listed: bool,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A GlobalID filter starting at an alias decodes against its relation's target type.

    ``vshelf`` (forward), ``vbooks`` (reverse), ``vgenres`` (many-to-many) and ``vbranch``
    (over the ``vshelf`` alias), bare or past to the target's key, answer what the same
    filter over the relation answers, on the connection, ``apply_sync``, ``apply_async``
    and the raw form: the target's own id its rows, a hidden target row's none where its
    type scopes them, an id of another type or the other spelling of the target's own a
    type mismatch before any statement, ``null`` every row and ``[]`` none.
    """
    rows = _library()
    shape = _ALIAS_SHAPES[shape_name]
    strategy = "type" if listed else "model"
    hidden = _named_row(rows, shape.hidden)
    world = _alias_world(
        shape,
        _twin_leaves(shape, _ALIAS_FORMS[form], listed=listed),
        lambda: (_alias_target(shape.target, strategy, hidden=hidden if scoped else None),),
    )
    label = shape.target._meta.label_lower
    accepted, other = ("AliasTarget", label) if strategy == "type" else (label, "AliasTarget")
    wrong = shape.model._meta.label_lower
    own = _named_row(rows, shape.own)
    values = [
        _AliasValue(
            "own",
            _sent(accepted, own, listed=listed),
            _Said(_joined_pks(shape, own), None, 1),
        ),
        _AliasValue(
            "wrong-type",
            _sent(wrong, own, listed=listed),
            _Said(_mismatch(accepted, wrong, listed=listed), None, 0),
        ),
        _AliasValue(
            "other-spelling",
            _sent(other, own, listed=listed),
            _Said(_mismatch(accepted, other, listed=listed), None, 0),
        ),
        _AliasValue("null", None, _Said(_every_pk(shape), None, 1)),
    ]
    if scoped:
        values.append(
            _AliasValue("hidden", _sent(accepted, hidden, listed=listed), _Said([], None, 1)),
        )
    if listed:
        # ``[]`` matches no row: a hop the target type scopes is read first, unless the
        # leaf folds into one forward join; ``shelf__branch`` walks its unscoped ``shelf``
        # hop where ``vbranch`` joins both relations as one alias.
        walks = scoped and (form != "bare" or shape_name in {"reverse", "many-to-many"})
        values.append(
            _AliasValue(
                "empty",
                [],
                _Said([], None, int(walks)),
                1 if scoped and form == "bare" and shape_name == "alias-over-alias" else None,
            ),
        )

    _assert_alias_answers_as_its_twin(world, values, record_compiled_sql("library_"))


def _alias_answers(
    world: _AliasWorld,
    leaf: str,
    values: Mapping[str, str | list[str]],
    recorded: list[str],
) -> dict[tuple[str, str], _Said]:
    """Every answer ``world``'s ``leaf`` gives each of ``values`` on each of its drivers."""
    drivers = _ALIAS_DRIVERS if world.served else _ALIAS_DRIVERS[1:]
    return {
        (name, driver): _alias_said(world, leaf, value, driver, recorded)
        for name, value in values.items()
        for driver in drivers
    }


_ENCODE_ONLY_WORLDS = [
    pytest.param(shape, form, target, id=f"{shape}-{form}-{target}")
    for shape in ("forward", "reverse")
    for form in ("bare", "id")
    for target in ("callable", "non-relay")
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(("shape_name", "form", "target"), _ENCODE_ONLY_WORLDS)
def test_an_encode_only_or_non_relay_target_through_a_filtered_relation_alias_is_refused_per_request(
    shape_name: str,
    form: str,
    target: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The schema build cannot see the alias: a request refuses its target as the twin's.

    A wired set over the relation itself is refused when the schema builds for a
    ``callable`` target, and is refused per request for a non-Relay one; the alias builds,
    and every well-formed id answers ``GLOBALID_UNVALIDATABLE`` before any statement, as
    the twin does (applied unserved, for the ``callable`` target).
    """
    rows = _library()
    shape = _ALIAS_SHAPES[shape_name]
    listed = shape_name == "reverse"
    suffix = _ALIAS_FORMS[form]

    def targets() -> tuple[type[DjangoType], ...]:
        if target == "callable":
            return (_alias_target(shape.target, _encode_by_name),)
        return (_alias_target(shape.target, None, node=False),)

    def leaf(field_name: str) -> dict[str, Callable[[], Filter]]:
        return {"leaf": functools.partial(_gid_leaf, field_name, listed=listed)}

    own = _named_row(rows, shape.own)
    values = {
        name: _sent(type_name, own, listed=listed)
        for name, type_name in (
            ("type-name", "AliasTarget"),
            ("model-label", shape.target._meta.label_lower),
            ("wrong-type", shape.model._meta.label_lower),
        )
    }
    recorded = record_compiled_sql("library_")
    if target == "callable":
        with pytest.raises(ConfigurationError, match="AliasTarget"):
            _ = _alias_world(shape, leaf(f"{shape.relation}{suffix}"), targets)
    twin = _alias_answers(
        _alias_world(
            shape,
            leaf(f"{shape.relation}{suffix}"),
            targets,
            served=target != "callable",
        ),
        "leaf",
        values,
        recorded,
    )
    said = _alias_answers(
        _alias_world(shape, leaf(f"{shape.alias}{suffix}"), targets),
        "leaf",
        values,
        recorded,
    )

    for (name, driver), answer in said.items():
        assert answer == twin.get((name, driver), twin[name, "apply-sync"]), (name, driver)
        assert (answer.code, answer.statements) == ("GLOBALID_UNVALIDATABLE", 0), answer


def _junk_key_refusal(target: type[Model], *, typed: bool) -> tuple[str, str]:
    """A ``target`` id whose node id no key of ``target`` holds, and its coded refusal.

    The refusal names the primary key where a type exposes ``target``, its key otherwise.
    """
    junk = _gid(target._meta.label_lower, "abc")
    key = "primary-key" if typed else "key"
    return junk, (
        f"Invalid GlobalID: {junk!r} carries a node id that is not a valid "
        f"{target.__name__} {key} value."
    )


_PLACED_WORLDS = [
    *(
        pytest.param(
            "forward",
            placement,
            form,
            typed,
            id=f"forward-{placement}-{form}-{'typed' if typed else 'untyped'}",
        )
        for placement in (_HANDED, _TYPE_HOOK, _FILTER_QUERYSET)
        for form in ("bare", "id")
        for typed in (True, False)
    ),
    *(
        pytest.param(
            shape,
            _FILTER_QUERYSET,
            form,
            False,
            id=f"{shape}-{_FILTER_QUERYSET}-{form}-untyped",
        )
        for shape in ("reverse", "many-to-many")
        for form in ("bare", "id")
    ),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    (
        "shape_name",
        "placement",
        "form",
        "typed",
    ),
    _PLACED_WORLDS,
)
def test_a_global_id_over_an_alias_answers_as_over_its_relation_in_every_placement(
    shape_name: str,
    placement: str,
    form: str,
    *,
    typed: bool,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """Wherever the alias is added, its key is coerced over the queryset the filter runs on.

    The queryset handed to the set, the rows type's ``get_queryset`` or the set's own
    ``filter_queryset`` override adds ``vshelf`` (``vbooks`` and ``vgenres`` under the
    override): a node id the target's key cannot hold is ``GLOBALID_INVALID`` before any
    statement, as over the relation, an id of another type a type mismatch where a type
    exposes the target, and the node id alone compared where none does.
    """
    rows = _library()
    shape = _ALIAS_SHAPES[shape_name]
    own = _named_row(rows, shape.own)
    hidden = _named_row(rows, shape.hidden)
    world = _alias_world(
        shape,
        _twin_leaves(shape, _ALIAS_FORMS[form], listed=False),
        lambda: (_alias_target(shape.target, hidden=hidden),) if typed else (),
        placement=placement,
    )
    junk, refusal = _junk_key_refusal(shape.target, typed=typed)
    label, wrong = shape.target._meta.label_lower, shape.model._meta.label_lower
    values = [
        _AliasValue("junk-key", junk, _Said(refusal, "GLOBALID_INVALID", 0)),
        _AliasValue(
            "wrong-type",
            _gid(wrong, own),
            _Said(_mismatch(label, wrong, listed=False), None, 0)
            if typed
            else _Said(_joined_pks(shape, own), None, 1),
        ),
    ]

    _assert_alias_answers_as_its_twin(world, values, record_compiled_sql("library_"))


_ANNOTATED_WORLDS = [
    pytest.param(shape, listed, id=f"{shape}-{'multiple' if listed else 'single'}")
    for shape in _ALIAS_SHAPES
    for listed in (False, True)
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(("shape_name", "listed"), _ANNOTATED_WORLDS)
def test_an_annotation_held_id_through_a_filtered_relation_alias_compares_on_the_visible_target_rows(
    shape_name: str,
    *,
    listed: bool,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An id only the target type's ``get_queryset`` annotation holds is compared on its rows.

    The bare alias names a row by its ``node_key`` (``k<pk>``) as its relation does: the
    target's own id answers its rows in one statement, an id of another type is a type
    mismatch before any, and ``[]`` reads the visible target rows once and answers none.
    """
    rows = _library()
    shape = _ALIAS_SHAPES[shape_name]
    world = _alias_world(
        shape,
        _twin_leaves(shape, "", listed=listed),
        lambda: (
            _alias_target(
                shape.target,
                namespace={
                    "__annotations__": {"node_key": relay.NodeID[str]},
                    "get_queryset": _keyed(),
                },
            ),
        ),
    )
    own = _named_row(rows, shape.own)
    handle = f"{_KEY_PREFIX}{saved_pk(own)}"
    label, wrong = shape.target._meta.label_lower, shape.model._meta.label_lower
    values = [
        _AliasValue(
            "own",
            _sent(label, handle, listed=listed),
            _Said(_joined_pks(shape, own), None, 1),
        ),
        _AliasValue(
            "wrong-type",
            _sent(wrong, handle, listed=listed),
            _Said(_mismatch(label, wrong, listed=listed), None, 0),
        ),
    ]
    if listed:
        values.append(_AliasValue("empty", [], _Said([], None, 1)))

    _assert_alias_answers_as_its_twin(world, values, record_compiled_sql("library_"))


#: Aliases whose condition leaves out the row a request names (``s1`` for ``vshelf``,
#: ``bk1`` for ``vbooks``, ``g1`` for ``vgenres``; ``vbranch`` reaches ``b1`` only through
#: ``vshelf``), beside the column the target's ``NodeID`` reads. A to-many alias's target
#: type scopes its rows, so the request walks it to the target rows.
_CONDITIONED_SHAPES: dict[str, tuple[_AliasShape, str]] = {
    "forward": (_ALIAS_SHAPES["forward"]._replace(add=_vshelf_past_s1), "code"),
    "reverse": (_ALIAS_SHAPES["reverse"]._replace(add=_vbooks_past_bk1), "title"),
    "many-to-many": (
        _ALIAS_SHAPES["many-to-many"]._replace(add=_vgenres_past_first_genre),
        "name",
    ),
    "alias-over-alias": (_ALIAS_SHAPES["alias-over-alias"]._replace(add=_vbranch_past_s1), "name"),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("form", ["bare", "id", "pk"])
@pytest.mark.parametrize("shape_name", sorted(_CONDITIONED_SHAPES))
def test_a_global_id_over_a_conditioned_alias_compares_its_id_column_through_the_alias(
    shape_name: str,
    form: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A ``NodeID`` column is compared past the alias, under the alias's own condition.

    ``vshelf`` joins no shelf ``s1``: the id naming ``s1`` (or ``b1``, reached through
    ``s1`` and ``s2``, ``bk1`` through ``vbooks``, ``g1`` through ``vgenres``) answers
    what Django's own ``vshelf__code`` / ``vbranch__name`` / ``vbooks__title`` /
    ``vgenres__name`` answers, never the relation's rows the condition leaves out, bare
    or past the key, a to-many alias walked to its scoped target rows included.
    """
    rows = _library()
    shape, column = _CONDITIONED_SHAPES[shape_name]
    to_many = shape_name in {"reverse", "many-to-many"}
    world = _alias_world(
        shape,
        _twin_leaves(shape, _ALIAS_FORMS[form], listed=False),
        lambda: (
            _alias_target(
                shape.target,
                hidden=_named_row(rows, shape.hidden) if to_many else None,
                namespace={"__annotations__": {column: relay.NodeID[str]}},
                fields=("id", column),
            ),
        ),
    )
    recorded = record_compiled_sql("library_")
    # ``_library`` names each row by the column its target's ``NodeID`` reads.
    node_id = shape.own
    every = shape.model._default_manager.all()
    expected = sorted(
        saved_pk(row) for row in shape.add(every).filter(**{f"{shape.alias}__{column}": node_id})
    )
    over_relation = sorted(
        saved_pk(row) for row in every.filter(**{f"{shape.relation}__{column}": node_id})
    )
    assert expected != over_relation
    value = _gid(shape.target._meta.label_lower, node_id)

    for driver in _ALIAS_DRIVERS:
        assert _alias_said(world, "alias", value, driver, recorded) == (expected, None, 1), driver
        assert _alias_said(world, "twin", value, driver, recorded) == (over_relation, None, 1)


class _NodeIdGlobalIDFilter(GlobalIDFilter):
    """A consumer ``filter`` override comparing the node id it decodes itself."""

    @override
    def filter(self, qs: QuerySet[_M], value: object) -> QuerySet[_M]:
        if value is None:
            return qs
        return qs.filter(**{str(self.field_name): _node_id_of(value)})


def _node_id_of(value: object) -> str:
    """The node id a GlobalID value names, decoded by consumer code."""
    global_id = value if isinstance(value, relay.GlobalID) else relay.GlobalID.from_id(str(value))
    return global_id.node_id


def _by_node(
    _set: FilterSet,
    queryset: QuerySet[Model],
    name: str,
    value: object,
) -> QuerySet[Model]:
    """A consumer ``method``: the node id the GlobalID names, compared on ``name``."""
    return queryset.filter(**{name: _node_id_of(value)})


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("decoder", ["method", "filter-override"])
@pytest.mark.parametrize("shape_name", ["forward", "reverse"])
def test_a_consumer_decoder_over_a_filtered_relation_alias_reads_its_own_value(
    shape_name: str,
    decoder: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A ``method`` or a ``filter`` override decodes the value itself, over the alias as not.

    Neither checks a type name: an id of another type naming the target's key answers
    the rows reaching that row, as over the relation, in one statement.
    """
    rows = _library()
    shape = _ALIAS_SHAPES[shape_name]

    def leaf(field_name: str) -> Callable[[], Filter]:
        if decoder == "method":
            return functools.partial(GlobalIDFilter, field_name=field_name, method="by_node")
        return functools.partial(_NodeIdGlobalIDFilter, field_name=field_name)

    world = _alias_world(
        shape,
        {"alias": leaf(shape.alias), "twin": leaf(shape.relation)},
        lambda: (_alias_target(shape.target, hidden=_named_row(rows, shape.hidden)),),
        methods={"by_node": _by_node},
    )
    own = _named_row(rows, shape.own)
    values = [
        _AliasValue(
            name,
            _gid(type_name, own),
            _Said(_joined_pks(shape, own), None, 1),
        )
        for name, type_name in (
            ("own", shape.target._meta.label_lower),
            ("wrong-type", shape.model._meta.label_lower),
        )
    ]

    _assert_alias_answers_as_its_twin(world, values, record_compiled_sql("library_"))
