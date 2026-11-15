"""DB-free test-client tests for endpoints, multipart bodies, responses, mixin assertions, and exports.

Placement per spec-043 Decision 11 and the live-first split: every
case that drives a real ``/graphql/`` request (the sync raising direction on a
live invalid selection, the ``AsyncTestClient`` paths, and the unittest family
end to end) lives in ``examples/fakeshop/test_query/test_client_api.py`` so it is
earned live per the ``test_query/README.md`` coverage rule. This file owns only
what a live request cannot (or need not) pin:

- the endpoint-resolution precedence ladder (per-call > constructor > class attr
  > settings key > default), proven against recording transports;
- the owned builder's uniform path-keyed map rule;
- ``files={}`` staying a plain JSON post;
- the assertion helpers' FAILURE directions against canned responses (their
  PASSING directions ride the live unittest tests);
- the mixin's ``self.client`` delegation and endpoint rungs against a recording
  client;
- the ``__test__ = False`` collection guard and the export surface.

``login()`` logout-on-exception is live in
``examples/fakeshop/test_query/test_client_api.py`` (sync and async); the
clean-exit sync bracket stays in ``test_products_api.py``.

Every test here is DB-free: no schema reload, no ``seed_data``, no database row.
The recording transports are real ``django.test.Client`` / ``AsyncClient``
subclasses, so each post is a real request through Django's own handler, routed
by this module's ``urlpatterns`` (its own ``ROOT_URLCONF``, no middleware) to a
local view that answers with the canned JSON payload the transport attached.
"""

import json
import unittest
from collections import UserDict
from collections.abc import Callable, Iterator, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseBase
from django.test import AsyncClient, Client, override_settings
from django.test.client import MULTIPART_CONTENT
from django.urls import re_path
from graphql import GraphQLFormattedError
from typing_extensions import override

import django_strawberry_framework
from django_strawberry_framework import testing as testing_root
from django_strawberry_framework.testing import (
    AsyncTestClient,
    GraphQLTestMixin,
    Response,
    TestClient,
)
from django_strawberry_framework.utils._narrowing import read_attr
from tests._idioms import json_at, json_loads

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedASGIResponse, _MonkeyPatchedWSGIResponse
    from django_stubs_ext import StrOrPromise

# ---------------------------------------------------------------------------
# Recording transports: real Django test clients whose ``post`` records its
# target, so TARGET SELECTION and body shape are read off what the package's own
# ``request()`` chose, and the canned answer comes from a local view rather than
# the fakeshop schema. The recording stops at the transport seam deliberately -
# one that overrode ``request()`` would re-implement the selection under test.
# Every test in this file is DB-free.
# ---------------------------------------------------------------------------


_CANNED_PAYLOAD_HEADER = "X-Canned-Payload"
_DEFAULT_PAYLOAD: dict[str, object] = {"data": {"ok": True}}


def _canned_view(request: HttpRequest) -> HttpResponse:
    """Answer every request with the JSON payload the recording client attached."""
    return JsonResponse(json.loads(request.headers.get(_CANNED_PAYLOAD_HEADER, "{}")))


#: This module is its own ``ROOT_URLCONF``: every path reaches the canned view.
urlpatterns = [re_path(r"^.*$", _canned_view)]


@pytest.fixture(autouse=True)
def _canned_transport_urlconf() -> Iterator[None]:
    """Route the real Django clients below to ``_canned_view`` with no middleware in the way."""
    with override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[]):
        yield


class _RecordingDjangoClient(Client):
    """A real ``django.test.Client`` recording ``post`` targets.

    The transport-level seam: it is the wrapped Django client, so the URL it
    records is the one the real ``TestClient.request`` chose, and the response it
    returns is a genuine one from Django's own request pipeline. A double that
    overrode ``request()`` itself would re-implement the selection under test and
    could never detect a change to it.
    """

    def __init__(self) -> None:
        super().__init__()
        self.posts: list[tuple[str, dict[str, object]]] = []
        self.responses: list[HttpResponseBase] = []

    @override
    def post(
        self,
        path: "StrOrPromise",
        data: object = None,
        content_type: str = MULTIPART_CONTENT,
        follow: bool = False,
        secure: bool = False,
        *,
        headers: Mapping[str, str] | None = None,
        query_params: Mapping[object, object] | None = None,
        **extra: object,
    ) -> "_MonkeyPatchedWSGIResponse":
        self.posts.append(
            (str(path), {"data": data, "content_type": content_type, "headers": headers}),
        )
        response = super().post(
            path,
            data,
            content_type,
            follow,
            secure,
            headers={**(headers or {}), _CANNED_PAYLOAD_HEADER: json.dumps(_DEFAULT_PAYLOAD)},
            query_params=query_params,
            **extra,
        )
        self.responses.append(response)
        return response


class _RecordingAsyncTransport(AsyncClient):
    """A real ``django.test.AsyncClient`` whose awaited ``post`` records its target."""

    def __init__(self) -> None:
        super().__init__()
        self.posts: list[tuple[str, dict[str, object]]] = []
        self.responses: list[HttpResponseBase] = []

    @override
    async def post(
        self,
        path: "StrOrPromise",
        data: object = None,
        content_type: str = MULTIPART_CONTENT,
        follow: bool = False,
        secure: bool = False,
        *,
        headers: Mapping[str, str] | None = None,
        query_params: Mapping[object, object] | None = None,
        **extra: object,
    ) -> "_MonkeyPatchedASGIResponse":
        self.posts.append(
            (str(path), {"data": data, "content_type": content_type, "headers": headers}),
        )
        response = await super().post(
            path,
            data,
            content_type,
            follow,
            secure,
            headers={**(headers or {}), _CANNED_PAYLOAD_HEADER: json.dumps(_DEFAULT_PAYLOAD)},
            query_params=query_params,
            **extra,
        )
        self.responses.append(response)
        return response


class _FalsySyncClient(_RecordingDjangoClient):
    """Falsy through ``__bool__``."""

    def __bool__(self) -> bool:
        return False


class _BoolFalsyAsyncTransport(_RecordingAsyncTransport):
    """Falsy through ``__bool__``."""

    def __bool__(self) -> bool:
        return False


class _LenFalsyAsyncTransport(_RecordingAsyncTransport):
    """Falsy through an empty ``__len__`` - the other spelling of falsiness."""

    def __len__(self) -> int:
        return 0


class _MixinProbe(GraphQLTestMixin):
    """A bare mixin composition proving ``query()`` reads only ``self.client``.

    It declares the host surface the mixin is typed against: the Django client slot and the
    three unittest assertions the helpers call.
    """

    client: Client

    def __init__(self) -> None:
        self.client = _RecordingDjangoClient()

    def assertEqual(  # noqa: N802 - unittest host method name
        self,
        first: object,
        second: object,
        msg: object = None,
    ) -> None:
        """Fail unless ``first == second``."""
        assert first == second, msg

    def assertIsNone(self, obj: object, msg: object = None) -> None:  # noqa: N802 - unittest host method name
        """Fail unless ``obj is None``."""
        assert obj is None, msg

    def assertTrue(self, expr: object, msg: object = None) -> None:  # noqa: N802 - unittest host method name
        """Fail unless ``expr`` is truthy."""
        assert expr, msg


class _AltProbe(_MixinProbe):
    """A mixin probe pinning its endpoint by class attribute (rung 3)."""

    GRAPHQL_URL: str | None = "/classattr/"


# ---------------------------------------------------------------------------
# Endpoint resolution - DB-free mechanics.
# ---------------------------------------------------------------------------


def test_default_endpoint_is_graphql_with_trailing_slash() -> None:
    """No settings key -> ``"/graphql/"`` (fakeshop's mount, slash kept)."""
    assert TestClient().path == "/graphql/"


def test_settings_key_sets_the_endpoint_and_the_default_restores_after_override() -> None:
    """The ``TESTING_ENDPOINT`` key is read at construction, on both clients.

    The second half pins the ``conf.py`` ``setting_changed`` receiver: after the
    override exits, a fresh client is back on the default - the settings read is
    live, not baked in at import.
    """
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/alt/"}):
        assert TestClient().path == "/alt/"
        assert AsyncTestClient().path == "/alt/"  # the async twin rides the same ladder
    assert TestClient().path == "/graphql/"


def test_constructor_path_outranks_the_settings_key() -> None:
    """Constructor rung: an explicit ``path=`` wins over the settings key.

    The resolved endpoint is also forwarded to the engine base, so the
    inherited ``url`` attribute mirrors ``path`` instead of reading the base's
    ``"/graphql/"`` default while ``path`` reads the real endpoint.
    """
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/settings/"}):
        client = TestClient("/explicit/")
    assert client.path == "/explicit/"
    assert client.url == "/explicit/"  # the base's attribute, kept in sync


def test_per_call_url_outranks_the_constructor_and_never_persists() -> None:
    """Per-call rung: ``query(url=)`` wins for ONE request; ``self.path`` is untouched.

    Driven through the real ``TestClient.request``: the recording transport
    is the wrapped Django client, so the URL it records is the one
    ``request()`` itself selected, not one the test re-derived. The overridden
    call posts to ``/percall/`` with the caller's headers forwarded, the
    ``Response`` wraps the very response the transport returned, the stored
    ``path`` is unchanged afterward (the non-persistence guarantee), and the
    next un-overridden call falls back to the constructor path.
    """
    transport = _RecordingDjangoClient()
    client = TestClient("/constructor/", client=transport)

    res = client.query("{ ok }", url="/percall/", headers={"X-Probe": "per-call"})
    assert [url for url, _ in transport.posts] == ["/percall/"]
    assert transport.posts[0][1]["headers"] == {"X-Probe": "per-call"}
    assert client.path == "/constructor/"
    assert isinstance(res, Response)
    assert res.data == {"ok": True}
    assert read_attr(res, "response") is transport.responses[0]

    client.query("{ ok }")
    assert [url for url, _ in transport.posts] == ["/percall/", "/constructor/"]


# ---------------------------------------------------------------------------
# The owned builder's uniform map rule.
# ---------------------------------------------------------------------------


def test_empty_files_dict_is_a_plain_json_post() -> None:
    """``files={}`` is falsy on every switch: JSON body, JSON content type, JSON decode.

    The three ``files`` gates (body build, content-type selection, decode mode)
    all use truthiness, so an empty dict cannot produce the mixed envelope of a
    multipart body posted as JSON.
    """
    transport = _RecordingDjangoClient()
    res = TestClient(client=transport).query("{ ok }", variables={"a": 1}, files={})

    url, kwargs = transport.posts[0]
    assert url == "/graphql/"
    assert kwargs["content_type"] == "application/json"
    assert kwargs["data"] == {"query": "{ ok }", "variables": {"a": 1}}  # no operations/map
    assert res.data == {"ok": True}


def test_build_body_map_rule_is_uniform_across_path_shapes() -> None:
    """The owned builder's one rule - ``map[key] = ["variables." + key]`` - for every shape.

    The nested input-object shape is earned live (``test_uploads_api.py``); no
    fakeshop mutation takes a TOP-LEVEL ``Upload`` variable or a list of them,
    so the top-level and list-index paths are pinned here against the builder
    directly, alongside ``operationName`` landing INSIDE the JSON-encoded
    ``operations`` field.
    """
    client = TestClient()
    f_top, f_nested, f_listed = object(), object(), object()

    body = client._build_body(
        "mutation Up($file: Upload!, $data: SpecInput!, $tags: [Upload!]!) { up }",
        {"file": None, "data": {"image": None}, "tags": [None, None]},
        {"file": f_top, "data.image": f_nested, "tags.0": f_listed},
        "Up",
    )

    assert isinstance(body["operations"], str)
    operations = json_loads(body["operations"])
    assert json_at(operations, "operationName") == "Up"
    assert json_at(operations, "variables") == {
        "file": None,
        "data": {"image": None},
        "tags": [None, None],
    }
    assert isinstance(body["map"], str)
    assert json.loads(body["map"]) == {
        "file": ["variables.file"],
        "data.image": ["variables.data.image"],
        "tags.0": ["variables.tags.0"],
    }
    # The file parts ride the body under their path keys, identity-preserved.
    assert body["file"] is f_top
    assert body["data.image"] is f_nested
    assert body["tags.0"] is f_listed


@pytest.mark.parametrize("wrap", [MappingProxyType, UserDict], ids=["mappingproxy", "userdict"])
def test_build_body_multipart_accepts_a_non_dict_variables_mapping(
    wrap: Callable[[dict[str, object]], Mapping[str, object]],
) -> None:
    """A non-``dict`` ``Mapping`` for ``variables=`` encodes like a ``dict``.

    ``query()`` annotates ``variables`` as ``Mapping[str, object]``, so a
    ``MappingProxyType`` or ``UserDict`` is a valid call: the builder copies it
    to a plain ``dict`` the JSON-encoded ``operations`` field carries, and the
    map rule holds.
    """
    upload = object()
    body = TestClient()._build_body(
        "mutation($file: Upload!) { up }",
        wrap({"file": None}),
        {"file": upload},
        None,
    )

    assert isinstance(body["operations"], str)
    assert json.loads(body["operations"])["variables"] == {"file": None}
    assert isinstance(body["map"], str)
    assert json.loads(body["map"]) == {"file": ["variables.file"]}
    assert body["file"] is upload


def test_build_body_sends_empty_operation_name_instead_of_dropping_it() -> None:
    """An explicit ``operation_name=""`` rides the body; the default ``None`` omits the key.

    The owned ``_build_body`` gates ``operationName`` on ``is not None``, not
    truthiness: a provided empty string is a malformed value sent for the server
    to reject with a real GraphQL error, not silently reinterpreted as "no
    operation name" (the module's fail-at-the-source posture). ``None`` (the
    default) omits the key entirely - never an ``operationName: null`` the server
    would reject as a validation error against a multi-operation document. No
    fakeshop live vehicle can pin the *absence* of the key, so it is pinned
    against the builder directly here.
    """
    client = TestClient()

    with_empty = client._build_body("{ x }", None, None, "")
    assert with_empty["operationName"] == ""

    absent = client._build_body("{ x }", None, None, None)
    assert "operationName" not in absent


# ---------------------------------------------------------------------------
# Surface guards - DB-free.
# ---------------------------------------------------------------------------


def test_clients_carry_the_pytest_collection_guard() -> None:
    """``__test__ is False`` on both ``Test*``-named classes.

    Without the guard, pytest collects the imported class as a suite and warns -
    a hard failure under the repo's ``-W error`` posture the moment any test
    module imports the client.
    """
    assert TestClient.__test__ is False
    assert AsyncTestClient.__test__ is False


@pytest.mark.parametrize("client_class", [TestClient, AsyncTestClient])
def test_clients_preserve_an_explicit_falsy_transport(
    client_class: type[TestClient] | type[AsyncTestClient],
) -> None:
    """An explicitly supplied client is selected by presence, not truthiness."""
    if client_class is TestClient:
        supplied = _FalsySyncClient()
        client = TestClient(client=supplied)
    else:
        supplied = _BoolFalsyAsyncTransport()
        client = AsyncTestClient(client=supplied)
    assert client.client is supplied


def test_async_client_defaults_to_djangos_async_transport() -> None:
    """With no transport supplied, the async twin builds an ``AsyncClient``, not a sync one.

    The default arm of the async selection: the awaited ``post`` the async
    ``query()`` relies on exists only on Django's async client, so a sync
    ``Client`` here would await a plain ``HttpResponse``.
    """
    client = AsyncTestClient()
    assert isinstance(client.client, AsyncClient)
    assert not isinstance(client.client, Client)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "transport_class",
    [_BoolFalsyAsyncTransport, _LenFalsyAsyncTransport],
    ids=["bool_falsy", "len_falsy"],
)
async def test_async_client_posts_a_real_query_through_a_falsy_transport(
    transport_class: type[_RecordingAsyncTransport],
) -> None:
    """A falsy async transport carries a real awaited operation, whichever way it is falsy.

    Presence, not truthiness, pinned behaviourally rather than by identity: the
    awaited request has to land on the supplied transport. A truthiness
    fallback would build a fresh ``AsyncClient`` and post the operation
    somewhere the test cannot observe, and falsiness has two spellings
    (``__bool__`` and an empty ``__len__``) that a presence check ignores alike.
    """
    transport = transport_class()
    client = AsyncTestClient("/async/", client=transport)

    res = await client.query("{ ok }")

    assert [url for url, _ in transport.posts] == ["/async/"]
    assert res.data == {"ok": True}
    assert read_attr(res, "response") is transport.responses[0]


@pytest.mark.parametrize(
    "name",
    [
        "TestClient",
        "AsyncTestClient",
        "Response",
        "GraphQLTestMixin",
        "GraphQLTestCase",
        "GraphQLTransactionTestCase",
    ],
    ids=str,
)
def test_export_surface_is_the_testing_root_not_the_package_root(name: str) -> None:
    """The six names live on ``testing``'s ``__all__``; the package root has none.

    The no-root-export contract is pinned by its two accurate shapes (spec-043
    Decision 4): ``getattr`` on the root raises ``AttributeError`` (the PEP 562
    ``__getattr__`` seam), and the ``from ... import`` STATEMENT form surfaces
    that as ``ImportError`` - Python's import machinery converts the module
    ``__getattr__``'s ``AttributeError`` for ``from ... import ...``.
    """
    assert name in testing_root.__all__
    assert getattr(testing_root, name) is not None

    assert not hasattr(django_strawberry_framework, name)
    with pytest.raises(AttributeError):
        getattr(django_strawberry_framework, name)
    with pytest.raises(ImportError):
        # The import statement is the probe; it raises, so the name is never bound.
        # basedpyright: the package root's PEP 562 __getattr__ returns Any; the statement
        # under test raises before it binds anything
        from django_strawberry_framework import TestClient as _  # noqa: F401, PLC0415 - the import is the probe  # pyright: ignore[reportAny]


# ---------------------------------------------------------------------------
# Mixin mechanics (the ``self.client`` delegation and endpoint rungs 3-5,
# proven against the recording client; the rungs are proven end-to-end live).
# ---------------------------------------------------------------------------


def test_mixin_query_delegates_to_the_test_cases_own_client() -> None:
    """The mixin's delegate ``TestClient`` posts through ``self.client``, JSON-typed.

    The state-free contract: the mixin reads only ``self.client`` and its own
    class attributes, so login/cookie state configured on the case's client
    applies to every ``self.query(...)`` call.
    """
    probe = _MixinProbe()
    res = probe.query("{ ok }")

    assert isinstance(probe.client, _RecordingDjangoClient)
    url, kwargs = probe.client.posts[0]
    assert url == "/graphql/"  # rung 5: the default, GRAPHQL_URL unset
    assert kwargs["content_type"] == "application/json"
    assert isinstance(res, Response)
    assert res.data == {"ok": True}


def test_mixin_class_attr_rung_beats_the_settings_key_and_the_default() -> None:
    """Rung 3 through the mixin: ``GRAPHQL_URL`` outranks the settings key and the default.

    One rung per node id, so a rung that stops working is distinguishable from
    its neighbours rather than hidden behind whichever assertion fires first.
    """
    alt = _AltProbe()
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/settings/"}):
        alt.query("{ ok }")
    assert isinstance(alt.client, _RecordingDjangoClient)
    assert alt.client.posts[-1][0] == "/classattr/"


def test_mixin_per_call_url_rung_beats_the_class_attr() -> None:
    """Rung 1 through the mixin: a per-call ``url=`` outranks ``GRAPHQL_URL``."""
    alt = _AltProbe()
    alt.query("{ ok }", url="/percall/")
    assert isinstance(alt.client, _RecordingDjangoClient)
    assert alt.client.posts[-1][0] == "/percall/"


def test_mixin_settings_rung_applies_when_the_class_attr_is_unset() -> None:
    """Rung 4 through the mixin: the settings key, read at call time.

    The mixin constructs its delegate per call, so a settings override observed
    mid-class applies (the read is at call time, not import time).
    """
    plain = _MixinProbe()
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT": "/settings/"}):
        plain.query("{ ok }")
    assert isinstance(plain.client, _RecordingDjangoClient)
    assert plain.client.posts[-1][0] == "/settings/"


# ---------------------------------------------------------------------------
# The assertion helpers' FAILURE directions, against canned Responses (their
# PASSING directions are earned live in test_query/test_client_api.py).
# ---------------------------------------------------------------------------


class AssertionHelperFailureDirectionTests(GraphQLTestMixin, unittest.TestCase):
    """Both assertion helpers FAIL in the right direction, carrying the decoded content.

    Canned Responses, no live request: the helpers are pure functions over a
    typed :class:`Response`, so their FAILURE directions are pinned against
    constructed responses here (spec-043 Decision 11 + the live-first split).
    Composed over ``unittest.TestCase`` (not the DB-backed
    ``GraphQLTestCase``) so this file stays DB-free. The ``client`` slot is declared for the
    mixin's host type and never read: the helpers under test touch no transport.
    """

    client: Client

    @staticmethod
    def _canned(
        *,
        errors: list[GraphQLFormattedError] | None,
        data: dict[str, object] | None,
        status_code: int = 200,
    ) -> Response[JsonResponse]:
        raw = JsonResponse({"data": data}, status=status_code)
        return Response(errors=errors, data=data, extensions=None, response=raw)

    def test_assert_response_no_errors_fails_on_an_errors_response(self) -> None:
        res = self._canned(errors=[{"message": "nope"}], data=None)
        with pytest.raises(AssertionError) as ctx:
            self.assertResponseNoErrors(res)
        assert "nope" in str(ctx.value)  # the decoded errors ride the message

    def test_assert_response_no_errors_fails_readably_on_a_non_200_without_errors(self) -> None:
        # A transport failure whose JSON body has no ``errors`` key: the status
        # check fails and the message still carries the decoded content (both
        # fields), never a bare ``None``.
        res = self._canned(errors=None, data={"detail": "boom"}, status_code=500)
        with pytest.raises(AssertionError) as ctx:
            self.assertResponseNoErrors(res)
        assert "boom" in str(ctx.value)

    def test_assert_response_no_errors_fails_with_custom_msg(self) -> None:
        res = self._canned(errors=[{"message": "nope"}], data=None)
        with pytest.raises(AssertionError) as ctx:
            self.assertResponseNoErrors(res, msg="custom no-errors failure")
        assert "custom no-errors failure" in str(ctx.value)

    def test_assert_response_has_errors_fails_on_a_clean_response(self) -> None:
        res = self._canned(errors=None, data={"__typename": "Query"})
        with pytest.raises(AssertionError):
            self.assertResponseHasErrors(res)

    def test_assert_response_has_errors_fails_with_custom_msg(self) -> None:
        res = self._canned(errors=None, data={"__typename": "Query"})
        with pytest.raises(AssertionError) as ctx:
            self.assertResponseHasErrors(res, msg="custom has-errors failure")
        assert "custom has-errors failure" in str(ctx.value)
