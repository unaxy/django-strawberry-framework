"""Live contracts of ``RelatedFilter(flat=False)`` on the shipped reading-list cycle.

``ReadingListFilter.entries`` is enabled and ``ReadingListEntryFilter.reading_list``
is ``flat=False``: the entry input carries the nested ``readingList`` branch and its
own ``readingListTitle`` traversal (``exact`` only) but no copy of the list set's
filters, while the list input carries the entry set's copies, its own traversal
included (``entriesReadingListTitle``). Every request crosses the disabled
declaration's branch or the enabled one's copies over ``/graphql/``: the branch's
form refuses before the set's own form, a malformed branch GlobalID before both, and
branch nesting through the disabled edge spends the ``_MAX_LOGIC_DEPTH`` budget.
``PatronFilter.borrowed_title``, a re-keyed copy through two enabled declarations,
executes too.
"""

import pytest
from apps.library import models
from django.test import override_settings
from graphql_client import (
    JSONObject,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    middleware_without_debug_toolbar,
)

_ENTRIES = """
query($f: ReadingListEntryFilterInputType) {
  allLibraryReadingListEntriesConnection(filter: $f) {
    edges {
      node {
        title
      }
    }
  }
}
"""

_LISTS = """
query($f: ReadingListFilterInputType) {
  allLibraryReadingListsConnection(filter: $f) {
    edges {
      node {
        title
      }
    }
  }
}
"""

_INPUT_FIELDS = """
query($name: String!) {
  __type(name: $name) {
    inputFields {
      name
    }
  }
}
"""


def _seed_reading_lists() -> None:
    """Classics holds Beloved and Middlemarch; Anthology holds Kindred."""
    classics = models.ReadingList.objects.create(title="Classics")
    anthology = models.ReadingList.objects.create(title="Anthology")
    for title in ("Beloved", "Middlemarch"):
        models.ReadingListEntry.objects.create(reading_list=classics, title=title)
    models.ReadingListEntry.objects.create(reading_list=anthology, title="Kindred")


def _input_field_names(type_name: str) -> list[str]:
    payload = graphql_payload(_INPUT_FIELDS, variables={"name": type_name})
    fields = json_list(payload, "data", "__type", "inputFields")
    return [str(json_object(field)["name"]) for field in fields]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("type_name", "names"),
    [
        (
            "ReadingListEntryFilterInputType",
            [
                "id",
                "title",
                "readingListTitle",
                "readingList",
                "and",
                "or",
                "not",
            ],
        ),
        (
            "ReadingListFilterInputType",
            [
                "id",
                "title",
                "entries",
                "entriesId",
                "entriesTitle",
                "entriesReadingListTitle",
                "and",
                "or",
                "not",
            ],
        ),
        ("ReadingListEntryFilterReadingListTitleFilterInputType", ["exact"]),
    ],
)
def test_the_reading_list_cycle_publishes_only_the_enabled_sides_flat_copies_over_http(
    type_name: str,
    names: list[str],
) -> None:
    """The disabled declaration publishes its branch and no copy; the entry set keeps its own key.

    ``readingListTitle`` is the entry set's own ``Meta.fields`` traversal, ``exact``
    only: an enabled declaration's copy of ``ReadingListFilter.title`` would replace
    it and add ``iContains``.
    """
    assert _input_field_names(type_name) == names


def _connection(titles: list[str], root: str) -> JSONObject:
    return {"data": {root: {"edges": [{"node": {"title": title}} for title in titles]}}}


_ENTRY_ROOT = "allLibraryReadingListEntriesConnection"
_LIST_ROOT = "allLibraryReadingListsConnection"


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "document",
        "root",
        "filter_input",
        "titles",
    ),
    [
        pytest.param(
            _ENTRIES,
            _ENTRY_ROOT,
            {"readingList": {"title": {"exact": "Classics"}}},
            ["Beloved", "Middlemarch"],
            id="disabled-declarations-nested-branch",
        ),
        pytest.param(
            _ENTRIES,
            _ENTRY_ROOT,
            {"readingList": {"title": {"exact": "Anthology"}}},
            ["Kindred"],
            id="disabled-declarations-nested-branch-other-list",
        ),
        pytest.param(
            _ENTRIES,
            _ENTRY_ROOT,
            {"readingListTitle": {"exact": "Classics"}},
            ["Beloved", "Middlemarch"],
            id="own-traversal-across-the-disabled-declaration",
        ),
        pytest.param(
            _LISTS,
            _LIST_ROOT,
            {"entriesTitle": {"exact": "Kindred"}},
            ["Anthology"],
            id="enabled-copy",
        ),
        pytest.param(
            _LISTS,
            _LIST_ROOT,
            {"entriesTitle": {"iContains": "march"}},
            ["Classics"],
            id="enabled-copy-icontains",
        ),
        pytest.param(
            _LISTS,
            _LIST_ROOT,
            {"entriesReadingListTitle": {"exact": "Anthology"}},
            ["Anthology"],
            id="enabled-copy-of-the-own-traversal",
        ),
        pytest.param(
            _LISTS,
            _LIST_ROOT,
            {"entries": {"readingList": {"title": {"exact": "Classics"}}}},
            ["Classics"],
            id="enabled-branch-into-the-disabled-branch",
        ),
    ],
)
def test_the_reading_list_cycle_executes_each_published_key_over_http(
    document: str,
    root: str,
    filter_input: JSONObject,
    titles: list[str],
) -> None:
    """Each published key of the cycle filters the rows it names."""
    _seed_reading_lists()
    assert graphql_payload(document, variables={"f": filter_input}) == _connection(titles, root)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("filter_input", "message"),
    [
        pytest.param(
            {"readingListId": {"exact": "1"}},
            "Variable '$f' has invalid value: Expected value of type "
            "'ReadingListEntryFilterInputType' not to include unknown field 'readingListId'. "
            "Did you mean 'readingList' or 'readingListTitle'? Found: "
            "{'readingListId': {'exact': '1'}}.",
            id="withdrawn-copy",
        ),
        pytest.param(
            {"readingListTitle": {"iContains": "class"}},
            "Variable '$f' has invalid value at .readingListTitle: Expected value of type "
            "'ReadingListEntryFilterReadingListTitleFilterInputType' not to include unknown "
            "field 'iContains', found: {'iContains': 'class'}.",
            id="own-key-keeps-its-own-lookups",
        ),
    ],
)
def test_a_flat_false_declaration_publishes_no_copied_key_over_http(
    filter_input: JSONObject,
    message: str,
) -> None:
    """A key only the disabled declaration's copy would publish is refused as unknown."""
    _seed_reading_lists()
    payload = graphql_payload(_ENTRIES, variables={"f": filter_input})
    assert payload == {
        "data": None,
        "errors": [{"message": message, "locations": [{"line": 2, "column": 7}]}],
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("value", "names"),
    [("two", ["p1", "p2"]), ("missing", [])],
    ids=["matching", "non-matching"],
)
def test_the_patron_override_alias_of_an_enabled_copy_executes_over_http(
    value: str,
    names: list[str],
) -> None:
    """``PatronFilter.borrowed_title`` re-keys a copy two enabled declarations deep; it filters.

    Both source edges (``PatronFilter.loans``, ``LoanFilter.book``) stay enabled, so the
    override finds ``loans__book__title__icontains`` and publishes it as ``borrowedTitle``.
    """
    branch = models.Branch.objects.create(name="Loans", city="Boston")
    shelf = models.Shelf.objects.create(code="L-1", topic="general", branch=branch)
    loaned = models.Book.objects.create(title="Two loans", shelf=shelf)
    other = models.Book.objects.create(title="Other", shelf=shelf)
    for name, book in (("p1", loaned), ("p2", loaned), ("p3", other)):
        patron = models.Patron.objects.create(name=name, email=f"{name}@x")
        models.Loan.objects.create(book=book, patron=patron)
    models.Patron.objects.create(name="p4", email="p4@x")

    payload = graphql_payload(
        "query($f: PatronFilterInputType) { allLibraryPatrons(filter: $f) { name } }",
        variables={"f": {"borrowedTitle": {"iContains": value}}},
    )
    assert payload == {"data": {"allLibraryPatrons": [{"name": name} for name in names]}}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("branch", "errors"),
    [
        pytest.param(
            {"title": {"exact": "C\x00"}},
            {"reading_list__title": ["null_characters_not_allowed"]},
            id="same-key",
        ),
        pytest.param(
            {"title": {"iContains": "C\x00"}},
            {"reading_list__title__icontains": ["null_characters_not_allowed"]},
            id="distinct-keys",
        ),
    ],
)
def test_a_nested_branch_and_its_own_key_sibling_refuse_together_over_http(
    branch: JSONObject,
    errors: dict[str, list[str]],
) -> None:
    """Across the disabled declaration, the branch's form refuses before the set's own form.

    The ``readingList`` branch's constraint is built (its nested form cleaned) before the
    entry set's own form validates ``readingListTitle``, as for any active branch; with
    both invalid the request is one ``FILTER_INVALID`` carrying the branch's error,
    under the key the branch spells.
    """
    _seed_reading_lists()
    payload = graphql_payload(
        _ENTRIES,
        variables={"f": {"readingList": branch, "readingListTitle": {"exact": "C\x00"}}},
    )
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1, payload
    error = json_object(payload, "errors", 0)
    assert error["message"] == "Invalid filter input"
    assert json_at(error, "extensions", "code") == "FILTER_INVALID"
    reported = json_object(error, "extensions", "errors")
    assert {
        key: [json_object(item)["code"] for item in json_list(reported, key)] for key in reported
    } == errors, payload


@pytest.mark.django_db
def test_a_branch_globalid_refusal_precedes_its_own_key_siblings_form_error_over_http() -> None:
    """A malformed GlobalID in the disabled declaration's branch is refused before any form cleans."""
    _seed_reading_lists()
    payload = graphql_payload(
        _ENTRIES,
        variables={
            "f": {"readingList": {"id": {"exact": "x"}}, "readingListTitle": {"exact": "C\x00"}},
        },
    )
    assert payload["data"] is None, payload
    refusal = (
        "Invalid GlobalID: 'x' is not a valid GlobalID (malformed base64 or not a "
        "'type_name:node_id' shape)."
    )
    assert [json_object(error)["message"] for error in json_list(payload, "errors")] == [refusal]


def _alternating_branches(hops: int) -> JSONObject:
    """``readingList`` / ``entries`` nested ``hops`` deep from the entry set, ending at a title."""
    criteria: JSONObject = {"title": {"exact": "Kindred"}}
    for index in reversed(range(hops)):
        criteria = {"readingList" if index % 2 == 0 else "entries": criteria}
    return criteria


@pytest.mark.django_db
@override_settings(DEBUG=True, MIDDLEWARE=middleware_without_debug_toolbar())
def test_the_logic_depth_budget_holds_across_a_disabled_declaration_over_http() -> None:
    """Branch nesting through the disabled ``readingList`` edge spends the same depth budget.

    Eight hops (entry -> list -> entry ... -> entry) answer Kindred, the one entry
    whose list holds an entry titled Kindred; ten pass ``_MAX_LOGIC_DEPTH`` and are
    refused naming the set the ninth hop reaches. ``DEBUG`` opens the error policy's
    pass-through so the cap's own sentence is the answer.
    """
    _seed_reading_lists()
    within = graphql_payload(_ENTRIES, variables={"f": _alternating_branches(8)})
    assert within == _connection(["Kindred"], _ENTRY_ROOT), within
    past = graphql_payload(_ENTRIES, variables={"f": _alternating_branches(10)})
    assert past["data"] is None, past
    refusal = (
        "FilterSet ReadingListFilter: logical-branch nesting exceeded _MAX_LOGIC_DEPTH=8. "
        "Flatten the filter input or split into multiple queries."
    )
    assert [json_object(error)["message"] for error in json_list(past, "errors")] == [refusal]
