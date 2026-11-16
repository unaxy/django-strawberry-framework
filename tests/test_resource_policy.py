"""``ResourcePolicy`` construction, narrowing, threading, and walker edge cases.

The package tier of the resource policy: everything a live ``/graphql/`` request
cannot reach. The boundaries themselves - what a real document, a real variable
payload, and a real upload are charged - are pinned over HTTP in
``examples/fakeshop/test_query/test_resource_policy_api.py``, because that is
where they matter. What is left here is the surface a request cannot express:

- policy construction and per-bound validation, including the ``bool`` trap
  (``True`` is an ``int``) and the deadline's separate domain (no live sibling:
  ``ConfigurationError`` at construction never reaches a view);
- the precedence ladder (constructor argument > setting > package default) and
  the settings-shape rejections (live sibling: the enforcement-authority rows
  on ``/rp-authority/`` / ``/rp-retained/``);
- the narrowing rule, which no request can exercise because it is a
  build-time contract between a field and the schema policy (live sibling:
  ``/rp-rows/`` collection ceilings);
- context threading against the frozen / dict / object context shapes, and the
  fail-closed default a missing stash produces (live sibling: ``/rp-deadline/``,
  the authority mounts, and the nested-schema restore on ``/rp-nested/``);
- the walker's degenerate inputs - an unknown fragment, a cyclic fragment set,
  an operation kind the schema does not define, an untyped container, an upload
  that cannot report its size - which a valid request cannot produce but a
  hostile or unusual one can (a malformed document IS expressible over the
  wire, so the swallow-the-lexer-error pair lives in the live suite;
  named-operation post-parse charging lives on ``/rp-shape/``);
- the walk's per-node directive work, which leaves every verdict unchanged and
  so shows only as the reads of a bare directive's arguments and the directives
  the walk resolves (live sibling: the argument-less directive rows on
  ``/rp-values/``);
- the value walker's IDENTITY contracts, which need constructed object graphs a
  JSON body cannot express: a container referenced twice charged twice, two
  distinct-but-equal containers both charged, and cycles closing onto a parent
  and onto a grandparent through both container families (live sibling:
  ``test_one_variable_spliced_into_two_mutation_fields_is_charged_twice``);
- the connection SHAPE test from both sides, against probe types that borrow the
  ``edges`` name without the edge shape - which the example schema, having only
  real connections, cannot supply (live sibling: collection-cost rows on
  ``/rp-cost/``);
- hostile numeric subclasses a JSON body cannot carry (live sibling: ordinary
  int / string charges on ``/rp-values/``); and
- the ID-scalar FALLBACK half of the relation-list classification, which a
  mutation the package did not generate (no bind specs) rides - the example
  schema's writes are all package-generated, so their spec-keyed twins are
  pinned live.
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import copy
import math
import time
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Generator,
    Iterable,
    Iterator,
    Mapping,
)
from dataclasses import FrozenInstanceError, replace
from dataclasses import fields as dataclass_fields
from itertools import islice
from types import MappingProxyType, SimpleNamespace
from typing import NoReturn, TypeVar
from unittest.mock import MagicMock

import pytest
import pytest_django
import strawberry
from apps.products.models import Category, Item
from apps.products.services import seed_data
from asgiref.sync import sync_to_async
from django.db.models import Manager, Model, QuerySet
from graphql import (
    DirectiveNode,
    GraphQLDirective,
    GraphQLError,
    GraphQLSchema,
    OperationDefinitionNode,
    SelectionNode,
    build_schema,
    parse,
)
from graphql.language.token_kind import TokenKind
from strawberry.extensions import ValidationCache
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types import Info
from typing_extensions import override

import django_strawberry_framework.resource_policy as rp
from django_strawberry_framework import DjangoSchema, DjangoType, Upload, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.resource_policy import (
    _CLOSE_TOKEN_KINDS,
    _OPEN_TOKEN_KINDS,
    _STRUCTURAL_DELIMITER_PAIRS,
    DjangoResourcePolicyExtension,
    charge_document,
    scan_document_text,
)
from django_strawberry_framework.resource_policy import (
    DEFAULT_RESOURCE_POLICY,
    DST_RESOURCE_DEADLINE,
    DST_RESOURCE_POLICY,
    MAX_RESOURCE_BOUND,
    ResourceLimitExceeded,
    ResourcePolicy,
    _BudgetScope,
    _cleanup_rejected_async_iterable,
    _RequestBudget,
    _windowed_rows,
    _windowed_rows_async,
    admission_rejection,
    begin_resource_budget,
    bounded_rows,
    bounded_rows_async,
    check_deadline,
    effective_bound,
    end_resource_budget,
    policy_from_info,
    record_admission_rejection,
    resolve_resource_policy,
    validate_collection_bound,
    validate_trusted_flag,
)
from django_strawberry_framework.schema import _consumer_extension_entries
from django_strawberry_framework.utils._narrowing import (
    call_method,
    instance_state,
    is_exact_pair,
    is_list_or_tuple,
    read_attr,
    require,
    require_instance,
)
from django_strawberry_framework.utils.context import stash_on_context
from django_strawberry_framework.utils.querysets import materialized_rows
from django_strawberry_framework.utils.typing import object_result
from tests._django_private import has_apply_rel_filters
from tests._execution import make_execution_context
from tests._idioms import (
    is_object_list,
    pickle_roundtrip,
    saved_pk,
)

_M = TypeVar("_M", bound=Model)
_QuerySetT = TypeVar("_QuerySetT", bound="QuerySet[Model, object]")


# ---------------------------------------------------------------------------
# Construction and validation
#
# No live sibling: ``ConfigurationError`` at construction never reaches a view.
# Consumer bounds live in examples/fakeshop/test_query/test_resource_policy_api.py.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        "5",
        1.5,
        None,
        True,
    ],
    ids=[
        "zero",
        "negative",
        "string",
        "float",
        "none",
        "bool",
    ],
)
def test_a_non_positive_integer_bound_is_rejected_at_construction(value: object) -> None:
    """``True`` is in this list on purpose: ``isinstance(True, int)`` is ``True``.

    A bound accepting ``True`` would silently become ``1``, which is a bound so
    tight it looks like a different bug entirely.
    """
    with pytest.raises(ConfigurationError, match="max_page_size must be a positive integer"):
        # basedpyright: each non-positive or non-int bound is the hostile input under test;
        # ResourcePolicy types the parameter as int
        ResourcePolicy(max_page_size=value)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
        "5",
        True,
        math.inf,
        math.nan,
        10**400,
    ],
    ids=[
        "zero",
        "negative",
        "string",
        "bool",
        "infinity",
        "nan",
        "oversized-integer",
    ],
)
def test_an_invalid_execution_deadline_is_rejected(value: object) -> None:
    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        # basedpyright: each invalid deadline is the hostile input under test; ResourcePolicy
        # types the parameter as float | None
        ResourcePolicy(execution_deadline_seconds=value)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize("value", [None, 1, 0.5])
def test_a_valid_execution_deadline_is_accepted(value: float | None) -> None:
    """The deadline is the one optional bound, and it accepts a float.

    The positive control for ``_is_valid_deadline``: without it the rejection
    tests above would still pass if the domain check refused everything.
    """
    assert ResourcePolicy(execution_deadline_seconds=value).execution_deadline_seconds == value


def test_a_hostile_numeric_deadline_subclass_is_typed_rejected() -> None:
    """A numeric SUBCLASS whose comparison raises is rejected as a typed error.

    It is a hostile configuration object: the domain check cannot classify it, so
    the answer is the typed ``ConfigurationError``, never the raw arithmetic
    error leaking out of schema construction.
    """

    class HostileFloat(float):
        @override
        def __gt__(self, other: object) -> NoReturn:
            raise RuntimeError("hostile __gt__ detonated")

    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=HostileFloat(1.0))


def test_a_huge_int_deadline_overflows_the_finite_check_into_the_typed_rejection() -> None:
    """``isfinite(float(10**600))`` overflows; the rejection must stay typed."""
    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=10**600)


@pytest.mark.parametrize(
    "name",
    [field.name for field in dataclass_fields(ResourcePolicy)],
    ids=str,
)
def test_the_package_default_policy_is_bounded_on_every_axis(name: str) -> None:
    """The fail-closed claim, asserted rather than assumed.

    There is no spelling of a bound that disables it, so the default policy must
    carry a positive integer on every axis except the deadline.
    """
    value = read_attr(DEFAULT_RESOURCE_POLICY, name)
    if name == "execution_deadline_seconds":
        assert value is None
    else:
        assert type(value) is int, name
        assert value >= 1, name


def test_a_policy_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError, match="cannot assign to field"):
        # basedpyright: the write to the frozen dataclass field is the mutation under test; the
        # checker rejects assignment to a frozen field
        DEFAULT_RESOURCE_POLICY.max_page_size = 1  # pyright: ignore[reportAttributeAccessIssue]


def test_a_bound_at_the_representable_maximum_is_accepted_and_can_reject() -> None:
    """The largest accepted bound must still reach SQL and render its own rejection.

    A ceiling is only real if the configuration at it works end to end, so this
    row builds the policy AND renders the typed rejection the bound drives -
    which is where an over-large value fails, inside CPython's integer-to-string
    conversion limit, rather than at construction.

    Live sibling: ``test_a_bound_at_the_representable_maximum_reaches_the_database``.
    """
    policy = ResourcePolicy(max_list_rows=MAX_RESOURCE_BOUND)
    assert policy.max_list_rows == MAX_RESOURCE_BOUND
    rejection = ResourceLimitExceeded(
        "max_list_rows",
        policy.max_list_rows,
        policy.max_list_rows + 1,
        "detail",
    )
    assert str(MAX_RESOURCE_BOUND) in rejection.message
    assert rejection.extensions is not None
    assert rejection.extensions["limit"] == MAX_RESOURCE_BOUND


@pytest.mark.parametrize(
    "value",
    [MAX_RESOURCE_BOUND + 1, 10**10000],
    ids=["one-past-the-maximum", "unrenderable-magnitude"],
)
def test_a_bound_past_the_representable_maximum_is_rejected_at_construction(value: int) -> None:
    """A bound no query and no rejection can carry fails the deployment at startup.

    ``10**10000`` is the shape that made this a defect rather than a curiosity:
    it passes a "positive integer" test, then the first request over the bound
    raises a bare ``ValueError`` out of the constructor of the typed error the
    deployment configured the bound to produce.
    """
    with pytest.raises(ConfigurationError, match="must be at most"):
        ResourcePolicy(max_list_rows=value)


def test_a_field_declared_collection_bound_shares_the_representable_maximum() -> None:
    """The two spellings of one bound domain reject the same magnitudes."""
    validate_collection_bound(MAX_RESOURCE_BOUND, field="max_rows")
    with pytest.raises(ConfigurationError, match="must be at most"):
        validate_collection_bound(MAX_RESOURCE_BOUND + 1, field="max_rows")


# ---------------------------------------------------------------------------
# The precedence ladder
#
# Live sibling: enforcement-authority rows on ``/rp-authority/`` / ``/rp-retained/``.
# ---------------------------------------------------------------------------


def test_an_explicit_mapping_is_applied_over_the_package_defaults() -> None:
    policy = resolve_resource_policy({"max_depth": 3})
    assert policy.max_depth == 3
    assert policy.max_page_size == DEFAULT_RESOURCE_POLICY.max_page_size


def test_no_source_at_all_resolves_to_the_package_defaults() -> None:
    assert resolve_resource_policy(None) == DEFAULT_RESOURCE_POLICY


def test_an_instance_through_the_setting_slot_resolves_on_the_same_terms(
    settings: pytest_django.Settings,
) -> None:
    """The setting slot and the explicit argument are one ladder with two spellings.

    A ``ResourcePolicy`` behind ``RESOURCE_POLICY`` is the same declaration the
    ``DjangoSchema(resource_policy=...)`` argument accepts, so it is admitted.
    """
    policy = ResourcePolicy(max_depth=3)
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": policy}
    assert resolve_resource_policy(None) == policy


def test_the_setting_supplies_the_policy_when_no_argument_does(
    settings: pytest_django.Settings,
) -> None:
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": {"max_depth": 4}}
    assert resolve_resource_policy(None).max_depth == 4


def test_an_explicit_argument_outranks_the_setting(settings: pytest_django.Settings) -> None:
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": {"max_depth": 4}}
    assert resolve_resource_policy({"max_depth": 9}).max_depth == 9


def test_a_non_mapping_policy_setting_is_rejected(settings: pytest_django.Settings) -> None:
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": 12}
    with pytest.raises(ConfigurationError, match="must be a ResourcePolicy or a mapping"):
        resolve_resource_policy(None)


def test_a_non_mapping_policy_argument_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="must be a ResourcePolicy or a mapping"):
        # basedpyright: the non-mapping policy is the hostile input under test;
        # resolve_resource_policy types the parameter as ResourcePolicy | Mapping[str, object] | None
        resolve_resource_policy(12)  # pyright: ignore[reportArgumentType]


def test_an_unknown_bound_name_is_rejected_with_the_valid_vocabulary() -> None:
    """Naming the valid bounds in the message is what makes a typo self-correcting."""
    with pytest.raises(ConfigurationError, match="Unknown resource-policy bound\\(s\\): max_deth"):
        resolve_resource_policy({"max_deth": 3})


# ---------------------------------------------------------------------------
# The narrowing rule
#
# Live sibling: ``/rp-rows/`` collection ceilings.
# ---------------------------------------------------------------------------


def test_narrowing_a_bound_returns_a_tighter_policy() -> None:
    assert DEFAULT_RESOURCE_POLICY.narrowed(max_page_size=5).max_page_size == 5


def test_widening_a_bound_is_refused() -> None:
    with pytest.raises(ConfigurationError, match="may only be narrowed"):
        DEFAULT_RESOURCE_POLICY.narrowed(max_page_size=10_000)


def test_narrowing_an_unknown_bound_is_refused() -> None:
    with pytest.raises(ConfigurationError, match="no bound named 'nope'"):
        DEFAULT_RESOURCE_POLICY.narrowed(nope=1)


def test_a_deadline_narrows_from_absent_to_present_but_never_back() -> None:
    """``None`` means "no deadline", so restoring it is the widest move there is."""
    with_deadline = DEFAULT_RESOURCE_POLICY.narrowed(execution_deadline_seconds=5)
    assert with_deadline.execution_deadline_seconds == 5
    assert with_deadline.narrowed(execution_deadline_seconds=2).execution_deadline_seconds == 2
    with pytest.raises(ConfigurationError, match="may only be narrowed"):
        with_deadline.narrowed(execution_deadline_seconds=None)
    with pytest.raises(ConfigurationError, match="may only be narrowed"):
        with_deadline.narrowed(execution_deadline_seconds=6)


def test_narrowing_validates_override_domains_before_comparing_them() -> None:
    """An invalid override is a configuration error, not a comparison ``TypeError``."""
    with pytest.raises(ConfigurationError, match="max_page_size must be a positive integer"):
        DEFAULT_RESOURCE_POLICY.narrowed(max_page_size="five")


def test_effective_bound_takes_the_tighter_of_the_two_unless_trusted() -> None:
    assert effective_bound(100, None) == 100
    assert effective_bound(100, 5) == 5
    assert effective_bound(5, 100) == 5
    assert effective_bound(5, 100, trusted=True) == 100


@pytest.mark.parametrize(
    "trusted",
    [
        "false",
        "True",
        1,
        [0],
        object(),
    ],
)
def test_only_the_literal_true_widens_a_declared_bound_past_the_request_policy(
    trusted: object,
) -> None:
    """A merely TRUTHY opt-in narrows like every other caller.

    This is the one primitive whose answer may exceed the request's own
    ``ResourcePolicy``, so the value that reaches the widening branch is exactly
    ``True``. A misspelled flag - the string ``"false"``, a stray ``1``, any
    object with a truthy ``__bool__`` - takes the narrowing branch instead of
    silently raising every request's row ceiling.
    """
    # basedpyright: each truthy non-bool flag is the hostile input under test; effective_bound
    # types the parameter as bool
    assert effective_bound(5, 100, trusted=trusted) == 5  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    "trusted",
    [
        0,
        "",
        None,
        [],
    ],
)
def test_a_falsy_non_bool_opt_in_also_narrows(trusted: object) -> None:
    """The narrowing answer is the same for every non-``True`` value, truthy or not."""
    # basedpyright: each falsy non-bool flag is the hostile input under test; effective_bound
    # types the parameter as bool
    assert effective_bound(5, 100, trusted=trusted) == 5  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    "value",
    [
        "false",
        "True",
        1,
        0,
        None,
        [],
    ],
)
def test_a_trusted_flag_must_be_exactly_true_or_false(value: object) -> None:
    with pytest.raises(
        ConfigurationError,
        match="probe trusted_max_rows must be exactly True or False",
    ):
        validate_trusted_flag(value, field="probe trusted_max_rows")


@pytest.mark.parametrize("value", [True, False])
def test_an_exact_boolean_trusted_flag_is_accepted(*, value: bool) -> None:
    assert validate_trusted_flag(value, field="probe trusted_max_rows") is None


@pytest.mark.parametrize(
    "value",
    [
        0,
        -3,
        True,
        "9",
    ],
)
def test_a_field_declared_collection_bound_must_be_a_positive_integer(value: object) -> None:
    with pytest.raises(ConfigurationError, match="probe max_rows must be a positive integer"):
        validate_collection_bound(value, field="probe max_rows")


# ---------------------------------------------------------------------------
# Context threading
#
# Live sibling: ``/rp-deadline/`` and the authority mounts.
# ---------------------------------------------------------------------------


def _frozen_context() -> MappingProxyType[str, object]:
    return MappingProxyType({})


@pytest.mark.parametrize(
    ("context_factory", "writable"),
    [(SimpleNamespace, True), (dict, True), (_frozen_context, False)],
    ids=["object", "dict", "frozen"],
)
def test_the_policy_round_trips_or_fails_closed_on_every_context_shape(
    context_factory: Callable[[], object],
    *,
    writable: bool,
) -> None:
    """A frozen context cannot hold the published mirror, and still gets a BOUNDED policy.

    The policy is read after its operation ended, so the mirror is all that
    answers. That is the whole point of the fail-closed miss path: an
    unwritable context degrades to the package defaults, never to "no policy".
    """
    context = context_factory()
    policy = ResourcePolicy(max_depth=3)
    with _armed(context, policy):
        pass
    read = policy_from_info(SimpleNamespace(context=context))
    assert read == (policy if writable else DEFAULT_RESOURCE_POLICY)


def test_a_non_policy_value_under_the_key_is_ignored() -> None:
    """A consumer key collision must not become "the request has no bounds"."""
    context = {DST_RESOURCE_POLICY: "not a policy"}
    assert policy_from_info(SimpleNamespace(context=context)) == DEFAULT_RESOURCE_POLICY


# ---------------------------------------------------------------------------
# The cooperative deadline
#
# Live sibling: ``test_a_passed_deadline_stops_*`` on ``/rp-deadline/``.
# ---------------------------------------------------------------------------


def test_no_stashed_deadline_leaves_the_request_running() -> None:
    check_deadline(SimpleNamespace(context={}))


def test_a_non_numeric_stashed_deadline_leaves_the_request_running() -> None:
    check_deadline(SimpleNamespace(context={DST_RESOURCE_DEADLINE: True}))


def test_a_future_deadline_leaves_the_request_running(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    arm_resource_budget(context, ResourcePolicy(execution_deadline_seconds=60))
    check_deadline(SimpleNamespace(context=context))


def test_a_passed_deadline_reports_the_configured_seconds_not_the_clock(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """``limit`` is the bound the deployment configured, never a monotonic timestamp.

    The elapsed time and the absolute deadline are process-internal timings a
    client can neither verify nor act on, and a wire field named ``limit``
    carrying a monotonic clock reading reads as a bound nobody configured.
    """
    context: dict[str, object] = {}
    arm_resource_budget(context, ResourcePolicy(execution_deadline_seconds=2.5))
    context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.bound == "execution_deadline_seconds"
    assert caught.value.limit == 3
    assert caught.value.charged == 4
    assert "2.5 seconds" in caught.value.message


def test_a_passed_deadline_with_no_policy_behind_it_still_rejects() -> None:
    """A hand-written deadline key has no configured budget to report - and still rejects.

    Fail-closed: the deadline HAS passed, so the answer is a rejection whose
    budget is stated as unknown rather than a number the deployment never chose.
    """
    context = {DST_RESOURCE_DEADLINE: time.monotonic() - 1}
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.limit == 0
    assert "unknown" in caught.value.message


def test_a_benign_comparison_int_subclass_is_still_refused_a_policy_field() -> None:
    """Rejecting only the subclasses that DETONATE would store the quiet ones.

    A subclass whose ``<`` answers normally passes a value check and is then
    carried by the policy into every later use of the bound: ``narrowed``'s
    comparison, and the ``limit`` / ``charged`` values every
    ``ResourceLimitExceeded`` formats into its message and ``extensions``. The
    domain is therefore the built-in type, not "an int that behaves today".
    """

    class QuietInt(int):
        @override
        def __format__(self, spec: str) -> str:
            raise RuntimeError("hostile __format__ detonated")

    with pytest.raises(ConfigurationError, match="max_list_rows must be a positive integer"):
        ResourcePolicy(max_list_rows=QuietInt(2))
    with pytest.raises(ConfigurationError, match="probe max_rows must be a positive integer"):
        validate_collection_bound(QuietInt(2), field="probe max_rows")


def test_a_hostile_int_subclass_narrowing_a_bound_is_typed_rejected() -> None:
    """The narrowing comparison runs on values the policy owns, so it cannot detonate."""

    class HostileInt(int):
        @override
        def __gt__(self, other: object) -> NoReturn:
            raise RuntimeError("hostile __gt__ detonated")

        @override
        def __lt__(self, other: object) -> NoReturn:
            raise RuntimeError("hostile __lt__ detonated")

    with pytest.raises(ConfigurationError, match="max_list_rows must be a positive integer"):
        ResourcePolicy(max_list_rows=2).narrowed(max_list_rows=HostileInt(3))


def test_a_float_subclass_cannot_reach_the_derived_deadline_arithmetic(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A reflected ``__radd__`` wins over ``float``'s, so it must never be stored.

    ``begin_resource_budget`` derives the absolute deadline as
    ``time.monotonic() + seconds``. Python gives a SUBCLASS's reflected operand
    priority, so a subclass that survived construction could hand that addition
    back a ``nan`` - and a ``nan`` deadline compares false against every clock
    reading, silently disarming the budget of a policy the deployment believes
    it configured.
    """

    class PoisonFloat(float):
        @override
        def __radd__(self, other: object) -> float:
            return math.nan

    with pytest.raises(ConfigurationError, match="execution_deadline_seconds"):
        ResourcePolicy(execution_deadline_seconds=PoisonFloat(0.001))

    context: dict[str, object] = {}
    arm_resource_budget(context, ResourcePolicy(execution_deadline_seconds=0.001))
    deadline = context[DST_RESOURCE_DEADLINE]
    assert isinstance(deadline, float)
    assert math.isfinite(deadline)


@pytest.mark.parametrize(
    "written",
    [math.nan, -math.inf],
    ids=["nan", "negative-infinity"],
)
def test_a_non_finite_deadline_with_no_budget_armed_fails_closed(written: float) -> None:
    """No clock reading is earlier than these, so the request is past them."""
    context = {DST_RESOURCE_DEADLINE: written}
    with pytest.raises(ResourceLimitExceeded) as caught:
        check_deadline(SimpleNamespace(context=context))
    assert caught.value.bound == "execution_deadline_seconds"


# ---------------------------------------------------------------------------
# The armed budget
#
# Live sibling: a resolver cannot widen the next request on ``/rp-authority/``.
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _armed(context: object, policy: ResourcePolicy) -> Generator[None, None, None]:
    """Run the body with ``policy`` armed as the operation budget, as the extension does."""
    token = begin_resource_budget(context, policy)
    try:
        yield
    finally:
        end_resource_budget(token)


def test_an_armed_budget_outranks_a_policy_a_resolver_writes_over_it() -> None:
    """The published key is a mirror; replacing it does not move any bound.

    ``info.context`` belongs to the consumer, so every resolver in the request
    can write ``DST_RESOURCE_POLICY``. If that key were the authority, a
    resolver could hand itself a wider ``max_list_rows`` - and with it the
    ``offset`` ceiling ``list_field.py`` derives from the same field - for the
    rest of the operation without ever passing ``narrowed``.
    """
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(max_list_rows=5)):
        context[DST_RESOURCE_POLICY] = ResourcePolicy(max_list_rows=999)
        assert policy_from_info(info).max_list_rows == 5
        rows = bounded_rows(list(range(1000)), info)
        assert isinstance(rows, list)
        assert len(rows) == 5


def test_a_policy_written_without_arming_one_still_answers() -> None:
    """The mirror is the fallback where nothing armed a budget.

    A plain ``strawberry.Schema`` that never installed the extension leaves the
    seams on this path, answered by whatever policy the consumer published
    under the key - a context ``DjangoSchema``, which always arms a budget,
    never produces.
    """
    context: dict[str, object] = {DST_RESOURCE_POLICY: ResourcePolicy(max_list_rows=5)}
    assert policy_from_info(SimpleNamespace(context=context)).max_list_rows == 5


@pytest.mark.parametrize(
    "written",
    [None, math.nan, math.inf],
    ids=["cleared", "nan", "infinity"],
)
def test_an_armed_deadline_cannot_be_widened_or_cleared_from_the_context(
    written: float | None,
) -> None:
    """A resolver cannot buy itself more wall clock by writing the deadline key."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=0.001)):
        time.sleep(0.01)
        context[DST_RESOURCE_DEADLINE] = written
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert caught.value.bound == "execution_deadline_seconds"
    assert caught.value.limit == 1


def test_deleting_the_deadline_key_outright_does_not_disarm_the_budget() -> None:
    """Absent is not "no deadline" while a budget is armed; it is no narrowing."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=0.001)):
        time.sleep(0.01)
        del context[DST_RESOURCE_DEADLINE]
        with pytest.raises(ResourceLimitExceeded):
            check_deadline(info)


def test_a_resolver_may_shorten_its_own_request() -> None:
    """The positive control for the narrowing rule, and what the live async row rides.

    Without it the widening refusals above would still pass if the seam simply
    ignored the context key, which would take a legitimate consumer narrowing
    with it.
    """
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=30)):
        check_deadline(info)
        context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert caught.value.limit == 30


def test_a_narrowing_deadline_arrives_where_the_operation_configured_none() -> None:
    """A budget armed with no deadline still honours a consumer that sets one."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy()):
        check_deadline(info)
        context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert "unknown" in caught.value.message


class _UnorderableDeadline(float):
    """A written deadline no comparison can order against the armed one."""

    @override
    def __lt__(self, other: object) -> NoReturn:
        raise RuntimeError("hostile __lt__ detonated")


class _NarrowsThenNeverExpires(float):
    """Orders as EARLIER than the armed instant, then as one that has not passed.

    Both answers come out of the same object, which is the whole escape: it is
    admitted as a narrowing and then refuses to read as expired.
    """

    @override
    def __lt__(self, other: object) -> bool:
        return True

    @override
    def __le__(self, other: object) -> bool:
        # ``time.monotonic() >= deadline`` dispatches to the REFLECTED operand
        # first, so this is the comparison that decides whether time is up.
        return False


_HOSTILE_DEADLINE_SUBCLASSES = [_UnorderableDeadline, _NarrowsThenNeverExpires]
_HOSTILE_DEADLINE_IDS = ["unorderable", "narrows-then-never-expires"]


@pytest.mark.parametrize(
    "hostile",
    _HOSTILE_DEADLINE_SUBCLASSES,
    ids=_HOSTILE_DEADLINE_IDS,
)
def test_a_numeric_subclass_written_deadline_leaves_the_armed_ceiling_standing(
    hostile: type[float],
) -> None:
    """A value outside the deadline domain cannot be shown to narrow the budget."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=30)):
        context[DST_RESOURCE_DEADLINE] = hostile(time.monotonic() - 1)
        check_deadline(info)


@pytest.mark.parametrize(
    "hostile",
    _HOSTILE_DEADLINE_SUBCLASSES,
    ids=_HOSTILE_DEADLINE_IDS,
)
def test_a_numeric_subclass_written_deadline_cannot_outlive_an_expired_budget(
    hostile: type[float],
) -> None:
    """The escape a narrowing rule alone leaves open once the domain is not exact.

    A subclass answers BOTH comparisons this seam makes - the one deciding
    whether the written instant narrows the armed one, and the one deciding
    whether that instant has passed - so a value that presents as a narrowing on
    the way in can answer every later reading as time remaining. Admitted as the
    effective deadline it buys the rest of the operation unbounded wall clock
    off a budget that has already run out.
    """
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(execution_deadline_seconds=0.001)):
        time.sleep(0.01)
        context[DST_RESOURCE_DEADLINE] = hostile(time.monotonic() - 1)
        with pytest.raises(ResourceLimitExceeded) as caught:
            check_deadline(info)
    assert caught.value.bound == "execution_deadline_seconds"


def test_ending_a_budget_restores_the_one_it_was_opened_inside() -> None:
    """A nested execution must hand the outer operation its own budget back."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(max_list_rows=3)):
        with _armed(context, ResourcePolicy(max_list_rows=2)):
            assert policy_from_info(info).max_list_rows == 2
        assert policy_from_info(info).max_list_rows == 3
    # Outside every armed scope the seams fall back to the published mirror,
    # whose cleanup belongs to the extension's ``restored_context_keys`` rather
    # than to the budget token.
    assert policy_from_info(info).max_list_rows == 2
    context.clear()
    assert policy_from_info(info) == DEFAULT_RESOURCE_POLICY


async def test_the_armed_budget_reaches_a_sync_to_async_worker_thread() -> None:
    """The bound must not evaporate where a resolver hands work to the executor.

    ``sync_to_async`` runs its callable in a worker thread, which is exactly
    where a per-thread stash would read back empty; the ``ContextVar`` is copied
    into that thread, so the seam there enforces the operation's own policy
    rather than falling back to a context the resolver can write.
    """
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    with _armed(context, ResourcePolicy(max_list_rows=7)):
        context[DST_RESOURCE_POLICY] = ResourcePolicy(max_list_rows=999)
        rows = await sync_to_async(lambda: bounded_rows(list(range(100)), info))()
    assert isinstance(rows, list)
    assert len(rows) == 7


# ---------------------------------------------------------------------------
# ``bounded_rows``
#
# Live sibling: ``/rp-rows/`` list-field ceilings and window rejections.
# ---------------------------------------------------------------------------


def test_bounded_rows_slices_a_sequence_to_the_policy_bound(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(list(range(10)), info) == [0, 1]


def test_bounded_rows_bounds_a_non_subscriptable_iterable(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """The unsliceable shape must still be bounded, not waved through."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))

    class _Rows:
        def __iter__(self) -> Iterator[int]:
            return iter(range(10))

    assert bounded_rows(_Rows(), info) == [0, 1]


@pytest.mark.parametrize(
    "mapping_cls",
    [dict, None],
    ids=["plain-dict", "guarded-mapping-subclass"],
)
def test_bounded_rows_bounds_a_mapping_shaped_result(
    mapping_cls: type[dict[str, object]] | None,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A MAPPING-shaped result is bounded via ``islice``, never a raw ``KeyError``.

    A mapping is never subscripted: the shape is classified by exact type, so a
    mapping - and a ``dict`` subclass whose ``__getitem__`` guards its keys -
    is counted into a fresh list via ``islice``. No ``KeyError`` can escape a
    collection resolver from a subscript that never runs, which is the same
    "bound silently stops applying" failure the classification exists to
    prevent.
    """

    class _GuardedDict(dict[str, object]):
        @override
        def __getitem__(self, key: str) -> NoReturn:
            raise KeyError("guarded")

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    source = (
        _GuardedDict({"a": 1, "b": 2, "c": 3})
        if mapping_cls is None
        else mapping_cls({"a": 1, "b": 2, "c": 3})
    )
    assert bounded_rows(source, info) == ["a", "b"]


def test_bounded_rows_honours_a_trusted_widening(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(list(range(10)), info, 4, trusted=True) == [
        0,
        1,
        2,
        3,
    ]


@pytest.mark.parametrize("color", ["sync", "async"], ids=["sync", "async"])
@pytest.mark.parametrize(
    "coordinate",
    ["offset", "requested_limit"],
    ids=["offset", "requested-limit"],
)
async def test_the_exported_raw_list_bound_takes_no_client_window(
    color: str,
    coordinate: str,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A client page window is not on the exported surface, so an importer cannot widen it.

    A supplied window is a claim the bounding seam cannot check, and the one that
    matters here is the wide one: a caller asking for more rows than the request
    policy allows would get them, from the helper whose whole contract is that
    nothing a caller passes can widen its bound. The argument normalizer owns
    that check and rejects an over-ceiling value with a typed, argument-named
    error long before the private window seam sees it, so the pair stays off this
    signature.
    """
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    if color == "sync":
        with pytest.raises(TypeError):
            object_result(bounded_rows, list(range(10)), info, **{coordinate: 10})
        assert bounded_rows(list(range(10)), info) == [0, 1]
        return
    with pytest.raises(TypeError):
        object_result(bounded_rows_async, list(range(10)), info, **{coordinate: 10})
    assert await bounded_rows_async(list(range(10)), info) == [0, 1]


async def test_bounded_rows_async_closes_after_the_effective_prefix(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    class Rows:
        def __init__(self) -> None:
            self.value = 0
            self.closed = False

        def __aiter__(self) -> Rows:
            return self

        async def __anext__(self) -> int:
            value = self.value
            self.value += 1
            return value

        async def aclose(self) -> None:
            self.closed = True

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    rows = Rows()

    assert await bounded_rows_async(rows, info) == [0, 1]
    assert rows.closed is True


async def test_bounded_rows_async_raises_a_cleanup_failure_over_the_source_error() -> None:
    class BrokenRows:
        def __aiter__(self) -> BrokenRows:
            return self

        async def __anext__(self) -> NoReturn:
            raise ValueError("source failed")

        async def aclose(self) -> NoReturn:
            raise RuntimeError("cleanup failed")

    with pytest.raises(RuntimeError, match="cleanup failed") as caught:
        await bounded_rows_async(BrokenRows(), SimpleNamespace(context={}))

    assert isinstance(caught.value.__context__, ValueError)


async def test_bounded_rows_async_surfaces_cleanup_failure_without_a_source_error(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    class BrokenCleanupRows:
        def __init__(self) -> None:
            self.value = 0

        def __aiter__(self) -> BrokenCleanupRows:
            return self

        async def __anext__(self) -> int:
            self.value += 1
            return self.value

        async def aclose(self) -> NoReturn:
            raise RuntimeError("cleanup failed")

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=1))
    with pytest.raises(RuntimeError, match="cleanup failed"):
        await bounded_rows_async(BrokenCleanupRows(), info)


async def test_bounded_rows_async_hostile_aclose_lookup_surfaces_without_source_error(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A hostile aclose attribute lookup raises directly when iteration succeeded."""

    class HostileAcloseLookupRows:
        def __init__(self) -> None:
            self.value = 0

        def __aiter__(self) -> HostileAcloseLookupRows:
            return self

        async def __anext__(self) -> int:
            self.value += 1
            return self.value

        @override
        def __getattribute__(self, name: str) -> object:
            if name == "aclose":
                raise RuntimeError("hostile aclose lookup")
            return object_result(super().__getattribute__, name)

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=1))
    with pytest.raises(RuntimeError, match="hostile aclose lookup"):
        await bounded_rows_async(HostileAcloseLookupRows(), info)


def test_bounded_rows_preserves_none(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    assert bounded_rows(None, info) is None


def test_bounded_rows_checks_deadline_before_preserving_none(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(
        context,
        ResourcePolicy(max_list_rows=2, execution_deadline_seconds=1),
    )
    context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1

    with pytest.raises(ResourceLimitExceeded, match="execution_deadline_seconds"):
        bounded_rows(None, info)


async def test_bounded_rows_async_closes_a_source_the_deadline_rejects_before_any_row(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A passed deadline abandons the source, so the seam closes it on the way out.

    The clock is read after the resolver has already produced its source, so this
    rejection owns an iterator that has never been advanced and that no later
    seam will see. Zero advances and exactly one close is the whole claim; the
    consumer-visible half rides live in
    ``examples/fakeshop/test_query/test_list_field_async_api.py::test_async_deadline_rejection_closes_the_source_it_never_advanced``.
    """

    class Rows:
        def __init__(self) -> None:
            self.advances = 0
            self.closes = 0

        def __aiter__(self) -> Rows:
            return self

        async def __anext__(self) -> NoReturn:
            self.advances += 1
            raise StopAsyncIteration

        async def aclose(self) -> None:
            self.closes += 1

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(execution_deadline_seconds=1))
    context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1
    rows = Rows()

    with pytest.raises(ResourceLimitExceeded) as caught:
        await bounded_rows_async(rows, info)

    assert caught.value.extensions is not None
    assert caught.value.extensions["bound"] == "execution_deadline_seconds"
    assert rows.advances == 0
    assert rows.closes == 1


@pytest.mark.parametrize("requested_limit", [None, 0], ids=["default-window", "limit-zero"])
async def test_bounded_rows_async_closes_the_rejected_source_whatever_the_window(
    requested_limit: int | None,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """The deadline rejection closes the source, and a failing ``aclose`` raises over it.

    ``limit: 0`` is covered beside the default window because its empty-window
    short-circuit sits downstream of the clock and therefore never gets to
    perform its own close.
    """

    class BrokenCleanupRows:
        def __aiter__(self) -> BrokenCleanupRows:
            return self

        async def __anext__(self) -> NoReturn:
            raise AssertionError("a rejected source must never be advanced")

        async def aclose(self) -> NoReturn:
            raise RuntimeError("cleanup failed")

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(execution_deadline_seconds=1))
    context[DST_RESOURCE_DEADLINE] = time.monotonic() - 1

    with pytest.raises(RuntimeError, match="cleanup failed") as caught:
        await _windowed_rows_async(
            BrokenCleanupRows(),
            info,
            requested_limit=requested_limit,
        )

    rejection = caught.value.__context__
    assert isinstance(rejection, ResourceLimitExceeded)
    assert rejection.extensions is not None
    assert rejection.extensions["bound"] == "execution_deadline_seconds"


async def test_bounded_rows_async_lets_a_cancellation_during_cleanup_reach_the_task(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A cancellation arriving while ``aclose`` runs outranks the source error it interrupts."""
    closing = asyncio.Event()
    source_error = ValueError("source failed")

    class CancelledDuringCleanupRows:
        def __aiter__(self) -> CancelledDuringCleanupRows:
            return self

        async def __anext__(self) -> NoReturn:
            raise source_error

        async def aclose(self) -> None:
            closing.set()
            await asyncio.sleep(3600)

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    task = asyncio.ensure_future(bounded_rows_async(CancelledDuringCleanupRows(), info))
    await closing.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled() is True


async def test_cleanup_rejected_async_iterable_lets_a_cancelled_acquisition_through() -> None:
    """Acquisition interrupted by cancellation propagates out of the pre-iteration cleanup."""

    class CancellingAsyncIterable:
        def __aiter__(self) -> NoReturn:
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await _cleanup_rejected_async_iterable(CancellingAsyncIterable())


async def test_bounded_rows_async_preserves_none(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    assert await bounded_rows_async(None, info) is None


async def test_bounded_rows_async_exhausted_iterator_without_truncation(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """An async iterator yielding fewer items than the bound exhausts normally without early aclose."""

    class ShortRows:
        def __init__(self) -> None:
            self.items = [1, 2]
            self.closed = False

        def __aiter__(self) -> ShortRows:
            self.iter = iter(self.items)
            return self

        async def __anext__(self) -> int:
            try:
                return next(self.iter)
            except StopIteration:
                raise StopAsyncIteration from None

        async def aclose(self) -> None:
            self.closed = True

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=5))
    rows = ShortRows()
    assert await bounded_rows_async(rows, info) == [1, 2]
    assert rows.closed is False


def test_bounded_rows_slices_with_offset_and_requested_limit(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    data = list(range(10))
    assert _windowed_rows(data, info, offset=2, requested_limit=3) == [2, 3, 4]
    assert _windowed_rows(data, info, offset=None, requested_limit=3) == [0, 1, 2]
    # When requested_limit is None, the policy limit (10) bounds the window:
    assert _windowed_rows(data, info, offset=7, requested_limit=None) == [7, 8, 9]


def test_bounded_rows_slices_unsliceable_iterable_with_offset_and_requested_limit(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    class _Rows:
        def __iter__(self) -> Iterator[int]:
            return iter(range(10))

    assert _windowed_rows(_Rows(), info, offset=3, requested_limit=4) == [
        3,
        4,
        5,
        6,
    ]


def test_bounded_rows_zero_window_does_not_advance_generator(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A zero window returns an empty list without consuming or advancing unsliceable iterators."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    def _gen() -> Iterator[int]:
        yield 1
        yield 2

    g = _gen()
    assert _windowed_rows(g, info, offset=0, requested_limit=0) == []
    # Generator has NOT been advanced:
    assert next(g) == 1

    # Also test sliceable sequence with zero window
    assert _windowed_rows([1, 2, 3], info, offset=1, requested_limit=0) == []


async def test_bounded_rows_async_slices_with_offset_and_requested_limit(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    class Rows:
        def __init__(self) -> None:
            self.value = 0
            self.closed = False

        def __aiter__(self) -> Rows:
            return self

        async def __anext__(self) -> int:
            value = self.value
            self.value += 1
            return value

        async def aclose(self) -> None:
            self.closed = True

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))
    rows = Rows()

    assert await _windowed_rows_async(rows, info, offset=2, requested_limit=3) == [2, 3, 4]
    assert rows.closed is True


async def test_bounded_rows_async_zero_window_closes_without_next(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A zero window on an async iterator closes it immediately without calling __anext__."""

    class Rows:
        def __init__(self) -> None:
            self.next_called = False
            self.closed = False

        def __aiter__(self) -> Rows:
            return self

        async def __anext__(self) -> int:
            self.next_called = True
            return 1

        async def aclose(self) -> None:
            self.closed = True

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))
    rows = Rows()

    assert await _windowed_rows_async(rows, info, offset=0, requested_limit=0) == []
    assert rows.next_called is False
    assert rows.closed is True


class _MatrixUnsliceable:
    def __init__(self, items: Iterable[int]) -> None:
        self._items = items

    def __iter__(self) -> Iterator[int]:
        return iter(self._items)


@pytest.mark.parametrize(
    "source_factory",
    [list, tuple, _MatrixUnsliceable],
    ids=["list", "tuple", "unsliceable"],
)
@pytest.mark.parametrize(
    (
        "offset",
        "requested_limit",
        "declared",
        "trusted",
        "expected",
    ),
    [
        (
            None,
            None,
            None,
            False,
            list(range(10)),
        ),
        (
            None,
            None,
            5,
            False,
            list(range(5)),
        ),
        (
            3,
            None,
            None,
            False,
            list(range(3, 13)),
        ),
        (
            None,
            4,
            None,
            False,
            list(range(4)),
        ),
        (
            2,
            5,
            None,
            False,
            list(range(2, 7)),
        ),
        (
            50,
            10,
            None,
            False,
            [],
        ),
        (
            2,
            0,
            None,
            False,
            [],
        ),
        (
            2,
            None,
            15,
            True,
            list(range(2, 17)),
        ),
    ],
)
def test_bounded_rows_window_parameter_matrix(
    source_factory: Callable[[list[int]], Iterable[int]],
    offset: int | None,
    requested_limit: int | None,
    declared: int | None,
    *,
    trusted: bool,
    expected: list[int],
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """Parametrize sequences and non-subscriptable iterables across window parameters."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))
    items = list(range(30))
    source = source_factory(items)

    result = _windowed_rows(
        source,
        info,
        declared,
        offset=offset,
        requested_limit=requested_limit,
        trusted=trusted,
    )
    assert list(result) == expected

    # Positional 3-argument call still binds declared
    result_positional = bounded_rows(source_factory(list(range(20))), info, 4)
    assert list(result_positional) == list(range(4))


async def test_bounded_rows_async_positive_offset_arithmetic(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """Positive-offset arithmetic over an async iterator at helper seam (spec-050 Decision 8)."""
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    async def _gen() -> AsyncIterator[int]:
        for i in range(20):
            yield i

    res = await _windowed_rows_async(_gen(), info, offset=5, requested_limit=4)
    assert res == [
        5,
        6,
        7,
        8,
    ]


def test_bounded_rows_declined_sync_cleanup_resumable(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """Pin the declined sync cleanup contract: truncated sync generator stays suspended and resumable."""
    finally_ran = False

    def _sync_gen() -> Generator[int, None, None]:
        nonlocal finally_ran
        try:
            yield from range(10)
        finally:
            finally_ran = True

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    g = _sync_gen()
    result = _windowed_rows(g, info, offset=2, requested_limit=3)
    assert result == [2, 3, 4]
    assert finally_ran is False

    # Resumable: can continue reading subsequent values
    assert next(g) == 5
    assert finally_ran is False

    g.close()
    assert finally_ran is True


def test_bounded_rows_unsliceable_iterable_exact_consumption(
    monkeypatch: pytest.MonkeyPatch,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """Counters around __iter__/__next__ and patched islice seam verify exact consumption."""

    class CountedUnsliceable:
        def __init__(self, count: int) -> None:
            self.count = count
            self.iter_calls = 0
            self.next_calls = 0

        def __iter__(self) -> CountedUnsliceable:
            self.iter_calls += 1
            return self

        def __next__(self) -> int:
            if self.next_calls >= self.count:
                raise StopIteration
            val = self.next_calls
            self.next_calls += 1
            return val

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    islice_calls = 0
    orig_islice = islice

    def spy_islice(iterable: Iterable[object], *bounds: int | None) -> islice[object]:
        nonlocal islice_calls
        islice_calls += 1
        return orig_islice(iterable, *bounds)

    monkeypatch.setattr("django_strawberry_framework.resource_policy.islice", spy_islice)

    # requested_limit=0 must return [] without constructing islice or advancing
    c0 = CountedUnsliceable(10)
    assert _windowed_rows(c0, info, offset=2, requested_limit=0) == []
    assert c0.next_calls == 0
    assert islice_calls == 0

    # positive window consumes exactly offset + returned rows and never the next item
    c1 = CountedUnsliceable(10)
    islice_calls = 0
    res = _windowed_rows(c1, info, offset=2, requested_limit=3)
    assert res == [2, 3, 4]
    assert islice_calls == 1
    assert c1.next_calls == 5


async def test_bounded_rows_async_exact_consumption_and_cleanup_matrix(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """Async-only exact consumption, iterator acquisition, and cleanup counts matrix."""

    class TrackedAsyncIterable:
        def __init__(
            self,
            items: list[int],
            fail_at: int | None = None,
            *,
            fail_close: bool = False,
        ) -> None:
            self.items = items
            self.fail_at = fail_at
            self.fail_close = fail_close
            self.iter_acquired = 0
            self.anext_calls = 0
            self.aclose_calls = 0

        def __aiter__(self) -> TrackedAsyncIterable:
            self.iter_acquired += 1
            return self

        async def __anext__(self) -> int:
            self.anext_calls += 1
            if self.fail_at is not None and self.anext_calls == self.fail_at:
                raise ValueError("Source failure")
            if self.anext_calls > len(self.items):
                raise StopAsyncIteration
            return self.items[self.anext_calls - 1]

        async def aclose(self) -> None:
            self.aclose_calls += 1
            if self.fail_close:
                raise RuntimeError("Cleanup failure")

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    # 1. Zero limit acquires and closes once with zero advances
    src_zero = TrackedAsyncIterable([1, 2, 3])
    res_zero = await _windowed_rows_async(src_zero, info, offset=0, requested_limit=0)
    assert res_zero == []
    assert src_zero.iter_acquired == 1
    assert src_zero.anext_calls == 0
    assert src_zero.aclose_calls == 1

    # 2. Reaching exclusive stop closes
    src_stop = TrackedAsyncIterable(
        [
            1,
            2,
            3,
            4,
            5,
        ],
    )
    res_stop = await _windowed_rows_async(src_stop, info, offset=1, requested_limit=2)
    assert res_stop == [2, 3]
    assert src_stop.anext_calls == 3
    assert src_stop.aclose_calls == 1

    # 3. Source holding EXACTLY offset + limit rows (2 rows, offset=1, limit=1)
    src_exact = TrackedAsyncIterable([10, 20])
    res_exact = await _windowed_rows_async(src_exact, info, offset=1, requested_limit=1)
    assert res_exact == [20]
    assert src_exact.anext_calls == 2
    assert src_exact.aclose_calls == 1

    # 4. Source holding FEWER rows than offset + limit: naturally exhausts, does NOT close
    src_fewer = TrackedAsyncIterable([10])
    res_fewer = await _windowed_rows_async(src_fewer, info, offset=1, requested_limit=2)
    assert res_fewer == []
    assert src_fewer.anext_calls == 2
    assert src_fewer.aclose_calls == 0

    # 5. Offset overshoot that naturally exhausts does not close
    src_over = TrackedAsyncIterable([1, 2])
    res_over = await _windowed_rows_async(src_over, info, offset=5, requested_limit=2)
    assert res_over == []
    assert src_over.anext_calls == 3
    assert src_over.aclose_calls == 0

    # 6. Source failure + cleanup failure raises the cleanup failure over the source
    src_both_fail = TrackedAsyncIterable([1, 2, 3], fail_at=2, fail_close=True)
    with pytest.raises(RuntimeError, match="Cleanup failure") as exc_info:
        await _windowed_rows_async(src_both_fail, info, offset=0, requested_limit=3)
    assert isinstance(exc_info.value.__context__, ValueError)

    # 7. Cleanup-only failure raises
    src_clean_fail = TrackedAsyncIterable([1, 2, 3], fail_close=True)
    with pytest.raises(RuntimeError, match="Cleanup failure"):
        await _windowed_rows_async(src_clean_fail, info, offset=0, requested_limit=2)


def test_bounded_rows_shared_policy_seams_spy(
    monkeypatch: pytest.MonkeyPatch,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """Spy on check_deadline and effective_bound at bounded_rows seam."""
    check_deadline_calls = 0
    effective_bound_calls = 0

    orig_check = rp.check_deadline
    orig_bound = rp.effective_bound

    def spy_check(info: object) -> None:
        nonlocal check_deadline_calls
        check_deadline_calls += 1
        return orig_check(info)

    def spy_bound(policy_value: int, declared: int | None, *, trusted: bool = False) -> int:
        nonlocal effective_bound_calls
        effective_bound_calls += 1
        return orig_bound(policy_value, declared, trusted=trusted)

    monkeypatch.setattr(rp, "check_deadline", spy_check)
    monkeypatch.setattr(rp, "effective_bound", spy_bound)

    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=10))

    # Coordinate-bearing call: calls each seam once before source advance
    check_deadline_calls = 0
    effective_bound_calls = 0
    res = _windowed_rows([1, 2, 3], info, offset=1, requested_limit=1)
    assert res == [2]
    assert check_deadline_calls == 1
    assert effective_bound_calls == 1

    # Relation-list caller with no coordinates: calls each seam once and retains old prefix bound
    check_deadline_calls = 0
    effective_bound_calls = 0
    res_no_coords = bounded_rows(list(range(20)), info)
    assert res_no_coords == list(range(10))
    assert check_deadline_calls == 1
    assert effective_bound_calls == 1


# ---------------------------------------------------------------------------
# The row source the bound is applied to
#
# Live sibling: the relation rows on ``/rp-hostile-relation/``.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_zero_width_window_on_a_queryset_subclass_returns_no_rows(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A zero-width window on a project queryset class is an empty slice of it."""
    seed_data(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=4))
    source = _ProjectQuerySet[Category](model=Category)
    rows = _windowed_rows(source, info, offset=1, requested_limit=0)
    assert list(rows) == []


@pytest.mark.django_db(transaction=True)
async def test_a_zero_width_window_on_a_queryset_subclass_returns_no_rows_when_awaited(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """The awaited window seam delegates here, so the zero-width arm is the same one."""
    await sync_to_async(seed_data)(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=4))
    source = _ProjectQuerySet[Category](model=Category)
    rows = await _windowed_rows_async(source, info, offset=1, requested_limit=0)
    assert list(rows) == []


@pytest.mark.django_db
def test_an_exact_queryset_still_carries_the_row_bound_into_sql(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """The common shape pays nothing and keeps the ``LIMIT`` the bound exists to push."""
    seed_data(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    source = Category.objects.all()
    rows = bounded_rows(source, info)
    assert type(rows) is QuerySet
    assert rows.query.high_mark == 2
    assert len(list(rows)) == 2


@pytest.mark.django_db
def test_a_project_queryset_class_keeps_the_row_bound_in_sql(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A project queryset class is sliced as itself, so the bound stays a ``LIMIT``.

    Counting it into a Python list would restore the row ceiling and lose the
    database one, which is the guarantee this seam is for.
    """
    seed_data(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))

    class _CategoryQuerySet(QuerySet[Category]):
        """A project's own queryset class for ``Category``."""

    rows = bounded_rows(_CategoryQuerySet(model=Category), info)
    assert type(rows) is _CategoryQuerySet
    assert rows.query.high_mark == 2
    assert len(list(rows)) == 2


@pytest.mark.django_db
def test_rows_a_source_already_fetched_are_read_from_the_frameworks_own_slot() -> None:
    """A prefetch cache's rows come out of Django's slot on an exact queryset."""
    seed_data(3)
    warm = Category.objects.all()
    list(warm)
    assert materialized_rows(warm) == list(warm)


def _relation_source(manager: Manager[Item], queryset: _QuerySetT) -> _QuerySetT:
    """Django's own ``_apply_rel_filters``: ``queryset`` carrying the relation's pending predicate."""
    assert has_apply_rel_filters(manager)
    source = manager._apply_rel_filters(queryset)
    assert isinstance(source, type(queryset))
    return source


class _ProjectQuerySet(QuerySet[_M]):
    """A project's own queryset class with no overrides.

    The shape ``QuerySet.as_manager()`` and ``Manager.from_queryset(...)`` put
    behind a model's default manager, and the one every relation built from such
    a manager hands the raw-list seam.
    """


def _evaluated(queryset_cls: type[QuerySet[Category]]) -> QuerySet[Category]:
    """A source of ``queryset_cls`` that has already fetched its rows."""
    source = queryset_cls(model=Category)
    list(source)
    return source


def _held_rows(source: QuerySet[Category]) -> list[object]:
    """The list a source holds, read from its instance state."""
    held = instance_state(source)["_result_cache"]
    assert is_object_list(held), held
    return held


@pytest.mark.django_db
def test_an_evaluated_exact_queryset_is_windowed_from_the_rows_it_holds(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A source that arrives evaluated is windowed from its own rows, not re-queried."""
    seed_data(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    source = _evaluated(QuerySet)
    held = _held_rows(source)

    with django_assert_num_queries(0):
        rows = bounded_rows(source, info)

    assert type(rows) is list
    assert list(rows) == held[:2]
    assert [row is held[index] for index, row in enumerate(rows)] == [True, True]


@pytest.mark.django_db
def test_an_evaluated_project_queryset_class_is_windowed_from_the_rows_it_holds(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A project queryset class that already fetched its rows is windowed from them.

    ``QuerySet.__getitem__`` reads a populated ``_result_cache``, so the window
    costs no second query.
    """
    seed_data(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    source = _evaluated(_ProjectQuerySet)
    held = _held_rows(source)

    with django_assert_num_queries(0):
        rows = bounded_rows(source, info)

    assert materialized_rows(source) is held
    assert type(rows) is list
    assert list(rows) == held[:2]
    assert [row is held[index] for index, row in enumerate(rows)] == [True, True]


@pytest.mark.django_db
def test_a_coordinate_window_over_an_evaluated_project_queryset_class_reads_carried_rows(
    django_assert_num_queries: pytest_django.DjangoAssertNumQueries,
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """The offset window is taken over the held rows, so it too costs nothing."""
    seed_data(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=4))
    source = _evaluated(_ProjectQuerySet)
    held = _held_rows(source)

    with django_assert_num_queries(0):
        rows = _windowed_rows(source, info, offset=1, requested_limit=2)

    assert list(rows) == held[1:3]
    # Identity, not equality: a window that re-queried would answer with equal
    # rows built from a second fetch, which no count taken around a lazily
    # sliced queryset can tell apart from this one.
    assert [row is held[index + 1] for index, row in enumerate(rows)] == [True, True]


@pytest.mark.django_db(transaction=True)
async def test_an_evaluated_exact_queryset_is_windowed_from_its_own_rows_when_awaited(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """The awaited seam reaches the same window, so it reads the same held rows.

    A query count is not the instrument here: the awaited call runs on the event
    loop thread while any ORM work would run on a ``sync_to_async`` worker
    thread, and a capture bound to the calling thread reads empty either way.
    Row IDENTITY answers the same question without that ambiguity - a second
    fetch cannot return the objects the source already holds.
    """
    await sync_to_async(seed_data)(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    source = await sync_to_async(_evaluated)(QuerySet)
    held = _held_rows(source)

    rows = await bounded_rows_async(source, info)

    assert type(rows) is list
    assert list(rows) == held[:2]
    assert [row is held[index] for index, row in enumerate(rows)] == [True, True]


@pytest.mark.django_db(transaction=True)
async def test_an_evaluated_project_queryset_class_is_windowed_from_its_own_rows_when_awaited(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """The awaited seam takes the source's held rows rather than a second fetch."""
    await sync_to_async(seed_data)(6)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    source = await sync_to_async(_evaluated)(_ProjectQuerySet)
    held = _held_rows(source)

    rows = await bounded_rows_async(source, info)

    assert type(rows) is list
    assert list(rows) == held[:2]
    assert [row is held[index] for index, row in enumerate(rows)] == [True, True]


@pytest.mark.django_db
def test_a_relation_source_from_a_project_queryset_class_keeps_its_relation_predicate(
    arm_resource_budget: Callable[[object, ResourcePolicy], None],
) -> None:
    """A relation's pending predicate reaches the window's SQL, whatever class carries it.

    Django's own ``_apply_rel_filters`` builds the source, so the pending state
    is what Django writes rather than a hand-planted tuple. Django's ``query``
    getter bakes it, so the window is the relation's own rows.
    """
    seed_data(3)
    context: dict[str, object] = {}
    info = SimpleNamespace(context=context)
    arm_resource_budget(context, ResourcePolicy(max_list_rows=2))
    parent = Category.objects.order_by("pk").first()
    assert parent is not None
    source = _relation_source(parent.items, _ProjectQuerySet[Item](model=Item))
    assert type(source) is _ProjectQuerySet
    assert object.__getattribute__(source, "__dict__")["_deferred_filter"] is not None

    compiler = object_result(source.query.get_compiler, using="default")
    compiled = call_method(compiler, "as_sql")
    assert is_exact_pair(compiled), compiled
    sql_str, params = compiled
    assert "category" in require_instance(sql_str, str).lower()
    assert saved_pk(parent) in require(params, is_list_or_tuple)

    rows = bounded_rows(source, info)
    assert list(rows) == list(parent.items.all())[:2]
    assert {row.category_id for row in rows} == {saved_pk(parent)}


# ---------------------------------------------------------------------------
# The pre-parse text scan
#
# Live sibling: token / depth rows on ``/rp-tokens/`` and ``/rp-depth/``.
# ---------------------------------------------------------------------------


def test_an_absent_document_charges_nothing() -> None:
    scan_document_text(DEFAULT_RESOURCE_POLICY, None)
    scan_document_text(DEFAULT_RESOURCE_POLICY, "")


@pytest.mark.parametrize(
    "hostile",
    [
        123,
        b"{ a }",
        ["{ a }"],
        {"query": "{ a }"},
        3.5,
        object(),
        True,
    ],
    ids=[
        "int",
        "bytes",
        "list",
        "dict",
        "float",
        "object",
        "bool",
    ],
)
def test_a_non_string_query_is_declined_not_scanned(hostile: object) -> None:
    """A non-string query is declined, never handed to the lexer.

    Handing a truthy non-string to the lexer raised a raw ``TypeError`` /
    ``AttributeError`` / ``KeyError`` from inside graphql-core. The HTTP
    transports type-check the query before the extension runs, but the
    WebSocket path does not, so the decline is the scanner's own
    contract: a value that is not text carries no tokens to charge.
    """
    # basedpyright: each non-string query is the hostile input under test; scan_document_text
    # types the parameter as str | None
    scan_document_text(DEFAULT_RESOURCE_POLICY, hostile)  # pyright: ignore[reportArgumentType]


def test_structural_delimiter_pairs_derivation() -> None:
    """_OPEN_TOKEN_KINDS and _CLOSE_TOKEN_KINDS derive from _STRUCTURAL_DELIMITER_PAIRS."""
    assert _STRUCTURAL_DELIMITER_PAIRS == (
        (TokenKind.BRACE_L, TokenKind.BRACE_R),
        (TokenKind.PAREN_L, TokenKind.PAREN_R),
        (TokenKind.BRACKET_L, TokenKind.BRACKET_R),
    )
    assert (
        frozenset(open_kind for open_kind, _ in _STRUCTURAL_DELIMITER_PAIRS) == _OPEN_TOKEN_KINDS
    )
    assert (
        frozenset(close_kind for _, close_kind in _STRUCTURAL_DELIMITER_PAIRS)
        == _CLOSE_TOKEN_KINDS
    )
    assert not (_OPEN_TOKEN_KINDS & _CLOSE_TOKEN_KINDS)


@pytest.mark.parametrize(
    ("doc", "limit", "should_exceed"),
    [
        ("{ a { b { c } } }", 2, True),
        ("{ a { b { c } } }", 3, False),
        ("{ foo(arg: { bar: 1 }) }", 2, True),
        ("{ foo(arg: { bar: 1 }) }", 3, False),
        ("{ foo(filter: [1, 2]) }", 2, True),
        ("{ foo(filter: [1, 2]) }", 3, False),
    ],
    ids=[
        "nested_braces_exceeds",
        "nested_braces_passes",
        "nested_parens_and_braces_exceeds",
        "nested_parens_and_braces_passes",
        "nested_brackets_exceeds",
        "nested_brackets_passes",
    ],
)
def test_pre_parse_scan_depth_across_delimiter_families(
    doc: str,
    limit: int,
    *,
    should_exceed: bool,
) -> None:
    """The pre-parse scan tracks depth across braces, parens, and brackets."""
    policy = ResourcePolicy(max_depth=limit)
    if should_exceed:
        with pytest.raises(ResourceLimitExceeded) as caught:
            scan_document_text(policy, doc)
        assert caught.value.bound == "max_depth"
    else:
        scan_document_text(policy, doc)


# ---------------------------------------------------------------------------
# Walker degenerate inputs
#
# Live sibling: named-operation, malformed-document, and introspection rows in
# examples/fakeshop/test_query/test_resource_policy_api.py. What remains is
# inputs a valid HTTP JSON body cannot produce.
# ---------------------------------------------------------------------------


@strawberry.type
class _NotAConnection:
    """A type that exposes a field called ``edges`` and is not connection-shaped.

    No ``node`` / ``cursor`` edge type behind it, so the collection-cost
    exemption a real connection's ``edges`` earns must not apply to this list.
    """

    edges: list[str]


@strawberry.type
class _ScalarEdges:
    """``edges`` that is not even a list - the other half of the shape test."""

    edges: str


@strawberry.type
class _ProbeEdge:
    node: str
    cursor: str


@strawberry.type
class _ProbeConnection:
    """The whole edge shape ``_is_connection_type`` matches on."""

    edges: list[_ProbeEdge]


@strawberry.type
class _Probe:
    """A minimal schema whose only job is to give the walker real types."""

    fauxes: list[_NotAConnection]
    scalar_edges: _ScalarEdges

    @strawberry.field
    def page(self, first: int | None = None) -> _ProbeConnection:
        del first  # Strawberry derives the probe's argument from it; the body never runs
        return _ProbeConnection(edges=[])

    @strawberry.field
    def echo(self, text: str = "x", tags: list[str] | None = None) -> str:
        del tags  # Strawberry derives the probe's argument from it; the body never runs
        return text

    @strawberry.field
    def nested(self, tags: list[list[str]] | None = None) -> str:
        return tags[0][0] if tags else ""

    @strawberry.field
    # basedpyright: Strawberry reads this annotation as the argument's GraphQL type; JSON | None
    # would make the probe's argument nullable and change its schema
    def blob(self, payload: strawberry.scalars.JSON = None) -> str:  # pyright: ignore[reportArgumentType]
        del payload  # Strawberry derives the probe's argument from it; the body never runs
        return "ok"

    @strawberry.field
    def stash(self, document: Upload) -> str:
        del document  # Strawberry derives the probe's argument from it; the body never runs
        return "ok"


_PROBE_SCHEMA = strawberry.Schema(query=_Probe)


@strawberry.type
class _WriteProbe:
    """A plain ``strawberry.Schema`` mutation root - no package bind specs anywhere.

    The ID-scalar fallback in ``_charge_list_family`` exists for exactly this
    schema shape: a mutation the package did not generate carries no
    ``_input_field_specs`` map, so an id list is classified by its scalar name.
    """

    @strawberry.mutation
    def tag(self, tags: list[strawberry.ID] | None = None) -> str:
        del tags  # Strawberry derives the probe's argument from it; the body never runs
        return "ok"


_PROBE_WRITE_SCHEMA = strawberry.Schema(query=_Probe, mutation=_WriteProbe)


def _charge(
    document: str,
    variables: Mapping[str, object] | None = None,
    operation_name: str | None = None,
    policy: ResourcePolicy | None = None,
) -> None:
    charge_document(
        policy or DEFAULT_RESOURCE_POLICY,
        _PROBE_SCHEMA._schema,
        parse(document),
        variables or {},
        operation_name,
    )


def _charge_write(
    document: str,
    variables: Mapping[str, object] | None = None,
    policy: ResourcePolicy | None = None,
) -> None:
    """Charge a mutation document against the plain-schema probe (no bind specs)."""
    charge_document(
        policy or DEFAULT_RESOURCE_POLICY,
        _PROBE_WRITE_SCHEMA._schema,
        parse(document),
        variables or {},
        None,
    )


def test_an_id_list_in_a_plain_mutation_charges_the_relation_fallback() -> None:
    """The ID-scalar fallback keeps charging relation ids without bind specs.

    The spec rule only ever ADDS a classification signal for writes the
    package generated; a plain ``strawberry.Schema`` mutation has none, and its
    ``[ID]`` list must keep charging ``max_relation_ids_per_mutation`` by name -
    the same contract the GlobalID twins pin live over the generated write.
    """
    _charge_write("mutation T($tags: [ID!]) { tag(tags: $tags) }", {"tags": ["a", "b"]})
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge_write(
            "mutation T($tags: [ID!]) { tag(tags: $tags) }",
            {"tags": ["x", "y"]},
            policy=ResourcePolicy(max_relation_ids_per_mutation=1),
        )
    assert caught.value.bound == "max_relation_ids_per_mutation"
    assert caught.value.charged == 2


def test_an_absent_optional_argument_value_is_charged_as_nothing() -> None:
    """A ``None`` argument value (an omitted optional variable) charges no leaves."""
    _charge("query T($t: [String!]) { echo(tags: $t) }", {"t": None})


def test_an_operation_kind_the_schema_does_not_define_is_skipped() -> None:
    """A mutation against a query-only schema has no root type to walk.

    Live sibling: named-operation rows on ``/rp-shape/`` (fakeshop defines both
    root types, so this skip is not a request a consumer can issue).
    """
    _charge("mutation { echo }")


def test_an_unknown_fragment_spread_is_skipped() -> None:
    """Validation would reject it; the walker must not crash on a missing fragment.

    Live sibling: fragment-expansion charging on ``/rp-shape/``.
    """
    _charge("{ ...Missing }")


def test_a_cyclic_fragment_set_terminates() -> None:
    """Validation rejects a fragment cycle; the walker must not depend on that.

    A schema that disabled validation would hand this document straight to the
    walk, and a walk that followed the cycle would never return.
    """
    _charge("{ ...A } fragment A on Query { ...B } fragment B on Query { ...A }")


def test_an_inline_fragment_without_a_type_condition_keeps_its_parent() -> None:
    _charge("{ ... { echo } }")


def test_an_inline_fragment_names_its_own_type_condition() -> None:
    _charge("{ ... on Query { echo } }")


def test_argument_less_directives_are_read_once_however_often_their_fragment_expands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A directive with no argument is read once, and only a directive with arguments is revisited.

    ``F`` is spread fifty times. Its definition and its field each carry
    argument-less directives around one ``@include`` value: the value is charged
    at every expansion (pinned live on ``/rp-values/``), while the argument-less
    directives charge nothing, so reading them again at each expansion is walk
    work no budget counts, multiplied by the spreads. The verdict is the same
    either way, which is why no request can observe it: the reads of each bare
    directive's arguments and the directives the walk resolves are what say the
    work is not repeated.
    """
    spreads = " ".join("...F" for _ in range(50))
    document = parse(
        f"{{ {spreads} }} fragment F on Query @a @include(if: true) @b {{ echo @c @d }}",
    )
    reads: list[str] = []

    def read_arguments(directive: DirectiveNode) -> object:
        reads.append(directive.name.value)
        return instance_state(directive)["arguments"]

    resolved: list[str] = []
    resolve = GraphQLSchema.get_directive

    def spy_get_directive(schema: GraphQLSchema, name: str) -> GraphQLDirective | None:
        resolved.append(name)
        return resolve(schema, name)

    monkeypatch.setattr(DirectiveNode, "arguments", property(read_arguments))
    monkeypatch.setattr(GraphQLSchema, "get_directive", spy_get_directive)
    charge_document(DEFAULT_RESOURCE_POLICY, _PROBE_SCHEMA._schema, document)
    assert {name: reads.count(name) for name in "abcd"} == dict.fromkeys("abcd", 1)
    assert resolved == ["include"] * 50


def test_an_untyped_container_inside_a_scalar_is_still_charged() -> None:
    """A JSON-shaped scalar's contents are nodes too, or they are a free payload."""
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query B($p: JSON!) { blob(payload: $p) }",
            {"p": {"a": [1, 2, 3], "b": {"c": 4}}},
            policy=ResourcePolicy(max_input_nodes=3),
        )
    assert caught.value.bound == "max_input_nodes"


def test_a_scalar_where_a_list_is_declared_is_charged_as_one_item() -> None:
    """GraphQL coerces a bare value into a single-item list; the charge follows."""
    _charge("query T($t: [String!]) { echo(tags: $t) }", {"t": "solo"})


def test_scalar_list_coercion_charges_synthetic_lists_as_input_nodes() -> None:
    """The coerced one-item list itself counts toward the input-node budget."""
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($t: [String!]) { echo(tags: $t) }",
            {"t": "solo"},
            policy=ResourcePolicy(max_input_nodes=1),
        )
    assert caught.value.bound == "max_input_nodes"


def test_scalar_list_coercion_charges_each_declared_list_level() -> None:
    """A bare variable is coerced to one item at every declared list level."""
    document = "query T($t: [[String!]]) { nested(tags: $t) }"
    _charge(document, {"t": "solo"}, policy=ResourcePolicy(max_value_depth=2))
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"t": "solo"}, policy=ResourcePolicy(max_value_depth=1))
    assert caught.value.bound == "max_value_depth"


def test_a_container_referenced_twice_is_charged_per_reference() -> None:
    """A charge fires per REFERENCE; only a cycle back onto an ancestor is skipped.

    Two references to one list are two lists' worth of work for the coercer, the
    walkers, and the ORM. The shape this pins is the one a request can actually
    build over the wire: one variable spliced into two arguments resolves to the
    same Python object both times.

    ``{"one": shared, "two": shared}`` is 7 nodes charged per reference (the
    mapping, then 1 + 2 for each of the two list references) and would be 5 if
    the second reference were skipped, so a 6-node budget separates the two
    contracts.
    """
    shared = ["a", "b"]
    payload = {"one": shared, "two": shared}
    document = "query B($p: JSON!) { blob(payload: $p) }"
    _charge(document, {"p": payload}, policy=ResourcePolicy(max_input_nodes=7))
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"p": payload}, policy=ResourcePolicy(max_input_nodes=6))
    assert caught.value.bound == "max_input_nodes"


def test_two_distinct_but_equal_containers_are_both_charged() -> None:
    """Two equal containers are two containers, each charged."""
    payload = {"one": ["a"], "two": ["a"]}
    with pytest.raises(ResourceLimitExceeded):
        _charge(
            "query B($p: JSON!) { blob(payload: $p) }",
            {"p": payload},
            policy=ResourcePolicy(max_input_nodes=4),
        )


class _AmountNoBoundCanExceed(int):
    """An amount no bound can ever be over, by whichever route it is charged.

    Its ``__gt__`` answers the comparison a rejection is decided by; its
    reflected ``__radd__`` and ``__rmul__`` - which take priority over
    ``int``'s own - decide what a running total and a multiplied bound become
    the moment one of these reaches them, and ``nan`` is over no limit ever
    again.
    """

    @override
    def __gt__(self, other: object) -> bool:
        return False

    @override
    # basedpyright: deliberately a NaN-producing int, the page bound the package must not own
    def __radd__(self, other: object) -> float:  # pyright: ignore[reportIncompatibleMethodOverride]
        return math.nan

    @override
    # basedpyright: deliberately a NaN-producing int, the page bound the package must not own
    def __rmul__(self, other: object) -> float:  # pyright: ignore[reportIncompatibleMethodOverride]
        return math.nan


def test_a_page_size_variable_outside_the_integers_narrows_nothing() -> None:
    """A page bound is a charge, so the value that sets it must be one the package owns.

    ``first`` narrows the rows a connection selection is charged. Supplied as an
    ``int`` SUBCLASS it answers the clamp that would cap it at the page ceiling
    AND, once charged, the reflected addition the running collection cost is
    accumulated through - a page bound that is over every ceiling and a total
    that is under every one. Out of the domain, it narrows nothing and the
    selection is charged the policy's own ceiling.
    """
    document = "query P($n: Int) { page(first: $n) { edges { node } } }"
    policy = ResourcePolicy(max_page_size=50, max_collection_cost=49)
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(document, {"n": _AmountNoBoundCanExceed(10**9)}, policy=policy)
    assert caught.value.bound == "max_collection_cost"
    assert caught.value.charged == 50
    _charge(document, {"n": 10}, policy=policy)


def test_a_type_that_merely_has_an_edges_field_is_not_a_connection() -> None:
    """The connection exemption makes a list FREE, so it must match the edge shape.

    A connection's own ``edges`` is exempt from collection cost because the
    connection field above it already charged the page. Granting that exemption
    on the field NAME alone hands a free unbounded list to any type that happens
    to expose one called ``edges``: a list of such types charges 100 for the
    outer list and then multiplies it by the inner list's own 100, which is the
    10,100 asserted here and would be a bare 100 if the exemption applied.

    Live sibling: nested collection-cost charging on ``/rp-cost/`` (real
    connections only).
    """
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge("{ fauxes { edges } }", policy=ResourcePolicy(max_collection_cost=5_000))
    assert caught.value.bound == "max_collection_cost"
    assert caught.value.charged == 10_100


def test_a_type_whose_edges_field_is_not_a_list_is_not_a_connection() -> None:
    """A connection charges a full page; a type that merely borrowed the name must not.

    Charged as a connection, ``scalarEdges`` would cost a whole page against the
    collection budget for selecting one string.
    """
    _charge("{ scalarEdges { edges } }", policy=ResourcePolicy(max_collection_cost=50))


# ---------------------------------------------------------------------------
# Values the walk measures
#
# Live sibling: ordinary JSON containers on ``/rp-values/``.
# ---------------------------------------------------------------------------


def test_an_ordinary_container_charges_its_own_width() -> None:
    """A ``list`` or ``dict`` is charged its real width, even far past the bound."""
    _charge(
        "query T($p: JSON) { blob(payload: $p) }",
        {"p": [1, 2]},
        policy=ResourcePolicy(max_container_width=2),
    )
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": {"a": 1, "b": 2, "c": 3}},
            policy=ResourcePolicy(max_container_width=2),
        )
    assert caught.value.charged == 3


def test_a_text_leaf_is_measured_by_the_built_in_encoding_not_its_own() -> None:
    """``max_scalar_bytes`` measures the text, not what the text says about itself.

    A ``str`` SUBCLASS carries its own ``encode``, and the byte count the bound
    compares against was that method's return value.

    Live sibling: ``test_a_scalar_larger_than_the_byte_bound_is_rejected``.
    """

    class _LyingEncode(str):
        @override
        def encode(self, *args: object, **kwargs: object) -> bytes:
            return b"x"

    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query T($p: JSON) { blob(payload: $p) }",
            {"p": _LyingEncode("y" * 100)},
            policy=ResourcePolicy(max_scalar_bytes=1),
        )
    assert caught.value.bound == "max_scalar_bytes"
    assert caught.value.charged == 100


# ---------------------------------------------------------------------------
# The extension's own wiring
#
# Live sibling: admission / authority / validation-cache rows on the ``/rp-*``
# mounts. What remains is hook identity and construction-time installation.
# ---------------------------------------------------------------------------


def test_an_explicit_policy_outranks_the_schemas() -> None:
    extension = DjangoResourcePolicyExtension(policy=ResourcePolicy(max_depth=2))
    extension.execution_context = make_execution_context()
    assert extension._resolved_policy().max_depth == 2


def test_a_schema_without_a_policy_falls_back_to_the_package_defaults() -> None:
    """A plain ``strawberry.Schema`` carries no ``resource_policy`` attribute."""
    extension = DjangoResourcePolicyExtension()
    extension.execution_context = make_execution_context()
    assert extension._resolved_policy() == DEFAULT_RESOURCE_POLICY


def test_an_operation_with_no_parsed_document_charges_no_document_budget() -> None:
    """The admission hook runs even when the parse produced nothing to walk."""
    extension = DjangoResourcePolicyExtension()
    extension.execution_context = make_execution_context()  # unparsed: no graphql_document
    hook = extension.on_parse()
    next(hook)
    with pytest.raises(StopIteration):
        next(hook)


def test_a_verdict_recorded_outside_an_operation_is_not_kept() -> None:
    """There is no operation for it to belong to, and no later one inherits it."""
    record_admission_rejection(
        ResourceLimitExceeded("max_container_width", 1, 2, "a list argument is too wide"),
    )
    assert admission_rejection() is None
    with _armed({}, DEFAULT_RESOURCE_POLICY):
        assert admission_rejection() is None


def test_an_operation_the_budget_rejected_does_not_begin_executing() -> None:
    """A rejection means nothing runs, restated where running starts.

    Publishing is what makes validation stand down, and every seam that reads a
    pre-execution error stops there - unless a validation hook set up after the
    extension erased it, which a plain ``strawberry.Schema`` with a later
    validation cache does. The hook execution begins from is entered only when an
    operation is about to run, so it is where that contradiction is closed.
    What it reads is the recorded verdict rather than the published error,
    because the published error is a field anything in the extension chain
    writes.
    """
    extension = DjangoResourcePolicyExtension()
    rejection = ResourceLimitExceeded("max_container_width", 1, 2, "a list argument is too wide")

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        record_admission_rejection(rejection)
        with pytest.raises(ResourceLimitExceeded) as caught:
            next(extension.on_execute())

    assert caught.value is rejection


def test_an_operation_the_budget_admitted_executes() -> None:
    """The other verdict: an admitted operation passes the same hook untouched."""
    extension = DjangoResourcePolicyExtension()

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        hook = extension.on_execute()
        next(hook)
        with pytest.raises(StopIteration):
            next(hook)


class _StreamWitness(SchemaExtension):
    """Record that the executing stage was entered, from ahead of the package's entries."""

    entered: list[str] = []

    @override
    def on_execute(self) -> Iterator[None]:
        _StreamWitness.entered.append(self.execution_context.query or "")
        yield


@strawberry.type
class _StreamedQuery:
    """One field, so a streaming schema has a query type to be built with."""

    @strawberry.field
    def hello(self) -> str:
        return "ok"


@strawberry.type
class _StreamedSubscription:
    """One subscription whose events only arrive if the operation was admitted."""

    @strawberry.subscription
    async def ticks(self) -> AsyncGenerator[int, None]:
        yield 1


@pytest.mark.parametrize(
    "extensions",
    [[], [ValidationCache]],
    ids=["no-cache", "with-a-validation-cache"],
)
@pytest.mark.parametrize("verdict", ["rejected", "admitted"])
async def test_the_streaming_path_carries_the_same_admission_verdict(
    extensions: list[type[SchemaExtension]],
    verdict: str,
) -> None:
    """One verdict per request, on the entry point that yields frames rather than a body.

    A streaming transport drives the schema's own generator, so a refusal that
    raised would reach it as an exception with no frame at all - which is why
    admission publishes. The cache row is here because the composed path has to
    answer the same way: what the client receives is one frame carrying the
    typed rejection, and no event from the subscription behind it.
    """
    schema = DjangoSchema(
        query=_StreamedQuery,
        subscription=_StreamedSubscription,
        resource_policy=ResourcePolicy(max_aliases=1),
        extensions=[_StreamWitness, *extensions],
    )
    query = (
        "subscription { a: ticks b: ticks }"
        if verdict == "rejected"
        else "subscription { a: ticks }"
    )

    _StreamWitness.entered.clear()
    frames = [frame async for frame in await schema.subscribe(query)]

    assert len(frames) == 1
    if verdict == "rejected":
        assert frames[0].data is None
        assert frames[0].errors is not None
        assert len(frames[0].errors) == 1
        assert frames[0].errors[0].extensions is not None
        assert frames[0].errors[0].extensions["bound"] == "max_aliases"
        assert _StreamWitness.entered == []
    else:
        assert frames[0].errors is None
        assert frames[0].data == {"a": 1}
        assert _StreamWitness.entered == [query]


@pytest.mark.parametrize(
    ("deadline", "spend_before_frame", "rejected"),
    [
        (60, 1, [False, True, True]),
        (60, None, [False, False, False]),
        (None, None, [False, False, False]),
    ],
    ids=["deadline-spent", "deadline-unspent", "no-deadline"],
)
@pytest.mark.usefixtures("isolate_global_registry")
@pytest.mark.django_db(transaction=True)
async def test_a_budget_spent_between_frames_fails_every_later_frames_relation_hop(
    deadline: int | None,
    spend_before_frame: int | None,
    rejected: list[bool],
) -> None:
    """Every frame's relation hop checks the budget, so once it is spent every later hop rejects.

    The first frame is delivered whole. The resolver then writes the one thing a
    resolver may write to the budget, an earlier instant, and every later frame
    answers its forward FK hop with the typed rejection, even though the category
    row was loaded with the item. A stream whose deadline is not narrowed, and a
    stream whose policy configures no deadline at all, deliver every frame whole.
    """

    class CategoryT(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemT(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    finalize_django_types()
    del CategoryT

    async def _items(info: Info[object, object]) -> AsyncGenerator[Item, None]:
        for index in range(3):
            if index == spend_before_frame:
                stash_on_context(info.context, DST_RESOURCE_DEADLINE, time.monotonic() - 1.0)
            yield await sync_to_async(
                lambda: Item.objects.select_related("category").order_by("id")[0],
            )()

    @strawberry.type
    class _Frames:
        items: AsyncGenerator[Item, None] = strawberry.subscription(
            resolver=_items,
            graphql_type=ItemT,
        )

    await sync_to_async(seed_data)(1)
    item = await sync_to_async(
        lambda: Item.objects.select_related("category").order_by("id")[0],
    )()
    whole = {"items": {"name": item.name, "category": {"name": item.category.name}}}
    schema = DjangoSchema(
        query=_StreamedQuery,
        subscription=_Frames,
        resource_policy=ResourcePolicy(execution_deadline_seconds=deadline),
    )
    frames = [
        frame
        async for frame in await schema.subscribe(
            "subscription { items { name category { name } } }",
            context_value={},
        )
    ]
    assert [frame.errors is not None for frame in frames] == rejected
    for frame, was_rejected in zip(frames, rejected, strict=True):
        if was_rejected:
            assert frame.data is None
            assert frame.errors is not None
            assert len(frame.errors) == 1
            assert frame.errors[0].path == ["items", "category"]
            assert frame.errors[0].extensions is not None
            assert frame.errors[0].extensions["bound"] == "execution_deadline_seconds"
        else:
            assert frame.data == whole


def test_a_rejection_an_extension_erased_is_restated_before_execution_is_decided() -> None:
    """The published error is a mutable field; the verdict is what survives it.

    A validation extension that runs its own pass assigns the result over
    whatever is published - Strawberry's ``ValidationCache`` does exactly that.
    Upstream decides whether to execute from INSIDE the validation stage, so the
    restatement has to happen while the hook is setting up, and the enforcing
    extension, behind every consumer entry, makes it.
    """
    extension = DjangoResourcePolicyExtension()
    rejection = ResourceLimitExceeded("max_aliases", 1, 2, "too many aliases")
    extension.execution_context = make_execution_context(pre_execution_errors=[])

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        record_admission_rejection(rejection)
        hook = extension.on_validate()
        next(hook)

        assert extension.execution_context.pre_execution_errors == [rejection]
        with pytest.raises(StopIteration):
            next(hook)


def test_an_admitted_operation_keeps_whatever_validation_published() -> None:
    """The restatement is a restatement, not an unconditional write."""
    extension = DjangoResourcePolicyExtension()
    validation_error = GraphQLError("Cannot query field 'nope'.")
    extension.execution_context = make_execution_context(pre_execution_errors=[validation_error])

    with _armed({}, DEFAULT_RESOURCE_POLICY):
        hook = extension.on_validate()
        next(hook)
        with pytest.raises(StopIteration):
            next(hook)

    assert extension.execution_context.pre_execution_errors == [validation_error]


def test_the_context_is_cleared_even_when_the_document_scan_rejects() -> None:
    """A rejection must not leave a policy (or a deadline) on a reused context."""
    extension = DjangoResourcePolicyExtension(policy=ResourcePolicy(max_document_tokens=1))
    context: dict[str, object] = {}
    extension.execution_context = make_execution_context(context=context, query="{ a b c }")
    with pytest.raises(ResourceLimitExceeded):
        next(extension.on_operation())
    assert DST_RESOURCE_POLICY not in context


def test_an_extension_policy_that_is_no_resource_policy_is_refused_at_construction() -> None:
    """``policy=`` is validated where the configuration is accepted, not at the first request."""
    with pytest.raises(
        ConfigurationError,
        match=r"DjangoResourcePolicyExtension\(policy=\.\.\.\) takes a ResourcePolicy; got ",
    ):
        DjangoResourcePolicyExtension(policy=MagicMock())


def test_an_extension_configured_with_no_policy_reads_the_schemas() -> None:
    """The absent case the preservation rule must not swallow."""
    extension = DjangoResourcePolicyExtension()
    extension.execution_context = make_execution_context()

    assert extension._explicit_policy is None
    assert extension._resolved_policy() == DEFAULT_RESOURCE_POLICY


def test_a_class_entry_is_constructed_fresh_and_bounded_for_every_operation() -> None:
    """A schema builds its own resource extension per operation, from its own policy.

    The entry is the supported spelling that declares the automatic extension,
    and every operation still gets an instance of its own: one shared object
    would share one set of charge counters between concurrent requests.
    """

    @strawberry.type
    class _Query:
        @strawberry.field
        def rows(self, info: Info) -> list[str]:
            return list(bounded_rows(["a", "b", "c"], info, None))

    schema = DjangoSchema(
        query=_Query,
        extensions=[DjangoResourcePolicyExtension],
        resource_policy=ResourcePolicy(max_list_rows=1),
    )
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    built = [
        entry
        for entry in schema.get_extensions(sync=True) + schema.get_extensions(sync=True)
        if isinstance(entry, DjangoResourcePolicyExtension)
    ]
    assert len(built) == 2
    assert built[0] is not built[1]


@pytest.mark.parametrize(
    "supplied",
    [DjangoResourcePolicyExtension, DjangoResourcePolicyExtension()],
    ids=["class", "instance"],
)
def test_a_directly_supplied_extension_does_not_travel_as_an_entry(supplied: object) -> None:
    """The schema installs its own of each kind, so keeping this one would be two."""
    assert _consumer_extension_entries([supplied]) == ([], None)


def test_an_entry_declaring_a_policy_is_read_into_the_schema_policy() -> None:
    """An instance built with a policy declares it; the schema's policy is where it lands."""
    entries, declared = _consumer_extension_entries(
        [DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=2))],
    )
    assert entries == []
    assert declared == ResourcePolicy(max_list_rows=2)


def test_entry_normalization_does_not_call_consumer_iterable_truthiness() -> None:
    """A stateful list subclass cannot suppress or break the read of the entries."""

    class _HostileTruthiness(list[object]):
        def __bool__(self) -> bool:
            raise RuntimeError("bool exploded")

    marker = object()
    assert _consumer_extension_entries(_HostileTruthiness([marker])) == ([marker], None)


def test_an_unrelated_extension_is_preserved_as_an_entry() -> None:
    marker = object()
    assert _consumer_extension_entries([marker]) == ([marker], None)


def test_a_resource_rejection_is_catchable_as_a_graphql_error() -> None:
    """The wire identity: one ``GraphQLError`` needing no per-transport translation."""
    error = ResourceLimitExceeded("max_depth", 1, 2, "detail")
    assert isinstance(error, GraphQLError)
    assert error.extensions is not None
    assert error.extensions["code"] == "RESOURCE_LIMIT_EXCEEDED"


def test_a_selection_under_a_leaf_field_has_no_field_definition_to_charge() -> None:
    """Validation rejects it; a walk that ran before validation must not crash on it.

    ``echo`` returns ``String``, so its "children" have a scalar parent - which is
    not a composite type and therefore holds no field definitions.
    """
    _charge("{ echo { nope } }")


@pytest.mark.parametrize(
    "size",
    [
        None,
        "12",
        -1,
        True,
        _AmountNoBoundCanExceed(10**9),
    ],
    ids=[
        "absent",
        "string",
        "negative",
        "boolean",
        "int-subclass",
    ],
)
def test_an_upload_that_cannot_report_its_size_is_rejected(size: object) -> None:
    """Guard the ANSWER, not one spelling of the missing input.

    An unmeasurable file charged as zero bytes would be an unbounded upload that
    every byte bound reports as free - the fail-open shape this bound exists to
    avoid. ``None``, a non-integer, a negative, ``True``, and an ``int``
    SUBCLASS are all "not a size": the subclass most of all, because its own
    ``__gt__`` answers the per-file bound and its reflected ``__radd__`` decides
    what the aggregate counter becomes for every file that follows it.
    """
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query U($f: Upload!) { stash(document: $f) }",
            {"f": SimpleNamespace(size=size)},
        )
    assert caught.value.bound == "max_upload_file_bytes"


def test_a_measurable_upload_is_charged_its_bytes() -> None:
    _charge("query U($f: Upload!) { stash(document: $f) }", {"f": SimpleNamespace(size=10)})
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            "query U($f: Upload!) { stash(document: $f) }",
            {"f": SimpleNamespace(size=10)},
            policy=ResourcePolicy(max_upload_file_bytes=9),
        )
    assert caught.value.charged == 10


def test_a_schema_strawberry_did_not_build_binds_no_upload_scalar() -> None:
    """The file scalar is the one a Strawberry schema binds ``Upload`` to, never a name.

    A graphql-core schema has no such binding, so a scalar it merely calls
    ``Upload`` is charged as an opaque scalar: the file bounds never see it.
    Unreachable over the wire, where every schema is Strawberry's.
    """
    schema = build_schema("scalar Upload type Query { stash(document: Upload): String }")
    charge_document(
        ResourcePolicy(max_upload_file_bytes=9),
        schema,
        parse("query U($f: Upload) { stash(document: $f) }"),
        {"f": SimpleNamespace(size=10)},
    )


class _TaggedResourceLimitExceeded(ResourceLimitExceeded):
    """A ``ResourceLimitExceeded`` carrying the extra instance state a roundtrip must keep."""

    custom_tag: str


def test_resource_limit_exceeded_pickle_and_copy_fidelity() -> None:
    """ResourceLimitExceeded roundtrips through pickle, copy, and deepcopy preserving attributes."""
    exc = _TaggedResourceLimitExceeded("max_depth", 10, 15, "query depth 15 exceeds 10")
    exc.custom_tag = "tagged"

    # Pickle serialization roundtrip
    restored = pickle_roundtrip(exc)
    assert isinstance(restored, ResourceLimitExceeded)
    assert restored.bound == "max_depth"
    assert restored.limit == 10
    assert restored.charged == 15
    assert restored.detail == "query depth 15 exceeds 10"
    assert getattr(restored, "custom_tag", None) == "tagged"
    assert str(restored) == str(exc)

    # copy and deepcopy
    copied = copy.copy(exc)
    assert isinstance(copied, ResourceLimitExceeded)
    assert copied.bound == "max_depth"
    assert copied.limit == 10
    assert copied.charged == 15
    assert copied.detail == "query depth 15 exceeds 10"
    assert getattr(copied, "custom_tag", None) == "tagged"

    deep_copied = copy.deepcopy(exc)
    assert isinstance(deep_copied, ResourceLimitExceeded)
    assert deep_copied.bound == "max_depth"
    assert deep_copied.limit == 10
    assert deep_copied.charged == 15
    assert deep_copied.detail == "query depth 15 exceeds 10"
    assert getattr(deep_copied, "custom_tag", None) == "tagged"


def test_an_untyped_container_list_is_not_classified_as_membership_list() -> None:
    """An untyped JSON list is not a typed GraphQL list, so it carries no membership bound."""
    document = "query B($p: JSON!) { blob(payload: $p) }"
    # 4 items > max_membership_items (2), but <= max_container_width (10)
    _charge(
        document,
        {
            "p": [
                1,
                2,
                3,
                4,
            ],
        },
        policy=ResourcePolicy(max_membership_items=2, max_container_width=10),
    )
    # Exceeding max_container_width (3) is rejected under max_container_width
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge(
            document,
            {
                "p": [
                    1,
                    2,
                    3,
                    4,
                ],
            },
            policy=ResourcePolicy(max_membership_items=2, max_container_width=3),
        )
    assert caught.value.bound == "max_container_width"


class _ExoticSelection(SelectionNode):
    """A selection node of a kind graphql-core's parser never builds."""


def test_charge_document_refuses_a_selection_that_is_no_known_kind() -> None:
    """A hand-built document whose selection is neither a field nor a fragment raises."""
    document = parse("{ echo }")
    operation = document.definitions[0]
    assert isinstance(operation, OperationDefinitionNode)
    selection_set = replace(operation.selection_set, selections=(_ExoticSelection(directives=()),))
    document = replace(document, definitions=(replace(operation, selection_set=selection_set),))

    with pytest.raises(TypeError, match="expected an instance of FieldNode"):
        charge_document(DEFAULT_RESOURCE_POLICY, _PROBE_SCHEMA._schema, document)


_INPUT_OBJECT_SCHEMA = build_schema(
    "input Pair { a: String b: String } type Query { pair(p: Pair): String }",
)


class _ListKeyedMapping(Mapping[object, object]):
    """A mapping whose keys are not names: one unhashable, one an ``int``."""

    def __init__(self) -> None:
        self._entries: list[tuple[object, object]] = [(["a"], "x"), (1, "y")]

    @override
    def __getitem__(self, key: object) -> object:
        for entry_key, value in self._entries:
            if entry_key == key:
                return value
        raise KeyError(key)

    @override
    def __iter__(self) -> Iterator[object]:
        return (key for key, _ in self._entries)

    @override
    def __len__(self) -> int:
        return len(self._entries)


def _charge_pair(value: object, policy: ResourcePolicy) -> None:
    charge_document(
        policy,
        _INPUT_OBJECT_SCHEMA,
        parse("query P($p: Pair) { pair(p: $p) }"),
        {"p": value},
    )


def test_keys_that_are_not_names_are_charged_and_name_no_input_field() -> None:
    """An input object's non-``str`` keys are charged for width and nodes like any entry.

    They name no declared field, so the lookup is never asked of them: an
    unhashable key raises nothing, and each entry is charged untyped.
    """
    _charge_pair(_ListKeyedMapping(), ResourcePolicy(max_container_width=2, max_input_nodes=3))
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge_pair(_ListKeyedMapping(), ResourcePolicy(max_container_width=1))
    assert caught.value.bound == "max_container_width"
    with pytest.raises(ResourceLimitExceeded) as caught:
        _charge_pair(_ListKeyedMapping(), ResourcePolicy(max_input_nodes=2))
    assert caught.value.bound == "max_input_nodes"


def test_charge_document_accepts_none_variables() -> None:
    """charge_document safely accepts variables=None."""
    charge_document(
        DEFAULT_RESOURCE_POLICY,
        _PROBE_SCHEMA._schema,
        parse("{ echo }"),
        None,
        None,
    )


def test_disarming_with_a_token_from_another_variable_is_not_swallowed() -> None:
    """The cross-context tolerance is for WHERE teardown ran, not for the wrong token.

    ``ContextVar.reset`` answers two different mistakes with ``ValueError``: a
    token minted in another context, which teardown legitimately reaches when a
    dropped stream is closed from a foreign task and which there is nothing to
    undo for; and a token minted by another VARIABLE, which is this module
    disarming something it never armed. Only the first is tolerated. A catch
    wide enough to cover both would turn the second into a silent no-op and
    leave the real budget armed for the rest of the process.
    """
    context: dict[str, object] = {}
    scope = begin_resource_budget(context, ResourcePolicy(max_list_rows=2))
    try:
        foreign: contextvars.ContextVar[_RequestBudget | None] = contextvars.ContextVar(
            "foreign_budget",
            default=None,
        )
        mismatched = _BudgetScope(
            policy=scope.policy,
            budget=scope.budget,
            token=foreign.set(None),
        )

        with pytest.raises(ValueError, match="different ContextVar"):
            end_resource_budget(mismatched)
    finally:
        end_resource_budget(scope)
