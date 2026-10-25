"""Shared PostgreSQL container-field doubles that run without ``django.contrib.postgres``.

``FakeArrayField`` and ``FakeHStoreField`` stand in for ``ArrayField`` / ``HStoreField``,
whose module needs a Postgres driver. Neither subclasses a ``SCALAR_MAP`` class, so a
column reaches the container arm of ``types/converters.py::scalar_route`` only once the
test points the converter's sentinel at the double, before declaring the type that
exposes the column::

    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", FakeArrayField)
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

A model hosting either double declares ``class Meta: managed = False``.

``FakeSplitArrayWidget`` stands in for ``django.contrib.postgres.forms.SplitArrayWidget``
(whose module needs the driver too) once a test points the widget sentinel at it::

    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.db import models
from typing_extensions import Never, override

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
