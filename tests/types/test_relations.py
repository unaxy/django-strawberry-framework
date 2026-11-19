"""PendingRelation tests for identity semantics, frozen fields and the sentinel annotation repr.

``PendingRelation`` is ``@dataclass(frozen=True, eq=False)``, so records compare
and hash by identity: two records built from the same values stay distinct.
``TypeRegistry.discard_pending`` matches records by identity too.

No GraphQL request observes record identity or hashing. Live relation fields
live in ``examples/fakeshop/test_query/test_library_api.py``.
"""

from dataclasses import FrozenInstanceError, replace

import pytest
from apps.products.models import Category, Item

from django_strawberry_framework import DjangoType
from django_strawberry_framework.types.relations import (
    PendingRelation,
    PendingRelationAnnotation,
)

# Each record's source type registers; the shared fixture clears it after the test.
pytestmark = pytest.mark.usefixtures("isolate_global_registry")


def _build_pending() -> PendingRelation:
    return PendingRelation(
        source_type=type(
            "Src",
            (DjangoType,),
            {"Meta": type("Meta", (), {"model": Category, "fields": ("id", "name")})},
        ),
        source_model=Category,
        field_name="items",
        related_model=Item,
    )


def test_equal_valued_pending_relations_stay_distinct() -> None:
    """Two records built from the same values are unequal and occupy two set slots."""
    first = _build_pending()
    second = replace(first)

    assert first != second
    assert len({first, second}) == 2


def test_pending_relation_annotation_repr() -> None:
    """``PendingRelationAnnotation`` provides a diagnostic repr for unfinalized schemas."""
    assert repr(PendingRelationAnnotation) == (
        "<unfinalized DjangoType relation; "
        "call finalize_django_types() before constructing strawberry.Schema>"
    )


def test_pending_relation_is_frozen_dataclass() -> None:
    """``PendingRelation`` attributes cannot be mutated post-construction."""
    pending = _build_pending()

    with pytest.raises(FrozenInstanceError):
        # basedpyright: the write to the frozen dataclass field is the mutation under test; the
        # checker rejects assignment to a frozen field
        pending.field_name = "mutated"  # pyright: ignore[reportAttributeAccessIssue]
