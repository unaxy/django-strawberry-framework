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
from typing import TYPE_CHECKING, NamedTuple, ParamSpec, TypeVar, cast

from graphql.execution.execute import ExecutionContext
from typing_extensions import override

from . import _graphql_core_patches as patches
from .utils import truth
from .utils._narrowing import is_list_or_tuple
from .utils.operation_lease import OperationLease

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Awaitable, Callable, Generator, Iterable

    from graphql import FieldNode, GraphQLList, GraphQLObjectType, GraphQLResolveInfo
    from graphql.pyutils import AwaitableOrValue, Path

    from ._graphql_core_patches import _GraphQLOutputType

    _ExecuteFields = Callable[
        [
            ExecutionContext,
            GraphQLObjectType,
            object,
            Path | None,
            dict[str, list[FieldNode]],
        ],
        AwaitableOrValue[dict[str, object]],
    ]

_owner: ContextVar[OperationLease[ExecutionContext] | None] = ContextVar(
    "completion_owner",
    default=None,
)


@contextmanager
def owned_completion(context: ExecutionContext) -> "Generator[None]":
    """Mark only this generated-mutation context's async completion window."""
    _ = _completion_methods()
    lease = OperationLease(context)
    token = _owner.set(lease)
    try:
        yield
    finally:
        lease.close()
        _owner.reset(token)


# Adapted from graphql-core 3.3.0, graphql/pyutils/gather_with_cancel.py (MIT).
# The complete upstream license ships in LICENSE.graphql-core.
async def _gather_with_cancel(*awaitables: "Awaitable[object]") -> list[object]:
    """Join siblings before propagating failure; cancel them only on caller cancellation.

    Adapted from graphql-core 3.3.0 graphql.pyutils.gather_with_cancel (MIT).
    Ordinary failures must not cancel a shared DataLoader future that a surviving
    branch also awaits. The shielded drain keeps repeated caller cancellation from
    ending the owning mutation window before cleanup finishes. GeneratorExit is
    deliberately outside this handler: closing a coroutine cannot await cleanup.
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
# 3.2.0, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.5, 3.2.6, 3.2.7, 3.2.8,
# 3.2.9 share one pair; 3.2.10-3.2.13 share the CollectedErrors list body.
# Comments, formatting and private docstrings do not affect the adapted dependency.
_AUDITED = MappingProxyType(
    {
        "execute_fields": frozenset(
            {
                "ac08e0c8950cb9e537af7ee8c0d3c19f022e94000de2631ecd6edd53f28e38e2",
            },
        ),
        "complete_list_value": frozenset(
            {
                "a9b89d6f1051eb73f349bb2bd575871d895626c9205b313d82d496067968bb5c",
                "0c89fe9a284dfc9edd7d0cb10a4190caadd7e1d1b90d08751a8be1fa2cfba0aa",
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


# Adapted graphql-core 3.2.0-3.2.13 graphql/execution/execute.py method bodies:
# retain installed code and replace only their gather dependency, under the audited body allowlist.
@functools.lru_cache(maxsize=8)
def _completion_method(method: "Callable[_P, _R]") -> "Callable[_P, _R]":
    """Adapt the installed upstream method by replacing only its gather dependency.

    The selected body retains upstream field ordering, error paths and version's
    error-collection protocol. No global in graphql-core is changed. The adapted
    bodies originate in graphql-core 3.2.0-3.2.13 graphql.execution.execute (MIT).
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
            "implementation. APPLY_UPSTREAM_PATCHES does not disable this transaction boundary",
        )
    namespace = dict(method.__globals__, gather=_gather_with_cancel)
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
    """The two installed methods, audited lazily for an owned mutation window."""

    execute_fields: "_ExecuteFields"
    complete_list_value: "patches._CompleteListValue"


def _completion_methods() -> _CompletionMethods:
    try:
        list_method = patches._upstream_captures().complete_list_value
    except RuntimeError as error:
        raise RuntimeError(
            "Cannot start async generated-mutation completion: graphql-core completion "
            "dependencies are unavailable. Use a supported graphql-core release; "
            "APPLY_UPSTREAM_PATCHES does not disable this transaction boundary",
        ) from error
    return _CompletionMethods(
        _completion_method(ExecutionContext.execute_fields),
        _completion_method(list_method),
    )


class CompletionExecutionContext(ExecutionContext):
    """Use the installed engine's completion with owned concurrent-child cleanup."""

    @override
    def execute_fields(
        self,
        parent_type: "GraphQLObjectType",
        source_value: object,
        path: "Path | None",
        fields: "dict[str, list[FieldNode]]",
    ) -> "AwaitableOrValue[dict[str, object]]":
        """Supervise concurrent completion only inside its generated mutation owner."""
        lease = _owner.get()
        if lease is not None and lease.held() is self:
            return _completion_methods().execute_fields(
                self,
                parent_type,
                source_value,
                path,
                fields,
            )
        return super().execute_fields(parent_type, source_value, path, fields)

    @override
    def complete_list_value(
        self,
        return_type: "GraphQLList[_GraphQLOutputType]",
        field_nodes: "list[FieldNode]",
        info: "GraphQLResolveInfo",
        path: "Path",
        result: "AsyncIterable[object] | Iterable[object]",
    ) -> "AwaitableOrValue[list[object]]":
        """Preserve the independently gated QuerySet and AsyncIterable adapter."""
        lease = _owner.get()
        if lease is None or lease.held() is not self:
            # Upstream leaves GraphQLWrappingType bare; this is the same runtime signature.
            upstream = cast("patches._BoundCompleteListValue", super().complete_list_value)
            return upstream(return_type, field_nodes, info, path, result)
        complete_list_value = _completion_methods().complete_list_value
        if patches._patch_is_installed():
            return patches._complete_list_value_with_adapter(
                self,
                return_type,
                field_nodes,
                info,
                path,
                result,
                complete_list_value,
            )
        return complete_list_value(self, return_type, field_nodes, info, path, result)
