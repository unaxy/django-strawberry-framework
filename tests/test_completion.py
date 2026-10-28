"""Completion source audits and revocable ownership that a wire response cannot inspect.

HTTP behavior belongs to examples/fakeshop/test_query/test_completion_lifecycle.py.
Here source refusal, metadata preservation and copied-context non-retention are
observable only through the private adapter and execution-context lease.
"""

import asyncio
import gc
import inspect
import weakref
from contextvars import copy_context
from types import FunctionType
from typing import cast
from unittest.mock import patch

import pytest
from graphql import ExecutionResult, GraphQLError
from graphql.execution.execute import ExecutionContext

from django_strawberry_framework import _completion as completion
from django_strawberry_framework import _graphql_core_patches as patches
from django_strawberry_framework.error_policy import DEFAULT_ERROR_POLICY
from django_strawberry_framework.extensions.error_policy import mask_execution_result


def execution_context() -> ExecutionContext:
    return object.__new__(ExecutionContext)


def test_owned_context_is_nested_revocable_and_not_retained() -> None:
    outer = execution_context()
    inner = execution_context()
    reference = weakref.ref(inner)
    assert completion._owner.get() is None
    with completion.owned_completion(outer):
        outer_lease = completion._owner.get()
        assert outer_lease is not None
        assert outer_lease.held() is outer
        with completion.owned_completion(inner):
            copied = copy_context()
            inner_lease = copied.run(completion._owner.get)
            assert inner_lease is not None
            assert inner_lease.held() is inner
        assert inner_lease.held() is None
        assert completion._owner.get() is outer_lease
        del inner
        gc.collect()
        assert reference() is None
    assert outer_lease.held() is None
    assert completion._owner.get() is None


@pytest.mark.parametrize("site", ["fields", "list"])
def test_adapted_method_preserves_code_metadata_and_private_globals(site: str) -> None:
    original = (
        ExecutionContext.execute_fields
        if site == "fields"
        else patches._upstream_captures().complete_list_value
    )
    assert isinstance(original, FunctionType)
    adapted = completion._completion_method(original)
    assert isinstance(original, FunctionType)
    assert isinstance(adapted, FunctionType)
    assert adapted.__code__ is original.__code__
    assert adapted.__defaults__ is original.__defaults__
    assert adapted.__kwdefaults__ is original.__kwdefaults__
    assert adapted.__closure__ is original.__closure__
    assert adapted.__annotations__ == original.__annotations__
    assert adapted.__name__ == original.__name__
    assert adapted.__qualname__ == original.__qualname__
    assert adapted.__module__ == original.__module__
    assert adapted.__doc__ == original.__doc__
    assert inspect.signature(adapted) == inspect.signature(original)
    assert adapted.__globals__ is not original.__globals__
    assert adapted.__globals__["gather"] is completion._gather_with_cancel
    assert original.__globals__["gather"] is asyncio.gather
    assert {
        key: value
        for key, value in cast("dict[str, object]", adapted.__globals__).items()
        if key != "gather"
    } == {
        key: value
        for key, value in cast("dict[str, object]", original.__globals__).items()
        if key != "gather"
    }


@pytest.mark.parametrize("unreadable", [False, True])
def test_unknown_or_unreadable_body_refuses_adaptation(*, unreadable: bool) -> None:
    with (
        patch.object(
            inspect,
            "getsource",
            side_effect=OSError("source unavailable") if unreadable else None,
            return_value="def execute_fields(self): pass",
        ),
        pytest.raises(RuntimeError, match=r"source-bearing|Unaudited"),
    ):
        completion._completion_method(ExecutionContext.execute_fields)


def test_non_python_callable_refuses_adaptation() -> None:
    with pytest.raises(TypeError, match="Python function"):
        completion._completion_method(len)


async def test_overlapping_owners_keep_distinct_leases() -> None:
    ready = asyncio.Event()
    release = asyncio.Event()
    first = execution_context()
    second = execution_context()

    async def other() -> None:
        with completion.owned_completion(second):
            lease = completion._owner.get()
            assert lease is not None
            assert lease.held() is second
            ready.set()
            await release.wait()
            assert lease.held() is second
        assert lease.held() is None

    with completion.owned_completion(first):
        lease = completion._owner.get()
        task = asyncio.create_task(other())
        await ready.wait()
        assert lease is not None
        assert lease.held() is first
        release.set()
        await task
        assert completion._owner.get() is lease
    assert lease.held() is None


@pytest.mark.parametrize("populated", [False, True])
def test_snapshot_detaches_lists_preserving_error_identity(*, populated: bool) -> None:

    deliberate = GraphQLError("deliberate", extensions={"code": "EXPECTED"})
    errors = [deliberate] if populated else []
    result = ExecutionResult(data={"value": None}, errors=errors)
    snapshot = mask_execution_result(result, DEFAULT_ERROR_POLICY, snapshot=True)
    assert snapshot is not result
    assert snapshot.data is result.data
    assert snapshot.errors is not errors
    assert snapshot.errors == errors
    if populated:
        assert snapshot.errors is not None
        assert snapshot.errors[0] is deliberate
    errors.append(GraphQLError("late", original_error=ValueError("late")))
    assert snapshot.errors == ([deliberate] if populated else [])
