"""Tests for ``django_strawberry_framework/utils/_narrowing.py``'s checked narrowings.

``require_instance`` and ``require`` are the checked narrowings the package applies to a
value whose source guarantees its class but types it loosely. They inspect a Python value,
not a GraphQL request, so there is no live sibling in ``examples/fakeshop/test_query/``.
"""

import pytest

from django_strawberry_framework.utils._narrowing import is_str, require, require_instance


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
