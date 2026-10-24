"""Smoke tests proving the shared ``tests/_idioms.py`` order helpers hand out what they promise."""

import pytest

from tests._idioms import canonical_order, scrambled

_COLUMNS = (
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
    "id",
)


def test_canonical_order_sorts_by_the_canonical_key() -> None:
    """A plain name's canonical key opens with its ``repr``."""
    assert canonical_order(["b", "a", "c"]) == ["a", "b", "c"]


@pytest.mark.parametrize("kind", [set, frozenset])
def test_scrambled_iterates_out_of_canonical_order(
    kind: type[set[str] | frozenset[str]],
) -> None:
    """``scrambled`` hands back a ``kind`` over a subset of the members, out of canonical order."""
    declared = scrambled(kind, _COLUMNS)

    assert type(declared) is kind
    assert len(declared) >= 2
    assert set(declared) <= set(_COLUMNS)
    assert list(declared) != canonical_order(declared)


def test_scrambled_ignores_drop_names_when_judging_the_order() -> None:
    """Every ``drop`` name is present, and the order judged is the other names' order."""
    kept_pool = tuple(name for name in _COLUMNS if name != "updated_date")
    declared = scrambled(set, kept_pool, drop=("updated_date",))

    assert "updated_date" in declared
    kept = [name for name in declared if name != "updated_date"]
    assert len(kept) >= 2
    assert kept != canonical_order(kept)


@pytest.mark.parametrize("kind", [set, frozenset])
def test_scrambled_fails_loudly_on_a_pool_that_cannot_scramble(
    kind: type[set[str] | frozenset[str]],
) -> None:
    """One member has a single order, so no layout scrambles it and the test fails by name."""
    with pytest.raises(pytest.fail.Exception) as excinfo:
        scrambled(kind, ("name",))

    assert str(excinfo.value) == (
        f"no {kind.__name__} over ('name',) iterates out of canonical order"
    )
