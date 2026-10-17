"""Shared live-``/graphql/`` HTTP helpers for the fakeshop acceptance suites.

Single-sites the live-tier request contracts: JSON GraphQL posts, raw-body posts,
status-code assertions, parsed payload extraction, GraphQL-error rejection, and
exact-data assertions. Superset signatures keep simple callers terse while
letting variable-driven and custom-client tests use the same envelope.

The JSON path routes through the package's own
:class:`django_strawberry_framework.testing.TestClient` (spec-043), so
every live suite's ordinary GraphQL post shares the one body-builder / decode
path instead of re-spelling the ``json.dumps`` + content-type + envelope-split
boilerplate. The functions return the raw ``HttpResponse`` (the client stashes
it on ``Response.response``), so call sites read ``.status_code`` /
``.json()`` directly. ``post_graphql_raw`` deliberately stays a
raw ``client.post`` - its subject is the raw request envelope (malformed bodies,
content-type negotiation), which ``TestClient`` exists to abstract away.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypeAlias, cast

from django.test import Client

from django_strawberry_framework.testing import TestClient

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

#: A parsed GraphQL JSON object (response envelope, ``data``, or variables).
# basedpyright: live suites chain subscripts into a parsed response (``data["a"]["b"][0]``);
# a recursive JSON alias would turn every hop of every chain into a narrowing site
JSONObject: TypeAlias = dict[str, Any]  # pyright: ignore[reportExplicitAny]
#: A JSON value a test writes as an expected literal (what a response decodes to). The
#: container arms are the read-only ``Sequence`` / ``Mapping`` so an expected value a test
#: builds first (``list[dict[str, str]]``) still matches: ``list`` / ``dict`` are invariant.
JSONValue: TypeAlias = (
    "str | int | float | bool | Sequence[JSONValue] | Mapping[str, JSONValue] | None"
)
#: ``json.loads`` typed as the ``object`` a decode returns; ``_json_object`` narrows it.
_loads: Callable[[bytes], object] = json.loads


def _json_object(value: object) -> JSONObject:
    """Return a decoded JSON value as a ``JSONObject``, failing the test when it is not one."""
    assert isinstance(value, dict), value
    # A decoded JSON object has string keys; its values stay the open ``JSONObject`` chain
    # the live suites subscript, which no check short of a full schema walk can type.
    return cast("JSONObject", value)


def _response_json(response: _MonkeyPatchedWSGIResponse) -> JSONObject:
    """Decode a live ``/graphql/`` response body as a JSON object."""
    return _json_object(_loads(response.content))


def post_graphql(
    query: str,
    *,
    client: Client | None = None,
    variables: Mapping[str, object] | None = None,
    url: str | None = None,
) -> _MonkeyPatchedWSGIResponse:
    """POST one GraphQL document through the shared package ``TestClient``.

    Routes through the package client's body-build + decode path;
    ``assert_no_errors`` is off here so error-expecting callers still read
    ``response.json()["errors"]`` (the shared assertion helpers below own the
    error policy). Returns the raw ``HttpResponse`` ``TestClient`` kept on
    ``Response.response``. The configured endpoint is used unless ``url`` supplies
    a one-call test mount.
    """
    result = TestClient(client=client).query(
        query,
        variables=variables,
        assert_no_errors=False,
        url=url,
    )
    # basedpyright: the package's public ``testing.Response.response`` is typed ``Any`` (it
    # carries whichever ``HttpResponse`` subclass the Django client returned)
    return result.response  # pyright: ignore[reportAny]


def post_graphql_raw(
    body: str | bytes,
    *,
    client: Client | None = None,
) -> _MonkeyPatchedWSGIResponse:
    """POST a raw JSON body to the live ``/graphql/`` endpoint.

    Deliberately a raw ``client.post`` (not ``TestClient``): the subject is the
    wire envelope itself - a hand-built or malformed body - which the client's
    body-builder would otherwise replace. This is the documented raw-envelope
    exemption (spec-043).
    """
    graphql_client = client or Client()
    return graphql_client.post(
        "/graphql/",
        data=body,
        content_type="application/json",
    )


def graphql_payload(
    query: str,
    *,
    client: Client | None = None,
    variables: Mapping[str, object] | None = None,
    url: str | None = None,
) -> JSONObject:
    """POST ``query`` to the configured or one-call ``url`` and return parsed JSON."""
    response = post_graphql(query, client=client, variables=variables, url=url)
    assert response.status_code == 200
    return _response_json(response)


def assert_graphql_success(
    query: str,
    *,
    client: Client | None = None,
    variables: Mapping[str, object] | None = None,
    url: str | None = None,
) -> JSONObject:
    """POST ``query``, assert HTTP 200 and no GraphQL errors, then return ``data``."""
    payload = graphql_payload(query, client=client, variables=variables, url=url)
    assert "errors" not in payload, payload
    return _json_object(payload.get("data"))


def assert_graphql_data(
    query: str,
    expected: Mapping[str, JSONValue],
    *,
    client: Client | None = None,
    variables: Mapping[str, object] | None = None,
    url: str | None = None,
) -> _MonkeyPatchedWSGIResponse:
    """POST ``query`` and assert a 200, no ``errors``, and exact ``data`` equality.

    Returns the response so callers can layer extra asserts (headers, query
    capture) on top of the shared preamble.
    """
    response = post_graphql(query, client=client, variables=variables, url=url)
    assert response.status_code == 200
    payload = _response_json(response)
    assert "errors" not in payload, payload
    assert payload.get("data") == expected
    return response
