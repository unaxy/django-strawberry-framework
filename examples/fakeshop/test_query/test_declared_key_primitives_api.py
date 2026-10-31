"""Declared key primitives compare the real column stored by scalar and relation-valued keys.

Ordinary JSON arguments call bound public filter primitives directly, preserving the
original low-level contract rather than introducing generated input or form refusal.
The custom UUID and BigInteger one-to-one keys use the original shared test models.
"""

import copy
import uuid
from collections.abc import Iterator

import pytest
import strawberry
from apps.library import models
from django.db import connection
from django.db.models import Model, QuerySet
from django_filters.filters import Filter
from strategy_schemas import make_django_type
from strawberry.scalars import JSON
from test_raw_filter_forms_api import _post

from django_strawberry_framework import DjangoSchema, finalize_django_types, strawberry_config
from django_strawberry_framework.filters import FilterSet, ListFilter, RangeFilter
from django_strawberry_framework.filters.base import (
    IntegerInFilter,
    RelationPkFilter,
    RelationPkMultipleFilter,
)
from tests._filter_key_models import _BigKeyed, _BigKeyedProfile, _UuidKeyed, _UuidKeyedProfile
from tests._idioms import saved_pk

pytestmark = pytest.mark.usefixtures("private_registry")


def _schema(
    source: type[Model],
    leaf: Filter,
    field_name: str,
    value_attr: str,
    *,
    bound: bool = True,
    node: bool = False,
) -> DjangoSchema:
    declared = copy.deepcopy(leaf)
    declared.field_name = field_name
    selected = type(
        "DeclaredPrimitiveSet",
        (FilterSet,),
        {"leaf": declared, "Meta": type("Meta", (), {"model": source, "fields": ()})},
    )

    def uuid_key(self: _UuidKeyedProfile) -> uuid.UUID:
        return self.owner_id

    output = make_django_type(
        "DeclaredPrimitiveOutput",
        source,
        () if source is _UuidKeyedProfile else (value_attr,),
        node=node,
        namespace_extra={
            "__annotations__": {"key": uuid.UUID},
            "key": strawberry.field(resolver=uuid_key),
        }
        if source is _UuidKeyedProfile
        else None,
    )

    def rows() -> QuerySet[Model]:
        return source._default_manager.order_by(value_attr)

    def apply_values(values: object) -> QuerySet[Model]:
        queryset = rows()
        primitive = selected(data={}, queryset=queryset).filters["leaf"] if bound else declared
        return primitive.filter(queryset, values)

    @strawberry.type
    class Query:
        def _rows(self, values: JSON | None = None) -> QuerySet[Model]:
            return apply_values(values)

        def _uuid_rows(self, values: list[uuid.UUID] | None = None) -> QuerySet[Model]:
            return apply_values(values)

        def _all_rows(self) -> QuerySet[Model]:
            return rows()

        matches: QuerySet[Model] = strawberry.field(
            resolver=_uuid_rows if source is _UuidKeyedProfile else _rows,
            graphql_type=list[output],
        )
        all_rows: QuerySet[Model] = strawberry.field(resolver=_all_rows, graphql_type=list[output])

    finalize_django_types()
    return DjangoSchema(query=Query, config=strawberry_config())


def _answer(
    schema: DjangoSchema,
    values: object,
    selection: str,
    matches: list[str],
    universe: list[str],
    *,
    variable_type: str = "JSON",
) -> None:
    payload = _post(
        schema,
        f"query($values: {variable_type}) {{ "
        f"rows: matches(values: $values) {{ value: {selection} }} "
        f"allRows {{ value: {selection} }} }}",
        {"values": values},
    )
    assert payload == {
        "data": {
            "rows": [{"value": value} for value in matches],
            "allRows": [{"value": value} for value in universe],
        },
    }, payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind",
    [
        "range",
        "list",
        "integer-in",
        "relation-range",
    ],
)
def test_a_declared_integer_key_primitive_never_binds_its_oversized_member(kind: str) -> None:
    """Both the scalar pk and a relation's pk compare the stored integer column safely."""
    lower = models.Branch.objects.create(name="Lower")
    models.Shelf.objects.create(branch=lower, code="PR-0")
    branch = models.Branch.objects.create(name="Upper")
    shelf = models.Shelf.objects.create(branch=branch, code="PR-1")
    selected: dict[str, tuple[Filter, str, list[object]]] = {
        "range": (RangeFilter(lookup_expr="range"), "pk", [saved_pk(shelf), 2**70]),
        "list": (ListFilter(lookup_expr="in"), "pk", [saved_pk(shelf), 2**70]),
        "integer-in": (IntegerInFilter(lookup_expr="in"), "pk", [saved_pk(shelf), 2**70]),
        "relation-range": (
            RangeFilter(lookup_expr="range"),
            "branch__pk",
            [saved_pk(branch), 2**70],
        ),
    }
    leaf, path, values = selected[kind]
    _answer(_schema(models.Shelf, leaf, path, "code"), values, "code", ["PR-1"], ["PR-0", "PR-1"])


@pytest.mark.django_db
@pytest.mark.parametrize("source", [models.LendingDesk, models.SelfServeDesk])
def test_a_declared_range_over_a_parent_link_key_compares_the_inherited_integer_column(
    source: type[models.LendingDesk],
) -> None:
    """Each MTI generation ranges Venue.id rather than applying range to the parent relation."""
    extra = {"kiosk_code": "K"} if source is models.SelfServeDesk else {}
    keys = [saved_pk(source.objects.create(name=name, **extra)) for name in ("D-1", "D-2", "D-3")]
    _answer(
        _schema(source, RangeFilter(lookup_expr="range"), "pk", "name"),
        keys[:2],
        "name",
        ["D-1", "D-2"],
        ["D-1", "D-2", "D-3"],
    )


@pytest.mark.django_db
def test_a_declared_range_into_a_parent_link_key_compares_the_faults_stored_column() -> None:
    """A KioskFault range walks both parent links to the integer column the kiosk key stores."""
    kiosks = [
        models.SelfServeDesk.objects.create(name=name, kiosk_code="K") for name in ("A", "B", "C")
    ]
    for kiosk in kiosks:
        models.KioskFault.objects.create(kiosk=kiosk, note=f"fault-{kiosk.name}")
    _answer(
        _schema(models.KioskFault, RangeFilter(lookup_expr="range"), "kiosk__pk", "note"),
        [saved_pk(kiosks[1]), saved_pk(kiosks[2])],
        "note",
        ["fault-B", "fault-C"],
        ["fault-A", "fault-B", "fault-C"],
    )


@pytest.fixture
def keyed_columns() -> Iterator[None]:
    columns = (
        _BigKeyed,
        _BigKeyedProfile,
        _UuidKeyed,
        _UuidKeyedProfile,
    )
    with connection.schema_editor() as editor:
        for model in columns:
            editor.create_model(model)
    try:
        yield
    finally:
        with connection.schema_editor() as editor:
            for model in reversed(columns):
                editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("keyed_columns")
@pytest.mark.parametrize("path", ["pk", "owner__code"])
@pytest.mark.parametrize(
    ("leaf", "values", "matches"),
    [
        pytest.param(RangeFilter(lookup_expr="range"), [6, 2**70], ["high"], id="two-bound"),
        pytest.param(RangeFilter(lookup_expr="range"), [2**70, None], [], id="start-only"),
        pytest.param(
            RangeFilter(lookup_expr="range"),
            [None, 2**70],
            ["high", "low"],
            id="end-only",
        ),
        pytest.param(RangeFilter(lookup_expr="range"), [-(2**70), 5], ["low"], id="low-start"),
        pytest.param(ListFilter(lookup_expr="in"), [12, 2**70], ["high"], id="list"),
        pytest.param(IntegerInFilter(lookup_expr="in"), [5, 2**70], ["low"], id="integer-in"),
    ],
)
def test_a_declared_one_to_one_integer_key_answers_as_its_underlying_column(
    path: str,
    leaf: Filter,
    values: list[object],
    matches: list[str],
) -> None:
    """Each original 64-bit O2O key range/list shape answers as the explicit owner column path."""
    for code, label in ((5, "low"), (12, "high")):
        _BigKeyedProfile.objects.create(owner=_BigKeyed.objects.create(code=code), label=label)
    _answer(
        _schema(_BigKeyedProfile, leaf, path, "label"),
        values,
        "label",
        matches,
        ["high", "low"],
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("keyed_columns")
@pytest.mark.parametrize("path", ["pk", "owner__code"])
@pytest.mark.parametrize(
    (
        "low",
        "high",
        "exclude",
        "matches",
    ),
    [
        pytest.param(1, 2, False, [1, 2], id="lower-pair"),
        pytest.param(2, 3, False, [2, 3], id="upper-pair"),
        pytest.param(1, 3, False, [1, 2, 3], id="every-row"),
        pytest.param(1, 2, True, [3], id="excluded"),
    ],
)
def test_a_declared_one_to_one_uuid_key_ranges_the_uuid_column(
    path: str,
    low: int,
    high: int,
    *,
    exclude: bool,
    matches: list[int],
) -> None:
    """UUID relation-valued keys retain the real column range and its exact excluded complement."""
    for value in (1, 2, 3):
        _UuidKeyedProfile.objects.create(
            owner=_UuidKeyed.objects.create(code=uuid.UUID(int=value)),
        )
    _answer(
        _schema(
            _UuidKeyedProfile,
            RangeFilter(lookup_expr="range", exclude=exclude),
            path,
            "owner_id",
        ),
        [str(uuid.UUID(int=low)), str(uuid.UUID(int=high))],
        "key",
        [str(uuid.UUID(int=value)) for value in matches],
        [str(uuid.UUID(int=value)) for value in (1, 2, 3)],
        variable_type="[UUID!]",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["single", "multiple"])
@pytest.mark.parametrize("shape", ["matching", "omitted"])
def test_an_unbound_relation_key_primitive_keeps_its_public_queryset_contract(
    kind: str,
    shape: str,
) -> None:
    """A standalone public primitive uses its incoming relation key without a parent binding."""
    branch = models.Branch.objects.create(name="Unbound primitives")
    shelf = models.Shelf.objects.create(branch=branch, code="A-1")
    other = models.Shelf.objects.create(branch=branch, code="B-2")
    models.Book.objects.create(title="Kept", shelf=shelf)
    models.Book.objects.create(title="Other", shelf=other)
    leaf = (
        RelationPkFilter(lookup_expr="exact")
        if kind == "single"
        else RelationPkMultipleFilter(lookup_expr="in")
    )
    values: object = saved_pk(shelf) if kind == "single" else [saved_pk(other)]
    if shape == "omitted":
        values = None
    matches = (
        ["Kept", "Other"] if shape == "omitted" else ["Kept"] if kind == "single" else ["Other"]
    )
    _answer(
        _schema(models.Book, leaf, "shelf", "title", bound=False),
        values,
        "title",
        matches,
        ["Kept", "Other"],
    )
