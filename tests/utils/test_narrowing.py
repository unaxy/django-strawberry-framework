"""Tests for ``django_strawberry_framework/utils/_narrowing.py``'s checked narrowings.

``require_instance`` and ``require`` are the checked narrowings the package applies to a
value whose source guarantees its class but types it loosely; the ``is_exact_*`` container
predicates prove a builtin type without consulting the value's class. They inspect a Python
value, not a GraphQL request, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

from collections import UserDict
from collections.abc import Callable, Collection, Mapping

import pytest
from django.db import models
from django.utils.functional import Promise, lazy
from django.utils.translation import gettext_lazy
from typing_extensions import override

from django_strawberry_framework.utils._narrowing import (
    del_item,
    get_item,
    is_char_wise,
    is_concrete_field,
    is_exact_list_or_tuple,
    is_exact_set_or_frozenset,
    is_exact_tuple_or_frozenset,
    is_queryset,
    is_real_collection,
    is_real_mapping,
    is_str,
    is_text_atom,
    iter_of,
    optional_annotation,
    require,
    require_instance,
    set_item,
)
from tests._idioms import ClaimsClassBase


def test_require_instance_returns_an_instance_of_the_class_unchanged() -> None:
    """A value of the class, a subclass included, comes back as the same object."""
    value = True

    assert require_instance(value, int) is value


def test_require_instance_refuses_a_value_of_another_class() -> None:
    """A value outside the class raises ``TypeError`` naming the class it had to be and its own."""
    with pytest.raises(TypeError, match=r"^expected an instance of int, got str$"):
        _ = require_instance("1", int)


def test_require_returns_a_value_the_predicate_accepts_unchanged() -> None:
    """A value the ``TypeIs`` predicate accepts comes back as the same object."""
    value = "text"

    assert require(value, is_str) is value


def test_require_refuses_a_value_the_predicate_rejects() -> None:
    """A value the predicate rejects raises ``TypeError`` naming the value's type."""
    with pytest.raises(TypeError, match=r"^expected the type the source guarantees, got int$"):
        _ = require(1, is_str)


class _StrSubclass(str):
    """A ``str`` subclass, which is still text."""

    __slots__ = ()


class _ClaimsStr(ClaimsClassBase):
    """A value whose ``__class__`` claims ``str``; its real class is not text."""

    __slots__ = ()
    claimed: type = str


class _ClaimsPromise(ClaimsClassBase):
    """A value whose ``__class__`` claims ``Promise``; its real class is not a lazy proxy."""

    __slots__ = ()
    claimed: type = Promise


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("text", True),
        (_StrSubclass("text"), True),
        (b"bytes", True),
        (bytearray(b"bytes"), True),
        (memoryview(b"bytes"), True),
        (["text"], False),
        ({"text": 1}, False),
        (1, False),
        (_ClaimsStr(), False),
    ],
    ids=[
        "str",
        "str_subclass",
        "bytes",
        "bytearray",
        "memoryview",
        "list",
        "dict",
        "int",
        "class_claims_str",
    ],
)
def test_is_char_wise_asks_the_real_class(value: object, expected: bool) -> None:  # noqa: FBT001 - the expected verdict
    """Text and bytes-like values pass, subclasses included; a ``__class__`` claim does not."""
    assert is_char_wise(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("text", True),
        (b"bytes", True),
        (memoryview(b"bytes"), True),
        (gettext_lazy("text"), True),
        (lazy(lambda: ["text"], list)(), True),
        (["text"], False),
        (1, False),
        (_ClaimsStr(), False),
        (_ClaimsPromise(), False),
    ],
    ids=[
        "str",
        "bytes",
        "memoryview",
        "gettext_lazy",
        "lazy_list",
        "list",
        "int",
        "class_claims_str",
        "class_claims_promise",
    ],
)
def test_is_text_atom_counts_a_lazy_promise_as_text(value: object, expected: bool) -> None:  # noqa: FBT001 - the expected verdict
    """A Django lazy ``Promise`` is text, judged by its real class and never evaluated.

    Every ``Promise`` counts, whatever its result class, since the proxy does not
    expose which one it stands for without evaluating it; Django's own
    ``smart_str`` reads every ``Promise`` as text the same way.
    """
    assert is_text_atom(value) is expected


def test_is_text_atom_never_evaluates_a_lazy_promise() -> None:
    """The verdict on a lazy proxy is read from its class: the wrapped function never runs."""
    calls: list[str] = []

    def translate() -> str:
        calls.append("run")
        return "text"

    assert is_text_atom(lazy(translate, str)()) is True
    assert calls == []


class _TupleSubclass(tuple[object, ...]):
    """A ``tuple`` subclass: an instance passes ``isinstance`` for ``tuple`` but is not one exactly."""


class _FrozensetSubclass(frozenset[object]):
    """A ``frozenset`` subclass, as ``_TupleSubclass`` is for ``tuple``."""


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ((), True),
        (("alias",), True),
        (frozenset[object](), True),
        (frozenset({"alias"}), True),
        (_TupleSubclass(), False),
        (_FrozensetSubclass(), False),
        (list[object](), False),
        (set[object](), False),
        ("alias", False),
    ],
    ids=[
        "empty_tuple",
        "tuple",
        "empty_frozenset",
        "frozenset",
        "tuple_subclass",
        "frozenset_subclass",
        "list",
        "set",
        "str",
    ],
)
def test_is_exact_tuple_or_frozenset_admits_exactly_the_two_builtins(
    value: object,
    expected: bool,  # noqa: FBT001 - the expected verdict
) -> None:
    """Only an exact ``tuple`` or ``frozenset`` passes; a subclass of either is refused."""
    assert is_exact_tuple_or_frozenset(value) is expected


class _ClaimsEveryClassMeta(type):
    """A metaclass whose ``__eq__`` claims equality with every class and records each call."""

    eq_calls: list[object] = []

    @override
    def __eq__(cls, other: object) -> bool:
        _ClaimsEveryClassMeta.eq_calls.append(other)
        return True

    __hash__ = type.__hash__


class _ClaimsEveryClass(metaclass=_ClaimsEveryClassMeta):
    """A class that compares equal to ``list``, ``tuple``, ``set`` and ``frozenset``."""


@pytest.mark.parametrize(
    "predicate",
    [is_exact_list_or_tuple, is_exact_set_or_frozenset, is_exact_tuple_or_frozenset],
    ids=["list_or_tuple", "set_or_frozenset", "tuple_or_frozenset"],
)
def test_exact_container_predicate_refuses_a_class_whose_metaclass_eq_claims_a_builtin(
    predicate: Callable[[object], bool],
) -> None:
    """The type is compared by identity, so the metaclass ``__eq__`` neither runs nor decides."""
    _ClaimsEveryClassMeta.eq_calls.clear()

    assert predicate(_ClaimsEveryClass()) is False
    assert _ClaimsEveryClassMeta.eq_calls == []


def test_is_concrete_field_accepts_a_model_field_and_refuses_a_reverse_relation() -> None:
    """A model ``Field`` passes; a reverse ``ForeignObjectRel`` and a non-field do not."""
    forward: models.TextField[str, str] = models.TextField()
    reverse = models.ManyToOneRel(models.ForeignKey("self", models.CASCADE), models.Model, "id")

    assert is_concrete_field(forward) is True
    assert is_concrete_field(reverse) is False
    assert is_concrete_field("text") is False


def test_is_queryset_accepts_a_queryset_and_refuses_a_manager_and_a_list() -> None:
    """A ``QuerySet`` passes whatever its rows; a manager or a list does not."""
    queryset: models.QuerySet[models.Model, object] = models.QuerySet(models.Model)

    assert is_queryset(queryset) is True
    manager: models.Manager[models.Model] = models.Manager()
    assert is_queryset(manager) is False
    assert is_queryset([]) is False


class _ClaimsMapping(ClaimsClassBase):
    """A value whose ``__class__`` claims ``Mapping``; its real class is not one."""

    __slots__ = ()
    claimed: type = Mapping


class _ClaimsCollection(ClaimsClassBase):
    """A value whose ``__class__`` claims ``Collection``; its real class is not one."""

    __slots__ = ()
    claimed: type = Collection


def test_is_real_mapping_asks_the_real_class() -> None:
    """A ``Mapping`` (a virtual subclass included) passes; a ``__class__`` claim does not."""
    assert is_real_mapping({"a": 1}) is True
    mapping: UserDict[str, int] = UserDict()
    assert is_real_mapping(mapping) is True
    assert is_real_mapping([("a", 1)]) is False
    assert is_real_mapping(_ClaimsMapping()) is False


def test_is_real_collection_asks_the_real_class() -> None:
    """A ``Collection`` passes; an iterator, a plain object and a ``__class__`` claim do not."""
    assert is_real_collection([1]) is True
    assert is_real_collection({1}) is True
    assert is_real_collection(iter([1])) is False
    assert is_real_collection(1) is False
    assert is_real_collection(_ClaimsCollection()) is False


def test_optional_annotation_widens_an_annotation_with_none() -> None:
    """A class widens to ``class | None``; a value with no ``|`` raises what the expression raises."""
    assert optional_annotation(int) == int | None
    with pytest.raises(TypeError):
        _ = optional_annotation(1)


def test_item_slots_run_the_subscript_operations() -> None:
    """``get_item`` / ``set_item`` / ``del_item`` are ``container[key]``, ``= value`` and ``del``."""
    container: dict[str, int] = {}

    set_item(container, "a", 1)

    assert get_item(container, "a") == 1
    del_item(container, "a")
    assert container == {}
    with pytest.raises(KeyError):
        _ = get_item(container, "a")
    with pytest.raises(TypeError):
        _ = get_item(object(), "a")


def test_iter_of_iterates_an_iterable_and_refuses_a_value_that_is_not() -> None:
    """``iter_of`` is ``iter``: an iterable yields its members, a bare value raises ``TypeError``."""
    assert list(iter_of([1, 2])) == [1, 2]
    with pytest.raises(TypeError):
        _ = iter_of(1)
