"""Tests for ``django_strawberry_framework/utils/_narrowing.py``'s checked narrowings.

``require_instance`` and ``require`` are the checked narrowings the package applies to a
value whose source guarantees its class but types it loosely; the ``is_exact_*`` container
predicates prove a builtin type without consulting the value's class. They inspect a Python
value, not a GraphQL request, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

from collections.abc import Callable

import pytest
from typing_extensions import override

from django_strawberry_framework.utils._narrowing import (
    is_char_wise,
    is_exact_list_or_tuple,
    is_exact_set_or_frozenset,
    is_str,
    require,
    require_instance,
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
    [is_exact_list_or_tuple, is_exact_set_or_frozenset],
    ids=["list_or_tuple", "set_or_frozenset"],
)
def test_exact_container_predicate_refuses_a_class_whose_metaclass_eq_claims_a_builtin(
    predicate: Callable[[object], bool],
) -> None:
    """The type is compared by identity, so the metaclass ``__eq__`` neither runs nor decides."""
    _ClaimsEveryClassMeta.eq_calls.clear()

    assert predicate(_ClaimsEveryClass()) is False
    assert _ClaimsEveryClassMeta.eq_calls == []
