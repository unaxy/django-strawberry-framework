"""Live GraphQL HTTP tests for the library relation shapes the optimizer plans specially.

One shape per planner rule, each read off the wire and off the SQL the request emitted:

- Relay id projection when the primary key IS a relation: ``PatronProfile.patron``
  is the one-to-one key, so ``PatronProfileType``'s id has to be built from the
  ``patron_id`` column instead of a lazy load of the related row.
- Digit-boundary names round-tripping to their real Django columns:
  ``Edition.isbn_10`` on a scalar, ``Edition.publisher_2`` on a forward key.
- Explicitly named fields resolving per published name: ``PatronProfileType``
  publishes ``address_2`` as ``secondaryAddress`` and ``postal_code`` as
  ``secondary_address``, two columns whose names differ only by casing convention.
- Forward-key id elision when the target's key is neither named ``id`` nor
  camel-case-stable: ``Printing.edition`` answers ``edition { isbn13 }`` from
  ``printing.edition_id``, and refuses to elide once a non-key edition column is
  selected.
- No elision through a ``to_field`` key: ``PatronProfile.favorite_genre`` stores
  the genre name, so ``favoriteGenre { id }`` still reads ``library_genre``.
- No elision into a custom ``relay.NodeID``: ``PublisherType`` publishes
  ``house_code`` as its node id, so ``publisher { id }`` still reads
  ``library_publisher``.
- A digit-boundary reverse accessor carrying a planned nested window:
  ``Publisher.printings_2`` pages as ``printings2Connection`` off one
  ``ROW_NUMBER() OVER (PARTITION BY ...)`` statement.
- A child default manager no strategy can window: ``AnnotationManager`` returns a
  distinct queryset, so ``PatronProfileType.annotationsConnection`` is left
  unplanned by ``optimizer/nested_planner.py`` and resolves per parent.
- A random child order the window cannot reproduce: ``Book`` ordered by ``"?"``
  or ``Random()`` - from a ``BookType.get_queryset`` hook (directly, reversed,
  under a composition, behind an annotation alias, a transform of one or an ``F``
  to one, in a ``When`` condition reading one) or from ``Meta.ordering`` - leaves
  ``GenreType.booksConnection`` unplanned, so each genre's page is one per-parent
  statement holding one random draw, structured exactly like the same window
  under a column order. A ``shelf`` name under a random ``Shelf.Meta.ordering``
  is such an order too: Django orders a relation name by its model's ordering.
- An order naming a relation, which Django compiles into the related model's
  ``Meta.ordering``: the window orders by that expansion, so a ``Book`` order by
  ``shelf`` (hook or ``Meta.ordering``, either direction, reversed) under every
  shape of ``Shelf.Meta.ordering``, a ``Book`` order by ``genres`` or ``loans``
  (rows multiplied by the join), a ``Printing`` order by ``edition`` reaching the
  nullable ``Edition.publisher_2``, a ``ShelfLabel`` order by its multi-column
  ``shelf`` (its carrier columns, which Django never expands) and a
  ``PatronProfile`` order by its one-to-one key (made total by that key) each
  page from one ``ROW_NUMBER`` statement exactly as the library schema pages
  them with no optimizer. A related ``"?"``, an ordering loop and a
  condition item raise Django's own error with and without the optimizer.
- A ``Book`` hook order through ``extra(order_by=...)``, which Django compiles
  in place of every other ordering - a descending field, the book's own
  ``table.column``, its foreign key's raw column, a joined shelf column and a
  quoted table name, each as written and reversed: the window pages it from
  one ``ROW_NUMBER`` statement exactly as the library schema pages it with no
  optimizer and as Django orders the hook queryset itself.
- Mixed-case Django names, whose published spelling reverses to a name the model
  lacks: ``Distributor.displayName`` projects its own column, the forward key
  ``Consignment.distributorRef`` plans one ``JOIN``, and its reverse
  ``consignmentItems`` loads through one prefetch on ``distributorRef_id``, the
  relation counts held at one and three parents.
- A model with no default order at all: ``ReadingListEntry`` clears its abstract
  parent's title ordering with ``ordering = None``, so a connection over entries
  with no ``orderBy:`` pages in primary-key order at the root and inside the
  nested window, while ``ReadingList`` keeps the title order it inherits; a
  resolver returning ``ReadingList.objects.order_by()`` switches that inherited
  order off, and its connection pages in primary-key order instead.
"""

from collections.abc import Callable

import pytest
import strawberry
from apps.library import models
from apps.library import schema as library_schema
from django.db import connection
from django.db.models import Case, F, FloatField, Model, Q, QuerySet, Value, When
from django.db.models.functions import Abs, Lower, Random
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext, register_lookup
from django.urls import clear_url_caches, path
from graphql_client import (
    JSONObject,
    assert_graphql_success,
    graphql_payload,
    json_at,
    json_int,
    json_list,
    json_object,
    json_str,
    middleware_without_debug_toolbar,
)
from strategy_schemas import make_django_type
from strawberry.relay.utils import to_base64

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import decode_global_id, global_id_for
from django_strawberry_framework.views import DjangoGraphQLView


def _sql_from_table(captured: CaptureQueriesContext, table: str) -> list[str]:
    """Return captured SQL whose ``FROM`` is exactly ``table`` (not a prefix match)."""
    needle = f'FROM "{table}"'
    return [entry["sql"] for entry in captured.captured_queries if needle in entry["sql"]]


def _sql_touching(captured: CaptureQueriesContext, table: str) -> list[str]:
    """Return captured SQL naming ``table`` anywhere - a ``FROM`` or a ``JOIN``."""
    needle = f'"{table}"'
    return [entry["sql"] for entry in captured.captured_queries if needle in entry["sql"]]


def _seed_two_patron_profiles() -> tuple[models.PatronProfile, models.PatronProfile]:
    """Two patrons with profiles; only the first carries a ``favorite_genre``."""
    genre = models.Genre.objects.create(name="Speculative")
    ada = models.Patron.objects.create(name="Ada")
    grace = models.Patron.objects.create(name="Grace")
    first = models.PatronProfile.objects.create(
        patron=ada,
        address_2="Flat 2",
        postal_code="02139",
        favorite_genre=genre,
    )
    second = models.PatronProfile.objects.create(
        patron=grace,
        address_2="Suite 7",
        postal_code="10001",
    )
    return first, second


def _seed_publishing_graph() -> tuple[models.Publisher, models.Publisher]:
    """Two publishers, one edition each, and press runs attributed to both houses."""
    first = models.Publisher.objects.create(name="Gollancz", house_code="HOUSE-G")
    second = models.Publisher.objects.create(name="Orbit", house_code="HOUSE-O")
    first_edition = models.Edition.objects.create(
        isbn_13="9780000000001",
        isbn_10="0000000001",
        imprint="Gollancz SF",
        publisher=first,
        publisher_2=second,
    )
    second_edition = models.Edition.objects.create(
        isbn_13="9780000000002",
        isbn_10="0000000002",
        imprint="Orbit Classics",
        publisher=second,
    )
    for run_size in (100, 200, 300):
        models.Printing.objects.create(
            edition=first_edition,
            publisher_2=first,
            run_size=run_size,
        )
    for run_size in (400, 500):
        models.Printing.objects.create(
            edition=second_edition,
            publisher_2=second,
            run_size=run_size,
        )
    return first, second


@pytest.mark.django_db
def test_patron_profile_relay_id_is_built_from_the_relation_primary_key_column() -> None:
    """A model whose primary key IS a relation mints its Relay id from the key column.

    ``PatronProfile.patron`` is a ``OneToOneField(primary_key=True)``, so the
    field name and the column an id projection must read (``patron_id``) differ.
    The page is one statement against ``library_patronprofile``: reading the id
    off the related row would cost a lazy ``library_patron`` load per edge.
    """
    first, second = _seed_two_patron_profiles()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryPatronProfilesConnection { edges { node { id } } } }",
        )

    edges = json_list(data, "allLibraryPatronProfilesConnection", "edges")
    assert [json_at(edge, "node", "id") for edge in edges] == [
        global_id_for(library_schema.PatronProfileType, first.patron_id),
        global_id_for(library_schema.PatronProfileType, second.patron_id),
    ], edges
    profile_sql = _sql_from_table(captured, "library_patronprofile")
    assert len(profile_sql) == 1, profile_sql
    assert "patron_id" in profile_sql[0], profile_sql[0]
    assert _sql_touching(captured, "library_patron") == [], captured.captured_queries


@pytest.mark.django_db
def test_edition_digit_boundary_names_project_their_own_django_columns() -> None:
    """``isbn10`` and ``publisher2`` resolve to the ``isbn_10`` / ``publisher_2_id`` columns.

    Both published names lose their ``<word>_<digit>`` boundary on the way to
    camelCase, so a name resolved by un-camel-casing alone would miss the model
    field. The values on the wire are the seeded ones and the root projection
    carries both real column names.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryEditions { isbn13 isbn10 publisher2 { name } } }",
        )

    assert data["allLibraryEditions"] == [
        {"isbn13": "9780000000001", "isbn10": "0000000001", "publisher2": {"name": "Orbit"}},
        {"isbn13": "9780000000002", "isbn10": "0000000002", "publisher2": None},
    ], data
    edition_sql = _sql_from_table(captured, "library_edition")
    assert len(edition_sql) == 1, edition_sql
    assert "isbn_10" in edition_sql[0], edition_sql[0]
    assert "publisher_2_id" in edition_sql[0], edition_sql[0]


@pytest.mark.django_db
def test_patron_profile_explicitly_named_fields_each_return_their_own_column() -> None:
    """``secondaryAddress`` and ``secondary_address`` are two columns, not one.

    ``PatronProfileType`` names ``address_2`` and ``postal_code`` with
    ``strawberry.field(name=...)``; the two published names normalize to the same
    string under a casing convention, so both are selected in ONE document - a
    resolution that matched on a normalized name would answer them alike.
    """
    _seed_two_patron_profiles()

    data = assert_graphql_success(
        """
        query {
          allLibraryPatronProfilesConnection {
            edges { node { secondaryAddress secondary_address } }
          }
        }
        """,
    )

    edges = json_list(data, "allLibraryPatronProfilesConnection", "edges")
    assert [json_at(edge, "node") for edge in edges] == [
        {"secondaryAddress": "Flat 2", "secondary_address": "02139"},
        {"secondaryAddress": "Suite 7", "secondary_address": "10001"},
    ], edges


@pytest.mark.django_db
def test_printing_edition_key_only_selection_is_answered_from_the_stored_key_column() -> None:
    """``edition { isbn13 }`` is served from ``printing.edition_id`` alone.

    ``Edition``'s primary key is the text column ``isbn_13`` - not named ``id``
    and not camel-case-stable - so the elision has to resolve the target's real
    primary-key name before it can answer the selection from the source row.
    ``library_edition`` is neither joined nor prefetched.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPrintingsConnection {
                edges { node { runSize edition { isbn13 } } }
              }
            }
            """,
        )

    edges = json_list(data, "allLibraryPrintingsConnection", "edges")
    assert [json_at(edge, "node", "edition", "isbn13") for edge in edges] == [
        "9780000000001",
        "9780000000001",
        "9780000000001",
        "9780000000002",
        "9780000000002",
    ], edges
    printing_sql = _sql_from_table(captured, "library_printing")
    assert len(printing_sql) == 1, printing_sql
    assert "edition_id" in printing_sql[0], printing_sql[0]
    assert _sql_touching(captured, "library_edition") == [], captured.captured_queries


@pytest.mark.django_db
def test_printing_edition_non_key_selection_reads_the_edition_table() -> None:
    """The same relation joins the moment a non-key edition column is selected.

    The elision is scoped to a selection the source row can answer; ``imprint``
    is not the edition's primary key, so ``library_edition`` is read.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPrintingsConnection {
                edges { node { edition { imprint } } }
              }
            }
            """,
        )

    edges = json_list(data, "allLibraryPrintingsConnection", "edges")
    assert {json_at(edge, "node", "edition", "imprint") for edge in edges} == {
        "Gollancz SF",
        "Orbit Classics",
    }, edges
    assert _sql_touching(captured, "library_edition") != [], captured.captured_queries


@pytest.mark.django_db
def test_patron_profile_favorite_genre_id_still_reads_the_genre_table() -> None:
    """A ``to_field`` key cannot answer ``favoriteGenre { id }`` from the source row.

    ``PatronProfile.favorite_genre`` is declared ``to_field="name"``, so the
    stored column carries the genre's NAME, not its primary key; the id a client
    receives is built from the genre's own key and the genre row has to be read.
    """
    _seed_two_patron_profiles()
    genre = models.Genre.objects.get(name="Speculative")

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPatronProfilesConnection {
                edges { node { favoriteGenre { id } } }
              }
            }
            """,
        )

    edges = json_list(data, "allLibraryPatronProfilesConnection", "edges")
    assert [json_at(edge, "node", "favoriteGenre") for edge in edges] == [
        {"id": global_id_for(library_schema.GenreType, genre.pk)},
        None,
    ], edges
    assert _sql_touching(captured, "library_genre") != [], captured.captured_queries


@pytest.mark.django_db
def test_edition_publisher_id_still_reads_the_publisher_table_for_its_node_id() -> None:
    """A custom ``relay.NodeID`` moves the id payload off the stored key column.

    ``PublisherType`` declares ``house_code: relay.NodeID[str]``, so the id a
    client receives is built from a column ``edition.publisher_id`` does not
    carry: the relation keeps its read of ``library_publisher``, and the id
    decodes to the house code rather than to the publisher's primary key.
    """
    first, _second = _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success("{ allLibraryEditions { publisher { id } } }")

    ids = [json_at(row, "publisher", "id") for row in json_list(data, "allLibraryEditions")]
    assert ids[0] == global_id_for(library_schema.PublisherType, first.house_code), ids
    target_type, node_id = decode_global_id(ids[0])
    assert target_type is library_schema.PublisherType, target_type
    assert node_id == first.house_code, node_id
    assert node_id != str(first.pk), node_id
    assert _sql_touching(captured, "library_publisher") != [], captured.captured_queries


@pytest.mark.django_db
def test_publisher_printings_2_connection_pages_from_one_partitioned_window() -> None:
    """The ``<word>_<digit>`` reverse accessor pages off ONE window statement.

    ``Publisher.printings_2`` publishes as ``printings2Connection``; the nested
    planner resolves the accessor to the ``printings_2`` relation over the
    ``publisher_2_id`` column and plans a single ``ROW_NUMBER() OVER (PARTITION
    BY ...)`` fetch for both parents. Two publishers are seeded because one
    parent collapses to a plain filtered ``LIMIT`` on the single-parent fast
    path, which would carry no window at all.
    """
    _seed_publishing_graph()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPublishersConnection {
                edges {
                  node {
                    name
                    printings2Connection(first: 2) {
                      edges { node { runSize } }
                      pageInfo { hasNextPage }
                    }
                  }
                }
              }
            }
            """,
        )

    nodes = [
        json_object(edge, "node")
        for edge in json_list(data, "allLibraryPublishersConnection", "edges")
    ]
    assert [node["name"] for node in nodes] == ["Gollancz", "Orbit"], nodes
    pages = [
        (
            [
                json_at(edge, "node", "runSize")
                for edge in json_list(node, "printings2Connection", "edges")
            ],
            json_at(node, "printings2Connection", "pageInfo", "hasNextPage"),
        )
        for node in nodes
    ]
    assert pages == [([100, 200], True), ([400, 500], False)], pages
    printing_sql = _sql_from_table(captured, "library_printing")
    assert len(printing_sql) == 1, printing_sql
    windowed = printing_sql[0].upper()
    assert "ROW_NUMBER() OVER (" in windowed, printing_sql[0]
    assert "PARTITION BY" in windowed, printing_sql[0]
    assert "PUBLISHER_2_ID" in windowed, printing_sql[0]


@pytest.mark.django_db
def test_patron_profile_annotations_connection_is_left_unplanned_and_fetched_per_parent() -> None:
    """A distinct default manager leaves the whole nested relation unplanned.

    ``AnnotationManager.get_queryset`` returns ``.distinct()``, which
    ``optimizer/nested_fetch.py::unwindowable_child_queryset_reason`` classifies
    as unwindowable: SQL evaluates window functions before ``DISTINCT``, so the
    planner refuses the relation outright rather than emit an over-counted
    window. Observably that is no ``OVER (`` anywhere in the annotation SQL and
    one ``library_annotation`` statement per parent - with the pages still
    correct, which is what makes the refusal a fallback rather than a hole.
    """
    first, second = _seed_two_patron_profiles()
    for body in ("first note", "second note", "third note"):
        models.Annotation.objects.create(profile=first, body=body)
    models.Annotation.objects.create(profile=second, body="only note")

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryPatronProfilesConnection {
                edges {
                  node {
                    annotationsConnection(first: 2) {
                      edges { node { body } }
                      pageInfo { hasNextPage }
                    }
                  }
                }
              }
            }
            """,
        )

    nodes = [
        json_object(edge, "node")
        for edge in json_list(data, "allLibraryPatronProfilesConnection", "edges")
    ]
    pages = [
        (
            [
                json_at(edge, "node", "body")
                for edge in json_list(node, "annotationsConnection", "edges")
            ],
            json_at(node, "annotationsConnection", "pageInfo", "hasNextPage"),
        )
        for node in nodes
    ]
    assert pages == [(["first note", "second note"], True), (["only note"], False)], pages
    annotation_sql = _sql_from_table(captured, "library_annotation")
    assert len(annotation_sql) == len(nodes), annotation_sql
    assert not any("OVER (" in sql.upper() for sql in annotation_sql), annotation_sql


def _seed_distributors(count: int) -> list[models.Distributor]:
    """``count`` distributors with one consignment each, both numbered from zero."""
    distributors: list[models.Distributor] = []
    for index in range(count):
        distributor = models.Distributor.objects.create(displayName=f"Distributor {index}")
        models.Consignment.objects.create(label=f"Consignment {index}", distributorRef=distributor)
        distributors.append(distributor)
    return distributors


@pytest.mark.django_db
def test_distributor_mixed_case_scalar_projects_its_own_column() -> None:
    """``displayName`` is served by one statement projecting the ``displayName`` column.

    Strawberry publishes the Django name unchanged; reversing it gives
    ``display_name``, which names no field, so the selection resolves by its exact
    published name and the root projection carries the real column.
    """
    distributors = _seed_distributors(2)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success("{ allLibraryDistributors { id displayName } }")

    assert sorted(
        json_list(data, "allLibraryDistributors"),
        key=lambda row: json_int(row, "id"),
    ) == [
        {"id": distributor.pk, "displayName": distributor.displayName}
        for distributor in distributors
    ], data
    distributor_sql = _sql_touching(captured, "library_distributor")
    assert len(distributor_sql) == 1, captured.captured_queries
    assert '"displayName"' in distributor_sql[0], distributor_sql[0]


@pytest.mark.parametrize("distributor_count", [1, 3])
@pytest.mark.django_db
def test_consignment_mixed_case_forward_key_joins_its_target_in_one_statement(
    distributor_count: int,
) -> None:
    """``distributorRef { displayName }`` is one ``JOIN`` at every parent cardinality.

    ``distributorRef`` reverses to ``distributor_ref``, which names no relation;
    resolved by its published name, the key plans a ``select_related`` whose
    joined projection carries the target's mixed-case ``displayName`` column.
    """
    _seed_distributors(distributor_count)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryConsignments { label distributorRef { displayName } } }",
        )

    assert sorted(
        (json_str(row, "label"), json_str(row, "distributorRef", "displayName"))
        for row in json_list(data, "allLibraryConsignments")
    ) == [(f"Consignment {index}", f"Distributor {index}") for index in range(distributor_count)]
    distributor_sql = _sql_touching(captured, "library_distributor")
    assert len(distributor_sql) == 1, captured.captured_queries
    assert _sql_from_table(captured, "library_consignment") == distributor_sql
    assert 'JOIN "library_distributor"' in distributor_sql[0], distributor_sql[0]
    assert '"displayName"' in distributor_sql[0], distributor_sql[0]


@pytest.mark.parametrize("distributor_count", [1, 3])
@pytest.mark.django_db
def test_distributor_mixed_case_reverse_relation_loads_through_one_prefetch(
    distributor_count: int,
) -> None:
    """``consignmentItems`` loads every parent's rows in one statement at every cardinality.

    The ``related_name`` ``consignmentItems`` reverses to ``consignment_items``,
    which names no relation; resolved by its published name it plans one prefetch
    filtered on the mixed-case ``distributorRef_id`` column.
    """
    _seed_distributors(distributor_count)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryDistributors { displayName consignmentItems { label } } }",
        )

    assert sorted(
        (
            json_str(row, "displayName"),
            [json_str(item, "label") for item in json_list(row, "consignmentItems")],
        )
        for row in json_list(data, "allLibraryDistributors")
    ) == [(f"Distributor {index}", [f"Consignment {index}"]) for index in range(distributor_count)]
    assert len(_sql_from_table(captured, "library_distributor")) == 1, captured.captured_queries
    consignment_sql = _sql_from_table(captured, "library_consignment")
    assert len(consignment_sql) == 1, captured.captured_queries
    assert '"distributorRef_id" IN (' in consignment_sql[0], consignment_sql[0]


def _seed_reading_lists() -> tuple[models.ReadingList, models.ReadingList]:
    """Two reading lists, each with entries added out of alphabetical order."""
    classics = models.ReadingList.objects.create(title="Classics")
    anthology = models.ReadingList.objects.create(title="Anthology")
    for title in ("Solaris", "Dune", "Anathem"):
        models.ReadingListEntry.objects.create(reading_list=classics, title=title)
    models.ReadingListEntry.objects.create(reading_list=anthology, title="Kindred")
    return classics, anthology


@pytest.mark.django_db
def test_reading_list_entries_connection_pages_in_primary_key_order_with_ordering_none() -> None:
    """A root connection over an ``ordering = None`` model pages in primary-key order.

    ``ReadingListEntry`` clears its abstract parent's ``Meta.ordering`` with
    ``None``, which Django accepts and treats as no default order. With no
    ``orderBy:`` and no ``Meta.cursor_field`` the connection's total order is the
    pk tiebreaker alone: the entries come back in insertion order, not by title.
    """
    _seed_reading_lists()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryReadingListEntriesConnection(first: 3) {
                edges { node { title } }
                pageInfo { hasNextPage }
              }
            }
            """,
        )

    page = data["allLibraryReadingListEntriesConnection"]
    assert [json_at(edge, "node", "title") for edge in json_list(page, "edges")] == [
        "Solaris",
        "Dune",
        "Anathem",
    ], page
    assert json_at(page, "pageInfo", "hasNextPage") is True, page
    entry_sql = _sql_from_table(captured, "library_readinglistentry")
    assert len(entry_sql) == 1, captured.captured_queries
    assert 'ORDER BY "library_readinglistentry"."id" ASC' in entry_sql[0], entry_sql[0]


@pytest.mark.django_db
def test_reading_list_entries_nested_connection_windows_in_primary_key_order() -> None:
    """The nested window over an ``ordering = None`` child orders each partition by pk.

    Two parents so the nested planner builds its ``ROW_NUMBER() OVER (PARTITION
    BY ...)`` window rather than the single-parent fast path. The child model
    brings no default order, so the window orders by the pk tiebreaker alone;
    the parent ``ReadingList`` keeps the ``title`` order it inherits, which is
    why "Anthology" leads.
    """
    _seed_reading_lists()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryReadingListsConnection {
                edges {
                  node {
                    title
                    entriesConnection(first: 2) {
                      edges { node { title } }
                      pageInfo { hasNextPage }
                    }
                  }
                }
              }
            }
            """,
        )

    nodes = [
        json_object(edge, "node")
        for edge in json_list(data, "allLibraryReadingListsConnection", "edges")
    ]
    pages = [
        (
            node["title"],
            [
                json_at(edge, "node", "title")
                for edge in json_list(node, "entriesConnection", "edges")
            ],
            json_at(node, "entriesConnection", "pageInfo", "hasNextPage"),
        )
        for node in nodes
    ]
    assert pages == [
        ("Anthology", ["Kindred"], False),
        ("Classics", ["Solaris", "Dune"], True),
    ], pages
    entry_sql = _sql_from_table(captured, "library_readinglistentry")
    assert len(entry_sql) == 1, entry_sql
    windowed = entry_sql[0].upper()
    assert "ROW_NUMBER() OVER (" in windowed, entry_sql[0]
    assert "PARTITION BY" in windowed, entry_sql[0]
    assert 'ORDER BY "LIBRARY_READINGLISTENTRY"."ID" ASC' in windowed, entry_sql[0]


@pytest.mark.django_db
def test_reading_lists_connection_honors_a_cleared_default_ordering() -> None:
    """A source whose ``.order_by()`` cleared ``Meta.ordering`` pages in primary-key order.

    Django compiles no ``Meta.ordering`` once ``query.default_ordering`` is off,
    so the connection's total order is the pk tiebreaker alone: "Classics"
    (created first) leads, where the same model's plain connection leads with
    "Anthology" under the inherited title order.
    """
    _seed_reading_lists()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryReadingListsUnorderedConnection {
                edges { node { title } }
              }
            }
            """,
        )

    titles = [
        json_at(edge, "node", "title")
        for edge in json_list(data, "allLibraryReadingListsUnorderedConnection", "edges")
    ]
    assert titles == ["Classics", "Anthology"], titles
    list_sql = _sql_from_table(captured, "library_readinglist")
    assert len(list_sql) == 1, captured.captured_queries
    assert 'ORDER BY "library_readinglist"."id" ASC' in list_sql[0], list_sql[0]
    assert '"library_readinglist"."title" ASC' not in list_sql[0], list_sql[0]


#: Each genre's ``booksConnection`` page under one window shape, with every edge cursor
#: and the full ``pageInfo``: the page STRUCTURE, which no total order changes.
_SHUFFLED_BOOKS_QUERY = """
query {
  allLibraryGenresConnection {
    edges {
      node {
        name
        booksConnection(%s) {
          edges { cursor node { title } }
          pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
        }
      }
    }
  }
}
"""

#: The four window shapes a nested page is planned under: forward, reversed, and each
#: bounded by a cursor.
_SHUFFLED_BOOKS_WINDOWS = {
    "first": "first: 2",
    "last": "last: 2",
    "first-after": f'first: 2, after: "{to_base64("arrayconnection", 0)}"',
    "last-before": f'last: 2, before: "{to_base64("arrayconnection", 3)}"',
}

_BookShuffle = Callable[[QuerySet[models.Book]], QuerySet[models.Book]]

#: A hook-side random order per row: ``"?"`` and the ``Random()`` expression, each
#: directly and reversed; ``Random()`` under a composition; ``Random()`` behind an
#: annotation alias - by name, descending, through a transform, under a name holding
#: ``__``, and through an ``F``; and a ``When`` condition reading ``Random()`` - through
#: a lookup on an alias, a ``Q`` combination, a negated ``Q`` beside a plain lookup, a
#: lookup value, and an alias of the ``Case``.
_RANDOM_BOOK_HOOK_ORDERS: dict[str, _BookShuffle] = {
    "hook-name": lambda books: books.order_by("?"),
    "hook-expression": lambda books: books.order_by(Random()),
    "hook-reversed-name": lambda books: books.order_by("?").reverse(),
    "hook-reversed-expression": lambda books: books.order_by(Random()).reverse(),
    "hook-composition": lambda books: books.order_by((Random() + Value(0.0)).asc()),
    "hook-alias": lambda books: books.annotate(shuffle=Random()).order_by("shuffle"),
    "hook-alias-descending": lambda books: books.annotate(shuffle=Random()).order_by(
        "-shuffle",
    ),
    "hook-alias-transform": lambda books: books.annotate(shuffle=Random()).order_by(
        "shuffle__abs",
    ),
    "hook-alias-transform-descending": lambda books: books.annotate(
        shuffle=Random(),
    ).order_by("-shuffle__abs"),
    "hook-alias-dunder": lambda books: books.annotate(shuffle__x=Random()).order_by(
        "shuffle__x",
    ),
    "hook-condition": lambda books: books.annotate(coin=Random()).order_by(
        Case(When(coin__gt=0.5, then=Value(1)), default=Value(0)).asc(),
    ),
    "hook-condition-q": lambda books: books.annotate(coin=Random()).order_by(
        Case(When(Q(coin__gt=0.7) | Q(coin__lt=0.3), then=Value(1)), default=Value(0)),
    ),
    "hook-condition-negated": lambda books: books.annotate(coin=Random()).order_by(
        Case(When(Q(title__gt="") & ~Q(coin__lt=0.3), then=Value(1)), default=Value(0)),
    ),
    "hook-condition-value": lambda books: books.order_by(
        Case(When(id__gt=Random() * 1000, then=Value(1)), default=Value(0)),
    ),
    "hook-condition-alias": lambda books: books.annotate(
        coin=Random(),
        heads=Case(When(coin__gt=0.5, then=Value(1)), default=Value(0)),
    ).order_by("heads"),
    "hook-reference": lambda books: books.annotate(shuffle=Random()).order_by(F("shuffle")),
    "hook-reference-descending": lambda books: books.annotate(shuffle=Random()).order_by(
        F("shuffle").desc(),
    ),
}

#: A ``Meta.ordering`` random order per row: the ``"?"`` name, the expression, and the
#: expression wrapped in a direction.
_RANDOM_BOOK_META_ORDERS: dict[str, tuple[object, ...]] = {
    "meta-name": ("?",),
    "meta-expression": (Random(),),
    "meta-composition": (Random().desc(),),
}

#: A book order naming the ``shelf`` relation under a random ``Shelf.Meta.ordering``,
#: which the compiler orders it by: from the hook, and from ``Book.Meta.ordering``.
_RANDOM_SHELF_BOOK_ORDERS: dict[str, _BookShuffle | tuple[object, ...]] = {
    "related-hook": lambda books: books.order_by("shelf"),
    "related-meta": ("shelf",),
}

#: Every random order row above, by its id.
_RANDOM_BOOK_ORDERS: dict[str, _BookShuffle | tuple[object, ...]] = {
    **_RANDOM_BOOK_HOOK_ORDERS,
    **_RANDOM_BOOK_META_ORDERS,
    **_RANDOM_SHELF_BOOK_ORDERS,
}


def _seed_shuffled_genres() -> dict[str, set[str]]:
    """Three genres holding five, one and no books; returns each genre's titles."""
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="Fiction", branch=branch)
    shelved = {"Speculative": 5, "Poetry": 1, "Empty": 0}
    titles: dict[str, set[str]] = {}
    for name, count in shelved.items():
        genre = models.Genre.objects.create(name=name)
        titles[name] = {f"{name} {index}" for index in range(count)}
        for title in sorted(titles[name]):
            genre.books.add(models.Book.objects.create(title=title, shelf=shelf))
    return titles


def _shuffled_books_pages(window: str) -> tuple[dict[str, JSONObject], list[str]]:
    """Each genre's ``booksConnection`` page under ``window``, and the ``library_book`` SQL."""
    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(_SHUFFLED_BOOKS_QUERY % _SHUFFLED_BOOKS_WINDOWS[window])
    pages = {
        json_str(edge, "node", "name"): json_object(edge, "node", "booksConnection")
        for edge in json_list(data, "allLibraryGenresConnection", "edges")
    }
    return pages, _sql_from_table(captured, "library_book")


def _page_structure(page: JSONObject) -> tuple[list[str], JSONObject]:
    """The order-independent half of a page: its edge cursors and its ``pageInfo``."""
    return [json_str(edge, "cursor") for edge in json_list(page, "edges")], json_object(
        page,
        "pageInfo",
    )


def _order_books_by(
    monkeypatch: pytest.MonkeyPatch,
    order: _BookShuffle | tuple[object, ...],
) -> None:
    """Order ``BookType``'s queryset through its hook, or set ``Book.Meta.ordering`` to a tuple."""
    if isinstance(order, tuple):
        monkeypatch.setattr(models.Book._meta, "ordering", order)
        return
    shipped_hook = library_schema.BookType.get_queryset

    def ordered_hook(
        _cls: type[library_schema.BookType],
        queryset: QuerySet[models.Book],
        info: strawberry.Info[object, object],
    ) -> QuerySet[models.Book]:
        return order(shipped_hook(queryset, info))

    monkeypatch.setattr(library_schema.BookType, "get_queryset", classmethod(ordered_hook))


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("source", list(_RANDOM_BOOK_ORDERS))
@pytest.mark.django_db
def test_random_book_order_leaves_genre_books_connection_to_the_per_parent_pipeline(
    source: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A random child order is served per parent, one random draw per page.

    The nested window evaluates its order more than once in one statement - the
    row-number window, the reversed window of a ``last:`` page and the outer
    ``ORDER BY`` - and a random term is a new draw at each, while a bare ``"?"``
    cannot be a window order term at all. So ``booksConnection`` is left unplanned
    under every spelling: one ``library_book`` statement per genre (three), none a
    window, each ordering by the database's random function. Every page is then a
    slice of ONE permutation, so its edge cursors and ``pageInfo`` are exactly the
    ones the shipped primary-key order serves through its window first (one
    windowed statement), and its titles are distinct books of that genre. A
    ``shelf`` name under a random ``Shelf.Meta.ordering`` is the same order:
    Django orders the name by that ordering.
    """
    titles = _seed_shuffled_genres()
    planned, planned_sql = _shuffled_books_pages(window)
    assert [len(planned_sql), "OVER (" in planned_sql[0]] == [1, True], planned_sql

    if source in _RANDOM_SHELF_BOOK_ORDERS:
        monkeypatch.setattr(models.Shelf._meta, "ordering", (Random(),))
    _order_books_by(monkeypatch, _RANDOM_BOOK_ORDERS[source])
    # The transform rows order through ``abs``, which Django registers on no field by default.
    with register_lookup(FloatField, Abs):
        shuffled, shuffled_sql = _shuffled_books_pages(window)

    assert len(shuffled_sql) == len(titles), shuffled_sql
    assert [("OVER (" in sql, "RAND" in sql.upper()) for sql in shuffled_sql] == [
        (False, True),
    ] * len(titles), shuffled_sql
    for name, genre_titles in titles.items():
        served = [json_at(edge, "node", "title") for edge in json_list(shuffled[name], "edges")]
        assert len(set(served)) == len(served), (name, served)
        assert set(served) <= genre_titles, (name, served)
        assert _page_structure(shuffled[name]) == _page_structure(planned[name]), name


#: A ``When`` condition comparing a column to a string literal spelled like a random
#: order: ``"?"``, and the name of a random annotation. A condition reads a reference
#: only through ``F``, so neither literal is random.
_LITERAL_CONDITION_BOOK_ORDERS: dict[str, _BookShuffle] = {
    "question-mark": lambda books: books.order_by(
        Case(When(title="?", then=Value(1)), default=Value(0)),
        "pk",
    ),
    "annotation-name": lambda books: books.annotate(shuffle=Random()).order_by(
        Case(When(title="shuffle", then=Value(1)), default=Value(0)),
        "pk",
    ),
}


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("source", list(_LITERAL_CONDITION_BOOK_ORDERS))
@pytest.mark.django_db
def test_string_literal_in_a_book_order_condition_keeps_genre_books_connection_windowed(
    source: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A condition's string literal is no random term: the nested window still plans.

    Every book's condition answers the default, so the order is the primary key
    and each genre's page, cursors and ``pageInfo`` equal the shipped order's,
    served from one windowed ``library_book`` statement.
    """
    _seed_shuffled_genres()
    planned, _ = _shuffled_books_pages(window)
    order = _LITERAL_CONDITION_BOOK_ORDERS[source]
    shipped_hook = library_schema.BookType.get_queryset

    def literal_hook(
        _cls: type[library_schema.BookType],
        queryset: QuerySet[models.Book],
        info: strawberry.Info[object, object],
    ) -> QuerySet[models.Book]:
        return order(shipped_hook(queryset, info))

    monkeypatch.setattr(library_schema.BookType, "get_queryset", classmethod(literal_hook))
    served, served_sql = _shuffled_books_pages(window)

    assert [len(served_sql), "OVER (" in served_sql[0]] == [1, True], served_sql
    assert served == planned


#: Opens the error policy's pass-through gate so a refused order's ``FieldError`` reaches
#: the wire; the toolbar middleware is dropped because ``config.urls`` computed its
#: ``djdt`` routes under the ambient ``DEBUG=False``.
_ERROR_POLICY_PASS_THROUGH = {"DEBUG": True, "MIDDLEWARE": middleware_without_debug_toolbar()}

_MOUNTED: dict[str, strawberry.Schema | None] = {"schema": None}


def _mounted_view(request: HttpRequest) -> HttpResponseBase:
    schema = _MOUNTED["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _mounted_view)]


def _post(query: str, *, schema: strawberry.Schema | None = None) -> JSONObject:
    """Post ``query`` and return the envelope, optimized or not.

    With no ``schema`` it posts to the shipped ``/graphql/``, whose schema carries the
    project's ``DjangoOptimizerExtension``; otherwise ``schema`` is mounted at
    ``/graphql-test/`` for the one request.
    """
    if schema is None:
        with override_settings(**_ERROR_POLICY_PASS_THROUGH):
            return graphql_payload(query)
    _MOUNTED["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__, **_ERROR_POLICY_PASS_THROUGH):
            clear_url_caches()
            return graphql_payload(query, url="/graphql-test/")
    finally:
        _MOUNTED["schema"] = None
        clear_url_caches()


def _unoptimized_library_schema() -> DjangoSchema:
    """The library app's own ``Query`` with no extension: every relation resolves per parent."""
    return DjangoSchema(query=library_schema.Query, config=strawberry_config())


def _hold(
    child_model: type[Model],
    child_fields: tuple[str, ...],
    parent_model: type[Model],
    relation: str,
    order: tuple[str, ...],
) -> tuple[strawberry.Schema, strawberry.Schema]:
    """A ``parents`` list over ``parent_model`` whose ``relation`` is a connection, optimized and not.

    The child type's ``get_queryset`` orders by ``order``; ``parents`` lists every parent
    by name, and ``children`` is the root connection over the child type.
    """

    def hook(
        _cls: type[DjangoType],
        queryset: QuerySet[Model],
        _info: strawberry.Info[object, object],
    ) -> QuerySet[Model]:
        return queryset.order_by(*order)

    registry.clear()
    child_type = make_django_type(
        "HeldChildType",
        child_model,
        child_fields,
        namespace_extra={"get_queryset": classmethod(hook)},
    )
    parent_type = make_django_type(
        "HeldParentType",
        parent_model,
        ("id", "name", relation),
        meta_extra={"relation_shapes": {relation: "connection"}},
    )
    finalize_django_types()

    @strawberry.type
    class Query:
        children = DjangoConnectionField(child_type)

        # basedpyright: strawberry.field's no-resolver overload (the decorator factory) returns Any
        @strawberry.field(graphql_type=list[parent_type])  # pyright: ignore[reportAny]
        def parents(self) -> QuerySet[Model]:
            return parent_model._default_manager.order_by("name")

    optimizer = DjangoOptimizerExtension()
    optimized = strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    return optimized, strawberry.Schema(query=Query, config=strawberry_config())


def _seed_shelved_genres() -> None:
    """Two genres of five books each over four shelves whose codes run against their ids.

    By id the shelves are ``B`` (South), ``D`` (North), ``A`` (North), ``C`` (South), so
    ``-code``, ``Lower("code")``, ``-pk`` and ``branch`` (South first) then ``-code``
    each order them differently from their ids and from each other. Books are
    shelved out of id order, the two genres' books interleave, two books sit on one
    shelf in each genre (the primary key breaks that tie) and one book is in both.
    """
    north = models.Branch.objects.create(name="North")
    south = models.Branch.objects.create(name="South")
    shelves = [
        models.Shelf.objects.create(code=code, branch=branch)
        for code, branch in (
            ("B", south),
            ("D", north),
            ("A", north),
            ("C", south),
        )
    ]
    fiction = models.Genre.objects.create(name="Fiction")
    history = models.Genre.objects.create(name="History")
    for index, shelf_index in enumerate(
        (
            2,
            0,
            3,
            1,
            0,
            2,
            1,
            3,
            3,
        ),
    ):
        book = models.Book.objects.create(title=f"Book {index}", shelf=shelves[shelf_index])
        book.genres.add(history if index % 2 else fiction)
    history.books.add(models.Book.objects.get(title="Book 0"))


def _genre_books_pages(
    window: str,
    *,
    schema: strawberry.Schema | None = None,
) -> tuple[dict[str, JSONObject], list[str]]:
    """Each genre's ``booksConnection`` page under ``window``, and every SQL statement run."""
    with CaptureQueriesContext(connection) as captured:
        payload = _post(_SHUFFLED_BOOKS_QUERY % _SHUFFLED_BOOKS_WINDOWS[window], schema=schema)
    assert "errors" not in payload, payload
    pages = {
        json_str(edge, "node", "name"): json_object(edge, "node", "booksConnection")
        for edge in json_list(payload, "data", "allLibraryGenresConnection", "edges")
    }
    return pages, [entry["sql"] for entry in captured.captured_queries]


#: A book order naming the ``shelf`` relation: from the hook ascending, descending and
#: reversed, and from ``Book.Meta.ordering``.
_SHELF_NAME_BOOK_ORDERS: dict[str, _BookShuffle | tuple[object, ...]] = {
    "hook": lambda books: books.order_by("shelf"),
    "hook-descending": lambda books: books.order_by("-shelf"),
    "hook-reversed": lambda books: books.order_by("shelf").reverse(),
    "meta": ("shelf",),
}

#: The ``Shelf.Meta.ordering`` a ``shelf`` name compiles into, and the ``Branch`` one a
#: nested ``branch`` name compiles into: a descending name, an ``OrderBy`` with its own
#: direction and nulls placement, a bare expression, the primary key, and a relation
#: name expanding again.
_SHELF_ORDERINGS: dict[str, tuple[tuple[object, ...], tuple[object, ...] | None]] = {
    "name": (("-code",), None),
    "order-by": ((F("code").desc(nulls_last=True),), None),
    "expression": ((Lower("code"),), None),
    "pk": (("-pk",), None),
    "relation": (("branch", "-code"), ("-name",)),
}


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("shelf_ordering", list(_SHELF_ORDERINGS))
@pytest.mark.parametrize("source", list(_SHELF_NAME_BOOK_ORDERS))
@pytest.mark.django_db
def test_relation_name_book_order_pages_genre_books_connection_like_the_pipeline(
    source: str,
    shelf_ordering: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A book order naming ``shelf`` pages through the window as the per-parent pipeline pages it.

    Django orders a relation NAME by the related model's ``Meta.ordering`` (the
    compiler's ``find_ordering_name``), which a window cannot read off the name
    itself. Under every spelling of the name, every shelf ordering and every page
    window, the optimized request still plans ``booksConnection`` as one
    ``ROW_NUMBER`` statement beside the genre page (two statements in all) and
    serves each genre exactly the titles, edge cursors and ``pageInfo`` the
    library schema serves with no optimizer.
    """
    _seed_shelved_genres()
    shelves, branches = _SHELF_ORDERINGS[shelf_ordering]
    monkeypatch.setattr(models.Shelf._meta, "ordering", shelves)
    if branches is not None:
        monkeypatch.setattr(models.Branch._meta, "ordering", branches)
    _order_books_by(monkeypatch, _SHELF_NAME_BOOK_ORDERS[source])

    optimized, optimized_sql = _genre_books_pages(window)
    unoptimized, _ = _genre_books_pages(window, schema=_unoptimized_library_schema())

    assert len(optimized_sql) == 2, optimized_sql
    assert ["ROW_NUMBER" in sql.upper() for sql in optimized_sql] == [False, True], optimized_sql
    assert optimized == unoptimized


#: A book order through the hook's ``extra(order_by=...)``, each total by itself so
#: Django's own compile of the hook queryset is the order every page is cut from: a
#: descending field, the book's own ``table.column``, its foreign key's raw column, a
#: column of the shelf table the hook joins through a filter, and a quoted table name.
_EXTRA_BOOK_HOOK_ORDERS: dict[str, _BookShuffle] = {
    "field": lambda books: books.extra(order_by=["-title"]),
    "table-column": lambda books: books.extra(order_by=["-library_book.title"]),
    "foreign-key": lambda books: books.extra(order_by=["library_book.shelf_id", "-title"]),
    "joined-table": lambda books: books.filter(shelf__code__gte="").extra(
        order_by=["library_shelf.code", "-title"],
    ),
    "quoted-table": lambda books: books.extra(order_by=['-"library_book".title']),
}


def _reversed_book_order(order: _BookShuffle) -> _BookShuffle:
    """``order`` with the hook's ``.reverse()`` after it."""
    return lambda books: order(books).reverse()


#: Each ``extra`` book order as written and ``.reverse()``'d.
_EXTRA_BOOK_ORDERS: dict[str, _BookShuffle] = {
    **_EXTRA_BOOK_HOOK_ORDERS,
    **{
        f"{name}-reversed": _reversed_book_order(order)
        for name, order in _EXTRA_BOOK_HOOK_ORDERS.items()
    },
}

#: The rows of a genre's whole order each window shape serves.
_SHUFFLED_BOOKS_SLICES = {
    "first": slice(0, 2),
    "last": slice(-2, None),
    "first-after": slice(1, 3),
    "last-before": slice(1, 3),
}


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("source", list(_EXTRA_BOOK_ORDERS))
@pytest.mark.django_db
def test_extra_book_order_pages_genre_books_connection_like_the_pipeline(
    source: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hook's ``extra`` book order pages through the window as the pipeline and Django order it.

    Django compiles an ``extra(order_by=...)`` ordering in place of every other
    one. Under every spelling, reversed or not, and every page window, the
    optimized request plans ``booksConnection`` as one ``ROW_NUMBER`` statement
    beside the genre page, serves each genre the page the library schema serves
    with no optimizer, and that page is cut from the order Django compiles for
    the hook queryset itself.
    """
    _seed_shelved_genres()
    order = _EXTRA_BOOK_ORDERS[source]
    _order_books_by(monkeypatch, order)

    optimized, optimized_sql = _genre_books_pages(window)
    unoptimized, _ = _genre_books_pages(window, schema=_unoptimized_library_schema())

    assert len(optimized_sql) == 2, optimized_sql
    assert ["ROW_NUMBER" in sql.upper() for sql in optimized_sql] == [False, True], optimized_sql
    assert optimized == unoptimized
    rows = _SHUFFLED_BOOKS_SLICES[window]
    assert {
        name: [json_str(edge, "node", "title") for edge in json_list(page, "edges")]
        for name, page in optimized.items()
    } == {
        genre.name: [book.title for book in order(genre.books.all())][rows]
        for genre in models.Genre.objects.all()
    }


#: A ``Shelf.Meta.ordering`` (and the ``Branch.Meta.ordering`` it reaches) that Django
#: cannot expand a ``shelf`` name into, with the start of the error it raises: a related
#: ``"?"``, an ordering loop between the two models, and a condition, which is no order
#: expression.
_UNEXPANDABLE_SHELF_ORDERINGS: dict[
    str,
    tuple[tuple[object, ...], tuple[str, ...] | None, str],
] = {
    "random-name": (("?",), None, "Cannot resolve keyword '?' into field."),
    "loop": (("branch",), ("shelves",), "Infinite loop caused by ordering."),
    "condition": ((Q(code="A"),), None, "'Q' object has no attribute"),
}


@pytest.mark.parametrize("shelf_ordering", list(_UNEXPANDABLE_SHELF_ORDERINGS))
@pytest.mark.parametrize("source", list(_SHELF_NAME_BOOK_ORDERS))
@pytest.mark.django_db
def test_unexpandable_relation_name_book_order_raises_djangos_error_with_and_without_optimizer(
    source: str,
    shelf_ordering: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``shelf`` name Django cannot expand raises Django's own error whether the window plans it or not.

    The window keeps such a term as written, so the statement compiling it raises
    the ``FieldError`` the per-parent pipeline raises: the optimized request fails
    where its window statement runs (the genre page that fetches it) and the
    unoptimized one at each genre's ``booksConnection``, both with Django's message
    (an unresolvable name lists the field choices of the statement it compiled in,
    and a condition fails on the direction method the order asked for).
    """
    _seed_shelved_genres()
    shelves, branches, message = _UNEXPANDABLE_SHELF_ORDERINGS[shelf_ordering]
    monkeypatch.setattr(models.Shelf._meta, "ordering", shelves)
    if branches is not None:
        monkeypatch.setattr(models.Branch._meta, "ordering", branches)
    _order_books_by(monkeypatch, _SHELF_NAME_BOOK_ORDERS[source])
    query = _SHUFFLED_BOOKS_QUERY % _SHUFFLED_BOOKS_WINDOWS["first"]

    optimized = _post(query)
    unoptimized = _post(query, schema=_unoptimized_library_schema())

    raised = [
        {
            json_str(error, "message").split(" Choices are:")[0]
            for error in json_list(payload, "errors")
        }
        for payload in (optimized, unoptimized)
    ]
    assert raised[0] == raised[1], raised
    assert [head.startswith(message) for head in raised[0]] == [True], raised


#: Each held parent's nested connection under one window shape, with every edge cursor
#: and the full ``pageInfo``; ``%s`` is the relation's field name, then the window.
_HELD_QUERY = """
query {
  parents {
    name
    %s(%s) {
      edges { cursor node { %s } }
      pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
    }
  }
}
"""


def _held_pages(
    schema: strawberry.Schema,
    relation: str,
    window: str,
    label: str,
) -> tuple[dict[str, JSONObject], list[str]]:
    """Each held parent's ``relation`` page under ``window``, and every SQL statement run."""
    query = _HELD_QUERY % (relation, _SHUFFLED_BOOKS_WINDOWS[window], label)
    with CaptureQueriesContext(connection) as captured:
        payload = _post(query, schema=schema)
    assert "errors" not in payload, payload
    pages = {
        json_str(parent, "name"): json_object(parent, relation)
        for parent in json_list(payload, "data", "parents")
    }
    return pages, [entry["sql"] for entry in captured.captured_queries]


def _seed_profiles_sharing_emails() -> None:
    """Two genres favored by three patrons each, two of each genre's three sharing an email.

    By id the emails run ``b``, ``a``, ``b`` under ``Fiction`` and ``a``, ``c``, ``a``
    under ``History``, so an email order ties twice and only the primary key decides.
    """
    fiction = models.Genre.objects.create(name="Fiction")
    history = models.Genre.objects.create(name="History")
    seeded = (
        (fiction, "b@example.com"),
        (history, "a@example.com"),
        (fiction, "a@example.com"),
        (history, "c@example.com"),
        (fiction, "b@example.com"),
        (history, "a@example.com"),
    )
    for index, (genre, email) in enumerate(seeded):
        patron = models.Patron.objects.create(name=f"Patron {index}", email=email)
        models.PatronProfile.objects.create(
            patron=patron,
            postal_code=f"0000{index}",
            favorite_genre=genre,
        )


#: Each order a profile's ``get_queryset`` names for its one-to-one primary key under
#: ``Patron.Meta.ordering = ["email"]``: the root page and the ``ORDER BY`` it compiles
#: into. The NAME ``patron`` orders by the shared ``email``, made total by the key;
#: ``pk`` is never substituted, so it orders by the key column alone.
_PROFILE_KEY_ORDERS = {
    "patron": (
        ("patron",),
        [
            "00001",
            "00002",
            "00005",
            "00000",
        ],
        '"library_patron"."email" ASC, "library_patronprofile"."patron_id" ASC',
    ),
    "pk": (
        ("pk",),
        [
            "00000",
            "00001",
            "00002",
            "00003",
        ],
        '"library_patronprofile"."patron_id" ASC',
    ),
}


@pytest.mark.parametrize("key", list(_PROFILE_KEY_ORDERS))
@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.django_db
def test_one_to_one_key_name_order_is_made_total_and_pages_like_the_pipeline(
    window: str,
    key: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A profile order naming its one-to-one primary key gets the key as its tiebreaker.

    ``PatronProfile.patron`` is the profile's unique primary key, but Django orders
    the NAME ``patron`` by ``Patron.Meta.ordering`` (here the shared ``email``), so
    the key is appended as the tiebreaker on every path: the root ``children``
    connection, the window planning a genre's ``favoringProfilesConnection`` (two
    statements, one ``ROW_NUMBER``) and each per-parent statement without the
    optimizer, which serves exactly the optimized pages. ``pk`` names the same key
    but is never substituted, so it stays the key column on every path.
    """
    order, rows, compiled = _PROFILE_KEY_ORDERS[key]
    _seed_profiles_sharing_emails()
    monkeypatch.setattr(models.Patron._meta, "ordering", ["email"])
    optimized, unoptimized = _hold(
        models.PatronProfile,
        ("postal_code",),
        models.Genre,
        "favoring_profiles",
        order,
    )

    with CaptureQueriesContext(connection) as captured:
        root = _post("{ children(first: 4) { edges { node { postalCode } } } }", schema=optimized)
    planned, planned_sql = _held_pages(
        optimized,
        "favoringProfilesConnection",
        window,
        "postalCode",
    )
    served, served_sql = _held_pages(
        unoptimized,
        "favoringProfilesConnection",
        window,
        "postalCode",
    )

    assert [
        json_at(edge, "node", "postalCode")
        for edge in json_list(root, "data", "children", "edges")
    ] == rows
    order_by = f"ORDER BY {compiled}"
    assert [order_by in entry["sql"] for entry in captured.captured_queries] == [True]
    assert len(planned_sql) == 2, planned_sql
    assert ["ROW_NUMBER" in sql.upper() for sql in planned_sql] == [False, True], planned_sql
    assert order_by in planned_sql[1], planned_sql
    assert [order_by in sql for sql in served_sql[1:]] == [True, True], served_sql
    assert planned == served


#: Each publisher's ``printings2Connection`` page under one window shape, with every edge
#: cursor and the full ``pageInfo``.
_PRINTINGS_QUERY = """
query {
  allLibraryPublishersConnection {
    edges {
      node {
        name
        printings2Connection(%s) {
          edges { cursor node { runSize } }
          pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
        }
      }
    }
  }
}
"""


def _seed_jointly_issued_printings() -> None:
    """Two publishers' press runs over four editions, two of them with no second house.

    Each publisher's runs (``publisher_2``) cover every edition out of id order, one
    edition twice, so an order by the edition's second house ties on ``NULL`` and on
    the repeated edition, and only the primary key decides.
    """
    gollancz = models.Publisher.objects.create(name="Gollancz", house_code="HOUSE-G")
    orbit = models.Publisher.objects.create(name="Orbit", house_code="HOUSE-O")
    tor = models.Publisher.objects.create(name="Tor", house_code="HOUSE-T")
    editions = [
        models.Edition.objects.create(
            isbn_13=f"978000000000{index}",
            publisher=house,
            publisher_2=second,
        )
        for index, (house, second) in enumerate(
            (
                (gollancz, tor),
                (orbit, None),
                (gollancz, orbit),
                (tor, None),
            ),
        )
    ]
    for run_size, (publisher, edition) in enumerate(
        (
            (gollancz, 2),
            (orbit, 3),
            (gollancz, 0),
            (orbit, 1),
            (gollancz, 3),
            (orbit, 1),
            (gollancz, 1),
            (orbit, 0),
            (gollancz, 2),
            (orbit, 2),
        ),
    ):
        models.Printing.objects.create(
            edition=editions[edition],
            publisher_2=publisher,
            run_size=run_size,
        )


def _printings_pages(
    window: str,
    *,
    schema: strawberry.Schema | None = None,
) -> tuple[dict[str, JSONObject], list[str]]:
    """Each publisher's ``printings2Connection`` page under ``window``, and every SQL statement run."""
    with CaptureQueriesContext(connection) as captured:
        payload = _post(_PRINTINGS_QUERY % _SHUFFLED_BOOKS_WINDOWS[window], schema=schema)
    assert "errors" not in payload, payload
    pages = {
        json_str(edge, "node", "name"): json_object(edge, "node", "printings2Connection")
        for edge in json_list(payload, "data", "allLibraryPublishersConnection", "edges")
    }
    return pages, [entry["sql"] for entry in captured.captured_queries]


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.django_db
def test_nullable_relation_name_reached_through_a_relation_order_pages_like_the_pipeline(
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A printing order by ``edition`` reaching the nullable ``publisher_2`` pages as the pipeline does.

    ``Printing.Meta.ordering = ["edition"]`` compiles into ``Edition.Meta.ordering``
    (``publisher_2``, a nullable key) and on into ``Publisher.Meta.ordering``
    (``-name``), joined with a ``LEFT OUTER JOIN`` so an edition with no second house
    keeps its runs. Each publisher's ``printings2Connection`` is still one
    ``ROW_NUMBER`` statement beside the publisher page, serving exactly the pages,
    cursors and ``pageInfo`` the library schema serves with no optimizer.
    """
    _seed_jointly_issued_printings()
    monkeypatch.setattr(models.Printing._meta, "ordering", ["edition"])
    monkeypatch.setattr(models.Edition._meta, "ordering", ["publisher_2"])
    monkeypatch.setattr(models.Publisher._meta, "ordering", ["-name"])

    planned, planned_sql = _printings_pages(window)
    served, _ = _printings_pages(window, schema=_unoptimized_library_schema())

    assert len(planned_sql) == 2, planned_sql
    assert ["ROW_NUMBER" in sql.upper() for sql in planned_sql] == [False, True], planned_sql
    assert "LEFT OUTER JOIN" in planned_sql[1], planned_sql
    assert planned == served


#: A book order naming a to-many relation, with the ``Meta.ordering`` of each model the
#: name compiles into: the ``genres`` many-to-many, and the ``loans`` reverse key on into
#: each loan's patron. Every book repeats once per row the relation joins.
_TO_MANY_BOOK_ORDERS: dict[str, tuple[str, tuple[tuple[type[Model], tuple[str, ...]], ...]]] = {
    "many-to-many": ("genres", ((models.Genre, ("-name",)),)),
    "reverse-key": ("loans", ((models.Loan, ("patron",)), (models.Patron, ("-name",)))),
}


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("source", list(_TO_MANY_BOOK_ORDERS))
@pytest.mark.django_db
def test_to_many_relation_name_book_order_pages_genre_books_connection_like_the_pipeline(
    source: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A book order naming a to-many relation multiplies rows the same way through the window.

    The compiler joins the relation to order by its model's ``Meta.ordering``, so a
    book appears once per joined row; the window numbers exactly those rows, and each
    genre's page, cursors and ``pageInfo`` equal the unoptimized library schema's,
    served from one ``ROW_NUMBER`` statement beside the genre page.
    """
    _seed_shelved_genres()
    patrons = [models.Patron.objects.create(name=name) for name in ("Ada", "Grace", "Linus")]
    for index, book in enumerate(models.Book.objects.order_by("pk")):
        for patron in patrons[index % 3 : index % 3 + 2]:
            models.Loan.objects.create(book=book, patron=patron)
    name, orderings = _TO_MANY_BOOK_ORDERS[source]
    for model, ordering in orderings:
        monkeypatch.setattr(model._meta, "ordering", ordering)
    _order_books_by(monkeypatch, lambda books: books.order_by(name))

    planned, planned_sql = _genre_books_pages(window)
    served, _ = _genre_books_pages(window, schema=_unoptimized_library_schema())

    assert len(planned_sql) == 2, planned_sql
    assert ["ROW_NUMBER" in sql.upper() for sql in planned_sql] == [False, True], planned_sql
    assert planned == served


def _seed_labelled_shelves() -> None:
    """Two branches with three shelves each, labelled out of code order, one shelf twice."""
    for branch_name in ("North", "South"):
        branch = models.Branch.objects.create(name=branch_name)
        for code in ("s2", "s1", "s3"):
            models.Shelf.objects.create(branch=branch, code=code)
        for index, code in enumerate(
            (
                "s2",
                "s1",
                "s3",
                "s1",
            ),
        ):
            models.ShelfLabel.objects.create(
                branch=branch,
                shelf_code=code,
                text=f"{branch_name} {index}",
            )


#: The ``Shelf.Meta.ordering`` declared beside a label's ``shelf`` order, or none: the
#: multi-column relation orders by its two carrier columns either way.
_LABEL_SHELF_ORDERINGS: dict[str, tuple[str, ...] | None] = {
    "no-ordering": None,
    "ordering-ignored": ("-code",),
}


@pytest.mark.parametrize("window", list(_SHUFFLED_BOOKS_WINDOWS))
@pytest.mark.parametrize("shelf_ordering", list(_LABEL_SHELF_ORDERINGS))
@pytest.mark.parametrize("order", ["shelf", "-shelf"])
@pytest.mark.django_db
def test_multi_column_relation_name_label_order_pages_like_the_pipeline(
    order: str,
    shelf_ordering: str,
    window: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A label order naming the multi-column ``shelf`` relation pages through the window.

    ``ShelfLabel.shelf`` lives in two carrier columns and its ``attname`` is its
    name, so Django orders the name by both carriers and never by
    ``Shelf.Meta.ordering``, declared or not; neither carrier is one key column the
    window could read off the name. Each branch's ``shelfLabelsConnection`` is
    one ``ROW_NUMBER`` statement beside the branch list, serving exactly the pages,
    cursors and ``pageInfo`` the per-parent pipeline serves.
    """
    _seed_labelled_shelves()
    shelves = _LABEL_SHELF_ORDERINGS[shelf_ordering]
    if shelves is not None:
        monkeypatch.setattr(models.Shelf._meta, "ordering", shelves)
    optimized, unoptimized = _hold(
        models.ShelfLabel,
        ("text",),
        models.Branch,
        "shelf_labels",
        (order,),
    )

    planned, planned_sql = _held_pages(optimized, "shelfLabelsConnection", window, "text")
    served, _ = _held_pages(unoptimized, "shelfLabelsConnection", window, "text")

    assert len(planned_sql) == 2, planned_sql
    assert ["ROW_NUMBER" in sql.upper() for sql in planned_sql] == [False, True], planned_sql
    assert planned == served
