"""Behavioral tests for the session-engine resolver and connection actor lease.

``session_store_class`` malformed and hostile ``SESSION_ENGINE`` shapes and the WebSocket actor
lease have no GraphQL document: login/logout sessions live in
``examples/fakeshop/test_query/test_auth_api.py``; actor serialization stays here
until fakeshop mounts ASGI.
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import types
from typing import NoReturn

import pytest
from django.contrib.sessions.backends.db import SessionStore as DBSessionStore
from django.contrib.sessions.backends.signed_cookies import (
    SessionStore as SignedCookieSessionStore,
)
from django.test import override_settings
from django.utils.functional import SimpleLazyObject

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.sessions import (
    _ACTOR_STATE_SCOPE_KEY,
    ConnectionActorState,
    actor_lease,
    actor_transition,
    connection_actor_state,
    connection_was_authenticated,
    note_authenticated_actor,
    session_store_class,
)
from tests._idioms import ClaimsClass, ClassReadRaises, stub_module
from tests.auth._helpers import _drain_until

# ---------------------------------------------------------------------------
# session_store_class
# ---------------------------------------------------------------------------


def test_session_store_class_resolves_default_engine() -> None:
    """Default engine resolves to Django's DB SessionStore."""
    resolved = session_store_class()
    assert resolved is DBSessionStore


@override_settings(SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies")
def test_session_store_class_honors_override_settings() -> None:
    """Settings overrides at call time dynamically resolve the new store class."""
    resolved = session_store_class()
    assert resolved is SignedCookieSessionStore


def test_session_store_class_resolves_custom_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    """A custom session engine resolves identically via import_string."""
    module_name = "tests.utils._stub_custom_session_engine"

    class CustomSessionStore:
        pass

    module = stub_module(module_name, SessionStore=CustomSessionStore)
    monkeypatch.setitem(sys.modules, module_name, module)

    with override_settings(SESSION_ENGINE=module_name):
        assert session_store_class() is CustomSessionStore


@override_settings(SESSION_ENGINE=object())
def test_session_store_class_rejects_a_non_string_engine() -> None:
    """A non-string ``SESSION_ENGINE`` names no importable engine."""
    with pytest.raises(ConfigurationError, match="Could not resolve SESSION_ENGINE <object"):
        session_store_class()


@override_settings(SESSION_ENGINE="")
def test_session_store_class_rejects_an_empty_engine() -> None:
    """An empty ``SESSION_ENGINE`` names no module."""
    with pytest.raises(
        ConfigurationError,
        match=r"SESSION_ENGINE ''.s SessionStore \(ValueError\)",
    ):
        session_store_class()


@override_settings(SESSION_ENGINE="tests.utils._no_such_session_engine")
def test_session_store_class_reports_an_unresolvable_engine_as_configuration_error() -> None:
    """An engine that does not import is a ``ConfigurationError`` naming the engine."""
    with pytest.raises(ConfigurationError, match="_no_such_session_engine"):
        session_store_class()


def test_session_store_class_reports_a_storeless_engine_as_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An engine module WITHOUT ``SessionStore`` is a ``ConfigurationError``, not an ImportError.

    ``import_string`` raises ``ImportError`` for a missing module and for a
    missing attribute alike; both arrive at the same guard, so the module-exists
    arm needs its own proof.
    """
    module_name = "tests.utils._stub_storeless_session_engine"
    monkeypatch.setitem(sys.modules, module_name, types.ModuleType(module_name))

    with (
        override_settings(SESSION_ENGINE=module_name),
        pytest.raises(ConfigurationError, match="SessionStore"),
    ):
        session_store_class()


class _PlainSubclassEngine(str):
    """A deployment-supplied engine subclass with benign dunders."""


@override_settings(
    SESSION_ENGINE=_PlainSubclassEngine("django.contrib.sessions.backends.db"),
)
def test_session_store_class_plain_subclass_engine_resolves() -> None:
    """A benign ``str`` subclass resolves exactly like the string it carries."""
    assert session_store_class() is DBSessionStore


@pytest.mark.parametrize(
    "engine",
    [
        pytest.param(ClassReadRaises(RuntimeError), id="class-read-raises"),
        pytest.param(ClassReadRaises(KeyboardInterrupt), id="class-read-interrupts"),
        pytest.param(ClaimsClass(str), id="claims-str"),
    ],
)
def test_session_store_class_rejects_an_engine_that_is_not_really_a_string(engine: object) -> None:
    """An engine whose ``__class__`` raises or claims ``str`` names no importable engine."""
    with override_settings(SESSION_ENGINE=engine), pytest.raises(ConfigurationError) as excinfo:
        session_store_class()
    assert str(excinfo.value).startswith("Could not resolve SESSION_ENGINE <")


@override_settings(
    SESSION_ENGINE=SimpleLazyObject(lambda: "django.contrib.sessions.backends.db"),
)
def test_session_store_class_resolves_a_lazy_engine_as_django_does() -> None:
    """A lazy engine name resolves like the string it carries, as Django's middleware does."""
    assert session_store_class() is DBSessionStore


@override_settings(SESSION_ENGINE=_PlainSubclassEngine("tests.utils._no_such_session_engine"))
def test_session_store_class_unresolvable_engine_message_is_pinned() -> None:
    """The import-failure rejection renders the engine as the exact string it carries."""
    with pytest.raises(ConfigurationError) as excinfo:
        session_store_class()
    assert str(excinfo.value) == (
        "Could not resolve SESSION_ENGINE 'tests.utils._no_such_session_engine''s "
        "SessionStore (ModuleNotFoundError); check settings.SESSION_ENGINE."
    )


# ---------------------------------------------------------------------------
# ConnectionActorState & connection_actor_state
# ---------------------------------------------------------------------------


def test_connection_actor_state_initialization() -> None:
    """Initial state has unlatched provenance and an asyncio.Lock."""
    state = ConnectionActorState()
    assert state.authenticated_provenance is False
    assert isinstance(state.lock, asyncio.Lock)
    assert not state.lock.locked()


def test_connection_actor_state_slots_prevent_arbitrary_attributes() -> None:
    """__slots__ enforces exact field shape and raises AttributeError on typos."""
    state = ConnectionActorState()
    with pytest.raises(AttributeError):
        # basedpyright: the undeclared slot write is the rejected operation under test
        state.unknown_field = True  # pyright: ignore[reportAttributeAccessIssue]


def test_connection_actor_state_get_or_create_reused_per_scope() -> None:
    """First access stores state under the private scope key; subsequent accesses return the same instance."""
    scope: dict[str, object] = {}
    state1 = connection_actor_state(scope)
    assert isinstance(state1, ConnectionActorState)
    assert _ACTOR_STATE_SCOPE_KEY in scope
    assert scope[_ACTOR_STATE_SCOPE_KEY] is state1

    state2 = connection_actor_state(scope)
    assert state2 is state1


def test_connection_actor_state_isolated_across_scopes() -> None:
    """Distinct scope dictionaries receive independent ConnectionActorState instances."""
    scope1: dict[str, object] = {}
    scope2: dict[str, object] = {}
    state1 = connection_actor_state(scope1)
    state2 = connection_actor_state(scope2)
    assert state1 is not state2
    assert state1.lock is not state2.lock


# ---------------------------------------------------------------------------
# note_authenticated_actor & connection_was_authenticated
# ---------------------------------------------------------------------------


def test_note_authenticated_actor_latches_provenance() -> None:
    """Provenance is initially False, becomes True on note, and remains True."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    note_authenticated_actor(scope)
    assert connection_was_authenticated(scope) is True

    # Repeated calls are idempotent
    note_authenticated_actor(scope)
    assert connection_was_authenticated(scope) is True


# ---------------------------------------------------------------------------
# actor_lease & actor_transition
# ---------------------------------------------------------------------------


async def test_actor_lease_returns_scope_lock() -> None:
    """actor_lease returns the ConnectionActorState lock and can be held via async with."""
    scope: dict[str, object] = {}
    lock = actor_lease(scope)
    assert isinstance(lock, asyncio.Lock)
    assert lock is connection_actor_state(scope).lock

    async with actor_lease(scope) as held_lock:
        assert held_lock is None  # asyncio.Lock.__aenter__ returns None
        assert lock.locked()
    assert not lock.locked()


async def test_actor_transition_with_authenticated_latches_provenance() -> None:
    """actor_transition(was_authenticated=True) latches provenance and holds lease."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async with actor_transition(scope, was_authenticated=True):
        assert connection_was_authenticated(scope) is True
        assert actor_lease(scope).locked()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is True


async def test_actor_transition_without_authenticated_does_not_latch_provenance() -> None:
    """actor_transition(was_authenticated=False) holds lease without latching provenance."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async with actor_transition(scope, was_authenticated=False):
        assert connection_was_authenticated(scope) is False
        assert actor_lease(scope).locked()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is False


async def test_actor_transition_failure_still_latches_provenance_and_releases_lease() -> None:
    """Fail closed: an exception inside actor_transition still latches provenance and frees lease."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async def body_that_raises() -> NoReturn:
        async with actor_transition(scope, was_authenticated=True):
            assert connection_was_authenticated(scope) is True
            raise RuntimeError("teardown boom")

    with pytest.raises(RuntimeError, match="teardown boom"):
        await body_that_raises()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is True


async def test_actor_transition_and_lease_are_mutually_exclusive() -> None:
    """An in-flight actor_transition serializes against another task acquiring actor_lease."""
    scope: dict[str, object] = {}
    transition_entered = asyncio.Event()
    transition_can_exit = asyncio.Event()
    lease_acquired = {"value": False}

    async def task_transition() -> None:
        async with actor_transition(scope, was_authenticated=True):
            transition_entered.set()
            await transition_can_exit.wait()

    async def task_lease() -> None:
        await transition_entered.wait()
        async with actor_lease(scope):
            lease_acquired["value"] = True

    tt = asyncio.create_task(task_transition())
    tl = asyncio.create_task(task_lease())

    try:
        await transition_entered.wait()
        lock = actor_lease(scope)
        await _drain_until(lambda: bool(getattr(lock, "_waiters", None)))

        assert lock.locked()
        assert lease_acquired["value"] is False

        transition_can_exit.set()
        await asyncio.gather(tt, tl)

        assert lease_acquired["value"] is True
        assert not lock.locked()
    finally:
        for task in (tt, tl):
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
