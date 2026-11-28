"""A related declaration named like a metaclass attribute survives a base that does not declare it.

A ``RelatedFilter`` or ``RelatedOrder`` may take any attribute name, ``mro`` and
``get_declared_filters`` included, though ``type`` and the set metaclass carry those names
too. Only a class attribute in a base's own MRO shadows an inherited declaration, so a set
listing a base that declares nothing first (``class C(NoDecl, Decl)``) keeps the relation:
it publishes ``mro`` (or ``getDeclaredFilters``) on its filter and order inputs, and a query
filtering or ordering through it answers the related rows.

A lazily spelled relation ``field_name`` (``gettext_lazy("shelves")``, a
``SimpleLazyObject``) names the relation its plain ``str`` spelling names, so the flat leaf
``shelvesCode`` walks its hop and fires the permission gate of the branch declaring it
(``visible_shelves``).
"""

import pytest
import strawberry
from apps.library import models
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy
from graphql import GraphQLError
from graphql_client import JSONObject, SchemaMount, graphql_payload, json_list, json_str
from strategy_schemas import make_django_type

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoSchema,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.orders import OrderSet, RelatedOrder

pytestmark = pytest.mark.usefixtures("private_registry")
_MOUNT = SchemaMount(__name__, "graphql-related-declaration-names/")
urlpatterns = _MOUNT.urlpatterns


def _schema(declared: str) -> tuple[DjangoSchema, type[FilterSet], type[OrderSet]]:
    """A ``Branch`` connection whose filter and order sets inherit ``declared`` from a second base."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class ShelfOrder(OrderSet):
        class Meta:
            model = models.Shelf
            fields = ["code"]

    class BranchNoDeclFilter(FilterSet):
        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    declaring_filter = type(
        "BranchDeclFilter",
        (FilterSet,),
        {
            declared: RelatedFilter(ShelfFilter, field_name="shelves"),
            "Meta": type("Meta", (), {"model": models.Branch, "fields": {"name": ["exact"]}}),
        },
    )

    class BranchFilter(BranchNoDeclFilter, declaring_filter):
        """Lists the base declaring nothing first; its ``Meta`` is that base's."""

    class BranchNoDeclOrder(OrderSet):
        class Meta:
            model = models.Branch
            fields = ["name"]

    declaring_order = type(
        "BranchDeclOrder",
        (OrderSet,),
        {
            "mro": RelatedOrder(ShelfOrder, field_name="shelves"),
            "Meta": type("Meta", (), {"model": models.Branch, "fields": ["name"]}),
        },
    )

    class BranchOrder(BranchNoDeclOrder, declaring_order):
        """Lists the base declaring nothing first; its ``Meta`` is that base's."""

    shelf_type = make_django_type("ShelfNode", models.Shelf, ("code",))
    branch_type = make_django_type(
        "BranchNode",
        models.Branch,
        ("name",),
        meta_extra={"filterset_class": BranchFilter, "orderset_class": BranchOrder},
    )
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"branches": DjangoConnection[branch_type]},
                "branches": DjangoConnectionField(branch_type),
            },
        ),
    )
    finalize_django_types()
    schema = DjangoSchema(query=query, types=[shelf_type], config=strawberry_config())
    return schema, BranchFilter, BranchOrder


def _world() -> None:
    east = models.Branch.objects.create(name="east")
    west = models.Branch.objects.create(name="west")
    models.Branch.objects.create(name="north")
    for code, branch in (("A1", east), ("C1", west)):
        models.Shelf.objects.create(code=code, topic="permanent collection", branch=branch)


def _names(schema: DjangoSchema, arguments: str) -> JSONObject:
    with _MOUNT.serving(schema):
        return graphql_payload(
            f"{{ branches({arguments}) {{ edges {{ node {{ name }} }} }} }}",
            url="/graphql-related-declaration-names/",
        )


def _expected(names: list[str]) -> JSONObject:
    return {"data": {"branches": {"edges": [{"node": {"name": name}} for name in names]}}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("declared", "published"),
    [("mro", "mro"), ("get_declared_filters", "getDeclaredFilters")],
    ids=["mro", "get-declared-filters"],
)
def test_a_filter_relation_named_like_a_metaclass_attribute_filters_through_a_later_base(
    declared: str,
    published: str,
) -> None:
    """``filter: {<name>: {code: {exact: "A1"}}}`` keeps the branch holding shelf ``A1``."""
    _world()
    schema, branch_filter, _ = _schema(declared)
    assert list(branch_filter.related_filters) == [declared]
    assert _names(schema, f'filter: {{ {published}: {{ code: {{ exact: "A1" }} }} }}') == (
        _expected(["east"])
    )


@pytest.mark.django_db
def test_an_order_relation_named_mro_orders_through_a_later_base() -> None:
    """``orderBy: [{mro: {code: DESC_NULLS_LAST}}]`` orders branches by their shelf codes, descending.

    ``north`` holds no shelf, so its code is NULL; ``DESC_NULLS_LAST`` places it last on every
    backend, where a bare ``DESC`` leaves NULL placement to the database.
    """
    _world()
    schema, _, branch_order = _schema("mro")
    assert list(branch_order.related_orders) == ["mro"]
    assert "mro: ShelfOrderInputType" in str(schema)
    assert _names(schema, "orderBy: [{ mro: { code: DESC_NULLS_LAST } }, { name: ASC }]") == (
        _expected(["west", "east", "north"])
    )


def _lazily_named_schema(field_name: object, *, gated: bool) -> DjangoSchema:
    """A ``Branch`` connection with a ``visible_shelves`` branch over ``field_name``.

    ``gated`` adds a ``check_visible_shelves_permission`` refusing everyone.
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        visible_shelves = RelatedFilter(ShelfFilter, field_name=field_name)

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"], "shelves__code": ["exact"]}

        def check_visible_shelves_permission(self, _request: object) -> None:
            if gated:
                raise GraphQLError("visible_shelves gate")

    shelf_type = make_django_type("ShelfNode", models.Shelf, ("code",))
    branch_type = make_django_type(
        "BranchNode",
        models.Branch,
        ("name",),
        meta_extra={"filterset_class": BranchFilter},
    )
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"branches": DjangoConnection[branch_type]},
                "branches": DjangoConnectionField(branch_type),
            },
        ),
    )
    finalize_django_types()
    return DjangoSchema(query=query, types=[shelf_type], config=strawberry_config())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name",
    ["shelves", SimpleLazyObject(lambda: "shelves"), gettext_lazy("shelves")],
    ids=["str", "simple-lazy-object", "gettext-lazy"],
)
def test_a_flat_leaf_through_a_lazily_named_branch_fires_the_branch_gate(
    field_name: object,
) -> None:
    """``filter: {shelvesCode: {exact: "A1"}}`` fires ``check_visible_shelves_permission``."""
    _world()
    schema = _lazily_named_schema(field_name, gated=True)
    payload = _names(schema, 'filter: { shelvesCode: { exact: "A1" } }')
    assert payload["data"] is None
    errors = json_list(payload, "errors")
    assert [json_str(error, "message") for error in errors] == ["visible_shelves gate"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field_name",
    ["shelves", SimpleLazyObject(lambda: "shelves"), gettext_lazy("shelves")],
    ids=["str", "simple-lazy-object", "gettext-lazy"],
)
@pytest.mark.parametrize(
    "predicate",
    ['shelvesCode: { exact: "A1" }', 'visibleShelves: { code: { exact: "A1" } }'],
    ids=["flat", "nested"],
)
def test_a_lazily_named_branch_filters_as_its_plain_spelling(
    field_name: object,
    predicate: str,
) -> None:
    """The flat leaf and the nested branch both keep the branch holding shelf ``A1``."""
    _world()
    schema = _lazily_named_schema(field_name, gated=False)
    assert _names(schema, f"filter: {{ {predicate} }}") == _expected(["east"])
