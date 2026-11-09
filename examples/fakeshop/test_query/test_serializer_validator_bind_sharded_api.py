"""Live sharded HTTP checks for conditional DRF uniqueness on the write alias."""

from __future__ import annotations

import os
from collections.abc import Mapping
from functools import wraps
from typing import TYPE_CHECKING

import pytest

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip("requires FAKESHOP_SHARDED=1", allow_module_level=True)

import strawberry
from apps.library.models import Branch
from django.db import connections
from django.db.models import Model, Q
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, graphql_payload, json_at
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from typing_extensions import override

from django_strawberry_framework import (
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    NestedSerializerConfig,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import ModelSerializerBase, saved_pk

if TYPE_CHECKING:
    from django_strawberry_framework.rest_framework.serializer_converter import DRFSerializer

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


class _BranchWriteRouter:
    """Select shard_b for Branch writes while leaving other apps on their own aliases."""

    def db_for_write(self, model: type[Model], **_hints: object) -> str | None:
        return "shard_b" if model is Branch else None


@wraps(DjangoGraphQLView.as_view())
def _view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-serializer-conditional-sharded/", _view)]


@strawberry.type
class _Query:
    ping: int = 1


class _ConditionalBranch(ModelSerializerBase[Branch]):
    name = serializers.CharField(validators=[])

    class Meta:
        model = Branch
        fields = ("name", "city")
        validators = [
            UniqueTogetherValidator(
                queryset=Branch.objects.all(),
                fields=("name", "city"),
                condition_fields=("city",),
                condition=Q(city="Boston"),
            ),
        ]


class _BranchBundle(ModelSerializerBase[Branch]):
    child = _ConditionalBranch()

    class Meta:
        model = Branch
        fields = ("name", "city", "child")

    @override
    def create(self, validated_data: dict[str, object]) -> Branch:
        child_data = validated_data.pop("child")
        parent = Branch.objects.create(**validated_data)
        assert isinstance(child_data, Mapping)
        _ = Branch.objects.create(**child_data)
        return parent


def _schema(serializer_class: type[DRFSerializer], *, operation: str = "create") -> DjangoSchema:
    registry.clear()

    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name", "city")

    selected_serializer = serializer_class
    selected_operation = operation
    nested = {"child": NestedSerializerConfig()} if serializer_class is _BranchBundle else None

    class Write(SerializerMutation):
        class Meta:
            serializer_class = selected_serializer
            operation = selected_operation
            nested_fields = nested
            permission_classes = []

    @strawberry.type
    class Mutation:
        write = DjangoMutationField(Write)

    finalize_django_types()
    return DjangoSchema(query=_Query, mutation=Mutation, types=(BranchType,))


def _post(
    schema: DjangoSchema,
    data: str,
    *,
    row_id: int | None = None,
) -> tuple[JSONObject, dict[str, list[str]]]:
    _CURRENT["schema"] = schema
    try:
        identifier = f'id: "{row_id}", ' if row_id is not None else ""
        with (
            override_settings(ROOT_URLCONF=__name__, DATABASE_ROUTERS=[_BranchWriteRouter()]),
            CaptureQueriesContext(connections["default"]) as on_default,
            CaptureQueriesContext(connections["shard_b"]) as on_shard,
        ):
            payload = graphql_payload(
                "mutation { write("
                f"{identifier}data: {{ {data} }}"
                ") { result { name city } errors { field messages codes } } }",
                url="/graphql-serializer-conditional-sharded/",
            )
        statements = {
            "default": [item["sql"] for item in on_default.captured_queries],
            "shard_b": [item["sql"] for item in on_shard.captured_queries],
        }
        return payload, statements
    finally:
        _CURRENT["schema"] = None


def _assert_only_shard_branch_sql(statements: dict[str, list[str]]) -> None:
    assert not any("library_branch" in sql for sql in statements["default"]), statements
    assert any("library_branch" in sql for sql in statements["shard_b"]), statements


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_conditional_create_update_and_nested_validation_use_shard_b() -> None:
    _ = Branch.objects.using("default").create(name="default-only", city="Boston")
    schema = _schema(_ConditionalBranch)
    new, new_sql = _post(schema, 'name: "new", city: "Boston"')
    assert json_at(new, "data", "write", "errors") == [], new
    _assert_only_shard_branch_sql(new_sql)
    assert Branch.objects.using("shard_b").filter(name="new").exists()
    assert not Branch.objects.using("default").filter(name="new").exists()

    remote, remote_sql = _post(schema, 'name: "default-only", city: "Boston"')
    assert json_at(remote, "data", "write", "errors") == [], remote
    _assert_only_shard_branch_sql(remote_sql)
    assert Branch.objects.using("shard_b").filter(name="default-only").exists()

    duplicate, duplicate_sql = _post(schema, 'name: "new", city: "Boston"')
    assert json_at(duplicate, "data", "write", "result") is None, duplicate
    assert json_at(duplicate, "data", "write", "errors", 0, "codes") == ["unique"], duplicate
    _assert_only_shard_branch_sql(duplicate_sql)
    assert Branch.objects.using("shard_b").filter(name="new").count() == 1

    moving = Branch.objects.using("shard_b").create(name="moving", city="Cambridge")
    updated, update_sql = _post(
        _schema(_ConditionalBranch, operation="update"),
        'city: "Boston"',
        row_id=saved_pk(moving),
    )
    assert json_at(updated, "data", "write", "errors") == [], updated
    _assert_only_shard_branch_sql(update_sql)
    moving.refresh_from_db(using="shard_b")
    assert moving.city == "Boston"

    nested, nested_sql = _post(
        _schema(_BranchBundle),
        'name: "bundle", city: "Cambridge", child: { name: "nested", city: "Boston" }',
    )
    assert json_at(nested, "data", "write", "errors") == [], nested
    _assert_only_shard_branch_sql(nested_sql)
    assert Branch.objects.using("shard_b").filter(name="nested").exists()
    assert not Branch.objects.using("default").filter(name="nested").exists()
