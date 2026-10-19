"""The prepared-view handoff's ignore arms.

``django_strawberry_framework/_boundary_ordering.py::consume_prepared_view``
honors only a well-formed pair stamped for the consuming mount. A malformed
stamp and a stamp carrying another mount's token both fall back to fresh
dispatch, and the stamp is left in place: only a consumed pair is deleted.
Package tier: the middleware stamps well-formed pairs only, so a malformed
or foreign stamp is unreachable from a real query and is forged directly,
the way the matching-pair oracle forges its own.
"""

from __future__ import annotations

import strawberry
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from typing_extensions import override

from django_strawberry_framework._boundary_ordering import (
    _BOUNDARY_MOUNT,
    _BOUNDARY_PREPARED_VIEW,
)
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.views import DjangoGraphQLView


@strawberry.type
class _PingQuery:
    ping: str = "pong"


_SCHEMA = strawberry.Schema(query=_PingQuery)


class _RecordingSyncView(DjangoGraphQLView):
    marker: str = "fresh"

    @override
    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        return HttpResponse(self.marker)


def test_as_view_dispatches_fresh_on_a_malformed_prepared_view_stamp() -> None:
    """A stamp that is not a 2-tuple is ignored, not consumed.

    The wrapper must not index into a pair of the wrong shape, and it
    must not delete a stamp it did not honor: the request dispatches a
    fresh instance and the stamp stays where it was.
    """
    callback = _RecordingSyncView.as_view(schema=_SCHEMA)
    request = RequestFactory().get("/graphql/")
    mount = read_attr(callback, _BOUNDARY_MOUNT)
    setattr(request, _BOUNDARY_PREPARED_VIEW, (mount,))

    response = callback(request)

    assert isinstance(response, HttpResponse)
    assert response.content == b"fresh"
    assert getattr(request, _BOUNDARY_PREPARED_VIEW, None) == (mount,)


def test_as_view_dispatches_fresh_on_a_foreign_mount_stamp() -> None:
    """A well-formed stamp for another mount is ignored, not consumed.

    The token is what binds a stamp to its mount: a pair carrying a
    token this callback never minted dispatches a fresh instance and
    the stamp stays where it was.
    """
    callback = _RecordingSyncView.as_view(schema=_SCHEMA)
    request = RequestFactory().get("/graphql/")
    prepared = _RecordingSyncView(schema=_SCHEMA)
    prepared.marker = "prepared"
    prepared.setup(request)
    foreign = object()
    setattr(request, _BOUNDARY_PREPARED_VIEW, (foreign, prepared))

    response = callback(request)

    assert isinstance(response, HttpResponse)
    assert response.content == b"fresh"
    assert getattr(request, _BOUNDARY_PREPARED_VIEW, None) == (foreign, prepared)
