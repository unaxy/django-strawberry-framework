"""Django lazy-proxy unwrapping: the object a ``LazyObject`` stands for, before a type check.

A proxy passes ``isinstance`` for the object it wraps only by forwarding
``__class__``, which ``utils/truth.py::is_instance`` deliberately ignores. The
wrapped object is read here in exactly two kinds of place. One is where Django
hands over a real runtime lazy object: ``request.user`` is a
``SimpleLazyObject``, and what stands behind it reaches the Relay node paths.
The other is a gate that reads a protocol ``LazyObject`` forwards (``__iter__``,
``__len__``, ``__contains__``), which would otherwise read a proxied ``str``
character by character or a proxied ``set`` in hash order. Every other
real-class gate (configuration: ``Meta`` keys, optimizer hints, policies,
transport and request classification, router applications) refuses a proxy
with its existing typed error, as ``Meta.name``, ``OptimizerHint.strategy``,
``strictness=`` and ``SESSION_ENGINE`` do. Only Django's own ``LazyObject`` is
unwrapped, recognised by its real class; any other object that forwards
``__class__`` (a ``Mock(spec=...)``, a hand-written stand-in) wraps no real
object and is checked as what it is.

This module is Django-aware and sits below every subsystem that unwraps, so
``utils/truth.py`` stays Django-free.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from django.utils.functional import LazyObject, empty

from . import truth
from ._narrowing import call_method, read_attr

__all__ = ("unwrap_lazy_object",)

# Django's proxy class with its parameter solved, so the real-class check narrows to a known type.
# The annotation is checker-only: ``LazyObject`` is generic in django-stubs but not subscriptable
# at run time unless django-stubs-ext patches it, and the package never requires that patch.
if TYPE_CHECKING:
    _LAZY_OBJECT: type[LazyObject[object]]
else:
    _LAZY_OBJECT = LazyObject

_T = TypeVar("_T")


# A proxy answers for the object it wraps; any other value comes back as itself, so its
# static type is unchanged. The overloads are checker-only for the same reason as
# ``_LAZY_OBJECT``: their ``LazyObject[_T]`` annotation is not evaluable at run time.
if TYPE_CHECKING:

    @overload
    def unwrap_lazy_object(obj: LazyObject[_T]) -> _T: ...
    @overload
    def unwrap_lazy_object(obj: _T) -> _T: ...


def unwrap_lazy_object(obj: object) -> object:
    """Return the object a Django lazy proxy stands for; any other value unchanged.

    Django's ``LazyObject`` (``request.user`` is a ``SimpleLazyObject``) passes
    for the object it wraps by forwarding ``__class__``, which a truthful class
    read deliberately ignores. The proxy is recognised by its real class and
    the wrapped object is read from it, so the type check runs against the
    object itself. The factory runs on first use, as any attribute access on
    the proxy would run it; whatever it raises propagates. A proxy whose target
    is itself a proxy is followed to the first object that is not one.
    """
    while truth.is_instance(obj, _LAZY_OBJECT):
        if read_attr(obj, "_wrapped") is empty:
            _ = call_method(obj, "_setup")
        obj = read_attr(obj, "_wrapped")
    return obj
