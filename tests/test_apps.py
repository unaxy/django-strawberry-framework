"""AppConfig tests for package registration and upstream patch dispatch.

``DjangoStrawberryFrameworkConfig`` is Django app-loader state: the class
identity, ``name`` / ``verbose_name``, registry pickup, the AppConfig attributes
the package refuses to set, and ``ready()`` as the process-wide dispatcher for
the Strawberry patch applier. None of that is a GraphQL wire shape. A live
``/graphql/`` request can show that the rebound connection-page check is in
effect; it cannot show that ``ready()`` was the caller, or that the AppConfig
omitted ``default_auto_field``.

The rebind's request-shaped outcome lives in
``examples/fakeshop/test_query/test_library_api.py``; the ``apply()`` install
lifecycle stays in ``tests/test_strawberry_patches.py``.
"""

import django.apps
import pytest
from strawberry.relay import types as relay_types
from strawberry.relay import utils as relay_utils

from django_strawberry_framework import _strawberry_patches
from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig
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
    not forbidden. The package ships a ``ready()`` body that dispatches the
    Strawberry patch module's ``apply()``, and the ``ready`` tests below pin it
    positively. See ``django_strawberry_framework/apps.py`` ``ready()``
    docstring and the ``_strawberry_patches`` module docstring.
    """
    assert attribute not in DjangoStrawberryFrameworkConfig.__dict__, (
        f"{attribute!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"
    )


def test_ready_dispatches_the_patch_applier_and_refires_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``ready()`` itself rebinds the connection-page check; a re-fire is safe.

    The direct ``apply()`` calls in ``tests/test_strawberry_patches.py`` would mask
    a ``ready()`` that lost its dispatch line, so this row restores upstream's
    check, drives ``ready()`` through the registered AppConfig, and asserts the
    rebind. A second ``ready()`` pins dispatch-layer idempotence (some Django test
    runners fire it more than once).
    """
    monkeypatch.setattr(
        relay_types,
        _strawberry_patches._EDGES_CHECK,
        relay_utils.should_resolve_list_connection_edges,
    )
    patched = _strawberry_patches._patched_should_resolve_list_connection_edges

    config = django.apps.apps.get_app_config("django_strawberry_framework")
    config.ready()
    assert read_attr(relay_types, _strawberry_patches._EDGES_CHECK) is patched

    config.ready()
    assert read_attr(relay_types, _strawberry_patches._EDGES_CHECK) is patched
