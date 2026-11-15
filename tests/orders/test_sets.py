"""OrderSet tests for Meta collection, validation, sync/async apply, and permission scope.

Declaration surface: metaclass collection / override / binding,
``_owner_definition`` slot default, cache slot defaults, list-form
``Meta.fields`` expansion, ``related_orders`` merge, and the cycle-safe
cache write gate.

Apply surface: the ``"__all__"`` cookbook-parity expansion, the
resolver-facing ``apply_sync`` / ``apply_async`` classmethods, the
``get_flat_orders`` walker, the ``_request_from_info`` context
resolver, and the per-field / per-branch ``check_*_permission``
dispatch (active-input-only / double-dispatch / dedup contract).
To-many ``MIN`` / ``MAX`` SQL and async to-many ``orderBy`` payload
order live in ``examples/fakeshop/test_query/test_library_api.py``.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from types import SimpleNamespace
from typing import TYPE_CHECKING, NoReturn, SupportsIndex, TypeAlias, TypeVar, overload

import pytest
from apps.library.models import (
    Book,
    Branch,
    DeskProfile,
    Genre,
    Patron,
    PatronProfile,
    Shelf,
    ShelfLabel,
    TaggedItem,
)
from django.contrib.auth.models import AnonymousUser, User
from django.db import connection, models
from django.db.models import F, Min, Model, QuerySet
from django.http import HttpRequest
from django.test.utils import CaptureQueriesContext
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy
from graphql import GraphQLError
from typing_extensions import override

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.orders import Ordering, OrderSet, RelatedOrder
from django_strawberry_framework.orders.factories import OrderArgumentsFactory
from django_strawberry_framework.orders.inputs import (
    _field_specs,
    _get_concrete_field_names_for_order,
    _materialized_names,
    clear_order_input_namespace,
)
from django_strawberry_framework.orders.sets import (
    OrderSetMetaclass,
    _validate_normalized_terms,
)
from django_strawberry_framework.types.base import DjangoType
from django_strawberry_framework.utils import introspection, relations
from django_strawberry_framework.utils._narrowing import is_class
from django_strawberry_framework.utils.input_values import UNSET
from django_strawberry_framework.utils.inputs import (
    _type_name_claims,
    promote_set_meta_fields,
    read_set_meta_fields,
)
from django_strawberry_framework.utils.querysets import model_for
from django_strawberry_framework.utils.relations import (
    path_traverses_to_many as _path_traverses_to_many,
)
from tests._generated_inputs import keyword_constructor as _keyword_constructor
from tests._idioms import (
    STR_ENUM,
    STR_SUBCLASS_KINDS,
    is_object_list,
    str_subclass_name,
)
from tests._relation_fixtures import RpGenericTag, generic_fixture_rows, relation_fixture_tables

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

_M = TypeVar("_M", bound=Model)

if TYPE_CHECKING:
    # Each field's descriptor types as django-stubs declares them (set type, get type), spelled
    # out because the checker runs without the django-stubs mypy plugin that would infer them.
    _FK: TypeAlias = models.ForeignKey[_M | Combinable, _M]
    _NullFK: TypeAlias = models.ForeignKey[_M | Combinable | None, _M | None]
    _Text: TypeAlias = models.TextField[str | Combinable, str]


# ---------------------------------------------------------------------------
# Metaclass collection / override / binding
# ---------------------------------------------------------------------------


def test_metaclass_collects_related_orders() -> None:
    """``related_orders`` is an ``OrderedDict`` keyed by declaration name."""

    class TargetOrder(OrderSet):
        pass

    class Owner(OrderSet):
        first = RelatedOrder(TargetOrder, field_name="first")
        second = RelatedOrder(TargetOrder, field_name="second")

    assert isinstance(Owner.related_orders, OrderedDict)
    assert list(Owner.related_orders) == ["first", "second"]


def test_metaclass_calls_bind_orderset_on_each_related_order() -> None:
    """Every collected ``RelatedOrder`` is bound to the new class."""

    class TargetOrder(OrderSet):
        pass

    class Owner(OrderSet):
        first = RelatedOrder(TargetOrder, field_name="first")

    assert Owner.related_orders["first"].bound_orderset is Owner


def test_metaclass_inherits_related_orders_from_bases() -> None:
    """Base-class ``related_orders`` propagate to subclasses via MRO."""

    class TargetOrder(OrderSet):
        pass

    class BaseOwner(OrderSet):
        rel = RelatedOrder(TargetOrder, field_name="rel")

    class ChildOwner(BaseOwner):
        pass

    assert "rel" in ChildOwner.related_orders
    assert ChildOwner.related_orders["rel"] is BaseOwner.related_orders["rel"]


def test_metaclass_subclass_overrides_inherited_related_order() -> None:
    """A same-named declaration on the subclass wins over the inherited one."""

    class TargetOrder(OrderSet):
        pass

    class BaseOwner(OrderSet):
        rel = RelatedOrder(TargetOrder, field_name="rel")

    class ChildOwner(BaseOwner):
        rel = RelatedOrder(TargetOrder, field_name="rel_override")

    assert ChildOwner.related_orders["rel"] is not BaseOwner.related_orders["rel"]
    assert ChildOwner.related_orders["rel"].field_name == "rel_override"


def test_metaclass_none_removal_survives_diamond_inheritance() -> None:
    """An earlier base's ``None`` tombstone prevents later-base resurrection."""

    class TargetOrder(OrderSet):
        pass

    class BaseOwner(OrderSet):
        # ``None`` in a subclass is the django-filter removal idiom, so the slot admits it.
        rel: RelatedOrder | None = RelatedOrder(TargetOrder, field_name="rel")

        class Meta:
            model = Book
            fields = ["title"]

    class RemovedOwner(BaseOwner):
        rel = None

        # basedpyright: an OrderSet subclass declares its own ``Meta`` (the django-filter idiom),
        # never a subclass of the parent's
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = Book
            fields = ["title"]

    class KeptOwner(BaseOwner):
        pass

    # basedpyright: RemovedOwner and KeptOwner carry unrelated ``Meta`` classes (each set declares
    # its own); the MRO takes RemovedOwner's, the combination under test
    class CombinedOwner(RemovedOwner, KeptOwner):  # pyright: ignore[reportIncompatibleVariableOverride]
        pass

    assert "rel" not in RemovedOwner.related_orders
    assert "rel" not in RemovedOwner.get_fields()
    assert "rel" not in CombinedOwner.related_orders
    assert "rel" not in CombinedOwner.get_fields()
    assert "rel" in BaseOwner.related_orders


# ---------------------------------------------------------------------------
# Class slot defaults
# ---------------------------------------------------------------------------


def test_orderset_owner_definition_default_none() -> None:
    """The binding seam is ``None`` until phase 2.5 wires it."""

    class FreshOrder(OrderSet):
        pass

    assert FreshOrder._owner_definition is None


def test_orderset_expanded_fields_default_none() -> None:
    """``_expanded_fields`` defaults to ``None`` (cache miss until populated)."""

    class FreshOrder(OrderSet):
        pass

    assert FreshOrder._expanded_fields is None


def test_orderset_is_expanding_fields_default_false() -> None:
    """``_is_expanding_fields`` defaults to ``False`` (no recursion in flight)."""

    class FreshOrder(OrderSet):
        pass

    assert FreshOrder._is_expanding_fields is False


# ---------------------------------------------------------------------------
# Meta.fields expansion + related_orders merge
# ---------------------------------------------------------------------------


def test_orderset_meta_fields_list_form() -> None:
    """List entries become ``key -> None`` per cookbook line 280."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    fields = BookOrder.get_fields()
    assert list(fields) == ["title", "subtitle"]
    assert all(v is None for v in fields.values())


def test_orderset_get_fields_merges_related_orders() -> None:
    """``Meta.fields`` entries land first; ``related_orders`` merge on top."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    fields = BookOrder.get_fields()
    assert list(fields) == ["title", "shelf"]
    assert fields["title"] is None
    assert fields["shelf"] is BookOrder.related_orders["shelf"]


def test_orderset_get_fields_caches_on_resolved_related_orders() -> None:
    """The two-condition gate writes ``_expanded_fields`` for class-ref targets."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    first = BookOrder.get_fields()
    assert BookOrder.__dict__.get("_expanded_fields") is first
    second = BookOrder.get_fields()
    assert second is first  # cache hit returns the same OrderedDict instance.


def test_orderset_get_fields_does_not_cache_with_unresolved_string_target() -> None:
    """A pending string target leaves the cache slot empty so a later resolve writes it."""

    class BookOrder(OrderSet):
        # Unresolvable absolute target; will not resolve to a real class
        # until something updates ``_orderset``. The cache gate
        # refuses to write while a string is still on the instance.
        shelf = RelatedOrder("tests.orders.test_sets.MissingOrder", field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    fields = BookOrder.get_fields()
    # Result is well-formed (cookbook's behavior: the unresolved target
    # is preserved as an OrderedDict value), but the cache is NOT written.
    assert list(fields) == ["title", "shelf"]
    assert BookOrder.__dict__.get("_expanded_fields") is None


def test_orderset_meta_fields_none_returns_only_related_orders() -> None:
    """Missing ``Meta.fields`` collapses to the ``related_orders`` map only."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

    fields = BookOrder.get_fields()
    assert list(fields) == ["shelf"]
    assert fields["shelf"] is BookOrder.related_orders["shelf"]


def test_orderset_metaclass_and_expansion_share_factory_fields_owner() -> None:
    """Class Meta write-back and Layer-4 expansion ride the shared fingerprint."""
    assert "promote_set_meta_fields" in OrderSetMetaclass.__new__.__code__.co_names
    assert "read_set_meta_fields" in OrderSet._expand_meta_fields.__code__.co_names
    assert (
        OrderSetMetaclass.__new__.__globals__["promote_set_meta_fields"] is promote_set_meta_fields
    )
    assert (
        OrderSet._expand_meta_fields.__func__.__globals__["read_set_meta_fields"]
        is read_set_meta_fields
    )


# ---------------------------------------------------------------------------
# Additional cookbook-parity __all__ shapes
# ---------------------------------------------------------------------------


def test_orderset_meta_fields_all_raises_configurationerror_without_meta_model() -> None:
    """``"__all__"`` requires ``Meta.model`` to derive column names."""

    class NoModelOrder(OrderSet):
        class Meta:
            fields = "__all__"

    with pytest.raises(ConfigurationError) as exc_info:
        NoModelOrder.get_fields()
    assert "Meta.model" in str(exc_info.value)


def test_orderset_meta_fields_rejects_unknown_order_path() -> None:
    """Unknown explicit paths fail before a query can raise Django FieldError."""

    class InvalidPathOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["does_not_exist"]

    with pytest.raises(ConfigurationError, match="invalid order path"):
        InvalidPathOrder.get_fields()


def test_orderset_resolve_order_expressions_rejects_unknown_order_path() -> None:
    """The expression builder re-validates rather than trusting its caller.

    ``Meta.fields`` validation catches a bad path at declaration, but the
    builder is reachable directly and runs against the concrete
    ``queryset.model`` -- which may be a descendant of ``Meta.model``, so a
    path valid at declaration is not proven valid here. Failing loud keeps the
    error a framework ``ConfigurationError`` instead of a Django ``FieldError``
    raised from deep inside query compilation.
    """

    class ValidPathOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="invalid order path"):
        ValidPathOrder._resolve_order_expressions(
            [("does_not_exist", Ordering.ASC)],
            model=Book,
            visible_rows=_every_row,
        )


def test_orderset_all_excludes_virtual_generic_fields() -> None:
    """``__all__`` leaves out the virtual GenericRelation / GFK descriptors."""
    assert "tags" not in _get_concrete_field_names_for_order(Branch)
    assert "content_object" not in _get_concrete_field_names_for_order(TaggedItem)


# ---------------------------------------------------------------------------
# Meta.exclude narrowing (the filter family's semantics)
# ---------------------------------------------------------------------------


def _order_class(meta: dict[str, object], **attrs: object) -> type[OrderSet]:
    """Return an ``OrderSet`` subclass declared with ``class Meta`` holding ``meta``."""
    built = type(
        "ExcludeOrder",
        (OrderSet,),
        {"Meta": type("Meta", (), meta), "__module__": __name__, **attrs},
    )
    assert issubclass(built, OrderSet)
    return built


_BOOK_SWEEP = [
    "id",
    "title",
    "subtitle",
    "circulation_status",
    "shelf",
]

_EXCLUDE_GRID: dict[str, tuple[dict[str, object], list[str]]] = {
    "all + exclude": (
        {"model": Book, "fields": "__all__", "exclude": ("subtitle",)},
        [
            "id",
            "title",
            "circulation_status",
            "shelf",
        ],
    ),
    "exclude only, empty": ({"model": Book, "exclude": ()}, _BOOK_SWEEP),
    "all + empty exclude": ({"model": Book, "fields": "__all__", "exclude": []}, _BOOK_SWEEP),
    "all + excluded pk": (
        {"model": Book, "fields": "__all__", "exclude": ["id"]},
        [
            "title",
            "subtitle",
            "circulation_status",
            "shelf",
        ],
    ),
    "all + excluded many-to-many": (
        {"model": Book, "fields": "__all__", "exclude": ("genres", "loans")},
        _BOOK_SWEEP,
    ),
    "list + exclude": (
        {"model": Book, "fields": ["title", "subtitle"], "exclude": ["subtitle"]},
        ["title"],
    ),
    "tuple + frozenset exclude": (
        {"model": Book, "fields": ("subtitle", "title"), "exclude": frozenset({"subtitle"})},
        ["title"],
    ),
    "set + exclude": (
        {
            "model": Book,
            "fields": {"title", "subtitle", "circulation_status"},
            "exclude": ["title"],
        },
        ["circulation_status", "subtitle"],
    ),
    "dict + exclude": (
        {
            "model": Book,
            "fields": {"title": ["exact"], "subtitle": ["exact"]},
            "exclude": {"title"},
        },
        ["subtitle"],
    ),
    "dict exclude": (
        {"model": Book, "fields": "__all__", "exclude": {"subtitle": None, "shelf": None}},
        ["id", "title", "circulation_status"],
    ),
    "list + excluded invalid path": (
        {"model": Book, "fields": ["title", "nope"], "exclude": ["nope"]},
        ["title"],
    ),
    "list + exclude, no model": (
        {"fields": ["title", "subtitle"], "exclude": ["subtitle"]},
        ["title"],
    ),
    "list + explicit None exclude": (
        {"model": Book, "fields": ["title"], "exclude": None},
        ["title"],
    ),
}


@pytest.mark.parametrize("shape", list(_EXCLUDE_GRID))
def test_orderset_meta_exclude_narrows_the_expansion(shape: str) -> None:
    """``Meta.exclude`` drops each name it lists from the ``Meta.fields`` expansion.

    ``"__all__"`` and an exclude-only declaration sweep the model and drop the excluded names
    (the primary key included); a named declaration drops them by exact name, before path
    validation; a field the sweep never publishes (a many-to-many, a reverse relation) and an
    empty exclude drop nothing.
    """
    meta, expected = _EXCLUDE_GRID[shape]

    assert list(_order_class(meta).get_fields()) == expected


def test_orderset_meta_exclude_is_inherited_with_the_parent_meta() -> None:
    """A subclass declaring no ``Meta`` expands its parent's ``Meta.exclude``, left as declared."""
    declared = ["subtitle", "shelf"]
    parent = _order_class({"model": Book, "exclude": declared})
    child = type("ChildExcludeOrder", (parent,), {"__module__": __name__})
    assert issubclass(child, OrderSet)

    assert list(child.get_fields()) == ["id", "title", "circulation_status"]
    assert list(parent.get_fields()) == ["id", "title", "circulation_status"]
    assert introspection.mro_attr(introspection.mro_attr(parent, "Meta"), "exclude") is declared
    assert declared == ["subtitle", "shelf"]


def test_orderset_meta_exclude_sweeps_beside_related_orders_only() -> None:
    """An exclude-only set sweeps its model even when it also declares ``RelatedOrder`` branches."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    order = _order_class(
        {"model": Book, "exclude": ("subtitle",)},
        shelf=RelatedOrder(ShelfOrder, field_name="shelf"),
    )

    fields = order.get_fields()
    assert list(fields) == [
        "id",
        "title",
        "circulation_status",
        "shelf",
    ]
    assert fields["shelf"] is order.related_orders["shelf"]


def test_orderset_meta_exclude_without_model_or_fields_is_refused_beside_related_orders() -> None:
    """A model-less related-only set may not declare ``Meta.exclude``: no model to sweep."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    order = _order_class(
        {"exclude": ("subtitle",)},
        shelf=RelatedOrder(ShelfOrder, field_name="shelf"),
    )

    with pytest.raises(ConfigurationError, match=r"Meta\.exclude without Meta\.fields"):
        order.get_fields()


@pytest.mark.usefixtures("isolate_global_registry")
def test_orderset_meta_exclude_of_a_carrier_column_keeps_the_foreign_object_ordering_by_it() -> (
    None
):
    """Excluding a ``ForeignObject`` carrier drops its own term, never the link ordering by it.

    ``ShelfLabel.shelf`` is held in ``branch`` and ``shelf_code``: excluding ``shelf_code``
    leaves ``shelf``, whose term still orders by both carriers; excluding the link too leaves
    no term reading the carrier column.
    """
    carrier_only = _order_class({"model": ShelfLabel, "exclude": ("shelf_code",)})
    assert list(carrier_only.get_fields()) == [
        "id",
        "text",
        "branch",
        "shelf",
    ]
    _annotations, expressions = carrier_only._resolve_order_expressions(
        [("shelf", Ordering.ASC)],
        model=ShelfLabel,
        visible_rows=_every_row,
    )
    assert [expression.expression for expression in expressions] == [F("branch"), F("shelf_code")]

    with_link = _order_class({"model": ShelfLabel, "exclude": ("shelf_code", "shelf")})
    assert list(with_link.get_fields()) == ["id", "text", "branch"]


@pytest.mark.parametrize("kind", STR_SUBCLASS_KINDS)
def test_orderset_meta_exclude_names_a_field_through_a_str_subclass_by_its_text(kind: str) -> None:
    """A ``str``-subclass ``Meta.exclude`` entry excludes the plain name it spells, no dunder run."""
    calls: list[str] = []
    excluded = str_subclass_name(kind, "subtitle", calls)
    calls.clear()

    names = list(
        _order_class({"model": Book, "fields": "__all__", "exclude": [excluded]}).get_fields(),
    )

    assert calls == []
    assert names == [
        "id",
        "title",
        "circulation_status",
        "shelf",
    ]


_EXCLUDE_REFUSALS: dict[str, tuple[dict[str, object], str]] = {
    "bare str": (
        {"model": Book, "fields": "__all__", "exclude": "subtitle"},
        (
            "OrderSet ExcludeOrder.Meta.exclude must be a re-readable collection of field names; "
            "got str ('subtitle')."
        ),
    ),
    "lazy translation str": (
        {"model": Book, "fields": "__all__", "exclude": gettext_lazy("subtitle")},
        (
            "OrderSet ExcludeOrder.Meta.exclude must be a re-readable collection of field names; "
            "got __proxy__ ('subtitle')."
        ),
    ),
    "one-shot iterator": (
        {"model": Book, "fields": "__all__", "exclude": iter(["subtitle"])},
        (
            "OrderSet ExcludeOrder.Meta.exclude must be a re-readable collection of field names; "
            "got list_iterator"
        ),
    ),
    "None entry": (
        {"model": Book, "fields": ["title"], "exclude": [None]},
        "OrderSet ExcludeOrder.Meta.exclude entries must be field-name strings; got NoneType (None).",
    ),
    "bytes entry, no model": (
        {"fields": ["title"], "exclude": [b"title"]},
        "OrderSet ExcludeOrder.Meta.exclude entries must be field-name strings; got bytes (b'title').",
    ),
    "exclude only, no model": (
        {"exclude": ("subtitle",)},
        (
            "ExcludeOrder.Meta.exclude without Meta.fields (the '__all__' sweep minus exclude) "
            "requires Meta.model"
        ),
    ),
    "all + unknown name": (
        {"model": Book, "fields": "__all__", "exclude": ("subtitel",)},
        "OrderSet ExcludeOrder.Meta.exclude names unknown fields: ['subtitel']. Available: [",
    ),
    "exclude only + unknown name": (
        {"model": Book, "exclude": ("subtitle", "nope")},
        "OrderSet ExcludeOrder.Meta.exclude names unknown fields: ['nope']. Available: [",
    ),
    "list + unknown name": (
        {"model": Book, "fields": ["title", "subtitle"], "exclude": ["subtitel"]},
        "OrderSet ExcludeOrder.Meta.exclude names unknown fields: ['subtitel']. Available: [",
    ),
    "pk alias": (
        {"model": Book, "fields": "__all__", "exclude": ["pk"]},
        (
            "OrderSet ExcludeOrder.Meta.exclude names unknown fields: ['pk']. Available: "
            "['archive_genres', 'circulation_status', 'genres', 'id', 'loans', 'shelf', "
            "'subtitle', 'title']. Exclude only a field of Book or a Meta.fields entry."
        ),
    ),
}


@pytest.mark.parametrize("shape", list(_EXCLUDE_REFUSALS))
def test_orderset_meta_exclude_refuses_a_declaration_it_cannot_apply(shape: str) -> None:
    """A ``Meta.exclude`` the expansion cannot apply on every re-run fails closed by name.

    A bare string (a lazy translation string included) would exclude by character, a
    one-shot iterator only on the first expansion, a non-string entry would match
    nothing, an exclude-only declaration without ``Meta.model`` has no model to
    sweep, and a name that is no field and no ``Meta.fields`` entry (a typo, ``pk``)
    would leave the column it meant orderable.
    """
    meta, message = _EXCLUDE_REFUSALS[shape]

    with pytest.raises(ConfigurationError) as excinfo:
        _order_class(meta).get_fields()
    assert message in str(excinfo.value)


def _shelf_code_order() -> type[OrderSet]:
    """Return a ``Shelf`` order set a ``RelatedOrder`` branch can target."""
    built = type(
        "ShelfCodeOrder",
        (OrderSet,),
        {"Meta": type("Meta", (), {"model": Shelf, "fields": ["code"]}), "__module__": __name__},
    )
    assert issubclass(built, OrderSet)
    return built


@pytest.mark.parametrize(
    ("shape", "name"),
    [
        pytest.param("own", "shelf_branch", id="own-branch"),
        pytest.param("own-sweep", "shelf", id="own-branch-over-a-model-field"),
        pytest.param("inherited", "shelf_branch", id="inherited-branch"),
    ],
)
def test_orderset_meta_exclude_refuses_a_declared_related_order_name(
    shape: str,
    name: str,
) -> None:
    """An exclude naming a declared ``RelatedOrder`` fails when the set expands, naming the remedy.

    The expansion publishes every declared branch whatever ``Meta.exclude`` says, so the
    exclude would remove nothing and leave the branch orderable; a branch over a model
    field's own name is no exception.
    """
    branch = RelatedOrder(_shelf_code_order(), field_name="shelf")
    if shape == "inherited":
        parent = _order_class({"model": Book, "fields": ["title"]}, shelf_branch=branch)
        order = type(
            "ExcludeOrder",
            (parent,),
            {
                "Meta": type("Meta", (), {"model": Book, "fields": ["title"], "exclude": [name]}),
                "__module__": __name__,
            },
        )
        assert issubclass(order, OrderSet)
    elif shape == "own-sweep":
        order = _order_class(
            {"model": Book, "fields": "__all__", "exclude": [name]},
            shelf=branch,
        )
    else:
        order = _order_class(
            {"model": Book, "fields": ["title"], "exclude": [name]},
            shelf_branch=branch,
        )

    with pytest.raises(ConfigurationError) as excinfo:
        order.get_fields()
    assert str(excinfo.value) == (
        f"OrderSet ExcludeOrder.Meta.exclude names declared RelatedOrder branches: [{name!r}]. "
        "An exclude never removes a declaration: remove it, or disable an inherited one with "
        f"`{name} = None` in the class body."
    )


def test_orderset_meta_exclude_accepts_the_field_name_of_a_tombstoned_branch() -> None:
    """A branch disabled with ``name = None`` is no declaration, so its field excludes."""
    parent = _order_class(
        {"model": Book, "fields": "__all__"},
        shelf=RelatedOrder(_shelf_code_order(), field_name="shelf"),
    )
    child = type(
        "TombstoneOrder",
        (parent,),
        {
            "shelf": None,
            "Meta": type("Meta", (), {"model": Book, "fields": "__all__", "exclude": ["shelf"]}),
            "__module__": __name__,
        },
    )
    assert issubclass(child, OrderSet)

    assert "shelf" not in child.get_fields()


@pytest.mark.parametrize(
    "fields",
    [pytest.param({"fields": "__all__"}, id="all-fields"), pytest.param({}, id="exclude-only")],
)
def test_orderset_model_less_sweep_base_builds_and_its_subclass_supplies_the_model(
    fields: dict[str, object],
) -> None:
    """A model-less sweep is refused where it is expanded, so a base set without a model builds.

    The subclass's ``Meta`` inherits the base's declaration and adds ``Meta.model``.
    """
    base = _order_class({**fields, "exclude": ("subtitle",)})
    base_meta = introspection.mro_attr(base, "Meta")
    assert is_class(base_meta)
    child = type("ModelOrder", (base,), {"Meta": type("Meta", (base_meta,), {"model": Book})})
    assert issubclass(child, OrderSet)

    assert list(child.get_fields()) == [
        "id",
        "title",
        "circulation_status",
        "shelf",
    ]
    with pytest.raises(ConfigurationError, match=r"requires Meta\.model"):
        base.get_fields()


_META_KEY_REFUSALS: dict[str, tuple[object, str]] = {
    "unknown key": (
        type("Meta", (), {"model": Book, "fields": ["title"], "bogus": True}),
        "OrderSet MetaKeyOrder.Meta has unknown keys: ['bogus'].",
    ),
    "misspelt fields": (
        type("Meta", (), {"model": Book, "fiels": ["title"]}),
        "OrderSet MetaKeyOrder.Meta has unknown keys: ['fiels'].",
    ),
    "filter-family synonym": (
        type("Meta", (), {"model": Book, "filter_fields": ["title"]}),
        "OrderSet MetaKeyOrder.Meta has unknown keys: ['filter_fields'].",
    ),
    "non-class Meta": (
        SimpleNamespace(model=Book, fields=["title"]),
        "OrderSet MetaKeyOrder.Meta must be a class; got namespace(",
    ),
}


@pytest.mark.parametrize("shape", list(_META_KEY_REFUSALS))
def test_orderset_meta_refuses_an_unknown_key_at_class_creation(shape: str) -> None:
    """An own ``Meta`` declaring a key an order set does not read fails at class creation.

    ``model`` / ``fields`` / ``exclude`` are the whole vocabulary; a typo would otherwise
    narrow nothing. The guard is the one every write flavor runs.
    """
    meta, message = _META_KEY_REFUSALS[shape]

    with pytest.raises(ConfigurationError) as excinfo:
        type("MetaKeyOrder", (OrderSet,), {"Meta": meta, "__module__": __name__})
    assert str(excinfo.value).startswith(message)


def test_orderset_meta_key_guard_reads_only_the_class_body_own_meta() -> None:
    """A subclass without its own ``Meta`` is not re-checked; an inherited ``Meta`` key counts once.

    A subclassed ``Meta`` declares only its own keys, so the parent's legal keys never read as
    the child's.
    """
    parent = _order_class({"model": Book, "fields": ["title"], "exclude": ["subtitle"]})
    parent_meta = introspection.mro_attr(parent, "Meta")
    assert is_class(parent_meta)
    child = type("PlainChildOrder", (parent,), {"__module__": __name__})
    grandchild = type(
        "MetaChildOrder",
        (parent,),
        {
            "Meta": type("Meta", (parent_meta,), {"fields": ["subtitle"]}),
            "__module__": __name__,
        },
    )
    assert issubclass(child, OrderSet)
    assert issubclass(grandchild, OrderSet)

    assert list(child.get_fields()) == ["title"]
    assert list(grandchild.get_fields()) == []


# ---------------------------------------------------------------------------
# apply_sync / apply_async / permissions fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_orderset_state() -> Iterator[None]:
    """Clear class-level factory caches + per-test field-spec ledger."""
    _materialized_names.clear()
    _field_specs.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    _type_name_claims.clear()
    yield
    _materialized_names.clear()
    _field_specs.clear()
    OrderArgumentsFactory.input_object_types.clear()
    OrderArgumentsFactory._type_orderset_registry.clear()
    _type_name_claims.clear()


def _every_row(scope: type[DjangoType]) -> QuerySet[Model]:
    """Every row of ``scope``'s model: a visibility reader for terms no hook should scope."""
    return model_for(scope)._base_manager.all()


def _make_info(*, user_is_anonymous: bool = False) -> SimpleNamespace:
    """Build a minimal ``info``-shaped stub with a Django ``HttpRequest`` on it."""
    request = HttpRequest()
    request.user = AnonymousUser() if user_is_anonymous else User(username="u")
    return SimpleNamespace(context=SimpleNamespace(request=request))


def _book_order_with_factory() -> tuple[type[OrderSet], Callable[..., object]]:
    """Declare ``BookOrder`` + build its Strawberry input class via the factory."""

    class BookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "subtitle"]

    factory = OrderArgumentsFactory(BookOrder)
    input_cls = _keyword_constructor(factory.arguments)
    return BookOrder, input_cls


# ---------------------------------------------------------------------------
# apply_async
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_orderset_apply_async_via_asyncio_run() -> None:
    """``apply_async`` writes a nonempty ``query.order_by`` for a scalar term.

    Consumer to-many async colour is
    ``test_library_genres_order_by_to_many_desc_applies_over_graphql_async``
    on ``allLibraryGenresViaListField``.
    """
    BookOrder, BookInput = _book_order_with_factory()
    input_value = [BookInput(title=Ordering.ASC)]
    info = _make_info()
    queryset = Book.objects.all()
    result = asyncio.run(BookOrder.apply_async(input_value, queryset, info))
    order_by = list(result.query.order_by)
    assert order_by


@pytest.mark.django_db
def test_orderset_apply_async_runs_check_permission_in_sync_to_async() -> None:
    """``check_*_permission`` raising propagates through the event loop."""

    class GatedAsyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        def check_title_permission(self, request: HttpRequest) -> None:
            if request.user.is_anonymous:
                raise GraphQLError("staff only", extensions={"code": "ORDER_PERMISSION_DENIED"})

    factory = OrderArgumentsFactory(GatedAsyncOrder)
    BookInput = _keyword_constructor(factory.arguments)
    input_value = [BookInput(title=Ordering.ASC)]
    info = _make_info(user_is_anonymous=True)
    queryset = Book.objects.all()
    with pytest.raises(GraphQLError):
        asyncio.run(GatedAsyncOrder.apply_async(input_value, queryset, info))


# ---------------------------------------------------------------------------
# Active-input-only + active-branch double-dispatch + dedup
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_orderset_check_permission_dedups_repeated_list_entries() -> None:
    """The dedup map fires each ``check_<field>_permission`` once per class."""
    counts = {"shelf": 0, "code": 0}

    class ShelfOrderDedup(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

        def check_code_permission(self, _request: object) -> None:
            counts["code"] += 1

    class BookOrderDedup(OrderSet):
        shelf = RelatedOrder(ShelfOrderDedup, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

        def check_shelf_permission(self, _request: object) -> None:
            counts["shelf"] += 1

    factory = OrderArgumentsFactory(BookOrderDedup)
    BookInput = _keyword_constructor(factory.arguments)
    ShelfInput = _keyword_constructor(
        OrderArgumentsFactory.input_object_types["ShelfOrderDedupInputType"],
    )
    input_value = [
        BookInput(shelf=ShelfInput(code=Ordering.ASC)),
        BookInput(shelf=ShelfInput(code=Ordering.DESC)),
    ]
    BookOrderDedup.apply_sync(input_value, Book.objects.all(), _make_info())
    # Each gate fires exactly once across the two list elements.
    assert counts["shelf"] == 1
    assert counts["code"] == 1


# ---------------------------------------------------------------------------
# _request_from_info shapes
# ---------------------------------------------------------------------------


def test_orderset_request_from_info_reads_context_request_attribute() -> None:
    """``info.context.request`` is the canonical shape."""
    request = HttpRequest()
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    assert OrderSet._request_from_info(info) is request


def test_orderset_request_from_info_reads_bare_httprequest_context() -> None:
    """``info.context`` being a bare ``HttpRequest`` is also accepted."""
    request = HttpRequest()
    info = SimpleNamespace(context=request)
    assert OrderSet._request_from_info(info) is request


def test_orderset_request_from_info_raises_on_unrecognized_context_shape() -> None:
    """A non-HttpRequest context with no ``.request`` attribute raises."""

    class _PlainCtx:
        pass

    info = SimpleNamespace(context=_PlainCtx())
    with pytest.raises(ConfigurationError) as exc_info:
        OrderSet._request_from_info(info)
    assert "OrderSet could not resolve" in str(exc_info.value)


def test_orderset_request_from_info_raises_when_info_context_is_none() -> None:
    """``info.context = None`` raises ``ConfigurationError``."""
    info = SimpleNamespace(context=None)
    with pytest.raises(ConfigurationError):
        OrderSet._request_from_info(info)


# ---------------------------------------------------------------------------
# get_flat_orders walker
# ---------------------------------------------------------------------------


def test_orderset_get_flat_orders_walks_normalized_pairs() -> None:
    """``get_flat_orders`` is a pass-through that applies the prefix per element."""
    result = OrderSet.get_flat_orders(
        [("title", Ordering.ASC), ("shelf__code", Ordering.DESC)],
    )
    assert result == [("title", Ordering.ASC), ("shelf__code", Ordering.DESC)]


def test_orderset_get_flat_orders_applies_prefix() -> None:
    """The ``prefix`` argument concatenates to each field path."""
    result = OrderSet.get_flat_orders(
        [("code", Ordering.ASC)],
        prefix="shelf__",
    )
    assert result == [("shelf__code", Ordering.ASC)]


# ---------------------------------------------------------------------------
# _normalize_input delegate (smoke; full coverage in test_inputs)
# ---------------------------------------------------------------------------


def test_orderset_normalize_input_delegates_to_module_helper() -> None:
    """The classmethod is a thin delegate to ``normalize_input_value``."""

    class BookOrderNormalize(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrderNormalize)
    BookInput = _keyword_constructor(factory.arguments)
    input_value = [BookInput(title=Ordering.ASC)]
    result = BookOrderNormalize._normalize_input(input_value)
    assert result == [("title", Ordering.ASC)]


@pytest.mark.django_db
def test_orderset_direct_mapping_initializes_specs_before_permissions() -> None:
    """Flat mappings must not bypass nested target permission gates."""

    class ShelfOrderDirectMapping(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

        def check_code_permission(self, _request: object) -> NoReturn:
            raise GraphQLError("code gate fired")

    class BookOrderDirectMapping(OrderSet):
        shelf = RelatedOrder(ShelfOrderDirectMapping, field_name="shelf")

        class Meta:
            model = Book
            fields = ["shelf__code"]

    with pytest.raises(GraphQLError, match="code gate fired"):
        BookOrderDirectMapping.apply_sync(
            {"shelf_code": Ordering.ASC},
            Book.objects.all(),
            _make_info(),
        )


def test_orderset_inactive_input_does_not_resolve_lazy_related_target() -> None:
    """None and empty-list order inputs remain no-ops before lazy resolution."""

    class NoOpOrder(OrderSet):
        shelf = RelatedOrder("MissingOrderForNoOp", field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    queryset = Book.objects.all()
    assert NoOpOrder.apply_sync(None, queryset, _make_info()) is queryset
    assert NoOpOrder.apply_sync([], queryset, _make_info()) is queryset
    assert NoOpOrder.apply_sync({}, queryset, _make_info()) is queryset


# ---------------------------------------------------------------------------
# sets.py edge-case branches
# ---------------------------------------------------------------------------


def test_orderset_expand_meta_fields_returns_empty_when_meta_has_no_fields_attr() -> None:
    """Covers ``orders/sets.py::OrderSet._expand_meta_fields`` #"if meta_fields is None:".

    Declaring ``Meta`` without a ``fields`` attribute -> the shared
    ``read_set_meta_fields(meta)`` reader returns ``None``; the helper
    early-returns an empty ``OrderedDict``.
    """

    class NoFieldsOrder(OrderSet):
        class Meta:
            model = Book

    result = NoFieldsOrder._expand_meta_fields()
    assert isinstance(result, OrderedDict)
    assert result == OrderedDict()


def test_orderset_extract_branch_value_returns_none_for_none_input() -> None:
    """Covers ``utils/permissions.py::extract_branch_value`` #"if input_value is None:"."""
    assert OrderSet._extract_branch_value(None, "anything") is None


def test_orderset_extract_branch_value_reads_dict_field() -> None:
    """Covers ``utils/input_values.py::input_field_value``'s dict branch.

    ``OrderSet._extract_branch_value`` delegates the dict-vs-dataclass sniff
    to that primitive, whose #"if isinstance(input_value, dict):" arm reads
    via ``dict.get`` so a missing key collapses to ``None`` rather than
    raising ``KeyError``.
    """
    assert OrderSet._extract_branch_value({"shelf": "value"}, "shelf") == "value"
    assert OrderSet._extract_branch_value({"shelf": "value"}, "missing") is None


def test_orderset_active_permission_leaf_paths_returns_empty_for_none_input() -> None:
    """Covers ``utils/input_values.py::iter_active_fields`` #"is_inactive_value(input_value"."""
    assert OrderSet._active_permission_targets(None)[0] == []


def test_orderset_active_permission_leaf_paths_returns_empty_for_non_dataclass_non_dict_input() -> (
    None
):
    """Covers ``utils/input_values.py::iter_active_fields`` #"if items is None:".

    A plain object (no ``__dataclass_fields__``, not a ``dict``) makes
    ``iter_input_items`` return ``None``, so the walker yields nothing and
    the delegate hands back an empty list.
    """
    assert OrderSet._active_permission_targets(object())[0] == []


def test_orderset_active_permission_leaf_paths_walks_dict_items() -> None:
    """Covers ``utils/input_values.py::iter_input_items`` #"if isinstance(input_value, dict):".

    Dict-shaped inputs are walked through ``dict.items`` so the
    active-input walker treats a dict like a dataclass.
    """

    class DictInputOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    # Populate ``_field_specs`` so the spec lookup in
    # ``utils/permissions.py::active_permission_targets`` returns a real
    # ``django_source_path`` rather than the python-attr fallback.
    _ = OrderArgumentsFactory(DictInputOrder).arguments

    paths = DictInputOrder._active_permission_targets({"title": Ordering.ASC})[0]
    assert paths == ["title"]


def test_orderset_active_permission_leaf_paths_falls_back_to_python_attr_when_no_field_spec_entry() -> (
    None
):
    """Covers ``utils/permissions.py::active_permission_targets`` #"else fallback_path(field.python_attr)".

    When ``_field_specs`` has no entry for ``(cls, python_attr)`` (e.g.
    a permission check fired outside the apply pipeline before
    ``_build_input_fields`` ran), ``field.spec`` is ``None`` and the
    walker falls back to the python-attr token rather than dropping the
    field.
    """

    class NoSpecsActiveOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    # Do NOT call ``_build_input_fields`` -- the ``_field_specs`` ledger
    # has no entry for ``(NoSpecsActiveOrder, "title")``. The autouse
    # ``_isolate_orderset_state`` fixture clears it at entry.
    paths = NoSpecsActiveOrder._active_permission_targets({"title": Ordering.ASC})[0]
    assert paths == ["title"]


@pytest.mark.django_db
def test_orderset_apply_sync_returns_queryset_when_all_directions_filter_to_empty_expressions() -> (
    None
):
    """Covers ``orders/sets.py::OrderSet._apply_orderings`` #"if not expressions:".

    A subclass overrides ``_normalize_input`` to emit
    ``[("title", None)]`` -- non-empty ``data``, so the #"if not data:"
    early return is skipped, but ``_resolve_order_expressions``'s
    #"if direction is None:" skip drops the one term, leaving an empty
    ``expressions`` list. Reached here through ``apply_sync``; the async
    entry point reaches the same guard in
    ``test_orderset_apply_async_returns_queryset_when_all_directions_filter_to_empty_expressions``.
    """

    class _NoneDirectionSyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        @override
        def _normalize_input(cls, input_value: object) -> list[tuple[str, Ordering | None]]:
            return [("title", None)]

    info = _make_info()
    queryset = Book.objects.all()
    result = _NoneDirectionSyncOrder.apply_sync(None, queryset, info)
    assert result is queryset


@pytest.mark.django_db
def test_orderset_apply_async_returns_queryset_when_data_is_empty() -> None:
    """Covers ``orders/sets.py::OrderSet._apply_orderings`` #"if not data:" via ``apply_async``.

    Calling ``apply_async`` with an empty list yields an empty normalized
    data list, hitting that early return before any ``order_by(...)``
    clause is built. ``apply_sync`` and ``apply_async`` share the one
    helper, so this row pins the async entry point reaching it, not a
    second copy of the guard.
    """

    class _EmptyAsyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    info = _make_info()
    queryset = Book.objects.all()
    result = asyncio.run(_EmptyAsyncOrder.apply_async([], queryset, info))
    assert result is queryset


@pytest.mark.django_db
def test_orderset_apply_async_returns_queryset_when_all_directions_filter_to_empty_expressions() -> (
    None
):
    """Covers ``orders/sets.py::OrderSet._apply_orderings`` #"if not expressions:" via ``apply_async``.

    Symmetric of the sync-side row: a subclass overrides
    ``_normalize_input`` to emit ``[("title", None)]`` and the async
    entry point reaches the same shared guard.
    """

    class _NoneDirectionAsyncOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        @override
        def _normalize_input(cls, input_value: object) -> list[tuple[str, Ordering | None]]:
            return [("title", None)]

    info = _make_info()
    queryset = Book.objects.all()
    result = asyncio.run(_NoneDirectionAsyncOrder.apply_async(None, queryset, info))
    assert result is queryset


# =============================================================================
# Row-preserving to-many ordering - aggregate, not fan-out JOIN
# =============================================================================


def test_path_traverses_to_many_detects_multiplying_relations() -> None:
    """``_path_traverses_to_many`` flags reverse-FK / M2M paths, not scalar / to-one."""
    assert _path_traverses_to_many(Branch, "shelves__code") is True  # reverse FK
    assert _path_traverses_to_many(Book, "genres__name") is True  # forward M2M
    assert _path_traverses_to_many(Genre, "books__title") is True  # reverse M2M
    assert _path_traverses_to_many(Book, "shelf__code") is False  # forward FK (to-one)
    assert _path_traverses_to_many(Genre, "name") is False  # scalar
    assert _path_traverses_to_many(Branch, "city") is False  # scalar


def test_path_traverses_to_many_is_cached() -> None:
    """Repeated to-many path checks reuse the metadata walk."""
    relations._path_traverses_to_many_cache_clear()
    try:
        assert _path_traverses_to_many(Branch, "shelves__code") is True
        assert _path_traverses_to_many(Branch, "shelves__code") is True

        cache_info = relations._path_traverses_to_many_cached.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits == 1
    finally:
        relations._path_traverses_to_many_cache_clear()


def test_resolve_order_expressions_aggregates_to_many_orders_scalar_directly() -> None:
    """A to-many term orders by a ``Min`` aggregate; a scalar term orders directly.

    Consumer two-term ``MIN(`` SQL is
    ``test_library_books_order_by_two_to_many_terms_each_get_their_own_aggregate``.
    """

    class _MultBranchOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["name"]

    annotations, expressions = _MultBranchOrder._resolve_order_expressions(
        [("shelves__code", Ordering.ASC), ("name", Ordering.DESC)],
        model=Branch,
        visible_rows=_every_row,
    )
    # The to-many path produced exactly one aggregate annotation (``Min`` for ASC).
    assert len(annotations) == 1
    ((alias, aggregate),) = annotations.items()
    assert isinstance(aggregate, Min)
    # Two order expressions: the aggregate alias (term 0) + the direct scalar (term 1).
    assert len(expressions) == 2
    assert isinstance(expressions[0].expression, F)
    assert isinstance(expressions[1].expression, F)
    # orders by the annotation alias
    assert expressions[0].expression == F(alias)
    # scalar ordered directly
    assert expressions[1].expression == F("name")


@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.parametrize(
    ("direction", "aggregate_name"),
    [(Ordering.ASC, "Min"), (Ordering.DESC_NULLS_LAST, "Max")],
    ids=["asc_min", "desc_max"],
)
def test_resolve_order_expressions_aggregates_each_carrier_of_a_to_many_foreign_object(
    direction: Ordering,
    aggregate_name: str,
) -> None:
    """A to-many path ending on a multi-column ``ForeignObject`` aggregates each carrier.

    ``Branch.shelf_labels`` fans out to the labels and ``ShelfLabel.shelf`` is
    held in ``branch`` and ``shelf_code``, so the term is two aggregates, one
    per carrier in link order, each under its own alias and ordered in the
    term's direction. No type is registered, so no relation hides rows and
    each aggregate reads its carrier path directly.
    """

    class _LabelShelfOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["shelf_labels__shelf"]

    annotations, expressions = _LabelShelfOrder._resolve_order_expressions(
        [("shelf_labels__shelf", direction)],
        model=Branch,
        visible_rows=_every_row,
    )

    assert {
        alias: (type(aggregate).__name__, aggregate.source_expressions)
        for alias, aggregate in annotations.items()
    } == {
        "_dst_order_0_shelf_labels_branch": (aggregate_name, [F("shelf_labels__branch")]),
        "_dst_order_0_shelf_labels_shelf_code": (aggregate_name, [F("shelf_labels__shelf_code")]),
    }
    assert [expression.expression for expression in expressions] == [
        F("_dst_order_0_shelf_labels_branch"),
        F("_dst_order_0_shelf_labels_shelf_code"),
    ]
    assert {expression.descending for expression in expressions} == {
        not direction.is_ascending,
    }


def test_path_traverses_to_many_returns_false_for_nonmultiplying_paths() -> None:
    """``_path_traverses_to_many`` returns False for unresolvable / generic / all-to-one paths.

    Covers the three non-multiplying exits: an unresolvable segment
    (``FieldDoesNotExist``), a relation field with no concrete ``related_model``
    (a ``GenericForeignKey``), and a path that resolves entirely through to-one
    relations without ever reaching a to-many.
    """
    # Unresolvable terminal / mid segment -> FieldDoesNotExist exit.
    assert _path_traverses_to_many(Branch, "does_not_exist") is False
    assert _path_traverses_to_many(Book, "shelf__nope") is False
    # GenericForeignKey: is_relation, not many-side, but related_model is None.
    assert _path_traverses_to_many(TaggedItem, "content_object") is False
    # All-to-one chain ending on a relation (no scalar terminal, never to-many).
    assert _path_traverses_to_many(Book, "shelf__branch") is False


@pytest.mark.django_db
def test_orderset_apply_sync_handles_unset_in_nested_dict() -> None:
    """apply_sync with UNSET fields normalizes cleanly and preserves queryset."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    branch = Branch.objects.create(name="Main")
    shelf = Shelf.objects.create(code="S1", branch=branch)
    book = Book.objects.create(shelf=shelf, title="Book 1")
    info = _make_info()
    qs = Book.objects.all()
    result = BookOrder.apply_sync({"shelf": {"code": UNSET}}, qs, info)
    assert list(result.query.order_by) == list(qs.query.order_by)
    assert list(result) == [book]


@pytest.mark.django_db
def test_orderset_expand_meta_fields_rejects_non_iterable_fields() -> None:
    """Non-collection or string Meta.fields (other than '__all__') raises ConfigurationError.

    A lazy translation string is a string: its proxy class is no ``str``, yet it would
    expand into one order path per character.
    """

    class IntFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = 123

    with pytest.raises(
        ConfigurationError,
        match="must be '__all__' or a re-readable collection of field names",
    ):
        IntFieldsOrder.get_fields()

    class StrFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = "title"

    with pytest.raises(
        ConfigurationError,
        match="not a bare string",
    ):
        StrFieldsOrder.get_fields()

    class LazyStrFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = gettext_lazy("title")

    with pytest.raises(
        ConfigurationError,
        match=r"got __proxy__ \('title'\)\. .*not a bare string",
    ):
        LazyStrFieldsOrder.get_fields()

    class ObjFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = object()

    with pytest.raises(
        ConfigurationError,
        match="must be '__all__' or a re-readable collection of field names",
    ):
        ObjFieldsOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_lazy_all_is_the_shorthand() -> None:
    """A lazy translation ``"__all__"`` compares equal to the shorthand and sweeps as it does."""

    class LazyAllOrder(OrderSet):
        class Meta:
            model = Book
            fields = gettext_lazy("__all__")

    class PlainAllOrder(OrderSet):
        class Meta:
            model = Book
            fields = "__all__"

    assert list(LazyAllOrder.get_fields()) == list(PlainAllOrder.get_fields())


@pytest.mark.django_db
def test_orderset_expand_meta_fields_rejects_non_string_entries_without_model() -> None:
    """Entry-TYPE validation is unconditional: it does not need ``Meta.model``.

    The model-less related-only arm validates entries too, so a ``None`` /
    bytes / unhashable entry neither lands silently in the expansion
    (``{None: None}``, ``{b'title': None}``) nor escapes as a raw
    ``TypeError: unhashable type`` from the expansion-dict write. Every
    entry is a path token regardless of ``Meta.model``, so the entry-type
    gate fires before the model-guarded path walk.
    """

    class NoModelNoneEntryOrder(OrderSet):
        class Meta:
            fields = [None]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        NoModelNoneEntryOrder.get_fields()

    class NoModelBytesEntryOrder(OrderSet):
        class Meta:
            fields = [b"title"]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        NoModelBytesEntryOrder.get_fields()

    class UnhashableEntryOrder(OrderSet):
        class Meta:
            fields = [["title"]]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        UnhashableEntryOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_rejects_non_string_entries_with_model() -> None:
    """The entry-type gate precedes path validation, with or without ``Meta.model``."""

    class NoneEntryOrder(OrderSet):
        class Meta:
            model = Book
            fields = [None]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        NoneEntryOrder.get_fields()

    class BytesEntryOrder(OrderSet):
        class Meta:
            model = Book
            fields = [b"title"]

    with pytest.raises(ConfigurationError, match="entries must be field-name strings"):
        BytesEntryOrder.get_fields()


_STR_SUBCLASS_ORDER_SHAPES: dict[str, Callable[[Callable[[str], str]], object]] = {
    "list": lambda n: [n("title"), "subtitle"],
    "tuple": lambda n: (n("title"), "subtitle"),
    "set": lambda n: {n("title"), "subtitle", "circulation_status"},
    "frozenset": lambda n: frozenset({n("title"), "subtitle"}),
    "dict key": lambda n: {n("title"): ["exact"], "subtitle": ["exact"]},
    "dict_keys": lambda n: {n("title"): None, "subtitle": None}.keys(),
    "top-level __all__": lambda n: n("__all__"),
}


@pytest.mark.django_db
@pytest.mark.parametrize("kind", STR_SUBCLASS_KINDS)
@pytest.mark.parametrize("shape", list(_STR_SUBCLASS_ORDER_SHAPES))
def test_orderset_meta_names_a_field_through_a_str_subclass_by_its_text(
    shape: str,
    kind: str,
) -> None:
    """A ``str``-subclass name in ``Meta.fields`` expands exactly as the plain name it spells.

    The expanded field map is keyed by plain ``str`` in the same order the
    plain declaration gives (a ``set`` sorts as the plain names would), and no
    dunder of the subclass runs.
    """
    calls: list[str] = []
    declare = _STR_SUBCLASS_ORDER_SHAPES[shape]
    meta = type(
        "Meta",
        (),
        {"model": Book, "fields": declare(lambda t: str_subclass_name(kind, t, calls))},
    )
    plain_meta = type("Meta", (), {"model": Book, "fields": declare(str)})
    calls.clear()

    probe = type("StrSubclassOrder", (OrderSet,), {"Meta": meta, "__module__": __name__})
    plain = type("PlainOrder", (OrderSet,), {"Meta": plain_meta, "__module__": __name__})
    assert issubclass(probe, OrderSet)
    assert issubclass(plain, OrderSet)
    names = list(probe.get_fields())

    assert calls == []
    assert all(type(name) is str for name in names)
    assert names == list(plain.get_fields())
    assert "title" in names


_LAZY_ORDER_FIELDS: dict[str, Callable[[Callable[[Callable[[], object]], object]], object]] = {
    "list": lambda w: w(lambda: ["title", "subtitle"]),
    "tuple": lambda w: w(lambda: ("title", "subtitle")),
    "set": lambda w: w(lambda: {"title", "subtitle", "circulation_status"}),
    "frozenset": lambda w: w(lambda: frozenset({"title", "subtitle"})),
    "dict": lambda w: w(lambda: {"title": ["exact"], "subtitle": ["exact"]}),
    "str-enum member": lambda w: w(
        lambda: [STR_ENUM("Names", {"TITLE": "title"})["TITLE"], "subtitle"],
    ),
    "nested lazy": lambda w: w(lambda: w(lambda: ["title", "subtitle"])),
}


@pytest.mark.django_db
@pytest.mark.parametrize("shape", list(_LAZY_ORDER_FIELDS))
def test_orderset_reads_a_lazy_meta_fields_as_the_object_it_stands_for(shape: str) -> None:
    """A ``SimpleLazyObject`` ``Meta.fields`` expands exactly as its evaluated twin does.

    A ``set`` sorts as the twin would, a lookup-bag ``dict`` degrades to its keys,
    and every name is plain ``str``.
    """
    declare = _LAZY_ORDER_FIELDS[shape]
    meta = type("Meta", (), {"model": Book, "fields": declare(SimpleLazyObject)})
    twin_meta = type("Meta", (), {"model": Book, "fields": declare(lambda target: target())})

    probe = type("LazyOrder", (OrderSet,), {"Meta": meta, "__module__": __name__})
    twin = type("TwinOrder", (OrderSet,), {"Meta": twin_meta, "__module__": __name__})
    assert issubclass(probe, OrderSet)
    assert issubclass(twin, OrderSet)
    names = list(probe.get_fields())

    assert names == list(twin.get_fields())
    assert all(type(name) is str for name in names)
    assert "title" in names


@pytest.mark.parametrize("shape", ["iterator", "generator"])
def test_orderset_expand_meta_fields_rejects_one_shot_iterator_fields(shape: str) -> None:
    """A one-shot fields declaration is refused before a later reread could exhaust it."""
    declared_fields: Iterator[str] = (
        iter(["title", "subtitle"])
        if shape == "iterator"
        else (name for name in ["title", "subtitle"])
    )

    class OneShotFieldsOrder(OrderSet):
        if shape == "iterator":
            shelf = RelatedOrder("tests.orders.test_sets.MissingOrder", field_name="shelf")

        class Meta:
            model = Book
            fields = declared_fields

    with pytest.raises(ConfigurationError, match="re-readable"):
        OneShotFieldsOrder.get_fields()


@pytest.mark.parametrize("shape", ["keys-view", "custom-collection"])
def test_orderset_expand_meta_fields_accepts_a_computed_re_readable_collection(shape: str) -> None:
    """A view or consumer Collection preserves its declared order on successive expansions."""

    class _NameSet:
        def __init__(self, *names: str) -> None:
            self._names = names

        def __iter__(self) -> Iterator[str]:
            return iter(self._names)

        def __len__(self) -> int:
            return len(self._names)

        def __contains__(self, item: object) -> bool:
            return item in self._names

    declared_fields = (
        {"title": None, "subtitle": None}.keys()
        if shape == "keys-view"
        else _NameSet("title", "subtitle")
    )

    class CollectionFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = declared_fields

    assert list(CollectionFieldsOrder._expand_meta_fields()) == ["title", "subtitle"]
    assert list(CollectionFieldsOrder._expand_meta_fields()) == ["title", "subtitle"]


def test_orderset_expand_meta_fields_rejects_hostile_iterable_without_iterating() -> None:
    """A hostile ``__iter__`` raising midway is rejected by the container gate.

    The shape gate is structural (an ``isinstance`` container check), so a
    one-shot iterable whose ``__iter__`` raises mid-iteration never gets
    iterated at all: the raw ``RuntimeError`` cannot escape ``get_fields()``
    because the object is rejected before the walk starts.
    """

    class Boom:
        def __iter__(self) -> Iterator[str]:
            yield "title"  # never reached past the gate
            raise RuntimeError("boom mid-iteration")

    class HostileIterOrder(OrderSet):
        class Meta:
            model = Book
            fields = Boom()

    with pytest.raises(ConfigurationError, match="re-readable"):
        HostileIterOrder.get_fields()


@pytest.mark.django_db
def test_orderset_expand_meta_fields_dict_shape_iterates_keys() -> None:
    """Dict-shaped ``Meta.fields`` (django-filter lookup bags) expands the KEYS.

    Pins the documented degradation: the lookup-bag values are dropped and
    each key becomes an order field, so a consumer porting a filter-style
    ``fields`` dict gets field-name ordering instead of a silent error.
    """

    class DictFieldsOrder(OrderSet):
        class Meta:
            model = Book
            fields = {"title": ["exact"], "subtitle": ["icontains"]}

    fields = DictFieldsOrder.get_fields()
    assert list(fields) == ["title", "subtitle"]
    assert all(v is None for v in fields.values())


@pytest.mark.parametrize(
    ("invalid_model", "model_name"),
    [("NotAModel", "str"), (123, "int")],
    ids=["string", "integer"],
)
def test_orderset_expand_meta_fields_handles_non_class_meta_model(
    invalid_model: object,
    model_name: str,
) -> None:
    """An invalid Meta.model gets its named ConfigurationError instead of an attribute crash."""

    class BadModelOrder(OrderSet):
        class Meta:
            model = invalid_model
            fields = ["title"]

    with pytest.raises(
        ConfigurationError,
        match=f"invalid order path 'title' for model {model_name}",
    ):
        BadModelOrder.get_fields()


@pytest.mark.parametrize("invalid_model", ["NotAModel", 123], ids=["string", "integer"])
def test_get_concrete_field_names_for_order_rejects_non_model(invalid_model: object) -> None:
    """The private concrete-field reader refuses each non-model input before reading metadata."""
    with pytest.raises(ConfigurationError, match="Expected a Django Model class"):
        _get_concrete_field_names_for_order(invalid_model)


def test_resolve_order_expressions_handles_non_class_model_on_path_error() -> None:
    """_resolve_order_expressions safely formats non-class model when path resolution fails."""

    class CustomBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(ConfigurationError, match="invalid order path 'bad_field' for model str"):
        CustomBookOrder._resolve_order_expressions(
            [("bad_field", Ordering.ASC)],
            # basedpyright: the string model is the hostile input under test;
            # _resolve_order_expressions types the parameter as type[Model]
            model="NotAModel",  # pyright: ignore[reportArgumentType]
            visible_rows=_every_row,
        )


def test_orderset_clear_order_input_namespace_clears_subclass_caches() -> None:
    """clear_order_input_namespace clears _expanded_fields on base and subclass OrderSets."""

    class BaseOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    class SubOrder(BaseOrder):
        # basedpyright: an OrderSet subclass declares its own ``Meta`` (the django-filter idiom),
        # never a subclass of the parent's
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = Book
            fields = ["subtitle"]

    assert list(BaseOrder.get_fields()) == ["title"]
    assert list(SubOrder.get_fields()) == ["subtitle"]
    assert BaseOrder._expanded_fields is not None
    assert SubOrder._expanded_fields is not None

    clear_order_input_namespace()

    assert BaseOrder._expanded_fields is None
    assert SubOrder._expanded_fields is None


def test_orderset_type_name_for_inherits_mixin_naming_convention() -> None:
    """OrderSet inherits ClassBasedTypeNameMixin defaulting to '<Name>InputType'."""

    class CustomOrder(OrderSet):
        pass

    assert CustomOrder.type_name_for() == "CustomOrderInputType"
    assert CustomOrder.type_name_for("field") == "CustomOrderFieldInputType"


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (None, False),
        (UNSET, False),
        ([], False),
        (["__EMPTY_BOOK_INPUT__"], False),
        (["__NULL_TITLE_BOOK_INPUT__"], False),
        (["__EMPTY_SHELF_BOOK_INPUT__"], False),
        (["__NULL_SHELF_CODE_BOOK_INPUT__"], False),
        (["__NULL_TITLE_BOOK_INPUT__", "__NULL_SHELF_CODE_BOOK_INPUT__"], False),
        (["__ACTIVE_TITLE_BOOK_INPUT__"], True),
        (["__ACTIVE_SHELF_BOOK_INPUT__"], True),
        (["__NULL_TITLE_BOOK_INPUT__", "__ACTIVE_SHELF_BOOK_INPUT__"], True),
        (["__ACTIVE_TITLE_BOOK_INPUT__", "__NULL_TITLE_BOOK_INPUT__"], True),
    ],
)
def test_input_has_active_terms_contract(input_value: object, *, expected: bool) -> None:
    """Pin OrderSet._input_has_active_terms against a comprehensive input variation matrix."""

    class ShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class BookOrder(OrderSet):
        shelf = RelatedOrder(ShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    factory = OrderArgumentsFactory(BookOrder)
    BookInput = _keyword_constructor(factory.arguments)
    ShelfInput = _keyword_constructor(
        OrderArgumentsFactory.input_object_types["ShelfOrderInputType"],
    )

    sentinel_map = {
        "__EMPTY_BOOK_INPUT__": [BookInput()],
        "__NULL_TITLE_BOOK_INPUT__": [BookInput(title=None)],
        "__EMPTY_SHELF_BOOK_INPUT__": [BookInput(shelf=ShelfInput())],
        "__NULL_SHELF_CODE_BOOK_INPUT__": [BookInput(shelf=ShelfInput(code=None))],
        "__ACTIVE_TITLE_BOOK_INPUT__": [BookInput(title=Ordering.ASC)],
        "__ACTIVE_SHELF_BOOK_INPUT__": [BookInput(shelf=ShelfInput(code=Ordering.DESC))],
    }

    resolved_input: object = input_value
    if is_object_list(input_value) and input_value and isinstance(input_value[0], str):
        resolved: list[object] = []
        for sentinel in input_value:
            assert isinstance(sentinel, str)
            resolved.extend(sentinel_map[sentinel])
        resolved_input = resolved

    assert BookOrder._input_has_active_terms(resolved_input) is expected


@pytest.mark.parametrize("guarded", [False, True], ids=["ordinary-context", "guarded-context"])
def test_public_apply_never_writes_the_consumer_context(*, guarded: bool) -> None:
    """``apply_sync`` / ``apply_async`` leave ``info.context`` exactly as they found it.

    A public apply on a connection or in a hand-written resolver stores nothing on
    the consumer's context: an existing value is never overwritten or deleted, and a
    mapping that forbids writes is never asked to accept one.
    """

    class GuardedContext(dict[str, object]):
        @override
        def __setitem__(self, key: str, value: object) -> None:
            raise RuntimeError(f"guarded context written: {key}")

        @override
        def __delitem__(self, key: str) -> None:
            raise RuntimeError(f"guarded context cleared: {key}")

    class TitleOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    marker = object()
    context: dict[str, object] = GuardedContext() if guarded else {}
    dict[str, object].__setitem__(context, "request", HttpRequest())
    dict[str, object].__setitem__(context, "consumer_marker", marker)
    TitleInput = _keyword_constructor(OrderArgumentsFactory(TitleOrder).arguments)
    order_input = [TitleInput(title=Ordering.ASC)]
    info = SimpleNamespace(context=context)

    ordered = TitleOrder.apply_sync(order_input, Book.objects.all(), info)
    ordered_async = asyncio.run(TitleOrder.apply_async(order_input, Book.objects.all(), info))

    assert ordered.ordered is True
    assert ordered_async.ordered is True
    assert TitleOrder._input_has_active_terms(order_input) is True
    assert set(context) == {"request", "consumer_marker"}
    assert context["consumer_marker"] is marker


def test_validate_normalized_terms_rejects_hostile_container_and_string_subclasses() -> None:
    """The data and each term are pinned by EXACT type, so no consumer hook can fire.

    A ``list`` subclass would run its ``__iter__`` in the validation loop and a
    ``tuple`` subclass its ``__len__`` / ``__getitem__`` while the term is read. Each
    is rejected before the member it would hook is touched, as the promised
    ``ConfigurationError`` naming ``_normalize_input``.
    """
    fired: list[str] = []

    class HostileList(list[object]):
        @override
        def __iter__(self) -> Iterator[object]:
            fired.append("list.__iter__")
            return super().__iter__()

    class HostileTuple(tuple[object, ...]):
        @override
        def __len__(self) -> int:
            fired.append("tuple.__len__")
            return super().__len__()

        @overload
        def __getitem__(self, index: SupportsIndex) -> object: ...
        @overload
        def __getitem__(self, index: slice) -> tuple[object, ...]: ...
        @override
        def __getitem__(self, index: SupportsIndex | slice) -> object:
            fired.append("tuple.__getitem__")
            return super().__getitem__(index)

    class HostileOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    with pytest.raises(
        ConfigurationError,
        match=r"HostileOrder\._normalize_input returned invalid data",
    ):
        _validate_normalized_terms(HostileOrder, HostileList([("title", Ordering.ASC)]))
    with pytest.raises(
        ConfigurationError,
        match=r"HostileOrder\._normalize_input returned invalid term",
    ):
        _validate_normalized_terms(HostileOrder, [HostileTuple(("title", Ordering.ASC))])
    assert fired == []

    # Exact builtins with the same content are accepted and returned as given.
    good = [("title", Ordering.ASC), ("shelf__code", None)]
    assert _validate_normalized_terms(HostileOrder, good) is good


def test_input_has_active_terms_public_apply_override_independence() -> None:
    """Overriding public apply without delegating leaves the helper an independent post-success query."""

    class CustomApplyOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        @override
        def apply_sync(
            cls,
            input_value: object,
            queryset: QuerySet[_M],
            info: object,
            **kwargs: object,
        ) -> QuerySet[_M]:
            return queryset.filter(pk__gt=0)

        @classmethod
        @override
        async def apply_async(
            cls,
            input_value: object,
            queryset: QuerySet[_M],
            info: object,
            **kwargs: object,
        ) -> QuerySet[_M]:
            return queryset.filter(pk__gt=0)

    factory = OrderArgumentsFactory(CustomApplyOrder)
    BookInput = _keyword_constructor(factory.arguments)
    active_input = [BookInput(title=Ordering.ASC)]
    empty_input = [BookInput(title=None)]

    # Proves helper is not routed through public apply and remains an independent query
    assert CustomApplyOrder._input_has_active_terms(active_input) is True
    assert CustomApplyOrder._input_has_active_terms(empty_input) is False
    assert CustomApplyOrder._input_has_active_terms(None) is False


def test_orderset_normalize_input_validation_contract() -> None:
    """_validate_normalized_terms enforces the declared return contract at the pipeline boundary."""

    class NonListOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        @override
        # basedpyright: deliberately a dict, the invalid data the boundary refuses
        def _normalize_input(cls, input_value: object) -> dict[str, Ordering]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return {"title": Ordering.ASC}

    with pytest.raises(
        ConfigurationError,
        match=r"NonListOrder\._normalize_input returned invalid data",
    ):
        NonListOrder._input_has_active_terms([{"title": "ASC"}])

    class NonTupleTermOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

        @classmethod
        @override
        # basedpyright: deliberately list terms, the invalid term shape the boundary refuses
        def _normalize_input(cls, input_value: object) -> list[list[str | Ordering]]:  # pyright: ignore[reportIncompatibleMethodOverride]
            return [["title", Ordering.ASC]]

    with pytest.raises(
        ConfigurationError,
        match=r"NonTupleTermOrder\._normalize_input returned invalid term",
    ):
        NonTupleTermOrder._input_has_active_terms([{"title": "ASC"}])


# ---------------------------------------------------------------------------
# Related-row visibility: which relations a term reads through a hiding type
# ---------------------------------------------------------------------------


def _hiding_type(
    model: type[Model],
    type_name: str,
    *,
    primary: bool = True,
    **hidden: object,
) -> type[DjangoType]:
    """Register a type for ``model`` whose ``get_queryset`` hides the rows matching ``hidden``."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset.exclude(**hidden)

    return type(
        type_name,
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": model, "fields": "__all__", "primary": primary}),
            "get_queryset": classmethod(get_queryset),
        },
    )


def _plain_type(model: type[Model], name: str) -> type[DjangoType]:
    """Register a type for ``model`` that keeps the identity ``get_queryset``."""
    return type(
        name,
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": "__all__"})},
    )


@pytest.mark.usefixtures("isolate_global_registry")
def test_scoped_hops_read_only_relations_whose_type_hides_rows() -> None:
    """A relation is scoped by a registered type with its own hook; nothing else is.

    Each hop carries the relation its joined path ends on, the field whose link its
    visibility test correlates on.
    """
    shelf_type = _hiding_type(Shelf, "HidingShelfType", topic="secret")
    _plain_type(Branch, "PlainBranchType")

    class BookPaths(OrderSet):
        class Meta:
            model = Book
            fields = ["title"]

    shelf = Book._meta.get_field("shelf")
    assert BookPaths._scoped_hops(Book, "shelf__topic") == (("shelf", shelf_type, shelf),)
    assert BookPaths._scoped_hops(Book, "shelf__branch__name") == (("shelf", shelf_type, shelf),)
    assert BookPaths._scoped_hops(Book, "genres__name") == ()
    assert BookPaths._scoped_hops(Book, "title") == ()


@pytest.mark.usefixtures("isolate_global_registry")
def test_scoped_hops_read_every_hop_of_an_undeclared_to_many_path() -> None:
    """Each relation segment is one hop, joined by the path that reaches it."""
    book_type = _hiding_type(Book, "HidingBookType", circulation_status="repair")
    shelf_type = _hiding_type(Shelf, "HidingShelfType", topic="secret")

    class GenrePaths(OrderSet):
        class Meta:
            model = Genre
            fields = ["name"]

    assert GenrePaths._scoped_hops(Genre, "books__shelf__topic") == (
        ("books", book_type, Genre._meta.get_field("books")),
        ("books__shelf", shelf_type, Book._meta.get_field("shelf")),
    )


@pytest.mark.usefixtures("isolate_global_registry")
def test_scoped_hops_read_a_pk_segment_on_a_relation_keyed_model_as_that_relation() -> None:
    """``pk`` on ``PatronProfile`` (keyed by ``patron``) is the relation, named by its field."""
    patron_type = _hiding_type(Patron, "HidingPatronType", name="secret")

    class ProfilePaths(OrderSet):
        class Meta:
            model = PatronProfile
            fields = ["postal_code"]

    assert ProfilePaths._scoped_hops(PatronProfile, "pk") == (
        ("patron", patron_type, PatronProfile._meta.get_field("patron")),
    )


@pytest.mark.usefixtures("isolate_global_registry")
def test_scoped_hops_read_a_declared_hop_through_its_target_sets_bound_type() -> None:
    """A ``RelatedOrder`` hop answers for the type its target set is bound to, not the primary."""
    primary = _hiding_type(Shelf, "PrimaryShelfType", topic="secret")
    secondary = _hiding_type(Shelf, "SecondaryShelfType", primary=False, topic="private")

    class BoundShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic"]

    BoundShelfOrder._owner_definition = secondary.__django_strawberry_definition__

    class DeclaredBookOrder(OrderSet):
        shelf = RelatedOrder(BoundShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class UndeclaredBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "shelf__topic"]

    shelf = Book._meta.get_field("shelf")
    assert DeclaredBookOrder._scoped_hops(Book, "shelf__topic") == (("shelf", secondary, shelf),)
    assert UndeclaredBookOrder._scoped_hops(Book, "shelf__topic") == (("shelf", primary, shelf),)


@pytest.mark.usefixtures("isolate_global_registry")
def test_scoped_hops_read_the_intermediate_model_of_a_multi_relation_declaration() -> None:
    """``RelatedOrder(field_name="shelf__branch")`` passes through the shelf's type too."""
    shelf_type = _hiding_type(Shelf, "HidingShelfType", topic="secret")
    branch_type = _hiding_type(Branch, "HidingBranchType", city="restricted")

    class UnboundBranchOrder(OrderSet):
        class Meta:
            model = Branch
            fields = ["city"]

    class ThroughShelfOrder(OrderSet):
        home = RelatedOrder(UnboundBranchOrder, field_name="shelf__branch")

        class Meta:
            model = Book
            fields = ["title"]

    assert ThroughShelfOrder._scoped_hops(Book, "shelf__branch__city") == (
        ("shelf", shelf_type, Book._meta.get_field("shelf")),
        ("shelf__branch", branch_type, Shelf._meta.get_field("branch")),
    )


@pytest.mark.usefixtures("isolate_global_registry")
def test_scoped_hops_reentering_the_sets_model_read_the_type_the_set_is_bound_to() -> None:
    """A path back into the set's own model reads its bound type, not the model's primary."""
    _hiding_type(Shelf, "PrimaryShelfType", topic="secret")
    secondary = _hiding_type(Shelf, "SecondaryShelfType", primary=False, topic="private")

    class ReentrantShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["topic", "books__shelf__topic"]

    ReentrantShelfOrder._owner_definition = secondary.__django_strawberry_definition__

    assert ReentrantShelfOrder._scoped_hops(Shelf, "books__shelf__topic") == (
        ("books__shelf", secondary, Book._meta.get_field("shelf")),
    )


@pytest.mark.django_db(transaction=True)
def test_orders_over_a_visible_reverse_generic_relation_order_by_the_one_holder() -> None:
    """The reverse ``GenericRel`` orders as the single-valued relation it is.

    The relation orders by the holder's key and a path through it by that one holder's
    column, as Django's own ``order_by("holder")`` does, with no aggregate; the stray
    tag, which belongs to no holder, orders as Django orders a missing holder.
    """

    class RpGenericTagOrder(OrderSet):
        class Meta:
            model = RpGenericTag
            fields = ["holder", "holder__title"]

    with generic_fixture_rows(connection):
        rows = RpGenericTag.objects.all()
        by_holder = RpGenericTagOrder.apply_sync({"holder": Ordering.DESC}, rows, _make_info())
        by_title = RpGenericTagOrder.apply_sync(
            {"holder_title": Ordering.ASC},
            rows,
            _make_info(),
        )
        titled = list(by_title.values_list("name", flat=True))
        assert list(by_holder.values_list("name", flat=True)) == list(
            rows.order_by("-holder").values_list("name", flat=True),
        )
        assert titled == list(rows.order_by("holder__title").values_list("name", flat=True))
        assert titled.index("t2") < titled.index("t1")


# ---------------------------------------------------------------------------
# Related-row visibility: a declared hop's target must be one its test can scope by
# ---------------------------------------------------------------------------


def _set_named(
    name: str,
    model: type[Model],
    fields: list[str],
    **related: RelatedOrder,
) -> type[OrderSet]:
    """Declare an ``OrderSet`` named ``name`` in this module, so its qualified name is ``name``."""
    return type(
        name,
        (OrderSet,),
        {
            **related,
            "Meta": type("Meta", (), {"model": model, "fields": fields}),
            "__module__": __name__,
        },
    )


_DESK_PROFILE_REFUSAL = (
    "OrderSet BookOrder: RelatedOrder 'shelf' has field_name 'shelf', which reaches Shelf, but "
    "its target OrderSet DeskOrder is bound to DeskType, whose model is DeskProfile. A "
    "RelatedOrder's target OrderSet must be bound to a type of Shelf, a proxy of it, or a "
    "multi-table-inheritance parent or child of it keyed by the same column."
)


@pytest.mark.usefixtures("isolate_global_registry")
def test_apply_refuses_a_declared_hop_whose_unwired_owner_names_an_unscopable_target() -> None:
    """An owner no finalize audits refuses its mismatched target when a term crosses it."""
    desk_type = _plain_type(DeskProfile, "DeskType")
    desk_order = _set_named("DeskOrder", DeskProfile, ["code"])
    desk_order._owner_definition = desk_type.__django_strawberry_definition__
    book_order = _set_named(
        "BookOrder",
        Book,
        ["title"],
        shelf=RelatedOrder(desk_order, field_name="shelf"),
    )

    with pytest.raises(ConfigurationError) as exc_info:
        book_order.apply_sync({"shelf": {"code": Ordering.ASC}}, Book.objects.all(), _make_info())
    assert str(exc_info.value) == _DESK_PROFILE_REFUSAL


class _OsUnmanagedModel(models.Model):
    """The abstract base whose ``Meta`` the multi-table child below subclasses.

    No fakeshop model has a foreign key onto a column only a multi-table child
    declares, so these models stand in for it; ``managed = False`` and the tests
    create the tables (``relation_fixture_tables``).
    """

    class Meta:
        abstract = True
        app_label = "products"
        managed = False


class _OsDesk(_OsUnmanagedModel):
    """The multi-table parent: it lacks ``kiosk_code``."""

    name: _Text = models.TextField()


class _OsKioskDesk(_OsDesk):
    """A multi-table child declaring its own unique ``kiosk_code``."""

    kiosk_code: _Text = models.TextField(unique=True)

    class Meta(_OsUnmanagedModel.Meta):
        pass


class _OsLamp(_OsUnmanagedModel):
    """A lamp keyed to kiosk desks by the child's ``kiosk_code``: required, nullable, unconstrained."""

    title: _Text = models.TextField()
    # DO_NOTHING, not CASCADE: outside the tests that create it the table does not
    # exist, so a cascade would make a delete of the target query a missing table.
    kiosk: _FK[_OsKioskDesk] = models.ForeignKey(
        _OsKioskDesk,
        on_delete=models.DO_NOTHING,
        to_field="kiosk_code",
        related_name="+",
    )
    spare_kiosk: _NullFK[_OsKioskDesk] = models.ForeignKey(
        _OsKioskDesk,
        on_delete=models.DO_NOTHING,
        to_field="kiosk_code",
        null=True,
        related_name="+",
    )
    # No constraint: the stored code may name no kiosk desk at all.
    loose_kiosk: _FK[_OsKioskDesk] = models.ForeignKey(
        _OsKioskDesk,
        on_delete=models.DO_NOTHING,
        to_field="kiosk_code",
        db_constraint=False,
        related_name="+",
    )


_STAFF_INFO = _make_info()
_ANONYMOUS_INFO = _make_info(user_is_anonymous=True)


def _override_lamp_order(desk_order: type[OrderSet], key: str) -> type[OrderSet]:
    """A lamp set whose ``get_flat_orders`` override orders by the ``key`` relation itself."""

    class OverrideLampOrder(OrderSet):
        kiosk = RelatedOrder(desk_order, field_name="kiosk")
        loose_kiosk = RelatedOrder(desk_order, field_name="loose_kiosk")

        class Meta:
            model = _OsLamp
            fields = ["title"]

        @classmethod
        @override
        def get_flat_orders(
            cls,
            order_data: list[tuple[str, Ordering | None]],
            prefix: str = "",
        ) -> list[tuple[str, Ordering | None]]:
            return [(key, Ordering.ASC_NULLS_LAST), ("title", Ordering.ASC)]

    return OverrideLampOrder


def _lamp_orders() -> dict[str, tuple[type[OrderSet], object]]:
    """The lamp sets ordering through a desk set bound to a parent type hiding ``"hidden"``.

    The type's rows hide the desk named ``"hidden"`` from every ``info`` but
    ``_STAFF_INFO``. Each set crosses ``kiosk``, ``spare_kiosk`` or
    ``loose_kiosk``, whose key is the child's ``kiosk_code``, a column the
    parent's rows do not carry. Every order ends on ``title``, so lamps whose
    value reads as missing keep one order.
    """

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset if info is _STAFF_INFO else queryset.exclude(name="hidden")

    desk_type = type(
        "HidingDeskType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": _OsDesk, "fields": ("id", "name")}),
            "get_queryset": classmethod(get_queryset),
        },
    )
    desk_order = _set_named("DeskOrder", _OsDesk, ["name"])
    desk_order._owner_definition = desk_type.__django_strawberry_definition__
    column_order = _set_named(
        "LampOrder",
        _OsLamp,
        [
            "kiosk",
            "spare_kiosk",
            "loose_kiosk",
            "title",
        ],
        kiosk_rel=RelatedOrder(desk_order, field_name="kiosk"),
        spare_rel=RelatedOrder(desk_order, field_name="spare_kiosk"),
        loose_rel=RelatedOrder(desk_order, field_name="loose_kiosk"),
    )
    by_title = {"title": Ordering.ASC}
    return {
        "column-term-ending-on-the-relation": (
            column_order,
            [{"kiosk": Ordering.ASC_NULLS_LAST}, by_title],
        ),
        "override-ending-on-the-relation": (_override_lamp_order(desk_order, "kiosk"), [by_title]),
        "nullable-column-term-ending-on-the-relation": (
            column_order,
            [{"spare_kiosk": Ordering.ASC_NULLS_LAST}, by_title],
        ),
        "unconstrained-column-term-ending-on-the-relation": (
            column_order,
            [{"loose_kiosk": Ordering.ASC_NULLS_LAST}, by_title],
        ),
        "unconstrained-override-ending-on-the-relation": (
            _override_lamp_order(desk_order, "loose_kiosk"),
            [by_title],
        ),
        "column-under-the-relation": (
            column_order,
            [{"kiosk_rel": {"name": Ordering.ASC_NULLS_LAST}}, by_title],
        ),
        "unconstrained-override-under-the-relation": (
            _override_lamp_order(desk_order, "loose_kiosk__kiosk_code"),
            [by_title],
        ),
    }


@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("shape", "staff", "anonymous"),
    [
        ("column-term-ending-on-the-relation", "L2 L1 L3 L4 L5", "L2 L3 L4 L5 L1"),
        ("override-ending-on-the-relation", "L2 L1 L3 L4 L5", "L2 L3 L4 L5 L1"),
        ("nullable-column-term-ending-on-the-relation", "L2 L1 L3 L4 L5", "L2 L3 L1 L4 L5"),
        ("unconstrained-column-term-ending-on-the-relation", "L2 L1 L3 L4 L5", "L2 L3 L4 L1 L5"),
        ("unconstrained-override-ending-on-the-relation", "L2 L1 L3 L4 L5", "L2 L3 L4 L1 L5"),
        ("column-under-the-relation", "L1 L3 L4 L5 L2", "L3 L4 L5 L2 L1"),
        ("unconstrained-override-under-the-relation", "L2 L1 L3 L4 L5", "L2 L3 L4 L1 L5"),
    ],
)
def test_a_hop_scoped_by_an_ancestor_lacking_the_to_field_hides_through_the_related_row(
    shape: str,
    staff: str,
    anonymous: str,
) -> None:
    """A parent's rows answer for the child row a ``to_field`` key names, and drop no lamp.

    A term ending on ``kiosk`` reads the lamp's own ``kiosk_code`` carrier; the
    parent's rows carry no ``kiosk_code`` to correlate it with, so the test keeps
    the parent rows whose key is that of the kiosk desk the carrier names, read
    inside its own subquery: the outer query joins nothing. The hidden desk's
    lamp reads as a lamp with no desk for the anonymous actor; a lamp whose
    nullable key is empty, and one whose unconstrained key names no desk
    (``L5``), stay listed and read as one for everyone. A term under the relation
    takes the same test: ``loose_kiosk__kiosk_code`` reads the trimmed carrier, so
    ``L5`` stays and reads as missing, and ``kiosk__name`` reads ``name`` through
    the join its value takes. One statement per apply.
    """
    lamp_order, order_input = _lamp_orders()[shape]
    with relation_fixture_tables(connection, (_OsDesk, _OsKioskDesk, _OsLamp)):
        kiosks = {
            code: _OsKioskDesk.objects.create(name=name, kiosk_code=code)
            for name, code in (("hidden", "b"), ("z", "a"), ("y", "c"))
        }
        for title, code, spare, loose in (
            (
                "L1",
                "b",
                "b",
                "b",
            ),
            (
                "L2",
                "a",
                "a",
                "a",
            ),
            (
                "L3",
                "c",
                "c",
                "c",
            ),
            (
                "L4",
                "c",
                None,
                "c",
            ),
            (
                "L5",
                "c",
                None,
                "zz",
            ),
        ):
            _ = _OsLamp.objects.create(
                title=title,
                kiosk=kiosks[code],
                spare_kiosk=None if spare is None else kiosks[spare],
                loose_kiosk_id=loose,
            )
        for info, expected in ((_STAFF_INFO, staff), (_ANONYMOUS_INFO, anonymous)):
            with CaptureQueriesContext(connection) as captured:
                ordered = lamp_order.apply_sync(order_input, _OsLamp.objects.all(), info)
                titles = list(ordered.values_list("title", flat=True))
            assert (titles, len(captured.captured_queries)) == (expected.split(), 1)


class _OsTier(_OsUnmanagedModel):
    """The root of a three-level multi-table-inheritance line: it lacks ``code``."""

    name: _Text = models.TextField()


class _OsTierMidMeta(_OsUnmanagedModel.Meta):
    """The ``Meta`` of ``_OsTierMid``, kept here so its child's ``Meta`` can subclass it.

    Django pops a concrete model's ``Meta``, so the grandchild cannot reach it
    through ``_OsTierMid``.
    """


class _OsTierMid(_OsTier):
    """The intermediate parent declaring the unique ``code`` its child inherits."""

    code: _Text = models.TextField(unique=True)

    Meta = _OsTierMidMeta


class _OsTierLeaf(_OsTierMid):
    """The grandchild a lamp's ``ForeignObject`` reaches through the inherited ``code``."""

    class Meta(_OsTierMidMeta):
        pass


class _OsTierLamp(_OsUnmanagedModel):
    """A lamp keyed to a leaf by ``code``, a column the intermediate parent declares.

    A ``ForeignObject``: Django refuses a ``ForeignKey`` whose ``to_field`` the
    target only inherits, so no constraint holds the stored code either.
    """

    title: _Text = models.TextField()
    leaf_code: _Text = models.TextField()
    leaf: models.ForeignObject[_OsTierLeaf, _OsTierLeaf] = models.ForeignObject(
        _OsTierLeaf,
        on_delete=models.DO_NOTHING,
        from_fields=["leaf_code"],
        to_fields=["code"],
        related_name="+",
    )


def _tier_lamp_orders() -> dict[str, type[OrderSet]]:
    """The tier-lamp sets ordering by ``leaf`` through a set bound to a root type hiding ``"hidden"``."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset if info is _STAFF_INFO else queryset.exclude(name="hidden")

    tier_type = type(
        "HidingTierType",
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": _OsTier, "fields": ("id", "name")}),
            "get_queryset": classmethod(get_queryset),
        },
    )
    tier_order = _set_named("TierOrder", _OsTier, ["name"])
    tier_order._owner_definition = tier_type.__django_strawberry_definition__

    class OverrideTierLampOrder(OrderSet):
        leaf = RelatedOrder(tier_order, field_name="leaf")

        class Meta:
            model = _OsTierLamp
            fields = ["title"]

        @classmethod
        @override
        def get_flat_orders(
            cls,
            order_data: list[tuple[str, Ordering | None]],
            prefix: str = "",
        ) -> list[tuple[str, Ordering | None]]:
            return [("leaf", Ordering.ASC_NULLS_LAST), ("title", Ordering.ASC)]

    return {
        "column-term-ending-on-the-relation": _set_named(
            "TierLampOrder",
            _OsTierLamp,
            ["leaf", "title"],
            leaf_rel=RelatedOrder(tier_order, field_name="leaf"),
        ),
        "override-ending-on-the-relation": OverrideTierLampOrder,
    }


@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "shape",
    ["column-term-ending-on-the-relation", "override-ending-on-the-relation"],
)
def test_a_hop_through_an_inherited_to_field_reads_only_rows_of_the_related_model(
    shape: str,
) -> None:
    """A code only an intermediate parent's row holds names no related row, so it reads as missing.

    ``_OsTierLamp.leaf`` reaches ``_OsTierLeaf`` by ``code``, which ``_OsTierMid``
    declares; the root type's rows carry no ``code``, so the test matches the
    related row the carriers name. It reads that row from the related model
    (``_OsTierLeaf``), not the model declaring the column: ``L2``'s code belongs
    to a ``_OsTierMid`` row no leaf extends, and orders as a lamp with no leaf,
    as ``L3``'s unknown code does. ``L4``'s leaf is hidden from the anonymous
    actor. One statement per apply.
    """
    lamp_order = _tier_lamp_orders()[shape]
    tables = (
        _OsTier,
        _OsTierMid,
        _OsTierLeaf,
        _OsTierLamp,
    )
    with relation_fixture_tables(connection, tables):
        _ = _OsTierLeaf.objects.create(name="g", code="m")
        _ = _OsTierLeaf.objects.create(name="hidden", code="b")
        _ = _OsTierMid.objects.create(name="mid-only", code="a")
        for title, code in (
            ("L1", "m"),
            ("L2", "a"),
            ("L3", "zz"),
            ("L4", "b"),
        ):
            _ = _OsTierLamp.objects.create(title=title, leaf_code=code)
        for info, expected in (
            (
                _STAFF_INFO,
                [
                    "L4",
                    "L1",
                    "L2",
                    "L3",
                ],
            ),
            (
                _ANONYMOUS_INFO,
                [
                    "L1",
                    "L2",
                    "L3",
                    "L4",
                ],
            ),
        ):
            with CaptureQueriesContext(connection) as captured:
                ordered = lamp_order.apply_sync(
                    [{"title": Ordering.ASC}]
                    if shape == "override-ending-on-the-relation"
                    else [{"leaf": Ordering.ASC_NULLS_LAST}, {"title": Ordering.ASC}],
                    _OsTierLamp.objects.all(),
                    info,
                )
                titles = list(ordered.values_list("title", flat=True))
            assert (titles, len(captured.captured_queries)) == (expected, 1)


class _OsShelf(_OsUnmanagedModel):
    """A shelf a chain desk names by its unique ``code``."""

    name: _Text = models.TextField()
    code: _Text = models.TextField(unique=True)


class _OsSlot(_OsUnmanagedModel):
    """A slot a chain desk holds one-to-one."""

    # Typed here: django-stubs types ``Model.pk`` as ``Any``. ``None`` until the row is saved.
    pk: int | None

    name: _Text = models.TextField()


class _OsChainDesk(_OsUnmanagedModel):
    """A desk keyed by ``kiosk_code`` that names its shelf by ``code`` and holds one slot."""

    name: _Text = models.TextField()
    kiosk_code: _Text = models.TextField(unique=True)
    # No constraint: the stored code may name no shelf at all.
    shelf: _FK[_OsShelf] = models.ForeignKey(
        _OsShelf,
        on_delete=models.DO_NOTHING,
        to_field="code",
        db_constraint=False,
        related_name="+",
    )
    slot: models.OneToOneField[_OsSlot | Combinable, _OsSlot] = models.OneToOneField(
        _OsSlot,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="+",
    )


class _OsChainLamp(_OsUnmanagedModel):
    """A lamp keyed to a chain desk by its ``kiosk_code`` and, separately, by its ``slot``.

    ``loose__shelf__code`` crosses a second ``to_field`` hop; ``viaslot__slot__id``
    is trimmed by Django across both joins to the lamp's own ``viaslot`` column.
    """

    title: _Text = models.TextField()
    loose: _FK[_OsChainDesk] = models.ForeignKey(
        _OsChainDesk,
        on_delete=models.DO_NOTHING,
        to_field="kiosk_code",
        db_constraint=False,
        related_name="+",
    )
    viaslot: _FK[_OsChainDesk] = models.ForeignKey(
        _OsChainDesk,
        on_delete=models.DO_NOTHING,
        to_field="slot",
        db_constraint=False,
        related_name="+",
    )


def _staff_sees_all_type(model: type[Model], name: str) -> type[DjangoType]:
    """Register a type for ``model`` hiding the row named ``"hidden"`` from all but ``_STAFF_INFO``."""

    def get_queryset(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        info: object,
        **_kwargs: object,
    ) -> QuerySet[Model]:
        return queryset if info is _STAFF_INFO else queryset.exclude(name="hidden")

    return type(
        name,
        (DjangoType,),
        {
            "Meta": type("Meta", (), {"model": model, "fields": "__all__"}),
            "get_queryset": classmethod(get_queryset),
        },
    )


def _override_order(lamp_model: type[Model], path: str) -> type[OrderSet]:
    """A ``lamp_model`` set whose ``get_flat_orders`` override orders by ``path``, then ``title``."""

    class OverrideOrder(OrderSet):
        class Meta:
            model = lamp_model
            fields = ["title"]

        @classmethod
        @override
        def get_flat_orders(
            cls,
            order_data: list[tuple[str, Ordering | None]],
            prefix: str = "",
        ) -> list[tuple[str, Ordering | None]]:
            return [(path, Ordering.ASC_NULLS_LAST), ("title", Ordering.ASC)]

    return OverrideOrder


def _kiosk_lamp_orders() -> dict[str, tuple[type[OrderSet], object]]:
    """The lamp sets ordering by ``loose_kiosk__kiosk_code`` through a hiding kiosk-desk type.

    The type is bound to ``_OsKioskDesk``, whose rows carry ``kiosk_code``, in
    each spelling a term can take: a declared ``RelatedOrder`` branch, a
    ``Meta.fields`` path, and a ``get_flat_orders`` override.
    """
    kiosk_type = _staff_sees_all_type(_OsKioskDesk, "HidingKioskDeskType")
    kiosk_order = _set_named("KioskDeskOrder", _OsKioskDesk, ["kiosk_code"])
    kiosk_order._owner_definition = kiosk_type.__django_strawberry_definition__
    nested = _set_named(
        "NestedLampOrder",
        _OsLamp,
        ["title"],
        loose_rel=RelatedOrder(kiosk_order, field_name="loose_kiosk"),
    )
    path = _set_named("PathLampOrder", _OsLamp, ["title", "loose_kiosk__kiosk_code"])
    by_title = {"title": Ordering.ASC}
    return {
        "related-order-branch": (
            nested,
            [{"loose_rel": {"kiosk_code": Ordering.ASC_NULLS_LAST}}, by_title],
        ),
        "meta-fields-path": (
            path,
            [{"loose_kiosk_kiosk_code": Ordering.ASC_NULLS_LAST}, by_title],
        ),
        "get-flat-orders-override": (
            _override_order(_OsLamp, "loose_kiosk__kiosk_code"),
            [by_title],
        ),
    }


@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "spelling",
    ["related-order-branch", "meta-fields-path", "get-flat-orders-override"],
)
@pytest.mark.parametrize(
    ("info", "expected"),
    [(_STAFF_INFO, "L2 L1 L3 L4 L5"), (_ANONYMOUS_INFO, "L2 L3 L4 L1 L5")],
    ids=["staff", "anonymous"],
)
def test_a_term_past_a_to_field_hop_keeps_a_lamp_naming_no_desk_and_reads_it_as_missing(
    spelling: str,
    info: object,
    expected: str,
) -> None:
    """``loose_kiosk__kiosk_code`` drops no lamp the plain term keeps, in every spelling.

    Django trims the value to the lamp's own ``loose_kiosk`` carrier, so the plain
    term joins nothing and keeps ``L5``, whose unconstrained code names no desk.
    The hop's test correlates the kiosk rows' ``kiosk_code`` to that carrier too,
    so ``L5`` stays listed and reads as a lamp with no desk for every actor; the
    hidden desk's ``L1`` reads as one for the anonymous actor. One statement.
    """
    lamp_order, order_input = _kiosk_lamp_orders()[spelling]
    with relation_fixture_tables(connection, (_OsDesk, _OsKioskDesk, _OsLamp)):
        kiosks = {
            code: _OsKioskDesk.objects.create(name=name, kiosk_code=code)
            for name, code in (("hidden", "b"), ("z", "a"), ("y", "c"))
        }
        for title, loose in (
            ("L1", "b"),
            ("L2", "a"),
            ("L3", "c"),
            ("L4", "c"),
            ("L5", "zz"),
        ):
            _ = _OsLamp.objects.create(title=title, kiosk=kiosks["a"], loose_kiosk_id=loose)
        with CaptureQueriesContext(connection) as captured:
            ordered = lamp_order.apply_sync(order_input, _OsLamp.objects.all(), info)
            titles = list(ordered.values_list("title", flat=True))
    assert (titles, len(captured.captured_queries)) == (expected.split(), 1)


@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("path", "staff", "anonymous"),
    [
        ("loose__shelf__code", "L1 L2 L5 L3", "L2 L5 L1 L3"),
        ("viaslot__slot__id", "L1 L2 L5 L3 L4", "L2 L5 L1 L3 L4"),
    ],
    ids=["second-to-field-hop", "two-join-trim"],
)
def test_every_hop_over_a_non_pk_link_correlates_on_its_link_columns(
    path: str,
    staff: str,
    anonymous: str,
) -> None:
    """A hop keyed by a non-pk link is read by its carriers wherever the path continues past it.

    Desks, shelves and slots each hide the row named ``"hidden"`` from the
    anonymous actor. ``loose__shelf__code`` reads the desk's ``shelf`` carrier
    through the ``loose`` join (``L4``'s code names no desk, so the plain term's
    join drops it too); ``L3``'s desk names no shelf, so the ``shelf`` hop's test
    correlated on that carrier keeps ``L3`` and reads it as missing.
    ``viaslot__slot__id`` is the lamp's own ``viaslot`` column, so the plain term
    keeps every lamp; the ``viaslot`` hop's test correlates the desks' ``slot``
    to it, so ``L4``, naming no desk, stays and reads as missing, as does ``L3``,
    whose desk names no slot. One statement per apply.
    """
    for model in (_OsChainDesk, _OsShelf, _OsSlot):
        _ = _staff_sees_all_type(model, f"Hiding{model.__name__}Type")
    lamp_order = _override_order(_OsChainLamp, path)
    with relation_fixture_tables(
        connection,
        (
            _OsShelf,
            _OsSlot,
            _OsChainDesk,
            _OsChainLamp,
        ),
    ):
        hidden_shelf = _OsShelf.objects.create(name="hidden", code="s1")
        _ = _OsShelf.objects.create(name="a", code="s2")
        hidden_slot = _OsSlot.objects.create(name="hidden")
        slot = _OsSlot.objects.create(name="a")
        _ = _OsChainDesk.objects.create(
            name="hidden",
            kiosk_code="k1",
            shelf=hidden_shelf,
            slot=hidden_slot,
        )
        _ = _OsChainDesk.objects.create(name="b", kiosk_code="k2", shelf_id="s2", slot=slot)
        _ = _OsChainDesk.objects.create(name="c", kiosk_code="k3", shelf_id="zz", slot_id=999)
        for title, loose, viaslot in (
            ("L1", "k1", hidden_slot.pk),
            ("L2", "k2", slot.pk),
            ("L3", "k3", 999),
            ("L4", "zz", 777),
            ("L5", "k2", slot.pk),
        ):
            _ = _OsChainLamp.objects.create(title=title, loose_id=loose, viaslot_id=viaslot)
        for info, expected in ((_STAFF_INFO, staff), (_ANONYMOUS_INFO, anonymous)):
            with CaptureQueriesContext(connection) as captured:
                ordered = lamp_order.apply_sync(
                    [{"title": Ordering.ASC}],
                    _OsChainLamp.objects.all(),
                    info,
                )
                titles = list(ordered.values_list("title", flat=True))
            assert (titles, len(captured.captured_queries)) == (expected.split(), 1)


_ManagerShape: TypeAlias = Callable[[type[Model], str, str], "AbstractContextManager[type]"]


@pytest.mark.django_db
@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.parametrize("shape", ["from_queryset", "hand_written", "polymorphic"])
@pytest.mark.parametrize("hop", ["declared", "undeclared"])
def test_order_hop_hook_reads_every_target_row_in_the_default_manager_class(
    *,
    shape: str,
    hop: str,
    default_manager_shape: _ManagerShape,
) -> None:
    """A related ordering runs the target hook over every row, in the class its manager returns.

    ``Shelf``'s default manager hides ``zz-hidden``. A declared ``RelatedOrder``
    hop and an undeclared ``shelf__code`` term into the hooked ``Shelf`` type
    hand the hook the manager's project class over every shelf, so the book on
    the hidden shelf sorts by its code, first descending, never as a missing one.
    """
    branch = Branch.objects.create(name="Shaped")
    shown = Shelf.objects.create(branch=branch, code="aa-ok")
    hidden = Shelf.objects.create(branch=branch, code="zz-hidden")
    Book.objects.create(title="B-PUB", shelf=shown)
    Book.objects.create(title="B-HID", shelf=hidden)
    seen: list[tuple[type, tuple[str, ...]]] = []

    class ShapedShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Shelf], info: object) -> QuerySet[Shelf]:
            codes = tuple(sorted(queryset.values_list("code", flat=True)))
            seen.append((type(queryset), codes))
            return queryset

    class ShapedShelfOrder(OrderSet):
        class Meta:
            model = Shelf
            fields = ["code"]

    class DeclaredBookOrder(OrderSet):
        shelf = RelatedOrder(ShapedShelfOrder, field_name="shelf")

        class Meta:
            model = Book
            fields = ["title"]

    class UndeclaredBookOrder(OrderSet):
        class Meta:
            model = Book
            fields = ["title", "shelf__code"]

    book_order, terms = (
        (DeclaredBookOrder, [{"shelf": {"code": Ordering.DESC}}])
        if hop == "declared"
        else (UndeclaredBookOrder, [{"shelf_code": Ordering.DESC}])
    )
    assert model_for(ShapedShelfType) is Shelf

    with default_manager_shape(Shelf, shape, "code") as queryset_class:
        rows = book_order.apply_sync(terms, Book.objects.all(), _make_info())

        assert list(rows.values_list("title", flat=True)) == ["B-HID", "B-PUB"]
    assert seen
    assert set(seen) == {(queryset_class, ("aa-ok", "zz-hidden"))}
