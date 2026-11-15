"""A dict is a per-field operator bag only when every key is a lookup-attr string.

``filters/sets.py::FilterSet._operator_bag_items`` decides whether a dict is a
per-field operator bag (every key a lookup attr) and returns its pairs; a dict
with a key that is not a string, or with no key at all, is no bag.
"""

from __future__ import annotations

from django_strawberry_framework.filters.sets import FilterSet


def test_non_string_key_makes_the_dict_no_bag() -> None:
    """A key that is not a string names no lookup, so the dict is not an operator bag."""
    assert FilterSet._operator_bag_items({1: "x"}, ()) is None


def test_empty_dict_is_no_bag() -> None:
    """An empty dict carries no lookup, so it is not an operator bag."""
    assert FilterSet._operator_bag_items({}, ()) is None
