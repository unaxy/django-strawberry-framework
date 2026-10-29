"""Defensive patches for upstream Django bugs, applied at app load.

The package ships fixes for a small set of Django bugs that affect
consumers of ``django-strawberry-framework`` in multi-database setups.
The patches are applied once from the package's
:meth:`apps.DjangoStrawberryFrameworkConfig.ready`, so consumers get
them automatically by having ``"django_strawberry_framework"`` in
``INSTALLED_APPS`` - no opt-in boilerplate (no ``conftest.py``
workaround, no test-case base class to inherit) is required on the
consumer side. Like every patch the package ships, it is gated by the
``APPLY_UPSTREAM_PATCHES`` setting (default on): a consumer who wants
the package to apply no patches at all sets
``DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}``,
and a consumer who wants to disable only this module's test-only patch
(for example while upgrading Django ahead of the package) sets the
per-dependency mapping ``{"APPLY_UPSTREAM_PATCHES": {"django":
False}}``, which leaves the production request-hardening patches
(``strawberry`` / ``cross_web``) installed. See
:func:`django_strawberry_framework.conf.upstream_patches_enabled`.

Currently implemented
---------------------

- :func:`_patched_remove_databases_failures` - defensive wrapper
  around :meth:`django.test.testcases.SimpleTestCase._remove_databases_failures`.
  Django defines the method on ``SimpleTestCase`` so a single patch
  covers every test-case class in Django's hierarchy
  (``SimpleTestCase`` -> ``TransactionTestCase`` -> ``TestCase``).
  Before delegating to Django's own classmethod, it wraps each
  connection method that something replaced between ``setUpClass``
  and ``tearDownClass`` in a ``_DatabaseFailure`` of its own, so
  Django's unwrap restores the replacement instead of crashing the
  cleanup loop with ``AttributeError: 'function' object has no
  attribute 'wrapped'``. The method list is read from either home
  Django has kept it in (a ``SimpleTestCase`` class attribute up to
  Django 6.0, a per-connection feature flag from 6.1) - see
  :func:`_disallowed_connection_methods`.

  Tracks Django Trac #37064 (closed upstream as ``wontfix``):
  <https://code.djangoproject.com/ticket/37064>.

Ecosystem precedent
-------------------

Two ``django-debug-toolbar`` fixes point at the same underlying
monkey-patch fragility from opposite directions.

First, the ``isinstance(_, _DatabaseFailure)`` guard pattern is not
unique to this package. ``django-debug-toolbar`` ships the same pattern
at the SQL panel's *wrap-time* site:
:func:`debug_toolbar.panels.sql.tracking.wrap_cursor` checks
``isinstance(connection.cursor, _DatabaseFailure)`` before installing
its own cursor wrapper and refuses to wrap on top of Django's
``_DatabaseFailure``:

  <https://github.com/django-commons/django-debug-toolbar/blob/main/debug_toolbar/panels/sql/tracking.py>

This package installs the matching check at the *unwrap-time* site so
the same Django fragility cannot crash teardown regardless of which
third-party library (debug-toolbar, Sentry's Django integration, a
consumer's own ``setUp``, or anything else) replaced the wrapper.

Second, ``django-debug-toolbar``'s cache-panel fix for Sentry
interoperability reached the broader teardown conclusion: once multiple
parties can monkey-patch the same method, undoing the patch stack
perfectly can be impossible without a shared ordering protocol. That
fix kept the debug-toolbar wrapper installed and toggled an owner
sentinel instead of trying to uninstall/reinstall around every request.
That exact strategy is available to libraries that own their wrapper,
and it is the right pattern for any future package-owned connection
instrumentation here.

This package does not own Django's ``_DatabaseFailure`` wrapper, so it
cannot adopt the cache-panel sentinel approach for
``_remove_databases_failures`` itself. The best root-cause mitigation
available at this layer is the combined guard strategy:

* **Wrap-time prevention** (debug-toolbar SQL panel's flavor, and this
  package's ``safe_wrap_connection_method`` helper) - each well-behaved
  wrap-party declines to clobber Django's wrapper when it sees one
  already installed. This is the cheapest path because it avoids
  installing another wrapper at all.

* **Unwrap-time recovery** (this package's automatic patch) - Django's
  teardown becomes robust to wrappers having been replaced anyway. This
  is necessary because this package cannot force every third-party
  wrapper to participate in the wrap-time protocol.

The two guards don't fix the underlying multi-party mutation design,
but together they protect against the worst observable symptom -
crashes during ``tearDownClass`` - at the two lifecycle sites this
package can influence.

This package wraps a connection method only transiently, inside the
teardown it patches, so it has no lasting wrap-time site of its OWN
at which to add the debug-toolbar-style preventive check. Instead the
package ships
:func:`django_strawberry_framework.testing.safe_wrap_connection_method`
as a consumer-facing helper: any consumer code path that wraps a
connection method (typically in a test ``setUp`` or in middleware)
calls the helper instead of raw ``setattr``, and the helper applies
the same wrap-time isinstance check debug-toolbar uses. Consumers who
use the helper are auto-protected at the wrap site; consumers who
don't (or who use a third-party library that doesn't) are still
auto-protected at the unwrap site by the patch in this module.

Surface visibility
------------------

The patch module is intentionally private (leading underscore on the
module). Consumers do not import from this module; the patch is
applied as a side effect of Django's app-loading. The :func:`apply`
entry point is exported (no leading underscore) so the package's
regression tests can call it explicitly without going through the
AppConfig.
"""

import inspect
from typing import TYPE_CHECKING, cast

from django.db import connections
from django.db.backends.base.features import BaseDatabaseFeatures
from django.test.testcases import SimpleTestCase

from .conf import upstream_patches_enabled
from .utils import truth
from .utils._narrowing import read_attr, require

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.test.testcases import _DatabaseFailure as _DatabaseFailureClass
    from typing_extensions import TypeIs

# Every audited Django release (5.2 - 6.1) defines this private wrapper; ``None``
# is the drift sentinel for a release that renames or removes it.
_DatabaseFailure: "type[_DatabaseFailureClass] | None"
try:
    from django.test.testcases import _DatabaseFailure as _imported_database_failure
except ImportError:  # pragma: no cover - every supported release imports; tests patch the sentinel
    # Preserve module import long enough for ``apply()`` to report the precise
    # unsupported upstream shape and the explicit opt-out.
    _DatabaseFailure = None
else:
    _DatabaseFailure = _imported_database_failure


_PATCH_OWNER_ATTRIBUTE = "_django_strawberry_framework_patch_owner"
_PATCH_ORIGINAL_ATTRIBUTE = "_django_strawberry_framework_original"
_PATCH_OWNER = "django_strawberry_framework._django_patches"

# The two homes of Django's ``(name, operation)`` list of disallowed connection
# methods: the connection feature flag from Django 6.1, the ``SimpleTestCase``
# class attribute before it.
_FEATURE_METHODS = "disallowed_simple_test_case_connection_methods"
_CLASS_METHODS = "_disallowed_connection_methods"


def _captured_upstream_descriptor() -> object:
    """Return Django's descriptor, retaining it across an in-process reload.

    ``importlib.reload()`` retains the module dictionary but re-executes this
    module while ``SimpleTestCase`` still points at the previous replacement.
    Reading that replacement as the original turns the next ``ready()`` into a
    false upstream-drift error. The replacement carries its exact captured
    descriptor, so reload can recover and revalidate that upstream contract
    rather than treating this package's own prior function as Django code.
    """
    descriptor = truth.class_dict(SimpleTestCase).get("_remove_databases_failures")
    function = descriptor.__func__ if truth.is_instance(descriptor, classmethod) else None
    if getattr(function, _PATCH_OWNER_ATTRIBUTE, None) == _PATCH_OWNER:
        return getattr(function, _PATCH_ORIGINAL_ATTRIBUTE, None)
    return descriptor


_original_remove_databases_failures = _captured_upstream_descriptor()


def _upstream_function() -> "Callable[[type[SimpleTestCase]], object] | None":
    """Return the function behind Django's captured classmethod, or ``None`` when it is none."""
    descriptor = _original_remove_databases_failures
    return descriptor.__func__ if truth.is_instance(descriptor, classmethod) else None


def _validate_upstream_shape() -> None:
    """Fail loudly when Django no longer matches the private shape this patch delegates to.

    Three checks: the private symbols exist (``_DatabaseFailure`` plus the
    ``_remove_databases_failures`` classmethod descriptor), the ``(cls)``
    call shape holds, and Django still keeps its list of disallowed
    connection methods in one of its two homes (the connection feature
    flag, or the ``SimpleTestCase`` class attribute before it), which
    :func:`_disallowed_connection_methods` reads to find the methods to
    re-wrap.
    """
    function = _upstream_function()
    if _DatabaseFailure is None or not callable(function):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: expected "
            "django.test.testcases._DatabaseFailure and "
            "SimpleTestCase._remove_databases_failures as a classmethod. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} '
            "or use a supported Django version.",
        )
    parameters = tuple(inspect.signature(function).parameters.values())
    if len(parameters) != 1 or parameters[0].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: "
            "SimpleTestCase._remove_databases_failures no longer has the expected (cls) signature. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} '
            "or use a supported Django version.",
        )
    if read_attr(BaseDatabaseFeatures, _FEATURE_METHODS, None) is None and (
        read_attr(SimpleTestCase, _CLASS_METHODS, None) is None
    ):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: "
            "Django no longer keeps its disallowed connection methods where this patch reads them. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} '
            "or use a supported Django version.",
        )


def _is_database_failure(method: object) -> "TypeIs[_DatabaseFailureClass]":
    """Return whether ``method`` is Django's disallowed-database wrapper."""
    return _DatabaseFailure is not None and isinstance(method, _DatabaseFailure)


def _disallowed_connection_methods(
    cls: type[SimpleTestCase],
    connection: "BaseDatabaseWrapper",
) -> list[tuple[str, str]]:
    """Return the ``(name, operation)`` pairs Django wrapped on ``connection``.

    Django 6.1 reads the pairs per connection from the feature flag
    ``disallowed_simple_test_case_connection_methods``; Django 5.2.16-6.0.x
    read them from the ``SimpleTestCase._disallowed_connection_methods``
    class attribute. The flag's presence is the discriminator, never the
    class attribute's: a Django 6.1 subclass may still declare the legacy
    attribute, but ``_add_databases_failures`` ignores it and wraps the
    feature list, so cleanup reads that same list to stay symmetric. An
    empty flag list is still the flag's answer.
    """
    feature_pairs = read_attr(connection.features, _FEATURE_METHODS, None)
    return cast(
        "list[tuple[str, str]]",
        read_attr(cls, _CLASS_METHODS) if feature_pairs is None else feature_pairs,
    )


def _patched_remove_databases_failures(cls: type[SimpleTestCase]) -> None:
    """Run Django's own ``_remove_databases_failures``, leaving foreign replacements in place.

    Django's classmethod unwraps every disallowed connection method by
    reading ``method.wrapped``, so a method that something replaced
    between ``setUpClass`` and ``tearDownClass`` crashes it with
    ``AttributeError: 'function' object has no attribute 'wrapped'``.
    This patch first wraps each such foreign replacement in a
    ``_DatabaseFailure`` of its own; Django's unwrap then puts the
    replacement back exactly as it found it, and a genuine wrapper is
    unwrapped by Django itself. The method list is read through
    :func:`_disallowed_connection_methods`, which covers both homes
    Django has kept it in.

    A foreign replacement that lives on the connection's class rather
    than on the instance (``mock.patch.object(BaseDatabaseWrapper,
    "cursor", ...)``) is read through the instance, so the re-wrap and
    Django's unwrap would leave an instance attribute shadowing the
    class-level replacement. Each such name is deleted from the
    instance afterwards, even when Django's call raises, so the
    connection ends where it started.

    The guard is the unwrap-time mirror of the wrap-time
    ``isinstance`` check ``django-debug-toolbar`` uses in
    :func:`debug_toolbar.panels.sql.tracking.wrap_cursor` (which
    declines to install a debug-cursor wrapper on top of a
    ``_DatabaseFailure``). Two pragmatic mitigations of the same
    underlying multi-party-wrap fragility, applied at the two
    lifecycle sites each library controls. See module docstring for
    the upstream ticket reference and the defense-in-depth framing.
    """
    failure = _DatabaseFailure
    shadowing: list[tuple[BaseDatabaseWrapper, str]] = []
    for alias in connections:
        if alias in cls.databases:
            continue
        connection = connections[alias]
        namespace = truth.instance_state(connection)
        for name, _ in _disallowed_connection_methods(cls, connection):
            method = read_attr(connection, name)
            if failure is None or isinstance(method, failure):
                continue
            if name not in namespace:
                shadowing.append((connection, name))
            setattr(connection, name, failure(method, ""))
    try:
        _ = require(_upstream_function(), callable)(cls)
    finally:
        for connection, name in shadowing:
            delattr(connection, name)


setattr(_patched_remove_databases_failures, _PATCH_OWNER_ATTRIBUTE, _PATCH_OWNER)
setattr(
    _patched_remove_databases_failures,
    _PATCH_ORIGINAL_ATTRIBUTE,
    _original_remove_databases_failures,
)


def _patch_is_installed() -> bool:
    """Return ``True`` iff ``SimpleTestCase._remove_databases_failures`` currently points at our patch.

    Encapsulates the ``__func__`` unwrap so ``apply()`` does not need to
    know that Django stores the method as a ``classmethod`` descriptor
    on the class. Used by ``apply()`` to enforce the "ensure current
    state" contract - if a third party reverted the class attribute
    after a prior ``apply()`` call, the next ``apply()`` re-installs.
    """
    installed = truth.class_dict(SimpleTestCase).get("_remove_databases_failures")
    if installed is None:
        return False
    return (
        truth.is_instance(installed, classmethod)
        and installed.__func__ is _patched_remove_databases_failures
    )


def apply() -> None:
    """Apply every Django defensive patch shipped by the package.

    Gated by the ``APPLY_UPSTREAM_PATCHES`` setting (default on):
    returns immediately, before touching ``SimpleTestCase``, when a
    consumer disabled the patches globally (``False``) or this
    dependency alone (``{"django": False}``).

    Idempotent and self-healing: re-entrant calls are no-ops when the
    patch is still installed, and re-install the patch if a third
    party reverted the class attribute since the prior call. Called
    from
    :meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`
    at Django startup (which may itself fire more than once under some
    Django test runners - the ``_patch_is_installed()`` check below
    handles both the re-entrant case and a third-party revert);
    exposed at the module level so the regression tests can drive the
    apply-and-revert cycle without spinning up a second AppConfig.

    Before installation, validates the private symbol, classmethod
    descriptor, and ``(cls)`` signature the replacement delegates to,
    plus the presence of Django's list of disallowed connection methods
    (see :func:`_validate_upstream_shape`). Dependency drift raises a
    targeted ``RuntimeError`` instead of silently dropping the
    protection; consumers can explicitly disable this test-only patch
    alone (``{"django": False}``) - or every upstream patch (``False``) -
    through ``APPLY_UPSTREAM_PATCHES`` while upgrading dependencies.
    """
    if not upstream_patches_enabled("django"):
        return
    _validate_upstream_shape()
    if _patch_is_installed():
        return
    # basedpyright: django-stubs omits the private classmethod, which reads as an unknown attribute
    SimpleTestCase._remove_databases_failures = classmethod(  # pyright: ignore[reportAttributeAccessIssue]
        _patched_remove_databases_failures,
    )
