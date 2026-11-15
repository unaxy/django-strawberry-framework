"""Class and callable identity for the package's own reads, and the spellings error messages use.

- ``overrides``, ``stored_function`` and ``mro_attr`` answer what a class stores under a
  name. ``mro_attr`` reads each class on ``cls.__mro__`` through its own ``__dict__``, as
  the interpreter's implicit special-method lookups search the MRO, so an attribute only a
  metaclass defines is absent.
  A ``classmethod`` or ``staticmethod`` wrapped around the same function is the same stored
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

import sys
import types
from typing import TYPE_CHECKING, TypeAlias, TypeVar

if TYPE_CHECKING:
    from collections.abc import Mapping

    #: Any ``classmethod`` wrapper.
    _ClassmethodAny: TypeAlias = classmethod[object, ..., object]
    #: Any ``staticmethod`` wrapper.
    _StaticmethodAny: TypeAlias = staticmethod[..., object]
else:
    # ``classmethod`` and ``staticmethod`` have no ``__class_getitem__`` before Python
    # 3.14: each hint stays the class.
    _ClassmethodAny = classmethod
    _StaticmethodAny = staticmethod

__all__ = (
    "kind",
    "mro_attr",
    "mro_entry",
    "name",
    "overrides",
    "stored_function",
    "text",
)

_K = TypeVar("_K")
_V = TypeVar("_V")

# log10(2): converts a bit length into a decimal digit count bound.
_LOG10_2 = 0.30102999566398120

# The two C descriptor types a ``callable`` check does not cover.
_NON_CALLABLE_C_TYPES = (types.GetSetDescriptorType, types.MemberDescriptorType)


def stored_function(value: object) -> object:
    """Return the function a stored ``classmethod``, ``staticmethod`` or bound method holds.

    Only the exact wrapper types unwrap. Any other value, a subclass of those wrappers
    included, comes back unchanged.
    """
    if type(value) is _ClassmethodAny:
        return value.__func__
    if type(value) is _StaticmethodAny:
        return value.__func__
    if type(value) is types.MethodType:
        return value.__func__
    return value


def mro_attr(cls: object, attr: str, default: object = None) -> object:
    """Return ``attr`` from the first namespace in the real MRO of ``cls`` that defines it.

    This is the lookup the interpreter makes for an implicit special method. The metaclass
    is not searched, so an attribute only a metaclass defines answers ``default``; a stored
    ``None`` answers ``None``. A non-class ``cls`` answers ``default``.
    """
    if not isinstance(cls, type):
        return default
    for entry in cls.__mro__:
        namespace = _own_namespace(entry)
        if attr in namespace:
            return namespace[attr]
    return default


def _own_namespace(cls: type) -> Mapping[str, object]:
    """Return the namespace ``cls`` defines in its own body."""
    return cls.__dict__


def overrides(cls: object, base: type[object], *names: str) -> bool:
    """Whether ``cls`` stores a different function than ``base`` under any of ``names``.

    ``False`` unless ``cls`` is a class whose real MRO contains ``base``. Both sides are read
    by ``mro_attr`` and compared by the identity of the stored function, so a
    ``classmethod`` or ``staticmethod`` re-wrap of the same function, and a bound method
    stored on the subclass, are not overrides.
    """
    if not isinstance(cls, type) or not any(entry is base for entry in cls.__mro__):
        return False
    return any(
        stored_function(mro_attr(cls, attr)) is not stored_function(mro_attr(base, attr))
        for attr in names
    )


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
    or a ``TextChoices`` member spells its value and no consumer ``__str__`` runs. A class
    spells as its ``repr``. Anything else renders through ``str()``.
    """
    if isinstance(value, str):
        rendered = str.__str__(value)
    elif isinstance(value, type):
        rendered = repr(value)
    elif isinstance(value, int) and _int_text_is_builtin(value) and _oversized_int(value):
        rendered = f"<unprintable {kind(value)}>"
    else:
        rendered = str(value)
    return rendered or fallback


def _int_text_is_builtin(value: int) -> bool:
    """Whether the class of ``value`` still resolves ``int``'s own ``__repr__`` and ``__str__``."""
    value_type = type(value)
    return value_type.__repr__ is int.__repr__ and value_type.__str__ is int.__str__


def _oversized_int(value: int) -> bool:
    """Whether ``value`` has more decimal digits than the interpreter lets an int spell.

    The bound comes from the bit length before any conversion runs. ``sys`` reports the digit
    limit; an interpreter without the query has none.
    """
    limit = sys.get_int_max_str_digits() if hasattr(sys, "get_int_max_str_digits") else 0
    return bool(limit) and int.bit_length(value) * _LOG10_2 + 1 > limit


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
