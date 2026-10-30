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

``is_str``, ``is_char_wise`` and ``is_text_atom`` stand apart from both:
``issubclass(type(value), C)`` checks (subclasses pass) that ask the value's real
type. ``isinstance`` falls back to a ``__class__`` read when the real type does not
match, and a ``__class__`` property can raise or claim a class the value is not;
the real type can do neither, so these are the predicates for a value whose answer
gates an operation that itself checks the real type (``str.__eq__`` refuses a value
that is not really a ``str``). Whether a value is a class is ``utils/truth.py::is_type``.

The typed slots (``dict_items``, ``list_iter``, ...) are the builtin base
methods themselves at runtime, so a subclass override of ``items`` /
``__iter__`` still cannot decide what a walk sees; under the checker they are
declared generic over the container they read.

The typed reads (``read_attr``, ``call_method``, ``pk_of``, ``enum_value``,
``dict_of``, ``list_of``) are, at runtime, ``getattr`` (read, or read and called),
``operator.attrgetter("pk")`` / ``("value")``, ``dict`` and ``list``. Typeshed
declares a ``getattr`` read and an enum member's ``value`` ``Any``, django-stubs
declares ``Model.pk`` ``Any``, and ``dict`` / ``list`` of an ``object`` match no
overload; under the checker each answers in ``object`` terms, which the caller
narrows like any other consumer value.

``is_concrete_field`` and ``is_queryset`` are ``isinstance`` checks (like ``is_dict``, each
name IS the class's own ``__instancecheck__``) whose claim is only what the check proves:
a model ``Field`` (never a reverse ``ForeignObjectRel``), and a ``QuerySet`` whose rows are
``object`` (a ``.values()`` queryset passes the same check, so no model-row claim is made).
``is_real_mapping`` / ``is_real_collection`` stand with ``is_str``: the
``issubclass(type(value), ABC)`` check asked of the real type.

``optional_annotation``, ``get_item`` / ``set_item`` / ``del_item`` and ``iter_of`` are typed
slots over ``annotation | None``, ``operator.getitem`` / ``setitem`` / ``delitem`` and
``iter``: each takes and answers ``object``, which is all the operation guarantees, so a
call site narrows the answer like any other consumer value.

``require_instance`` / ``require`` are the narrowing for a value whose source
guarantees its class but types it loosely: each checks the guarantee (``isinstance``,
or a ``TypeIs`` predicate for a generic class) and raises ``TypeError`` the moment it
stops holding. ``optional_instance`` is ``require_instance`` for a slot that may hold
``None``.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from collections.abc import Set as AbstractSet
from typing import TYPE_CHECKING, TypeGuard, TypeVar

from django.utils.functional import Promise

from . import truth

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, ItemsView, Iterator
    from enum import Enum
    from typing import Protocol, overload

    from django.db.models import Model, QuerySet
    from typing_extensions import TypeIs

    from .typing import ConcreteField

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

    def is_concrete_field(_value: object, /) -> TypeIs[ConcreteField]:
        """Return whether the value is a model ``Field`` (a reverse ``ForeignObjectRel`` is not one).

        Any ``models.Field``, not only a ``.concrete`` column: a many-to-many, a
        ``GenericRelation`` and a ``GenericForeignKey`` (a ``Field`` subclass in the Django
        releases this package supports) pass too.
        """
        ...

    def is_queryset(_value: object, /) -> TypeIs[QuerySet[Model, object]]:
        """Return whether the value is a ``QuerySet`` (subclasses included).

        The claim is ``object`` rows: a ``.values()`` queryset passes the same check, so
        a caller reads ``model`` / ``db`` and nothing about the rows.
        """
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

    def is_awaitable(_value: object, /) -> TypeIs[Awaitable[object]]:
        """Return whether ``await`` accepts the value (``inspect.isawaitable``).

        A generator-based coroutine (``@types.coroutine``) answers ``True`` without being an
        ``Awaitable`` instance; ``await`` is the one operation the narrowing licenses.
        """
        ...

    def optional_annotation(_annotation: object, /) -> object:
        """Return ``annotation | None``: the annotation widened to accept ``None``.

        A class, an alias or a special form (``Annotated[...]``) widens; a value with no
        ``|`` raises the ``TypeError`` the expression raises.
        """
        ...

    def get_item(_container: object, _key: object, /) -> object:
        """Return ``container[key]``: the lookup raises whatever the container raises."""
        ...

    def set_item(_container: object, _key: object, _value: object, /) -> None:
        """Run ``container[key] = value``: the store raises whatever the container raises."""
        ...

    def del_item(_container: object, _key: object, /) -> None:
        """Run ``del container[key]``: the delete raises whatever the container raises."""
        ...

    def iter_of(_value: object, /) -> Iterator[object]:
        """Return ``iter(value)``, raising whatever ``iter`` raises for a value it cannot iterate."""
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

else:
    import inspect
    from operator import attrgetter, delitem, getitem, setitem

    from django.db import models

    is_dict = dict.__instancecheck__
    is_list = list.__instancecheck__
    is_tuple = tuple.__instancecheck__
    is_frozenset = frozenset.__instancecheck__
    is_mapping = Mapping.__instancecheck__
    is_iterable = Iterable.__instancecheck__
    is_abstract_set = AbstractSet.__instancecheck__
    is_memoryview = memoryview.__instancecheck__
    is_concrete_field = models.Field.__instancecheck__
    is_queryset = models.QuerySet.__instancecheck__
    dict_items = dict.items
    dict_get = dict.get
    list_iter = list.__iter__
    tuple_iter = tuple.__iter__
    set_iter = set.__iter__
    frozenset_iter = frozenset.__iter__
    mapping_get = Mapping.get
    is_awaitable = inspect.isawaitable
    read_attr = getattr
    pk_of = attrgetter("pk")
    enum_value = attrgetter("value")
    dict_of = dict
    list_of = list
    get_item = getitem
    set_item = setitem
    del_item = delitem
    iter_of = iter

    def optional_annotation(annotation: object, /) -> object:
        return annotation | None

    def call_method(value: object, name: str, /, *args: object) -> object:
        return getattr(value, name)(*args)


__all__ = (
    "call_method",
    "del_item",
    "dict_get",
    "dict_items",
    "dict_of",
    "enum_value",
    "frozenset_iter",
    "get_item",
    "is_abstract_set",
    "is_awaitable",
    "is_char_wise",
    "is_concrete_field",
    "is_dict",
    "is_exact_dict",
    "is_exact_list",
    "is_exact_list_or_tuple",
    "is_exact_pair",
    "is_exact_set_or_frozenset",
    "is_exact_tuple",
    "is_exact_tuple_or_frozenset",
    "is_frozenset",
    "is_iterable",
    "is_list",
    "is_list_or_tuple",
    "is_mapping",
    "is_memoryview",
    "is_queryset",
    "is_real_collection",
    "is_real_mapping",
    "is_set_or_frozenset",
    "is_str",
    "is_text_atom",
    "is_tuple",
    "iter_of",
    "list_iter",
    "list_of",
    "mapping_get",
    "optional_annotation",
    "optional_instance",
    "pk_of",
    "read_attr",
    "require",
    "require_instance",
    "set_item",
    "set_iter",
    "tuple_iter",
)


def is_list_or_tuple(value: object) -> TypeIs[list[object] | tuple[object, ...]]:
    """Return whether ``value`` is a ``list`` or a ``tuple`` (subclasses included)."""
    return isinstance(value, (list, tuple))


def is_set_or_frozenset(value: object) -> TypeIs[set[object] | frozenset[object]]:
    """Return whether ``value`` is a ``set`` or a ``frozenset`` (subclasses included)."""
    return isinstance(value, (set, frozenset))


def is_real_mapping(value: object) -> TypeIs[Mapping[object, object]]:
    """Return whether ``value`` IS a ``Mapping`` (virtual subclasses included), asked of its real type.

    ``issubclass(type(value), Mapping)`` rather than ``isinstance``: a ``__class__``
    property on the value can neither claim ``Mapping`` nor raise.
    """
    return issubclass(type(value), Mapping)


def is_real_collection(value: object) -> TypeIs[Collection[object]]:
    """Return whether ``value`` IS a ``Collection`` (virtual subclasses included), asked of its real type.

    ``issubclass(type(value), Collection)`` rather than ``isinstance``, as in
    ``is_real_mapping``. A ``str`` is a ``Collection``; a caller that refuses text
    asks ``is_char_wise`` first.
    """
    return issubclass(type(value), Collection)


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


def is_text_atom(value: object) -> TypeIs[str | bytes | bytearray | memoryview | Promise]:
    """Return whether ``value`` is one piece of text, asked of its real type.

    ``is_char_wise`` plus a Django lazy ``Promise`` (a ``gettext_lazy(...)``
    string): the proxy is no ``str``, yet it stands for one and forwards
    ``__iter__`` / ``__len__`` / ``__contains__`` to it, so it walks and answers
    membership character by character exactly as the text does. Django reads a
    ``Promise`` as text it has not evaluated yet (``django.utils.encoding.smart_str``
    returns it unchanged), and so does this predicate: the proxy is recognised by
    its real class and never evaluated. Every ``Promise`` counts, whatever result
    class it wraps, since the proxy does not say which without evaluating it (a
    ``lazy(..., list)`` value is text here too). A caller that refuses text where
    it expects a container of items, or keeps text whole where it would iterate
    anything else, asks this rather than ``is_char_wise``.
    """
    return is_char_wise(value) or issubclass(type(value), Promise)


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


def is_exact_tuple_or_frozenset(
    value: object,
) -> TypeGuard[tuple[object, ...] | frozenset[object]]:
    """Return whether ``value`` is EXACTLY a builtin ``tuple`` or ``frozenset``.

    The type is compared by identity, as in ``is_exact_list_or_tuple``.
    """
    value_type = type(value)
    return value_type is tuple or value_type is frozenset
