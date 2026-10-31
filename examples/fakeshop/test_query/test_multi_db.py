"""Live GraphQL HTTP tests for sharded resolver isolation and multi-database debug capture.

Scope: live ``/graphql/`` HTTP rows against the sharded fakeshop layout.

Resolver isolation and debug capture (per spec Goals item 3 + Test plan
``### examples/fakeshop/test_query/test_multi_db.py``):

- Seeding rows on ``shard_b`` and reading them through ``/graphql/`` via a
  ``.using("shard_b")`` root resolver returns the seeded rows.
- Cross-shard isolation: a chain seeded on ``default`` is NOT visible through a
  ``using("shard_b")`` resolver.
- A debug-enabled probe captures SQL from ``shard_b`` with the correct database
  alias and restores every connection's debug-cursor state.
- A planned prefetch child cannot pin an alias of its own: a child
  ``get_queryset`` returning ``.using("shard_b")`` under a ``default`` parent
  fails the relation closed before either alias runs a ``library_book`` read,
  while the same hook without the routing call follows whichever alias the
  parent was pinned to, and a hook running ``apply_cascade_permissions`` under
  a ``.using("shard_b")`` parent composes its membership subquery on
  ``shard_b`` too.

The suite also owns the alias pins that only a second database can prove: the
row-preserving relational leaf predicate executing wholly on ``shard_b``, a
``GenericRelation`` branch filter matching ``shard_b``'s own content-type pk, the write
alias for generated and serializer mutations, and the post-``OrderSet`` routing
attestation. Four routing rows mount a consumer override on a ``.using("shard_b")``
list field and cover an alias change, a hints change, an in-place rewrite of the
queryset the override was handed, and an equal-but-distinct hint token under a router
that tells hint objects apart by identity; each must fail before any row executes,
with no ``library_branch`` SQL on either alias. The fifth row is ACCEPTED and is what
the attestation rests on: the override mutates state INSIDE a hint object it preserves
by identity, so nothing the seal compares changed, yet a router reading into that
object would now answer ``default``. The effective alias is frozen before the override
runs and the result is pinned to it, so the completed read returns the ``shard_b`` row
and ``default`` sees no ``library_branch`` SQL at all. A sixth row runs the alias-change
case through a ``DjangoConnectionField`` instead, because the connection field runs the
SAME post-``OrderSet`` seal and would otherwise take its Relay window on the substituted
shard's rows.

Critical contract pins (do not violate without an explicit spec revision):

- Module-level ``pytest.skip(allow_module_level=True)`` gate per Decision 6
  (NOT ``pytest.mark.skipif`` - the env var changes ``config.settings.DATABASES``
  at module import time; mark evaluation happens after import).
- ``@pytest.mark.django_db(databases=["default", "shard_b"])`` on each test
  (pytest-django blocks non-default-DB access otherwise).
- Full ``Branch -> Shelf -> Book`` chain per alias via ``_seed_book_chain``
  (``Book.shelf`` and ``Shelf.branch`` are non-null FKs).
- Live ``/graphql/`` HTTP only - new ordinary JSON rows use the shared
  ``graphql_client.py`` helper, and no row uses an in-process ``execute_sync(...)``
  alternative.
- Schema built inside a per-test fixture that depends on the shared module
  reload - the holder pattern below defers schema construction until after
  the registry clear so the test sees freshly-reloaded ``BookType``.
- ``override_settings(ROOT_URLCONF=__name__)`` with
  ``clear_url_caches()`` on enter AND in teardown.
"""


# ``os`` owns the import-time environment gate below.

import os
from collections.abc import Callable, Iterator, Mapping
from functools import wraps
from typing import TypeGuard

import pytest
from apps.library import filters as library_filters
from apps.library import schema as library_schema
from apps.library.orders import BranchOrder
from apps.library.orders_genre import GenreOrder
from apps.products import models as product_models
from apps.products import schema as products_schema
from apps.products.services import create_users, seed_data
from config import schema as config_schema
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db import connection as default_connection

from django_strawberry_framework.filters import FilterInput, FilterSet, RelatedFilter

if os.environ.get("FAKESHOP_SHARDED") != "1":
    pytest.skip(
        "requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)",
        allow_module_level=True,
    )

# Below this line, FAKESHOP_SHARDED=1 is set and ``shard_b`` is in DATABASES.
# These imports run only after the skip check passes - otherwise
# ``from apps.library import models`` would crash in single-DB mode where
# ``shard_b`` is not registered in DATABASES.

import strawberry
from apps.library import models
from django.db import connections
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import (
    JSONObject,
    graphql_payload,
    json_at,
    json_list,
    json_object,
    json_str,
    middleware_without_debug_toolbar,
    read_attr,
    saved_pk,
)
from graphql_client import assert_graphql_success as _graphql_data
from strategy_schemas import make_django_type
from strawberry import relay
from strawberry.types import Info

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    apply_cascade_permissions,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.extensions import DjangoDebugExtension
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import TestClient
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils._queryset_private import (
    set_queryset_db,
    set_queryset_hints,
)
from django_strawberry_framework.views import DjangoGraphQLView

_UPDATE_BOOK_TITLE_VALIDATOR_MUTATION = """
mutation($id: ID!, $d: AliasValidatedBookSerializerPartialInput!) {
  updateBookTitleWithAliasValidator(id: $id, data: $d) {
    node { title }
    errors { field messages }
  }
}
"""

# ---------------------------------------------------------------------------
# Holder-pattern URLConf (per Decision 6)
# ---------------------------------------------------------------------------
#
# The temp URLConf binds at module load, but the schema is built per-test
# (after the autouse reload clears the registry). The holder lets the URLConf's
# view read whichever schema the current test's fixture stored.


_current: dict[str, object | None] = {"schema": None}


@wraps(DjangoGraphQLView.as_view())
def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    """Closure-bound view that reads ``_current['schema']`` per request."""
    schema = _current["schema"]
    assert schema is not None, "_build_test_schema fixture must run before any /graphql/ request"
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view)]


def _capture_payload(
    document: str,
    *,
    client: Client | None = None,
    variables: Mapping[str, object] | None = None,
) -> tuple[JSONObject, dict[str, list[str]]]:
    """Capture both physical aliases around one native HTTP request only."""
    with (
        CaptureQueriesContext(connections["default"]) as on_default,
        CaptureQueriesContext(connections["shard_b"]) as on_shard_b,
    ):
        payload = graphql_payload(document, client=client, variables=variables)
    return payload, {
        alias: [entry["sql"] for entry in captured.captured_queries]
        for alias, captured in (("default", on_default), ("shard_b", on_shard_b))
    }


def _from_table(statements: list[str], table: str) -> list[str]:
    """Count a SELECT's outer FROM, not mentions in JOINs or membership subqueries."""
    return [
        sql
        for sql in statements
        if sql.lstrip().upper().startswith("SELECT ")
        and " FROM " in sql
        and sql.split(" FROM ", 1)[1].startswith(f'"{table}"')
    ]


def _touching_tables(statements: list[str], *tables: str) -> list[str]:
    return [sql for sql in statements if any(f'"{table}"' in sql for table in tables)]


def _assert_read_alias(
    statements: dict[str, list[str]],
    alias: str,
    counts: Mapping[str, int],
) -> None:
    """Pin each outer table read and forbid these tables on the other connection."""
    for table, count in counts.items():
        assert len(_from_table(statements[alias], table)) == count, statements
    assert len(_touching_tables(statements[alias], *counts)) == sum(counts.values()), statements
    for other_alias, sql in statements.items():
        if other_alias != alias:
            assert _touching_tables(sql, *counts) == [], statements


def _assert_one_refusal(payload: JSONObject, *, message: str, field: str) -> None:
    assert payload["data"] is None, payload
    assert len(json_list(payload, "errors")) == 1, payload
    assert json_str(payload, "errors", 0, "message") == message
    assert json_at(payload, "errors", 0, "path") == [field]


@pytest.fixture
def list_routing_override(
    _reload_project_schema_for_acceptance_tests: None,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[dict[str, bool]]:
    """Build a schema with Branch list field whose OrderSet maliciously routes shard_b to default."""
    routing = {"reject": False}

    def _malicious_apply_sync(
        _cls: type[BranchOrder],
        _order_input: object,
        _queryset: QuerySet[models.Branch],
        _info: object,
    ) -> QuerySet[models.Branch]:
        if not routing["reject"]:
            return _queryset.order_by("name")
        # Receives shard_b queryset, maliciously returns default queryset
        return models.Branch.objects.using("default").order_by("name")

    monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(_malicious_apply_sync))

    def _shard_b_branches(_root: object, _info: Info[object, object]) -> QuerySet[models.Branch]:
        return models.Branch.objects.using("shard_b")

    @strawberry.type
    class _RoutingQuery:
        branches_shard_b: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_shard_b_branches,
        )

    _current["schema"] = DjangoSchema(
        query=_RoutingQuery,
        config=strawberry_config(),
    )
    yield routing
    _current["schema"] = None


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_post_orderset_routing_mismatch_rejected_on_sharded_db(
    list_routing_override: dict[str, bool],
) -> None:
    """Preserved routing executes; changing only the routing is refused before either alias reads."""
    models.Branch.objects.using("shard_b").create(name="Branch-ShardB", city="Boston")
    models.Branch.objects.using("default").create(name="Branch-Default", city="Boston")
    query = "{ branchesShardB(orderBy: [{ city: ASC }]) { name } }"
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=True,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        control, control_sql = _capture_payload(query)
        list_routing_override["reject"] = True
        rejected, rejected_sql = _capture_payload(query)

    assert control == {"data": {"branchesShardB": [{"name": "Branch-ShardB"}]}}
    _assert_read_alias(control_sql, "shard_b", {"library_branch": 1})
    _assert_one_refusal(
        rejected,
        message=(
            "BranchOrder.apply_sync changed database routing intent; "
            "expected db='shard_b', hints={}, "
            "got db='default', hints={}."
        ),
        field="branchesShardB",
    )
    assert {
        alias: _touching_tables(sql, "library_branch") for alias, sql in rejected_sql.items()
    } == {"default": [], "shard_b": []}


@pytest.fixture
def connection_routing_override(
    _reload_project_schema_for_acceptance_tests: None,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[dict[str, bool]]:
    """Build a schema with a Genre CONNECTION whose OrderSet re-routes shard_b to default."""
    routing = {"reject": False}

    def _malicious_apply_sync(
        _cls: type[GenreOrder],
        _order_input: object,
        _queryset: QuerySet[models.Genre],
        _info: object,
    ) -> QuerySet[models.Genre]:
        if not routing["reject"]:
            return _queryset.order_by("name")
        # Receives the shard_b queryset, maliciously returns a default one.
        return models.Genre.objects.using("default").order_by("name")

    monkeypatch.setattr(GenreOrder, "apply_sync", classmethod(_malicious_apply_sync))

    def _shard_b_genres(_root: object, _info: Info[object, object]) -> QuerySet[models.Genre]:
        return models.Genre.objects.using("shard_b")

    @strawberry.type
    class _ConnectionRoutingQuery:
        genres_shard_b: DjangoConnection[library_schema.GenreType] = DjangoConnectionField(
            library_schema.GenreType,
            resolver=_shard_b_genres,
        )

    _current["schema"] = DjangoSchema(
        query=_ConnectionRoutingQuery,
        config=strawberry_config(),
    )
    yield routing
    _current["schema"] = None


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_post_orderset_routing_mismatch_rejected_on_connection_field(
    connection_routing_override: dict[str, bool],
) -> None:
    """Preserved routing executes; changing only the routing is refused before either alias reads."""
    models.Genre.objects.using("shard_b").create(name="Genre-ShardB")
    models.Genre.objects.using("default").create(name="Genre-Default")
    query = "{ genresShardB(orderBy: [{ name: ASC }]) { edges { node { name } } } }"
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=True,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        control, control_sql = _capture_payload(query)
        connection_routing_override["reject"] = True
        rejected, rejected_sql = _capture_payload(query)

    assert control == {"data": {"genresShardB": {"edges": [{"node": {"name": "Genre-ShardB"}}]}}}
    _assert_read_alias(control_sql, "shard_b", {"library_genre": 1})
    _assert_one_refusal(
        rejected,
        message=(
            "GenreOrder.apply_sync changed database routing intent; "
            "expected db='shard_b', hints={}, "
            "got db='default', hints={}."
        ),
        field="genresShardB",
    )
    assert {
        alias: _touching_tables(sql, "library_genre") for alias, sql in rejected_sql.items()
    } == {"default": [], "shard_b": []}


@pytest.fixture
def hints_routing_override(
    _reload_project_schema_for_acceptance_tests: None,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[dict[str, bool]]:
    """Build a schema with Branch list field whose OrderSet changes routing hints with db=None."""
    routing = {"reject": False}

    def _malicious_hints_apply_sync(
        _cls: type[BranchOrder],
        _order_input: object,
        queryset: QuerySet[models.Branch],
        _info: object,
    ) -> QuerySet[models.Branch]:
        # Receives an unrouted queryset with hints={'tenant': 1}; returns a candidate
        # carrying hints={'tenant': 2}. Both sides have ``_db is None``, so the hints
        # are the only thing that could route them apart.
        ordered = queryset.order_by("name")
        if routing["reject"]:
            set_queryset_hints(ordered, {"tenant": 2})
        return ordered

    monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(_malicious_hints_apply_sync))

    def _hints_resolver(_root: object, _info: Info[object, object]) -> QuerySet[models.Branch]:
        qs = models.Branch.objects.all()
        monkeypatch.setattr(qs, "_hints", {"tenant": 1})
        return qs

    @strawberry.type
    class _RoutingHintsQuery:
        branches_hints: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_hints_resolver,
        )

    _current["schema"] = DjangoSchema(
        query=_RoutingHintsQuery,
        config=strawberry_config(),
    )
    yield routing
    _current["schema"] = None


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_post_orderset_hints_routing_mismatch_rejected_on_sharded_db(
    hints_routing_override: dict[str, bool],
) -> None:
    """Preserved routing executes; changing only the routing is refused before either alias reads."""
    models.Branch.objects.using("shard_b").create(name="Branch-ShardB", city="Boston")
    models.Branch.objects.using("default").create(name="Branch-Default", city="Boston")
    query = "{ branchesHints(orderBy: [{ city: ASC }]) { name } }"
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=True,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        control, control_sql = _capture_payload(query)
        hints_routing_override["reject"] = True
        rejected, rejected_sql = _capture_payload(query)

    assert control == {"data": {"branchesHints": [{"name": "Branch-Default"}]}}
    _assert_read_alias(control_sql, "default", {"library_branch": 1})
    _assert_one_refusal(
        rejected,
        message=(
            "BranchOrder.apply_sync changed database routing intent; "
            "expected db=None, hints={'tenant': 1}, "
            "got db=None, hints={'tenant': 2}."
        ),
        field="branchesHints",
    )
    assert {
        alias: _touching_tables(sql, "library_branch") for alias, sql in rejected_sql.items()
    } == {"default": [], "shard_b": []}


@pytest.fixture
def _build_list_field_in_place_routing_mutation_schema(
    _reload_project_schema_for_acceptance_tests: None,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    """Branch list field whose OrderSet rewrites the RECEIVED queryset's routing in place."""

    def _in_place_apply_sync(
        _cls: type[BranchOrder],
        _order_input: object,
        queryset: QuerySet[models.Branch],
        _info: object,
    ) -> QuerySet[models.Branch]:
        # Mutates the very object it was handed and returns it unchanged otherwise:
        # a post-call read of that object would see the rewritten routing as the baseline.
        set_queryset_db(queryset, "default")
        set_queryset_hints(queryset, {"tenant": 2})
        return queryset

    monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(_in_place_apply_sync))

    def _shard_b_tenant_resolver(
        _root: object,
        _info: Info[object, object],
    ) -> QuerySet[models.Branch]:
        qs = models.Branch.objects.using("shard_b")
        monkeypatch.setattr(qs, "_hints", {"tenant": 1})
        return qs

    @strawberry.type
    class _InPlaceRoutingQuery:
        branches_shard_b: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_shard_b_tenant_resolver,
        )

    _current["schema"] = DjangoSchema(query=_InPlaceRoutingQuery, config=strawberry_config())
    yield
    _current["schema"] = None


def _branch_sql(captured: list[dict[str, str]]) -> list[str]:
    return _from_table([q["sql"] for q in captured], "library_branch")


@pytest.mark.usefixtures("_build_list_field_in_place_routing_mutation_schema")
@pytest.mark.django_db(databases=["default", "shard_b"])
def test_post_orderset_in_place_routing_mutation_rejected_on_sharded_db() -> None:
    """Routing is snapshotted BEFORE ``apply_sync`` runs, so an in-place rewrite cannot pass.

    The override receives the sealed ``shard_b`` queryset, points it at ``default``
    with new hints, and returns the same object. Compared against the pre-call
    snapshot it is a routing change; the request fails before any row executes,
    and no ``library_branch`` SQL reaches either alias.
    """
    models.Branch.objects.using("shard_b").create(name="Branch-ShardB", city="Boston")
    models.Branch.objects.using("default").create(name="Branch-Default", city="Boston")

    query = """
    query {
      branchesShardB(orderBy: [{ city: ASC }]) {
        name
      }
    }
    """
    client = Client()
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=True,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        clear_url_caches()
        try:
            with (
                CaptureQueriesContext(connections["default"]) as default_ctx,
                CaptureQueriesContext(connections["shard_b"]) as shard_ctx,
            ):
                payload = graphql_payload(query, client=client)
        finally:
            clear_url_caches()

    assert payload["data"] is None
    err_msg = json_str(payload, "errors", 0, "message")
    assert "apply_sync changed database routing intent" in err_msg
    assert "expected db='shard_b', hints={'tenant': 1}" in err_msg
    assert "got db='default', hints={'tenant': 2}" in err_msg
    assert _branch_sql(default_ctx.captured_queries) == []
    assert _branch_sql(shard_ctx.captured_queries) == []


# Two EQUAL but DISTINCT hint tokens: a router is handed the object itself and may
# tell them apart by identity, which is what the identity-only hints compare protects.
_TENANT_TOKEN = "tenant-a!"[:-1]
_EQUAL_DISTINCT_TOKEN = "tenant-a!"[:-1]
assert _TENANT_TOKEN == _EQUAL_DISTINCT_TOKEN
assert _TENANT_TOKEN is not _EQUAL_DISTINCT_TOKEN


class _IdentitySensitiveRouter:
    """Routes reads carrying THE tenant token object to ``shard_b``; equal copies stay on default."""

    def db_for_read(self, _model: type[Model], **hints: object) -> str | None:
        return "shard_b" if hints.get("tenant") is _TENANT_TOKEN else None

    def db_for_write(self, _model: type[Model], **_hints: object) -> str | None:
        return None

    def allow_relation(self, _obj1: Model, _obj2: Model, **_hints: object) -> bool | None:
        return None

    def allow_migrate(
        self,
        _db: str,
        _app_label: str,
        **_hints: object,
    ) -> bool | None:
        return None


@pytest.fixture
def identity_token_swap(
    _reload_project_schema_for_acceptance_tests: None,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[dict[str, bool]]:
    """Unrouted Branch list field whose hints carry the identity token; the override swaps it."""
    swap = {"active": False}

    def _token_swapping_apply_sync(
        _cls: type[BranchOrder],
        _order_input: object,
        queryset: QuerySet[models.Branch],
        _info: object,
    ) -> QuerySet[models.Branch]:
        ordered = queryset.order_by("name")
        if swap["active"]:
            set_queryset_hints(ordered, {"tenant": _EQUAL_DISTINCT_TOKEN})
        return ordered

    monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(_token_swapping_apply_sync))

    def _tenant_resolver(_root: object, _info: Info[object, object]) -> QuerySet[models.Branch]:
        qs = models.Branch.objects.all()
        monkeypatch.setattr(qs, "_hints", {"tenant": _TENANT_TOKEN})
        return qs

    @strawberry.type
    class _TenantQuery:
        branches_tenant: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_tenant_resolver,
        )

    _current["schema"] = DjangoSchema(query=_TenantQuery, config=strawberry_config())
    yield swap
    _current["schema"] = None


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_post_orderset_equal_but_distinct_hint_token_rejected_under_identity_router(
    identity_token_swap: dict[str, bool],
) -> None:
    """An equal-but-not-identical hint value is a routing change under a legal identity router.

    Control: with the token preserved, the identity-sensitive router reads the
    unrouted queryset on ``shard_b`` and the request returns the row seeded there.
    Then the override replaces the token with an equal but distinct string; the
    same router would have sent that read to ``default``, so the seal rejects the
    result before any row executes and no ``library_branch`` SQL reaches either alias.
    """
    swap = identity_token_swap
    models.Branch.objects.using("shard_b").create(name="Branch-ShardB", city="Boston")
    models.Branch.objects.using("default").create(name="Branch-Default", city="Boston")

    query = """
    query {
      branchesTenant(orderBy: [{ city: ASC }]) {
        name
      }
    }
    """
    client = Client()
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=True,
        MIDDLEWARE=middleware_without_debug_toolbar(),
        DATABASE_ROUTERS=[_IdentitySensitiveRouter()],
    ):
        clear_url_caches()
        try:
            swap["active"] = False
            with (
                CaptureQueriesContext(connections["default"]) as control_default_ctx,
                CaptureQueriesContext(connections["shard_b"]) as control_shard_ctx,
            ):
                control = graphql_payload(query, client=client)
            swap["active"] = True
            with (
                CaptureQueriesContext(connections["default"]) as default_ctx,
                CaptureQueriesContext(connections["shard_b"]) as shard_ctx,
            ):
                rejected = graphql_payload(query, client=client)
        finally:
            clear_url_caches()

    assert "errors" not in control, control
    assert json_at(control, "data", "branchesTenant") == [{"name": "Branch-ShardB"}]
    assert _branch_sql(control_default_ctx.captured_queries) == []
    assert len(_branch_sql(control_shard_ctx.captured_queries)) == 1

    assert rejected["data"] is None
    err_msg = json_str(rejected, "errors", 0, "message")
    assert "apply_sync changed database routing intent" in err_msg
    assert "expected db=None, hints={'tenant': 'tenant-a'}" in err_msg
    assert "got db=None, hints={'tenant': 'tenant-a'}" in err_msg
    assert _branch_sql(default_ctx.captured_queries) == []
    assert _branch_sql(shard_ctx.captured_queries) == []


def _is_exact_dict(value: object) -> TypeGuard[dict[object, object]]:
    """Whether a router hint is exactly a ``dict`` (a subclass is not a tenant token)."""
    return type(value) is dict


class _NestedTenantRouter:
    """Routes by state INSIDE the tenant hint object, which is ordinary router code.

    ``ConnectionRouter`` hands hint values to a router untouched, and a standard
    ``instance`` hint is itself mutable, so reading into one is legal. It is also
    why preserving a hint's identity cannot prove the route is unchanged.
    """

    def db_for_read(self, _model: type[Model], **hints: object) -> str | None:
        token = hints.get("tenant")
        if not _is_exact_dict(token):
            return None
        alias = token["alias"]
        assert type(alias) is str, token
        return alias

    def db_for_write(self, _model: type[Model], **_hints: object) -> str | None:
        return None

    def allow_relation(self, _obj1: Model, _obj2: Model, **_hints: object) -> bool | None:
        return None

    def allow_migrate(
        self,
        _db: str,
        _app_label: str,
        **_hints: object,
    ) -> bool | None:
        return None


@pytest.fixture
def mutable_hint_token(
    _reload_project_schema_for_acceptance_tests: None,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[dict[str, str]]:
    """Unrouted Branch list field whose tenant hint is a dict the override mutates in place."""
    token = {"alias": "shard_b"}

    def _hint_mutating_apply_sync(
        _cls: type[BranchOrder],
        _order_input: object,
        queryset: QuerySet[models.Branch],
        _info: object,
    ) -> QuerySet[models.Branch]:
        # Mutate INSIDE the hint value the source carried, then return an ordinary
        # ordered clone. ``QuerySet._clone`` carries the same ``_hints`` object
        # forward, so every identity the seal compares still holds.
        token["alias"] = "default"
        return queryset.order_by("name")

    monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(_hint_mutating_apply_sync))

    def _tenant_resolver(_root: object, _info: Info[object, object]) -> QuerySet[models.Branch]:
        qs = models.Branch.objects.all()
        monkeypatch.setattr(qs, "_hints", {"tenant": token})
        return qs

    @strawberry.type
    class _MutableHintQuery:
        branches_tenant: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=_tenant_resolver,
        )

    _current["schema"] = DjangoSchema(query=_MutableHintQuery, config=strawberry_config())
    yield token
    _current["schema"] = None


@pytest.mark.django_db(databases=["default", "shard_b"])
def test_post_orderset_mutable_hint_cannot_reroute_the_completed_read(
    mutable_hint_token: dict[str, str],
) -> None:
    """A hint mutated behind a preserved identity cannot move the read to another alias.

    The source is unrouted and carries a mutable tenant token the router reads
    into; at request time that token says ``shard_b``. The override edits the
    token to ``default`` and returns an ordinary ordered clone, so every hint
    object the seal compares is still the same object and the result is
    legitimately accepted. The effective alias was resolved and frozen before the
    override ran, and the accepted result is pinned to it, so the completed read
    is the one the source intended: the ``shard_b`` row comes back, the
    distinguishable ``default`` row does not, and no ``library_branch`` SQL
    reaches ``default`` at all.
    """
    token = mutable_hint_token
    models.Branch.objects.using("shard_b").create(name="Branch-ShardB", city="Boston")
    models.Branch.objects.using("default").create(name="Branch-Default", city="Boston")

    query = """
    query {
      branchesTenant(orderBy: [{ city: ASC }]) {
        name
      }
    }
    """
    client = Client()
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=True,
        MIDDLEWARE=middleware_without_debug_toolbar(),
        DATABASE_ROUTERS=[_NestedTenantRouter()],
    ):
        clear_url_caches()
        try:
            with (
                CaptureQueriesContext(connections["default"]) as default_ctx,
                CaptureQueriesContext(connections["shard_b"]) as shard_ctx,
            ):
                payload = graphql_payload(query, client=client)
        finally:
            clear_url_caches()

    assert "errors" not in payload, payload
    assert json_at(payload, "data", "branchesTenant") == [{"name": "Branch-ShardB"}]
    assert len(_branch_sql(shard_ctx.captured_queries)) == 1
    assert _branch_sql(default_ctx.captured_queries) == []
    # The override really did change what a late resolution would have answered.
    assert token["alias"] == "default"


# ---------------------------------------------------------------------------
# Per-test schema fixture (runs AFTER the autouse reload)
# ---------------------------------------------------------------------------


@pytest.fixture
def _build_test_schema(_reload_project_schema_for_acceptance_tests: None) -> Iterator[None]:
    """Build the per-test schema against the freshly-reloaded ``BookType``."""

    # IMPORTANT: read ``BookType`` off the module HERE (inside the fixture body).
    # A module-level ``from apps.library.schema import BookType`` would hold a
    # stale class object after each autouse reload cycle (per the shared
    # ``test_query/conftest.py::_reload_project_schema_for_acceptance_tests``
    # invariant); the reload is in place, so the module binding stays current.
    # The dependency ensures the read runs after that reload.
    @strawberry.type
    class _MultiDbTestQuery:
        def _books_on_shard_b(self) -> QuerySet[models.Book]:
            return (
                models.Book.objects.using("shard_b")
                .order_by("pk")
                .select_related(
                    "shelf__branch",
                )
            )

        books_on_shard_b: QuerySet[models.Book] = strawberry.field(
            resolver=_books_on_shard_b,
            graphql_type=list[library_schema.BookType],
        )

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = DjangoSchema(
        query=_MultiDbTestQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    yield
    _current["schema"] = None


@pytest.fixture
def _build_debug_test_schema(_reload_project_schema_for_acceptance_tests: None) -> Iterator[None]:
    """The debug-enabled sibling of ``_build_test_schema`` (spec-044 scenario 16).

    Same freshly-reloaded ``BookType`` / ``.using("shard_b")`` resolver shape,
    plus ``DjangoDebugExtension`` beside the optimizer's factory - the canonical
    consumer wiring under test.

    The debug extension is spelled as the acknowledgement factory
    (``lambda: DjangoDebugExtension(allow_unsafe_production=True)``) rather than
    a bare class entry: the extension fails closed under ``settings.DEBUG``
    false (spec-048 Decision 5) and pytest-django holds the setting false for
    the whole suite, so a bare class entry would publish nothing and this
    per-alias capture proof would assert against an absent payload. The factory
    still constructs one fresh instance per operation, which is the property the
    class entry was chosen for.
    """

    @strawberry.type
    class _MultiDbDebugTestQuery:
        def _books_on_shard_b(self) -> QuerySet[models.Book]:
            return (
                models.Book.objects.using("shard_b")
                .order_by("pk")
                .select_related(
                    "shelf__branch",
                )
            )

        books_on_shard_b: QuerySet[models.Book] = strawberry.field(
            resolver=_books_on_shard_b,
            graphql_type=list[library_schema.BookType],
        )

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = DjangoSchema(
        query=_MultiDbDebugTestQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer, lambda: DjangoDebugExtension(allow_unsafe_production=True)],
    )
    yield
    _current["schema"] = None


@pytest.fixture
def _build_loan_filter_test_schema(
    _reload_project_schema_for_acceptance_tests: None,
) -> Iterator[None]:
    """Build a per-test schema exposing a ``.using('shard_b')`` Loan LIST field with ``LoanFilter``.

    The shard-alias twin of ``_build_test_schema`` for the row-preserving
    relational-leaf predicate proof (spec-060 Part 1): the
    resolver applies the PRODUCTION ``LoanFilter`` (whose deep
    ``book__loans__patron__email`` leaf compiles to restriction subqueries, one per
    declared hop) over a queryset pinned to ``shard_b``, so every hop's subquery must
    run on that alias. ``LoanFilter`` / ``LoanType``
    are read off their modules inside the fixture body (like ``BookType`` above) so
    the freshly reloaded classes are used after the autouse registry clear.
    """

    @strawberry.type
    class _LoanFilterShardQuery:
        def _loans_on_shard_b(
            self,
            info: Info[object, object],
            filter: FilterInput[library_filters.LoanFilter] | None = None,  # noqa: A002
        ) -> QuerySet[models.Loan]:
            queryset = models.Loan.objects.using("shard_b").order_by("id")
            if filter is not None:
                queryset = library_filters.LoanFilter.apply_sync(filter, queryset, info)
            return queryset

        loans_on_shard_b: QuerySet[models.Loan] = strawberry.field(
            resolver=_loans_on_shard_b,
            graphql_type=list[library_schema.LoanType],
        )

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = DjangoSchema(
        query=_LoanFilterShardQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    yield
    _current["schema"] = None


# ---------------------------------------------------------------------------
# Seed helper - full Branch -> Shelf -> Book chain per alias
# ---------------------------------------------------------------------------


def _seed_book_chain(alias: str, *, title: str) -> "models.Book":
    """Seed a full ``Branch -> Shelf -> Book`` chain on ``alias``.

    ``Branch.name`` is ``unique=True``
    (``examples/fakeshop/apps/library/models.py::Branch #"models.TextField(unique=True)"``),
    so the branch / shelf field values are varied by ``title`` to keep two calls
    on the same alias from colliding when a test seeds multiple chains.
    """
    branch = models.Branch.objects.using(alias).create(
        name=f"Branch-{alias}-{title}",
        city="Boston",
    )
    shelf = models.Shelf.objects.using(alias).create(
        code=f"S-{alias}-{title}",
        topic="Test",
        branch=branch,
    )
    return models.Book.objects.using(alias).create(
        title=title,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
        shelf=shelf,
    )


# ---------------------------------------------------------------------------
# Tests - live /graphql/ HTTP against the sharded layout
# ---------------------------------------------------------------------------


def _expected_book(alias: str, title: str) -> JSONObject:
    return {
        "title": title,
        "shelf": {"code": f"S-{alias}-{title}", "branch": {"name": f"Branch-{alias}-{title}"}},
    }


@pytest.mark.usefixtures("_build_test_schema")
@pytest.mark.django_db(databases=["default", "shard_b"])
def test_using_shard_b_resolver_returns_rows_seeded_on_shard_b() -> None:
    """Two exact nested graphs are served from shard_b, with one read of each selected table."""
    _seed_book_chain("shard_b", title="A")
    _seed_book_chain("shard_b", title="B")
    query = "{ booksOnShardB { title shelf { code branch { name } } } }"
    with override_settings(ROOT_URLCONF=__name__):
        payload, statements = _capture_payload(query)
    assert payload == {
        "data": {
            "booksOnShardB": [_expected_book("shard_b", "A"), _expected_book("shard_b", "B")],
        },
    }
    _assert_read_alias(
        statements,
        "shard_b",
        {"library_book": 1, "library_shelf": 1, "library_branch": 1},
    )


@pytest.mark.usefixtures("_build_test_schema")
@pytest.mark.django_db(databases=["default", "shard_b"])
def test_cross_shard_isolation_default_rows_not_visible_via_shard_b_resolver() -> None:
    """Only the shard_b singleton is served; duplicates and default reads cannot hide in a set."""
    _seed_book_chain("default", title="default-only")
    _seed_book_chain("shard_b", title="shard-b-only")
    with override_settings(ROOT_URLCONF=__name__):
        payload, statements = _capture_payload("{ booksOnShardB { title } }")
    assert payload == {"data": {"booksOnShardB": [{"title": "shard-b-only"}]}}
    _assert_read_alias(statements, "shard_b", {"library_book": 1})


@pytest.mark.usefixtures("_build_debug_test_schema")
@pytest.mark.django_db(databases=["default", "shard_b"])
def test_debug_extension_captures_shard_b_alias_rows() -> None:
    """The debug payload reports all three real nested shard reads and restores both cursors."""
    _seed_book_chain("shard_b", title="DebugShard")
    prior_flags = {
        database_connection.alias: database_connection.force_debug_cursor
        for database_connection in connections.all()
    }
    with override_settings(ROOT_URLCONF=__name__):
        payload, statements = _capture_payload(
            "{ booksOnShardB { title shelf { code branch { name } } } }",
        )
    assert json_at(payload, "data") == {"booksOnShardB": [_expected_book("shard_b", "DebugShard")]}
    _assert_read_alias(
        statements,
        "shard_b",
        {"library_book": 1, "library_shelf": 1, "library_branch": 1},
    )
    debug = json_object(payload, "extensions", "debug")
    relevant = [
        row
        for row in json_list(debug, "sql")
        if any(
            f'"{table}"' in json_str(row, "sql")
            for table in ("library_book", "library_shelf", "library_branch")
        )
    ]
    assert len(relevant) == 3, relevant
    for row in relevant:
        assert json_str(row, "alias") == "shard_b"
        assert json_str(row, "vendor") == connections["shard_b"].vendor
        assert json_at(row, "isSelect") is True
    assert json_at(debug, "exceptions") == []
    for database_connection in connections.all():
        assert database_connection.force_debug_cursor is prior_flags[database_connection.alias]


def _seed_loan_relation_graph_on_shard_b() -> dict[str, int]:
    """Seed a small row-preserving relational-leaf graph on ``shard_b``.

    A ``shared_book`` carries two loans whose patrons both have "Cardio" emails,
    plus an ``other_book`` with a single non-matching ("Ortho") loan. The deep
    leaf ``book__loans__patron__email icontains "Cardio"`` matches a root loan
    when its BOOK has any loan to a "Cardio" patron - so both shared-book loans
    match (each once, row-preserving) and the other-book loan does not. Returns
    the captured pks (``unique_open_loan_per_book_patron`` forbids repeating a
    ``(book, patron)`` pair, so patrons are distinct per loan).
    """
    branch = models.Branch.objects.using("shard_b").create(name="Shard Medtrics", city="Boston")
    shelf = models.Shelf.objects.using("shard_b").create(
        code="SHARD-MED-1",
        topic="ward",
        branch=branch,
    )
    shared_book = models.Book.objects.using("shard_b").create(shelf=shelf, title="Shard Shared")
    other_book = models.Book.objects.using("shard_b").create(shelf=shelf, title="Shard Other")
    patron_a = models.Patron.objects.using("shard_b").create(name="Shard A", email="Cardio A")
    patron_b = models.Patron.objects.using("shard_b").create(name="Shard B", email="Cardio B")
    patron_c = models.Patron.objects.using("shard_b").create(name="Shard C", email="Ortho")
    relation_a = models.Loan.objects.using("shard_b").create(
        book=shared_book,
        patron=patron_a,
        note="checkout",
    )
    relation_b = models.Loan.objects.using("shard_b").create(
        book=shared_book,
        patron=patron_b,
        note="checkout",
    )
    unrelated = models.Loan.objects.using("shard_b").create(
        book=other_book,
        patron=patron_c,
        note="checkout",
    )
    return {
        "relation_a": saved_pk(relation_a.pk),
        "relation_b": saved_pk(relation_b.pk),
        "unrelated": saved_pk(unrelated.pk),
    }


@pytest.mark.usefixtures("_build_loan_filter_test_schema")
@pytest.mark.django_db(databases=["default", "shard_b"])
def test_row_preserving_relational_leaf_predicate_executes_on_shard_b_alias() -> None:
    """The relational-leaf predicate runs on the ``shard_b`` alias.

    The production ``LoanFilter`` deep leaf ``book__loans__patron__email`` (spelled
    ``bookLoansPatronEmail`` on the wire) is applied over a ``.using('shard_b')``
    queryset. Each declared hop's subquery derives from ``queryset.db``, so the
    whole filter - outer root scan AND the walk through ``book`` / ``loans`` /
    ``patron`` - must execute on ``shard_b``: the seeded shard rows return
    row-preserved (both shared-book loans, each once), and the captured ``shard_b``
    statement carries the ``library_book`` hop with no ``DISTINCT``.
    """
    pks = _seed_loan_relation_graph_on_shard_b()

    client = TestClient()
    with override_settings(ROOT_URLCONF=__name__):
        clear_url_caches()
        try:
            with (
                CaptureQueriesContext(connections["shard_b"]) as shard_captured,
                CaptureQueriesContext(default_connection) as default_captured,
            ):
                res = client.query(
                    """
                    query {
                      loansOnShardB(filter: { bookLoansPatronEmail: { iContains: "Cardio" } }) {
                        id
                      }
                    }
                    """,
                )
        finally:
            clear_url_caches()

    # Row-preserving: exactly both shared-book loans, id-ordered, each once.
    assert res.data is not None
    assert [json_at(loan, "id") for loan in json_list(res.data, "loansOnShardB")] == [
        pks["relation_a"],
        pks["relation_b"],
    ]

    # The filtered root statement, its hops included, ran on shard_b, never on default.
    shard_loan_sql = [
        query["sql"]
        for query in shard_captured.captured_queries
        if 'FROM "library_loan"' in query["sql"] and "library_book" in query["sql"]
    ]
    assert len(shard_loan_sql) == 1, shard_captured.captured_queries
    for sql in shard_loan_sql:
        assert "DISTINCT" not in sql.upper()
    statements = {
        "default": [query["sql"] for query in default_captured.captured_queries],
        "shard_b": [query["sql"] for query in shard_captured.captured_queries],
    }
    _assert_read_alias(
        statements,
        "shard_b",
        {"library_loan": 1, "library_book": 0, "library_patron": 0},
    )
    assert '"library_patron"' in shard_loan_sql[0], shard_loan_sql


@pytest.fixture
def _build_branch_tag_filter_test_schema() -> Iterator[None]:
    """Build a per-test schema whose ``.using('shard_b')`` Branch list filters through ``tags``.

    ``tags`` is ``Branch``'s ``GenericRelation``; the branch-local ``RelatedFilter``
    over it restricts the branches through ``optimizer/predicates.py::related_rows_exist``,
    which reads ``TaggedItem`` rows through their registered type. The project schema
    registers none, so the test runs on ``private_registry``.
    """
    make_django_type("ShardTaggedItemType", models.TaggedItem, ("id", "tag"), node=False)
    branch_type = make_django_type("ShardBranchType", models.Branch, ("id", "name"), node=False)
    finalize_django_types()

    class _TaggedItemFilter(FilterSet):
        class Meta:
            model = models.TaggedItem
            fields = {"tag": ["exact"]}

    class _BranchTagFilter(FilterSet):
        tags = RelatedFilter(_TaggedItemFilter, field_name="tags")

        class Meta:
            model = models.Branch
            fields = {"name": ["exact"]}

    @strawberry.type
    class _BranchTagShardQuery:
        def _branches_tagged_on_shard_b(
            self,
            info: Info[object, object],
            tag: str,
        ) -> QuerySet[models.Branch]:
            queryset = models.Branch.objects.using("shard_b").order_by("id")
            return _BranchTagFilter.apply_sync({"tags": {"tag": tag}}, queryset, info)

        branches_tagged_on_shard_b: QuerySet[models.Branch] = strawberry.field(
            resolver=_branches_tagged_on_shard_b,
            graphql_type=list[branch_type],
        )

    optimizer = DjangoOptimizerExtension()
    _current["schema"] = strawberry.Schema(
        query=_BranchTagShardQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )
    ContentType.objects.clear_cache()
    yield
    ContentType.objects.clear_cache()
    _current["schema"] = None


@pytest.mark.usefixtures("private_registry", "_build_branch_tag_filter_test_schema")
@pytest.mark.django_db(databases=["default", "shard_b"])
def test_generic_relation_filter_matches_content_type_on_shard_b_alias() -> None:
    """A ``GenericRelation`` branch filter matches ``shard_b``'s own ``Branch`` content type.

    Content-type pks are per database: ``shard_b``'s ``library.branch`` row is
    forced onto a pk ``default`` does not use. The restriction names the content
    type by natural key and joins it on the statement's alias, so the branch
    tagged under ``shard_b``'s pk comes back, and the branch whose tag sits on
    a ``Shelf`` with the same ``object_id`` does not.
    """
    default_branch_type = ContentType.objects.db_manager("default").get_for_model(models.Branch)
    shard_branch_type_pk = default_branch_type.id + 500
    ContentType.objects.using("shard_b").filter(app_label="library", model="branch").delete()
    ContentType.objects.using("shard_b").create(
        pk=shard_branch_type_pk,
        app_label="library",
        model="branch",
    )
    ContentType.objects.clear_cache()
    shelf_type = ContentType.objects.using("shard_b").get(app_label="library", model="shelf")
    tagged = models.Branch.objects.using("shard_b").create(name="Shard Tagged")
    other = models.Branch.objects.using("shard_b").create(name="Shard Other")
    models.TaggedItem.objects.using("shard_b").create(
        tag="a1",
        content_type_id=shard_branch_type_pk,
        object_id=saved_pk(tagged.pk),
    )
    models.TaggedItem.objects.using("shard_b").create(
        tag="a1",
        content_type_id=shelf_type.id,
        object_id=saved_pk(other.pk),
    )

    client = Client()
    with override_settings(ROOT_URLCONF=__name__):
        clear_url_caches()
        try:
            data = _graphql_data('{ branchesTaggedOnShardB(tag: "a1") { name } }', client=client)
        finally:
            clear_url_caches()

    assert [json_at(b, "name") for b in json_list(data, "branchesTaggedOnShardB")] == [
        "Shard Tagged",
    ]


# ---------------------------------------------------------------------------
# Write-alias pinning and uniqueness refusals for generated mutations (live sharded HTTP)
# ---------------------------------------------------------------------------
#
# The write tests drive the PROJECT schema (config.schema - the real products
# write surface over DjangoSchema) under a router whose READ and WRITE answers
# diverge for the products app: reads route to ``default``, writes to
# ``shard_b``. The pipeline must pin EVERYTHING - locate, relation visibility,
# the write, the re-fetch, and uniqueness validation - to the ONE write alias,
# so the shard_b twin of a same-pk row pair is the one affected and the
# default twin never is.


class _ProductsWriteToShardBRouter:
    """Route products reads to ``default`` and products writes to ``shard_b``.

    Only the products app is routed; auth/session/user machinery stays on
    ``default`` so login and permissions behave normally.
    """

    def db_for_read(self, model: type[Model], **hints: object) -> str | None:
        if model._meta.app_label != "products":
            return None
        # Honor the instance hint (the standard primary/replica router shape,
        # per Django's own router conventions): a relation loaded FROM a
        # shard_b-materialized instance reads beside it. Fresh reads with no
        # instance context go to the divergent read alias - the divergence the
        # pipeline's pinning must override.
        instance = hints.get("instance")
        instance_db = getattr(getattr(instance, "_state", None), "db", None)
        if isinstance(instance_db, str):
            return instance_db
        return "default"

    def db_for_write(self, model: type[Model], **_hints: object) -> str | None:
        if model._meta.app_label == "products":
            return "shard_b"
        return None

    def allow_relation(self, _obj1: Model, _obj2: Model, **_hints: object) -> bool | None:
        return True


@pytest.fixture
def _project_schema(_reload_project_schema_for_acceptance_tests: None) -> Iterator[None]:
    """Serve the freshly-reloaded PROJECT schema (the real write surface)."""
    _current["schema"] = config_schema.schema
    yield
    _current["schema"] = None


def _pin_seeded_same_pk_item_pair(pk_base: int) -> None:
    """Pin caller-service-seeded rows to the intentional same-PK twins on both aliases."""
    for alias in ("default", "shard_b"):
        categories = list(product_models.Category.objects.using(alias).order_by("pk")[:2])
        assert len(categories) == 2
        category, parking_category = categories
        item = (
            product_models.Item.objects.using(alias)
            .filter(category=category)
            .order_by("pk")
            .first()
        )
        assert item is not None
        # Existing child foreign keys prevent a parent-PK update. Park seeded Items
        # on another real seeded Category and remove only the old property's graph.
        product_models.Item.objects.using(alias).filter(category=category).update(
            category=parking_category,
        )
        product_models.Property.objects.using(alias).filter(category=category).delete()
        assert (
            product_models.Category.objects.using(alias)
            .filter(pk=category.pk)
            .update(
                id=pk_base,
                name=f"pin-category-{alias}-{pk_base}",
                is_private=False,
            )
            == 1
        )
        # Entry.item is a real FK, so its rows must go before moving this Item's PK.
        product_models.Entry.objects.using(alias).filter(item=item).delete()
        assert (
            product_models.Item.objects.using(alias)
            .filter(pk=item.pk)
            .update(
                id=pk_base,
                name=f"pin-item-{alias}",
                category_id=pk_base,
                is_private=False,
            )
            == 1
        )


def _login_products_writer(*codenames: str) -> Client:
    create_users(1)
    user = User.objects.get(username="staff_1")
    for codename in codenames:
        user.user_permissions.add(
            Permission.objects.get(codename=codename, content_type__app_label="products"),
        )
    client = Client()
    client.force_login(User.objects.get(pk=read_attr(user, "pk")))
    return client


_UPDATE_ITEM_MUTATION = """
mutation($id: ID!, $d: ItemPartialInput!) {
  updateItem(id: $id, data: $d) {
    node { name category { name } }
    errors { field messages codes }
  }
}
"""


def _item_gid(pk: int) -> str:
    return global_id_for(products_schema.ItemType, pk)


@pytest.mark.usefixtures("_project_schema")
@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_mutation_write_pins_locate_write_and_refetch_to_the_write_alias() -> None:
    """Locate, update, relation and returned row all stay on the write alias's same-PK twin."""
    seed_data(2, db_alias="default")
    seed_data(2, db_alias="shard_b")
    _pin_seeded_same_pk_item_pair(90001)
    client = _login_products_writer("change_item", "view_category")
    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_ProductsWriteToShardBRouter()],
    ):
        payload, statements = _capture_payload(
            _UPDATE_ITEM_MUTATION,
            client=client,
            variables={"id": _item_gid(90001), "d": {"name": "pinned-write"}},
        )
    assert payload == {
        "data": {
            "updateItem": {
                "node": {
                    "name": "pinned-write",
                    "category": {"name": "pin-category-shard_b-90001"},
                },
                "errors": [],
            },
        },
    }
    assert _touching_tables(statements["default"], "products_item", "products_category") == []
    assert any(sql.startswith('UPDATE "products_item"') for sql in statements["shard_b"])
    assert product_models.Item.objects.using("shard_b").get(pk=90001).name == "pinned-write"
    assert product_models.Item.objects.using("default").get(pk=90001).name == "pin-item-default"


@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
@pytest.mark.usefixtures("private_registry")
def test_custom_nodeid_mutation_resolves_real_pk_on_write_alias() -> None:
    """A custom NodeID mutation resolves its non-pk payload on ``shard_b``.

    ``CategoryNode.name`` is the Relay id, while the mutation locate still needs
    the row's real integer pk. The target exists only on the write alias and the
    router sends fresh reads to ``default``; resolving the NodeID through the
    default manager would produce an in-band not-found error before the locate.
    """
    seed_data(1, db_alias="default")
    seed_data(1, db_alias="shard_b")
    registry.clear()
    category_pk = 92021
    for alias, name, description in (
        ("default", "read-alias-category", "default untouched"),
        ("shard_b", "write-alias-category", "before"),
    ):
        seeded = product_models.Category.objects.using(alias).order_by("pk").first()
        assert seeded is not None
        # Move an existing seeded row to the intentional shared PK. Its child FKs
        # must be pruned before that update; the other seeded providers stay intact.
        product_models.Item.objects.using(alias).filter(category_id=seeded.pk).delete()
        product_models.Property.objects.using(alias).filter(category_id=seeded.pk).delete()
        updated = (
            product_models.Category.objects.using(alias)
            .filter(pk=seeded.pk)
            .update(
                id=category_pk,
                name=name,
                description=description,
            )
        )
        assert updated == 1
    target = product_models.Category.objects.using("shard_b").get(pk=category_pk)

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = product_models.Category
            fields = ("id", "name", "description")
            interfaces = (relay.Node,)
            primary = True

    class UpdateCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "update"

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        update_category = DjangoMutationField(UpdateCategory)

    finalize_django_types()
    _current["schema"] = DjangoSchema(
        query=Query,
        mutation=Mutation,
        config=strawberry_config(),
        extensions=[],
    )
    client = _login_products_writer("change_category")
    query = """
      mutation($id: ID!, $d: CategoryPartialInput!) {
        updateCategory(id: $id, data: $d) {
          node { id description }
          errors { field messages }
        }
      }
    """
    try:
        with override_settings(
            ROOT_URLCONF=__name__,
            DATABASE_ROUTERS=[_ProductsWriteToShardBRouter()],
        ):
            clear_url_caches()
            try:
                with (
                    CaptureQueriesContext(connections["default"]) as on_default,
                    CaptureQueriesContext(connections["shard_b"]) as on_shard_b,
                ):
                    response = TestClient(client=client).query(
                        query,
                        variables={
                            "id": global_id_for(CategoryNode, target.name),
                            "d": {"description": "write-alias-updated"},
                        },
                    )
            finally:
                clear_url_caches()
    finally:
        _current["schema"] = None

    assert response.data == {
        "updateCategory": {
            "node": {
                "id": global_id_for(CategoryNode, target.name),
                "description": "write-alias-updated",
            },
            "errors": [],
        },
    }
    category_sql = {
        alias: [
            entry["sql"]
            for entry in captured.captured_queries
            if '"products_category"' in entry["sql"]
        ]
        for alias, captured in (("default", on_default), ("shard_b", on_shard_b))
    }
    assert category_sql["default"] == [], category_sql
    assert any(sql.startswith('UPDATE "products_category"') for sql in category_sql["shard_b"])
    assert (
        product_models.Category.objects.using("shard_b").get(pk=category_pk).description
        == "write-alias-updated"
    )
    assert (
        product_models.Category.objects.using("default").get(pk=category_pk).description
        == "default untouched"
    )


@pytest.mark.usefixtures("_project_schema")
@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_model_uniqueness_validation_uses_write_alias_without_changing_either_twin() -> None:
    """A name collision is refused by pre-write validation on shard_b; both twins stay unchanged."""
    seed_data(2, db_alias="default")
    seed_data(2, db_alias="shard_b")
    _pin_seeded_same_pk_item_pair(90011)
    sibling = product_models.Item.objects.using("shard_b").exclude(pk=90011).order_by("pk").first()
    assert sibling is not None
    product_models.Entry.objects.using("shard_b").filter(item=sibling).delete()
    product_models.Item.objects.using("shard_b").filter(pk=sibling.pk).update(
        name="pin-sibling",
        category_id=90011,
        is_private=False,
    )
    client = _login_products_writer("change_item", "view_category")
    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_ProductsWriteToShardBRouter()],
    ):
        payload, statements = _capture_payload(
            _UPDATE_ITEM_MUTATION,
            client=client,
            variables={"id": _item_gid(saved_pk(sibling.pk)), "d": {"name": "pin-item-shard_b"}},
        )
    assert payload == {
        "data": {
            "updateItem": {
                "node": None,
                "errors": [
                    {
                        "field": "__all__",
                        "messages": ["Item with this Category and Name already exists."],
                        "codes": ["unique_together"],
                    },
                ],
            },
        },
    }
    assert _touching_tables(statements["default"], "products_item", "products_category") == []
    assert _from_table(statements["shard_b"], "products_item"), statements
    assert not any(sql.startswith('UPDATE "products_item"') for sql in statements["shard_b"])
    assert product_models.Item.objects.using("shard_b").get(pk=sibling.pk).name == "pin-sibling"
    assert product_models.Item.objects.using("shard_b").get(pk=90011).name == "pin-item-shard_b"
    assert product_models.Item.objects.using("default").get(pk=90011).name == "pin-item-default"


class _SessionStoreToShardBRouter:
    """Route ``sessions.Session`` reads and writes to ``shard_b``; everything else stays default.

    The session store on its own alias: the write pins ``default``, the user and
    permission tables stay there too, and only the lazy request user's session
    load reads ``shard_b``.
    """

    def db_for_read(self, model: type[Model], **_hints: object) -> str | None:
        return "shard_b" if model._meta.label == "sessions.Session" else None

    def db_for_write(self, model: type[Model], **_hints: object) -> str | None:
        return "shard_b" if model._meta.label == "sessions.Session" else None


@pytest.mark.usefixtures("_project_schema")
@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_mutation_authorizes_a_session_stored_on_its_own_alias() -> None:
    """A shard_b session authenticates a default-only Category write without cross-alias copies."""
    create_users(1)
    user = User.objects.get(username="staff_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_category", content_type__app_label="products"),
    )
    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_SessionStoreToShardBRouter()],
    ):
        client = Client()
        client.force_login(User.objects.get(pk=read_attr(user, "pk")))
        payload, statements = _capture_payload(
            "mutation($d: CategoryInput!) { createCategory(data: $d) { "
            "node { name } errors { field messages } } }",
            client=client,
            variables={"d": {"name": "zzz_session_alias_cat"}},
        )
    assert payload == {
        "data": {
            "createCategory": {"node": {"name": "zzz_session_alias_cat"}, "errors": []},
        },
    }
    assert (
        product_models.Category.objects.using("default")
        .filter(name="zzz_session_alias_cat")
        .count()
        == 1
    )
    assert (
        not product_models.Category.objects.using("shard_b")
        .filter(name="zzz_session_alias_cat")
        .exists()
    )
    assert _from_table(statements["default"], "django_session") == []
    assert len(_from_table(statements["shard_b"], "django_session")) == 1, statements
    assert _from_table(statements["default"], "auth_user"), statements
    assert (
        _touching_tables(
            statements["shard_b"],
            "auth_user",
            "auth_permission",
            "products_category",
        )
        == []
    )
    assert any(sql.startswith('INSERT INTO "products_category"') for sql in statements["default"])


# ---------------------------------------------------------------------------
# Serializer-flavor write-alias pinning
# ---------------------------------------------------------------------------
#
# The serializer twin of the model-flavor pinning tests above: the SERIALIZER
# pipeline's locate, relation decode, DRF's second relation lookup (the scoped
# field queryset), the save, the re-fetch, and constraint refusal must all
# ride the router's ONE write answer. Routed on the library app so the project
# schema's ``updateBookGenresViaSerializer`` (a ``SerializerMutation`` with an
# M2M ``genres`` relation) is the surface under test.


class _LibraryWriteToShardBRouter:
    """Route library reads to ``default`` and library writes to ``shard_b``."""

    def db_for_read(self, model: type[Model], **hints: object) -> str | None:
        if model._meta.app_label != "library":
            return None
        instance = hints.get("instance")
        instance_db = getattr(getattr(instance, "_state", None), "db", None)
        if isinstance(instance_db, str):
            return instance_db
        return "default"

    def db_for_write(self, model: type[Model], **_hints: object) -> str | None:
        if model._meta.app_label == "library":
            return "shard_b"
        return None

    def allow_relation(self, _obj1: Model, _obj2: Model, **_hints: object) -> bool | None:
        return True


def _seed_same_pk_book_pair(pk_base: int) -> None:
    """Seed a same-pk ``Branch -> Shelf -> Book`` chain on BOTH aliases.

    Same rationale as ``_pin_seeded_same_pk_item_pair``: only per-alias field values
    can prove which alias each pipeline step really used.
    """
    for alias in ("default", "shard_b"):
        branch = models.Branch.objects.using(alias).create(
            pk=pk_base,
            name=f"ser-branch-{alias}-{pk_base}",
            city="Boston",
        )
        shelf = models.Shelf.objects.using(alias).create(
            pk=pk_base,
            code=f"ser-shelf-{alias}",
            topic="Test",
            branch=branch,
        )
        models.Book.objects.using(alias).create(
            pk=pk_base,
            title=f"ser-book-{alias}",
            shelf=shelf,
        )


_UPDATE_BOOK_GENRES_MUTATION = """
mutation($id: ID!, $d: BookGenresSerializerPartialInput!) {
  updateBookGenresViaSerializer(id: $id, data: $d) {
    node { title }
    errors { field messages codes }
  }
}
"""


def _library_gid(node_type: type[DjangoType], pk: int) -> str:
    return global_id_for(node_type, pk)


@pytest.mark.usefixtures("_project_schema")
@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_serializer_mutation_pins_locate_relation_save_and_refetch_to_write_alias() -> None:
    """The serializer updates only shard_b and replaces its old genre while retaining default's set."""
    _seed_same_pk_book_pair(91001)
    shard_genre = models.Genre.objects.using("shard_b").create(name="ser-genre-shard-b-only")
    old_shard_genre = models.Genre.objects.using("shard_b").create(name="old-shard-genre")
    default_genre = models.Genre.objects.using("default").create(name="retained-default-genre")
    shard_book = models.Book.objects.using("shard_b").get(pk=91001)
    default_book = models.Book.objects.using("default").get(pk=91001)
    shard_book.genres.add(old_shard_genre)
    default_book.genres.add(default_genre)
    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_LibraryWriteToShardBRouter()],
    ):
        payload, statements = _capture_payload(
            _UPDATE_BOOK_GENRES_MUTATION,
            variables={
                "id": _library_gid(library_schema.BookType, 91001),
                "d": {
                    "title": "ser-pinned-write",
                    "genres": [
                        _library_gid(library_schema.GenreType, saved_pk(shard_genre.pk)),
                    ],
                },
            },
        )
    assert payload == {
        "data": {
            "updateBookGenresViaSerializer": {"node": {"title": "ser-pinned-write"}, "errors": []},
        },
    }
    shard_book.refresh_from_db()
    default_book.refresh_from_db()
    assert shard_book.title == "ser-pinned-write"
    assert list(shard_book.genres.values_list("name", flat=True)) == ["ser-genre-shard-b-only"]
    assert default_book.title == "ser-book-default"
    assert list(default_book.genres.values_list("name", flat=True)) == ["retained-default-genre"]
    assert (
        _touching_tables(
            statements["default"],
            "library_book",
            "library_genre",
            "library_book_genres",
        )
        == []
    )
    assert any(sql.startswith('UPDATE "library_book"') for sql in statements["shard_b"])
    assert any(
        sql.startswith('DELETE FROM "library_book_genres"') for sql in statements["shard_b"]
    )


@pytest.mark.usefixtures("_project_schema")
@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_serializer_unique_validator_reads_write_alias() -> None:
    """A default-only collision does not poison validation of the shard_b update."""
    _seed_same_pk_book_pair(91006)
    default_shelf = models.Shelf.objects.using("default").get(pk=91006)
    models.Book.objects.using("default").create(
        title="validator-default-only-collision",
        shelf=default_shelf,
    )

    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_LibraryWriteToShardBRouter()],
    ):
        clear_url_caches()
        try:
            with (
                CaptureQueriesContext(connections["default"]) as on_default,
                CaptureQueriesContext(connections["shard_b"]) as on_shard_b,
            ):
                res = TestClient().query(
                    _UPDATE_BOOK_TITLE_VALIDATOR_MUTATION,
                    variables={
                        "id": _library_gid(library_schema.BookType, 91006),
                        "d": {"title": "validator-default-only-collision"},
                    },
                )
        finally:
            clear_url_caches()

    assert res.data == {
        "updateBookTitleWithAliasValidator": {
            "node": {"title": "validator-default-only-collision"},
            "errors": [],
        },
    }
    assert _touching_tables([row["sql"] for row in on_default], "library_book") == []
    assert _from_table([row["sql"] for row in on_shard_b], "library_book")
    assert (
        models.Book.objects.using("shard_b").get(pk=91006).title
        == "validator-default-only-collision"
    )
    assert models.Book.objects.using("default").get(pk=91006).title == "ser-book-default"


@pytest.mark.usefixtures("_project_schema")
@pytest.mark.django_db(databases=["default", "shard_b"], transaction=True)
def test_serializer_constraint_refusal_leaves_each_alias_unchanged() -> None:
    """The database rejects a conflicting shard_b title before a successful write can change either twin."""
    _seed_same_pk_book_pair(91011)
    shard_shelf = models.Shelf.objects.using("shard_b").get(pk=91011)
    models.Book.objects.using("shard_b").create(title="ser-sibling", shelf=shard_shelf)
    with override_settings(
        ROOT_URLCONF=__name__,
        DATABASE_ROUTERS=[_LibraryWriteToShardBRouter()],
    ):
        payload, statements = _capture_payload(
            _UPDATE_BOOK_GENRES_MUTATION,
            variables={
                "id": _library_gid(library_schema.BookType, 91011),
                "d": {"title": "ser-sibling"},
            },
        )
    assert payload == {
        "data": {
            "updateBookGenresViaSerializer": {
                "node": None,
                "errors": [
                    {
                        "field": "__all__",
                        "messages": ["A database constraint was violated."],
                        "codes": ["constraint"],
                    },
                ],
            },
        },
    }
    assert _touching_tables(statements["default"], "library_book") == []
    assert any(sql.startswith('UPDATE "library_book"') for sql in statements["shard_b"])
    assert models.Book.objects.using("shard_b").get(pk=91011).title == "ser-book-shard_b"
    assert models.Book.objects.using("default").get(pk=91011).title == "ser-book-default"


# ---------------------------------------------------------------------------
# The planned prefetch child's connection
# ---------------------------------------------------------------------------


def _prefetch_alias_schema(
    child_hook: Callable[
        [type[DjangoType], QuerySet[models.Book], Info[object, object]],
        QuerySet[models.Book],
    ],
    *,
    root_alias: str | None = None,
    expose_routing_error: bool = False,
) -> strawberry.Schema:
    """A ``shelves { books }`` schema whose CHILD type carries ``child_hook``.

    The root resolver hands back a queryset (pinned to ``root_alias`` when one is
    given) under a mounted optimizer, so the walker plans ``books`` as a
    ``Prefetch`` and builds that child itself
    (``django_strawberry_framework/optimizer/walker.py::_build_child_queryset``).
    ``child_hook`` is the only consumer code running inside the child's seal, and
    the child is the only thing in the query that could name a second connection.
    """
    registry.clear()
    make_django_type(
        "AliasBookType",
        models.Book,
        ("id", "title"),
        node=False,
        namespace_extra={"get_queryset": classmethod(child_hook)},
    )
    shelf_type = make_django_type(
        "AliasShelfType",
        models.Shelf,
        ("id", "code", "books"),
        node=False,
    )
    finalize_django_types()

    @strawberry.type
    class _PrefetchAliasQuery:
        def _shelves(self) -> QuerySet[models.Shelf]:
            queryset = models.Shelf.objects.all()
            if root_alias is not None:
                queryset = queryset.using(root_alias)
            return queryset

        shelves: QuerySet[models.Shelf] = strawberry.field(
            resolver=_shelves,
            graphql_type=list[shelf_type],
        )

    optimizer = DjangoOptimizerExtension()
    # The alias-refusal row names its internal ConfigurationError; accepted controls
    # retain the native policy instead of globally disabling masking in this holder.
    return DjangoSchema(
        error_policy={"enabled": False} if expose_routing_error else None,
        query=_PrefetchAliasQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


_PREFETCH_ALIAS_QUERY = "{ shelves { code books { title } } }"


def _post_prefetch_alias_query(
    schema: strawberry.Schema,
) -> tuple[JSONObject, dict[str, list[str]]]:
    """POST ``_PREFETCH_ALIAS_QUERY`` against ``schema``; return (payload, per-alias SQL)."""
    _current["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            with (
                CaptureQueriesContext(connections["default"]) as on_default,
                CaptureQueriesContext(connections["shard_b"]) as on_shard_b,
            ):
                payload = graphql_payload(
                    _PREFETCH_ALIAS_QUERY,
                    client=Client(),
                    url="/graphql/",
                )
    finally:
        _current["schema"] = None
        clear_url_caches()
    book_sql = {
        alias: [
            entry["sql"]
            for entry in captured.captured_queries
            if 'FROM "library_book"' in entry["sql"]
        ]
        for alias, captured in (("default", on_default), ("shard_b", on_shard_b))
    }
    return payload, book_sql


@pytest.mark.django_db(databases=["default", "shard_b"])
@pytest.mark.usefixtures("private_registry")
def test_planned_prefetch_child_cannot_route_itself_to_the_other_shard() -> None:
    """A child hook returning ``.using('shard_b')`` fails the planned relation closed.

    Nothing else in the query names ``shard_b``: the parent rows are read on
    ``default``, so accepting the child would schedule one GraphQL resolution
    across two connections and serve the other shard's rows through a relation
    whose parents do not exist there. The refusal is what keeps that from
    reaching SQL at all - neither alias runs a ``library_book`` read.
    """
    _seed_book_chain("default", title="on-default")
    _seed_book_chain("shard_b", title="on-shard-b")

    payload, book_sql = _post_prefetch_alias_query(
        _prefetch_alias_schema(
            lambda _cls, queryset, _info: queryset.using("shard_b"),
            expose_routing_error=True,
        ),
    )

    assert payload["data"] is None
    assert len(json_list(payload, "errors")) == 1, payload
    assert json_at(payload, "errors", 0, "path") == ["shelves"]
    message = json_str(payload, "errors", 0, "message")
    assert "AliasBookType.get_queryset" in message
    assert "routed to alias 'shard_b'" in message
    assert book_sql == {"default": [], "shard_b": []}


@pytest.mark.django_db(databases=["default", "shard_b"])
@pytest.mark.usefixtures("private_registry")
def test_planned_prefetch_child_inherits_an_unrouted_parents_connection() -> None:
    """Control: an unrouted child under an unrouted parent stays on ``default``."""
    _seed_book_chain("default", title="on-default")
    _seed_book_chain("shard_b", title="on-shard-b")

    payload, book_sql = _post_prefetch_alias_query(
        _prefetch_alias_schema(lambda _cls, queryset, _info: queryset.exclude(title="")),
    )

    assert payload == {
        "data": {
            "shelves": [
                {"code": "S-default-on-default", "books": [{"title": "on-default"}]},
            ],
        },
    }
    assert len(book_sql["default"]) == 1, book_sql
    assert book_sql["shard_b"] == []


@pytest.mark.django_db(databases=["default", "shard_b"])
@pytest.mark.usefixtures("private_registry")
def test_planned_prefetch_child_follows_a_routed_parent_onto_its_shard() -> None:
    """Control: the same unrouted child follows a ``.using('shard_b')`` parent.

    The child queryset the walker builds carries no alias of its own, which is
    exactly what lets Django resolve it against the parent rows' connection at
    fetch time - so pinning the parent is how a consumer moves a whole resolution
    onto another shard, and the child never has to say so itself.
    """
    _seed_book_chain("default", title="on-default")
    _seed_book_chain("shard_b", title="on-shard-b")

    payload, book_sql = _post_prefetch_alias_query(
        _prefetch_alias_schema(
            lambda _cls, queryset, _info: queryset.exclude(title=""),
            root_alias="shard_b",
        ),
    )

    assert payload == {
        "data": {
            "shelves": [
                {"code": "S-shard_b-on-shard-b", "books": [{"title": "on-shard-b"}]},
            ],
        },
    }
    assert len(book_sql["shard_b"]) == 1, book_sql
    assert book_sql["default"] == []


@pytest.mark.django_db(databases=["default", "shard_b"])
@pytest.mark.usefixtures("private_registry")
def test_planned_prefetch_child_cascade_subquery_follows_a_routed_parent_onto_its_shard() -> None:
    """A child hook's cascade composes its ``Book.shelf`` subquery on the parent's shard.

    The child queryset the walker builds carries no alias, so the cascade inside
    the child hook runs while the child has not yet been bound to a connection.
    Under a ``.using('shard_b')`` parent the whole child read - the outer
    ``library_book`` SELECT and the inlined ``library_shelf`` membership subquery -
    must execute on ``shard_b``: a subquery pinned anywhere else is either refused
    by Django as a cross-database subquery or reads another shard's visibility.
    """
    _seed_book_chain("default", title="on-default")
    _seed_book_chain("shard_b", title="on-shard-b")

    payload, book_sql = _post_prefetch_alias_query(
        _prefetch_alias_schema(
            apply_cascade_permissions,
            root_alias="shard_b",
        ),
    )

    assert payload == {
        "data": {
            "shelves": [
                {"code": "S-shard_b-on-shard-b", "books": [{"title": "on-shard-b"}]},
            ],
        },
    }
    assert book_sql["default"] == []
    assert len(book_sql["shard_b"]) == 1, book_sql
    assert "IN (SELECT" in book_sql["shard_b"][0]
    assert 'FROM "library_shelf"' in book_sql["shard_b"][0]
