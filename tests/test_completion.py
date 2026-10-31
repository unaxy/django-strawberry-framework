"""Completion source audits and revocable ownership that a wire response cannot inspect.

HTTP behavior belongs to examples/fakeshop/test_query/test_completion_lifecycle.py.
Here source refusal, metadata preservation and copied-context non-retention are
observable only through the private adapter and execution-context lease.
"""

import ast
import asyncio
import functools
import gc
import inspect
import textwrap
import weakref
from collections.abc import Iterator
from contextvars import copy_context
from types import FunctionType
from unittest.mock import patch

import pytest
from graphql import ExecutionResult, GraphQLError
from graphql.execution.execute import ExecutionContext

from django_strawberry_framework import _completion as completion
from django_strawberry_framework import _graphql_core_patches as patches
from django_strawberry_framework.error_policy import DEFAULT_ERROR_POLICY
from django_strawberry_framework.extensions.error_policy import mask_execution_result
from tests._subprocess import run_in_fresh_process


@pytest.fixture(autouse=True)
def clear_completion_audit_cache() -> Iterator[None]:
    completion._completion_method.cache_clear()
    yield
    completion._completion_method.cache_clear()


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
    adapted_globals: dict[str, object] = dict(adapted.__globals__)
    original_globals: dict[str, object] = dict(original.__globals__)
    assert {key: value for key, value in adapted_globals.items() if key != "gather"} == {
        key: value for key, value in original_globals.items() if key != "gather"
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
        pytest.raises(RuntimeError, match=r"source-bearing|unaudited"),
    ):
        completion._completion_method(ExecutionContext.execute_fields)


@pytest.mark.parametrize("site", ["fields", "list"])
def test_docstring_and_formatting_changes_preserve_the_audited_syntax(site: str) -> None:
    original = (
        ExecutionContext.execute_fields
        if site == "fields"
        else patches._upstream_captures().complete_list_value
    )
    assert isinstance(original, FunctionType)
    function = ast.parse(textwrap.dedent(inspect.getsource(original.__code__))).body[0]
    assert isinstance(function, ast.FunctionDef)
    for node in ast.walk(function):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            documentation = ast.Expr(value=ast.Constant(value="Revised private documentation."))
            if ast.get_docstring(node) is None:
                node.body.insert(0, documentation)
            else:
                node.body[0] = documentation
    source = ast.unparse(function) + "\n# Local packaging comment.\n"
    with patch.object(inspect, "getsource", return_value=source) as read_source:
        adapted = completion._completion_method(original)
    read_source.assert_called_once_with(original.__code__)
    assert isinstance(adapted, FunctionType)
    assert adapted.__code__ is original.__code__


def test_wrapped_method_is_refused_instead_of_auditing_its_wrapped_body() -> None:
    @functools.wraps(ExecutionContext.execute_fields)
    def instrumented() -> None:
        """An APM wrapper is a different function even with upstream metadata."""

    with (
        patch.object(inspect, "getsource") as read_source,
        pytest.raises(RuntimeError, match="wrapped graphql-core method"),
    ):
        completion._completion_method(instrumented)
    read_source.assert_not_called()


def test_missing_optional_patch_capture_names_the_mandatory_boundary() -> None:
    with (
        patch.object(patches, "_original_complete_list_value", None),
        pytest.raises(RuntimeError, match="APPLY_UPSTREAM_PATCHES does not disable"),
    ):
        completion._completion_methods()


@pytest.mark.parametrize("change", ["unreadable", "different"])
def test_package_import_does_not_audit_mutation_completion(change: str) -> None:
    run_in_fresh_process(
        textwrap.dedent(
            f"""
            import inspect
            from unittest.mock import patch
            original = inspect.getsource
            def source(value):
                if getattr(value, "co_name", getattr(value, "__name__", None)) in {{
                    "execute_fields", "complete_list_value"
                }}:
                    if {change!r} == "unreadable":
                        raise OSError("sourceless deployment")
                    return "def execute_fields(self): pass"
                return original(value)
            with patch.object(inspect, "getsource", side_effect=source):
                from django_strawberry_framework import DjangoType, DjangoSchema
                assert DjangoType is not None and DjangoSchema is not None
            """,
        ),
        fakeshop=False,
        timeout=30,
    )


async def test_closing_a_suspended_gather_does_not_await_during_generator_exit() -> None:
    loop = asyncio.get_running_loop()
    first: asyncio.Future[object] = loop.create_future()
    second: asyncio.Future[object] = loop.create_future()
    coroutine = completion._gather_with_cancel(first, second)
    assert coroutine.send(None) is not None
    try:
        coroutine.close()
        assert not first.cancelled()
        assert not second.cancelled()
    finally:
        for future in (first, second):
            if not future.done():
                future.set_result(None)
        await asyncio.sleep(0)


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
