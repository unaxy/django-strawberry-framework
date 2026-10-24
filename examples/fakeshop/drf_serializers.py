"""Shared DRF ``ModelSerializer`` base for the fakeshop apps' serializer-mutation surfaces.

``djangorestframework-stubs`` types ``ModelSerializer.Meta``, but DRF's runtime class has
no such attribute to subclass, so a serializer declaring ``class Meta:`` overrides the
stub's attribute. ``ModelSerializerBase`` declares that override once for every app's
serializers (``apps/library/serializers.py``, ``apps/scalars/serializers.py``), so each
serializer derives from it instead of carrying its own suppression.
"""

from typing import ClassVar, TypeVar

from django.db.models import Model
from rest_framework import serializers

_ModelT = TypeVar("_ModelT", bound=Model)


class ModelSerializerBase(serializers.ModelSerializer[_ModelT]):
    """``ModelSerializer`` carrying the ``Meta`` the stubs declare and the runtime class lacks.

    ``djangorestframework-stubs`` types ``ModelSerializer.Meta``, but DRF's class has no such
    attribute to subclass, so every serializer that declares ``class Meta:`` derives from
    this base and the one override of the stub's attribute is declared once. The annotation
    creates no class attribute, so DRF's metaclass and ``__class_getitem__`` see the same class
    body and the same ``ModelSerializer`` they see without it.
    """

    # basedpyright: the DRF stubs declare ModelSerializer.Meta; the runtime class has none
    Meta: ClassVar[type[object]]  # pyright: ignore[reportIncompatibleVariableOverride]
