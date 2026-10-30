"""DjangoType tests for GenericForeignKey rejection and GenericRelation support.

``content_object`` auto-map refusal is class-creation time. Reverse GenericRelation
payloads over HTTP live in
``examples/fakeshop/test_query/test_library_api.py``
(``test_generic_relation_tags_resolve_over_http_with_optimizer``). This module
keeps the GFK auto-map refusal, exclude-and-finalize field set, and the
``list[TaggedItemType]`` annotation rewrite, and the refusal of the reverse
``GenericRel`` a ``related_query_name`` makes visible on the generic-key model.
"""

import re
from collections.abc import Iterator

import pytest
from apps.library.models import Branch, TaggedItem
from django.contrib.contenttypes.models import ContentType
from strawberry import relay
from strawberry.types import get_object_definition

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from tests._idioms import definition_raises
from tests._relation_fixtures import RpGenericTag

_REVERSE_GENERIC_REFUSAL = (
    "RpGenericTag.holder is the reverse side of a GenericRelation (its related_query_name). "
    "Django can neither select_related it nor read it as a related object, so it cannot be "
    "auto-mapped to a GraphQL type. Exclude it via Meta.exclude, or supply an explicit "
    "annotation or resolver."
)


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def test_generic_foreign_key_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="cannot be auto-mapped to a single GraphQL type"):

        @definition_raises
        class TaggedItemType(DjangoType):
            class Meta:
                model = TaggedItem
                fields = "__all__"


@pytest.mark.parametrize(
    ("fields", "exclude"),
    [(("id", "holder"), None), (None, ("content_object", "content_type"))],
    ids=["named_in_fields", "left_in_by_exclude"],
)
def test_visible_reverse_generic_relation_is_refused_at_declaration(
    fields: tuple[str, ...] | None,
    exclude: tuple[str, ...] | None,
) -> None:
    """The reverse ``GenericRel`` is no related object Django can join or read.

    ``select_related`` refuses it and its instance accessor is the holder's
    manager, so a type that selects it is refused when it is declared, never
    published as a single related object that fails every query reading it.
    """
    meta_attrs = {"model": RpGenericTag, "fields": fields, "exclude": exclude}
    meta = type("Meta", (), {k: v for k, v in meta_attrs.items() if v is not None})
    with pytest.raises(ConfigurationError, match=re.escape(_REVERSE_GENERIC_REFUSAL)):
        type("RpGenericTagType", (DjangoType,), {"__module__": __name__, "Meta": meta})
    assert registry.get(RpGenericTag) is None


def test_visible_reverse_generic_relation_names_its_shape_in_relation_shapes() -> None:
    """A ``relation_shapes`` entry over it is the single-valued refusal, naming the shape."""
    with pytest.raises(
        ConfigurationError,
        match=re.escape("names single-valued relation 'holder' (reverse GenericRelation)"),
    ):

        @definition_raises
        class RpGenericTagType(DjangoType):
            class Meta:
                model = RpGenericTag
                fields = ("id", "holder")
                interfaces = (relay.Node,)
                relation_shapes = {"holder": "connection"}


def test_consumer_authored_reverse_generic_relation_is_exempt() -> None:
    """A consumer-authored field over it owns its shape, so the declaration stands."""

    class RpGenericTagType(DjangoType):
        holder: str

        class Meta:
            model = RpGenericTag
            fields = ("id", "holder")

    assert registry.get(RpGenericTag) is RpGenericTagType


def test_generic_foreign_key_works_if_excluded() -> None:
    class ContentTypeType(DjangoType):
        class Meta:
            model = ContentType
            fields = ("id", "app_label", "model")

    assert registry.get(ContentType) is ContentTypeType

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            exclude = ("content_object",)

    finalize_django_types()

    assert hasattr(TaggedItemType, "__strawberry_definition__")
    field_names = {
        field.python_name for field in get_object_definition(TaggedItemType, strict=True).fields
    }
    assert "content_object" not in field_names
    assert {
        "id",
        "tag",
        "content_type",
        "object_id",
    } <= field_names


def test_generic_relation_reverse_side_finalizes_to_list_target() -> None:
    class BranchType(DjangoType):
        class Meta:
            model = Branch
            fields = ("id", "name", "tags")

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "tag")

    finalize_django_types()
    assert BranchType.__annotations__["tags"] == list[TaggedItemType]
