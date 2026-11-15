"""Current-user query tests for alias binding, permission gates, and sync/async resolution.

The ``current_user`` residue a live fakeshop request cannot drive: the
``CurrentUserAlias`` namespace lifecycle (the ``make_input_namespace`` trio +
its pre-bind ``register_subsystem_clear`` row), the surface-keyed
current-user-only bind (its no-``UserType`` arm + no orphan payloads), the
one-declaration conflict error, the sync/async dispatch counting, the
mapping-context request shape, the absent-user arms (the Channels adapter
shape, a lazy ``None``, a custom actor), the bare-string ``directives``
rejection, the gated-anonymous ``GraphQLError`` and its exact denial string,
a raising ``is_authenticated``'s propagation, and the async lazy-user forcing inside the one
``sync_to_async`` boundary. The live ``me`` behavior (authenticated /
anonymous / no-``AuthenticationMiddleware`` / hide-everyone ``get_queryset``
skip / ``me: UserType`` SDL / unplanned relation under ``strictness="raise"``)
is earned in
``examples/fakeshop/test_query/test_auth_api.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import pytest
import strawberry
from apps.products.services import create_users
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils.functional import SimpleLazyObject
from strawberry import relay

from django_strawberry_framework import DjangoSchema, DjangoType, finalize_django_types
from django_strawberry_framework.auth import current_user
from django_strawberry_framework.auth import queries as auth_queries
from django_strawberry_framework.auth.queries import (
    CURRENT_USER_ALIAS_NAME,
    _current_user_alias_names,
    clear_current_user_alias_namespace,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.inputs import _materialized_names
from django_strawberry_framework.registry import iter_subsystem_clears
from tests.auth._helpers import _session_request

pytestmark = pytest.mark.usefixtures("isolate_global_registry")


class _IsAuthenticated:
    """An ``IsAuthenticated``-style gate: denies the anonymous caller."""

    def has_permission(
        self,
        _info: object,
        _mutation: type[object],
        _operation: str,
        _data: object,
        instance: object = None,
    ) -> bool:
        return instance is not None


def _declare_user_type() -> type:
    """Register a fresh Relay-backed primary ``DjangoType`` over the user model."""
    return type(
        "UserT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": User, "fields": ("id", "username", "email"), "primary": True},
            ),
        },
    )


def _me_schema(
    *,
    declare: Callable[[], object] = _declare_user_type,
    permission_classes: Iterable[type[object]] | None = None,
) -> strawberry.Schema:
    """Declare UserT + a me-only Query; return the finalized schema.

    ``declare`` is the per-call user-type declaration callable;
    ``permission_classes`` flows to ``current_user``.
    """
    declare()

    @strawberry.type
    class Query:
        me = current_user(permission_classes=permission_classes)

    finalize_django_types()
    return DjangoSchema(query=Query)


class _FakeConsumer:
    """The ``consumer`` half of Strawberry's ``ChannelsRequest`` duck shape."""

    def __init__(self, scope: dict[str, object]) -> None:
        self.scope = scope


class _FakeChannelsRequest:
    """A ``ChannelsRequest``-shaped object: ``consumer.scope`` + request attrs."""

    def __init__(self, scope: dict[str, object]) -> None:
        self.consumer = _FakeConsumer(scope)
        self.headers = {}
        self.method = "POST"


def _channels_context(scope: dict[str, object]) -> dict[str, _FakeChannelsRequest]:
    """Build a Strawberry-Channels mapping context (spec-041) that resolves to the adapter."""
    return {"request": _FakeChannelsRequest(scope)}


_ME_Q = "{ me { username } }"


def test_alias_namespace_rides_make_input_namespace_and_the_pre_bind_row() -> None:
    """The alias is a ``make_input_namespace``-owned emit artifact with a pre-bind row."""
    assert clear_current_user_alias_namespace in iter_subsystem_clears(before_bind=True)

    user_type = _declare_user_type()

    @strawberry.type
    class Query:
        me = current_user()

    finalize_django_types()
    # The bind pinned the resolved user primary as this module's parked global
    # (the ``strawberry.lazy`` target) through the trio's materializer.
    assert auth_queries.CurrentUserAlias is user_type
    assert _current_user_alias_names == {CURRENT_USER_ALIAS_NAME: user_type}


def test_current_user_only_bind_emits_no_login_logout_payloads() -> None:
    """The surface-keyed bind: a me-only schema materializes the alias and nothing else."""
    _me_schema()
    assert "LoginPayload" not in _materialized_names
    assert "LogoutPayload" not in _materialized_names
    assert CURRENT_USER_ALIAS_NAME in _current_user_alias_names


def test_current_user_only_schema_without_user_type_raises_its_own_arm() -> None:
    """The current-user arm's auth-specific message, distinct from login's."""

    @strawberry.type
    class Query:
        me = current_user()

    with pytest.raises(
        ConfigurationError,
        match=r"auth current_user\(\) declared with no registered DjangoType for the user model",
    ):
        finalize_django_types()


def test_conflicting_current_user_gates_raise_the_one_declaration_error() -> None:
    current_user()
    with pytest.raises(ConfigurationError, match=r"auth current_user\(\) is already declared"):
        current_user(permission_classes=[_IsAuthenticated])


@pytest.mark.django_db
def test_sync_me_dispatch_never_enters_the_async_boundary(
    sync_boundary_spy: list[Callable[..., object]],
) -> None:
    """``execute_sync`` ``me`` runs the native sync body with no event-loop bridge."""
    create_users(1)
    schema = _me_schema()
    user = User.objects.get(username="regular_1")
    user.username = "me_sync"
    user.set_password("pw-9x-strong")
    user.save(update_fields=["username", "password"])
    res = schema.execute_sync(_ME_Q, context_value=_session_request(user))
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["me"] == {"username": "me_sync"}
    assert sync_boundary_spy == []


@pytest.mark.django_db(transaction=True)
async def test_async_me_dispatch_awaits_the_bridged_async_body_exactly_once(
    sync_boundary_spy: list[Callable[..., object]],
) -> None:
    """``await schema.execute`` ``me`` awaits the bridged async body exactly once."""
    await sync_to_async(create_users)(1)
    schema = _me_schema()
    user = await User.objects.aget(username="regular_1")
    user.username = "me_async"
    user.set_password("pw-9x-strong")
    await user.asave(update_fields=["username", "password"])
    res = await schema.execute(_ME_Q, context_value=_session_request(user))
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["me"] == {"username": "me_async"}
    assert len(sync_boundary_spy) == 1


@pytest.mark.django_db
def test_me_accepts_a_regular_mapping_context_with_a_django_request() -> None:
    """A direct ``Schema.execute`` mapping context carries its Django request to ``me``."""
    create_users(1)
    schema = _me_schema()
    user = User.objects.get(username="regular_1")
    user.username = "mapping_me"
    user.set_password("pw-9x-strong")
    user.save(update_fields=["username", "password"])

    result = schema.execute_sync(_ME_Q, context_value={"request": _session_request(user)})

    assert result.errors is None, result.errors
    assert result.data is not None
    assert result.data["me"] == {"username": "mapping_me"}


@pytest.mark.django_db
def test_me_is_null_not_a_crash_when_the_request_user_is_absent() -> None:
    """An absent request user is anonymous -> ``null``, never a ``'NoneType'`` crash.

    ``request.user`` is ``None`` for a Strawberry-Channels
    ``ChannelsRequestAdapter`` whose scope carries no
    ``AuthMiddlewareStack``-populated user (spec-041's supported adapter shape;
    ``tests/utils/test_permissions.py`` pins ``.user`` -> ``None`` there).
    The no-``AuthenticationMiddleware`` Django HTTP arm lives in
    ``examples/fakeshop/test_query/test_auth_api.py``. Remaining arms here are
    the Channels adapter plus actor shapes a live request cannot mint.
    """
    schema = _me_schema()

    # The Channels adapter shape: a mapping context whose scope has no ``user`` key,
    # so ``ChannelsRequestAdapter.user`` returns ``None``.
    channels = schema.execute_sync(
        _ME_Q,
        context_value=_channels_context({"type": "websocket"}),
    )
    assert channels.errors is None, channels.errors
    assert channels.data is not None
    assert channels.data["me"] is None

    # A SimpleLazyObject returning None (lazy unauthenticated user resolving to None).
    lazy_none = RequestFactory().post("/graphql/")
    # basedpyright: the non-user object planted on request.user is the hostile input under
    # test; django-stubs types the slot as AbstractBaseUser | AnonymousUser
    lazy_none.user = SimpleLazyObject(lambda: None)  # pyright: ignore[reportAttributeAccessIssue]
    lazy_none_res = schema.execute_sync(_ME_Q, context_value=lazy_none)
    assert lazy_none_res.errors is None, lazy_none_res.errors
    assert lazy_none_res.data is not None
    assert lazy_none_res.data["me"] is None

    # A custom actor object without is_authenticated attribute.
    custom_actor = RequestFactory().post("/graphql/")
    # basedpyright: the non-user object planted on request.user is the hostile input under
    # test; django-stubs types the slot as AbstractBaseUser | AnonymousUser
    custom_actor.user = object()  # pyright: ignore[reportAttributeAccessIssue]
    custom_res = schema.execute_sync(_ME_Q, context_value=custom_actor)
    assert custom_res.errors is None, custom_res.errors
    assert custom_res.data is not None
    assert custom_res.data["me"] is None


@pytest.mark.django_db
def test_a_raising_is_authenticated_propagates_to_the_error_policy() -> None:
    """The user model's ``is_authenticated`` is consumer behaviour: its exception propagates.

    It is never collapsed to anonymous ``null``; the field errors, and the
    schema's error policy masks the unexpected exception on the wire.
    """

    class RaisingIsAuth:
        @property
        def is_authenticated(self) -> bool:
            raise ValueError("is_authenticated failed")

    schema = _me_schema()
    req = RequestFactory().post("/graphql/")
    # basedpyright: the non-user object planted on request.user is the input under test;
    # django-stubs types the slot as AbstractBaseUser | AnonymousUser
    req.user = RaisingIsAuth()  # pyright: ignore[reportAttributeAccessIssue]
    res = schema.execute_sync(_ME_Q, context_value=req)
    assert res.errors is not None
    assert res.errors[0].message == "An unexpected error occurred."
    assert res.errors[0].path == ["me"]


def test_current_user_bare_string_directives_raise_configuration_error() -> None:
    """A bare string ``directives`` value is rejected, never iterated character-wise."""
    with pytest.raises(ConfigurationError):
        current_user(directives="oops")


@pytest.mark.django_db
def test_gated_me_denies_the_anonymous_caller_with_the_exact_pinned_string() -> None:
    """An ``IsAuthenticated``-style gate turns anonymous ``null`` into the ``GraphQLError``."""
    create_users(1)
    schema = _me_schema(permission_classes=[_IsAuthenticated])
    denied = schema.execute_sync(_ME_Q, context_value=_session_request())
    assert denied.errors is not None
    assert denied.errors[0].message == "Not authorized to current_user UserT."

    user = User.objects.get(username="regular_1")
    user.username = "gated_probe"
    user.set_password("pw-9x-strong")
    user.save(update_fields=["username", "password"])
    allowed = schema.execute_sync(_ME_Q, context_value=_session_request(user))
    assert allowed.errors is None, allowed.errors
    assert allowed.data is not None
    assert allowed.data["me"] == {"username": "gated_probe"}


@pytest.mark.django_db(transaction=True)
async def test_async_gated_me_forces_the_lazy_user_inside_the_one_sync_boundary() -> None:
    """The gate's ``instance=request.user`` forces the ``SimpleLazyObject`` in-boundary.

    The spec-040 Decision 10 async gate: computing the gate argument forces the lazy
    user (a sync ORM touch that would raise ``SynchronousOnlyOperation`` outside
    a sync context); because the whole gate-then-return body runs inside the ONE
    ``sync_to_async(thread_sensitive=True)`` worker, the forced load succeeds and
    the recorded gate ``instance`` is the real user row.
    """
    await sync_to_async(create_users)(1)
    seen: dict[str, object] = {}

    class RecordingGate:
        def has_permission(
            self,
            _info: object,
            _mutation: type[object],
            operation: str,
            data: object,
            instance: object = None,
        ) -> bool:
            seen.update(operation=operation, data=data, instance=instance)
            return True

    schema = _me_schema(permission_classes=[RecordingGate])
    user = await User.objects.aget(username="regular_1")
    user.username = "lazy_probe"
    user.set_password("pw-9x-strong")
    await user.asave(update_fields=["username", "password"])

    request = RequestFactory().post("/graphql/")
    SessionMiddleware(lambda _request: HttpResponse()).process_request(request)
    # The middleware shape: a lazy user whose first attribute access hits the ORM.
    # basedpyright: AuthenticationMiddleware installs a SimpleLazyObject on request.user;
    # django-stubs types the slot as AbstractBaseUser | AnonymousUser
    request.user = SimpleLazyObject(lambda: User.objects.get(username="lazy_probe"))  # pyright: ignore[reportAttributeAccessIssue]

    res = await schema.execute(_ME_Q, context_value=request)
    assert res.errors is None, res.errors
    assert res.data is not None
    assert res.data["me"] == {"username": "lazy_probe"}
    assert seen["operation"] == "current_user"
    assert seen["data"] is None
    assert seen["instance"] == user
