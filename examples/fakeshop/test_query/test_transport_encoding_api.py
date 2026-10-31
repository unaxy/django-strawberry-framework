"""Live HTTP tests for declared multipart codecs and middleware-assigned form encodings."""

from __future__ import annotations

import contextlib
import json
from collections.abc import Callable, Generator

import pytest
import strawberry
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.test import AsyncClient, Client, override_settings
from django.test.client import encode_multipart
from django.urls import URLPattern, path

from django_strawberry_framework import DjangoSchema
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_UNCHANGED = object()
_ENCODING: dict[str, object] = {"effective": _UNCHANGED}
_ENCODING_ATTRIBUTE = "encoding"
_BOUNDARY = "GraphQLCodecBoundary"
_VALUE = "caf\u00e9_\u00fcber"
_BOUNDARY_ENTRY = (
    "django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware"
)


@strawberry.type
class _Query:
    @strawberry.field
    def echo(self, value: str) -> str:
        return value


urlpatterns: list[URLPattern] = []


class EncodingMiddleware:
    """Apply a consumer's public per-request encoding override before the view boundary."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]) -> None:
        """Bind the following middleware without inspecting or coercing the encoding."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        if _ENCODING["effective"] is not _UNCHANGED:
            setattr(request, _ENCODING_ATTRIBUTE, _ENCODING["effective"])
        return self.get_response(request)


@contextlib.contextmanager
def _mounted(effective: object = _UNCHANGED) -> Generator[None, None, None]:
    previous_patterns = list(urlpatterns)
    previous_encoding = _ENCODING["effective"]
    schema = DjangoSchema(query=_Query)
    urlpatterns[:] = [
        path(
            "graphql-codec/sync/",
            DjangoGraphQLView.as_view(schema=schema, multipart_uploads_enabled=True),
        ),
        path(
            "graphql-codec/async/",
            AsyncDjangoGraphQLView.as_view(schema=schema, multipart_uploads_enabled=True),
        ),
    ]
    _ENCODING["effective"] = effective
    try:
        with override_settings(
            ROOT_URLCONF=__name__,
            MIDDLEWARE=[f"{__name__}.EncodingMiddleware", _BOUNDARY_ENTRY],
            DEFAULT_CHARSET="utf-8",
        ):
            yield
    finally:
        _ENCODING["effective"] = previous_encoding
        urlpatterns[:] = previous_patterns


async def _multipart_response(*, is_async: bool, declared: str | None) -> HttpResponse:
    operations = json.dumps(
        {
            "query": "query Echo($value: String!) { echo(value: $value) }",
            "variables": {"value": _VALUE},
        },
        ensure_ascii=False,
    )
    body = encode_multipart(_BOUNDARY, {"operations": operations, "map": "{}"})
    content_type = f"multipart/form-data; boundary={_BOUNDARY}"
    if declared is not None:
        content_type += f"; charset={declared}"
    url = "/graphql-codec/async/" if is_async else "/graphql-codec/sync/"
    if is_async:
        # raw-envelope exemption: the multipart bytes and declared codec are the subject.
        response = await AsyncClient().generic(
            "POST",
            url,
            data=body,
            content_type=content_type,
        )
    else:
        # raw-envelope exemption: the multipart bytes and declared codec are the subject.
        response = Client().generic("POST", url, data=body, content_type=content_type)
    assert isinstance(response, HttpResponse)
    return response


def _assert_response(response: HttpResponse, *, accepted: bool) -> None:
    if accepted:
        assert response.status_code == 200
        assert json.loads(response.content) == {"data": {"echo": _VALUE}}
    else:
        assert response.status_code == 400
        assert response.content == b"Unable to parse request body as JSON"
        assert response.headers["Content-Type"].startswith("text/plain")


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    ("declared", "accepted"),
    [
        pytest.param("utf-8", True, id="utf-8"),
        pytest.param("UTF-8", True, id="uppercase"),
        pytest.param("utf8", True, id="unhyphenated"),
        pytest.param("u8", True, id="obscure-alias"),
        pytest.param("utf-8-sig", False, id="different-bom-codec"),
    ],
)
async def test_declared_utf8_aliases_preserve_the_multibyte_operation(
    declared: str,
    *,
    accepted: bool,
    is_async: bool,
) -> None:
    """Python's UTF-8 aliases execute unchanged while the distinct BOM codec is refused."""
    with _mounted():
        response = await _multipart_response(is_async=is_async, declared=declared)
        _assert_response(response, accepted=accepted)


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "effective",
    [
        pytest.param(b"utf-8", id="bytes"),
        pytest.param(42, id="integer"),
        pytest.param(object(), id="object"),
        pytest.param("utf-8\x00", id="embedded-nul"),
        pytest.param("\ud800", id="lone-surrogate"),
    ],
)
async def test_an_unusable_middleware_encoding_gets_the_controlled_form_refusal(
    effective: object,
    *,
    is_async: bool,
) -> None:
    """A public request-encoding assignment cannot replace the form refusal with a server error."""
    with _mounted(effective):
        response = await _multipart_response(is_async=is_async, declared="utf-8")
        _assert_response(response, accepted=False)


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    ("declared", "effective", "accepted"),
    [
        pytest.param("iso-8859-1", "utf-8", False, id="declared-latin1-effective-utf8"),
        pytest.param("no-such-codec", "utf-8", False, id="unknown-declaration-effective-utf8"),
        pytest.param(None, "iso-8859-1", False, id="undeclared-effective-latin1"),
        pytest.param(None, "utf-8", True, id="undeclared-effective-utf8"),
        pytest.param("utf-8", "utf-8", True, id="declared-and-effective-utf8"),
    ],
)
async def test_the_declaration_and_the_actual_form_decoder_must_each_be_utf8(
    declared: str | None,
    effective: str,
    *,
    accepted: bool,
    is_async: bool,
) -> None:
    """Neither a client declaration nor a middleware override can mask the other's codec."""
    with _mounted(effective):
        response = await _multipart_response(is_async=is_async, declared=declared)
        _assert_response(response, accepted=accepted)
