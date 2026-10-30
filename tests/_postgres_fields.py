"""Shared PostgreSQL container-field doubles that run without ``django.contrib.postgres``.

``FakeArrayField`` and ``FakeHStoreField`` stand in for ``ArrayField`` / ``HStoreField``,
whose module needs a Postgres driver. Neither subclasses a ``SCALAR_MAP`` class, so a
column reaches the container arm of ``types/converters.py::scalar_route`` only once the
test points the sentinel at the double, before declaring the type that exposes the
column::

    patch_array_field(monkeypatch)
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

``patch_array_field`` points the one ``ArrayField`` owner
(``django_strawberry_framework/utils/_array_field.py::ARRAY_FIELD_CLS``) at the double,
so every reader of ``array_element_field`` (the read converter, the write inputs, the
filter form fields, the filter bind ask and the write-side storability rule) sees the
same class.

``real_array_of`` builds a real ``django.contrib.postgres`` ``ArrayField`` and skips the
test where the module is unimportable (no PostgreSQL driver).

``FakeArrayField`` reads an index (``<column>__0``), a slice (``<column>__0_2``) and ``len``
as a real ``ArrayField`` does: an index's output is ``base_field``, a slice's the array,
``len``'s an ``IntegerField``.

A model hosting either double declares ``class Meta: managed = False``.

``FakeSplitArrayWidget`` stands in for ``django.contrib.postgres.forms.SplitArrayWidget``
(whose module needs the driver too) once a test points the widget sentinel at it::

    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django import forms
from django.db import models
from django.db.models.functions import Length
from django.utils.functional import cached_property
from typing_extensions import Never, override

from django_strawberry_framework.utils import _array_field

if TYPE_CHECKING:
    from django.forms.utils import _DataT, _FilesT


class FakeArrayField(models.Field[object, object]):
    """An ``ArrayField`` stand-in carrying the ``base_field`` each element is stored through.

    Mirrors the real field's metadata propagation, so a ``base_field`` declared on a model
    carries that model and the column's name; the element choice enum is named from both.
    """

    def __init__(
        self,
        base_field: models.Field[Never, object],
        *,
        null: bool = False,
        choices: list[tuple[int, str]] | None = None,
    ) -> None:
        super().__init__(null=null, choices=choices)
        self.base_field = base_field

    @override
    def contribute_to_class(
        self,
        cls: type[models.Model],
        name: str,
        private_only: bool = False,
    ) -> None:
        super().contribute_to_class(cls, name, private_only=private_only)
        self.base_field.set_attributes_from_name(name)
        self.base_field.model = cls

    @override
    def get_transform(self, lookup_name: str) -> type[models.Transform] | None:
        """Read an index (``0``) or a slice (``0_2``) as a real ``ArrayField`` reads them.

        Adapted from ``django/contrib/postgres/fields/array.py::ArrayField.get_transform``
        (Django, BSD): a registered transform wins, an index's output is the element
        column (``base_field``) and a slice's the array itself. Typing only: neither
        compiles to SQL.
        """
        transform = super().get_transform(lookup_name)
        if transform is not None:
            return transform
        start, separator, end = lookup_name.partition("_")
        if not start.isdigit() or (separator and not end.isdigit()):
            return None
        output: models.Field[Never, object] = self if separator else self.base_field

        class _ArrayItemTransform(models.Transform):
            """One element (an index) or a sub-array (a slice) of the array."""

            @cached_property
            def output_field(self) -> models.Field[Never, object]:
                return output

        return _ArrayItemTransform


class FakeArrayLength(Length):
    """An array's element count under the ``len`` name a real ``ArrayField`` registers.

    Django's ``Length`` transform, whose output is an ``IntegerField``: an integer no
    column stores.
    """

    lookup_name = "len"


FakeArrayField.register_lookup(FakeArrayLength)


def patch_array_field(
    monkeypatch: pytest.MonkeyPatch,
    field_cls: type[models.Field[object, object]] | None = FakeArrayField,
) -> None:
    """Point the one ``ArrayField`` owner at ``field_cls`` (``FakeArrayField`` by default).

    ``None`` stands for an environment without ``django.contrib.postgres``, where no
    column is an ``ArrayField``.
    """
    monkeypatch.setattr(_array_field, "ARRAY_FIELD_CLS", field_cls)


class FakeHStoreField(models.Field[object, object]):
    """An ``HStoreField`` stand-in: a plain column the converter's sentinel names."""


class FakeSplitArrayWidget(forms.Widget):
    """A ``SplitArrayWidget`` stand-in: ``size`` copies of ``widget`` under ``<name>_<index>``.

    Reads and reports omission exactly as Django's widget does, so a form field over it
    reads the list its keys hold.
    """

    def __init__(self, widget: forms.Widget, size: int) -> None:
        super().__init__()
        self.widget = widget
        self.size = size

    @override
    def value_from_datadict(
        self,
        data: _DataT,
        files: _FilesT,
        name: str,
    ) -> list[object]:
        return [
            self.widget.value_from_datadict(data, files, f"{name}_{index}")
            for index in range(self.size)
        ]

    @override
    def value_omitted_from_data(
        self,
        data: _DataT,
        files: _FilesT,
        name: str,
    ) -> bool:
        return all(
            self.widget.value_omitted_from_data(data, files, f"{name}_{index}")
            for index in range(self.size)
        )


def real_array_of(base_field: models.Field[object, object]) -> models.Field[object, object]:
    """A ``django.contrib.postgres`` ``ArrayField`` of ``base_field``; skips without a driver."""
    pytest.importorskip("django.contrib.postgres.fields")
    from django.contrib.postgres.fields import ArrayField  # noqa: PLC0415 - after the skip guard

    return ArrayField(base_field)
