"""AppConfig tests for package registration and upstream patch dispatch.

``DjangoStrawberryFrameworkConfig`` is Django app-loader state: the class
identity, ``name`` / ``verbose_name``, registry pickup, the AppConfig attributes
the package refuses to set, and ``ready()`` as the process-wide dispatcher for
the four upstream-patch appliers. None of that is a GraphQL wire shape. A live
``/graphql/`` request can show that a patched parse is in effect; it cannot show
that ``ready()`` was the caller, that a reloaded applier kept its upstream
capture, or that the AppConfig omitted ``default_auto_field``.

Request-shaped outcomes of the patches ``ready()`` dispatches live in
``examples/fakeshop/test_query/test_products_api.py`` (GET
``parse_query_params`` shield) and
``examples/fakeshop/test_query/test_transport_api.py`` (body cap, UTF-8,
``APPLY_UPSTREAM_PATCHES`` opt-out). Per-module ``apply()`` install lifecycle
stays in ``tests/test_django_patches.py``, ``tests/test_strawberry_patches.py``,
``tests/test_cross_web_patches.py``, and ``tests/test_graphql_core_patches.py``.
"""

import importlib
from types import ModuleType

import django.apps
import pytest
from cross_web import DjangoHTTPRequestAdapter
from django.test.testcases import SimpleTestCase
from graphql.execution.execute import ExecutionContext
from strawberry.http.async_base_view import AsyncBaseHTTPView
from strawberry.http.base import BaseView
from strawberry.http.sync_base_view import SyncBaseHTTPView
from strawberry.relay import types as relay_types

from django_strawberry_framework import (
    _cross_web_patches,
    _django_patches,
    _graphql_core_patches,
    _strawberry_patches,
)
from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig
from django_strawberry_framework.utils import truth
from django_strawberry_framework.utils._narrowing import read_attr


def test_djangostrawberryframeworkconfig_is_appconfig_subclass() -> None:
    assert issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)


@pytest.mark.parametrize(
    ("attribute", "expected"),
    [("name", "django_strawberry_framework"), ("verbose_name", "Django Strawberry Framework")],
    ids=["name", "verbose-name"],
)
def test_djangostrawberryframeworkconfig_pins_name_and_verbose_name(
    attribute: str,
    expected: str,
) -> None:
    assert getattr(DjangoStrawberryFrameworkConfig, attribute) == expected


def test_djangostrawberryframeworkconfig_resolves_through_django_app_registry() -> None:
    config = django.apps.apps.get_app_config("django_strawberry_framework")
    assert isinstance(config, DjangoStrawberryFrameworkConfig)


@pytest.mark.parametrize(
    ("attribute", "why"),
    [
        ("label", "spec-021 Decision 2 (default last-segment label is already unique)"),
        ("default_auto_field", "spec-021 Decision 5 (package ships zero Django models)"),
        ("default", "spec-021 Decision 8 (no `default` attribute at any value)"),
    ],
    ids=["label", "default-auto-field", "default"],
)
def test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes(
    attribute: str,
    why: str,
) -> None:
    """The AppConfig class body omits ``label``, ``default_auto_field``, and ``default``.

    ``ready`` is deliberately absent from this set: it is required on this class,
    not forbidden. The package ships a ``ready()`` body that dispatches the four
    upstream patch modules' ``apply()`` calls, and the ``ready`` tests below pin
    it positively. See ``django_strawberry_framework/apps.py`` ``ready()``
    docstring and the four ``_*_patches`` module docstrings.
    """
    assert attribute not in DjangoStrawberryFrameworkConfig.__dict__, (
        f"{attribute!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"
    )


# Every upstream class attribute, then every upstream module global, the four patch
# modules replace. A test that drives ``apply()`` (directly or through ``ready()``)
# mutates process-global state at each of these slots, so a test that also perturbs the
# patch modules themselves restores both halves from these two tables.
_PATCHED_SLOTS = (
    (SimpleTestCase, "_remove_databases_failures"),
    (BaseView, "parse_json"),
    (BaseView, "parse_query_params"),
    (SyncBaseHTTPView, "parse_multipart"),
    (AsyncBaseHTTPView, "parse_multipart"),
    (DjangoHTTPRequestAdapter, "body"),
    (ExecutionContext, "complete_list_value"),
    (relay_types.ListConnection, "resolve_connection"),
)


_PATCHED_MODULE_SLOTS = ((relay_types, "should_resolve_list_connection_edges"),)


def _all_patches_installed() -> tuple[bool, bool, bool, bool]:
    return (
        _django_patches._patch_is_installed(),
        _strawberry_patches._patch_is_installed(),
        _cross_web_patches._patch_is_installed(),
        _graphql_core_patches._patch_is_installed(),
    )


def test_ready_dispatches_all_four_patch_appliers_and_refires_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``ready()`` itself installs all four upstream patches; a re-fire is safe.

    The patch-module suites each pin "installed at collection via
    ``ready()``", but in the three suites that split that assertion from
    idempotence the direct ``apply()`` calls ``test_apply_is_idempotent``
    makes earlier in file order on the same worker mask it - a ``ready()``
    that lost one of those three dispatch lines would still pass them.
    (The graphql-core suite's combined test asserts installed before
    applying.) This test owns the dispatch contract deterministically
    for every member: it reverts all four patches to the captured
    upstream originals, drives ``ready()`` through the registered
    AppConfig, and asserts every patch is installed. A second
    ``ready()`` pins dispatch-layer idempotence (some Django test
    runners fire it more than once).
    """
    monkeypatch.setattr(
        SimpleTestCase,
        "_remove_databases_failures",
        _django_patches._original_remove_databases_failures,
    )
    monkeypatch.setattr(BaseView, "parse_json", _strawberry_patches._original_parse_json)
    monkeypatch.setattr(
        BaseView,
        "parse_query_params",
        _strawberry_patches._original_parse_query_params,
    )
    original_connection = _strawberry_patches._original_relay_list_connection
    assert callable(original_connection)
    monkeypatch.setattr(
        relay_types.ListConnection,
        "resolve_connection",
        classmethod(original_connection),
    )
    monkeypatch.setattr(
        relay_types,
        "should_resolve_list_connection_edges",
        _strawberry_patches._original_should_resolve_list_connection_edges,
    )
    monkeypatch.setattr(
        DjangoHTTPRequestAdapter,
        "body",
        property(_cross_web_patches._original_body_fget),
    )
    monkeypatch.setattr(
        ExecutionContext,
        "complete_list_value",
        _graphql_core_patches._original_complete_list_value,
    )
    assert _all_patches_installed() == (
        False,
        False,
        False,
        False,
    )

    config = django.apps.apps.get_app_config("django_strawberry_framework")
    config.ready()
    assert _all_patches_installed() == (
        True,
        True,
        True,
        True,
    )

    config.ready()
    assert _all_patches_installed() == (
        True,
        True,
        True,
        True,
    )


@pytest.mark.parametrize(
    ("module", "original_names"),
    [
        (_django_patches, ("_original_remove_databases_failures",)),
        (
            _strawberry_patches,
            (
                "_original_parse_json",
                "_original_parse_query_params",
                "_original_sync_parse_multipart",
                "_original_async_parse_multipart",
                "_original_should_resolve_list_connection_edges",
                "_original_relay_list_connection",
            ),
        ),
        (_cross_web_patches, ("_original_body_fget",)),
        (_graphql_core_patches, ("_original_complete_list_value",)),
    ],
    ids=[
        "django",
        "strawberry",
        "cross-web",
        "graphql-core",
    ],
)
def test_ready_reinstalls_patches_after_their_modules_reload(
    module: ModuleType,
    original_names: tuple[str, ...],
) -> None:
    """A reloaded applier retains its true upstream capture and re-installs cleanly.

    An interactive test session can reload a private patch module while its
    process-global method replacement remains installed. The next AppConfig
    ``ready()`` call must distinguish that prior package replacement from an
    unsupported upstream change: retain the original capture, then install the
    reloaded replacement instead of rejecting the prior replacement's source.

    Each module is reloaded TWICE. The first pass reloads a module whose
    installed replacement was built by the module's original execution; the
    second reloads one whose installed replacement is itself a product of the
    first reload, so the capture contract is pinned for repeated reloads rather
    than only for the first one.

    The reload rebinds every module global (captures, replacements, and the
    identity operands each ``_patch_is_installed`` compares against), and
    ``ready()`` then writes the post-reload replacements onto the upstream
    classes. Both halves are process-global and both are restored together:
    restoring only the class attributes would leave them pointing at
    pre-reload objects while the modules hold post-reload ones, i.e. every
    ``_patch_is_installed`` reporting a spurious ``False`` for the rest of the
    worker's run.
    """
    config = django.apps.apps.get_app_config("django_strawberry_framework")
    saved_namespace = dict(module.__dict__)
    saved_slots = (
        *(
            (owner, attribute, truth.class_dict(owner)[attribute])
            for owner, attribute in _PATCHED_SLOTS
        ),
        *(
            (module_owner, attribute, read_attr(module_owner, attribute))
            for module_owner, attribute in _PATCHED_MODULE_SLOTS
        ),
    )
    try:
        original_captures = tuple(getattr(module, name) for name in original_names)

        importlib.reload(module)
        assert tuple(getattr(module, name) for name in original_names) == original_captures
        config.ready()
        assert _all_patches_installed() == (
            True,
            True,
            True,
            True,
        )

        importlib.reload(module)
        assert tuple(getattr(module, name) for name in original_names) == original_captures
        config.ready()
        assert _all_patches_installed() == (
            True,
            True,
            True,
            True,
        )
    finally:
        module.__dict__.clear()
        module.__dict__.update(saved_namespace)
        for owner, attribute, descriptor in saved_slots:
            setattr(owner, attribute, descriptor)
