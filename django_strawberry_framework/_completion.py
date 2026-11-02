"""Join graphql-core-owned concurrent completion before returning to its owner."""

import ast
import asyncio
import functools
import hashlib
import inspect
import textwrap
from contextlib import contextmanager
from contextvars import ContextVar
from types import FunctionType, MappingProxyType
from typing import TYPE_CHECKING, NamedTuple, ParamSpec, TypeVar

from strawberry.schema.schema import StrawberryGraphQLCoreExecutionContext
from typing_extensions import override

from .utils import truth
from .utils._narrowing import is_list_or_tuple
from .utils.operation_lease import OperationLease

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Generator, Iterable
    from typing import Protocol, TypeAlias

    from graphql import (
        GraphQLEnumType,
        GraphQLInterfaceType,
        GraphQLList,
        GraphQLNonNull,
        GraphQLObjectType,
        GraphQLResolveInfo,
        GraphQLScalarType,
        GraphQLType,
        GraphQLUnionType,
    )
    from graphql.execution.collect_fields import FieldDetailsList, GroupedFieldSet
    from graphql.execution.incremental.incremental_executor import DeliveryGroupMap
    from graphql.pyutils import AwaitableOrValue, Path

    _GraphQLNullableOutputType: TypeAlias = (
        GraphQLScalarType
        | GraphQLObjectType
        | GraphQLInterfaceType
        | GraphQLUnionType
        | GraphQLEnumType
        | GraphQLList[GraphQLType]
    )
    #: graphql-core's ``GraphQLOutputType``, with the list member it leaves bare
    #: parametrized by ``GraphQLList``'s own bound.
    _GraphQLOutputType: TypeAlias = (
        _GraphQLNullableOutputType | GraphQLNonNull[_GraphQLNullableOutputType]
    )
    #: What graphql-core settles in the background during the open window: siblings of a
    #: field whose synchronous failure bubbled, awaited (``drain_settling``) before it closes.
    _Settling: TypeAlias = list[asyncio.Future[list[object]]]

    class _ListCompletion(Protocol):
        """The two list-completion methods of Strawberry's execution context.

        graphql-core declares their ``item_type`` as ``GraphQLOutputType``, whose list
        member is the bare generic ``GraphQLList``; read through this view the methods
        carry ``_GraphQLOutputType`` instead and nothing Unknown.
        """

        async def complete_async_iterator_value(
            self,
            item_type: _GraphQLOutputType,
            field_details_list: FieldDetailsList,
            info: GraphQLResolveInfo[object],
            path: Path,
            async_iterator: AsyncIterator[object],
            position_context: DeliveryGroupMap | None,
        ) -> list[object]: ...

        def complete_iterable_value(
            self,
            item_type: _GraphQLOutputType,
            field_details_list: FieldDetailsList,
            info: GraphQLResolveInfo[object],
            path: Path,
            items: Iterable[object],
            position_context: DeliveryGroupMap | None,
        ) -> AwaitableOrValue[list[object]]: ...

    _ExecuteFields = Callable[
        [
            StrawberryGraphQLCoreExecutionContext,
            GraphQLObjectType,
            object,
            Path | None,
            GroupedFieldSet,
            DeliveryGroupMap | None,
        ],
        AwaitableOrValue[dict[str, object]],
    ]
    _CompleteAsyncIteratorValue = Callable[
        [
            StrawberryGraphQLCoreExecutionContext,
            _GraphQLOutputType,
            FieldDetailsList,
            GraphQLResolveInfo[object],
            Path,
            AsyncIterator[object],
            DeliveryGroupMap | None,
        ],
        Awaitable[list[object]],
    ]
    _CompleteIterableValue = Callable[
        [
            StrawberryGraphQLCoreExecutionContext,
            _GraphQLOutputType,
            FieldDetailsList,
            GraphQLResolveInfo[object],
            Path,
            Iterable[object],
            DeliveryGroupMap | None,
        ],
        AwaitableOrValue[list[object]],
    ]

#: The lease on the execution context whose generated-mutation window is open; read by
#: identity only.
_owner: ContextVar[OperationLease[object] | None] = ContextVar(
    "completion_owner",
    default=None,
)

#: The lease on the open window's settle list.
_settling: "ContextVar[OperationLease[_Settling] | None]" = ContextVar(
    "completion_settling",
    default=None,
)

#: Strawberry's execution context, read as ``_ListCompletion``: where the two audited
#: list-completion methods are read from.
_LIST_COMPLETION: "type[_ListCompletion]" = StrawberryGraphQLCoreExecutionContext


def _as_list_completion(view: "_ListCompletion") -> "_ListCompletion":
    """Return ``view`` - a ``super()`` proxy - read as ``_ListCompletion``.

    A declared parameter is the one read the checker keeps at the declared type; an
    annotated assignment narrows back to the proxy's own class, whose two methods
    carry graphql-core's bare list.
    """
    return view


@contextmanager
def owned_completion(context: object) -> "Generator[_Settling]":
    """Mark only this generated-mutation context's async completion window.

    Yields the window's settle list, which the owner drains (``drain_settling``) before
    the window closes.
    """
    _ = _completion_methods()
    settling: _Settling = []
    lease = OperationLease(context)
    settling_lease = OperationLease(settling)
    token = _owner.set(lease)
    settling_token = _settling.set(settling_lease)
    try:
        yield settling
    finally:
        settling_lease.close()
        lease.close()
        _settling.reset(settling_token)
        _owner.reset(token)


async def drain_settling(settling: "_Settling") -> None:
    """Await every sibling the owned window settled in the background.

    A bubbling synchronous error leaves its already-started siblings to graphql-core's
    background settling, which would otherwise outlive the window's transaction. They run
    to completion here, across any cancellation of the awaiting task; a cancellation
    cancels them first and is re-raised once they have ended.
    """
    cancelled = False
    while settling:
        future = settling.pop()
        while not future.done():
            try:
                _ = await asyncio.wait((future,))
            except asyncio.CancelledError:  # noqa: PERF203 - cleanup must outlast repeated cancellation
                cancelled = True
                _ = future.cancel()
    if cancelled:
        raise asyncio.CancelledError


async def _gather_with_cancel(*awaitables: "Awaitable[object]") -> list[object]:
    """Join siblings before propagating failure; cancel them only on caller cancellation.

    graphql-core's own ``gather_with_cancel`` cancels every sibling on the first
    failure; this join cancels none on an ordinary failure, which must not cancel a
    shared DataLoader future that a surviving branch also awaits. The shielded drain
    keeps repeated caller cancellation from ending the owning mutation window before
    cleanup finishes. GeneratorExit is deliberately outside this handler: closing a
    coroutine cannot await cleanup.
    """
    futures = [asyncio.ensure_future(value) for value in awaitables]
    running = asyncio.gather(*futures)
    try:
        return await asyncio.shield(running)
    except (Exception, asyncio.CancelledError) as error:
        cancelled = isinstance(error, asyncio.CancelledError)
        if cancelled:
            for future in futures:
                if not future.done():
                    _ = future.cancel()
        # Also observe the original gather if cancellation reached its shield
        # before it delivered its own exception.
        remaining: list[Awaitable[object]] = [running, *futures]
        drain = asyncio.gather(*remaining, return_exceptions=True)
        while not drain.done():
            try:
                _ = await asyncio.shield(drain)
            except asyncio.CancelledError:  # noqa: PERF203 - cleanup must outlast repeated cancellation
                if not cancelled:
                    for future in futures:
                        if not future.done():
                            _ = future.cancel()
                cancelled = True
        if cancelled:
            raise asyncio.CancelledError from None
        raise


# Complete stable support census (docstring-free syntax, not version-only approval):
# 3.3.1. Comments, formatting and private docstrings do not affect the audited dependency.
_AUDITED = MappingProxyType(
    {
        "execute_fields": frozenset(
            {
                "ffacf6dd0fb4c965f6580b17059bd7ef16d91481cba02a89fbbe0cefd966a3e3",
            },
        ),
        "complete_async_iterator_value": frozenset(
            {
                "c84708d97b2c7fb397f313c52b17d3b4488c429cf43984477b14acb0c76ee347",
            },
        ),
        "complete_iterable_value": frozenset(
            {
                "7a51dcb90237e6258d6ffec70e7179d5bb0e798b89201edec67bb4c0322613bc",
            },
        ),
    },
)

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _syntax_shape(node: object) -> object:
    """Serialize syntax consistently across supported Python AST schema versions."""
    if isinstance(node, ast.AST):
        # ast.iter_fields yields each syntax value as Any; the list holds them as object,
        # since none is interpreted here.
        fields: list[tuple[str, object]] = list(ast.iter_fields(node))
        return (
            truth.name(type(node)),
            tuple(
                (name, _syntax_shape(value))
                for name, value in fields
                # Python 3.12 adds this field; retain any actual type parameters.
                if name != "type_params" or value
            ),
        )
    if is_list_or_tuple(node):
        return tuple(_syntax_shape(value) for value in node)
    return node


# The installed graphql-core 3.3.1 Executor methods run as installed: the rebuilt
# function keeps their code object and swaps only its gather global, under the audited
# digest allowlist. No upstream source is stored here.
@functools.lru_cache(maxsize=8)
def _completion_method(method: "Callable[_P, _R]") -> "Callable[_P, _R]":
    """Rebuild the installed upstream method with only its gather dependency replaced.

    The selected body retains upstream field ordering, error paths and the release's
    error-collection protocol. No global in graphql-core is changed. The rebuilt
    function runs the installed method's own code object.
    """
    if not isinstance(method, FunctionType):
        raise TypeError(
            "Cannot start async generated-mutation completion: expected a Python function",
        )
    if hasattr(method, "__wrapped__"):
        raise RuntimeError(
            "Cannot start async generated-mutation completion with a wrapped graphql-core method; "
            "instrument the execution-context subclass instead of replacing the upstream method",
        )
    try:
        source = textwrap.dedent(inspect.getsource(method.__code__))
    except (OSError, TypeError) as error:
        raise RuntimeError(
            "Cannot start async generated-mutation completion without graphql-core source; "
            "install a supported source-bearing release. Queries and synchronous execution "
            "do not require this adapter",
        ) from error
    method_name = truth.name(method)
    function = ast.parse(source).body[0]
    for node in ast.walk(function):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and ast.get_docstring(node) is not None
        ):
            del node.body[0]
    digest = hashlib.sha256(repr(_syntax_shape(function)).encode()).hexdigest()
    if digest not in _AUDITED.get(method_name, frozenset()):
        raise RuntimeError(
            f"Cannot start async generated-mutation completion: unaudited graphql-core "
            f"{method_name} implementation. Use a supported release or audit its completion "
            "implementation",
        )
    namespace = dict(method.__globals__, gather_with_cancel=_gather_with_cancel)
    adapted = FunctionType(
        method.__code__,
        namespace,
        method_name,
        method.__defaults__,
        method.__closure__,
    )
    adapted.__kwdefaults__ = method.__kwdefaults__
    _ = functools.update_wrapper(adapted, method)
    # FunctionType preserves the audited callable code and call signature exactly, so the
    # rebuilt function takes the method's parameters and returns its result.
    return adapted


class _CompletionMethods(NamedTuple):
    """The three installed methods that join siblings, audited lazily for an owned window."""

    execute_fields: "_ExecuteFields"
    complete_async_iterator_value: "_CompleteAsyncIteratorValue"
    complete_iterable_value: "_CompleteIterableValue"


def _completion_methods() -> _CompletionMethods:
    return _CompletionMethods(
        _completion_method(StrawberryGraphQLCoreExecutionContext.execute_fields),
        _completion_method(_LIST_COMPLETION.complete_async_iterator_value),
        _completion_method(_LIST_COMPLETION.complete_iterable_value),
    )


class CompletionExecutionContext(StrawberryGraphQLCoreExecutionContext):
    """Use the installed engine's completion with owned concurrent-child cleanup."""

    def _owns_completion(self) -> bool:
        lease = _owner.get()
        return lease is not None and lease.held() is self

    @override
    def execute_fields(
        self,
        parent_type: "GraphQLObjectType",
        source_value: object,
        path: "Path | None",
        grouped_field_set: "GroupedFieldSet",
        position_context: "DeliveryGroupMap | None",
    ) -> "AwaitableOrValue[dict[str, object]]":
        """Supervise concurrent completion only inside its generated mutation owner."""
        if self._owns_completion():
            return _completion_methods().execute_fields(
                self,
                parent_type,
                source_value,
                path,
                grouped_field_set,
                position_context,
            )
        return super().execute_fields(
            parent_type,
            source_value,
            path,
            grouped_field_set,
            position_context,
        )

    @override
    async def complete_async_iterator_value(
        self,
        item_type: "_GraphQLOutputType",
        field_details_list: "FieldDetailsList",
        info: "GraphQLResolveInfo[object]",
        path: "Path",
        async_iterator: "AsyncIterator[object]",
        position_context: "DeliveryGroupMap | None",
    ) -> list[object]:
        """Join an async iterator's items under the owner's sibling rule."""
        if not self._owns_completion():
            return await _as_list_completion(super()).complete_async_iterator_value(
                item_type,
                field_details_list,
                info,
                path,
                async_iterator,
                position_context,
            )
        return await _completion_methods().complete_async_iterator_value(
            self,
            item_type,
            field_details_list,
            info,
            path,
            async_iterator,
            position_context,
        )

    @override
    def complete_iterable_value(
        self,
        item_type: "_GraphQLOutputType",
        field_details_list: "FieldDetailsList",
        info: "GraphQLResolveInfo[object]",
        path: "Path",
        items: "Iterable[object]",
        position_context: "DeliveryGroupMap | None",
    ) -> "AwaitableOrValue[list[object]]":
        """Join an iterable's items under the owner's sibling rule."""
        if self._owns_completion():
            return _completion_methods().complete_iterable_value(
                self,
                item_type,
                field_details_list,
                info,
                path,
                items,
                position_context,
            )
        return _as_list_completion(super()).complete_iterable_value(
            item_type,
            field_details_list,
            info,
            path,
            items,
            position_context,
        )

    @override
    def settle_in_background(self, awaitables: "list[Awaitable[object]]") -> None:
        """Record what the owned window settles in the background, so the window awaits it."""
        settling_lease = _settling.get() if self._owns_completion() else None
        settling = None if settling_lease is None else settling_lease.held()
        if settling is None:
            super().settle_in_background(awaitables)
            return
        known = set(self.background_futures)
        super().settle_in_background(awaitables)
        settling.extend(self.background_futures - known)
