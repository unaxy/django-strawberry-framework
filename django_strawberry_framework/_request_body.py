"""The one place the package touches Django's private request-body internals.

``views.py``'s cumulative body cap (spec-046 Decision 7) needs an answer to
exactly one question - "is this request body larger than ``limit`` bytes?" - and
it must obtain that answer *without* first materializing the body it may be
about to refuse. :func:`body_exceeds_limit` is that answer, and this module is
the only file in the package that names ``HttpRequest._stream``,
``HttpRequest._body``, or ``HttpRequest._read_started``. Centralizing them here
rather than spreading them across the two view classes is what makes the
compatibility surface with Django's request object auditable from one file and
pinnable to one documented contract.

Why the public API cannot do this
---------------------------------

``HttpRequest.body`` is the public way to obtain a request body, and it is
structurally unusable for a *cap*: it performs an unbounded ``self.read()`` that
copies the whole request into one ``bytes`` value and only then returns it, so
``len(request.body) > limit`` detects an over-limit body strictly *after* the
attacker-sized allocation the limit exists to prevent. On ASGI that allocation
also re-reads a ``SpooledTemporaryFile`` which
``django.core.handlers.asgi.ASGIHandler.read_body`` may already have rolled to
disk past ``FILE_UPLOAD_MAX_MEMORY_SIZE`` - synchronously, on the event loop, for
the async view.

Django's own ``HttpRequest.body`` narrows that window, unevenly across the
supported range: every release compares ``CONTENT_LENGTH`` against
``DATA_UPLOAD_MAX_MEMORY_SIZE`` before reading; the 5.2.x series from the
``Django>=`` floor and the 6.x series from 6.0.4 also seek a *seekable* stream to
its end to check the real buffered size, but 6.0.0 through 6.0.3 do not; and only
the 5.2.x series reads at most one byte past that limit from a stream it could not
size. Every one of those checks is against Django's setting, not the package's
cap, and ``DATA_UPLOAD_MAX_MEMORY_SIZE = None`` turns all of them off, leaving the
read unbounded. The package cap therefore has to measure the body itself on every
supported release, and measuring it means reaching for the stream Django keeps
private.

The Django contract this module pins
------------------------------------

Read out of ``django/http/request.py`` (and the two handler modules) at both
ends of the supported range - the ``Django>=`` floor pinned in ``pyproject.toml``
and the newest release ``uv.lock`` resolves - not from memory. The three
attributes behave identically across them; only ``body``'s own size checks
differ, and none of those checks reads the package's cap.

- ``_body`` is set as an *instance* attribute, once, by ``HttpRequest.body``
  after it has read the stream. Neither release declares a class-level default,
  so ``hasattr(request, "_body")`` is an exact test for "the body has already
  been materialized" - the same test ``HttpRequest.body`` and
  ``_load_post_and_files`` themselves perform.
- ``_read_started`` is initialized to ``False`` by ``WSGIRequest.__init__`` and
  ``ASGIRequest.__init__`` - **not** by ``HttpRequest.__init__``, so a bare
  ``HttpRequest`` has no such attribute - and set to ``True`` by
  ``HttpRequest.read`` / ``readline``. ``HttpRequest.body`` raises
  ``RawPostDataException`` when it is true and ``_body`` is absent.
- ``_stream`` is the byte source. ``ASGIRequest`` assigns the
  ``SpooledTemporaryFile`` that ``read_body`` filled; ``WSGIRequest`` assigns a
  ``LimitedStream`` that truncates reads at ``CONTENT_LENGTH``;
  ``django.test.AsyncRequestFactory`` also assigns a ``LimitedStream``. After
  materializing, ``HttpRequest.body`` closes the old stream and replaces it with
  ``BytesIO(self._body)``, so substituting a rewound ``BytesIO`` for a consumed
  stream is a shape Django both produces and accepts.

Note which attribute this module never writes: ``_body``. Filling Django's cache
would make ``HttpRequest.body`` short-circuit past its own
``DATA_UPLOAD_MAX_MEMORY_SIZE`` check, so the bounded branch hands its bytes back
as a *stream* instead and leaves the property fully in charge (see
:func:`_measured_by_bounded_read`). The package's job is to add a ceiling, never
to remove Django's.

Seekability, measured rather than assumed
-----------------------------------------

- ``LimitedStream`` subclasses ``io.IOBase``, so it *declares* ``seekable()`` and
  returns ``False``. WSGI and the async test client therefore take the
  bounded-read branch.
- ``tempfile.SpooledTemporaryFile`` is seekable in fact on every supported
  Python, but only *declares* it from 3.11, where it became an ``io.IOBase``
  subclass. On the **Python 3.10 floor the attribute is absent entirely**
  (verified: ``hasattr(spool, "seekable")`` is ``False`` at 3.10.19 and ``True``
  at 3.14.2), while ``tell()`` / ``seek()`` work and return positions on both.
  That is why :func:`_measured_remaining` believes ``seekable()`` when the method
  exists and otherwise defers to ``tell()``: anything narrower would silently drop
  the ASGI spool onto the read branch at the exact floor the boundary protects.

What this module deliberately does not do
-----------------------------------------

It never raises ``HTTPException`` and never looks at settings: the cap's policy -
which limit applies, and what the ``413`` says - stays in
``views.py::_RequestBodyBoundaryMixin``. It also never touches a multipart
request; ``views.py`` returns before calling here, because reading a multipart
body would defeat Django's streaming upload handlers: a multipart body is bounded
by its declared length and Django's own parser (spec-046 Decision 7).

A request stream that fails mid-read is a broken or aborted client, so the
bounded read (:func:`_bounded_read_exceeds_limit`) reports it as this module's
fail-closed ``True`` rather than letting the ``OSError`` from the socket (which
Django's own ``HttpRequest.read`` re-raises as ``UnreadablePostError``) escape the
boundary and become a ``500`` and an error log for a request the package simply
could not measure. That refusal is the one this module records, as a ``WARNING``
(:data:`_UNREADABLE_STREAM_LOG_MESSAGE`): its *reason* is deliberately invisible
to the client and therefore invisible to an operator too, and the record changes
nothing on the wire.
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import TYPE_CHECKING

from . import logger
from .utils._narrowing import call_method, read_attr

if TYPE_CHECKING:
    from django.http import HttpRequest


__all__ = ("body_exceeds_limit",)


#: Ceiling on one bounded ``read()`` call. The bounded branch never reads more
#: than ``limit + 1`` bytes in total, so this only caps the size of a single
#: allocation on the way there: a mount configured with a very large limit must
#: not turn one hostile request into one very large ``read()``.
_READ_CHUNK_BYTES = 64 * 1024

#: The server-side record of a bounded read that could not complete. It is a
#: ``WARNING`` - a broken client stream is a condition a deployment should be able
#: to see, not this process's error - and carries ``exc_info``, because the
#: traceback is the actionable part: it names whether the request stream died, the
#: consumed stream refused to close, or the replacement could not be installed.
#: ``logger.exception`` would say the same thing at ``ERROR``, which would classify
#: an aborted upload as a package failure.
_UNREADABLE_STREAM_LOG_MESSAGE = (
    "The GraphQL request-body size probe could not read this request's stream (%s) to "
    "measure it, so the body is reported as over-limit (fail closed) rather than passed on "
    "unmeasured or allowed to escape as a server error. The client sees the endpoint's "
    "ordinary body-limit rejection, which says nothing about this condition by design - so a "
    "burst of these for requests that are NOT oversized is a broken or aborted client stream, "
    "or a stream installed by the ASGI server or by a middleware that cannot be read, not the "
    "configured limit."
)


def body_exceeds_limit(request: HttpRequest, limit: int) -> bool:
    """Whether ``request``'s body is longer than ``limit`` bytes.

    Answers in the cheapest way the request's actual state allows, in
    descending order of preference:

    1. **Already materialized** (``_body`` present, e.g. a urlencoded body some
       consumer middleware read on the way in). The allocation happened before
       the view ran and cannot be undone, so the length is simply measured - the
       caller must still refuse an over-limit body rather than process it.
       Django's own ``CsrfViewMiddleware``, which reads ``request.POST`` for every
       cookie-bearing POST, does not reach this rung, because ``views.py``
       re-enters CSRF from *inside* the view, after this measurement (spec-046
       Decision 18). What remains reachable is a
       consumer's own inbound body read, which no application-level ordering can
       precede.
    2. **Measurable without reading** (a seekable stream, which is what ASGI's
       spooled body file is). The size is probed with ``seek`` / ``tell``, the
       original position is restored, and nothing is read or copied. This is the
       branch that makes an over-limit ASGI request cost no allocation at all.
    3. **Neither** (a genuinely non-seekable stream: WSGI's ``LimitedStream``,
       the async test client, a custom stream - or a seekable one whose probe
       came out at zero or less, which is a measurement failure rather than an
       empty body, see :func:`_measured_remaining`). The body is read in bounded
       chunks up to ``limit + 1`` bytes - one byte more than the largest legal
       body, which is the least information that can distinguish "at the limit"
       from "over it" - and no further. An allowed body is handed back as a
       rewound stream, so ``HttpRequest.body`` still runs normally over the
       original bytes and Django's own ceiling still applies. A read that cannot
       complete answers ``True`` without a measurement (see
       :func:`_bounded_read_exceeds_limit`).

    Returns ``False`` without measuring anything in two states the package
    cannot bound and must not pretend to: no ``_stream`` at all (a synthetic
    ``HttpRequest``), and a stream some earlier component already read from
    without caching ``_body``. In the second state ``HttpRequest.body`` itself
    raises ``RawPostDataException``, so the request cannot be processed by
    anything downstream either; measuring is impossible and translating another
    component's error into a misleading ``413`` would be worse than deferring.
    """
    if hasattr(request, "_body"):
        return len(request._body) > limit
    stream = read_attr(request, "_stream", None)
    if stream is None or getattr(request, "_read_started", False):
        return False
    remaining = _measured_remaining(stream)
    if remaining is None:
        return _bounded_read_exceeds_limit(request, stream, limit)
    return remaining > limit


def _measured_remaining(stream: object) -> int | None:
    """Return the unread byte count of ``stream``, or ``None`` to measure it by reading.

    A stream that declares ``seekable()`` false is believed without being poked.
    One with no ``seekable`` method at all - the Python 3.10
    ``SpooledTemporaryFile``, the ASGI body file at the supported floor - is asked
    for its position instead, and a ``tell()`` raising ``io.UnsupportedOperation``
    (a pipe-backed stream) sends it to the bounded read. Otherwise the stream is
    sought to its end and back to where it started, and nothing is read.

    A probed count of zero or less is a measurement FAILURE, never "the body is
    empty": :func:`body_exceeds_limit` would read it as "within the limit" and the
    request would go straight to ``HttpRequest.body`` with **no package bound at
    all**, whose only ceiling on Django 6.0.0 through 6.0.3 is the
    ``CONTENT_LENGTH`` this cap exists precisely not to trust. A
    ``seek(0, SEEK_END)`` that under-reports (a stream that can report a position
    but not take one) produces it, so ``None`` is returned and the bounded read
    supplies the bound; a genuinely empty body still ends up allowed, by one
    ``read`` call. A position or end that is not an ``int`` is ``None`` the same
    way.
    """
    if hasattr(stream, "seekable") and not call_method(stream, "seekable"):
        return None
    try:
        position = call_method(stream, "tell")
    except OSError:
        return None
    if not isinstance(position, int):
        return None
    end = call_method(stream, "seek", 0, os.SEEK_END)
    _ = call_method(stream, "seek", position)
    if not isinstance(end, int) or end <= position:
        return None
    return end - position


def _bounded_read_exceeds_limit(request: HttpRequest, stream: object, limit: int) -> bool:
    """Measure by reading, and answer fail-closed if the stream will not be read.

    The bounded read's error boundary, kept separate from the read itself so that
    the measurement below can be written as the straight line it is. A failure
    reading the request stream, closing it, or installing the replacement means
    the package cannot prove this body is within the limit, so it produces the
    fail-closed ``True`` and the caller's ordinary ``413``.

    The shape this closes is an ordinary aborted or broken client: a non-seekable
    request stream whose ``read`` raises ``OSError``, which Django re-raises as
    ``django.http.request.UnreadablePostError``. Unguarded, that would propagate
    through ``views.py::_RequestBodyBoundaryMixin`` and past upstream's
    ``except HTTPException``, turning a client that hung up mid-upload into a
    ``500`` and an error log.

    ``Exception``, never ``BaseException`` - cancellation and process-control
    exceptions still propagate. A partially consumed
    stream is left as it is: ``_read_started`` stays ``True`` and ``_body`` is
    never written, so if anything downstream did reach for the body it would get
    Django's own ``RawPostDataException`` rather than the prefix this function
    happened to collect. The caller refuses the request instead, and the prefix is
    dropped with the request.
    """
    try:
        return _measured_by_bounded_read(request, stream, limit)
    except Exception:
        logger.warning(_UNREADABLE_STREAM_LOG_MESSAGE, type(stream).__name__, exc_info=True)
        return True


def _measured_by_bounded_read(request: HttpRequest, stream: object, limit: int) -> bool:
    """Read at most ``limit + 1`` bytes of ``stream``; report whether that exceeds ``limit``.

    Reads through ``request.read`` rather than ``stream.read`` so Django keeps
    ownership of its own bookkeeping: ``read`` sets ``_read_started`` and
    translates a stream ``OSError`` into ``UnreadablePostError`` - which the caller
    turns into this module's fail-closed answer, so the translation is kept for
    Django's sake rather than for an error contract of its own.

    Over the limit, the loop stops as soon as ``limit + 1`` bytes have arrived
    and the collected chunks are **never joined** - the remainder of the request
    is left unread and no over-limit ``bytes`` value is ever allocated.

    Under it, the prefix *is* the whole body (the loop only exits early on
    end-of-stream), and it is handed back by giving the request an equivalent
    byte source rather than by pre-filling Django's cache: the consumed stream is
    closed and replaced with a rewound ``BytesIO`` over those exact bytes, and
    ``_read_started`` is reset to the ``False`` the request was constructed with -
    which is now true again, because the installed stream is complete and
    unread. ``HttpRequest.body`` therefore still runs in full when Strawberry asks
    for the body: it returns the original bytes byte-for-byte, and, crucially, it
    still applies **Django's own** ``DATA_UPLOAD_MAX_MEMORY_SIZE`` ceiling in
    whatever form the installed Django implements it (a ``CONTENT_LENGTH``
    comparison everywhere, plus a seekable-size check on the releases that have
    one - which the substituted ``BytesIO`` now satisfies).

    Writing ``request._body`` directly instead was the obvious shape and is
    wrong: it makes ``HttpRequest.body`` short-circuit on its cache, silently
    disabling Django's ceiling for every request that took this branch, so a
    project relying on a ``DATA_UPLOAD_MAX_MEMORY_SIZE`` lower than the package cap
    would lose it. The package must add a ceiling, never remove one.
    """
    chunks: list[bytes] = []
    read_so_far = 0
    while read_so_far <= limit:
        chunk = request.read(min(_READ_CHUNK_BYTES, limit + 1 - read_so_far))
        if not chunk:
            break
        chunks.append(chunk)
        read_so_far += len(chunk)
    if read_so_far > limit:
        return True
    _ = call_method(stream, "close")
    request._stream = BytesIO(b"".join(chunks))
    # basedpyright: django-stubs omits HttpRequest._read_started, which HttpRequest.read reads; the
    # omission reads as an unknown attribute
    request._read_started = False  # pyright: ignore[reportAttributeAccessIssue]
    return False
