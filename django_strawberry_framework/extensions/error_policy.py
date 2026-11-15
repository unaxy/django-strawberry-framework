"""``DjangoErrorPolicyExtension`` - the response-side enforcement of ``ErrorPolicy``.

Spec: ``docs/SPECS/spec-048-secure_output_defaults-0_0_14.md``.

``error_policy.py`` owns the policy object; this module is the one place that
applies it. ``DjangoSchema`` installs the extension automatically, so a schema
built through this package does not leak an unexpected exception's message by
default.

One pass over a completed result: every error on it is classified and, when it is
unexpected, replaced by a fresh ``GraphQLError`` carrying the policy's stable
message and a correlation identifier, while the original exception is logged
server-side under that same identifier.

**There are three seams, because a response is not always one result and is not
always a result this extension can still reach.** A query or mutation answered
through ``schema.execute`` normally produces exactly one already-torn-down result,
and this extension's ``on_operation`` teardown masks its current errors. A
STREAMED operation is not: a subscription delivers one ``ExecutionResult`` PER EVENT
through the result source the transport iterates, and a query or mutation run over a
streaming transport has its single result yielded from inside the operation
lifecycle - either way that teardown runs only when the operation ENDS, so the
errors would already be on the wire by the time it ran. The per-result seam is
therefore the transport's own result source
(``consumers.py::_stop_aware_results``), which masks each yielded value through
``mask_execution_result`` below, under the shared ``is_maskable_result`` shape gate.

The third is the one no extension can be: an exception escaping any HOOK - this
extension's own teardown included - unwinds the whole operation lifecycle and is
converted into a result by upstream AFTER every teardown has run, so the result
carrying it was never assigned to the execution context this teardown reads and
no extension exists at the moment it is built. That result is the value
``schema.execute`` / ``schema.execute_sync`` RETURN, so the seam is the schema's
own return (``schema.py::DjangoSchema._masked_return``), applying this module's
same masking under the same gates. It is idempotent with the teardown by
construction: a result the teardown already masked carries errors whose
``original_error`` is ``None``, which the structural classifier reads as
deliberate and leaves alone, so nothing is masked or logged twice.

One masking implementation, three places it is applied, and none of them
re-states the classification or the replacement. The three sites become one
only if the engine offers a single hook that sees every yielded frame and
every result built after teardown; until then a check moved to any one of
them observes different state than the other two. A plain ``strawberry.Schema``
that a consumer assembled themselves with ``DjangoErrorPolicyExtension`` in its
extensions list has no schema seam, so on that schema a hook failure is the one
case the masking does not cover. Teardown snapshots the error list on both schema
shapes; late resolver errors cannot append into the published result during result
collection. Managed schemas also snapshot at final return to cover hook failures.

``mask_execution_result`` RETURNS a masked value rather than editing the result
it was handed, which is what lets the per-event seam leave the engine's own
result object untouched: the extensions that read ``GraphQLError.original_error``
(``debug.py::DjangoDebugExtension`` above all) still see the originals on the
object the engine assigned to ``execution_context.result``, exactly as the LIFO
teardown ordering promises them.

**Install position is load-bearing, and it is the FRONT of the extension
chain.** Strawberry's ``on_operation`` teardowns unwind LIFO, so the
first-listed extension tears down LAST. Masking must happen after every
extension that reads ``original_error`` has had its turn - in particular
``debug.py::DjangoDebugExtension``, which is documented to run after any
masking extension - so ``schema.py::_admitted_chain`` lists the policy ahead
of every consumer extension. The resource policy goes behind them for the
mirror-image reason: it gates BEFORE execution, so it sets up last, with its
budget armed around every consumer hook; the error policy rewrites AFTER
execution, so it finishes last.

Sync and async execution share one implementation. The teardown is a plain
synchronous generator - the engine enters sync generator hooks on the async
path too - so there is exactly one masking code path and no color-specific
branch to keep in parity.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, TypeVar

from graphql import GraphQLError
from graphql.execution import ExecutionResult as GraphQLExecutionResult
from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult
from typing_extensions import override

from django_strawberry_framework import logger
from django_strawberry_framework.conf import django_setting
from django_strawberry_framework.error_policy import (
    _PACKAGE_ERROR_POLICY,
    ErrorPolicy,
    new_correlation_id,
)
from django_strawberry_framework.utils import truth

from .operation_state import OperationState, _OperationBoundExtension

if TYPE_CHECKING:
    from collections.abc import Iterator

    from typing_extensions import TypeIs

#: Either result shape ``is_maskable_result`` admits; masking hands back the same shape.
_MaskableResultT = TypeVar(
    "_MaskableResultT",
    bound="GraphQLExecutionResult | StrawberryExecutionResult",
)

__all__ = [
    "DjangoErrorPolicyExtension",
    "is_maskable_result",
    "mask_execution_result",
    "masking_is_active",
]


def _is_unexpected(error: GraphQLError) -> bool:
    """Whether ``error`` reached the wire by accident (spec-048 Decision 8).

    Three cases, in the order graphql-core produces them:

    - ``original_error is None`` on a ``GraphQLError`` - a parse, syntax, or
      validation error, or an error graphql-core constructed itself with
      nothing behind it. Nothing raised it; its message describes the client's
      own request. Not masked.
    - ``original_error`` IS a ``GraphQLError`` - something raised a GraphQL error
      deliberately. Every framework rejection does this (the invalid-GlobalID
      boundary, the resource bounds, the connection / keyset / filter argument
      rejections, and the mutation pipeline's authorization denial), and a
      consumer raising ``GraphQLError`` is making the same statement about their
      own message. Not masked.
    - anything else - a plain Python exception that escaped a resolver or hook.
      Masked.

    **The rule reads through graphql-core's ``located_error`` wrapping, which is
    why it covers the completion phase as well as the resolve phase.** Every
    exception graphql-core surfaces from a field - whether it escaped the
    resolver, escaped an awaited value, or was raised while COMPLETING the
    resolved value (non-nullable ``null`` propagation, list-item completion, a
    custom scalar's ``serialize``) - arrives as a ``GraphQLError`` whose
    ``original_error`` IS that exception. So a resolver failure surfaced through
    value completion is still an unexpected plain exception here and is still
    masked; graphql-core's own completion ``TypeError`` is masked for the same
    structural reason, which is the fail-closed direction. Only a completion
    error whose ``original_error`` a consumer deliberately typed as a
    ``GraphQLError`` travels unchanged.

    The rule is structural rather than an allowlist of ``extensions.code``
    values on purpose: an allowlist must be extended by every future rejection
    site and fails OPEN when it is not, while this fails CLOSED for every new
    exception type the package or a consumer ever raises.
    """
    original = error.original_error
    if original is None:
        return False
    return not isinstance(original, GraphQLError)


def _masked(error: GraphQLError, policy: ErrorPolicy) -> GraphQLError:
    """Return the client-safe replacement for one unexpected ``error``.

    The location information - ``nodes``, ``source``, ``positions``, and ``path``
    - is deliberately RETAINED. It names which field of the client's own document
    failed, which the client already knows and which a client needs in order to
    report the failure usefully; nothing about it comes from the server's
    internals. What is dropped is the message and ``original_error``, which are
    the parts written by whatever raised.
    """
    correlation_id = new_correlation_id()
    logger.error(
        "Unhandled exception during GraphQL execution; the client received the "
        "policy message and correlation id %s.",
        correlation_id,
        exc_info=error.original_error,
    )
    return GraphQLError(
        message=policy.message,
        nodes=error.nodes,
        source=error.source,
        positions=error.positions,
        path=error.path,
        original_error=None,
        extensions={policy.correlation_extension_key: correlation_id},
    )


def masking_is_active(policy: ErrorPolicy) -> bool:
    """Whether ``policy`` masks anything for the operation being answered now.

    Masking is off only under a ``DEBUG`` that is exactly ``True``. ``enabled``
    is an exact ``bool`` field of an exact ``ErrorPolicy`` and is read as stored.
    """
    return policy.enabled and django_setting("DEBUG") is not True


def is_maskable_result(
    value: object,
) -> TypeIs[GraphQLExecutionResult | StrawberryExecutionResult]:
    """Whether ``value`` is the execution-result shape this policy can rewrite.

    Both seams ask this one question, so neither can drift on the shape gate. The
    two admitted shapes are the only ones carrying a flat ``errors`` list this
    policy knows how to classify and replace; a strawberry ``PreExecutionError`` is
    itself an ``ExecutionResult`` and is admitted, contributing nothing to mask
    because its errors carry no ``original_error``.

    What the gate excludes is what makes it necessary rather than decorative. The
    operation-teardown seam meets a sync parse or validation early-return, which
    has nothing masked to begin with. The per-event seam meets a raw graphql-core
    incremental-delivery frame (``@defer`` / ``@stream``), whose errors are nested
    inside incremental payloads and which carries no flat ``errors`` to read.
    Excluding it by shape leaves the transport's own unrenderable-frame rejection
    intact, which discloses nothing: the frame never reaches the wire at all.
    """
    return isinstance(value, (GraphQLExecutionResult, StrawberryExecutionResult))


def schema_error_policy(schema: object) -> ErrorPolicy:
    """Return the resolved policy carried by ``schema``, or the package default.

    A plain ``strawberry.Schema`` a consumer wired the extension into by hand has
    no ``error_policy`` attribute; that is a supported standalone use, so it falls
    back rather than raising. The exact-type gate is the same fail-closed
    reasoning applied to a WRONG attribute: something that is not exactly an
    ``ErrorPolicy`` cannot be asked whether masking is enabled - a subclass could
    answer ``enabled`` / ``message`` with code of its own - and treating its
    truthiness as an answer would let an unrelated ``schema.error_policy``
    silently disable masking. Either way the fallback is the MASKING one -
    the package's own policy - because an extension whose whole job is to mask
    must not become a no-op because it could not find its configuration.
    ``DjangoSchema`` always supplies a valid one, validated at construction.
    """
    policy = getattr(schema, "error_policy", None)
    return policy if truth.is_exact(policy, ErrorPolicy) else _PACKAGE_ERROR_POLICY


def mask_execution_result(
    result: _MaskableResultT,
    policy: ErrorPolicy,
    *,
    snapshot: bool = False,
) -> _MaskableResultT:
    """Return the client-safe value for one completed or per-event ``result``.

    By default ``result`` itself is returned whenever nothing needed masking,
    so the caller can test identity to learn whether the policy did anything.
    ``snapshot=True`` instead owns a fresh list even when every entry is deliberate
    or the list is empty; error identity and order remain unchanged. A SHALLOW
    COPY carries the rewritten error list: the object the engine assigned to
    ``execution_context.result`` keeps its originals, so an extension reading
    ``original_error`` after this ran still reads what was raised.

    Order and arity are preserved - every error keeps its position whether it was
    masked or not, so a client matching errors to its document by index is
    unaffected.
    """
    errors = result.errors
    if errors is None:
        return result
    replacements = [_masked(error, policy) if _is_unexpected(error) else error for error in errors]
    if not snapshot and all(new is old for new, old in zip(replacements, errors, strict=True)):
        return result
    masked = copy.copy(result)
    masked.errors = replacements
    return masked


class DjangoErrorPolicyExtension(_OperationBoundExtension[OperationState]):
    """Replace unexpected exception messages with a stable message plus a correlation id.

    ``DjangoSchema`` installs one of these on every operation and is the only
    thing that can: the policy object is resolved once at schema construction
    and read from ``schema.error_policy``, and an entry that resolves to one of
    these on a request already running raises ``ConfigurationError``. A
    ``DjangoSchema(extensions=[...])`` entry that IS this class, or an exact
    instance of it, is read as a declaration of the schema's own masker and
    does not travel into the chain; a subclass is refused at construction, and a
    factory resolving to either raises ``ConfigurationError`` when the operation
    resolves it.

    **Which result is masked is per-operation state, not an attribute.** The
    teardown reads the completed result off the operation's engine context, and
    that context is bound by the package runner for the operation being answered
    (``extensions/operation_state.py``). Read from an ordinary attribute on a
    shared instance it would be whichever operation assigned last - a nested
    ``info.schema.execute_sync(...)`` is enough - and the teardown would then
    mask the inner operation's result while the outer one's unexpected exception
    reached the client with its own message on it. On a plain
    ``strawberry.Schema`` the supported entry is therefore the class or a fresh
    factory, never a shared instance.

    Active only when the policy is enabled AND the schema is not in debug
    execution. Under ``settings.DEBUG`` the extension is a pass-through: the
    unmasked message is the reason a developer set the setting, and a
    development schema has no untrusted reader to protect the message from.
    """

    def _policy(self) -> ErrorPolicy:
        """Return the schema's resolved policy, or the package default."""
        schema = getattr(getattr(self, "execution_context", None), "schema", None)
        return schema_error_policy(schema)

    def _process_result(
        self,
        result: GraphQLExecutionResult | StrawberryExecutionResult,
        policy: ErrorPolicy,
    ) -> None:
        """Adopt the masked result onto the value the transport will render.

        The masking itself belongs to ``mask_execution_result``, which the
        subscription seam shares; this method is only the assignment.
        """
        masked = mask_execution_result(result, policy, snapshot=True)
        if masked is not result:
            result.errors = masked.errors

    @override
    def on_operation(self) -> Iterator[None]:
        """Apply the policy to the completed result, once, at teardown.

        The completed result is the whole response for a query or a mutation
        upstream ran through ``schema.execute`` and finished normally. For
        anything the transport streamed - every subscription, and a query or
        mutation over a streaming transport - it is only the operation's end,
        because each yielded result was already masked at the transport's result
        source. And when an exception escaped a HOOK there is no completed result
        here at all: upstream builds one out of that exception after every
        teardown has unwound, so the response is masked where it is returned
        instead (see the module docstring for all three seams).

        The shape gate is ``is_maskable_result``, which carries what it admits and
        what it excludes.
        """
        yield
        policy = self._policy()
        if not masking_is_active(policy):
            return
        result = getattr(getattr(self, "execution_context", None), "result", None)
        if is_maskable_result(result):
            self._process_result(result, policy)
