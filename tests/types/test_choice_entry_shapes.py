"""A choice entry is unpacked as a pair only once it is proven iterable.

``types/converters.py::_unpack_choice_entry`` reads one consumer-declared choice
entry as its ``(value, label)`` pair. An entry that is not iterable at all is the
same malformed declaration as a short or long pair and gets the same typed
refusal, raised before any unpacking is attempted. A text atom (text, bytes-like,
or a lazy translation string) is malformed even at length two.
"""

from __future__ import annotations

import pytest
from django.utils.functional import SimpleLazyObject, lazy
from django.utils.translation import gettext_lazy

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.types.converters import build_enum_from_choices
from django_strawberry_framework.utils._narrowing import enum_value


def test_non_iterable_choice_entry_is_a_malformed_choice() -> None:
    """A bare integer entry is refused as a malformed choice."""
    with pytest.raises(ConfigurationError, match="declares a malformed choice 1;"):
        build_enum_from_choices([1], "ChoiceEntryShapeEnum", source_label="probe")


def test_pair_choice_entry_builds_its_member() -> None:
    """A ``(value, label)`` pair still builds the enum member it declares."""
    enum_cls = build_enum_from_choices([("a", "A")], "ChoiceEntryShapeEnum", source_label="probe")

    assert [enum_value(member) for member in enum_cls] == ["a"]


@pytest.mark.parametrize(
    "entry",
    [
        pytest.param("ab", id="str"),
        pytest.param(b"ab", id="bytes"),
        pytest.param(bytearray(b"ab"), id="bytearray"),
        pytest.param(memoryview(b"ab"), id="memoryview"),
        pytest.param(gettext_lazy("ab"), id="lazy-translation"),
        pytest.param(SimpleLazyObject(lambda: gettext_lazy("ab")), id="simple-lazy-over-lazy"),
        pytest.param(SimpleLazyObject(lambda: "ab"), id="simple-lazy-str"),
        pytest.param(lazy(lambda: ("a", "A"), tuple)(), id="lazy-translation-tuple"),
    ],
)
def test_two_character_text_entry_is_a_malformed_choice(entry: object) -> None:
    """A length-two text atom is one value, never a pair read off its two characters.

    Unpacking would accept ``"ab"`` as the pair ``("a", "b")`` (bytes-like values as two byte
    integers). A lazy translation string walks its text the same way, a ``SimpleLazyObject`` is
    read as the object it stands for, and every lazy ``Promise`` is text whatever result class
    it wraps, so a lazy tuple is refused with it.
    """
    with pytest.raises(ConfigurationError, match="declares a malformed choice"):
        build_enum_from_choices([entry], "ChoiceEntryShapeEnum", source_label="probe")


def test_simple_lazy_pair_choice_entry_builds_its_member() -> None:
    """A ``SimpleLazyObject`` over a ``(value, label)`` pair is that pair."""
    enum_cls = build_enum_from_choices(
        [SimpleLazyObject(lambda: ("a", "A"))],
        "ChoiceEntryShapeEnum",
        source_label="probe",
    )

    assert [enum_value(member) for member in enum_cls] == ["a"]
