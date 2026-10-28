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
  a consumer's own entry exactly where they put it;
- the schema attribute answering a duplicate of the stored policy (identity is
  not on the wire; the resolver-write consequence is live);
- the standalone fallback a plain ``strawberry.Schema`` takes, which has no
  ``error_policy`` attribute to read, and the exact-type-gated fallback a schema
  carrying a WRONG ``error_policy`` attribute takes;
- the two teardown no-ops (a ``None`` result, an error-free result) whose whole
  observable behavior is that nothing happened, and the async
  ``PreExecutionError`` whose ``original_error is None`` the JSON envelope cannot
  show (the client-visible validation message is live);
- the two fail-closed degrades, which need an error object and a result object no
  engine builds;
- the gate and the floor under inputs no engine produces: a ``DEBUG`` setting
  that cannot be read at all, an ``ErrorPolicy`` subclass whose attribute reads
  raise, a container that lies about its emptiness, and an error whose
  ``original_error`` read raises - every read the policy cannot verify answers
  toward MASKING, and the floor that everything degrades onto cannot itself
  raise; and
- ``mask_execution_result``'s copy contract - the property that lets the
  subscription seam mask an event without disturbing the originals an extension
  reads. What that seam does on the wire is pinned at the consumer tier in
  ``tests/test_routers.py``, the only tier that can observe a subscription frame.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import NoReturn

import pytest
import pytest_django
import strawberry
from django.conf import settings as django_settings
from graphql import GraphQLError
from graphql.execution import ExecutionResult as GraphQLExecutionResult
from strawberry.extensions import SchemaExtension
from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult
from typing_extensions import override

from django_strawberry_framework import DjangoSchema
from django_strawberry_framework import schema as schema_module
from django_strawberry_framework.error_policy import (
    DEFAULT_ERROR_POLICY,
    ErrorPolicy,
    new_correlation_id,
    resolve_error_policy,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.debug import DjangoDebugExtension
from django_strawberry_framework.extensions.error_policy import (
    DjangoErrorPolicyExtension,
    mask_execution_result,
    masking_is_active,
    schema_error_policy,
)
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.utils._narrowing import (
    dict_of,
    is_str,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.typing import object_result
from tests._execution import execution_result, make_execution_context
from tests._idioms import ClassReadRaises, json_at, json_list

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
    the stored enforcement record.
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


def test_a_callable_policy_entry_cannot_become_the_masking_authority() -> None:
    """What a factory returns next request is decided after the entry was accepted.

    A mutable factory can hand back the real extension for one operation and a
    subclass whose ``on_operation`` does nothing for the next; both answer every
    inheritance check and only one masks. The schema installs its own masking
    extension per operation and refuses a resolved member claiming that role.
    """

    class _FactoryPolicy(DjangoErrorPolicyExtension):
        pass

    def factory() -> DjangoErrorPolicyExtension:
        return _FactoryPolicy()

    schema = DjangoSchema(query=_Query, extensions=[factory])
    result = schema.execute_sync("{ ok }")

    assert result.data is None
    assert result.errors is not None
    assert [error.extensions for error in result.errors] == [
        {"code": "SCHEMA_CONFIGURATION_UNAVAILABLE"},
    ]


def test_a_declared_policy_beside_a_debug_factory_preserves_debug_exception_capture() -> None:
    """Declaring the masking extension must not duplicate it or preempt debug teardown.

    A direct entry of the schema's own error-policy extension is read once as a
    declaration and never joins the chain, so the schema still installs exactly
    one masking authority - and the neighbouring factory entry still builds its
    own extension per operation and still captures the exception that was
    masked. Two masking extensions would mint a second correlation id for an
    already-masked error and leave debug's teardown looking at the wrong one.
    """

    def debug_factory() -> DjangoDebugExtension:
        return DjangoDebugExtension(allow_unsafe_production=True)

    schema = DjangoSchema(
        query=_Query,
        extensions=[DjangoErrorPolicyExtension(), debug_factory],
    )
    result = schema.execute_sync("{ boom }")

    assert result.extensions is not None
    assert len(json_list(result.extensions, "debug", "exceptions")) == 1


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


def test_a_plain_schema_with_the_extension_installed_by_hand_falls_back_to_the_default(
    settings: pytest_django.Settings,
) -> None:
    """A hand-wired ``strawberry.Schema`` has no ``error_policy`` attribute to read.

    The fallback is the MASKING one on purpose: an extension whose whole job is to
    mask must not quietly become a no-op because it could not find its
    configuration. This is a supported standalone use, so it must not raise
    either.
    """
    assert read_attr(settings, "DEBUG") is False
    schema = strawberry.Schema(query=_Query, extensions=[DjangoErrorPolicyExtension])
    assert not hasattr(schema, "error_policy")

    result = schema.execute_sync("{ boom }")
    assert result.errors is not None
    error = result.errors[0]
    assert error.message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in error.message
    assert error.original_error is None
    assert error.extensions is not None
    correlation_id = json_at(error.extensions, DEFAULT_ERROR_POLICY.correlation_extension_key)
    assert len(require_instance(correlation_id, str)) == 32


class _FailingHookExtension(SchemaExtension):
    """An ordinary consumer extension failing at the operation-teardown half."""

    @override
    def on_operation(self) -> Iterator[None]:
        yield
        raise RuntimeError(_SENSITIVE)


def test_a_plain_schema_leaves_a_hook_failure_unmasked() -> None:
    """The hook seam lives on the schema, so a hand-wired plain schema has none.

    A hook exception is converted into a result only after every teardown has
    unwound, so no extension is left to mask it; ``DjangoSchema`` masks that
    result at its own return. A plain ``strawberry.Schema`` carrying the
    exported extension by hand has no such return, so the identical hook
    failure reaches the client with its own message and no correlation id.
    """
    assert read_attr(django_settings, "DEBUG") is False
    schema = strawberry.Schema(
        query=_Query,
        extensions=[DjangoErrorPolicyExtension, _FailingHookExtension],
    )
    result = schema.execute_sync("{ ping }")
    assert result.errors, result
    messages = " ".join(error.message for error in result.errors)
    assert _SENSITIVE in messages, messages
    for error in result.errors:
        assert (error.extensions or {}).get(
            DEFAULT_ERROR_POLICY.correlation_extension_key,
        ) is None, error.extensions


def test_the_schema_masks_the_same_hook_failure_its_extension_cannot_reach() -> None:
    """Positive control: ``DjangoSchema`` masks the hook failure above."""
    assert read_attr(django_settings, "DEBUG") is False
    schema = DjangoSchema(query=_Query, extensions=[_FailingHookExtension])
    result = schema.execute_sync("{ ping }")
    assert result.errors, result
    assert result.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in result.errors[0].message
    assert result.errors[0].extensions is not None
    correlation_id = dict_of(result.errors[0].extensions)[
        DEFAULT_ERROR_POLICY.correlation_extension_key
    ]
    assert len(require(correlation_id, is_str)) == 32


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
# Masking degrades CLOSED
# ---------------------------------------------------------------------------


class _HostileError(GraphQLError):
    """A ``GraphQLError`` whose ``original_error`` raises when read.

    Not reachable through a request - graphql-core builds every error on a result
    - but reachable through a consumer extension that put its own object in
    ``result.errors``, and the point of a fail-closed degrade is that it does not
    depend on the object being well behaved.
    """

    def __init__(self) -> None:
        super().__init__(_SENSITIVE)

    @override
    def __getattribute__(self, name: str) -> object:
        if name == "original_error":
            raise RuntimeError(_SENSITIVE)
        return object_result(super().__getattribute__, name)


class _HostileResult(GraphQLExecutionResult):
    """A graphql-core result whose ``errors`` cannot be read at all."""

    def __init__(self) -> None:
        super().__init__(data={"ping": 1})

    @override
    def __getattribute__(self, name: str) -> object:
        if name == "errors":
            raise RuntimeError(_SENSITIVE)
        return object_result(super().__getattribute__, name)


class _HostileStrawberryResult(StrawberryExecutionResult):
    """An admitted result whose error list raises when read but accepts replacement."""

    @property
    @override
    def errors(self) -> list[GraphQLError] | None:
        raise RuntimeError(_SENSITIVE)

    @errors.setter
    # basedpyright: the hostile shape under test, an ``errors`` property whose read raises; the
    # checker rejects any property overriding a base class attribute
    def errors(self, value: list[GraphQLError] | None) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        self._replacement_errors = value


class _WriteRejectingStrawberryResult(StrawberryExecutionResult):
    """A stock-shape subclass that rejects adoption after construction."""

    @override
    def __setattr__(self, name: str, value: object) -> None:
        if name == "data" and name in self.__dict__:
            raise RuntimeError("result is frozen")
        super().__setattr__(name, value)


class _SneakyError(GraphQLError):
    """A ``GraphQLError`` subclass whose ``original_error`` read raises ``AttributeError``.

    The property shadows the instance attribute ``__init__`` sets, so every read
    raises - exactly the ambiguity a defaulted ``getattr`` cannot resolve: it
    would answer it as absence, taking the deliberate-delivery branch with the
    error's own message left on the wire.
    """

    @property
    @override
    # basedpyright: the hostile shape under test, an ``original_error`` property whose read raises;
    # the checker rejects any property overriding a base class attribute
    def original_error(self) -> NoReturn:  # pyright: ignore[reportIncompatibleVariableOverride]
        raise AttributeError("original_error is not available")


class _LyingErrors(list[GraphQLError]):
    """A populated container answering falsy, so a truthiness check skips it."""

    def __bool__(self) -> bool:
        return False


class _UnreadableSettings:
    """A wrapped-settings stand-in that admits no attribute reads at all.

    One unreadable-``DEBUG`` shape: the wrapped holder answers
    ``AttributeError`` to every read, which the gate must survive as surely
    as a deleted ``DEBUG``.
    """

    def __getattr__(self, name: str) -> NoReturn:
        raise AttributeError(f"No setting {name!r} exists on this holder.")


@pytest.mark.parametrize(
    "absence",
    ["deleted", "unreadable-holder"],
    ids=["LazySettings cache + _wrapped cleared", "_wrapped replaced by unreadable"],
)
def test_the_masking_gate_stays_active_when_debug_cannot_be_read(
    monkeypatch: pytest.MonkeyPatch,
    absence: str,
) -> None:
    """A masking question answered by exception is one that stays masking ON.

    Deleting the attribute (both the proxy's cache and the wrapped holder,
    through the proxy's ``__delattr__``), or replacing the wrapped holder with
    one that raises ``AttributeError`` on attribute access, both make the read
    raise. The gate catches the documented settings failures and defaults toward
    masking: an unreadable ``DEBUG`` answer becomes not exactly ``True``.
    """
    if absence == "deleted":
        monkeypatch.delattr(django_settings, "DEBUG")
    else:
        monkeypatch.setattr(django_settings, "_wrapped", _UnreadableSettings())

    assert masking_is_active(DEFAULT_ERROR_POLICY) is True


def test_a_teardown_with_unreadable_debug_masks_normally_and_keeps_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unreadable ``DEBUG`` keeps masking AND the client's own data.

    A gate answering by exception would escape the teardown instead of masking.
    The gate catches the documented settings failures, so the mask simply runs -
    policy message and correlation id on the errors, ``data`` untouched.
    """
    monkeypatch.setattr(django_settings, "_wrapped", _UnreadableSettings())
    result = GraphQLExecutionResult(
        data={"ping": 1},
        errors=[GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))],
    )

    _run_teardown(result)

    assert result.data == {"ping": 1}
    assert result.errors is not None
    assert len(result.errors) == 1
    assert result.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in result.errors[0].message
    assert result.errors[0].extensions is not None
    correlation_id = json_at(
        result.errors[0].extensions,
        DEFAULT_ERROR_POLICY.correlation_extension_key,
    )
    assert len(require_instance(correlation_id, str)) == 32


def test_a_falsy_but_populated_errors_container_is_still_masked() -> None:
    """Iteration, not the container's own truthiness, decides what is classified.

    A populated container whose ``__bool__`` answers falsy would be waved
    through an emptiness check unclassified, its messages intact. The list is
    materialized before the check, so what is classified is what the container
    actually carries, and order and arity survive the rewrite.
    """
    fine = GraphQLError("Deliberate.", original_error=GraphQLError("Deliberate."))
    result = StrawberryExecutionResult(
        data={"ping": 1},
        errors=_LyingErrors(
            [fine, GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))],
        ),
    )

    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked is not result
    assert masked.errors is not None
    assert masked.errors[0] is fine
    assert masked.errors[1].message == DEFAULT_ERROR_POLICY.message
    assert masked.data == {"ping": 1}


def test_a_genuinely_empty_error_list_is_still_a_no_op() -> None:
    """Materializing before the emptiness check keeps the empty-list no-op."""
    result = GraphQLExecutionResult(data={"ping": 1}, errors=[])

    assert mask_execution_result(result, DEFAULT_ERROR_POLICY) is result
    assert result.errors == []


def test_an_original_error_read_that_raises_is_masked_not_trusted() -> None:
    """An error the classifier cannot read behind is unexpected, not deliberate.

    A defaulted ``getattr`` cannot tell an absent ``original_error`` - the parse
    and validation case, which travels unchanged - from one whose read RAISES.
    Answering a raise with "absent" would ship the error's own message as a
    deliberate delivery. The direct read's failure lands on the per-entry
    degrade instead: the policy-message floor, no location, nothing of the original.
    """
    error = _SneakyError.__new__(_SneakyError)
    result = StrawberryExecutionResult(data={"ping": 1}, errors=[error])

    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked is not result
    assert masked.errors is not None
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in str(masked.errors[0].message)
    assert masked.errors[0].original_error is None
    assert masked.data == {"ping": 1}


def test_one_error_that_cannot_be_masked_degrades_to_the_policy_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A masking failure is a disclosure risk, so it fails CLOSED, not open.

    The tempting degrade - leave the entry as it was found - publishes exactly the
    text the policy exists to withhold, and it publishes it on the one path nobody
    tested. So the entry becomes the policy message with no location and no
    correlation id (nothing may be read off the error that just failed to be
    read), the failure is logged with its traceback, and every OTHER entry in the
    same result is masked normally.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    fine = GraphQLError("Deliberate.", original_error=GraphQLError("Deliberate."))
    result = GraphQLExecutionResult(data=None, errors=[_HostileError(), fine])

    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked is not result
    assert masked.errors is not None
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert masked.errors[0].extensions in (None, {})
    assert masked.errors[1] is fine
    assert _SENSITIVE not in "".join(str(error.message) for error in masked.errors)
    assert any(record.exc_info for record in caplog.records)


def test_a_result_whose_errors_cannot_be_read_degrades_to_one_policy_message(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The outer floor: an unreadable error list still answers something safe.

    One policy-message error and no ``data``. Dropping ``data`` is deliberate - a
    result this module could not read is a result it cannot vouch for - and it is
    the only degrade that changes arity, which is why the per-entry degrade above
    exists to keep the common case faithful.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")

    masked = mask_execution_result(_HostileResult(), DEFAULT_ERROR_POLICY)

    assert masked.data is None
    assert masked.errors is not None
    assert len(masked.errors) == 1
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert any(record.exc_info for record in caplog.records)


def test_the_extension_adopts_all_fields_of_the_outer_fail_closed_degrade(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unreadable result retains neither data nor extensions after the floor applies.

    The degrade drops all three fields, so the adoption must overwrite the
    populated ``extensions`` map too -- leaving it in place would publish
    whatever the failed result carried there.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    result = _HostileStrawberryResult(
        data={"secret": _SENSITIVE},
        errors=[],
        extensions={"leak": _SENSITIVE},
    )
    extension = DjangoErrorPolicyExtension()
    context = make_execution_context()
    context.result = result
    extension.execution_context = context

    extension._process_result(result, DEFAULT_ERROR_POLICY)

    assert result.data is None
    assert result._replacement_errors is not None
    assert result._replacement_errors[0].message == DEFAULT_ERROR_POLICY.message
    assert result.extensions is None
    assert any(record.exc_info for record in caplog.records)


def test_the_extension_replaces_a_result_that_rejects_safe_field_adoption(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    result = _WriteRejectingStrawberryResult(
        data={"secret": _SENSITIVE},
        errors=[GraphQLError(_SENSITIVE, original_error=RuntimeError(_SENSITIVE))],
    )
    extension = DjangoErrorPolicyExtension()
    context = make_execution_context()
    context.result = result
    extension.execution_context = context

    extension._process_result(result, DEFAULT_ERROR_POLICY)

    degraded = execution_result(context)
    assert degraded is not result
    assert isinstance(degraded, StrawberryExecutionResult)
    assert degraded.data is None
    assert degraded.errors is not None
    assert degraded.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert any(record.exc_info for record in caplog.records)


def test_a_non_graphql_error_with_none_original_error_is_masked_as_unexpected() -> None:
    """Any non-GraphQLError object in errors is classified as unexpected and masked."""

    class _CustomError:
        message = _SENSITIVE
        original_error = None

    error = _CustomError()
    # basedpyright: the non-GraphQLError entry is the hostile input under test; strawberry types
    # the parameter as list[GraphQLError] | None
    result = StrawberryExecutionResult(data={"data": 123}, errors=[error])  # pyright: ignore[reportArgumentType]
    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked.data == {"data": 123}
    assert masked.errors is not None
    assert len(masked.errors) == 1
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message
    assert _SENSITIVE not in str(masked.errors[0].message)


def test_a_generator_or_iterator_error_list_is_masked_preserving_data() -> None:
    """An iterator or generator on result.errors is consumed safely without crashing zip."""
    original = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = StrawberryExecutionResult(
        data={"safe_field": 42},
        # basedpyright: the one-shot generator is the input under test; strawberry types the
        # parameter as list[GraphQLError] | None
        errors=(err for err in [original]),  # pyright: ignore[reportArgumentType]
    )
    masked = mask_execution_result(result, DEFAULT_ERROR_POLICY)

    assert masked.data == {"safe_field": 42}
    assert masked.errors is not None
    assert len(masked.errors) == 1
    assert masked.errors[0].message == DEFAULT_ERROR_POLICY.message


# ---------------------------------------------------------------------------
# The per-event seam's contract with the extensions that read originals
# ---------------------------------------------------------------------------


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


def test_the_return_seam_degrades_when_masking_itself_raises(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A seam that cannot decide what is safe publishes the floor, not the result.

    ``mask_execution_result`` contains its own failures, so what is left for this
    guard is a gate that will not answer at all - and the direction is the one the
    whole policy takes: the response degrades to the policy message alone rather
    than falling back to whatever the result was carrying.
    """
    caplog.set_level(logging.ERROR, logger="django_strawberry_framework")
    schema = DjangoSchema(query=_Query)

    def _unanswerable(_policy: ErrorPolicy) -> NoReturn:
        raise RuntimeError("the masking gate cannot answer")

    monkeypatch.setattr(schema_module, "masking_is_active", _unanswerable)
    leaky = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    degraded = schema._masked_return(
        StrawberryExecutionResult(data={"leaky": None}, errors=[leaky]),
    )

    assert degraded.data is None
    assert degraded.errors is not None
    assert [error.message for error in degraded.errors] == [DEFAULT_ERROR_POLICY.message]
    assert not degraded.errors[0].extensions  # no correlation id: nothing to resolve it to
    assert any(
        "could not be applied to the returned execution result" in record.message
        for record in caplog.records
    )


def test_the_return_seam_is_a_no_op_when_the_policy_is_disabled() -> None:
    """``error_policy={"enabled": False}`` reaches this seam like every other one."""
    schema = DjangoSchema(query=_Query, error_policy={"enabled": False})
    leaky = GraphQLError(_SENSITIVE, original_error=ValueError(_SENSITIVE))
    result = StrawberryExecutionResult(data=None, errors=[leaky])

    assert schema._masked_return(result) is result
    assert result.errors is not None
    assert result.errors[0].message == _SENSITIVE
