"""``ResourcePolicy`` - the one immutable execution resource budget for a request.

Spec: ``docs/SPECS/spec-047-resource_policy-0_0_14.md``.

A GraphQL endpoint's cost is not bounded by its schema. A single small document
can ask for an unbounded number of rows, and a single small *variable* payload
can ask for an unbounded number of ids, filter terms, or upload bytes. Both
halves of that are bounded here, by one object rather than by settings reads
scattered across resolvers:

- the **document budget** - tokens, structural nesting depth, expanded selection
  and alias counts, and the aggregate collection cost the document would drive;
- the **value budget** - total input nodes, container nesting depth, container
  width, membership-list items, node-refetch ids, per-mutation and per-request
  relation ids, nested input rows, upload count / per-file bytes / aggregate
  bytes, and scalar byte size; and
- the **collection bounds** the fields themselves enforce - maximum page size for
  a connection, maximum rows for a raw list.

Three properties are contractual:

**Normalized once.** ``resolve_resource_policy`` validates every bound at schema
construction (``schema.py::DjangoSchema``), so an invalid deployment fails at
startup and no resolver re-reads or re-validates a setting per request.

**Immutable and armed for the whole operation.** The resolved policy is armed as
the operation's authoritative budget by ``begin_resource_budget`` and read back
by ``policy_from_info`` and ``check_deadline``. The authority is a ``ContextVar``
rather than a request-context key, so a resolver cannot widen the budget by
REPLACING it, and the policy is a frozen dataclass. The same call publishes the
policy and its derived deadline under ``DST_RESOURCE_POLICY`` /
``DST_RESOURCE_DEADLINE``, mirroring the optimizer's ``DST_OPTIMIZER_*`` context
seam; those keys are a consumer-readable mirror, and no enforcement seam trusts
them while a budget is armed.

**Narrowing-only per field.** ``effective_bound`` is how a field applies its own
declared maximum: the tighter of the field's value and the request policy wins.
The schema-construction policy IS the trusted declaration - it is the only place
that may widen a package default - and a per-field value may widen it only under
an explicit ``trusted=True`` opt-in at the call site.

Fail-closed defaults. Every bound is a positive integer with a package default;
there is no "disable this bound" spelling, and a context with no stashed policy
reads back the package's own baseline rather than "unbounded". The one optional
bound is ``execution_deadline_seconds``, which defaults to ``None`` because a
wall-clock deadline that a deployment did not choose is a correctness hazard, not
a safety one.
"""

from __future__ import annotations

import math
import time
from contextvars import ContextVar, Token
from dataclasses import dataclass, fields, replace
from itertools import islice
from typing import TYPE_CHECKING, TypeGuard, TypeVar, overload

from django.db.models import Model, QuerySet
from graphql import GraphQLError
from typing_extensions import override

from .conf import resource_policy_setting
from .exceptions import ConfigurationError, DjangoStrawberryFrameworkError
from .utils import introspection
from .utils._narrowing import iter_of, read_attr, require_instance
from .utils.context import get_context_value, stash_on_context
from .utils.errors import coded_error_extensions
from .utils.policies import resolve_policy
from .utils.querysets import _is_queryset, is_async_only_iterable

if TYPE_CHECKING:
    from collections.abc import AsyncIterable, Iterable, Mapping

__all__ = (
    "DEFAULT_RESOURCE_POLICY",
    "DST_RESOURCE_DEADLINE",
    "DST_RESOURCE_POLICY",
    "MAX_RESOURCE_BOUND",
    "RESOURCE_LIMIT_ERROR_CODE",
    "ResourceLimitExceeded",
    "ResourcePolicy",
    "begin_resource_budget",
    "bounded_rows",
    "bounded_rows_async",
    "check_deadline",
    "effective_bound",
    "end_resource_budget",
    "policy_from_info",
    "resolve_resource_policy",
    "validate_collection_bound",
    "validate_trusted_flag",
)


#: The single wire-visible ``extensions.code`` every resource rejection carries.
#: Sync HTTP, async HTTP, WebSocket queries / mutations and a rejected
#: SUBSCRIPTION all render the rejection as an ordinary GraphQL error entry, so
#: one code is what makes them recognizable as the same failure rather than
#: four: the admission stage publishes its verdict as the operation's
#: pre-execution error, and the streaming path yields that as its one frame.
#: The exception is the pre-parse token and structural-depth scan, which has to
#: refuse before a document exists and therefore raises; a streaming caller sees
#: that as an exception out of the operation rather than as this code.
RESOURCE_LIMIT_ERROR_CODE = "RESOURCE_LIMIT_EXCEEDED"

#: Request-context keys, mirroring the optimizer's ``DST_OPTIMIZER_*`` seam.
DST_RESOURCE_POLICY = "dst_resource_policy"
DST_RESOURCE_DEADLINE = "dst_resource_deadline"


# basedpyright: ``GraphQLError.__init__`` calls ``super().__init__(message)``, which reaches
# ``BaseException.__init__`` through the package base (it defines no ``__init__``)
class ResourceLimitExceeded(GraphQLError, DjangoStrawberryFrameworkError):  # pyright: ignore[reportUnsafeMultipleInheritance]  # noqa: N818 - the wire-visible name of a bound rejection, not an internal error class
    """A request exceeded one of its resource bounds; nothing was executed.

    Multiple-inherits ``GraphQLError`` (so the rejection travels the wire as a
    normal error entry carrying ``extensions.code`` wherever Strawberry renders
    a pre-execution failure into the response envelope, which is every transport
    except a WebSocket subscription - see ``RESOURCE_LIMIT_ERROR_CODE``) and the
    package base (so a consumer can
    ``except DjangoStrawberryFrameworkError`` alongside every other framework
    error). The ``SyncMisuseError`` precedent.

    ``bound`` names the ``ResourcePolicy`` field that rejected, ``limit`` is its
    configured value, and ``charged`` is the amount the request asked for. All
    three ride in ``extensions`` so a client can act on the rejection without
    parsing prose.
    """

    def __init__(
        self,
        bound: str,
        limit: int,
        charged: int,
        detail: str,
    ) -> None:
        """Name the exceeded ``bound`` with its ``limit``, the ``charged`` amount and a ``detail``."""
        super().__init__(
            f"Request exceeds the {bound} resource bound: {detail} "
            f"({charged} charged, {limit} allowed).",
            extensions=coded_error_extensions(
                RESOURCE_LIMIT_ERROR_CODE,
                bound=bound,
                limit=limit,
                charged=charged,
            ),
        )
        self.bound: str = bound
        self.limit: int = limit
        self.charged: int = charged
        self.detail: str = detail

    @override
    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (
            type(self),
            (
                self.bound,
                self.limit,
                self.charged,
                self.detail,
            ),
            self.__dict__,
        )


def _is_builtin_number(value: object) -> TypeGuard[int | float]:
    """Whether ``value`` is an exact built-in ``int`` or ``float``.

    The test is EXACT, not ``isinstance``, everywhere a number crosses into the
    budget machinery - a deployment's configured bound, a consumer-written
    deadline mirror, an uploaded file's reported size - which also keeps
    ``bool`` out.
    """
    return type(value) is int or type(value) is float


def _is_valid_deadline(value: object) -> bool:
    """Whether ``value`` sits in the deadline domain (``None`` is decided by the caller).

    Exact built-in numbers only (:func:`_is_builtin_number`), finite and
    positive.
    """
    if not _is_builtin_number(value):
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        # ``isfinite`` overflows converting a huge int, which is therefore not
        # classifiable as a positive number of seconds: the domain check answers
        # False and the typed rejection fires at the caller.
        return False


#: The largest value any bound may hold: the signed 64-bit maximum. Every
#: collection bound is handed to the database as ``LIMIT`` / ``OFFSET``, where
#: SQLite's integer and PostgreSQL's ``bigint`` are that width, so a wider one
#: would fail inside the driver on the query it was supposed to permit.
MAX_RESOURCE_BOUND = 2**63 - 1


def _require_positive_int(value: object, label: str) -> None:
    """Reject a non-positive-integer bound under whatever name declared it.

    The package's bound-domain rule, stated once for the two spellings of the
    same rule: a ``ResourcePolicy`` field validated at construction and a
    field-declared collection bound validated at its factory line.

    The type test is EXACT, which is what rejects ``True``
    (``isinstance(True, int)`` is ``True``, and a bound of ``True`` would
    silently become ``1``).

    The domain is bounded ABOVE as well, at :data:`MAX_RESOURCE_BOUND`, because
    a bound is only as configurable as the query and the rejection it has to
    survive.
    """
    if type(value) is not int or value < 1:
        raise ConfigurationError(
            f"{label} must be a positive integer; got {introspection.describe(value)}.",
        )
    if value > MAX_RESOURCE_BOUND:
        raise ConfigurationError(
            f"{label} must be at most {MAX_RESOURCE_BOUND}, the largest value a bound can "
            f"carry into a database query and into the rejection it drives.",
        )


@dataclass(frozen=True)
class ResourcePolicy:
    """The immutable per-request resource budget.

    Constructed once (``resolve_resource_policy``) and read many times. Every
    field is a positive ``int`` except ``execution_deadline_seconds``, which is
    ``None`` (no deadline) or a positive number of seconds.

    The document bounds:

    ``max_document_tokens``
        Lexical tokens in the raw document, counted before it is parsed. The
        first bound a request meets, and the only one that can protect
        graphql-core's own recursive parser.
    ``max_depth``
        Maximum structural nesting - ``{``, ``(``, ``[`` - again counted before
        the parse. Input-object and argument nesting therefore count toward
        depth alongside selection-set nesting; the bound is deliberately
        structural rather than selection-only because a bound applied after the
        parse cannot stop the parse from recursing.
    ``max_name_bytes``
        Bytes in the longest name in the raw document - a field, argument,
        variable, type, fragment or directive name - again measured before the
        parse. A name is ASCII by the GraphQL grammar, so its length is its byte
        count. Validation copies a name into the message of every error it
        reports about it, and one undefined variable inside a fragment is
        reported once for every operation that spreads the fragment, so an
        unmeasured name is copied into the response up to a hundred times, the
        error count at which graphql-core's validation stops. No value bound
        sees a name: it is never a value.
    ``max_selections``
        Field selections after fragment expansion, summed across the operation.
        A fragment spread is charged wherever it is spread, so spreading one
        fragment ten times costs ten times. The fragment spreads and inline
        fragments the expansion enters are counted against the same ceiling on
        a count of their own, so a fragment that selects no field is not free.
    ``max_aliases``
        Aliased field selections after fragment expansion. The same expensive
        field under many aliases is charged once per alias.
    ``max_collection_cost``
        The multiplicative row cost of the document: every collection selection
        contributes the product of its own page bound and those of its
        ancestors. This is the bound that sees "100 categories x 100 items each",
        and it is the only bound that grows with NESTING rather than with any one
        collection. It is a SHAPE bound, not a row-count promise: the rows a
        request can actually return are bounded per collection by
        ``max_page_size`` / ``max_list_rows``, and this bound exists to stop the
        product of those from compounding without limit down a deep document. Its
        default is correspondingly generous - a legitimate four-level document
        whose pages are all left unspecified already charges 10**8 - because a
        bound that rejects ordinary documents gets raised to infinity by the
        first deployment that meets it.

    The collection bounds fields enforce at resolve time:

    ``max_page_size``
        Ceiling on a connection's effective ``relay_max_results``.
    ``max_list_rows``
        Ceiling on the returned rows and accepted skip (``offset``) for a
        raw (non-Relay) list field. This is an accepted-coordinate and
        returned-row ceiling, not a guarantee on total physical database
        rows scanned.

    The value bounds, charged over the input as the request spelled it before
    any id is decoded and before any queryset is built:

    ``max_input_nodes``
        Every scalar, list, and object node in the request's argument values.
    ``max_container_width``
        The widest single list or input object, an input object counting every
        field it spells, a repeated field name included.
    ``max_value_depth``
        The deepest chain of nested lists / input objects in one argument value.
        ``max_depth`` bounds nesting spelled out in the document TEXT; a value
        arriving through a variable never passes that scan, so a 10,000-deep
        list-of-list-of-... payload is bounded here or nowhere. It is what stops
        a value the walker must traverse from being arbitrarily deep even while
        each level stays narrow and the node total stays small.
    ``max_membership_items``
        Items in one membership list (an ``in`` lookup and its relatives).
    ``max_node_ids``
        Ids in one Relay node-refetch list.
    ``max_relation_ids_per_mutation`` / ``max_relation_ids_total``
        Relation ids in one mutation field, and across the whole request.
    ``max_nested_rows``
        Rows in one nested input-object list (a nested serializer / formset
        payload).
    ``max_upload_count`` / ``max_upload_file_bytes`` / ``max_upload_total_bytes``
        Files in the request, bytes in the largest file, and bytes in all of
        them. The transport body cap (``MAX_REQUEST_BODY_BYTES``) does not cover
        these: a multipart body is deliberately never materialized there.
    ``max_scalar_bytes``
        UTF-8 bytes in one scalar value, for the parsers and validators whose
        cost is superlinear in their input length.

    ``execution_deadline_seconds``
        Optional wall-clock budget for the operation. Cooperative: every seam
        that is about to hand work to the database calls ``check_deadline``
        first - ``bounded_rows`` (both raw-list spellings, and the generated
        many-side relation resolver), the generated forward FK / forward
        OneToOne and reverse OneToOne relation resolvers
        (``types/resolvers.py::_make_relation_resolver``) on every call, loaded
        or not, ``connection.py::DjangoConnection.resolve_connection`` (the head
        every connection shape passes through), the Relay refetch fields
        (``relay.py::DjangoNodeField`` / ``DjangoNodesField``) and the
        ``resolve_nodes`` default installed on every Relay ``DjangoType``
        (``types/relay.py::_resolve_nodes_default``), which Strawberry's own
        ``relay.node()`` field and a consumer's ``GlobalID.resolve_node`` reach
        directly (a single id through Strawberry's ``Node.resolve_node``), the
        session-auth fields ``login`` / ``logout`` / ``me``
        (``auth/mutations.py::_make_auth_field``) before the request is
        resolved, a user authenticated or a session touched, and the write
        pipelines
        (``mutations/resolvers.py::run_write_pipeline_sync``, which ``register``
        rides too) before their own transaction opens. It is not a preemptive
        timeout and does not claim to be one - nothing in-process can interrupt
        a query already handed to the database driver, so what the deadline buys
        is that the request starts no MORE work.

        Outside that list by audit: the generated file resolver
        (``types/resolvers.py::_make_file_resolver``), which reads a column the
        row already loaded; the storage I/O its subfields may do is not database
        work. Strawberry's ``Node.resolve_id``, which every Relay ``DjangoType``
        resolves its id through, likewise reads the id column the row already
        loaded; a consumer ``.only()`` that defers that column is
        application configuration. The completion-spanning transaction
        ``schema.py::DjangoMutationExecutionContext`` enters around a generated
        mutation field before its resolver runs: it reads, locks and writes no
        row, the pipeline's check is the first statement inside it, and a
        rejection rolls it back. Application code - hand-written root fields,
        resolver overrides, and the ``get_queryset`` visibility hooks and
        consumer ``FilterSet`` / ``OrderSet`` classes the field pipelines run (a
        connection field's resolver pipeline, ``DjangoListField`` and the
        many-side relation re-check run them ahead of their check) - is trusted
        code (``GOAL.md`` "Trust boundary"): a query it issues itself is inside
        the deadline only where it calls ``check_deadline``, or ``bounded_rows``
        / ``bounded_rows_async``, itself.
    """

    max_document_tokens: int = 4_000
    max_depth: int = 20
    max_name_bytes: int = 1_024
    max_selections: int = 500
    max_aliases: int = 100
    max_collection_cost: int = 1_000_000_000
    max_page_size: int = 100
    max_list_rows: int = 100
    max_input_nodes: int = 5_000
    max_container_width: int = 1_000
    max_value_depth: int = 20
    max_membership_items: int = 500
    max_node_ids: int = 200
    max_relation_ids_per_mutation: int = 200
    max_relation_ids_total: int = 1_000
    max_nested_rows: int = 200
    max_upload_count: int = 10
    max_upload_file_bytes: int = 10 * 1024 * 1024
    max_upload_total_bytes: int = 25 * 1024 * 1024
    max_scalar_bytes: int = 65_536
    execution_deadline_seconds: float | None = None

    def __post_init__(self) -> None:
        """Validate every bound at construction, so an invalid policy cannot exist.

        Validation lives in ``__post_init__`` rather than in the settings reader
        because a policy built directly (``DjangoSchema(resource_policy=...)``,
        or a ``narrowed`` copy) must be validated on exactly the same terms as
        one built from settings - one gate, not two that can drift.
        """
        for field in fields(self):
            value = read_attr(self, field.name)
            if field.name == "execution_deadline_seconds":
                if value is None or _is_valid_deadline(value):
                    continue
                raise ConfigurationError(
                    "ResourcePolicy.execution_deadline_seconds must be None or a "
                    f"positive number of seconds; got {introspection.describe(value)}.",
                )
            _require_positive_int(value, f"ResourcePolicy.{field.name}")

    def check(
        self,
        bound: str,
        charged: int,
        detail: str,
    ) -> None:
        """Raise ``ResourceLimitExceeded`` when ``charged`` exceeds this policy's ``bound``."""
        limit = require_instance(read_attr(self, bound), int)
        if charged > limit:
            raise ResourceLimitExceeded(bound, limit, charged, detail)

    def narrowed(self, **overrides: object) -> ResourcePolicy:
        """Return a copy with ``overrides`` applied, rejecting any that widen a bound.

        The narrowing contract in one place: a caller that holds a policy may
        tighten it freely and may never loosen it. Used by any surface that
        derives a stricter budget from the request's own - the schema policy
        stays the ceiling.

        ``execution_deadline_seconds`` narrows from ``None`` (no deadline) to any
        positive value, and from a value only downward; widening it back to
        ``None`` is a widening like any other.
        """
        known = {field.name for field in fields(self)}
        for name in overrides:
            if name not in known:
                raise ConfigurationError(
                    f"ResourcePolicy has no bound named {name!r}.",
                )
        candidate = replace(self, **overrides)
        for name in overrides:
            current = read_attr(self, name)
            value = read_attr(candidate, name)
            # Both policies passed ``__post_init__``, so each bound is an exact number or,
            # for the deadline alone, ``None`` (no deadline): dropping one widens it.
            if _is_builtin_number(value) and _is_builtin_number(current):
                widens = value > current
            else:
                widens = value is None and current is not None
            if widens:
                raise ConfigurationError(
                    f"ResourcePolicy.{name} may only be narrowed: the request policy "
                    f"allows {current!r} and the override asks for {value!r}. Widen the "
                    "schema-construction policy instead.",
                )
        return candidate


#: The package's fail-closed baseline: what a deployment gets by configuring
#: nothing, the miss path of :func:`policy_from_info` and the resource extension's
#: answer for a schema that carries no policy.
DEFAULT_RESOURCE_POLICY = ResourcePolicy()


def resolve_resource_policy(
    explicit: ResourcePolicy | Mapping[str, object] | None,
) -> ResourcePolicy:
    """Normalize the deployment's policy once, at schema construction.

    Precedence, highest first: the ``DjangoSchema(resource_policy=...)``
    argument, the ``DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]`` mapping, and
    the package defaults. A ``ResourcePolicy`` instance from either override slot
    is used as it is, having validated itself at construction; a mapping from
    either source is applied over the package defaults so a deployment overrides
    only the bounds it cares about.

    Both override sources are *trusted declarations* and may therefore widen a
    package default - that is the distinction the narrowing rule draws between a
    deployment's deliberate choice and a per-field value.

    The normalization contract itself is the shared
    ``utils/policies.py::resolve_policy``, stated once alongside
    ``error_policy.py::resolve_error_policy``, which resolves by the same
    ladder.
    """
    return resolve_policy(
        explicit,
        policy_cls=ResourcePolicy,
        default=DEFAULT_RESOURCE_POLICY,
        read_setting=resource_policy_setting,
        display_name="resource policy",
        unit="bound",
    )


class _AdmissionVerdict:
    """Whether the admission stage rejected this operation, once it has decided.

    The verdict has to be the package's own, because the shape a rejection
    reaches the client in cannot also be the record of it: a rejection is
    published as ``ExecutionContext.pre_execution_errors``, and that field is an
    ordinary mutable slot every validation extension writes - Strawberry's own
    ``ValidationCache`` assigns its cached result over whatever is there. An
    operation whose rejection was overwritten is still a rejected operation, and
    this is what says so.
    """

    __slots__: tuple[str, ...] = ("rejection",)

    def __init__(self) -> None:
        self.rejection: ResourceLimitExceeded | None = None


@dataclass(frozen=True)
class _RequestBudget:
    """One operation's authoritative budget: its policy, its deadline, its verdict.

    The policy and the absolute deadline are established once, at
    ``on_operation`` entry, and travel together so that no seam can read a
    deadline derived from a policy other than the one it is about to enforce.
    The verdict is decided later, by the admission stage, and travels with them
    so that every stage after it reads one answer for the operation.
    """

    policy: ResourcePolicy
    deadline: float | None
    admission: _AdmissionVerdict


#: The budget in force for the CURRENT operation, or ``None`` when nothing armed
#: one here.
#:
#: The published ``DST_RESOURCE_*`` keys cannot be the authority, because they
#: live on the CONSUMER's ``info.context`` and every resolver in the request can
#: write it. Replacing ``DST_RESOURCE_DEADLINE`` with a future scalar disarms
#: ``check_deadline``; replacing ``DST_RESOURCE_POLICY`` with a wider
#: ``ResourcePolicy`` widens ``max_list_rows`` - both the returned-row bound and
#: the accepted ``offset`` ceiling ``list_field.py`` derives from it - and
#: ``max_page_size``, for the rest of the operation and without passing
#: ``narrowed``. Neither needs hostile intent: an application context key or a
#: middleware that reuses a generic string name collides just as effectively.
#:
#: A ``ContextVar`` is not reachable by writing the request context, is scoped
#: per task under asyncio and per thread otherwise, and propagates across
#: ``sync_to_async`` / ``async_to_sync``, so it is armed wherever the package's
#: own bound and deadline seams run. The ``ContextVar``-over-stash idiom is the
#: optimizer's (``optimizer/_context.py``'s execution frame), adopted for the
#: same reason: a per-execution answer a context stash cannot be trusted to
#: give.
#:
#: The published keys keep the shape spec-047 specifies, as a mirror a
#: consumer can read; they are also the fallback wherever no budget is armed (a
#: plain ``strawberry.Schema`` with no extension, whose consumer may publish a
#: policy under the key, or a task the operation's binding does not reach),
#: which is a context no resolver of this package's is running inside.
_active_budget: ContextVar[_RequestBudget | None] = ContextVar(
    "django_strawberry_framework_resource_budget",
    default=None,
)


class _BudgetScope:
    """One armed budget's policy and budget, the token restoring the enclosing one, and its owner.

    The token is what gives THIS context back whatever an enclosing operation
    had armed, and only this context: a task that closes a streamed operation
    from elsewhere has nothing of its own to restore.

    ``adopted`` records that something else took the token over. A streamed
    operation arms its budget inside its first frame, and the resume driving
    that frame takes the binding back when the frame is handed over - so the
    binding ends there, while the budget stays armed for the frames still to
    come. Once that has happened this scope no longer has a binding of its own
    to end, and ending it again would be a used token rather than a restore.

    ``policy`` is the policy the budget holds, kept here so
    the arming caller charges the operation's own policy without a second read
    of the variable it has just set.

    ``__slots__`` and not a ``NamedTuple``: ownership is settled after the scope
    is built, by whoever adopts it.
    """

    __slots__: tuple[str, ...] = (
        "adopted",
        "budget",
        "policy",
        "token",
    )

    def __init__(
        self,
        policy: ResourcePolicy,
        budget: _RequestBudget,
        token: Token[_RequestBudget | None],
    ) -> None:
        self.policy: ResourcePolicy = policy
        self.budget: _RequestBudget = budget
        self.token: Token[_RequestBudget | None] = token
        self.adopted: bool = False


def _armed_budget() -> _RequestBudget | None:
    """Return the budget armed here, or ``None``.

    The one read every seam in this module goes through.
    """
    return _active_budget.get()


def _absolute_deadline(policy: ResourcePolicy) -> float | None:
    """Return the monotonic instant ``policy``'s budget ends, or ``None`` for no deadline.

    ``execution_deadline_seconds`` is an exact built-in by construction
    (:func:`_is_valid_deadline`), so this addition is plain ``float``
    arithmetic and cannot be redirected through a consumer's ``__radd__``.
    """
    seconds = policy.execution_deadline_seconds
    return None if seconds is None else time.monotonic() + seconds


def _publish_budget_mirror(
    context: object,
    policy: ResourcePolicy,
    deadline: float | None,
) -> None:
    """Write the consumer-readable mirror of a budget onto the request context."""
    stash_on_context(context, DST_RESOURCE_POLICY, policy)
    stash_on_context(context, DST_RESOURCE_DEADLINE, deadline)


def begin_resource_budget(context: object, policy: ResourcePolicy) -> _BudgetScope:
    """Arm ``policy`` as this operation's budget and publish it; returns its scope.

    One derived absolute deadline reaches both the armed budget and the
    published mirror, so the authority and the mirror cannot disagree about when
    the operation's budget ends. :func:`end_resource_budget` closes the scope,
    restoring whatever budget an enclosing operation had armed.
    """
    deadline = _absolute_deadline(policy)
    _publish_budget_mirror(context, policy, deadline)
    budget = _RequestBudget(policy, deadline, _AdmissionVerdict())
    return _BudgetScope(policy, budget, _active_budget.set(budget))


def budget_resume_binding(
    scope: _BudgetScope,
) -> tuple[
    ContextVar[_RequestBudget | None],
    _RequestBudget,
    Token[_RequestBudget | None],
]:
    """Return what a streamed operation has to bind again on resume, and what armed it here.

    An operation's budget is armed once, in the task that started it, and a
    streamed operation's later frames run in whatever task drives them. The
    runner re-binds the variable and the budget around every resumption
    (``extensions/operation_state.py::OperationState.rebind_on_resume``), so a
    frame produced in a second task is bounded by the policy the request was
    admitted under rather than by the fallback.

    The token goes with them because the arming happens INSIDE the first frame:
    the resume driving that frame has no binding of its own to take back, so
    without this the budget would stay armed in the driving task after the frame
    was handed over - an unrelated call in that task would then be answered by a
    paused operation's ceiling rather than by its own context. The token is one
    task's binding of the budget; the resume ends that binding without touching
    the budget.
    """
    return _active_budget, scope.budget, scope.token


def adopt_budget_binding(scope: _BudgetScope) -> None:
    """Record that a resume took this scope's binding over.

    Called only when a registrar actually accepted it, so an ordinary operation
    - and a plain ``strawberry.Schema``, which has no runner at all - still ends
    its own binding in :func:`end_resource_budget`.
    """
    scope.adopted = True


def armed_resource_policy() -> ResourcePolicy | None:
    """Return the policy armed for this operation, or ``None`` when nothing armed one.

    The package's own way of asking "which policy is this operation being
    bounded by", for the seams that run inside an armed scope but hold no
    ``info``: :func:`policy_from_info` answers the same question for a resolver
    and falls back to the published mirror, while a caller of this one wants to
    know whether a budget is armed at all.
    """
    budget = _armed_budget()
    return None if budget is None else budget.policy


def record_admission_rejection(rejection: ResourceLimitExceeded) -> None:
    """Record ``rejection`` as this operation's admission verdict.

    Does nothing when no budget is armed, which is the plain
    ``strawberry.Schema`` case a caller reaches by invoking a hook outside an
    operation scope: there is no operation for a verdict to belong to.
    """
    budget = _armed_budget()
    if budget is not None:
        budget.admission.rejection = rejection


def admission_rejection() -> ResourceLimitExceeded | None:
    """Return the operation's admission rejection, or ``None`` if it was admitted.

    The answer every stage after admission reads, in preference to the published
    error it can be told apart from: publishing is how a rejection reaches the
    client, and what is published is writable by anything else in the extension
    chain.
    """
    budget = _armed_budget()
    return None if budget is None else budget.admission.rejection


def end_resource_budget(scope: _BudgetScope) -> None:
    """Disarm the budget armed by :func:`begin_resource_budget`.

    A cancelled subscription closes the generator
    driving it from a context that is not the one the operation armed in, and a
    token is resettable only where it was created; the copy that context holds
    is discarded with it, so there is nothing to restore - and raising here
    would replace the cancellation with a ``ValueError`` from teardown.

    Only that condition is ignored. ``ValueError`` also answers a token minted
    by another variable, which is this module's bookkeeping gone wrong rather
    than a fact about where teardown ran, so it is re-raised; a reused token is
    ``RuntimeError`` and is not caught at all.

    An adopted scope has nothing left to reset: the resume that took the
    binding over ended it when it handed its frame back
    (:func:`adopt_budget_binding`).
    """
    if scope.adopted:
        return
    try:
        _active_budget.reset(scope.token)
    except ValueError:
        if scope.token.var is not _active_budget:
            raise


def policy_from_info(info: object) -> ResourcePolicy:
    """Return the request's policy, or the package default when none was published.

    The armed budget outranks the published mirror, and is consulted without
    reference to ``info`` at all: a resolver that rewrites ``DST_RESOURCE_POLICY``
    to widen ``max_list_rows`` for the rest of its own operation changes nothing
    that any bound reads. The mirror answers only where no budget is armed:
    ``DjangoSchema`` always installs the extension that arms one, so only a
    schema that never installed it reaches the mirror.

    Fail-closed by construction: the miss path returns the package's own
    baseline (``DEFAULT_RESOURCE_POLICY``), never ``None``. A field consulting
    the policy is therefore always bounded, including under a plain
    ``strawberry.Schema`` that never installed the extension, and never needs a
    ``None`` branch of its own.
    """
    budget = _armed_budget()
    if budget is not None:
        return budget.policy
    value = get_context_value(getattr(info, "context", None), DST_RESOURCE_POLICY)
    return value if isinstance(value, ResourcePolicy) else DEFAULT_RESOURCE_POLICY


def check_deadline(info: object) -> None:
    """Raise if the operation's optional wall-clock deadline has already passed.

    Cooperative and called first at every seam that is about to hand work to the
    database (the seams are enumerated at ``ResourcePolicy``'s
    ``execution_deadline_seconds`` entry). The armed
    budget is the ceiling: the earliest of it and an exact built-in number a
    resolver stashed under ``DST_RESOURCE_DEADLINE`` decides, so a resolver may
    SHORTEN its own request and cannot lengthen or clear it. Where no budget is
    armed, the published mirror is all there is and answers alone. Anything
    under the key that is not an exact built-in number is not a deadline.

    The rejection reports the CONFIGURED budget, never the clock: ``limit`` is
    the policy's own ``execution_deadline_seconds`` and ``charged`` is one second
    past it (the "exceeded an unmeasurable-in-integers budget" spelling the
    admission walk already uses for an upload whose size cannot be read). The
    monotonic
    deadline and the overrun are process-internal timings a client can neither
    act on nor verify, and a wire field named ``limit`` carrying a monotonic
    timestamp is worse than useless - it reads as a bound the deployment never
    configured.
    """
    budget = _armed_budget()
    mirror = get_context_value(getattr(info, "context", None), DST_RESOURCE_DEADLINE)
    armed = None if budget is None else budget.deadline
    deadlines = [value for value in (armed, mirror) if _is_builtin_number(value)]
    if not deadlines or time.monotonic() < min(deadlines):
        return
    source = budget.policy if budget is not None else policy_from_info(info)
    configured = source.execution_deadline_seconds
    # A stashed deadline whose policy carries none is only reachable by writing
    # the key by hand: reject (the deadline HAS passed) and say the budget is
    # unknown rather than inventing a number for it.
    seconds = math.ceil(configured) if configured is not None else 0
    budget_label = f"{configured} seconds" if configured is not None else "unknown"
    raise ResourceLimitExceeded(
        "execution_deadline_seconds",
        seconds,
        seconds + 1,
        f"the operation exceeded its configured execution deadline ({budget_label}) "
        "before this field reached the database",
    )


def _bounds_by_its_own_slice(
    result: object,
) -> TypeGuard[
    list[object] | tuple[object, ...] | str | bytes | bytearray | QuerySet[Model, object]
]:
    """Whether slicing ``result`` carries the bound: a built-in sequence, or a ``QuerySet``.

    A ``QuerySet`` of any class, a project's own included, is sliced so the bound
    reaches SQL as ``LIMIT`` rather than being counted out of a fully fetched
    table. Everything else is bounded by COUNTING instead (``_windowed_rows``).
    """
    return isinstance(
        result,
        (
            list,
            tuple,
            str,
            bytes,
            bytearray,
        ),
    ) or _is_queryset(result)


def _raw_list_bound(info: object, declared: int | None, *, trusted: bool = False) -> int:
    """Deadline check plus the effective raw-list row bound, spelled once for both colors.

    ``bounded_rows`` and ``bounded_rows_async`` enforce the same seam - the last
    look at the clock before rows are fetched, then the tighter of
    ``max_list_rows`` and the field's own declaration - so neither execution
    color can drift onto a different bound than the other.
    """
    check_deadline(info)
    return effective_bound(policy_from_info(info).max_list_rows, declared, trusted=trusted)


_RowT = TypeVar("_RowT")
_ModelT = TypeVar("_ModelT", bound=Model)


@overload
def _windowed_rows(
    result: None,
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> None: ...
@overload
def _windowed_rows(
    result: QuerySet[_ModelT, _RowT],
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> QuerySet[_ModelT, _RowT] | list[_RowT]: ...
@overload
def _windowed_rows(
    result: Iterable[_RowT],
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> Iterable[_RowT]: ...
@overload
def _windowed_rows(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> object: ...
def _windowed_rows(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> object:
    """Bound a raw list and window it to coordinates the caller has already validated.

    The seam under ``bounded_rows``: the same ceiling, plus the ``offset`` /
    ``requested_limit`` pair a ``DjangoListField`` request carries. ``offset``
    defines the skip (``start``, defaulting to 0) and ``requested_limit`` the
    returned-row window (defaulting to the effective ``limit``); together they
    name the slice ``start:stop`` where ``stop = start + window``. Those bounds
    are an accepted-coordinate ceiling on skipped and returned items, not a
    guarantee on total physical rows scanned by the underlying database query.

    ``[start:stop]`` is reached for a built-in sequence (``list``, ``tuple``,
    ``str``, ``bytes``, ``bytearray``) and for a ``QuerySet``, whose slice is what
    pushes ``LIMIT`` into SQL. Every other shape - a mapping, a bare iterable, a
    relation accessor's sequence proxy - is bounded by COUNTING through
    ``islice`` into a list this package built, and a zero-width window on such a
    shape is the empty list.

    A source that arrives evaluated is windowed from the rows it already holds,
    because ``QuerySet.__getitem__`` reads a populated ``_result_cache`` directly,
    so the window costs no query.

    Package-private because a coordinate pair is a claim this seam cannot check:
    a window wider than the request's own ceiling would silently widen the bound
    ``bounded_rows`` advertises to everyone who imports it.
    ``list_field.py::_normalize_list_arguments`` is the single owner of that
    check - it rejects a non-integer, negative, or over-ceiling value with the
    typed, argument-named error a client can act on, before any of it reaches
    here - so the exported helper stays coordinate-free and unconditionally
    bounded rather than growing a second ceiling with a second error contract.
    """
    limit = _raw_list_bound(info, declared, trusted=trusted)
    if result is None:
        return None
    by_slice = _bounds_by_its_own_slice(result)
    if offset is None and requested_limit is None:
        return result[:limit] if by_slice else list(islice(iter_of(result), limit))

    start = offset if offset is not None else 0
    window = requested_limit if requested_limit is not None else limit
    if window == 0:
        return result[start:start] if by_slice else []
    stop = start + window
    return result[start:stop] if by_slice else list(islice(iter_of(result), start, stop))


@overload
def bounded_rows(
    result: None,
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> None: ...
@overload
def bounded_rows(
    result: QuerySet[_ModelT, _RowT],
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> QuerySet[_ModelT, _RowT] | list[_RowT]: ...
@overload
def bounded_rows(
    result: Iterable[_RowT],
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> Iterable[_RowT]: ...
@overload
def bounded_rows(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> object: ...
def bounded_rows(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> object:
    """Apply the request's raw-list row bound to whatever a collection resolver produced.

    The one place a raw (non-Relay) list is bounded, shared by the root
    ``DjangoListField`` and by the generated many-side relation resolvers, so
    both spellings of "a list of rows with no cursor" carry the same ceiling.
    The bound is the tighter of ``ResourcePolicy.max_list_rows`` and the field's
    own ``declared`` maximum unless the field declared ``trusted=True``. It is an
    accepted-row ceiling on what the response can carry, not a guarantee on total
    physical rows scanned by the underlying database query.

    An unevaluated ``QuerySet`` is bounded by SLICING, so it carries the bound
    into SQL as ``LIMIT`` and is never evaluated unbounded; a value whose rows
    are already fetched when it reaches this call - a materialized sequence, a
    consumer resolver's list return, or the prefetch cache a generated relation
    resolver hands over - is windowed in Python from the rows it holds, which
    cannot un-fetch them but does stop the response from serializing them and
    costs no second query. A queryset a ``DjangoListField`` resolver returns is
    not such a value even when the resolver evaluated it: the visibility seal in
    front of the window drops its result cache, so its window is a query.
    Which operation does the truncating follows from what the value IS: a
    ``list``, ``tuple``, ``str``, ``bytes`` or ``bytearray`` is sliced, and every
    other shape - a mapping, a bare iterable - is counted into a fresh list
    instead. A ``QuerySet`` of a project's own class is sliced too, so it keeps the
    SQL ``LIMIT`` a counted truncation would lose. The slice answers in the
    sliced value's own type, except on a
    queryset whose rows are already fetched: there ``QuerySet.__getitem__``
    answers from the rows it holds, so the window comes back as a ``list``. A
    mapping therefore still comes back as a bounded list of its keys.

    A raw list is the one collection shape Relay pagination does not bound, so
    this is the only thing between a client and the whole table. It is
    unconditional: there is no argument or configuration that turns it off, only
    values that make it larger. Nothing a caller passes here can widen it - the
    client page coordinates a ``DjangoListField`` request carries ride on
    ``_windowed_rows``, below this surface and behind that field's own
    validation.
    """
    return _windowed_rows(result, info, declared, trusted=trusted)


async def _close_async_iterator(iterator: object) -> None:
    """Invoke ``iterator.aclose()`` if present."""
    close = getattr(iterator, "aclose", None)
    if close is not None:
        await close()


async def _cleanup_rejected_async_iterable(iterable: AsyncIterable[object]) -> None:
    """Close an async-only source that is being rejected before it is ever advanced.

    Sits below every caller that can reject such a source: the list field's
    non-queryset and argument rejections, and this module's own pre-iteration
    bound check. An iterator that has not yet produced an item can still own an
    open external resource, so the rejection owes it a close even though no row
    was ever requested.
    """
    await _close_async_iterator(aiter(iterable))


@overload
async def _windowed_rows_async(
    result: None,
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> None: ...
@overload
async def _windowed_rows_async(
    result: QuerySet[_ModelT, _RowT],
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> QuerySet[_ModelT, _RowT] | list[_RowT]: ...
@overload
async def _windowed_rows_async(
    result: Iterable[_RowT] | AsyncIterable[_RowT],
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> Iterable[_RowT]: ...
@overload
async def _windowed_rows_async(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> object: ...
async def _windowed_rows_async(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    offset: int | None = None,
    requested_limit: int | None = None,
    trusted: bool = False,
) -> object:
    """Bound a possibly async-iterable result and window it to validated coordinates.

    The async seam under ``bounded_rows_async``, carrying the same client page
    coordinates ``_windowed_rows`` does and behind the same caller-owned
    validation. For async-only iterables the coordinates define an
    accepted-coordinate and returned-row ceiling rather than a database
    row-scan guarantee: the helper discards exactly ``offset`` items, collects at
    most ``window`` items (where ``window`` is the prevalidated
    ``requested_limit``, defaulting to the effective limit), and closes the
    iterator early without over-requesting subsequent items - the rows it
    returns are collected into a list of its own, so an async source bounds the
    same way a non-sliceable sync one does. Synchronous iterables fall back to
    ``_windowed_rows`` and are bounded there on its terms.
    """
    if not is_async_only_iterable(result):
        return _windowed_rows(
            result,
            info,
            declared,
            offset=offset,
            requested_limit=requested_limit,
            trusted=trusted,
        )
    try:
        limit = _raw_list_bound(info, declared, trusted=trusted)
    except BaseException:
        # The source was handed over before this seam looked at the clock, so a
        # rejection here abandons an iterator the resolver has already built.
        # Nothing has been advanced, but an unadvanced iterator can still hold
        # an open external resource, and no later seam will ever see it again.
        await _cleanup_rejected_async_iterable(result)
        raise
    start = offset if offset is not None else 0
    window = requested_limit if requested_limit is not None else limit

    iterator = aiter(result)
    if window == 0:
        await _close_async_iterator(iterator)
        return []

    rows: list[object] = []
    exhausted = False
    skipped = 0
    try:
        async for item in iterator:
            if skipped < start:
                skipped += 1
                continue
            rows.append(item)
            if len(rows) >= window:
                break
        else:
            exhausted = True
    finally:
        if not exhausted:
            await _close_async_iterator(iterator)
    return rows


@overload
async def bounded_rows_async(
    result: None,
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> None: ...
@overload
async def bounded_rows_async(
    result: QuerySet[_ModelT, _RowT],
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> QuerySet[_ModelT, _RowT] | list[_RowT]: ...
@overload
async def bounded_rows_async(
    result: Iterable[_RowT] | AsyncIterable[_RowT],
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> Iterable[_RowT]: ...
@overload
async def bounded_rows_async(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> object: ...
async def bounded_rows_async(
    result: object,
    info: object,
    declared: int | None = None,
    *,
    trusted: bool = False,
) -> object:
    """Apply a raw-list row bound to a result that may be async-iterable.

    ``graphql-core`` accepts ``AsyncIterable`` list results and materializes
    them during async completion. A synchronous ``bounded_rows`` call cannot
    slice an async generator, however, so an async field must consume only its
    bounded prefix before returning the result to GraphQL. Synchronous
    iterables (including Django ``QuerySet`` objects, which expose both
    protocols) stay on ``bounded_rows`` so lazy querysets retain their SQL
    ``LIMIT`` instead of being materialized through the async iterator.

    When the prefix ends early, or iteration fails, the iterator is closed.

    The deadline and row bound are read here, after the resolver has already
    produced its source, so a rejection at that read abandons an async-only
    source the same way an early prefix end does and owes it the same close.

    Like ``bounded_rows``, this surface carries no client page coordinates:
    ``_windowed_rows_async`` is where a validated ``offset`` / ``limit`` pair
    narrows the window further.
    """
    return await _windowed_rows_async(result, info, declared, trusted=trusted)


def validate_collection_bound(declared: object, *, field: str) -> None:
    """Reject a field-declared collection bound that is not a positive integer.

    Called at the line that constructs the field, so a typo fails where it was
    written rather than on the first request that reaches the resolver -
    the constructor-site posture the field factories' target guards already take.
    """
    _require_positive_int(declared, field)


def validate_trusted_flag(declared: object, *, field: str) -> None:
    """Reject a trusted-declaration opt-in that is not exactly ``True`` or ``False``.

    The opt-in that lets a field-declared maximum outrank the request's own
    ``ResourcePolicy`` is a security decision, so the value that makes it is an
    exact ``bool`` and the check fires at the line that constructs the field -
    a misspelled ``trusted_max_rows="false"`` fails where it was written rather
    than silently widening every request the field serves. ``effective_bound``
    independently admits only ``True``, so a caller that bypasses this
    constructor-site check still cannot widen by accident.
    """
    if type(declared) is not bool:
        raise ConfigurationError(
            f"{field} must be exactly True or False; got {introspection.describe(declared)}.",
        )


def effective_bound(policy_value: int, declared: int | None, *, trusted: bool = False) -> int:
    """Combine a request bound with a field's own declared maximum.

    The narrowing rule at a field: ``None`` means "the field declares nothing,
    the request policy governs"; a declared value narrows to the tighter of the
    two. Only the literal ``True`` widens - the call site is stating that this
    field's maximum is a deliberate declaration that outranks the policy, which
    is exactly the trusted-declaration carve-out and is never the default.

    ``trusted is True``, not ``if trusted:``. This is the one primitive in the
    package whose answer can be WIDER than the request policy, so the condition
    that reaches it admits exactly the one value that means it: a truthy string,
    a non-empty container, or any object whose ``__bool__`` answers ``True``
    narrows like every other non-opt-in caller. The field factories validate the
    flag's type at their own construction line as well
    (:func:`validate_trusted_flag`); the rule is repeated here because this
    primitive must stay safe for an internal caller that has no factory in front
    of it.
    """
    if declared is None:
        return policy_value
    if trusted is True:
        return declared
    return min(policy_value, declared)
