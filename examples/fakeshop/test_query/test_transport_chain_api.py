"""Live HTTP tests for configured middleware policies and GraphQL callback fallbacks."""

from __future__ import annotations

import contextlib
import json
from collections.abc import Awaitable, Callable, Coroutine, Generator
from typing import IO

import pytest
import strawberry
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseForbidden
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.test import AsyncClient, Client, RequestFactory, override_settings
from django.test.client import encode_multipart
from django.urls import URLPattern, path
from typing_extensions import override

from django_strawberry_framework import DjangoSchema
from django_strawberry_framework.testing import AsyncTestClient, TestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CAP = 1024
_BOUNDARY_ENTRY = (
    "django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware"
)
_STOCK_CSRF_ENTRY = "django.middleware.csrf.CsrfViewMiddleware"
_BOUNDARY = "GraphQLChainBoundary"
_POLICY_CALLS: list[str] = []
_UPLOAD_CALLS: list[str] = []


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


def _partial_sync(
    callback: Callable[[HttpRequest], HttpResponseBase],
) -> Callable[[HttpRequest], HttpResponseBase]:
    """Delegate to the actual bound callback while carrying only its CSRF exemption."""

    def wrapped(request: HttpRequest) -> HttpResponseBase:
        return callback(request)

    vars(wrapped)["csrf_exempt"] = vars(callback)["csrf_exempt"]
    return wrapped


def _partial_async(
    callback: Callable[[HttpRequest], Awaitable[HttpResponseBase]],
) -> Callable[[HttpRequest], Coroutine[object, object, HttpResponseBase]]:
    """Keep the async callback's real coroutine execution and deliberate partial marks."""

    async def wrapped(request: HttpRequest) -> HttpResponseBase:
        return await callback(request)

    vars(wrapped)["csrf_exempt"] = vars(callback)["csrf_exempt"]
    return wrapped


urlpatterns: list[URLPattern] = []


class ProjectPolicyMiddleware(CsrfViewMiddleware):
    """A configured project policy whose additional refusal precedes GraphQL execution."""

    @override
    def process_view(
        self,
        request: HttpRequest,
        callback: Callable[..., HttpResponseBase],
        callback_args: tuple[object, ...],
        callback_kwargs: dict[str, object],
    ) -> HttpResponseForbidden | None:
        if request.method in {
            "GET",
            "HEAD",
            "OPTIONS",
            "TRACE",
        } or getattr(
            callback,
            "csrf_exempt",
            False,
        ):
            return super().process_view(request, callback, callback_args, callback_kwargs)
        _POLICY_CALLS.append(request.path)
        return HttpResponseForbidden("project policy refused the operation")


class RecordingUploadHandler(MemoryFileUploadHandler):
    """Record Django's public multipart-parser handoff without taking over parsing."""

    @override
    def handle_raw_input(
        self,
        input_data: IO[bytes],
        META: dict[str, str],
        content_length: int,
        boundary: str,
        encoding: str | None = None,
    ) -> None:
        _UPLOAD_CALLS.append("parse")
        super().handle_raw_input(input_data, META, content_length, boundary, encoding)


def csrf_failure(_request: HttpRequest, reason: str = "") -> HttpResponseForbidden:
    """Give Django's real token-check refusal a stable project response."""
    del reason
    return HttpResponseForbidden("project token check refused the operation")


@contextlib.contextmanager
def _mounted(chain: list[str]) -> Generator[None, None, None]:
    previous_patterns = list(urlpatterns)
    schema = DjangoSchema(query=_Query)
    sync_callback = DjangoGraphQLView.as_view(
        schema=schema,
        max_request_body_bytes=_CAP,
        multipart_uploads_enabled=True,
    )
    async_callback = AsyncDjangoGraphQLView.as_view(
        schema=schema,
        max_request_body_bytes=_CAP,
        multipart_uploads_enabled=True,
    )
    urlpatterns[:] = [
        path("graphql-chain/sync-marked/", sync_callback),
        path("graphql-chain/async-marked/", async_callback),
        path("graphql-chain/sync-partial/", _partial_sync(sync_callback)),
        path("graphql-chain/async-partial/", _partial_async(async_callback)),
    ]
    _POLICY_CALLS.clear()
    _UPLOAD_CALLS.clear()
    try:
        with override_settings(
            ROOT_URLCONF=__name__,
            MIDDLEWARE=chain,
            CSRF_FAILURE_VIEW=f"{__name__}.csrf_failure",
            FILE_UPLOAD_HANDLERS=[f"{__name__}.RecordingUploadHandler"],
        ):
            yield
    finally:
        urlpatterns[:] = previous_patterns
        _POLICY_CALLS.clear()
        _UPLOAD_CALLS.clear()


def _path(*, is_async: bool, shape: str) -> str:
    color = "async" if is_async else "sync"
    return f"/graphql-chain/{color}-{shape}/"


async def _json_response(
    *,
    is_async: bool,
    shape: str = "marked",
    token: bool = False,
) -> HttpResponse:
    url = _path(is_async=is_async, shape=shape)
    client = (
        AsyncClient(enforce_csrf_checks=True) if is_async else Client(enforce_csrf_checks=True)
    )
    headers: dict[str, object] = {}
    if token:
        csrf_token = get_token(RequestFactory().get(url))
        client.cookies["csrftoken"] = csrf_token
        headers["X-CSRFToken"] = csrf_token
    if isinstance(client, AsyncClient):
        response = await AsyncTestClient(path=url, client=client).request(
            {"query": "{ ping }"},
            headers=headers,
        )
    else:
        response = TestClient(path=url, client=client).request(
            {"query": "{ ping }"},
            headers=headers,
        )
    assert isinstance(response, HttpResponse)
    return response


async def _multipart_response(*, is_async: bool, shape: str, oversized: bool) -> HttpResponse:
    url = _path(is_async=is_async, shape=shape)
    csrf_token = get_token(RequestFactory().get(url))
    client = (
        AsyncClient(enforce_csrf_checks=True) if is_async else Client(enforce_csrf_checks=True)
    )
    client.cookies["csrftoken"] = csrf_token
    body = encode_multipart(
        _BOUNDARY,
        {
            "operations": json.dumps({"query": "{ ping }"}),
            "map": "{}",
            "padding": "x" * (2 * _CAP if oversized else 1),
        },
    )
    assert (len(body) > _CAP) is oversized
    if isinstance(client, AsyncClient):
        # raw-envelope exemption: multipart framing, token headers and declared body size.
        response = await client.generic(
            "POST",
            url,
            data=body,
            content_type=f"multipart/form-data; boundary={_BOUNDARY}",
            headers={"X-CSRFToken": csrf_token},
        )
    else:
        # raw-envelope exemption: multipart framing, token headers and declared body size.
        response = client.generic(
            "POST",
            url,
            data=body,
            content_type=f"multipart/form-data; boundary={_BOUNDARY}",
            headers={"X-CSRFToken": csrf_token},
        )
    assert isinstance(response, HttpResponse)
    return response


def _assert_success(response: HttpResponse) -> None:
    assert response.status_code == 200
    assert json.loads(response.content) == {"data": {"ping": "pong"}}


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("policy", ["stock", "project"])
async def test_the_configured_policy_decides_a_recognized_callbacks_response(
    policy: str,
    *,
    is_async: bool,
) -> None:
    """A project's additional refusal runs on recognized callbacks on both transports."""
    entry = _STOCK_CSRF_ENTRY if policy == "stock" else f"{__name__}.ProjectPolicyMiddleware"
    with _mounted([_BOUNDARY_ENTRY, entry]):
        response = await _json_response(is_async=is_async, token=True)
        if policy == "stock":
            _assert_success(response)
            assert _POLICY_CALLS == []
        else:
            assert response.status_code == 403
            assert response.content == b"project policy refused the operation"
            assert [_path(is_async=is_async, shape="marked")] == _POLICY_CALLS


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    ("shape", "boundary_present"),
    [
        pytest.param("marked", False, id="marked-no-boundary"),
        pytest.param("partial", False, id="partial-no-boundary"),
        pytest.param("partial", True, id="partial-with-boundary"),
    ],
)
@pytest.mark.parametrize("oversized", [False, True], ids=["within-cap", "over-cap"])
async def test_fallback_callbacks_keep_the_cap_ahead_of_multipart_parsing(
    shape: str,
    *,
    boundary_present: bool,
    oversized: bool,
    is_async: bool,
) -> None:
    """Fallback mounts keep parsing behind the cap while skipping the configured extra policy."""
    chain = [_BOUNDARY_ENTRY] if boundary_present else []
    chain.append(f"{__name__}.ProjectPolicyMiddleware")
    with _mounted(chain):
        response = await _multipart_response(is_async=is_async, shape=shape, oversized=oversized)
        assert _POLICY_CALLS == []
        if oversized:
            assert response.status_code == 413
            assert (
                response.content
                == b"Request body exceeded the configured GraphQL request-body limit."
            )
            assert response.headers["Content-Type"].startswith("text/plain")
            assert _UPLOAD_CALLS == []
        else:
            _assert_success(response)
            assert _UPLOAD_CALLS == ["parse"]


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("token", [False, True], ids=["missing-token", "valid-token"])
async def test_a_partial_callback_still_checks_the_requests_token(
    *,
    is_async: bool,
    token: bool,
) -> None:
    """An unrecognized wrapper keeps the full token check in the view's continuation."""
    with _mounted([_BOUNDARY_ENTRY, _STOCK_CSRF_ENTRY]):
        response = await _json_response(is_async=is_async, shape="partial", token=token)
        if token:
            _assert_success(response)
        else:
            assert response.status_code == 403
            assert response.content == b"project token check refused the operation"


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("token", [False, True], ids=["missing-token", "valid-token"])
async def test_a_recognized_callback_checks_tokens_without_global_csrf_middleware(
    *,
    is_async: bool,
    token: bool,
) -> None:
    """A chain that measures the body without a CSRF entry still gets the view's token check."""
    with _mounted([_BOUNDARY_ENTRY]):
        response = await _json_response(is_async=is_async, token=token)
        if token:
            _assert_success(response)
        else:
            assert response.status_code == 403
            assert response.content == b"project token check refused the operation"
