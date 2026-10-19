"""Django lazy-proxy unwrapping: the object a ``LazyObject`` stands for, before a type check.

Django hands the framework lazy proxies in ordinary operation: ``request.user``
is a ``SimpleLazyObject``, and a deployment may put a request or a policy behind
one. A proxy passes ``isinstance`` for the object it wraps only by forwarding
``__class__``, which ``utils/truth.py::is_instance`` deliberately ignores, so
every real-class check on a value that may be such a proxy first reads the
wrapped object here and checks that instead. Only Django's own ``LazyObject``
is unwrapped, recognised by its real class; any other object that forwards
``__class__`` (a ``Mock(spec=...)``, a hand-written stand-in) wraps no real
object and is checked as what it is.

This module is Django-aware and sits below every subsystem that type-checks a
request, a policy or a Relay node, so ``utils/truth.py`` stays Django-free.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
