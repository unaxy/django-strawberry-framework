"""Mutation permission construction, hidden exception state, and direct helper contracts.

The HTTP authorization verdicts for consumer-declared permission classes live in
``examples/fakeshop/test_query/test_mutation_permissions_api.py``. The shipped
model-permission matrix is in ``examples/fakeshop/test_query/test_products_api.py``.
This module keeps the operation/action mapping, permission-class snapshot internals,
non-HTTP actor shapes, and exception objects and validated records a wire response
cannot encode. The in-process schema rows read only that hidden state.
"""

from __future__ import annotations

from collections.abc import Awaitable, Generator, Iterator
from types import SimpleNamespace

import pytest
import strawberry
from apps.products import models as product_models
from apps.products.services import create_users, seed_data
from django.apps import apps
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser, Permission, User
from django.db.models import Model
from django.test import override_settings
from strawberry import relay
from strawberry.types import ExecutionResult
from typing_extensions import override

from django_strawberry_framework import (
    DjangoModelPermission,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    SyncMisuseError,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.operations import _OPERATION_PERMISSION_ACTION
from django_strawberry_framework.mutations.permissions import (
    DenyAll,
    _require_sync_bool_auth_result,
    run_permission_classes,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.write_mixins import _ValidatedMutationMeta
from tests._idioms import saved_pk
from tests._info import make_info


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry (co-clears the mutation declaration registry) per test."""
    registry.clear()
    yield
    registry.clear()


def _info_for(user: object) -> strawberry.Info[object, object]:
    """Build a stub ``info`` whose ``context.request.user`` is ``user``.

    Matches the ``info.context.request`` shape ``request_from_info`` resolves -
    the canonical Strawberry-Django context the read-side permission pipeline uses.
    """
    return make_info(context=SimpleNamespace(request=SimpleNamespace(user=user)))


def _create_item_mutation() -> type[DjangoMutation]:
    """A ``create`` ``DjangoMutation`` over the products ``Item`` model."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    return CreateItem


def _user_with_perms(*codenames: str) -> AbstractBaseUser:
    """Grant exactly the named products permissions to a service-seeded regular user."""
    user = User.objects.get(username="regular_1")
    for codename in codenames:
        perm = Permission.objects.get(codename=codename, content_type__app_label="products")
        user.user_permissions.add(perm)
    # Re-fetch so the permission cache reflects the freshly added rows.
    return get_user_model().objects.get(pk=saved_pk(user))


def test_operation_action_map_is_pinned() -> None:
    """The operation -> Django-action map matches the spec (create/update/delete)."""
    assert _OPERATION_PERMISSION_ACTION == {
        "create": "add",
        "update": "change",
        "delete": "delete",
    }


@pytest.mark.django_db
def test_anonymous_user_is_denied() -> None:
    """An ``AnonymousUser`` holds no perms, so the write is denied (safe default)."""
    mutation = _create_item_mutation()
    info = _info_for(AnonymousUser())
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is False


@pytest.mark.django_db
def test_user_lacking_perm_is_denied() -> None:
    """An authenticated user without ``add_item`` is denied for ``create``."""
    create_users(1)
    mutation = _create_item_mutation()
    user = _user_with_perms()  # no perms
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is False


@pytest.mark.django_db
def test_user_with_add_perm_allowed_for_create() -> None:
    """A user holding ``add_item`` is allowed for ``create``."""
    create_users(1)
    mutation = _create_item_mutation()
    user = _user_with_perms("add_item")
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is True


@pytest.mark.django_db
def test_create_perm_does_not_authorize_update_or_delete() -> None:
    """``add_item`` alone does not authorize ``update`` (needs ``change``) or ``delete``."""
    create_users(1)
    mutation = _create_item_mutation()
    user = _user_with_perms("add_item")
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "update", data=None) is False
    assert DjangoModelPermission().has_permission(info, mutation, "delete", data=None) is False


@pytest.mark.django_db
def test_change_and_delete_perms_authorize_their_operations() -> None:
    """``change_item`` authorizes ``update``; ``delete_item`` authorizes ``delete``."""
    create_users(1)
    mutation = _create_item_mutation()
    user = _user_with_perms("change_item", "delete_item")
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "update", data=None) is True
    assert DjangoModelPermission().has_permission(info, mutation, "delete", data=None) is True


@pytest.mark.django_db
@pytest.mark.parametrize(("codename", "allowed"), [("add_item", True), ("add_property", False)])
def test_model_permission_checks_the_model_the_class_declared(
    codename: str,
    *,
    allowed: bool,
) -> None:
    """The default checks the model the class resolved at declaration, the one its write uses.

    The class resolves its model once, through ``_resolve_model``, and the write pipeline
    reads that validated model. A settings-driven resolver answers ``Property`` once the
    setting changes, yet the checked permission stays ``Item``'s, so the user holding
    ``add_item`` is authorized and the one holding only ``add_property`` is not.
    """
    create_users(1)
    with override_settings(PRODUCTS_WRITE_MODEL="products.Item"):

        class CreateItem(DjangoMutation):
            @classmethod
            @override
            def _resolve_model(cls, meta: type[object]) -> type[Model] | None:
                return apps.get_model(str(read_attr(django_settings, "PRODUCTS_WRITE_MODEL")))

            class Meta:
                operation = "create"

    info = _info_for(_user_with_perms(codename))
    with override_settings(PRODUCTS_WRITE_MODEL="products.Property"):
        assert (
            DjangoModelPermission().has_permission(info, CreateItem, "create", data=None)
            is allowed
        )


# ---------------------------------------------------------------------------
# Write-auth ENFORCEMENT through a schema (Decision 15)
# ---------------------------------------------------------------------------


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


#: Every probe schema in this file opts out of the spec-048 response-boundary error
#: policy. The subject here is the AUTHORIZATION pipeline - whether a coroutine or a
#: non-bool permission result is refused rather than silently treated as ALLOW - and
#: the proof is the ``SyncMisuseError`` text (and, in one row, the surviving
#: ``original_error``) that the pipeline raises. Masking is a different, later concern
#: that would replace exactly that evidence, so it is disabled here rather than
#: pretending these in-process schemas are running a debug deployment; the masking
#: contract itself is pinned in ``tests/test_error_policy.py`` and the live tier.
_NO_ERROR_MASKING = {"enabled": False}


def _build_auth_schema(
    *,
    create_permission_classes: list[type] | None = None,
) -> tuple[DjangoSchema, tuple[type[DjangoType], type[DjangoType]]]:
    """Declare Item/Category primaries + create/update/delete mutations; return (schema, types).

    ``create_permission_classes`` overrides ``CreateItem.Meta.permission_classes``;
    ``None`` keeps the default ``[DjangoModelPermission]`` so the model-perm
    enforcement is exercised end-to-end.
    """

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    create_meta_attrs: dict[str, object] = {"model": product_models.Item, "operation": "create"}
    if create_permission_classes is not None:
        create_meta_attrs["permission_classes"] = create_permission_classes
    CreateItem = type(
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
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    schema = DjangoSchema(query=_Query, mutation=Mutation, error_policy=_NO_ERROR_MASKING)
    return schema, (CategoryT, ItemT)


def _execute(
    schema: DjangoSchema,
    query: str,
    user: object,
    variables: dict[str, object],
) -> ExecutionResult:
    """Execute ``query`` with ``info.context.request.user`` set to ``user``."""
    return schema.execute_sync(
        query,
        variable_values=variables,
        context_value=SimpleNamespace(request=SimpleNamespace(user=user)),
    )


_CREATE_Q = "mutation($d: ItemInput!){ createItem(data:$d){ node{ name } errors{ field } } }"


@pytest.mark.django_db
def test_awaitable_permission_error_keeps_original_sync_misuse_exception() -> None:
    """The refusal keeps its ``SyncMisuseError`` as ``original_error``, an unwired property.

    The HTTP verdict lives in ``test_mutation_permissions_api.py``; JSON cannot carry
    the exception object this row reads.
    """
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

    schema, (CategoryT, _ItemT) = _build_auth_schema(
        create_permission_classes=[AwaitableDeny],
    )
    cat = product_models.Category.objects.earliest("pk")
    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "AwaitableBlocked", "categoryId": global_id_for(CategoryT, saved_pk(cat))}},
    )

    assert res.errors is not None
    assert isinstance(res.errors[0].original_error, SyncMisuseError)


@pytest.mark.django_db
def test_hostile_permission_result_keeps_its_original_exception() -> None:
    """The result renderer's raised exception remains the GraphQL error's original object.

    The HTTP refusal lives in ``test_mutation_permissions_api.py``. Exception identity
    is not a response field, so this half is observed on the in-process result.
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

    schema, (CategoryT, _ItemT) = _build_auth_schema(
        create_permission_classes=[HostileResult],
    )
    cat = product_models.Category.objects.earliest("pk")
    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "HostileBlocked", "categoryId": global_id_for(CategoryT, saved_pk(cat))}},
    )

    assert res.errors is not None
    assert isinstance(res.errors[0].original_error, RuntimeError)


@pytest.mark.django_db
def test_awaitable_has_perm_is_rejected_not_bypassed() -> None:
    """An awaitable ``user.has_perm`` raises SyncMisuseError, never a silent allow.

    ``bool(coroutine)`` is True, so a naive ``return bool(user.has_perm(...))``
    would treat an async / buggy auth-backend result as ALLOW - the same
    authorization-bypass class closed for async ``has_permission``. Unreachable
    from stock Django ``User.has_perm`` (always sync bool); earned here with a
    stub user whose ``has_perm`` returns a coroutine.
    """

    class _AwaitablePermUser:
        is_authenticated = True

        def has_perm(self, _codename: str) -> Awaitable[bool]:
            async def _deny() -> bool:
                return False

            return _deny()

    mutation = _create_item_mutation()
    info = _info_for(_AwaitablePermUser())
    with pytest.raises(SyncMisuseError, match="has_perm"):
        DjangoModelPermission().has_permission(info, mutation, "create", data=None)


def test_request_without_user_attribute_is_denied() -> None:
    """A request carrying no ``user`` attribute is denied (the ``user is None`` guard).

    Distinct from the ``AnonymousUser`` case (denied later via ``has_perm``): under a
    live request ``AuthenticationMiddleware`` always sets ``request.user``, so this
    guard only fires when the resolved request has no ``user`` at all (a bare context
    / no auth middleware). It returns ``False`` before resolving the model, so the
    branch is unreachable from a live ``/graphql/`` request and is earned here.
    """
    mutation = _create_item_mutation()
    info = make_info(context=SimpleNamespace(request=SimpleNamespace()))
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is False


def test_deny_all_always_returns_false() -> None:
    """``DenyAll.has_permission`` returns ``False`` unconditionally across all operations."""
    deny = DenyAll()
    info = SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace(user=None)))
    mutation = _create_item_mutation()
    assert (
        deny.has_permission(info, mutation, "create", data={"name": "test"}, instance=None)
        is False
    )
    assert deny.has_permission(info, mutation, "update", data=None, instance=None) is False
    assert deny.has_permission(info, mutation, "delete", data=None, instance=None) is False
    assert deny.has_permission(info, mutation, "form", data={"ping": True}, instance=None) is False


def test_run_permission_classes_short_circuits_on_first_denial() -> None:
    """``run_permission_classes`` evaluates classes sequentially and short-circuits on first False."""
    eval_order: list[str] = []

    class AllowingPerm:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            eval_order.append("AllowingPerm")
            return True

    class DenyingPerm:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            eval_order.append("DenyingPerm")
            return False

    class NeverReachedPerm:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            eval_order.append("NeverReachedPerm")
            return True

    class GuardedMutation(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [AllowingPerm, DenyingPerm, NeverReachedPerm]

    result = run_permission_classes(
        GuardedMutation(),
        info=make_info(),
        operation="create",
        data=None,
        instance=None,
    )
    assert result is False
    assert eval_order == ["AllowingPerm", "DenyingPerm"]


@pytest.mark.parametrize(
    "invalid_result",
    [
        1,
        0,
        "true",
        "false",
        None,
        [],
        {},
        object(),
    ],
)
def test_require_sync_bool_auth_result_rejects_non_bool_values(invalid_result: object) -> None:
    """``_require_sync_bool_auth_result`` rejects non-bool values without coercion."""
    with pytest.raises(ConfigurationError, match="must return a bool"):
        _require_sync_bool_auth_result(invalid_result, owner="CustomPerm", method="has_permission")


def test_require_sync_bool_auth_result_message_is_exact() -> None:
    """The non-bool reject names the owner, the method and the rendered value."""
    with pytest.raises(ConfigurationError) as exc:
        _require_sync_bool_auth_result(1, owner="CustomPerm", method="has_permission")
    assert str(exc.value) == (
        "CustomPerm.has_permission must return a bool; got 1. Authorization results are "
        "never coerced from truthiness."
    )


# ---------------------------------------------------------------------------
# Class-state hostility: the walk reads a SNAPSHOT, never the live list
# ---------------------------------------------------------------------------


def test_walk_ignores_mid_request_pollution_of_the_class_permission_list() -> None:
    """A hook emptying the class's permission list cannot flip the in-flight walk.

    ``run_permission_classes`` iterates a SNAPSHOT (the tuple captured before the
    walk), never the class's list object: a ``has_permission`` hook receives the
    mutation class and can otherwise reach the exact list the loop is iterating -
    clearing it would hit ``StopIteration`` on the next read and the walk would
    return ALLOW without running the configured deniers, an authorization bypass
    that also PERSISTS on the class (every later request authorized by the
    polluted empty list, the allow-any posture). Over the snapshot the denier
    still runs and the deny is honored.
    """
    events: list[str] = []

    class AllowAndPollute:
        def has_permission(
            self,
            _info: object,
            mutation: type[object],
            _operation: str,
            _data: object,
            _instance: object = None,
        ) -> bool:
            # ``mutation`` IS the mutation class the walk passes; the pollution
            # reach is the exact object the walk would iterate live.
            try:
                # basedpyright: the hostile hook reaches the walked class's live permission list;
                # the hook receives the class as type[object], which declares no _mutation_meta
                mutation._mutation_meta.permission_classes.clear()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            except AttributeError:  # tuple substrate: in-place mutation refused
                events.append("pollution-refused")
                return True
            events.append("cleared")
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
            events.append("Denier")
            return False

    # LIST substrate: the hostile hook CAN clear the class's list mid-walk, the
    # bypass shape the snapshot walk refuses. Over the snapshot the denier still runs
    # and the deny is honored.
    class ListSubstrateMutation:
        _mutation_meta = SimpleNamespace(permission_classes=[AllowAndPollute, Denier])

    assert (
        run_permission_classes(
            # basedpyright: the mutable-list substrate is the input under test and a real
            # mutation seals its snapshot against it; run_permission_classes types the parameter
            # as DjangoMutation | DjangoFormMutation
            ListSubstrateMutation(),  # pyright: ignore[reportArgumentType]
            info=make_info(),
            operation="create",
            data=None,
            instance=None,
        )
        is False
    )
    # The hook really emptied the live list - the in-flight walk ran the denier
    # anyway (it iterates the captured snapshot, not the live list).
    assert read_attr(ListSubstrateMutation._mutation_meta, "permission_classes") == []
    assert events == ["cleared", "Denier"]

    # The SHIPPED tuple substrate refuses the in-place pollution outright, and
    # the walk still reaches the denier.
    events.clear()

    class TupleSubstrateMutation(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = (AllowAndPollute, Denier)

    assert (
        run_permission_classes(
            TupleSubstrateMutation(),
            info=make_info(),
            operation="create",
            data=None,
            instance=None,
        )
        is False
    )
    assert events == ["pollution-refused", "Denier"]
    # The shipped substrate is untouched by the pollution attempt.
    assert TupleSubstrateMutation._mutation_meta.permission_classes == (AllowAndPollute, Denier)


@pytest.mark.django_db
def test_permission_slot_refusal_preserves_snapshot_and_original_error() -> None:
    """A refused permission-slot write keeps the validated record and its original exception.

    The two-request HTTP verdict lives in ``test_mutation_permissions_api.py``. This
    row retains only the record's identity/type and the unencoded original error.
    """
    seed_data(1)

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
            return False

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

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

    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "Blocked", "categoryId": global_id_for(CategoryT, saved_pk(cat))}},
    )
    # The seal raises OUT of the walk: loud top-level failure, no write.
    assert res.errors is not None
    assert isinstance(res.errors[0].original_error, ConfigurationError)
    # The seal refused the rebind: the validated configuration is untouched.
    assert isinstance(CreateItem._mutation_meta, _ValidatedMutationMeta)
    assert CreateItem._mutation_meta.permission_classes == (AllowAndRebind, Denier)
