"""OptimizerHint tests for Meta.optimizer_hints normalization and validation.

SKIP identity, factory classmethods, frozen immutability, and invalid-state
``ConfigurationError`` have no GraphQL envelope. Shipped skip / prefetch SQL is
``examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_hints_are_observable_over_http``.
"""

import typing
from collections.abc import Callable
from typing import NoReturn

import pytest
from django.db.models import Prefetch
from django.utils.functional import SimpleLazyObject
from typing_extensions import override

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.optimizer.hints import OptimizerHint, hint_is_skip
from django_strawberry_framework.optimizer.nested_fetch import (
    WINDOWED_STRATEGY,
    NestedConnectionStrategy,
    WindowedPrefetchStrategy,
    resolve_strategy,
)
from django_strawberry_framework.utils.typing import object_result
from tests._idioms import ClaimsClassBase, ClassReadRaisesBase

_RAISING_CLASS_ERRORS = [RuntimeError, TypeError, KeyboardInterrupt]


class RaisingClass(ClassReadRaisesBase):
    """A value whose ``__class__`` read raises (so a bare ``isinstance`` raises)."""


class _ClaimsStr(ClaimsClassBase):
    """A non-``str`` value whose ``__class__`` claims ``str``."""

    claimed = str


# ``Prefetch[str]`` subscripts at run time through the ``django_stubs_ext.monkeypatch()`` the
# fakeshop settings make, which hands back ``Prefetch`` itself
class _PrefetchSubclass(Prefetch[str]):
    """A consumer ``Prefetch`` subclass."""


def _prefetch_through_factory(obj: object) -> OptimizerHint:
    """Build a prefetch hint through ``OptimizerHint.prefetch``."""
    # basedpyright: the non-Prefetch value is the hostile input under test;
    # OptimizerHint.prefetch types the parameter as a Prefetch
    return OptimizerHint.prefetch(obj)  # pyright: ignore[reportArgumentType]


def _prefetch_through_constructor(obj: object) -> OptimizerHint:
    """Build a prefetch hint through ``OptimizerHint(prefetch_obj=...)``."""
    # basedpyright: as above; OptimizerHint types prefetch_obj as a Prefetch
    return OptimizerHint(prefetch_obj=obj)  # pyright: ignore[reportArgumentType]


class TestSkipSentinel:
    """``OptimizerHint.SKIP`` is a singleton-like frozen sentinel."""

    def test_skip_is_an_optimizer_hint(self) -> None:
        """The sentinel is an ``OptimizerHint`` instance."""
        assert isinstance(OptimizerHint.SKIP, OptimizerHint)

    def test_skip_has_skip_flag_true(self) -> None:
        """The sentinel's ``skip`` attribute is ``True``."""
        assert OptimizerHint.SKIP.skip is True

    def test_skip_has_no_other_flags(self) -> None:
        """No force or prefetch flags are set on SKIP."""
        assert OptimizerHint.SKIP.force_select is False
        assert OptimizerHint.SKIP.force_prefetch is False
        assert OptimizerHint.SKIP.prefetch_obj is None

    def test_skip_identity_stable(self) -> None:
        """``SKIP`` is the same object across accesses."""
        assert OptimizerHint.SKIP is OptimizerHint.SKIP

    def test_skip_equality(self) -> None:
        """A fresh ``OptimizerHint(skip=True)`` equals the sentinel."""
        assert OptimizerHint(skip=True) == OptimizerHint.SKIP


class TestSelectRelatedFactory:
    """``OptimizerHint.select_related()`` forces select_related."""

    def test_force_select_flag(self) -> None:
        """The hint has ``force_select=True``."""
        hint = OptimizerHint.select_related()
        assert hint.force_select is True

    def test_no_other_flags(self) -> None:
        """No skip, prefetch, or prefetch_obj flags."""
        hint = OptimizerHint.select_related()
        assert hint.skip is False
        assert hint.force_prefetch is False
        assert hint.prefetch_obj is None


class TestPrefetchRelatedFactory:
    """``OptimizerHint.prefetch_related()`` forces prefetch_related."""

    def test_force_prefetch_flag(self) -> None:
        """The hint has ``force_prefetch=True``."""
        hint = OptimizerHint.prefetch_related()
        assert hint.force_prefetch is True

    def test_no_other_flags(self) -> None:
        """No skip, select, or prefetch_obj flags."""
        hint = OptimizerHint.prefetch_related()
        assert hint.skip is False
        assert hint.force_select is False
        assert hint.prefetch_obj is None


class TestPrefetchFactory:
    """``OptimizerHint.prefetch(obj)`` carries a specific Prefetch object."""

    def test_prefetch_obj_stored(self) -> None:
        """The ``Prefetch`` object is stored on the hint."""
        pf = Prefetch("items")
        hint = OptimizerHint.prefetch(pf)
        assert hint.prefetch_obj is pf

    def test_no_other_flags(self) -> None:
        """No skip, select, or prefetch flags."""
        hint = OptimizerHint.prefetch(Prefetch("items"))
        assert hint.skip is False
        assert hint.force_select is False
        assert hint.force_prefetch is False

    def test_none_rejected(self) -> None:
        """``None`` must not collapse into the empty no-op hint."""
        with pytest.raises(ConfigurationError, match="Prefetch"):
            # basedpyright: the None prefetch is the hostile input under test; OptimizerHint.prefetch
            # types the parameter as a Prefetch
            OptimizerHint.prefetch(None)  # pyright: ignore[reportArgumentType]

    def test_prefetch_subclass_accepted(self) -> None:
        """A ``Prefetch`` subclass passes and is stored as is."""
        obj = _PrefetchSubclass("items")
        assert OptimizerHint.prefetch(obj).prefetch_obj is obj
        assert OptimizerHint(prefetch_obj=obj).prefetch_obj is obj

    @pytest.mark.parametrize(
        "route",
        [_prefetch_through_factory, _prefetch_through_constructor],
        ids=["factory", "direct"],
    )
    def test_prefetch_lazy_proxy_rejected(self, route: Callable[[object], OptimizerHint]) -> None:
        """A Django lazy proxy of a ``Prefetch`` is not a ``Prefetch``: refused like ``strategy``'s."""
        with pytest.raises(ConfigurationError, match="got SimpleLazyObject"):
            _ = route(SimpleLazyObject(lambda: Prefetch("items")))


class TestStrategyFactory:
    """``OptimizerHint.strategy(name)`` overrides the nested-connection strategy."""

    def test_stores_name(self) -> None:
        """The factory carries the strategy name on ``nested_strategy``."""
        hint = OptimizerHint.strategy("windowed")
        assert hint.nested_strategy == "windowed"

    def test_no_other_flags(self) -> None:
        """No skip / select / prefetch flags come along for the ride."""
        hint = OptimizerHint.strategy("lateral")
        assert hint.skip is False
        assert hint.force_select is False
        assert hint.force_prefetch is False
        assert hint.prefetch_obj is None

    def test_default_hint_has_no_strategy(self) -> None:
        """An unspecified ``nested_strategy`` stays ``None``."""
        assert OptimizerHint().nested_strategy is None
        assert OptimizerHint.SKIP.nested_strategy is None

    def test_accepts_lateral_and_auto(self) -> None:
        """``lateral`` and ``auto`` are registered / resolvable names."""
        assert OptimizerHint.strategy("lateral").nested_strategy == "lateral"
        assert OptimizerHint.strategy("auto").nested_strategy == "auto"

    def test_force_prefetch_is_redundant_but_allowed(self) -> None:
        """``force_prefetch`` + ``nested_strategy`` is redundant, not rejected."""
        hint = OptimizerHint(force_prefetch=True, nested_strategy="windowed")
        assert hint.nested_strategy == "windowed"
        assert hint.force_prefetch is True

    def test_none_rejected(self) -> None:
        """``None`` must not collapse into the empty no-op hint."""
        with pytest.raises(ConfigurationError, match="strategy name"):
            # basedpyright: the None strategy is the hostile input under test; OptimizerHint.strategy
            # types the parameter as StrategySelection
            OptimizerHint.strategy(None)  # pyright: ignore[reportArgumentType]

    def test_bad_name_raises_at_construction(self) -> None:
        """A typo'd strategy name fails loud through ``resolve_strategy``."""
        with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
            OptimizerHint.strategy("winowed")
        with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
            OptimizerHint(nested_strategy="not-a-strategy")

    def test_strategy_with_skip_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="nested_strategy"):
            OptimizerHint(skip=True, nested_strategy="windowed")

    def test_strategy_with_force_select_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="nested_strategy"):
            OptimizerHint(force_select=True, nested_strategy="windowed")

    def test_strategy_with_prefetch_obj_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="nested_strategy"):
            OptimizerHint(prefetch_obj=Prefetch("items"), nested_strategy="windowed")

    def test_strategy_rejects_hostile_type_name_safely(self) -> None:
        """A hostile metaclass cannot replace the typed strategy rejection."""

        class HostileType(type):
            @property
            @override
            # basedpyright: the hostile shape under test, a ``__name__`` property whose read
            # raises; the checker rejects any property overriding a base class attribute
            def __name__(cls) -> NoReturn:  # pyright: ignore[reportIncompatibleVariableOverride]
                raise RuntimeError("type name should never run")

        class NotStrategy(metaclass=HostileType):
            pass

        with pytest.raises(ConfigurationError, match="nested_connection_strategy"):
            # basedpyright: the non-strategy object is the hostile input under test;
            # OptimizerHint.strategy types the parameter as StrategySelection
            OptimizerHint.strategy(NotStrategy())  # pyright: ignore[reportArgumentType]

    def test_strategy_rejects_class_with_clean_name(self) -> None:
        """Passing a strategy class instead of an instance names the class, not 'type'."""
        with pytest.raises(ConfigurationError, match="WindowedPrefetchStrategy"):
            # basedpyright: the strategy class is the hostile input under test; OptimizerHint.strategy
            # types the parameter as StrategySelection
            OptimizerHint.strategy(WindowedPrefetchStrategy)  # pyright: ignore[reportArgumentType]

    def test_strategy_str_subclass_selection_values_match_by_content(self) -> None:
        """A ``str`` subclass selection value is matched by content, rendered by its own repr.

        The typed contract is owned by ``resolve_strategy`` itself: the
        ``__eq__`` check reads through the base ``str`` slot and the registry is
        scanned without hashing, so neither override decides the verdict. A
        ``__repr__`` override is the consumer's own rendering and what it raises
        propagates.
        """

        class HostileRepr(str):
            @override
            def __repr__(self) -> str:
                raise RuntimeError("hostile repr")

        class HostileEq(str):
            @override
            def __eq__(self, other: object) -> NoReturn:
                raise RuntimeError("eq should never run")

            @override
            def __hash__(self) -> int:
                return str.__hash__(self)

        class HostileHash(str):
            @override
            def __hash__(self) -> NoReturn:
                raise RuntimeError("hash should never run")

        # An unknown name raises the typed rejection; a ``__hash__`` override never runs.
        with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
            OptimizerHint.strategy(HostileHash("winowed"))
        with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
            OptimizerHint(nested_strategy=HostileHash("winowed"))
        # Rendering the unknown name runs the value's own ``__repr__``, which propagates.
        with pytest.raises(RuntimeError, match="hostile repr"):
            OptimizerHint.strategy(HostileRepr("winowed"))
        with pytest.raises(RuntimeError, match="hostile repr"):
            OptimizerHint(nested_strategy=HostileRepr("winowed"))

        class HostilePlan(NestedConnectionStrategy):
            name = "hostile"

            @override
            def plan(self, *_args: object) -> bool:
                return False

            @override
            def __getattribute__(self, name: str) -> object:
                if name == "plan":
                    raise RuntimeError("plan read failed")
                return object_result(super().__getattribute__, name)

        # A consumer strategy's ``plan`` read runs untouched; what it raises propagates.
        with pytest.raises(RuntimeError, match="plan read failed"):
            OptimizerHint.strategy(HostilePlan())
        # Content decides through the base ``str`` slot: a hostile ``__eq__``
        # can neither force a false AUTO_STRATEGY match nor break a valid name.
        # (Even the assertion reads through the base slot - ``==`` on the
        # carried instance would dispatch back into the hostile override.)
        carried = OptimizerHint.strategy(HostileEq("windowed")).nested_strategy
        assert isinstance(carried, str)
        assert str.__eq__(carried, "windowed") is True
        assert resolve_strategy(HostileEq("windowed")) is WINDOWED_STRATEGY

    def test_strategy_hostile_rejection_is_raised_directly(self) -> None:
        """The typed rejection needs no containment chain: nothing escapes first."""

        class HostileHash(str):
            @override
            def __hash__(self) -> NoReturn:
                raise RuntimeError("hash should never run")

        with pytest.raises(
            ConfigurationError,
            match="Unknown nested_connection_strategy",
        ) as exc_info:
            OptimizerHint.strategy(HostileHash("winowed"))
        assert exc_info.value.__cause__ is None

    @pytest.mark.parametrize(
        ("make", "type_name"),
        [
            (lambda: RaisingClass(RuntimeError), "RaisingClass"),
            (lambda: RaisingClass(KeyboardInterrupt), "RaisingClass"),
            (_ClaimsStr, "_ClaimsStr"),
            (lambda: SimpleLazyObject(lambda: "windowed"), "SimpleLazyObject"),
        ],
        ids=[
            "class-read-raises",
            "class-read-raises-base-exception",
            "class-claims-str",
            "lazy-str",
        ],
    )
    def test_strategy_non_str_lookalikes_stay_typed(
        self,
        make: Callable[[], object],
        type_name: str,
    ) -> None:
        """A value that is not really a ``str`` (and has no ``plan``) takes the typed rejection."""
        message = (
            "nested_connection_strategy must be a strategy name, 'auto', or an object with a "
            f"plan(request, plan) method; got {type_name}."
        )
        with pytest.raises(ConfigurationError) as factory_exc:
            # basedpyright: the non-str lookalike is the hostile input under test;
            # OptimizerHint.strategy types the parameter as StrategySelection
            OptimizerHint.strategy(make())  # pyright: ignore[reportArgumentType]
        assert str(factory_exc.value) == message
        with pytest.raises(ConfigurationError) as direct_exc:
            # basedpyright: as above; OptimizerHint types nested_strategy as StrategySelection
            OptimizerHint(nested_strategy=make())  # pyright: ignore[reportArgumentType]
        assert str(direct_exc.value) == message

    def test_public_annotations_resolve_at_runtime(self) -> None:
        """``typing.get_type_hints(OptimizerHint)`` resolves ``StrategySelection``.

        The public dataclass annotates ``nested_strategy`` (and the
        ``strategy()`` factory) with ``StrategySelection``, whose name must live
        in ``hints``' runtime globals so a docs generator / runtime-validation
        library / IDE bridge doing an ordinary ``get_type_hints`` introspection
        (no custom ``globalns``) does not hit ``NameError``. Regression against
        the ``TYPE_CHECKING``-only import that resolved for static checkers but
        left the postponed annotation unevaluable at runtime.
        """
        resolved = typing.get_type_hints(OptimizerHint)
        assert resolved["nested_strategy"] == (str | NestedConnectionStrategy | None)
        # The factory signature resolves too (no custom globalns workaround).
        factory_hints = typing.get_type_hints(OptimizerHint.strategy)
        assert factory_hints["name"] == (str | NestedConnectionStrategy)


class TestFrozenImmutability:
    """Hints are frozen dataclasses - mutation raises."""

    def test_cannot_mutate_skip(self) -> None:
        """Attempting to set an attribute raises ``FrozenInstanceError``."""
        hint = OptimizerHint.select_related()
        with pytest.raises(AttributeError):
            # basedpyright: the write to the frozen dataclass field is the mutation under test; the
            # checker rejects assignment to a frozen field
            hint.force_select = False  # pyright: ignore[reportAttributeAccessIssue]

    def test_skip_sentinel_cannot_be_mutated(self) -> None:
        """The SKIP sentinel is also frozen."""
        with pytest.raises(AttributeError):
            # basedpyright: the write to the frozen dataclass field is the mutation under test; the
            # checker rejects assignment to a frozen field
            OptimizerHint.SKIP.skip = False  # pyright: ignore[reportAttributeAccessIssue]


class TestEquality:
    """Frozen dataclass equality works as expected."""

    def test_same_factory_produces_equal_hints(self) -> None:
        """Two ``select_related()`` calls produce equal hints."""
        assert OptimizerHint.select_related() == OptimizerHint.select_related()

    def test_different_factories_not_equal(self) -> None:
        """``select_related()`` != ``prefetch_related()``."""
        assert OptimizerHint.select_related() != OptimizerHint.prefetch_related()

    def test_prefetch_with_different_objects_not_equal(self) -> None:
        """Two prefetch hints with different objects are not equal."""
        assert OptimizerHint.prefetch(Prefetch("a")) != OptimizerHint.prefetch(Prefetch("b"))


class TestInvalidStatesRejected:
    """``__post_init__`` rejects states the walker would silently misread.

    Combining flags beyond the four directives, or the empty no-op form, would
    let the walker's priority order silently swallow the lower-priority directive. Each
    rejected state raises ``ConfigurationError`` at construction time.
    """

    def test_non_bool_flags_raise(self) -> None:
        """Truthy and falsy non-booleans must not control dispatch."""
        for kwargs in ({"force_select": 1}, {"force_prefetch": ""}, {"skip": "false"}):
            with pytest.raises(ConfigurationError, match="bool values"):
                # basedpyright: each non-bool flag is the hostile input under test; OptimizerHint types
                # the flags as bool
                OptimizerHint(**kwargs)  # pyright: ignore[reportArgumentType]

    def test_skip_with_force_select_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="skip=True"):
            OptimizerHint(skip=True, force_select=True)

    def test_skip_with_force_prefetch_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="skip=True"):
            OptimizerHint(skip=True, force_prefetch=True)

    def test_skip_with_prefetch_obj_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="skip=True"):
            OptimizerHint(skip=True, prefetch_obj=Prefetch("items"))

    def test_force_select_with_force_prefetch_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="force_select and force_prefetch"):
            OptimizerHint(force_select=True, force_prefetch=True)

    def test_prefetch_obj_with_force_select_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="prefetch_obj"):
            OptimizerHint(prefetch_obj=Prefetch("items"), force_select=True)

    def test_prefetch_obj_with_force_prefetch_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="prefetch_obj"):
            OptimizerHint(prefetch_obj=Prefetch("items"), force_prefetch=True)

    def test_prefetch_obj_rejects_non_prefetch_value(self) -> None:
        """``prefetch(obj)`` must receive a ``Prefetch`` instance.

        An ``obj: Any`` factory signature would let strings or other shapes through
        ``__post_init__`` and crash later in the walker, so construction rejects them.
        """
        with pytest.raises(ConfigurationError, match="Prefetch"):
            # basedpyright: the lookup string is the hostile input under test; OptimizerHint.prefetch
            # types the parameter as a Prefetch
            OptimizerHint.prefetch("entries__items")  # pyright: ignore[reportArgumentType]
        with pytest.raises(ConfigurationError, match="Prefetch"):
            # basedpyright: the lookup string is the hostile input under test; OptimizerHint types
            # prefetch_obj as a Prefetch
            OptimizerHint(prefetch_obj="entries__items")  # pyright: ignore[reportArgumentType]

    def test_prefetch_obj_rejects_hostile_type_name_safely(self) -> None:
        """A hostile metaclass cannot replace the typed Prefetch rejection."""

        class HostileType(type):
            @property
            @override
            # basedpyright: the hostile shape under test, a ``__name__`` property whose read
            # raises; the checker rejects any property overriding a base class attribute
            def __name__(cls) -> NoReturn:  # pyright: ignore[reportIncompatibleVariableOverride]
                raise RuntimeError("type name should never run")

        class NotPrefetch(metaclass=HostileType):
            pass

        with pytest.raises(ConfigurationError, match="Prefetch"):
            # basedpyright: the non-Prefetch object is the hostile input under test;
            # OptimizerHint.prefetch types the parameter as a Prefetch
            OptimizerHint.prefetch(NotPrefetch())  # pyright: ignore[reportArgumentType]

    @pytest.mark.parametrize("raised", _RAISING_CLASS_ERRORS)
    @pytest.mark.parametrize(
        "route",
        [_prefetch_through_factory, _prefetch_through_constructor],
        ids=["factory", "direct"],
    )
    def test_prefetch_obj_rejects_raising_class_read(
        self,
        route: Callable[[object], OptimizerHint],
        raised: type[BaseException],
    ) -> None:
        """A value whose ``__class__`` read raises is not a ``Prefetch``: the rejection stays typed."""
        with pytest.raises(ConfigurationError) as exc_info:
            _ = route(RaisingClass(raised))
        assert str(exc_info.value) == (
            "OptimizerHint.prefetch(obj) requires a django.db.models.Prefetch instance; "
            "got RaisingClass."
        )


class TestSkipPredicate:
    """``hint_is_skip`` answers the skip directive for every hint shape."""

    def test_skip_shapes(self) -> None:
        """``None`` and a shape without ``.skip`` are not skips; ``SKIP`` is."""
        assert hint_is_skip(None) is False
        assert hint_is_skip(OptimizerHint.SKIP) is True
        assert hint_is_skip(OptimizerHint.select_related()) is False
        # basedpyright: a shape without ``.skip`` is the input under test; hint_is_skip types
        # the parameter as OptimizerHint | None
        assert hint_is_skip(object()) is False  # pyright: ignore[reportArgumentType]

    def test_hostile_skip_shapes_propagate(self) -> None:
        """A hint whose ``skip`` read or truth test raises lets that error through."""
        # ``OptimizerHint.__post_init__`` reads ``skip``, so the hostile read arms only once
        # construction is done.
        armed = False

        class HostileAttribute(OptimizerHint):
            @override
            def __getattribute__(self, name: str) -> object:
                if armed and name == "skip":
                    raise RuntimeError("skip read failed")
                return object_result(super().__getattribute__, name)

        class HostileBoolean:
            def __bool__(self) -> bool:
                raise RuntimeError("bool failed")

        hostile_attribute = HostileAttribute()
        armed = True
        hostile_value = OptimizerHint()
        object.__setattr__(hostile_value, "skip", HostileBoolean())

        with pytest.raises(RuntimeError, match="skip read failed"):
            hint_is_skip(hostile_attribute)
        with pytest.raises(RuntimeError, match="bool failed"):
            hint_is_skip(hostile_value)
