"""Shared PostgreSQL container-field doubles that run without ``django.contrib.postgres``.

``FakeArrayField`` and ``FakeHStoreField`` stand in for ``ArrayField`` / ``HStoreField``,
whose module needs a Postgres driver. Neither subclasses a ``SCALAR_MAP`` class, so a
column reaches the container arm of ``types/converters.py::scalar_route`` only once the
test points the converter's sentinel at the double, before declaring the type that
exposes the column::

    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", FakeArrayField)
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", FakeHStoreField)

A model hosting either double declares ``class Meta: managed = False``.
"""

from django.db import models
from typing_extensions import Never, override


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
