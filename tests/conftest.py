"""Shared package-test fixtures: registry isolation, script imports, stop signals, budgets.

Also the default-manager shapes a project writes (``default_manager_shape``), swapped onto a
library model for one test.
"""

import contextlib
import importlib
import signal
import sys
from collections.abc import Callable, Generator, Iterator
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest
from django.db import models
from django.db.models.sql import Query
from typing_extensions import Self

from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.registry import registry
from django_strawberry_framework.resource_policy import (
    begin_resource_budget,
    end_resource_budget,
)
from django_strawberry_framework.utils._narrowing import require_instance
from django_strawberry_framework.utils._queryset_private import super_clone_queryset

if TYPE_CHECKING:
    from django.db.models.options import Options

    from django_strawberry_framework import ResourcePolicy
    from django_strawberry_framework.resource_policy import _BudgetScope


@pytest.fixture
def isolate_global_registry() -> Iterator[None]:
    """Clear the global registry and the connection-type cache around a test.

    The shared test-isolation invariant for modules that declare fresh
    function-scope ``DjangoType`` classes: connection classes are cached on
    ``target_type`` identity, so a discarded class must not leak into a later
    test's identity check (the ``tests/test_connection.py`` fixture shape).
    Opt-in - a module declares ``pytestmark =
    pytest.mark.usefixtures("isolate_global_registry")`` so the invariant has
    ONE implementation without imposing the clears on suites that use the
    shipped fakeshop types. A function-level ``usefixtures`` mark is requested
    before the module mark, so a fixture that must see the cleared registry takes
    it as an explicit argument or is requested by an argument instead.
    """
    registry.clear()
    _connection_type_cache.clear()
    yield
    registry.clear()
    _connection_type_cache.clear()


@pytest.fixture
def scripts_module(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], ModuleType]:
    """Return ``load(name)``, importing ``scripts/<name>.py`` the way the script runs.

    The scripts directory leads ``sys.path`` for the test, so a script's bare
    sibling imports resolve; ``monkeypatch`` restores ``sys.path`` afterwards. Import
    caches are invalidated first, as ``MonkeyPatch.syspath_prepend`` does, so a
    directory the finder already cached is re-listed.
    """
    scripts_dir = str(Path(__file__).resolve().parents[1] / "scripts")
    monkeypatch.setattr(sys, "path", [scripts_dir, *sys.path])
    importlib.invalidate_caches()

    def load(name: str) -> ModuleType:
        return importlib.import_module(name)

    return load


# The signals that ask a run to stop, spelled out as the stop-signal test modules spell them.
_STOP_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM,
    signal.SIGHUP,
    signal.SIGQUIT,
)


@pytest.fixture
def stop_signals_at_default() -> Iterator[None]:
    """Give every stop signal pytest inherited as ignored its default action for one test.

    ``SIG_IGN`` survives ``exec``: pytest started as a background job of a
    non-interactive shell ignores ``SIGINT`` and ``SIGQUIT``, under ``nohup``
    it ignores ``SIGHUP``, and every process a test starts inherits the same.
    ``scripts/_stop_signals.py::routed_to`` leaves an inherited ``SIG_IGN``
    alone by contract, so a row that signals a run it started would measure
    how pytest was launched instead of the script. Each ignored signal gets the
    disposition an interpreter starts with (``default_int_handler`` for
    ``SIGINT``, ``SIG_DFL`` for the rest) and is ignored again at teardown; a
    signal that was not ignored is left as it was. A row about an inherited
    ``SIG_IGN`` sets it on the process it starts.
    """
    ignored = [signum for signum in _STOP_SIGNALS if signal.getsignal(signum) == signal.SIG_IGN]
    for signum in ignored:
        default = signal.default_int_handler if signum == signal.SIGINT else signal.SIG_DFL
        signal.signal(signum, default)
    yield
    for signum in ignored:
        signal.signal(signum, signal.SIG_IGN)


@pytest.fixture
def arm_resource_budget() -> "Iterator[Callable[[object, ResourcePolicy], None]]":
    """Return ``arm(context, policy)``, arming a budget the way the resource extension does.

    ``begin_resource_budget`` is the production entry point: it arms the policy
    the enforcement seams read and publishes the consumer-readable mirror. Every
    budget armed through ``arm`` is ended at teardown, so no armed budget
    outlives the test that armed it.
    """
    scopes: list[_BudgetScope] = []

    def arm(context: object, policy: "ResourcePolicy") -> None:
        scopes.append(begin_resource_budget(context, policy))

    yield arm
    for scope in reversed(scopes):
        end_resource_budget(scope)


#: The value a shaped manager hides in its model's ``field``.
HIDDEN_BY_MANAGER = "zz-hidden"


class FromQuerySetShapeQuerySet(models.QuerySet[models.Model]):
    """The class ``Manager.from_queryset`` builds a manager from."""

    def project_rows(self) -> Self:
        """A project method a hook can call."""
        return self.all()


class HandWrittenShapeQuerySet(models.QuerySet[models.Model]):
    """The class a hand-written ``get_queryset`` constructs."""

    def project_rows(self) -> Self:
        """A project method a hook can call."""
        return self.all()


class PolymorphicShapeQuerySet(models.QuerySet[models.Model]):
    """django-polymorphic's ``PolymorphicQuerySet`` shape: ``__init__`` state ``_clone`` carries."""

    shape_state: bool

    def __init__(
        self,
        model: type[models.Model] | None = None,
        query: Query | None = None,
        using: str | None = None,
        hints: dict[str, models.Model] | None = None,
    ) -> None:
        """Construct as ``QuerySet`` does, then set the state ``_clone`` carries."""
        super().__init__(model=model, query=query, using=using, hints=hints)
        self.shape_state = True

    def _clone(self) -> Self:
        clone = super_clone_queryset(PolymorphicShapeQuerySet, self)
        assert isinstance(clone, type(self))
        clone.shape_state = self.shape_state
        return clone

    def project_rows(self) -> Self:
        """A project method a hook can call."""
        return self.all()


def _shape_manager(shape: str, field: str) -> tuple[models.Manager[models.Model], type]:
    """Return a manager of ``shape`` hiding ``field == HIDDEN_BY_MANAGER``, and its class.

    The ``annotating`` shape hides nothing: it annotates ``field`` as the constant ``1``.
    """
    hidden = {field: HIDDEN_BY_MANAGER}
    if shape == "annotating":

        def annotating_rows(self: models.Manager[models.Model]) -> models.QuerySet[models.Model]:
            return HandWrittenShapeQuerySet(self.model, using=self._db).annotate(
                **{field: models.Value(1)},
            )

        manager_cls = type(
            "HandWrittenAnnotating",
            (models.Manager,),
            {"get_queryset": annotating_rows},
        )
        return manager_cls(), HandWrittenShapeQuerySet

    if shape == "from_queryset":
        base = models.Manager[models.Model].from_queryset(FromQuerySetShapeQuerySet)

        def from_queryset_rows(
            self: models.Manager[models.Model],
        ) -> models.QuerySet[models.Model]:
            return base.get_queryset(self).exclude(**hidden)

        manager_cls = type("FromQuerySetHiding", (base,), {"get_queryset": from_queryset_rows})
        return require_instance(manager_cls(), base), FromQuerySetShapeQuerySet

    if shape == "hand_written":

        def hand_written_rows(self: models.Manager[models.Model]) -> models.QuerySet[models.Model]:
            return HandWrittenShapeQuerySet(self.model, using=self._db).exclude(**hidden)

        manager_cls = type(
            "HandWrittenHiding",
            (models.Manager,),
            {"get_queryset": hand_written_rows},
        )
        return manager_cls(), HandWrittenShapeQuerySet

    def polymorphic_rows(self: models.Manager[models.Model]) -> models.QuerySet[models.Model]:
        # ``PolymorphicManager.get_queryset``: its ``queryset_class``, narrowed on a proxy.
        return PolymorphicShapeQuerySet(self.model, using=self._db).exclude(**hidden)

    manager_cls = type(
        "PolymorphicHiding",
        (models.Manager,),
        {"queryset_class": PolymorphicShapeQuerySet, "get_queryset": polymorphic_rows},
    )
    return manager_cls(), PolymorphicShapeQuerySet


def _expire_managers(options: "Options[models.Model]") -> None:
    """Drop the manager reads ``Options`` caches, as ``Options._expire_cache`` does."""
    cache = vars(options)
    for name in (
        "managers",
        "managers_map",
        "base_manager",
        "default_manager",
    ):
        if name in cache:
            del cache[name]


@contextlib.contextmanager
def _swapped_manager(
    model: type[models.Model],
    shape: str,
    field: str,
) -> Generator[type, None, None]:
    manager, queryset_class = _shape_manager("hand_written" if shape == "base" else shape, field)
    options = model._meta
    saved = (options.default_manager_name, options.base_manager_name)
    model.add_to_class("shape_rows", manager)
    if shape == "base":
        options.base_manager_name = "shape_rows"
    else:
        options.default_manager_name = "shape_rows"
    _expire_managers(options)
    try:
        yield queryset_class
    finally:
        options.default_manager_name, options.base_manager_name = saved
        options.local_managers.remove(manager)
        delattr(model, "shape_rows")
        _expire_managers(options)


@pytest.fixture
def default_manager_shape() -> Callable[
    [type[models.Model], str, str],
    contextlib.AbstractContextManager[type],
]:
    """Return a context manager making a hiding manager ``model``'s default for a block.

    ``shape`` is how a project writes it: ``from_queryset`` (``Manager.from_queryset`` with a
    filtering ``get_queryset`` override), ``hand_written`` (a ``get_queryset`` returning its own
    ``QuerySet`` class, filtered) or ``polymorphic`` (django-polymorphic's manager shape: a
    ``queryset_class`` whose ``__init__`` sets state ``_clone`` carries); ``base`` makes the
    ``hand_written`` manager the ``Meta.base_manager_name`` instead, the default untouched. Each
    hides the rows whose ``field`` is ``HIDDEN_BY_MANAGER``, except ``annotating``, a
    ``hand_written`` manager annotating ``field`` as ``1`` instead; the block receives the
    ``QuerySet`` class it returns.
    """
    return _swapped_manager
