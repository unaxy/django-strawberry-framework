"""Construction-time and handshake-projection units for the WebSocket consumer.

Package-tier because fakeshop has no ``config/asgi.py`` and no WebSocket
mount: a live ``/graphql/`` HTTP request cannot present a Channels scope,
drive ``WebsocketCommunicator``, or reach either actor-revalidation
checkpoint. That fixture gap is recorded with ``tests/test_routers.py`` in
``examples/fakeshop/test_query/README.md``; this file does not add the mount.

What a live HTTP request cannot express, and what therefore stays here:

- construction-time ``resolved_revalidation_window`` (pure function;
  ``tests/test_routers.py`` drives the same domain through router
  construction);
- ``_host_validation_request`` projection shape (handshake verdicts live
  in ``tests/test_routers.py`` via ``WebsocketCommunicator``);
- ``connection_actor_state``'s typed rejection of a corrupted scope slot used
  by those checkpoints (happy-path lease lifecycle is
  ``tests/utils/test_sessions.py``).

Both revalidation checkpoints, the revocation-gated adapter and
``_revoke_connection`` are driven end to end through ``WebsocketCommunicator``
in ``tests/test_routers.py``. The HTTP transport boundary is earned over
fakeshop's real ``/graphql/`` in ``examples/fakeshop/test_query/test_transport_api.py``.
"""

from __future__ import annotations

import pytest

from django_strawberry_framework import consumers as cmod
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.sessions import (
    _ACTOR_STATE_SCOPE_KEY,
    connection_actor_state,
)
from tests._idioms import websocket_scope

# ---------------------------------------------------------------------------
# utils/sessions - corrupted scope state (owning layer)
# ---------------------------------------------------------------------------


def test_connection_actor_state_corrupted_value_raises_configuration_error() -> None:
    scope: dict[str, object] = {_ACTOR_STATE_SCOPE_KEY: "not-a-state"}
    with pytest.raises(ConfigurationError, match="corrupted"):
        connection_actor_state(scope)


# ---------------------------------------------------------------------------
# resolved_revalidation_window - construction-time domain
# ---------------------------------------------------------------------------


class _WindowIntSubclass(int):
    """An ``int`` subclass the exact-type window gate must reject."""


class _WindowFloatSubclass(float):
    """A ``float`` subclass the exact-type window gate must reject."""


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(True, id="true"),
        pytest.param(False, id="false"),
        pytest.param(_WindowIntSubclass(1), id="int-subclass"),
        pytest.param(_WindowFloatSubclass(1.0), id="float-subclass"),
        pytest.param("1.0", id="string"),
        pytest.param(None, id="none"),
        pytest.param([], id="list"),
        pytest.param({}, id="dict"),
    ],
)
def test_resolved_window_rejects_bool_and_subclasses(bad: object) -> None:
    """Only the built-in ``int`` and ``float`` types are a usable window."""
    with pytest.raises(ConfigurationError):
        cmod.resolved_revalidation_window(bad)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="inf"),
        pytest.param(float("-inf"), id="neg-inf"),
        pytest.param(-0.1, id="negative-float"),
        pytest.param(-1, id="negative-int"),
    ],
)
def test_resolved_window_rejects_nan_and_inf_and_negative(bad: float) -> None:
    """A non-finite or negative number is not a usable number of seconds."""
    with pytest.raises(ConfigurationError):
        cmod.resolved_revalidation_window(bad)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(0, 0.0, id="int-zero"),
        pytest.param(0.0, 0.0, id="float-zero"),
        pytest.param(1, 1.0, id="int-one"),
        pytest.param(1.5, 1.5, id="float-fraction"),
        pytest.param(10**300, float(10**300), id="astronomical-int"),
    ],
)
def test_resolved_window_accepts_zero_and_positive(value: float, expected: float) -> None:
    """Zero and every finite non-negative number coerce to ``float``."""
    assert cmod.resolved_revalidation_window(value) == expected


def test_resolved_window_rejection_message_names_the_value() -> None:
    """The rejection's honest message, byte for byte."""
    with pytest.raises(ConfigurationError) as excinfo:
        cmod.resolved_revalidation_window("1.0")
    assert str(excinfo.value) == (
        "websocket_revalidation_window must be a finite number of seconds >= 0.0 that "
        "converts to a float (0.0 revalidates the session actor at every operation "
        "admission and before every information-bearing operation frame); got str '1.0'."
    )


def test_resolved_window_huge_int_overflow_is_configuration_error() -> None:
    """An ``int`` with no ``float`` image is a typed construction error, chained."""
    huge = 10**10000
    with pytest.raises(ConfigurationError) as excinfo:
        cmod.resolved_revalidation_window(huge)
    assert isinstance(excinfo.value.__cause__, OverflowError)


# ---------------------------------------------------------------------------
# _host_validation_request - WebSocket handshake Host projection
# ---------------------------------------------------------------------------


def test_host_validation_absent_headers_and_server_uses_defaults() -> None:
    """A scope with neither Host headers nor ``server`` reconstructs Django's literals."""
    scope: dict[str, object] = {}
    # basedpyright: the absent keys (no headers, no server) are the input under test; asgiref's
    # WebSocketScope declares every key required
    req = cmod._host_validation_request(scope)  # pyright: ignore[reportArgumentType]
    assert req.META["SERVER_NAME"] == "unknown"
    assert req.META["SERVER_PORT"] == "0"
    assert "HTTP_HOST" not in req.META


def test_host_validation_duplicate_hosts_are_comma_joined() -> None:
    """Two Host headers become Django's comma-joined form, not a silently picked one."""
    scope = websocket_scope([(b"host", b"a.com"), (b"host", b"b.com")], ("x", 80))
    req = cmod._host_validation_request(scope)
    assert req.META["HTTP_HOST"] == "a.com,b.com"


def test_host_validation_case_insensitive_header() -> None:
    """Header names are normalized; an odd-cased ``Host`` still projects."""
    scope = websocket_scope([(b"Host", b"example.com")], ("x", 80))
    req = cmod._host_validation_request(scope)
    assert req.META["HTTP_HOST"] == "example.com"


@pytest.mark.parametrize(
    "server",
    [
        pytest.param(None, id="none"),
        pytest.param(0, id="zero"),
        pytest.param(False, id="false"),
        pytest.param("", id="empty-str"),
    ],
)
def test_host_validation_server_absent_vs_null(server: object) -> None:
    """A falsy ``scope['server']`` uses the same ``unknown`` reconstruction as absence."""
    scope: dict[str, object] = {"headers": [], "server": server}
    # basedpyright: the ill-typed server value is the input under test; asgiref's WebSocketScope
    # types server as tuple[str, int | None] | None
    req = cmod._host_validation_request(scope)  # pyright: ignore[reportArgumentType]
    assert req.META["SERVER_NAME"] == "unknown"
