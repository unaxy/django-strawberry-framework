"""The package's raw-request-body boundary, expressed as a ``MIDDLEWARE`` entry.

``views.py`` owns the boundary itself - the cumulative body cap (spec-046
Decision 7) and the header-only wire-encoding refusals (Decision 9). What this
module owns is *where in the request lifecycle* that boundary runs, for
deployments that install it::

    MIDDLEWARE = [
        ...,
        "django_strawberry_framework.middleware.request_body"
        ".GraphQLRequestBodyBoundaryMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        ...,
    ]

Why a middleware entry is the right owner of the ordering
---------------------------------------------------------

Django's ``CsrfViewMiddleware.process_view`` reads
``request.POST.get("csrfmiddlewaretoken", "")`` on every cookie-bearing POST, and
on a multipart request that single read is what invokes ``MultiPartParser`` and
the project's upload handlers - before the view runs. A cap that runs after
something else has already parsed the body is not a gate, so the package's
boundary has to precede that read.

Doing it from inside the view requires exempting the view's callback from the
CSRF middleware and re-entering CSRF from the view, and that re-entry can only
name a CSRF implementation the package chooses. A deployment whose
``MIDDLEWARE`` names a ``CsrfViewMiddleware`` **subclass** - one that strengthens
token binding, adds a tenant check, or logs failures - would then have its own
class silently replaced by Django's base implementation on the GraphQL endpoint
alone. That is a policy substitution, and no view-local decorator can avoid it,
because the configured class is a property of the middleware chain.

So the ordering moves into the chain. This middleware runs the whole boundary
from ``process_view`` - which Django calls after URL resolution and before any
later middleware's ``process_view``, hence before the CSRF middleware's - and
cancels the CSRF exemption the package view's callback carries for the requests
whose boundary it has run. The configured CSRF middleware, whatever class it is,
then runs in full on every request that survives the boundary.

The exemption is a lazily-evaluated object rather than the usual ``True`` for
exactly that reason: whether the ordering is supplied by the chain is not known
when a URLconf is imported, and a deployment must not have to state the same fact
twice. It lives in ``_boundary_ordering.py``
(``::_CsrfOrderingExemption``) together with the marks, and it is ``False``
for a request this middleware has actually run the boundary for - the narrow
fact, and the load-bearing one, since that is the request whose body is proven
measured. For every other request, including one whose callback this middleware
did not recognize as a package view's, the exemption stays ``True`` and the view's
own boundary-then-CSRF re-entry runs exactly as it does without this
middleware. Both arrangements enforce CSRF and both enforce the cap; they differ
only in which class performs the check.

Ordering is verified rather than documented: a chain that lists this middleware
*after* a ``CsrfViewMiddleware`` would put the parse back in front of the cap
while looking correct, so :meth:`GraphQLRequestBodyBoundaryMiddleware.__init__`
refuses it with a ``ConfigurationError`` at startup instead.

What it deliberately does not do
--------------------------------

It holds no policy of its own: the limit, the refusal statuses, and the wire
reasons all stay in ``views.py``, and this module reaches them by instantiating
the resolved view exactly as ``View.as_view`` does. It recognizes a package view
by the marker attribute stamped on the callback and the ``view_class`` /
``view_initkwargs`` bookkeeping behind it (:func:`_package_view_instance`), never
by importing the view classes - the marker and the boundary method's *name* both
reach this module through ``_boundary_ordering.py`` - so no non-package view is
touched and this module imports neither ``views.py`` nor anything that imports
it. And it translates the boundary's
``HTTPException`` into the same ``text/plain`` response upstream's ``dispatch``
produces, so the wire shape of a refusal does not depend on which side of the
CSRF check refused it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from asgiref.sync import markcoroutinefunction
from cross_web import HTTPException
from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.module_loading import import_string
from django.views import View

from django_strawberry_framework._boundary_ordering import (
    _BOUNDARY_ENFORCED,
    _BOUNDARY_MARKER,
    _BOUNDARY_METHOD,
    _BOUNDARY_MOUNT,
    _boundary_middleware_request,
    stamp_prepared_view,
)
from django_strawberry_framework.conf import django_setting
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils import introspection
from django_strawberry_framework.utils._narrowing import (
    is_awaitable,
    is_class,
    is_dict,
    is_str,
    list_of,
    require,
    require_instance,
)
from django_strawberry_framework.utils.typing import is_marked_coroutine_function, object_result

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from django.http import HttpRequest, HttpResponseBase
    from typing_extensions import TypeIs

__all__ = ("GraphQLRequestBodyBoundaryMiddleware",)

#: Django's ``import_string``: django-stubs types its result ``Any``; a ``MIDDLEWARE``
#: entry names a class or a function middleware.
_import_entry: Callable[[str], object] = import_string


#: The ``ConfigurationError`` text for a chain that would defeat the ordering.
_MISORDERED_MIDDLEWARE_MESSAGE = (
    "GraphQLRequestBodyBoundaryMiddleware must appear BEFORE Django's CsrfViewMiddleware in "
    "MIDDLEWARE: the CSRF check reads request.POST, which parses a multipart body, so a "
    "request-body boundary listed after it can no longer run before the parse it exists to "
    "prevent."
)


class GraphQLRequestBodyBoundaryMiddleware:
    """Run the package views' request-body boundary from the middleware chain.

    Install it immediately before the project's ``CsrfViewMiddleware`` entry. See
    the module docstring for why the ordering is a middleware question rather than
    a view-local one, and for what changes on a mount when it is installed.

    Every request that is not a package view's is passed through untouched, at the
    cost of one ``getattr`` in ``process_view``.
    """

    #: Declared for both chains so Django adapts nothing: an async deployment
    #: keeps its coroutine view dispatch, and ``__acall__`` awaits downstream
    #: rather than handing a coroutine to a synchronous caller.
    sync_capable: ClassVar[bool] = True
    async_capable: ClassVar[bool] = True

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponseBase | Awaitable[HttpResponseBase]],
    ) -> None:
        """Bind the downstream chain and refuse a chain that cannot deliver the ordering."""
        self.get_response: Callable[
            [HttpRequest],
            HttpResponseBase | Awaitable[HttpResponseBase],
        ] = get_response
        _require_boundary_before_csrf()
        if is_marked_coroutine_function(self.get_response):
            _ = markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        """Publish the request this middleware is handling, then call downstream.

        The request object rather than a bare "installed" flag, because the
        question the exemption has to answer is per-request - *was the boundary
        run for this one?* - and the answer is the ``_BOUNDARY_ENFORCED`` stamp
        ``process_view`` writes on that same object. Publishing the request
        is therefore what lets one read answer the narrow question instead of the
        broad one.

        The mark spans the downstream call rather than the ``process_view`` hook
        alone, because it is read by the CSRF middleware - which may be *any*
        later entry in the chain - and reset in a ``finally`` so a raising view
        cannot leave it set for whatever the worker handles next.
        """
        # A plain ``bool``: ``is_marked_coroutine_function`` is a TypeGuard, and a guard
        # on it - direct, or through a local, which pyright follows - would re-type
        # ``self`` as a bare callable.
        is_async = bool(is_marked_coroutine_function(self))
        if is_async:
            return self.__acall__(request)
        token = _boundary_middleware_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _boundary_middleware_request.reset(token)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        """Run the async twin of :meth:`__call__` - the ``await`` is the whole difference.

        Separate rather than shared because the reset has to happen after the
        downstream response exists: returning the coroutine from a synchronous
        ``finally`` would reset the mark before the CSRF middleware ever read it.
        """
        token = _boundary_middleware_request.set(request)
        try:
            # An async chain: ``__init__`` marked this instance a coroutine function
            # only when ``get_response`` is one, and only such an instance reaches here.
            response = self.get_response(request)
            if not is_awaitable(response):
                raise TypeError(
                    "an async middleware chain's get_response must return an awaitable, "
                    f"got {introspection.kind(response)}",
                )
            return await response
        finally:
            _boundary_middleware_request.reset(token)

    def process_view(
        self,
        request: HttpRequest,
        view_func: object,
        view_args: tuple[object, ...],
        view_kwargs: dict[str, object],
    ) -> HttpResponseBase | None:
        """Run a package view's body boundary here, before any later ``process_view``.

        The boundary itself is the view's, reached through an instance built and
        set up the way ``View.as_view`` builds and sets one up, so the limit that
        applies is the mount's own
        ``max_request_body_bytes`` and this module states no policy. Running
        ``setup`` before the boundary is load-bearing: a consumer subclass may
        derive request-local boundary state there, and stamping a request after
        checking the pre-setup instance would make the real view skip that state.
        A refusal
        becomes the same ``text/plain`` response upstream's ``dispatch`` produces
        for the identical ``HTTPException``, so a client cannot tell from the
        response which side of the CSRF check refused it.

        It is invoked under the name ``_boundary_ordering.py::_BOUNDARY_METHOD``
        holds, not spelled again here, so the boundary this hook runs cannot come to
        differ from the one ``views.py`` defines under that name.

        A callback :func:`_package_view_instance` declines is left entirely alone:
        no boundary run here, and therefore no stamp, which is what leaves that
        request on the view-local arrangement rather than on neither.
        """
        if getattr(request, _BOUNDARY_ENFORCED, False):
            return None
        view = _package_view_instance(view_func)
        if view is None:
            return None
        view.setup(request, *view_args, **view_kwargs)
        try:
            getattr(view, _BOUNDARY_METHOD)(request)
        except HTTPException as exc:
            return HttpResponse(
                content=exc.reason,
                status=exc.status_code,
                content_type="text/plain",
            )
        mount = introspection.mro_attr(view_func, _BOUNDARY_MOUNT, None)
        if mount is not None:
            stamp_prepared_view(request, mount, view)
        setattr(request, _BOUNDARY_ENFORCED, True)
        return None


def _is_initkwargs(value: object) -> TypeIs[dict[str, object]]:
    """Whether ``value`` is a ``dict`` of keyword arguments: every key a ``str``."""
    return is_dict(value) and all(is_str(key) for key in value)


def _package_view_instance(view_func: object) -> View | None:
    """Return the package view instance whose boundary this callback's mount would run.

    ``None`` means "not a callback this middleware can run a boundary for", and
    that is the whole answer :meth:`GraphQLRequestBodyBoundaryMiddleware
    .process_view` branches on: a declined callback is left with the request
    unstamped, so the view supplies the ordering itself and the CSRF exemption
    stays true (``_boundary_ordering.py::_CsrfOrderingExemption``).

    A package callback carries the marker ``views.py::_boundary_view`` stamps, a
    ``view_class`` that is a class and a ``view_initkwargs`` mapping - Django's own
    ``as_view`` bookkeeping, and what makes the built instance carry the mount's
    own ``max_request_body_bytes``. The attributes are read statically
    (``utils/introspection.py::mro_attr``), so no ``__getattr__``, property or
    descriptor runs. There is deliberately no ``or {}`` default: an absent attribute
    means "not ours", never "ours, with nothing configured". Forging the marker is
    outside the threat model.

    A ``TypeError`` from the construction is a decline too. A function view
    decorated with ``functools.wraps(DjangoGraphQLView.as_view())`` copies the
    marker and an empty ``view_initkwargs`` while building its own view with a
    schema per request; that class cannot be built from the copied kwargs, and
    the view it builds supplies the ordering itself.
    """
    if introspection.mro_attr(view_func, _BOUNDARY_MARKER, default=False) is not True:
        return None
    view_class = introspection.mro_attr(view_func, "view_class", None)
    initkwargs = introspection.mro_attr(view_func, "view_initkwargs", None)
    if not is_class(view_class) or not _is_initkwargs(initkwargs):
        return None
    try:
        return require_instance(object_result(view_class, **initkwargs), View)
    except TypeError:
        return None


def _require_boundary_before_csrf() -> None:
    """Raise ``ConfigurationError`` when a CSRF entry precedes this middleware.

    Read off ``settings.MIDDLEWARE`` at instantiation - which is chain-build time,
    so a misordered deployment fails at startup rather than on the first
    multipart request. Entries are resolved and compared by class rather than by
    dotted path, so a subclass of either middleware is recognized as what it is;
    a non-class entry (a function middleware) is neither and is skipped.

    The first entry of each middleware type in ``MIDDLEWARE`` is what decides the
    comparison: the first boundary entry is what runs first to measure the body,
    and the first CSRF entry is what would parse it.

    Nothing is raised when the chain contains no CSRF middleware at all: there is
    then no read to run behind, and the package view's own CSRF continuation
    still protects the endpoint.
    """
    boundary_index = csrf_index = None
    for index, path in enumerate(list_of(django_setting("MIDDLEWARE"))):
        entry = _import_entry(require(path, is_str))
        if not is_class(entry):
            continue
        if issubclass(entry, GraphQLRequestBodyBoundaryMiddleware) and boundary_index is None:
            boundary_index = index
        elif issubclass(entry, CsrfViewMiddleware) and csrf_index is None:
            csrf_index = index
    if boundary_index is None or csrf_index is None or csrf_index > boundary_index:
        return
    raise ConfigurationError(_MISORDERED_MIDDLEWARE_MESSAGE)
