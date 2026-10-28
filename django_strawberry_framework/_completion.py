"""Join graphql-core-owned concurrent completion before returning to its owner."""

import asyncio
import functools
import hashlib
import inspect
import textwrap
from contextlib import contextmanager
from contextvars import ContextVar
from types import FunctionType, MappingProxyType
from typing import TYPE_CHECKING, ParamSpec, TypeVar, cast

from graphql.execution.execute import ExecutionContext
from typing_extensions import override

from . import _graphql_core_patches as patches
from .utils import truth
from .utils.operation_lease import OperationLease

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Awaitable, Callable, Generator, Iterable

    from graphql import FieldNode, GraphQLList, GraphQLObjectType, GraphQLResolveInfo
    from graphql.pyutils import AwaitableOrValue, Path

    from ._graphql_core_patches import _GraphQLOutputType

_owner: ContextVar[OperationLease[ExecutionContext] | None] = ContextVar(
    "completion_owner",
    default=None,
)


@contextmanager
def owned_completion(context: ExecutionContext) -> "Generator[None]":
    """Mark only this generated-mutation context's async completion window."""
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
    """Cancel abandoned siblings and finish their cleanup before propagating failure.

    Adapted from graphql-core 3.3.0 graphql.pyutils.gather_with_cancel (MIT).
    BaseException includes caller cancellation; the shielded drain keeps repeated
    cancellation from ending the owning mutation window before cleanup finishes.
    """
    futures = [asyncio.ensure_future(value) for value in awaitables]
    try:
        return await asyncio.gather(*futures)
    except BaseException:
        for future in futures:
            if not future.done():
                _ = future.cancel()
        drain = asyncio.gather(*futures, return_exceptions=True)
        cancelled = False
        while not drain.done():
            try:
                _ = await asyncio.shield(drain)
            except asyncio.CancelledError:  # noqa: PERF203 - cleanup must outlast repeated cancellation
                cancelled = True
        if cancelled:
            raise asyncio.CancelledError from None
        raise


# Complete stable support census (normalized source, not version-only approval):
# 3.2.0, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.5, 3.2.6, 3.2.7, 3.2.8,
# 3.2.9: b9ac004a / dfb41f48; 3.2.10, 3.2.11, 3.2.12: b9ac004a / c72c56c5
# (CollectedErrors paths); 3.2.13: 10c99f6c / 262a0e64 (private docstrings).
# Hash prefixes name field/list bodies below; all retain the two gather sites.
_AUDITED = MappingProxyType(
    {
        "execute_fields": frozenset(
            {
                "10c99f6c2a3610deb7989cb148a32fb4382667186d67e10a96db4278e88cdf95",
                "b9ac004a5131ec1467c720889724deecd15c5f357248f8d383be9e6e0c6e785f",
            },
        ),
        "complete_list_value": frozenset(
            {
                "262a0e644fd4b2d17000d7238860d29bf980deb05797cdc731e43814a33dbdb2",
                "c72c56c5ad0968d85ff1d636602c0656c0326c6c49595d4580239888a5c7adf8",
                "dfb41f48d4533ca92a1f216d29c28b06a1e31854ca5cf2052ff8d2d0dc39236e",
            },
        ),
    },
)

_P = ParamSpec("_P")
_R = TypeVar("_R")


# Adapted graphql-core 3.2.0-3.2.13 graphql/execution/execute.py method bodies:
# retain installed code and replace only their gather dependency, under the audited body allowlist.
def _completion_method(method: "Callable[_P, _R]") -> "Callable[_P, _R]":
    """Adapt the installed upstream method by replacing only its gather dependency.

    The selected body retains upstream field ordering, error paths and version's
    error-collection protocol. No global in graphql-core is changed. The adapted
    bodies originate in graphql-core 3.2.0-3.2.13 graphql.execution.execute (MIT).
    """
    if not isinstance(method, FunctionType):
        raise TypeError("Cannot supervise graphql-core completion: expected a Python function")
    try:
        source = textwrap.dedent(inspect.getsource(method))
    except (OSError, TypeError) as error:
        raise RuntimeError(
            "Cannot inspect graphql-core completion source; install a supported source-bearing release",
        ) from error
    method_name = truth.name(method)
    digest = hashlib.sha256(source.strip().encode()).hexdigest()
    if digest not in _AUDITED.get(method_name, frozenset()):
        raise RuntimeError(
            f"Unaudited graphql-core {method_name} body; use a supported release "
            "or audit its completion implementation before enabling generated mutations",
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
    # FunctionType preserves the audited callable code and call signature exactly.
    return cast("Callable[_P, _R]", adapted)


_execute_fields = _completion_method(ExecutionContext.execute_fields)
_complete_list_value = _completion_method(patches._upstream_captures().complete_list_value)


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
            return _execute_fields(self, parent_type, source_value, path, fields)
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
            upstream = cast("patches._CompleteListValue", ExecutionContext.complete_list_value)
            return upstream(self, return_type, field_nodes, info, path, result)
        if patches._patch_is_installed():
            return patches._complete_list_value_with_adapter(
                self,
                return_type,
                field_nodes,
                info,
                path,
                result,
                _complete_list_value,
            )
        return _complete_list_value(self, return_type, field_nodes, info, path, result)
