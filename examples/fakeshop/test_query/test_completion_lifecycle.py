"""Live HTTP acceptance for owned async mutation completion and stable error delivery."""

import asyncio
import inspect
from collections.abc import AsyncIterator, Awaitable, Iterable
from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING, NoReturn

import graphql
import pytest
import strawberry
from apps.library.models import Branch
from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseBase
from django.test import override_settings
from django.urls import path
from graphql import ExecutionResult as CoreResult
from graphql import GraphQLError, GraphQLObjectType
from graphql.execution.collect_fields import FieldDetailsList, GroupedFieldSet
from graphql.execution.incremental.incremental_executor import DeliveryGroupMap
from graphql.pyutils import AwaitableOrValue, Path
from graphql_client import (
    JSONObject,
    JSONValue,
    json_at,
    json_list,
    middleware_without_debug_toolbar,
    response_json,
)
from strawberry.dataloader import DataLoader
from strawberry.extensions import SchemaExtension
from strawberry.http import GraphQLHTTPResponse
from strawberry.schema.schema import StrawberryGraphQLCoreExecutionContext as CoreExecutionContext
from strawberry.types.execution import ExecutionResult
from typing_extensions import override

from django_strawberry_framework import (
    DjangoErrorPolicyExtension,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework import _completion as completion
from django_strawberry_framework.schema import DjangoMutationExecutionContext
from django_strawberry_framework.testing import AsyncTestClient, TestClient
from django_strawberry_framework.utils._narrowing import read_attr
from django_strawberry_framework.views import AsyncDjangoGraphQLView

if TYPE_CHECKING:
    from django_strawberry_framework._completion import _GraphQLOutputType


@dataclass
class CompletionState:
    """Barriers and observations owned by the current in-process HTTP request."""

    initial: str = "deliberate"
    view: str = "stock"
    work: str = "error"
    shape: str = "root"
    context: str = "default"
    started: asyncio.Event = field(default_factory=asyncio.Event)
    release: asyncio.Event = field(default_factory=asyncio.Event)
    drained: asyncio.Event = field(default_factory=asyncio.Event)
    cleanup_started: asyncio.Event | None = None
    fail_before_cancel: bool = False
    cleanup_release: asyncio.Event = field(default_factory=asyncio.Event)
    start_atomic: bool | None = None
    start_rows: list[str] = field(default_factory=list)
    orm_atomic: bool | None = None
    orm_pk: int | None = None
    orm_error: str | None = None
    cancelled: bool = False
    custom_used: bool = False
    engine_errors: list[GraphQLError] = field(default_factory=list)
    operation_errors: list[str] = field(default_factory=list)
    result_collection_errors: list[str] = field(default_factory=list)
    view_errors_before: list[str] = field(default_factory=list)
    view_errors_after: list[str] = field(default_factory=list)
    schema: strawberry.Schema | None = None
    nested_shape: str = "root"
    loader: DataLoader[str, str] | None = None


@dataclass
class Harness:
    """The URL mount reads the state selected by the sequential test."""

    state: CompletionState = field(default_factory=CompletionState)


CURRENT = Harness()


def messages(result: ExecutionResult | CoreResult) -> list[str]:
    """Read real execution result messages for measurement."""
    return [error.message for error in result.errors or []]


async def fast() -> NoReturn:
    """Fail only after the sibling is executing and held at its I/O barrier."""
    await CURRENT.state.started.wait()
    if CURRENT.state.fail_before_cancel:
        # Fail while the sibling is still held, so the caller cancels during the drain.
        pass
    elif CURRENT.state.cleanup_started is not None:
        await CURRENT.state.release.wait()
    elif CURRENT.state.shape in {"mutation", "mutation_list"}:
        # Model completion of independent I/O; transport hooks cannot release an
        # owned child because the transaction must join it before reaching them.
        asyncio.get_running_loop().call_soon(CURRENT.state.release.set)
    if CURRENT.state.initial == "deliberate":
        raise GraphQLError("INITIAL_DELIBERATE")
    raise ValueError("INITIAL_UNEXPECTED")


async def late() -> str:
    """Finish normal asynchronous I/O after the early sibling completes."""
    task = asyncio.current_task()
    assert task is not None
    task.add_done_callback(lambda _completed: CURRENT.state.drained.set())
    if CURRENT.state.work in {"orm", "cleanup"}:

        def observe_start() -> None:
            CURRENT.state.start_atomic = connection.in_atomic_block
            CURRENT.state.start_rows = list(Branch.objects.values_list("name", flat=True))

        await sync_to_async(observe_start)()
    CURRENT.state.started.set()
    try:
        await CURRENT.state.release.wait()
    except asyncio.CancelledError:
        CURRENT.state.cancelled = True
        if CURRENT.state.work != "cleanup":
            raise
        if CURRENT.state.cleanup_started is not None:
            CURRENT.state.cleanup_started.set()
            await CURRENT.state.cleanup_release.wait()

    if CURRENT.state.work in {"orm", "cleanup"}:

        def create() -> int | None:
            CURRENT.state.orm_atomic = connection.in_atomic_block
            row = Branch.objects.create(name="late-created")
            return row.pk

        try:
            CURRENT.state.orm_pk = await sync_to_async(create)()
        except Exception as exc:
            CURRENT.state.orm_error = f"{type(exc).__name__}: {exc}"
            raise
    if CURRENT.state.cancelled:
        raise asyncio.CancelledError
    if CURRENT.state.work in {"orm", "cleanup"}:
        return "late-completed"
    raise ValueError("LATE_SYNTHETIC_EXCEPTION")


class Observe(SchemaExtension):
    """Keep the real engine result before the framework masks its returned copy."""

    @override
    async def on_operation(self) -> AsyncIterator[None]:
        """Record upstream result and optionally perform async operation audit I/O."""
        yield
        result = self.execution_context.result
        assert isinstance(result, CoreResult)
        CURRENT.state.engine_errors = result.errors or []
        CURRENT.state.operation_errors = messages(result)
        if CURRENT.state.view == "extension":
            CURRENT.state.release.set()
            await CURRENT.state.drained.wait()

    @override
    async def get_results(self) -> dict[str, object]:
        """Collect asynchronous audit metadata after operation teardown."""
        if CURRENT.state.view == "results":
            result = read_attr(self.execution_context, "result")
            assert isinstance(result, CoreResult)
            CURRENT.state.result_collection_errors = messages(result)
            CURRENT.state.release.set()
            await CURRENT.state.drained.wait()
        return {}


class AuditView(AsyncDjangoGraphQLView):
    """An ordinary async result hook awaits audit I/O before standard formatting."""

    @override
    async def process_result(
        self,
        request: HttpRequest,
        result: ExecutionResult,
    ) -> GraphQLHTTPResponse:
        """Record the handed-back result then wait for the synthetic audit barrier."""
        CURRENT.state.view_errors_before = messages(result)
        CURRENT.state.release.set()
        await CURRENT.state.drained.wait()
        CURRENT.state.view_errors_after = messages(result)
        return await super().process_result(request, result)


@wraps(AsyncDjangoGraphQLView.as_view())
async def view(request: HttpRequest) -> HttpResponseBase:
    """Mount the actual package async view through Django's in-process client."""
    view_class = AuditView if CURRENT.state.view == "audit" else AsyncDjangoGraphQLView
    assert CURRENT.state.schema is not None
    return await view_class.as_view(schema=CURRENT.state.schema)(request)


urlpatterns = [path("graphql-async/", view)]


def make_schema(shape: str) -> tuple[strawberry.Schema, str]:
    """Declare a model type and generated mutation using the package's Meta API."""

    @strawberry.type
    class SharedInner:
        """A nullable branch sharing one loader key with its surviving sibling."""

        @strawberry.field
        async def fast(self) -> str:
            await CURRENT.state.started.wait()
            raise GraphQLError("SHARED_INNER_FAILURE")

        @strawberry.field
        async def late(self) -> str | None:
            assert CURRENT.state.loader is not None
            return await CURRENT.state.loader.load("k")

    async def branch_names() -> "QuerySet[Branch, str]":
        # The QuerySet itself, so list completion reaches the async QuerySet adapter.
        return Branch.objects.order_by("name").values_list("name", flat=True)

    async def awaitable_values() -> list[Awaitable[str]] | None:
        # Unawaited items: graphql-core completes each list item as an awaitable.
        if CURRENT.state.work == "success":

            async def value(text: str) -> str:
                await asyncio.sleep(0)
                return text

            return [value("first"), value("second")]
        return [fast(), late()]

    class ProbeBranch(DjangoType):
        """A library branch with asynchronous computed fields."""

        @strawberry.field
        @staticmethod
        async def fast() -> str:
            return await fast()

        @strawberry.field
        @staticmethod
        async def late(root: strawberry.Parent[Branch]) -> str | None:
            if CURRENT.state.shape == "list" and root.name == "early":
                return "fine"
            return await late()

        @strawberry.field
        @staticmethod
        async def value(root: strawberry.Parent[Branch]) -> str:
            if root.name == "early":
                return await fast()
            if CURRENT.state.shape == "list":
                return "fine"
            return await late()

        names: "QuerySet[Branch, str]" = strawberry.field(
            resolver=branch_names,
            graphql_type=list[str],
        )
        values: list[Awaitable[str]] | None = strawberry.field(
            resolver=awaitable_values,
            graphql_type=list[str] | None,
        )

        @strawberry.field
        @staticmethod
        def refused() -> str:
            """Fail synchronously on a non-null field once its asynchronous sibling started."""
            raise GraphQLError("SYNC_FAILURE")

        @strawberry.field
        @staticmethod
        async def tolerated() -> str | None:
            CURRENT.state.started.set()
            raise GraphQLError("NULLABLE_FAILURE")

        @strawberry.field
        @staticmethod
        async def survives() -> str:
            await CURRENT.state.started.wait()

            def create() -> str:
                CURRENT.state.orm_atomic = connection.in_atomic_block
                return Branch.objects.create(name="surviving-sibling").name

            return await sync_to_async(create)()

        @strawberry.field
        @staticmethod
        async def nested() -> str:
            inner = DjangoSchema(query=Query)
            CURRENT.state.shape = CURRENT.state.nested_shape
            document = (
                "{ branches { value } }"
                if CURRENT.state.nested_shape == "list_nonnull"
                else "{ fast late }"
            )
            result = await inner.execute(document)
            assert result.errors is not None
            CURRENT.state.release.set()
            await CURRENT.state.drained.wait()
            return "nested-finished"

        @strawberry.field
        @staticmethod
        async def inner() -> SharedInner | None:
            return SharedInner()

        @strawberry.field
        @staticmethod
        async def shared() -> str | None:
            assert CURRENT.state.loader is not None
            return await CURRENT.state.loader.load("k")

        class Meta:
            model = Branch
            fields = ("id", "name")

    class CreateProbeBranch(DjangoMutation):
        """The normal generated create pipeline with anonymous writes enabled."""

        class Meta:
            model = Branch
            operation = "create"
            fields = ("name",)
            permission_classes = []

    finalize_django_types()

    @strawberry.type
    class Query:
        """Root fields and model objects exercise different completion parents."""

        @strawberry.field
        async def fast(self) -> str:
            return await fast()

        @strawberry.field
        async def late(self) -> str | None:
            return await late()

        async def _branch(self) -> Branch | None:
            return await Branch.objects.aget(name="early")

        branch: Branch | None = strawberry.field(
            resolver=_branch,
            graphql_type=ProbeBranch | None,
        )

        async def _branches(self) -> list[Branch] | None:
            return [row async for row in Branch.objects.order_by("id")]

        branches: list[Branch] | None = strawberry.field(
            resolver=_branches,
            graphql_type=list[ProbeBranch] | None,
        )

    @strawberry.type
    class Mutation:
        """Only the stock generated field, with its completion-spanning atomic."""

        create = DjangoMutationField(CreateProbeBranch)

    context = None
    if CURRENT.state.context == "core":
        context = CoreExecutionContext
    elif CURRENT.state.context == "custom":

        class CustomContext(CoreExecutionContext):
            @override
            def execute_fields(
                self,
                parent_type: GraphQLObjectType,
                source_value: object,
                path: Path | None,
                grouped_field_set: GroupedFieldSet,
                position_context: DeliveryGroupMap | None,
            ) -> AwaitableOrValue[dict[str, object]]:
                CURRENT.state.custom_used = True
                return super().execute_fields(
                    parent_type,
                    source_value,
                    path,
                    grouped_field_set,
                    position_context,
                )

        context = CustomContext
    elif CURRENT.state.context == "cooperative":

        class Tracing(CoreExecutionContext):
            @override
            def complete_iterable_value(
                self,
                item_type: "_GraphQLOutputType",
                field_details_list: FieldDetailsList,
                info: graphql.GraphQLResolveInfo[object],
                path: Path,
                items: Iterable[object],
                position_context: DeliveryGroupMap | None,
            ) -> AwaitableOrValue[list[object]]:
                CURRENT.state.custom_used = True
                return completion._as_list_completion(super()).complete_iterable_value(
                    item_type,
                    field_details_list,
                    info,
                    path,
                    items,
                    position_context,
                )

        class CooperativeContext(DjangoMutationExecutionContext, Tracing):
            """An ordinary cooperative mixin following the mutation context."""

        context = CooperativeContext
    if CURRENT.state.context == "plain":
        schema = strawberry.Schema(query=Query, extensions=[DjangoErrorPolicyExtension, Observe])
    else:
        schema = DjangoSchema(
            query=Query,
            mutation=Mutation,
            extensions=[Observe],
            execution_context_class=context,
        )
    queries = {
        "root": "{ fast late }",
        "object": "{ branch { fast late } }",
        "list": "{ branches { value late } }",
        "list_nonnull": "{ branches { value } }",
        "mutation": (
            'mutation { create(data: {name: "mutation-created"}) {'
            " result { fast late } errors { field messages } } }"
        ),
    }
    queries["mutation_list"] = (
        'mutation { create(data: {name: "mutation-created"}) {'
        " result { values } errors { field messages } } }"
    )
    return schema, queries[shape]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("context_kind", ["default"])
@pytest.mark.parametrize(
    "shape",
    [
        "root",
        "object",
        "list",
        "list_nonnull",
        "mutation",
    ],
)
@pytest.mark.parametrize("initial", ["deliberate", "unexpected"])
@pytest.mark.parametrize(
    "view_kind",
    [
        "stock",
        "audit",
        "extension",
        "results",
    ],
)
async def test_live_late_errors(
    private_registry: None,
    shape: str,
    initial: str,
    view_kind: str,
    context_kind: str,
) -> None:
    """Only errors present at the publication boundary can reach the response."""
    assert private_registry is None
    await Branch.objects.acreate(name="early")
    await Branch.objects.acreate(name="late")
    CURRENT.state = CompletionState(
        started=asyncio.Event(),
        release=asyncio.Event(),
        drained=asyncio.Event(),
        initial=initial,
        view=view_kind,
        work="error",
        shape=shape,
        context=context_kind,
    )
    schema, query = make_schema(shape)
    CURRENT.state.schema = schema
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        result = await asyncio.wait_for(
            AsyncTestClient(path="/graphql-async/").query(query, assert_no_errors=False),
            timeout=15,
        )
        response = result.response
        response_bytes = response.content.decode()
        CURRENT.state.release.set()
        await asyncio.wait_for(CURRENT.state.drained.wait(), timeout=15)
        after_drain = [error.message for error in CURRENT.state.engine_errors]
        names = [row.name async for row in Branch.objects.order_by("name")]
        assert response.status_code == 200
        # Outside a mutation window graphql-core's ``gather_with_cancel`` cancels the
        # late sibling; inside one the window's join lets it finish, so its error is
        # recorded before the bubbling error nulls their shared ancestor.
        late_is_collected = shape == "mutation"
        assert ("LATE_SYNTHETIC_EXCEPTION" in after_drain) == late_is_collected
        assert "mutation-created" not in names
        errors = json_list(response_json(response), "errors")
        visible = [json_at(error, "message") for error in errors]
        expected = ["An unexpected error occurred."] if late_is_collected else []
        expected.append(
            "INITIAL_DELIBERATE" if initial == "deliberate" else "An unexpected error occurred.",
        )
        assert visible == expected
        expected_data: dict[str, JSONValue] = {
            "root": None,
            "object": {"branch": None},
            "list": {"branches": None},
            "list_nonnull": {"branches": None},
            "mutation": {"create": {"result": None, "errors": []}},
        }
        assert json_at(response_json(response), "data") == expected_data[shape]
        assert response.content.decode() == response_bytes


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("work_kind", ["orm"])
@pytest.mark.parametrize("mutation_shape", ["mutation"])
@pytest.mark.parametrize(
    "view_kind",
    [
        "stock",
        "audit",
        "extension",
        "results",
    ],
)
async def test_live_late_mutation_orm(
    private_registry: None,
    view_kind: str,
    work_kind: str,
    mutation_shape: str,
) -> None:
    """Observe a normal thread-sensitive ORM call from a late payload resolver."""
    assert private_registry is None
    CURRENT.state = CompletionState(
        started=asyncio.Event(),
        release=asyncio.Event(),
        drained=asyncio.Event(),
        initial="deliberate",
        view=view_kind,
        work=work_kind,
        shape=mutation_shape,
    )
    schema, query = make_schema(mutation_shape)
    CURRENT.state.schema = schema
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        result = await asyncio.wait_for(
            AsyncTestClient(path="/graphql-async/").query(query, assert_no_errors=False),
            timeout=15,
        )
        response = result.response
        CURRENT.state.release.set()
        await asyncio.wait_for(CURRENT.state.drained.wait(), timeout=15)
        names = [row.name async for row in Branch.objects.all()]
        assert response.status_code == 200
        failing_field = "values" if mutation_shape == "mutation_list" else "fast"
        location = graphql.get_location(graphql.Source(query), query.index(failing_field))
        error_path: list[JSONValue] = ["create", "result", failing_field]
        if mutation_shape == "mutation_list":
            error_path.append(0)
        expected: JSONObject = {
            "data": {
                "create": {
                    "result": {"values": None} if mutation_shape == "mutation_list" else None,
                    "errors": [],
                },
            },
            "errors": [
                {
                    "message": "INITIAL_DELIBERATE",
                    "locations": [{"line": location.line, "column": location.column}],
                    "path": error_path,
                },
            ],
        }
        assert response_json(response) == expected
        assert names == []
        assert CURRENT.state.orm_atomic is True
        assert CURRENT.state.orm_pk is not None
        assert CURRENT.state.orm_error is None
        assert CURRENT.state.cancelled is False


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("work_kind", ["orm"])
@pytest.mark.parametrize("mutation_shape", ["mutation"])
@pytest.mark.parametrize("view_kind", ["audit", "results"])
def test_live_sync_bridge_mutation_orm(
    private_registry: None,
    view_kind: str,
    work_kind: str,
    mutation_shape: str,
) -> None:
    """Observe the same async view with Django's supported sync client bridge."""
    assert private_registry is None
    CURRENT.state = CompletionState(
        started=asyncio.Event(),
        release=asyncio.Event(),
        drained=asyncio.Event(),
        initial="deliberate",
        view=view_kind,
        work=work_kind,
        shape=mutation_shape,
    )
    schema, query = make_schema(mutation_shape)
    CURRENT.state.schema = schema
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        response = (
            TestClient(path="/graphql-async/")
            .query(
                query,
                assert_no_errors=False,
            )
            .response
        )
        assert response.status_code == 200
        assert CURRENT.state.drained.is_set()
        assert not Branch.objects.filter(name="mutation-created").exists()
        assert CURRENT.state.start_atomic is True
        assert CURRENT.state.start_rows == ["mutation-created"]
        assert CURRENT.state.orm_atomic is True
        assert CURRENT.state.orm_error is None
        assert CURRENT.state.orm_pk is not None
        assert CURRENT.state.cancelled is False
        assert not Branch.objects.exists()
        errors = json_list(response_json(response), "errors")
        assert len(errors) == 1
        assert json_at(errors, 0, "message") == "INITIAL_DELIBERATE"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("context_kind", ["core", "custom"])
@pytest.mark.parametrize("initial", ["deliberate", "unexpected"])
@pytest.mark.parametrize(
    "view_kind",
    [
        "stock",
        "audit",
        "extension",
        "results",
    ],
)
async def test_live_custom_query_context(
    private_registry: None,
    context_kind: str,
    initial: str,
    view_kind: str,
) -> None:
    await test_live_late_errors(private_registry, "root", initial, view_kind, context_kind)
    if context_kind == "custom":
        assert CURRENT.state.custom_used is True


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mutation_shape", ["mutation", "mutation_list"])
@pytest.mark.parametrize("view_kind", ["audit", "results"])
def test_live_sync_bridge_cleanup(
    private_registry: None,
    mutation_shape: str,
    view_kind: str,
) -> None:
    test_live_sync_bridge_mutation_orm(
        private_registry,
        view_kind,
        "cleanup",
        mutation_shape,
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mutation_shape", ["mutation", "mutation_list"])
@pytest.mark.parametrize("view_kind", ["audit", "results"])
async def test_live_direct_cleanup(
    private_registry: None,
    mutation_shape: str,
    view_kind: str,
) -> None:
    await test_live_late_mutation_orm(
        private_registry,
        view_kind,
        "cleanup",
        mutation_shape,
    )
    assert CURRENT.state.orm_atomic is True
    assert CURRENT.state.orm_pk is not None
    assert not await Branch.objects.aexists()


def _draining_after_failure() -> bool:
    """Whether an owned join is awaiting its drain after an ordinary sibling failure.

    Reads the suspended ``_gather_with_cancel`` frames of every running task: one
    that has created ``drain`` with ``cancelled`` still false took the
    ordinary-failure path and is waiting only on its surviving siblings.
    """
    for task in asyncio.all_tasks():
        awaited: object = task.get_coro()
        while inspect.iscoroutine(awaited):
            frame = awaited.cr_frame
            if frame is not None and awaited.cr_code is completion._gather_with_cancel.__code__:
                state = frame.f_locals
                if "drain" in state and state.get("cancelled") is False:
                    return True
            awaited = awaited.cr_await
    return False


async def _until_draining_after_failure() -> None:
    """Yield to the loop, never to the clock, until the failed join reaches its drain."""
    for _ in range(1000):
        if _draining_after_failure():
            return
        await asyncio.sleep(0)
    pytest.fail("the owned join never drained after the sibling failure")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mutation_shape", ["mutation", "mutation_list"])
@pytest.mark.parametrize("cancels", [1, 3])
@pytest.mark.parametrize("first", ["cancel", "failure"])
async def test_live_cancellation_waits_for_payload_cleanup(
    private_registry: None,
    mutation_shape: str,
    cancels: int,
    first: str,
) -> None:
    """Caller cancellation cancels the held sibling and waits out its cleanup.

    ``first`` is what the join sees first: the cancellation itself, or an
    ordinary failure of the early sibling, after which the join is draining the
    held sibling when the cancellation arrives and must cancel it then.
    """
    assert private_registry is None
    CURRENT.state = CompletionState(
        started=asyncio.Event(),
        release=asyncio.Event(),
        drained=asyncio.Event(),
        cleanup_started=asyncio.Event(),
        cleanup_release=asyncio.Event(),
        initial="deliberate",
        view="stock",
        work="cleanup",
        shape=mutation_shape,
        fail_before_cancel=first == "failure",
    )
    schema, query = make_schema(mutation_shape)
    CURRENT.state.schema = schema
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        request = asyncio.create_task(
            AsyncTestClient(path="/graphql-async/").query(query, assert_no_errors=False),
        )
        assert CURRENT.state.cleanup_started is not None
        await asyncio.wait_for(CURRENT.state.started.wait(), timeout=15)
        if first == "failure":
            await _until_draining_after_failure()
            assert not CURRENT.state.cancelled
        request.cancel()
        await asyncio.wait_for(CURRENT.state.cleanup_started.wait(), timeout=15)
        for _ in range(cancels - 1):
            request.cancel()
            await asyncio.sleep(0)
        assert not request.done()
        CURRENT.state.cleanup_release.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(request, timeout=15)
    assert CURRENT.state.drained.is_set()
    assert CURRENT.state.orm_atomic is True
    assert CURRENT.state.orm_pk is not None
    assert not await Branch.objects.aexists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("async_request", ["direct", "bridge"])
async def test_live_queryset_completion_inside_mutation(
    private_registry: None,
    async_request: str,
) -> None:
    assert private_registry is None
    CURRENT.state = CompletionState(
        initial="deliberate",
        view="stock",
        work="error",
        shape="mutation",
    )
    schema, _ = make_schema("mutation")
    CURRENT.state.schema = schema
    query = 'mutation { create(data: {name: "queryset-created"}) { result { names } } }'
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        if async_request == "direct":
            result = await AsyncTestClient(path="/graphql-async/").query(
                query,
                assert_no_errors=False,
            )
        else:
            result = await sync_to_async(TestClient(path="/graphql-async/").query)(
                query,
                assert_no_errors=False,
            )
        response = result.response
    assert response_json(response) == {
        "data": {"create": {"result": {"names": ["queryset-created"]}}},
    }
    assert [row.name async for row in Branch.objects.all()] == [
        "queryset-created",
    ]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("initial", ["deliberate", "unexpected"])
@pytest.mark.parametrize(
    "view_kind",
    [
        "stock",
        "audit",
        "extension",
        "results",
    ],
)
async def test_live_standalone_error_extension(
    private_registry: None,
    initial: str,
    view_kind: str,
) -> None:
    await test_live_late_errors(private_registry, "root", initial, view_kind, "plain")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("shape", ["success", "nullable"])
async def test_live_completed_siblings_keep_upstream_results(
    private_registry: None,
    shape: str,
) -> None:
    """Successful lists finish; a nullable error does not abandon surviving siblings."""
    assert private_registry is None
    CURRENT.state = CompletionState(work="success", shape="mutation")
    schema, _ = make_schema("mutation")
    CURRENT.state.schema = schema
    selection = "values" if shape == "success" else "tolerated survives"
    query = 'mutation { create(data: {name: "created"}) { result { ' + selection + " } } }"
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        result = await AsyncTestClient(path="/graphql-async/").query(
            query,
            assert_no_errors=False,
        )
        response = result.response
    result = response_json(response)
    if shape == "success":
        assert result == {"data": {"create": {"result": {"values": ["first", "second"]}}}}
        assert await Branch.objects.filter(name="created").aexists()
    else:
        assert json_at(result, "data", "create", "result") == {
            "tolerated": None,
            "survives": "surviving-sibling",
        }
        assert json_at(result, "errors", 0, "message") == "NULLABLE_FAILURE"
        assert CURRENT.state.orm_atomic is True
        assert not await Branch.objects.aexists()


@pytest.mark.django_db(transaction=True)
async def test_live_synchronous_failure_drains_the_started_sibling_inside_the_window(
    private_registry: None,
) -> None:
    """A sibling graphql-core settles in the background still runs inside the transaction.

    ``refused`` fails synchronously after ``survives`` has started, so graphql-core hands
    ``survives`` to its background settling; the window awaits it before closing, so its
    write runs inside the atomic block and is rolled back with the mutation's own row.
    """
    assert private_registry is None
    CURRENT.state = CompletionState(work="success", shape="mutation")
    CURRENT.state.started.set()
    schema, _ = make_schema("mutation")
    CURRENT.state.schema = schema
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        result = await asyncio.wait_for(
            AsyncTestClient(path="/graphql-async/").query(
                'mutation { create(data: {name: "created"}) { result { survives refused } } }',
                assert_no_errors=False,
            ),
            timeout=15,
        )
    response = response_json(result.response)
    assert json_at(response, "data", "create", "result") is None
    assert json_at(response, "errors", 0, "message") == "SYNC_FAILURE"
    assert CURRENT.state.orm_atomic is True
    assert not await Branch.objects.aexists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("nested_shape", ["root", "list_nonnull"])
async def test_live_nested_query_keeps_its_own_completion_context(
    private_registry: None,
    nested_shape: str,
) -> None:
    """An inner query does not inherit its outer generated mutation's child supervision."""
    assert private_registry is None
    if nested_shape == "list_nonnull":
        await Branch.objects.acreate(name="early")
        await Branch.objects.acreate(name="late")
    CURRENT.state = CompletionState(shape="mutation", nested_shape=nested_shape)
    schema, _ = make_schema("mutation")
    CURRENT.state.schema = schema
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        result = await asyncio.wait_for(
            AsyncTestClient(path="/graphql-async/").query(
                'mutation { create(data: {name: "outer"}) { result { nested } } }',
                assert_no_errors=False,
            ),
            timeout=15,
        )
        response = result.response
    assert response_json(response) == {
        "data": {"create": {"result": {"nested": "nested-finished"}}},
    }
    # graphql-core's own ``gather_with_cancel`` cancelled the inner query's sibling;
    # the outer mutation window's join would have let it finish.
    assert CURRENT.state.cancelled is True
    assert await Branch.objects.filter(name="outer").aexists()


@pytest.mark.django_db(transaction=True)
async def test_live_nullable_failure_preserves_a_surviving_shared_loader_key(
    private_registry: None,
) -> None:
    """A nulled inner object cannot cancel the surviving branch's cached future."""
    assert private_registry is None
    CURRENT.state = CompletionState(shape="mutation")

    async def batch(keys: list[str]) -> list[str]:
        CURRENT.state.started.set()
        # Ordinary asynchronous I/O completes after the inner non-null failure.
        await asyncio.sleep(0.2)
        return ["loaded-" + key for key in keys]

    CURRENT.state.loader = DataLoader(load_fn=batch)
    schema, _ = make_schema("mutation")
    CURRENT.state.schema = schema
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        result = await asyncio.wait_for(
            AsyncTestClient(path="/graphql-async/").query(
                'mutation { create(data: {name: "shared"}) '
                "{ result { inner { fast late } shared } } }",
                assert_no_errors=False,
            ),
            timeout=15,
        )
    response = result.response
    assert json_at(response_json(response), "data", "create", "result") == {
        "inner": None,
        "shared": "loaded-k",
    }
    assert json_at(response_json(response), "errors", 0, "message") == "SHARED_INNER_FAILURE"
    assert json_at(response_json(response), "errors", 0, "path") == [
        "create",
        "result",
        "inner",
        "fast",
    ]
    assert not await Branch.objects.aexists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("source_available", [False, True])
async def test_live_unowned_list_uses_the_cooperative_context_without_an_audit(
    private_registry: None,
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_available: bool,
) -> None:
    """Queries preserve the next list override and need no mutation source audit."""
    assert private_registry is None
    await Branch.objects.acreate(name="query-only")
    CURRENT.state = CompletionState(context="cooperative")
    schema, _ = make_schema("root")
    CURRENT.state.schema = schema

    def source_unavailable(_value: object) -> str:
        if source_available:
            return "def execute_fields(self): pass"
        raise OSError("sourceless deployment")

    completion._completion_method.cache_clear()
    monkeypatch.setattr(inspect, "getsource", source_unavailable)
    with override_settings(
        ROOT_URLCONF=__name__,
        DEBUG=False,
        MIDDLEWARE=middleware_without_debug_toolbar(),
    ):
        result = await asyncio.wait_for(
            AsyncTestClient(path="/graphql-async/").query(
                "{ branches { name } }",
                assert_no_errors=False,
            ),
            timeout=15,
        )
    response = result.response
    assert response_json(response) == {"data": {"branches": [{"name": "query-only"}]}}
    assert CURRENT.state.custom_used is True
