"""Tests for ``django_strawberry_framework/utils/introspection.py``.

The helpers are checked on the shapes the package passes them: plain, metaclass and enum
classes, the ``classmethod``, ``staticmethod`` and ``property`` entries of a class namespace,
C callables, bound methods, ``functools`` wrappers and callable instances. Each expectation is
the answer the interpreter gives for that shape. A Django ``SimpleLazyObject`` is answered as
itself and its factory never runs.
"""

from __future__ import annotations

import abc
import codecs
import enum
import functools

import pytest
from django.db import models
from django.utils.functional import SimpleLazyObject
from typing_extensions import override

from django_strawberry_framework.utils.introspection import (
    class_mro_attr,
    kind,
    mro_attr,
    mro_entry,
    name,
    overrides,
    plain_str,
    text,
)

MODULE = __name__


def _plain_func() -> int:
    return 1


def _cm_func(cls: type[object]) -> str:
    return cls.__name__


def _other_cm(cls: type[object]) -> str:
    return cls.__name__.lower()


def _sm_func() -> str:
    return "static"


_CM_WRAPPER = classmethod(_cm_func)
_SM_WRAPPER = staticmethod(_sm_func)


class _Base:
    marker = "base"
    cm = _CM_WRAPPER
    sm = _SM_WRAPPER

    def meth(self) -> str:
        return "base"

    @property
    def prop(self) -> str:
        return "base"


class _Sub(_Base):
    @override
    def meth(self) -> str:
        return "sub"


class _Rewrap(_Base):
    cm = classmethod(_cm_func)
    sm = staticmethod(_sm_func)
    meth = _Base.meth


_ALIAS = type("_Alias", (_Base,), {"cm": _Base.cm})


class _Override(_Base):
    cm = classmethod(_other_cm)


class _Unrelated:
    marker = "unrelated"


class _ReprMeta(type):
    @override
    def __repr__(cls) -> str:
        return "custom-repr"


class _WithMetaRepr(metaclass=_ReprMeta):
    pass


class _Color(enum.Enum):
    RED = "red"


class _Mixin(str, enum.Enum):
    R = "r"


class _Choices(models.TextChoices):
    STAR = "STAR", "Star"


class _MyInt(int):
    pass


class _AbcBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self) -> None: ...


class _Callable:
    def __call__(self) -> int:
        return 5


class _Named:
    __name__ = "class-level"


class _Outer:
    class Inner:
        pass


def test_mro_attr_reads_the_static_attribute() -> None:
    Unsupported = type("Unsupported", (), {"__iter__": None})
    sentinel = object()
    assert mro_attr(_Sub, "meth") is _Sub.meth
    assert mro_attr(_Sub, "marker") == "base"
    assert mro_attr(_Sub, "absent", sentinel) is sentinel
    assert mro_attr(Unsupported, "__iter__", sentinel) is None
    assert mro_attr(_Callable, "__call__") is _Callable.__call__


class _StoresMro(_Base):
    mro = "stored"


def _unevaluated(value: object) -> object:
    """A lazy proxy of ``value`` whose factory fails the test if anything evaluates it."""

    def setup() -> object:
        pytest.fail(f"the lazy proxy of {value!r} was evaluated")

    return SimpleLazyObject(setup)


def test_class_mro_attr_reads_the_class_mro_and_never_the_metaclass() -> None:
    """``mro`` only ``type`` carries is absent; a class or ancestor storing it answers."""
    sentinel = object()
    assert class_mro_attr(_Sub, "mro", sentinel) is sentinel
    assert class_mro_attr(_Sub, "__call__", sentinel) is sentinel
    assert mro_attr(_Sub, "mro", sentinel) is not sentinel
    assert class_mro_attr(type("_Child", (_StoresMro,), {}), "mro") == "stored"
    assert class_mro_attr(_Sub, "marker") == "base"
    assert class_mro_attr(_Sub, "prop") is vars(_Base)["prop"]
    assert class_mro_attr(_Base(), "marker", sentinel) is sentinel


def test_the_class_reads_answer_a_lazy_proxy_of_a_class_as_no_class() -> None:
    """A lazy proxy forwards ``__class__``; each class read asks the proxy's real class instead."""
    lazy = _unevaluated(_Sub)
    assert kind(lazy) == "SimpleLazyObject"
    assert name(lazy) == "SimpleLazyObject"
    assert mro_entry({_Base: "base", object: "object"}, lazy) is None
    assert overrides(lazy, _Base, "meth") is False
    assert class_mro_attr(lazy, "marker") is None


@pytest.mark.parametrize(
    (
        "cls",
        "base",
        "names",
        "expected",
    ),
    [
        (
            _Sub,
            _Base,
            ("meth",),
            True,
        ),
        (
            _Override,
            _Base,
            ("cm",),
            True,
        ),
        (
            _Sub,
            _Base,
            ("marker", "cm"),
            False,
        ),
        (
            _Sub,
            _Base,
            ("prop", "meth"),
            True,
        ),
        (
            _Rewrap,
            _Base,
            ("cm", "sm", "meth"),
            False,
        ),
        (
            _ALIAS,
            _Base,
            ("cm",),
            False,
        ),
        (
            _Base,
            _Base,
            ("meth",),
            False,
        ),
        (
            _Unrelated,
            _Base,
            ("meth",),
            False,
        ),
        (
            _Sub,
            _Base,
            ("absent",),
            False,
        ),
        (
            _Sub,
            _Base,
            (),
            False,
        ),
        (
            _Base(),
            _Base,
            ("meth",),
            False,
        ),
    ],
)
def test_overrides_compares_the_stored_function(
    cls: object,
    base: type[object],
    names: tuple[str, ...],
    *,
    expected: bool,
) -> None:
    assert overrides(cls, base, *names) is expected


def test_mro_entry_picks_the_nearest_registered_class() -> None:
    assert mro_entry({_Base: "base", object: "object"}, _Sub) == (_Base, "base")
    assert mro_entry({object: "object", _Base: "base"}, _Sub) == (_Base, "base")
    assert mro_entry({_Sub: "sub", _Base: "base"}, _Sub) == (_Sub, "sub")
    assert mro_entry({_Base: None}, _Sub) == (_Base, None)


def test_mro_entry_answers_none_without_a_registered_ancestor() -> None:
    assert mro_entry({}, _Sub) is None
    assert mro_entry({_Unrelated: 1}, _Sub) is None
    assert mro_entry({object: 1}, _Base()) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (_Sub, "_Sub"),
        (_WithMetaRepr, "_WithMetaRepr"),
        (_Color, "_Color"),
        (_AbcBase, "_AbcBase"),
        (_Color.RED, "_Color"),
        (_Mixin.R, "_Mixin"),
        (_Base(), "_Base"),
        (_Base.meth, "function"),
        (1, "int"),
        (None, "NoneType"),
        (type("", (), {}), "type"),
    ],
)
def test_kind_names_a_class_by_itself_and_any_other_value_by_its_type(
    value: object,
    expected: str,
) -> None:
    assert kind(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (_Mixin.R, "r"),
        (_Choices.STAR, "STAR"),
        (_Color.RED, "_Color.RED"),
        ("plain", "plain"),
        (5, "5"),
        (_MyInt(5), "5"),
        (None, "None"),
        (True, "True"),
        (b"x", "b'x'"),
    ],
)
def test_text_spells_each_value_as_its_own_text(value: object, expected: str) -> None:
    assert text(value) == expected


def test_text_spells_classes_as_their_metaclass_does() -> None:
    NoModule = type("NoModule", (), {"__module__": None})
    assert text(int) == "<class 'int'>"
    assert text(_Sub) == f"<class '{MODULE}._Sub'>"
    assert text(_WithMetaRepr) == "custom-repr"
    assert text(_Color) == "<enum '_Color'>"
    assert text(_Outer.Inner) == f"<class '{MODULE}._Outer.Inner'>"
    assert text(NoModule) == "<class 'NoModule'>"


def test_plain_str_copies_a_str_subclass_and_passes_anything_else_through() -> None:
    """A ``TextChoices`` member comes back as its exact ``str``; a non-``str`` as itself."""

    class Color(models.TextChoices):
        RED = "red"

    sentinel = object()
    assert (type(plain_str(Color.RED)), plain_str(Color.RED), plain_str(sentinel)) == (
        str,
        "red",
        sentinel,
    )


def test_text_uses_fallback_only_for_empty_text() -> None:
    assert text("", "fallback") == "fallback"
    assert text(None, "fallback") == "None"
    assert text("") == ""


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (str.join, "join"),
        (len, "len"),
        ([1].append, "append"),
        (int.real, "real"),
        (object.__init__, "__init__"),
        ((1).__add__, "__add__"),
        (codecs.strict_errors, "strict_errors"),
        (_Base.meth, "meth"),
        (_Base().meth, "meth"),
        (_Base.cm, "_cm_func"),
        (_plain_func, "_plain_func"),
        (_Base.prop, "property"),
        (_Base(), "_Base"),
        (_Named(), "_Named"),
        (_Callable(), "_Callable"),
        (functools.partial(_plain_func), "partial"),
        (functools.lru_cache(maxsize=None)(_plain_func), "_plain_func"),
    ],
)
def test_name_answers_for_c_callables_and_callable_instances(obj: object, expected: str) -> None:
    assert name(obj) == expected


def test_name_of_a_callable_instance_is_its_stored_name_unless_empty() -> None:
    instance = _Callable()
    vars(instance)["__name__"] = "stored"
    assert name(instance) == "stored"
    vars(instance)["__name__"] = ""
    assert name(instance) == "_Callable"
