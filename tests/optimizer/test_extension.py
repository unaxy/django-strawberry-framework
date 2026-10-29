"""DjangoOptimizerExtension tests for gating, caching, strictness, schema audit, context, and querysets.

Plan-object, cache-key, and construction-time rows. SQL facts live in
``examples/fakeshop/test_query/test_library_api.py``,
``examples/fakeshop/test_query/test_optimizer_auto_api.py``, and
``examples/fakeshop/test_query/test_products_visibility_api.py``.

The prefetch lookup for a reverse FK declared without ``related_name`` (the
accessor, never the query name) is pinned live over ``Venue.repairticket`` in
``examples/fakeshop/test_query/test_library_inheritance_api.py``.

Every test uses the autouse ``_isolate_registry`` fixture so the
global ``registry`` is cleared on entry and exit.
"""

import asyncio
import contextlib
import contextvars
import datetime
import decimal
import gc
import uuid
import warnings
import weakref
from collections import OrderedDict
from collections.abc import Callable, Coroutine, Iterable, Iterator, Mapping
from types import MappingProxyType, SimpleNamespace
from typing import TYPE_CHECKING, NoReturn, TypeGuard

import pytest
import pytest_django
import strawberry
from apps.library.models import Issue, MembershipCard, Patron
from apps.products import services
from apps.products.models import Category, Entry, Item, Property
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import Manager, Model, Prefetch, QuerySet
from django.http import HttpRequest, QueryDict
from django.test.utils import CaptureQueriesContext
from django.utils.functional import SimpleLazyObject
from graphql import (
    DefinitionNode,
    DocumentNode,
    FragmentDefinitionNode,
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    OperationDefinitionNode,
    OperationType,
    parse,
)
from strawberry import relay
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types import ExecutionResult
from strawberry.types.nodes import SelectedField
from typing_extensions import override

import django_strawberry_framework.optimizer._context as ctx_mod
import django_strawberry_framework.optimizer.extension as extension_module
from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    OptimizerHint,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.keyset import declared_cursor_state_for_definition
from django_strawberry_framework.optimizer import logger as optimizer_logger
from django_strawberry_framework.optimizer._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_KEYS,
    DST_OPTIMIZER_LOOKUP_PATHS,
    DST_OPTIMIZER_PLAN,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_STRICTNESS,
    active_optimizer,
    active_strictness,
    begin_execution_frame,
    cache_key_parts_memo,
    clear_optimizer_context,
    converted_selections_memo,
    end_execution_frame,
    execution_plan_memo,
    fk_id_elision_keys,
    get_context_value,
    optimizer_value,
    planned_resolver_keys,
    publish_scoped_relations,
    publish_window_cursor_states,
    relation_is_optimizer_scoped,
    stash_for_optimizer,
    stash_on_context,
    stashed_strictness,
    window_cursor_state,
)
from django_strawberry_framework.optimizer._context import (
    active_optimizer as _active_optimizer,
)
from django_strawberry_framework.optimizer.extension import (
    _collect_cache_relevant_var_names,
    _collect_cache_var_families,
    _collect_schema_reachable_types,
    _hashable_variable_value,
    _named_children,
    _node_children_with_runtime_prefix,
    _resolve_model_from_return_type,
    _stash_on_context,
    _walk_cache_relevant_vars,
    apply_connection_optimization,
    clear_document_key_cache,
)
from django_strawberry_framework.optimizer.hints import hint_is_skip
from django_strawberry_framework.optimizer.plans import OptimizationPlan, PrefetchSeal
from django_strawberry_framework.optimizer.selections import PYTHON_NAME_ATTR
from django_strawberry_framework.permissions import apply_cascade_permissions
from django_strawberry_framework.registry import iter_subsystem_clears, registry
from django_strawberry_framework.types.resolvers import (
    _will_lazy_load_many,
    _will_lazy_load_single,
)
from django_strawberry_framework.utils._narrowing import (
    is_set_or_frozenset,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils._queryset_private import (
    queryset_prefetch_lookups,
)
from django_strawberry_framework.utils.querysets import (
    _AsyncQuerySetRows,
    run_in_one_sync_boundary,
    unwrap_async_queryset_adapter,
    wrap_async_queryset_adapter,
)
from tests._definition import make_definition
from tests._idioms import (
    STR_SUBCLASS_KINDS,
    ClaimsClassBase,
    ClassReadRaisesBase,
    definition_raises,
    is_object_dict,
    is_object_list,
    saved_pk,
    str_subclass_name,
)
from tests._info import make_info, response_path

if TYPE_CHECKING:
    from strawberry.types import ExecutionContext

    from django_strawberry_framework.optimizer._context import PlanCacheKey
    from django_strawberry_framework.optimizer.selections import FragmentVisitKey

#: The optimizer's document-key memo shape, for a test that swaps in an empty one.
_DocKeyCache = OrderedDict[tuple[str, str | None, frozenset[str]], tuple[str, frozenset[str]]]

#: The wire names the default ``NameConverter`` publishes the pagination arguments
#: under, the vocabulary the collector rows below spell their documents in.
_DEFAULT_PAGINATION_WIRE_NAMES = frozenset(
    {
        "first",
        "last",
        "before",
        "after",
    },
)


def _as_partial_resolve_info(stand_in: object) -> GraphQLResolveInfo:
    """Hand a partial info to an extension hook that takes a graphql-core resolve info."""
    # basedpyright: an info lacking the slots, or the graphql-core slot types, every real
    # resolve info carries is the input under test: the hook either returns before reading
    # it or takes a defensive arm; the extension hooks type info as GraphQLResolveInfo
    return stand_in  # pyright: ignore[reportReturnType]


def _operation(doc: DocumentNode) -> OperationDefinitionNode:
    """The document's first definition, proven to be its operation."""
    operation = doc.definitions[0]
    assert isinstance(operation, OperationDefinitionNode)
    return operation


def _fragments_by_name(definitions: Iterable[DefinitionNode]) -> dict[str, FragmentDefinitionNode]:
    """``definitions`` proven to be fragment definitions, keyed by fragment name."""
    fragments: dict[str, FragmentDefinitionNode] = {}
    for definition in definitions:
        assert isinstance(definition, FragmentDefinitionNode)
        fragments[definition.name.value] = definition
    return fragments


def _stashed_plan(ctx: object) -> OptimizationPlan:
    """The optimizer plan the extension stashed on the attribute-style context ``ctx``."""
    return require_instance(read_attr(ctx, DST_OPTIMIZER_PLAN), OptimizationPlan)


def _stashed_keys(ctx: object, key: str) -> set[object] | frozenset[object]:
    """The resolver-key set the extension stashed on ``ctx`` under ``key``."""
    return require(read_attr(ctx, key), is_set_or_frozenset)


def _run_coroutine(coroutine: Coroutine[object, object, object]) -> object:
    """Run ``coroutine`` to completion on a fresh event loop and return its result."""
    return asyncio.run(coroutine)


def _at(value: object, *keys: str) -> object:
    """The member of a JSON payload ``value`` at the object-key path ``keys``."""
    for key in keys:
        assert is_object_dict(value), value
        value = value[key]
    return value


def _list_at(value: object, *keys: str) -> list[object]:
    """The JSON list member of ``value`` at the object-key path ``keys``."""
    return require(_at(value, *keys), is_object_list)


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _force_unregister_after_finalize(type_cls: type[DjangoType]) -> None:
    """Test-only helper: drop ``type_cls`` from a *finalized* registry.

    The schema-audit tests in this module build a Strawberry schema, then
    want to simulate a missing registration so ``check_schema`` reports a
    gap. The public ``registry.unregister`` honours ``_check_mutable``
    and raises post-finalize because removing entries from a
    runtime-active registry would silently disable optimizer planning
    and produce false missing-target warnings; this helper exists only
    so the test fixtures can poke that exact state without smuggling
    the surgery into production code.
    """
    model = registry._models.pop(type_cls, None)
    if model is None:
        return
    types = registry._types.get(model, [])
    if type_cls in types:
        types.remove(type_cls)
    if not types:
        registry._types.pop(model, None)
    if registry._primaries.get(model) is type_cls:
        registry._primaries.pop(model, None)
    registry._definitions.pop(type_cls, None)


# ---------------------------------------------------------------------------
# End-to-end query-count tests (O3 unskips the first two)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimize_coerces_manager_through_all_records_cache_miss() -> None:
    """The optimizer's plan cache records a miss when coercing ``Manager`` -> ``.all()``.

    The behavioral half (1 SQL query, JOIN applied, data round-trips) is
    pinned end-to-end by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_coerces_manager_to_queryset_in_http_query``.
    This test keeps the package-internal cache-state assertion that proves
    the plan was actually BUILT (cache miss recorded) rather than the
    Manager being short-circuited by the ``isinstance(QuerySet)`` gate -
    a guarantee unreachable from the live HTTP path because the project
    schema doesn't expose its extension instance for inspection.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> Manager[Item]:
            # Return the Manager itself, not ``Manager.all()``.
            return Item.objects

        all_items: Manager[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    result = schema.execute_sync("{ allItems { name category { name } } }")
    assert result.errors is None
    # The plan was built (miss recorded), proving the Manager was NOT
    # short-circuited by the QuerySet-only gate.
    assert ext.cache_info().misses == 1


@pytest.mark.django_db
def test_optimizer_plans_merged_duplicate_root_field_nodes_plan_shape() -> None:
    """Merged duplicate root fields contribute all child selections to one plan.

    The behavioral half is pinned end-to-end by
    ``examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http``.
    This package test keeps the plan-state assertion that the merged
    selection contributes ``category`` to the stashed optimizer plan.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension(strictness="raise")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name } allItems { category { name } } }",
        context_value=ctx,
    )

    assert result.errors is None
    assert _stashed_plan(ctx).select_related == ("category",)
    assert "ItemType.category@allItems.category" in _stashed_keys(ctx, DST_OPTIMIZER_PLANNED)


@pytest.mark.django_db
def test_optimizer_elides_forward_fk_id_only_selection_plan_shape() -> None:
    """B2 plan-state inspection: ``category { id }`` produces an elision plan.

    The behavioral half (1 SQL query, no JOIN, id round-trips) is pinned by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_for_self_fk_in_http_query``.
    This test keeps the package-internal plan-state assertions that are
    unreachable from a live ``/graphql/`` request: ``plan.select_related``
    must be empty, ``plan.only_fields`` must include the source FK column,
    ``plan.fk_id_elisions`` must record the resolver key, and
    ``ctx.dst_optimizer_fk_id_elisions`` must mirror it (the set the
    forward-FK resolver consults at resolve time).
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("name", "category_id")
    assert plan.fk_id_elisions == ("ItemType.category@allItems.category",)
    assert _stashed_keys(ctx, DST_OPTIMIZER_FK_ID_ELISIONS) == {
        "ItemType.category@allItems.category",
    }


@pytest.mark.django_db
def test_optimizer_elides_forward_fk_id_only_selection_for_each_alias_plan_shape() -> None:
    """B2/O4 plan-state inspection: duplicate aliases each register their own elision key.

    The behavioral half (1 SQL query, no JOIN, both aliases return the same
    FK id) is pinned by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_fk_id_elision_for_each_alias_in_http_query``.
    This test keeps the package-internal plan-state assertions: the plan
    records BOTH alias resolver keys, ``only_fields`` projects exactly the
    source FK column (deduped), and the context-side elision set carries
    both keys for the per-alias forward-FK resolver to consult.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { first: category { id } second: category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("category_id",)
    assert plan.fk_id_elisions == (
        "ItemType.category@allItems.first",
        "ItemType.category@allItems.second",
    )
    assert _stashed_keys(ctx, DST_OPTIMIZER_FK_ID_ELISIONS) == {
        "ItemType.category@allItems.first",
        "ItemType.category@allItems.second",
    }


@pytest.mark.django_db
def test_optimizer_does_not_elide_forward_fk_when_extra_scalar_selected_plan_shape() -> None:
    """B2 plan-state inspection: extra target scalar forces ``select_related`` over elision.

    The behavioral half (1 SQL query via JOIN, extra scalar populates from
    the joined row) is pinned by
    ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_no_fk_id_elision_when_extra_scalar_selected_in_http_query``.
    This test keeps the package-internal plan-state assertions: the
    optimizer plans ``select_related("category",)``, records NO elisions,
    and projects the full ``category__*`` chain in ``only_fields``.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name category { id name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert plan.select_related == ("category",)
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == (
        "name",
        "category_id",
        "category__id",
        "category__name",
    )


@pytest.mark.django_db
def test_optimizer_does_not_elide_forward_fk_when_target_has_custom_get_queryset_plan_shape() -> (
    None
):
    """B2/O6 plan-state inspection: custom ``get_queryset`` forces ``Prefetch`` even on id-only.

    The behavioral half (2 SQL queries, no JOIN on the root, prefetched
    SELECT with the consumer filter applied, inactive rows resolve to
    ``null`` on the source) is pinned by these HTTP tests in
    ``examples/fakeshop/test_query/test_scalars_api.py``:
    ``test_scalars_optimizer_o6_downgrade_to_prefetch_for_custom_get_queryset_in_http_query``
    and ``test_scalars_custom_get_queryset_filters_inactive_tag_to_null_in_http_query``.
    This test keeps the package-internal plan-state assertions: even though
    only ``id`` is selected on the FK target, the optimizer must NOT elide
    (``fk_id_elisions == ()``) and must NOT use ``select_related`` -
    instead it records exactly one ``Prefetch`` entry.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Category]:
            return queryset

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert plan.select_related == ()
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("name", "category_id")
    assert len(plan.prefetch_related) == 1


@pytest.mark.django_db
def test_optimizer_passes_through_unregistered_return_type(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If the return type isn't in the registry, the queryset is unchanged."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # Drop the registry mid-test - schema is already built, but the optimizer
    # looks up the registry per resolver call, so the lookup misses.
    registry.clear()

    caplog.set_level("DEBUG", logger=optimizer_logger.name)
    result = schema.execute_sync("{ allCategories { name } }")
    assert result.errors is None
    # The optimizer logs a debug line when it falls through.
    assert any("no registered DjangoType" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# G1 (spec-035): evaluated-queryset guard internals
#
# Wire SQL (one query, no re-execution) is
# ``examples/fakeshop/test_query/test_library_api.py::test_library_evaluated_queryset_not_re_executed_over_http``.  # noqa: E501 - citation path cannot wrap
# Manager coercion SQL is
# ``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_coerces_manager_to_queryset_in_http_query``.  # noqa: E501 - citation path cannot wrap
# What remains here is cache-miss / instance-identity / async routing, none of
# which a response can show.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_evaluated_root_queryset_does_not_record_a_plan_cache_miss() -> None:
    """The G1 guard short-circuits before ``_get_or_build_plan``, so misses stay 0.

    Live HTTP one-query SQL is ``allLibraryBranchesEagerEval``. This row keeps
    the cache-state half AND the consumer-``select_related`` relation that the
    shipped eager-eval field cannot host: ``category { name }`` is served from
    the JOIN the resolver already applied, in one query, with no plan miss.
    """
    services.seed_data(2)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            qs = Item.objects.select_related("category").all()
            len(qs)
            return qs

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    with CaptureQueriesContext(connection) as captured:
        result = schema.execute_sync("{ allItems { name category { name } } }")
    assert result.errors is None
    assert ext.cache_info().misses == 0
    item_sql = [q["sql"] for q in captured.captured_queries if "products_item" in q["sql"]]
    assert len(item_sql) == 1, captured.captured_queries
    assert "JOIN" in item_sql[0].upper()


@pytest.mark.django_db
def test_optimize_returns_same_instance_for_evaluated_queryset() -> None:
    """``_optimize`` returns the SAME evaluated queryset object, never a clone.

    Instance identity has no wire shape. ``_optimize`` never touches ``info``
    for an evaluated queryset, so a bare namespace suffices.
    """
    services.seed_data(1)
    ext = DjangoOptimizerExtension()

    qs = Category.objects.all()
    len(qs)

    assert ext._optimize(qs, _as_partial_resolve_info(SimpleNamespace())) is qs
    assert ext.cache_info().misses == 0


@pytest.mark.django_db
def test_apply_to_returns_a_combined_queryset_unplanned(caplog: pytest.LogCaptureFixture) -> None:
    """A combined queryset is returned as-is before any plan is built.

    Django refuses ``only`` / ``select_related`` on a ``union`` result, so
    ``apply_to`` skips planning it. ``field_nodes`` is non-empty so the skip is
    the combinator check, not the empty-selection early return.
    """
    services.seed_data(1)
    ext = DjangoOptimizerExtension()
    qs = Category.objects.filter(pk__lt=0).union(Category.objects.all())
    info = make_info(field_name="allCategories")._raw_info
    caplog.set_level("DEBUG", logger=optimizer_logger.name)

    assert ext.apply_to(None, Category, qs, info) is qs
    assert ext.cache_info().misses == 0
    assert any("combined (union) queryset" in r.message for r in caplog.records)


def _seal_items(seed: QuerySet[Model] | None, _info: object) -> QuerySet[Model]:
    """An item hook admitting every row of the seed (the default manager without one)."""
    return seed if seed is not None else Item.objects.all()


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        pytest.param("cold", True, id="cold-builds"),
        pytest.param("cold-in-execution", True, id="memo-miss-builds"),
        pytest.param("cached", False, id="cache-hit-reuses"),
        pytest.param("memoized", False, id="memo-hit-reuses"),
        pytest.param("memoized-sealed", True, id="memo-hit-seals-the-consumer-prefetch"),
        pytest.param("memoized-sealed-elsewhere", False, id="memo-hit-seals-nothing"),
        pytest.param("combined", False, id="combined-plans-nothing"),
        pytest.param("no-field-nodes", False, id="no-field-nodes-plans-nothing"),
    ],
)
def test_builds_plan_is_true_only_when_apply_to_would_run_the_walker(
    state: str,
    expected: bool,  # noqa: FBT001
) -> None:
    """The async plan hop's gate answers exactly ``apply_to``'s walker-run question.

    A plan built off the event loop costs one worker hop, so the gate mirrors
    ``apply_to``'s two pass-throughs (no root field nodes, a combined queryset)
    and ``_get_or_build_plan``'s two lookups (the cross-request cache, the
    execution memo): only the remaining case runs the walker, and so consumer
    hooks. A reused plan that seals a path the queryset's own ``Prefetch`` takes
    over runs the target type's hook in the reconciliation, so it hops too; a
    consumer ``Prefetch`` on any other path does not.
    """
    ext = DjangoOptimizerExtension()
    info = make_info(field_name="allCategories")._raw_info
    queryset: QuerySet[Category] = Category.objects.all()
    key = DjangoOptimizerExtension._build_cache_key(info, Category, None)
    if state == "cached":
        ext._plan_cache[key] = OptimizationPlan()
    elif state == "combined":
        queryset = Category.objects.filter(pk__lt=0).union(Category.objects.all())
    elif state == "no-field-nodes":
        info = info._replace(field_nodes=[])
    elif state == "memoized-sealed":
        queryset = Category.objects.prefetch_related(
            Prefetch("items", queryset=Item.objects.all()),
        )
    elif state == "memoized-sealed-elsewhere":
        queryset = Category.objects.prefetch_related(
            Prefetch("properties", queryset=Property.objects.all()),
        )
    frame = (
        begin_execution_frame({}, nested=False)
        if state.startswith("memoized") or state == "cold-in-execution"
        else None
    )
    try:
        memo = execution_plan_memo()
        if memo is not None and state == "memoized":
            memo[key] = OptimizationPlan()
        elif memo is not None and state.startswith("memoized-sealed"):
            memo[key] = OptimizationPlan(
                prefetch_path_seals={
                    "items": PrefetchSeal(own_keys=(), model=Item, seal=_seal_items),
                },
            ).finalize()
        assert ext._builds_plan(info, Category, None, queryset) is expected
    finally:
        if frame is not None:
            end_execution_frame(frame)


@pytest.mark.django_db
def test_resolve_async_passes_through_evaluated_queryset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Async mirror: the await -> ``_optimize`` wrapper inherits the G1 guard.

    The async path (``_async_optimize`` awaits the resolver then calls
    ``_optimize_async``, which hands an evaluated queryset straight to
    ``_optimize``) routes it through the same guard. The
    tripwire on ``_resolve_model_from_return_type`` proves ``_optimize``
    short-circuits BEFORE return-type resolution / plan build - if the guard
    failed to fire, the tripwire would raise.
    """
    services.seed_data(1)
    ext = DjangoOptimizerExtension()

    qs = Category.objects.all()
    len(qs)  # evaluate synchronously, before the await -> no DB access in the coroutine

    def _tripwire(_info: object) -> NoReturn:
        raise AssertionError("guard must short-circuit before return-type resolution")

    monkeypatch.setattr(extension_module, "_resolve_model_from_return_type", _tripwire)

    async def fake_next(
        _root: object,
        _info: object,
        *_args: object,
        **_kwargs: object,
    ) -> QuerySet[Category]:
        return qs

    info = make_info(field_name="allCategories")._raw_info
    result = ext.resolve(fake_next, None, info)
    assert asyncio.iscoroutine(result)
    resolved = _run_coroutine(result)
    assert resolved is qs  # same instance, no clone
    assert ext.cache_info().misses == 0  # guard fired before plan build


@pytest.mark.django_db(transaction=True)
async def test_resolve_hops_a_sync_root_under_the_async_executor_only_to_build_a_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Under the asynchronous executor a plain ``def`` root's plan is built off the loop.

    The plan hop follows the executor, not the resolver's color: the first async
    request builds the plan in one sync boundary, the second reuses the cached plan
    on the loop with no hop, and the synchronous executor never hops. Every request
    answers the same rows, which list completion fetches.
    """
    await sync_to_async(services.seed_data)(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.order_by("id")

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(query=Query, extensions=[lambda: optimizer])
    hopped: list[object] = []

    async def _counting_boundary(
        fn: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> object:
        hopped.append(fn)
        return await run_in_one_sync_boundary(fn, *args, **kwargs)

    monkeypatch.setattr(extension_module, "run_in_one_sync_boundary", _counting_boundary)
    names = [{"name": category.name} async for category in Category.objects.order_by("id")]
    document = "{ allCategories { name } }"

    first = await schema.execute(document)
    assert first.errors is None, first.errors
    assert first.data == {"allCategories": names}
    assert hopped == [optimizer._optimize]
    second = await schema.execute(document)
    assert second.errors is None, second.errors
    assert second.data == {"allCategories": names}
    assert len(hopped) == 1
    synchronous = await sync_to_async(schema.execute_sync)(document)
    assert synchronous.errors is None, synchronous.errors
    assert synchronous.data == {"allCategories": names}
    assert len(hopped) == 1


# ---------------------------------------------------------------------------
# O3: type-tracing through graphql-core wrappers
# ---------------------------------------------------------------------------


def test_resolve_model_from_return_type_unwraps_nested_wrappers() -> None:
    """Recursive unwrap through NonNull(List(NonNull(ObjectType))) -> (origin, Django model)."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    # Build a minimal schema so get_type_by_name works.
    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    # Simulate the graphql-core wrapper stack the resolve hook sees.
    inner = schema._schema.type_map["CategoryType"]
    assert isinstance(inner, GraphQLObjectType)
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))

    info = make_info()._raw_info._replace(return_type=wrapped, schema=schema._schema)
    result = _resolve_model_from_return_type(info)
    assert result is not None
    assert result.model is Category
    assert result.origin is CategoryType


def test_resolve_model_returns_none_for_non_object_leaf() -> None:
    """When the leaf type has no name, returns None.

    Every graphql-core named type carries a name, so a nameless leaf is a defensive arm.
    """
    info = SimpleNamespace(
        return_type=SimpleNamespace(),  # no of_type, no name
        schema=None,
    )
    assert _resolve_model_from_return_type(_as_partial_resolve_info(info)) is None


def _object_type_outside_schema(name: str) -> GraphQLObjectType:
    """A graphql-core object type ``name`` with one string field, in no Strawberry schema."""
    # graphql-core's named-type constructor is typed to return any named type.
    value_type = GraphQLString
    assert isinstance(value_type, GraphQLScalarType)
    object_type = GraphQLObjectType(name, {"value": GraphQLField(value_type)})
    assert isinstance(object_type, GraphQLObjectType)
    return object_type


def test_resolve_model_returns_none_when_no_strawberry_schema() -> None:
    """When schema._strawberry_schema is missing, returns None.

    A graphql-core schema Strawberry did not build files no ``_strawberry_schema``.
    """
    some_type = _object_type_outside_schema("SomeType")
    info = make_info()._raw_info._replace(
        return_type=some_type,
        schema=GraphQLSchema(types=[some_type]),
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_type_not_in_schema() -> None:
    """When get_type_by_name returns None (type not in schema), returns None."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    info = make_info()._raw_info._replace(
        return_type=_object_type_outside_schema("NonExistentType"),
        schema=schema._schema,
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_definition_has_no_origin() -> None:
    """When the schema's type definition lacks an ``origin`` (e.g. a scalar / interface), returns None."""

    def _definition_without_origin(_name: str) -> SimpleNamespace:
        return SimpleNamespace()

    fake_strawberry_schema = SimpleNamespace(get_type_by_name=_definition_without_origin)
    info = SimpleNamespace(
        return_type=SimpleNamespace(name="SomeType"),
        schema=SimpleNamespace(_strawberry_schema=fake_strawberry_schema),
    )
    assert _resolve_model_from_return_type(_as_partial_resolve_info(info)) is None


# ---------------------------------------------------------------------------
# O3: root-field gate
# ---------------------------------------------------------------------------


def test_resolve_passes_through_non_root_resolvers() -> None:
    """Non-root resolvers (info.path.prev is not None) bypass _optimize entirely."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    # Simulate a non-root resolver: path.prev is not None.
    qs = Category.objects.all()
    called_with = {}

    def fake_next(
        _root: object,
        _info: object,
        *_args: object,
        **_kwargs: object,
    ) -> QuerySet[Category]:
        called_with["fired"] = True
        return qs

    info = make_info(path=response_path("parent", "allCategories"))._raw_info
    result = ext.resolve(fake_next, None, info)
    # _next was called and result passed through unchanged (no _optimize).
    assert called_with["fired"] is True
    assert result is qs


# ---------------------------------------------------------------------------
# O3: async resolver parity
# ---------------------------------------------------------------------------


def test_resolve_handles_async_root_resolver() -> None:
    """An async root resolver's coroutine is awaited before optimization."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    qs = Category.objects.all()

    async def fake_next(
        _root: object,
        _info: object,
        *_args: object,
        **_kwargs: object,
    ) -> QuerySet[Category]:
        return qs

    # Root resolver: path.prev is None. Its String return type maps to no registered model.
    info = make_info(field_name="allCategories")._raw_info
    result = ext.resolve(fake_next, None, info)
    # result should be a coroutine (async wrapper)
    assert asyncio.iscoroutine(result)
    # Await it - _optimize will pass through because no model backs the return type.
    resolved = _run_coroutine(result)
    assert resolved is qs


# ---------------------------------------------------------------------------
# O3: defensive branches in _optimize
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.usefixtures("django_assert_num_queries")
def test_optimize_handles_empty_field_nodes() -> None:
    """If field_nodes is empty, _optimize returns the queryset unchanged."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # Drive _optimize directly with a real info whose field_nodes is empty.
    ext = DjangoOptimizerExtension()

    info = make_info(field_name="allCategories")._raw_info._replace(
        return_type=schema._schema.type_map["CategoryType"],
        schema=schema._schema,
        field_nodes=[],
    )
    qs = Category.objects.all()
    result = ext._optimize(qs, info)
    # Should return the queryset unchanged (no field_nodes to plan from).
    assert isinstance(result, QuerySet)
    assert result.query.select_related is False


@pytest.mark.django_db
def test_optimize_returns_original_queryset_for_empty_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the walker produces an empty plan, _optimize returns the original queryset."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    def _empty_plan(*_args: object, **_kwargs: object) -> OptimizationPlan:
        return OptimizationPlan()

    monkeypatch.setattr(extension_module, "plan_optimizations", _empty_plan)
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    assert _stashed_plan(ctx).is_empty


# ---------------------------------------------------------------------------
# O3: on_execute execution-frame lifecycle
# ---------------------------------------------------------------------------


def test_on_execute_sets_and_resets_context_var() -> None:
    """on_execute publishes the running instance for the operation, then closes."""
    ext = DjangoOptimizerExtension()
    assert _active_optimizer() is None
    gen = ext.on_execute()
    next(gen)  # enter
    assert _active_optimizer() is ext
    with contextlib.suppress(StopIteration):
        next(gen)
    assert _active_optimizer() is None


# ---------------------------------------------------------------------------
# B1: plan cache
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.usefixtures("django_assert_num_queries")
def test_cache_differentiates_queries() -> None:
    """B1: different queries produce different cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allItems { name category { name } } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_cache_differentiates_reachable_named_fragment_bodies() -> None:
    """B1: matching operation text with different fragment bodies gets distinct plans."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query_prefix = "query Q { allItems { ...ItemBits } }"
    ctx_scalar = SimpleNamespace()
    ctx_relation = SimpleNamespace()

    result_scalar = schema.execute_sync(
        f"{query_prefix} fragment ItemBits on ItemType {{ name }}",
        context_value=ctx_scalar,
    )
    result_relation = schema.execute_sync(
        f"{query_prefix} fragment ItemBits on ItemType {{ category {{ name }} }}",
        context_value=ctx_relation,
    )

    assert result_scalar.errors is None
    assert result_relation.errors is None
    assert _stashed_plan(ctx_scalar).select_related == ()
    assert _stashed_plan(ctx_relation).select_related == ("category",)
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_cache_differentiates_same_model_root_fields(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
) -> None:
    """B1/O4: root fields returning the same model do not share one cached plan."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

        def _featured_categories(self) -> QuerySet[Category]:
            return Category.objects.filter(is_private=False)

        featured_categories: QuerySet[Category] = strawberry.field(
            resolver=_featured_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    query = "{ allCategories { name items { name } } featuredCategories { name } }"

    with django_assert_num_queries(3):
        result = schema.execute_sync(query, context_value=ctx)

    assert result.errors is None
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2
    assert _stashed_plan(ctx).prefetch_related == ()


def test_cache_key_includes_root_runtime_path_for_same_model_fields() -> None:
    """B1/O4: cache keys differ for root fields returning the same model."""
    # One operation, two response paths: the path alone separates the keys.
    info_a = make_info(
        field_name="allCategories",
        selections="{ name }",
        path=response_path("allCategories"),
    )._raw_info
    info_b = make_info(
        field_name="allCategories",
        selections="{ name }",
        path=response_path("featured"),
    )._raw_info

    assert DjangoOptimizerExtension._build_cache_key(
        info_a,
        Category,
    ) != DjangoOptimizerExtension._build_cache_key(info_b, Category)


def test_cache_key_differs_for_named_operations_in_same_document() -> None:
    """B1: two named operations in one document must not share a plan cache entry."""
    document = "query A { allItems { name } } query B { allItems { category { name } } }"
    info_a = make_info(document=document, operation_name="A")._raw_info
    info_b = make_info(document=document, operation_name="B")._raw_info

    assert DjangoOptimizerExtension._build_cache_key(
        info_a,
        Item,
    ) != DjangoOptimizerExtension._build_cache_key(info_b, Item)


def test_query_and_mutation_plans_coexist_distinct_keys() -> None:
    """A query and a byte-identical-selection mutation get distinct plan-cache keys.

    The plan-cache key's first component is the printed operation AST, and
    ``print_ast(operation)`` includes the ``query`` / ``mutation`` keyword - so the
    query plan (``introduce_projection`` on) and the mutation plan (off) can never
    collide on one cache entry even with identical selection bodies, which is what
    lets the flag be cached with the plan. Pins the key inequality directly, not a
    cache stat.
    """
    selection = "{ category { name } }"
    info_query = make_info(field_name="allItems", selections=selection)._raw_info
    info_mutation = make_info(
        field_name="allItems",
        selections=selection,
        operation=OperationType.MUTATION,
    )._raw_info

    assert DjangoOptimizerExtension._build_cache_key(
        info_query,
        Item,
    ) != DjangoOptimizerExtension._build_cache_key(info_mutation, Item)


@pytest.mark.django_db
def test_mutation_real_execution_records_columns_and_introduces_no_projection() -> None:
    """A REAL ``mutation`` execution plans the query's shape with ``introduce_projection`` off.

    The walker-level tests drive the flag with synthetic ``OperationType.MUTATION``
    info doubles; this proves the integration seam end-to-end - a Strawberry
    ``mutation`` root field returning a queryset, with the installed
    ``DjangoOptimizerExtension`` receiving the REAL ``info.operation.operation``
    object from the graphql-core runtime (not a test double). The mutation's
    published plan records the same ``only_fields`` and ``select_related`` as the
    byte-identical ``query``; only the query's plan may introduce a projection.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    @strawberry.type
    class Mutation:
        def _touch_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        touch_items = strawberry.mutation(_touch_items, graphql_type=list[ItemType])

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[lambda: ext])

    mutation_ctx = SimpleNamespace()
    mutation_result = schema.execute_sync(
        "mutation { touchItems { name category { name } } }",
        context_value=mutation_ctx,
    )
    assert mutation_result.errors is None
    mutation_plan = _stashed_plan(mutation_ctx)
    assert mutation_plan.only_fields == ("name", "category_id", "category__name")
    assert mutation_plan.select_related == ("category",)
    assert mutation_plan.introduce_projection is False

    query_ctx = SimpleNamespace()
    query_result = schema.execute_sync(
        "query { allItems { name category { name } } }",
        context_value=query_ctx,
    )
    assert query_result.errors is None
    query_plan = _stashed_plan(query_ctx)
    assert query_plan.select_related == ("category",)
    assert query_plan.only_fields == ("name", "category_id", "category__name")
    assert query_plan.introduce_projection is True


def test_cache_eviction_removes_old_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    """B1: the plan cache evicts least-recently-used entries when full."""
    ext = DjangoOptimizerExtension()
    monkeypatch.setattr(extension_module, "_MAX_PLAN_CACHE_SIZE", 4)

    def _cache_info_for(root_field: str) -> GraphQLResolveInfo:
        document = f"query {root_field} {{ {root_field} {{ name }} }}"
        return make_info(document=document)._raw_info

    infos = [_cache_info_for(f"root{idx}") for idx in range(4)]
    keys = [DjangoOptimizerExtension._build_cache_key(info, Category, None) for info in infos]
    plans = [OptimizationPlan() for _ in range(4)]
    ext._plan_cache = OrderedDict(zip(keys, plans, strict=True))

    assert ext._get_or_build_plan([], Category, infos[0], None) is plans[0]

    root4_info = _cache_info_for("root4")
    root4_key = DjangoOptimizerExtension._build_cache_key(
        root4_info,
        Category,
        None,
    )
    ext._get_or_build_plan([], Category, root4_info, None)

    assert keys[0] in ext._plan_cache
    assert keys[1] not in ext._plan_cache
    assert root4_key in ext._plan_cache
    assert ext.cache_info().misses == 1
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 4


def test_doc_key_cache_evicts_when_full(monkeypatch: pytest.MonkeyPatch) -> None:
    """B1: the cross-request document-key cache is a bounded LRU.

    ``_doc_cache_entry`` memoizes the printed operation-plus-fragments key AND
    the cache-relevant variable-name set across requests (keyed on the raw
    source text), so a hot query neither prints nor re-walks its AST after
    first sight. The cache is bounded so a long-lived process seeing many
    distinct documents cannot grow it without limit: inserting past a shrunk
    max evicts the least-recently-used entry while the newest survive.
    """
    monkeypatch.setattr(extension_module, "_MAX_DOC_KEY_CACHE_SIZE", 2)
    monkeypatch.setattr(extension_module, "_doc_key_cache", _DocKeyCache())

    ops = [_operation(parse(f"query Q{i} {{ field{i} }}")) for i in range(3)]
    for op in ops:
        extension_module._doc_cache_entry(op, {}, _DEFAULT_PAGINATION_WIRE_NAMES)

    # Three distinct documents into a size-2 cache: the first (LRU) is evicted,
    # the two most-recent survive.
    assert len(extension_module._doc_key_cache) == 2
    cached_bodies = {body for (body, _name, _wire_names) in extension_module._doc_key_cache}
    assert ops[0].loc is not None
    assert ops[0].loc.source.body not in cached_bodies
    assert ops[1].loc is not None
    assert ops[1].loc.source.body in cached_bodies
    assert ops[2].loc is not None
    assert ops[2].loc.source.body in cached_bodies


@pytest.mark.django_db
def test_cache_clear_makes_the_next_request_build_its_plan_again() -> None:
    """``cache_clear`` empties the plan cache and zeroes both counters.

    A warm hit before the clear, zeroed ``cache_info`` after it, and a miss
    with a rebuilt entry on the next identical request. Package tier: the
    project schema does not expose its extension instance.
    """
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allItems { name } }"
    assert schema.execute_sync(query).errors is None
    assert schema.execute_sync(query).errors is None
    assert ext.cache_info() == (1, 1, 1)

    ext.cache_clear()

    assert ext.cache_info() == (0, 0, 0)
    assert schema.execute_sync(query).errors is None
    assert ext.cache_info() == (0, 1, 1)


def test_registry_clear_empties_the_document_key_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """The document-key memo is registered with ``registry.clear()`` and empties on it."""
    monkeypatch.setattr(extension_module, "_doc_key_cache", _DocKeyCache())
    extension_module._doc_cache_entry(
        _operation(parse("query Q { field }")),
        {},
        _DEFAULT_PAGINATION_WIRE_NAMES,
    )
    assert len(extension_module._doc_key_cache) == 1

    assert clear_document_key_cache in iter_subsystem_clears()
    clear_document_key_cache()

    assert len(extension_module._doc_key_cache) == 0


def test_stash_union_skips_restash_when_subset() -> None:
    """A re-publish whose sentinel set is already contained leaves the stash alone.

    A nested fallback connection re-publishes the SAME plan once per parent row;
    after the first row every ``_stash_union`` call carries a subset of what is
    already stashed. The subset early-out skips the union (no per-row frozenset
    reallocation) - observable as the stashed OBJECT staying identical - while a
    genuinely new element still unions in.
    """
    context = SimpleNamespace()
    DjangoOptimizerExtension._stash_union(context, "sentinels", frozenset({"a", "b"}))
    first = read_attr(context, "sentinels")

    DjangoOptimizerExtension._stash_union(context, "sentinels", frozenset({"a"}))
    assert read_attr(context, "sentinels") is first  # subset: no re-stash, same object

    DjangoOptimizerExtension._stash_union(context, "sentinels", frozenset({"c"}))
    assert read_attr(context, "sentinels") == frozenset({"a", "b", "c"})


def test_get_or_build_plan_reuses_uncacheable_plan_within_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B1: the per-execution memo reuses an uncacheable plan built earlier this execution.

    A nested fallback connection pipeline calls ``_get_or_build_plan`` once per
    parent row with an IDENTICAL cache key, and those plans are ``cacheable =
    False`` so the cross-request cache never serves them. Within one
    ``on_execute`` lifecycle the per-execution memo returns the plan built for the
    first parent instead of re-running the walker for every subsequent parent -
    collapsing N per-parent walks to one. The intra-execution reuse is NOT counted
    as a cross-request cache hit (``cache_info`` reports the instance cache only).
    """
    builds = {"count": 0}

    def _fake_plan_optimizations(*_args: object, **_kwargs: object) -> OptimizationPlan:
        builds["count"] += 1
        return OptimizationPlan(prefetch_related=["items"], cacheable=False).finalize()

    monkeypatch.setattr(extension_module, "plan_optimizations", _fake_plan_optimizations)

    info = make_info(field_name="allItems", selections="{ name }")._raw_info

    ext = DjangoOptimizerExtension()
    gen = ext.on_execute()
    next(gen)  # enter the lifecycle: installs the per-execution plan memo
    try:
        first = ext._get_or_build_plan([], Item, info, None)
        second = ext._get_or_build_plan([], Item, info, None)
    finally:
        with contextlib.suppress(StopIteration):
            next(gen)  # exit: resets the memo

    # Built once, reused for the second call within the same execution.
    assert builds["count"] == 1
    assert second is first
    # The uncacheable plan never entered the cross-request cache, and the
    # intra-execution reuse did not inflate the hit counter.
    assert ext.cache_info().size == 0
    assert ext.cache_info().misses == 1
    assert ext.cache_info().hits == 0


@pytest.mark.django_db
def test_filter_vars_do_not_affect_cache() -> None:
    """B1: variables not used in @skip/@include don't split cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self, limit: int = 10) -> QuerySet[Item]:
            return Item.objects.all()[:limit]

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "query Q($limit: Int!) { allItems(limit: $limit) { name category { name } } }"

    schema.execute_sync(query, variable_values={"limit": 5})
    schema.execute_sync(query, variable_values={"limit": 10})
    # Same query shape, different filter var - should be 1 miss + 1 hit.
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1


@pytest.mark.django_db
def test_cache_separates_operation_names_in_same_document() -> None:
    """B1: executing two named operations in one document yields two cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    document = "query A { allItems { name } } query B { allItems { name category { name } } }"

    result_a = schema.execute_sync(document, operation_name="A")
    result_b = schema.execute_sync(document, operation_name="B")

    assert result_a.errors is None
    assert result_b.errors is None
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


def test_build_cache_key_is_stable_when_source_location_missing() -> None:
    """B1: cache key still works when the operation has no source body."""
    document = "{ allCategories { name } }"
    operation = _operation(parse(document, no_location=True))
    info = make_info(document=document)._raw_info._replace(operation=operation)

    key = DjangoOptimizerExtension._build_cache_key(info, Category)

    assert key[2] is Category
    assert isinstance(key[3], tuple)


def test_directive_var_family_with_skip() -> None:
    """B1: the directive family finds vars in @skip directives."""
    doc = parse("query Q($show: Boolean!) { items @skip(if: $show) { name } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset({"show"})


def test_directive_var_family_with_include() -> None:
    """B1: the directive family finds vars in @include directives."""
    doc = parse("query Q($v: Boolean!) { items @include(if: $v) { name } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset({"v"})


def test_directive_var_family_ignores_non_directive_vars() -> None:
    """B1: variables in field arguments (not directives) are not collected."""
    doc = parse("query Q($limit: Int!) { items(limit: $limit) { name } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset()


def test_walk_cache_relevant_vars_ignores_non_directive_objects() -> None:
    """B1: directive collection skips defensive non-DirectiveNode entries."""
    operation = parse("query Q($v: Boolean!) { items @skip(if: $v) { name } }").definitions[0]
    assert isinstance(operation, OperationDefinitionNode)
    field = operation.selection_set.selections[0]

    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    node = SimpleNamespace(directives=[object(), *field.directives], selection_set=None)
    _walk_cache_relevant_vars(
        # basedpyright: a stand-in node carrying only the slots the code under test reads;
        # _walk_cache_relevant_vars types the parameter as Node
        node,  # pyright: ignore[reportArgumentType]
        {},
        set(),
        0,
        directive_names,
        pagination_names,
        _DEFAULT_PAGINATION_WIRE_NAMES,
    )
    assert directive_names == {"v"}


def test_walk_cache_relevant_vars_visits_each_fragment_once_across_sibling_spreads() -> None:
    """Sibling spreads of the same fragment do not re-walk the fragment subtree."""
    doc = parse(
        "query Q($v: Boolean!) { "
        "a: items { ...F } "
        "b: items { ...F } "
        "} "
        "fragment F on Item { name @skip(if: $v) }",
    )
    operation = doc.definitions[0]
    fragments = _fragments_by_name(doc.definitions[1:])
    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    visited: set[FragmentVisitKey] = set()
    _walk_cache_relevant_vars(
        operation,
        fragments,
        visited,
        0,
        directive_names,
        pagination_names,
        _DEFAULT_PAGINATION_WIRE_NAMES,
    )
    assert directive_names == {"v"}
    # Fragment F was descended exactly once even though it was spread twice: both
    # spread sites sit at the same response-path depth (inside an ``items`` field),
    # so the depth-aware ``(name, depth)`` guard dedupes them to a single entry.
    assert visited == {("F", 1)}


def test_walk_cache_relevant_vars_handles_unresolved_fragment_name() -> None:
    """A spread referencing an unknown fragment name is skipped silently."""
    doc = parse("query Q { items { ...Missing } }")
    operation = doc.definitions[0]
    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    visited: set[FragmentVisitKey] = set()
    _walk_cache_relevant_vars(
        operation,
        {},
        visited,
        0,
        directive_names,
        pagination_names,
        _DEFAULT_PAGINATION_WIRE_NAMES,
    )
    assert directive_names == set()
    assert visited == set()


def test_directive_var_family_ignores_other_directives() -> None:
    """B1: only @skip and @include directives split the plan cache."""
    doc = parse("query Q($v: Boolean!) { items @custom(if: $v) { name } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset()


def test_directive_var_family_nested_fragments() -> None:
    """B1: vars in directives on nested fields are collected."""
    doc = parse(
        "query Q($a: Boolean!, $b: Boolean!) { "
        "items { name @skip(if: $a) entries @include(if: $b) { value } } }",
    )
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset({"a", "b"})


def test_directive_var_family_no_directives() -> None:
    """B1: a query with no directives yields an empty directive family."""
    doc = parse("{ items { name } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset()


# ---------------------------------------------------------------------------
# B1: plan-cache key hygiene for nested pagination variables (spec-033
# Decision 7). Nested ``first``/``last``/``before``/``after`` variables are
# baked into windowed prefetch plans, so their values must key the
# cache; root pagination variables stay out (root slicing is post-plan).
# ---------------------------------------------------------------------------


def _key_for(
    document: str,
    *,
    variable_values: dict[str, object],
    path_key: str,
    model: type[Model] = Category,
) -> "PlanCacheKey":
    """Build a ``_build_cache_key`` tuple for ``document``'s operation at root ``path_key``.

    The calls under test differ only in ``variable_values``, so any key inequality is
    attributable to the variable-collection rule.
    """
    info = make_info(
        document=document,
        variables=variable_values,
        path=response_path(path_key),
    )._raw_info
    return DjangoOptimizerExtension._build_cache_key(info, model)


def test_nested_pagination_variable_keys_cache() -> None:
    """A nested ``first: $n`` value keys the plan cache: two values -> two keys."""
    operation = (
        "query Q($n: Int!) { parents { booksConnection(first: $n) { edges { node { title } } } } }"
    )

    key_two = _key_for(operation, variable_values={"n": 2}, path_key="parents")
    key_five = _key_for(operation, variable_values={"n": 5}, path_key="parents")
    assert key_two != key_five


def test_root_pagination_variable_shares_cache() -> None:
    """A root ``first: $n`` value does NOT key the cache (root slicing post-plan)."""
    operation = "query Q($n: Int!) { someRootConnection(first: $n) { edges { node { name } } } }"

    key_two = _key_for(operation, variable_values={"n": 2}, path_key="someRootConnection")
    key_five = _key_for(operation, variable_values={"n": 5}, path_key="someRootConnection")
    assert key_two == key_five


def test_mixed_root_and_nested_pagination_variables() -> None:
    """Only the nested pagination variable keys: vary root -> share, vary nested -> split."""
    operation = (
        "query Q($r: Int!, $n: Int!) { parents(first: $r) "
        "{ booksConnection(first: $n) { edges { node { title } } } } }"
    )

    base = _key_for(operation, variable_values={"r": 1, "n": 2}, path_key="parents")
    vary_root = _key_for(operation, variable_values={"r": 9, "n": 2}, path_key="parents")
    vary_nested = _key_for(operation, variable_values={"r": 1, "n": 5}, path_key="parents")

    assert base == vary_root  # root pagination variable is invariant in the plan
    assert base != vary_nested  # nested pagination variable keys the cache


def test_root_fragment_pagination_variable_shares_cache() -> None:
    """A root connection through a ``Query`` fragment is still root: ``$n`` stays out.

    spec-033 Decision 7: depth is preserved at the spread SITE. The fragment spreads at
    response-path depth 0, so its connection field is root and its pagination
    variable does not key the cache.
    """
    document = (
        "query Q($n: Int!) { ...RootFrag } "
        "fragment RootFrag on Query { someRootConnection(first: $n) "
        "{ edges { node { name } } } }"
    )
    info_two = make_info(document=document, variables={"n": 2})._raw_info
    info_five = make_info(document=document, variables={"n": 5})._raw_info
    assert DjangoOptimizerExtension._build_cache_key(
        info_two,
        Category,
    ) == DjangoOptimizerExtension._build_cache_key(info_five, Category)


def test_fragment_carried_nested_pagination_variable_collected() -> None:
    """A nested connection through a parent-node fragment is still nested: ``$n`` keys.

    The fragment spreads inside ``node`` (response-path depth >= 1), so its
    ``booksConnection`` field is nested and its pagination variable keys the
    cache - the positive spread-site-depth pin (spec-033 Decision 7).
    """
    document = (
        "query Q($n: Int!) { parents { edges { node { ...BooksFrag } } } } "
        "fragment BooksFrag on ParentNode { booksConnection(first: $n) "
        "{ edges { node { title } } } }"
    )
    info_two = make_info(document=document, variables={"n": 2})._raw_info
    info_five = make_info(document=document, variables={"n": 5})._raw_info
    assert DjangoOptimizerExtension._build_cache_key(
        info_two,
        Category,
    ) != DjangoOptimizerExtension._build_cache_key(info_five, Category)


def test_fragment_spread_at_two_depths_collects_nested_pagination_variable() -> None:
    """A fragment spread at BOTH root and nested depth still keys on its nested ``$n``.

    Regression pin for the depth-aware fragment cycle guard. The same fragment is
    spread once at root depth (pagination excluded) and once inside ``node``
    (response-path depth >= 1, pagination collected). A name-only visited guard let
    the first-visited (root) spread suppress the nested spread, dropping ``$n`` from
    the cache key so two requests differing only in ``$n`` shared one cached plan --
    serving the wrong windowed prefetch (Decision 7: "under-collection would serve
    wrong data"). Both spread orders must collect ``$n``.
    """
    frag = "fragment F on Thing { booksConnection(first: $n) { edges { node { title } } } }"
    root_first = parse(
        "query Q($n: Int!) { ...F parents { edges { node { ...F } } } } " + frag,
    )
    nested_first = parse(
        "query Q($n: Int!) { parents { edges { node { ...F } } } ...F } " + frag,
    )
    for doc in (root_first, nested_first):
        operation = doc.definitions[0]
        fragments = _fragments_by_name(doc.definitions[1:])
        names = _collect_cache_var_families(operation, fragments, _DEFAULT_PAGINATION_WIRE_NAMES)[
            1
        ]
        assert names == frozenset({"n"})


def test_pagination_var_collection_is_syntactic_superset() -> None:
    """A non-connection nested field with ``first: $n`` is still collected (over-collection).

    spec-033 Decision 7: the collection is a syntactic superset by design - any non-root
    field's pagination-named variable keys the cache, even on a plain resolver
    that is not a synthesized connection. Over-collection costs cheap duplicate
    cache entries; under-collection would serve wrong data.
    """
    doc = parse("{ parents { someField(first: $n) { value } } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[1]
    assert names == frozenset({"n"})


def test_nested_pagination_var_family_excludes_root_field() -> None:
    """Root-field pagination variables are excluded from the collected name set."""
    doc = parse("query Q($n: Int!) { rootConn(first: $n) { edges { node { name } } } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[1]
    assert names == frozenset()


def test_nested_pagination_var_family_all_arg_names() -> None:
    """All four pagination arg names collect; a non-pagination arg (``limit``) does not."""
    doc = parse(
        "query Q($f: Int, $l: Int, $b: String, $a: String, $lim: Int) { "
        "parents { conn(first: $f, last: $l, before: $b, after: $a, limit: $lim) "
        "{ edges { node { name } } } } }",
    )
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[1]
    assert names == frozenset(
        {
            "f",
            "l",
            "b",
            "a",
        },
    )  # ``$lim`` (a filter var) stays out


def test_nested_pagination_var_family_ignores_inline_literals() -> None:
    """A nested pagination arg with an inline literal (not a variable) is not collected.

    Inline literals already key the cache via the printed AST; the collector
    only tracks variable references (mirroring the directive collector).
    """
    doc = parse("{ parents { booksConnection(first: 3) { edges { node { title } } } } }")
    names = _collect_cache_var_families(doc.definitions[0], {}, _DEFAULT_PAGINATION_WIRE_NAMES)[1]
    assert names == frozenset()


def test_hashable_variable_value_builds_typed_structural_identity() -> None:
    """Runtime values become hashable identities without cross-shape collisions."""
    assert _hashable_variable_value(5) == _hashable_variable_value(5)
    assert _hashable_variable_value(1) != _hashable_variable_value(True)  # noqa: FBT003 - the bool is the value under test
    assert _hashable_variable_value([1, 2]) != _hashable_variable_value((1, 2))
    assert _hashable_variable_value({"b": 2, "a": [1]}) == _hashable_variable_value(
        {"a": [1], "b": 2},
    )
    assert _hashable_variable_value({1, "a"}) == _hashable_variable_value({"a", 1})
    assert isinstance(hash(_hashable_variable_value({"k": [1, {"x": 2}]})), int)


def test_hashable_variable_value_safely_degrades_for_opaque_and_cyclic_values() -> None:
    """Unknown custom-scalar values avoid both crashes and unsafe cache hits."""

    class Opaque:
        # Defining ``__eq__`` without ``__hash__`` makes the class unhashable (that is the
        # input under test).
        @override
        def __eq__(self, other: object) -> bool:
            return self is other

        # basedpyright: None is the runtime marker for unhashable; typeshed types the slot as a method
        __hash__ = None  # pyright: ignore[reportAssignmentType]

    first = _hashable_variable_value(Opaque())
    second = _hashable_variable_value(Opaque())
    assert isinstance(hash(first), int)
    assert first != second

    cyclic: list[object] = []
    cyclic.append(cyclic)
    assert isinstance(hash(_hashable_variable_value(cyclic)), int)


def test_hashable_custom_scalar_equality_cannot_abort_cache_key_lookup() -> None:
    """Hostile hashable custom scalars become opaque cache identities.

    Live HTTP:
    ``examples/fakeshop/test_query/test_optimizer_auto_api.py::test_repeated_live_query_survives_hashable_custom_scalar_equality``.
    This row is the freezer unit: opaque identities compare unequal without
    running consumer ``__eq__``.
    """

    class EqualityBomb:
        @override
        def __hash__(self) -> int:
            return 1

        @override
        def __eq__(self, _other: object) -> NoReturn:
            raise RuntimeError("custom scalar equality must not run in cache lookup")

    first = _hashable_variable_value(EqualityBomb())
    second = _hashable_variable_value(EqualityBomb())

    assert first != second
    assert isinstance(hash(first), int)
    assert isinstance(hash(second), int)
    document = "query Q($value: Int!) { parents { child(first: $value) { value } } }"

    def _key(value: object) -> "PlanCacheKey":
        info = make_info(document=document, variables={"value": value})._raw_info
        return DjangoOptimizerExtension._build_cache_key(info, Category)

    assert _key(EqualityBomb()) != _key(EqualityBomb())


def test_library_owned_scalars_share_one_cache_identity_across_requests() -> None:
    """Built-in and stdlib scalar variables must still reach the cross-request cache.

    The opaque-identity fallback protects the cache from consumer-defined
    equality, but Strawberry's own built-in scalars parse to stdlib types
    (``Date`` -> ``date``, ``DateTime`` -> ``datetime``, ``Time`` -> ``time``,
    ``Decimal`` -> ``Decimal``, ``UUID`` -> ``UUID``). Their equality is library
    code, so two requests sending the same value must produce ONE key: the
    pagination collector over-collects by argument name, so an ordinary
    ``logs(after: $timestamp)`` would otherwise never hit the plan cache and
    would evict live plans from the bounded LRU on every request.
    """
    equal_pairs = (
        (None, None),
        (True, True),
        (7, 7),
        (1.5, 1.5),
        (complex(1, 2), complex(1, 2)),
        ("cursor", "cursor"),
        (b"cursor", b"cursor"),
        (datetime.date(2026, 8, 17), datetime.date(2026, 8, 17)),
        (
            datetime.datetime(2026, 8, 17, 12, 30, tzinfo=datetime.timezone.utc),
            datetime.datetime(2026, 8, 17, 12, 30, tzinfo=datetime.timezone.utc),
        ),
        (datetime.time(12, 30), datetime.time(12, 30)),
        (datetime.timedelta(hours=3), datetime.timedelta(hours=3)),
        (decimal.Decimal("1.50"), decimal.Decimal("1.50")),
        (uuid.UUID(int=99), uuid.UUID(int=99)),
    )
    for left, right in equal_pairs:
        assert _hashable_variable_value(left) == _hashable_variable_value(right), left

    # Distinct values of the same safe type must NOT collide, or the cache would
    # serve one value's plan for another's.
    assert _hashable_variable_value(datetime.date(2026, 8, 17)) != _hashable_variable_value(
        datetime.date(2026, 8, 18),
    )
    assert _hashable_variable_value(decimal.Decimal("1.50")) != _hashable_variable_value(
        decimal.Decimal("2.50"),
    )

    # A SUBCLASS may override equality, so exact-type membership must exclude it.
    class SneakyDate(datetime.date):
        @override
        def __eq__(self, _other: object) -> NoReturn:
            raise RuntimeError("subclass equality must not run in cache lookup")

        __hash__ = datetime.date.__hash__

    assert _hashable_variable_value(SneakyDate(2026, 8, 17))[0] == "opaque"


def test_freezer_lets_cancellation_propagate_rather_than_caching_it() -> None:
    """A ``BaseException`` from hostile type inspection is not absorbed into a key.

    Cancellation and process-control signals are not cache outcomes -- swallowing
    one would convert an interrupted request into a silent cache miss.
    """

    class CancellingMeta(type):
        @override
        def __hash__(cls) -> NoReturn:
            raise asyncio.CancelledError

    class Cancelling(metaclass=CancellingMeta):
        pass

    class InterruptingMeta(type):
        @override
        def __hash__(cls) -> NoReturn:
            raise KeyboardInterrupt

    class Interrupting(metaclass=InterruptingMeta):
        pass

    # The safe-scalar test compares ``type(value)`` by identity, but the container
    # classification (``utils/_narrowing.py::is_mapping``, an ABC instance check)
    # hashes it, so a hostile metaclass ``__hash__`` is reachable and propagates.
    with pytest.raises(asyncio.CancelledError):
        _hashable_variable_value(Cancelling())
    with pytest.raises(KeyboardInterrupt):
        _hashable_variable_value(Interrupting())


def test_hashable_variable_value_never_hashes_a_custom_value() -> None:
    """A custom-scalar value keys as an opaque token; its ``__hash__`` never runs."""

    class ExplodingHash:
        @override
        def __hash__(self) -> NoReturn:
            raise RuntimeError("hash boom")

    for value in (ExplodingHash(), [ExplodingHash()]):
        frozen = _hashable_variable_value(value)
        assert isinstance(hash(frozen), int)


def test_hashable_variable_value_container_iteration_error_propagates() -> None:
    """A container a custom scalar returned is iterated on its own terms; its errors propagate."""

    class ExplodingItems(dict[str, object]):
        @override
        def items(self) -> NoReturn:
            raise RuntimeError("items boom")

    with pytest.raises(RuntimeError, match="items boom"):
        _hashable_variable_value(ExplodingItems(value=1))


def test_build_cache_key_tolerates_unhashable_pagination_variable() -> None:
    """Nested pagination-named args accept every standard input container.

    A non-connection field reusing ``after`` / ``before`` / ``first`` / ``last``
    can bind an unhashable list, input-object dict, or custom-scalar value that
    the syntactic collector over-collects. The cache key must remain buildable
    while keeping structurally different values distinct.
    """

    def _key(document: str, values: dict[str, object]) -> "PlanCacheKey":
        info = make_info(document=document, variables=values)._raw_info
        return DjangoOptimizerExtension._build_cache_key(info, Category)

    logs = "query Q($x: [Int!]!) { parents { logs(after: $x) { value } } }"
    assert _key(logs, {"x": [1, 2, 3]}) != _key(logs, {"x": [4, 5]})

    # An input-object (dict) value on ``before`` is likewise tolerated.
    events = "query Q($x: DateRange) { parents { events(before: $x) { value } } }"
    dict_key = _key(events, {"x": {"start": "2020", "end": "2021"}})
    assert _key(events, {"x": {"end": "2021", "start": "2020"}}) == dict_key


def _categories_list_schema(ext: DjangoOptimizerExtension) -> strawberry.Schema:
    """Build a ``DjangoListField(CategoryType)`` root over the reverse FK ``Category.items``.

    With the optimizer installed the parent ``Category`` queryset is planned, so
    the nested ``itemsConnection`` window lands on each category's ``to_attr``
    and the nested pagination value is baked into the cached plan - the
    end-to-end shape the cache-key rule must keep honest. A non-visibility
    synthetic target (no ``get_queryset``), so the plan is cacheable (spec-033
    Decision 7: the visibility-bearing library shape is uncacheable for an
    orthogonal reason and is covered elsewhere).
    """
    type(
        "ItemType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": Item, "fields": ("id", "name"), "interfaces": (relay.Node,)},
            ),
        },
    )
    category_type = type(
        "CategoryType",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": Category,
                    "fields": ("id", "name", "items"),
                    "interfaces": (relay.Node,),
                },
            ),
        },
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"objs": list[category_type]},
                "objs": DjangoListField(category_type),
            },
        ),
    )
    return strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )


@pytest.mark.django_db
def test_nested_pagination_variable_two_plans_two_windows() -> None:
    """End-to-end: a nested ``first: $n`` value varying yields two distinct cached plans.

    Executes the real synthesized ``itemsConnection`` under an optimizer-planned
    parent list with ``$n=2`` then ``$n=5``: two misses, two cache entries (each
    plan bakes its own window), no hit. The correctness rule of Decision 7
    observed through the live ``on_execute`` lifecycle and plan cache.
    """
    services.seed_data(2)
    ext = DjangoOptimizerExtension()
    schema = _categories_list_schema(ext)
    query = (
        "query Q($n: Int!) { objs { name itemsConnection(first: $n) "
        "{ edges { node { name } } } } }"
    )

    result_two = schema.execute_sync(query, variable_values={"n": 2})
    result_five = schema.execute_sync(query, variable_values={"n": 5})

    assert result_two.errors is None, result_two.errors
    assert result_five.errors is None, result_five.errors
    assert ext.cache_info().misses == 2
    assert ext.cache_info().hits == 0
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_root_pagination_variable_one_plan_through_schema() -> None:
    """End-to-end: a ROOT connection's ``first: $n`` value shares one cached plan.

    The optimizer-on counterpart of ``test_filter_vars_do_not_affect_cache`` for
    pagination: a root list field whose own ``first: $n`` slices post-plan does
    not fragment the cache - one miss + one hit across two ``$n`` values.
    """
    services.seed_data(2)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_categories(self, first: int = 10) -> QuerySet[Category]:
            return Category.objects.all()[:first]

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "query Q($n: Int!) { allCategories(first: $n) { name } }"

    schema.execute_sync(query, variable_values={"n": 1})
    schema.execute_sync(query, variable_values={"n": 2})

    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1


@pytest.mark.django_db
def test_cache_key_variable_name_collection_memoized_for_nested_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The unified var-name AST walk runs once per operation, not per ``_build_cache_key``.

    Decision 7: nested fallback connections call ``_build_cache_key`` once per
    parent row, so the full-operation cache-relevant-variable walk must be
    memoized per ``id(operation)`` within one ``on_execute`` lifecycle. Wrap the
    unified collector (``_collect_cache_relevant_var_names`` -- which folds
    both the directive and nested-pagination families into one traversal) with a
    call counter and assert repeated ``_build_cache_key`` calls on the SAME
    operation walk it only once - including one call made after the
    cross-request document LRU has been emptied, so the per-execution memo is
    pinned on its own rather than through the document cache standing in for it.
    """
    calls = {"count": 0}
    real = extension_module._collect_cache_relevant_var_names

    def _counting(
        operation: OperationDefinitionNode,
        fragments: Mapping[str, FragmentDefinitionNode],
        pagination_wire_names: frozenset[str],
    ) -> frozenset[str]:
        calls["count"] += 1
        return real(operation, fragments, pagination_wire_names)

    monkeypatch.setattr(extension_module, "_collect_cache_relevant_var_names", _counting)
    # Isolate the cross-request document LRU. This document's text is byte-
    # identical to ``test_nested_pagination_variable_keys_cache``'s, which
    # inserts the same key, and ``--dist loadscope`` keeps the whole module on
    # one worker - so a populated cache would serve the first call from a HIT
    # and the counter would read 0 whenever that sibling ran first. A fresh
    # mapping makes the first call a guaranteed MISS, which is what makes the
    # count below a measurement rather than an artifact of collection order.
    monkeypatch.setattr(extension_module, "_doc_key_cache", _DocKeyCache())

    info = make_info(
        document=(
            "query Q($n: Int!) { parents { booksConnection(first: $n) "
            "{ edges { node { title } } } } }"
        ),
        variables={"n": 2},
    )._raw_info

    ext = DjangoOptimizerExtension()
    gen = ext.on_execute()
    next(gen)  # enter the lifecycle: installs the per-execution var-name memo
    try:
        DjangoOptimizerExtension._build_cache_key(info, Category)
        DjangoOptimizerExtension._build_cache_key(info, Category)
        DjangoOptimizerExtension._build_cache_key(info, Category)
        assert calls["count"] == 1
        # Empty the cross-request LRU mid-lifecycle so only the per-execution
        # ``id(operation)`` memo can answer the next call. The counter staying
        # at 1 pins THAT tier specifically - without it this fourth call is a
        # document-cache miss and the collector runs again.
        extension_module._doc_key_cache.clear()
        DjangoOptimizerExtension._build_cache_key(info, Category)
    finally:
        with contextlib.suppress(StopIteration):
            next(gen)  # exit the lifecycle: resets the memo

    assert calls["count"] == 1


def test_collect_cache_relevant_var_names_unifies_both_families_through_fragment() -> None:
    """B1: one traversal returns BOTH a directive var and a nested-pagination var.

    The unified ``_collect_cache_relevant_var_names`` walk collects the
    ``@skip``/``@include`` family and the non-root pagination family in a single
    descent, including through a fragment spread. ``$skip`` (a directive variable
    on a nested field) and ``$n`` (a ``first:`` pagination variable on a nested
    field) both reach the cache key from one walk; the root field ``parents``
    contributes neither.
    """
    doc = parse(
        "query Q($skip: Boolean!, $n: Int!) { parents { ...F } } "
        "fragment F on Parent { booksConnection(first: $n) @skip(if: $skip) "
        "{ edges { node { title } } } }",
    )
    operation = _operation(doc)
    fragments = _fragments_by_name(doc.definitions[1:])
    names = _collect_cache_relevant_var_names(
        operation,
        fragments,
        _DEFAULT_PAGINATION_WIRE_NAMES,
    )
    assert names == frozenset({"skip", "n"})


# ---------------------------------------------------------------------------
# B3: N+1 detection (strictness API)
# ---------------------------------------------------------------------------


def test_strictness_invalid_value_raises() -> None:
    """B3: passing an invalid strictness value raises ValueError."""
    with pytest.raises(ValueError, match="strictness must be"):
        DjangoOptimizerExtension(strictness="invalid")


_END_DETONATION = "hostile dunder detonated"


class _DetonatingEqStr(str):
    @override
    def __eq__(self, other: object) -> NoReturn:
        raise RuntimeError(_END_DETONATION)

    @override
    def __hash__(self) -> int:
        return str.__hash__(self)


class _DetonatingReprStr(str):
    @override
    def __repr__(self) -> str:
        raise RuntimeError(_END_DETONATION)


class _DetonatingEqObject:
    @override
    def __eq__(self, other: object) -> NoReturn:
        raise RuntimeError(_END_DETONATION)

    # basedpyright: None is the runtime marker for unhashable; typeshed types the slot as a method
    __hash__ = None  # pyright: ignore[reportAssignmentType]


@pytest.mark.parametrize(
    "hostile",
    [_DetonatingEqStr("bogus"), _DetonatingEqObject()],
    ids=["eq-str-subclass", "eq-object"],
)
def test_strictness_hostile_dunder_values_raise_typed_valueerror(hostile: object) -> None:
    """A strictness value's ``__eq__`` never decides the typed rejection.

    The strictness boundary is construction-time consumer configuration with a
    promised ``ValueError``. The membership read compares ``str`` candidates
    through the base ``str`` slot and rejects non-``str`` candidates without an
    equality probe, so a raising ``__eq__`` (reached through reflected
    comparison for a plain object) never runs.
    """
    with pytest.raises(ValueError, match="strictness must be") as exc_info:
        # basedpyright: the non-str strictness is the hostile input under test;
        # DjangoOptimizerExtension types the parameter as str
        DjangoOptimizerExtension(strictness=hostile)  # pyright: ignore[reportArgumentType]
    assert _END_DETONATION not in str(exc_info.value)


class _StrictnessClaimsStr(ClaimsClassBase):
    """A non-``str`` strictness value whose ``__class__`` claims ``str``."""

    claimed = str


@pytest.mark.parametrize(
    "make",
    [
        lambda: ClassReadRaisesBase(RuntimeError, _END_DETONATION),
        lambda: ClassReadRaisesBase(TypeError, _END_DETONATION),
        lambda: ClassReadRaisesBase(KeyboardInterrupt, _END_DETONATION),
        _StrictnessClaimsStr,
        lambda: SimpleLazyObject(lambda: "warn"),
    ],
    ids=[
        "class-read-raises-runtime-error",
        "class-read-raises-type-error",
        "class-read-raises-base-exception",
        "class-claims-str",
        "lazy-str",
    ],
)
def test_strictness_non_str_lookalikes_raise_typed_valueerror(
    make: Callable[[], object],
) -> None:
    """Whether strictness is a ``str`` is asked of its real type, never its ``__class__``.

    A ``__class__`` that raises, or that claims ``str`` for a value the base
    ``str`` slot then refuses, and a lazy proxy of a mode are all not ``str``, so
    each is rejected with the typed ``ValueError`` before any comparison.
    """
    with pytest.raises(ValueError, match="strictness must be") as exc_info:
        # basedpyright: the non-str strictness is the hostile input under test;
        # DjangoOptimizerExtension types the parameter as str
        _ = DjangoOptimizerExtension(strictness=make())  # pyright: ignore[reportArgumentType]
    assert str(exc_info.value).startswith("strictness must be 'off', 'warn', or 'raise', got <")
    assert _END_DETONATION not in str(exc_info.value)


def test_strictness_rejection_renders_the_value_through_its_own_repr() -> None:
    """Rendering a rejected ``str`` subclass runs its own ``__repr__``, which propagates."""
    with pytest.raises(RuntimeError, match=_END_DETONATION):
        DjangoOptimizerExtension(strictness=_DetonatingReprStr("bogus"))


def test_strictness_accepts_content_equal_str_subclass() -> None:
    """B3: a benign str subclass with valid CONTENT keeps being accepted.

    The base-slot comparison classifies by content, so a ``str`` subclass is
    not over-blocked by the hostility guard (mirroring the strategy resolver's
    content-equality convention).
    """

    class ContentRaise(str):
        @override
        def __repr__(self) -> str:
            raise RuntimeError(_END_DETONATION)

    extension = DjangoOptimizerExtension(strictness=ContentRaise("raise"))
    assert type(extension.strictness) is str
    assert extension.strictness == "raise"


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["warn", "raise"])
@pytest.mark.parametrize("kind", STR_SUBCLASS_KINDS)
def test_str_subclass_strictness_arms_the_guard_as_its_text(
    kind: str,
    mode: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A ``str`` subclass spelling ``"warn"`` / ``"raise"`` arms exactly that mode.

    The extension stores the vocabulary's own constant, so every request compares
    a plain ``str`` the package owns: a subclass whose ``__eq__`` never matches
    still warns or raises on an unplanned relation, one whose comparison raises
    never turns a request into an error of its own, and none of its dunders run
    after construction.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.SKIP}

    @strawberry.type
    class Query:
        def _projected_items(self) -> QuerySet[Item]:
            return Item.objects.order_by("id").only("name")

        projected_items: QuerySet[Item] = strawberry.field(
            resolver=_projected_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    calls: list[str] = []
    optimizer = DjangoOptimizerExtension(strictness=str_subclass_name(kind, mode, calls))
    assert type(optimizer.strictness) is str
    assert optimizer.strictness == mode
    schema = strawberry.Schema(query=Query, extensions=[lambda: optimizer])

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync("{ projectedItems { name category { name } } }")

    if mode == "raise":
        assert result.errors is not None
        assert [error.message for error in result.errors] == ["Unplanned N+1: category"]
    else:
        assert result.errors is None
        assert any("Potential N+1 on category" in r.message for r in caplog.records)
    assert calls == []


@pytest.mark.parametrize(
    "drain_at_pop",
    [
        1,
        2,
        3,
        4,
    ],
)
def test_plan_cache_eviction_survives_concurrent_drain(
    monkeypatch: pytest.MonkeyPatch,
    drain_at_pop: int,
) -> None:
    """B1: the eviction sweep tolerates the shared-instance drain race.

    One extension instance is shared across a threaded / ASGI execution, and
    the eviction loop pops up to a quarter of the cache after reading its
    length. Concurrent requests' own sweeps can empty the cache between that
    length read and any one of those pops; like the hit path's
    ``move_to_end`` and the document-key cache's ``popitem``, the sweep must
    absorb the ``KeyError`` instead of failing the request that was building a
    plan. The drain lands on each pop position of the sweep in turn, so every
    interleaving is pinned, not just the first.
    """
    monkeypatch.setattr(extension_module, "_MAX_PLAN_CACHE_SIZE", 16)

    def _info_for(root_field: str) -> GraphQLResolveInfo:
        return make_info(document=f"query Q{root_field} {{ {root_field} }}")._raw_info

    extension = DjangoOptimizerExtension()
    for idx in range(16):
        key = DjangoOptimizerExtension._build_cache_key(
            _info_for(f"root{idx}"),
            Category,
            None,
        )
        extension._plan_cache[key] = OptimizationPlan()
    assert len(extension._plan_cache) == 16

    # Simulate the interleaving: after this thread's length read, other
    # requests' evictions drain the cache just before the ``drain_at_pop``-th
    # pop of OUR sweep, so that pop hits an empty dict.
    real_popitem = extension._plan_cache.popitem
    pops: list[None] = []

    def racing_popitem(*, last: bool) -> "tuple[PlanCacheKey, OptimizationPlan]":
        pops.append(None)
        if len(pops) == drain_at_pop:
            extension._plan_cache.clear()
        return real_popitem(last=last)

    monkeypatch.setattr(extension._plan_cache, "popitem", racing_popitem)

    new_plan = SimpleNamespace(cacheable=True)

    def _new_plan(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return new_plan

    monkeypatch.setattr(extension_module, "plan_optimizations", _new_plan)

    plan = extension._get_or_build_plan([], Category, _info_for("rootnew"), None)
    assert plan is new_plan
    assert len(pops) == 4


@pytest.mark.django_db
def test_strictness_warn_logs_unplanned_relation(caplog: pytest.LogCaptureFixture) -> None:
    """B3: strictness='warn' logs a warning for unplanned uncached relation access."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> list[Item]:
            return list(Item.objects.all()[:1])

        all_items: list[Item] = strawberry.field(resolver=_all_items, graphql_type=list[ItemType])

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="warn",
    )

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert any("Potential N+1 on category" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_strictness_off_does_not_stash_sentinel() -> None:
    """B3: strictness='off' does not stash the sentinel on context."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    ext = DjangoOptimizerExtension(strictness="off")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    # No sentinel stashed when strictness is off.
    assert not hasattr(ctx, "dst_optimizer_planned")


@pytest.mark.django_db
def test_strictness_warn_stashes_sentinel() -> None:
    """B3: strictness='warn' stashes the sentinel on context."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    planned = getattr(ctx, "dst_optimizer_planned", None)
    assert planned is not None
    assert "ItemType.category@allItems.category" in planned
    assert read_attr(ctx, DST_OPTIMIZER_STRICTNESS) == "warn"


@pytest.mark.django_db
@pytest.mark.parametrize("mode", ["warn", "raise"])
def test_strictness_with_empty_plan_does_not_raise_or_warn(
    mode: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """B3: an empty plan plus strictness='warn'/'raise' must not raise or warn.

    ``_publish_plan_to_context`` stashes the strictness sentinels (planned set,
    lookup paths, mode) before ``_optimize`` short-circuits on ``plan.is_empty``.
    The invariant is that an empty plan implies no relation selections, so the
    downstream resolver path never compares against the empty planned set.  This
    test pins the invariant for the enabled-optimizer path under both ``warn``
    and ``raise`` - a scalar-only query against a registered type produces an
    empty plan and must resolve cleanly with no warning emitted and no
    exception raised.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    ext = DjangoOptimizerExtension(strictness=mode)
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    with caplog.at_level("WARNING", logger=optimizer_logger.name):
        result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    # No GraphQL execution errors (would surface a "raise" strictness trip).
    assert result.errors is None
    # No optimizer-level warning logged (would surface a "warn" strictness trip).
    assert not any(
        record.name == optimizer_logger.name and record.levelname == "WARNING"
        for record in caplog.records
    )
    # Strictness sentinels are still stashed (the plan is published before the
    # is_empty short-circuit); the planned set is just empty.
    assert read_attr(ctx, DST_OPTIMIZER_STRICTNESS) == mode
    assert _stashed_keys(ctx, DST_OPTIMIZER_PLANNED) == set()


@pytest.mark.django_db
def test_strictness_includes_fk_id_elision_in_planned_paths(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """B2+B3: FK-id-elided relations are planned and do not warn."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert "ItemType.category@allItems.category" in _stashed_keys(ctx, DST_OPTIMIZER_PLANNED)
    assert _stashed_keys(ctx, DST_OPTIMIZER_FK_ID_ELISIONS) == {
        "ItemType.category@allItems.category",
    }
    assert not any("Potential N+1" in r.message for r in caplog.records)


def test_will_lazy_load_false_when_cached() -> None:
    """B3: pin the __dict__ compatibility seam used by synthetic test doubles."""
    root = SimpleNamespace(category="cached_value")
    assert _will_lazy_load_single(root, "category") is False


def test_will_lazy_load_false_when_in_fields_cache() -> None:
    """B3: _will_lazy_load_single returns False when a relation is in _state.fields_cache."""
    root = SimpleNamespace(_state=SimpleNamespace(fields_cache={"card": "cached"}))
    assert _will_lazy_load_single(root, "card") is False


@pytest.mark.django_db
def test_will_lazy_load_false_for_real_forward_fk_in_fields_cache() -> None:
    """B3: real forward FKs cache in _state.fields_cache, not __dict__."""
    services.seed_data(1)
    item = Item.objects.select_related("category").first()

    assert item is not None
    assert "category" not in item.__dict__
    assert "category" in item._state.fields_cache
    assert _will_lazy_load_single(item, "category") is False


@pytest.mark.django_db
def test_will_lazy_load_false_for_real_reverse_one_to_one_in_fields_cache() -> None:
    """B3: real reverse OneToOne relations also cache in _state.fields_cache."""
    patron = Patron.objects.create(name="Ada")
    MembershipCard.objects.create(patron=patron, barcode="1234")
    cached_patron = Patron.objects.select_related("card").get(pk=saved_pk(patron))

    assert "card" not in cached_patron.__dict__
    assert "card" in cached_patron._state.fields_cache
    assert _will_lazy_load_single(cached_patron, "card") is False


def test_will_lazy_load_true_when_not_cached() -> None:
    """B3: _will_lazy_load_single returns True when the relation is not cached."""
    root = SimpleNamespace()
    assert _will_lazy_load_single(root, "category") is True


def test_will_lazy_load_false_when_prefetched() -> None:
    """B3: _will_lazy_load_many returns False when relation is in _prefetched_objects_cache."""
    root = SimpleNamespace()
    root._prefetched_objects_cache = {
        "items": [1, 2, 3],
    }
    assert _will_lazy_load_many(root, "items") is False


@pytest.mark.django_db
def test_strictness_raise_accepts_unplanned_cached_forward_fk() -> None:
    """B3: strictness='raise' accepts an unplanned forward FK that is already loaded."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> list[Item]:
            return list(Item.objects.select_related("category").all()[:1])

        all_items: list[Item] = strawberry.field(resolver=_all_items, graphql_type=list[ItemType])

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="raise",
    )

    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert result.data is not None
    assert result.data["allItems"][0]["category"]["name"]


@pytest.mark.django_db
def test_strictness_raise_accepts_unplanned_cached_reverse_one_to_one() -> None:
    """B3: strictness='raise' accepts an unplanned reverse OneToOne already loaded."""
    patron = Patron.objects.create(name="Ada")
    MembershipCard.objects.create(patron=patron, barcode="1234")

    class CardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode")

    assert registry.get(MembershipCard) is CardType

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    @strawberry.type
    class Query:
        def _all_patrons(self) -> list[Patron]:
            return list(Patron.objects.select_related("card").all())

        all_patrons: list[Patron] = strawberry.field(
            resolver=_all_patrons,
            graphql_type=list[PatronType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="raise",
    )

    result = schema.execute_sync(
        "{ allPatrons { name card { barcode } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert result.data == {
        "allPatrons": [
            {"name": "Ada", "card": {"barcode": "1234"}},
        ],
    }


@pytest.mark.django_db
def test_strictness_warn_planned_alias_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    """B3: aliased relation that IS planned does not trigger a warning."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    # Use an alias "cat" for the planned "category" relation.
    result = schema.execute_sync(
        "{ allItems { name cat: category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # The plan includes "category" and the resolver uses field_name
    # (not the alias), so no false-positive warning.
    assert not any("Potential N+1" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_optimizer_strictness_accepts_nested_planned_relation() -> None:
    """O4+B3: strictness accepts resolver keys from nested plans."""
    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    assert registry.get(Entry) is EntryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "entries")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "items")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    ext = DjangoOptimizerExtension(strictness="raise")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { items { entries { value } } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert "ItemType.entries@allCategories.items.entries" in _stashed_keys(
        ctx,
        DST_OPTIMIZER_PLANNED,
    )


@pytest.mark.django_db
def test_optimizer_nested_prefetch_with_custom_get_queryset_marks_uncacheable() -> None:
    """O4+O6: nested request-dependent prefetch plans are not cached."""
    services.seed_data(1)
    calls: list[object] = []

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Entry],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Entry]:
            calls.append(info)
            return queryset

    assert registry.get(Entry) is EntryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "entries")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "items")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allCategories { items { entries { value } } } }"

    assert schema.execute_sync(query).errors is None
    assert schema.execute_sync(query).errors is None
    assert len(calls) == 2
    assert ext.cache_info().size == 0


def test_directive_var_family_in_named_fragment() -> None:
    """B1: the directive family follows named fragment spreads."""
    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits } } "
        "fragment ItemBits on ItemType { category @include(if: $show) { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if isinstance(d, FragmentDefinitionNode)}
    names = _collect_cache_var_families(operation, fragments, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset({"show"})


def test_directive_var_family_includes_fragment_spread_directives() -> None:
    """B1: directives on a ``...Spread`` itself feed the cache key, not just the body."""
    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits @include(if: $show) } } "
        "fragment ItemBits on ItemType { category { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if isinstance(d, FragmentDefinitionNode)}
    names = _collect_cache_var_families(operation, fragments, _DEFAULT_PAGINATION_WIRE_NAMES)[0]
    assert names == frozenset({"show"})


def test_cache_key_includes_fragment_spread_directive_variable_value() -> None:
    """B1: a variable on a fragment-spread ``@include`` splits the cache."""
    document = (
        "query Q($show: Boolean!) { allItems { ...ItemBits @include(if: $show) } } "
        "fragment ItemBits on ItemType { category { name } }"
    )
    info_false = make_info(document=document, variables={"show": False})._raw_info
    info_true = make_info(document=document, variables={"show": True})._raw_info

    assert DjangoOptimizerExtension._build_cache_key(
        info_false,
        Item,
    ) != DjangoOptimizerExtension._build_cache_key(info_true, Item)


# ---------------------------------------------------------------------------
# B6: Schema-build-time optimization audit
# ---------------------------------------------------------------------------


def test_collect_schema_reachable_types_returns_empty_without_graphql_schema() -> None:
    """B6: schemas without a graphql-core schema expose no reachable types."""
    assert len(_collect_schema_reachable_types(SimpleNamespace())) == 0


def test_check_schema_skips_unreachable_and_missing_field_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B6: check_schema skips orphan types and types without optimizer metadata."""

    class ReachableWithoutFieldMap:
        pass

    class UnreachableType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    # basedpyright: a class registered with no definition is the input under test (a type
    # without optimizer metadata); registry.register types the parameter as type[DjangoType]
    registry.register(Category, ReachableWithoutFieldMap)  # pyright: ignore[reportArgumentType]
    del UnreachableType

    def _reachable_types(_schema: object) -> set[type]:
        return {ReachableWithoutFieldMap}

    monkeypatch.setattr(extension_module, "_collect_schema_reachable_types", _reachable_types)

    assert DjangoOptimizerExtension.check_schema(SimpleNamespace()) == []


def test_check_schema_warns_unregistered_target() -> None:
    """B6: check_schema warns when a relation's target has no registered DjangoType."""

    # Must register CategoryType first so ItemType's category relation resolves at finalize time,
    # then clear it from the registry so check_schema sees the gap.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    # Clear Category's registration so the audit finds a gap.
    _force_unregister_after_finalize(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_descends_into_union_types() -> None:
    """B6: union members are reachable in check_schema's audit walk.

    GraphQL unions expose their constituent object types via ``.types``,
    not ``.fields``. The schema walker must descend into ``.types`` so a
    ``DjangoType`` reachable only through a union (e.g.
    ``list[ItemType | CategoryType]``) still participates in the audit.
    Without that, ``check_schema`` silently skips missing-target warnings
    for any relation that lives on a union-member type.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self) -> list[ItemType | CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    # Internal reachable set must include both union members.
    reachable = _collect_schema_reachable_types(schema)
    assert ItemType in reachable
    assert CategoryType in reachable

    # User-visible consequence: drop Category's registration and check_schema
    # must still surface the gap on ItemType.category. Without the union walk
    # ItemType is unreachable from the root, the audit skips it, and the
    # warning is silently lost.
    _force_unregister_after_finalize(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_descends_into_interface_implementations() -> None:
    """B6: interface implementers are reachable in check_schema's audit walk.

    GraphQL interfaces expose their concrete implementers via
    ``schema.get_implementations(interface_type).objects``, not via
    ``.fields`` or ``.types``. When a root field is typed as an
    interface and the only ``DjangoType``s involved are the concrete
    implementations, the schema walker must descend into those
    implementations so each implementer's relations still participate
    in the audit. Without that, ``check_schema`` silently skips missing
    -target warnings for any relation that lives on an interface
    implementer.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class ItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            interfaces = (relay.Node,)

    @strawberry.type
    class Query:
        @strawberry.field
        def some_node(self) -> relay.Node:
            # Never executed: the annotation only builds the schema whose interface implementers
            # the reachability audit walks.
            raise NotImplementedError

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[CategoryNode, ItemNode])

    # Internal reachable set must include both implementers even though
    # the root field is typed as the ``Node`` interface.
    reachable = _collect_schema_reachable_types(schema)
    assert ItemNode in reachable
    assert CategoryNode in reachable

    # User-visible consequence: drop Category's registration and the
    # audit must still surface the gap on ItemNode.category. Without
    # interface descent ItemNode would not be reachable and the warning
    # would be silently lost.
    _force_unregister_after_finalize(CategoryNode)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_no_warnings_when_all_covered() -> None:
    """B6: check_schema returns no warnings when all relations have registered targets."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # category's target (Category) is registered, so no warnings for it.
    assert not any("category" in w for w in warnings)


def test_check_schema_skip_hint_suppresses_warning() -> None:
    """B6: relations with OptimizerHint.SKIP are not flagged."""

    # Register CategoryType so the ItemType.category PendingRelation resolves at finalize time.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.SKIP}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    # Clear Category so the audit would normally warn - but SKIP suppresses.
    _force_unregister_after_finalize(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # SKIP means category is intentionally unoptimized - no warning.
    assert not any("category" in w for w in warnings)


def test_check_schema_hidden_fields_not_flagged() -> None:
    """B6: relations excluded by Meta.fields are not flagged."""

    # ItemType excludes "category" from Meta.fields.
    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # category is not in the definition field map, so it is not flagged.
    assert not any("category" in w for w in warnings)


# ---------------------------------------------------------------------------
# B4: the Meta.optimizer_hints option
# ---------------------------------------------------------------------------


def test_optimizer_hints_unknown_field_raises() -> None:
    """B4: unknown field name in optimizer_hints raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        @definition_raises
        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")
                optimizer_hints = {"nonexistent": OptimizerHint.SKIP}


def test_optimizer_hints_non_hint_value_raises() -> None:
    """B4: non-OptimizerHint value in optimizer_hints raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="OptimizerHint instances"):

        @definition_raises
        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name", "category")
                optimizer_hints = {"category": "skip"}  # string, not OptimizerHint


def test_optimizer_hint_importable_from_top_level() -> None:
    """B4: OptimizerHint is importable from the top-level package."""
    assert OptimizerHint.SKIP is not None
    assert OptimizerHint.select_related() is not None


# ---------------------------------------------------------------------------
# B5: plan introspection via context
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.usefixtures("django_assert_num_queries")
def test_plan_stashed_with_select_related() -> None:
    """B5: the stashed plan contains the expected select_related entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    # Execute the query with a custom context to capture the plan.
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert "category" in plan.select_related


@pytest.mark.django_db
@pytest.mark.usefixtures("django_assert_num_queries")
def test_plan_stashed_with_prefetch_related() -> None:
    """B5: the stashed plan contains the expected prefetch_related entries."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    assert registry.get(Property) is PropertyType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert [
        require_instance(lookup, Prefetch).prefetch_to for lookup in plan.prefetch_related
    ] == ["items"]


def test_publish_plan_to_context_reuses_finalized_metadata() -> None:
    """B5: context publish reuses finalized frozensets instead of rebuilding them."""
    ext = DjangoOptimizerExtension(strictness="raise")
    plan = OptimizationPlan(
        select_related=["category"],
        fk_id_elisions=["ItemType.category@allItems.category"],
        planned_resolver_keys=["ItemType.category@allItems.category"],
    ).finalize()
    ctx = SimpleNamespace()

    ext._publish_plan_to_context(plan, make_info(context=ctx)._raw_info)

    assert _stashed_plan(ctx) is plan
    assert _stashed_keys(ctx, DST_OPTIMIZER_FK_ID_ELISIONS) is plan.finalized_fk_id_elisions
    assert _stashed_keys(ctx, DST_OPTIMIZER_PLANNED) is plan.finalized_planned_resolver_keys
    assert _stashed_keys(ctx, DST_OPTIMIZER_LOOKUP_PATHS) is plan.finalized_lookup_paths


def test_publish_plan_to_context_rebuilds_metadata_for_unfinalized_plan() -> None:
    """B5: an unfinalized plan published under strictness rebuilds the sentinel sets.

    Production plans are always finalized, but the publish path keeps a
    defensive fallback: when ``finalized_*`` is ``None`` it recomputes the
    frozensets from the live directive lists rather than stashing ``None``.
    """
    ext = DjangoOptimizerExtension(strictness="raise")
    plan = OptimizationPlan(
        select_related=["category"],
        fk_id_elisions=["ItemType.category@allItems.category"],
        planned_resolver_keys=["ItemType.category@allItems.category"],
    )
    assert plan.finalized_planned_resolver_keys is None
    assert plan.finalized_lookup_paths is None
    ctx = SimpleNamespace()

    ext._publish_plan_to_context(plan, make_info(context=ctx)._raw_info)

    assert _stashed_keys(ctx, DST_OPTIMIZER_FK_ID_ELISIONS) == frozenset(
        {"ItemType.category@allItems.category"},
    )
    assert _stashed_keys(ctx, DST_OPTIMIZER_PLANNED) == frozenset(
        {"ItemType.category@allItems.category"},
    )
    assert _stashed_keys(ctx, DST_OPTIMIZER_LOOKUP_PATHS) == frozenset({"category"})


def test_named_children_skips_excluded_and_recurses_through_fragments() -> None:
    """Connection extraction: ``@skip`` children are dropped and fragments inlined."""
    edges = {PYTHON_NAME_ATTR: "edges"}
    skipped = SimpleNamespace(
        name="edges",
        directives={"skip": {"if": True}},
        selections=[],
        **edges,
    )
    inner_edges = SimpleNamespace(name="edges", alias=None, directives={}, selections=[], **edges)
    fragment = SimpleNamespace(
        type_condition="ItemConnectionEdge",
        directives={},
        selections=[inner_edges],
    )
    plain = SimpleNamespace(name="edges", alias=None, directives={}, selections=[], **edges)
    container = SimpleNamespace(selections=[skipped, fragment, plain])

    result = _named_children(container, "edges")

    # ``skipped`` excluded; the fragment's inner ``edges`` is inlined; ``plain`` kept.
    assert result == [inner_edges, plain]


def test_node_children_with_runtime_prefix_skips_excluded_and_clones_fragments() -> None:
    """Connection extraction: node children honor ``@include`` and clone fragments."""
    skipped = SimpleNamespace(name="name", directives={"include": {"if": False}}, selections=[])
    fragment = SimpleNamespace(type_condition="ItemNode", directives={}, selections=[])
    plain = SimpleNamespace(name="name", alias=None, directives={}, arguments={}, selections=[])
    node = SimpleNamespace(selections=[skipped, fragment, plain])
    prefixes = (("items", "edges", "node"),)

    result = _node_children_with_runtime_prefix(node, runtime_prefixes=prefixes)

    # ``skipped`` excluded; fragment cloned (carries its type condition); plain
    # cloned carrying the connection-aware runtime prefix for the walker.
    assert len(result) == 2
    assert read_attr(result[0], "type_condition") == "ItemNode"
    assert read_attr(result[1], "_optimizer_runtime_prefixes") == [("items", "edges", "node")]


def test_plan_stashed_on_dict_context() -> None:
    """B5: when context is a plain dict, plan is stashed via __setitem__."""
    ctx: dict[str, object] = {}

    plan = OptimizationPlan(select_related=["category"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx["dst_optimizer_plan"] is plan


def test_stash_on_dict_subclass_writes_mapping_before_attributes() -> None:
    """Dict-like contexts must use the mapping branch."""

    class AttributeBackedDict(dict[str, object]):
        attributes: dict[str, object]

        def __init__(self) -> None:
            super().__init__()
            super().__setattr__("attributes", {})

        @override
        def __setattr__(self, key: str, value: object) -> None:
            self.attributes[key] = value

    ctx = AttributeBackedDict()
    plan = OptimizationPlan(select_related=["category"])
    stash_on_context(ctx, "dst_optimizer_plan", plan)

    assert ctx["dst_optimizer_plan"] is plan
    assert ctx.attributes == {}
    assert get_context_value(ctx, "dst_optimizer_plan") is plan


def test_stash_on_non_dict_mapping_reads_correctly() -> None:
    """get_context_value retrieves stashes from non-dict mappings via item access fallback."""

    class NonDictMapping:
        __slots__ = ("_data",)

        def __init__(self) -> None:
            self._data: dict[str, object] = {}

        def __setitem__(self, key: str, value: object) -> None:
            self._data[key] = value

        def __getitem__(self, key: str) -> object:
            return self._data[key]

    ctx = NonDictMapping()
    plan = OptimizationPlan()
    stash_on_context(ctx, "dst_optimizer_plan", plan)

    # Assert stash bypassed setattr (because of __slots__) and populated _data
    assert ctx._data["dst_optimizer_plan"] is plan

    # Assert get_context_value safely falls back to item access and retrieves it
    assert get_context_value(ctx, "dst_optimizer_plan") is plan


def test_get_context_value_swallows_attribute_error_from_getitem() -> None:
    """A ``__getitem__`` raising ``AttributeError`` on a missing key returns ``default``.

    ``strawberry-graphql-django``'s ``StrawberryDjangoContext`` bridges
    ``__getitem__`` to ``__getattribute__``, so reading a key that was never
    stashed raises ``AttributeError`` out of the item access path. The read
    helper's ``except`` tuple must catch ``AttributeError`` alongside
    ``KeyError`` / ``TypeError`` so the resolver chain sees ``default`` rather
    than a leaking ``AttributeError`` from deep inside item lookup.
    """

    class BridgedItemAccess:
        """Mimics ``StrawberryDjangoContext.__getitem__`` shape."""

        def __getitem__(self, key: str) -> NoReturn:
            raise AttributeError(f"missing attribute {key!r}")

    sentinel = object()
    ctx = BridgedItemAccess()
    assert get_context_value(ctx, "dst_optimizer_plan", sentinel) is sentinel


def test_stash_on_none_context_is_silent() -> None:
    """B5: when context is None (Strawberry default), stash is silently skipped."""
    plan = OptimizationPlan()
    # Should not raise.
    _stash_on_context(None, "dst_optimizer_plan", plan)


def test_plan_stashed_on_object_context_unit() -> None:
    """B5: when context is an object, plan is stashed via setattr."""
    ctx = SimpleNamespace()

    plan = OptimizationPlan(prefetch_related=["items"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert _stashed_plan(ctx) is plan


def test_stash_on_read_only_mapping_is_silent() -> None:
    """B5: a read-only ``MappingProxyType`` context must not abort the resolver chain.

    ``setattr`` on a ``MappingProxyType`` raises ``TypeError`` (not ``AttributeError``), and
    ``__setitem__`` then raises ``TypeError`` again. Both must be swallowed
    so the optimizer's introspection-stash failure never crashes the
    request.
    """
    ctx = MappingProxyType[str, object]({})
    plan = OptimizationPlan(prefetch_related=["items"])
    # Should not raise.
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert "dst_optimizer_plan" not in ctx


def test_stash_falls_back_to_setitem_on_typeerror() -> None:
    """B5: a ``dict`` subclass is still stashed through ``__setitem__``.

    Dict-like context objects take the mapping branch before attribute
    writes, so a subclass with hostile attribute assignment still stores
    the optimizer plan where ``get_context_value`` will read it.
    """

    class TypeErrorOnSetattr(dict[str, object]):
        @override
        def __setattr__(self, _key: str, _value: object) -> None:
            raise TypeError("read-only attribute access")

    ctx = TypeErrorOnSetattr()
    plan = OptimizationPlan(prefetch_related=["items"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx["dst_optimizer_plan"] is plan


def test_stash_on_immutable_dict_subclass_is_silent() -> None:
    """``AttributeError`` from a frozen ``dict`` subclass is silently skipped.

    Django's ``QueryDict`` is a ``dict`` subclass that raises
    ``AttributeError("This QueryDict instance is immutable")`` from
    ``__setitem__`` when locked. The dict-first dispatch in
    ``stash_on_context`` routes subclasses through the mapping write
    path, so the trailing ``except`` must catch ``AttributeError`` in
    addition to ``TypeError`` - otherwise an immutable-``QueryDict``
    context would crash the resolver chain instead of being silently
    skipped, contradicting the docstring contract ("Frozen contexts ...
    raise on assignment; those stashes are silently skipped").
    """

    class ImmutableDictSubclass(dict[str, object]):
        @override
        def __setitem__(self, _key: str, _value: object) -> None:
            raise AttributeError("this dict is immutable")

    ctx = ImmutableDictSubclass()
    plan = OptimizationPlan(prefetch_related=["items"])
    stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert "dst_optimizer_plan" not in ctx


def test_stash_does_not_swallow_unexpected_exceptions_from_setitem() -> None:
    """The mapping-write ``except`` stays narrow.

    Read-only mapping failures are intentionally limited to ``TypeError``
    and ``AttributeError``. A guarded mapping that raises a different
    exception from ``__setitem__`` must surface the error rather than
    silently losing the optimizer stash.
    """

    class GuardedMapping(dict[str, object]):
        @override
        def __setattr__(self, _key: str, _value: object) -> None:
            raise TypeError("no attribute writes")

        @override
        def __setitem__(self, _key: str, _value: object) -> None:
            raise RuntimeError("guarded write rejected")

    ctx = GuardedMapping()
    with pytest.raises(RuntimeError, match="guarded write rejected"):
        stash_on_context(ctx, "dst_optimizer_plan", object())


def test_clear_optimizer_context_removes_all_keys_from_object_and_dict() -> None:
    """Start-of-execution clear drops every DST_OPTIMIZER_* key on object and dict contexts."""
    empty: dict[str, object] = {}
    for ctx in (SimpleNamespace(), empty):
        stash_on_context(ctx, DST_OPTIMIZER_PLAN, object())
        stash_on_context(ctx, DST_OPTIMIZER_FK_ID_ELISIONS, frozenset({"k"}))
        stash_on_context(ctx, DST_OPTIMIZER_PLANNED, frozenset({"k"}))
        stash_on_context(ctx, DST_OPTIMIZER_LOOKUP_PATHS, frozenset({"p"}))
        stash_on_context(ctx, DST_OPTIMIZER_STRICTNESS, "warn")
        clear_optimizer_context(ctx)
        assert get_context_value(ctx, DST_OPTIMIZER_PLAN) is None
        assert get_context_value(ctx, DST_OPTIMIZER_FK_ID_ELISIONS) is None
        assert get_context_value(ctx, DST_OPTIMIZER_PLANNED) is None
        assert get_context_value(ctx, DST_OPTIMIZER_LOOKUP_PATHS) is None
        assert get_context_value(ctx, DST_OPTIMIZER_STRICTNESS) is None


def test_clear_optimizer_context_clears_slots_mapping_via_item_delete() -> None:
    """``__slots__`` mapping stash (setattr fails -> ``__setitem__``) clears via ``del``."""

    class SlotsMapping:
        __slots__ = ("_data",)
        _data: dict[str, object]

        def __init__(self) -> None:
            object.__setattr__(self, "_data", {})

        def __getitem__(self, key: str) -> object:
            return self._data[key]

        def __setitem__(self, key: str, value: object) -> None:
            self._data[key] = value

        def __delitem__(self, key: str) -> None:
            del self._data[key]

    ctx = SlotsMapping()
    plan = object()
    stash_on_context(ctx, DST_OPTIMIZER_PLAN, plan)
    assert get_context_value(ctx, DST_OPTIMIZER_PLAN) is plan
    clear_optimizer_context(ctx)
    assert get_context_value(ctx, DST_OPTIMIZER_PLAN) is None


def test_clear_optimizer_context_none_and_frozen_are_noops() -> None:
    """``None`` and frozen mappings skip clear without raising."""
    clear_optimizer_context(None)
    clear_optimizer_context(MappingProxyType({"dst_optimizer_plan": object()}))


def test_clear_optimizer_context_locked_querydict_is_noop() -> None:
    """A locked ``QueryDict`` (immutable ``dict`` subclass) clears without raising.

    ``QueryDict`` subclasses ``dict``, so a ``.pop()``-based dict fast-path
    would satisfy ``isinstance(ctx, dict)`` and raise the immutable
    ``AttributeError`` uncaught. The guarded mapping-delete tail must swallow
    it - matching how ``stash_on_context`` tolerates the same object on write.
    """
    locked = QueryDict("dst_optimizer_plan=x")  # immutable by default
    assert not locked._mutable
    clear_optimizer_context(locked)  # must not raise
    assert "dst_optimizer_plan" in locked  # untouched (read-only)


def test_optimizer_context_all_exports() -> None:
    """All public constants and functions in ``optimizer/_context.py`` are listed in ``__all__``."""
    expected = {
        "DST_OPTIMIZER_FK_ID_ELISIONS",
        "DST_OPTIMIZER_KEYS",
        "DST_OPTIMIZER_LOOKUP_PATHS",
        "DST_OPTIMIZER_PLAN",
        "DST_OPTIMIZER_PLANNED",
        "DST_OPTIMIZER_STRICTNESS",
        "active_nested_strategy",
        "active_optimizer",
        "active_strictness",
        "begin_execution_frame",
        "cache_key_parts_memo",
        "clear_optimizer_context",
        "converted_selections_memo",
        "end_execution_frame",
        "execution_plan_memo",
        "fk_id_elision_keys",
        "get_context_value",
        "operation_publishes_to_context",
        "optimizer_value",
        "planned_resolver_keys",
        "publish_scoped_relations",
        "publish_window_cursor_states",
        "relation_is_optimizer_scoped",
        "stash_for_optimizer",
        "stash_on_context",
        "stashed_strictness",
        "window_cursor_state",
    }
    assert set(ctx_mod.__all__) == expected
    for name in expected:
        assert hasattr(ctx_mod, name)


@pytest.mark.parametrize(
    "stashed",
    [{"ItemType.category@allItems.category"}, frozenset({"ItemType.category@allItems.category"})],
    ids=["set", "frozenset"],
)
def test_stashed_key_sets_read_a_set_or_frozenset_stash_as_stashed(stashed: object) -> None:
    """A ``set`` or ``frozenset`` under either key-set stash is the set the accessor returns."""
    ctx = {DST_OPTIMIZER_PLANNED: stashed, DST_OPTIMIZER_FK_ID_ELISIONS: stashed}

    assert planned_resolver_keys(ctx) is stashed
    assert fk_id_elision_keys(ctx) is stashed


def test_stashed_key_sets_read_an_absent_stash_as_no_keys() -> None:
    """An absent stash plans nothing and elides nothing."""
    assert planned_resolver_keys({}) is None
    assert fk_id_elision_keys({}) == frozenset()


@pytest.mark.parametrize("key", [DST_OPTIMIZER_PLANNED, DST_OPTIMIZER_FK_ID_ELISIONS])
def test_stashed_key_sets_refuse_a_stash_that_is_not_a_set(key: str) -> None:
    """A key-set stash that is not a set raises rather than reading as no keys."""
    ctx: dict[str, object] = {key: ["ItemType.category@allItems.category"]}
    read = planned_resolver_keys if key == DST_OPTIMIZER_PLANNED else fk_id_elision_keys

    with pytest.raises(TypeError, match="expected the type the source guarantees, got list"):
        _ = read(ctx)


def test_stashed_strictness_reads_the_stashed_string_or_off_when_absent() -> None:
    """The stashed strictness string answers; an absent stash reads as ``"off"``."""
    assert stashed_strictness({DST_OPTIMIZER_STRICTNESS: "raise"}) == "raise"
    assert stashed_strictness({}) == "off"


def test_stashed_strictness_refuses_a_non_string_stash() -> None:
    """A strictness stash that is not a string raises rather than reading as ``"off"``."""
    with pytest.raises(TypeError, match="expected an instance of str, got int"):
        stashed_strictness({DST_OPTIMIZER_STRICTNESS: 1})


def test_publish_scoped_relations_handles_empty_and_generator_keys_when_active_and_inactive() -> (
    None
):
    """``publish_scoped_relations`` records nothing for empty keys and consumes generators."""
    # Inactive: no frame to record into
    publish_scoped_relations(set())
    publish_scoped_relations([])
    publish_scoped_relations(())

    # Active: iterables and generators are consumed
    frame = begin_execution_frame({}, nested=False)
    try:
        publish_scoped_relations(set())
        publish_scoped_relations([])
        publish_scoped_relations(["rel_a@Type"])
        publish_scoped_relations(x for x in ["rel_b@Type", "rel_c@Type"])
        assert relation_is_optimizer_scoped("rel_a@Type")
        assert relation_is_optimizer_scoped("rel_b@Type")
        assert relation_is_optimizer_scoped("rel_c@Type")
        assert not relation_is_optimizer_scoped("unplanned@Type")
    finally:
        end_execution_frame(frame)


def test_window_cursor_states_publish_read_and_clear_with_the_frame() -> None:
    """The frame carries each window's vocabulary by resolver key, for this execution only."""
    declared = declared_cursor_state_for_definition(make_definition(Issue, cursor_field=("id",)))
    other = declared_cursor_state_for_definition(make_definition(Issue, cursor_field=("-id",)))
    assert declared is not None
    assert other is not None
    # Inactive: nothing to record into and nothing to read.
    publish_window_cursor_states({"Root.kids@roots.kids": declared})
    assert window_cursor_state("Root.kids@roots.kids") is None

    scope = begin_execution_frame({}, nested=False)
    frame = scope.lease.held()
    assert frame is not None
    try:
        publish_window_cursor_states({"Root.kids@roots.kids": declared})
        publish_window_cursor_states({"Kid.kids@roots.kids.edges.node.kids": other})
        assert window_cursor_state("Root.kids@roots.kids") is declared
        assert window_cursor_state("Kid.kids@roots.kids.edges.node.kids") is other
        assert window_cursor_state("Root.other@roots.other") is None
    finally:
        end_execution_frame(scope)
    assert frame.window_cursor_states == {}
    assert window_cursor_state("Root.kids@roots.kids") is None


def test_relation_is_optimizer_scoped_unhashable_fail_closed() -> None:
    """``relation_is_optimizer_scoped`` fails closed (returns False) for unhashable objects."""
    # Inactive: returns False for unhashable shapes
    # basedpyright: the unhashable key is the hostile input under test;
    # relation_is_optimizer_scoped types the parameter as str
    assert not relation_is_optimizer_scoped({})  # pyright: ignore[reportArgumentType]
    assert not relation_is_optimizer_scoped([])  # pyright: ignore[reportArgumentType]

    # Active: still fail-closed (returns False rather than raising TypeError)
    frame = begin_execution_frame({}, nested=False)
    try:
        publish_scoped_relations({"valid@Type"})
        assert relation_is_optimizer_scoped("valid@Type")
        # basedpyright: the unhashable key is the hostile input under test;
        # relation_is_optimizer_scoped types the parameter as str
        assert not relation_is_optimizer_scoped({})  # pyright: ignore[reportArgumentType]
        assert not relation_is_optimizer_scoped([])  # pyright: ignore[reportArgumentType]
    finally:
        end_execution_frame(frame)


def test_strictness_and_scoped_relations_reentrant_isolation() -> None:
    """Re-entrant nested executions isolate strictness and scoped relations and restore cleanly."""
    outer = begin_execution_frame({}, nested=False, strictness="raise")
    try:
        publish_scoped_relations(["outer@Type"])
        assert active_strictness() == "raise"
        assert relation_is_optimizer_scoped("outer@Type")

        # Nested execution with different strictness and separate relations
        inner = begin_execution_frame({}, nested=False, strictness="warn")
        try:
            publish_scoped_relations(["inner@Type"])
            assert active_strictness() == "warn"
            assert relation_is_optimizer_scoped("inner@Type")
            assert not relation_is_optimizer_scoped("outer@Type")
        finally:
            end_execution_frame(inner)

        # Outer state restored
        assert active_strictness() == "raise"
        assert relation_is_optimizer_scoped("outer@Type")
        assert not relation_is_optimizer_scoped("inner@Type")
    finally:
        end_execution_frame(outer)

    assert active_strictness() is None
    assert not relation_is_optimizer_scoped("outer@Type")


@pytest.mark.asyncio
async def test_shared_singleton_answers_each_operation_with_its_own_context() -> None:
    """Two overlapping operations on one shared instance each see their own context.

    The documented ``extensions=[lambda: ext]`` form returns ONE instance to
    every operation, and Strawberry assigns ``execution_context`` on it before
    either operation's hooks start. Read from an attribute, both operations
    would answer with whichever assigned last - so the plan, the elisions and
    the clear would all land on one request's context object twice while the
    other's went untouched. Under ``DjangoSchema`` the assignment is a handoff
    and the answer comes from the state its runner bound for each operation.

    Both requests are held inside their own resolver until the other has
    started, so the overlap is a fact of the test rather than a scheduling
    hope.
    """
    extension = DjangoOptimizerExtension()
    started = 0
    overlapping = asyncio.Event()
    seen: dict[str, object] = {}

    @strawberry.type
    class Query:
        @strawberry.field
        async def probe(self, info: strawberry.Info[object, object]) -> str:
            nonlocal started
            started += 1
            if started == 2:
                overlapping.set()
            await asyncio.wait_for(overlapping.wait(), timeout=5)
            context = info.context
            assert is_object_dict(context)
            name = context["name"]
            assert isinstance(name, str)
            execution_context = extension.execution_context
            assert execution_context is not None
            seen[name] = read_attr(execution_context, "context")
            return name

    schema = DjangoSchema(query=Query, extensions=[lambda: extension])
    contexts = [{"name": "first"}, {"name": "second"}]
    results = await asyncio.gather(
        *(schema.execute("{ probe }", context_value=context) for context in contexts),
    )

    assert [result.errors for result in results] == [None, None]
    assert seen == {"first": contexts[0], "second": contexts[1]}
    assert seen["first"] is contexts[0]
    assert seen["second"] is contexts[1]


class _UnsettledOptimizer(DjangoOptimizerExtension):
    """An optimizer subclass the test builds without its constructor, so no record is settled."""


def test_a_resolver_cannot_rewrite_the_optimizer_configuration_for_a_later_request() -> None:
    """Strictness and the fetch strategy are settled at construction, not per request.

    The documented shape is a module-level singleton behind a factory, so this
    object is reachable from every resolver of every request for the life of the
    process. Written as attributes, one assignment inside one resolver would
    disarm a deployment's N+1 guard for all of them, and another would replace
    the strategy the instance's cached plans were keyed for.
    """
    extension = DjangoOptimizerExtension(strictness="raise")
    settled_strategy = extension.nested_connection_strategy

    for attempt in (
        lambda: setattr(extension, "strictness", "off"),
        lambda: extension.__dict__.update(strictness="off"),
        lambda: setattr(extension, "nested_connection_strategy", "windowed"),
        lambda: extension.__dict__.update(nested_connection_strategy="windowed"),
    ):
        with contextlib.suppress(AttributeError):
            attempt()

    assert extension.strictness == "raise"
    assert extension.nested_connection_strategy is settled_strategy


def test_an_optimizer_that_settled_no_configuration_reads_the_zero_argument_shape() -> None:
    """A record that was never settled answers as the construction that settles none.

    The strictness and the nested-connection strategy are read at the start of
    every execution, so the read cannot be the place a missing record surfaces;
    it answers with what ``DjangoOptimizerExtension()`` would have produced. Such
    an extension has no binding carrier either, so the operation it was installed
    for is refused before either value is spent
    (``tests/extensions/test_operation_state.py``).
    """
    # Built without ``__init__``, as a subclass that skipped ``super().__init__`` leaves it.
    extension = _UnsettledOptimizer.__new__(_UnsettledOptimizer)

    assert extension.strictness == "off"
    assert (
        extension.nested_connection_strategy
        == DjangoOptimizerExtension().nested_connection_strategy
    )


def _published_optimizer_keys(context: object) -> dict[str, object]:
    """Every optimizer stash currently readable off a request context object."""
    return {key: get_context_value(context, key) for key in DST_OPTIMIZER_KEYS}


@pytest.mark.django_db
def test_a_nested_operation_does_not_take_the_outer_operations_optimizer_state() -> None:
    """An inner execution through the documented singleton leaves the outer one intact.

    The optimizer publishes its plan, its FK-id elisions, its planned-relation
    keys and its strictness for the operation it is running. The request context
    object is the REQUEST's, not the operation's, and a resolver may hand its own
    ``info.context`` to an inner execution - whose start-of-execution clear then
    erases what the outer operation published and whose own publishes answer the
    outer resolvers that have not run yet.

    The inner document selects the FK by id alone, which is exactly the shape
    that publishes an elision key; the outer document then selects the whole
    related object through the same resolver key. Reading the shared object, the
    outer forward resolver would take the id-stub path and ``category.name``
    would come back empty.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    seen_contexts: list[ExecutionContext | None] = []
    seen_published: list[dict[str, object]] = []

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

        @strawberry.field
        def nest(self, info: strawberry.Info[object, object]) -> str:
            """Run a whole inner operation on this request's own context object."""
            before = extension.execution_context
            published_before = _published_optimizer_keys(info.context)
            inner = info.schema.execute_sync(
                "{ allItems { name category { id } } }",
                context_value=info.context,
            )
            assert inner.errors is None, inner.errors
            seen_contexts.extend((before, extension.execution_context))
            seen_published.extend((published_before, _published_optimizer_keys(info.context)))
            return "nested"

    finalize_django_types()
    extension = DjangoOptimizerExtension(strictness="raise")
    schema = DjangoSchema(query=Query, extensions=[lambda: extension])
    shared = SimpleNamespace()

    outer = schema.execute_sync(
        "{ nest allItems { name category { name } } }",
        context_value=shared,
    )

    assert outer.errors is None, outer.errors
    before, after = seen_contexts
    assert before is after
    assert after is not None
    assert after.query is not None
    assert after.query.startswith("{ nest")
    assert outer.data is not None
    assert all(_at(item, "category", "name") for item in _list_at(outer.data, "allItems"))

    # The request context object is the OUTER operation's introspection medium:
    # the inner execution neither erased what was on it nor published its own
    # plan and FK-id elisions there, and the outer operation's plan is what the
    # consumer can read off their request once it completes.
    published_before, published_after = seen_published
    assert published_after == published_before
    assert get_context_value(shared, DST_OPTIMIZER_PLAN) is not None

    # And the next independent request inherits nothing from either operation.
    fresh = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=SimpleNamespace(),
    )
    assert fresh.errors is None
    assert fresh.data is not None
    assert all(_at(item, "category", "name") for item in _list_at(fresh.data, "allItems"))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "consumer_first",
    [True, False],
    ids=["consumer-before-the-optimizer", "consumer-after-the-optimizer"],
)
def test_an_operation_started_from_a_consumer_teardown_leaves_the_request_its_plan(
    *,
    consumer_first: bool,
) -> None:
    """Whether an operation is nested is the runner's answer, not the hook order's.

    A consumer extension may run its own operation from its ``on_operation``
    teardown, which happens after the optimizer's executing hook has already
    reset everything it opened. An inner operation that decided it was outermost
    from what the optimizer had open would clear the request context and publish
    its own plan there - onto the object the consumer holding that request reads
    its plan, elisions and lookup paths off. The runner knows the whole
    lifetime, so the answer is the same whichever side of the optimizer the
    consumer entry is installed on.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    seen: dict[str, list[dict[str, object]]] = {}

    class _Nester(SchemaExtension):
        """A consumer extension that runs its own operation once, at teardown."""

        @override
        def on_operation(self) -> Iterator[None]:
            yield
            if seen:
                return
            context = read_attr(self.execution_context, "context")
            state = extension._operation_state()
            seen["published"] = [_published_optimizer_keys(context)]
            assert state is not None
            seen["stashes"] = [dict(state.stashes)]
            inner = self.execution_context.schema.execute_sync(
                "{ allItems { name category { id } } }",
                context_value=context,
            )
            assert inner.errors is None, inner.errors
            seen["published"].append(_published_optimizer_keys(context))
            seen["stashes"].append(dict(state.stashes))

    finalize_django_types()
    extension = DjangoOptimizerExtension(strictness="raise")
    entries = [_Nester, lambda: extension] if consumer_first else [lambda: extension, _Nester]
    schema = DjangoSchema(query=Query, extensions=entries)
    shared = SimpleNamespace()

    outer = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=shared,
    )

    assert outer.errors is None, outer.errors
    assert outer.data is not None
    assert all(_at(item, "category", "name") for item in _list_at(outer.data, "allItems"))
    published_before, published_after = seen["published"]
    stashes_before, stashes_after = seen["stashes"]
    assert published_after == published_before
    assert stashes_after == stashes_before
    assert get_context_value(shared, DST_OPTIMIZER_PLAN) is not None


@pytest.mark.django_db
def test_on_execute_clears_reused_context_fk_elisions_before_full_selection() -> None:
    """Reused ``context_value``: id-only elisions must not survive into a full selection.

    Without the ``on_execute`` clear, ``_stash_union`` retains the prior
    execution's FK-id elision key; the forward resolver then returns id-stubs
    and ``category.name`` resolves empty. Pinned end-to-end via real execute.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    shared = SimpleNamespace()

    r1 = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=shared,
    )
    assert r1.errors is None
    assert "ItemType.category@allItems.category" in _stashed_keys(
        shared,
        DST_OPTIMIZER_FK_ID_ELISIONS,
    )

    r2 = schema.execute_sync(
        "{ allItems { name category { id name } } }",
        context_value=shared,
    )
    assert r2.errors is None
    assert "ItemType.category@allItems.category" not in _stashed_keys(
        shared,
        DST_OPTIMIZER_FK_ID_ELISIONS,
    )
    assert r2.data is not None
    names = [_at(it, "category", "name") for it in _list_at(r2.data, "allItems")]
    assert all(n for n in names)


@pytest.mark.django_db
def test_on_execute_clears_reused_context_planned_keys_across_executions() -> None:
    """Reused ``context_value``: planned-resolver keys must not leak into a later op."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension(strictness="raise")
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    shared = SimpleNamespace()

    r1 = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=shared,
    )
    assert r1.errors is None
    assert "ItemType.category@allItems.category" in _stashed_keys(shared, DST_OPTIMIZER_PLANNED)

    r2 = schema.execute_sync(
        "{ allItems { name } }",
        context_value=shared,
    )
    assert r2.errors is None
    planned = getattr(shared, "dst_optimizer_planned", frozenset[str]())
    assert "ItemType.category@allItems.category" not in planned


@pytest.mark.django_db
def test_empty_plan_still_stashed() -> None:
    """B5/O5: even when no relations are selected, the scalar-only plan is stashed."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert plan.only_fields == ("name",)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()


# ---------------------------------------------------------------------------
# O5 - only() projection
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_applies_only_for_selected_scalars() -> None:
    """O5: selected scalar fields are collected into the stashed plan.

    Query count, JOIN-absence, and unused-column omission are live on
    ``test_library_api.py::test_scalar_only_branch_list_projects_name_without_a_join_or_unused_column``.
    This row keeps the plan-slot tuple a response cannot name.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "description")

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.all()

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = _stashed_plan(ctx)
    assert plan.only_fields == ("name",)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()


# ---------------------------------------------------------------------------
# O6 - get_queryset + Prefetch downgrade
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_downgrades_select_related_for_custom_get_queryset() -> None:
    """O6: custom target ``get_queryset`` downgrades forward FK traversal to ``Prefetch``.

    Two-query SQL is live in
    ``examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_selects_book_shelf_in_http_query``.
    This row keeps the plan slots (empty ``select_related``, one ``Prefetch``,
    uncacheable).
    """
    services.seed_data(1)
    calls: list[object] = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Category]:
            calls.append(info)
            return queryset

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert calls
    plan = _stashed_plan(ctx)
    assert plan.select_related == ()
    assert "category_id" in plan.only_fields
    assert "category__name" not in plan.only_fields
    assert plan.cacheable is False
    assert ext.cache_info().size == 0
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"


@pytest.mark.django_db
def test_optimizer_does_not_cache_custom_get_queryset_prefetch_plans() -> None:
    """O6: request-dependent ``Prefetch`` querysets are rebuilt instead of cached."""
    services.seed_data(1)
    calls: list[object] = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> QuerySet[Category]:
            calls.append(info)
            return queryset

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allItems { name category { name } } }"

    assert schema.execute_sync(query).errors is None
    assert schema.execute_sync(query).errors is None

    assert len(calls) == 2
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 0


# ---------------------------------------------------------------------------
# B8: queryset optimization diffing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_b8_consumer_select_related_does_not_mutate_cached_plan() -> None:
    """B8: a consumer's pre-applied ``select_related`` must not mutate B1's cached plan."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.select_related("category")

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])

    # First request warms the plan cache. B5 stashes the POST-diff plan
    # (consumer already applied ``select_related("category")``, so that
    # directive is empty on the introspection stash) while B1's cache keeps
    # the pre-diff plan.
    ctx1 = SimpleNamespace()
    result1 = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx1,
    )
    assert result1.errors is None
    assert _stashed_plan(ctx1).select_related == ()
    assert len(ext._plan_cache) == 1
    cached_plan = next(iter(ext._plan_cache.values()))
    assert cached_plan.select_related == ("category",)
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 1

    # Second request hits the cache. The cached plan must still carry
    # ["category"] - the diff must not have mutated it during request 1.
    ctx2 = SimpleNamespace()
    result2 = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx2,
    )
    assert result2.errors is None
    assert _stashed_plan(ctx2).select_related == ()
    assert next(iter(ext._plan_cache.values())) is cached_plan
    assert cached_plan.select_related == ("category",)
    assert ext.cache_info().hits == 1


@pytest.mark.django_db
def test_b8_consumer_prefetch_object_suppresses_optimizer_entry() -> None:
    """B8: a consumer ``Prefetch("items", queryset=Item.objects.all())`` keeps its slot."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    consumer_pf = Prefetch("items", queryset=Item.objects.all())
    captured: list[object] = []

    class _CaptureExt(DjangoOptimizerExtension):
        @override
        def _optimize(self, result: object, info: GraphQLResolveInfo) -> object:
            optimized = super()._optimize(result, info)
            captured.append(optimized)
            return optimized

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.prefetch_related(consumer_pf)

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    capture_ext = _CaptureExt()
    schema = strawberry.Schema(query=Query, extensions=[lambda: capture_ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # B5 stashes the POST-diff plan (publish runs after B8 reconciliation) so
    # introspection matches what was actually applied: consumer won, optimizer
    # ``items`` Prefetch is gone from the stashed directives.
    plan = _stashed_plan(ctx)
    assert [getattr(entry, "prefetch_to", entry) for entry in plan.prefetch_related] == []
    # The queryset that came out of ``_optimize`` carries exactly the
    # consumer's ``Prefetch`` - the optimizer entry was diffed away.
    optimized_qs = captured[0]
    assert isinstance(optimized_qs, QuerySet)
    lookups = queryset_prefetch_lookups(optimized_qs)
    assert lookups == (consumer_pf,)


# The two B8 behavior-only collision tests (descendant prefetch and
# exact-plus-descendant) live in the fakeshop suite:
# examples/fakeshop/test_query/test_library_api.py::
#   test_b8_consumer_descendant_prefetch_stays_flat_over_http and
#   test_b8_consumer_exact_plus_descendant_prefetch_stays_flat_over_http.
# Those run the real Genre -> books -> loans consumer prefetch through /graphql/
# and add HTTP + flat-query-count pressure the synthetic in-process schema could
# not. The plan/diff-asserting B8 tests below stay package-internal (they inspect
# the optimized queryset's _prefetch_related_lookups, which HTTP cannot expose).


@pytest.mark.django_db
def test_b8_consumer_plain_string_upgraded_to_optimizer_prefetch() -> None:
    """B8: a consumer's plain ``"items"`` string is replaced by the optimizer's nested ``Prefetch``."""
    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    assert registry.get(Entry) is EntryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "entries")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    captured: list[object] = []

    class _CaptureExt(DjangoOptimizerExtension):
        @override
        def _optimize(self, result: object, info: GraphQLResolveInfo) -> object:
            optimized = super()._optimize(result, info)
            captured.append(optimized)
            return optimized

    @strawberry.type
    class Query:
        def _all_categories(self) -> QuerySet[Category]:
            return Category.objects.prefetch_related("items")

        all_categories: QuerySet[Category] = strawberry.field(
            resolver=_all_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    capture_ext = _CaptureExt()
    schema = strawberry.Schema(query=Query, extensions=[lambda: capture_ext])
    result = schema.execute_sync(
        "{ allCategories { name items { name entries { value } } } }",
    )
    assert result.errors is None
    optimized_qs = captured[0]
    assert isinstance(optimized_qs, QuerySet)
    lookups = queryset_prefetch_lookups(optimized_qs)
    # Exactly one ``items`` lookup - the optimizer's ``Prefetch`` -
    # carrying the nested ``entries`` chain. The consumer's plain
    # ``"items"`` string was stripped.
    assert len(lookups) == 1
    items_pf = lookups[0]
    assert isinstance(items_pf, Prefetch)
    assert items_pf.prefetch_to == "items"
    assert items_pf.queryset is not None
    nested = queryset_prefetch_lookups(items_pf.queryset)
    assert any(getattr(entry, "prefetch_to", entry) == "entries" for entry in nested)


# ---------------------------------------------------------------------------
# Construction surface - unknown kwargs raise loudly
# ---------------------------------------------------------------------------


def test_extension_rejects_unknown_kwargs_at_construction() -> None:
    """Misspelled config (e.g. ``strict=`` instead of ``strictness=``) raises TypeError."""
    with pytest.raises(TypeError):
        # basedpyright: a deliberately misspelled keyword; the test proves construction rejects it
        DjangoOptimizerExtension(strict=True)  # pyright: ignore[reportCallIssue]


def test_extension_accepts_strawberry_execution_context_kwarg() -> None:
    """Strawberry instantiates extension *classes* with ``execution_context=...``.

    When the *class* (not an instance) is registered, Strawberry calls
    ``ext(execution_context=None)`` internally to build the per-request instance.
    The extension must accept that keyword without ``TypeError``.
    """
    ext = DjangoOptimizerExtension(execution_context=None)
    assert ext.strictness == "off"


def test_singleton_factory_extensions_form_emits_no_deprecation_warning() -> None:
    """The migrated ``extensions=[lambda: _optimizer]`` form does not warn.

    Strawberry's ``Schema.__init__`` emits a ``DeprecationWarning``
    when an extension *instance* is passed in ``extensions=[...]``. The
    singleton-factory form passes a *callable*, so no such warning fires.
    ``simplefilter("always")`` is set inside the context so a warning that
    Strawberry already emitted-and-deduped earlier in the process cannot
    produce a false green. Pins the spec-029 no-instance-form-warning contract.
    """

    @strawberry.type
    class Query:
        hello: str

    _optimizer = DjangoOptimizerExtension()
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        strawberry.Schema(query=Query, extensions=[lambda: _optimizer])

    instance_form_warnings = [
        w
        for w in recorded
        if issubclass(w.category, DeprecationWarning) and "instance" in str(w.message)
    ]
    assert instance_form_warnings == []


# ---------------------------------------------------------------------------
# hint_is_skip - centralised hint-shape dispatch
# ---------------------------------------------------------------------------


def test_hint_is_skip_handles_sentinel_record_and_unknown_shapes() -> None:
    """``hint_is_skip`` returns the documented bool for every supported shape."""
    assert hint_is_skip(None) is False
    assert hint_is_skip(OptimizerHint.SKIP) is True
    assert hint_is_skip(OptimizerHint(skip=True)) is True
    assert hint_is_skip(OptimizerHint.select_related()) is False
    # Unknown shape with no ``.skip`` attribute must not raise - the
    # schema audit's "never raises" contract depends on this.
    # basedpyright: the unknown hint shape is the hostile input under test; hint_is_skip types
    # the parameter as OptimizerHint | None
    assert hint_is_skip(object()) is False  # pyright: ignore[reportArgumentType]


# ---------------------------------------------------------------------------
# Plan-cache origin separation + multi-type audit dedupe
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model() -> None:
    """A primary-return resolver and a secondary-return resolver do not collide.

    Two root fields on the same schema return ``list[ItemType]`` and
    ``list[AdminItemType]`` respectively. Both target ``Item`` but
    carry different origin types, so the plan cache must hold two
    distinct entries. Without the origin component of the cache key
    the two queries would share one cached plan keyed by ``Item``
    alone.
    """
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

        def _all_admin_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_admin_items: QuerySet[Item] = strawberry.field(
            resolver=_all_admin_items,
            graphql_type=list[AdminItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    # Run the same selection through both root fields. Same response shape
    # so doc_key + relevant_vars + target_model agree; only response_path
    # and origin differ. With the new cache key both fields produce
    # distinct entries.
    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allAdminItems { name } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


def test_schema_audit_warns_on_relation_field_exposed_only_on_secondary_type() -> None:
    """A relation field only present on a secondary still surfaces a warning.

    ``ItemType`` (primary) excludes ``category``; ``AdminItemType``
    (secondary) includes ``category`` with an unregistered target. The
    audit must walk every reachable type so the secondary's relation is
    audited and the missing-target warning is produced. Switching to a
    primary-only iterator would silently drop this warning.
    """

    # Register CategoryType first so AdminItemType.category can resolve
    # during __init_subclass__, then clear it before check_schema runs.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[ItemType])
    # Clear Category's registration so the audit sees the gap.
    _force_unregister_after_finalize(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    # Item.category is the secondary-only relation; the audit must surface it.
    assert any("Item.category" in w and "no registered target" in w for w in warnings)


def test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types() -> None:
    """Identical (source_model, field_name) warnings collapse to one.

    Both ``ItemType`` (primary) and ``AdminItemType`` (secondary) expose
    ``category`` whose target ``Category`` has no registered
    ``DjangoType``. Without dedupe, ``registry.iter_types()`` (one
    yield per registered type) would produce two identical warnings.
    """

    # Register CategoryType so the type declarations succeed, then drop
    # its registration before check_schema runs.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    _force_unregister_after_finalize(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    item_category_warnings = [w for w in warnings if "Item.category" in w]
    assert len(item_category_warnings) == 1


def test_schema_audit_warning_names_the_source_type_for_multi_type_models() -> None:
    """B6: the warning text includes ``type_cls.__name__`` for multi-type models.

    Per-source-model dedupe collapses warnings to one per ``(model, field_name)``
    even when two registered types for the same model expose the same relation.
    The warning string must still identify *which* type's audit produced the
    entry so a consumer can disambiguate; the source type's name is rendered
    alongside ``model.field`` so the dedupe artifact never loses provenance.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    _force_unregister_after_finalize(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    item_category_warnings = [w for w in warnings if "Item.category" in w]
    # Dedupe still applies - one warning per (model, field_name).
    assert len(item_category_warnings) == 1
    # The surviving warning must name the source type (the first one iterated)
    # so the consumer can identify which type's audit produced the entry.
    [warning] = item_category_warnings
    assert "ItemType" in warning or "AdminItemType" in warning


def test_model_for_type_reverse_lookup_works_for_secondary_type() -> None:
    """Secondary types remain discoverable for the optimizer's reverse lookup.

    Both ``ItemType`` and ``AdminItemType`` are registered against
    ``Item``; ``registry.model_for_type`` returns the same ``Item`` for
    either origin. The optimizer's ``_resolve_model_from_return_type``
    composition surfaces both legs of the pair: ``origin`` is the
    secondary, ``model`` is the underlying Django model.
    """

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.model_for_type(AdminItemType) is Item

    @strawberry.type
    class Query:
        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[ItemType])
    inner = schema._schema.type_map["AdminItemType"]
    assert isinstance(inner, GraphQLObjectType)
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))
    info = make_info()._raw_info._replace(return_type=wrapped, schema=schema._schema)
    resolved = _resolve_model_from_return_type(info)
    assert resolved is not None
    assert resolved.origin is AdminItemType
    assert resolved.model is Item


# ---------------------------------------------------------------------------
# ``apply_connection_optimization`` and the shared ``apply_to`` core
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimize_delegates_to_the_shared_apply_to_core(monkeypatch: pytest.MonkeyPatch) -> None:
    """The middleware path builds and applies its plan through the shared ``apply_to`` core.

    Per spec-030 Decision 11 the plan-build-and-apply tail lives in
    ``DjangoOptimizerExtension.apply_to`` (shared with the connection field's
    ``apply_connection_optimization``). The B1-B8 suite in this module
    is the broad guard; this focused test pins that a non-connection
    root field still has its plan built and applied (``select_related`` lands)
    and that ``_optimize`` delegates to ``apply_to``.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension(strictness="raise")
    delegations: list[tuple[object, ...]] = []
    real_apply_to = ext.apply_to

    def _spy_apply_to(
        target_type: type[DjangoType] | None,
        target_model: type[Model],
        queryset: QuerySet[Model],
        info: GraphQLResolveInfo,
    ) -> QuerySet[Model]:
        delegations.append((target_type, target_model))
        return real_apply_to(target_type, target_model, queryset, info)

    monkeypatch.setattr(ext, "apply_to", _spy_apply_to)

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allItems { category { name } } }", context_value=ctx)

    assert result.errors is None
    # The plan was built and applied on the middleware path (the forward FK is
    # select_related-ed).
    assert _stashed_plan(ctx).select_related == ("category",)
    # ``_optimize`` delegated to ``apply_to`` with the resolved (origin, model),
    # NOT inferred inside the helper.
    assert delegations == [(ItemType, Item)]


@pytest.mark.django_db
def test_apply_connection_optimization_uses_active_optimizer_cache() -> None:
    """``apply_connection_optimization`` shares the active extension's plan cache.

    spec-030 Decision 11 plan-cache-reuse route: ``on_execute`` publishes the
    active extension on the execution frame; the connection helper discovers it
    so connection-field plans hit the SAME instance-bound cache the middleware
    uses (rather than a throwaway cache-less extension).
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()
    captured: dict[str, object] = {}

    @strawberry.type
    class Query:
        def _all_items(self, info: strawberry.Info[object, object]) -> QuerySet[Item]:
            # Inside a resolver the ``on_execute`` lifecycle has published the
            # active extension; the helper must discover it (not build a
            # throwaway). Apply twice so the second call is a cache hit on the
            # SAME instance.
            qs = Item.objects.all()
            apply_connection_optimization(ItemType, qs, info)
            captured["active"] = _active_optimizer()
            return qs

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    result = schema.execute_sync("{ allItems { id } }")
    assert result.errors is None
    # The helper saw the installed extension instance through the frame.
    assert captured["active"] is ext


def test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets() -> None:
    """A nested fallback publish UNIONS the correctness sentinels, never overwrites them.

    spec-033 Decision 8 foundation: a nested fallback connection pipeline is a
    real optimizer run that re-enters ``_publish_plan_to_context`` per parent.
    Its publish must not shrink the parent plan's planned / FK-id-elision /
    lookup-path sets - especially under ``"warn"``, where execution continues
    after the nested connection returns. ``DST_OPTIMIZER_PLAN`` stays last-wins
    introspection (not unioned).
    """
    ext = DjangoOptimizerExtension(strictness="warn")
    parent_plan = OptimizationPlan(
        select_related=["category"],
        fk_id_elisions=["ItemType.category@allItems.category"],
        planned_resolver_keys=["ItemType.category@allItems.category"],
    ).finalize()
    nested_plan = OptimizationPlan(
        prefetch_related=["entries"],
        fk_id_elisions=["EntryType.property@allItems.entries.property"],
        planned_resolver_keys=["EntryType.property@allItems.entries.property"],
    ).finalize()
    ctx = SimpleNamespace()

    ext._publish_plan_to_context(parent_plan, make_info(context=ctx)._raw_info)
    # The nested publish (a fallback pipeline re-entry) unions into the parent's stash.
    ext._publish_plan_to_context(nested_plan, make_info(context=ctx)._raw_info)

    # The parent's resolver key + FK-id elision survive the nested publish.
    assert _stashed_keys(ctx, DST_OPTIMIZER_PLANNED) == frozenset(
        {"ItemType.category@allItems.category", "EntryType.property@allItems.entries.property"},
    )
    assert _stashed_keys(ctx, DST_OPTIMIZER_FK_ID_ELISIONS) == frozenset(
        {"ItemType.category@allItems.category", "EntryType.property@allItems.entries.property"},
    )
    # Lookup paths union too (parent "category" + nested "entries").
    assert {"category", "entries"} <= _stashed_keys(ctx, DST_OPTIMIZER_LOOKUP_PATHS)
    # DST_OPTIMIZER_PLAN stays last-wins introspection data (not unioned).
    assert _stashed_plan(ctx) is nested_plan


def test_publish_plan_to_context_union_tolerates_non_set_existing_stash() -> None:
    """``_stash_union`` overwrites a non-set existing stash defensively (no crash)."""
    ctx = SimpleNamespace()
    # Pre-seed a non-set value under the planned key (defensive shape).
    DjangoOptimizerExtension._stash_union(ctx, "dst_optimizer_planned", frozenset({"a"}))
    # Existing is a frozenset -> union.
    DjangoOptimizerExtension._stash_union(ctx, "dst_optimizer_planned", frozenset({"b"}))
    assert get_context_value(ctx, "dst_optimizer_planned") == frozenset({"a", "b"})
    # A non-set existing value is overwritten rather than crashing the union.
    ctx.dst_optimizer_planned = "not-a-set"
    DjangoOptimizerExtension._stash_union(ctx, "dst_optimizer_planned", frozenset({"c"}))
    assert get_context_value(ctx, "dst_optimizer_planned") == frozenset({"c"})


def _is_resolver_key_set(value: object) -> TypeGuard[frozenset[str]]:
    """Whether ``value`` is the frozenset of resolver keys the optimizer publishes."""
    return isinstance(value, frozenset) and all(isinstance(key, str) for key in value)


@pytest.mark.django_db
def test_nested_connection_fallback_publish_unions_parent_planned_set_end_to_end() -> None:
    """End-to-end: a real nested-connection fallback publish UNIONS, never clobbers.

    spec-033 Decision 8: the unit pin
    (``test_publish_plan_to_context_unions_parent_and_nested_sentinel_sets``)
    proves the helper unions; THIS pins the union holds through an actual nested
    -connection-fallback EXECUTION - the scenario that motivates the union. A
    sidecar-filtered ``itemsConnection(filter:)`` is a Decision-6 fallback: its
    per-parent pipeline is a real optimizer run that re-publishes, but the
    parent's planned ``items`` list-sibling resolver key must survive on the
    shared context (otherwise a planned sibling would spuriously strictness-flag
    after the nested connection returned).
    """
    services.seed_data(1)

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact"]}

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            filterset_class = ItemFilter

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)
            # The test needs BOTH surfaces on one relation: the raw ``items``
            # list sibling whose planned key must survive, and the
            # ``itemsConnection`` sidecar fallback that re-publishes. The
            # package default emits the connection alone.
            relation_shapes = {"items": "both"}

    finalize_django_types()

    @strawberry.type
    class Query:
        objs: list[CategoryType] = DjangoListField(CategoryType)

    ext = DjangoOptimizerExtension(strictness="warn")
    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        extensions=[lambda: ext],
    )
    # An ``HttpRequest`` context: the sidecar filter pipeline needs a resolvable
    # request, and the optimizer stashes its sentinels onto the same object
    # (read back via ``get_context_value``). Warn mode so execution continues and
    # the post-return context can be inspected.
    ctx = HttpRequest()
    # ``items`` is the planned reverse-FK list sibling; ``itemsConnection(filter:)``
    # is the sidecar fallback (a real per-parent optimizer publish).
    result = schema.execute_sync(
        "{ objs { items { name } "
        '  itemsConnection(filter: { name: { exact: "nope" } }) '
        "{ edges { node { name } } } } }",
        context_value=ctx,
    )
    assert result.errors is None, result.errors
    planned = get_context_value(ctx, DST_OPTIMIZER_PLANNED, frozenset[str]())
    assert _is_resolver_key_set(planned)
    # The parent's planned ``items`` resolver key survives the nested fallback's
    # publish (the union foundation) - it is NOT shrunk away.
    assert any(key.startswith("CategoryType.items@") for key in planned), planned
    # The sidecar fallback connection was left unplanned (Decision 6): no planned
    # key for the ``items`` relation keyed under the connection's runtime path.
    assert not any("@objs.itemsConnection" in key for key in planned), planned


# =============================================================================
# Cascade <-> optimizer cooperation pins (spec-034). No optimizer source change is
# involved: a type whose get_queryset CASCADES is, to the optimizer, just a type
# with a custom hook, so the shipped rules fire unchanged (spec-034 Decision 7).
# =============================================================================


@pytest.mark.django_db
def test_cascading_target_downgrades_join_to_prefetch() -> None:
    """A relation whose target hook cascades plans a ``Prefetch`` (not ``select_related``).

    The target reports ``has_custom_get_queryset() is True``, so the shipped
    ``optimizer/walker.py::_target_has_custom_get_queryset`` rule fires the
    downgrade and bakes the cascade into the child queryset - no optimizer change.
    ``select_related`` is empty, the relation plans one ``Prefetch``, and the plan
    is ``cacheable is False``.

    LOAD-BEARING (spec-034 Decision 12 dependency to protect): the assertion that
    the prefetch CHILD queryset narrows by the LIVE request user, not merely that
    a ``Prefetch`` is planned. ``walker.py::_build_child_queryset`` hands the
    target hook an ``Info`` over the root walk's own resolve info; a future refactor that
    dropped ``info`` would still plan a ``Prefetch`` while silently breaking
    cascade transitivity (the nested hook would lose ``info.context.user``). The
    cascading hook here both (a) cascades via ``apply_cascade_permissions`` AND
    (b) narrows by a user-derived predicate, so the child SQL carries the live
    user's value - a non-distinguishing ``Prefetch``-only assertion cannot pass.
    """
    seen_users: list[object] = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: strawberry.Info[object, object],
            **kwargs: object,
        ) -> QuerySet[Category]:
            user = read_attr(info.context, "user", None)
            seen_users.append(user)
            # Cascade AND narrow by a user-derived predicate so the live request
            # user reaches the prefetch child queryset's compiled SQL.
            assert user is not None
            queryset = queryset.filter(name=read_attr(user, "name"))
            return apply_cascade_permissions(cls, queryset, info)

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    # One public category whose name matches the request user, one item under it.
    request_cat = Category.objects.create(name="request_user", is_private=False)
    Item.objects.create(name="i0", category=request_cat)

    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    request_user = SimpleNamespace(name="request_user")
    ctx = SimpleNamespace(user=request_user)

    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None

    plan = _stashed_plan(ctx)
    assert plan.select_related == ()
    assert plan.cacheable is False
    assert ext.cache_info().size == 0
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"

    # Load-bearing: the cascading hook saw the LIVE request user...
    assert seen_users
    assert seen_users[0] is request_user
    # ...and that user's narrowing is baked into the prefetch child queryset's SQL
    # (proving ``_build_child_queryset`` threaded the live ``info``, not a default).
    child_queryset = plan.prefetch_related[0].queryset
    assert child_queryset is not None
    child_sql = str(child_queryset.query)
    assert "request_user" in child_sql


@pytest.mark.django_db
def test_plan_with_cascading_hook_uncacheable() -> None:
    """A plan baking a cascading hook is ``cacheable = False``; B1 counters unaffected otherwise.

    The shipped rule marks ANY plan baking a custom ``get_queryset`` uncacheable
    (it keys on the *presence* of a custom hook, not on whether the hook reads the
    request - the coarser walker.py rule); the cascade adds no new cache dimension.
    So executing a cascading query twice records ``misses == 2 / hits == 0 /
    size == 0`` - the plan is rebuilt each request (spec-034 Edge case
    "Plan-cache interaction").

    The non-cascading half pins that this uncacheability does NOT contaminate
    ordinary plan caching: a SIBLING non-cascading schema run twice on its own
    extension produces the normal ``miss-then-hit`` (``size == 1``, B1 counters
    unaffected for non-cascading types). Separate extension instances keep the two
    counter streams independently observable.
    """
    public_cat = Category.objects.create(name="public_cat", is_private=False)
    Item.objects.create(name="pub_item", category=public_cat)

    # --- Cascading schema: plan is uncacheable, rebuilt each request. ---
    class CascadingCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: QuerySet[Category],
            info: strawberry.Info,
            **kwargs: object,
        ) -> QuerySet[Category]:
            return apply_cascade_permissions(cls, queryset.filter(is_private=False), info)

    assert registry.get(Category) is CascadingCategoryType

    class CascadingItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    cascading_ext = DjangoOptimizerExtension()

    @strawberry.type
    class CascadingQuery:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[CascadingItemType],
        )

    finalize_django_types()
    cascading_schema = strawberry.Schema(
        query=CascadingQuery,
        extensions=[lambda: cascading_ext],
    )
    query = "{ allItems { name category { name } } }"
    ctx_a = SimpleNamespace(user=None)
    ctx_b = SimpleNamespace(user=None)
    assert cascading_schema.execute_sync(query, context_value=ctx_a).errors is None
    assert cascading_schema.execute_sync(query, context_value=ctx_b).errors is None

    assert _stashed_plan(ctx_a).cacheable is False
    assert cascading_ext.cache_info().hits == 0
    assert cascading_ext.cache_info().misses == 2
    assert cascading_ext.cache_info().size == 0

    # --- Non-cascading sibling: ordinary caching is unaffected (miss then hit). ---
    registry.clear()

    class PlainCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is PlainCategoryType

    class PlainItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    plain_ext = DjangoOptimizerExtension()

    @strawberry.type
    class PlainQuery:
        def _all_items(self) -> QuerySet[Item]:
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[PlainItemType],
        )

    finalize_django_types()
    plain_schema = strawberry.Schema(query=PlainQuery, extensions=[lambda: plain_ext])
    assert plain_schema.execute_sync(query).errors is None
    assert plain_ext.cache_info().misses == 1
    assert plain_ext.cache_info().hits == 0

    assert plain_schema.execute_sync(query).errors is None
    assert plain_ext.cache_info().hits == 1
    assert plain_ext.cache_info().misses == 1
    assert plain_ext.cache_info().size == 1


# TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card): add
# the strictness no-false-fire package pin here if it needs real extension execution rather than
# pure walker inspection. The test is named in spec-035's G3 deferred test plan; the narrowing it
# exercises is spec-035 Decision 6, unreachable until that card builds the abstract-return
# production-entry contract (R1).
# Pseudocode: execute an abstract/interface-shaped query whose sibling fragment
# is correctly narrowed; assert strictness ``warn`` emits no optimizer warning
# and strictness ``raise`` returns no "Unplanned N+1" GraphQL error for the
# sibling branch the resolver never runs.


@pytest.mark.django_db
def test_consumer_projection_widens_to_the_selection_and_keeps_the_join() -> None:
    """A consumer ``.only()`` and the plan's projection load as one union.

    ``select_related("category")`` over a consumer ``.only("name")`` is
    written with the connector and the selection's columns added to the
    consumer's, so the JOIN compiles and nothing lazy-loads per row: under
    ``strictness="raise"`` both the projected and the plain resolver stay
    silent, and each answers in one query.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        def _projected_items(self) -> QuerySet[Item]:
            return Item.objects.order_by("id").only("name")

        projected_items: QuerySet[Item] = strawberry.field(
            resolver=_projected_items,
            graphql_type=list[ItemType],
        )

        def _planned_items(self) -> QuerySet[Item]:
            return Item.objects.order_by("id")

        planned_items: QuerySet[Item] = strawberry.field(
            resolver=_planned_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension(strictness="raise")
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: optimizer],
    )
    # Strictness sentinels stash on the context: execution needs a real
    # context object (the standing strictness-test convention).
    with CaptureQueriesContext(connection) as captured:
        projected = schema.execute_sync(
            "{ projectedItems { name category { name } } }",
            context_value=SimpleNamespace(),
        )
    assert projected.errors is None, projected.errors
    assert len(captured) == 1
    assert 'JOIN "products_category"' in captured[0]["sql"]

    planned = schema.execute_sync(
        "{ plannedItems { name category { name } } }",
        context_value=SimpleNamespace(),
    )
    assert planned.errors is None, planned.errors


@pytest.mark.django_db
def test_b8_consumer_wins_prefetch_nested_keys_stay_strictness_visible() -> None:
    """B8 + B3: consumer-wins Prefetch drop must not mask nested N+1 under raise.

    When the root resolver already carries ``Prefetch("items", queryset=...)``,
    B8 drops the optimizer's richer nested Prefetch (consumer wins) but must
    ALSO strip the nested ``entries`` planned-resolver keys before publishing
    strictness sentinels. Publishing the pre-diff plan left ``entries`` marked
    planned while every item row lazy-loaded it.
    """
    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    assert registry.get(Entry) is EntryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "entries")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        def _objs(self) -> QuerySet[Category]:
            return Category.objects.all().prefetch_related(
                Prefetch("items", queryset=Item.objects.filter(is_private=False)),
            )

        objs: QuerySet[Category] = strawberry.field(
            resolver=_objs,
            graphql_type=list[CategoryType],
        )

        def _planned_objs(self) -> QuerySet[Category]:
            return Category.objects.all()

        planned_objs: QuerySet[Category] = strawberry.field(
            resolver=_planned_objs,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension(strictness="raise")
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: optimizer],
    )
    consumer_wins = schema.execute_sync(
        "{ objs { name items { name entries { value } } } }",
        context_value=SimpleNamespace(),
    )
    assert consumer_wins.errors is not None
    assert any(
        "Unplanned N+1" in str(error) and "entries" in str(error) for error in consumer_wins.errors
    )

    planned = schema.execute_sync(
        "{ plannedObjs { name items { name entries { value } } } }",
        context_value=SimpleNamespace(),
    )
    assert planned.errors is None, planned.errors


@pytest.mark.django_db
def test_b8_consumer_wins_prefetch_preserves_nested_fk_id_elision() -> None:
    """B8 + FK-id elision: a consumer-wins Prefetch drop must PRESERVE nested elisions.

    A nested ``{ category { id } }`` selection under a consumer-won ``items``
    prefetch is an FK-id elision - it reads ``item.category_id`` off the
    already-materialised item row and issues no query. It must therefore
    survive the drop and NOT be reported as an unplanned N+1 under
    ``strictness="raise"``: the nested elision keys are kept when the Prefetch
    is dropped, so the elided relation is not flagged.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    assert registry.get(Item) is ItemType

    @strawberry.type
    class Query:
        def _objs(self) -> QuerySet[Category]:
            return Category.objects.all().prefetch_related(
                Prefetch("items", queryset=Item.objects.filter(is_private=False)),
            )

        objs: QuerySet[Category] = strawberry.field(
            resolver=_objs,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension(strictness="raise")
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: optimizer],
    )
    result = schema.execute_sync(
        "{ objs { name items { name category { id } } } }",
        context_value=SimpleNamespace(),
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    ids = [
        _at(item, "category", "id")
        for obj in _list_at(result.data, "objs")
        for item in _list_at(obj, "items")
    ]
    assert all(cid for cid in ids)


# B3 strictness reachability: ``_check_n1`` consults the in-force strictness
# BEFORE it decides to stay silent. Gating on the ``DST_OPTIMIZER_PLANNED`` stash
# alone left an armed guard silently disarmed for three shapes - an execution with
# no stashable context, an operation whose root the walker cannot plan, and an
# async execution where Django's sync gate fires first.


@pytest.mark.django_db
def test_strictness_reaches_an_execution_with_no_stashable_context() -> None:
    """B3: an armed guard fires without a ``context_value`` to stash on.

    The strictness sentinel rides a request-context stash, which an execution
    given ``None`` - or no ``context_value`` argument at all - cannot carry. The
    guard belongs to the running extension, not to the context shape, so every
    execution of the same unplanned relation reports the same N+1.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.SKIP}

    @strawberry.type
    class Query:
        def _projected_items(self) -> QuerySet[Item]:
            return Item.objects.order_by("id").only("name")

        projected_items: QuerySet[Item] = strawberry.field(
            resolver=_projected_items,
            graphql_type=list[ItemType],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension(strictness="raise")
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: optimizer],
    )
    query = "{ projectedItems { name category { name } } }"

    stashable = schema.execute_sync(query, context_value=SimpleNamespace())
    assert stashable.errors is not None
    assert any("Unplanned N+1: category" in str(error) for error in stashable.errors)

    none_context = schema.execute_sync(query, context_value=None)
    assert none_context.errors is not None
    assert any("Unplanned N+1: category" in str(error) for error in none_context.errors)

    bare = schema.execute_sync(query)
    assert bare.errors is not None
    assert any("Unplanned N+1: category" in str(error) for error in bare.errors)


@pytest.mark.django_db
def test_strictness_flags_a_relation_under_an_unplannable_root() -> None:
    """B3: a root the walker cannot plan leaves every relation strictness-visible.

    A resolver returning a materialized ``list`` gives the walker no queryset to
    rewrite, so the operation publishes no planned-resolver keys at all. That is
    the case the guard exists to report - every parent row lazy-loads - not a
    reason to treat the relation as satisfied. ``strictness="off"`` on the same
    schema stays silent and serves the rows.
    """
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        def _categories(self) -> list[Category]:
            return list(Category.objects.order_by("id"))

        categories: list[Category] = strawberry.field(
            resolver=_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    query = "{ categories { name items { name } } }"

    raising_optimizer = DjangoOptimizerExtension(strictness="raise")
    raising = strawberry.Schema(
        query=Query,
        extensions=[lambda: raising_optimizer],
    )
    flagged = raising.execute_sync(query, context_value=SimpleNamespace())
    assert flagged.errors is not None
    assert any("Unplanned N+1: items" in str(error) for error in flagged.errors)

    silent_optimizer = DjangoOptimizerExtension(strictness="off")
    silent = strawberry.Schema(
        query=Query,
        extensions=[lambda: silent_optimizer],
    )
    served = silent.execute_sync(query, context_value=SimpleNamespace())
    assert served.errors is None, served.errors
    assert served.data is not None
    assert served.data["categories"]


@pytest.mark.django_db(transaction=True)
async def test_strictness_flags_an_unplanned_relation_before_the_async_sync_gate() -> None:
    """B3: the guard speaks before Django's ``SynchronousOnlyOperation``.

    A many-side lazy load inside an async execution trips Django's sync-only gate,
    which surfaces to the consumer as an opaque "cannot call this from an async
    context" rather than as the actionable unplanned-relation report. The N+1
    probe reads only the instance cache (never the database), so an armed guard
    reaches the relation first and names it.
    """
    await sync_to_async(services.seed_data)(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.get(Item) is ItemType

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        async def _categories(self) -> list[Category]:
            return [obj async for obj in Category.objects.order_by("id")]

        categories: list[Category] = strawberry.field(
            resolver=_categories,
            graphql_type=list[CategoryType],
        )

    finalize_django_types()
    optimizer = DjangoOptimizerExtension(strictness="raise")
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: optimizer],
    )
    result = await schema.execute(
        "{ categories { name items { name } } }",
        context_value=SimpleNamespace(),
    )
    assert result.errors is not None
    messages = [str(error) for error in result.errors]
    assert any("Unplanned N+1: items" in message for message in messages)
    assert not any("async context" in message for message in messages)


def test_optimizer_unadapted_non_queryset_passthrough() -> None:
    """Non-queryset results pass through ``_optimize`` unadapted.

    Wire cost of a list-returning root with the optimizer installed is
    ``examples/fakeshop/test_query/test_products_visibility_api.py::test_nested_connection_still_costs_one_query_per_parent_when_the_optimizer_gets_a_list``.
    """
    ext = DjangoOptimizerExtension()
    non_qs_result = ext._optimize([1, 2, 3], _as_partial_resolve_info(SimpleNamespace()))
    assert non_qs_result == [1, 2, 3]
    assert not unwrap_async_queryset_adapter(non_qs_result)[1]


def test_optimizer_preserves_async_adapter_evaluated_cache() -> None:
    """Evaluated queryset with adapter returns re-wrapped adapter."""
    ext = DjangoOptimizerExtension()
    qs_eval = Category.objects.all()
    qs_eval._result_cache = []
    adapted_eval = wrap_async_queryset_adapter(qs_eval)
    assert unwrap_async_queryset_adapter(adapted_eval)[1]
    eval_res = ext._optimize(adapted_eval, _as_partial_resolve_info(SimpleNamespace()))
    assert unwrap_async_queryset_adapter(eval_res)[1]
    assert isinstance(eval_res, _AsyncQuerySetRows)
    assert eval_res._queryset is qs_eval


def test_optimizer_preserves_async_adapter_unresolved_type() -> None:
    """Unresolved return type with adapter returns re-wrapped adapter."""
    ext = DjangoOptimizerExtension()
    qs_unresolved = Category.objects.all()
    adapted_unresolved = wrap_async_queryset_adapter(qs_unresolved)

    # A String root return type maps to no registered model.
    info_unresolved = make_info(field_name="unresolvedField")._raw_info
    unresolved_res = ext._optimize(adapted_unresolved, info_unresolved)
    assert unwrap_async_queryset_adapter(unresolved_res)[1]
    assert isinstance(unresolved_res, _AsyncQuerySetRows)
    assert unresolved_res._queryset is qs_unresolved


def test_optimizer_preserves_async_adapter_optimized_tail() -> None:
    """Optimized tail with adapter returns re-wrapped adapter."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        categories: list[CategoryType] = DjangoListField(CategoryType)

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    info_optimized = make_info(field_name="categories")._raw_info._replace(
        return_type=schema._schema.type_map["CategoryType"],
        schema=schema._schema,
        field_nodes=[],
    )
    qs_valid = Category.objects.all()
    adapted_valid = wrap_async_queryset_adapter(qs_valid)
    optimized_res = ext._optimize(adapted_valid, info_optimized)
    assert unwrap_async_queryset_adapter(optimized_res)[1]
    assert isinstance(optimized_res, _AsyncQuerySetRows)
    assert optimized_res._queryset is not None


# ---------------------------------------------------------------------------
# The execution frame ends with its execution
# ---------------------------------------------------------------------------


class _FrameSentinel:
    """A weak-referenceable value, so what a frame holds can be asked about."""


def _read_optimizer_state_in_a_copied_context(copied: contextvars.Context) -> dict[str, object]:
    """Everything a task that copied an execution's context could read back."""
    read: dict[str, object] = {}

    def _read() -> None:
        read["optimizer"] = active_optimizer()
        read["strictness"] = active_strictness()
        read["stash"] = optimizer_value(None, "probe")
        read["plans"] = execution_plan_memo()
        read["key_parts"] = cache_key_parts_memo()
        read["converted"] = converted_selections_memo()
        read["scoped"] = relation_is_optimizer_scoped("probe@Type")

    copied.run(_read)
    return read


def test_an_execution_frame_a_task_copied_answers_nothing_once_the_execution_ends() -> None:
    """Every per-execution store ends with the execution, in every context at once.

    ``asyncio.create_task`` copies the whole context, and a token reset rewrites
    only the context that created it - so a resolver's background task went on
    reading the completed operation's stashes, plan memo, converted selections
    and cache-key parts, and held the querysets and plans inside them for as
    long as it ran. The frame is reached through a lease the execution closes,
    so the copy answers exactly as a context with no optimizer running does, and
    every sentinel the frame held is collectable.
    """
    extension = DjangoOptimizerExtension()
    # Real memo entries of each memo's declared type; the weak-referenceable part of each is
    # what the references below watch (a tuple or a list is not itself weak-referenceable).
    stash = _FrameSentinel()
    plan = OptimizationPlan()
    frozen_variables = frozenset({("probe", ("probe", 0, None))})
    node = SelectedField(name="probe", directives={}, arguments={}, selections=[])
    sentinels: dict[str, object] = {
        "stash": stash,
        "plans": plan,
        "key_parts": frozen_variables,
        "converted": node,
    }
    references = {name: weakref.ref(value) for name, value in sentinels.items()}

    frame = begin_execution_frame(
        {},
        nested=False,
        optimizer=extension,
        strictness="warn",
    )
    try:
        stash_for_optimizer(None, "probe", stash)
        plans_memo = execution_plan_memo()
        assert plans_memo is not None
        plan_key: PlanCacheKey = (
            "probe",
            frozenset(),
            Category,
            (),
            None,
        )
        plans_memo[plan_key] = plan
        key_parts_memo = cache_key_parts_memo()
        assert key_parts_memo is not None
        key_parts_memo[1] = ("probe", frozen_variables)
        selections_memo = converted_selections_memo()
        assert selections_memo is not None
        selections_memo[1] = [node]
        publish_scoped_relations({"probe@Type"})
        copied = contextvars.copy_context()
        inside = _read_optimizer_state_in_a_copied_context(copied)
    finally:
        end_execution_frame(frame)

    assert inside["optimizer"] is extension
    assert inside["stash"] is sentinels["stash"]
    assert inside["scoped"] is True

    after = _read_optimizer_state_in_a_copied_context(copied)

    assert after["optimizer"] is None
    assert after["strictness"] is None
    assert after["stash"] is None
    assert after["plans"] is None
    assert after["key_parts"] is None
    assert after["converted"] is None
    assert after["scoped"] is False

    sentinels.clear()
    del inside, after, stash, plan, frozen_variables, node
    gc.collect()
    assert {name: reference() for name, reference in references.items()} == dict.fromkeys(
        references,
        None,
    )


@pytest.mark.django_db
def test_an_operation_in_a_context_that_outlived_a_request_publishes_as_its_own() -> None:
    """The second operation is top-level, clears its own context, and restores to none.

    A task that copied an execution's context and outlived the request is not
    inside anything by the time it runs its own operation. Classified as nested
    it would publish nothing to the context object it was handed - leaving a
    consumer reading their own request's plan with the values of a request that
    has already returned - and what it read back would be the earlier
    operation's stashes rather than its own.
    """
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is CategoryType

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    seen: dict[str, object] = {}

    @strawberry.type
    class Query:
        def _all_items(self) -> QuerySet[Item]:
            """Copy this operation's context, as a resolver starting a task does."""
            seen.setdefault("copied", contextvars.copy_context())
            return Item.objects.all()

        all_items: QuerySet[Item] = strawberry.field(
            resolver=_all_items,
            graphql_type=list[ItemType],
        )

    def _second_operation() -> None:
        """Run a whole operation from the copied context, after the first has ended."""
        context = SimpleNamespace()
        seen["result"] = schema.execute_sync(
            "{ allItems { name category { id name } } }",
            context_value=context,
        )
        seen["published"] = _published_optimizer_keys(context)
        seen["after"] = optimizer_value(None, DST_OPTIMIZER_PLAN)

    finalize_django_types()
    extension = DjangoOptimizerExtension()
    schema = DjangoSchema(query=Query, extensions=[lambda: extension])

    first = schema.execute_sync("{ allItems { name } }", context_value=SimpleNamespace())
    assert first.errors is None, first.errors

    assert isinstance(seen["copied"], contextvars.Context)
    seen["copied"].run(_second_operation)

    assert isinstance(seen["result"], ExecutionResult)
    assert seen["result"].errors is None, seen["result"].errors
    assert seen["result"].data is not None
    assert seen["result"].data["allItems"][0]["category"]["name"]
    published = seen["published"]
    assert isinstance(published, dict)
    assert published[DST_OPTIMIZER_PLAN] is not None
    assert seen["after"] is None


# =============================================================================
# The ``info`` a consumer ``get_queryset`` receives on every optimizer path.
# =============================================================================


class _ConsumerInfo(strawberry.Info[object, object]):
    """A schema ``info_class``: Strawberry hands every resolver this subclass."""


#: ``shape -> (query, root field the hook's Info describes)``. The root list hook
#: runs in the list field's resolver; the two nested hooks run in the plan walk,
#: which the root field's resolver owns.
_HOOK_INFO_QUERIES = {
    "root_list": ("{ items { name } }", "items"),
    "nested_list_prefetch": ("{ categories { items { name } } }", "categories"),
    "nested_connection_prefetch": (
        "{ categories { itemsConnection(first: 1) { edges { node { name } } } } }",
        "categories",
    ),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("shape", sorted(_HOOK_INFO_QUERIES))
@pytest.mark.parametrize("execution", ["sync", "async"])
def test_get_queryset_receives_strawberry_info_on_every_optimizer_path(
    shape: str,
    execution: str,
) -> None:
    """A consumer hook gets the schema's ``info_class`` instance on the root and plan-walk paths.

    The plan walk reads graphql-core's raw resolve info; the hook is typed and
    documented against ``strawberry.Info``, so the walk hands it the ``Info`` of
    the resolver that owns the plan: the schema's ``info_class`` over the same raw
    info, describing that one field.
    """
    services.seed_data(1)
    seen: list[object] = []

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        @override
        def get_queryset(cls, queryset: QuerySet[Item], info: strawberry.Info) -> QuerySet[Item]:
            seen.append(info)
            return queryset

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")
            interfaces = (relay.Node,)
            relation_shapes = {"items": "both"}

    finalize_django_types()

    @strawberry.type
    class Query:
        items: list[ItemType] = DjangoListField(ItemType)
        categories: list[CategoryType] = DjangoListField(CategoryType)

    optimizer = DjangoOptimizerExtension()
    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(info_class=_ConsumerInfo),
        extensions=[lambda: optimizer],
    )
    query, root_field = _HOOK_INFO_QUERIES[shape]
    context = SimpleNamespace()
    if execution == "sync":
        result = schema.execute_sync(query, context_value=context)
    else:
        result = asyncio.run(schema.execute(query, context_value=context))
    assert result.errors is None, result.errors
    assert len(seen) == 1
    (info,) = seen
    assert type(info) is _ConsumerInfo
    assert info.context is context
    assert info.field_name == root_field
    assert info.python_name == root_field
