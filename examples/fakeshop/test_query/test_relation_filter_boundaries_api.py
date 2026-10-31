"""Native HTTP relation filters over ancestor models, child models and admitted querysets.

Each consumer declares its RelatedFilter and applies a
public JSON argument to an explicit ordered root queryset. Plain output types
and an unfiltered sibling retain every root; target-type visibility and the
declaration's queryset constrain only the relation being filtered. Shipped
filters do not declare these ancestor/descendant target-set mismatches or the
forward nonnullable Shelf admission boundary.
"""

from collections.abc import Sequence
from functools import wraps

import pytest
import strawberry
from apps.library import models
from django.db import models as django_models
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from django_filters import BooleanFilter, CharFilter
from graphql_client import JSONObject, RecordCompiledSql, graphql_payload
from strawberry.scalars import JSON
from typing_extensions import override

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet, RelatedFilter
from django_strawberry_framework.views import DjangoGraphQLView

pytestmark = pytest.mark.usefixtures("private_registry")
_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-mti-queryset-boundaries/", _graphql_view)]


def _schema(query: type[object], targets: Sequence[type[DjangoType]]) -> DjangoSchema:
    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=query,
        types=targets,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _where(python_path: Sequence[str], value: object) -> JSONObject:
    """Keep the consumer's public FilterSet mapping unchanged across JSON transport."""
    assert python_path
    result: JSONObject = {python_path[-1]: value}
    for name in reversed(python_path[:-1]):
        result = {name: result}
    return result


def _post(
    schema: DjangoSchema,
    where: JSONObject,
    selection: str,
    *,
    extra: str = "",
) -> JSONObject:
    document = (
        "query($where: JSON!) { "
        f"rows(where: $where) {{ {selection} }} allRows {{ {selection} }} {extra} }}"
    )
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            return graphql_payload(
                document,
                variables={"where": where},
                url="/graphql-mti-queryset-boundaries/",
            )
    finally:
        _CURRENT["schema"] = None


def _root_sql(sqls: Sequence[str], model: type[django_models.Model]) -> list[str]:
    return [
        sql
        for sql in sqls
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith(f'"{model._meta.db_table}"')
    ]


def _active_sql(
    sqls: Sequence[str],
    root_model: type[django_models.Model],
    targets: Sequence[type[django_models.Model]],
    carriers: Sequence[str],
) -> None:
    roots = _root_sql(sqls, root_model)
    assert len(roots) == 2, sqls
    filtered = [sql for sql in roots if "EXISTS" in sql.upper()]
    assert len(filtered) == 1, roots
    assert all("DISTINCT" not in sql.upper() for sql in roots), roots
    for target in targets:
        assert f'"{target._meta.db_table}"' in filtered[0], filtered
    for column in carriers:
        assert f'"{column}"' in filtered[0], filtered


def _ancestor_schema() -> DjangoSchema:
    class AncestorChild(FilterSet):
        class Meta:
            model = models.Venue
            fields = {"name": ["exact"]}

    class KioskParent(FilterSet):
        branch = RelatedFilter(AncestorChild, field_name="lendingdesk_ptr")

        class Meta:
            model = models.SelfServeDesk
            fields = {"id": ["exact"]}

    class VenueTarget(DjangoType):
        class Meta:
            model = models.Venue
            fields = ("name",)

    class KioskOutput(DjangoType):
        class Meta:
            model = models.SelfServeDesk
            fields = ("name", "kiosk_code")

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: JSON,
        ) -> django_models.QuerySet[models.SelfServeDesk]:
            return KioskParent.apply_sync(where, models.SelfServeDesk.objects.order_by("pk"), info)

        def _all_rows(self) -> django_models.QuerySet[models.SelfServeDesk]:
            return models.SelfServeDesk.objects.order_by("pk")

        def _all_venues(self) -> django_models.QuerySet[models.Venue]:
            return models.Venue.objects.order_by("pk")

        rows: django_models.QuerySet[models.SelfServeDesk] = strawberry.field(
            resolver=_rows,
            graphql_type=list[KioskOutput],
        )
        all_rows: django_models.QuerySet[models.SelfServeDesk] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[KioskOutput],
        )
        all_venues: django_models.QuerySet[models.Venue] = strawberry.field(
            resolver=_all_venues,
            graphql_type=list[VenueTarget],
        )

    return _schema(Query, (VenueTarget,))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name",
    ["kiosk", "other kiosk", "plain"],
    ids=["kiosk", "other-kiosk", "plain-venue"],
)
@pytest.mark.parametrize("spelling", ["expanded", "nested"])
def test_parent_link_branch_can_filter_with_its_venue_ancestor_set(
    name: str,
    spelling: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A Venue child set matches each kiosk's inherited name, never an unrelated plain Venue."""
    models.Venue.objects.create(name="plain")
    for label in ("kiosk", "other kiosk"):
        models.SelfServeDesk.objects.create(name=label, kiosk_code=label + "-code")
    schema = _ancestor_schema()
    path = ("branch__name",) if spelling == "expanded" else ("branch", "name")
    all_kiosks = [
        {"name": label, "kioskCode": label + "-code"} for label in ("kiosk", "other kiosk")
    ]
    expected = [] if name == "plain" else [{"name": name, "kioskCode": name + "-code"}]
    sql = record_compiled_sql()
    assert _post(
        schema,
        _where(path, name),
        "name kioskCode",
        extra="allVenues { name }",
    ) == {
        "data": {
            "rows": expected,
            "allRows": all_kiosks,
            "allVenues": [{"name": label} for label in ("plain", "kiosk", "other kiosk")],
        },
    }
    _active_sql(
        sql,
        models.SelfServeDesk,
        (models.LendingDesk, models.Venue),
        ("lendingdesk_ptr_id", "venue_ptr_id"),
    )


def _descendant_schema(*, include_no_desk: bool) -> DjangoSchema:
    class DeskChild(FilterSet):
        class Meta:
            model = models.LendingDesk
            fields = {"window_count": ["exact"]}

    class TicketParent(FilterSet):
        desk = RelatedFilter(DeskChild, field_name="venue")
        if include_no_desk:
            no_desk = BooleanFilter(field_name="venue", lookup_expr="isnull")

        class Meta:
            model = models.RepairTicket
            fields = {"code": ["exact"]}

    class ScopedDesk(DjangoType):
        class Meta:
            model = models.LendingDesk
            fields = ("name", "window_count")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: django_models.QuerySet[models.LendingDesk],
            info: strawberry.Info[object, object],
        ) -> django_models.QuerySet[models.LendingDesk]:
            del info
            return queryset.exclude(name__startswith="secret")

    class TicketOutput(DjangoType):
        class Meta:
            model = models.RepairTicket
            fields = ("code",)

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: JSON,
        ) -> django_models.QuerySet[models.RepairTicket]:
            return TicketParent.apply_sync(where, models.RepairTicket.objects.order_by("pk"), info)

        def _all_rows(self) -> django_models.QuerySet[models.RepairTicket]:
            return models.RepairTicket.objects.order_by("pk")

        rows: django_models.QuerySet[models.RepairTicket] = strawberry.field(
            resolver=_rows,
            graphql_type=list[TicketOutput],
        )
        all_rows: django_models.QuerySet[models.RepairTicket] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[TicketOutput],
        )

    return _schema(Query, (ScopedDesk,))


def _ticket_world(window_count: int) -> None:
    venues = [
        ("plain", models.Venue.objects.create(name="plain")),
        ("desk", models.LendingDesk.objects.create(name="desk", window_count=window_count)),
        (
            "secret",
            models.LendingDesk.objects.create(name="secret desk", window_count=window_count),
        ),
    ]
    for code, venue in venues:
        models.RepairTicket.objects.create(code=code, venue=venue)


def _tickets(codes: Sequence[str]) -> JSONObject:
    return {
        "data": {
            "rows": [{"code": code} for code in codes],
            "allRows": [{"code": code} for code in ("plain", "desk", "secret")],
        },
    }


@pytest.mark.django_db
@pytest.mark.parametrize("case", ["visible-child", "no-visible-child"])
def test_child_model_branch_distinguishes_plain_venues_from_visible_and_hidden_desks(
    case: str,
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """A child-set branch correlates a Venue FK with only visible LendingDesk PKs."""
    _ticket_world(0)
    schema = _descendant_schema(include_no_desk=True)
    path, value, codes = (
        (("desk", "window_count"), 0, ["desk"])
        if case == "visible-child"
        else (("no_desk",), True, ["plain", "secret"])
    )
    sql = record_compiled_sql()
    assert _post(schema, _where(path, value), "code") == _tickets(codes)
    _active_sql(
        sql,
        models.RepairTicket,
        (models.LendingDesk, models.Venue),
        ("venue_id", "venue_ptr_id"),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path", "value", "codes"),
    [
        (("desk__window_count",), None, ["plain", "desk", "secret"]),
        (("desk__window_count",), 2, ["desk"]),
        (("desk", "window_count"), 2, ["desk"]),
        (("desk__window_count",), 0, []),
        (("desk", "window_count"), 0, []),
    ],
    ids=[
        "absent-flat",
        "matching-flat",
        "matching-nested",
        "missing-flat",
        "missing-nested",
    ],
)
def test_expanded_child_column_runs_on_the_descendant_model_where_it_resolves(
    path: tuple[str, ...],
    value: int | None,
    codes: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """The desk-only column works flat/nested; an absent flat value leaves all Ticket roots."""
    _ticket_world(2)
    schema = _descendant_schema(include_no_desk=False)
    sql = record_compiled_sql()
    assert _post(schema, _where(path, value), "code") == _tickets(codes)
    if value is None:
        roots = _root_sql(sql, models.RepairTicket)
        assert len(roots) == 2, sql
        assert all("EXISTS" not in statement.upper() for statement in roots), roots
        assert all('"library_lendingdesk"' not in statement for statement in sql), sql
        assert all('"library_venue"' not in statement for statement in sql), sql
    else:
        _active_sql(
            sql,
            models.RepairTicket,
            (models.LendingDesk, models.Venue),
            ("venue_id", "venue_ptr_id"),
        )


def _admission_schema() -> DjangoSchema:
    class ShelfChild(FilterSet):
        class Meta:
            model = models.Shelf
            fields = {"topic": ["exact"]}

    class BookParent(FilterSet):
        shelf = RelatedFilter(
            ShelfChild,
            field_name="shelf",
            queryset=models.Shelf.objects.filter(code="kept"),
        )
        no_shelf = BooleanFilter(field_name="shelf", lookup_expr="isnull")
        not_topic = CharFilter(field_name="shelf__topic", exclude=True)

        class Meta:
            model = models.Book
            fields = {"shelf__topic": ["exact"]}

    class ShelfTarget(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("code", "topic")

    class BookOutput(DjangoType):
        class Meta:
            model = models.Book
            fields = ("title",)

    @strawberry.type
    class Query:
        def _rows(
            self,
            info: strawberry.Info[object, object],
            where: JSON,
        ) -> django_models.QuerySet[models.Book]:
            return BookParent.apply_sync(where, models.Book.objects.order_by("pk"), info)

        def _all_rows(self) -> django_models.QuerySet[models.Book]:
            return models.Book.objects.order_by("pk")

        rows: django_models.QuerySet[models.Book] = strawberry.field(
            resolver=_rows,
            graphql_type=list[BookOutput],
        )
        all_rows: django_models.QuerySet[models.Book] = strawberry.field(
            resolver=_all_rows,
            graphql_type=list[BookOutput],
        )

    return _schema(Query, (ShelfTarget,))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("path", "value", "titles"),
    [
        (("shelf__topic",), "t", ["kept"]),
        (("no_shelf",), True, ["outside"]),
        (("not_topic",), "t", ["outside", "kept-other"]),
    ],
    ids=["matching-admitted", "excluded-is-absent", "exclude-matching-admitted"],
)
def test_declaration_queryset_is_absence_for_a_forward_nonnullable_relation(
    *,
    path: tuple[str, ...],
    value: str | bool,
    titles: list[str],
    record_compiled_sql: RecordCompiledSql,
) -> None:
    """An excluded existing Shelf is absent to null/exclude; admitted nonmatches remain distinct."""
    branch = models.Branch.objects.create(name="Admission boundary")
    other_branch = models.Branch.objects.create(name="Other admitted parent")
    kept = models.Shelf.objects.create(branch=branch, code="kept", topic="t")
    outside = models.Shelf.objects.create(branch=branch, code="outside", topic="t")
    kept_other = models.Shelf.objects.create(branch=other_branch, code="kept", topic="other")
    for title, shelf in [("kept", kept), ("outside", outside), ("kept-other", kept_other)]:
        models.Book.objects.create(title=title, shelf=shelf)
    schema = _admission_schema()
    sql = record_compiled_sql()
    assert _post(schema, _where(path, value), "title") == {
        "data": {
            "rows": [{"title": title} for title in titles],
            "allRows": [{"title": title} for title in ("kept", "outside", "kept-other")],
        },
    }
    columns = ("shelf_id", "code") if path[0] == "no_shelf" else ("shelf_id", "code", "topic")
    _active_sql(sql, models.Book, (models.Shelf,), columns)
