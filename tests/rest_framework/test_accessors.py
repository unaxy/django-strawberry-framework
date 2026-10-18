"""The typed DRF reads every package module (and its tests) go through.

``rest_framework/accessors.py`` spells each DRF attribute djangorestframework-stubs
declares with a bare generic once; these tests pin that each accessor returns
the attribute it names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import serializers
from typing_extensions import override

from django_strawberry_framework.rest_framework.accessors import (
    base_fields,
    bound_fields,
    child_relation_of,
    choices_of,
    declared_fields_of,
    is_drf_field,
    is_serializer,
    list_child_of,
    serializer_errors,
    validated_data_of,
)
from django_strawberry_framework.utils._narrowing import is_dict
from django_strawberry_framework.utils.typing import object_result

if TYPE_CHECKING:
    from django_strawberry_framework.rest_framework.serializer_converter import DRFField


class _NoteSerializer(serializers.Serializer[object]):
    title = serializers.CharField()
    tags = serializers.ListField(child=serializers.IntegerField())
    ids = object_result(serializers.PrimaryKeyRelatedField, many=True, read_only=True)


def test_bound_fields_are_the_serializer_fields() -> None:
    """``bound_fields`` is ``serializer.fields``, keyed by field name."""
    serializer = _NoteSerializer()

    assert list(bound_fields(serializer)) == ["title", "tags", "ids"]


def test_declared_fields_are_the_class_body_fields() -> None:
    """``declared_fields_of`` is the class's ``_declared_fields``."""
    assert list(declared_fields_of(_NoteSerializer)) == ["title", "tags", "ids"]


def test_list_child_is_the_element_field() -> None:
    """``list_child_of`` is the ``ListField``'s element field."""
    field = bound_fields(_NoteSerializer())["tags"]

    assert isinstance(field, serializers.ListField)
    assert isinstance(list_child_of(field), serializers.IntegerField)


def test_child_relation_is_the_wrapped_relation() -> None:
    """``child_relation_of`` is the single relation a ``many=True`` field wraps."""
    many = bound_fields(_NoteSerializer())["ids"]

    assert isinstance(many, serializers.ManyRelatedField)
    assert isinstance(child_relation_of(many), serializers.PrimaryKeyRelatedField)


def test_serializer_errors_are_the_validation_errors() -> None:
    """``serializer_errors`` is the serializer's error tree after validation."""
    serializer = _NoteSerializer(data={})
    serializer.is_valid()
    errors = serializer_errors(serializer)

    assert is_dict(errors)
    assert set(errors) == {"title", "tags"}


def test_validated_data_is_what_validation_built() -> None:
    """``validated_data_of`` is ``serializer.validated_data``, coerced by the fields."""
    serializer = _NoteSerializer(data={"title": "Note", "tags": [1, "2"]})

    assert serializer.is_valid()
    assert validated_data_of(serializer) == {"title": "Note", "tags": [1, 2]}


def test_choices_of_is_a_copy_of_the_value_display_mapping() -> None:
    """``choices_of`` is the field's value -> display mapping, in order, as a copy."""
    field = serializers.ChoiceField(choices=[("b", "Bee"), ("a", "Ay")])
    choices = choices_of(field)
    choices["c"] = "Sea"

    assert list(choices) == ["b", "a", "c"]
    assert list(choices_of(field).items()) == [("b", "Bee"), ("a", "Ay")]


def test_predicates_tell_serializers_and_fields_apart() -> None:
    """``is_serializer`` admits a serializer only; ``is_drf_field`` admits any field."""
    serializer = _NoteSerializer()
    field = serializers.CharField()

    assert is_serializer(serializer)
    assert not is_serializer(field)
    assert is_drf_field(field)
    assert is_drf_field(serializer)
    assert not is_drf_field(object())


class _TaggedNoteSerializer(_NoteSerializer):
    @override
    def get_fields(self) -> dict[str, DRFField]:
        fields = base_fields(super())
        fields["label"] = serializers.CharField(required=False)
        return fields


def test_base_fields_of_super_skips_the_running_override() -> None:
    """Through ``super()``, ``base_fields`` is the next class's ``get_fields`` in the MRO."""
    serializer = _TaggedNoteSerializer()

    assert list(base_fields(super(_TaggedNoteSerializer, serializer))) == ["title", "tags", "ids"]
    assert list(base_fields(serializer)) == [
        "title",
        "tags",
        "ids",
        "label",
    ]
    assert list(bound_fields(serializer)) == [
        "title",
        "tags",
        "ids",
        "label",
    ]


def test_base_fields_returns_a_fresh_dict_per_call() -> None:
    """Each read is DRF's freshly built dict, so an override's additions never leak back."""
    serializer = _TaggedNoteSerializer()
    first = base_fields(super(_TaggedNoteSerializer, serializer))
    first["extra"] = serializers.CharField()

    assert "extra" not in base_fields(super(_TaggedNoteSerializer, serializer))
