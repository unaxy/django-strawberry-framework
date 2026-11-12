"""Live GraphQL HTTP tests for declared filters whose ``field_name`` or ``lookup_expr`` is lazy text.

A project may declare a filter's ``field_name`` or ``lookup_expr`` as Django's lazy
translation text (``gettext_lazy``). A package ``FilterSet`` reads each as the text it
renders, on every path, so each lazily spelled filter fakeshop ships answers the rows its
plain ``str`` spelling answers, in one statement:

- ``ScalarSpecimenFilter.tagLabelAmong``, a ``MultipleChoiceFilter`` over
  ``gettext_lazy("tag__label")``, a flat leaf walked across the ``tag`` branch, whose type
  shows active tags only;
- ``NullableScalarSpecimenFilter.partnerTagLabelAny``, the same filter two hops out across
  ``partner``, and ``partnerTagLabelContaining``, a multiple-choice filter on that path
  whose ``lookup_expr`` is ``gettext_lazy("icontains")``;
- ``NullableScalarSpecimenFilter.scoreWindow``, a ``RangeFilter`` over
  ``gettext_lazy("score")``, whose range input is named off the text;
- ``BranchFilter.shelfCodes``, a ``MultipleChoiceFilter`` over
  ``gettext_lazy("shelves__code")``, walked across the ``shelves`` branch onto the reverse
  foreign key's target column, and ``BookFilter.shelfBranchShelfCodes``, its flat copy
  walked across ``shelf`` and ``branch`` first.

Stock django-filter refuses the multiple-choice family with a lazy name (its predicate keys
a ``Q`` by the name and joins it to the lookup); reading the text is the package's own
guarantee.
"""

import datetime
import uuid

import pytest
from apps.library import models as library_models
from apps.scalars import models as scalars_models
from django.db import connection
from django.test.utils import CaptureQueriesContext
from graphql_client import assert_graphql_success, json_list, json_str

_SPECIMENS = """
query ($filter: ScalarSpecimenFilterInputType) {
  allScalarSpecimens(filter: $filter, orderBy: [{ label: ASC }]) { label }
}
"""

_NULLABLE_SPECIMENS = """
query ($filter: NullableScalarSpecimenFilterInputType) {
  allNullableScalarSpecimens(filter: $filter, orderBy: [{ label: ASC }]) { label }
}
"""

_BRANCHES = """
query ($filter: BranchFilterInputType) {
  allLibraryBranches(filter: $filter) { name }
}
"""


def _specimen(
    label: str,
    tag: scalars_models.ScalarSpecimenTag | None,
) -> scalars_models.ScalarSpecimen:
    """A scalar specimen labelled ``label`` carrying ``tag``."""
    return scalars_models.ScalarSpecimen.objects.create(
        label=label,
        flag=False,
        score=1.0,
        occurred_on=datetime.date(2021, 6, 15),
        occurred_at=datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc),
        occurred_time=datetime.time(9, 30),
        external_id=uuid.uuid4(),
        signed_big=1,
        unsigned_big=1,
        tag=tag,
    )


def _tagged_specimens() -> dict[str, scalars_models.ScalarSpecimen]:
    """``alpha`` tagged ``hot``, ``beta`` an inactive ``cold``, ``gamma`` ``warm``, ``delta`` none."""
    hot = scalars_models.ScalarSpecimenTag.objects.create(label="hot", active=True)
    cold = scalars_models.ScalarSpecimenTag.objects.create(label="cold", active=False)
    warm = scalars_models.ScalarSpecimenTag.objects.create(label="warm", active=True)
    return {
        "alpha": _specimen("alpha", hot),
        "beta": _specimen("beta", cold),
        "gamma": _specimen("gamma", warm),
        "delta": _specimen("delta", None),
    }


def _answered(
    query: str,
    root: str,
    filter_input: dict[str, object],
    key: str = "label",
) -> list[str]:
    """``key`` of every ``root`` row ``filter_input`` answers, after asserting one statement ran."""
    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(query, variables={"filter": filter_input})
    assert len(captured.captured_queries) == 1, captured.captured_queries
    return [json_str(row, key) for row in json_list(data, root)]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("labels", "expected"),
    [(["hot"], ["alpha"]), (["hot", "cold"], ["alpha"]), (["cold"], [])],
    ids=["one", "two", "hidden"],
)
def test_a_lazily_named_multiple_choice_leaf_walked_across_a_branch_answers_its_text(
    labels: list[str],
    expected: list[str],
) -> None:
    """``tagLabelAmong`` keeps the specimens whose visible tag carries a listed label.

    ``beta``'s tag is labelled ``cold`` but inactive, which the ``tag`` branch's type
    hides, so the walked leaf skips it as ``field_name="tag__label"`` does.
    """
    _ = _tagged_specimens()
    filter_input: dict[str, object] = {"tagLabelAmong": {"exact": labels}}
    assert _answered(_SPECIMENS, "allScalarSpecimens", filter_input) == expected


def _partnered() -> None:
    """``n1`` partners ``alpha`` (``hot``), ``n2`` ``beta``, ``n3`` ``gamma``, ``n4`` none."""
    specimens = _tagged_specimens()
    for label, partner in (("n1", "alpha"), ("n2", "beta"), ("n3", "gamma")):
        _ = scalars_models.NullableScalarSpecimen.objects.create(
            label=label,
            partner=specimens[partner],
        )
    _ = scalars_models.NullableScalarSpecimen.objects.create(label="n4")


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("filter_input", "expected"),
    [
        ({"partnerTagLabelAny": {"exact": ["hot"]}}, ["n1"]),
        ({"partnerTagLabelAny": {"exact": ["hot", "cold"]}}, ["n1"]),
        ({"partnerTagLabelContaining": {"iContains": ["ho"]}}, ["n1"]),
        ({"partnerTagLabelContaining": {"iContains": ["ho", "co"]}}, ["n1"]),
    ],
    ids=[
        "field-name-one",
        "field-name-two",
        "lookup-expr-one",
        "lookup-expr-two",
    ],
)
def test_a_lazily_spelled_multiple_choice_leaf_two_hops_out_answers_its_text(
    filter_input: dict[str, object],
    expected: list[str],
) -> None:
    """A lazy ``field_name`` or ``lookup_expr`` across ``partner`` and ``tag`` answers as text does.

    ``n2``'s partner carries the inactive ``cold`` tag, hidden on the second hop as
    ``field_name="partner__tag__label"`` and ``lookup_expr="icontains"`` hide it.
    """
    _partnered()
    assert _answered(_NULLABLE_SPECIMENS, "allNullableScalarSpecimens", filter_input) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("bounds", "expected"),
    [
        ({"start": 1.5, "end": 2.5}, ["two"]),
        ({"start": 1.5}, ["three", "two"]),
        ({"end": 2.5}, ["one", "two"]),
    ],
    ids=["two-bounds", "start", "end"],
)
def test_a_lazily_named_range_filter_serves_and_compares_its_column(
    bounds: dict[str, float],
    expected: list[str],
) -> None:
    """``scoreWindow`` builds a range input named off ``score`` and compares that column."""
    for label, score in (
        ("one", 1.0),
        ("two", 2.0),
        ("three", 3.0),
        ("unscored", None),
    ):
        _ = scalars_models.NullableScalarSpecimen.objects.create(label=label, score=score)
    filter_input: dict[str, object] = {"scoreWindow": {"exact": bounds}}
    assert _answered(_NULLABLE_SPECIMENS, "allNullableScalarSpecimens", filter_input) == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("codes", "expected"),
    [(["A1"], ["east"]), (["A1", "C1"], ["east", "west"]), (["A1", "B1"], ["east"])],
    ids=["one", "two-branches", "two-shelves-one-branch"],
)
def test_a_lazily_named_leaf_walked_onto_a_to_many_target_column_answers_its_text(
    codes: list[str],
    expected: list[str],
) -> None:
    """``shelfCodes`` keeps each branch holding a listed shelf code, once."""
    east = library_models.Branch.objects.create(name="east")
    west = library_models.Branch.objects.create(name="west")
    _ = library_models.Branch.objects.create(name="north")
    for code, branch in (("A1", east), ("B1", east), ("C1", west)):
        _ = library_models.Shelf.objects.create(
            code=code,
            topic="permanent collection",
            branch=branch,
        )
    filter_input: dict[str, object] = {"shelfCodes": {"exact": codes}}
    assert sorted(_answered(_BRANCHES, "allLibraryBranches", filter_input, "name")) == expected


_BOOKS = """
query ($filter: BookFilterInputType) {
  allLibraryBooks(filter: $filter) { title }
}
"""


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("codes", "expected"),
    [
        (["A1"], ["east-a", "east-b"]),
        (["C1"], ["west"]),
        (["A1", "C1"], ["east-a", "east-b", "west"]),
    ],
    ids=["one", "other-branch", "both"],
)
def test_a_flat_copy_of_a_lazily_named_leaf_answers_its_text(
    codes: list[str],
    expected: list[str],
) -> None:
    """``shelfBranchShelfCodes``, ``BookFilter``'s flat copy of ``shelfCodes``, answers as text does.

    The copy walks ``shelf`` and ``branch`` before the lazily named leaf's own
    ``shelves__code``, keeping each book whose shelf's branch holds a listed shelf code.
    """
    east = library_models.Branch.objects.create(name="east")
    west = library_models.Branch.objects.create(name="west")
    shelves = {
        code: library_models.Shelf.objects.create(
            code=code,
            topic="permanent collection",
            branch=branch,
        )
        for code, branch in (("A1", east), ("B1", east), ("C1", west))
    }
    for title, code in (("east-a", "A1"), ("east-b", "B1"), ("west", "C1")):
        _ = library_models.Book.objects.create(title=title, shelf=shelves[code])
    filter_input: dict[str, object] = {"shelfBranchShelfCodes": {"exact": codes}}
    assert sorted(_answered(_BOOKS, "allLibraryBooks", filter_input, "title")) == expected
