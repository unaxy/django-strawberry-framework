"""Bind normalized filter values through the actual consumer form and widget readers.

``BindAskingFilterForm`` refuses unstorable text before fields clean, prepares a
missing automatic inner parser before field cleaning, and binds final active values
after the entire consumer clean. A pipeline may defer that last ask until root and
logical-arm forms finish native cleaning. Every refusal enters the actual form errors.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from django import forms
from django.core.exceptions import ValidationError
from django.forms import MultiWidget, Widget
from django.forms.utils import ErrorDict
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
    """Keep all consumer form overrides ahead of the actual-widget binding seam.

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


@dataclass(frozen=True)
class FilterFormAsks:
    """The owning filter set's preparation and refusals a bound filter form runs.

    ``unstorable_text`` reads each field's data as its widget hands it to ``clean``;
    ``prepare_comparisons`` installs missing source-aware inner cleaners before fields clean;
    ``prepare_binding`` acquires valid active postclean source context or defers it to
    the apply pipeline; ``unbindable_values`` reads the final ``cleaned_data``
    (``filters/sets.py::_unstorable_text_errors``, ``filters/sets.py::_unbindable_value_errors``).
    """

    reset_binding: Callable[[], None]
    unstorable_text: Callable[[forms.BaseForm], Mapping[str, ValidationError]]
    prepare_comparisons: Callable[[forms.BaseForm], None]
    prepare_binding: Callable[[forms.BaseForm], bool]
    unbindable_values: Callable[[forms.BaseForm], Mapping[str, ValidationError]]


class BindAskingFilterForm(forms.Form):
    """Refuse, as the form's own errors, unstorable text and each value the database cannot bind.

    The generated owner encloses every consumer ``full_clean`` / ``clean`` /
    ``_post_clean`` call, so the bind ask reads the ``cleaned_data`` they leave. A
    pipeline defers new bind-only source acquisition until its root and logical
    forms have finished native cleaning without ordinary errors. An
    inherited generated form delegates its ask while the current owner cleans, even
    through multiple public ``Meta.form`` reuse generations. ``_filter_asks`` holds the
    owner's asks (``FilterFormAsks``), stored in the class the filter set builds; each refusal enters
    the form through ``add_error``, so django-filter's ``is_valid()`` / ``errors``,
    ``DjangoFilterBackend``'s ``raise_exception`` and ``FilterView``'s ``strict`` see it,
    and the refused value leaves ``cleaned_data``, so ``BaseFilterSet.qs`` never binds it.
    """

    _filter_asks: ClassVar[FilterFormAsks]
    _errors: ErrorDict | None
    cleaned_data: dict[str, object]
    _filter_asking_active: bool
    _filter_cleaning_cached: bool
    _filter_cleaning_route: bool | None
    _filter_bind_finalized: bool

    @override
    def full_clean(self) -> None:
        """Clean the bound form, refusing unstorable text first and unbindable values after.

        An unbound form, and an empty-permitted one whose data has not changed, clean as
        Django cleans them (``super().full_clean()``), consumer overrides included.
        An unchanged bound form normally needs no ask; if its consumer outer
        ``full_clean`` adds an active final value after Django's early return, that
        value is bind-asked on this same form. Change detection itself may read an
        owned widget; a refusal from that widget is the field's form error.
        Otherwise a field holding text the
        package refuses (``utils/errors.py::unstorable_text``) is refused before any field cleans, and
        cleaning is skipped, so only those refusals are the form's errors; with no such
        text the form cleans as Django cleans it, consumer overrides included, and
        local or cached-source bind refusals can join its errors. An uncached
        bind-only source is acquired only after the whole native validation domain
        has no ordinary form error; raw forms stage their logical siblings too.
        """
        self._ask_full_clean(super().full_clean)

    def _ask_full_clean(self, clean: Callable[[], None]) -> None:
        """Enclose the actual form's whole clean in exactly one owning pair of asks."""
        if getattr(self, "_filter_asking_active", False):
            # Every generated form in a reuse chain delegates to the current
            # outer owner, including a generated form reused more than once.
            clean()
            return
        if read_attr(self, "_errors", None) is not None:
            # An explicit second full_clean starts another native generation.
            # The earlier widget/change route belonged to the first one.
            self._filter_cleaning_cached = False
            self._filter_text_errors = None
        self._filter_bind_finalized = False
        self._filter_asks.reset_binding()
        route = self._field_cleaning_route()
        if route is None:
            return
        if not route:
            self._filter_asking_active = True
            try:
                clean()
            finally:
                self._filter_asking_active = False
            # An unchanged bound form normally cleans no fields. A consumer's
            # outer full_clean may nevertheless create a final active value
            # after Django's early return; ask that value on this same form.
            if (
                self.is_bound
                and read_attr(self, "cleaned_data", {})
                and self._filter_asks.prepare_binding(self)
            ):
                self._finish_binding()
            return
        asks = self._filter_asks
        refusals = self._text_refusals()
        if refusals:
            self._add_preflight_errors(refusals)
            return
        asks.prepare_comparisons(self)
        self._filter_asking_active = True
        try:
            clean()
        finally:
            self._filter_asking_active = False
        if asks.prepare_binding(self):
            self._finish_binding()

    _filter_text_errors: Mapping[str, ValidationError] | None = None

    def _text_refusals(self) -> Mapping[str, ValidationError]:
        """Reuse the owner's preflight when the pipeline has already asked this form."""
        if self._filter_text_errors is None:
            self._filter_text_errors = self._filter_asks.unstorable_text(self)
        return self._filter_text_errors

    def _finish_binding(self) -> None:
        """Add the current owner's bind refusals once after the entire actual clean."""
        if getattr(self, "_filter_bind_finalized", False):
            return
        refusals = self._filter_asks.unbindable_values(self)
        for name, refusal in refusals.items():
            self.add_error(name, refusal)
        self._filter_bind_finalized = True

    def _field_cleaning_route(self) -> bool | None:
        """Reuse this form's native change decision before comparison preparation.

        ``True`` means fields clean, ``False`` delegates to Django's unchanged
        or unbound path, and ``None`` means the actual widget already supplied
        a matching form error. The pipeline may ask before ``full_clean``;
        ``_ask_full_clean`` reads the same decision without a second widget read.
        """
        if getattr(self, "_filter_cleaning_cached", False):
            return self._filter_cleaning_route
        route: bool | None = self.is_bound
        if route and self.empty_permitted:
            try:
                route = self.has_changed()
            except ValidationError as error:
                # Change detection reads widgets too. Only a refusal recovered from
                # this form's actual widget belongs to our preflight boundary.
                refusals = self._filter_asks.unstorable_text(self)
                if not any(refusal == error for refusal in refusals.values()):
                    raise
                self._add_preflight_errors(refusals)
                route = None
        self._filter_cleaning_route = route
        self._filter_cleaning_cached = True
        return route

    def _add_preflight_errors(self, refusals: Mapping[str, ValidationError]) -> None:
        # Adapted from Django BaseForm.full_clean (BSD-3-Clause; LICENSE.django):
        # reset errors and cleaned data before adding field errors.
        self._errors = ErrorDict(renderer=self.renderer)
        self.cleaned_data = {}
        for name, refusal in refusals.items():
            self.add_error(name, refusal)


def _is_bind_asking_form_class(value: object) -> TypeIs[type[BindAskingFilterForm]]:
    """Whether ``value`` is a ``BindAskingFilterForm`` subclass; asked of the class ``type()`` built."""
    return truth.is_subclass(value, BindAskingFilterForm)


def bind_asking_form_class(
    actual: type[forms.Form],
    asks: FilterFormAsks,
) -> type[BindAskingFilterForm]:
    """Put one owning ask around the actual form, including an inherited asking form."""
    if issubclass(actual, BindAskingFilterForm):
        # A generated form is a supported Meta.form. Keep its consumer subclasses
        # inside this owner's boundary; their inherited ask delegates while active.
        def full_clean(self: BindAskingFilterForm) -> None:
            self._ask_full_clean(lambda: super(owned, self).full_clean())

        owned = require(
            object_result(
                type,
                truth.name(actual),
                (actual,),
                {
                    "_filter_asks": asks,
                    "full_clean": full_clean,
                    "__module__": truth.module(actual),
                },
            ),
            _is_bind_asking_form_class,
        )
        return owned
    return require(
        object_result(
            type,
            truth.name(actual),
            (BindAskingFilterForm, actual),
            {"_filter_asks": asks, "__module__": truth.module(actual)},
        ),
        _is_bind_asking_form_class,
    )
