"""Live GraphQL HTTP tests for the library inheritance, proxy, and relation-shape surface.

Each row reads one shape off the wire and, where the claim is a cost or a
query shape, off the SQL the request emitted:

- Multi-table inheritance: ``LendingDesk`` and ``SelfServeDesk`` project their
  inherited ``Venue`` columns through the parent-link join in one statement,
  order by the inherited ``opened_on`` column, and are hidden with their
  ``Venue`` row because the visibility cascade walks the ``<parent>_ptr``
  link (transitively for the two-level chain).
- Reverse relations declared without ``related_name``:
  ``VenueType.repairticket`` / ``venuebadge`` / ``venuesponsor`` resolve
  through Django's default accessors, each batched once, and the rows the
  badge and sponsor hooks hide are absent from those accessors and from both
  roots.
- The nullable ``Venue.lead_ticket`` <-> ``RepairTicket.venue`` cycle:
  ``VenueType`` cascades over the nullable key (a venue with no lead ticket
  stays visible, one whose lead ticket is hidden does not) and
  ``RepairTicketType`` does not cascade back, so the walk never re-enters.
- Proxies with a filtering default manager: ``allLibraryOpenVenues`` is the
  ``OpenVenue`` manager's rows, and a ``BranchSignage`` row declared to the
  ``VisibleBranch`` proxy is hidden when ``VisibleBranchType``'s hook hides its
  branch (the manager alone does not reach across the relation). On a private
  schema whose branch type declares no rule (or returns its input), every read
  across ``branch`` reaches the branch the manager hides: declared and flat
  filter hops, an undeclared hooked path and relation key, related orderings,
  the cascade on list and connection roots, and the non-null ``branch``
  optimized and unoptimized, each sync and async.
- ``CirculationDesk``, one model carrying every relation kind: its reverse
  ``children`` / ``profile`` resolve, and its cascade scoped to ``branch`` /
  ``shelf`` serves rows despite the generic foreign key a full walk refuses.
- A multi-column forward ``ForeignObject``: ``ShelfLabel.shelf`` is held in
  ``branch`` and ``shelf_code``; the ``"__all__"`` ``ShelfLabelOrder`` publishes
  it after its carriers, a ``shelf`` term orders by both carriers in one
  statement, and a label on a shelf ``ShelfType`` hides, or naming no shelf at
  all, stays listed and sorts as one with none, under a ``shelfRow: { code }``
  term past the relation as well; behind the to-many
  ``BranchOrder.shelf_labels`` hop each carrier is aggregated per branch and
  correlated to the label's own carrier columns. ``ShelfLabelFilter`` filters by
  it: ``exact`` / ``in`` take the shelf's primary key and match both carriers,
  never a hidden shelf, and ``isNull`` is a Boolean answered over the shelves
  the viewer sees (a hidden shelf and a missing one alike), in one statement.
  Selecting ``shelf`` on a label whose shelf is hidden is a masked completion
  error for an anonymous viewer, while staff are served the shelf.
- Multi-table updates: ``updateLendingDesk`` and its ``ViaForm`` / ``ViaSerializer``
  siblings write the ``Venue`` table and the desk's own as two ``UPDATE`` s, the model and
  ``ModelForm`` flavors naming every loaded non-key column in ``update_fields``; a desk
  deleted after authorization (the whole row, or only the desk's table) is the in-band
  ``conflict`` envelope, never re-INSERTed by the model or ``ModelForm`` flavor, and the
  serializer's re-INSERT is refused the same way and rolled back; an ``id`` past
  ``Venue.id``'s range is the not-found error in every flavor, the desk kept.
- A serializer write saving a row of its model's family: over ``Venue``, ``OpenVenue``
  and ``LendingDesk``, a ``create()`` / ``update()`` saving a proxy, a proxy of a proxy,
  a multi-table child or grandchild or a proxy of a child (test-local proxies included)
  answers that row; the concrete base under the proxy is refused as no ``OpenVenue``; a
  create saving a child over a stored plain ``Venue`` is that child's INSERT, an update
  doing so over the located row is never observed being UPDATED (no ``conflict``), and an
  INSERT through the concrete base or a sibling proxy under the ``OpenVenue`` update is
  no re-INSERT.
- A key into a parent-link chain: ``createKioskFault`` and its ``ViaForm`` /
  ``ViaSerializer`` siblings name a non-Relay ``SelfServeDesk``, whose primary key is
  the ``lendingdesk_ptr`` -> ``venue_ptr`` chain, so ``kioskId`` is typed ``Int!`` from
  ``Venue.id``; a visible kiosk stores, and a kiosk under a closed venue or a missing
  one is the relation error with nothing written.
- Write-input requiredness: ``Book.archive_genres`` (``editable=False``) is
  absent from both generated ``Book`` inputs, and ``MediaSpecimen``'s optional
  file columns are optional through the ``blank`` arm and the ``null`` arm
  separately.
"""

import asyncio
import datetime
import re
from collections.abc import Callable, Generator
from functools import wraps
from typing import TypeVar

import pytest
import strawberry
from apps.library import models
from apps.library import schema as library_schema
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Model, QuerySet
from django.db.models.signals import pre_save
from django.http import HttpRequest, HttpResponseBase
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import (
    DeleteAfterAuthorization,
    JSONObject,
    RecordCompiledSql,
    assert_graphql_success,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    json_str,
    post_lock_reread_shapes,
    response_json,
    select_tables_after_last_delete,
    statement_shapes,
    statement_shapes_after_last_delete,
)
from strategy_schemas import make_django_type
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoListField,
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    SerializerMutation,
    aapply_cascade_permissions,
    apply_cascade_permissions,
    finalize_django_types,
)
from django_strawberry_framework.connection import _connection_type_for
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.orders import OrderSet, RelatedOrder
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView
from tests._idioms import ModelSerializerBase, saved_pk


def _sql_from_table(captured: CaptureQueriesContext, table: str) -> list[str]:
    """Return captured SQL whose OUTER ``FROM`` is ``table``, not a subquery's."""
    return [
        entry["sql"]
        for entry in captured.captured_queries
        if entry["sql"].split(" FROM ", 1)[-1].startswith(f'"{table}"')
    ]


def _select_list(sql: str) -> str:
    """Return the projection of ``sql``: the text between ``SELECT`` and the first ``FROM``."""
    return sql.split(" FROM ", 1)[0]


def _seed_desks() -> None:
    """Three lending desks, one under a closed venue, and two kiosks, one closed."""
    models.LendingDesk.objects.create(
        name="North Desk",
        opened_on=datetime.date(2020, 1, 1),
        window_count=2,
    )
    models.LendingDesk.objects.create(
        name="Closed East Desk",
        opened_on=datetime.date(2019, 1, 1),
        window_count=1,
    )
    models.LendingDesk.objects.create(
        name="South Desk",
        opened_on=datetime.date(2021, 1, 1),
        window_count=3,
    )
    models.SelfServeDesk.objects.create(
        name="Lobby Kiosk",
        opened_on=datetime.date(2022, 1, 1),
        window_count=0,
        kiosk_code="K-1",
    )
    models.SelfServeDesk.objects.create(
        name="Closed Annex Kiosk",
        opened_on=datetime.date(2018, 1, 1),
        window_count=0,
        kiosk_code="K-2",
    )


def _introspect_input_fields(type_name: str) -> dict[str, dict[str, object]]:
    """Return ``{field name: type}`` for the input object ``type_name`` over HTTP."""
    data = assert_graphql_success(
        f'{{ __type(name: "{type_name}") {{ inputFields {{ name type {{ kind name ofType '
        "{ kind name } } } } }",
    )
    return {
        json_str(field, "name"): json_object(field, "type")
        for field in json_list(data, "__type", "inputFields")
    }


@pytest.mark.django_db
def test_lending_desk_projects_inherited_columns_through_the_parent_link_join() -> None:
    """``name`` is read from ``library_venue`` in the same statement as ``windowCount``.

    ``LendingDesk`` stores only ``window_count`` on its own table; ``name`` and
    ``opened_on`` live on ``library_venue`` behind the ``venue_ptr`` parent
    link. The optimizer's projection names the inherited column, so the page is
    one ``library_lendingdesk`` statement joining ``library_venue`` - and the
    unselected inherited ``opened_on`` is not projected.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success("{ allLibraryLendingDesks { name windowCount } }")

    assert data["allLibraryLendingDesks"] == [
        {"name": "North Desk", "windowCount": 2},
        {"name": "South Desk", "windowCount": 3},
        {"name": "Lobby Kiosk", "windowCount": 0},
    ], data
    desk_sql = _sql_from_table(captured, "library_lendingdesk")
    assert len(desk_sql) == 1, captured.captured_queries
    assert len(captured.captured_queries) == 1, captured.captured_queries
    assert 'INNER JOIN "library_venue"' in desk_sql[0], desk_sql[0]
    projection = _select_list(desk_sql[0])
    assert '"library_venue"."name"' in projection, projection
    assert '"library_lendingdesk"."window_count"' in projection, projection
    assert '"library_venue"."opened_on"' not in projection, projection


@pytest.mark.django_db
def test_self_serve_desk_reads_both_parent_tables_in_one_statement() -> None:
    """A two-level chain joins both parent tables and projects a column from each.

    ``SelfServeDesk`` extends ``LendingDesk``, which extends ``Venue``, so
    ``kioskCode`` is local, ``windowCount`` one parent link away and ``name``
    two. One statement carries all three, and the unselected ``opened_on``
    stays out of the projection.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibrarySelfServeDesks { name windowCount kioskCode } }",
        )

    assert data["allLibrarySelfServeDesks"] == [
        {"name": "Lobby Kiosk", "windowCount": 0, "kioskCode": "K-1"},
    ], data
    assert len(captured.captured_queries) == 1, captured.captured_queries
    sql = captured.captured_queries[0]["sql"]
    assert 'INNER JOIN "library_lendingdesk"' in sql, sql
    assert 'INNER JOIN "library_venue"' in sql, sql
    projection = _select_list(sql)
    assert '"library_venue"."name"' in projection, projection
    assert '"library_lendingdesk"."window_count"' in projection, projection
    assert '"library_venue"."opened_on"' not in projection, projection


@pytest.mark.django_db
def test_lending_desks_order_by_the_inherited_opened_on_column() -> None:
    """``orderBy: openedOn`` sorts desks by the parent table's column, in each direction.

    ``opened_on`` is declared on ``Venue``; ``LendingDeskOrder`` publishes it,
    and the ``ORDER BY`` names ``library_venue`` rather than the child table.
    Both directions are read so a lost direction cannot pass.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        descending = assert_graphql_success(
            "{ allLibraryLendingDesks(orderBy: [{ openedOn: DESC }]) { name } }",
        )
    # Read the capture before the next request: Django clears the query log on
    # every ``request_started``, and the capture slices that log lazily.
    (sql,) = _sql_from_table(captured, "library_lendingdesk")
    ascending = assert_graphql_success(
        "{ allLibraryLendingDesks(orderBy: [{ openedOn: ASC }]) { name } }",
    )

    assert [json_at(row, "name") for row in json_list(descending, "allLibraryLendingDesks")] == [
        "Lobby Kiosk",
        "South Desk",
        "North Desk",
    ], descending
    assert [json_at(row, "name") for row in json_list(ascending, "allLibraryLendingDesks")] == [
        "North Desk",
        "South Desk",
        "Lobby Kiosk",
    ], ascending
    assert 'ORDER BY "library_venue"."opened_on" DESC' in sql, sql


@pytest.mark.django_db
def test_parent_link_cascade_hides_a_desk_whose_venue_is_hidden() -> None:
    """A desk under a closed ``Venue`` is hidden through the ``<parent>_ptr`` cascade.

    ``VenueType.get_queryset`` hides venues named ``Closed ...``;
    ``LendingDeskType`` cascades over ``venue_ptr`` and ``SelfServeDeskType``
    over ``lendingdesk_ptr`` into it, so the closed desk and the closed kiosk
    drop out of both roots while their rows still exist. A parent link is never
    null, so the desk statement tests ``venue_ptr_id`` membership with no
    ``IS NULL`` branch beside it.
    """
    _seed_desks()

    with CaptureQueriesContext(connection) as captured:
        desks = assert_graphql_success("{ allLibraryLendingDesks { name } }")
    (desk_sql,) = _sql_from_table(captured, "library_lendingdesk")
    kiosks = assert_graphql_success("{ allLibrarySelfServeDesks { name } }")

    assert [json_at(row, "name") for row in json_list(desks, "allLibraryLendingDesks")] == [
        "North Desk",
        "South Desk",
        "Lobby Kiosk",
    ], desks
    assert [json_at(row, "name") for row in json_list(kiosks, "allLibrarySelfServeDesks")] == [
        "Lobby Kiosk",
    ], kiosks
    assert models.LendingDesk.objects.filter(name="Closed East Desk").exists()
    assert models.SelfServeDesk.objects.filter(name="Closed Annex Kiosk").exists()
    assert '"library_lendingdesk"."venue_ptr_id" IN (SELECT' in desk_sql, desk_sql
    assert '"library_lendingdesk"."venue_ptr_id" IS NULL' not in desk_sql, desk_sql


@pytest.mark.django_db
def test_venue_reverse_relations_without_related_name_resolve_through_default_accessors() -> None:
    """``repairticket`` / ``venuebadge`` / ``venuesponsor`` read the default accessors.

    None of the three relations declares ``related_name``, so each is published
    under its query name while rows live behind ``repairticket_set``,
    ``venuebadge`` and ``venuesponsor_set``. The page is one venue statement
    and one prefetch per relation (each target's hook keeps the badge out of
    a join); the withdrawn ``VOID-`` ticket stays hidden and a venue with no
    badge answers ``null``.
    """
    annex = models.Venue.objects.create(name="Annex")
    depot = models.Venue.objects.create(name="Depot")
    models.RepairTicket.objects.create(code="T-1", venue=annex)
    models.RepairTicket.objects.create(code="T-2", venue=annex)
    models.RepairTicket.objects.create(code="VOID-3", venue=annex)
    models.RepairTicket.objects.create(code="T-4", venue=depot)
    models.VenueBadge.objects.create(code="STEP-FREE", venue=annex)
    acme = models.VenueSponsor.objects.create(name="Acme")
    acme.venues.add(annex, depot)
    models.VenueSponsor.objects.create(name="Globex").venues.add(annex)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            """
            query {
              allLibraryVenues {
                name
                repairticket { code }
                venuebadge { code }
                venuesponsor { name }
              }
            }
            """,
        )

    assert data["allLibraryVenues"] == [
        {
            "name": "Annex",
            "repairticket": [{"code": "T-1"}, {"code": "T-2"}],
            "venuebadge": {"code": "STEP-FREE"},
            "venuesponsor": [{"name": "Acme"}, {"name": "Globex"}],
        },
        {
            "name": "Depot",
            "repairticket": [{"code": "T-4"}],
            "venuebadge": None,
            "venuesponsor": [{"name": "Acme"}],
        },
    ], data
    assert len(captured.captured_queries) == 4, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venue")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_repairticket")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venuebadge")) == 1, captured.captured_queries
    assert len(_sql_from_table(captured, "library_venuesponsor")) == 1, captured.captured_queries


def _seed_withdrawn_badge_and_sponsor() -> None:
    """Two venues, each with a visible and a withdrawn row on the no-``related_name`` relations.

    ``Annex`` holds the visible ``STEP-FREE`` badge and ``Depot`` the withdrawn
    ``VOID-RAMP`` one; both venues are funded by the visible ``Acme`` and the
    withdrawn ``Withdrawn Initech``.
    """
    annex = models.Venue.objects.create(name="Annex")
    depot = models.Venue.objects.create(name="Depot")
    models.VenueBadge.objects.create(code="STEP-FREE", venue=annex)
    models.VenueBadge.objects.create(code="VOID-RAMP", venue=depot)
    models.VenueSponsor.objects.create(name="Acme").venues.add(annex, depot)
    models.VenueSponsor.objects.create(name="Withdrawn Initech").venues.add(annex, depot)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "visible", "expected"),
    [
        (
            "{ allLibraryVenues { name venuebadge { code } venuesponsor { name } } }",
            ("STEP-FREE", "Acme"),
            {
                "allLibraryVenues": [
                    {
                        "name": "Annex",
                        "venuebadge": {"code": "STEP-FREE"},
                        "venuesponsor": [{"name": "Acme"}],
                    },
                    {"name": "Depot", "venuebadge": None, "venuesponsor": [{"name": "Acme"}]},
                ],
            },
        ),
        (
            "{ allLibraryVenueBadges { code venue { name } } }",
            ("STEP-FREE",),
            {"allLibraryVenueBadges": [{"code": "STEP-FREE", "venue": {"name": "Annex"}}]},
        ),
        (
            "{ allLibraryVenueSponsors { name venues { name } } }",
            ("Acme",),
            {
                "allLibraryVenueSponsors": [
                    {"name": "Acme", "venues": [{"name": "Annex"}, {"name": "Depot"}]},
                ],
            },
        ),
    ],
    ids=["reverse-relations-from-venue", "badge-root", "sponsor-root"],
)
def test_withdrawn_badges_and_sponsors_are_absent_from_every_read_path(
    query: str,
    visible: tuple[str, ...],
    expected: dict[str, object],
) -> None:
    """A withdrawn badge or sponsor is absent from the wire, never an error.

    ``VenueBadgeType`` hides ``VOID-`` badges and ``VenueSponsorType`` hides
    ``Withdrawn`` sponsors. Through the reverse accessors a venue whose only
    badge is withdrawn answers ``null`` and the sponsor list drops the
    withdrawn sponsor; the roots drop both rows outright.
    """
    _seed_withdrawn_badge_and_sponsor()
    assert models.VenueBadge.objects.filter(code="VOID-RAMP", venue__name="Depot").exists()
    assert models.VenueSponsor.objects.filter(
        name="Withdrawn Initech",
        venues__name="Annex",
    ).exists()

    data = assert_graphql_success(query)

    assert all(marker in str(data) for marker in visible), data
    assert "VOID-RAMP" not in str(data), data
    assert "Withdrawn" not in str(data), data
    assert data == expected, data


@pytest.mark.django_db
def test_nullable_lead_ticket_cycle_cascades_one_way() -> None:
    """The nullable half of the ``Venue`` <-> ``RepairTicket`` cycle keeps unled venues.

    ``VenueType`` cascades over ``lead_ticket``: ``Shed``, whose lead ticket is
    withdrawn, is hidden; ``Depot``, which has no lead ticket, stays visible
    through the ``IS NULL`` disjunct a nullable edge adds. ``RepairTicketType``
    does not cascade back over ``venue``, so the request resolves instead of
    raising the cycle error, and ``leadTicket { venue }`` walks the cycle back
    to its own venue.
    """
    annex = models.Venue.objects.create(name="Annex")
    models.Venue.objects.create(name="Depot")
    shed = models.Venue.objects.create(name="Shed")
    annex.lead_ticket = models.RepairTicket.objects.create(code="T-1", venue=annex)
    annex.save()
    shed.lead_ticket = models.RepairTicket.objects.create(code="VOID-9", venue=shed)
    shed.save()

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allLibraryVenues { name leadTicket { code venue { name } } } }",
        )

    # ``Venue`` declares no ordering, so the rows compare by name, never by storage order.
    assert sorted(json_list(data, "allLibraryVenues"), key=lambda row: json_str(row, "name")) == [
        {"name": "Annex", "leadTicket": {"code": "T-1", "venue": {"name": "Annex"}}},
        {"name": "Depot", "leadTicket": None},
    ], data
    # The root venues, their lead tickets, and the tickets' venues: one statement each.
    assert len(captured.captured_queries) == 3, captured.captured_queries
    root_sql = captured.captured_queries[0]["sql"]
    assert _select_list(root_sql).endswith('"library_venue"."lead_ticket_id"'), root_sql
    assert '"library_venue"."lead_ticket_id" IS NULL' in root_sql, root_sql


@pytest.mark.django_db
def test_open_venues_are_the_proxy_default_manager_rows() -> None:
    """``allLibraryOpenVenues`` serves ``OpenVenue.objects``, which hides unopened venues.

    ``OpenVenueType`` declares no hook, so the only filter is the proxy's
    default manager; the same unopened row is served by ``allLibraryVenues``,
    whose seed is ``Venue``'s plain manager.
    """
    models.Venue.objects.create(name="Annex", opened_on=datetime.date(2020, 5, 1))
    models.Venue.objects.create(name="Planned Wing")

    open_venues = assert_graphql_success("{ allLibraryOpenVenues { name openedOn } }")
    all_venues = assert_graphql_success("{ allLibraryVenues { name } }")

    assert open_venues["allLibraryOpenVenues"] == [
        {"name": "Annex", "openedOn": "2020-05-01"},
    ], open_venues
    assert [json_at(row, "name") for row in json_list(all_venues, "allLibraryVenues")] == [
        "Annex",
        "Planned Wing",
    ], all_venues


@pytest.mark.django_db
def test_signage_on_a_city_less_branch_is_hidden_by_the_proxy_type_hook() -> None:
    """The cascade hides a sign whose branch the ``VisibleBranchType`` hook hides.

    ``BranchSignage.branch`` is declared to ``VisibleBranch``, whose hook (and
    default manager) hide city-less branches. The cascade seeds the target from
    every branch, as the forward descriptor's base manager loads them, and runs
    the hook, so the sign on the city-less branch is hidden over the wire
    although ``sign.branch`` still loads that branch.
    """
    main = models.Branch.objects.create(name="Main", city="Metro")
    outpost = models.Branch.objects.create(name="Outpost", city="")
    models.BranchSignage.objects.create(code="S-MAIN", branch_id=main.pk)
    hidden = models.BranchSignage.objects.create(code="S-OUTPOST", branch_id=outpost.pk)

    data = assert_graphql_success("{ allLibraryBranchSignage { code branch { name } } }")

    assert data["allLibraryBranchSignage"] == [
        {"code": "S-MAIN", "branch": {"name": "Main"}},
    ], data
    assert models.BranchSignage.objects.get(pk=hidden.pk).branch.name == "Outpost"
    assert not models.VisibleBranch.objects.filter(pk=outpost.pk).exists()


_BRANCH_READS: dict[str, DjangoSchema | None] = {"schema": None}
_MODES = ["sync", "async"]


@wraps(DjangoGraphQLView.as_view())
def _branch_reads_view(request: HttpRequest) -> HttpResponseBase:
    schema = _BRANCH_READS["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


@wraps(AsyncDjangoGraphQLView.as_view())
async def _branch_reads_async_view(request: HttpRequest) -> HttpResponseBase:
    schema = _BRANCH_READS["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


#: The private schema ``_post_family`` serves, set for one request.
_FAMILY_WRITES: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _family_writes_view(request: HttpRequest) -> HttpResponseBase:
    schema = _FAMILY_WRITES["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


# Served only under ``override_settings(ROOT_URLCONF=__name__)`` by ``_branch_reads`` and
# ``_post_family``.
urlpatterns = [
    path("graphql-branch-reads/", _branch_reads_view),
    path("graphql-branch-reads-async/", _branch_reads_async_view),
    path("graphql-venue-family/", _family_writes_view),
]


async def _branch_reads_async(document: str) -> JSONObject:
    result = await AsyncTestClient(path="/graphql-branch-reads-async/").query(
        document,
        assert_no_errors=False,
    )
    assert result.response.status_code == 200
    return response_json(result.response)


def _branch_reads(schema: DjangoSchema, document: str, mode: str) -> JSONObject:
    """Post ``document`` to ``schema``'s sync or async mount and return the whole payload."""
    _BRANCH_READS["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            if mode == "async":
                return asyncio.run(_branch_reads_async(document))
            return graphql_payload(document, url="/graphql-branch-reads/")
    finally:
        _BRANCH_READS["schema"] = None


def _seed_branch_signage() -> int:
    """Signs ``S-MAIN`` on ``Main`` and ``S-OUTPOST`` on the city-less ``Outpost``; its pk."""
    main = models.Branch.objects.create(name="Main", city="Metro")
    outpost = models.Branch.objects.create(name="Outpost", city="")
    models.BranchSignage.objects.create(code="S-MAIN", branch_id=main.pk)
    models.BranchSignage.objects.create(code="S-OUTPOST", branch_id=outpost.pk)
    assert outpost.pk is not None
    return outpost.pk


def _passthrough_hook(
    _cls: type[DjangoType],
    queryset: QuerySet[Model],
    _info: object,
    **_kwargs: object,
) -> QuerySet[Model]:
    return queryset


def _cascade_hook(
    cls: type[DjangoType],
    queryset: QuerySet[Model],
    info: object,
    **_kwargs: object,
) -> QuerySet[Model]:
    return apply_cascade_permissions(cls, queryset, info)


async def _async_cascade_hook(
    cls: type[DjangoType],
    queryset: QuerySet[Model],
    info: object,
    **_kwargs: object,
) -> QuerySet[Model]:
    return await aapply_cascade_permissions(cls, queryset, info)


def _branch_type(hook: str, **meta: object) -> type[DjangoType]:
    """``VisibleBranch`` with no hook (``identity``) or one returning its input (``passthrough``)."""
    namespace: dict[str, object] = {}
    if hook == "passthrough":
        namespace["get_queryset"] = classmethod(_passthrough_hook)
    return make_django_type(
        "SignBranchNode",
        models.VisibleBranch,
        ("id", "name"),
        node=False,
        meta_extra=meta,
        namespace_extra=namespace,
    )


def _branch_filterset() -> type[FilterSet]:
    return type(
        "SignBranchFilter",
        (FilterSet,),
        {"Meta": type("Meta", (), {"model": models.VisibleBranch, "fields": {"name": ["exact"]}})},
    )


def _signage_schema(
    *,
    hook: Callable[..., object] | None = None,
    optimizer: bool = True,
    **meta: object,
) -> DjangoSchema:
    """A ``BranchSignage`` connection (``rows``) and list (``listed``) over the declared types."""
    namespace: dict[str, object] = {} if hook is None else {"get_queryset": classmethod(hook)}
    signage = make_django_type(
        "SignNode",
        models.BranchSignage,
        ("id", "code", "branch"),
        meta_extra=meta,
        namespace_extra=namespace,
    )
    finalize_django_types()
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "rows": _connection_type_for(
                        signage,
                        signage.__django_strawberry_definition__,
                    ),
                    "listed": list[signage],
                },
                "rows": DjangoConnectionField(signage),
                "listed": DjangoListField(signage),
            },
        ),
    )
    extension = DjangoOptimizerExtension()
    return DjangoSchema(
        query=query,
        extensions=[lambda: extension] if optimizer else [],
        error_policy={"enabled": False},
    )


def _signage_rows(*codes: str) -> JSONObject:
    return {"data": {"rows": {"edges": [{"node": {"code": code}} for code in codes]}}}


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("hook", ["identity", "passthrough"])
@pytest.mark.parametrize(
    ("where", "statements"),
    [('{branch: {name: {exact: "Outpost"}}}', 1), ('{branchName: {exact: "Outpost"}}', 1)],
    ids=["nested", "flat"],
)
def test_signage_filter_through_the_declared_branch_hop_reads_every_branch(
    *,
    mode: str,
    hook: str,
    where: str,
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A declared ``RelatedFilter`` hop seeds every branch, not the proxy manager's rows.

    ``VisibleBranch``'s default manager hides the city-less ``Outpost``, and the
    branch type declares no rule of its own (no hook, or one returning its
    input), so a nested branch filter and a flat leaf through the declared hop
    both reach ``Outpost``, as Django's join across ``branch`` does.
    """
    _seed_branch_signage()
    branch_filterset = _branch_filterset()
    _branch_type(hook, filterset_class=branch_filterset)
    signage_filterset = type(
        "SignFilter",
        (FilterSet,),
        {
            "branch": RelatedFilter(branch_filterset, field_name="branch"),
            "Meta": type(
                "Meta",
                (),
                {
                    "model": models.BranchSignage,
                    "fields": {"code": ["exact"], "branch__name": ["exact"]},
                },
            ),
        },
    )
    schema = _signage_schema(filterset_class=signage_filterset)
    recorded = record_compiled_sql()

    payload = _branch_reads(
        schema,
        f"{{ rows(filter: {where}) {{ edges {{ node {{ code }} }} }} }}",
        mode,
    )

    assert payload == _signage_rows("S-OUTPOST"), payload
    assert len(recorded) == statements, recorded


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize(
    ("where", "statements"),
    [('{branchName: {exact: "Outpost"}}', 1), ("{branch: {exact: OUTPOST}}", 1)],
    ids=["path", "key"],
)
def test_signage_filter_across_an_undeclared_hooked_branch_hop_reads_every_branch(
    *,
    mode: str,
    where: str,
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An undeclared hop into a hooked branch type runs the hook over every branch.

    The flat ``branch__name`` path and the ``branch`` relation key are scoped by
    the branch type's ``get_queryset``, which returns its input, so the rows it
    scopes are every branch and ``Outpost``'s sign matches.
    """
    outpost = _seed_branch_signage()
    _branch_type("passthrough")
    signage_filterset = type(
        "SignFilter",
        (FilterSet,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": models.BranchSignage,
                    "fields": {"code": ["exact"], "branch__name": ["exact"], "branch": ["exact"]},
                },
            ),
        },
    )
    schema = _signage_schema(filterset_class=signage_filterset)
    recorded = record_compiled_sql()
    document = f"{{ rows(filter: {where}) {{ edges {{ node {{ code }} }} }} }}"

    payload = _branch_reads(schema, document.replace("OUTPOST", str(outpost)), mode)

    assert payload == _signage_rows("S-OUTPOST"), payload
    assert len(recorded) == statements, recorded


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize(
    ("term", "order_by", "statements"),
    [("declared", "{branch: {name: DESC}}", 1), ("undeclared", "{branchName: DESC}", 1)],
    ids=["declared", "undeclared"],
)
def test_signage_order_by_a_hooked_branch_hop_reads_every_branch(
    *,
    mode: str,
    term: str,
    order_by: str,
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A related ordering into a hooked branch type sorts by every branch's name.

    The hook returns its input, so ``Outpost`` is a row it admits and sorts
    ahead of ``Main`` descending; a branch the manager alone hides is not sorted
    as a missing one.
    """
    _seed_branch_signage()
    branch_orderset = type(
        "SignBranchOrder",
        (OrderSet,),
        {"Meta": type("Meta", (), {"model": models.VisibleBranch, "fields": ["name"]})},
    )
    _branch_type("passthrough", orderset_class=branch_orderset)
    signage_attrs: dict[str, object] = {}
    fields = ["code"]
    if term == "declared":
        signage_attrs["branch"] = RelatedOrder(branch_orderset, field_name="branch")
    else:
        fields.append("branch__name")
    signage_attrs["Meta"] = type("Meta", (), {"model": models.BranchSignage, "fields": fields})
    signage_orderset = type("SignOrder", (OrderSet,), signage_attrs)
    schema = _signage_schema(orderset_class=signage_orderset)
    recorded = record_compiled_sql()

    payload = _branch_reads(
        schema,
        f"{{ rows(orderBy: [{order_by}]) {{ edges {{ node {{ code }} }} }} }}",
        mode,
    )

    assert payload == _signage_rows("S-OUTPOST", "S-MAIN"), payload
    assert len(recorded) == statements, recorded


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize(
    ("document", "statements"),
    [("{ rows { edges { node { code } } } }", 1), ("{ listed { code } }", 1)],
    ids=["connection", "list"],
)
def test_signage_cascade_over_an_identity_branch_type_reads_every_branch(
    *,
    mode: str,
    document: str,
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The cascade composes a registered identity branch type over every branch.

    The branch type declares no hook, so no rule hides ``Outpost`` and its sign
    stays listed on both roots; the proxy's filtering default manager is not a
    visibility rule.
    """
    _seed_branch_signage()
    _branch_type("identity")
    schema = _signage_schema(hook=_async_cascade_hook if mode == "async" else _cascade_hook)
    recorded = record_compiled_sql()

    payload = _branch_reads(schema, document, mode)

    data = json_object(payload, "data")
    rows = (
        [json_at(edge, "node", "code") for edge in json_list(data, "rows", "edges")]
        if "rows" in data
        else [json_at(row, "code") for row in json_list(data, "listed")]
    )
    assert "errors" not in payload, payload
    assert sorted(map(str, rows)) == ["S-MAIN", "S-OUTPOST"], payload
    assert len(recorded) == statements, recorded


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize(
    ("optimizer", "statements"),
    [(True, 2), (False, 5)],
    ids=["optimized", "unoptimized"],
)
def test_signage_branch_through_a_hooked_branch_type_resolves_every_branch(
    *,
    mode: str,
    optimizer: bool,
    statements: int,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A sign's non-null ``branch`` resolves a branch only the proxy manager hides.

    The hooked branch type returns its input, so the planned child (optimized)
    and the resolver's re-check of the loaded row (unoptimized) both read every
    branch, as ``sign.branch`` does: ``Outpost`` resolves, never a null
    completion error.
    """
    _seed_branch_signage()
    _branch_type("passthrough")
    schema = _signage_schema(optimizer=optimizer)
    recorded = record_compiled_sql()

    payload = _branch_reads(
        schema,
        "{ rows { edges { node { code branch { name } } } } }",
        mode,
    )

    assert payload == {
        "data": {
            "rows": {
                "edges": [
                    {"node": {"code": "S-MAIN", "branch": {"name": "Main"}}},
                    {"node": {"code": "S-OUTPOST", "branch": {"name": "Outpost"}}},
                ],
            },
        },
    }, payload
    assert len(recorded) == statements, recorded


@pytest.mark.django_db
def test_circulation_desk_publishes_children_and_profile_under_a_scoped_cascade() -> None:
    """Every relation kind on one model; the explicit reverse names resolve.

    ``DeskShift.desk`` and ``DeskProfile.desk`` publish on the desk as
    ``children`` and ``profile``. The desk also carries a generic foreign key
    (set on ``Front``) and a generic relation, both outside ``Meta.fields``;
    ``CirculationDeskType`` cascades with ``fields=["branch", "shelf"]``, so the
    request is served instead of refused over the generic key, and the desk on
    the ``restricted`` branch is hidden from an anonymous viewer while a staff
    viewer sees it.
    """
    create_users(1)
    main = models.Branch.objects.create(name="Main", city="Metro")
    vault = models.Branch.objects.create(name="Vault", city="restricted")
    genre = models.Genre.objects.create(name="Reference")
    front = models.CirculationDesk.objects.create(
        name="Front",
        branch=main,
        shelf=models.Shelf.objects.create(code="A-1", branch=main),
        content_type=ContentType.objects.get_for_model(models.Genre),
        object_id=genre.pk,
    )
    front.genres.add(genre)
    models.CirculationDesk.objects.create(
        name="Vault Desk",
        branch=vault,
        shelf=models.Shelf.objects.create(code="V-1", branch=vault),
    )
    models.DeskShift.objects.create(name="Morning", desk=front)
    models.DeskShift.objects.create(name="Evening", desk=front)
    models.DeskProfile.objects.create(code="LATE-OPENING", desk=front)
    document = """
    query {
      allLibraryCirculationDesks {
        name
        branch { name }
        shelf { code }
        genres { name }
        children { name }
        profile { code }
      }
    }
    """

    anonymous = assert_graphql_success(document)
    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))
    staff = assert_graphql_success(document, client=staff_client)

    assert anonymous["allLibraryCirculationDesks"] == [
        {
            "name": "Front",
            "branch": {"name": "Main"},
            "shelf": {"code": "A-1"},
            "genres": [{"name": "Reference"}],
            "children": [{"name": "Morning"}, {"name": "Evening"}],
            "profile": {"code": "LATE-OPENING"},
        },
    ], anonymous
    assert [json_at(row, "name") for row in json_list(staff, "allLibraryCirculationDesks")] == [
        "Front",
        "Vault Desk",
    ], staff


def _seed_shelf_labels() -> None:
    """Four labels over two branches, one naming the ``secret`` shelf, inserted out of order.

    ``Central`` is created first, so its primary key sorts before ``Annex``'s
    although its name sorts after. Carrier order is ``(branch, shelf_code)``:
    ``central-a1``, ``central-c3``, ``annex-b2``, ``annex-s9``, which neither
    insertion order nor ``shelf_code`` alone reproduces.
    """
    central = models.Branch.objects.create(name="Central")
    annex = models.Branch.objects.create(name="Annex")
    for branch, code, topic in (
        (central, "A1", ""),
        (central, "C3", ""),
        (annex, "B2", ""),
        (annex, "S9", "secret"),
    ):
        models.Shelf.objects.create(branch=branch, code=code, topic=topic)
    for text, branch, code in (
        ("annex-b2", annex, "B2"),
        ("central-c3", central, "C3"),
        ("annex-s9", annex, "S9"),
        ("central-a1", central, "A1"),
    ):
        models.ShelfLabel.objects.create(text=text, branch=branch, shelf_code=code)


def _shelf_label_texts(
    direction: str,
    client: Client | None = None,
) -> tuple[list[str], list[str]]:
    """Return the label texts ordered by ``shelf`` in ``direction`` and the label statements."""
    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            f"{{ allLibraryShelfLabels(orderBy: [{{shelf: {direction}}}]) {{ text }} }}",
            client=client,
        )
    texts = [json_str(row, "text") for row in json_list(data, "allLibraryShelfLabels")]
    return texts, _sql_from_table(captured, "library_shelflabel")


#: Every ``Ordering`` member: the bare pair defers ``NULL`` placement to the
#: database, the four ``NULLS`` members fix it on every backend.
_DIRECTIONS = (
    "ASC",
    "ASC_NULLS_FIRST",
    "ASC_NULLS_LAST",
    "DESC",
    "DESC_NULLS_FIRST",
    "DESC_NULLS_LAST",
)


def _ordered_with_missing(direction: str, present: list[str], *missing: str) -> list[str]:
    """``present`` (given ascending) in ``direction``, with the rows ordering as ``NULL`` placed.

    A ``NULLS`` member places it where it says. A bare ``ASC`` / ``DESC`` leaves
    it to the database (``orders/inputs.py::Ordering``), which Django names
    ``nulls_order_largest``: PostgreSQL sorts ``NULL`` above every value, so
    last ascending and first descending, and SQLite below every value.
    """
    ascending = direction.startswith("ASC")
    if direction.endswith("NULLS_FIRST"):
        missing_first = True
    elif direction.endswith("NULLS_LAST"):
        missing_first = False
    else:
        missing_first = ascending != connection.features.nulls_order_largest
    ordered = present if ascending else present[::-1]
    return [*missing, *ordered] if missing_first else [*ordered, *missing]


def test_shelf_label_order_input_publishes_the_foreign_object_beside_its_carriers() -> None:
    """``"__all__"`` publishes the multi-column ``shelf`` relation as an order leaf.

    ``ShelfLabelOrder`` declares ``fields = "__all__"``. ``shelf`` has no column
    of its own (its value is the ``branch`` / ``shelf_code`` pair), and it is
    published after its carriers in model field order, like every other field.
    The ``shelf_row`` branch over the same relation follows under its own name,
    so the ``shelf`` leaf stays an ``Ordering``.
    """
    fields = _introspect_input_fields("ShelfLabelOrderInputType")

    assert list(fields) == [
        "id",
        "text",
        "branch",
        "shelfCode",
        "shelf",
        "shelfRow",
    ], fields
    assert fields["shelf"] == {"kind": "ENUM", "name": "Ordering", "ofType": None}, fields
    assert fields["shelfRow"] == {
        "kind": "INPUT_OBJECT",
        "name": "ShelfOrderInputType",
        "ofType": None,
    }, fields


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        (
            "ASC",
            [
                "central-a1",
                "central-c3",
                "annex-b2",
                "annex-s9",
            ],
        ),
        (
            "DESC",
            [
                "annex-s9",
                "annex-b2",
                "central-c3",
                "central-a1",
            ],
        ),
    ],
    ids=["asc", "desc"],
)
def test_shelf_labels_order_by_shelf_sorts_by_both_carriers(
    direction: str,
    expected: list[str],
) -> None:
    """A ``shelf`` term orders by ``branch_id`` then ``shelf_code``, each in the term's direction.

    The relation is ordered the way Django's ``order_by("shelf")`` orders it:
    one key per carrier column in link order, never ``Shelf``'s own columns.
    The viewer is staff, so ``ShelfType`` hides no shelf and each carrier keeps
    its value; the page is one ``library_shelflabel`` statement.
    """
    create_users(1)
    _seed_shelf_labels()
    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))

    texts, label_sql = _shelf_label_texts(direction, staff_client)

    assert texts == expected, texts
    assert len(label_sql) == 1, label_sql
    order_clause = label_sql[0].split(" ORDER BY ", 1)[1]
    assert re.findall(
        r'"library_shelflabel"\."(branch_id|shelf_code)" ELSE NULL END (ASC|DESC)',
        order_clause,
    ) == [("branch_id", direction), ("shelf_code", direction)], order_clause


@pytest.mark.django_db
@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_shelf_labels_order_a_hidden_shelf_as_a_missing_one(direction: str) -> None:
    """A label on a shelf ``ShelfType`` hides from the viewer sorts as one with no shelf.

    Anonymous viewers do not see the ``secret`` shelf, so both of
    ``annex-s9``'s carriers order as ``NULL``, where the direction places a
    ``NULL``. The label itself stays listed.
    """
    _seed_shelf_labels()

    texts, label_sql = _shelf_label_texts(direction)

    assert texts == _ordered_with_missing(
        direction,
        ["central-a1", "central-c3", "annex-b2"],
        "annex-s9",
    ), texts
    assert len(label_sql) == 1, label_sql


@pytest.mark.django_db
@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_shelf_labels_keep_a_label_naming_no_shelf_and_sort_it_as_missing(direction: str) -> None:
    """A label whose ``(branch, shelf_code)`` matches no shelf stays listed and sorts as missing.

    No database constraint holds a ``ForeignObject``, so ``central-zz`` names a
    shelf that does not exist. ``ShelfType`` declares ``get_queryset``, so each
    carrier is read under a visibility test; the test correlates on the link's
    carrier / target columns, adds no join to ``library_shelf`` and so drops no
    label, and the label with no shelf reads ``NULL`` on both carriers, placed
    where the direction places a ``NULL``. The viewer is staff, so every
    existing shelf keeps its value.
    """
    create_users(1)
    _seed_shelf_labels()
    models.ShelfLabel.objects.create(
        text="central-zz",
        branch=models.Branch.objects.get(name="Central"),
        shelf_code="ZZ",
    )
    staff_client = Client()
    staff_client.force_login(get_user_model().objects.get(username="staff_1"))

    texts, label_sql = _shelf_label_texts(direction, staff_client)

    assert texts == _ordered_with_missing(
        direction,
        [
            "central-a1",
            "central-c3",
            "annex-b2",
            "annex-s9",
        ],
        "central-zz",
    ), texts
    assert len(label_sql) == 1, label_sql
    assert "JOIN" not in label_sql[0], label_sql[0]


@pytest.mark.django_db
@pytest.mark.parametrize("direction", _DIRECTIONS)
@pytest.mark.parametrize(
    ("staff", "missing", "statements"),
    [(True, ["central-zz"], 3), (False, ["annex-s9", "central-zz"], 1)],
    ids=["staff", "anonymous"],
)
def test_shelf_labels_keep_a_label_naming_no_shelf_under_a_term_past_the_relation(
    *,
    direction: str,
    staff: bool,
    missing: list[str],
    statements: int,
) -> None:
    """``shelfRow: { code: ... }`` keeps the label naming no shelf and sorts it as missing.

    ``shelf__code`` is a target column of the ``shelf`` link, so Django trims the
    value to the label's ``shelf_code`` carrier and the plain term joins nothing.
    ``ShelfType`` hides the ``secret`` shelf from anonymous viewers, so the hop is
    scoped; its test correlates the shelf's ``(branch, code)`` to the label's
    carriers, so it adds no ``library_shelf`` join either: ``central-zz`` stays
    listed and reads as a label with no shelf, as ``annex-s9`` does for an
    anonymous viewer. Ties among them keep the ``text`` order. The label page is
    one statement; staff add their session and user reads.
    """
    create_users(1)
    _seed_shelf_labels()
    models.ShelfLabel.objects.create(
        text="central-zz",
        branch=models.Branch.objects.get(name="Central"),
        shelf_code="ZZ",
    )
    client = Client()
    if staff:
        client.force_login(get_user_model().objects.get(username="staff_1"))

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            f"{{ allLibraryShelfLabels(orderBy: [{{shelfRow: {{code: {direction}}}}}, "
            "{text: ASC}]) { text } }",
            client=client,
        )

    texts = [json_str(row, "text") for row in json_list(data, "allLibraryShelfLabels")]
    present = [
        "central-a1",
        "annex-b2",
        "central-c3",
        "annex-s9",
    ]
    assert texts == _ordered_with_missing(
        direction,
        [text for text in present if text not in missing],
        *missing,
    ), texts
    assert len(captured.captured_queries) == statements, captured.captured_queries
    label_sql = _sql_from_table(captured, "library_shelflabel")
    assert len(label_sql) == 1, label_sql
    assert "JOIN" not in label_sql[0], label_sql[0]


@pytest.mark.django_db
@pytest.mark.parametrize("direction", _DIRECTIONS)
def test_branches_order_by_label_shelves_aggregate_each_carrier_behind_the_labels(
    direction: str,
) -> None:
    """``shelfLabels: { shelf: ... }`` orders branches by one aggregate per carrier, keeping every branch.

    ``BranchOrder.shelf_labels`` is a to-many hop, so the ``shelf`` term is
    ``Min`` / ``Max`` of each carrier (``branch_id``, then ``shelf_code``) over
    a branch's labels. ``ShelfType`` hides the ``secret`` shelf from this
    anonymous viewer, and each aggregate's visibility test correlates the
    shelf's ``(branch, code)`` to the label's own carriers through the label
    join, adding no join to ``library_shelf``: ``Vault``'s only label names a
    shelf that does not exist, so both its aggregates are ``NULL`` and it sorts
    where the direction places a ``NULL``, still listed. One statement serves
    the page.
    """
    _seed_shelf_labels()
    vault = models.Branch.objects.create(name="Vault")
    models.ShelfLabel.objects.create(text="vault-zz", branch=vault, shelf_code="ZZ")

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            f"{{ allLibraryBranches(orderBy: [{{shelfLabels: {{shelf: {direction}}}}}]) "
            "{ name } }",
        )

    assert [
        json_at(row, "name") for row in json_list(data, "allLibraryBranches")
    ] == _ordered_with_missing(
        direction,
        ["Central", "Annex"],
        "Vault",
    ), data
    assert len(captured.captured_queries) == 1, captured.captured_queries
    # Django 6 quotes the subquery alias (``"U0"``); 5.2 does not.
    branch_sql = captured.captured_queries[0]["sql"].replace('"U0"', "U0")
    correlation = (
        'U0."branch_id" = ("library_shelflabel"."branch_id") '
        'AND U0."code" = ("library_shelflabel"."shelf_code")'
    )
    assert branch_sql.count(correlation) == 2, branch_sql
    assert 'JOIN "library_shelf"' not in branch_sql, branch_sql


def _filtered_shelf_label_texts(
    filter_input: str,
    client: Client | None = None,
) -> tuple[list[str], list[str]]:
    """Return the label texts ``filter_input`` keeps and the label statements it ran."""
    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            f"{{ allLibraryShelfLabelsFiltered(filter: {filter_input}) {{ text }} }}",
            client=client,
        )
    texts = sorted(
        json_str(row, "text") for row in json_list(data, "allLibraryShelfLabelsFiltered")
    )
    return texts, _sql_from_table(captured, "library_shelflabel")


def test_shelf_label_filter_input_publishes_the_foreign_object_key_with_a_boolean_null_test() -> (
    None
):
    """The multi-column ``shelf`` key takes the shelf's primary key and ``isNull`` a Boolean.

    ``ShelfType`` is not a Relay node, so ``exact`` takes one raw ``Int`` primary key
    and ``in`` a list of them; ``isNull`` is the Boolean null test a ``ForeignKey``
    key carries, never an identity.
    """
    fields = _introspect_input_fields("ShelfLabelFilterShelfFilterInputType")

    assert fields == {
        "exact": {"kind": "SCALAR", "name": "Int", "ofType": None},
        "in": {"kind": "LIST", "name": None, "ofType": {"kind": "NON_NULL", "name": None}},
        "isNull": {"kind": "SCALAR", "name": "Boolean", "ofType": None},
    }, fields


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("staff", "is_null", "expected"),
    [
        (False, True, ["annex-s9", "central-zz"]),
        (False, False, ["annex-b2", "central-a1", "central-c3"]),
        (True, True, ["central-zz"]),
        (
            True,
            False,
            [
                "annex-b2",
                "annex-s9",
                "central-a1",
                "central-c3",
            ],
        ),
    ],
    ids=[
        "anonymous-true",
        "anonymous-false",
        "staff-true",
        "staff-false",
    ],
)
def test_shelf_labels_filter_shelf_isnull_over_the_shelves_the_viewer_sees(
    *,
    staff: bool,
    is_null: bool,
    expected: list[str],
) -> None:
    """``shelf: { isNull }`` asks whether a label reaches a shelf ``ShelfType`` shows the viewer.

    ``central-zz`` names no shelf, so it is null for everyone; anonymous viewers do
    not see the ``secret`` shelf, so ``annex-s9`` is null for them and not for staff.
    The answer is one ``library_shelflabel`` statement whose visibility test
    correlates on both carriers and joins no ``library_shelf``.
    """
    create_users(1)
    _seed_shelf_labels()
    models.ShelfLabel.objects.create(
        text="central-zz",
        branch=models.Branch.objects.get(name="Central"),
        shelf_code="ZZ",
    )
    client = None
    if staff:
        client = Client()
        client.force_login(get_user_model().objects.get(username="staff_1"))

    texts, label_sql = _filtered_shelf_label_texts(
        f"{{ shelf: {{ isNull: {'true' if is_null else 'false'} }} }}",
        client,
    )

    assert texts == expected, texts
    assert len(label_sql) == 1, label_sql
    # Django 6 quotes the subquery alias (``"U0"``); 5.2 does not.
    sql = label_sql[0].replace('"U0"', "U0")
    assert 'U0."branch_id" = ("library_shelflabel"."branch_id")' in sql, sql
    assert 'U0."code" = ("library_shelflabel"."shelf_code")' in sql, sql
    assert "JOIN" not in sql, sql


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("lookup", "shelves", "expected"),
    [
        ("exact", ["central_a1"], ["central-a1"]),
        ("exact", ["annex_a1"], []),
        ("exact", ["secret"], []),
        ("in", ["central_a1", "secret"], ["central-a1"]),
        ("in", ["annex_a1", "central_c3"], ["central-c3"]),
    ],
    ids=[
        "exact-central-a1",
        "exact-same-code-other-branch",
        "exact-hidden",
        "in-visible-and-hidden",
        "in-same-code-other-branch-and-visible",
    ],
)
def test_shelf_labels_filter_shelf_key_matches_both_carriers_and_never_a_hidden_shelf(
    *,
    lookup: str,
    shelves: list[str],
    expected: list[str],
) -> None:
    """``shelf: { exact }`` / ``{ in }`` match the shelf's ``(branch, code)``, hiding ``secret``.

    ``Annex`` also holds an ``A1`` shelf, which no label names: ``central-a1``
    matches only ``Central``'s ``A1``. The anonymous viewer's key naming the
    hidden ``secret`` shelf matches nothing, as a missing shelf would. Each answer
    is one ``library_shelflabel`` statement.
    """
    _seed_shelf_labels()
    pks = {
        "annex_a1": models.Shelf.objects.create(
            branch=models.Branch.objects.get(name="Annex"),
            code="A1",
        ).pk,
        "central_a1": models.Shelf.objects.get(branch__name="Central", code="A1").pk,
        "central_c3": models.Shelf.objects.get(branch__name="Central", code="C3").pk,
        "secret": models.Shelf.objects.get(topic="secret").pk,
    }
    value = (
        str(pks[shelves[0]])
        if lookup == "exact"
        else "[" + ", ".join(str(pks[name]) for name in shelves) + "]"
    )

    texts, label_sql = _filtered_shelf_label_texts(f"{{ shelf: {{ {lookup}: {value} }} }}")

    assert texts == expected, texts
    assert len(label_sql) == 1, label_sql


_SHELF_LABEL_SHELF_CODES = (
    "query { allLibraryShelfLabels(orderBy: [{ text: ASC }]) { text shelf { code } } }"
)


@pytest.mark.django_db
def test_shelf_label_on_a_hidden_shelf_reads_its_shelf_as_missing_for_anonymous() -> None:
    """A listed label whose non-null ``shelf`` the viewer cannot see is a masked error.

    ``ShelfLabelType`` keeps every label (the cascade helper cannot walk the
    multi-column ``shelf``), so ``annex-s9`` is listed while ``ShelfType`` hides
    its shelf: the relation resolves as a missing row, the non-null ``shelf`` field
    is a completion error at that label's path, masked by the default error policy,
    and the non-null list nulls ``data``.
    """
    _seed_shelf_labels()

    payload = graphql_payload(_SHELF_LABEL_SHELF_CODES)
    correlation_id = json_str(payload, "errors", 0, "extensions", "correlationId")

    assert re.fullmatch("[0-9a-f]{32}", correlation_id), correlation_id
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": "An unexpected error occurred.",
                "locations": [{"line": 1, "column": 64}],
                "path": ["allLibraryShelfLabels", 1, "shelf"],
                "extensions": {"correlationId": correlation_id},
            },
        ],
    }, payload


@pytest.mark.django_db
def test_shelf_label_on_a_hidden_shelf_serves_its_shelf_to_staff() -> None:
    """Staff see the ``secret`` shelf, so every label answers with its shelf."""
    create_users(1)
    _seed_shelf_labels()
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    payload = graphql_payload(_SHELF_LABEL_SHELF_CODES, client=client)

    assert payload == {
        "data": {
            "allLibraryShelfLabels": [
                {"text": "annex-b2", "shelf": {"code": "B2"}},
                {"text": "annex-s9", "shelf": {"code": "S9"}},
                {"text": "central-a1", "shelf": {"code": "A1"}},
                {"text": "central-c3", "shelf": {"code": "C3"}},
            ],
        },
    }, payload


@pytest.mark.parametrize(
    "input_name",
    ["BookInput", "BookPartialInput"],
    ids=["create", "partial"],
)
def test_book_write_inputs_omit_the_non_editable_archive_genres(input_name: str) -> None:
    """``archiveGenres`` is absent from the generated ``Book`` input; ``genres`` is present.

    ``Book.archive_genres`` is a forward many-to-many declared
    ``editable=False``. The editable ``genres`` beside it is the control: a
    generator that stopped reading ``editable`` would publish both.
    """
    fields = _introspect_input_fields(input_name)

    assert "genres" in fields, fields
    assert "archiveGenres" not in fields, fields


@pytest.mark.parametrize("name", ["optionalAttachment", "spareImage"], ids=["blank", "null"])
def test_media_specimen_create_input_requiredness_reads_blank_and_null_separately(
    name: str,
) -> None:
    """Each optional file column is optional through its own arm of the requiredness rule.

    ``optionalAttachment`` is ``blank=True`` only and ``spareImage`` is
    ``null=True`` only, and each renders as a nullable ``Upload``; the required
    ``attachment`` control is pinned by
    ``test_uploads_api.py::test_media_specimen_input_exposes_upload_over_http``.
    """
    fields = _introspect_input_fields("MediaSpecimenInput")

    assert fields[name] == {"kind": "SCALAR", "name": "Upload", "ofType": None}, fields


# ===========================================================================
# Multi-table update writes: every table as an UPDATE, a deleted row ``conflict``
# ===========================================================================

_DESK_UPDATE_INPUTS = {
    "updateLendingDesk": "LendingDeskPartialInput",
    "updateLendingDeskViaForm": "LendingDeskFormPartialInput",
    "updateLendingDeskViaSerializer": "LendingDeskSerializerPartialInput",
}

_DESK_CONFLICT_ERRORS = [
    {
        "field": "id",
        "messages": ["The row was changed or removed by a concurrent operation; retry."],
        "codes": ["conflict"],
    },
]


def _desk_update_mutation(mutation: str) -> type[DjangoMutation]:
    """The mutation class the rebuilt schema serves, read off its module at test time."""
    return {
        "updateLendingDesk": library_schema.UpdateLendingDesk,
        "updateLendingDeskViaForm": library_schema.UpdateLendingDeskViaForm,
        "updateLendingDeskViaSerializer": library_schema.UpdateLendingDeskViaSerializer,
    }[mutation]


def _post_desk_update(mutation: str, desk: models.LendingDesk) -> tuple[object, list[str]]:
    """Rename ``desk`` and change its window count; return the payload and the SQL."""
    query = (
        f"mutation($id: ID!, $d: {_DESK_UPDATE_INPUTS[mutation]}!) {{ "
        f"{mutation}(id: $id, data: $d) {{ result {{ name windowCount }} "
        "errors { field messages codes } } }"
    )
    with CaptureQueriesContext(connection) as captured:
        payload = graphql_payload(
            query,
            variables={"id": desk.pk, "d": {"name": "Renamed Desk", "windowCount": 9}},
        )
    assert "errors" not in payload, payload
    return json_at(payload, "data", mutation), [
        query["sql"] for query in captured.captured_queries
    ]


def _stored_desk(desk_pk: int | None) -> tuple[list[tuple[str, int]], list[str]]:
    """The desk's stored columns, and its parent ``Venue`` row's name alone."""
    return (
        list(
            models.LendingDesk._base_manager.filter(pk=desk_pk).values_list(
                "name",
                "window_count",
            ),
        ),
        list(models.Venue._base_manager.filter(pk=desk_pk).values_list("name", flat=True)),
    )


#: A desk update's statements in every flavor: the locate (and its post-lock re-read where
#: rows lock), then both tables UPDATEd inside the write's own savepoint (the forced update's,
#: or the serializer save's), the re-fetch.
_DESK_UPDATE = [
    "SAVEPOINT",
    "SAVEPOINT",
    "SELECT",
    *post_lock_reread_shapes(1),
    "SAVEPOINT",
    'UPDATE "library_venue"',
    'UPDATE "library_lendingdesk"',
    "RELEASE",
    "SELECT",
    "RELEASE",
    "RELEASE",
]

#: The pipeline's tail after a write it refuses: its rollback and releases.
_REFUSED_TAIL = ["ROLLBACK", "RELEASE", "RELEASE"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mutation", "update_fields"),
    [
        pytest.param(
            "updateLendingDesk",
            frozenset(
                {
                    "name",
                    "opened_on",
                    "lead_ticket",
                    "window_count",
                },
            ),
            id="updateLendingDesk",
        ),
        pytest.param(
            "updateLendingDeskViaForm",
            frozenset(
                {
                    "name",
                    "opened_on",
                    "lead_ticket",
                    "window_count",
                },
            ),
            id="updateLendingDeskViaForm",
        ),
        pytest.param(
            "updateLendingDeskViaSerializer",
            None,
            id="updateLendingDeskViaSerializer",
        ),
    ],
)
def test_lending_desk_update_writes_both_tables_over_http(
    mutation: str,
    update_fields: frozenset[str] | None,
) -> None:
    """A ``LendingDesk`` update writes its ``Venue`` table and its own, each as an ``UPDATE``.

    The model and ``ModelForm`` flavors save the multi-table row with ``force_update`` and
    every loaded non-key column of both tables in ``update_fields``, which a ``pre_save``
    receiver sees: Django's update-only save on each table, so the statements are the two
    ``UPDATE`` s a plain save runs. The serializer flavor's DRF save is a plain one
    (``update_fields=None``) with the same two statements.
    """
    desk = models.LendingDesk.objects.create(name="Desk", window_count=2)
    seen: list[object] = []

    def _record(sender: object, **kwargs: object) -> None:
        del sender
        seen.append(kwargs["update_fields"])

    pre_save.connect(_record, sender=models.LendingDesk, weak=False)
    try:
        result, sql = _post_desk_update(mutation, desk)
    finally:
        _ = pre_save.disconnect(_record, sender=models.LendingDesk)

    assert result == {"result": {"name": "Renamed Desk", "windowCount": 9}, "errors": []}
    assert seen == [update_fields]
    assert statement_shapes(sql) == _DESK_UPDATE
    assert _stored_desk(desk.pk) == ([("Renamed Desk", 9)], ["Renamed Desk"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("mutation", "deleted", "writes"),
    [
        pytest.param(
            "updateLendingDesk",
            "row",
            [
                "SAVEPOINT",
                'UPDATE "library_venue"',
                "ROLLBACK",
                "RELEASE",
                "SELECT",
            ],
            id="updateLendingDesk-row",
        ),
        pytest.param(
            "updateLendingDesk",
            "desk-table",
            [
                "SAVEPOINT",
                'UPDATE "library_venue"',
                'UPDATE "library_lendingdesk"',
                "ROLLBACK",
                "RELEASE",
                "SELECT",
            ],
            id="updateLendingDesk-desk-table",
        ),
        pytest.param(
            "updateLendingDeskViaForm",
            "row",
            [
                "SAVEPOINT",
                'UPDATE "library_venue"',
                "ROLLBACK",
                "RELEASE",
                "SELECT",
            ],
            id="updateLendingDeskViaForm-row",
        ),
        pytest.param(
            "updateLendingDeskViaForm",
            "desk-table",
            [
                "SAVEPOINT",
                'UPDATE "library_venue"',
                'UPDATE "library_lendingdesk"',
                "ROLLBACK",
                "RELEASE",
                "SELECT",
            ],
            id="updateLendingDeskViaForm-desk-table",
        ),
        pytest.param(
            "updateLendingDeskViaSerializer",
            "row",
            [
                "SAVEPOINT",
                'UPDATE "library_venue"',
                'INSERT "library_venue"',
                'INSERT "library_lendingdesk"',
                "RELEASE",
            ],
            id="updateLendingDeskViaSerializer-row",
        ),
        pytest.param(
            "updateLendingDeskViaSerializer",
            "desk-table",
            [
                "SAVEPOINT",
                'UPDATE "library_venue"',
                'UPDATE "library_lendingdesk"',
                'INSERT "library_lendingdesk"',
                "RELEASE",
            ],
            id="updateLendingDeskViaSerializer-desk-table",
        ),
    ],
)
def test_lending_desk_update_of_a_row_deleted_after_authorization_is_conflict_over_http(
    mutation: str,
    deleted: str,
    writes: list[str],
    delete_after_authorization: DeleteAfterAuthorization,
) -> None:
    """A ``LendingDesk`` update whose row is deleted after authorization is ``conflict``.

    ``row`` deletes the whole multi-table row (its ``Venue`` parent with it); ``desk-table``
    deletes only the desk's own table (``keep_parents=True``). The model and ``ModelForm``
    flavors UPDATE each table with ``update_fields`` named, so the table that matches no row
    raises Django's zero-row signal inside the forced update's savepoint and nothing is
    INSERTed: neither the vanished parent row nor the desk row is re-created. The
    serializer flavor's DRF save keeps Django's update-else-insert and re-INSERTs the row,
    which its write witness answers with ``conflict``. Every flavor rolls the transaction
    back, the stand-in delete with it, so the stored desk is as before the request.
    """
    desk = models.LendingDesk.objects.create(name="Desk", window_count=2)
    before = _stored_desk(desk.pk)
    delete_after_authorization(
        _desk_update_mutation(mutation),
        (lambda: models.Venue._base_manager.filter(pk=desk.pk).delete())
        if deleted == "row"
        else (lambda: models.LendingDesk._base_manager.get(pk=desk.pk).delete(keep_parents=True)),
    )

    result, sql = _post_desk_update(mutation, desk)

    assert result == {"result": None, "errors": _DESK_CONFLICT_ERRORS}
    assert statement_shapes_after_last_delete(sql) == [*writes, *_REFUSED_TAIL]
    assert _stored_desk(desk.pk) == before


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", list(_DESK_UPDATE_INPUTS))
def test_lending_desk_update_out_of_range_id_is_not_found_over_http(mutation: str) -> None:
    """A desk update ``id`` past ``Venue.id``'s range is the not-found error; the desk is kept.

    ``LendingDeskType`` is non-Relay, so the ``id`` is the raw primary key, the
    ``venue_ptr`` parent link. The id is held to the integer range the database stores
    for ``Venue.id``, the column the link stores, before the locate query runs, never
    reaching it as a backend ``OverflowError``.
    """
    desk = models.LendingDesk.objects.create(name="Desk", window_count=2)
    before = _stored_desk(desk.pk)

    payload = graphql_payload(
        f"mutation($id: ID!, $d: {_DESK_UPDATE_INPUTS[mutation]}!) {{ "
        f"{mutation}(id: $id, data: $d) {{ result {{ name }} errors {{ field messages }} }} }}",
        variables={"id": str(2**70), "d": {"name": "Renamed Desk"}},
    )

    assert "errors" not in payload, payload
    assert json_at(payload, "data", mutation) == {
        "result": None,
        "errors": [{"field": "id", "messages": ["No matching row found."]}],
    }
    assert _stored_desk(desk.pk) == before


@pytest.mark.django_db
def test_lending_desk_update_naming_a_ticket_that_vanished_with_the_row_is_conflict_over_http(
    delete_after_authorization: DeleteAfterAuthorization,
) -> None:
    """A desk update naming its lead ticket, deleted whole with its tickets, is ``conflict``.

    The stand-in deletes the multi-table desk through its ``Venue`` parent after
    authorization, and the ``CASCADE`` takes the repair ticket the input names as
    ``leadTicketId``. The relation lookup refuses the ticket; the pipeline probes the located
    desk (through its own table), finds it gone and answers ``conflict`` on ``id`` instead of
    the relation's ``invalid``. The transaction rolls back: the desk, its venue row and its
    ticket are stored as before.
    """
    desk = models.LendingDesk.objects.create(name="Desk", window_count=2)
    ticket = models.RepairTicket.objects.create(code="T-1", venue=desk)
    _ = models.Venue._base_manager.filter(pk=desk.pk).update(lead_ticket=ticket)

    def stored() -> object:
        return (
            _stored_desk(desk.pk),
            list(models.Venue._base_manager.filter(pk=desk.pk).values_list("lead_ticket_id")),
            models.RepairTicket._base_manager.filter(venue_id=desk.pk).count(),
        )

    before = stored()
    delete_after_authorization(
        library_schema.UpdateLendingDesk,
        lambda: models.Venue._base_manager.filter(pk=desk.pk).delete(),
    )

    with CaptureQueriesContext(connection) as captured:
        payload = graphql_payload(
            "mutation($id: ID!, $d: LendingDeskPartialInput!) { "
            "updateLendingDesk(id: $id, data: $d) { result { name } "
            "errors { field messages codes } } }",
            variables={"id": desk.pk, "d": {"name": "Renamed Desk", "leadTicketId": ticket.pk}},
        )

    assert "errors" not in payload, payload
    assert json_at(payload, "data", "updateLendingDesk") == {
        "result": None,
        "errors": _DESK_CONFLICT_ERRORS,
    }
    sql = [query["sql"] for query in captured.captured_queries]
    assert statement_shapes_after_last_delete(sql) == ["SELECT", "SELECT", *_REFUSED_TAIL]
    assert select_tables_after_last_delete(sql) == [
        '"library_repairticket"',
        '"library_lendingdesk"',
    ]
    assert stored() == before


# ===========================================================================
# A key into a parent-link chain: typed and checked through the column it stores
# ===========================================================================

_KIOSK_FAULT_CREATES = {
    "createKioskFault": "KioskFaultInput",
    "createKioskFaultViaForm": "KioskFaultFormInput",
    "createKioskFaultViaSerializer": "KioskFaultSerializerInput",
}


@pytest.mark.parametrize("mutation", list(_KIOSK_FAULT_CREATES))
def test_kiosk_fault_inputs_type_the_kiosk_key_from_the_column_its_chain_stores(
    mutation: str,
) -> None:
    """``kioskId`` is ``Int!`` in every flavor: the ``Venue.id`` two parent links down.

    ``SelfServeDeskType`` is non-Relay, so the key is a raw id typed from the target's
    primary key, and that key is the ``lendingdesk_ptr`` parent link, which stores
    ``LendingDesk.venue_ptr``, which stores ``Venue.id``. A walk stopping one link short
    lands on ``venue_ptr``, a relation with no scalar.
    """
    fields = _introspect_input_fields(_KIOSK_FAULT_CREATES[mutation])

    assert fields == {
        "kioskId": {"kind": "NON_NULL", "name": None, "ofType": {"kind": "SCALAR", "name": "Int"}},
        "note": {"kind": "NON_NULL", "name": None, "ofType": {"kind": "SCALAR", "name": "String"}},
    }


def _post_kiosk_fault(mutation: str, kiosk_id: int | None) -> object:
    """Create a fault naming ``kiosk_id`` through ``mutation``; return its payload."""
    payload = graphql_payload(
        f"mutation($d: {_KIOSK_FAULT_CREATES[mutation]}!) {{ {mutation}(data: $d) {{ "
        "result { note kiosk { kioskCode } } errors { field messages codes path } } }",
        variables={"d": {"kioskId": kiosk_id, "note": "Jammed"}},
    )
    assert "errors" not in payload, payload
    return json_at(payload, "data", mutation)


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", list(_KIOSK_FAULT_CREATES))
def test_kiosk_fault_create_naming_a_visible_kiosk_stores_it(mutation: str) -> None:
    """A visible kiosk's id stores the fault against that kiosk."""
    _seed_desks()
    kiosk = models.SelfServeDesk.objects.get(name="Lobby Kiosk")

    result = _post_kiosk_fault(mutation, kiosk.pk)

    assert result == {"result": {"note": "Jammed", "kiosk": {"kioskCode": "K-1"}}, "errors": []}
    assert list(models.KioskFault.objects.values_list("kiosk_id", "note")) == [
        (kiosk.pk, "Jammed"),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", list(_KIOSK_FAULT_CREATES))
@pytest.mark.parametrize("kiosk", ["hidden", "missing"])
def test_kiosk_fault_create_naming_a_hidden_or_missing_kiosk_is_the_relation_error(
    mutation: str,
    kiosk: str,
) -> None:
    """A kiosk under a closed venue, or no kiosk at all, is the relation error; nothing is written.

    ``SelfServeDeskType`` cascades over its parent links into ``VenueType``, which hides
    venues named ``Closed ...``, so the ``Closed Annex Kiosk`` row exists but is not
    visible; the missing id is one past every venue.
    """
    _seed_desks()
    hidden = models.SelfServeDesk.objects.get(name="Closed Annex Kiosk")
    last = models.Venue.objects.order_by("pk").last()
    assert last is not None
    assert last.pk is not None
    kiosk_id = {"hidden": hidden.pk, "missing": last.pk + 1}[kiosk]

    result = _post_kiosk_fault(mutation, kiosk_id)

    assert result == {
        "result": None,
        "errors": [
            {
                "field": "kioskId",
                "messages": ["Invalid id for relation 'kioskId'."],
                "codes": ["invalid"],
                "path": ["kioskId"],
            },
        ],
    }
    assert not models.KioskFault.objects.exists()


# ===========================================================================
# A serializer write saving a proxy or multi-table child of its model's rows
# ===========================================================================

_FAMILY_DAY = datetime.date(2024, 1, 2)

_VenueT = TypeVar("_VenueT", bound=models.Venue)

#: The request's consumer scenario: what the write does (``scenario``), the class key of
#: the row it saves (``saved``) and, for a create promoting a stored venue, its key.
_FAMILY: dict[str, str] = {}

#: The classes the scenario keys name, rebuilt per request (the proxies are test-local).
_FAMILY_CLASSES: dict[str, type[models.Venue]] = {}


def _proxy_of(base: type[_VenueT], name: str) -> type[_VenueT]:
    """Declare a test-local proxy of ``base``; the registry restore drops it after the test."""
    meta = type("Meta", (), {"proxy": True, "app_label": "library"})
    made = type(name, (base,), {"Meta": meta, "__module__": __name__})
    assert issubclass(made, base)
    return made


def _install_family_classes() -> None:
    """Key the shipped ``Venue`` family and three test-local proxies for the scenario."""
    _FAMILY_CLASSES.update(
        venue=models.Venue,
        venue_proxy=_proxy_of(models.Venue, "SavedVenueProxy"),
        open_venue=models.OpenVenue,
        open_venue_proxy=_proxy_of(models.OpenVenue, "SavedOpenVenueProxy"),
        desk=models.LendingDesk,
        desk_proxy=_proxy_of(models.LendingDesk, "SavedLendingDeskProxy"),
        self_serve=models.SelfServeDesk,
    )


def _child_values(cls: type[models.Venue]) -> dict[str, object]:
    """The local columns a new row of ``cls`` stores beside its ``Venue`` ones."""
    values: dict[str, object] = {}
    if issubclass(cls, models.LendingDesk):
        values["window_count"] = 3
    if issubclass(cls, models.SelfServeDesk):
        values["kiosk_code"] = "K-9"
    return values


def _family_write(instance: models.Venue | None) -> models.Venue:
    """The consumer's ``create()`` / ``update()``: save the scenario's row, return it.

    ``save`` saves a new row of the class (create) or the located row loaded as it
    (update), named ``Saved``. ``promote`` saves a new row of the multi-table class over a
    stored plain ``Venue`` row (the located one on an update), turning that row into a
    child. ``replace`` deletes the located row, stores it again through the class and then
    saves the located instance, renamed ``Saved``.
    """
    scenario = _FAMILY["scenario"]
    cls = _FAMILY_CLASSES[_FAMILY["saved"]]
    if scenario == "save":
        if instance is None:
            row = cls(name="Saved", opened_on=_FAMILY_DAY, **_child_values(cls))
        else:
            row = cls._base_manager.get(pk=instance.pk)
            row.name = "Saved"
        row.save()
        return row
    if scenario == "promote":
        key = int(_FAMILY["promoted"]) if instance is None else instance.pk
        child = cls(pk=key, name="Promoted", opened_on=_FAMILY_DAY, **_child_values(cls))
        child.save()
        return child
    assert instance is not None
    _ = models.Venue._base_manager.filter(pk=instance.pk).delete()
    cls(pk=instance.pk, name="Replaced", opened_on=_FAMILY_DAY).save()
    instance.name = "Saved"
    instance.save()
    return instance


class FamilySerializer(ModelSerializerBase[models.Venue]):
    """A ``Venue``-family serializer whose ``create()`` / ``update()`` save the scenario's row."""

    @override
    def create(self, validated_data: dict[str, object]) -> models.Venue:
        return _family_write(None)

    @override
    def update(self, instance: models.Venue, validated_data: dict[str, object]) -> models.Venue:
        return _family_write(instance)


class FamilyVenueSerializer(FamilySerializer):
    """The ``Venue`` serializer."""

    class Meta:
        model = models.Venue
        fields = ("name",)


class FamilyOpenVenueSerializer(FamilySerializer):
    """The ``OpenVenue`` proxy's serializer."""

    class Meta:
        model = models.OpenVenue
        fields = ("name",)


class FamilyLendingDeskSerializer(FamilySerializer):
    """The ``LendingDesk`` child's serializer."""

    class Meta:
        model = models.LendingDesk
        fields = ("name",)


def _family_schema() -> DjangoSchema:
    """A serializer create and update per backing model: ``Venue``, a proxy, a child."""

    class VenueNode(DjangoType):
        class Meta:
            model = models.Venue
            fields = ("id", "name")

    class OpenVenueNode(DjangoType):
        class Meta:
            model = models.OpenVenue
            fields = ("id", "name")

    class LendingDeskNode(DjangoType):
        class Meta:
            model = models.LendingDesk
            fields = ("id", "name")

    class CreateVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyVenueSerializer
            operation = "create"
            permission_classes = []

    class UpdateVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyVenueSerializer
            operation = "update"
            permission_classes = []

    class CreateOpenVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyOpenVenueSerializer
            operation = "create"
            permission_classes = []

    class UpdateOpenVenueFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyOpenVenueSerializer
            operation = "update"
            permission_classes = []

    class CreateLendingDeskFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyLendingDeskSerializer
            operation = "create"
            permission_classes = []

    class UpdateLendingDeskFamily(SerializerMutation):
        class Meta:
            serializer_class = FamilyLendingDeskSerializer
            operation = "update"
            permission_classes = []

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        create_venue_family = DjangoMutationField(CreateVenueFamily)
        update_venue_family = DjangoMutationField(UpdateVenueFamily)
        create_open_venue_family = DjangoMutationField(CreateOpenVenueFamily)
        update_open_venue_family = DjangoMutationField(UpdateOpenVenueFamily)
        create_lending_desk_family = DjangoMutationField(CreateLendingDeskFamily)
        update_lending_desk_family = DjangoMutationField(UpdateLendingDeskFamily)

    del VenueNode, OpenVenueNode, LendingDeskNode
    finalize_django_types()
    return DjangoSchema(query=Query, mutation=Mutation, error_policy={"enabled": False})


#: (root field suffix, serializer class name) per backing model.
_FAMILY_BACKINGS = {
    "venue": ("VenueFamily", "FamilyVenueSerializer"),
    "open_venue": ("OpenVenueFamily", "FamilyOpenVenueSerializer"),
    "desk": ("LendingDeskFamily", "FamilyLendingDeskSerializer"),
}


def _post_family(backing: str, located: int | None) -> tuple[JSONObject, list[str], int]:
    """POST ``backing``'s create, or its update of ``located``.

    Returns the payload, the SQL and the root field's 1-based column in the document.
    """
    suffix, serializer = _FAMILY_BACKINGS[backing]
    if located is None:
        root = f"create{suffix}"
        document = (
            f"mutation($d: {serializer}Input!) {{ {root}(data: $d) {{ {_FAMILY_RESULT} }} }}"
        )
        variables: JSONObject = {"d": {"name": "Sent"}}
    else:
        root = f"update{suffix}"
        document = (
            f"mutation($id: ID!, $d: {serializer}PartialInput!) "
            f"{{ {root}(id: $id, data: $d) {{ {_FAMILY_RESULT} }} }}"
        )
        variables = {"id": located, "d": {"name": "Sent"}}
    _install_family_classes()
    _FAMILY_WRITES["schema"] = _family_schema()
    try:
        with (
            override_settings(ROOT_URLCONF=__name__),
            CaptureQueriesContext(connection) as captured,
        ):
            payload = graphql_payload(document, variables=variables, url="/graphql-venue-family/")
    finally:
        _FAMILY_WRITES["schema"] = None
        _FAMILY_CLASSES.clear()
    return payload, [query["sql"] for query in captured.captured_queries], document.index(root) + 1


def _family_writes(sql: list[str]) -> list[str]:
    """The ``INSERT`` and ``UPDATE`` shapes of ``sql``, in order."""
    return [shape for shape in statement_shapes(sql) if shape.split()[0] in {"INSERT", "UPDATE"}]


_FAMILY_RESULT = "result { name } errors { field messages codes }"


def _stored_venues() -> tuple[list[tuple[int | None, str]], list[int | None], list[int | None]]:
    """Every venue's key and name, every desk's key and every kiosk's key."""
    return (
        list(models.Venue._base_manager.order_by("pk").values_list("pk", "name")),
        list(models.LendingDesk._base_manager.order_by("pk").values_list("pk", flat=True)),
        list(models.SelfServeDesk._base_manager.order_by("pk").values_list("pk", flat=True)),
    )


def _plain_venue(name: str) -> int:
    """Store a plain, opened ``Venue`` row; return its key."""
    return saved_pk(models.Venue.objects.create(name=name, opened_on=_FAMILY_DAY))


@pytest.fixture
def family_scenario() -> Generator[dict[str, str], None, None]:
    """The family scenario, cleared after the test."""
    try:
        yield _FAMILY
    finally:
        _FAMILY.clear()


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db
@pytest.mark.parametrize("op", ["create", "update"])
@pytest.mark.parametrize(
    ("backing", "saved"),
    [
        pytest.param("venue", "venue", id="venue-venue"),
        pytest.param("venue", "open_venue", id="venue-proxy"),
        pytest.param("venue", "open_venue_proxy", id="venue-proxy-of-proxy"),
        pytest.param("venue", "desk", id="venue-child"),
        pytest.param("venue", "desk_proxy", id="venue-proxy-of-child"),
        pytest.param("venue", "self_serve", id="venue-grandchild"),
        pytest.param("open_venue", "open_venue", id="proxy-proxy"),
        pytest.param("open_venue", "open_venue_proxy", id="proxy-proxy-of-proxy"),
        pytest.param("desk", "desk", id="child-child"),
        pytest.param("desk", "desk_proxy", id="child-proxy-of-child"),
        pytest.param("desk", "self_serve", id="child-grandchild"),
    ],
)
def test_a_serializer_returning_a_row_of_its_models_family_answers_the_payload(
    backing: str,
    saved: str,
    op: str,
    family_scenario: dict[str, str],
) -> None:
    """A ``create()`` / ``update()`` saving a proxy or child row of the model answers it.

    The consumer saves a row of another class and returns it: a proxy, a proxy of a
    proxy, a multi-table child or grandchild, a proxy of a child. Django sends its
    ``post_save`` with that class, and each saves the model's rows, so the write witness
    records the save and the returned row is the one observed being INSERTED (create) or
    UPDATED (update), and the payload answers it.
    """
    kiosk = models.SelfServeDesk.objects.create(
        name="Kiosk",
        opened_on=_FAMILY_DAY,
        window_count=1,
        kiosk_code="K-0",
    )
    located = saved_pk(kiosk) if op == "update" else None
    venues, desks, kiosks = _stored_venues()
    family_scenario.update(scenario="save", saved=saved)

    payload, _sql, _column = _post_family(backing, located)

    assert payload == {
        "data": {
            f"{op}{_FAMILY_BACKINGS[backing][0]}": {"result": {"name": "Saved"}, "errors": []},
        },
    }
    if op == "update":
        assert _stored_venues() == ([(located, "Saved")], desks, kiosks)
        return
    stored_venues, stored_desks, stored_kiosks = _stored_venues()
    [(new, name)] = [entry for entry in stored_venues if entry not in venues]
    assert name == "Saved"
    child = saved in {"desk", "desk_proxy", "self_serve"}
    assert stored_desks == [*desks, new] if child else desks
    assert stored_kiosks == [*kiosks, new] if saved == "self_serve" else kiosks


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db
@pytest.mark.parametrize("op", ["create", "update"])
def test_a_proxy_serializer_returning_its_concrete_base_row_is_refused(
    op: str,
    family_scenario: dict[str, str],
) -> None:
    """The ``OpenVenue`` serializer's write returning a plain ``Venue`` row is refused.

    The concrete base is not a subclass of the proxy, so the returned row is not an
    ``OpenVenue`` instance: a ``ConfigurationError``, the write rolled back.
    """
    located = _plain_venue("Located") if op == "update" else None
    before = _stored_venues()
    family_scenario.update(scenario="save", saved="venue")

    payload, _sql, column = _post_family("open_venue", located)

    mutation = f"{op.title()}OpenVenueFamily"
    assert payload == {
        "data": None,
        "errors": [
            {
                "message": (
                    f"SerializerMutation {mutation}: FamilyOpenVenueSerializer.save() returned "
                    "<Venue: Saved>, not a OpenVenue instance; the serializer's "
                    "create()/update() must return the written model row."
                ),
                "locations": [{"line": 1, "column": column}],
                "path": [f"{op}OpenVenueFamily"],
            },
        ],
    }
    assert _stored_venues() == before


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db
@pytest.mark.parametrize(
    ("saved", "writes"),
    [
        pytest.param(
            "desk",
            [
                'UPDATE "library_venue"',
                'UPDATE "library_lendingdesk"',
                'INSERT "library_lendingdesk"',
            ],
            id="child",
        ),
        pytest.param(
            "self_serve",
            [
                'UPDATE "library_venue"',
                'UPDATE "library_lendingdesk"',
                'INSERT "library_lendingdesk"',
                'INSERT "library_selfservedesk"',
            ],
            id="grandchild",
        ),
    ],
)
def test_a_create_promoting_a_stored_venue_to_a_child_is_its_insert(
    saved: str,
    writes: list[str],
    family_scenario: dict[str, str],
) -> None:
    """A create saving a child row over a stored plain ``Venue`` answers the child.

    The consumer's ``create()`` saves a new ``LendingDesk`` (or ``SelfServeDesk``) whose key
    is a stored plain venue's: Django UPDATEs the ``Venue`` row and INSERTs the child's own
    table rows, and its ``post_save`` reports ``created=True``. The witness takes that
    answer as the create's INSERT, so the payload answers the promoted row.
    """
    promoted = _plain_venue("Plain")
    family_scenario.update(scenario="promote", saved=saved, promoted=str(promoted))

    payload, sql, _column = _post_family("venue", None)

    assert payload == {
        "data": {"createVenueFamily": {"result": {"name": "Promoted"}, "errors": []}},
    }
    assert _family_writes(sql) == writes
    kiosks = [promoted] if saved == "self_serve" else []
    assert _stored_venues() == ([(promoted, "Promoted")], [promoted], kiosks)


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "saved",
    [pytest.param("desk", id="child"), pytest.param("self_serve", id="grandchild")],
)
def test_an_update_promoting_its_located_venue_to_a_child_is_refused(
    saved: str,
    family_scenario: dict[str, str],
) -> None:
    """An update saving a child row over the located plain ``Venue`` is no update of it.

    The child's ``post_save`` reports ``created=True`` under the authorized key, but for
    the child's own table, not the located row's: the located ``Venue`` row was UPDATEd,
    never re-INSERTed, so it is not the ``conflict`` of a vanished row. No ``created=False``
    save of the returned row was observed, so the result is refused as never UPDATED and
    the write rolled back.
    """
    located = _plain_venue("Located")
    before = _stored_venues()
    family_scenario.update(scenario="promote", saved=saved)

    payload, _sql, column = _post_family("venue", located)

    assert payload == {
        "data": None,
        "errors": [
            {
                "message": (
                    "SerializerMutation UpdateVenueFamily: FamilyVenueSerializer.save() "
                    "returned a Venue that was never observed being UPDATED on alias "
                    "'default' during the save; the serializer must persist and return the "
                    "same row addressed by this mutation. Returning an existing instance "
                    "without saving it is not an update and cannot be reported as success."
                ),
                "locations": [{"line": 1, "column": column}],
                "path": ["updateVenueFamily"],
            },
        ],
    }
    assert _stored_venues() == before


@pytest.mark.usefixtures("private_registry")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "saved",
    [pytest.param("venue", id="concrete-base"), pytest.param("venue_proxy", id="sibling-proxy")],
)
def test_an_update_restoring_its_row_through_a_class_outside_the_family_answers_the_payload(
    saved: str,
    family_scenario: dict[str, str],
) -> None:
    """A row the ``OpenVenue`` update INSERTs through the concrete base or a sibling is unread.

    The consumer's ``update()`` deletes the located row, stores it again under its key
    through ``Venue`` or another proxy of it, then saves the located ``OpenVenue``, an
    UPDATE. Neither class is a subclass of the proxy, so their INSERT under the
    authorized key is not recorded and is never read as the re-INSERT of a vanished row:
    the observed UPDATE answers the payload.
    """
    located = _plain_venue("Located")
    family_scenario.update(scenario="replace", saved=saved)

    payload, sql, _column = _post_family("open_venue", located)

    assert payload == {
        "data": {"updateOpenVenueFamily": {"result": {"name": "Saved"}, "errors": []}},
    }
    # The restore's update-else-insert, then the located row's UPDATE.
    assert _family_writes(sql) == [
        'UPDATE "library_venue"',
        'INSERT "library_venue"',
        'UPDATE "library_venue"',
    ]
    assert _stored_venues() == ([(located, "Saved")], [], [])
