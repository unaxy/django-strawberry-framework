"""``ErrorPolicy`` construction, precedence, and install position.

The package tier of the production error policy: everything a live ``/graphql/``
request cannot reach. What a client actually reads out of a masked response - the
category matrix, the correlation id on the wire and in the log, the retained
``path``, sync/async parity, both opt-outs, a non-boolean ``DEBUG`` value, and a
resolver write to ``info.schema.error_policy`` - is pinned over real HTTP in
``examples/fakeshop/test_query/test_error_policy_api.py``, because that is where
it matters. What is left here is the surface a request cannot express:

- the dataclass's per-field validation, which fails at CONSTRUCTION and therefore
  never reaches a request at all;
- the precedence ladder (constructor argument > setting > package default) and
  the settings-shape rejections;
- the correlation id's format and its uniqueness, read directly rather than
  inferred from two sampled responses;
- the extension's INSTALL POSITION, which is a property of the extensions list
  rather than of any response, and the consumer-supplied suppression that keeps
  a consumer's own entry exactly where they put it (a declared entry beside a
  debug factory leaving debug's exception capture intact is live);
- the schema attribute answering a duplicate of the stored policy (identity is
  not on the wire; the resolver-write consequence is live);
- the absent ``error_policy`` attribute behind the standalone fallback a plain
  ``strawberry.Schema`` takes (the masked response it serves is live), the
  exact-type-gated fallback a schema carrying a WRONG ``error_policy`` attribute
  takes (the hook failure a plain schema leaves unmasked is live);
- the two teardown no-ops (a ``None`` result, an error-free result) whose whole
  observable behavior is that nothing happened, and the async
  ``PreExecutionError`` whose ``original_error is None`` the JSON envelope cannot
  show (the client-visible validation message is live);
- an ``ErrorPolicy`` subclass whose attribute reads raise, which the exact-type
  gate answers toward MASKING; and
- ``mask_execution_result``'s copy contract - the property that lets the
  subscription seam mask an event without disturbing the originals an extension
  reads. What that seam does on the wire is pinned at the consumer tier in
  ``tests/test_routers.py``, the only tier that can observe a subscription frame.
"""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace

import pytest
import pytest_django
import strawberry
from graphql import GraphQLError
from graphql.execution import ExecutionResult as GraphQLExecutionResult
from strawberry.extensions import SchemaExtension
from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult
from typing_extensions import override

from django_strawberry_framework import DjangoSchema
from django_strawberry_framework.error_policy import (
    DEFAULT_ERROR_POLICY,
    ErrorPolicy,
    new_correlation_id,
    resolve_error_policy,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.error_policy import (
    DjangoErrorPolicyExtension,
    mask_execution_result,
    schema_error_policy,
)
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.utils._narrowing import (
    read_attr,
)
from tests._execution import make_execution_context
from tests._idioms import ClassReadRaises

_SENSITIVE = "standalone schema secret /srv/private/standalone.key"


@strawberry.type
class _Query:
    """A schema-shaped query with one always-failing field."""

    @strawberry.field
    def ping(self) -> int:
        return 1

    @strawberry.field
    def boom(self) -> str | None:
        raise ValueError(_SENSITIVE)


# ---------------------------------------------------------------------------
# Construction and validation
# ---------------------------------------------------------------------------


def test_the_package_default_is_masking_on_with_the_documented_strings() -> None:
    """The fail-closed answer is the one a deployment gets by doing nothing."""
    assert DEFAULT_ERROR_POLICY.enabled is True
    assert DEFAULT_ERROR_POLICY.message == "An unexpected error occurred."
    assert DEFAULT_ERROR_POLICY.correlation_extension_key == "correlationId"


@pytest.mark.parametrize(
    "value",
    [
        1,
        0,
        "yes",
        None,
    ],
    ids=[
        "truthy-int",
        "falsy-int",
        "string",
        "none",
    ],
)
def test_a_non_bool_enabled_is_rejected_at_construction(value: object) -> None:
    """``enabled`` is a switch, not a truthiness test.

    ``1`` and ``"yes"`` would both silently work under a ``bool()`` coercion, and
    so would ``0`` - which is the dangerous one, because a deployment that meant
    to disable masking and a deployment that fat-fingered the type would be
    indistinguishable. The rejection names the field.
    """
    with pytest.raises(ConfigurationError, match=r"ErrorPolicy\.enabled must be a bool"):
        # basedpyright: each non-bool value is the hostile input under test; ErrorPolicy types
        # the parameter as bool
        ErrorPolicy(enabled=value)  # pyright: ignore[reportArgumentType]


def test_the_enabled_rejection_message_names_the_value() -> None:
    """The honest rejection message, byte for byte."""
    with pytest.raises(ConfigurationError) as excinfo:
        # basedpyright: the non-bool value is the hostile input under test; ErrorPolicy types the
        # parameter as bool
        ErrorPolicy(enabled="yes")  # pyright: ignore[reportArgumentType]
    assert str(excinfo.value) == "ErrorPolicy.enabled must be a bool; got str 'yes'."


@pytest.mark.parametrize(
    "value",
    ["", None, 42],
    ids=["empty", "none", "int"],
)
def test_a_non_string_or_empty_message_is_rejected_at_construction(value: object) -> None:
    """An empty mask is not a mask - the client would read a blank error."""
    with pytest.raises(
        ConfigurationError,
        match=r"ErrorPolicy\.message must be a non-empty string",
    ):
        # basedpyright: each non-string value is the hostile input under test; ErrorPolicy types
        # the parameter as str
        ErrorPolicy(message=value)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    "value",
    ["", None, 42],
    ids=["empty", "none", "int"],
)
def test_a_non_string_or_empty_correlation_key_is_rejected_at_construction(value: object) -> None:
    """An unusable extensions key would publish the id where no client can find it."""
    with pytest.raises(
        ConfigurationError,
        match=r"ErrorPolicy\.correlation_extension_key must be a non-empty string",
    ):
        # basedpyright: each non-string value is the hostile input under test; ErrorPolicy types
        # the parameter as str
        ErrorPolicy(correlation_extension_key=value)  # pyright: ignore[reportArgumentType]


class _HostileMessage(str):
    """A ``str`` SUBCLASS: ``isinstance``-valid, with a hostile ``__format__``."""

    @override
    def __format__(self, spec: str) -> str:
        raise RuntimeError("Hostile message format")


def _with_message(value: str) -> ErrorPolicy:
    return ErrorPolicy(message=value)


def _with_key(value: str) -> ErrorPolicy:
    return ErrorPolicy(correlation_extension_key=value)


@pytest.mark.parametrize(
    ("field", "build"),
    [("message", _with_message), ("correlation_extension_key", _with_key)],
    ids=["message", "correlation_extension_key"],
)
def test_a_str_subclass_is_rejected_at_construction(
    field: str,
    build: Callable[[str], ErrorPolicy],
) -> None:
    """The string fields take the built-in type only, the bound rule's own terms.

    ``isinstance`` admits a subclass, whose ``__str__`` / ``__format__`` are
    consumer code - and the place they would run is the masking path, whose whole
    job is to publish one string the deployment chose. A policy carrying one is a
    policy whose message can raise or rewrite itself at the moment an unexpected
    exception is being hidden, so it never becomes a policy at all
    (``resource_policy.py::_require_positive_int`` states the rule for a bound).
    """
    with pytest.raises(
        ConfigurationError,
        match=f"ErrorPolicy.{field} must be a non-empty string",
    ):
        build(_HostileMessage("Nope."))


def test_a_schema_refuses_a_policy_option_carrying_a_str_subclass() -> None:
    """The rejection is a deployment-time failure, not a per-request surprise."""
    with pytest.raises(
        ConfigurationError,
        match=r"ErrorPolicy\.message must be a non-empty string",
    ):
        DjangoSchema(query=_Query, error_policy={"message": _HostileMessage("Nope.")})


def test_a_str_subclass_cannot_survive_into_the_private_record() -> None:
    """The bypass shape: a policy built without ever running the validation.

    ``object.__new__`` plus a ``__dict__`` write produces an ``isinstance``-valid
    ``ErrorPolicy`` whose fields were never checked, which is how a subclass would
    reach a schema even with construction closed. Canonicalization re-validates
    what it reads, so the object an enforcement seam ends up with cannot carry
    one.
    """
    smuggled = object.__new__(ErrorPolicy)
    smuggled.__dict__.update(
        enabled=True,
        message=_HostileMessage("Nope."),
        correlation_extension_key="correlationId",
    )
    with pytest.raises(
        ConfigurationError,
        match=r"ErrorPolicy\.message must be a non-empty string",
    ):
        resolve_error_policy(smuggled)


def test_the_policy_is_frozen_so_a_plain_assignment_raises() -> None:
    """Frozen rejects the accident, not the adversary: a plain assignment raises.

    The ``__dict__`` write frozen admits touches only the object held, never
    the policy the schema stores.
    """
    with pytest.raises(Exception, match="cannot assign to field"):
        # basedpyright: the write to the frozen dataclass field is the mutation under test; the
        # checker rejects assignment to a frozen field
        DEFAULT_ERROR_POLICY.enabled = False  # pyright: ignore[reportAttributeAccessIssue]


# ---------------------------------------------------------------------------
# The precedence ladder
# ---------------------------------------------------------------------------


def test_an_explicit_instance_is_taken_as_a_private_duplicate() -> None:
    """An ``ErrorPolicy`` argument supplies values, never the object enforcement reads.

    The caller keeps what they passed, so what a schema masks with cannot be
    rewritten afterwards through the reference they still hold.
    """
    policy = ErrorPolicy(message="Nope.")
    resolved = resolve_error_policy(policy)
    assert resolved == policy
    assert resolved is not policy


def test_an_explicit_mapping_is_applied_over_the_package_defaults() -> None:
    """A deployment overrides only what it cares about."""
    policy = resolve_error_policy({"message": "Nope."})
    assert policy.message == "Nope."
    assert policy.enabled is True
    assert policy.correlation_extension_key == "correlationId"


def test_no_source_at_all_resolves_to_the_package_defaults() -> None:
    """The values of the exported template, in an object the exported name is not.

    A deployment that configures nothing is on exactly the same footing as one
    that passes an instance: what the schema masks with is a private duplicate.
    """
    resolved = resolve_error_policy(None)
    assert resolved == DEFAULT_ERROR_POLICY
    assert resolved is not DEFAULT_ERROR_POLICY


def test_a_written_exported_default_reaches_no_resolution() -> None:
    """The exported constant is a value template, never the object masking reads.

    ``DEFAULT_ERROR_POLICY`` is a public export, so consumer code holds it, and a
    frozen dataclass admits a ``__dict__`` write. Were the no-override path to
    answer with it, one write after startup would disable masking for every
    schema in the process - including schemas already built - and put raw
    exception text on the wire. The resolution carries the package's own values
    instead.
    """
    declared = dict(DEFAULT_ERROR_POLICY.__dict__)
    DEFAULT_ERROR_POLICY.__dict__["enabled"] = False
    DEFAULT_ERROR_POLICY.__dict__["message"] = "Written after startup."
    try:
        resolved = resolve_error_policy(None)
        assert resolved.enabled is True
        assert resolved.message == "An unexpected error occurred."
        assert resolved is not DEFAULT_ERROR_POLICY
        assert schema_error_policy(SimpleNamespace()).enabled is True
    finally:
        # The export is process-global: a write left behind would answer every
        # later test in the session.
        DEFAULT_ERROR_POLICY.__dict__.update(declared)


def test_the_setting_supplies_the_policy_when_no_argument_does(
    settings: pytest_django.Settings,
) -> None:
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"ERROR_POLICY": {"message": "From settings."}}
    assert resolve_error_policy(None).message == "From settings."


def test_an_explicit_argument_outranks_the_setting(settings: pytest_django.Settings) -> None:
    """A process running a public schema and an internal one must be able to differ."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"ERROR_POLICY": {"message": "From settings."}}
    assert resolve_error_policy({"message": "From the argument."}).message == "From the argument."


def test_a_non_mapping_policy_setting_is_rejected(settings: pytest_django.Settings) -> None:
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"ERROR_POLICY": 12}
    with pytest.raises(ConfigurationError, match="must be an ErrorPolicy or a mapping"):
        resolve_error_policy(None)


def test_a_non_mapping_policy_argument_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="must be an ErrorPolicy or a mapping"):
        # basedpyright: the non-mapping policy is the hostile input under test;
        # resolve_error_policy types the parameter as ErrorPolicy | Mapping[str, object] | None
        resolve_error_policy("invalid")  # pyright: ignore[reportArgumentType]


def test_a_policy_argument_whose_class_read_raises_is_rejected() -> None:
    """A value that cannot be classified is "not a policy, not a mapping", so the typed rejection names it."""
    with pytest.raises(ConfigurationError) as excinfo:
        # basedpyright: the unclassifiable policy is the hostile input under test;
        # resolve_error_policy types the parameter as ErrorPolicy | Mapping[str, object] | None
        resolve_error_policy(ClassReadRaises())  # pyright: ignore[reportArgumentType]
    assert str(excinfo.value) == (
        "The error policy must be an ErrorPolicy or a mapping of option names to values; "
        "got ClassReadRaises <ClassReadRaises>."
    )


def test_an_unknown_option_name_is_rejected_with_the_valid_vocabulary() -> None:
    """Naming the valid options in the message is what makes a typo self-correcting."""
    with pytest.raises(ConfigurationError, match=r"Unknown error-policy option\(s\): mesage"):
        resolve_error_policy({"mesage": "typo"})


# ---------------------------------------------------------------------------
# The correlation identifier
# ---------------------------------------------------------------------------


def test_a_correlation_id_is_thirty_two_lowercase_hex_characters() -> None:
    """The format is pinned so a log grep for one cannot match anything else."""
    value = new_correlation_id()
    assert len(value) == 32
    assert value == value.lower()
    assert all(character in "0123456789abcdef" for character in value)


def test_correlation_ids_do_not_repeat() -> None:
    """Random, not derived: a derived id would be an oracle over the masked text."""
    assert len({new_correlation_id() for _ in range(1000)}) == 1000


# ---------------------------------------------------------------------------
# Schema construction and install position
# ---------------------------------------------------------------------------


def test_the_schema_resolves_and_exposes_its_policy_once() -> None:
    """The schema resolves its policy once, at construction, for the extension to read."""
    schema = DjangoSchema(query=_Query, error_policy={"message": "Nope."})
    assert isinstance(schema.error_policy, ErrorPolicy)
    assert schema.error_policy.message == "Nope."


def test_reading_schema_error_policy_answers_a_copy() -> None:
    """The object a resolver can reach is not the stored policy.

    Writing ``__dict__["enabled"]`` on the handed-out object must not change a
    later read. The wire-visible consequence (a resolver write cannot unmask the
    response) lives in ``examples/fakeshop/test_query/test_error_policy_api.py``.
    """
    schema = DjangoSchema(query=_Query, error_policy=ErrorPolicy())
    reached = schema.error_policy
    reached.__dict__["enabled"] = False
    assert reached.enabled is False
    assert schema.error_policy.enabled is True


def test_an_invalid_policy_fails_the_deployment_at_schema_construction() -> None:
    """Startup, not the first request that happens to raise."""
    with pytest.raises(ConfigurationError, match=r"Unknown error-policy option\(s\): nope"):
        DjangoSchema(query=_Query, error_policy={"nope": 1})


def test_the_error_policy_extension_runs_first_in_every_chain() -> None:
    """Position is the contract, not a detail (spec-048 Decision 10).

    ``on_operation`` teardowns unwind LIFO, so the FIRST-listed extension tears
    down LAST - and masking must be last, after every extension that reads
    ``original_error`` has had its turn. The resource policy's position is
    asserted alongside it, because the two directions are what make the rule
    ("put the extension where its own half of the lifecycle runs last")
    legible: a future refactor that tidies them into a symmetric append fails
    here rather than silently emptying the debug payload's exception rows.
    """
    schema = DjangoSchema(query=_Query)
    resolved = schema.get_extensions(sync=True)
    assert isinstance(resolved[0], DjangoErrorPolicyExtension)
    assert isinstance(resolved[-3], DjangoResourcePolicyExtension)


def test_a_consumer_extension_is_prepended_behind_the_policy_not_in_front_of_it() -> None:
    """A consumer's own extension keeps its order relative to its peers."""

    class _ConsumerExtension(SchemaExtension):
        """A consumer extension with no behavior, present only to hold a position."""

    schema = DjangoSchema(query=_Query, extensions=[_ConsumerExtension])
    assert list(schema.extensions) == [_ConsumerExtension]
    assert [type(entry).__name__ for entry in schema.get_extensions(sync=True)] == [
        "DjangoErrorPolicyExtension",
        "_ConsumerExtension",
        "DjangoResourcePolicyExtension",
        "AdmissionGuard",
        "_OperationModeMarker",
    ]


def test_a_consumer_supplied_policy_entry_declares_the_automatic_one() -> None:
    """A consumer who names the extension gets it, and gets exactly one of it.

    A second copy would mask an already-masked error and mint a SECOND
    correlation id for it, so the client's id would not be the one in the log
    that carries the traceback. The entry declares the extension the schema
    installs anyway rather than adding another, and the consumer's own
    neighbours keep their order.
    """

    class _Other(SchemaExtension):
        """A neighbour, so "kept its position" is a real claim."""

    schema = DjangoSchema(query=_Query, extensions=[_Other, DjangoErrorPolicyExtension])
    assert list(schema.extensions) == [_Other]
    resolved = schema.get_extensions(sync=True)
    assert sum(isinstance(item, DjangoErrorPolicyExtension) for item in resolved) == 1
    assert isinstance(resolved[1], _Other)


# ---------------------------------------------------------------------------
# The standalone-schema fallback
# ---------------------------------------------------------------------------


def test_a_plain_schema_with_the_extension_installed_by_hand_masks_with_no_policy_attribute(
    settings: pytest_django.Settings,
) -> None:
    """A hand-wired ``strawberry.Schema`` has no ``error_policy``; its masked error, no original.

    What the client reads - the default policy's message and a correlation id, the
    sensitive text absent - is pinned over HTTP in
    ``examples/fakeshop/test_query/test_error_policy_api.py::test_a_plain_schema_with_the_extension_installed_by_hand_falls_back_to_the_default``.
    What stays here has no wire shape: the schema really has no attribute to read,
    and the error the policy hands back has shed its ``original_error``.
    """
    assert read_attr(settings, "DEBUG") is False
    schema = strawberry.Schema(query=_Query, extensions=[DjangoErrorPolicyExtension])
    assert not hasattr(schema, "error_policy")

    result = schema.execute_sync("{ boom }")
    assert result.errors is not None
    assert result.errors[0].original_error is None


# ---------------------------------------------------------------------------
# The teardown no-ops
# ---------------------------------------------------------------------------


def _run_teardown(result: GraphQLExecutionResult | None) -> None:
    """Drive one ``on_operation`` teardown over ``result`` under the default policy.

    Built directly rather than through a schema because a request cannot be
    relied on to hand the hook these shapes: whether the hooks see
    ``execution_context.result`` at ``None`` on a parse/validation early
    return is engine-version behavior, and Strawberry never hands the hook a
    result object it did not build. The context's schema is a plain
    ``strawberry.Schema``, which carries no ``error_policy``, so the hook falls
    back to the package's default policy.
    """
    extension = DjangoErrorPolicyExtension()
    # ``SchemaExtension.__init__`` accepts the argument but stores nothing; the
    # engine assigns the attribute, so the harness does the same.
    context = make_execution_context()
    context.result = result
    extension.execution_context = context
    hook = extension.on_operation()
    next(hook)
    with pytest.raises(StopIteration):
        next(hook)


def test_a_none_result_is_a_no_op() -> None:
    """A parse or validation early return has nothing to mask."""
    _run_teardown(None)


def test_an_error_free_result_is_left_alone() -> None:
    """The happy path must not allocate a new error list or touch ``data``."""
    result = GraphQLExecutionResult(data={"ping": 1}, errors=None)
    _run_teardown(result)
    assert result.errors is None
    assert result.data == {"ping": 1}


def test_a_graphql_core_execution_result_is_rewritten_in_place_preserving_order(
    settings: pytest_django.Settings,
) -> None:
    """Both result shapes are served by the one implementation (spec-048 Decision 11).

    Arity and order are preserved whether an entry was masked or not, so a client
    matching errors to its document by index is unaffected - asserted here over a
    mixed list, which a single-error response cannot show.
    """
    assert read_attr(settings, "DEBUG") is False
    deliberate = GraphQLError("Deliberate.", original_error=GraphQLError("Deliberate."))
    unexpected = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = GraphQLExecutionResult(data=None, errors=[deliberate, unexpected])

    _run_teardown(result)

    assert result.errors is not None
    assert len(result.errors) == 2
    assert result.errors[0] is deliberate
    assert result.errors[1].message == DEFAULT_ERROR_POLICY.message
    assert result.errors[1].original_error is None


async def test_an_async_pre_execution_error_carries_no_original_error(
    settings: pytest_django.Settings,
) -> None:
    """Strawberry's async validation result has ``original_error is None``.

    graphql-core never builds this shape during execution; the async path assigns
    a ``PreExecutionError`` that passes the teardown shape gate with nothing
    behind the errors. The JSON envelope cannot show that field. The
    client-visible message, ``data: null``, and absent correlation id live in
    ``examples/fakeshop/test_query/test_error_policy_api.py``.
    """
    assert read_attr(settings, "DEBUG") is False
    schema = DjangoSchema(query=_Query)

    result = await schema.execute("{ notAField }")

    assert result.errors is not None
    assert "notAField" in result.errors[0].message
    assert result.errors[0].original_error is None
    assert result.errors[0].extensions in (None, {})


# ---------------------------------------------------------------------------
# The exact-type-gated policy read
# ---------------------------------------------------------------------------


class _PolicySubclass(ErrorPolicy):
    """An ``ErrorPolicy`` subclass: its field reads would be code of its own."""


@pytest.mark.parametrize(
    "attribute",
    [
        "not a policy",
        {"enabled": False},
        None,
        0,
        _PolicySubclass(enabled=False),
    ],
    ids=[
        "string",
        "mapping",
        "none",
        "zero",
        "disabled-subclass",
    ],
)
def test_a_schema_attribute_that_is_not_a_policy_falls_back_to_the_default(
    attribute: object,
) -> None:
    """A wrong ``schema.error_policy`` must not become a silent way to stop masking.

    ``getattr(schema, "error_policy", DEFAULT)`` alone answers the default only
    when the attribute is ABSENT; anything present is returned whatever it is, and
    a mapping or a string would then be asked ``policy.enabled`` (raising) or read
    for its truthiness (disabling masking). The fallback is therefore gated on
    the exact ``ErrorPolicy`` class - a subclass could answer ``enabled`` with
    code of its own, so even a disabled one is not read - and it lands on the
    MASKING default in every wrong-shape case, the fail-closed direction.
    ``DjangoSchema`` cannot produce any of these (it stores a canonical exact
    copy); a consumer subclass or a stray assignment can.
    """
    schema = SimpleNamespace(error_policy=attribute)
    fallback = schema_error_policy(schema)
    assert fallback == DEFAULT_ERROR_POLICY
    assert fallback is not DEFAULT_ERROR_POLICY


def test_an_absent_attribute_and_a_real_policy_are_both_read_correctly() -> None:
    """The two shapes that are not failures: no attribute at all, and a real policy."""
    fallback = schema_error_policy(SimpleNamespace())
    assert fallback == DEFAULT_ERROR_POLICY
    assert fallback is not DEFAULT_ERROR_POLICY
    policy = ErrorPolicy(message="Mine.")
    assert schema_error_policy(SimpleNamespace(error_policy=policy)) is policy


# ---------------------------------------------------------------------------
# The per-event seam's contract with the extensions that read originals
# ---------------------------------------------------------------------------


def test_a_genuinely_empty_error_list_is_still_a_no_op() -> None:
    """An empty error list leaves nothing to mask, so the result itself comes back."""
    result = GraphQLExecutionResult(data={"ping": 1}, errors=[])

    assert mask_execution_result(result, DEFAULT_ERROR_POLICY) is result
    assert result.errors == []


def test_masking_returns_the_same_object_when_nothing_needed_masking() -> None:
    """Identity, so the caller can tell "nothing happened" without comparing lists."""
    deliberate = GraphQLError("Deliberate.", original_error=GraphQLError("Deliberate."))
    result = GraphQLExecutionResult(data=None, errors=[deliberate])

    assert mask_execution_result(result, DEFAULT_ERROR_POLICY) is result
    assert (
        mask_execution_result(
            GraphQLExecutionResult(data={"ping": 1}, errors=None),
            DEFAULT_ERROR_POLICY,
        ).errors
        is None
    )


def test_masking_leaves_the_original_result_holding_its_originals() -> None:
    """The COPY is what makes the per-event seam safe for the debug extension.

    The subscription seam masks each event before delivery, and the engine's own
    result object is the one an extension reading ``GraphQLError.original_error``
    sees at teardown. Masking a copy is what keeps the LIFO ordering promise true
    on the subscription path as well as the query path - an in-place rewrite here
    would empty the debug payload's exception rows for every subscription.
    """
    original = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = GraphQLExecutionResult(data={"leaky": None}, errors=[original])

    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked is not result
    assert result.errors == [original]
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, ValueError)
    assert masked.data == {"leaky": None}
    assert masked.errors is not None
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message


# ---------------------------------------------------------------------------
# The schema's return seam, over results no engine hands it
# ---------------------------------------------------------------------------


def test_the_return_seam_snapshots_an_already_masked_result_without_remasking(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Final publication owns its list while keeping the teardown's exact errors."""
    schema = DjangoSchema(query=_Query)
    already_masked = GraphQLError(
        DEFAULT_ERROR_POLICY.message,
        original_error=None,
        extensions={DEFAULT_ERROR_POLICY.correlation_extension_key: new_correlation_id()},
    )
    result = StrawberryExecutionResult(data=None, errors=[already_masked])

    snapshot = schema._masked_return(result)
    assert isinstance(snapshot, StrawberryExecutionResult)
    assert snapshot is not result
    assert snapshot.errors is not result.errors
    assert snapshot.errors is not None
    assert snapshot.errors[0] is already_masked
    assert not caplog.records


def test_the_return_seam_is_a_no_op_when_the_policy_is_disabled() -> None:
    """``error_policy={"enabled": False}`` reaches this seam like every other one."""
    schema = DjangoSchema(query=_Query, error_policy={"enabled": False})
    leaky = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = StrawberryExecutionResult(data=None, errors=[leaky])

    assert schema._masked_return(result) is result
    assert result.errors is not None
    assert result.errors[0].message == _SENSITIVE
