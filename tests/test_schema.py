"""Permanent behavioral tests for django_strawberry_framework.schema.

Construction, hostile extension matching, rollback windows, and the
chain-resolution rows a request cannot express.
``Schema.stream`` stays here: fakeshop has no ASGI/WS mount.
Consumer-visible policy enforcement and masking live in
``examples/fakeshop/test_query/test_resource_policy_api.py`` and
``examples/fakeshop/test_query/test_error_policy_api.py``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, NoReturn, TypedDict
from unittest.mock import MagicMock, patch

import pytest
import strawberry
from apps.library.models import Branch, Shelf
from django import forms
from django.db.models import IntegerField, Model, TextField
from django_filters import CharFilter
from graphql import FieldNode, NameNode
from graphql.execution import Executor
from graphql.execution.executor import CollectedErrors
from graphql.pyutils import Path
from strawberry import relay
from strawberry.exceptions import DuplicatedTypeName
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.runner import SchemaExtensionsRunner
from strawberry.schema.config import StrawberryConfig
from strawberry.types import ExecutionContext as StrawberryExecutionContext
from strawberry.types import ExecutionResult
from typing_extensions import override

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.error_policy import ErrorPolicy
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.error_policy import DjangoErrorPolicyExtension
from django_strawberry_framework.extensions.operation_state import _ResumedStream
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.filters import FilterSet, RangeFilter
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.resource_policy import ResourcePolicy, bounded_rows
from django_strawberry_framework.schema import (
    DjangoMutationExecutionContext,
    DjangoSchema,
    _consumer_extension_entries,
)
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import read_attr
from tests._idioms import (
    ModelSerializerBase,
    declare_django_type,
)


def _unchecked_entries(*entries: object) -> list[SchemaExtension]:
    """Hand ``DjangoSchema(extensions=...)`` entries its annotation refuses, for the refusal under test."""
    # basedpyright: trust boundary: hostile entries the schema's construction-time check refuses
    return list(entries)  # pyright: ignore[reportReturnType]


class CustomErrorPolicyExtension(DjangoErrorPolicyExtension):
    """A consumer subclass of the masking authority, which is not one."""


class CustomResourcePolicyExtension(DjangoResourcePolicyExtension):
    """A consumer subclass of the bounding authority, which is not one."""


#: Every marker extension that ran, in order, since a test last cleared it.
_MARKS: list[str] = []


class _MarkerExtension(SchemaExtension):
    """A consumer extension that records itself when its operation begins.

    The mark is the observation of which extensions ran the operation; neither
    enforcement authority is an entry.
    """

    mark = "accepted"

    @override
    def on_operation(self) -> Iterator[None]:
        """Record that this entry ran the operation."""
        _MARKS.append(self.mark)
        yield


@pytest.fixture(autouse=True)
def _clear_marks() -> Iterator[None]:
    """Start every test with no marks recorded."""
    _MARKS.clear()
    yield
    _MARKS.clear()


@strawberry.type
class DummyQuery:
    """A one-field root query the schema tests build their schemas around."""

    @strawberry.field
    def hello(self) -> str:
        return "world"


@strawberry.type
class _RowQuery:
    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))


@strawberry.type
class DummyMutation:
    """A one-field root mutation, for schemas that need a mutation type."""

    @strawberry.mutation
    def plain_mutation(self) -> str:
        return "plain"


def test_schema_init_with_none_and_iterable_extensions() -> None:
    schema_none = DjangoSchema(query=DummyQuery, extensions=None)
    assert schema_none.extensions == ()

    schema_tuple = DjangoSchema(query=DummyQuery, extensions=(_MarkerExtension,))
    assert schema_tuple.extensions == (_MarkerExtension,)

    def ext_gen() -> Iterator[type[_MarkerExtension]]:
        yield _MarkerExtension

    schema_gen = DjangoSchema(query=DummyQuery, extensions=ext_gen())
    assert schema_gen.extensions == (_MarkerExtension,)


def test_schema_init_with_none_execution_context_class_falls_back() -> None:
    schema = DjangoSchema(query=DummyQuery, execution_context_class=None)
    assert read_attr(schema, "execution_context_class") is DjangoMutationExecutionContext


def test_consumer_extension_entries_shapes() -> None:
    """What travels as configuration, and what is read once and folded into the schema's policy."""
    assert _consumer_extension_entries(None) == ([], None)
    assert _consumer_extension_entries([]) == ([], None)
    assert _consumer_extension_entries([_MarkerExtension]) == ([_MarkerExtension], None)
    assert _consumer_extension_entries([DjangoResourcePolicyExtension]) == ([], None)
    assert _consumer_extension_entries([DjangoErrorPolicyExtension]) == ([], None)
    assert _consumer_extension_entries([DjangoErrorPolicyExtension()]) == ([], None)
    assert _consumer_extension_entries([CustomResourcePolicyExtension]) == (
        [CustomResourcePolicyExtension],
        None,
    )

    entries, declared = _consumer_extension_entries(
        [_MarkerExtension, DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=4))],
    )
    assert entries == [_MarkerExtension]
    assert declared == ResourcePolicy(max_list_rows=4)


@pytest.mark.parametrize(
    "entry",
    [CustomErrorPolicyExtension, CustomResourcePolicyExtension],
    ids=["error-subclass-class", "resource-subclass-class"],
)
def test_a_subclass_of_an_enforcement_extension_is_an_ordinary_entry(entry: object) -> None:
    """Only the exact class, or an exact instance of it, is read as configuration."""
    schema = DjangoSchema(query=DummyQuery, extensions=_unchecked_entries(entry))

    assert schema.extensions == (entry,)
    assert schema.execute_sync("{ hello }").data == {"hello": "world"}


def _field_node(name: str) -> FieldNode:
    """A selection of the root field ``name``."""
    return FieldNode(name=NameNode(value=name))


def test_marked_mutation_class_is_none_off_a_marked_root_mutation_field() -> None:
    schema = DjangoSchema(query=DummyQuery)
    graphql_schema = schema._schema

    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx.schema = graphql_schema

    # parent_type is None when schema.mutation_type is None (query-only schema)
    assert ctx._marked_mutation_class(None, []) is None

    # Schema with mutation
    schema_with_mut = DjangoSchema(query=DummyQuery, mutation=DummyMutation)
    ctx_mut = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx_mut.schema = schema_with_mut._schema
    mut_type = schema_with_mut._schema.mutation_type

    # parent_type is None when schema.mutation_type is present
    assert ctx_mut._marked_mutation_class(None, []) is None

    # field_nodes is empty
    assert ctx_mut._marked_mutation_class(mut_type, []) is None

    # Introspection field (__typename)
    assert ctx_mut._marked_mutation_class(mut_type, [_field_node("__typename")]) is None

    # Plain strawberry mutation (unmarked)
    assert ctx_mut._marked_mutation_class(mut_type, [_field_node("plainMutation")]) is None

    # A name the mutation root does not define
    assert ctx_mut._marked_mutation_class(mut_type, [_field_node("doesNotExist")]) is None


def test_schema_policy_resolution_and_validation() -> None:
    s1 = DjangoSchema(
        query=DummyQuery,
        resource_policy={"max_depth": 10},
        error_policy={"enabled": False},
    )
    assert s1.resource_policy.max_depth == 10
    assert s1.error_policy.enabled is False

    rp = ResourcePolicy(max_depth=12)
    ep = ErrorPolicy(enabled=True, message="Custom error")
    s2 = DjangoSchema(query=DummyQuery, resource_policy=rp, error_policy=ep)
    assert s2.resource_policy.max_depth == 12
    assert s2.error_policy.message == "Custom error"

    with pytest.raises(ConfigurationError):
        DjangoSchema(query=DummyQuery, resource_policy={"max_depth": -5})

    with pytest.raises(ConfigurationError):
        DjangoSchema(query=DummyQuery, error_policy={"enabled": "invalid"})


#: A root mutation field's execution path, for the windows that forward it upstream.
_MUTATION_ROOT_PATH = Path(None, "mutation", "Mutation")


@pytest.mark.django_db
def test_execute_mutation_field_sync_exception_rolls_back() -> None:
    class DummyMutationCls:
        _mutation_meta = MagicMock(model=None)

    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    mutation_type = MagicMock()
    ctx.schema = MagicMock(mutation_type=mutation_type)
    ctx.collected_errors = CollectedErrors()

    with (
        patch.object(ctx, "_marked_mutation_class", return_value=DummyMutationCls),
        patch.object(
            Executor,
            "execute_field",
            side_effect=RuntimeError("sync field crash"),
        ),
        pytest.raises(RuntimeError, match="sync field crash"),
    ):
        ctx.execute_field(mutation_type, None, [MagicMock()], _MUTATION_ROOT_PATH, None)


#: The row the patched resolver writes inside the open window. Both rows below
#: assert its ABSENCE afterwards, which is the half a closed-transaction
#: assertion cannot see: an atomic that exits WITHOUT the rollback mark exits
#: cleanly and commits, so ``connection.in_atomic_block`` is false either way and
#: the row is the only witness that says which of the two happened.


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_execute_mutation_field_async_exception_rolls_back() -> None:
    class DummyMutationCls:
        _mutation_meta = MagicMock(model=None)

    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    mutation_type = MagicMock()
    ctx.schema = MagicMock(mutation_type=mutation_type)
    ctx.collected_errors = CollectedErrors()

    async def async_failing_resolve(*_args: object, **_kwargs: object) -> NoReturn:
        raise RuntimeError("async field crash")

    with (
        patch.object(ctx, "_marked_mutation_class", return_value=DummyMutationCls),
        patch.object(
            Executor,
            "execute_field",
            return_value=async_failing_resolve(),
        ),
    ):
        pending = ctx.execute_field(
            mutation_type,
            None,
            [MagicMock()],
            _MUTATION_ROOT_PATH,
            None,
        )
        assert inspect.isawaitable(pending)
        with pytest.raises(RuntimeError, match="async field crash"):
            await pending


def test_get_extensions_gives_an_unrelated_factory_both_package_authorities() -> None:
    """The control: an ordinary consumer factory runs between the two authorities."""

    def unrelated_factory() -> _MarkerExtension:
        return _MarkerExtension()

    schema = DjangoSchema(query=DummyQuery, extensions=[unrelated_factory])
    resolved = schema.get_extensions(sync=True)

    assert [type(entry).__name__ for entry in resolved] == [
        "DjangoErrorPolicyExtension",
        "_MarkerExtension",
        "DjangoResourcePolicyExtension",
        "_OperationModeMarker",
    ]


def test_get_extensions_resolves_one_authority_of_each_kind_for_a_bare_class_entry() -> None:
    """A bare class entry declares the automatic extension, so it is not a second one."""
    schema = DjangoSchema(query=DummyQuery, extensions=[DjangoResourcePolicyExtension])
    resolved = schema.get_extensions(sync=True)

    assert schema.extensions == ()
    assert sum(truth.is_instance(e, DjangoResourcePolicyExtension) for e in resolved) == 1
    assert sum(truth.is_instance(e, DjangoErrorPolicyExtension) for e in resolved) == 1


def test_get_extensions_sync_and_async() -> None:
    schema = DjangoSchema(query=DummyQuery)
    sync_exts = schema.get_extensions(sync=True)
    async_exts = schema.get_extensions(sync=False)
    assert sum(isinstance(e, DjangoErrorPolicyExtension) for e in sync_exts) == 1
    assert sum(isinstance(e, DjangoResourcePolicyExtension) for e in sync_exts) == 1
    assert sum(isinstance(e, DjangoErrorPolicyExtension) for e in async_exts) == 1
    assert sum(isinstance(e, DjangoResourcePolicyExtension) for e in async_exts) == 1


class _PolicyKeyword(TypedDict, total=False):
    """The one policy keyword a row hands ``DjangoSchema``, keyed by the attribute it lands on."""

    resource_policy: ResourcePolicy
    error_policy: ErrorPolicy


@pytest.mark.parametrize(
    "row",
    [
        {"resource_policy": ResourcePolicy(max_list_rows=7)},
        {"error_policy": ErrorPolicy(message="masked")},
    ],
    ids=["resource", "error"],
)
def test_a_schema_policy_attribute_is_read_only(row: _PolicyKeyword) -> None:
    """The attribute answers the resolved policy and refuses assignment."""
    [(attribute, policy)] = row.items()
    schema = DjangoSchema(query=DummyQuery, **row)

    assert read_attr(schema, attribute) == policy
    with pytest.raises(AttributeError):
        setattr(schema, attribute, policy)


@strawberry.type
class _BoundedRowQuery:
    """One field whose rows are bounded by whatever policy the operation armed."""

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))


def test_a_policy_declared_by_an_entry_and_by_the_argument_is_refused() -> None:
    """Two declarations of one ceiling are a configuration with two answers."""
    with pytest.raises(ConfigurationError, match="declared twice"):
        DjangoSchema(
            query=DummyQuery,
            extensions=[DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=5))],
            resource_policy=ResourcePolicy(max_list_rows=3),
        )


def test_two_entries_declaring_a_policy_of_their_own_are_refused() -> None:
    """Two entries carrying a policy are the same two answers, spelled differently."""
    with pytest.raises(ConfigurationError, match="two resource-policy"):
        DjangoSchema(
            query=DummyQuery,
            extensions=[
                DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=5)),
                DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=3)),
            ],
        )


@pytest.mark.parametrize(
    "config_factory",
    [StrawberryConfig, strawberry_config],
    ids=["StrawberryConfig", "strawberry_config"],
)
@pytest.mark.parametrize("with_mutation", [False, True], ids=["query-only", "with-mutation"])
def test_incremental_execution_is_refused_at_construction(
    config_factory: Callable[..., StrawberryConfig],
    *,
    with_mutation: bool,
) -> None:
    """Incremental delivery serves frames outside the one response every guarantee holds for.

    Refused for every schema shape, not only one exposing mutations: a deferred
    query payload escapes masking and the resource bounds as surely as a
    deferred mutation payload escapes its transaction. Both spellings of the
    config are refused, since ``strawberry_config()`` forwards the flag verbatim.
    """
    config = config_factory(enable_experimental_incremental_execution=True)
    with pytest.raises(ConfigurationError, match="enable_experimental_incremental_execution"):
        DjangoSchema(
            query=DummyQuery,
            mutation=DummyMutation if with_mutation else None,
            config=config,
        )


@pytest.mark.parametrize(
    "config",
    [None, strawberry_config(), StrawberryConfig(enable_experimental_incremental_execution=False)],
    ids=["no-config", "strawberry_config", "flag-off"],
)
def test_a_config_without_incremental_execution_constructs(
    config: StrawberryConfig | None,
) -> None:
    """The refusal reads the flag alone: an omitted config or one with the flag off is accepted."""
    schema = DjangoSchema(query=DummyQuery, config=config)

    assert not schema.config.enable_experimental_incremental_execution


def test_a_policy_declared_by_an_entry_becomes_the_schemas_own() -> None:
    """An entry declaring a policy is read once, where it is accepted, and folded in.

    Keeping the entry would leave the object a resolver reaches through
    ``info.schema.extensions`` deciding what the next request is bounded by;
    dropping what it declared would answer the deployment with a ceiling it did
    not choose. The schema's policy takes the declaration and the entry does not travel.
    """
    schema = DjangoSchema(
        query=_BoundedRowQuery,
        extensions=[DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))],
    )

    assert schema.extensions == ()
    assert schema.resource_policy.max_list_rows == 1
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}


class _SlottedFactory:
    """A valid extension factory whose layout admits no weak reference.

    ``__slots__`` without ``__weakref__`` is an ordinary, supported way to write
    a callable, and Strawberry runs one exactly as it runs any other factory.
    Refusing it would be refusing a memory layout rather than a configuration.
    """

    __slots__ = ()

    def __call__(self) -> _MarkerExtension:
        return _MarkerExtension()


class _WeakReferenceableFactory:
    """The control: the same factory, with the layout a weak reference can be taken of."""

    def __call__(self) -> _MarkerExtension:
        return _MarkerExtension()


@pytest.mark.parametrize(
    "factory",
    [_SlottedFactory, _WeakReferenceableFactory],
    ids=["slotted-callable", "weak-referenceable-control"],
)
def test_a_slotted_callable_factory_is_accepted_and_runs(
    factory: type[_SlottedFactory | _WeakReferenceableFactory],
) -> None:
    """A callable factory works whatever its object layout is.

    Strawberry accepts either one, so a schema that refused the slotted form
    would be refusing a configuration for a reason that has nothing to do with
    what runs the operation. Both build the extension per operation and both
    run it.
    """
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[factory()],
    )

    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted"]


@pytest.mark.parametrize(
    "entry",
    [(), "DjangoResourcePolicyExtension", 7],
    ids=["a-tuple", "a-name", "a-number"],
)
def test_an_extension_entry_strawberry_could_not_resolve_is_refused(entry: object) -> None:
    """Acceptance is per entry, and the one reason to refuse one is resolution.

    Strawberry resolves an entry as itself when it is an extension instance and
    by CALLING it otherwise, so a class, an instance and a factory are the three
    shapes that work. A builtin value is none of them and fails at the first
    operation, deep inside the engine, on a schema the deployment already
    started; the refusal names it where it was supplied instead.
    """
    with pytest.raises(ConfigurationError, match="is none of those"):
        DjangoSchema(query=DummyQuery, extensions=_unchecked_entries(entry))


# ---------------------------------------------------------------------------
# The resolved chain
# ---------------------------------------------------------------------------


def _narrow_resource_factory() -> DjangoResourcePolicyExtension:
    """A factory producing a resource extension with a bound of its own."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=1))


_SHARED_MARKER_EXTENSION = _MarkerExtension()


def _first_error_factory() -> DjangoErrorPolicyExtension:
    """A factory producing a masking extension for the operation."""
    return DjangoErrorPolicyExtension()


def _fresh_marker_factory() -> _MarkerExtension:
    """The supported consumer spelling: a new extension per operation."""
    return _MarkerExtension()


def _singleton_marker_factory() -> _MarkerExtension:
    """The documented shared-instance spelling: one object, returned every time."""
    return _SHARED_MARKER_EXTENSION


class _BoundMethodMarkerFactory:
    """The bound-method spelling, for an extension that is not an authority."""

    def build(self) -> _MarkerExtension:
        """Build this owner's consumer extension, fresh per operation."""
        return _MarkerExtension()


_SHARED_OPTIMIZER_EXTENSION = DjangoOptimizerExtension()


def _optimizer_singleton_factory() -> DjangoOptimizerExtension:
    """The optimizer's own documented spelling, whose cache is deliberately shared."""
    return _SHARED_OPTIMIZER_EXTENSION


def test_a_factory_entrys_own_policy_configures_nothing_under_a_django_schema() -> None:
    """Every pass, the pre-parse token scan included, runs under the schema's policy.

    A six-token document passes the schema's wider bound although the entry's own
    policy admits five; on a plain ``strawberry.Schema`` the same entry refuses it.
    """
    document = "{ hello hello hello hello }"

    def narrow_entry() -> DjangoResourcePolicyExtension:
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_document_tokens=5))

    schema = DjangoSchema(
        query=DummyQuery,
        resource_policy=ResourcePolicy(max_document_tokens=50),
        extensions=[narrow_entry],
    )
    plain = strawberry.Schema(query=DummyQuery, extensions=[narrow_entry])

    assert schema.execute_sync(document).data == {"hello": "world"}
    refused = plain.execute_sync(document)
    assert refused.data is None
    assert refused.errors is not None
    assert [error.extensions for error in refused.errors] == [
        {
            "code": "RESOURCE_LIMIT_EXCEEDED",
            "bound": "max_document_tokens",
            "limit": 5,
            "charged": 6,
        },
    ]


def test_a_resource_policy_that_is_no_policy_is_refused_at_construction() -> None:
    """``resource_policy=`` takes a ``ResourcePolicy`` or a mapping, nothing else."""
    with pytest.raises(ConfigurationError, match="resource policy must be a ResourcePolicy"):
        DjangoSchema(query=DummyQuery, resource_policy=MagicMock())


def test_an_error_policy_that_is_no_policy_is_refused_at_construction() -> None:
    """``error_policy=`` takes an ``ErrorPolicy`` or a mapping, nothing else."""
    with pytest.raises(ConfigurationError, match="error policy must be an ErrorPolicy"):
        DjangoSchema(query=DummyQuery, error_policy=MagicMock())


@pytest.mark.parametrize(
    "entry",
    [_narrow_resource_factory, _first_error_factory],
    ids=["resource-factory", "error-factory"],
)
def test_a_factory_producing_an_enforcement_extension_is_an_ordinary_entry(
    entry: object,
) -> None:
    """A factory's member runs between the schema's own two authorities."""
    schema = DjangoSchema(query=DummyQuery, extensions=_unchecked_entries(entry))

    assert len(schema.get_extensions(sync=True)) == 4
    assert schema.execute_sync("{ hello }").data == {"hello": "world"}


@pytest.mark.parametrize(
    "entry",
    [
        _MarkerExtension,
        _fresh_marker_factory,
        _singleton_marker_factory,
        _BoundMethodMarkerFactory().build,
        _optimizer_singleton_factory,
    ],
    ids=[
        "class",
        "fresh-factory",
        "singleton-factory",
        "bound-method",
        "optimizer-singleton-factory",
    ],
)
def test_every_supported_entry_spelling_still_resolves_into_one_chain(entry: object) -> None:
    """Every supported consumer spelling still runs.

    A class, a module-level function, a factory handing back one shared object
    and the optimizer's own documented singleton-in-a-factory are configurations
    rather than defects.
    Each resolves between exactly one masking authority and exactly one resource
    authority, both of which are the schema's.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=_unchecked_entries(entry))
    resolved = schema.get_extensions(sync=True)

    assert schema.execute_sync("{ hello }").data == {"hello": "world"}
    assert sum(truth.is_instance(e, DjangoErrorPolicyExtension) for e in resolved) == 1
    assert sum(truth.is_instance(e, DjangoResourcePolicyExtension) for e in resolved) == 1
    assert len(resolved) == 4


class _UpstreamRunnerSchema(DjangoSchema):
    """A subclass that opts out of the package's runner, and of what depends on it.

    Both overrides are needed together. Every extension ``DjangoSchema`` installs
    reads its request through the operation state the package's runner binds, so
    a subclass that swapped only the runner would have stripped those extensions
    of their context while still running them; a subclass that meant to use
    upstream's machinery replaces both halves.
    """

    @override
    def create_extensions_runner(
        self,
        execution_context: StrawberryExecutionContext,
        extensions: list[SchemaExtension],
    ) -> SchemaExtensionsRunner:
        """Build the plain upstream runner, as such a subclass may."""
        return SchemaExtensionsRunner(
            execution_context=execution_context,
            extensions=extensions,
        )

    @override
    def get_extensions(self, sync: bool = False) -> list[SchemaExtension]:
        """Run no extension, so nothing in the operation needs the package's runner."""
        return []


@pytest.mark.asyncio
async def test_a_stream_whose_runner_is_not_the_packages_is_handed_back_untouched() -> None:
    """The resume wrapper binds what a ``DjangoExtensionsRunner`` owns, and nothing else.

    A subclass may build its own runner, and upstream's holds no per-task state:
    wrapping it would put a resume hook around frames whose producer has nothing
    to rebind, so the stream is returned exactly as upstream built it.

    The package's own schema is the other half of the row. Without it, "this one
    is not wrapped" would read the same whether the check discriminates or the
    wrapper had stopped being applied to anything at all.
    """
    foreign = _UpstreamRunnerSchema(query=DummyQuery)
    plain = DjangoSchema(query=DummyQuery)

    foreign_stream = await foreign.stream("{ hello }")
    plain_stream = await plain.stream("{ hello }")
    try:
        assert not isinstance(foreign_stream, _ResumedStream)
        assert isinstance(plain_stream, _ResumedStream)

        foreign_frames = [frame async for frame in foreign_stream]
        assert len(foreign_frames) == 1
        assert isinstance(foreign_frames[0], ExecutionResult)
        assert foreign_frames[0].errors is None
    finally:
        await plain_stream.aclose()


# ---------------------------------------------------------------------------
# Generated type-name clashes are per schema; DjangoSchema names their sources.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ClashSide:
    """One declaration's half of a generated type-name clash: its root fields.

    ``query`` maps a root field name to its ``(annotation, field)`` pair (the root is
    built with ``type(...)`` because ``from __future__ import annotations`` would leave a
    class-body annotation naming a function local unresolved); ``mutation`` maps a root
    mutation name to its field.
    """

    query: dict[str, tuple[object, object]]
    mutation: dict[str, object] = field(default_factory=dict[str, object])


def _roots(*sides: _ClashSide) -> tuple[type, type | None]:
    """Return the query root, and the mutation root when any, serving every side given."""
    query_fields = {name: pair for side in sides for name, pair in side.query.items()}
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {name: pair[0] for name, pair in query_fields.items()},
                **{name: pair[1] for name, pair in query_fields.items()},
            },
        ),
    )
    mutation_fields = {name: value for side in sides for name, value in side.mutation.items()}
    if not mutation_fields:
        return query, None
    return query, strawberry.type(type("Mutation", (), mutation_fields))


def _node(
    name: str,
    model: type[Model],
    fields: tuple[str, ...],
    **meta: object,
) -> type[DjangoType]:
    """Declare a relay ``DjangoType`` over ``model`` with ``meta`` added to its ``Meta``."""
    body = {
        "model": model,
        "fields": fields,
        "interfaces": (relay.Node,),
        **meta,
    }
    return declare_django_type(name, {"Meta": type("Meta", (), body)})


def _connection(name: str, node: type[DjangoType]) -> dict[str, tuple[object, object]]:
    """Return one connection root field over ``node``."""
    return {name: (DjangoConnection[node], DjangoConnectionField(node))}


def _set_member_split() -> tuple[_ClashSide, _ClashSide]:
    """``BookFilter`` + ``set_code`` and ``BookFilterSet`` + ``code`` spell one bag name."""

    class BookFilter(FilterSet):
        set_code = CharFilter(field_name="name")

        class Meta:
            model = Branch
            fields = []

    class BookFilterSet(FilterSet):
        code = RangeFilter(field_name="topic")

        class Meta:
            model = Shelf
            fields = []

    branches = _node("BranchNode", Branch, ("id", "name"), filterset_class=BookFilter)
    shelves = _node("ShelfNode", Shelf, ("id", "code"), filterset_class=BookFilterSet)
    return (
        _ClashSide(_connection("branches", branches)),
        _ClashSide(_connection("shelves", shelves)),
    )


def _range_split() -> tuple[_ClashSide, _ClashSide]:
    """``A`` over ``b_c`` and ``AB`` over ``c`` spell one range name, of two axis types."""

    class _IntRangeRow(Model):
        b_c: IntegerField[float | int | str | Combinable, int] = IntegerField()

        class Meta:
            app_label = "library"
            managed = False

    class _TextRangeRow(Model):
        c: TextField[str | Combinable, str] = TextField()

        class Meta:
            app_label = "library"
            managed = False

    class A(FilterSet):
        x = RangeFilter(field_name="b_c")

        class Meta:
            model = _IntRangeRow
            fields = []

    class AB(FilterSet):
        y = RangeFilter(field_name="c")

        class Meta:
            model = _TextRangeRow
            fields = []

    ints = _node("IntRangeNode", _IntRangeRow, ("id",), filterset_class=A)
    texts = _node("TextRangeNode", _TextRangeRow, ("id",), filterset_class=AB)
    return _ClashSide(_connection("ints", ints)), _ClashSide(_connection("texts", texts))


def _root_and_bag() -> tuple[_ClashSide, _ClashSide]:
    """FilterSet ``BookFilterSetFilter``'s root and ``BookFilter.set``'s bag share a name."""

    class BookFilter(FilterSet):
        set = CharFilter(field_name="name")

        class Meta:
            model = Branch
            fields = []

    class BookFilterSetFilter(FilterSet):
        code = CharFilter(field_name="code")

        class Meta:
            model = Shelf
            fields = []

    branches = _node("BranchNode", Branch, ("id", "name"), filterset_class=BookFilter)
    shelves = _node("ShelfNode", Shelf, ("id", "code"), filterset_class=BookFilterSetFilter)
    return (
        _ClashSide(_connection("branches", branches)),
        _ClashSide(_connection("shelves", shelves)),
    )


def _filter_and_order_root() -> tuple[_ClashSide, _ClashSide]:
    """A FilterSet and an OrderSet both named ``Foo`` both mint ``FooInputType``."""

    class Foo(FilterSet):
        name = CharFilter(field_name="name")

        class Meta:
            model = Branch
            fields = []

    # The order side's class is declared under the very name the filter side's holds.
    foo_order = type(
        "Foo",
        (OrderSet,),
        {
            "__module__": Foo.__module__,
            "__qualname__": Foo.__qualname__,
            "Meta": type("Meta", (), {"model": Shelf, "fields": ["code"]}),
        },
    )
    branches = _node("BranchNode", Branch, ("id", "name"), filterset_class=Foo)
    shelves = _node("ShelfNode", Shelf, ("id", "code"), orderset_class=foo_order)
    return (
        _ClashSide(_connection("branches", branches)),
        _ClashSide(_connection("shelves", shelves)),
    )


def _model_input_mutation() -> dict[str, object]:
    """Return a ``DjangoMutation`` creating a ``Shelf`` from ``code`` and ``topic``."""

    class CreateShelfFromCodeAndTopic(DjangoMutation):
        class Meta:
            model = Shelf
            operation = "create"
            fields = ("code", "topic")
            permission_classes = []

    return {"create_shelf": DjangoMutationField(CreateShelfFromCodeAndTopic)}


def _write_roots() -> dict[str, tuple[object, object]]:
    """Declare the primary types the write flavors resolve, and a query root over them."""
    shelves = _node("ShelfNode", Shelf, ("id", "code", "topic"))
    _node("BranchNode", Branch, ("id", "name", "city"))
    return _connection("shelves", shelves)


def _model_and_form_input() -> tuple[_ClashSide, _ClashSide]:
    """A model input narrowed to ``(code, topic)`` and a ``ModelForm`` named ``ShelfCodeTopic``."""
    query = _write_roots()

    class ShelfCodeTopic(forms.ModelForm[Branch]):
        class Meta:
            model = Branch
            fields = ("name", "city")

    class CreateBranchViaForm(DjangoModelFormMutation):
        class Meta:
            form_class = ShelfCodeTopic
            operation = "create"
            permission_classes = []

    return (
        _ClashSide(query, _model_input_mutation()),
        _ClashSide(query, {"create_branch": DjangoMutationField(CreateBranchViaForm)}),
    )


def _model_and_serializer_input() -> tuple[_ClashSide, _ClashSide]:
    """A model input narrowed to ``(code, topic)`` and a serializer named ``ShelfCodeTopic``."""
    query = _write_roots()

    class ShelfCodeTopic(ModelSerializerBase[Branch]):
        class Meta:
            model = Branch
            fields = ("name", "city")

    class CreateBranchViaSerializer(SerializerMutation):
        class Meta:
            serializer_class = ShelfCodeTopic
            operation = "create"
            permission_classes = []

    return (
        _ClashSide(query, _model_input_mutation()),
        _ClashSide(query, {"create_branch": DjangoMutationField(CreateBranchViaSerializer)}),
    )


_LOCALS = "tests.test_schema.{}.<locals>.{}"

# One row per way two declarations derive one generated input name: the builder, the
# clashing name, and the message ``DjangoSchema`` restates Strawberry's refusal with.
_GENERATED_NAME_CLASHES = [
    pytest.param(
        _set_member_split,
        "BookFilterSetCodeFilterInputType",
        "by FilterSet {} member 'set_code' and by FilterSet {} member 'code'".format(
            _LOCALS.format("_set_member_split", "BookFilter"),
            _LOCALS.format("_set_member_split", "BookFilterSet"),
        ),
        "A member's nested input name joins the set name and the member's PascalCase stem, "
        "so another set/member split spells the same name.",
        id="set-member-split",
    ),
    pytest.param(
        _range_split,
        "ABCRangeInputType",
        "by the 'exact' input of FilterSet {} member 'x' and by the 'exact' input of "
        "FilterSet {} member 'y'".format(
            _LOCALS.format("_range_split", "A"),
            _LOCALS.format("_range_split", "AB"),
        ),
        "A range input's name joins the set name, the PascalCase stem of the range filter's "
        "field_name (letter case dropped, interior underscore runs collapsed) and "
        "'RangeInputType', so two field paths or sets can spell one name.",
        id="range-split",
    ),
    pytest.param(
        _root_and_bag,
        "BookFilterSetFilterInputType",
        "by FilterSet {} and by FilterSet {} member 'set'".format(
            _LOCALS.format("_root_and_bag", "BookFilterSetFilter"),
            _LOCALS.format("_root_and_bag", "BookFilter"),
        ),
        "A root input's name (its declaration's name plus a suffix) equals a nested input's "
        "name (a set name, a member stem and a suffix).",
        id="root-and-bag",
    ),
    pytest.param(
        _filter_and_order_root,
        "FooInputType",
        "by FilterSet {} and by OrderSet {}".format(
            _LOCALS.format("_filter_and_order_root", "Foo"),
            _LOCALS.format("_filter_and_order_root", "Foo"),
        ),
        "Both are root inputs, each named from its declaration's name (a set, model, form or "
        "serializer class) plus a suffix, and the two derivations meet.",
        id="filter-and-order-root",
    ),
    pytest.param(
        _model_and_form_input,
        "ShelfCodeTopicInput",
        "by the input of DjangoMutation 'CreateShelfFromCodeAndTopic' and by the input of "
        "{}".format(_LOCALS.format("_model_and_form_input", "CreateBranchViaForm")),
        "Both are root inputs, each named from its declaration's name (a set, model, form or "
        "serializer class) plus a suffix, and the two derivations meet.",
        id="model-and-form-input",
    ),
    pytest.param(
        _model_and_serializer_input,
        "ShelfCodeTopicInput",
        "by the input of DjangoMutation 'CreateShelfFromCodeAndTopic' and by the input of "
        "{}".format(_LOCALS.format("_model_and_serializer_input", "CreateBranchViaSerializer")),
        "Both are root inputs, each named from its declaration's name (a set, model, form or "
        "serializer class) plus a suffix, and the two derivations meet.",
        id="model-and-serializer-input",
    ),
]


# The same rows with only the builder and the clashing name.
_GENERATED_NAMES = [
    pytest.param(*clash.values[:2], id=clash.id) for clash in _GENERATED_NAME_CLASHES
]


@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.parametrize(("build", "name"), _GENERATED_NAMES)
def test_a_generated_name_clash_in_one_strawberry_schema_is_refused(
    build: Callable[[], tuple[_ClashSide, _ClashSide]],
    name: str,
) -> None:
    """A plain ``strawberry.Schema`` serving both refuses them with Strawberry's own error."""
    sides = build()
    finalize_django_types()
    query, mutation = _roots(*sides)
    with pytest.raises(DuplicatedTypeName) as raised:
        strawberry.Schema(query=query, mutation=mutation, config=strawberry_config())
    assert str(raised.value) == f"Type {name} is defined multiple times in the schema"


@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.parametrize(
    (
        "build",
        "name",
        "sources",
        "cause",
    ),
    _GENERATED_NAME_CLASHES,
)
def test_django_schema_names_the_declarations_behind_a_generated_name_clash(
    build: Callable[[], tuple[_ClashSide, _ClashSide]],
    name: str,
    sources: str,
    cause: str,
) -> None:
    """``DjangoSchema`` restates the refusal naming both declarations and the cause."""
    sides = build()
    finalize_django_types()
    query, mutation = _roots(*sides)
    with pytest.raises(ConfigurationError) as raised:
        DjangoSchema(query=query, mutation=mutation, config=strawberry_config())
    assert str(raised.value) == (
        f"Generated GraphQL type {name!r} is claimed with different fields {sources}; a "
        f"schema serves one input type per name, so it cannot serve both. {cause} Rename "
        "one so its generated type name is unique."
    )
    assert isinstance(raised.value.__cause__, DuplicatedTypeName)


def _same_named_enums() -> list[type]:
    """Two enums both published as ``Shade``."""

    @strawberry.enum(name="Shade")
    class Light(Enum):
        PALE = "pale"

    @strawberry.enum(name="Shade")
    class Dark(Enum):
        DEEP = "deep"

    return [Light, Dark]


def _same_named_object_types() -> list[type]:
    """Two object types both published as ``Shade``."""

    @strawberry.type(name="Shade")
    class Light:
        pale: str

    @strawberry.type(name="Shade")
    class Dark:
        deep: int

    return [Light, Dark]


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_same_named_enums, id="enums"),
        pytest.param(_same_named_object_types, id="object-types"),
    ],
)
def test_django_schema_passes_any_other_duplicate_name_through(
    build: Callable[[], list[object]],
) -> None:
    """A duplicate name the package did not generate keeps Strawberry's own error."""
    shade = build()
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"first": shade[0], "second": shade[1]},
            },
        ),
    )
    with pytest.raises(DuplicatedTypeName) as plain:
        strawberry.Schema(query=query)
    with pytest.raises(DuplicatedTypeName) as package:
        DjangoSchema(query=query)
    assert (
        str(package.value)
        == str(plain.value)
        == "Type Shade is defined multiple times in the schema"
    )


@strawberry.type
class _PostponedPrivateSurface:
    """``fooBar`` is a ``strawberry.Private`` whose type is defined only below this class.

    Under postponed annotations decoration cannot resolve it, so the field stays in
    the definition until the schema build resolves it as private.
    """

    foo_bar: int
    fooBar: strawberry.Private[_PostponedSecret]  # noqa: N815 - the camel spelling of foo_bar


class _PostponedSecret:
    """The type ``_PostponedPrivateSurface.fooBar`` names before it exists."""


@strawberry.type
class _PostponedPrivateQuery:
    surface: _PostponedPrivateSurface | None = None


def test_postponed_private_field_does_not_collide_with_the_name_it_spells() -> None:
    """A private field the schema build resolves late publishes no name, so none collides.

    ``fooBar`` reaches the build as a field and is skipped as Strawberry's conversion
    skips it; only ``foo_bar`` publishes ``fooBar``.
    """
    sdl = str(DjangoSchema(query=_PostponedPrivateQuery, config=strawberry_config()))

    assert "type Postponedprivatesurface {\n  fooBar: Int!\n}" in sdl
