"""``DjangoSchema`` - the schema whose mutation transactions span response completion.

The mutation-atomicity commit-gap fix. A generated mutation's write pipeline runs inside
``transaction.atomic()``, but graphql-core *completes* (serializes) the returned
payload only after the resolver returns - after a transaction scoped to the resolver
has already committed. A completion failure (a non-nullable field resolving ``null``,
a corrupt scalar) would therefore surface as ``data: null`` + a top-level error while
the write stays committed: the client is told the mutation failed, the database
says it succeeded.

``DjangoMutationExecutionContext`` closes the gap at the only layer that sees
both sides: for each TOP-LEVEL generated mutation field it opens one
``transaction.atomic(using=<write alias>)`` BEFORE the resolver runs and exits it
only after graphql-core finished completing that field's value. Any error added
to the execution during that window - resolver-raised or completion-raised -
marks the transaction for rollback, so an unserializable payload rolls the write
back. The window also publishes the managed alias
(``utils/write_transaction.py::managed_write_transaction``), which the write pipeline
REQUIRES: a generated mutation executed through a plain ``strawberry.Schema``
fails before any database work, directing the consumer here.

Execution-mode split:

- **Sync** (``schema.execute_sync`` / the WSGI view): graphql-core completes the
  field synchronously inside ``execute_field``, so the context holds the
  transaction directly around the ``super()`` call on the calling thread.
- **Async** (``await schema.execute`` / ASGI / Channels): each window is one
  sync call on a private thread, and therefore a private Django connection. The
  thread enters the atomic and blocks in ``async_to_sync`` while the event loop
  resolves and completes the field; asgiref sends every thread-sensitive call
  made meanwhile (the ORM pipeline's work, completion's nested resolvers) to
  that blocked thread before it consults any ``ThreadSensitiveContext``, so the
  window stays private under an outer one (Django's per-request context, or one
  a consumer shares across concurrent operations). Nothing outside the window
  reaches its connection: another socket's connection hygiene (Channels runs
  ``close_old_connections`` before every dispatched message) runs on another
  thread, and concurrent windows hold independent transactions. The atomic
  lives on the thread's own stack, so a cancellation cannot strand it: it
  reaches the completion, the thread exits the atomic, rolled back, and
  closes its connections, and the cancelled task ends only after that. Under
  a sync caller blocked in ``async_to_sync`` the window runs on that caller's
  thread and nests in whatever transaction the caller holds, exactly as sync
  execution does.

Already-running engine-owned field and list-item siblings finish inside that same
window after an ordinary async completion failure. Their shared awaitables remain
available to surviving branches. Caller cancellation cancels those siblings once
and drains cleanup across repeated cancellation; GeneratorExit propagates directly.
Nullable errors preserve upstream surviving-sibling completion; queries, unmarked
mutations and application-created jobs stay stock. The installed upstream methods
are audited lazily when an async generated-mutation window opens, so a missing or
changed source body refuses that window without preventing package import or queries.
Optional upstream iterable patches do not control this mandatory transaction boundary.

Both modes apply the same two failure rules. Any error added during the window
rolls it back. A window whose connection was closed inside it
(``close_old_connections`` run by consumer code on the window's own thread -
``channels.db.database_sync_to_async`` runs it before and after its body) cannot
commit, because Django's atomic skips the commit of a transaction whose
connection is gone, so the field fails with an error instead of reporting a
write that was never stored.

Mutation root fields execute serially (the GraphQL spec's mutation semantics,
graphql-core's ``execute_fields_serially``), so consecutive top-level mutation
fields get INDEPENDENT transactions: field two's transaction opens only after
field one's committed or rolled back.

Only fields whose resolver carries the ``DjangoMutationField`` marker are
wrapped; every other field (queries, consumer-written mutations, introspection)
executes exactly as stock graphql-core.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, TypeVar

import strawberry
from asgiref.sync import AsyncToSync, async_to_sync, sync_to_async
from django.db import DatabaseError, connections, transaction
from django.db.transaction import TransactionManagementError
from graphql import located_error
from graphql.execution.executor import to_nodes
from strawberry.exceptions import DuplicatedTypeName
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField
from strawberry.types.graphql import OperationType
from strawberry.types.private import is_private
from strawberry.utils.await_maybe import await_maybe
from typing_extensions import override

from ._completion import CompletionExecutionContext, drain_settling, owned_completion
from .error_policy import ErrorPolicy, resolve_error_policy
from .exceptions import ConfigurationError
from .extensions.error_policy import (
    DjangoErrorPolicyExtension,
    is_maskable_result,
    mask_execution_result,
    masking_is_active,
)
from .extensions.operation_state import DjangoExtensionsRunner, _OperationModeMarker
from .extensions.resource_policy import DjangoResourcePolicyExtension
from .mutations.fields import MUTATION_CLASS_MARKER
from .relay import refuse_unreturnable_node_targets
from .resource_policy import ResourcePolicy, resolve_resource_policy
from .utils import truth
from .utils.execution_mode import OperationMode, async_execution
from .utils.inputs import field_name_collision_remedy, generated_type_name_collision
from .utils.typing import call_forwarded, wrapped_resolver
from .utils.write_transaction import managed_write_transaction, resolve_write_alias

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from typing import Protocol, TypeAlias

    from graphql import FieldNode, GraphQLObjectType
    from graphql.execution import Executor
    from graphql.execution.collect_fields import FieldDetailsList
    from graphql.execution.incremental.incremental_executor import DeliveryGroupMap
    from graphql.pyutils import AwaitableOrValue, Path, UndefinedType
    from strawberry.extensions.runner import SchemaExtensionsRunner
    from strawberry.schema.config import StrawberryConfig
    from strawberry.schema.schema import StreamResult
    from strawberry.types import ExecutionContext as StrawberryExecutionContext
    from strawberry.types import ExecutionResult as StrawberryExecutionResult

    #: One ``extensions=`` entry as Strawberry resolves it: an instance answers for itself,
    #: and anything else (a class, a factory) is called once per operation for one.
    _ExtensionEntry: TypeAlias = (
        SchemaExtension | type[SchemaExtension] | Callable[[], SchemaExtension]
    )

    from .write_mixins import WriteMutationClass

    class _DBAPIConnection(Protocol):
        """The raw handle a Django connection wraps, as far as closing it goes (PEP 249)."""

        def close(self) -> object: ...

    class _RawHandleOwner(Protocol):
        """A Django connection as far as its raw handle goes; django-stubs types the slot ``Any``."""

        connection: _DBAPIConnection | None


#: What one window's ``run`` produces, handed back unchanged.
_WindowT = TypeVar("_WindowT")

#: The message of the field error a window reports when its connection was closed
#: inside the transaction: Django's ``Atomic.__exit__`` skips the commit of such a
#: transaction without raising, so without this the payload would describe a row the
#: database never stored.
_CLOSED_WINDOW_MESSAGE = (
    "The database connection was closed before the mutation's transaction could "
    "commit; nothing was written."
)


def _close_thread_connections() -> None:
    """Close every Django connection the CURRENT thread opened, then drop its handle.

    Runs on a window's private thread as the window's last step, because that
    thread ends with the window and Django keeps connections per
    thread: nothing else can ever close them. A backend may decline ``close()`` -
    SQLite keeps an in-memory database's handle open, since closing it would
    destroy that connection's database - but the thread owning the handle is
    ending either way, so the raw handle is closed here rather than by the
    finalizer. A ``DatabaseError`` from closing a connection that is being
    discarded changes nothing the window reports (the transaction has already
    committed or rolled back), so it does not replace the window's outcome.
    """
    for connection in connections.all(initialized_only=True):
        with contextlib.suppress(DatabaseError):
            connection.close()
        _drop_raw_handle(connection)


def _drop_raw_handle(owner: _RawHandleOwner) -> None:
    """Close the raw handle ``owner`` still holds, if any, and clear the slot."""
    handle = owner.connection
    if handle is not None:
        _ = handle.close()
        owner.connection = None


def _window_drained() -> None:
    """Do nothing: queued behind a window, it completes once the window has returned."""


async def _outlast_cancellation(done: asyncio.Future[None]) -> None:
    """Wait until ``done`` completes, however often the awaiting task is cancelled.

    The caller re-raises its own cancellation afterwards, so the task still ends
    cancelled; only the moment it ends moves.
    """
    while not done.done():
        with contextlib.suppress(asyncio.CancelledError):
            _ = await asyncio.wait((done,))


class DjangoMutationExecutionContext(CompletionExecutionContext):
    """Generated-mutation execution context.

    The execution context that holds each generated mutation field's transaction open
    through value completion.
    """

    @override
    def execute_field(
        self,
        parent_type: GraphQLObjectType,
        source: object,
        field_details_list: FieldDetailsList,
        path: Path,
        position_context: DeliveryGroupMap | None,
    ) -> AwaitableOrValue[object] | UndefinedType:
        """Wrap a marked top-level mutation field in its completion-spanning transaction."""
        field_nodes = to_nodes(field_details_list)
        mutation_cls = self._marked_mutation_class(parent_type, field_nodes)
        execute = functools.partial(
            super().execute_field,
            parent_type,
            source,
            field_details_list,
            path,
            position_context,
        )
        if mutation_cls is None:
            return execute()

        mutation_meta = truth.static_attr(mutation_cls, "_mutation_meta", None)
        model = getattr(mutation_meta, "model", None)
        alias = resolve_write_alias(model)
        if async_execution():
            return self._execute_mutation_field_async(alias, field_nodes, path, execute)
        return self._run_window(alias, field_nodes, path, execute)

    def _marked_mutation_class(
        self,
        parent_type: GraphQLObjectType | None,
        field_nodes: list[FieldNode],
    ) -> WriteMutationClass | None:
        """Return the field's bound mutation class, or ``None`` for any unmarked field.

        Only TOP-LEVEL mutation fields qualify (``parent_type`` is the schema's
        mutation root; ``execute_field`` also fires for every nested payload
        field, whose completion the already-open transaction covers). The marker
        is read off the synthesized ``_resolve`` the ``DjangoMutationField``
        factory stamped with its mutation class (``utils/typing.py::wrapped_resolver``).
        """
        if (
            parent_type is None
            or self.schema.mutation_type is None
            or parent_type is not self.schema.mutation_type
        ):
            return None
        if not field_nodes:
            return None
        field_def = self.schema.get_field(parent_type, field_nodes[0].name.value)
        return getattr(wrapped_resolver(field_def), MUTATION_CLASS_MARKER, None)

    def _refuse_uncommitted_window(
        self,
        alias: str,
        field_nodes: list[FieldNode],
        path: Path,
    ) -> None:
        """Fail the field when the window's connection was closed inside its transaction.

        The window's closed-connection rule, consulted after the atomic exited in
        both execution modes. Closing a connection inside an atomic block marks it
        ``closed_in_transaction``, and ``Atomic.__exit__`` then skips the commit
        WITHOUT raising (the database rolls the transaction back itself), so a
        clean exit alone would let the field report a payload - often a node id -
        for a write that was never stored. The flag stays set until the
        connection is next opened, so it is still readable here. The error is
        located at the mutation field, exactly as graphql-core locates a
        resolver's failure on a non-null field.
        """
        if connections[alias].closed_in_transaction:
            raise located_error(
                TransactionManagementError(_CLOSED_WINDOW_MESSAGE),
                field_nodes,
                path.as_list(),
            )

    def _run_window(
        self,
        alias: str,
        field_nodes: list[FieldNode],
        path: Path,
        run: Callable[[], _WindowT],
    ) -> _WindowT:
        """Hold one window's transaction around ``run`` on the calling thread.

        The window body of both execution modes: ``run`` resolves and completes
        the field under the managed alias, and an exception escaping it exits the
        atomic with that exception (rolled back). Any located error added to the
        execution during the window - resolver-raised or completion-raised - marks
        the transaction for rollback before it exits: a resolver failure is a
        located error, not an exception, and ``collected_errors.errors`` is
        append-only during execution, so comparing its length is enough. The
        closed-connection rule runs after the atomic has exited.
        """
        errors_before = len(self.collected_errors.errors)
        with transaction.atomic(using=alias):
            with managed_write_transaction(alias):
                result = run()
            if len(self.collected_errors.errors) > errors_before:
                transaction.set_rollback(True, using=alias)
        self._refuse_uncommitted_window(alias, field_nodes, path)
        return result

    async def _execute_mutation_field_async(
        self,
        alias: str,
        field_nodes: list[FieldNode],
        path: Path,
        execute: Callable[[], AwaitableOrValue[object] | UndefinedType],
    ) -> object:
        """Async execution: run the window on a thread that drives the completion.

        ``window`` is one sync call: it enters the atomic, then blocks in
        ``async_to_sync(complete)`` while the event loop resolves and completes
        the field. asgiref sends every thread-sensitive call from ``complete``'s
        task tree (the pipeline's ``run_in_one_sync_boundary`` work, completion's
        nested resolvers, ``channels.db.database_sync_to_async``) to the thread
        blocked in ``async_to_sync`` before it consults any
        ``ThreadSensitiveContext``, so the enter, the pipeline's queries and the
        exit share one connection. Outside a blocked sync caller that thread is
        a private single-thread executor's, whose connections ``window`` closes
        when it ends; under one (``AsyncToSync.executors.current`` set) it is
        the caller's thread, and the window nests in the caller's transaction
        and leaves its connections alone.

        A cancellation arriving while ``complete`` runs is propagated into it by
        ``SyncToAsync``; one arriving before ``complete`` started has no task to
        reach, so it sets ``cancelled`` and ``complete`` raises it on entry
        (both on the event loop). Either way the thread exits the atomic with
        the cancellation, rolled back.

        A cancelled private window ends only once its thread has returned from
        ``window``: ``SyncToAsync`` stops waiting for the thread when the
        cancellation is repeated, so the task waits for a no-op queued behind
        ``window`` on the executor's one worker, across any further
        cancellation, and then re-raises. Without that the next mutation could
        start while this window still holds its write. On a caller's thread no
        wait is owed: the caller's executor runs work in order, so nothing the
        caller runs next can overtake the window.

        ``AsyncToSync.executors.current`` is the one asgiref attribute read, and
        the precedence it relies on - ``SyncToAsync.__call__`` takes the caller's
        executor before any context, ``AsyncToSync.__call__`` publishes its
        executor before copying the context ``complete`` runs in, and a
        cancelled ``SyncToAsync`` cancels the task recorded in ``task_context`` -
        is unchanged in every release from 3.8.1 (the minimum the Django floor
        requires) through 3.12.1.
        """
        cancelled = False

        async def complete() -> object:
            if cancelled:
                raise asyncio.CancelledError
            with owned_completion(self) as settling:
                try:
                    return await await_maybe(execute())
                finally:
                    await drain_settling(settling)

        caller = getattr(AsyncToSync.executors, "current", None)

        def window() -> object:
            try:
                return self._run_window(alias, field_nodes, path, async_to_sync(complete))
            finally:
                if caller is None:
                    _close_thread_connections()

        executor = None
        if caller is None:
            executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="django-strawberry-framework-mutation",
            )
        try:
            return await sync_to_async(
                window,
                thread_sensitive=executor is None,
                executor=executor,
            )()
        except asyncio.CancelledError:
            cancelled = True
            if executor is not None:
                await _outlast_cancellation(asyncio.wrap_future(executor.submit(_window_drained)))
            raise
        finally:
            if executor is not None:
                executor.shutdown(wait=False)


#: The stable ``extensions.code`` name reserved for a schema-configuration refusal,
#: exported beside ``RESOURCE_LIMIT_ERROR_CODE``; no package path emits it, and it is
#: distinct from a resource rejection, since nothing about a request decides it.
SCHEMA_CONFIGURATION_ERROR_CODE = "SCHEMA_CONFIGURATION_UNAVAILABLE"


def _operation_mode(*, sync: bool) -> OperationMode:
    """Return the executor this operation is being driven by, from the flag upstream passed.

    ``get_extensions(sync=True)`` is ``execute_sync`` and nothing else;
    ``execute``, ``stream`` and ``subscribe`` all leave it false. That flag is
    the authoritative statement of which executor holds the operation, and it is
    the only one: the ambient event loop answers a different question and
    disagrees with this one whenever a synchronous operation is started from
    inside an asynchronous one.
    """
    return OperationMode.SYNC if sync else OperationMode.ASYNC


class DjangoSchema(strawberry.Schema):
    """``strawberry.Schema`` with the mutation-transaction execution context installed.

    The REQUIRED schema class for any schema exposing generated mutations
    (``DjangoMutationField`` targets): the write pipeline refuses to run outside
    the managed transaction this schema's execution context opens. Drop-in
    otherwise - every constructor argument passes through (a ``config=`` that
    enables incremental delivery is refused, below), and a consumer
    needing a custom execution context subclasses
    ``DjangoMutationExecutionContext`` and passes it explicitly.

    **The execution resource policy is resolved here, once.** ``resource_policy=``
    accepts a ``ResourcePolicy`` or a mapping of bound names to values; omitted,
    the ``DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]`` setting and then the
    package defaults apply. The resolved object is validated at construction - an
    invalid bound fails the deployment at startup, not on a request - is exposed
    as ``schema.resource_policy``, and is enforced by
    ``extensions/resource_policy.py::DjangoResourcePolicyExtension``, which every
    operation's chain begins and ends with whatever the consumer configured. A
    schema built through this class is therefore bounded with no opt-in
    boilerplate, which is the whole point: an endpoint whose only limiter is one
    a consumer remembered to install is an endpoint with no limiter.

    **The production error policy is resolved here too, and by the same rule.**
    ``error_policy=`` accepts an ``ErrorPolicy`` or a mapping of option names to
    values; omitted, the ``DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]`` setting
    and then the package defaults apply. It is validated at construction, exposed
    as ``schema.error_policy``, and enforced by
    ``extensions/error_policy.py::DjangoErrorPolicyExtension``, which is FIRST in
    every operation's chain - the position is load-bearing, see
    ``_admitted_chain``. Under ``settings.DEBUG = False`` an unexpected resolver
    or hook exception therefore reaches the client as a stable message plus a
    correlation identifier rather than as whatever the exception happened to say.
    Opting out is explicit: ``DjangoSchema(error_policy={"enabled": False})``.

    **An exception that escapes a HOOK is masked by this class rather than by
    that extension**, because upstream converts such an exception into a result
    only after every teardown has unwound, and nothing an extension can hook runs
    afterwards. :meth:`_masked_return` is that seam, applied to what
    :meth:`execute` and :meth:`execute_sync` hand back; it shares the extension's
    one masking implementation and is a no-op on a result the teardown already
    masked. A consumer assembling a plain ``strawberry.Schema`` around the
    exported extension has no such seam, so a hook failure is unmasked there.

    **Both authorities are the schema's, not entries in ``extensions=``.** They
    are built per operation from the two policies this constructor resolves, so
    ``extensions=`` carries the consumer's own extensions and nothing else, and
    the two arguments above are the only way to configure what enforces a
    request. Supplying ``DjangoResourcePolicyExtension(policy=...)`` as an entry
    is read as a declaration of that policy - the entry is
    folded into the schema's policy rather than kept - and declaring the policy twice is
    refused here. A subclass of either enforcement extension, or a factory
    returning one, is an ordinary consumer entry.

    **Incremental delivery is refused at construction.** A ``config=`` with
    ``enable_experimental_incremental_execution`` set raises
    ``ConfigurationError`` (:func:`_refuse_incremental_execution`): masking, the
    resource bounds and deadline, and the mutation transaction window each hold
    for one response per operation, and a ``@defer`` / ``@stream`` payload is
    delivered outside it.

    **A generated type-name clash names its declarations.** Two generated input
    classes of different fields under one GraphQL type name (two sets, two
    families, or a model and a form or serializer deriving one name) cannot share
    a schema; Strawberry refuses the pair with ``DuplicatedTypeName``, and this
    class restates that refusal as ``ConfigurationError`` naming the two
    declarations and members that generated them
    (``utils/inputs.py::generated_type_name_collision``). Any other duplicate name
    passes through with Strawberry's own error.

    **Two fields this schema names alike are refused.** Strawberry keeps one of
    two distinct fields its ``NameConverter`` gives one GraphQL name and drops the
    other with no error; this class raises ``ConfigurationError`` naming the type
    and both fields and, for two generated input fields, the declaration and the
    members they are generated from (:func:`_refuse_field_name_collisions`). The name is this
    schema's, so ``foo_bar`` beside ``fooBar`` is refused under the default
    ``auto_camel_case=True`` and served as two fields under
    ``auto_camel_case=False``.

    **A typed node field that cannot return its target is refused.**
    ``DjangoNodeField(GenreType)`` / ``DjangoNodesField(GenreType)`` whose published
    return type cannot hold ``GenreType``, or whose target this schema does not
    publish, raises ``ConfigurationError`` naming the field
    (``relay.py::refuse_unreturnable_node_targets``): such a field answers only
    refusals. A plain ``strawberry.Schema`` builds it and refuses the target's ids
    at request time.
    """

    def __init__(
        self,
        *args: object,
        resource_policy: ResourcePolicy | Mapping[str, object] | None = None,
        error_policy: ErrorPolicy | Mapping[str, object] | None = None,
        extensions: Iterable[_ExtensionEntry] | None = None,
        execution_context_class: type[Executor[DeliveryGroupMap]] | None = None,
        config: StrawberryConfig | None = None,
        **kwargs: object,
    ) -> None:
        """Build the schema, settling the two policies and forwarding the rest to Strawberry.

        ``extensions``, ``execution_context_class`` and ``config`` are Strawberry's
        own arguments, read here before they are forwarded. Every other argument is
        forwarded verbatim, so a parameter an uncapped Strawberry adds passes through.
        """
        entries, declared_resource = _consumer_extension_entries(extensions)
        if declared_resource is not None and resource_policy is not None:
            raise ConfigurationError(
                "A schema's resource policy is declared once. This one is declared "
                "twice - by DjangoSchema(resource_policy=...) and by a "
                "DjangoResourcePolicyExtension(policy=...) entry - and the two "
                "declarations are not composable into one ceiling. Keep the "
                "resource_policy= argument.",
            )
        resolved_resource = resolve_resource_policy(
            resource_policy if declared_resource is None else declared_resource,
        )
        resolved_error = resolve_error_policy(error_policy)
        _refuse_incremental_execution(config)
        # Strawberry resolves an entry as ``ext if isinstance(ext, SchemaExtension)
        # else ext()``, so anything that is neither an instance nor callable would
        # fail at the first operation, deep inside the engine; it is named here.
        for entry in entries:
            if not _is_resolvable_extension_entry(entry):
                raise ConfigurationError(
                    "Every entry in DjangoSchema(extensions=[...]) has to be something "
                    "Strawberry can resolve into an extension for an operation - a "
                    "SchemaExtension subclass, an instance of one, or a callable that "
                    f"returns one. {truth.describe(entry)} is none of those.",
                )
        self._resource_policy: ResourcePolicy = resolved_resource
        self._error_policy: ErrorPolicy = resolved_error
        if execution_context_class is None:
            execution_context_class = DjangoMutationExecutionContext
        forwarded: dict[str, object] = {
            **kwargs,
            "execution_context_class": execution_context_class,
            "config": config,
        }
        # basedpyright: Strawberry's schema/_graphql_core.py aliases graphql-core's bare generic
        # Executor, so Schema.__init__'s execution_context_class carries Unknown; the other
        # arguments are forwarded verbatim, and ``extensions`` carries the instances Strawberry
        # accepts at run time but leaves out of its annotation
        try:
            super().__init__(*args, extensions=entries, **forwarded)  # pyright: ignore[reportUnknownMemberType, reportArgumentType]
        except DuplicatedTypeName as exc:
            # Two generated input classes of different fields under one name reached
            # this schema (``utils/inputs.py::claim_generated_type_name`` gave the
            # second its own identity so Strawberry refuses it here rather than merge
            # it): restate the refusal naming the declarations that generated them.
            # Any other duplicate is Strawberry's to report.
            restated = generated_type_name_collision(exc.second_cls, exc.first_cls)
            if restated is None:
                raise
            raise restated from exc
        _refuse_field_name_collisions(self)
        refuse_unreturnable_node_targets(self)

    @property
    def resource_policy(self) -> ResourcePolicy:
        """The resolved execution resource policy: read-only, and a frozen dataclass.

        There is no setter, so assigning the attribute raises ``AttributeError``
        and changes no later request.
        """
        return self._resource_policy

    @property
    def error_policy(self) -> ErrorPolicy:
        """The resolved error policy: read-only, and a frozen dataclass.

        Read-only on the same terms as :attr:`resource_policy`, for the policy
        whose ``enabled`` decides whether an unexpected exception is masked at all.
        """
        return self._error_policy

    @override
    def get_extensions(self, sync: bool = False) -> list[SchemaExtension]:
        """Resolve the entries into this operation's chain, between this schema's authorities.

        The chain is this schema's two enforcement authorities with the
        consumer's resolved extensions between them (:func:`_admitted_chain`):
        the error policy tears down last, so it is first, and the resource
        policy sets up last, so it is last.
        """
        return _admitted_chain(super().get_extensions(sync=sync), sync=sync)

    @override
    def create_extensions_runner(
        self,
        execution_context: StrawberryExecutionContext,
        extensions: list[SchemaExtension],
    ) -> SchemaExtensionsRunner:
        """Build the runner that owns every framework extension's operation state.

        The one point that sees the resolved extension list and this operation's
        engine context together, after upstream's assignment loop and without
        calling a factory a second time - which is why the boundary is here and
        not in each extension's hooks. A class entry, an accepted instance and a
        factory returning a shared singleton all arrive as resolved members, and
        all three get one state per operation out of this.

        The context handed here is the whole input: upstream assigns
        ``execution_context`` on every resolved extension just before this call
        and runs no hook in between, so the assignment carries nothing this
        argument does not, and recording it would only add a place for a
        half-built request to be left behind.
        """
        return DjangoExtensionsRunner(
            execution_context=execution_context,
            extensions=extensions,
        )

    @override
    def execute_sync(
        self,
        query: str | None,
        variable_values: dict[str, object] | None = None,
        context_value: object = None,
        root_value: object = None,
        operation_name: str | None = None,
        allowed_operation_types: Iterable[OperationType] | None = None,
        operation_extensions: dict[str, object] | None = None,
    ) -> StrawberryExecutionResult:
        """Run the operation synchronously and mask what is RETURNED.

        The masking extension's teardown answers for a result upstream assigned
        to the execution context, and for the ordinary operation that is the same
        object this returns. It is not the same object when an exception escaped
        a hook: upstream converts that exception into a fresh result inside the
        ``except`` behind its operation lifecycle, which runs after every teardown
        has already unwound over an execution context whose ``result`` was still
        ``None``. No extension can reach that result, because none is still
        running when it is built - so the schema masks the value it hands back.
        """
        result = super().execute_sync(
            query,
            variable_values,
            context_value,
            root_value,
            operation_name,
            allowed_operation_types,
            operation_extensions,
        )
        return self._masked_return(result)

    @override
    async def execute(
        self,
        query: str | None,
        variable_values: dict[str, object] | None = None,
        context_value: object = None,
        root_value: object = None,
        operation_name: str | None = None,
        allowed_operation_types: Iterable[OperationType] | None = None,
        operation_extensions: dict[str, object] | None = None,
    ) -> StrawberryExecutionResult:
        """Run the operation asynchronously and mask what is RETURNED.

        The async twin of :meth:`execute_sync`, for the same reason and with the
        same one hole to close: upstream's own ``except`` hands the coerced
        exception to a handler that assigns ``execution_context.result`` only
        AFTER the operation lifecycle has finished unwinding, so the teardown saw
        nothing and the leak is identical. Streamed operations are not masked
        here - each frame is masked at the transport's result source - and
        nothing about this override touches them.
        """
        result = await super().execute(
            query,
            variable_values,
            context_value,
            root_value,
            operation_name,
            allowed_operation_types,
            operation_extensions,
        )
        return self._masked_return(result)

    def _masked_return(self, result: StrawberryExecutionResult) -> StrawberryExecutionResult:
        """Apply this schema's error policy to one returned execution result.

        The gates and the masking itself are the extension module's own
        (``extensions/error_policy.py``), so this seam cannot drift from the
        operation teardown or the streamed-result source on what counts as
        active, what shape is maskable, or what a masked error looks like.

        **Masking twice preserves error identity.** Already-masked errors carry
        no ``original_error``, so no second correlation id is minted or logged.
        The final return snapshots the list after extension result collection,
        including an all-deliberate or empty list. Later engine appends cannot
        change what an awaiting HTTP result hook publishes. Debug and disabled
        policies retain their pass-through behavior.
        """
        policy = self._error_policy
        if not masking_is_active(policy) or not is_maskable_result(result):
            return result
        return mask_execution_result(result, policy, snapshot=True)

    @override
    def _stream(
        self,
        execution_context: StrawberryExecutionContext,
        extensions_runner: SchemaExtensionsRunner,
        *args: object,
        **kwargs: object,
    ) -> StreamResult:
        """Stream the operation's frames with this operation bound in every task.

        The narrowest seam that already receives the exact runner and the raw
        iterator upstream built, which is what the wrapper needs: a streamed
        operation's frames are produced wherever the transport drives them, and
        an async generator's body runs in the resuming caller's context. Upstream
        binds nothing per resume because nothing upstream is task-local; this
        package's budget, operation state and optimizer frame all are.

        ``stream`` and ``subscribe`` both come through here - the second is a
        thin wrapper around the first - so one override covers every streamed
        operation on every transport. A runner some subclass built instead is
        passed through untouched: the wrapper binds what a
        :class:`DjangoExtensionsRunner` owns and has nothing to say about
        anything else.
        """
        upstream_args = (execution_context, extensions_runner, *args)
        # basedpyright: Strawberry types ``_stream``'s ``execution_context_class`` as graphql-core's
        # bare generic ``Executor``, so the method reads as partially Unknown
        source = call_forwarded(super()._stream, upstream_args, kwargs)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        if truth.is_instance(extensions_runner, DjangoExtensionsRunner):
            return extensions_runner.resumed_stream(source)
        return source


def _is_resolvable_extension_entry(entry: object) -> bool:
    """Whether Strawberry can turn ``entry`` into an extension for an operation.

    Its resolution is ``entry if isinstance(entry, SchemaExtension) else
    entry()``, so an instance answers for itself and everything else has to be
    callable - which a class and a factory both are. The instance test is
    ``utils/truth.py::is_instance``, which reads the entry's real class.
    """
    return truth.is_instance(entry, SchemaExtension) or callable(entry)


def _admitted_chain(resolved: list[SchemaExtension], *, sync: bool) -> list[SchemaExtension]:
    """Return the schema's authorities around ``resolved``.

    The error policy is FIRST and the resource policy LAST, and both positions
    are the contract (spec-048 Decision 10). Strawberry's ``on_operation``
    teardowns unwind LIFO, so the first-listed extension tears down last - and
    masking must be last, after every extension that reads
    ``GraphQLError.original_error`` has had its turn.
    ``extensions/debug.py::DjangoDebugExtension`` is exactly such an extension
    and is documented to be listed after any masking extension. The resource
    policy is last for the mirror-image reason: it gates BEFORE execution, so it
    wants to set up last, with its own budget armed around every consumer hook.

    The resource policy's own validation hook restates a rejection a consumer
    validation hook ahead of it replaced, and nothing sets up after it, so the
    published rejection survives every consumer entry wherever the consumer put
    a validation cache.

    Both authorities are constructed fresh per operation and read their
    configuration from this schema. An
    instance shared across operations would share one set of charge counters
    between concurrent requests.

    The mode marker goes last because it is not a hook at all: it
    declares which executor is driving this operation, the runner reads it out
    of this list, and nothing in the chain's setup or teardown order has
    anything to say about it (``utils/execution_mode.py``).
    """
    return [
        DjangoErrorPolicyExtension(),
        *resolved,
        DjangoResourcePolicyExtension(),
        _OperationModeMarker(_operation_mode(sync=sync)),
    ]


def _refuse_field_name_collisions(schema: strawberry.Schema) -> None:
    """Refuse two fields of one published type that this schema names alike.

    Strawberry keys each object, interface and input type's GraphQL fields by
    ``config.name_converter.from_field`` (``_get_thunk_mapping`` in
    ``strawberry/schema/schema_converter.py``), so two distinct fields the
    converter names alike leave ONE field on the wire and the other silently
    dropped, with no error. The name is the executing schema's: ``foo_bar``
    beside ``fooBar`` collides under the default ``auto_camel_case=True``, not
    under ``auto_camel_case=False``, and a custom ``NameConverter`` can collide
    two names neither of those does. One ``DjangoType`` (or merged mutation
    input) can be served by schemas of different configs, so the check runs
    here, per schema, over the same fields the conversion walked: the schema's
    own ``get_fields`` with ``strawberry.Private`` ones skipped. The refusal names
    what the consumer can change (``utils/inputs.py::field_name_collision_remedy``):
    a generated input field takes no ``name=``, so two of them name the set,
    mutation, form or serializer and the members they are generated from.
    """
    name_converter = schema.config.name_converter
    for type_name, concrete in schema.schema_converter.type_map.items():
        definition = concrete.definition
        if not truth.is_instance(definition, StrawberryObjectDefinition):
            continue
        published: dict[str, StrawberryField] = {}
        for field in schema.get_fields(definition):
            if is_private(field.type):
                continue
            graphql_name = name_converter.from_field(field)
            prior = published.setdefault(graphql_name, field)
            if prior is field:
                continue
            raise ConfigurationError(
                f"{type_name}: fields {prior.python_name!r} and {field.python_name!r} both "
                f"publish the GraphQL field name {truth.text(graphql_name)!r} under this schema's name "
                "converter, so one would silently replace the other. "
                f"{field_name_collision_remedy(prior, field)}",
            )


def _refuse_incremental_execution(config: StrawberryConfig | None) -> None:
    """Refuse a config that turns on incremental delivery (``@defer`` / ``@stream``).

    Every guarantee this schema enforces is enforced on ONE response per
    operation: the error policy masks the result an operation hands back, the
    resource bounds and the deadline are armed for the operation's scope, and a
    generated mutation's transaction spans the completion of its own payload.
    A deferred payload is delivered after that response, outside all three, so
    a schema that accepted the flag would publish those guarantees while serving
    frames none of them reach. On the graphql-core this package pins the flag
    has no executor at all and fails every operation with a raw ``RuntimeError``
    outside every extension; refusing it here names that misconfiguration at
    startup instead of on every request.

    The flag is read the way Strawberry reads it - by truthiness, from the
    ``config=`` argument - because that is what decides whether Strawberry takes
    the incremental path. ``config`` is a keyword-only parameter of
    :meth:`DjangoSchema.__init__`, so it is the only spelling that reaches it.
    """
    if config is None or not config.enable_experimental_incremental_execution:
        return
    raise ConfigurationError(
        "DjangoSchema does not support incremental delivery (@defer / @stream): the "
        "error policy, the execution resource bounds and deadline, and a generated "
        "mutation's transaction are each enforced on one response per operation, "
        "and a deferred payload is delivered outside it. Remove "
        "enable_experimental_incremental_execution from the StrawberryConfig.",
    )


def _consumer_extension_entries(
    extensions: Iterable[object] | None,
) -> tuple[list[object], ResourcePolicy | None]:
    """Split ``extensions`` into the consumer's entries and the policy one of them declared.

    An enforcement extension supplied directly (the class itself, or an instance
    of exactly that class) is a CONFIGURATION statement rather than a chain
    member: the schema installs its own of each kind on every operation, so
    keeping the entry too would put two of a kind in the chain. Such an entry is
    read once, here, and what it declared is folded into the schema's policy;
    the entry itself does not travel. A bare class entry, an error-policy entry
    and a resource-policy instance built without a policy declare nothing beyond
    the automatic extension and are dropped; a resource-policy instance declares
    the policy it was constructed with. ``None`` comes back when no entry
    declared one, which is the ordinary case.
    """
    supplied = [] if extensions is None else list(extensions)
    entries: list[object] = []
    declared: ResourcePolicy | None = None
    for entry in supplied:
        kind = entry if isinstance(entry, type) else type(entry)
        if kind is not DjangoResourcePolicyExtension and kind is not DjangoErrorPolicyExtension:
            entries.append(entry)
            continue
        if not isinstance(entry, DjangoResourcePolicyExtension):
            continue
        policy = entry._explicit_policy
        if policy is None:
            continue
        if declared is not None:
            raise ConfigurationError(
                "DjangoSchema(extensions=[...]) carries two resource-policy "
                "extensions declaring a policy of their own, and an operation is "
                "bounded by one. Declare it once, with "
                "DjangoSchema(resource_policy=...).",
            )
        declared = policy
    return entries, declared
