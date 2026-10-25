"""The form-data keys a Django widget reads, and the entries that bind a value under them.

The one owner of "which keys a widget reads", shared by the filter and form subsystems,
neither of which owns a widget:

- ``multi_widget_keys`` - the keys a ``MultiWidget`` (django-filter's
  ``SuffixedMultiWidget`` included) reads for a field name; the filter side types and
  binds a range filter's bounds through it and names a flat copy by it;
- ``widget_keys`` / ``widget_entries`` - every key a widget reads, recursing into a
  ``MultiWidget``'s and PostgreSQL's ``SplitArrayWidget``'s sub-widgets, and the
  form-data entries binding one value under them; the form flavors bind each field's
  value through them (``forms/resolvers.py::_bind_under_form_keys``).
"""

from __future__ import annotations

from django.contrib.postgres.validators import ArrayMaxLengthValidator
from django.forms import MultiWidget, Widget
from django_filters.widgets import SuffixedMultiWidget

from . import truth
from ._narrowing import (
    call_method,
    is_list_or_tuple,
    list_of,
    read_attr,
    require,
    require_instance,
)
from .imports import import_attr_if_importable

__all__ = ("multi_widget_keys", "widget_entries", "widget_keys")


def _postgres_split_array_widget() -> type[Widget] | None:
    """Return ``django.contrib.postgres.forms.SplitArrayWidget``, or ``None``.

    Soft-imported through the shared optional-import owner: the module imports a
    PostgreSQL driver, so it is unavailable on an environment without one, where no
    consumer form can declare the widget either.
    """
    cls = import_attr_if_importable("django.contrib.postgres.forms", "SplitArrayWidget")
    return cls if truth.is_subclass(cls, Widget) else None


#: PostgreSQL's ``SplitArrayWidget`` (``None`` without a PostgreSQL driver).
_SPLIT_ARRAY_WIDGET = _postgres_split_array_widget()


# Audited upstream, every published release from the floor to the latest:
#
#   django-filter 21.1 -> 26.2   ``SuffixedMultiWidget`` reads ``suffixed(name, suffix)`` per
#                                ``suffixes``: ``RangeWidget`` ``min`` / ``max``,
#                                ``DateRangeWidget`` ``after`` / ``before``
#   Django 5.2.16 -> 6.1.2       ``MultiWidget`` reads ``name + widgets_names[i]`` through
#                                ``widgets[i]``: ``_0`` / ``_1`` for a two-widget sequence;
#                                ``get_context`` splits a value that is no list or tuple
#                                with ``decompress`` and gives a missing part ``None``
#   Django 5.2.16 -> 6.1.2       ``SplitArrayWidget`` reads ``"%s_%s" % (name, index)``
#                                through ``widget`` for each index in ``range(size)``, and
#                                ignores every key past ``size``; ``ArrayMaxLengthValidator``
#                                (code ``max_length``) carries one message
#
# A widget is asked for its own keys, never assumed to read one of these pairs, so a
# consumer ``SuffixedMultiWidget`` with its own ``suffixes`` is read as it reads itself.
def multi_widget_keys(widget: object, name: str) -> list[str] | None:
    """Return the form-data keys a multi-widget reads for the field ``name``, in widget order.

    A django-filter ``SuffixedMultiWidget`` (``RangeWidget``, ``DateRangeWidget``, a
    consumer's) reads ``suffixed(name, suffix)`` for each of its ``suffixes``; any other
    Django ``MultiWidget`` (the package's ``_RangeWidget`` included) reads ``name`` plus
    each of its ``widgets_names``. ``None`` for a widget that is not a ``MultiWidget``.
    """
    if isinstance(widget, SuffixedMultiWidget):
        return [widget.suffixed(name, suffix) for suffix in widget.suffixes]
    if isinstance(widget, MultiWidget):
        # django-stubs declare no ``widgets_names``; ``MultiWidget.__init__`` sets it.
        return [f"{name}{suffix}" for suffix in list_of(read_attr(widget, "widgets_names"))]
    return None


def _sub_widgets(widget: object, key: str) -> list[tuple[str, object]] | None:
    """Return each sub-widget of ``widget`` beside the key it reads under ``key``.

    A ``MultiWidget`` pairs each of its ``widgets`` with its own key
    (``multi_widget_keys``); a ``SplitArrayWidget`` reads its one ``widget`` under
    ``<key>_<index>`` for each index below its ``size``. ``None`` for any other widget,
    which reads ``key`` alone.
    """
    multi_keys = multi_widget_keys(widget, key)
    if multi_keys is not None:
        return list(zip(multi_keys, list_of(read_attr(widget, "widgets")), strict=False))
    if _SPLIT_ARRAY_WIDGET is not None and isinstance(widget, _SPLIT_ARRAY_WIDGET):
        inner = read_attr(widget, "widget")
        size = require_instance(read_attr(widget, "size"), int)
        return [(f"{key}_{index}", inner) for index in range(size)]
    return None


def widget_keys(widget: object, key: str) -> list[str]:
    """Return every form-data key ``widget`` reads for a field bound under ``key``.

    ``[key]`` for a widget reading one key; a ``MultiWidget`` or ``SplitArrayWidget``
    reads the keys its sub-widgets read (``_sub_widgets``), recursively.
    """
    subs = _sub_widgets(widget, key)
    if subs is None:
        return [key]
    return [read for sub_key, sub_widget in subs for read in widget_keys(sub_widget, sub_key)]


def widget_entries(widget: object, key: str, value: object) -> dict[str, object]:
    """Return the form-data entries that bind ``value`` where ``widget`` reads it under ``key``.

    A widget reading one key binds ``{key: value}``. A ``MultiWidget`` binds each part
    of ``value`` under its sub-widget's key: a list or tuple is its parts, any other value
    is split by the widget's own ``decompress``, and a part past the end is ``None``, as
    ``MultiWidget.get_context`` renders it. A ``SplitArrayWidget`` binds each element
    under ``<key>_<index>`` and pads to its ``size`` with ``None``, so an empty list binds
    every key and is never read as an omitted field; ``None`` binds no element and a value
    that is no list or tuple binds as its one element. A list longer than ``size`` cannot
    be bound (the widget reads no key past it, so the extra elements would be dropped):
    ``ArrayMaxLengthValidator`` refuses it with Django's own ``ValidationError``, code
    ``max_length``. Each part recurses into its sub-widget.
    """
    subs = _sub_widgets(widget, key)
    if subs is None:
        return {key: value}
    if _SPLIT_ARRAY_WIDGET is not None and isinstance(widget, _SPLIT_ARRAY_WIDGET):
        parts = _array_parts(value)
        ArrayMaxLengthValidator(len(subs))(parts)
    elif is_list_or_tuple(value):
        parts = list(value)
    else:
        parts = list_of(require(call_method(widget, "decompress", value), is_list_or_tuple))
    entries: dict[str, object] = {}
    for index, (sub_key, sub_widget) in enumerate(subs):
        part = parts[index] if index < len(parts) else None
        entries.update(widget_entries(sub_widget, sub_key, part))
    return entries


def _array_parts(value: object) -> list[object]:
    """Return the elements a ``SplitArrayWidget`` binds for ``value``."""
    if value is None:
        return []
    if is_list_or_tuple(value):
        return list(value)
    return [value]
