"""Live HTTP tests for consumer-declared mutation authorization and its configuration boundary."""

from __future__ import annotations

from collections.abc import Generator
from functools import wraps
from typing import NoReturn

import pytest
import strawberry
from apps.products import models as product_models
from apps.products.services import create_users, seed_data
from django.contrib.auth.models import AnonymousUser, Permission, User
from django.http import HttpRequest, HttpResponseBase
from django.test import Client, override_settings
from django.urls import path
from django.utils.functional import SimpleLazyObject
from graphql_client import JSONObject, json_at, json_list, post_graphql, response_json
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import DjangoGraphQLView
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, object] = {"schema": None, "actor": None}
_NO_ERROR_MASKING = {"enabled": False}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert isinstance(schema, DjangoSchema), schema
    actor = _CURRENT["actor"]
    if actor is not None:
        vars(request)["user"] = actor
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _graphql_view)]


def _post(
    schema: DjangoSchema,
    query: str,
    user: object,
    variables: dict[str, object],
) -> JSONObject:
    """Run a real HTTP mutation, carrying real actors through a Django session."""
    client = Client()
    if type(user) is User:
        client.force_login(user)
    _CURRENT.update(schema=schema, actor=None if type(user) in (User, AnonymousUser) else user)
    try:
        with override_settings(ROOT_URLCONF=__name__):
            response = post_graphql(
                query,
                client=client,
                variables=variables,
                url="/graphql-test/",
            )
        assert response.status_code == 200
        return response_json(response)
    finally:
        _CURRENT.update(schema=None, actor=None)


def _user_with_perms(*codenames: str) -> User:
    """Grant the requested model permissions to an already service-seeded regular user."""
    user = User.objects.get(username="regular_1")
    for codename in codenames:
        user.user_permissions.add(
            Permission.objects.get(codename=codename, content_type__app_label="products"),
        )
    return User.objects.get(pk=saved_pk(user))


def _assert_refusal(payload: JSONObject, message: str) -> None:
    """Pin the complete error verdict rather than accepting any failed request."""
    assert payload["data"] is None, payload
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    assert json_at(errors[0], "message") == message, payload
    assert json_at(errors[0], "path") == ["createItem"], payload


_ASYNC_REPAIR = (
    "A DjangoMutation runs its permission check synchronously, so it cannot await "
    "an async permission hook; redefine has_permission / check_permission as a sync "
    "method returning a bool, and ensure user.has_perm / auth backends return a bool."
)


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _build_auth_schema(
    *,
    create_permission_classes: list[type[object]] | None = None,
) -> tuple[DjangoSchema, tuple[type[DjangoType], type[DjangoType]]]:
    """Declare Item/Category primaries + create/update/delete mutations; return (schema, types).

    ``create_permission_classes`` overrides ``CreateItem.Meta.permission_classes``;
    ``None`` keeps the default ``[DjangoModelPermission]`` so the model-perm
    enforcement is exercised end-to-end.
    """

    class CategoryT(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True
            interfaces = (relay.Node,)

    class ItemT(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True
            interfaces = (relay.Node,)

    create_meta_attrs: dict[str, object] = {"model": product_models.Item, "operation": "create"}
    if create_permission_classes is not None:
        create_meta_attrs["permission_classes"] = create_permission_classes
    create_mutation = type(
        "CreateItem",
        (DjangoMutation,),
        {"Meta": type("Meta", (), create_meta_attrs)},
    )

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(create_mutation)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    schema = DjangoSchema(query=_Query, mutation=Mutation, error_policy=_NO_ERROR_MASKING)
    return schema, (CategoryT, ItemT)


_CREATE_Q = "mutation($d: ItemInput!){ createItem(data:$d){ node{ name } errors{ field } } }"


@pytest.mark.django_db
def test_empty_permission_classes_never_resolves_request_auth() -> None:
    """The explicit allow-any opt-out does not invoke lazy user or auth-backend code."""
    seed_data(1)

    def load_user() -> NoReturn:
        raise AssertionError("permission-free mutations must not resolve the lazy request user")

    schema, (category_type, _item_type) = _build_auth_schema(create_permission_classes=[])
    cat = product_models.Category.objects.earliest("pk")
    res = _post(
        schema,
        _CREATE_Q,
        SimpleLazyObject(load_user),
        {"d": {"name": "Open", "categoryId": global_id_for(category_type, saved_pk(cat))}},
    )
    assert res == {"data": {"createItem": {"node": {"name": "Open"}, "errors": []}}}


@pytest.mark.django_db
def test_permission_classes_override_deny_blocks_permitted_caller() -> None:
    """A custom deny-all override blocks an otherwise-permitted caller (proving the override path)."""
    seed_data(1)
    create_users(1)

    class DenyAll:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            return False

    schema, (category_type, _item_type) = _build_auth_schema(create_permission_classes=[DenyAll])
    cat = product_models.Category.objects.earliest("pk")
    user = _user_with_perms("add_item")  # holds the default perm, still denied by override
    res = _post(
        schema,
        _CREATE_Q,
        user,
        {"d": {"name": "Nope", "categoryId": global_id_for(category_type, saved_pk(cat))}},
    )
    _assert_refusal(res, "Not authorized to create ItemT.")
    assert not product_models.Item.objects.filter(name="Nope").exists()


@pytest.mark.django_db
def test_async_has_permission_is_rejected_not_bypassed() -> None:
    """An async ``has_permission`` raises SyncMisuseError, never a silent allow.

    A coroutine is truthy, so a naive ``if not has_permission(...)`` would treat an
    async deny-check as ALLOW - an authorization bypass. The sync pipeline cannot
    await the coroutine, so it is closed and raised as a ``SyncMisuseError`` (surfacing
    as a top-level GraphQL error), and crucially NO row is written: the deny is
    honored, not bypassed.
    """
    seed_data(1)

    class AsyncDeny:
        async def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            return False

    schema, (category_type, _item_type) = _build_auth_schema(create_permission_classes=[AsyncDeny])
    cat = product_models.Category.objects.earliest("pk")
    res = _post(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "AsyncBlocked", "categoryId": global_id_for(category_type, saved_pk(cat))}},
    )
    _assert_refusal(
        res,
        "AsyncDeny.has_permission returned a coroutine in a sync mutation context. "
        + _ASYNC_REPAIR,
    )
    assert not product_models.Item.objects.filter(name="AsyncBlocked").exists()


@pytest.mark.django_db
def test_awaitable_has_permission_is_rejected_not_bypassed() -> None:
    """A custom awaitable permission result cannot be treated as truthy authorization."""
    seed_data(1)

    class DeferredDeny:
        def __await__(self) -> Generator[None, None, bool]:
            yield from ()  # resolves without suspending
            return False

    class AwaitableDeny:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> DeferredDeny:
            return DeferredDeny()

    schema, (category_type, _item_type) = _build_auth_schema(
        create_permission_classes=[AwaitableDeny],
    )
    cat = product_models.Category.objects.earliest("pk")
    res = _post(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {
            "d": {
                "name": "AwaitableBlocked",
                "categoryId": global_id_for(category_type, saved_pk(cat)),
            },
        },
    )

    _assert_refusal(
        res,
        "AwaitableDeny.has_permission returned an awaitable in a sync mutation context. "
        + _ASYNC_REPAIR,
    )
    assert not product_models.Item.objects.filter(name="AwaitableBlocked").exists()


@pytest.mark.django_db
def test_hostile_non_bool_permission_result_repr_propagates_and_denies() -> None:
    """A non-bool result's own ``__repr__`` renders it; what that raises propagates, no write.

    The non-bool is still refused before any write: the message that names it is built
    from the result's ``repr``, which is consumer behaviour, so its exception surfaces
    in place of the ``ConfigurationError`` and the create never runs.
    """
    seed_data(1)

    class Hostile:
        @override
        def __repr__(self) -> str:
            raise RuntimeError("repr escape")

    class HostileResult:
        def has_permission(
            self,
            info: object,
            mutation: type[object],
            operation: str,
            data: object,
            instance: object = None,
        ) -> Hostile:
            del info, mutation, operation, data, instance
            return Hostile()

    schema, (category_type, _item_type) = _build_auth_schema(
        create_permission_classes=[HostileResult],
    )
    cat = product_models.Category.objects.earliest("pk")
    res = _post(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {
            "d": {
                "name": "HostileBlocked",
                "categoryId": global_id_for(category_type, saved_pk(cat)),
            },
        },
    )

    _assert_refusal(res, "repr escape")
    assert not product_models.Item.objects.filter(name="HostileBlocked").exists()


@pytest.mark.django_db
def test_async_check_permission_override_is_rejected_not_bypassed() -> None:
    """An async ``check_permission`` override raises SyncMisuseError, not a silent allow.

    The override returns a coroutine; ``authorize_or_raise`` closes it and raises
    ``SyncMisuseError`` rather than treating the truthy coroutine as authorized. No
    row is written.
    """
    seed_data(1)

    class CategoryT(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True
            interfaces = (relay.Node,)

    class ItemT(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True
            interfaces = (relay.Node,)

    assert registry.get(product_models.Item) is ItemT

    class AsyncCheckCreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

        @override
        # basedpyright: deliberately async: the coroutine is the result the sync write-auth check refuses
        async def check_permission(  # pyright: ignore[reportIncompatibleMethodOverride]
            self,
            info: strawberry.Info,
            operation: str,
            data: object,
            instance: object = None,
        ) -> bool:
            return False

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(AsyncCheckCreateItem)

    finalize_django_types()
    schema = DjangoSchema(query=_Query, mutation=Mutation, error_policy=_NO_ERROR_MASKING)
    cat = product_models.Category.objects.earliest("pk")
    res = _post(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {
            "d": {
                "name": "AsyncCheckBlocked",
                "categoryId": global_id_for(CategoryT, saved_pk(cat)),
            },
        },
    )
    _assert_refusal(
        res,
        "AsyncCheckCreateItem.check_permission returned a coroutine in a sync mutation context. "
        + _ASYNC_REPAIR,
    )
    assert not product_models.Item.objects.filter(name="AsyncCheckBlocked").exists()


@pytest.mark.django_db
def test_hook_rebinding_the_validated_permission_slot_fails_closed() -> None:
    """A hook reassigning the validated permission set fails the request closed (live tier).

    The snapshot walk survives list pollution; a hook could also try to
    REASSIGN the validated ``permission_classes`` slot on the shared
    ``_ValidatedMutationMeta`` record, which would leave an empty posture on the
    class that authorizes every later request. The sealed record refuses the write with
    ``ConfigurationError``, so the hostile hook fails the request loudly (a
    top-level error, no row), the validated configuration survives untouched,
    and a second identical anonymous request is still denied.
    """
    seed_data(1)
    denier_runs: list[str] = []

    class AllowAndRebind:
        def has_permission(
            self,
            _info: object,
            mutation: type[DjangoMutation],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            # The hook's ``mutation`` IS the mutation class; the plain attribute
            # statement is the persistent-bypass shape the seal refuses.
            mutation._mutation_meta.permission_classes = ()
            return True

    class Denier:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            denier_runs.append("Denier")
            return False

    class CategoryT(DjangoType):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True
            interfaces = (relay.Node,)

    class ItemT(DjangoType):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True
            interfaces = (relay.Node,)

    assert registry.get(product_models.Item) is ItemT

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [AllowAndRebind, Denier]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = DjangoSchema(query=_Query, mutation=Mutation, error_policy=_NO_ERROR_MASKING)
    cat = product_models.Category.objects.earliest("pk")

    res = _post(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "Blocked", "categoryId": global_id_for(CategoryT, saved_pk(cat))}},
    )
    # The seal raises OUT of the walk: loud top-level failure, no write.
    message = (
        "The validated mutation Meta snapshot is sealed and 'permission_classes' cannot be "
        "reassigned; authorization configuration is captured once at class creation."
    )
    _assert_refusal(res, message)
    assert not product_models.Item.objects.filter(name="Blocked").exists()
    # The seal refused the rebind: the validated configuration is untouched.

    # The next (identical anonymous) request is still denied by the intact posture.
    res2 = _post(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "StillBlocked", "categoryId": global_id_for(CategoryT, saved_pk(cat))}},
    )
    _assert_refusal(res2, message)
    assert not product_models.Item.objects.filter(name="StillBlocked").exists()
    # The walk aborts at the FIRST entry (the raising hook) on every request:
    # the configured denier never ran at all under the seal.
    assert denier_runs == []
