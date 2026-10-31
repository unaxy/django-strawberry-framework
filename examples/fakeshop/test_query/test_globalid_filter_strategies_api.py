"""GlobalID filters accept only the target's configured emitted identifier spellings.

These native Relay types use real Meta strategies and emit identifiers over HTTP.
The JSON consumer applies its associated FilterSet; a typed GlobalID consumer uses
its bound public filter primitive to preserve Strawberry's already-decoded value.
A GlobalID filter into a model no type exposes compares the node id on the relation's
key, through a ``GenericRelation`` too; one on a ``GenericForeignKey`` is refused when
its set publishes its filters, served or applied unbound.
"""

import logging
from collections.abc import Mapping
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql_client import (
    JSONObject,
    RecordCompiledSql,
    graphql_payload,
    json_at,
    json_list,
    json_object,
)
from strawberry import relay
from strawberry.scalars import JSON
from strawberry.types import Info
from strawberry.types.base import StrawberryList

from django_strawberry_framework import (
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
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}
_URL = "/graphql-globalid-strategies/"


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-globalid-strategies/", _view)]


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
