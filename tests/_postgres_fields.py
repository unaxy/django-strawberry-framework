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
``len``'s an ``IntegerField``. Its ``in`` is ``FakeArrayInLookup``, whose members are whole
array values as ``ArrayInLookup``'s are, and it registers ``contained_by`` and ``overlap``
(``FakeArrayContainedBy``, ``FakeArrayOverlap``), the array lookups no core field carries.
Its ``exact`` and ``contains`` stay the core field's. A test class is not Django's own, so
a per-field ``"__all__"`` publishes neither ``in``, ``contained_by`` nor ``overlap`` on the
double (``filters/sets.py::_lookups_for_field``); listed by name, each is published.

A model hosting either double declares ``class Meta: managed = False``.

``FakeSplitArrayWidget`` stands in for ``django.contrib.postgres.forms.SplitArrayWidget``
(whose module needs the driver too) once a test points the widget sentinel at it::

    monkeypatch.setattr(widgets, "_SPLIT_ARRAY_WIDGET", FakeSplitArrayWidget)
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import pytest
from django import forms
from django.db import models
from django.db.models.functions import Length
from django.db.models.lookups import PostgresOperatorLookup
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
    def deconstruct(self) -> tuple[str, str, list[object], dict[str, object]]:
        """Carry a clone of ``base_field``, as a real ``ArrayField`` does, so ``clone()`` rebuilds it."""
        name, path, args, kwargs = super().deconstruct()
        return name, path, list(args), {**kwargs, "base_field": self.base_field.clone()}

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


class FakeArrayInLookup(models.lookups.In):
    """An ``in`` whose members are whole array values, as a real ``ArrayField`` registers.

    Adapted from ``django/contrib/postgres/fields/array.py::ArrayInLookup`` (Django, BSD):
    each member that is no expression is converted to a tuple, so a member that is no
    iterable raises ``TypeError`` as the real lookup's does.
    """

    @override
    def get_prep_lookup(self) -> Iterable[object]:
        values: Iterable[object] = super().get_prep_lookup()
        if hasattr(values, "resolve_expression"):
            return values
        return [_array_in_member(value) for value in values]


def _array_in_member(value: object) -> object:
    """One ``in`` member as ``ArrayInLookup`` prepares it: an expression, else a tuple."""
    if hasattr(value, "resolve_expression"):
        return value
    if not isinstance(value, Iterable):
        message = f"{type(value).__name__!r} object is not iterable"
        raise TypeError(message)
    return tuple(value)


FakeArrayField.register_lookup(FakeArrayInLookup)


class FakeArrayContainedBy(PostgresOperatorLookup):
    """An array's ``contained_by`` (``<@``), registered under the name a real ``ArrayField`` uses.

    Adapted from ``django/contrib/postgres/lookups.py::ContainedBy`` (Django, BSD), which a
    real ``ArrayField`` registers through ``ArrayContainedBy``; its module needs a PostgreSQL
    driver. Only the operator is reproduced: ``ArrayRHSMixin``'s ``ARRAY[...]::type[]`` cast
    of the right-hand side is not.
    """

    lookup_name = "contained_by"
    postgres_operator = "<@"


class FakeArrayOverlap(PostgresOperatorLookup):
    """An array's ``overlap`` (``&&``), registered under the name a real ``ArrayField`` uses.

    Adapted from ``django/contrib/postgres/lookups.py::Overlap`` (Django, BSD), which a real
    ``ArrayField`` registers through ``ArrayOverlap``; its module needs a PostgreSQL driver.
    Only the operator is reproduced: neither ``ArrayRHSMixin``'s ``ARRAY[...]::type[]`` cast
    of the right-hand side nor ``Overlap.get_prep_lookup`` (which takes a subquery's values).
    """

    lookup_name = "overlap"
    postgres_operator = "&&"


FakeArrayField.register_lookup(FakeArrayContainedBy)
FakeArrayField.register_lookup(FakeArrayOverlap)


def patch_array_field(
    monkeypatch: pytest.MonkeyPatch,
    field_cls: type[models.Field[object, object]] | None = FakeArrayField,
) -> None:
    """Point the one ``ArrayField`` owner at ``field_cls`` (``FakeArrayField`` by default).

    ``None`` stands for an environment without ``django.contrib.postgres``, where no
    column is an ``ArrayField`` and no lookup is its ``in``; otherwise the array ``in`` is
    ``FakeArrayInLookup``.
    """
    monkeypatch.setattr(_array_field, "ARRAY_FIELD_CLS", field_cls)
    in_lookup = None if field_cls is None else FakeArrayInLookup
    monkeypatch.setattr(_array_field, "ARRAY_IN_LOOKUP_CLS", in_lookup)


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
