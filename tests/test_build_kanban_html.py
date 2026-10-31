"""Tests for KANBAN version-tuple parsing, placeholder resolvability, and truncation.

Repo tooling: these rows pin ``scripts/_kanban_lib.py`` helpers and
``scripts/build_kanban_html.py::assert_placeholders_resolve``, which run at
render time against an in-process snapshot. A live ``/graphql/`` request has
no wire shape for a version-tuple parse, a Vue-shell placeholder that would
print literally in ``KANBAN.html``, or a silent ``max_list_rows`` cap the
freshness checks cannot see, so none of these rows can move. The kanban
GraphQL surface lives in ``examples/fakeshop/test_query/test_kanban_api.py``
and ``examples/fakeshop/test_query/test_kanban_mutations_api.py``; those cover
reads and writes over HTTP, not this renderer.
"""

import pytest

from scripts._kanban_lib import (
    CARD_NESTED_LISTS,
    CardLink,
    CardRow,
    DashboardData,
    assert_nothing_truncated,
    placeholder_defects,
    truncation_defects,
    unresolvable_placeholders,
    version_tuple,
)
from scripts.build_kanban_html import assert_placeholders_resolve


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1\u00b2.2", (1, 2)),
        ("\u00b2.2", (0,)),
    ],
    ids=["digit-then-superscript", "leading-superscript"],
)
def test_version_tuple_ignores_non_ascii_digit_like_characters(
    text: str,
    expected: tuple[int, ...],
) -> None:
    assert version_tuple(text) == expected


def test_version_tuple_stops_at_an_oversized_decimal_segment() -> None:
    assert version_tuple(f"1.{'2' * 5000}.3") == (1,)


def _card(text: str, *, orders: tuple[int, ...] = ()) -> CardRow:
    """A card carrying one scope item and the reference orders it may cite."""
    target: CardLink = {
        "id": "0",
        "cardId": "TODO-ALPHA-001-0.0.1",
        "number": 1,
        "title": "target",
        "slug": "target",
    }
    return {
        "id": "52",
        "cardId": "TODO-ALPHA-052-0.0.16",
        "number": 52,
        "title": "card",
        "slug": "card",
        "planningNote": "",
        "updatedDate": "2026-01-01",
        "status": {"key": "todo", "label": "Todo"},
        "milestone": None,
        "targetVersion": None,
        "priority": None,
        "relativeSize": None,
        "spec": None,
        "labels": [],
        "items": [
            {
                "id": "1",
                "order": 59,
                "text": text,
                "isComplete": False,
                "section": {"key": "scope", "label": "Scope", "order": 0},
            },
        ],
        "outgoingReferences": [
            {
                "id": str(order),
                "order": order,
                "rawText": "",
                "kind": {"key": "mention", "label": "Mention"},
                "targetCard": target,
            }
            for order in orders
        ],
        "pathLinks": [],
        "parityClaims": [],
        "dependencies": [],
    }


def _snapshot(cards: list[CardRow]) -> DashboardData:
    """A board snapshot holding ``cards``, no board docs and empty lookup tables."""
    return {
        "cards": cards,
        "boardDocs": [],
        "lookups": {
            "statuses": [],
            "milestones": [],
            "targetVersions": [],
            "priorities": [],
            "relativeSizes": [],
            "upstreams": [],
            "parityLevels": [],
            "sections": [],
            "referenceKinds": [],
            "boardDocKinds": [],
            "trackedPaths": [],
        },
        "blockingReferenceKindKeys": [],
    }


def test_a_numeric_card_ref_backed_by_a_reference_row_resolves() -> None:
    assert unresolvable_placeholders("{{card_ref:0}}", reference_orders={0}) == []


@pytest.mark.parametrize(
    "text",
    ["{{card_ref:N}}", "{{card_ref:99}}"],
    ids=["non-numeric", "out-of-range"],
)
def test_a_card_ref_the_shell_cannot_resolve_is_reported(text: str) -> None:
    assert unresolvable_placeholders(text, reference_orders={0}) == [text]


@pytest.mark.parametrize("computed", [False, True], ids=["card-text", "board-doc"])
def test_a_computed_token_resolves_in_a_board_doc_body_but_not_in_card_text(
    *,
    computed: bool,
) -> None:
    """Only a computed-token owner admits this board-doc placeholder."""
    assert unresolvable_placeholders(
        "{{active_version}}",
        reference_orders=set[int](),
        computed_tokens={"active_version"} if computed else set[str](),
    ) == ([] if computed else ["{{active_version}}"])


def test_a_defect_names_the_row_that_stores_it() -> None:
    """The token alone does not locate it; one placeholder can be on any card item."""
    assert placeholder_defects([_card("rewritten to {{card_ref:N}} placeholders")], []) == [
        "card TODO-ALPHA-052-0.0.16 item order=59 section=scope: {{card_ref:N}}",
    ]


@pytest.mark.parametrize("resolvable", [True, False], ids=["resolved", "unresolved"])
def test_the_html_build_refuses_a_placeholder_that_resolves_nowhere(*, resolvable: bool) -> None:
    """An export accepts a real card reference and independently refuses an unresolved one."""
    if resolvable:
        assert (
            assert_placeholders_resolve(_snapshot([_card("see {{card_ref:0}}", orders=(0,))]))
            is None
        )
    else:
        with pytest.raises(RuntimeError, match=r"resolve nowhere"):
            assert_placeholders_resolve(_snapshot([_card("see {{card_ref:N}}")]))


def _payload_card(number: int, **lists: int) -> dict[str, object]:
    """A card as the GraphQL payload carries it, with the named lists' lengths."""
    return {
        "number": number,
        **{key: [{"order": index} for index in range(count)] for key, count in lists.items()},
    }


def _expected(number: int, **lists: int) -> dict[str, dict[int, int]]:
    """Ground truth for one card: every guarded list, defaulting to zero."""
    return {key: {number: lists.get(key, 0)} for key in CARD_NESTED_LISTS}


def test_a_board_matching_the_database_reports_no_truncation() -> None:
    """The control: without it, an assertion that never fires reads as a passing proof."""
    assert (
        truncation_defects(
            [_payload_card(52, items=101, glossaryLinks=53)],
            _expected(52, items=101, glossaryLinks=53),
        )
        == []
    )


def test_a_card_whose_items_were_capped_is_reported() -> None:
    """A nested ``items`` list short of the database count is reported."""
    assert truncation_defects(
        [_payload_card(52, items=100)],
        _expected(52, items=101),
    ) == ["card 52 items: payload has 100, database has 101"]


@pytest.mark.parametrize("payload_key", sorted(CARD_NESTED_LISTS))
def test_every_guarded_list_can_actually_fail(payload_key: str) -> None:
    """Each nested list in the census reports its own shortfall.

    Covering ``items`` does not prove ``glossaryLinks`` (or any other key); a
    map entry no case exercises is coverage on paper only.
    """
    defects = truncation_defects(
        [_payload_card(52, **{payload_key: 4})],
        _expected(52, **{payload_key: 5}),
    )
    assert defects == [f"card 52 {payload_key}: payload has 4, database has 5"]


def test_a_card_without_an_integer_number_is_reported() -> None:
    """A card the database counts cannot be matched against never checks clean."""
    assert truncation_defects(
        [{"number": None, "items": []}],
        _expected(52, items=0),
    ) == ["card None: payload has no integer number"]


def test_a_top_level_list_is_not_checked() -> None:
    """The bound is nested-only, so a top-level count here could never fail."""
    assert truncation_defects([], {}) == []


@pytest.mark.parametrize("items", [101, 100], ids=["complete", "truncated"])
def test_the_build_refuses_a_board_that_came_back_short(
    monkeypatch: pytest.MonkeyPatch,
    items: int,
) -> None:
    """A complete board exports; a silent item cap independently stops the build."""
    monkeypatch.setattr("scripts._kanban_lib.board_row_counts", lambda: _expected(52, items=101))
    if items == 101:
        assert assert_nothing_truncated([_payload_card(52, items=items)]) is None
    else:
        with pytest.raises(RuntimeError, match=r"came back short of the database"):
            assert_nothing_truncated([_payload_card(52, items=items)])
