"""PostgreSQL tests for internal JSON adapters, connection cleanup and EXPLAIN index usability.

Consumer-visible strategy parity and custom-through joins are exercised over HTTP
in examples/fakeshop/test_query/test_lateral_strategy_api.py. The JSON cursor
carrier here is intentionally disallowed by the public cursor-field contract;
EXPLAIN and executor-thread connection handles have no GraphQL representation.
"""

import datetime
import threading
import uuid
from typing import Protocol, TypeVar, runtime_checkable

import pytest
from apps.library.models import Issue, Periodical
from apps.scalars.models import ScalarSpecimen
from django.db import connection as db_connection
from django.db import connections as django_connections
from django.db.models import Model, Prefetch
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from django_strawberry_framework.keyset import (
    KeysetCursor,
    KeysetSeek,
    cursor_columns_for,
)
from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
from django_strawberry_framework.optimizer.lateral_fetch import (
    LATERAL_STRATEGY,
    LateralQuerySet,
    build_lateral_sql,
)
from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import call_method, is_list_or_tuple
from tests._idioms import (
    is_object_list,
    run_capturing,
    saved_pk,
)
from tests._lateral_data import _seed_periodicals

pytestmark = [
    pytest.mark.pg,
    pytest.mark.django_db,
    pytest.mark.usefixtures("isolate_global_registry"),
]

_RowT = TypeVar("_RowT", bound=Model)


def _prefetched_rows(instance: Model, to_attr: str, model: type[_RowT]) -> list[_RowT]:
    """The rows a ``Prefetch(to_attr=...)`` planted on ``instance``, each checked to be a ``model``.

    The model class declares no such attribute; Django's prefetch writes it onto the instance.
    """
    rows = truth.instance_state(instance)[to_attr]
    assert is_object_list(rows)
    typed = [row for row in rows if isinstance(row, model)]
    assert len(typed) == len(rows)
    return typed


def _first_column_texts(cursor: object) -> list[str]:
    """The first column of every row the cursor's last statement returned, each a ``str``.

    Django's ``CursorWrapper`` delegates ``fetchall`` to the driver cursor through
    ``__getattr__``, so the stub types the read ``Any``; each row is checked here instead.
    """
    rows = call_method(cursor, "fetchall")
    assert is_object_list(rows), rows
    texts: list[str] = []
    for row in rows:
        assert is_list_or_tuple(row), row
        first = row[0]
        assert isinstance(first, str), first
        texts.append(first)
    return texts


@runtime_checkable
class _Closeable(Protocol):
    """A raw database connection handle, as the stray-connection registry holds them."""

    def close(self) -> None: ...


def test_stray_executor_thread_connections_are_tracked_for_session_close() -> None:
    """The root-conftest tracker registers handles main-thread teardown misses.

    The xdist ``DROP DATABASE ... is being accessed by other users`` fix:
    a connection opened on a non-main thread (asgiref's
    thread-sensitive executor in production async tests; a plain worker
    thread here) is invisible to pytest-django's main-thread
    ``close_all()``. The Postgres backend wrapper must register it so the
    session-teardown fixture can close it before the test database drops.
    """
    from django.db.backends.postgresql import base as postgres_base  # noqa: PLC0415 - psycopg is optional

    # The root conftest's Postgres wrapper plants the registry on the backend module at run
    # time; the module declares no such attribute, so it is read out of the module namespace.
    registry_list = truth.instance_state(postgres_base)["_dst_stray_connection_registry"]
    assert is_object_list(registry_list)
    before = len(registry_list)
    failures: list[BaseException] = []

    def _open_and_close_on_worker_thread() -> None:
        django_connections["default"].ensure_connection()
        django_connections["default"].close()

    worker = threading.Thread(
        target=run_capturing,
        args=(failures, _open_and_close_on_worker_thread),
    )
    worker.start()
    worker.join()
    assert not failures, failures
    assert len(registry_list) > before
    # The wrapper closed its handle already; the session drain re-closing it
    # must be a harmless no-op (idempotent close is the drain's contract).
    newest = registry_list[-1]
    assert isinstance(newest, _Closeable)
    newest.close()


@pytest.mark.parametrize(
    (
        "cursor_field",
        "cursor_rank",
        "expected_labels",
        "sql_fragment",
    ),
    [
        (
            ("payload", "id"),
            1,
            ["child-2", "child-3"],
            ") > (",
        ),
        (
            ("-payload", "id"),
            3,
            ["child-2", "child-1"],
            '"payload" <= ',
        ),
    ],
)
def test_keyset_json_seek_uses_field_adapter_on_postgres(
    cursor_field: tuple[str, ...],
    cursor_rank: int,
    expected_labels: list[str],
    sql_fragment: str,
) -> None:
    """Internal JSONB seek values are field-prepared before raw lateral execution.

    JSONField is deliberately rejected at the public cursor-field and runtime
    orderBy validation gates because its ordering is not backend-portable.
    This direct internal carrier still pins the raw SQL adapter boundary so a
    future custom field with structured prepared values cannot bypass Django.
    """

    def create_specimen(
        label: str,
        payload: object,
        *,
        parent: ScalarSpecimen | None = None,
    ) -> ScalarSpecimen:
        return ScalarSpecimen.objects.create(
            label=label,
            occurred_on=datetime.date(2026, 1, 1),
            occurred_at=timezone.now(),
            occurred_time=datetime.time(12, 0),
            payload=payload,
            external_id=uuid.uuid4(),
            parent=parent,
        )

    parent = create_specimen("parent", {"rank": 0})
    children = {
        rank: create_specimen(f"child-{rank}", {"rank": rank}, parent=parent)
        for rank in range(1, 4)
    }
    columns = cursor_columns_for(ScalarSpecimen, cursor_field)
    seek = KeysetSeek(
        columns=columns,
        cursor=KeysetCursor(
            values=(children[cursor_rank].payload, saved_pk(children[cursor_rank])),
        ),
    )
    field = ScalarSpecimen._meta.get_field("children")
    request = NestedConnectionRequest(
        django_field=field,
        relation_field_name="children",
        prefix="",
        child_queryset=ScalarSpecimen.objects.all(),
        join=classify_relation_join(field),
        order_by=cursor_field,
        offset=0,
        limit=2,
        reverse=False,
        with_total_count=False,
        next_page_probe=True,
        keyset_seek=seek,
        to_attr="_dst_children_connection",
        lookup="children",
    )
    plan = OptimizationPlan()
    assert LATERAL_STRATEGY.plan(request, plan)
    (planned_prefetch,) = plan.prefetch_related
    assert isinstance(planned_prefetch, Prefetch)
    with CaptureQueriesContext(db_connection) as captured:
        loaded = ScalarSpecimen.objects.prefetch_related(planned_prefetch).get(pk=saved_pk(parent))
    lateral_sql = next(entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"])
    assert sql_fragment in lateral_sql
    window = _prefetched_rows(loaded, "_dst_children_connection", ScalarSpecimen)
    assert [row.label for row in window] == expected_labels
    assert all(isinstance(row.payload, dict) for row in window)


@pytest.mark.django_db(transaction=True)
def test_keyset_lateral_seek_is_an_index_seek() -> None:
    """EXPLAIN pin: with the composite index present, the count-free lateral branch seeks it.

    The index is the composite ``(cursor columns..., pk)`` one; the branch seeks it instead of
    scanning.

    ``enable_seqscan`` is forced off for the EXPLAIN so the planner's
    small-table seq-scan preference cannot mask index-usability; the pin is
    "the seek CAN use the index", not a cost-model assertion.
    """
    issues = _seed_periodicals()
    seek = KeysetSeek(
        columns=cursor_columns_for(Issue, ("number", "id")),
        cursor=KeysetCursor(values=(2, saved_pk(issues[1]))),
    )

    field = Periodical._meta.get_field("issues")
    request = NestedConnectionRequest(
        django_field=field,
        relation_field_name="issues",
        prefix="",
        child_queryset=Issue.objects.all(),
        join=classify_relation_join(field),
        order_by=("number", "id"),
        offset=0,
        limit=2,
        reverse=False,
        with_total_count=False,
        next_page_probe=True,
        keyset_seek=seek,
        to_attr="_dst_issues_connection",
        lookup="issues",
    )
    plan = OptimizationPlan()

    assert LATERAL_STRATEGY.plan(request, plan)
    planned_prefetch = plan.prefetch_related[0]
    assert isinstance(planned_prefetch, Prefetch)
    assert planned_prefetch.queryset is not None
    lateral_queryset = planned_prefetch.queryset
    assert isinstance(lateral_queryset, LateralQuerySet)
    spec = lateral_queryset._dst_lateral_spec
    assert spec is not None
    parent_ids = list(Periodical.objects.values_list("pk", flat=True))
    sql, params = build_lateral_sql(
        spec,
        parent_ids,
        quote_name=db_connection.ops.quote_name,
        parent_cast=spec.parent_link_field.db_type(db_connection),
    )
    with db_connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX keyset_seek_pin_idx ON library_issue (periodical_id, number, id)",
        )
        cursor.execute("SET enable_seqscan = off")
        try:
            # basedpyright: django-stubs admits a closed set of Python scalars as ``execute``
            # params; build_lateral_sql returns the backend-prepared values as ``list[object]``,
            # which the driver binds
            cursor.execute(f"EXPLAIN {sql}", params)  # pyright: ignore[reportArgumentType]
            explain_plan = " ".join(_first_column_texts(cursor))
        finally:
            cursor.execute("SET enable_seqscan = on")
            cursor.execute("DROP INDEX keyset_seek_pin_idx")
    assert "keyset_seek_pin_idx" in explain_plan
    assert "Index" in explain_plan
