"""Optimizer execution over a reverse one-to-one whose query name and accessor differ.

``SpParent.card`` (``tests/optimizer/_spelling_models.py``) is reached on an
instance and by ``prefetch_related`` as ``card`` and by ``select_related`` and
``only()`` as ``cards``, the name the generated GraphQL field carries. The plan
holds each ledger in the spelling Django reads it in, so a consumer
``Prefetch("card", queryset=...)`` owns the planned ``cards`` JOIN, a consumer
``select_related("cards")`` yields to a planned ``Prefetch("card")``, and a
prefetch or connection window planned beneath the ``cards`` JOIN is looked up
through ``card``.
``SpParent.badge`` names both the same and is the control. Each row compares the
optimized wire with the optimizer-off wire and pins both query counts; the
schemas execute in-process because fakeshop carries no such relation.
"""

from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING

import pytest
import strawberry
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper
from django.db.models import Prefetch, QuerySet
from strategy_schemas import make_django_type

from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.registry import registry

from ._spelling_models import SpBadge, SpCard, SpGenre, SpParent, spelling_fixture_tables

if TYPE_CHECKING:
    from django.db.backends.utils import _ExecuteParameters, _ExecuteQuery

pytestmark = [
    pytest.mark.usefixtures("isolate_global_registry", "spelling_tables"),
    pytest.mark.django_db(transaction=True),
]

#: A ``get_queryset`` hook body, bound as a classmethod on the type it narrows.
_Hook = Callable[..., object]


@pytest.fixture
def spelling_tables() -> Iterator[None]:
    """Materialize and seed the split-name fixture tables for one row."""
    with spelling_fixture_tables(connection):
        yield


def _hooks(hook: _Hook | None) -> Mapping[str, object] | None:
    return {"get_queryset": classmethod(hook)} if hook is not None else None


def _schema(
    *,
    optimizer: bool,
    parent_hook: _Hook | None = None,
    card_hook: _Hook | None = None,
) -> strawberry.Schema:
    registry.clear()
    _connection_type_cache.clear()
    make_django_type("SpGenreType", SpGenre, ("id", "name"))
    make_django_type(
        "SpCardType",
        SpCard,
        ("id", "name", "genres"),
        meta_extra={"relation_shapes": {"genres": "both"}},
        namespace_extra=_hooks(card_hook),
    )
    make_django_type("SpBadgeType", SpBadge, ("id", "name"), node=False)
    parent_type = make_django_type(
        "SpParentType",
        SpParent,
        (
            "id",
            "code",
            "cards",
            "badge",
        ),
        node=False,
        namespace_extra=_hooks(parent_hook),
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"parents": list[parent_type]},
                "parents": DjangoListField(parent_type),
            },
        ),
    )
    extensions = []
    if optimizer:
        extension = DjangoOptimizerExtension(strictness="raise")
        extensions = [lambda: extension]
    return strawberry.Schema(query=query_cls, config=strawberry_config(), extensions=extensions)


def _recorded_statements(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record every statement the request runs, on whichever thread runs it.

    The async executor runs the ORM on a worker thread whose connection the test
    thread's ``CaptureQueriesContext`` never sees; recording at the cursor class
    counts both colors the same way.
    """
    recorded: list[str] = []
    execute = CursorWrapper.execute

    def _recording_execute(
        cursor: CursorWrapper,
        sql: "_ExecuteQuery",
        params: "_ExecuteParameters" = None,
    ) -> None:
        # The ORM reads rows from the cursor, never this call's return value.
        recorded.append(str(sql))
        execute(cursor, sql, params)

    monkeypatch.setattr(CursorWrapper, "execute", _recording_execute)
    return recorded


def _run_sync(
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    optimizer: bool,
    parent_hook: _Hook | None = None,
    card_hook: _Hook | None = None,
) -> tuple[object, int]:
    schema = _schema(optimizer=optimizer, parent_hook=parent_hook, card_hook=card_hook)
    with monkeypatch.context() as patch:
        recorded = _recorded_statements(patch)
        result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    return result.data, len(recorded)


async def _run_async(
    query: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    optimizer: bool,
    parent_hook: _Hook | None = None,
    card_hook: _Hook | None = None,
) -> tuple[object, int]:
    schema = await sync_to_async(_schema)(
        optimizer=optimizer,
        parent_hook=parent_hook,
        card_hook=card_hook,
    )
    with monkeypatch.context() as patch:
        recorded = _recorded_statements(patch)
        result = await schema.execute(query)
    assert result.errors is None, result.errors
    return result.data, len(recorded)


def _prefetch_card_without_b(
    _cls: type[DjangoType],
    queryset: QuerySet[SpParent],
    _info: object,
    **_kwargs: object,
) -> QuerySet[SpParent]:
    """The parent hook: ``Prefetch("card")`` over every card but ``CARD-B``."""
    return queryset.prefetch_related(
        Prefetch("card", queryset=SpCard.objects.exclude(name="CARD-B")),
    )


def _prefetch_badge_without_b(
    _cls: type[DjangoType],
    queryset: QuerySet[SpParent],
    _info: object,
    **_kwargs: object,
) -> QuerySet[SpParent]:
    """The control hook: ``Prefetch("badge")`` over every badge but ``BADGE-B``."""
    return queryset.prefetch_related(
        Prefetch("badge", queryset=SpBadge.objects.exclude(name="BADGE-B")),
    )


def _join_cards(
    _cls: type[DjangoType],
    queryset: QuerySet[SpParent],
    _info: object,
    **_kwargs: object,
) -> QuerySet[SpParent]:
    """The parent hook: the consumer's own ``select_related`` JOIN, in query-name spelling."""
    return queryset.select_related("cards")


def _cards_without_b(
    _cls: type[DjangoType],
    queryset: QuerySet[SpCard],
    _info: object,
    **_kwargs: object,
) -> QuerySet[SpCard]:
    """The card type's hook: ``CARD-B`` is not visible."""
    return queryset.exclude(name="CARD-B")


_CARDS_QUERY = "{ parents { code cards { name } } }"
_CARDS_WITHOUT_B = {
    "parents": [
        {"code": "P-A", "cards": {"name": "CARD-A"}},
        {"code": "P-B", "cards": None},
        {"code": "P-C", "cards": None},
    ],
}


def test_consumer_prefetch_by_accessor_owns_the_query_name_join(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A consumer ``Prefetch("card", queryset=...)`` owns the rows the plan would JOIN as ``cards``.

    The planned ``select_related("cards")`` is withdrawn with its resolver key, so
    the consumer's queryset is the one source of the relation's rows and
    ``CARD-B`` stays hidden: the root query and the consumer's prefetch, as
    without the optimizer.
    """
    expected = _run_sync(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=False,
        parent_hook=_prefetch_card_without_b,
    )
    assert expected == (_CARDS_WITHOUT_B, 2)
    optimized = _run_sync(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=True,
        parent_hook=_prefetch_card_without_b,
    )
    assert optimized == expected


async def test_consumer_prefetch_by_accessor_owns_the_query_name_join_async(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The async color of the accessor-spelled ownership row: same rows, same two queries."""
    expected = await _run_async(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=False,
        parent_hook=_prefetch_card_without_b,
    )
    assert expected == (_CARDS_WITHOUT_B, 2)
    optimized = await _run_async(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=True,
        parent_hook=_prefetch_card_without_b,
    )
    assert optimized == expected


def test_consumer_prefetch_owns_the_join_when_both_names_coincide(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The control: ``Prefetch("badge", queryset=...)`` owns the planned ``badge`` JOIN."""
    query = "{ parents { code badge { name } } }"
    expected = _run_sync(
        query,
        monkeypatch,
        optimizer=False,
        parent_hook=_prefetch_badge_without_b,
    )
    assert expected == (
        {
            "parents": [
                {"code": "P-A", "badge": {"name": "BADGE-A"}},
                {"code": "P-B", "badge": None},
                {"code": "P-C", "badge": None},
            ],
        },
        2,
    )
    optimized = _run_sync(
        query,
        monkeypatch,
        optimizer=True,
        parent_hook=_prefetch_badge_without_b,
    )
    assert optimized == expected


def test_consumer_join_by_query_name_yields_to_the_hooked_prefetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A consumer ``select_related("cards")`` is released for the planned ``Prefetch("card")``.

    The card type's hook hides ``CARD-B`` and downgrades the relation to a
    ``Prefetch`` through it; the consumer's JOIN on the same relation would
    cache every card first and serve the hidden one. Released, the prefetch is
    the one source: the root query and one prefetch, where the unoptimized
    resolver reads each joined card back through the hook once per parent.
    """
    expected = _run_sync(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=False,
        parent_hook=_join_cards,
        card_hook=_cards_without_b,
    )
    assert expected[0] == _CARDS_WITHOUT_B
    optimized = _run_sync(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=True,
        parent_hook=_join_cards,
        card_hook=_cards_without_b,
    )
    assert optimized == (_CARDS_WITHOUT_B, 2)
    assert expected[1] == 3


async def test_consumer_join_by_query_name_yields_to_the_hooked_prefetch_async(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The async color of the released consumer JOIN: same rows, one prefetch."""
    expected = await _run_async(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=False,
        parent_hook=_join_cards,
        card_hook=_cards_without_b,
    )
    assert expected[0] == _CARDS_WITHOUT_B
    optimized = await _run_async(
        _CARDS_QUERY,
        monkeypatch,
        optimizer=True,
        parent_hook=_join_cards,
        card_hook=_cards_without_b,
    )
    assert optimized == (_CARDS_WITHOUT_B, 2)
    assert expected[1] == 3


def test_prefetch_beneath_the_query_name_join_is_looked_up_through_the_accessor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``genres`` beneath the ``cards`` JOIN is prefetched as ``card__genres``.

    One query JOINs each parent's card and one prefetches every card's genres;
    the lookup Django refuses (``cards__genres``) is never planned.
    """
    query = "{ parents { code cards { name genres { name } } } }"
    expected = _run_sync(query, monkeypatch, optimizer=False)
    assert expected[0] == {
        "parents": [
            {
                "code": "P-A",
                "cards": {"name": "CARD-A", "genres": [{"name": "g1"}, {"name": "g2"}]},
            },
            {"code": "P-B", "cards": {"name": "CARD-B", "genres": [{"name": "g1"}]}},
            {"code": "P-C", "cards": None},
        ],
    }
    optimized = _run_sync(query, monkeypatch, optimizer=True)
    assert optimized == (expected[0], 2)


def test_window_beneath_the_query_name_join_is_looked_up_through_the_accessor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``genresConnection`` window beneath the ``cards`` JOIN attaches through ``card__genres``.

    One query JOINs each parent's card and one windows every card's genres, where
    the unoptimized schema pages each card's genres on its own.
    """
    query = "{ parents { code cards { genresConnection(first: 1) { edges { node { name } } } } } }"
    expected = _run_sync(query, monkeypatch, optimizer=False)
    first_genre = {"genresConnection": {"edges": [{"node": {"name": "g1"}}]}}
    assert expected[0] == {
        "parents": [
            {"code": "P-A", "cards": first_genre},
            {"code": "P-B", "cards": first_genre},
            {"code": "P-C", "cards": None},
        ],
    }
    optimized = _run_sync(query, monkeypatch, optimizer=True)
    assert optimized == (expected[0], 2)
    assert expected[1] > optimized[1]
