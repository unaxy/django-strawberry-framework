"""Bind normalized filter values through the actual consumer form and widget readers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from django import forms
from django.forms import MultiWidget, Widget
from django.utils.datastructures import MultiValueDict
from typing_extensions import override

from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import (
    is_list_or_tuple,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.typing import object_result
from django_strawberry_framework.utils.widgets import bound_value, widget_entries, widget_keys

from .inputs import _range_widget_keys

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from django_filters import Filter
    from typing_extensions import TypeIs


@dataclass(frozen=True)
class NormalizedFormValue:
    """One normalized logical field and its original canonical data keys, never raw input."""

    name: str
    declaration: Filter
    axes: tuple[str, str] | None = None

    def supplied(self, current: Mapping[str, object]) -> bool:
        """Return whether current data still supplies this logical field or range axis."""
        keys = (self.name,) if self.axes is None else self.axes
        return any(key in current for key in keys)

    def render(
        self,
        current: Mapping[str, object],
        widget: Widget,
        html_name: str,
    ) -> dict[str, object] | None:
        """Read CURRENT data so constructor copies, value edits and removals win."""
        if self.axes is None:
            if self.name not in current:
                return None
            # A widget reading the canonical key already has its input; do not alter
            # current dict/QueryDict semantics on the ordinary, existing path.
            if widget_keys(widget, html_name) == [self.name]:
                return None
            return widget_entries(widget, html_name, bound_value(current, self.name))
        actual = list(_range_widget_keys(self.declaration, widget, html_name))
        if tuple(actual) == self.axes and widget_keys(widget, html_name) == actual:
            return None
        # Range axes may themselves be multi-widget fields (SplitDateTimeField).
        # Keep the supplied-axis mask, then use the same recursive widget owner
        # used for ordinary fields; never write an entire bound to an unread key.
        widget = require_instance(widget, MultiWidget)
        entries: dict[str, object] = {}
        for index, original in enumerate(self.axes):
            if original in current:
                entries.update(
                    widget_entries(
                        widget.widgets[index],
                        actual[index],
                        bound_value(current, original),
                    ),
                )
        return entries


@dataclass(frozen=True)
class FilterFormBindings:
    """Per-construction metadata held outside data; constructor copies keep current values."""

    values: Mapping[str, NormalizedFormValue]

    def names(self, current: Mapping[str, object]) -> frozenset[str]:
        """Return the logical fields the current constructor data still names."""
        return frozenset(
            name for name, binding in self.values.items() if binding.supplied(current)
        )

    def supplied(self, name: str, current: Mapping[str, object]) -> bool:
        """Return whether one logical field remains present in current form data."""
        binding = self.values.get(name)
        return binding is not None and binding.supplied(current)


class _WidgetData(Mapping[str, object]):
    """Reader overlay for semantic values and explicit current physical entries.

    Untouched values are read only when the widget asks for them: an unrelated
    disabled field or lazy consumer mapping is never read while copying data.
    An automatic get reader sees one semantic object; an automatic getlist reader
    sees its members. A custom opaque grouping cannot be inferred: its Meta.form
    binds physical keys explicitly, which take precedence over derived entries.

    Derived entries keep plain-dict widget semantics.

    A SelectMultiple asks getlist and receives the derived list whole; a TextInput
    asks get and receives the SAME list whole. Untouched keys retain the original
    mapping's getter/list getter behavior. No choice is made from the value type.
    """

    _current: Mapping[str, object]
    _entries: dict[str, object]

    def __init__(self, current: Mapping[str, object], entries: Mapping[str, object]) -> None:
        self._current = current
        self._entries = {key: value for key, value in entries.items() if key not in current}

    @override
    def __getitem__(self, key: str) -> object:
        if key in self._entries:
            return self._entries[key]
        return self._current[key]

    @override
    def __iter__(self) -> Iterator[str]:
        return iter(dict.fromkeys((*self._current, *self._entries)))

    @override
    def __len__(self) -> int:
        return len(dict.fromkeys((*self._current, *self._entries)))

    @override
    def __contains__(self, key: object) -> bool:
        return key in self._entries or key in self._current

    @override
    def get(self, key: str, default: object = None) -> object:
        if key in self._entries:
            return self._entries[key]
        return self._current.get(key, default)


class _ListedWidgetData(_WidgetData):
    """Expose getlist only when the consumer's current mapping exposes that reader."""

    _getter: Callable[..., object]

    def __init__(
        self,
        current: Mapping[str, object],
        entries: Mapping[str, object],
        getter: Callable[..., object],
    ) -> None:
        super().__init__(current, entries)
        self._getter = getter

    def getlist(self, key: str, *args: object, **kwargs: object) -> object:
        if key in self._entries:
            value = self._entries[key]
            if value is None:
                return []
            return list(value) if is_list_or_tuple(value) else [value]
        return self._getter(key, *args, **kwargs)


class _AliasedWidgetData(Mapping[str, object]):
    """Re-key one raw input without reading, copying or regrouping any values."""

    _current: Mapping[str, object]
    _alias: str
    _source: str
    _getter: Callable[..., object]

    def __init__(
        self,
        current: Mapping[str, object],
        alias: str,
        source: str,
        getter: Callable[..., object],
    ) -> None:
        self._current = current
        self._alias = alias
        self._source = source
        self._getter = getter

    def _key(self, key: str) -> str:
        return self._source if key == self._alias else key

    @override
    def __getitem__(self, key: str) -> object:
        return self._current[self._key(key)]

    @override
    def __iter__(self) -> Iterator[str]:
        return iter(dict.fromkeys((*self._current, self._alias)))

    @override
    def __len__(self) -> int:
        return len(dict.fromkeys((*self._current, self._alias)))

    @override
    def __contains__(self, key: object) -> bool:
        return self._source in self._current if key == self._alias else key in self._current

    @override
    def get(self, key: str, default: object = None) -> object:
        return self._current.get(self._key(key), default)

    def getlist(self, key: str, *args: object, **kwargs: object) -> object:
        return self._getter(self._key(key), *args, **kwargs)


class _BoundFilterForm(forms.Form):
    """Bind after the consumer's cooperative form overrides."""

    _filter_bindings: ClassVar[FilterFormBindings]

    def _widget_data_value(self, widget: Widget, html_name: str) -> object:
        # The actual generated/consumer Form class precedes this mixin, so its
        # cooperative override reaches us AFTER its current-data edits.
        binding = next(
            (
                value
                for name, value in self._filter_bindings.values.items()
                if name in self.fields and self.add_prefix(name) == html_name
            ),
            None,
        )
        current: Mapping[str, object] = self.data
        reads: Mapping[str, object] = current
        field_name = next(
            (name for name in self.fields if self.add_prefix(name) == html_name),
            None,
        )
        disabled = field_name is not None and self.fields[field_name].disabled
        if binding is not None and not disabled:
            actual_keys = widget_keys(widget, html_name)
            canonical = {binding.name} if binding.axes is None else set(binding.axes)
            physical_keys = [key for key in actual_keys if key not in canonical]
            completely_physical = bool(physical_keys) and all(
                key in current for key in physical_keys
            )
            if not completely_physical:
                if (
                    binding.axes is None
                    and binding.name in current
                    and actual_keys == [html_name]
                    and html_name != binding.name
                    and isinstance(current, MultiValueDict)
                ):
                    # Preserve get versus getlist from the original container for
                    # a one-key alias; no final value is extracted first.
                    reads = _AliasedWidgetData(
                        current,
                        html_name,
                        binding.name,
                        current.getlist,
                    )
                else:
                    entries = binding.render(current, widget, html_name)
                    if entries is not None:
                        getter = read_attr(current, "getlist", None)
                        reads = (
                            _ListedWidgetData(current, entries, getter)
                            if callable(getter)
                            else _WidgetData(current, entries)
                        )
        # Django BaseForm._widget_data_value delegates to the widget's own reader.
        # Ask that public seam directly; form.data itself is never temporarily
        # replaced, so consumer callbacks always see their own current data.
        return object_result(widget.value_from_datadict, reads, self.files, html_name)


def _is_form_class(value: object) -> TypeIs[type[forms.Form]]:
    """Whether ``value`` is a Django ``Form`` subclass; asked of the class ``type()`` built."""
    return truth.is_subclass(value, forms.Form)


def bound_filter_form_class(
    actual: type[forms.Form],
    bindings: FilterFormBindings,
) -> type[forms.Form]:
    """Keep all consumer form overrides ahead of the new actual-widget binding seam.

    Bare ``forms.Form`` cannot precede the mixin, which inherits it (no consistent MRO),
    so it is replaced by the mixin; every other form class keeps its place ahead of it.
    """
    bases = (_BoundFilterForm,) if actual is forms.Form else (actual, _BoundFilterForm)
    return require(
        object_result(
            type,
            truth.name(actual),
            bases,
            {"_filter_bindings": bindings, "__module__": truth.module(actual)},
        ),
        _is_form_class,
    )
