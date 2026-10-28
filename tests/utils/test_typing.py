"""Typing utility tests for async-callable detection and Strawberry, Python, and GraphQL unwrapping.

Wrapper peeling and cyclic-of_type refusal have no selection-set spelling.
Async field colour on the wire lives in
``examples/fakeshop/test_query/test_list_field_async_api.py``.
"""

import functools
import typing
from types import SimpleNamespace
from typing import Any

import pytest
import strawberry
from asgiref.sync import markcoroutinefunction
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInputField,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLNullableType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLString,
    InlineFragmentNode,
    OperationDefinitionNode,
    parse,
)
from strawberry.types.base import StrawberryList
from typing_extensions import Self, override

import django_strawberry_framework.utils.typing as typing_module
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils._narrowing import class_dict, require, require_instance
from django_strawberry_framework.utils.typing import (
    MAX_TYPE_WRAPPER_DEPTH,
    _callable_inspection_target,
    inline_fragment_type_condition,
    is_async_callable,
    is_marked_coroutine_function,
    published_argument,
    published_python_name,
    schema_config_from_info,
    strawberry_schema_from_info,
    strawberry_schema_from_schema,
    unwrap_container_type,
    unwrap_graphql_type,
    unwrap_non_null,
    unwrap_return_type,
)
from tests._info import make_info


def test_typing_exports_all() -> None:
    """``django_strawberry_framework.utils.typing`` exports expected public symbols."""
    assert typing_module.__all__ == (
        "MAX_TYPE_WRAPPER_DEPTH",
        "MISSING_ATTRIBUTE",
        "call_forwarded",
        "graphql_fields",
        "graphql_input_fields",
        "graphql_type_of",
        "inline_fragment_type_condition",
        "is_async_callable",
        "is_graphql_list",
        "is_marked_coroutine_function",
        "object_result",
        "published_argument",
        "published_python_name",
        "return_type_of",
        "schema_config_from_info",
        "strawberry_schema_from_info",
        "strawberry_schema_from_schema",
        "unwrap_container_type",
        "unwrap_graphql_type",
        "unwrap_non_null",
        "unwrap_return_type",
    )


def test_inline_fragment_type_condition_reads_a_typeless_fragment_as_none() -> None:
    """A typed inline fragment yields its named type; a typeless one (no ``on``) yields ``None``."""
    operation = parse("{ ... on Query { a } ... @include(if: true) { a } }").definitions[0]
    assert isinstance(operation, OperationDefinitionNode)
    typed, typeless = operation.selection_set.selections
    assert isinstance(typed, InlineFragmentNode)
    assert isinstance(typeless, InlineFragmentNode)

    condition = inline_fragment_type_condition(typed)
    assert condition is not None
    assert condition.name.value == "Query"
    assert inline_fragment_type_condition(typeless) is None


def test_unwrap_return_type_handles_typing_list() -> None:
    """``list[T]`` annotation unwraps to ``T``."""

    class Inner:
        pass

    assert unwrap_return_type(list[Inner]) is Inner


def test_unwrap_return_type_handles_bare_typing_list() -> None:
    """``typing.List`` (no parameter) returns ``Any``.

    ``get_origin(typing.List) is list`` so the list branch fires, but
    ``get_args(typing.List)`` returns ``()``. Indexing ``get_args(rt)[0]``
    would ``IndexError`` here; the helper returns ``Any``
    as the "unknown element type" sentinel.
    """
    # basedpyright: the bare deprecated ``typing.List`` alias is the input under test; ``list``
    # is covered by the next test and cannot reach the ``get_args(...) == ()`` list-origin branch
    assert unwrap_return_type(typing.List) is Any  # noqa: UP006  # pyright: ignore[reportDeprecated]


def test_unwrap_return_type_handles_bare_builtin_list() -> None:
    """A bare ``list`` (no parameter) returns ``Any``.

    ``get_origin(list)`` is ``None`` (a bare builtin is not a generic
    alias), so the list-origin branch does not fire and the dedicated
    ``rt is list`` branch returns the same ``Any`` sentinel as
    ``typing.List``.
    """
    assert unwrap_return_type(list) is Any


def test_unwrap_return_type_handles_strawberry_of_type() -> None:
    """A Strawberry-style wrapper exposing ``of_type`` unwraps to the inner type."""

    class Inner:
        pass

    class FakeStrawberryList:
        of_type = Inner

    assert unwrap_return_type(FakeStrawberryList()) is Inner


def test_unwrap_return_type_peels_only_one_layer() -> None:
    """The annotation helper keeps nested wrappers for callers to inspect."""

    class Inner:
        pass

    class Outer:
        of_type = list[Inner]

    assert unwrap_return_type(Outer()) == list[Inner]


def test_unwrap_graphql_type_peels_all_of_type_layers() -> None:
    """The GraphQL helper recursively unwraps wrapper stacks to the leaf type."""

    class Inner:
        pass

    class NonNull:
        def __init__(self, of_type: object) -> None:
            self.of_type = of_type

    class List:
        def __init__(self, of_type: object) -> None:
            self.of_type = of_type

    wrapped = NonNull(List(NonNull(Inner)))

    assert unwrap_graphql_type(wrapped) is Inner


def test_unwrap_graphql_type_peels_a_deep_but_finite_stack() -> None:
    """A stack just under the ceiling still peels to the leaf (no false overrun)."""

    class Inner:
        pass

    class Wrap:
        def __init__(self, of_type: object) -> None:
            self.of_type = of_type

    wrapped = Inner
    for _ in range(MAX_TYPE_WRAPPER_DEPTH - 1):
        wrapped = Wrap(wrapped)

    assert unwrap_graphql_type(wrapped) is Inner


def test_unwrap_graphql_type_raises_on_cyclic_of_type_stack() -> None:
    """A cyclic ``of_type`` chain hits the bound and fails loud instead of spinning."""

    class Cyclic:
        @property
        def of_type(self) -> Self:
            return self  # never bottoms out

    with pytest.raises(RuntimeError, match="cyclic or corrupt"):
        unwrap_graphql_type(Cyclic())


def test_unwrap_container_type_peels_containers_but_not_a_leaf_with_of_type() -> None:
    """Only ``StrawberryContainer`` layers peel; a leaf exposing ``of_type`` is NOT descended.

    The load-bearing distinction from ``unwrap_graphql_type``'s bare-``hasattr``
    contract: an ``Edge`` subclass that happens to carry an
    ``of_type`` attribute must be returned as the leaf, not peeled into.
    """

    class Edge:
        of_type = "not a wrapper"

    assert unwrap_container_type(StrawberryList(of_type=Edge)) is Edge
    assert unwrap_container_type(Edge) is Edge


def test_unwrap_container_type_raises_on_cyclic_container_stack() -> None:
    """A cyclic container chain hits the Power-of-Ten bound and fails loud."""
    cyclic = StrawberryList(of_type=str)
    cyclic.of_type = cyclic  # never bottoms out

    with pytest.raises(RuntimeError, match="cyclic or corrupt"):
        unwrap_container_type(cyclic)


def test_unwrap_return_type_returns_direct_class_when_unwrapped() -> None:
    """A bare class with no wrapper passes through unchanged."""

    class Inner:
        pass

    assert unwrap_return_type(Inner) is Inner


def test_unwrap_graphql_type_passes_through_none() -> None:
    """``None`` carries no ``of_type`` attribute and passes through unchanged.

    The optimizer's ``_walk_gql_type`` recursion at
    ``optimizer/extension.py`` feeds ``getattr(field_obj, "type", None)``
    into this helper; the post-peel ``type_name is None`` gate downstream
    relies on the passthrough holding so the recursion terminates cleanly.
    """
    assert unwrap_graphql_type(None) is None


# ---------------------------------------------------------------------------
# is_async_callable -- shared by the field factories + GlobalID-callable validator
# ---------------------------------------------------------------------------


# These callables are never invoked; ``is_async_callable`` only reads their
# coroutine-function flags. (Test code is outside the coverage source.)
async def _async_fn() -> None: ...


def _sync_fn() -> None: ...


class _AsyncCallable:
    async def __call__(self) -> None: ...


class _SyncCallable:
    def __call__(self) -> None: ...


class _MethodHolder:
    @staticmethod
    async def async_static() -> None: ...

    @staticmethod
    def sync_static() -> None: ...

    @classmethod
    async def async_cls(cls) -> None: ...


# The RAW descriptor objects (as seen when a ``@staticmethod async def`` resolver
# is referenced by name INSIDE its own class body, e.g. ``resolver=async_static``);
# attribute access via the class would unwrap these to the underlying function.
_async_static_obj = require(class_dict(_MethodHolder)["async_static"], callable)
_sync_static_obj = class_dict(_MethodHolder)["sync_static"]
_async_cls_obj = class_dict(_MethodHolder)["async_cls"]
_async_static_partial_obj = staticmethod(functools.partial(_AsyncCallable()))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (_async_fn, True),
        (_sync_fn, False),
        (_AsyncCallable, False),  # class itself: instantiation is sync
        (_AsyncCallable(), True),  # async ``__call__`` instance
        (_SyncCallable, False),  # class itself: instantiation is sync
        (_SyncCallable(), False),
        (functools.partial(_async_fn), True),  # partial around an async function
        (functools.partial(_AsyncCallable), False),  # partial around a class constructor
        (functools.partial(_AsyncCallable()), True),  # partial around an async instance
        (functools.partial(_SyncCallable), False),  # partial around a class constructor
        (functools.partial(_sync_fn), False),
        (_async_static_obj, True),  # raw ``staticmethod`` descriptor around an async def
        (_sync_static_obj, False),
        (_async_cls_obj, False),  # raw ``classmethod`` descriptors are not callable
        (functools.partial(_async_static_obj), True),  # partial around a staticmethod descriptor
        (_async_static_partial_obj, True),  # staticmethod descriptor around a partial instance
    ],
)
def test_is_async_callable_sees_through_supported_wrappers(
    value: object,
    *,
    expected: bool,
) -> None:
    """The predicate sees through supported async callable wrappers.

    These are the shapes ``inspect.iscoroutinefunction`` alone misses; both the
    public field factories and the GlobalID-callable validator depend on the
    shared predicate catching them at construction time. The raw ``staticmethod``
    case is reachable when a class-body resolver references the decorated method
    by name. The classmethod case pins the opposite boundary: its raw descriptor
    is not callable, even when its underlying function is async.
    """
    assert is_async_callable(value) is expected


def _marked_sync_fn() -> None:
    """Sync body Django is told to await through the ``markcoroutinefunction`` marker."""


markcoroutinefunction(_marked_sync_fn)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (_async_fn, True),
        (_marked_sync_fn, True),  # sync def carrying the marker Django honours
        (_sync_fn, False),
    ],
)
def test_is_marked_coroutine_function_reads_the_marker(value: object, *, expected: bool) -> None:
    """The detector answers as Django's own does, so a marked sync callable is async.

    Django awaits a view or a middleware on this detector's word, and below Python
    3.12 ``inspect.iscoroutinefunction`` does not read the marker, so the row holds
    on every supported Python only through asgiref's shim.
    """
    assert is_marked_coroutine_function(value) is expected


def test_strawberry_schema_from_info_and_schema() -> None:
    """Private ``_strawberry_schema`` digs stay on the shared typing helpers."""
    inner = object()
    assert strawberry_schema_from_schema(SimpleNamespace(_strawberry_schema=inner)) is inner
    assert strawberry_schema_from_schema(inner) is inner
    null_schema = SimpleNamespace(_strawberry_schema=None)
    assert strawberry_schema_from_schema(null_schema) is null_schema
    wrapped = SimpleNamespace(schema=SimpleNamespace(_strawberry_schema=inner))
    assert strawberry_schema_from_info(wrapped) is inner
    assert strawberry_schema_from_info(SimpleNamespace(schema=SimpleNamespace())) is None
    assert strawberry_schema_from_info(SimpleNamespace()) is None


def test_strawberry_schema_from_info_reads_both_info_flavors() -> None:
    """Both resolver ``info`` flavors over one schema resolve to that Strawberry ``Schema``.

    A Strawberry ``Info`` names the Strawberry ``Schema`` as ``info.schema``; the
    graphql-core ``GraphQLResolveInfo`` under it names the graphql-core schema, which
    carries the Strawberry one as ``_strawberry_schema``. An info with no schema reads
    as ``None``.
    """
    info = make_info()
    schema = info.schema
    assert isinstance(schema, strawberry.Schema)
    assert strawberry_schema_from_info(info) is schema
    assert strawberry_schema_from_info(info._raw_info) is schema
    assert strawberry_schema_from_info(SimpleNamespace(schema=None)) is None


def test_schema_config_from_info_prefers_wrapped_then_direct() -> None:
    """Plan-time ``_strawberry_schema.config`` wins over bare ``schema.config``."""
    wrapped = SimpleNamespace(
        schema=SimpleNamespace(
            _strawberry_schema=SimpleNamespace(config=SimpleNamespace(relay_max_results=7)),
            config=SimpleNamespace(relay_max_results=99),
        ),
    )
    wrapped_config = schema_config_from_info(wrapped)
    assert wrapped_config is not None
    assert wrapped_config.relay_max_results == 7
    direct = SimpleNamespace(schema=SimpleNamespace(config=SimpleNamespace(name_converter="nc")))
    direct_config = schema_config_from_info(direct)
    assert direct_config is not None
    assert direct_config.name_converter == "nc"
    assert schema_config_from_info(SimpleNamespace(schema=SimpleNamespace())) is None
    assert schema_config_from_info(SimpleNamespace()) is None
    assert schema_config_from_info(None) is None


def test_schema_config_from_info_explicit_none_wrapped_falls_back_to_direct() -> None:
    """An explicitly present ``_strawberry_schema=None`` falls through to ``schema.config``.

    ``getattr`` cannot distinguish a missing attribute from an attribute whose
    value is ``None``, so this pins the contract for the value-is-``None`` case:
    the wrapped dig yields ``None`` and ``schema_config_from_info`` must still
    reach the bare ``schema.config`` fallback rather than short-circuiting.
    """
    info = SimpleNamespace(
        schema=SimpleNamespace(
            _strawberry_schema=None,
            config=SimpleNamespace(relay_max_results=42),
        ),
    )
    assert strawberry_schema_from_info(info) is None
    config = schema_config_from_info(info)
    assert config is not None
    assert config.relay_max_results == 42
    # And when both the wrapped dig and the direct config are absent, ``None``.
    no_config = SimpleNamespace(schema=SimpleNamespace(_strawberry_schema=None))
    assert schema_config_from_info(no_config) is None


def test_unwrap_graphql_type_accepts_exact_wrapper_depth() -> None:
    """The configured depth is inclusive; only a longer chain is corrupt."""

    class Inner:
        pass

    class Wrap:
        def __init__(self, of_type: object) -> None:
            self.of_type = of_type

    wrapped = Inner
    for _ in range(MAX_TYPE_WRAPPER_DEPTH):
        wrapped = Wrap(wrapped)

    assert unwrap_graphql_type(wrapped) is Inner


def test_unwrap_container_type_accepts_exact_wrapper_depth() -> None:
    """The configured depth is inclusive for Strawberry containers too."""

    class Inner:
        pass

    wrapped = Inner
    for _ in range(MAX_TYPE_WRAPPER_DEPTH):
        wrapped = StrawberryList(of_type=wrapped)

    assert unwrap_container_type(wrapped) is Inner


def test_unwrap_return_type_preserves_none_inner_type() -> None:
    """An ``of_type`` wrapper may carry ``None`` while being resolved."""
    assert unwrap_return_type(SimpleNamespace(of_type=None)) is None


def test_callable_inspection_target_accepts_exact_wrapper_depth() -> None:
    """The configured depth is inclusive for partial/staticmethod chains."""

    def inner() -> int:
        return 42

    wrapped = inner
    for _ in range(MAX_TYPE_WRAPPER_DEPTH):
        wrapped = functools.partial(wrapped)

    assert _callable_inspection_target(wrapped) is inner


def test_callable_inspection_target_raises_on_cyclic_partial_stack() -> None:
    """A cyclic partial wrapper stack raises RuntimeError instead of hanging."""

    class CyclicPartial(functools.partial[int]):
        @property
        @override
        def func(self) -> Self:
            return self

    p = CyclicPartial(lambda: 0)
    with pytest.raises(RuntimeError, match="cyclic or corrupt"):
        _callable_inspection_target(p)


def test_callable_inspection_target_raises_on_cyclic_staticmethod_stack() -> None:
    """A cyclic staticmethod wrapper stack raises RuntimeError instead of hanging."""
    # ``staticmethod`` is not subscriptable at runtime before Python 3.11 and a class base is
    # evaluated there, so the parametrized type is carried by an annotated local alias.
    _StaticMethodBase: type[staticmethod[[], int]] = staticmethod

    class CyclicStaticMethod(_StaticMethodBase):
        @property
        @override
        def __func__(self) -> Self:
            return self

    sm = CyclicStaticMethod(lambda: 0)
    with pytest.raises(RuntimeError, match="cyclic or corrupt"):
        _callable_inspection_target(sm)


def test_is_async_callable_raises_on_cyclic_wrapper_stack() -> None:
    """The async predicate fails loud via RuntimeError when given a cyclic callable."""

    class CyclicPartial(functools.partial[int]):
        @property
        @override
        def func(self) -> Self:
            return self

    p = CyclicPartial(lambda: 0)
    with pytest.raises(RuntimeError, match="cyclic or corrupt"):
        is_async_callable(p)


def test_is_async_callable_sees_through_an_async_call_metaclass() -> None:
    """A class whose metaclass carries ``async def __call__`` is async to CALL.

    Calling a class dispatches through ``type(target).__call__`` -- the
    metaclass -- not the class body's ``__call__`` (that one is instance-call
    semantics). A predicate that hard-returned ``False`` for every class would
    violate the "calling ``value`` yields a coroutine" contract for a
    metaclass-async class, which yields a coroutine when called, and such a
    class passed as a ``globalid_strategy`` encoder would slip past the
    build-time sync-ness gate (``types/base.py::_validate_globalid_callable``)
    to fail per request.
    Plain classes keep the pinned "instantiation is sync" answer because
    ``type.__call__`` is sync, and a class body's ``__call__`` never answers
    for the class itself.
    """

    class _AsyncMeta(type):
        @override
        async def __call__(cls) -> None: ...

    class _UsesAsyncMeta(metaclass=_AsyncMeta): ...

    class _InstanceAsyncCallable:
        async def __call__(self) -> None: ...

    class _ClassDictAsyncCall:
        # Instances are async-callable; instantiation stays sync.
        __call__ = _async_fn

    assert is_async_callable(_UsesAsyncMeta) is True
    assert is_async_callable(functools.partial(_UsesAsyncMeta)) is True
    assert is_async_callable(_InstanceAsyncCallable) is False
    assert is_async_callable(_ClassDictAsyncCall) is False
    assert is_async_callable(_InstanceAsyncCallable()) is True


def test_is_async_callable_ignores_the_metaclass_call_of_an_instance_class() -> None:
    """An instance is called through its class's MRO, never its class's metaclass.

    ``_UsesAsyncMeta``'s metaclass carries ``async def __call__`` (calling the
    class is async), but the class itself declares no ``__call__``, so an
    instance of it is not callable at all and is not an async callable.
    """

    class _AsyncMeta(type):
        @override
        async def __call__(cls) -> None: ...

    class _UsesAsyncMeta(metaclass=_AsyncMeta): ...

    instance = object.__new__(_UsesAsyncMeta)
    assert not callable(instance)
    assert is_async_callable(instance) is False


def test_unwrap_non_null_peels_only_non_null_layers() -> None:
    """The narrow peel stops at the list wrapper its callers must still see.

    ``unwrap_graphql_type`` would peel the ``GraphQLList`` too, which is exactly
    why the resource policy's list-vs-connection classification could not use it
    and grew raw ``while isinstance`` loops instead.
    """
    # graphql-core's ``GraphQLNamedType.__new__`` widens every built-in scalar to its base.
    assert isinstance(GraphQLString, GraphQLScalarType)
    inner = GraphQLList(GraphQLNonNull(GraphQLString))
    assert unwrap_non_null(GraphQLNonNull(inner)) is inner
    assert unwrap_non_null(inner) is inner
    assert unwrap_non_null(GraphQLString) is GraphQLString


def test_unwrap_non_null_raises_on_a_cyclic_non_null_chain() -> None:
    """A cyclic non-null chain raises instead of spinning the request thread.

    graphql-core forbids ``NonNull(NonNull(x))``, so no genuine schema reaches
    the ceiling - which is why the three unbounded ``while isinstance`` loops
    this replaced looked safe. A hand-built or corrupted wrapper is the case the
    bound exists for, and an unbounded loop on one hangs rather than failing.
    """

    class _CyclicNonNull(GraphQLNonNull[GraphQLNullableType]):
        """A non-null wrapper built without its constructor, which refuses a non-null type."""

    chain = _CyclicNonNull.__new__(_CyclicNonNull)
    # basedpyright: a non-null wrapping a non-null is the malformed chain under test
    chain.of_type = chain  # pyright: ignore[reportAttributeAccessIssue]

    with pytest.raises(RuntimeError, match="unwrap_non_null"):
        unwrap_non_null(chain)


def _info_stand_in(stand_in: object) -> strawberry.Info[object, object]:
    """Hand ``published_argument`` an info shape no execution builds: the shape is the input."""
    return typing.cast("strawberry.Info[object, object]", stand_in)


def test_published_argument_reads_the_executable_schemas_argument_map() -> None:
    """A parameter's published argument is read back by its definition, never re-derived."""
    # graphql-core's ``GraphQLNamedType.__new__`` widens every built-in scalar to its base.
    int_scalar = require_instance(GraphQLInt, GraphQLScalarType)
    arg_def = SimpleNamespace(python_name="offset")

    def defines_offset(name: str) -> object:
        return arg_def if name == "offset" else None

    # 1. A direct-call stub: no definition reader, or a definition but no ``_raw_info``.
    assert published_argument(_info_stand_in(SimpleNamespace()), "offset") is None
    no_raw = SimpleNamespace(get_argument_definition=defines_offset)
    assert published_argument(_info_stand_in(no_raw), "offset") is None
    # 2. The field declares no such parameter.
    assert published_argument(_info_stand_in(no_raw), "limit") is None

    def info_over(args: dict[str, GraphQLArgument]) -> strawberry.Info[object, object]:
        parent = GraphQLObjectType("Query", {"cats": GraphQLField(int_scalar, args=args)})
        raw = SimpleNamespace(parent_type=parent, field_name="cats")
        return _info_stand_in(
            SimpleNamespace(get_argument_definition=defines_offset, _raw_info=raw),
        )

    # 3. A definition no published argument back-references is a configuration error.
    other = GraphQLArgument(int_scalar, extensions={"strawberry-definition": object()})
    with pytest.raises(ConfigurationError, match="has a definition but no published wire name"):
        _ = published_argument(info_over({"offset": other}), "offset")

    # 4. The back-referencing entry comes back with its key, whatever its spelling.
    published = GraphQLArgument(int_scalar, extensions={"strawberry-definition": arg_def})
    assert published_argument(info_over({"other": other, "OFFSET": published}), "offset") == (
        "OFFSET",
        published,
    )


def test_published_python_name_reads_the_definition_backref() -> None:
    """An input field's attr comes from the ``StrawberryField`` filed on it, else ``None``."""
    assert isinstance(GraphQLInt, GraphQLScalarType)
    named = GraphQLInputField(
        GraphQLInt,
        extensions={"strawberry-definition": SimpleNamespace(python_name="isbn_10")},
    )
    assert published_python_name(named) == "isbn_10"
    assert published_python_name(GraphQLInputField(GraphQLInt)) is None
    not_text = GraphQLInputField(
        GraphQLInt,
        extensions={"strawberry-definition": SimpleNamespace(python_name=10)},
    )
    assert published_python_name(not_text) is None
