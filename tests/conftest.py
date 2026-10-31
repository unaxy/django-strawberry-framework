"""Shared package-test fixtures: registry isolation, script imports, stop signals, budgets."""

import importlib
import signal
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.registry import registry
from django_strawberry_framework.resource_policy import (
    begin_resource_budget,
    end_resource_budget,
)

if TYPE_CHECKING:
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
