"""The one owner of the soft-imported ``ArrayField`` class and the read of its element column.

``django.contrib.postgres.fields`` needs a PostgreSQL driver, so ``ARRAY_FIELD_CLS`` is
resolved best-effort through ``utils/imports.py::import_attr_if_importable``: ``None``
when the module is unavailable (no column can then be an ``ArrayField``), and a loud
``AttributeError`` when the module imports but lacks the class, a broken environment
that should fail rather than silently degrade.

``array_element_field`` is every subsystem's ``ArrayField`` test: the read-side
converter (``types/converters.py::scalar_route``), the write inputs and their decode
(``forms/inputs.py``, ``rest_framework/serializer_converter.py``), the filter form
fields (``filters/base.py``), the filter bind ask (``filters/sets.py``) and the
write-side storability rule (``utils/errors.py::unstorable_temporal``) all ask it, so a
column is an array to every one of them or to none. ``array_leaf_field`` walks it
through nested arrays to the column the innermost elements are stored through.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from . import truth
from .imports import import_attr_if_importable

if TYPE_CHECKING:
    from django.contrib.postgres.fields import ArrayField
    from typing_extensions import Never

    from .typing import ConcreteField

__all__ = ("ARRAY_FIELD_CLS", "array_element_field", "array_leaf_field")

#: ``django.contrib.postgres.fields.ArrayField``, or ``None`` without a PostgreSQL
#: driver. The cast names the class the by-name lookup returns.
ARRAY_FIELD_CLS = cast(
    "type[ArrayField[Never, object]] | None",
    import_attr_if_importable("django.contrib.postgres.fields", "ArrayField"),
)


def array_element_field(field: object) -> ConcreteField | None:
    """Return an ``ArrayField``'s ``base_field``, the column each element is stored through.

    ``None`` for any other column, and for every column when ``django.contrib.postgres``
    is unavailable. The class is matched through ``utils/truth.py::is_instance``, so a
    field class cannot claim to be an ``ArrayField``. An ``ArrayField`` reads as
    ``list[<base_field's type>]``, so its element choices live on ``base_field``, never
    on the array column itself.
    """
    if ARRAY_FIELD_CLS is not None and truth.is_instance(field, ARRAY_FIELD_CLS):
        return field.base_field
    return None


def array_leaf_field(field: object) -> tuple[object, int]:
    """Return the column an ``ArrayField``'s innermost elements are stored through, and its depth.

    The depth counts the ``ArrayField`` levels walked, each read through
    ``array_element_field``; ``(field, 0)`` for a column that is no ``ArrayField``.
    """
    depth = 0
    while (element := array_element_field(field)) is not None:
        field = element
        depth += 1
    return field, depth
