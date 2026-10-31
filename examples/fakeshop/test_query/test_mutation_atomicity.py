"""Live HTTP acceptance for the mutation transaction that spans response completion.

Pins the mutation-atomicity contract: a ``DjangoMutation``'s write transaction
does not stand committed once the resolver returns - BEFORE the returned payload
is *completed* (serialized) - so a completion failure never leaves the write
committed while the client sees ``data: null`` + a top-level error.
``DjangoSchema``'s execution context holds each generated top-level mutation field's
transaction open THROUGH value completion and rolls it back when completion adds an
error.

The trigger requires a row that can be written but not serialized back. Normal
ORM writes can't produce one, so the tests corrupt the DB directly with raw
SQL: a ``created_date`` that hydrates to ``None`` on refetch or snapshot (no
exception, so nothing fails at write time) only fails at completion as
``Cannot return null for non-nullable field ...createdDate`` - by which point
the create/update/delete side effect must ROLL BACK, not stay committed. The
stored corruption is vendor-shaped (``_corrupt_created_date``); the hydrated
value, the failing field and the rollback assertion are identical on both.

The assertions encode the shipped contract (no 500, the completion error is surfaced, the
write rolled back).
The success-side contract (a serializable payload still commits, and serial
top-level mutation fields keep independent transactions) is pinned alongside, as is the
mutation root's ``__typename`` meta-field, which carries no mutation class and resolves
as a plain field.
Async colour uses a module-local ``/graphql-async/`` mount (``graphql_client.py``
is sync-only).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from functools import wraps
from typing import TYPE_CHECKING

import pytest
from apps.products import models
from apps.products.services import create_users, seed_data
from asgiref.sync import sync_to_async
from config import schema as config_schema
from django.apps import apps
from django.contrib.auth.models import Permission, User
from django.db import connection
from django.db.backends.utils import CursorWrapper
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import AsyncClient, Client, override_settings
from django.urls import path
from graphql_client import JSONObject, json_at, json_list, read_attr, response_json

from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient, TestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import AsyncDjangoGraphQLView
from tests._idioms import saved_pk

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedASGIResponse, _MonkeyPatchedWSGIResponse

_UPDATE_ITEM = """
mutation($id: ID!, $d: ItemPartialInput!) {
  updateItem(id: $id, data: $d) {
    node {
      id
      name
      category { id name createdDate updatedDate }
    }
    errors { field messages }
  }
}
"""

_DELETE_ITEM_OWN_SCALAR = """
mutation($id: ID!) {
  deleteItem(id: $id) {
    node {
      id
      name
      createdDate
    }
    errors { field messages }
  }
}
"""

_CREATE_ITEM = """
mutation($d: ItemInput!) {
  createItem(data: $d) {
    node {
      id
      name
      category { id name createdDate updatedDate }
    }
    errors { field messages }
  }
}
"""

_DELETE_ITEM = """
mutation($id: ID!) {
  deleteItem(id: $id) {
    node {
      id
      name
      category { id name createdDate updatedDate }
    }
    errors { field messages }
  }
}
"""

# Two serial top-level fields in ONE operation: the GraphQL spec executes them
# serially, and each generated field gets its OWN completion-spanning
# transaction - the first field's outcome must not couple to the second's.
_TWO_UPDATES = """
mutation($idA: ID!, $dA: ItemPartialInput!, $idB: ID!, $dB: ItemPartialInput!) {
  first: updateItem(id: $idA, data: $dA) {
    node { id name }
    errors { field messages }
  }
  second: updateItem(id: $idB, data: $dB) {
    node { id name category { createdDate } }
    errors { field messages }
  }
}
"""


def _login_with_perm(username: str, *codenames: str) -> Client:
    user = User.objects.get(username=username)
    for codename in codenames:
        permission = Permission.objects.get(codename=codename, content_type__app_label="products")
        user.user_permissions.add(permission)
    client = Client()
    client.force_login(User.objects.get(username=user.username))
    return client


def _global_id(type_name: str, pk: int) -> str:
    """Mint the id from the finalized primary type rather than an assumed strategy."""
    type_cls = registry.get(apps.get_model(type_name))
    assert type_cls is not None, type_name
    return global_id_for(type_cls, pk)


_VALID_DATE = "2026-01-02 03:04:05"


@pytest.fixture(autouse=True)
def _restore_created_date_columns(transactional_db: None) -> Iterator[None]:
    """A PostgreSQL corruption probe restores the nullability it found before it ran."""
    del transactional_db
    original_nullability: dict[str, bool] = {}
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            for table in ("products_category", "products_item"):
                columns: list[object] = connection.introspection.get_table_description(
                    cursor,
                    table,
                )
                created_column = next(
                    column for column in columns if read_attr(column, "name") == "created_date"
                )
                nullable = read_attr(created_column, "null_ok")
                assert isinstance(nullable, bool), nullable
                original_nullability[table] = nullable
    try:
        yield
    finally:
        repair_statements = {
            "products_category": (
                "UPDATE products_category SET created_date = %s WHERE created_date IS NULL"
            ),
            "products_item": (
                "UPDATE products_item SET created_date = %s WHERE created_date IS NULL"
            ),
        }
        with connection.cursor() as cursor:
            for table, was_nullable in original_nullability.items():
                if not was_nullable:
                    cursor.execute(
                        repair_statements[table],
                        (_VALID_DATE,),
                    )
                    cursor.execute(f"ALTER TABLE {table} ALTER COLUMN created_date SET NOT NULL")


def _first_column(cursor: CursorWrapper) -> object:
    """The first column of the first row the cursor's last statement returned."""
    row: tuple[object, ...] = next(iter(cursor))
    return row[0]


def _update_raw(sql: str, params: tuple[str | int | None, ...]) -> int:
    """Rewrite an existing seeded row and return its unchanged key through ``RETURNING``."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        pk = _first_column(cursor)
    assert isinstance(pk, int), pk
    return pk


def _corrupt_created_date(table: str) -> str | None:
    """Return the value to store so ``table``'s ``created_date`` hydrates to ``None``.

    SQLite stores datetimes as text and hydrates an unparseable string to
    ``None``. Postgres type-checks the column, so the equivalent stored value is
    a real ``NULL``; ``created_date`` is declared NOT NULL, so relax that first.
    Both vendors then hand the ORM the same ``None`` and fail the same
    non-nullable ``createdDate`` at response completion.
    """
    if connection.vendor == "sqlite":
        return "not-a-date"
    with connection.cursor() as cursor:
        cursor.execute(f"ALTER TABLE {table} ALTER COLUMN created_date DROP NOT NULL")
    return None


def _post_update(
    client: Client,
    item_pk: int,
    *,
    query: str = _UPDATE_ITEM,
    name: str,
) -> _MonkeyPatchedWSGIResponse:
    res = TestClient(client=client).query(
        query,
        variables={"id": _global_id("products.item", item_pk), "d": {"name": name}},
        assert_no_errors=False,
    )
    return res.response


def _post_create(client: Client, category_pk: int) -> _MonkeyPatchedWSGIResponse:
    res = TestClient(client=client).query(
        _CREATE_ITEM,
        variables={
            "d": {
                "name": "create-post-corruption",
                "categoryId": _global_id("products.category", category_pk),
            },
        },
        assert_no_errors=False,
    )
    return res.response


def _post_delete(client: Client, item_pk: int) -> _MonkeyPatchedWSGIResponse:
    res = TestClient(client=client).query(
        _DELETE_ITEM,
        variables={"id": _global_id("products.item", item_pk)},
        assert_no_errors=False,
    )
    return res.response


def _prepare_category(name: str, *, position: int = 0, corrupt: bool = False) -> int:
    """Rewrite a service-seeded category; ``corrupt=True`` plants an un-hydratable date.

    A corrupt date hydrates to ``None`` on refetch (no exception, nothing rolls
    back at write time) and only fails later, completing the non-nullable
    ``createdDate``. ``is_private`` is bound as a real Python ``bool`` so the
    parameter matches Postgres' ``boolean`` column as well as SQLite's.
    """
    pk = saved_pk(models.Category.objects.order_by("pk")[position])
    created_date = _corrupt_created_date("products_category") if corrupt else _VALID_DATE
    return _update_raw(
        """
        UPDATE products_category
        SET name = %s, description = %s, is_private = %s, created_date = %s, updated_date = %s
        WHERE id = %s
        RETURNING id
        """,
        (
            name,
            "service-seeded category",
            False,
            created_date,
            _VALID_DATE,
            pk,
        ),
    )


def _prepare_item(
    name: str,
    category_pk: int,
    *,
    position: int = 0,
    corrupt: bool = False,
) -> int:
    """Rewrite a service-seeded item; raw SQL is reserved for the corrupt date."""
    pk = saved_pk(models.Item.objects.order_by("pk")[position])
    created_date = _corrupt_created_date("products_item") if corrupt else _VALID_DATE
    return _update_raw(
        """
        UPDATE products_item
        SET name = %s, description = %s, category_id = %s, is_private = %s,
            created_date = %s, updated_date = %s
        WHERE id = %s
        RETURNING id
        """,
        (
            name,
            "service-seeded item",
            category_pk,
            False,
            created_date,
            _VALID_DATE,
            pk,
        ),
    )


def _stored_item_name(item_pk: int) -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM products_item WHERE id = %s", (item_pk,))
        name = _first_column(cursor)
    assert isinstance(name, str), name
    return name


def _completion_failure(
    response: _MonkeyPatchedWSGIResponse | _MonkeyPatchedASGIResponse,
    root: str,
    *field_path: str,
) -> JSONObject:
    """Require the intended completion failure rather than any error before the write."""
    assert response.status_code == 200
    payload = response_json(response)
    errors = json_list(payload, "errors")
    assert len(errors) == 1, payload
    assert json_at(errors[0], "message") == "An unexpected error occurred.", payload
    assert json_at(errors[0], "path") == [root, "node", *field_path], payload
    assert json_at(payload, "data", root, "node") is None, payload
    return payload


@pytest.mark.django_db(transaction=True)
def test_update_does_not_commit_when_response_completion_fails() -> None:
    """An update whose response can't be serialized must roll back, not commit a partial write."""
    create_users(1)
    seed_data(2)
    client = _login_with_perm("view_item_1", "view_category", "change_item")

    # A category whose `created_date` cannot round-trip: it hydrates to None on
    # refetch (no exception), then fails the non-nullable `createdDate` at completion.
    category_pk = _prepare_category("raw-update-bad-date-category", corrupt=True)
    item_pk = _prepare_item("raw-bad-date-item", category_pk)

    response = _post_update(client, item_pk, name="post-corruption-update")

    _completion_failure(response, "updateItem", "category", "createdDate")

    # ...but the write must NOT have committed: the row keeps its original name.
    assert _stored_item_name(item_pk) == "raw-bad-date-item"


@pytest.mark.django_db(transaction=True)
def test_delete_does_not_commit_when_own_scalar_response_completion_fails() -> None:
    """A delete selecting a corrupt scalar on the deleted object ITSELF must roll back.

    Distinct from the relation-path tests: here the completion failure is on the
    target row's OWN non-nullable ``createdDate`` (the corrupt date lives on the
    ITEM, hydrating to ``None`` in the pre-delete snapshot), so the failing field
    sits directly under the payload's ``node`` slot. Delete is the only operation
    that can surface an own-column corruption at completion: create/update
    ``save()`` writes every column back, so a corrupt own column is refused at
    write time as a NOT NULL constraint envelope instead (itself rolled back).
    """
    create_users(1)
    seed_data(2)
    client = _login_with_perm("staff_1", "delete_item")
    category_pk = _prepare_category("raw-own-scalar-category")
    item_pk = _prepare_item("raw-own-scalar-item", category_pk, corrupt=True)

    res = TestClient(client=client).query(
        _DELETE_ITEM_OWN_SCALAR,
        variables={"id": _global_id("products.item", item_pk)},
        assert_no_errors=False,
    )
    response = res.response

    _completion_failure(response, "deleteItem", "createdDate")
    # The delete rolled back: the row survives.
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products_item WHERE id = %s", (item_pk,))
        assert _first_column(cursor) == 1


@pytest.mark.django_db(transaction=True)
def test_create_does_not_commit_when_response_completion_fails() -> None:
    """A create whose response can't be serialized must roll back, not leave a row."""
    create_users(1)
    seed_data(2)
    client = _login_with_perm("view_item_1", "add_item")
    category_pk = _prepare_category("raw-create-bad-date-category", corrupt=True)

    response = _post_create(client, category_pk)

    _completion_failure(response, "createItem", "category", "createdDate")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM products_item WHERE name = %s",
            ("create-post-corruption",),
        )
        created_count = _first_column(cursor)
    assert created_count == 0


@pytest.mark.django_db(transaction=True)
def test_delete_does_not_commit_when_response_completion_fails() -> None:
    """A delete whose response can't be serialized must roll back, not remove the row."""
    create_users(1)
    seed_data(2)
    client = _login_with_perm("staff_1", "delete_item")
    category_pk = _prepare_category("raw-delete-bad-date-category", corrupt=True)
    item_pk = _prepare_item("raw-delete-bad-date-item", category_pk)

    response = _post_delete(client, item_pk)

    _completion_failure(response, "deleteItem", "category", "createdDate")
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products_item WHERE id = %s", (item_pk,))
        remaining_count = _first_column(cursor)
    assert remaining_count == 1


@pytest.mark.django_db(transaction=True)
def test_successful_update_still_commits_through_the_completion_spanning_transaction() -> None:
    """The completion-spanning transaction COMMITS a cleanly-serializable write.

    The rollback contract's other half: extending the transaction through
    completion must not turn every mutation read-only. A normal update over
    healthy rows completes, returns the success payload, and persists.
    """
    create_users(1)
    seed_data(2)
    client = _login_with_perm("view_item_1", "view_category", "change_item")
    category_pk = _prepare_category("healthy-commit-category")
    item_pk = _prepare_item("healthy-commit-item", category_pk)

    response = _post_update(client, item_pk, name="committed-update")

    payload = response_json(response)
    assert response.status_code == 200
    assert "errors" not in payload, payload
    assert json_at(payload, "data", "updateItem", "errors") == []
    assert _stored_item_name(item_pk) == "committed-update"


@pytest.mark.django_db(transaction=True)
def test_serial_top_level_mutations_keep_independent_transactions() -> None:
    """Two serial top-level mutation fields keep independent transactions.

    The second's completion failure rolls back ONLY the second's write - the first
    field's already-committed transaction survives.
    """
    create_users(1)
    seed_data(2)
    client = _login_with_perm("view_item_1", "view_category", "change_item")
    healthy_category_pk = _prepare_category("serial-healthy-category")
    corrupt_category_pk = _prepare_category("serial-corrupt-category", position=1, corrupt=True)
    first_pk = _prepare_item("serial-first-item", healthy_category_pk)
    second_pk = _prepare_item("serial-second-item", corrupt_category_pk, position=1)

    res = TestClient(client=client).query(
        _TWO_UPDATES,
        variables={
            "idA": _global_id("products.item", first_pk),
            "dA": {"name": "serial-first-updated"},
            "idB": _global_id("products.item", second_pk),
            "dB": {"name": "serial-second-updated"},
        },
        assert_no_errors=False,
    )

    payload = _completion_failure(res.response, "second", "category", "createdDate")
    # The second field's completion failed (its category createdDate is corrupt);
    # the non-nullable error null-bubbles to the nearest nullable ancestor - the
    # payload's `node` slot - and surfaces as a top-level error...
    # ...and only ITS write rolled back; the first field committed independently.
    assert json_at(payload, "data", "first", "node", "name") == "serial-first-updated"
    assert _stored_item_name(first_pk) == "serial-first-updated"
    assert _stored_item_name(second_pk) == "serial-second-item"


@pytest.mark.django_db
def test_mutation_root_typename_meta_field_resolves() -> None:
    """``mutation { __typename }`` resolves the root meta-field, which names no mutation class."""
    res = TestClient(client=Client()).query("mutation { __typename }", assert_no_errors=False)

    assert res.response.status_code == 200
    assert response_json(res.response) == {"data": {"__typename": "Mutation"}}


@wraps(AsyncDjangoGraphQLView.as_view())
async def _async_shipped_graphql_view(request: HttpRequest) -> HttpResponseBase:

    return await AsyncDjangoGraphQLView.as_view(schema=config_schema.schema)(request)


urlpatterns = [path("graphql-async/", _async_shipped_graphql_view)]


async def _post_async(
    query: str,
    *,
    variables: Mapping[str, object] | None = None,
    client: AsyncClient | None = None,
) -> _MonkeyPatchedASGIResponse:
    """POST ``query`` against the shipped schema over ``/graphql-async/``."""
    with override_settings(ROOT_URLCONF=__name__):
        result = await AsyncTestClient(client=client).query(
            query,
            variables=variables,
            assert_no_errors=False,
            url="/graphql-async/",
        )
    return result.response


async def _async_client_with_perm(username: str, *codenames: str) -> AsyncClient:
    def _login() -> Client:
        return _login_with_perm(username, *codenames)

    await sync_to_async(_login)()
    user = await sync_to_async(User.objects.get)(username=username)
    client = AsyncClient()
    await sync_to_async(client.force_login)(user)
    return client


@pytest.mark.django_db(transaction=True)
async def test_update_does_not_commit_when_response_completion_fails_over_graphql_async() -> None:
    """Async ``updateItem`` whose response can't be serialized must roll back."""
    await sync_to_async(create_users)(1)
    await sync_to_async(seed_data)(2)
    client = await _async_client_with_perm("view_item_1", "view_category", "change_item")

    def _seed() -> int:
        category_pk = _prepare_category("async-raw-update-bad-date-category", corrupt=True)
        return _prepare_item("async-raw-bad-date-item", category_pk)

    item_pk = await sync_to_async(_seed)()
    response = await _post_async(
        _UPDATE_ITEM,
        client=client,
        variables={
            "id": _global_id("products.item", item_pk),
            "d": {"name": "async-post-corruption-update"},
        },
    )

    _completion_failure(response, "updateItem", "category", "createdDate")
    stored = await sync_to_async(_stored_item_name)(item_pk)
    assert stored == "async-raw-bad-date-item"


@pytest.mark.django_db(transaction=True)
async def test_successful_update_still_commits_over_graphql_async() -> None:
    """A serializable async ``updateItem`` still commits through completion."""
    await sync_to_async(create_users)(1)
    await sync_to_async(seed_data)(2)
    client = await _async_client_with_perm("view_item_1", "view_category", "change_item")

    def _seed() -> int:
        category_pk = _prepare_category("async-healthy-commit-category")
        return _prepare_item("async-healthy-commit-item", category_pk)

    item_pk = await sync_to_async(_seed)()
    response = await _post_async(
        _UPDATE_ITEM,
        client=client,
        variables={
            "id": _global_id("products.item", item_pk),
            "d": {"name": "async-committed-update"},
        },
    )

    payload = response_json(response)
    assert response.status_code == 200
    assert "errors" not in payload, payload
    assert json_at(payload, "data", "updateItem", "errors") == []
    stored = await sync_to_async(_stored_item_name)(item_pk)
    assert stored == "async-committed-update"
