"""Live HTTP serializer tests for save errors, runtime field ownership and post-save conflicts."""

from __future__ import annotations

from collections.abc import Mapping
from functools import wraps
from typing import TYPE_CHECKING, NoReturn

import graphql
import pytest
import strawberry
from apps.products import models as product_models
from apps.products.services import seed_data
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import connection
from django.db.models import Model
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_list, json_str
from rest_framework import serializers
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    ErrorPolicy,
    NestedSerializerConfig,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.rest_framework.accessors import base_fields, validated_data_of
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import dict_of
from django_strawberry_framework.views import DjangoGraphQLView
from tests._catalog_data import categories_from_seed, items_from_seed
from tests._idioms import ModelSerializerBase, is_object_dict, is_object_list

if TYPE_CHECKING:
    from typing import TypeAlias

    from django_strawberry_framework.rest_framework.serializer_converter import (
        DRFField,
        DRFSerializer,
    )

    _PkRelation: TypeAlias = (
        serializers.RelatedField[product_models.Category, product_models.Category, object]
        | serializers.ManyRelatedField
    )

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-serializer-runtime/", _graphql_view)]


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _schema(
    serializer_class: type[DRFSerializer],
    *,
    operation: str = "create",
    nested_fields: Mapping[str, NestedSerializerConfig] | None = None,
    expose_errors: bool = False,
) -> tuple[DjangoSchema, type[DjangoType], type[DjangoType]]:
    class CategoryNode(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class ItemNode(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            interfaces = (relay.Node,)

    selected_serializer = serializer_class
    selected_operation = operation
    selected_nested = nested_fields

    class Write(SerializerMutation):
        class Meta:
            serializer_class = selected_serializer
            operation = selected_operation
            nested_fields = selected_nested
            permission_classes = []

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(Write)

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=_Query,
        mutation=Mutation,
        extensions=[lambda: optimizer],
        error_policy=ErrorPolicy(enabled=False) if expose_errors else None,
    )
    return schema, CategoryNode, ItemNode


def _post(
    schema: DjangoSchema,
    document: str,
    variables: Mapping[str, object] | None = None,
) -> JSONObject:
    """Return the complete native HTTP envelope and restore the function's schema mount."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables=variables,
                url="/graphql-serializer-runtime/",
            )
    finally:
        _CURRENT["schema"] = None


def _document(schema: DjangoSchema, *, update: bool = False) -> str:
    """Read the public argument's actual input name before the SQL-observed write request."""
    described = _post(
        schema,
        """
        { __type(name: "Mutation") {
          fields { name args { name type { kind name ofType { kind name } } } }
        } }
    """,
    )
    assert set(described) == {"data"}, described
    (write,) = json_list(described, "data", "__type", "fields")
    assert json_str(write, "name") == "write"
    data_argument = next(
        arg for arg in json_list(write, "args") if json_str(arg, "name") == "data"
    )
    input_name = json_str(data_argument, "type", "ofType", "name")
    definitions = f"$d: {input_name}!" + (", $id: ID!" if update else "")
    arguments = "data: $d" + (", id: $id" if update else "")
    return (
        f"mutation({definitions}){{ write({arguments}){{ node{{ name }} "
        "errors{ field messages codes path } } }"
    )


def _writes(captured: CaptureQueriesContext, model: type[Model]) -> list[str]:
    """Keep only DML on this exact model table, independently of transaction/auth statements."""
    table = connection.ops.quote_name(model._meta.db_table)
    positions = {"INSERT": 2, "UPDATE": 1, "DELETE": 2}
    writes: list[str] = []
    for row in captured.captured_queries:
        words = row["sql"].split()
        table_position = positions.get(words[0])
        if table_position is not None and words[table_position] == table:
            writes.append(row["sql"])
    return writes


def _field_error(field: str, message: str, *, drf: bool = False) -> JSONObject:
    return {
        "field": field,
        "messages": [message],
        "codes": ["invalid"] if drf else [],
        "path": [field],
    }


def _save_serializer(case: str) -> type[ModelSerializerBase[product_models.Item]]:
    if case == "drf":

        class DRFRaisingSerializer(ModelSerializerBase[product_models.Item]):
            class Meta:
                model = product_models.Item
                fields = ("name", "category")

            @override
            def save(self, **kwargs: object) -> NoReturn:
                raise serializers.ValidationError({"name": ["drf save-time"]})

        return DRFRaisingSerializer
    if case == "django":

        class DjangoRaisingSerializer(ModelSerializerBase[product_models.Item]):
            class Meta:
                model = product_models.Item
                fields = ("name", "category")

            @override
            def save(self, **kwargs: object) -> NoReturn:
                raise DjangoValidationError({"name": ["django save-time"]})

        return DjangoRaisingSerializer
    if case == "source-name":

        class RenamedRaisingSerializer(ModelSerializerBase[product_models.Item]):
            full_name = serializers.CharField(source="name")

            class Meta:
                model = product_models.Item
                fields = ("full_name", "category")

            @override
            def save(self, **kwargs: object) -> NoReturn:
                raise DjangoValidationError(
                    {"name": ["bad name"], "description": ["bad description"]},
                )

        return RenamedRaisingSerializer
    if case == "source-relation":

        class RenamedRefRaisingSerializer(ModelSerializerBase[product_models.Item]):
            category_ref: _PkRelation = serializers.PrimaryKeyRelatedField(
                source="category",
                queryset=product_models.Category.objects.all(),
            )

            class Meta:
                model = product_models.Item
                fields = ("name", "category_ref")

            @override
            def save(self, **kwargs: object) -> NoReturn:
                raise DjangoValidationError(
                    {"category": ["on the FK"], "category_id": ["on the column"]},
                )

        return RenamedRefRaisingSerializer
    assert case == "valid"

    class PlainSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    return PlainSerializer


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    [
        "drf",
        "django",
        "source-name",
        "source-relation",
        "valid",
    ],
)
def test_serializer_save_errors_keep_their_family_and_all_source_names(case: str) -> None:
    """Each save exception preserves its messages, codes and source mapping; an ordinary save writes."""
    seed_data(0)
    (category,) = categories_from_seed(("Runtime category", False))
    schema, category_type, _item_type = _schema(_save_serializer(case))
    document = _document(schema)
    name_field = "fullName" if case == "source-name" else "name"
    relation_field = "categoryRefId" if case == "source-relation" else "categoryId"
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            document,
            {
                "d": {
                    name_field: "Written item",
                    relation_field: global_id_for(category_type, category.pk, schema=schema),
                },
            },
        )
    errors: list[JSONObject] = {
        "drf": [_field_error("name", "drf save-time", drf=True)],
        "django": [_field_error("name", "django save-time")],
        "source-name": [
            _field_error("fullName", "bad name"),
            _field_error("description", "bad description"),
        ],
        "source-relation": [
            _field_error("categoryRefId", "on the FK"),
            _field_error("categoryRefId", "on the column"),
        ],
        "valid": [],
    }[case]
    assert payload == {
        "data": {
            "write": {
                "node": {"name": "Written item"} if case == "valid" else None,
                "errors": errors,
            },
        },
    }
    assert list(product_models.Item.objects.values_list("name", "category_id")) == (
        [("Written item", category.pk)] if case == "valid" else []
    )
    assert len(_writes(captured, product_models.Item)) == int(case == "valid")
    assert list(product_models.Category.objects.values_list("name", flat=True)) == [category.name]


@pytest.mark.django_db
@pytest.mark.parametrize("outcome", ["refused", "saved"])
def test_serializer_error_after_a_real_partial_insert_leaves_no_partial_row(outcome: str) -> None:
    """A post-INSERT validation failure rolls back its row; the same consumer can commit a valid save."""
    seed_data(0)
    categories_from_seed()

    class PartialWriteSerializer(ModelSerializerBase[product_models.Category]):
        class Meta:
            model = product_models.Category
            fields = ("name",)

        @override
        def save(self, **kwargs: object) -> product_models.Category:
            if dict_of(validated_data_of(self))["name"] == "Refused category":
                product_models.Category.objects.create(name="Partial side effect")
                raise serializers.ValidationError({"name": ["rejected after a partial write"]})
            return super().save(**kwargs)

    schema, _category_type, _item_type = _schema(PartialWriteSerializer)
    document = _document(schema)
    name = "Refused category" if outcome == "refused" else "Complete category"
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, {"d": {"name": name}})
    expected: JSONObject = (
        {
            "node": None,
            "errors": [_field_error("name", "rejected after a partial write", drf=True)],
        }
        if outcome == "refused"
        else {"node": {"name": name}, "errors": []}
    )
    assert payload == {"data": {"write": expected}}
    writes = _writes(captured, product_models.Category)
    assert len(writes) == 1, writes
    assert writes[0].lstrip().startswith("INSERT INTO")
    assert ("Partial side effect" in writes[0]) is (outcome == "refused")
    assert list(product_models.Category.objects.values_list("name", flat=True)) == (
        [] if outcome == "refused" else [name]
    )


def _runtime_serializer(
    shape: str,
    *,
    writable: bool,
) -> type[ModelSerializerBase[product_models.Item] | ModelSerializerBase[product_models.Category]]:
    class ContextualAttnameSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        @override
        def get_fields(self) -> dict[str, DRFField]:
            fields = base_fields(super())
            if self.context.get("request") is not None:
                if writable:
                    fields["cat"] = serializers.PrimaryKeyRelatedField(
                        source="category_id",
                        queryset=product_models.Category.objects.all(),
                        required=False,
                        default=None,
                    )
                else:
                    fields["cat"] = serializers.PrimaryKeyRelatedField(
                        source="category_id",
                        read_only=True,
                    )
            return fields

    if shape == "root":
        return ContextualAttnameSerializer
    assert shape == "nested"

    class CategoryWithContextualItems(ModelSerializerBase[product_models.Category]):
        items = ContextualAttnameSerializer(many=True)

        class Meta:
            model = product_models.Category
            fields = ("name", "items")

        @override
        def create(self, validated_data: dict[str, object]) -> product_models.Category:
            children = validated_data.pop("items")
            name = validated_data["name"]
            assert isinstance(name, str)
            assert is_object_list(children)
            category = product_models.Category.objects.create(name=name)
            for child in children:
                assert is_object_dict(child)
                child_name = child["name"]
                target = child["category"]
                assert isinstance(child_name, str)
                assert isinstance(target, product_models.Category)
                product_models.Item.objects.create(name=child_name, category=target)
            return category

    return CategoryWithContextualItems


@pytest.mark.django_db
@pytest.mark.parametrize("shape", ["root", "nested"])
@pytest.mark.parametrize("ownership", ["writable", "read-only"])
def test_runtime_fk_attname_alias_refuses_only_competing_writable_fields(
    shape: str,
    ownership: str,
) -> None:
    """A runtime writable alias fails before DML, while the same read-only source permits a real write."""
    seed_data(0)
    (category,) = categories_from_seed(("Existing category", False))
    writable = ownership == "writable"
    serializer_class = _runtime_serializer(shape, writable=writable)
    schema, category_type, _item_type = _schema(
        serializer_class,
        nested_fields={"items": NestedSerializerConfig()} if shape == "nested" else None,
        expose_errors=True,
    )
    document = _document(schema)
    item_data = {
        "name": "Client item",
        "categoryId": global_id_for(category_type, category.pk, schema=schema),
    }
    data = {"name": "Runtime parent", "items": [item_data]} if shape == "nested" else item_data
    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, document, {"d": data})
    if writable:
        path = "items" if shape == "nested" else "<root>"
        message = (
            f"SerializerMutation Write: runtime serializer path {path!r} has multiple writable "
            "fields that bind one serializer source: source 'category' <- fields "
            "['category', 'cat' (source 'category_id')]. DRF resolves a source collision "
            "last-write-wins, so one field's validated value would silently overwrite another's "
            "(including values from HiddenField or narrowed-out field defaults). Give every "
            "runtime writable field a distinct source."
        )
        location = graphql.get_location(graphql.Source(document), document.index("write("))
        assert payload == {
            "data": None,
            "errors": [
                {
                    "message": message,
                    "locations": [{"line": location.line, "column": location.column}],
                    "path": ["write"],
                },
            ],
        }
    else:
        assert payload == {
            "data": {
                "write": {
                    "node": {"name": "Runtime parent" if shape == "nested" else "Client item"},
                    "errors": [],
                },
            },
        }
    assert list(product_models.Item.objects.values_list("name", "category_id")) == (
        [] if writable else [("Client item", category.pk)]
    )
    assert list(product_models.Category.objects.order_by("pk").values_list("name", flat=True)) == (
        [category.name] if writable or shape == "root" else [category.name, "Runtime parent"]
    )
    assert len(_writes(captured, product_models.Item)) == int(not writable)
    assert len(_writes(captured, product_models.Category)) == int(
        not writable and shape == "nested",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("vanishes", [False, True], ids=["kept", "vanished"])
def test_serializer_post_save_disappearance_returns_conflict_and_restores_the_prior_row(
    *,
    vanishes: bool,
) -> None:
    """A vanished saved row produces conflict and rolls back both UPDATE and DELETE; a kept row commits."""
    seed_data(1)
    old, new = categories_from_seed(("Previous category", False), ("Selected category", False))
    (item,) = items_from_seed(old, ("Original item", False))
    product_models.Item.objects.exclude(pk=item.pk).delete()
    product_models.Entry.objects.filter(item=item).delete()

    class DeletingItemSerializer(ModelSerializerBase[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        @override
        def update(
            self,
            instance: product_models.Item,
            validated_data: dict[str, object],
        ) -> product_models.Item:
            updated = super().update(instance, validated_data)
            if vanishes:
                product_models.Item._base_manager.filter(pk=updated.pk).delete()
            return updated

    schema, category_type, item_type = _schema(DeletingItemSerializer, operation="update")
    document = _document(schema, update=True)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(
            schema,
            document,
            {
                "id": global_id_for(item_type, item.pk, schema=schema),
                "d": {
                    "name": "Changed item",
                    "categoryId": global_id_for(category_type, new.pk, schema=schema),
                },
            },
        )
    expected: JSONObject = (
        {
            "node": None,
            "errors": [
                {
                    "field": "id",
                    "messages": [
                        "The row was changed or removed by a concurrent operation; retry.",
                    ],
                    "codes": ["conflict"],
                    "path": ["id"],
                },
            ],
        }
        if vanishes
        else {"node": {"name": "Changed item"}, "errors": []}
    )
    assert payload == {"data": {"write": expected}}
    item.refresh_from_db()
    assert (item.name, item.category_id) == (
        ("Original item", old.pk) if vanishes else ("Changed item", new.pk)
    )
    assert product_models.Item.objects.count() == 1
    writes = _writes(captured, product_models.Item)
    assert sum(sql.lstrip().startswith("UPDATE") for sql in writes) == 1, writes
    assert sum(sql.lstrip().startswith("DELETE") for sql in writes) == int(vanishes), writes
