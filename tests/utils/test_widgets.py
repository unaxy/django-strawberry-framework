"""Tests for the form-data keys a widget reads (``utils/widgets.py``).

``widget_keys`` / ``widget_entries`` answer, for one widget, every key it reads and the
entries binding a value under them; the form flavors bind through them
(``tests/forms/test_resolvers.py`` drives that end to end, on PostgreSQL for the real
``SplitArrayField``). These rows pin the recursion, the ``decompress`` split, the padding
and the ``size`` refusal on their own, PostgreSQL's ``SplitArrayWidget`` through its
driver-free double (``tests/_postgres_fields.py::FakeSplitArrayWidget``) and, on the
Postgres tier, as itself. ``multi_widget_keys`` is pinned by the filter rows that read it
(``tests/filters/test_sets.py``).
"""

from __future__ import annotations

import datetime

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django_filters.widgets import RangeWidget
from typing_extensions import override

from django_strawberry_framework.utils import widgets
from django_strawberry_framework.utils.widgets import widget_entries, widget_keys
from tests._postgres_fields import FakeSplitArrayWidget
from tests._soft_dependency import blocked_modules

_STAMP = datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)


class _PairWidget(forms.MultiWidget):
    """Two text boxes holding a ``"<left>:<right>"`` value."""

    def __init__(self) -> None:
        super().__init__((forms.TextInput, forms.TextInput))

    @override
    def decompress(self, value: object) -> list[object]:
        """Split ``"<left>:<right>"``; an empty value is two empty boxes."""
        if isinstance(value, str) and value:
            return list(value.split(":", 1))
        return [None, None]


class _TupleSplitWidget(forms.MultiWidget):
    """A widget whose ``decompress`` answers a value that is no list or tuple."""

    def __init__(self) -> None:
        super().__init__((forms.TextInput, forms.TextInput))

    @override
    def decompress(self, value: object) -> object:
        """Answer the value itself."""
        return value


def test_a_single_key_widget_reads_its_key_and_binds_the_value_there() -> None:
    """A ``TextInput`` reads ``key`` alone; the value is bound there unchanged."""
    widget = forms.TextInput()

    assert widget_keys(widget, "p-name") == ["p-name"]
    assert widget_entries(widget, "p-name", ["kept", "whole"]) == {"p-name": ["kept", "whole"]}


@pytest.mark.parametrize(
    ("value", "entries"),
    [
        pytest.param(
            _STAMP,
            {"stamp_0": _STAMP.date(), "stamp_1": _STAMP.time()},
            id="decompressed",
        ),
        pytest.param(
            ["2026-01-02", "03:04:05"],
            {"stamp_0": "2026-01-02", "stamp_1": "03:04:05"},
            id="list",
        ),
        pytest.param(("2026-01-02",), {"stamp_0": "2026-01-02", "stamp_1": None}, id="short"),
        pytest.param(None, {"stamp_0": None, "stamp_1": None}, id="none"),
    ],
)
def test_a_multi_widget_binds_each_part_under_its_sub_widget_key(
    value: object,
    entries: dict[str, object],
) -> None:
    """``SplitDateTimeWidget`` reads ``_0`` / ``_1``: a list is its parts, else ``decompress``."""
    widget = forms.SplitDateTimeWidget()

    assert widget_keys(widget, "stamp") == ["stamp_0", "stamp_1"]
    assert widget_entries(widget, "stamp", value) == entries


def test_a_suffixed_multi_widget_binds_under_its_own_suffixes() -> None:
    """django-filter's ``RangeWidget`` reads ``_min`` / ``_max``."""
    widget = RangeWidget()

    assert widget_keys(widget, "price") == ["price_min", "price_max"]
    assert widget_entries(widget, "price", [1, 2]) == {"price_min": 1, "price_max": 2}


def test_a_consumer_multi_widget_splits_its_value_with_its_own_decompress() -> None:
    """A consumer ``MultiWidget`` is asked for its parts; nested widgets recurse."""
    widget = forms.MultiWidget((forms.TextInput, _PairWidget()))

    assert widget_keys(widget, "f") == ["f_0", "f_1_0", "f_1_1"]
    assert widget_entries(widget, "f", ["top", "left:right"]) == {
        "f_0": "top",
        "f_1_0": "left",
        "f_1_1": "right",
    }


def test_a_decompress_answering_no_list_or_tuple_raises() -> None:
    """A ``decompress`` that splits nothing is the widget's defect, never a silent bind."""
    with pytest.raises(TypeError):
        widget_entries(_TupleSplitWidget(), "f", "whole")


@pytest.mark.parametrize(
    ("value", "entries"),
    [
        pytest.param(["a", "b", "c"], {"t_0": "a", "t_1": "b", "t_2": "c"}, id="full"),
        pytest.param(["a"], {"t_0": "a", "t_1": None, "t_2": None}, id="padded"),
        pytest.param([], {"t_0": None, "t_1": None, "t_2": None}, id="empty"),
        pytest.param(None, {"t_0": None, "t_1": None, "t_2": None}, id="none"),
        pytest.param("a", {"t_0": "a", "t_1": None, "t_2": None}, id="one-element"),
    ],
)
def test_a_split_array_widget_binds_each_element_padded_to_its_size(
    value: object,
    entries: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every ``<key>_<index>`` below ``size`` is bound, so an empty list is never omitted."""
    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    widget = FakeSplitArrayWidget(forms.TextInput(), size=3)

    assert widget_keys(widget, "t") == ["t_0", "t_1", "t_2"]
    assert widget_entries(widget, "t", value) == entries


def test_a_split_array_widget_recurses_into_its_element_widget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each element is bound through the element widget, a ``MultiWidget`` split in turn."""
    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    widget = FakeSplitArrayWidget(_PairWidget(), size=2)

    assert widget_keys(widget, "t") == [
        "t_0_0",
        "t_0_1",
        "t_1_0",
        "t_1_1",
    ]
    assert widget_entries(widget, "t", ["a:b"]) == {
        "t_0_0": "a",
        "t_0_1": "b",
        "t_1_0": None,
        "t_1_1": None,
    }


def test_a_list_longer_than_the_split_array_size_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The widget reads no key past ``size``: Django's ``ArrayMaxLengthValidator`` refuses it."""
    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
    widget = FakeSplitArrayWidget(forms.TextInput(), size=3)

    with pytest.raises(ValidationError) as caught:
        widget_entries(
            widget,
            "t",
            [
                "a",
                "b",
                "c",
                "d",
            ],
        )

    assert caught.value.code == "max_length"
    assert caught.value.messages == ["List contains 4 items, it should contain no more than 3."]


def test_the_split_array_widget_is_none_without_its_module() -> None:
    """An unimportable ``django.contrib.postgres.forms`` leaves the widget unrecognised."""
    with blocked_modules("django.contrib.postgres.forms"):
        assert widgets._postgres_split_array_widget() is None


@pytest.mark.pg
def test_the_postgres_split_array_widget_reads_one_key_per_index() -> None:
    """PostgreSQL's own ``SplitArrayWidget`` is the sentinel and binds as its double does."""
    from django.contrib.postgres.forms import SplitArrayWidget  # noqa: PLC0415 - needs the Postgres driver

    assert widgets._SPLIT_ARRAY_WIDGET is SplitArrayWidget
    widget = SplitArrayWidget(forms.NumberInput, size=2)
    assert widget_keys(widget, "n") == ["n_0", "n_1"]
    assert widget_entries(widget, "n", [7]) == {"n_0": 7, "n_1": None}
