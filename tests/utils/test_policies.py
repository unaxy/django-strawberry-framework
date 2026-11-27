"""``utils/policies.py::resolve_policy`` - the shared schema-construction resolver.

The generic contract that ``resource_policy.py::resolve_resource_policy`` and
``error_policy.py::resolve_error_policy`` both delegate to, exercised directly
with probe policies so the precedence ladder, the mapping-type gate, the
unknown-key vocabulary message, and the derived article are pinned once here.
Each flavor's own tier (``tests/test_resource_policy.py``,
``tests/test_error_policy.py``) plus
``examples/fakeshop/test_query/test_error_policy_api.py`` and
``examples/fakeshop/test_query/test_resource_policy_api.py`` pins
wire-visible wording end to end.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import NoReturn

import pytest
from typing_extensions import override

from django_strawberry_framework.error_policy import resolve_error_policy
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.resource_policy import resolve_resource_policy
from django_strawberry_framework.utils.policies import resolve_policy
from tests._idioms import ClaimsClass, ClassReadRaises


@dataclass(frozen=True)
class _ProbePolicy:
    width: int = 10


_PROBE_DEFAULT = _ProbePolicy()


def _resolve(
    explicit: _ProbePolicy | Mapping[str, object] | None = None,
    setting: object = None,
) -> _ProbePolicy:
    return resolve_policy(
        explicit,
        policy_cls=_ProbePolicy,
        default=_PROBE_DEFAULT,
        read_setting=(lambda: setting),
        display_name="probe policy",
        unit="bound",
    )


def test_an_explicit_instance_is_used() -> None:
    policy = _ProbePolicy(width=3)
    assert _resolve(policy) is policy


def test_no_source_at_all_resolves_to_the_default() -> None:
    assert _resolve(None, None) is _PROBE_DEFAULT


def test_an_instance_through_the_setting_slot_is_taken_on_the_same_terms() -> None:
    """A validated instance behind the setting slot is the same trusted declaration.

    The explicit argument and the setting read are two spellings of one override
    source, so an instance from either is used as it is.
    """
    policy = _ProbePolicy(width=3)
    assert _resolve(None, policy) is policy


def test_the_setting_supplies_overrides_when_the_argument_is_absent() -> None:
    assert _resolve(None, {"width": 4}) == _ProbePolicy(width=4)


def test_an_explicit_mapping_outranks_the_setting() -> None:
    assert _resolve({"width": 9}, {"width": 4}) == _ProbePolicy(width=9)


def test_a_non_mapping_override_is_rejected_with_the_derived_article() -> None:
    with pytest.raises(ConfigurationError) as excinfo:
        # basedpyright: the int policy is the hostile input under test; _resolve types the
        # parameter as resolve_policy does: a policy, a mapping or None
        _resolve(12)  # pyright: ignore[reportArgumentType]
    assert str(excinfo.value) == (
        "The probe policy must be a _ProbePolicy or a mapping of bound names to values; "
        "got int 12."
    )


def test_unknown_keys_are_rejected_naming_the_valid_vocabulary() -> None:
    with pytest.raises(ConfigurationError, match=r"Unknown probe-policy bound\(s\): wirth"):
        _resolve({"wirth": 1})


# ---------------------------------------------------------------------------
# Override mappings: the mapping's own errors propagate
# ---------------------------------------------------------------------------


class _RaisingIterMapping(Mapping[str, object]):
    @override
    def __iter__(self) -> NoReturn:
        raise RuntimeError("hostile __iter__")

    @override
    def __getitem__(self, key: str) -> int:
        return 1

    @override
    def __len__(self) -> int:
        return 1


_FLAVORS = [
    pytest.param(resolve_error_policy, "message", "From hostile mapping.", id="error-policy"),
    pytest.param(resolve_resource_policy, "max_page_size", 20, id="resource-policy"),
]


@pytest.mark.parametrize(
    "resolver",
    [row.values[0] for row in _FLAVORS],
    ids=["error-policy", "resource-policy"],
)
def test_a_raising_iterator_propagates_its_own_error(
    resolver: Callable[[Mapping[str, object]], object],
) -> None:
    """The override mapping's iteration is deployment code: its exception propagates."""
    with pytest.raises(RuntimeError, match="hostile __iter__"):
        resolver(_RaisingIterMapping())


@pytest.mark.parametrize(
    "resolver",
    [row.values[0] for row in _FLAVORS],
    ids=["error-policy", "resource-policy"],
)
def test_a_hashable_non_string_key_is_typed_rejected_at_the_key_guard(
    resolver: Callable[[Mapping[str, object]], object],
) -> None:
    """A hashable non-string override key reaches the key-type guard.

    It materializes fine and must reach the ``must be strings`` rejection, not a
    bare ``TypeError`` from ``sorted()`` over mixed keys.
    """
    with pytest.raises(ConfigurationError, match="must be strings"):
        # basedpyright: the int-keyed mapping is the hostile input under test; each resolver types
        # the parameter as Mapping[str, object]
        resolver({42: 1})  # pyright: ignore[reportArgumentType]


# ---------------------------------------------------------------------------
# Deployment values whose class hooks cannot be trusted
# ---------------------------------------------------------------------------


def _resolve_through(slot: str, value: object) -> _ProbePolicy:
    """Resolve ``value`` as the explicit argument or as the deployment setting."""
    if slot == "explicit":
        # basedpyright: the hostile value is the input under test; the parameter is typed as
        # a policy or a mapping
        return _resolve(explicit=value)  # pyright: ignore[reportArgumentType]
    return _resolve(setting=value)


@pytest.mark.parametrize("slot", ["explicit", "setting"])
def test_a_policy_value_whose_class_read_raises_is_typed_rejected(slot: str) -> None:
    """A value whose ``__class__`` raises is classified "not a policy, not a mapping".

    ``isinstance`` falls back to the value's ``__class__``, so the kind tests that
    route a deployment value to the instance, mapping or rejection arm would
    otherwise leak the value's own exception out of schema construction.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        _resolve_through(slot, ClassReadRaises())
    assert str(excinfo.value) == (
        "The probe policy must be a _ProbePolicy or a mapping of bound names to values; "
        "got ClassReadRaises <ClassReadRaises>."
    )


@pytest.mark.parametrize("slot", ["explicit", "setting"])
@pytest.mark.parametrize(
    "key",
    [
        pytest.param(ClassReadRaises(), id="class-read-raises"),
        pytest.param(ClaimsClass(str), id="claims-str"),
    ],
)
def test_a_key_that_is_not_really_a_string_is_typed_rejected(slot: str, key: object) -> None:
    """A key is a name only if its real type is a string: its ``__class__`` is never consulted."""
    with pytest.raises(ConfigurationError) as excinfo:
        _resolve_through(slot, {key: 1})
    assert str(excinfo.value) == (
        f"The probe policy bound names must be strings; got {type(key).__name__} {key!r}."
    )


# ---------------------------------------------------------------------------
# Key names: read by real class
# ---------------------------------------------------------------------------


class _NameStr(str):
    """A ``str`` subclass bound name (a ``StrEnum``-style key)."""


def test_a_str_subclass_key_resolves_by_its_string_value() -> None:
    """A ``str`` subclass key names its bound like the string it carries."""
    resolved = _resolve({_NameStr("width"): 4})
    assert resolved.width == 4
