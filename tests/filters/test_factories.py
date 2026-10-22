"""FilterArgumentsFactory tests for BFS input generation.

Covers `FilterArgumentsFactory`'s BFS walk and per-class collision check.

Shipped filter argument types are introspected live via ``*FilterInputType``.
This file keeps the BFS walk and name-collision refusal -- construction
internals a request cannot name.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Literal, get_args

import pytest
import strawberry
from apps.library import models as library_models
from apps.products.models import Category
from django.db.models import CASCADE, ForeignKey, IntegerField, Model, TextField
from django_filters import CharFilter, NumberFilter
from strawberry import relay
from strawberry.types.base import get_object_definition

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterSet,
    GlobalIDMultipleChoiceFilter,
    RangeFilter,
    RelatedFilter,
)
from django_strawberry_framework.filters.base import RelationPkFilter, RelationPkMultipleFilter
from django_strawberry_framework.filters.factories import FilterArgumentsFactory
from django_strawberry_framework.filters.inputs import _field_specs
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import apply_interfaces
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import is_tuple, read_attr, require
from django_strawberry_framework.utils.inputs import GeneratedInputArgumentsFactory
from django_strawberry_framework.utils.typing import unwrap_container_type
from tests._idioms import comparing_metaclass, declare_django_type, definition_raises
from tests.filters.fixtures.filtersets import SelfReferentialBranchFilter


def _args(annotation: object) -> tuple[object, ...]:
    """``typing.get_args`` with each member typed ``object`` (typeshed declares them ``Any``)."""
    return get_args(annotation)


@pytest.fixture(autouse=True)
def _isolate_state() -> Iterator[None]:
    registry.clear()
    _field_specs.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    yield
    registry.clear()
    _field_specs.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()


# ---------------------------------------------------------------------------
# FilterArgumentsFactory BFS
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_filter_arguments_factory_visits_every_reachable_filterset() -> None:
    """A `Branch -> Shelf` `RelatedFilter` -> both classes appear in `input_object_types`."""

    class ShelfFilterA(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilterA(FilterSet):
        shelves = RelatedFilter(ShelfFilterA, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(BranchFilterA)
    _ = factory.arguments  # trigger build
    assert "BranchFilterAInputType" in FilterArgumentsFactory.input_object_types
    assert "ShelfFilterAInputType" in FilterArgumentsFactory.input_object_types


@pytest.mark.django_db
def test_filter_arguments_factory_bfs_handles_cycle() -> None:
    """`A -> B -> A` mutual `RelatedFilter`s do not blow the BFS stack."""
    # Use the package's `tests.filters.fixtures.filtersets` self-referential
    # fixture: the cookbook-style cycle path is exercised by
    # `SelfReferentialBranchFilter` whose `RelatedFilter("SelfReferentialBranchFilter")`
    # resolves back to itself (a degenerate A -> A cycle covers the same
    # `seen`-set short-circuit branch as A -> B -> A).

    factory = FilterArgumentsFactory(SelfReferentialBranchFilter)
    _ = factory.arguments  # must not recurse forever
    assert "SelfReferentialBranchFilterInputType" in FilterArgumentsFactory.input_object_types


@pytest.mark.django_db
def test_filter_arguments_factory_dedupes_target_enqueued_twice() -> None:
    """A diamond ``A -> {B, C} -> D`` enqueues ``D`` twice; the BFS dedups it.

    Unlike the ``A -> B -> A`` cycle (caught by the enqueue-time
    ``target not in seen`` gate), a diamond enqueues the shared child ``D``
    from both sibling parents BEFORE ``D`` is popped, so the pop-time
    ``if fs_class in seen: continue`` dedup is what prevents the duplicate
    build.
    """

    class DFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    class BFilter(FilterSet):
        d = RelatedFilter(DFilter, field_name="books__loans")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class CFilter(FilterSet):
        d = RelatedFilter(DFilter, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class AFilter(FilterSet):
        b = RelatedFilter(BFilter, field_name="shelves")
        c = RelatedFilter(CFilter, field_name="alt_shelves__books")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(AFilter)
    _ = factory.arguments  # BFS: D is enqueued by both B and C, deduped at pop.
    for name in (
        "AFilterInputType",
        "BFilterInputType",
        "CFilterInputType",
        "DFilterInputType",
    ):
        assert name in FilterArgumentsFactory.input_object_types


@pytest.mark.django_db
def test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name() -> None:
    """Two distinct `FilterSet`s named `DupFilter` in different modules -> ConfigurationError."""

    class DupFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(DupFilter)
    _ = factory.arguments  # build the first one

    # Synthesize a second class with the same `__name__`.
    DupFilter2 = type(
        "DupFilter",
        (FilterSet,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Shelf, "fields": {"code": ["exact"]}},
            ),
        },
    )
    factory2 = FilterArgumentsFactory(DupFilter2)
    with pytest.raises(ConfigurationError) as excinfo:
        _ = factory2.arguments
    message = str(excinfo.value)
    assert "DupFilterInputType" in message
    # The shared BFS substrate keeps family-specific wording: the message
    # still names FilterArgumentsFactory / FilterSet (not the order twin).
    assert "FilterArgumentsFactory" in message
    assert "FilterSet" in message


@pytest.mark.django_db
def test_filter_arguments_factory_rejects_flattened_field_collision() -> None:
    """Two members whose paths flatten to one python attr must fail loud, not drop one.

    ``flatten_lookup_path`` maps a relation traversal ``branch__name`` and a
    declared / scalar ``branch_name`` onto the SAME python attr ``branch_name``
    (and the SAME GraphQL name ``branchName``). Both survive
    ``get_filters()`` as distinct entries, but the generated input dataclass and
    the ``_field_specs`` provenance table are keyed by that one attr, so the
    second member would silently overwrite the first -- the declared
    ``branch__name`` exact filter would vanish from the public schema with no
    error. This is the exact silent-drop class the type surface
    (``_audit_field_surface``) and the write-input surfaces
    (``iter_input_field_collisions``) already reject; the generated filter input
    surface must reject it too. Without the guard in
    ``utils/inputs.py::emit_set_input_field_triples`` the build silently emits a
    single ``branchName`` field (the collision is invisible); with it the build
    raises an actionable ``ConfigurationError`` naming both offending members.
    """

    class ShelfFlattenCollide(FilterSet):
        # Declared filter literally named ``branch_name``.
        branch_name = CharFilter(field_name="branch__name", lookup_expr="icontains")

        class Meta:
            model = library_models.Shelf
            # Relation-traversal path that flattens to the SAME python attr.
            fields = {"branch__name": ["exact"]}

    # Both members are distinct entries at the django-filter layer ...
    assert {"branch__name", "branch_name"} <= set(ShelfFlattenCollide.get_filters())

    # ... but they collapse onto one generated input attribute, so the build
    # must fail loud instead of silently dropping one.
    factory = FilterArgumentsFactory(ShelfFlattenCollide)
    with pytest.raises(ConfigurationError) as excinfo:
        _ = factory.arguments
    message = str(excinfo.value)
    assert "branch__name" in message
    assert "branch_name" in message
    assert "ShelfFlattenCollide" in message


@pytest.mark.django_db
def test_filter_arguments_factory_rejects_graphql_name_collision() -> None:
    """Distinct python attrs that camel-case alike must not share one GraphQL field."""

    class ShelfGraphqlCollide(FilterSet):
        foo_bar = CharFilter(field_name="code", lookup_expr="exact")
        fooBar = CharFilter(  # noqa: N815 - intentional camel-case collision fixture.
            field_name="topic",
            lookup_expr="exact",
        )

        class Meta:
            model = library_models.Shelf
            fields = []

    factory = FilterArgumentsFactory(ShelfGraphqlCollide)
    with pytest.raises(ConfigurationError) as excinfo:
        _ = factory.arguments
    message = str(excinfo.value)
    assert "'foo_bar'" in message
    assert "'fooBar'" in message
    assert "GraphQL input field name 'fooBar'" in message


@pytest.mark.django_db
def test_filter_arguments_factory_idempotent_repeated_arguments() -> None:
    """Repeated reads of `.arguments` return the same input class object."""

    class IdempotentFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(IdempotentFilter)
    first = factory.arguments
    second = factory.arguments
    assert first is second


@pytest.mark.django_db
def test_filter_arguments_factory_input_shape_matches_runtime_filter_for_relay_target() -> None:
    """A Relay-shaped M2M target -> input annotation forwards to the target's input class.

    The input shape is downstream of the resolved filter instance
    (`GlobalIDMultipleChoiceFilter` for the M2M cardinality), and the factory
    produces an `Annotated[...]` lazy reference to the target filterset's
    input class.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    class BookFilterRelay(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    # Confirm runtime filter resolves to the Relay multi-value primitive.
    field = library_models.Book._meta.get_field("genres")
    runtime_filter = BookFilterRelay.filter_for_field(field, "genres")
    assert isinstance(runtime_filter, GlobalIDMultipleChoiceFilter)

    # Build the input class and assert the `genres` field's annotation
    # is a lazy reference to GenreFilterInputType.
    factory = FilterArgumentsFactory(BookFilterRelay)
    input_cls = factory.arguments
    fields = {f.python_name: f for f in get_object_definition(input_cls, strict=True).fields}
    genres_field = fields["genres"]
    # Strawberry resolves the `Annotated[..., strawberry.lazy(...)]` form
    # into a `LazyType` at field-collection time; both shapes are
    # accepted here so the test is robust to Strawberry version changes.
    assert genres_field.type_annotation is not None
    type_annotation = genres_field.type_annotation.annotation
    non_none = [arg for arg in _args(type_annotation) if arg is not type(None)]
    assert non_none, type_annotation
    inner = non_none[0]
    if hasattr(inner, "__metadata__"):
        forward = require(read_attr(inner, "__args__"), is_tuple)[0]
        forward_name = read_attr(forward, "__forward_arg__", forward)
    else:
        # `LazyType` carries `.type_name` after Strawberry has resolved
        # the Annotated wrapper.
        forward_name = read_attr(inner, "type_name")
    assert forward_name == "GenreFilterInputType"


@pytest.mark.django_db
def test_filter_arguments_factory_input_shape_matches_runtime_filter_for_non_relay_target() -> (
    None
):
    """A non-Relay target -> raw-pk runtime filters and a pk-typed input bag.

    ``Shelf`` is exposed by a non-Relay ``DjangoType``, so the ``shelf`` key filters by
    the shelf's primary key: ``RelationPkFilter`` for ``exact`` and
    ``RelationPkMultipleFilter`` for ``in``, and the built input types them from the
    target's ``AutoField`` column (``Int`` / ``[Int!]``), never a model-choice shape.
    """

    class ShelfTypeNon(DjangoType):
        class Meta:
            model = library_models.Shelf

    assert registry.get(library_models.Shelf) is ShelfTypeNon

    class BookFilterNon(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"], "shelf": ["exact", "in"]}

    field = library_models.Book._meta.get_field("shelf")
    assert isinstance(BookFilterNon.filter_for_field(field, "shelf"), RelationPkFilter)
    assert isinstance(
        BookFilterNon.filter_for_field(field, "shelf", "in"),
        RelationPkMultipleFilter,
    )

    input_cls = FilterArgumentsFactory(BookFilterNon).arguments
    fields = {f.python_name: f for f in get_object_definition(input_cls, strict=True).fields}
    assert fields["shelf"].type_annotation is not None
    bag_annotation = fields["shelf"].type_annotation.annotation
    (bag_cls,) = [arg for arg in _args(bag_annotation) if arg is not type(None)]
    bag = {f.python_name: f for f in get_object_definition(bag_cls, strict=True).fields}
    exact_annotation = bag["exact"].type_annotation
    in_annotation = bag["in_"].type_annotation
    assert exact_annotation is not None
    assert in_annotation is not None
    assert exact_annotation.annotation == (int | None)
    assert in_annotation.annotation == (list[int] | None)


@pytest.mark.django_db
def test_an_in_lookup_is_not_replaced_by_a_csv_filter() -> None:
    """The cookbook's ``replace_csv_filters`` rewrap is dropped per spec-027.

    `Meta.fields = {"name": ["in"]}` -> the resulting filter is the
    upstream `django-filter` default (with the inherited list shape),
    NOT a CSV-rewritten variant.
    """

    class CategoryInFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["in"]}

    filters = CategoryInFilter.get_filters()
    # `name__in` should land as a regular filter; the import path the
    # cookbook's CSV variant would have used (`graphene_django.filter`
    # internals) is NOT touched.
    assert "name__in" in filters
    # Confirm the resulting filter is NOT a graphene-django-CSV variant
    # by checking its class hierarchy contains no graphene module path.
    cls_path = type(filters["name__in"]).__module__
    assert "graphene" not in cls_path


@pytest.mark.django_db
def test_filter_fields_alias_resolves_on_class_meta() -> None:
    """A declared ``Meta.filter_fields`` resolves to the FilterSet's fields."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            filter_fields = {"name": ["exact"]}

    assert CategoryFilter._meta.fields == {"name": ["exact"]}


def test_filter_arguments_factory_rejects_subclassing() -> None:
    """Subclassing is rejected at class-creation time (M-filters-3 / H-filters-3).

    The class-level ``input_object_types`` / ``_type_filterset_registry``
    caches are shared mutable dicts a subclass would inherit rather than
    isolate, so subclassing is an unsupported design path; the factory's
    ``__init_subclass__`` raises ``TypeError`` to enforce it.
    """
    with pytest.raises(TypeError) as excinfo:

        @definition_raises
        class _SubFactory(FilterArgumentsFactory):
            pass

    assert "does not support subclassing" in str(excinfo.value)


@pytest.mark.parametrize("shape", ["grand_subclass", "direct"])
@pytest.mark.parametrize("verdict", ["equal", "unequal", "raises"])
def test_factory_subclassing_check_finds_the_base_by_identity(
    verdict: Literal["equal", "unequal", "raises"],
    shape: Literal["grand_subclass", "direct"],
) -> None:
    """A mixin listed before the factory cannot change whether subclassing is rejected.

    The subclassing check looks for ``GeneratedInputArgumentsFactory`` among the new class's
    bases by identity, so a consumer metaclass ``__eq__`` on a mixin listed first is never
    called: an always-equal answer cannot pass a grand-subclass of ``FilterArgumentsFactory``
    off as a direct family factory, a raising one cannot escape class creation, and a direct
    family factory behind the same mixin is still accepted. The mixin answers only comparisons
    with ``GeneratedInputArgumentsFactory``: ``typing``'s ``Generic.__init_subclass__`` runs
    first and tests ``Generic in cls.__bases__``, which compares every base by equality outside
    the package.
    """
    calls: list[str] = []
    meta = comparing_metaclass(type, verdict, calls, against=GeneratedInputArgumentsFactory)
    mixin = meta("HostileMixin", (), {})
    if shape == "grand_subclass":
        with pytest.raises(TypeError, match="does not support subclassing"):
            _ = meta("GrandFactory", (mixin, FilterArgumentsFactory), {})
    else:
        direct = meta("DirectFactory", (mixin, GeneratedInputArgumentsFactory), {})
        assert direct.__bases__[1] is GeneratedInputArgumentsFactory
    assert calls == []


@pytest.mark.django_db
def test_filter_arguments_factory_empty_filterset_emits_logic_fields() -> None:
    """A FilterSet with empty fields still emits the and_/or_/not_ logic fields."""

    class EmptyFilter(FilterSet):
        class Meta:
            model = Category
            fields = []

    factory = FilterArgumentsFactory(EmptyFilter)
    input_cls = factory.arguments
    field_names = {f.python_name for f in get_object_definition(input_cls, strict=True).fields}
    assert field_names == {"and_", "or_", "not_"}


@pytest.mark.django_db
def test_filter_arguments_factory_skips_placeholder_related_filter_target() -> None:
    """A RelatedFilter(None, ...) placeholder is skipped during BFS traversal."""

    class BranchFilterPlaceholder(FilterSet):
        shelves = RelatedFilter(None, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(BranchFilterPlaceholder)
    _ = factory.arguments
    assert "BranchFilterPlaceholderInputType" in FilterArgumentsFactory.input_object_types


# ---------------------------------------------------------------------------
# Generated type-name claims reached from one set
# ---------------------------------------------------------------------------


def _node_over(model: type[Model], filterset: type[FilterSet], *fields: str) -> None:
    """Declare a relay ``DjangoType`` over ``model`` serving ``filterset``."""
    declare_django_type(
        f"{model.__name__}Node",
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": model,
                    "fields": ("id", *fields),
                    "filterset_class": filterset,
                    "interfaces": (relay.Node,),
                },
            ),
        },
    )


def _case_variant_members() -> type[FilterSet]:
    """``Price`` and ``price`` mint one bag name: a ``CharFilter`` bag and a range bag."""

    class CaseFilter(FilterSet):
        Price = CharFilter(field_name="name")
        price = RangeFilter(field_name="city")

        class Meta:
            model = library_models.Branch
            fields = []

    _node_over(library_models.Branch, CaseFilter, "name")
    return CaseFilter


def _prefix_case_variant_members() -> type[FilterSet]:
    """``MY_price`` and ``my_price`` mint one bag name: lookups of two filter classes."""

    class PrefixCaseFilter(FilterSet):
        MY_price = CharFilter(field_name="name")
        my_price = CharFilter(field_name="name", lookup_expr="icontains")

        class Meta:
            model = library_models.Branch
            fields = []

    _node_over(library_models.Branch, PrefixCaseFilter, "name")
    return PrefixCaseFilter


def _range_field_paths() -> type[FilterSet]:
    """Ranges over ``shelf__code`` (text) and ``shelf_code`` (integer) mint one range name."""

    class _ShelfCodeRow(Model):
        shelf: ForeignKey[library_models.Shelf | Combinable, library_models.Shelf] = ForeignKey(
            library_models.Shelf,
            on_delete=CASCADE,
            related_name="+",
        )
        shelf_code: IntegerField[int | Combinable, int] = IntegerField()

        class Meta:
            app_label = "library"
            managed = False

    class RangePathFilter(FilterSet):
        a = RangeFilter(field_name="shelf__code")
        b = RangeFilter(field_name="shelf_code")

        class Meta:
            model = _ShelfCodeRow
            fields = []

    _node_over(_ShelfCodeRow, RangePathFilter)
    return RangePathFilter


def _declared_and_flat_members() -> type[FilterSet]:
    """A declared ``Branch_name`` and the flat ``branch__name`` path mint one bag name."""

    class BranchNameFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class FlatShelfFilter(FilterSet):
        branch = RelatedFilter(BranchNameFilter, field_name="branch")
        Branch_name = CharFilter(field_name="code", lookup_expr="icontains")

        class Meta:
            model = library_models.Shelf
            fields = []

    _node_over(library_models.Branch, BranchNameFilter, "name")
    _node_over(library_models.Shelf, FlatShelfFilter, "code")
    return FlatShelfFilter


@pytest.mark.django_db
def test_two_members_of_one_bag_name_and_one_lookup_set_in_any_order_finalize() -> None:
    """Case-variant members whose lookups match in another order mint one shape, not a clash."""

    class _CaseVariantRow(Model):
        Price: TextField[str | Combinable, str] = TextField(db_column="price_upper")
        price: TextField[str | Combinable, str] = TextField()

        class Meta:
            app_label = "library"
            managed = False

    class CaseOrderFilter(FilterSet):
        class Meta:
            model = _CaseVariantRow
            fields = {"Price": ["exact", "icontains"], "price": ["icontains", "exact"]}

    _node_over(_CaseVariantRow, CaseOrderFilter)
    finalize_django_types()
    root = get_object_definition(
        FilterArgumentsFactory.input_object_types["CaseOrderFilterInputType"],
        strict=True,
    )
    bags = {field.python_name: unwrap_container_type(field.type) for field in root.fields}
    assert truth.qualname(bags["Price"]) == truth.qualname(bags["price"])


_CASE_CAUSE = "The member names differ only in letter case, which the PascalCase stem drops."
_RANGE_CAUSE = (
    "A range input's name joins the set name, the PascalCase stem of the range filter's "
    "field_name (letter case dropped, interior underscore runs collapsed) and "
    "'RangeInputType', so two field paths or sets can spell one name."
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "build",
        "type_name",
        "first",
        "second",
        "cause",
    ),
    [
        pytest.param(
            _case_variant_members,
            "CaseFilterPriceFilterInputType",
            "member 'Price'",
            "member 'price'",
            _CASE_CAUSE,
            id="case-variant",
        ),
        pytest.param(
            _prefix_case_variant_members,
            "PrefixCaseFilterMyPriceFilterInputType",
            "member 'MY_price'",
            "member 'my_price'",
            _CASE_CAUSE,
            id="prefix-case-variant",
        ),
        pytest.param(
            _range_field_paths,
            "RangePathFilterShelfCodeRangeInputType",
            "member 'a'",
            "member 'b'",
            _RANGE_CAUSE,
            id="range-field-paths",
        ),
        pytest.param(
            _declared_and_flat_members,
            "FlatShelfFilterBranchNameFilterInputType",
            "member 'Branch_name'",
            "member 'branch_name'",
            _CASE_CAUSE,
            id="declared-and-flat",
        ),
    ],
)
def test_two_shapes_of_one_generated_name_in_one_set_raise_at_finalize(
    build: Callable[[], type[FilterSet]],
    type_name: str,
    first: str,
    second: str,
    cause: str,
) -> None:
    """Every schema serving the set would serve both shapes, so finalize refuses the set.

    The message names both members (a range input through the member whose operator bag
    embeds it) and how their names met.
    """
    filterset = build()
    owner = f"FilterSet {truth.label(filterset)}"
    via = "the 'exact' input of " if cause is _RANGE_CAUSE else ""
    with pytest.raises(ConfigurationError) as raised:
        finalize_django_types()
    assert str(raised.value) == (
        f"Generated GraphQL type {type_name!r} is claimed with different fields by "
        f"{via}{owner} {first} and by {via}{owner} {second}; a schema serves one input "
        f"type per name, so it cannot serve both. {cause} Rename one so its generated "
        "type name is unique."
    )


# Touch `NumberFilter` import to ensure the import is exercised (used
# implicitly by django-filter for the integer-PK FK in the
# `test_filter_arguments_factory_input_shape_matches_runtime_filter_for_non_relay_target`
# test above).
assert NumberFilter is not None
