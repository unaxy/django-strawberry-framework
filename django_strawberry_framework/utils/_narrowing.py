"""Narrowing predicates and typed base slots for values whose type is only ``object``.

The package reads consumer-controlled values (input payloads, ``Meta`` options,
context objects, stored queryset state) that arrive typed ``object``. A bare
``isinstance(value, dict)`` on such a value narrows to ``dict[Unknown, Unknown]``
because ``dict``'s slots are invariant, and a bare unbound slot call
(``dict.items(value)``, ``list.__iter__(value)``) specializes the class with
``Unknown`` the same way. Each predicate here runs exactly the check its call
sites spell and states the element types as ``object``, so the narrowed value is
a container of ``object`` the caller then checks member by member.

Two families of container check, kept apart because they answer different questions:

* ``is_dict`` / ``is_list`` / ... are ``isinstance`` checks (subclasses pass) and
  ``TypeIs`` predicates. At runtime each name IS the class's own
  ``__instancecheck__`` bound to it, so a check costs no extra Python frame on the
  input walks that make one per value.
* ``is_exact_*`` are ``type(value) is C`` checks (subclasses fail) and
  ``TypeGuard`` predicates, since a negative answer says nothing about a subclass.

``is_class``, ``is_str`` and ``is_char_wise`` stand apart from both:
``issubclass(type(value), C)`` checks (subclasses pass) that ask the value's real
type. ``isinstance`` falls back to a ``__class__`` read when the real type does not
match, and a ``__class__`` property can raise or claim a class the value is not;
the real type can do neither, so these are the predicates for a value whose answer
gates an operation that itself checks the real type (``str.__eq__`` refuses a value
that is not really a ``str``, ``issubclass`` one that is not really a class).

The typed slots (``dict_items``, ``list_iter``, ...) are the builtin base
methods themselves at runtime, so a subclass override of ``items`` /
``__iter__`` still cannot decide what a walk sees; under the checker they are
declared generic over the container they read.

The typed reads (``read_attr``, ``call_method``, ``pk_of``, ``enum_value``,
``dict_of``, ``list_of``, ``instance_dict``) are, at runtime, ``getattr`` (read, or
read and called), ``operator.attrgetter("pk")`` / ``("value")``, ``dict``, ``list``
and ``utils/truth.py::instance_state``. Typeshed declares a ``getattr`` read and an
enum member's ``value`` ``Any``, django-stubs declares ``Model.pk`` ``Any``, and ``dict`` / ``list`` of an
``object`` match no overload; under the checker each answers in ``object`` terms,
which the caller narrows like any other consumer value.

``require_instance`` / ``require`` are the narrowing for a value whose source
guarantees its class but types it loosely: each checks the guarantee (``isinstance``,
or a ``TypeIs`` predicate for a generic class) and raises ``TypeError`` the moment it
stops holding. ``optional_instance`` is ``require_instance`` for a slot that may hold
``None``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING, TypeGuard, TypeVar

from . import truth

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, ItemsView, Iterator
    from enum import Enum
    from typing import Protocol, overload

    from django.db.models import Model
    from typing_extensions import TypeIs

    _KeyT = TypeVar("_KeyT")
    _ValueT = TypeVar("_ValueT")

    def is_dict(_value: object, /) -> TypeIs[dict[object, object]]:
        """Return whether the value is a ``dict`` (subclasses included)."""
        ...

    def is_list(_value: object, /) -> TypeIs[list[object]]:
        """Return whether the value is a ``list`` (subclasses included)."""
        ...

    def is_tuple(_value: object, /) -> TypeIs[tuple[object, ...]]:
        """Return whether the value is a ``tuple`` (subclasses included)."""
        ...

    def is_set(_value: object, /) -> TypeIs[set[object]]:
        """Return whether the value is a ``set`` (subclasses included)."""
        ...

    def is_frozenset(_value: object, /) -> TypeIs[frozenset[object]]:
        """Return whether the value is a ``frozenset`` (subclasses included)."""
        ...

    def is_abstract_set(_value: object, /) -> TypeIs[AbstractSet[object]]:
        """Return whether the value is a ``collections.abc.Set`` (registered virtual subclasses included)."""
        ...

    def is_memoryview(_value: object, /) -> TypeIs[memoryview]:
        """Return whether the value is a ``memoryview`` (subclasses included)."""
        ...

    def is_iterable(_value: object, /) -> TypeIs[Iterable[object]]:
        """Return whether the value is a ``collections.abc.Iterable`` (declares ``__iter__``)."""
        ...

    def is_mapping(_value: object, /) -> TypeIs[Mapping[object, object]]:
        """Return whether the value is a ``Mapping`` (registered virtual subclasses included)."""
        ...

    def dict_items(_value: dict[_KeyT, _ValueT], /) -> ItemsView[_KeyT, _ValueT]:
        """``dict.items`` read through the base slot."""
        ...

    def dict_get(_value: dict[_KeyT, _ValueT], _key: _KeyT, /) -> _ValueT | None:
        """``dict.get`` read through the base slot."""
        ...

    def list_iter(_value: list[_ValueT], /) -> Iterator[_ValueT]:
        """``list.__iter__`` read through the base slot."""
        ...

    def tuple_iter(_value: tuple[_ValueT, ...], /) -> Iterator[_ValueT]:
        """``tuple.__iter__`` read through the base slot."""
        ...

    def set_iter(_value: set[_ValueT], /) -> Iterator[_ValueT]:
        """``set.__iter__`` read through the base slot."""
        ...

    def frozenset_iter(_value: frozenset[_ValueT], /) -> Iterator[_ValueT]:
        """``frozenset.__iter__`` read through the base slot."""
        ...

    def mapping_get(_value: Mapping[_KeyT, _ValueT], _key: _KeyT, /) -> _ValueT | None:
        """``Mapping.get`` read through the ABC's own method."""
        ...

    def type_mro(_cls: type[object], /) -> tuple[type[object], ...]:
        """Read the real ``__mro__`` (``utils/truth.py::mro``), past any metaclass."""
        ...

    def class_dict(_cls: type[object], /) -> Mapping[str, object]:
        """Read the real own namespace (``utils/truth.py::class_dict``), past any metaclass."""
        ...

    def type_attr(_cls: type[object], _name: str, /) -> object:
        """``type.__getattribute__``: an attribute read that skips a metaclass ``__getattribute__``."""
        ...

    def is_awaitable(_value: object, /) -> TypeIs[Awaitable[object]]:
        """Return whether ``await`` accepts the value (``inspect.isawaitable``).

        A generator-based coroutine (``@types.coroutine``) answers ``True`` without being an
        ``Awaitable`` instance; ``await`` is the one operation the narrowing licenses.
        """
        ...

    class _AttrReader(Protocol):
        """``getattr``'s two call shapes, each answering ``object``."""

        @overload
        def __call__(self, value: object, name: str, /) -> object: ...
        @overload
        def __call__(
            self,
            value: object,
            name: str,
            default: object,
            /,
        ) -> object: ...

    #: ``getattr``, its read typed ``object``.
    read_attr: _AttrReader

    def pk_of(_row: Model, /) -> object:
        """Return a model row's ``pk``, typed ``object``."""
        ...

    def dict_of(_value: object, /) -> dict[object, object]:
        """Return ``dict(value)``, raising whatever ``dict`` raises for a value it cannot copy."""
        ...

    def call_method(_value: object, _name: str, /, *_args: object) -> object:
        """Return ``value.<name>(*args)``: the lookup and the call each raise what they raise."""
        ...

    def list_of(_value: object, /) -> list[object]:
        """Return ``list(value)``, raising whatever ``list`` raises for a value it cannot iterate."""
        ...

    def enum_value(_member: Enum, /) -> object:
        """Return an enum member's ``value``, typed ``object`` (typeshed declares it ``Any``)."""
        ...

    def instance_dict(_value: object, /) -> dict[str, object]:
        """Return the value's own ``__dict__``, read past any ``__getattribute__`` its class defines.

        ``utils/truth.py::instance_state``: a value whose class keeps no instance
        ``__dict__`` is a ``TypeError``.
        """
        ...

else:
    import inspect
    from operator import attrgetter

    is_dict = dict.__instancecheck__
    is_list = list.__instancecheck__
    is_tuple = tuple.__instancecheck__
    is_set = set.__instancecheck__
    is_frozenset = frozenset.__instancecheck__
    is_mapping = Mapping.__instancecheck__
    is_iterable = Iterable.__instancecheck__
    is_abstract_set = AbstractSet.__instancecheck__
    is_memoryview = memoryview.__instancecheck__
    dict_items = dict.items
    dict_get = dict.get
    list_iter = list.__iter__
    tuple_iter = tuple.__iter__
    set_iter = set.__iter__
    frozenset_iter = frozenset.__iter__
    mapping_get = Mapping.get
    type_mro = truth.mro
    class_dict = truth.class_dict
    type_attr = type.__getattribute__
    is_awaitable = inspect.isawaitable
    read_attr = getattr
    pk_of = attrgetter("pk")
    enum_value = attrgetter("value")
    dict_of = dict
    list_of = list
    instance_dict = truth.instance_state

    def call_method(value: object, name: str, /, *args: object) -> object:
        return getattr(value, name)(*args)


__all__ = (
    "call_method",
    "class_dict",
    "dict_get",
    "dict_items",
    "dict_of",
    "enum_value",
    "frozenset_iter",
    "instance_dict",
    "is_abstract_set",
    "is_awaitable",
    "is_char_wise",
    "is_class",
    "is_dict",
    "is_exact_dict",
    "is_exact_list",
    "is_exact_list_or_tuple",
    "is_exact_pair",
    "is_exact_set_or_frozenset",
    "is_exact_tuple",
    "is_frozenset",
    "is_iterable",
    "is_list",
    "is_list_or_tuple",
    "is_mapping",
    "is_memoryview",
    "is_set",
    "is_set_or_frozenset",
    "is_str",
    "is_tuple",
    "list_iter",
    "list_of",
    "mapping_get",
    "optional_instance",
    "pk_of",
    "read_attr",
    "require",
    "require_instance",
    "set_iter",
    "tuple_iter",
    "type_attr",
    "type_mro",
)


def is_list_or_tuple(value: object) -> TypeIs[list[object] | tuple[object, ...]]:
    """Return whether ``value`` is a ``list`` or a ``tuple`` (subclasses included)."""
    return isinstance(value, (list, tuple))


def is_set_or_frozenset(value: object) -> TypeIs[set[object] | frozenset[object]]:
    """Return whether ``value`` is a ``set`` or a ``frozenset`` (subclasses included)."""
    return isinstance(value, (set, frozenset))


def is_class(value: object) -> TypeIs[type[object]]:
    """Return whether ``value`` IS a class, asked of its real type.

    ``issubclass(type(value), type)`` rather than ``isinstance(value, type)``: the real
    type cannot be restated by a ``__class__`` property on the value.
    """
    return issubclass(type(value), type)


_InstanceT = TypeVar("_InstanceT")


def require_instance(value: object, cls: type[_InstanceT], /) -> _InstanceT:
    """Return ``value`` as the ``cls`` instance it must be, raising ``TypeError`` when it is not."""
    if not isinstance(value, cls):
        raise TypeError(
            f"expected an instance of {truth.kind(cls)}, got {truth.kind(value)}",
        )
    return value


def optional_instance(value: object, cls: type[_InstanceT], /) -> _InstanceT | None:
    """``require_instance`` for an optional slot: ``None`` stays ``None``, anything else must be a ``cls``."""
    return None if value is None else require_instance(value, cls)


def require(value: object, predicate: Callable[[object], TypeIs[_InstanceT]], /) -> _InstanceT:
    """Return ``value`` as the type ``predicate`` proves, raising ``TypeError`` when it does not."""
    if not predicate(value):
        raise TypeError(
            f"expected the type the source guarantees, got {truth.kind(value)}",
        )
    return value


def is_str(value: object) -> TypeIs[str]:
    """Return whether ``value`` IS a ``str`` (subclasses included), asked of its real type.

    ``issubclass(type(value), str)`` rather than ``isinstance(value, str)``: a
    ``__class__`` property on the value can neither claim ``str`` nor raise, so a
    ``True`` answer is one the base ``str`` slots accept.
    """
    return issubclass(type(value), str)


def is_char_wise(value: object) -> TypeIs[str | bytes | bytearray | memoryview]:
    """Return whether ``value`` is text or bytes-like (subclasses included), asked of its real type.

    The values that iterate character by character (or byte by byte into ``int``),
    so a caller expecting a container of items refuses them before iterating. A
    ``__class__`` property on the value can neither claim one of these types nor
    raise; a Django lazy proxy is judged as itself, so a caller that means the
    wrapped object unwraps it first (``utils/lazy.py::unwrap_lazy_object``).
    """
    return issubclass(
        type(value),
        (
            str,
            bytes,
            bytearray,
            memoryview,
        ),
    )


def is_exact_dict(value: object) -> TypeGuard[dict[object, object]]:
    """Return whether ``value`` is EXACTLY a builtin ``dict`` (never a subclass)."""
    return type(value) is dict


def is_exact_list(value: object) -> TypeGuard[list[object]]:
    """Return whether ``value`` is EXACTLY a builtin ``list`` (never a subclass)."""
    return type(value) is list


def is_exact_tuple(value: object) -> TypeGuard[tuple[object, ...]]:
    """Return whether ``value`` is EXACTLY a builtin ``tuple`` (never a subclass)."""
    return type(value) is tuple


def is_exact_pair(value: object) -> TypeGuard[tuple[object, object]]:
    """Return whether ``value`` is EXACTLY a builtin ``tuple`` of two members (never a subclass).

    The type is proven first, so the length read and the pattern never dispatch a
    consumer ``__len__`` / ``__getitem__``.
    """
    if not is_exact_tuple(value):
        return False
    match value:
        case (_, _):
            return True
        case _:
            return False


def is_exact_list_or_tuple(value: object) -> TypeGuard[list[object] | tuple[object, ...]]:
    """Return whether ``value`` is EXACTLY a builtin ``list`` or ``tuple``.

    The type is compared by identity: ``in`` over a tuple of classes would compare by
    equality and run a consumer metaclass ``__eq__``, which can claim a builtin.
    """
    value_type = type(value)
    return value_type is list or value_type is tuple


def is_exact_set_or_frozenset(value: object) -> TypeGuard[set[object] | frozenset[object]]:
    """Return whether ``value`` is EXACTLY a builtin ``set`` or ``frozenset``.

    The type is compared by identity, as in ``is_exact_list_or_tuple``.
    """
    value_type = type(value)
    return value_type is set or value_type is frozenset
