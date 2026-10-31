"""Filter form overlays preserve lazy mapping reads and QueryDict copy protocols.

The raising unused-value and str.__deepcopy__ protocols are Python observations,
so they stay package-side. Ordinary disabled-field and prefixed widget rowsets
remain live in test_filter_widget_binding_api.py.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping

import django_filters
from django import forms
from django.http import QueryDict
from typing_extensions import Self, override

from django_strawberry_framework.filters.form_binding import (
    FilterFormBindings,
    NormalizedFormValue,
    bound_filter_form_class,
)


class _PairField(forms.MultiValueField):
    def __init__(self) -> None:
        super().__init__(
            fields=[forms.CharField(), forms.CharField()],
            widget=forms.MultiWidget([forms.TextInput(), forms.TextInput()]),
        )

    @override
    def compress(self, data_list: list[object]) -> tuple[str, ...]:
        return tuple(str(value) for value in data_list)


def test_widget_overlay_does_not_read_unrequested_mapping_values() -> None:
    """Binding one widget never reads the value a disabled sibling does not request."""

    class DeferredData(Mapping[str, object]):
        def __init__(self, source: Mapping[str, object]) -> None:
            self._source = source

        @override
        def __getitem__(self, key: str) -> object:
            if key == "ignored":
                raise ValueError("The disabled input has no decoded value.")
            return self._source[key]

        @override
        def __iter__(self) -> Iterator[str]:
            return iter(self._source)

        @override
        def __len__(self) -> int:
            return len(self._source)

        @override
        def __contains__(self, key: object) -> bool:
            return key in self._source

    class PairForm(forms.Form):
        pick = _PairField()
        ignored = forms.CharField(disabled=True, initial="unused")

    data = DeferredData({"pick": ["Alpha", "Beta"], "ignored": "untrusted"})
    bindings = FilterFormBindings({"pick": NormalizedFormValue("pick", django_filters.Filter())})
    form = bound_filter_form_class(PairForm, bindings)(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data == {"pick": ("Alpha", "Beta"), "ignored": "unused"}
    assert form.data is data


def test_single_key_alias_does_not_copy_unrequested_querydict_values() -> None:
    """Re-keying one posted list never invokes an unused str subclass's copy protocol."""

    class UncopiedText(str):
        def __deepcopy__(self, _memo: dict[int, object]) -> Self:
            raise RuntimeError("An unrelated posted value must never be deep-copied.")

    class ChoiceForm(forms.Form):
        prefix: str | None = "search"
        pick = forms.MultipleChoiceField(choices=[("Alpha", "Alpha"), ("Beta", "Beta")])

    data = QueryDict(mutable=True)
    data.setlist("pick", ["Alpha", "Beta"])
    data["unrelated"] = UncopiedText("Never needed by this form")
    bindings = FilterFormBindings({"pick": NormalizedFormValue("pick", django_filters.Filter())})
    form = bound_filter_form_class(ChoiceForm, bindings)(data=data)

    assert form.is_valid(), form.errors
    assert form.cleaned_data == {"pick": ["Alpha", "Beta"]}
    assert form.data is data
    assert "search-pick" not in data
