"""The permission walk's related-declaration read holds a collection to attribute-name keys.

``utils/permissions.py::walk_declared_relation_path`` reads a set's related
collection for the flat-path walk; a key becomes the hop's declared attribute
name, so a collection keyed by anything but a string raises rather than walks.
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from django_strawberry_framework.sets_mixins import (
    ActiveInputPermissionAttrs,
    ActiveInputPermissionMixin,
)
from django_strawberry_framework.utils.input_values import SetInputTraversal
from django_strawberry_framework.utils.permissions import walk_declared_relation_path

_PERMISSION = ActiveInputPermissionAttrs(
    family_label="Probe",
    target_attr="target",
    traversal=SetInputTraversal(field_specs={}, related_attr="related_filters"),
)


class _Target:
    """A declaration target with no further related declarations."""


class _Declaration:
    """A related declaration naming the ``category`` relation."""

    field_name = "category"
    target = _Target


def test_non_string_related_declaration_key_is_refused() -> None:
    """A non-string key in the related collection raises before it is walked."""

    class _Owner(ActiveInputPermissionMixin):
        _permission = _PERMISSION
        related_filters: ClassVar[dict[object, object]] = {1: _Declaration()}

    with pytest.raises(TypeError, match="expected an instance of str"):
        walk_declared_relation_path(
            _Owner,
            "category__name",
        )


def test_string_related_declaration_key_is_walked() -> None:
    """A string-keyed collection still walks to its declared hop."""

    class _Owner(ActiveInputPermissionMixin):
        _permission = _PERMISSION
        related_filters: ClassVar[dict[object, object]] = {"category": _Declaration()}

    hops, remainder = walk_declared_relation_path(
        _Owner,
        "category__name",
    )

    assert [hop.declared_attr for hop in hops] == ["category"]
    assert remainder == ("name",)
