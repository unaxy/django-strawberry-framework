"""Class and callable identity for the package's own reads, and the spellings error messages use.

- ``overrides`` and ``mro_attr`` answer what a class stores under a name, or else its
  metaclass does, read by ``inspect.getattr_static`` so no descriptor runs. A
  ``classmethod`` or ``staticmethod`` wrapped around the same function is the same stored
  function, so a re-wrap is not an override.
- ``mro_entry`` finds the nearest registered ancestor by identity, never by ``==`` or
  ``hash`` on the class.
- ``kind`` and ``text`` spell a value for an error message: a class names itself, any other
  value names its type, and a ``str`` subclass such as a ``(str, Enum)`` member spells as
  its own text.
- ``name`` names a C callable or a callable instance, which may carry no ``__name__`` of its
  own.
"""

from __future__ import annotations

import inspect
import types
from typing import TYPE_CHECKING, TypeVar

from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.utils.typing import object_result

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = (
    "kind",
    "mro_attr",
    "mro_entry",
    "name",
    "overrides",
    "text",
)

_K = TypeVar("_K")
_V = TypeVar("_V")

# The two C descriptor types a ``callable`` check does not cover.
_NON_CALLABLE_C_TYPES = (types.GetSetDescriptorType, types.MemberDescriptorType)


def mro_attr(cls: object, attr: str, default: object = None) -> object:
    """Return ``attr`` as ``inspect.getattr_static`` finds it on ``cls``, else ``default``."""
    return object_result(inspect.getattr_static, cls, attr, default)


def overrides(cls: object, base: type[object], *names: str) -> bool:
    """Whether ``cls`` stores a different function than ``base`` under any of ``names``.

    ``False`` unless ``cls`` is a class whose real MRO contains ``base``. Both sides are read
    by ``mro_attr`` and compared by the identity of the function a wrapper's ``__func__``
    holds, so a ``classmethod`` or ``staticmethod`` re-wrap of the same function, and a
    bound method stored on the subclass, are not overrides.
    """
    if not isinstance(cls, type) or not any(entry is base for entry in cls.__mro__):
        return False
    for attr in names:
        own, inherited = mro_attr(cls, attr), mro_attr(base, attr)
        if read_attr(own, "__func__", own) is not read_attr(inherited, "__func__", inherited):
            return True
    return False


def mro_entry(mapping: Mapping[_K, _V], cls: object) -> tuple[_K, _V] | None:
    """Return the ``(key, value)`` entry keyed by the first class in the real MRO of ``cls``.

    The most specific class wins whatever the mapping's insertion order, so an unregistered
    subclass answers through its nearest registered ancestor. A key mapped to ``None``
    answers ``(key, None)``. ``None`` when no class in the MRO is a key, and for a non-class
    ``cls``. ``mapping`` is copied once, so a registration on another thread cannot change it
    during the scan, and keys are matched by identity.
    """
    if not isinstance(cls, type):
        return None
    entries = dict(mapping)
    for klass in cls.__mro__:
        for key, value in entries.items():
            if key is klass:
                return key, value
    return None


def kind(value: object) -> str:
    """Return the kind an error message names ``value`` by.

    A class names itself, so a Django model reads ``Galaxy`` and not ``ModelBase``. Any other
    value names its real class. A name that is empty falls back to the metaclass's name, then
    to ``"object"``.
    """
    if isinstance(value, type):
        return value.__name__ or type(value).__name__ or "object"
    return type(value).__name__ or "object"


def text(value: object, fallback: str = "") -> str:
    """Return ``value`` as an exact ``str``, or ``fallback`` when that text is empty.

    A ``str`` subclass is copied through the base ``str`` slot, so a ``(str, Enum)`` member
    or a ``TextChoices`` member spells its value and no consumer ``__str__`` runs. Anything
    else renders through ``str()``.
    """
    rendered = str.__str__(value) if isinstance(value, str) else str(value)
    return rendered or fallback


def name(obj: object) -> str:
    """Return the name a C callable or callable instance declares, else its type's name.

    A class, function, builtin, bound method or C descriptor answers its own ``__name__``. A
    callable instance answers a ``__name__`` it stores (the one ``functools.update_wrapper``
    copies onto a wrapper). Any other value answers its type's name, so the result is always
    a non-empty ``str``.
    """
    fallback = type(obj).__name__ or "object"
    if callable(obj) or isinstance(obj, _NON_CALLABLE_C_TYPES):
        declared: object = getattr(obj, "__name__", None)
        if isinstance(declared, str) and declared:
            return declared
    return fallback
