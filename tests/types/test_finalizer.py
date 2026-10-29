"""Finalizer malformed-state boundaries.

Live schema composition is ``examples/fakeshop/test_query/test_schema_composition_api.py``.
This file keeps finalize-time diagnostics that never become a GraphQL response.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NoReturn

import pytest
import strawberry
from apps.library.models import Book, Genre
from strawberry.exceptions import MissingReturnAnnotationError
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet, filter_input_type
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import finalizer as finalizer_module
from django_strawberry_framework.types.finalizer import (
    _annotation_names,
    _audit_model_label_routing,
    _field_surface_names,
    _format_owner_model_mismatch_error,
    _format_owner_orderset_model_mismatch_error,
    _warn_model_label_secondary_collapse,
)
from django_strawberry_framework.types.relations import PendingRelation

pytestmark = pytest.mark.usefixtures("isolate_global_registry")


def test_malformed_annotation_key_is_rejected_before_graphql_conversion() -> None:
    """A non-string annotation key is rejected by name before GraphQL conversion."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    # basedpyright: the int annotation key is the hostile input under test; typeshed types
    # __annotations__ keys as str
    BookType.__annotations__[123] = str  # pyright: ignore[reportArgumentType]

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()
    assert str(exc_info.value) == (
        "Cannot finalize BookType: annotation keys must be field-name strings; got 123."
    )


def test_pending_relation_without_field_metadata_is_rejected_before_relation_lookup() -> None:
    """A pending record naming a field absent from the definition's field map is typed."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    assert registry.get(Genre) is GenreType

    field = Book._meta.get_field("genres")
    registry.add_pending_relation(
        PendingRelation(
            source_type=BookType,
            source_model=Book,
            field_name="missing",
            django_field=field,
            related_model=Genre,
        ),
    )

    with pytest.raises(
        ConfigurationError,
        match="Cannot finalize BookType: pending relation missing has no field metadata",
    ):
        finalize_django_types()


def test_annotation_name_snapshot_propagates_an_unreadable_mapping() -> None:
    """An annotation mapping that refuses enumeration propagates its own error."""

    class _UnreadableAnnotations(Mapping[str, object]):
        @override
        def __iter__(self) -> NoReturn:
            raise RuntimeError("annotation enumeration exploded")

        @override
        def __len__(self) -> int:
            return 1

        @override
        def __getitem__(self, key: str) -> NoReturn:
            raise KeyError(key)

    class _Type:
        # basedpyright: an unreadable annotations mapping replaces the dict on purpose; the test
        # proves ``_annotation_names`` lets the mapping's own failure propagate
        __annotations__ = _UnreadableAnnotations()  # pyright: ignore[reportAssignmentType]

    with pytest.raises(RuntimeError, match="annotation enumeration exploded"):
        # basedpyright: the class with unreadable annotations is the hostile input under test;
        # _annotation_names types the parameter as type[DjangoType]
        _annotation_names(_Type)  # pyright: ignore[reportArgumentType]


def test_pending_relation_without_source_definition_is_typed() -> None:
    """A pending relation whose source type never registered a definition raises."""

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    del GenreType
    registry.add_pending_relation(
        PendingRelation(
            # basedpyright: the definition-less class is the hostile input under test;
            # PendingRelation types source_type as type[DjangoType]
            source_type=type("MissingDefinition", (), {}),  # pyright: ignore[reportArgumentType]
            source_model=Book,
            field_name="genres",
            django_field=Book._meta.get_field("genres"),
            related_model=Genre,
        ),
    )

    with pytest.raises(
        ConfigurationError,
        match="pending relation genres has no DjangoTypeDefinition",
    ):
        finalize_django_types()


def test_model_label_routing_audit_rejects_a_missing_primary_definition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The routing audit rejects a primary type carrying no registered definition."""
    primary = type("Primary", (), {})
    emitter = type("Emitter", (), {})

    def _emitter_for(_model: object) -> type:
        return emitter

    def _primary_for(_model: object) -> type:
        return primary

    def _no_definition(_type_cls: object) -> None:
        return None

    monkeypatch.setattr(finalizer_module, "_first_model_label_emitter", _emitter_for)
    monkeypatch.setattr(registry, "primary_for", _primary_for)
    monkeypatch.setattr(registry, "get_definition", _no_definition)

    with pytest.raises(ConfigurationError, match="has no registered DjangoTypeDefinition"):
        _audit_model_label_routing((Book,))


def test_incomplete_registry_registration_is_typed_at_finalize() -> None:
    """A registry registration with no definition is a typed error at finalize."""

    class BareModel:
        pass

    # basedpyright: the bare class and plain types are the incomplete registration under test;
    # TypeRegistry.register types the parameters as type[Model] and type[DjangoType]
    registry.register(BareModel, type("PrimaryType", (), {}), primary=True)  # pyright: ignore[reportArgumentType]
    registry.register(BareModel, type("SecondaryType", (), {}))  # pyright: ignore[reportArgumentType]

    with pytest.raises(
        ConfigurationError,
        match="registered DjangoType PrimaryType has no DjangoTypeDefinition",
    ):
        finalize_django_types()


def test_model_label_collapse_warning_refuses_a_secondary_with_no_definition() -> None:
    """A registered secondary carrying no definition is a typed error, not a strategy read."""

    class GenrePrimaryType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            primary = True

    bare_secondary = type("BareGenreType", (DjangoType,), {})
    registry.register(Genre, bare_secondary)

    with pytest.raises(
        ConfigurationError,
        match="registered DjangoType BareGenreType has no DjangoTypeDefinition",
    ):
        _warn_model_label_secondary_collapse((Genre,))
    assert registry.primary_for(Genre) is GenrePrimaryType


def test_owner_model_mismatch_formatters_ride_shared_template() -> None:
    """FilterSet and OrderSet first-bind model-mismatch messages share one template."""
    for fn in (_format_owner_model_mismatch_error, _format_owner_orderset_model_mismatch_error):
        assert "_format_owner_set_model_mismatch_error" in fn.__code__.co_names


def test_field_surface_names_ignores_field_without_python_or_graphql_name() -> None:
    """An inherited strawberry field with no python or graphql name is skipped."""

    class _FakeField:
        python_name = None
        graphql_name = None

    class _FakeDefinition:
        fields = [_FakeField()]

    class _BaseWithFakeDef:
        __strawberry_definition__ = _FakeDefinition()

    class _ChildType(_BaseWithFakeDef):
        pass

    # basedpyright: a plain class inheriting a Strawberry definition whose field has no python or
    # graphql name, the malformed base the surface read skips; _field_surface_names types the
    # parameter as type[DjangoType]
    surface = _field_surface_names(_ChildType)  # pyright: ignore[reportArgumentType]
    assert surface == frozenset()


def test_filterset_multi_owner_model_mismatch_raises_on_secondary_owner() -> None:
    """A secondary owner with an incompatible model is rejected during FilterSet binding."""

    class GenreFilterSet(FilterSet):
        class Meta:
            model = Genre
            fields = {"name": ["exact"]}

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            filterset_class = GenreFilterSet

    assert registry.get(Genre) is GenreType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = GenreFilterSet

    assert registry.get(Book) is BookType

    with pytest.raises(
        ConfigurationError,
        match=r"A filterset's Meta\.model must be its owner's model",
    ):
        finalize_django_types()


def test_orderset_non_class_meta_model_is_typed_at_finalize() -> None:
    """A non-class OrderSet ``Meta.model`` is a typed finalize failure, not a ``TypeError``.

    The order side reads the RAW ``Meta.model`` (no metaclass validation, unlike
    the filter side's django-filter-validated ``_meta.model``), so the Django
    lazy-ref string idiom reaches the owner-binding model-compat guard. The
    guard must raise the family model-mismatch ``ConfigurationError`` naming
    the declared value instead of leaking ``issubclass()``'s raw ``TypeError``.
    """

    class GenreOrderSet(OrderSet):
        class Meta:
            model = "library.Genre"
            fields = ("name",)

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            orderset_class = GenreOrderSet

    assert registry.get(Genre) is GenreType

    with pytest.raises(
        ConfigurationError,
        match=r"An orderset's Meta\.model must be its owner's model",
    ) as excinfo:
        finalize_django_types()
    # The shared template names the declared VALUE by its repr.
    assert "'library.Genre'" in str(excinfo.value)


def test_orderset_multi_owner_model_mismatch_raises_on_secondary_owner() -> None:
    """A secondary owner with an incompatible model is rejected during OrderSet binding."""

    class GenreOrderSet(OrderSet):
        class Meta:
            model = Genre
            fields = ("name",)

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            orderset_class = GenreOrderSet

    assert registry.get(Genre) is GenreType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = GenreOrderSet

    assert registry.get(Book) is BookType

    with pytest.raises(
        ConfigurationError,
        match=r"An orderset's Meta\.model must be its owner's model",
    ):
        finalize_django_types()


def test_finalize_rerun_after_phase3_raise_keeps_finalized_sets_wired() -> None:
    """A recover-in-place rerun does not orphan sets wired via finalized types.

    Pass 1 finalizes ``AType`` then raises mid-Phase-3 decorating ``BType``;
    the rerun must resume instead of flagging ``AFilter`` orphan because
    subpass 1 skipped its finalized owner.
    """

    class AFilter(FilterSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"]}

    class AType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = AFilter

    class BType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

        def label_resolver(self: BType) -> str:
            del self  # Strawberry binds the root to ``self``; the resolver never reads it
            return "x"

        # A method resolver with no return annotation, named as the field it backs: Strawberry
        # refuses it while decorating.
        del label_resolver.__annotations__["return"]
        label_resolver.__qualname__ = label_resolver.__qualname__.removesuffix("_resolver")
        label = strawberry.field(label_resolver)

    filter_input_type(AFilter)

    with pytest.raises(
        MissingReturnAnnotationError,
        match='Return annotation missing for field "label"',
    ):
        finalize_django_types()
    a_def = registry.get_definition(AType)
    assert a_def is not None
    assert a_def.finalized
    b_def = registry.get_definition(BType)
    assert b_def is not None
    assert not b_def.finalized
    assert not registry.is_finalized()

    def _fixed_label(self: BType) -> str:
        del self  # Strawberry binds the root to ``self``; the fixed resolver never reads it
        return "x"

    # basedpyright: the fixture replaces the decoration-failing field with the
    # fixed one; the assignment intentionally changes the attribute's type
    BType.label = strawberry.field(resolver=_fixed_label)  # pyright: ignore[reportAttributeAccessIssue]

    finalize_django_types()

    b_def = registry.get_definition(BType)
    assert b_def is not None
    assert b_def.finalized
    assert registry.is_finalized()
