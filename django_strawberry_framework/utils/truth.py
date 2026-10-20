"""Truthful identity reads: facts about an object read from the interpreter, never asked of it.

A consumer class can run arbitrary code in its body, its metaclass and its
hooks. It cannot misinform the framework about what it is, because every
identity fact the package records (a class's name, qualname, module, MRO,
bases, own namespace, and whether it subclasses a framework base) is read
here, from the interpreter's own type slots, instead of through attribute
lookup a metaclass property, ``__getattr__`` / ``__getattribute__``,
``__class__`` override, ``__instancecheck__`` / ``__subclasscheck__`` or a
metaclass ``__eq__`` / ``__hash__`` could intercept:

- ``type(obj)`` reads ``ob_type`` directly; ``obj.__class__`` is an attribute
  lookup an instance can override.
- ``type.__dict__["__name__"].__get__(cls)`` (and the ``__qualname__`` /
  ``__mro__`` / ``__bases__`` / ``__dict__`` slots beside it) is the base
  ``type`` getset descriptor, which reads the C slot and never consults the
  metaclass. ``type`` itself enforces that ``__name__`` and ``__qualname__``
  are exact ``str``. Functions, builtins and C descriptors are named the same
  way, through their own types' slots.
- Membership in a read MRO is tested by identity (``is``), never ``in`` or
  ``==``, so a metaclass ``__eq__`` cannot claim to be a framework base.
- Declared attributes (``static_attr`` / ``own_attr`` / ``instance_dict``) are
  looked up in the real MRO's raw namespaces, never through ``__getattr__`` /
  ``__getattribute__`` or a descriptor. ``inspect.getattr_static`` is not
  equivalent: it reads ``entry.__dict__`` by ordinary attribute lookup, which a
  metaclass ``__getattribute__`` intercepts.

Scope, exactly. No function here runs a consumer dunder method, property,
descriptor or metaclass hook, with one exception shared with the interpreter's
own attribute lookup: finding a name in a namespace dict compares it with any
planted non-``str`` key whose hash collides, which runs that key's ``__eq__``
(and propagates whatever it raises). That applies to every read that consults
a namespace: ``module`` / ``label`` of a class, ``static_attr``, ``own_attr``,
``instance_dict``, the name of a callable instance, and the class and scalar
spellings of ``render`` / ``text`` / ``describe``. The reads that consult no
namespace (``class_of``, ``is_type``, ``is_instance``, ``is_mapping_dict``,
``is_subclass``, ``is_exact``, ``mro``, ``bases``, ``class_dict``, ``kind``,
``stored_function``, and ``name`` / ``qualname`` of a class, function, builtin
or C descriptor) never raise and run no consumer code for any object. ``render`` /
``text`` / ``describe`` spell a builtin scalar through the builtin's own slot only
while its class still resolves that slot; any other object renders through its own ``__repr__`` /
``__str__``, which is consumer behaviour, and its exceptions propagate to the
schema's error policy like any other consumer hook's.

This module is the only place in the package allowed to touch identity
dunders directly; ``scripts/check_truthful_reads.py`` enforces that.
"""

from __future__ import annotations

import enum
import sys
import types
from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING, Generic, TypeAlias, TypeGuard, TypeVar, overload

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from typing_extensions import TypeIs

__all__ = (
    "IdentityMap",
    "bases",
    "class_dict",
    "class_of",
    "describe",
    "instance_dict",
    "instance_state",
    "is_exact",
    "is_instance",
    "is_mapping_dict",
    "is_subclass",
    "is_type",
    "kind",
    "label",
    "module",
    "mro",
    "name",
    "own_attr",
    "qualname",
    "render",
    "static_attr",
    "stored_function",
    "text",
)

# The interpreter's own slot getters, each declared under the checker over what it reads:
# ``type``'s getset descriptors (``type.__dict__["__name__"].__get__`` and the slots
# beside it), the function, builtin, bound-method, ``classmethod`` and ``staticmethod``
# slots, ``dict.get`` through the base slot (so a ``dict`` subclass namespace's own
# ``get`` never runs), the ``__name__`` / ``__objclass__`` / ``__get__`` slots of the C
# descriptor types, and a builtin scalar's own ``__repr__`` slot wrapper.
if TYPE_CHECKING:

    def _get_name(_cls: type[object], /) -> str: ...
    def _get_qualname(_cls: type[object], /) -> str: ...
    def _get_mro(_cls: type[object], /) -> tuple[type, ...]: ...
    def _get_bases(_cls: type[object], /) -> tuple[type, ...]: ...
    def _get_dict(_cls: type[object], /) -> types.MappingProxyType[str, object]: ...
    def _get_flags(_cls: type[object], /) -> int: ...
    def _get_module(_cls: type[object], /) -> object: ...
    def _get_function_name(_function: object, /) -> str: ...
    def _get_function_qualname(_function: object, /) -> str: ...
    def _get_function_module(_function: object, /) -> object: ...
    def _get_builtin_name(_builtin: object, /) -> str: ...
    def _get_builtin_self(_builtin: object, /) -> object: ...
    def _get_builtin_module(_builtin: object, /) -> object: ...
    def _get_method_func(_method: object, /) -> object: ...
    def _get_classmethod_func(_wrapper: object, /) -> object: ...
    def _get_staticmethod_func(_wrapper: object, /) -> object: ...
    def _dict_get(_namespace: dict[str, object], _key: str, _default: object, /) -> object: ...
    def _name_reader(_descriptor_type: type[object], /) -> Callable[[object], str]: ...
    def _objclass_reader(_descriptor_type: type[object], /) -> Callable[[object], type]: ...
    def _namespace_getter(
        _descriptor_type: type[object],
        /,
    ) -> Callable[[object, object], dict[str, object] | None]: ...
    def _repr_slot(_builtin: type[object], /) -> Callable[[object], str]: ...

else:
    _TYPE_SLOTS = type.__dict__
    _get_name = _TYPE_SLOTS["__name__"].__get__
    _get_qualname = _TYPE_SLOTS["__qualname__"].__get__
    _get_mro = _TYPE_SLOTS["__mro__"].__get__
    _get_bases = _TYPE_SLOTS["__bases__"].__get__
    _get_dict = _TYPE_SLOTS["__dict__"].__get__
    _get_flags = _TYPE_SLOTS["__flags__"].__get__
    _get_module = _TYPE_SLOTS["__module__"].__get__

    _FUNCTION_SLOTS = types.FunctionType.__dict__
    _get_function_name = _FUNCTION_SLOTS["__name__"].__get__
    _get_function_qualname = _FUNCTION_SLOTS["__qualname__"].__get__
    _get_function_module = _FUNCTION_SLOTS["__module__"].__get__

    _BUILTIN_SLOTS = types.BuiltinFunctionType.__dict__
    _get_builtin_name = _BUILTIN_SLOTS["__name__"].__get__
    _get_builtin_self = _BUILTIN_SLOTS["__self__"].__get__
    _get_builtin_module = _BUILTIN_SLOTS["__module__"].__get__

    _get_method_func = types.MethodType.__dict__["__func__"].__get__
    _get_classmethod_func = classmethod.__dict__["__func__"].__get__
    _get_staticmethod_func = staticmethod.__dict__["__func__"].__get__
    _dict_get = dict.get

    def _name_reader(descriptor_type: type[object]) -> Callable[[object], str]:
        return descriptor_type.__dict__["__name__"].__get__

    def _objclass_reader(descriptor_type: type[object]) -> Callable[[object], type]:
        return descriptor_type.__dict__["__objclass__"].__get__

    def _namespace_getter(
        descriptor_type: type[object],
    ) -> Callable[[object, object], dict[str, object] | None]:
        return _get_dict(descriptor_type)["__get__"]

    def _repr_slot(builtin: type[object]) -> Callable[[object], str]:
        return _mro_lookup(builtin, "__repr__")


_HEAPTYPE = 1 << 9

# C descriptors and slot wrappers: each carries its own name and defining class
# in C slots, read through the descriptor type's own getters. The name slot holds
# an exact ``str`` and the defining-class slot a class.
_DescriptorReader: TypeAlias = tuple[type, Callable[[object], str], Callable[[object], type]]
_DESCRIPTOR_READERS: tuple[_DescriptorReader, ...] = tuple(
    (descriptor_type, _name_reader(descriptor_type), _objclass_reader(descriptor_type))
    for descriptor_type in (
        types.MethodDescriptorType,
        types.ClassMethodDescriptorType,
        types.WrapperDescriptorType,
        types.MethodWrapperType,
        types.GetSetDescriptorType,
        types.MemberDescriptorType,
    )
)
# The two C descriptor types that can hold an instance ``__dict__``: a heap
# class's is a getset, a builtin such as ``SimpleNamespace`` or a module keeps it
# in a member slot. Python code cannot instantiate either.
_NAMESPACE_DESCRIPTOR_READERS = _DESCRIPTOR_READERS[-2:]

# ``EnumType.__repr__`` spells a ``Flag`` class ``<flag 'Name'>`` from 3.11 on.
_ENUM_TYPE_REPR = _get_dict(enum.EnumMeta)["__repr__"]
_FLAG_REPR_PREFIX = "<flag" if sys.version_info >= (3, 11) else "<enum"

_UNKNOWN_MODULE = "<unknown module>"
_ABSENT = object()


class _Unrendered(enum.Enum):
    """What ``_scalar_repr`` answers for a value it does not spell through a builtin slot."""

    OVERSIZED = enum.auto()
    NOT_SCALAR = enum.auto()


# log10(2): converts a bit length into a decimal digit count bound.
_LOG10_2 = 0.30102999566398120


_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")


def _is_in(candidate: object, classes: tuple[type, ...]) -> bool:
    """Whether ``candidate`` is one of ``classes`` by identity, never by ``__eq__``."""
    return any(candidate is entry for entry in classes)


def class_of(obj: object) -> type:
    """Return the real class of ``obj``: ``ob_type``, never the ``__class__`` attribute."""
    return type(obj)


def mro(cls: object) -> tuple[type, ...]:
    """Return the real MRO of ``cls`` (of ``cls``'s class when ``cls`` is not a class)."""
    found: tuple[type, ...] = _get_mro(cls) if is_type(cls) else _get_mro(type(cls))
    return found


def is_type(obj: object) -> TypeIs[type[object]]:
    """Whether ``obj`` is a class, decided by its real metaclass chain."""
    return _is_in(type, _get_mro(type(obj)))


# The checker solves ``type[_T]`` from a bare generic class (``dict``, ``list``,
# ``classmethod``) with ``Unknown`` type arguments, so the builtin containers and
# ``classmethod`` the package reads consumer values against narrow through their own
# overloads to a container of ``object``, which the caller then checks member by
# member (``is_mapping_dict`` is the ``dict`` check for a value already typed as a
# ``Mapping``, keeping its key and value types). A subclass of one of them
# (``OrderedDict``) matches its base's overload and narrows to the base's form.
@overload
def is_instance(obj: object, cls: type[dict[object, object]]) -> TypeIs[dict[object, object]]: ...


@overload
def is_instance(obj: object, cls: type[list[object]]) -> TypeIs[list[object]]: ...


@overload
def is_instance(obj: object, cls: type[tuple[object, ...]]) -> TypeIs[tuple[object, ...]]: ...


@overload
def is_instance(obj: object, cls: type[set[object]]) -> TypeIs[set[object]]: ...


@overload
def is_instance(obj: object, cls: type[frozenset[object]]) -> TypeIs[frozenset[object]]: ...


@overload
def is_instance(
    obj: object,
    cls: type[classmethod[object, ..., object]],
) -> TypeIs[classmethod[object, ..., object]]: ...


@overload
def is_instance(obj: object, cls: type[_T]) -> TypeIs[_T]: ...


def is_instance(obj: object, cls: type[object]) -> bool:
    """``isinstance`` by the real class; no ``__class__`` or ``__instancecheck__`` runs."""
    return _is_in(cls, _get_mro(type(obj)))


def is_mapping_dict(obj: Mapping[_K, _V] | None) -> TypeIs[dict[_K, _V]]:
    """``is_instance(obj, dict)`` for a value typed as a ``Mapping``, keeping its key and value types."""
    return _is_in(dict, _get_mro(type(obj)))


def is_subclass(sub: object, cls: type[_T]) -> TypeIs[type[_T]]:
    """``issubclass`` by the real MRO; ``False`` for a non-class, never a ``TypeError``."""
    return is_type(sub) and _is_in(cls, _get_mro(sub))


# ``is_exact`` narrows the builtin wrappers and containers it is asked about to their
# ``object`` forms for the same reason ``is_instance`` does.
@overload
def is_exact(obj: object, cls: type[list[object]]) -> TypeGuard[list[object]]: ...


@overload
def is_exact(
    obj: object,
    cls: type[staticmethod[..., object]],
) -> TypeGuard[staticmethod[..., object]]: ...


@overload
def is_exact(obj: object, cls: type[_T]) -> TypeGuard[_T]: ...


def is_exact(obj: object, cls: type[object]) -> bool:
    """Whether ``obj``'s real class is exactly ``cls`` (no subclass accepted).

    A ``TypeGuard``, not a ``TypeIs``: a ``False`` answer does not mean ``obj``
    is not a ``cls``, since a subclass instance also answers ``False``.
    """
    return type(obj) is cls


def bases(cls: object) -> tuple[type, ...]:
    """Return the real ``__bases__`` of ``cls``; ``()`` for a non-class."""
    found: tuple[type, ...] = _get_bases(cls) if is_type(cls) else ()
    return found


def class_dict(cls: object) -> types.MappingProxyType[str, object]:
    """Return the real, read-only own namespace of ``cls``; empty for a non-class."""
    found: types.MappingProxyType[str, object] = (
        _get_dict(cls) if is_type(cls) else types.MappingProxyType({})
    )
    return found


def _nonempty(value: str, fallback: str) -> str:
    return value or fallback


def _mro_lookup(cls: type, attr: str) -> object:
    """``attr`` from the first real-MRO namespace of the class ``cls``, or ``_ABSENT``.

    The MRO and every namespace are read through the ``type`` slots, so no
    metaclass hook runs. The one thing this cannot exclude is the lookup's own
    key comparison: a non-``str`` key planted in a namespace whose hash equals
    ``hash(attr)`` is compared with ``attr``, which runs that key's ``__eq__``
    (CPython's own attribute lookup walks the same dicts and has the same
    property); whatever it raises propagates, and a key that claims equality
    answers for ``attr``.
    """
    for entry in _get_mro(cls):
        namespace = _get_dict(entry)
        if attr in namespace:
            return namespace[attr]
    return _ABSENT


def _descriptor_parts(obj: object) -> tuple[str, type] | None:
    """``(name, defining class)`` of a C descriptor or slot wrapper; ``None`` otherwise."""
    obj_type = type(obj)
    for descriptor_type, get_name, get_objclass in _DESCRIPTOR_READERS:
        if obj_type is descriptor_type:
            return get_name(obj), get_objclass(obj)
    return None


def _builtin_owner(obj: object) -> type | None:
    """Return the class a bound builtin method belongs to; ``None`` for a module-level builtin.

    The class CPython's own ``__qualname__`` names (the bound object when it is
    a class, else its class), found from the builtin's ``__self__`` slot. The
    builtin's ``__qualname__`` getter is not used: it asks that class for its
    ``__qualname__`` by attribute lookup, which a metaclass intercepts.
    """
    bound: object = _get_builtin_self(obj)
    if bound is None or is_instance(bound, types.ModuleType):
        return None
    return bound if is_type(bound) else type(bound)


def _declared_str(obj: object, attr: str) -> str | None:
    """Return a callable instance's stored ``attr`` when it is an exact non-empty ``str``.

    ``functools.update_wrapper`` (behind ``lru_cache``, ``wraps`` and their
    kind) stores the wrapped callable's ``__name__`` / ``__qualname__`` /
    ``__module__`` on the wrapper instance; ``static_attr`` reads them the way
    attribute lookup would find them, without running any of it.
    """
    if not callable(obj):
        return None
    value = static_attr(obj, attr, None)
    return value if type(value) is str and value else None


def name(obj: object) -> str:
    """Return the declared name of a class or callable; the class's name for any other object.

    A class, function, builtin, bound method, C descriptor or slot wrapper names
    itself from its own slots; a callable instance carrying a stored exact
    ``str`` ``__name__`` (a ``functools.update_wrapper`` wrapper) names itself by
    it; any other value is named by its real class, so the result is always a
    non-empty exact ``str``.
    """
    if is_type(obj):
        return _nonempty(_get_name(obj), _nonempty(_get_name(type(obj)), "object"))
    obj_type = type(obj)
    if obj_type is types.FunctionType:
        return _nonempty(_get_function_name(obj), "function")
    if obj_type is types.BuiltinFunctionType:
        return _nonempty(_get_builtin_name(obj), "builtin_function_or_method")
    if obj_type is types.MethodType:
        return name(_get_method_func(obj))
    parts = _descriptor_parts(obj)
    if parts is not None:
        return _nonempty(parts[0], _get_name(obj_type))
    declared = _declared_str(obj, "__name__")
    if declared is not None:
        return declared
    return _nonempty(_get_name(obj_type), "object")


def qualname(obj: object) -> str:
    """Return the declared qualname of a class or callable; the class's qualname otherwise.

    A bound builtin and a C descriptor are qualified by their owning class's
    truthful qualname, as CPython spells them (``str.join``, ``list.append``).
    """
    if is_type(obj):
        return _nonempty(_get_qualname(obj), name(obj))
    obj_type = type(obj)
    if obj_type is types.FunctionType:
        return _nonempty(_get_function_qualname(obj), name(obj))
    if obj_type is types.BuiltinFunctionType:
        owner = _builtin_owner(obj)
        return name(obj) if owner is None else f"{qualname(owner)}.{name(obj)}"
    if obj_type is types.MethodType:
        return qualname(_get_method_func(obj))
    parts = _descriptor_parts(obj)
    if parts is not None:
        return f"{qualname(parts[1])}.{name(obj)}"
    declared = _declared_str(obj, "__qualname__")
    if declared is not None:
        return declared
    return _nonempty(_get_qualname(obj_type), name(obj_type))


def _class_module(cls: type) -> object:
    """Return the raw ``__module__`` of the class ``cls``, as ``type.__module__`` would read it."""
    # A heap class keeps ``__module__`` in its own namespace, where the body may
    # have put anything; a static builtin class derives it from its C-level
    # name, which the ``type`` slot reads without dispatch.
    if _get_flags(cls) & _HEAPTYPE:
        return _get_dict(cls).get("__module__", None)
    return _get_module(cls)


def module(obj: object) -> str:
    """Return the module a class or callable was defined in; its class's module otherwise.

    A bound builtin without a module of its own (``[].append``) and a C
    descriptor (``str.join``) take their owning class's module. ``__module__``
    is body-controlled (a class body can assign anything to it), so a value
    that is not an exact non-empty ``str`` reads as ``"<unknown module>"``
    instead of being trusted or rendered.
    """
    obj_type = type(obj)
    if is_type(obj):
        value = _class_module(obj)
    elif obj_type is types.FunctionType:
        value = _get_function_module(obj)
    elif obj_type is types.MethodType:
        return module(_get_method_func(obj))
    elif obj_type is types.BuiltinFunctionType:
        value = _get_builtin_module(obj)
        owner = _builtin_owner(obj)
        if owner is not None and not (type(value) is str and value):
            return module(owner)
    else:
        parts = _descriptor_parts(obj)
        if parts is not None:
            return module(parts[1])
        value = _declared_str(obj, "__module__")
        if value is None:
            value = _class_module(obj_type)
    return value if type(value) is str and value else _UNKNOWN_MODULE


def label(obj: object) -> str:
    """``module.qualname`` of a class or callable (of the object's class otherwise)."""
    return f"{module(obj)}.{qualname(obj)}"


def kind(value: object) -> str:
    """Return the name identifying ``value``'s kind for an error message's ``got <kind>``.

    A class names itself (reporting its metaclass would put ``ModelBase`` in
    front of every Django model and ``type`` in front of every plain class);
    any other value is named by its real class.
    """
    if is_type(value):
        return name(value)
    return _nonempty(_get_name(type(value)), "object")


def _is_data_descriptor(value: object) -> bool:
    value_type = type(value)
    return (
        _mro_lookup(value_type, "__set__") is not _ABSENT
        or _mro_lookup(value_type, "__delete__") is not _ABSENT
    )


def _namespace_reader(
    descriptor: object,
    obj_mro: tuple[type, ...],
) -> Callable[[object, object], dict[str, object] | None] | None:
    """``descriptor``'s ``__get__`` when it is a genuine instance-``__dict__`` slot, else ``None``.

    Genuine means a C getset / member descriptor named ``__dict__`` whose
    defining class is in the instance's real MRO, so reading it cannot raise.
    A foreign slot (another class's ``__dict__``, a ``__slots__`` member, a
    builtin's getset such as ``int.real``) assigned to ``__dict__`` is not one.
    """
    descriptor_type = type(descriptor)
    for reader_type, get_name, get_objclass in _NAMESPACE_DESCRIPTOR_READERS:
        if descriptor_type is reader_type:
            if get_name(descriptor) == "__dict__" and _is_in(get_objclass(descriptor), obj_mro):
                return _namespace_getter(descriptor_type)
            return None
    return None


def instance_dict(obj: object) -> dict[str, object] | None:
    """Return the real instance ``__dict__`` of ``obj`` (the live dict, not a copy), or ``None``.

    Read through the first genuine ``__dict__`` getset / member descriptor in
    ``obj``'s real MRO, which is the storage attribute lookup itself uses; a
    class-level ``__dict__`` property or foreign descriptor is skipped and never
    runs, so the answer is the real namespace even when ``obj.__dict__`` would
    raise or lie. Returns ``None`` (rather than raising) when no class in the real MRO
    carries a genuine ``__dict__`` slot: ``object()``, an ``int``, a slotted
    instance, and a class whose only ``__dict__`` entry is a replacement (a
    property, another class's slot) with no genuine one on a base.
    """
    obj_mro = _get_mro(type(obj))
    for entry in obj_mro:
        descriptor = _get_dict(entry).get("__dict__", _ABSENT)
        if descriptor is _ABSENT:
            continue
        reader = _namespace_reader(descriptor, obj_mro)
        if reader is not None:
            namespace = reader(descriptor, obj)
            # A namespace maps attribute names; a non-``str`` key a consumer plants in
            # it is only ever looked up by an attribute name, never read as one.
            return namespace if is_instance(namespace, dict) else None
    return None


def instance_state(obj: object) -> dict[str, object]:
    """``instance_dict(obj)`` for an object whose class keeps a real instance ``__dict__``.

    For the reads that are sound only on such an object (a Django ``Query``,
    ``QuerySet``, ``Prefetch`` or expression node): the answer is typed as the
    dict itself, and an object without one is a ``TypeError`` here rather than
    a ``None`` failing later at whatever the caller does with it.
    """
    namespace = instance_dict(obj)
    if namespace is None:
        raise TypeError(f"a {kind(obj)} carries no instance __dict__")
    return namespace


def static_attr(obj: object, attr: str, default: object = None) -> object:
    """Read ``obj.<attr>`` from the real namespaces without running any consumer code.

    Walks the real MRO and namespace slots (for a class: its own MRO, then its
    metaclass's; for an instance: its ``__dict__``, unless a data descriptor on
    its class takes precedence, then its class's MRO) and never invokes
    ``__getattr__`` / ``__getattribute__``, a metaclass property, or a
    descriptor. The result is the stored object: a ``property`` /
    ``classmethod`` / ``staticmethod`` comes back as the descriptor itself,
    which a caller that needs a plain value then rejects by its exact type.
    ``inspect.getattr_static`` is not a substitute: it reads ``entry.__dict__``
    through ordinary attribute lookup, which a metaclass ``__getattribute__``
    intercepts.
    """
    if is_type(obj):
        found = _mro_lookup(obj, attr)
        if found is _ABSENT:
            found = _mro_lookup(type(obj), attr)
        return default if found is _ABSENT else found
    class_value = _mro_lookup(type(obj), attr)
    if class_value is _ABSENT or not _is_data_descriptor(class_value):
        namespace = instance_dict(obj)
        if namespace is not None:
            found = _dict_get(namespace, attr, _ABSENT)
            if found is not _ABSENT:
                return found
    return default if class_value is _ABSENT else class_value


def own_attr(cls: object, attr: str, default: object = None) -> object:
    """``attr`` from the first real-MRO namespace of ``cls`` that defines it.

    Unlike ``static_attr`` the metaclass is never consulted, so the answer is
    what the class body (or a base's) declared.
    """
    if not is_type(cls):
        return default
    found = _mro_lookup(cls, attr)
    return default if found is _ABSENT else found


def stored_function(value: object) -> object:
    """Return the function a stored builtin method wrapper holds; any other value unchanged.

    ``value`` is a namespace entry as ``static_attr`` returns it. An exact
    ``classmethod``, ``staticmethod`` or bound method (``MethodType``) answers
    its ``__func__`` slot, read through the wrapper type's own getter; a
    subclass of one of them, a plain function and every other value come back
    as given. Two reads naming the same function therefore compare by identity
    whatever wrapper each one sits in. Unlike ``inspect.unwrap`` it never
    follows ``__wrapped__``, and unlike ``getattr`` it binds no descriptor.
    """
    value_type = type(value)
    if value_type is classmethod:
        return _get_classmethod_func(value)
    if value_type is staticmethod:
        return _get_staticmethod_func(value)
    if value_type is types.MethodType:
        return _get_method_func(value)
    return value


def _class_repr(cls: type) -> str:
    """``repr(cls)`` as the class's metaclass spells it, built from truthful reads.

    An ``Enum`` class whose metaclass resolves ``EnumType.__repr__`` takes that
    spelling (``<enum 'Name'>``; ``<flag 'Name'>`` for a ``Flag`` on 3.11+).
    Every other class takes ``type.__repr__``'s: ``<class 'module.qualname'>``,
    or ``<class 'name'>`` when the module is ``builtins`` or not a ``str``. A
    metaclass's own ``__repr__`` never runs.
    """
    if _mro_lookup(type(cls), "__repr__") is _ENUM_TYPE_REPR:
        prefix = _FLAG_REPR_PREFIX if _is_in(enum.Flag, _get_mro(cls)) else "<enum"
        return f"{prefix} {str.__repr__(_get_name(cls))}>"
    owner = _class_module(cls)
    if is_instance(owner, str) and str.__str__(owner) != "builtins":
        return f"<class '{str.__str__(owner)}.{_get_qualname(cls)}'>"
    return f"<class '{_get_name(cls)}'>"


def _oversized_int(value: int) -> bool:
    """Whether rendering ``value`` in decimal would exceed the interpreter's digit limit.

    CPython refuses to stringify an int with more than
    ``sys.get_int_max_str_digits()`` decimal digits. The limit arrived in a
    patch release (3.10.7, part of the CVE-2020-10735 fix), so its presence is
    read from ``sys`` itself, never inferred from the minor version. The bound
    is decided from the bit length before any conversion is attempted; the
    one-digit band the bit length cannot resolve counts as oversized.
    """
    limit = sys.get_int_max_str_digits() if hasattr(sys, "get_int_max_str_digits") else 0
    if not limit:
        return False
    return int.bit_length(value) * _LOG10_2 + 1 > limit


# Builtin value types whose repr is computed by the builtin itself, reading only
# the value's own storage, with the ``__repr__`` / ``__str__`` each resolves.
# ``bool`` precedes ``int`` so a bool is spelled by its own slot. Containers are
# deliberately absent: their builtin repr recurses into the elements' own
# ``__repr__``, so they render through ``repr`` like any other object.
# Each listed builtin resolves ``__repr__`` to its own C slot wrapper, which
# takes the value and returns an exact ``str``; ``__str__`` is only compared by
# identity.
_SCALAR_SLOTS: tuple[tuple[type, Callable[[object], str], object], ...] = tuple(
    (builtin, _repr_slot(builtin), _mro_lookup(builtin, "__str__"))
    for builtin in (
        bool,
        int,
        float,
        complex,
        str,
        bytes,
        type(None),
    )
)


def _scalar_repr(value: object, *, as_text: bool = False) -> str | _Unrendered:
    """Return the builtin-slot spelling of a builtin scalar, ``OVERSIZED``, or ``NOT_SCALAR``.

    A subclass is spelled through the builtin's slot only while its class still
    resolves the builtin's own ``__repr__`` (and, for ``as_text``, ``__str__``),
    which is exactly the spelling ``repr`` / ``str`` would produce. A subclass
    that overrides either (an ``IntEnum`` / ``TextChoices`` member, a consumer
    subclass) is ``NOT_SCALAR``: its rendering is its own behaviour.
    """
    value_type = type(value)
    value_mro = _get_mro(value_type)
    for builtin, builtin_repr, builtin_str in _SCALAR_SLOTS:
        if _is_in(builtin, value_mro):
            if value_type is not builtin and (
                _mro_lookup(value_type, "__repr__") is not builtin_repr
                or (as_text and _mro_lookup(value_type, "__str__") is not builtin_str)
            ):
                return _Unrendered.NOT_SCALAR
            if builtin is int and is_instance(value, int) and _oversized_int(value):
                return _Unrendered.OVERSIZED
            return str.__str__(builtin_repr(value))
    return _Unrendered.NOT_SCALAR


def render(value: object) -> str:
    """``repr(value)`` as an exact ``str``; truthful and total for builtin scalars.

    A builtin scalar (or a subclass that keeps the builtin's ``__repr__``)
    renders through that slot; an int too large to render becomes
    ``<unprintable int>``. A class renders as its metaclass spells it (see
    ``_class_repr``), from truthful reads. Anything else, including a scalar
    subclass with its own ``__repr__`` such as an ``IntEnum`` member, renders
    through its own ``__repr__``: that is the object's behaviour, and whatever
    it raises propagates.
    """
    if is_type(value):
        return _class_repr(value)
    scalar = _scalar_repr(value)
    if scalar is _Unrendered.OVERSIZED:
        return f"<unprintable {kind(value)}>"
    if scalar is not _Unrendered.NOT_SCALAR:
        return scalar
    return str.__str__(repr(value))


def text(value: object, fallback: str = "") -> str:
    """``str(value)`` as an exact ``str``; ``fallback`` when the render is empty.

    A ``str`` (or subclass) is copied through the base ``str`` slot, so an
    overridden ``__str__`` / ``__format__`` / ``__len__`` never runs; a class
    renders like ``render``; another builtin scalar (or a subclass keeping the
    builtin's ``__repr__`` and ``__str__``) renders through the builtin slot.
    Anything else renders through its own ``__str__``, whose exceptions
    propagate.
    """
    if is_instance(value, str):
        rendered = str.__str__(value)
    elif is_type(value):
        rendered = _class_repr(value)
    else:
        scalar = _scalar_repr(value, as_text=True)
        if scalar is _Unrendered.OVERSIZED:
            rendered = f"<unprintable {kind(value)}>"
        elif scalar is not _Unrendered.NOT_SCALAR:
            rendered = scalar
        else:
            rendered = str.__str__(str(value))
    return rendered or fallback


def describe(value: object) -> str:
    """Return an error message's ``got <this>`` tail: ``"<kind> <render>"``.

    An int too large to render reads ``"an unprintable int"`` so the prose
    around the fragment stays grammatical.
    """
    if not is_type(value) and _scalar_repr(value) is _Unrendered.OVERSIZED:
        return f"an unprintable {kind(value)}"
    return f"{kind(value)} {render(value)}"


_D = TypeVar("_D")


class IdentityMap(Generic[_K, _V]):
    """A mapping keyed by object identity, never by the key's ``__hash__`` / ``__eq__``.

    A class registry keyed by the class itself would call the metaclass's
    ``__hash__`` on every insert and its ``__eq__`` on every collision, letting
    a consumer class claim another class's slot. Keys here are ``id(key)``
    and each entry holds the key object, so the id cannot be recycled while
    the entry lives. ``_K`` types the keys stored and handed back; a lookup
    takes any object, since an identity miss is an answer, not an error.
    """

    __slots__: tuple[str, ...] = ("_entries",)

    def __init__(self) -> None:
        """Start with no entries."""
        self._entries: dict[int, tuple[_K, _V]] = {}

    def __contains__(self, key: object) -> bool:
        """Whether ``key`` (this very object) has an entry."""
        return id(key) in self._entries

    def __len__(self) -> int:
        """Return the number of entries."""
        return len(self._entries)

    def __iter__(self) -> Iterator[_K]:
        """Iterate over a snapshot of the keys."""
        return (key for key, _value in list(self._entries.values()))

    @overload
    def get(self, key: object) -> _V | None: ...

    @overload
    def get(self, key: object, default: _D) -> _V | _D: ...

    def get(self, key: object, default: object = None) -> object:
        """Return the value stored for ``key``, or ``default``."""
        entry = self._entries.get(id(key))
        return default if entry is None else entry[1]

    def __getitem__(self, key: object) -> _V:
        """Return the value for ``key``; ``KeyError`` naming its label when absent."""
        entry = self._entries.get(id(key))
        if entry is None:
            raise KeyError(label(key) if is_type(key) else kind(key))
        return entry[1]

    def __setitem__(self, key: _K, value: _V) -> None:
        """Store ``value`` for ``key`` by identity."""
        self._entries[id(key)] = (key, value)

    def __delitem__(self, key: object) -> None:
        """Remove ``key``; ``KeyError`` naming its label when absent."""
        if self._entries.pop(id(key), None) is None:
            raise KeyError(label(key) if is_type(key) else kind(key))

    @overload
    def pop(self, key: object) -> _V | None: ...

    @overload
    def pop(self, key: object, default: _D) -> _V | _D: ...

    def pop(self, key: object, default: object = None) -> object:
        """Remove ``key`` and return its value, or ``default`` when absent."""
        entry = self._entries.pop(id(key), None)
        return default if entry is None else entry[1]

    def setdefault(self, key: _K, default: _V) -> _V:
        """Return the value for ``key``, storing ``default`` first when absent."""
        entry = self._entries.get(id(key))
        if entry is None:
            self._entries[id(key)] = (key, default)
            return default
        return entry[1]

    def items(self) -> list[tuple[_K, _V]]:
        """Return a snapshot of ``(key, value)`` pairs in insertion order."""
        return list(self._entries.values())

    def keys(self) -> list[_K]:
        """Return a snapshot of the keys in insertion order."""
        return [key for key, _value in self._entries.values()]

    def values(self) -> list[_V]:
        """Return a snapshot of the values in insertion order."""
        return [value for _key, value in self._entries.values()]

    def clear(self) -> None:
        """Remove every entry."""
        self._entries.clear()
