"""Tests for ``django_strawberry_framework/utils/truth.py``: identity reads a consumer cannot fake.

The hostile bestiary lives here once, against the module, instead of once per
caller. Each attack shape lives on its own class, and each is paired with a
negative control proving the ordinary read of THAT class is intercepted by
THAT attack (the attack's own marker lands in ``DISPATCHED``, or the read
returns the attack's lie), while the truthful read of the same class returns
the real answer and dispatches nothing. A pass therefore means the truthful
read defeated a live attack rather than a harmless double.
"""

from __future__ import annotations

import abc
import enum
import functools
import inspect
import math
import sys
import types
import warnings
from collections.abc import Callable, Iterable, Iterator, Sized
from typing import NoReturn, Protocol

import pytest
from django.db import models
from django.utils.functional import SimpleLazyObject, lazy
from typing_extensions import override

from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    call_method,
    is_dict,
    read_attr,
    require,
)
from django_strawberry_framework.utils.typing import object_result
from tests._idioms import STR_ENUM

DISPATCHED: list[str] = []
#: ``object.__getattribute__``: the instance read past a class's own ``__getattribute__``.
_object_getattribute: Callable[[object, str], object] = object.__getattribute__
#: ``type.__getattribute__``: the class read past a metaclass's own ``__getattribute__``.
_type_getattribute: Callable[[type, str], object] = type.__getattribute__


class _Base:
    """A framework-owned base every attacked class really does inherit."""

    stored: str


class _Unrelated:
    """A framework-owned base no attacked class inherits."""


# Lies a class-level attack returns for each identity dunder. ``__qualname__``
# cannot be a metaclass property (``type()`` requires the namespace entry to be
# a ``str``), so only a ``__getattribute__`` attack can lie about it.
_IDENTITY_LIES: dict[str, object] = {
    "__name__": "Liar",
    "__qualname__": "Liar",
    "__module__": "liar.module",
    "__mro__": (_Unrelated, object),
    "__bases__": (_Unrelated,),
    "__dict__": types.MappingProxyType({"marker": "lie"}),
}
_PROPERTY_DUNDERS = (
    "__name__",
    "__module__",
    "__mro__",
    "__bases__",
    "__dict__",
)


class _RaisingGetattributeMeta(type):
    """A metaclass whose ``__getattribute__`` raises for every attribute."""

    @override
    def __getattribute__(cls, attr: str) -> NoReturn:
        DISPATCHED.append(f"getattribute:{attr}")
        raise RuntimeError(attr)


class _RaisingGetattribute(_Base, metaclass=_RaisingGetattributeMeta):
    """A class every ordinary attribute read of which raises."""

    marker = "declared"


class _LyingGetattributeMeta(type):
    """A metaclass whose ``__getattribute__`` lies about every identity dunder."""

    @override
    def __getattribute__(cls, attr: str) -> object:
        if attr in _IDENTITY_LIES:
            DISPATCHED.append(f"lie:{attr}")
            return _IDENTITY_LIES[attr]
        return _type_getattribute(cls, attr)


class _LyingGetattribute(_Base, metaclass=_LyingGetattributeMeta):
    """A class whose ordinary identity reads all return lies."""

    marker = "declared"


class _LyingChecksMeta(type):
    """A metaclass whose ``__instancecheck__`` / ``__subclasscheck__`` claim everything."""

    @override
    def __instancecheck__(cls, obj: object) -> bool:
        DISPATCHED.append("instancecheck")
        return True

    @override
    def __subclasscheck__(cls, sub: type) -> bool:
        DISPATCHED.append("subclasscheck")
        return True


class _LyingChecks(_Base, metaclass=_LyingChecksMeta):
    """A class that claims every object and every class as its own."""


class _EqualsEverythingMeta(type):
    """A metaclass whose ``__eq__`` claims equality with every class."""

    @override
    def __eq__(cls, other: object) -> bool:
        DISPATCHED.append("eq")
        return True

    @override
    def __hash__(cls) -> int:
        DISPATCHED.append("hash")
        return 0


class _EqualsEverything(_Base, metaclass=_EqualsEverythingMeta):
    """A class that compares equal to (and hashes like) every other class."""


class _RaisingReprMeta(type):
    """A metaclass whose ``__repr__`` raises."""

    @override
    def __repr__(cls) -> str:
        DISPATCHED.append("repr")
        raise RuntimeError("__repr__")


class _RaisingRepr(_Base, metaclass=_RaisingReprMeta):
    """A class whose ``repr`` raises."""


def _spoofed_module(_self: object) -> str:
    return "spoofed"


class _NonStrModule(_Base):
    """A class whose body assigns a non-``str`` ``__module__``."""

    # basedpyright: a non-``str`` ``__module__`` is the hostile class body under test
    __module__ = property(_spoofed_module)  # pyright: ignore[reportAssignmentType]


class _ClassRaiser:
    """An instance whose ``__class__`` raises."""

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__`` that raises: the hostile input
    def __class__(self) -> NoReturn:  # pyright: ignore[reportIncompatibleMethodOverride]
        DISPATCHED.append("class")
        raise RuntimeError("__class__")


class _ClassClaimer:
    """An instance whose ``__class__`` claims to be ``int``."""

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__``: the forged type is the hostile input
    def __class__(self) -> type:  # pyright: ignore[reportIncompatibleMethodOverride]
        DISPATCHED.append("class")
        return int


class _GetattributeTrap:
    """An instance whose ``__getattribute__`` raises for every attribute."""

    stored = "class-value"

    @override
    def __getattribute__(self, attr: str) -> NoReturn:
        DISPATCHED.append(f"instance-getattribute:{attr}")
        raise RuntimeError(attr)


class _GetattrTrap:
    """An instance whose ``__getattr__`` raises for every attribute it lacks."""

    stored = "class-value"

    def __getattr__(self, attr: str) -> NoReturn:
        DISPATCHED.append(f"instance-getattr:{attr}")
        raise RuntimeError(attr)


class _DictRaiser:
    """An instance whose class replaces ``__dict__`` with a raising property."""

    @property
    @override
    # basedpyright: deliberately a raising ``__dict__`` property: the hostile input
    def __dict__(self) -> NoReturn:  # pyright: ignore[reportIncompatibleVariableOverride]
        DISPATCHED.append("dict")
        raise RuntimeError("__dict__")


class _DictBase:
    """A plain base whose genuine ``__dict__`` slot its subclasses inherit."""


class _DictLiar(_DictBase):
    """An instance whose class shadows the inherited ``__dict__`` with a lying property."""

    stored: str

    @property
    @override
    # basedpyright: deliberately a lying ``__dict__`` property: the hostile input
    def __dict__(self) -> dict[str, object]:  # pyright: ignore[reportIncompatibleVariableOverride]
        DISPATCHED.append("dict")
        return {"stored": "lie"}


class _Slotted:
    """A slotted class: its instances carry no ``__dict__``."""

    __slots__ = ("x",)


# Descriptors that are not this class's ``__dict__`` slot, assigned to ``__dict__``:
# a ``__slots__`` member, a builtin getset, and slots genuinely named ``__dict__``
# whose defining class is foreign (a heap class's getset, ``SimpleNamespace``'s member).
_FOREIGN_DICT_DESCRIPTORS = {
    "slot-member": truth.class_dict(_Slotted)["x"],
    "builtin-getset": truth.class_dict(int)["real"],
    "foreign-class-getset": truth.class_dict(_Unrelated)["__dict__"],
    "foreign-builtin-member": truth.class_dict(types.SimpleNamespace)["__dict__"],
}


class _HostileStr(str):
    """A ``str`` subclass whose rendering dunders all raise."""

    @override
    def __str__(self) -> str:
        raise RuntimeError("__str__")

    @override
    def __repr__(self) -> str:
        raise RuntimeError("__repr__")

    @override
    def __format__(self, spec: str) -> str:
        raise RuntimeError("__format__")

    @override
    def __len__(self) -> int:
        raise RuntimeError("__len__")


class _HostileInt(int):
    """An ``int`` subclass whose ``__repr__`` raises."""

    @override
    def __repr__(self) -> str:
        raise RuntimeError("__repr__")


class _PlainInt(int):
    """An ``int`` subclass that keeps the builtin rendering."""


class _OwnStrInt(int):
    """An ``int`` subclass that keeps the builtin ``__repr__`` but defines ``__str__``."""

    @override
    def __str__(self) -> str:
        return "own"


class _Color(enum.Enum):
    RED = 1


class _Shade(enum.Flag):
    DARK = 1


class _Level(enum.IntEnum):
    LOW = 1


class _Named(str, enum.Enum):
    ALPHA = "a"


class _Strategy(models.TextChoices):
    BOGUS = "bogus", "Bogus"


class _CollidingKey:
    """A namespace key whose hash collides with ``__module__`` and whose ``__eq__`` can raise."""

    armed = False

    @override
    def __hash__(self) -> int:
        return hash("__module__")

    @override
    def __eq__(self, other: object) -> bool:
        if _CollidingKey.armed:
            DISPATCHED.append("planted-eq")
            raise RuntimeError("planted key compared")
        return False


def _plain_function() -> None:
    """A module-level function."""


@functools.lru_cache
def _cached_function() -> None:
    """A module-level function behind ``functools.lru_cache``."""


def _property_attacked_class(dunder: str, *, raising: bool) -> type:
    """A class whose metaclass defines ``dunder`` as a property that lies or raises."""

    def read(_cls: type) -> object:
        DISPATCHED.append(f"property:{dunder}")
        if raising:
            raise RuntimeError(dunder)
        return _IDENTITY_LIES[dunder]

    meta = type(f"_Property{dunder}Meta", (type,), {dunder: property(read)})
    return meta("_PropertyAttacked", (_Base,), {"marker": "declared"})


def _foreign_dict_class(descriptor: object, *, base: type) -> type[object]:
    return type("_ForeignDict", (base,), {"__dict__": descriptor})


@pytest.fixture(autouse=True)
def _reset_dispatched() -> Iterator[None]:
    DISPATCHED.clear()
    yield
    DISPATCHED.clear()


def _assert_class_identity(cls: type, expected_name: str, expected_module: str) -> None:
    assert truth.name(cls) == expected_name
    assert truth.qualname(cls) == expected_name
    assert truth.module(cls) == expected_module
    assert truth.label(cls) == f"{expected_module}.{expected_name}"
    assert truth.kind(cls) == expected_name
    assert truth.mro(cls) == (cls, _Base, object)
    assert truth.bases(cls) == (_Base,)
    assert truth.class_dict(cls)["marker"] == "declared"
    assert truth.static_attr(cls, "marker") == "declared"
    assert truth.mro_attr(cls, "marker") == "declared"
    assert truth.render(cls) == f"<class '{expected_module}.{expected_name}'>"
    assert truth.is_subclass(cls, _Base) is True
    assert truth.is_subclass(cls, _Unrelated) is False


# --- class-level attacks ---


@pytest.mark.parametrize(
    "attr",
    [
        "__name__",
        "__qualname__",
        "__module__",
        "__mro__",
        "__bases__",
        "__dict__",
        "marker",
    ],
)
def test_raising_getattribute_intercepts_the_ordinary_read(attr: str) -> None:
    with pytest.raises(RuntimeError, match=attr):
        getattr(_RaisingGetattribute, attr)
    assert [f"getattribute:{attr}"] == DISPATCHED


def test_raising_getattribute_intercepts_getattr_static() -> None:
    with pytest.raises(RuntimeError):
        inspect.getattr_static(_RaisingGetattribute, "marker")
    assert DISPATCHED == ["getattribute:__dict__"]


def test_raising_getattribute_never_reaches_the_truthful_reads() -> None:
    _assert_class_identity(_RaisingGetattribute, "_RaisingGetattribute", __name__)
    assert DISPATCHED == []


@pytest.mark.parametrize("attr", sorted(_IDENTITY_LIES))
def test_lying_getattribute_intercepts_the_ordinary_read(attr: str) -> None:
    assert getattr(_LyingGetattribute, attr) is _IDENTITY_LIES[attr]
    assert [f"lie:{attr}"] == DISPATCHED


def test_lying_getattribute_intercepts_getattr_static() -> None:
    assert inspect.getattr_static(_LyingGetattribute, "marker") == "lie"
    assert "lie:__dict__" in DISPATCHED


def test_lying_getattribute_never_reaches_the_truthful_reads() -> None:
    _assert_class_identity(_LyingGetattribute, "_LyingGetattribute", __name__)
    assert DISPATCHED == []


@pytest.mark.parametrize("raising", [False, True], ids=["lying", "raising"])
@pytest.mark.parametrize("dunder", _PROPERTY_DUNDERS)
def test_metaclass_property_attack_on_each_identity_dunder(dunder: str, *, raising: bool) -> None:
    attacked = _property_attacked_class(dunder, raising=raising)
    DISPATCHED.clear()
    if raising:
        with pytest.raises(RuntimeError, match=dunder):
            getattr(attacked, dunder)
    else:
        assert getattr(attacked, dunder) is _IDENTITY_LIES[dunder]
    assert [f"property:{dunder}"] == DISPATCHED
    DISPATCHED.clear()
    _assert_class_identity(attacked, "_PropertyAttacked", __name__)
    assert DISPATCHED == []


def test_lying_checks_intercept_isinstance_and_issubclass() -> None:
    assert isinstance(object(), _LyingChecks) is True
    assert issubclass(int, _LyingChecks) is True
    assert DISPATCHED == ["instancecheck", "subclasscheck"]
    DISPATCHED.clear()
    assert truth.is_instance(object(), _LyingChecks) is False
    assert truth.is_subclass(int, _LyingChecks) is False
    assert truth.is_subclass(_LyingChecks, _Base) is True
    assert DISPATCHED == []


def test_equals_everything_intercepts_eq_membership_and_hashing() -> None:
    assert (_EqualsEverything == _Unrelated) is True
    members = (_EqualsEverything,)
    assert _Unrelated in members
    assert hash(_EqualsEverything) == 0
    assert "eq" in DISPATCHED
    assert "hash" in DISPATCHED
    DISPATCHED.clear()
    assert truth.is_subclass(_EqualsEverything, _Unrelated) is False
    assert truth.is_subclass(_EqualsEverything, _Base) is True
    registry: truth.IdentityMap[type, str] = truth.IdentityMap()
    registry[_EqualsEverything] = "hostile"
    assert _Unrelated not in registry
    assert registry.get(_Unrelated, "none") == "none"
    assert registry[_EqualsEverything] == "hostile"
    assert DISPATCHED == []


def test_raising_repr_intercepts_repr() -> None:
    with pytest.raises(RuntimeError, match="__repr__"):
        repr(_RaisingRepr)
    assert DISPATCHED == ["repr"]
    DISPATCHED.clear()
    spelled = f"<class '{__name__}._RaisingRepr'>"
    assert truth.render(_RaisingRepr) == spelled
    assert truth.text(_RaisingRepr) == spelled
    assert truth.describe(_RaisingRepr) == f"_RaisingRepr {spelled}"
    assert DISPATCHED == []


def test_non_str_module_is_neither_trusted_nor_rendered() -> None:
    assert type(_NonStrModule.__module__) is property
    assert truth.module(_NonStrModule) == "<unknown module>"
    assert truth.label(_NonStrModule) == "<unknown module>._NonStrModule"
    assert type(truth.static_attr(_NonStrModule, "__module__")) is property
    assert truth.render(_NonStrModule) == repr(_NonStrModule) == "<class '_NonStrModule'>"


def test_planted_colliding_key_runs_its_eq_in_every_namespace_lookup() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        # basedpyright: a non-``str`` namespace key is the hostile class body under test
        planted = type("_Planted", (), {_CollidingKey(): "planted"})  # pyright: ignore[reportArgumentType]
    _CollidingKey.armed = True
    try:
        with pytest.raises(RuntimeError, match="planted key compared"):
            _ = planted.__module__
        with pytest.raises(RuntimeError, match="planted key compared"):
            truth.module(planted)
    finally:
        _CollidingKey.armed = False
    assert DISPATCHED == ["planted-eq", "planted-eq"]
    assert truth.name(planted) == "_Planted"
    assert truth.mro(planted) == (planted, object)


# --- instance-level attacks ---


def test_raising_class_intercepts_the_ordinary_read() -> None:
    with pytest.raises(RuntimeError, match="__class__"):
        _ = _ClassRaiser().__class__
    with pytest.raises(RuntimeError, match="__class__"):
        isinstance(_ClassRaiser(), int)
    assert DISPATCHED == ["class", "class"]
    DISPATCHED.clear()
    raiser = _ClassRaiser()
    assert truth.class_of(raiser) is _ClassRaiser
    assert truth.is_instance(raiser, _ClassRaiser) is True
    assert truth.is_instance(raiser, int) is False
    assert truth.kind(raiser) == "_ClassRaiser"
    assert truth.name(raiser) == "_ClassRaiser"
    assert truth.qualname(raiser) == "_ClassRaiser"
    assert truth.label(raiser) == f"{__name__}._ClassRaiser"
    assert type(truth.static_attr(raiser, "__class__")) is property
    assert DISPATCHED == []


def test_class_claimer_intercepts_isinstance() -> None:
    assert isinstance(_ClassClaimer(), int) is True
    assert DISPATCHED == ["class"]
    DISPATCHED.clear()
    assert truth.is_instance(_ClassClaimer(), int) is False
    assert truth.kind(_ClassClaimer()) == "_ClassClaimer"
    assert DISPATCHED == []


def test_class_claimer_intercepts_isinstance_of_a_tuple() -> None:
    assert isinstance(_ClassClaimer(), (str, int)) is True
    assert DISPATCHED == ["class", "class"]
    DISPATCHED.clear()
    assert truth.is_one_of(_ClassClaimer(), (str, int)) is False
    assert truth.is_one_of(_ClassClaimer(), (str, _ClassClaimer)) is True
    assert DISPATCHED == []


def test_raising_class_intercepts_isinstance_of_a_tuple() -> None:
    with pytest.raises(RuntimeError, match="__class__"):
        isinstance(_ClassRaiser(), (str, int))
    assert DISPATCHED == ["class"]
    DISPATCHED.clear()
    assert truth.is_one_of(_ClassRaiser(), (str, int)) is False
    assert truth.is_one_of(_ClassRaiser(), (str, _ClassRaiser)) is True
    assert DISPATCHED == []


def test_getattr_trap_intercepts_the_ordinary_read_of_a_missing_attribute() -> None:
    trap = _GetattrTrap()
    with pytest.raises(RuntimeError, match="absent"):
        _ = trap.absent
    assert DISPATCHED == ["instance-getattr:absent"]
    DISPATCHED.clear()
    assert truth.static_attr(trap, "absent", 7) == 7
    assert truth.static_attr(trap, "stored") == "class-value"
    assert DISPATCHED == []


def test_getattribute_trap_intercepts_the_ordinary_read() -> None:
    trap = _GetattributeTrap()
    with pytest.raises(RuntimeError, match="stored"):
        _ = trap.stored
    assert DISPATCHED == ["instance-getattribute:stored"]
    DISPATCHED.clear()
    real = require(_object_getattribute(trap, "__dict__"), is_dict)
    real["own"] = "instance-value"
    assert truth.instance_dict(trap) is real
    assert truth.static_attr(trap, "own") == "instance-value"
    assert truth.static_attr(trap, "stored") == "class-value"
    assert truth.static_attr(trap, "absent", 7) == 7
    assert DISPATCHED == []


def test_raising_dict_property_intercepts_the_ordinary_read() -> None:
    raiser = _DictRaiser()
    with pytest.raises(RuntimeError, match="__dict__"):
        _ = raiser.__dict__
    assert DISPATCHED == ["dict"]
    DISPATCHED.clear()
    assert truth.instance_dict(raiser) is None
    assert truth.static_attr(raiser, "absent", "d") == "d"
    assert DISPATCHED == []


def test_lying_dict_property_never_hides_the_real_namespace() -> None:
    liar = _DictLiar()
    liar.stored = "real"
    assert liar.__dict__ == {"stored": "lie"}
    assert DISPATCHED == ["dict"]
    DISPATCHED.clear()
    assert truth.instance_dict(liar) == {"stored": "real"}
    assert truth.static_attr(liar, "stored") == "real"
    assert DISPATCHED == []


@pytest.mark.parametrize("shape", sorted(_FOREIGN_DICT_DESCRIPTORS))
def test_foreign_dict_descriptor_is_never_read(shape: str) -> None:
    descriptor = _FOREIGN_DICT_DESCRIPTORS[shape]
    orphan = _foreign_dict_class(descriptor, base=object)()
    with pytest.raises(TypeError, match="doesn't apply to a '_ForeignDict' object"):
        read_attr(orphan, "__dict__")
    assert truth.instance_dict(orphan) is None
    assert truth.static_attr(orphan, "absent", "d") == "d"

    inheriting = _foreign_dict_class(descriptor, base=_DictBase)()
    object.__setattr__(inheriting, "stored", "real")
    with pytest.raises(TypeError, match="doesn't apply to a '_ForeignDict' object"):
        read_attr(inheriting, "__dict__")
    assert truth.instance_dict(inheriting) == {"stored": "real"}
    assert truth.static_attr(inheriting, "stored") == "real"


def test_bound_builtin_on_a_hostile_class_is_named_without_its_metaclass() -> None:
    bound_to_class = call_method(truth.class_dict(type)["mro"], "__get__", _RaisingGetattribute)
    bound_to_instance = object.__sizeof__.__get__(_RaisingGetattribute())
    DISPATCHED.clear()
    for bound in (bound_to_class, bound_to_instance):
        with pytest.raises(RuntimeError, match="__qualname__"):
            read_attr(bound, "__qualname__")
    assert DISPATCHED == ["getattribute:__qualname__", "getattribute:__qualname__"]
    DISPATCHED.clear()
    assert truth.name(bound_to_class) == "mro"
    assert truth.qualname(bound_to_class) == "_RaisingGetattribute.mro"
    assert truth.label(bound_to_class) == f"{__name__}._RaisingGetattribute.mro"
    assert truth.qualname(bound_to_instance) == "_RaisingGetattribute.__sizeof__"
    assert truth.module(bound_to_instance) == __name__
    assert DISPATCHED == []


def test_hostile_str_is_copied_through_the_base_slot() -> None:
    with pytest.raises(RuntimeError, match="__str__"):
        str(_HostileStr("x"))
    with pytest.raises(RuntimeError, match="__format__"):
        _ = f"{_HostileStr('x')}"
    assert truth.text(_HostileStr("x")) == "x"
    assert type(truth.text(_HostileStr("x"))) is str


# --- structure reads ---


def test_is_subclass_of_a_non_class_is_false() -> None:
    assert truth.is_subclass(3, int) is False
    assert truth.is_subclass(_ClassRaiser(), _ClassRaiser) is False


def test_is_one_of_accepts_a_real_subclass_and_rejects_an_empty_tuple() -> None:
    true_value: object = True
    assert truth.is_one_of(true_value, (str, int)) is True
    assert truth.is_one_of(true_value, ()) is False


def test_is_one_of_ignores_a_virtual_abc_registration() -> None:
    class _Virtual(abc.ABC):
        """An ABC ``_Unrelated`` is registered on but never inherits."""

        @abc.abstractmethod
        def required(self) -> None:
            """The abstract member that makes this a real ABC."""

    _ = _Virtual.register(_Unrelated)
    assert isinstance(_Unrelated(), (str, _Virtual)) is True
    assert truth.is_one_of(_Unrelated(), (str, _Virtual)) is False


class _EqualsEverythingTwin(_Base, metaclass=_EqualsEverythingMeta):
    """A second class under ``_EqualsEverythingMeta``: same hash, claims equality with the first."""


class _RaisingHashEqMeta(type):
    """A metaclass whose ``__hash__`` and ``__eq__`` raise."""

    @override
    def __eq__(cls, other: object) -> NoReturn:
        DISPATCHED.append("eq")
        raise RuntimeError("__eq__")

    @override
    def __hash__(cls) -> NoReturn:
        DISPATCHED.append("hash")
        raise RuntimeError("__hash__")


class _RaisingHashEq(_Base, metaclass=_RaisingHashEqMeta):
    """A class every hash or equality test of which raises."""


def test_mro_entry_most_specific_class_wins_over_insertion_order() -> None:
    class _Child(_Base):
        """A subclass whose entry is inserted after its parent's."""

    class _Grandchild(_Child):
        """An unregistered subclass that answers through its nearest ancestor."""

    mapping: dict[type, str] = {object: "object", _Base: "base", _Child: "child"}
    assert truth.mro_entry(mapping, _Child) == (_Child, "child")
    assert truth.mro_entry(mapping, _Grandchild) == (_Child, "child")
    assert truth.mro_entry(mapping, _Unrelated) == (object, "object")


def test_mro_entry_ignores_an_aliasing_metaclass_key() -> None:
    mapping: dict[type, str] = {_EqualsEverything: "aliased"}
    assert mapping[_EqualsEverythingTwin] == "aliased"
    assert "eq" in DISPATCHED
    DISPATCHED.clear()
    assert truth.mro_entry(mapping, _EqualsEverythingTwin) is None
    assert truth.mro_entry(mapping, _EqualsEverything) == (_EqualsEverything, "aliased")
    assert DISPATCHED == []


def test_mro_entry_never_hashes_or_compares_a_raising_class() -> None:
    mapping: dict[type, str] = {_Base: "base"}
    with pytest.raises(RuntimeError, match="__hash__"):
        _ = _RaisingHashEq in mapping
    DISPATCHED.clear()
    assert truth.mro_entry(mapping, _RaisingHashEq) == (_Base, "base")
    assert DISPATCHED == []


def test_mro_entry_returns_a_none_value_and_misses_as_none() -> None:
    mapping: dict[type, None] = {_Base: None}
    assert truth.mro_entry(mapping, _RaisingGetattribute) == (_Base, None)
    assert truth.mro_entry(mapping, _Unrelated) is None
    empty: dict[type, str] = {}
    assert truth.mro_entry(empty, _Base) is None


def test_mro_entry_of_a_non_class_is_none() -> None:
    assert truth.mro_entry({int: "int", object: "object"}, 3) is None


def test_is_type_and_is_exact() -> None:
    assert truth.is_type(_RaisingGetattribute) is True
    assert truth.is_type(int) is True
    assert truth.is_type(3) is False
    assert truth.is_exact("x", str) is True
    assert truth.is_exact(_HostileStr("x"), str) is False
    true_value: object = True
    assert truth.is_exact(true_value, int) is False


def test_is_type_never_asks_a_hostile_metaclass_or_class_claim() -> None:
    hostile_classes = (
        _LyingChecks,
        _EqualsEverything,
        _LyingGetattribute,
        _RaisingGetattribute,
    )
    assert all(truth.is_type(cls) for cls in hostile_classes)
    assert truth.is_type(_LyingChecksMeta) is True
    assert not any(truth.is_type(cls()) for cls in hostile_classes)
    assert truth.is_type(_ClassRaiser()) is False
    assert truth.is_type(_ClassClaimer()) is False
    assert DISPATCHED == []


def test_non_class_structure_reads_are_empty() -> None:
    assert truth.bases(3) == ()
    assert dict(truth.class_dict(3)) == {}
    assert truth.mro(3) == (int, object)


def test_declared_meta_keys_are_the_sorted_public_keys_of_the_own_body() -> None:
    class _BaseMeta:
        inherited = 1

    class _Meta(_BaseMeta):
        zeta = 1
        _private = 1
        alpha = 1
        __dunder__ = 1

    assert truth.declared_meta_keys(_Meta) == ["alpha", "zeta"]


@pytest.mark.parametrize(
    "meta",
    [
        3,
        "Meta",
        None,
        _Base(),
    ],
)
def test_declared_meta_keys_of_a_non_class_are_empty(meta: object) -> None:
    assert truth.declared_meta_keys(meta) == []


@pytest.mark.filterwarnings("ignore:non-string key in the __dict__")
def test_declared_meta_keys_keep_a_planted_non_str_key_after_the_str_keys() -> None:
    meta = object_result(
        type,
        "_Meta",
        (),
        {
            11: "x",
            "model": 1,
            2: "y",
            "_private": 1,
        },
    )
    assert truth.declared_meta_keys(meta) == ["model", 11, 2]


def test_static_attr_on_a_class_falls_back_to_the_metaclass() -> None:
    assert type(truth.static_attr(_LyingChecks, "__instancecheck__")) is types.FunctionType
    assert truth.static_attr(_LyingChecks, "absent", "default") == "default"
    assert truth.mro_attr(_LyingChecks, "__instancecheck__", "none") == "none"
    assert truth.mro_attr(3, "real", "none") == "none"


def test_mro_attr_is_the_special_method_lookup() -> None:
    class _Color(enum.Enum):
        RED = 1

    member = _Color.RED
    member_class = type(member)
    for dunder in ("__iter__", "__len__", "__getitem__"):
        # The metaclass carries the dunder, the member's class does not: the
        # member is not iterable / sized / subscriptable, as ``mro_attr`` says.
        assert truth.static_attr(member_class, dunder) is truth.static_attr(enum.EnumMeta, dunder)
        assert truth.static_attr(member_class, dunder) is not None
        assert truth.mro_attr(member_class, dunder, "absent") == "absent"
    assert not isinstance(member, Iterable)
    assert not isinstance(member, Sized)

    class _Unsupported:
        __iter__ = None

    class _Plain: ...

    assert truth.mro_attr(_Unsupported, "__iter__", "absent") is None
    assert truth.mro_attr(_Plain, "__iter__", "absent") == "absent"
    assert truth.mro_attr(member, "__iter__", "absent") == "absent"
    assert truth.mro_attr(3, "real", "absent") == "absent"


def test_static_attr_data_descriptor_beats_instance_dict() -> None:
    class Holder:
        @property
        def value(self) -> NoReturn:
            raise RuntimeError("value")

    holder = Holder()
    holder.__dict__["value"] = "shadow"
    assert type(truth.static_attr(holder, "value")) is property


def _wrapped(_owner: type[object]) -> None:
    """The function each builtin wrapper below holds in its ``__func__`` slot."""


# ``classmethod`` is not subscriptable at runtime before Python 3.11 and a class base is
# evaluated there, so the parametrized type is carried by an annotated alias.
_ClassmethodBase: type[classmethod[object, ..., object]] = classmethod


class _LyingClassmethod(_ClassmethodBase):
    """A ``classmethod`` subclass whose ``__func__`` lies; never an exact builtin wrapper."""

    @property
    @override
    def __func__(self) -> NoReturn:
        DISPATCHED.append("lie:__func__")
        raise RuntimeError("__func__")


_LYING_CLASSMETHOD = _LyingClassmethod(_wrapped)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(classmethod(_wrapped), _wrapped, id="classmethod"),
        pytest.param(staticmethod(_wrapped), _wrapped, id="staticmethod"),
        pytest.param(
            types.MethodType(_wrapped, _Base),
            _wrapped,
            id="bound-method",
        ),
        pytest.param(_wrapped, _wrapped, id="plain-function"),
        pytest.param(_LYING_CLASSMETHOD, _LYING_CLASSMETHOD, id="wrapper-subclass"),
        pytest.param("not callable", "not callable", id="non-callable"),
        pytest.param(None, None, id="none"),
    ],
)
def test_stored_function_reads_the_builtin_wrapper_slot(value: object, expected: object) -> None:
    DISPATCHED.clear()
    assert truth.stored_function(value) is expected
    assert DISPATCHED == []


def test_lying_wrapper_subclass_intercepts_the_ordinary_read() -> None:
    DISPATCHED.clear()
    with pytest.raises(RuntimeError, match="__func__"):
        read_attr(_LYING_CLASSMETHOD, "__func__")
    assert DISPATCHED == ["lie:__func__"]


def _base_hook(_cls: type[object]) -> str:
    """The function ``_HookBase.hook`` stores."""
    return "base"


def _own_hook(_cls: type[object]) -> str:
    """A different function an overriding subclass stores."""
    return "own"


class _HookBase:
    """A framework-shaped base whose ``hook`` a subclass may override."""

    hook = classmethod(_base_hook)


def test_overrides_a_direct_override() -> None:
    overriding = type("Overriding", (_HookBase,), {"hook": classmethod(_own_hook)})

    assert truth.overrides(overriding, _HookBase, "hook") is True


def test_overrides_through_an_intermediate_base() -> None:
    intermediate = type("Intermediate", (_HookBase,), {"hook": staticmethod(_own_hook)})
    leaf = type("Leaf", (intermediate,), {})

    assert "hook" not in truth.class_dict(leaf)
    assert truth.overrides(leaf, _HookBase, "hook") is True


def test_overrides_no_override() -> None:
    class Inheriting(_HookBase): ...

    assert truth.overrides(Inheriting, _HookBase, "hook") is False
    assert truth.overrides(_HookBase, _HookBase, "hook") is False


def test_overrides_a_rewrap_of_the_base_function_is_not_an_override() -> None:
    rewrapped = type("Rewrapped", (_HookBase,), {"hook": classmethod(_base_hook)})
    reassigned = type("Reassigned", (_HookBase,), {"hook": _HookBase.hook})

    assert truth.class_dict(rewrapped)["hook"] is not truth.class_dict(_HookBase)["hook"]
    assert truth.class_dict(reassigned)["hook"] is not truth.class_dict(_HookBase)["hook"]
    assert truth.overrides(rewrapped, _HookBase, "hook") is False
    assert truth.overrides(reassigned, _HookBase, "hook") is False


def test_overrides_asks_about_any_of_the_named_hooks() -> None:
    class TwoHooks(_HookBase):
        other = classmethod(_base_hook)

    first_only = type("FirstOnly", (TwoHooks,), {"hook": classmethod(_own_hook)})
    second_only = type("SecondOnly", (TwoHooks,), {"other": classmethod(_own_hook)})
    neither = type("Neither", (TwoHooks,), {})

    assert truth.overrides(first_only, TwoHooks, "other", "hook") is True
    assert truth.overrides(second_only, TwoHooks, "hook", "other") is True
    assert truth.overrides(neither, TwoHooks, "hook", "other") is False
    assert truth.overrides(second_only, TwoHooks, "hook") is False


@pytest.mark.parametrize(
    "value",
    [
        None,
        3,
        "not_a_type",
        _HookBase(),
    ],
    ids=[
        "none",
        "int",
        "text",
        "instance",
    ],
)
def test_overrides_a_non_subclass_or_non_class_is_false(value: object) -> None:
    class Unrelated:
        @classmethod
        def hook(cls) -> str:
            return "unrelated"

    class ClaimingMeta(type):
        @override
        def __subclasscheck__(cls, subclass: type) -> bool:
            return True

    class ClaimingBase(_HookBase, metaclass=ClaimingMeta): ...

    # The ordinary check believes the base's lie; the real MRO does not.
    assert issubclass(Unrelated, ClaimingBase)
    assert truth.overrides(Unrelated, ClaimingBase, "hook") is False
    assert truth.overrides(Unrelated, _HookBase, "hook") is False
    assert truth.overrides(value, _HookBase, "hook") is False


def test_overrides_never_consults_the_metaclass() -> None:
    class HookMeta(type):
        def hook(cls) -> str:
            return "meta"

    class Plain:
        pass

    class Carrying(Plain, metaclass=HookMeta): ...

    assert truth.static_attr(Carrying, "hook") is HookMeta.__dict__["hook"]
    assert truth.overrides(Carrying, Plain, "hook") is False


def test_instance_dict_reads_the_real_namespace_slot() -> None:
    plain = _Base()
    plain.stored = "value"
    assert truth.instance_dict(plain) is plain.__dict__
    namespace = types.SimpleNamespace(stored="value")
    assert truth.instance_dict(namespace) is namespace.__dict__
    assert truth.static_attr(namespace, "stored") == "value"
    assert truth.instance_dict(types) is types.__dict__
    assert truth.static_attr(types, "SimpleNamespace") is types.SimpleNamespace


def test_instance_dict_is_none_without_a_namespace() -> None:
    assert truth.instance_dict(object()) is None
    assert truth.instance_dict(3) is None
    assert truth.instance_dict(_Slotted()) is None
    assert truth.static_attr(3, "real") is int.__dict__["real"]
    assert truth.static_attr(object(), "absent", "d") == "d"


def test_instance_state_is_the_namespace_or_a_type_error() -> None:
    plain = _Base()
    assert truth.instance_state(plain) is plain.__dict__
    with pytest.raises(TypeError, match="a _Slotted carries no instance __dict__"):
        truth.instance_state(_Slotted())


# --- callables name themselves ---


class _SelfNamed(Protocol):
    """A callable or descriptor that carries its own ``__name__`` / ``__qualname__`` slots."""

    __name__: str
    __qualname__: str


class _Owner:
    def method(self) -> None:
        """A method."""


@pytest.mark.parametrize(
    (
        "callable_",
        "expected_name",
        "expected_qualname",
        "expected_module",
    ),
    [
        pytest.param(
            _plain_function,
            "_plain_function",
            "_plain_function",
            __name__,
            id="function",
        ),
        pytest.param(_Owner().method, "method", "_Owner.method", __name__, id="bound-method"),
        pytest.param(len, "len", "len", "builtins", id="module-builtin"),
        pytest.param(math.sqrt, "sqrt", "sqrt", "math", id="extension-builtin"),
        pytest.param(
            list[object]().append,
            "append",
            "list.append",
            "builtins",
            id="bound-builtin",
        ),
        pytest.param(dict.fromkeys, "fromkeys", "dict.fromkeys", "builtins", id="class-builtin"),
        pytest.param(str.join, "join", "str.join", "builtins", id="method-descriptor"),
        pytest.param(
            truth.class_dict(dict)["fromkeys"],
            "fromkeys",
            "dict.fromkeys",
            "builtins",
            id="classmethod-descriptor",
        ),
        pytest.param(
            object.__init__,
            "__init__",
            "object.__init__",
            "builtins",
            id="slot-wrapper",
        ),
        pytest.param(
            _Base().__init__,
            "__init__",
            "object.__init__",
            "builtins",
            id="method-wrapper",
        ),
        pytest.param(truth.class_dict(int)["real"], "real", "int.real", "builtins", id="getset"),
        pytest.param(
            truth.class_dict(types.SimpleNamespace)["__dict__"],
            "__dict__",
            "SimpleNamespace.__dict__",
            "types",
            id="member",
        ),
        pytest.param(
            _cached_function,
            "_cached_function",
            "_cached_function",
            __name__,
            id="update-wrapper",
        ),
    ],
)
def test_callable_identity_matches_its_own_slots(
    callable_: _SelfNamed,
    expected_name: str,
    expected_qualname: str,
    expected_module: str,
) -> None:
    assert truth.name(callable_) == expected_name == callable_.__name__
    assert truth.qualname(callable_) == expected_qualname == callable_.__qualname__
    assert truth.module(callable_) == expected_module
    assert truth.label(callable_) == f"{expected_module}.{expected_qualname}"


def test_callable_instance_without_a_declared_name_is_named_by_its_class() -> None:
    partial = functools.partial(print)
    assert truth.name(partial) == "partial"
    assert truth.qualname(partial) == "partial"
    assert truth.module(partial) == "functools"

    class Callable:
        def __call__(self) -> None:
            """Call."""

    spoofed = Callable()
    # basedpyright: a non-``str`` ``__name__`` is the hostile instance under test
    spoofed.__name__ = 42  # pyright: ignore[reportAttributeAccessIssue]
    assert truth.name(spoofed) == "Callable"
    assert truth.module(spoofed) == __name__


def test_function_with_lying_module_attribute() -> None:
    def spoofed() -> None:
        """A function whose ``__module__`` is not a string."""

    # A non-``str`` ``__module__`` is the hostile function under test; the generic setter
    # stores it in the function's own ``__module__`` slot, as plain assignment would.
    object.__setattr__(spoofed, "__module__", 42)
    assert truth.module(spoofed) == "<unknown module>"


def test_builtin_class_module_is_read_from_its_name() -> None:
    assert truth.module(int) == "builtins"
    assert truth.label(int) == "builtins.int"
    assert truth.module(types.SimpleNamespace) == "types"


def test_empty_class_name_falls_back() -> None:
    nameless = type("", (), {})
    assert truth.name(nameless) == "type"
    assert truth.kind(nameless) == "type"


@pytest.mark.parametrize(
    "read",
    [
        pytest.param(lambda: truth.name(_RaisingGetattribute), id="name"),
        pytest.param(lambda: truth.qualname(_LyingGetattribute), id="qualname"),
        pytest.param(lambda: truth.module(_RaisingGetattribute), id="module"),
        pytest.param(lambda: truth.label(_LyingGetattribute), id="label"),
        pytest.param(lambda: truth.kind(_ClassRaiser()), id="kind"),
        pytest.param(lambda: truth.text(_HostileStr("x")), id="text"),
        pytest.param(lambda: truth.render(_PlainInt(3)), id="render"),
    ],
)
def test_results_are_exact_str(read: Callable[[], str]) -> None:
    """Every identity/render reader returns an exact str."""
    assert type(read()) is str


def _str_subclass_named_class(module: str = "consumer") -> type[object]:
    named = type("Plain", (), {"__module__": module})
    named.__name__ = _HostileStr("Named")
    named.__qualname__ = _HostileStr("Outer.Named")
    return named


def _nameless_class_of_a_str_subclass_named_metaclass() -> type:
    meta = type("PlainMeta", (type,), {})
    meta.__name__ = _HostileStr("NamedMeta")
    return meta("", (), {})


def _str_subclass_named_function() -> Callable[[], None]:
    def plain() -> None: ...

    plain.__name__ = _HostileStr("named")
    plain.__qualname__ = _HostileStr("Outer.named")
    return plain


@pytest.mark.parametrize(
    ("read", "expected"),
    [
        pytest.param(lambda: truth.name(_str_subclass_named_class()), "Named", id="name-class"),
        pytest.param(
            lambda: truth.name(_nameless_class_of_a_str_subclass_named_metaclass()),
            "NamedMeta",
            id="name-metaclass-fallback",
        ),
        pytest.param(
            lambda: truth.name(_str_subclass_named_class()()),
            "Named",
            id="name-instance",
        ),
        pytest.param(
            lambda: truth.name(_str_subclass_named_function()),
            "named",
            id="name-function",
        ),
        pytest.param(
            lambda: truth.qualname(_str_subclass_named_class()),
            "Outer.Named",
            id="qualname-class",
        ),
        pytest.param(
            lambda: truth.qualname(_str_subclass_named_class()()),
            "Outer.Named",
            id="qualname-instance",
        ),
        pytest.param(
            lambda: truth.qualname(_str_subclass_named_function()),
            "Outer.named",
            id="qualname-function",
        ),
        pytest.param(
            lambda: truth.kind(_str_subclass_named_class()()),
            "Named",
            id="kind-instance",
        ),
        pytest.param(
            lambda: truth.render(_str_subclass_named_class()),
            "<class 'consumer.Outer.Named'>",
            id="render-class",
        ),
        pytest.param(
            lambda: truth.render(_str_subclass_named_class("builtins")),
            "<class 'Named'>",
            id="render-builtins-class",
        ),
    ],
)
def test_a_str_subclass_name_reads_as_an_exact_str(read: Callable[[], str], expected: str) -> None:
    """A ``str`` subclass name comes back from every name read as an exact ``str``."""
    value = read()
    assert type(value) is str
    assert value == expected


# --- rendering matches repr / str for honest values ---


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(3, id="int"),
        pytest.param(True, id="bool"),
        pytest.param(None, id="none"),
        pytest.param(1.5, id="float"),
        pytest.param(1j, id="complex"),
        pytest.param("x", id="str"),
        pytest.param(b"x", id="bytes"),
        pytest.param(_PlainInt(3), id="int-subclass"),
        pytest.param(_Color.RED, id="enum-member"),
        pytest.param(_Level.LOW, id="intenum-member"),
        pytest.param(_Named.ALPHA, id="str-enum-member"),
        pytest.param(_Strategy.BOGUS, id="textchoices-member"),
        pytest.param(int, id="builtin-class"),
        pytest.param(_Base, id="class"),
        pytest.param(_Color, id="enum-class"),
        pytest.param(_Shade, id="flag-class"),
        pytest.param(_Strategy, id="textchoices-class"),
        pytest.param(_NonStrModule, id="non-str-module-class"),
        pytest.param(
            type("Named", (), {"__module__": "builtins", "__qualname__": "Outer.Named"}),
            id="builtins-module-class",
        ),
    ],
)
def test_render_matches_repr(value: object) -> None:
    assert truth.render(value) == repr(value)
    assert truth.describe(value) == f"{truth.kind(value)} {value!r}"


def test_honest_spellings_are_pinned_on_every_supported_version() -> None:
    flag_spelling = "<flag '_Shade'>" if sys.version_info >= (3, 11) else "<enum '_Shade'>"
    assert truth.render(_Color) == "<enum '_Color'>"
    assert truth.text(_Color) == "<enum '_Color'>"
    assert truth.render(_Shade) == flag_spelling
    assert truth.render(_Strategy) == "<enum '_Strategy'>"
    assert truth.describe(_Strategy) == "_Strategy <enum '_Strategy'>"
    assert truth.render(_Strategy.BOGUS) == "_Strategy.BOGUS"
    assert truth.describe(_Strategy.BOGUS) == "_Strategy _Strategy.BOGUS"
    assert truth.text(_Strategy.BOGUS) == "bogus"
    assert truth.render(_Level.LOW) == "<_Level.LOW: 1>"
    assert truth.text(_Level.LOW) == ("1" if sys.version_info >= (3, 11) else "_Level.LOW")
    assert truth.text(_Level.LOW) == str(_Level.LOW)
    assert truth.text(_Named.ALPHA) == "a"
    assert truth.render(_NonStrModule) == "<class '_NonStrModule'>"
    assert truth.render(_Base) == f"<class '{__name__}._Base'>"
    assert truth.render(int) == "<class 'int'>"


@pytest.mark.parametrize(
    "value",
    [
        3,
        1.5,
        None,
        _PlainInt(3),
        _OwnStrInt(3),
        _Level.LOW,
        _Color.RED,
    ],
    ids=[
        "int",
        "float",
        "none",
        "plain-int",
        "own-str-int",
        "int-enum",
        "enum",
    ],
)
def test_text_matches_str_for_non_str_scalars(value: object) -> None:
    assert truth.text(value) == str(value)
    assert truth.render(_OwnStrInt(3)) == "3"
    assert truth.text(_OwnStrInt(3)) == "own"


def test_text_fallback_for_an_empty_render() -> None:
    assert truth.text("", "<unknown>") == "<unknown>"
    assert truth.text("value", "<unknown>") == "value"


def test_plain_str_returns_an_exact_str_as_the_same_object() -> None:
    value = "title"
    assert truth.plain_str(value) is value


class _Flavor(models.TextChoices):
    """A ``TextChoices`` enum whose members are ``str`` subclass instances."""

    SWEET = "sweet", "Sweet"


def test_plain_str_reads_a_str_subclass_member_as_its_exact_text() -> None:
    """A ``StrEnum`` / ``TextChoices`` member comes back as the exact ``str`` it spells."""
    members = (STR_ENUM("Names", {"TITLE": "title"})["TITLE"], _Flavor.SWEET)
    for member, spelled in zip(members, ("title", "sweet"), strict=True):
        plain = truth.plain_str(member)
        assert type(plain) is str
        assert plain == spelled


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(3, id="int"),
        pytest.param(None, id="none"),
        pytest.param(b"title", id="bytes"),
        pytest.param(["title"], id="list"),
        pytest.param(SimpleLazyObject(lambda: "title"), id="simple-lazy-object"),
    ],
)
def test_plain_str_passes_a_non_str_through_unchanged(value: object) -> None:
    """A value whose real class is no ``str`` comes back as itself, a lazy proxy included."""
    assert truth.plain_str(value) is value


def test_plain_str_never_evaluates_a_lazy_string() -> None:
    """A lazy translation string is no ``str``: it comes back as itself, unevaluated."""
    evaluations: list[str] = []

    def _spell() -> str:
        evaluations.append("title")
        return "title"

    declaration = lazy(_spell, str)()

    assert truth.plain_str(declaration) is declaration
    assert evaluations == []


@pytest.mark.skipif(
    not hasattr(sys, "get_int_max_str_digits"),
    reason="the interpreter has no int string-conversion limit",
)
def test_oversized_int_renders_without_conversion() -> None:
    # Four bits per decimal digit overshoots the limit by well over ten digits.
    huge = 1 << (4 * (sys.get_int_max_str_digits() + 10))
    with pytest.raises(ValueError, match="Exceeds the limit"):
        repr(huge)
    assert truth.render(huge) == "<unprintable int>"
    assert truth.text(huge) == "<unprintable int>"
    assert truth.describe(huge) == "an unprintable int"
    assert truth.render(_PlainInt(huge)) == "<unprintable _PlainInt>"
    assert truth.render(10**10) == "10000000000"


def test_oversized_int_check_honours_a_disabled_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "get_int_max_str_digits", lambda: 0, raising=False)
    assert truth.render(10**20) == "100000000000000000000"


# --- rendering a consumer object is the object's own behaviour ---


def test_consumer_object_rendering_is_the_object_behaviour() -> None:
    class Rendered:
        @override
        def __repr__(self) -> str:
            return "<Rendered>"

        @override
        def __str__(self) -> str:
            return "rendered"

    assert truth.render(Rendered()) == "<Rendered>"
    assert truth.text(Rendered()) == "rendered"
    assert truth.describe(Rendered()) == "Rendered <Rendered>"


@pytest.mark.parametrize(
    "render",
    [
        pytest.param(lambda: truth.render(_HostileStr("x")), id="str-subclass-repr"),
        pytest.param(lambda: truth.render(_HostileInt(3)), id="int-subclass-repr"),
        pytest.param(lambda: truth.text(_HostileInt(3)), id="int-subclass-str"),
        pytest.param(lambda: truth.describe(_HostileInt(3)), id="int-subclass-describe"),
    ],
)
def test_a_scalar_subclass_override_is_consumer_behaviour_and_propagates(
    render: Callable[[], str],
) -> None:
    with pytest.raises(RuntimeError, match="__repr__"):
        render()


# --- IdentitySet / is_exact_one_of / is_among ---


def test_identity_set_never_hashes_or_compares_members() -> None:
    members: truth.IdentitySet[type] = truth.IdentitySet((_EqualsEverything, _Base))
    assert _EqualsEverything in members
    assert _Unrelated not in members
    assert len(members) == 2
    assert list(members) == [_EqualsEverything, _Base]
    members.add(_Unrelated)
    members.add(_Unrelated)
    assert _Unrelated in members
    assert list(members) == [_EqualsEverything, _Base, _Unrelated]
    assert "hash" not in DISPATCHED
    assert "eq" not in DISPATCHED


@pytest.mark.parametrize(
    "probe",
    [_EqualsEverythingTwin, _Unrelated, _Base],
    ids=["eq-claiming-class", "unrelated-class", "base-class"],
)
def test_identity_set_admits_only_its_own_members(probe: type) -> None:
    members: truth.IdentitySet[type] = truth.IdentitySet((_EqualsEverything,))
    assert probe not in members
    assert DISPATCHED == []


def test_is_exact_one_of_matches_the_real_class_only() -> None:
    classes: truth.IdentitySet[type[object]] = truth.IdentitySet((str, _EqualsEverything))
    assert truth.is_exact_one_of("text", classes) is True
    assert truth.is_exact_one_of(_EqualsEverything(), classes) is True
    assert truth.is_exact_one_of(_EqualsEverythingTwin(), classes) is False
    assert truth.is_exact_one_of(_ClassClaimer(), classes) is False
    true_value: object = True
    assert truth.is_exact_one_of(true_value, truth.IdentitySet((int,))) is False
    assert truth.is_exact_one_of(None, truth.IdentitySet()) is False
    assert DISPATCHED == []


def test_is_among_compares_by_identity_only() -> None:
    path: tuple[type, ...] = (_Base, _EqualsEverything)
    assert truth.is_among(_EqualsEverything, path) is True
    assert truth.is_among(_EqualsEverythingTwin, path) is False
    assert truth.is_among(_Unrelated, ()) is False
    assert truth.is_among(_Unrelated, iter([_Unrelated])) is True
    assert DISPATCHED == []


# --- IdentityMap ---


def test_identity_map_never_hashes_or_compares_keys() -> None:
    registry: truth.IdentityMap[type, str] = truth.IdentityMap()
    registry[_EqualsEverything] = "hostile"
    registry[_Base] = "base"
    assert _EqualsEverything in registry
    assert _Unrelated not in registry
    assert registry[_EqualsEverything] == "hostile"
    assert registry.get(_Unrelated, "none") == "none"
    assert registry.get(_Base) == "base"
    assert len(registry) == 2
    assert list(registry) == [_EqualsEverything, _Base]
    assert registry.keys() == [_EqualsEverything, _Base]
    assert registry.values() == ["hostile", "base"]
    assert registry.items() == [(_EqualsEverything, "hostile"), (_Base, "base")]
    assert registry.setdefault(_Base, "other") == "base"
    assert registry.setdefault(_Unrelated, "unrelated") == "unrelated"
    assert registry.pop(_Unrelated) == "unrelated"
    assert registry.pop(_Unrelated, "gone") == "gone"
    del registry[_Base]
    assert _Base not in registry
    registry.clear()
    assert len(registry) == 0
    assert "hash" not in DISPATCHED
    assert "eq" not in DISPATCHED


def test_identity_map_starts_with_the_given_entries_by_identity() -> None:
    registry: truth.IdentityMap[type, str] = truth.IdentityMap(
        [(_EqualsEverything, "hostile"), (_Base, "base")],
    )
    assert registry.items() == [(_EqualsEverything, "hostile"), (_Base, "base")]
    assert _EqualsEverythingTwin not in registry
    assert "hash" not in DISPATCHED
    assert "eq" not in DISPATCHED


def test_identity_map_missing_key_names_the_label() -> None:
    registry: truth.IdentityMap[type, int] = truth.IdentityMap()
    with pytest.raises(KeyError, match="_RaisingGetattribute"):
        registry[_RaisingGetattribute]
    with pytest.raises(KeyError, match="int"):
        del registry[3]
    assert DISPATCHED == []
