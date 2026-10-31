"""Tests for the shared request-context read / write / delete dispatch.

Stash/clear on slotted objects and frozen mappings are not a response field.
Optimizer and resource-policy stashes on the live request
are in ``examples/fakeshop/test_query/test_library_api.py`` and
``examples/fakeshop/test_query/test_resource_policy_api.py``.
"""

from collections.abc import Callable
from types import MappingProxyType, SimpleNamespace
from typing import NoReturn

import pytest
from typing_extensions import override

from django_strawberry_framework.utils.context import (
    MISSING,
    clear_context_key,
    get_context_value,
    restored_context_keys,
    stash_on_context,
)


class SlotsMapping:
    """A non-dict mapping-only context: ``setattr`` is impossible, items work."""

    __slots__: tuple[str, ...] = ("values",)

    def __init__(self) -> None:
        """Start with no stored items."""
        self.values: dict[str, object] = {}

    def __getitem__(self, key: str) -> object:
        """Read ``key`` from the item store."""
        return self.values[key]

    def __setitem__(self, key: str, value: object) -> None:
        """Store ``value`` under ``key``."""
        self.values[key] = value

    def __delitem__(self, key: str) -> None:
        """Remove ``key`` from the item store."""
        del self.values[key]


@pytest.mark.parametrize(
    "make",
    [SimpleNamespace, dict, SlotsMapping],
    ids=["object", "dict", "slots"],
)
def test_context_stash_round_trips_and_clears_object_dict_and_slots_mapping(
    make: Callable[[], object],
) -> None:
    """Each supported writable shape uses the same read and clear contract."""
    context = make()
    marker = object()
    stash_on_context(context, "dst_context_test", marker)
    assert get_context_value(context, "dst_context_test") is marker
    clear_context_key(context, "dst_context_test")
    assert get_context_value(context, "dst_context_test", "missing") == "missing"


def test_context_read_propagates_a_consumer_descriptor_error() -> None:
    """A consumer context's own descriptor runs untouched; what it raises propagates."""

    class RaisingAttribute:
        @property
        def dst_context_test(self) -> NoReturn:
            raise RuntimeError("descriptor failed")

    with pytest.raises(RuntimeError, match="descriptor failed"):
        get_context_value(RaisingAttribute(), "dst_context_test", "missing")


def test_frozen_context_stash_and_clear_are_noops() -> None:
    """Read-only mappings keep their original value; the write and clear are silently skipped."""
    context = MappingProxyType({"dst_context_test": 42})
    stash_on_context(context, "dst_context_test", 99)
    clear_context_key(context, "dst_context_test")
    assert get_context_value(context, "dst_context_test") == 42


def test_context_none_short_circuits_and_skips_writes_and_clears() -> None:
    """None context returns default on read and silently skips write and clear."""
    assert get_context_value(None, "dst_context_test") is None
    assert get_context_value(None, "dst_context_test", "missing") == "missing"
    stash_on_context(None, "dst_context_test", 42)
    clear_context_key(None, "dst_context_test")


def test_context_distinguishes_explicit_none_from_missing_sentinel() -> None:
    """Stashing an explicit None value returns None rather than falling back to default."""
    obj_ctx = SimpleNamespace()
    dict_ctx: dict[str, object] = {}

    stash_on_context(obj_ctx, "dst_context_test", None)
    stash_on_context(dict_ctx, "dst_context_test", None)

    assert get_context_value(obj_ctx, "dst_context_test", "default") is None
    assert get_context_value(dict_ctx, "dst_context_test", "default") is None


def test_locked_dict_subclass_stash_and_clear_are_noops() -> None:
    """Immutable dict subclasses (e.g. locked QueryDict) silently skip stash and clear."""

    class LockedDict(dict[str, object]):
        @override
        def __setitem__(self, key: str, value: object) -> None:
            raise AttributeError("This dict is immutable")

        @override
        def __delitem__(self, key: str) -> None:
            raise AttributeError("This dict is immutable")

    ctx = LockedDict({"dst_context_test": 42})
    stash_on_context(ctx, "dst_context_test", 99)
    clear_context_key(ctx, "dst_context_test")
    assert get_context_value(ctx, "dst_context_test") == 42


@pytest.mark.parametrize(
    "make",
    [SimpleNamespace, dict, SlotsMapping],
    ids=["object", "dict", "slots"],
)
@pytest.mark.parametrize("stashed", ["outer", None, MISSING], ids=["present", "none", "absent"])
def test_restored_context_keys_round_trips_absent_present_and_none(
    make: Callable[[], object],
    stashed: object,
) -> None:
    """The restore puts ABSENT keys back to absent and re-stashes found values.

    An explicit ``None`` snapshot is a VALUE: it is re-stashed, never cleared,
    on every writable context shape the helpers dispatch on.
    """
    context = make()
    if stashed is not MISSING:
        stash_on_context(context, "dst_context_test", stashed)
    with restored_context_keys(context, "dst_context_test"):
        stash_on_context(context, "dst_context_test", "inner")
    assert get_context_value(context, "dst_context_test", MISSING) is stashed


def test_restored_context_keys_still_restores_when_the_body_raises() -> None:
    """Restoration runs in a ``finally``: a raising body leaves the context as found."""
    context: dict[str, object] = {}
    stash_on_context(context, "kept", "outer")

    def body_that_raises() -> NoReturn:
        with restored_context_keys(context, "kept", "never-was"):
            stash_on_context(context, "kept", "inner")
            stash_on_context(context, "never-was", "transient")
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        body_that_raises()
    assert get_context_value(context, "kept") == "outer"
    assert get_context_value(context, "never-was", "absent") == "absent"


def test_restored_context_keys_on_a_none_context_is_inert() -> None:
    """No context means nothing to snapshot and nothing to restore."""
    with restored_context_keys(None, "dst_context_test"):
        stash_on_context(None, "dst_context_test", 42)
        assert get_context_value(None, "dst_context_test", "d") == "d"
    assert get_context_value(None, "dst_context_test", "d") == "d"


def test_the_public_missing_sentinel_is_the_round_trip_identity() -> None:
    """``MISSING`` is importable and is the exact sentinel the read dispatches on."""
    assert get_context_value({}, "dst_context_test", MISSING) is MISSING
    assert MISSING is not None


def test_get_context_value_swallows_attribute_error_from_getitem() -> None:
    """A ``__getitem__`` raising ``AttributeError`` on a missing key returns ``default``.

    ``strawberry-graphql-django``'s ``StrawberryDjangoContext`` bridges
    ``__getitem__`` to ``__getattribute__``, so reading a key that was never
    stashed raises ``AttributeError`` out of the item access path. The read
    helper's ``except`` tuple must catch ``AttributeError`` alongside
    ``KeyError`` / ``TypeError`` so the resolver chain sees ``default`` rather
    than a leaking ``AttributeError`` from deep inside item lookup.
    """

    class BridgedItemAccess:
        """Mimics ``StrawberryDjangoContext.__getitem__`` shape."""

        def __getitem__(self, key: str) -> NoReturn:
            raise AttributeError(f"missing attribute {key!r}")

    sentinel = object()
    ctx = BridgedItemAccess()
    assert get_context_value(ctx, "dst_optimizer_plan", sentinel) is sentinel


def test_stash_does_not_swallow_unexpected_exceptions_from_setitem() -> None:
    """The mapping-write ``except`` stays narrow.

    Read-only mapping failures are intentionally limited to ``TypeError``
    and ``AttributeError``. A guarded mapping that raises a different
    exception from ``__setitem__`` must surface the error rather than
    silently losing the optimizer stash.
    """

    class GuardedMapping(dict[str, object]):
        @override
        def __setattr__(self, _key: str, _value: object) -> None:
            raise TypeError("no attribute writes")

        @override
        def __setitem__(self, _key: str, _value: object) -> None:
            raise RuntimeError("guarded write rejected")

    ctx = GuardedMapping()
    with pytest.raises(RuntimeError, match="guarded write rejected"):
        stash_on_context(ctx, "dst_optimizer_plan", object())
