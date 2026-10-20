"""Shared live-``/graphql/`` HTTP helpers for the fakeshop acceptance suites.

Single-sites the live-tier request contracts: JSON GraphQL posts, raw-body posts,
status-code assertions, parsed payload extraction, GraphQL-error rejection,
exact-data assertions, and the verb-and-table reading of captured SQL. Superset
signatures keep simple callers terse while letting variable-driven and custom-client
tests use the same envelope.

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
from typing import TYPE_CHECKING, Protocol, TypeAlias

from django.conf import settings
from django.test import Client
from typing_extensions import TypeIs

from django_strawberry_framework import DjangoMutation
from django_strawberry_framework.testing import TestClient

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedASGIResponse, _MonkeyPatchedWSGIResponse

#: A parsed GraphQL JSON object (response envelope, ``data``, or variables). Its members are
#: ``object``: read a nested member through :func:`json_at` / :func:`json_object` /
#: :func:`json_list`, which check each step's container kind.
JSONObject: TypeAlias = dict[str, object]
#: A JSON value a test writes as an expected literal (what a response decodes to). The
#: container arms are the read-only ``Sequence`` / ``Mapping`` so an expected value a test
#: builds first (``list[dict[str, str]]``) still matches: ``list`` / ``dict`` are invariant.
JSONValue: TypeAlias = (
    "str | int | float | bool | Sequence[JSONValue] | Mapping[str, JSONValue] | None"
)
#: ``json.loads`` typed as the ``object`` a decode returns; :func:`json_object` narrows it.
json_loads: Callable[[str | bytes], object] = json.loads


def _is_object_dict(value: object) -> TypeIs[dict[object, object]]:
    """Whether ``value`` is a ``dict``, its items typed ``object``."""
    return isinstance(value, dict)


def is_json_object(value: object) -> TypeIs[JSONObject]:
    """Whether ``value`` is a ``dict`` whose keys are all strings, as a decoded JSON object's are."""
    return _is_object_dict(value) and all(isinstance(key, str) for key in value)


def is_json_list(value: object) -> TypeIs[list[object]]:
    """Whether ``value`` is a ``list``, its items typed ``object``."""
    return isinstance(value, list)


def json_at(value: object, *path: str | int) -> object:
    """Return ``value[path[0]][path[1]]...``, failing the test when a step meets the wrong kind.

    A ``str`` step reads a JSON object member, an ``int`` step a JSON array item.
    """
    for key in path:
        if isinstance(key, str):
            assert is_json_object(value), (
                f"expected a JSON object to read {key!r} from, got {value!r}"
            )
            value = value[key]
        else:
            assert is_json_list(value), (
                f"expected a JSON array to read [{key}] from, got {value!r}"
            )
            value = value[key]
    return value


def json_object(value: object, *path: str | int) -> JSONObject:
    """Return the JSON object ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert is_json_object(found), f"expected a JSON object at {path!r}, got {found!r}"
    return found


def json_list(value: object, *path: str | int) -> list[object]:
    """Return the JSON array ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert is_json_list(found), f"expected a JSON array at {path!r}, got {found!r}"
    return found


def json_str(value: object, *path: str | int) -> str:
    """Return the JSON string ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert isinstance(found, str), f"expected a JSON string at {path!r}, got {found!r}"
    return found


def json_optional_str(value: object, *path: str | int) -> str | None:
    """Return the JSON string or ``null`` ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert found is None or isinstance(found, str), (
        f"expected a JSON string or null at {path!r}, got {found!r}"
    )
    return found


def json_int(value: object, *path: str | int) -> int:
    """Return the JSON integer ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert isinstance(found, int), f"expected a JSON integer at {path!r}, got {found!r}"
    assert not isinstance(found, bool), f"expected a JSON integer at {path!r}, got {found!r}"
    return found


def json_bool(value: object, *path: str | int) -> bool:
    """Return the JSON boolean ``json_at(value, *path)`` reaches, failing on any other kind."""
    found = json_at(value, *path)
    assert isinstance(found, bool), f"expected a JSON boolean at {path!r}, got {found!r}"
    return found


def saved_pk(pk: int | None) -> int:
    """Return a saved row's integer primary key (``Model.pk`` is ``None`` only before the first save)."""
    assert pk is not None, "expected a saved row"
    return pk


class DeleteAfterAuthorization(Protocol):
    """Arm a mutation class to delete its located row once authorization has run.

    The ``test_query/conftest.py::delete_after_authorization`` fixture's type: ``delete`` runs
    inside the armed class's ``check_permission``, after the mutation's own authorization.
    """

    def __call__(self, mutation: type[DjangoMutation], delete: Callable[[], object], /) -> None:
        """Wrap ``mutation.check_permission`` to run ``delete`` once it authorized."""
        ...


def statement_shapes(sqls: Sequence[str]) -> list[str]:
    """Return each statement's verb, with the table an ``INSERT`` / ``UPDATE`` writes.

    ``INSERT INTO "t" ...`` reads ``INSERT "t"`` and ``UPDATE "t" ...`` reads ``UPDATE "t"``;
    every other statement reads as its first word (``SELECT``, ``SAVEPOINT``, ``RELEASE``,
    ``ROLLBACK``, ``DELETE``), so a row pins which tables a write touched and in what order.
    """
    shapes: list[str] = []
    for sql in sqls:
        words = sql.split()
        if words[0] == "INSERT":
            shapes.append(f"INSERT {words[2]}")
        elif words[0] == "UPDATE":
            shapes.append(f"UPDATE {words[1]}")
        else:
            shapes.append(words[0])
    return shapes


def statement_shapes_after_last_delete(sqls: Sequence[str]) -> list[str]:
    """Return the ``statement_shapes`` of the statements after the last ``DELETE``.

    The statements a write ran after a stand-in concurrent delete
    (``test_query/conftest.py::delete_after_authorization``) of its located row.
    """
    last_delete = max(index for index, sql in enumerate(sqls) if sql.startswith("DELETE"))
    return statement_shapes(sqls[last_delete + 1 :])


#: ``getattr`` typed ``-> object``: reads a setting (django-stubs types every ``LazySettings``
#: attribute ``Any``), ``User.pk`` or a module attribute as a value the caller then checks.
read_attr: Callable[[object, str], object] = getattr


def middleware() -> list[str]:
    """Return the configured ``settings.MIDDLEWARE``, checked to be a list of dotted paths."""
    configured = read_attr(settings, "MIDDLEWARE")
    assert is_json_list(configured), configured
    entries = [entry for entry in configured if isinstance(entry, str)]
    assert len(entries) == len(configured), configured
    return entries


def middleware_without_debug_toolbar() -> list[str]:
    """Return ``settings.MIDDLEWARE`` minus its debug-toolbar entries."""
    return [entry for entry in middleware() if "debug_toolbar" not in entry]


def response_json(response: _MonkeyPatchedWSGIResponse | _MonkeyPatchedASGIResponse) -> JSONObject:
    """Decode a live ``/graphql/`` response body as a JSON object."""
    return json_object(json_loads(response.content))


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
    return result.response


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
    return response_json(response)


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
    return json_object(payload, "data")


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
    payload = response_json(response)
    assert "errors" not in payload, payload
    assert payload.get("data") == expected
    return response
