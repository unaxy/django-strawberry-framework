"""Django patch tests for DB connection wrapping and multi-database safety.

Repo / test-runner patch lifecycle for
:mod:`django_strawberry_framework._django_patches`, applied at app-load
by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.
These rows pin ``apply()`` idempotence and self-heal, the identity of
the ``SimpleTestCase._remove_databases_failures`` replacement (and its
inheritance onto ``TransactionTestCase`` / ``TestCase``), the Trac
#37064 unwrap-vs-skip contract against synthetic test-case subclasses
(including a class-level replacement left unshadowed), both homes of
Django's disallowed-method list plus loud refusal when neither holds it, the
``APPLY_UPSTREAM_PATCHES`` global and per-dependency toggles, and
``importlib.reload()`` leaving a still-installed generation's teardown
valid.

The shipped patch hardens
``SimpleTestCase._remove_databases_failures`` against Django Trac
#37064 (closed upstream as ``wontfix``):
<https://code.djangoproject.com/ticket/37064>. Without it, replacing a
connection method between ``setUpClass`` and ``tearDownClass`` crashes
cleanup with ``AttributeError: 'function' object has no attribute
'wrapped'``. Django defines the classmethod on ``SimpleTestCase``
itself, so one patch covers the whole hierarchy - including direct
``SimpleTestCase`` subclasses, which ``TransactionTestCase`` is not in
the MRO of.

A live ``/graphql/`` request cannot express any of this: GraphQL
execution never runs Django's test-case cleanup loop, never calls
``apply()``, and cannot observe whether a classmethod descriptor on
``SimpleTestCase`` is this package's replacement. There is no live
sibling in ``examples/fakeshop/test_query/``.

These tests do not require ``FAKESHOP_SHARDED=1``; they drive the
patched method directly against synthetic ``SimpleTestCase`` /
``TransactionTestCase`` subclasses with hand-built ``databases``
allow-lists. The test ``default`` alias is always present, so a
one-alias multi-DB scenario is enough to exercise both branches of
the patched loop. A standalone demo project of this shape runs
under vanilla ``manage.py test`` rather than pytest-django and cannot
be reproduced 1:1 here: pytest-django's per-test flush calls
``connection.cursor()`` mid-lifecycle and crashes on the swapped
cursor before ``tearDownClass``.
"""

import importlib
from typing import TYPE_CHECKING, NoReturn
from unittest import mock

import pytest
import pytest_django
from django.db import connections
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.features import BaseDatabaseFeatures
from django.test.testcases import SimpleTestCase, TestCase, TransactionTestCase

from django_strawberry_framework import _django_patches
from django_strawberry_framework._django_patches import _CLASS_METHODS, _FEATURE_METHODS
from django_strawberry_framework.utils._narrowing import class_dict, read_attr
from tests._idioms import call_remove_databases_failures, remove_databases_failures_function

if TYPE_CHECKING:
    from typing_extensions import TypeIs


def _is_test_case_classmethod(value: object) -> "TypeIs[classmethod[SimpleTestCase, ..., object]]":
    """Whether ``value`` is a ``classmethod`` descriptor, the shape every captured upstream has."""
    return isinstance(value, classmethod)


def _database_failure(wrapped: object) -> object:
    if _django_patches._DatabaseFailure is None:
        pytest.skip("Django private _DatabaseFailure symbol is unavailable.")
    return _django_patches._DatabaseFailure(wrapped, "test message")


def test_apply_is_idempotent() -> None:
    """Repeated calls to :func:`apply` leave the patch installed.

    Pins the "ensure current state" contract called out in the
    _patch_is_installed docstring. AppConfig.ready() may run more than
    once under some Django test runners; the patch must tolerate that.
    """
    _django_patches.apply()
    _django_patches.apply()  # second call should be a self-healing no-op
    assert _django_patches._patch_is_installed() is True


def test_apply_reinstalls_when_class_attribute_reverted(monkeypatch: pytest.MonkeyPatch) -> None:
    """``apply()`` re-installs the patch if a third party reverted the class attribute.

    The revert happens between calls.

    Pins the strengthened "re-entrant calls are no-ops; the patch
    re-installs if not currently present" contract on ``apply()``.
    Without this, a misbehaving test that swapped
    ``SimpleTestCase._remove_databases_failures`` without restoring
    would leave the class permanently in the unpatched state for the
    rest of the process - and the next ``apply()`` call would silently
    decline to re-install.
    """
    _django_patches.apply()
    assert _django_patches._patch_is_installed() is True

    # ``monkeypatch`` saves the class ``__dict__`` entry, so teardown puts the
    # classmethod descriptor itself back (assigning a bound method back via the
    # attribute would replace the descriptor with a regular function and break
    # later tests).
    def _foreign(_cls: type[SimpleTestCase]) -> None:
        pass

    monkeypatch.setattr(SimpleTestCase, "_remove_databases_failures", classmethod(_foreign))
    assert _django_patches._patch_is_installed() is False

    _django_patches.apply()
    assert _django_patches._patch_is_installed() is True


def test_patch_is_installed_on_simple_test_case() -> None:
    """``SimpleTestCase._remove_databases_failures`` is the patched version after ``apply``.

    Django defines the method on ``SimpleTestCase`` (not on
    ``TransactionTestCase``), so the patch is installed there. By the
    time pytest starts collecting, the patched version should already
    be in place via ``AppConfig.ready()``.
    """
    assert (
        remove_databases_failures_function(SimpleTestCase)
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_inherited_by_transaction_test_case() -> None:
    """``TransactionTestCase`` inherits ``_remove_databases_failures`` from ``SimpleTestCase``.

    Patching the base class covers the subclass for free.
    """
    assert (
        remove_databases_failures_function(TransactionTestCase)
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_inherited_by_test_case() -> None:
    """``TestCase`` inherits ``_remove_databases_failures`` from ``SimpleTestCase``.

    The inheritance runs via ``TransactionTestCase``, so one patch covers the whole
    Django test-case hierarchy.
    """
    assert (
        remove_databases_failures_function(TestCase)
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin the ``installed is None`` branch of ``_patch_is_installed()``.

    Defensive contract: if a future Django release moves
    ``_remove_databases_failures`` off ``SimpleTestCase`` (e.g., onto a
    parent class, or removes it entirely),
    ``SimpleTestCase.__dict__.get(...)`` returns ``None`` rather than a
    classmethod descriptor. ``_patch_is_installed()`` must return
    ``False`` in that case so the next ``apply()`` call falls through
    to the install path rather than mis-reporting that the patch is
    already in place.
    """
    monkeypatch.delattr(SimpleTestCase, "_remove_databases_failures")
    assert "_remove_databases_failures" not in SimpleTestCase.__dict__
    assert _django_patches._patch_is_installed() is False


def test_patched_remove_databases_failures_unwraps_a_real_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Happy path: a genuine ``_DatabaseFailure`` on ``connection.<method>`` is unwrapped.

    The patched method unwraps it exactly as Django's upstream version does.

    Builds a ``TransactionTestCase`` subclass whose ``databases``
    allow-list excludes ``default``, wraps
    ``connections["default"].cursor`` with a ``_DatabaseFailure``
    pointing at an original (sentinel) callable, and invokes the
    patched method. The cursor must be restored to the sentinel.
    """

    class _NarrowTest(TransactionTestCase):
        databases = set()  # exclude every alias including default

    connection = connections["default"]
    original_cursor = connection.cursor
    sentinel = read_attr(mock.sentinel, "original_cursor")

    wrapper = _database_failure(sentinel)
    monkeypatch.setattr(connection, "cursor", wrapper)
    try:
        call_remove_databases_failures(_NarrowTest)
        # Wrapper unwrapped -> method now equals the sentinel.
        assert connection.cursor is sentinel
    finally:
        connection.cursor = original_cursor


def test_patched_remove_databases_failures_skips_non_wrapper_methods() -> None:
    """The Trac #37064 fix proper: a non-``_DatabaseFailure`` method is left alone.

    When ``connection.<method>`` is NOT a ``_DatabaseFailure`` instance (something
    replaced it without restoring the wrapper), the patched method leaves it alone
    instead of crashing on ``method.wrapped``.

    This is the load-bearing assertion of the whole patch - without
    the ``isinstance`` guard, the same setup raises
    ``AttributeError: 'function' object has no attribute 'wrapped'``.
    The companion test
    :func:`test_unpatched_remove_databases_failures_crashes_on_non_wrapper`
    pins that the crash IS real at our Django pin.
    """

    class _NarrowTest(TransactionTestCase):
        databases = set()  # exclude every alias including default

    connection = connections["default"]
    original_cursor = connection.cursor

    def _plain_cursor(*_args: object, **_kwargs: object) -> NoReturn:
        raise AssertionError("not a ``_DatabaseFailure`` wrapper; only its identity is read")

    connection.cursor = _plain_cursor
    try:
        # Should NOT raise.
        call_remove_databases_failures(_NarrowTest)
        # And the replacement is left untouched (the patch declines to
        # restore a wrapper it never installed).
        assert connection.cursor is _plain_cursor
    finally:
        connection.cursor = original_cursor


def test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass() -> None:
    """Direct ``SimpleTestCase`` subclasses must also get the unwrap-time protection.

    ``TransactionTestCase`` is NOT in their MRO.

    Pins that the patch is installed on ``SimpleTestCase`` itself, not
    only on ``TransactionTestCase``. Without this coverage, the patch
    silently bypasses the simplest kind of Django test class.
    """

    class _NarrowSimpleTest(SimpleTestCase):
        databases = set()  # exclude every alias including default

    # MRO sanity-check the test's premise: ``TransactionTestCase`` is
    # NOT in the inheritance chain.
    assert TransactionTestCase not in _NarrowSimpleTest.__mro__

    connection = connections["default"]
    original_cursor = connection.cursor

    def _plain_cursor(*_args: object, **_kwargs: object) -> NoReturn:
        raise AssertionError("not a ``_DatabaseFailure`` wrapper; only its identity is read")

    connection.cursor = _plain_cursor
    try:
        # Should NOT raise even though this class only inherits from
        # ``SimpleTestCase``. If the patch were still installed on
        # ``TransactionTestCase``, this call would raise.
        call_remove_databases_failures(_NarrowSimpleTest)
        assert connection.cursor is _plain_cursor
    finally:
        connection.cursor = original_cursor


def test_unpatched_remove_databases_failures_crashes_on_non_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pins that Trac #37064's bug shape IS still in Django at our pin.

    Temporarily reverts ``SimpleTestCase._remove_databases_failures`` to
    the genuine upstream classmethod the module captured at import time
    (``_original_remove_databases_failures``), exercises the same setup
    as the happy-path test above, and asserts that the crash happens
    inside the *installed* Django's own body. A Django upgrade that
    fixed the bug upstream makes this test fail (no ``AttributeError``
    raised), signalling that the package's patch can be retired. A
    hardcoded copy of the upstream body could not deliver that signal:
    the copy would keep crashing no matter what the installed Django
    ships.
    """
    captured = _django_patches._original_remove_databases_failures
    # Premise check: the import-time capture is genuinely upstream's
    # method, not this package's patch (the module is imported - and the
    # capture taken - before ``apply()`` ever runs).
    assert _is_test_case_classmethod(captured)
    assert captured.__func__.__module__ == "django.test.testcases"

    # ``monkeypatch`` saves the class ``__dict__`` entry, so teardown puts the patch
    # back in its native shape (a ``classmethod`` descriptor on ``SimpleTestCase``).
    monkeypatch.setattr(SimpleTestCase, "_remove_databases_failures", captured)

    class _NarrowTest(TransactionTestCase):
        databases = set()  # exclude every alias including default

    connection = connections["default"]
    original_cursor = connection.cursor

    def _plain_cursor(*_args: object, **_kwargs: object) -> NoReturn:
        raise AssertionError("not a ``_DatabaseFailure`` wrapper; only its identity is read")

    connection.cursor = _plain_cursor
    try:
        with pytest.raises(AttributeError, match="wrapped"):
            call_remove_databases_failures(_NarrowTest)
    finally:
        connection.cursor = original_cursor


def test_apply_fails_loudly_when_database_failure_symbol_missing() -> None:
    """A private-Django shape change cannot silently disable the teardown patch."""
    with (
        mock.patch.object(_django_patches, "_DatabaseFailure", None),
        pytest.raises(RuntimeError, match="_DatabaseFailure"),
    ):
        _django_patches.apply()


def test_apply_fails_loudly_when_upstream_method_signature_changes() -> None:
    """The patch pins the classmethod arity its replacement assumes."""

    def changed(_cls: type[SimpleTestCase], _extra: object) -> None:
        pass

    with (
        mock.patch.object(
            _django_patches,
            "_original_remove_databases_failures",
            classmethod(changed),
        ),
        pytest.raises(RuntimeError, match=r"expected \(cls\) signature"),
    ):
        _django_patches.apply()


@pytest.mark.parametrize("home", ["class_attribute", "feature_flag", "empty_feature_flag"])
def test_disallowed_methods_read_follows_the_home_django_keeps_them_in(
    home: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The method list comes from the feature flag when Django has one, else the class attribute.

    Django 5.2.16-6.0.x keep the ``(name, operation)`` pairs on the
    ``SimpleTestCase`` class attribute; Django 6.1 keeps them on the connection
    feature flag and ignores a legacy class attribute a subclass still declares,
    even when the flag's list is empty. Each home is staged on whichever Django
    is installed, against a synthetic ``cls``, so both reads run on every
    release. Only the read is staged: the teardown it feeds delegates to the
    installed Django's own body, which reads its own home, and the unwrap rows
    above pin that against the real home.
    """

    class _HomeCls(SimpleTestCase):
        databases = set()
        _disallowed_connection_methods = (("cursor", "queries"), ("chunked_cursor", "queries"))

    connection = connections["default"]
    if home == "class_attribute":
        monkeypatch.delattr(BaseDatabaseFeatures, _FEATURE_METHODS, raising=False)
        expected: object = _HomeCls._disallowed_connection_methods
    else:
        # A legacy override may survive a Django upgrade; Django 6.1's
        # ``_add_databases_failures`` ignores it and wraps the feature list, so
        # removal reads the feature list too.
        expected = [] if home == "empty_feature_flag" else [("cursor", "queries")]
        monkeypatch.setattr(connection.features, _FEATURE_METHODS, expected, raising=False)
    assert _django_patches._disallowed_connection_methods(_HomeCls, connection) is expected


def test_apply_fails_loudly_when_disallowed_method_list_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Django that keeps the method list in neither known home is refused, not patched.

    The patch reads the list to find the methods to re-wrap before delegating;
    with neither the connection feature flag nor the ``SimpleTestCase`` class
    attribute, it could re-wrap nothing and teardown would crash again on a
    foreign replacement. ``apply()`` must raise before installing anything.
    """

    def _foreign(_cls: type[SimpleTestCase]) -> None:
        pass

    monkeypatch.setattr(SimpleTestCase, "_remove_databases_failures", classmethod(_foreign))
    monkeypatch.delattr(BaseDatabaseFeatures, _FEATURE_METHODS, raising=False)
    monkeypatch.delattr(SimpleTestCase, _CLASS_METHODS, raising=False)
    with pytest.raises(RuntimeError, match="disallowed connection methods"):
        _django_patches.apply()
    assert _django_patches._patch_is_installed() is False


def test_patched_remove_databases_failures_leaves_a_class_level_replacement_unshadowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A foreign replacement on the connection's class stays the one the instance reads.

    ``mock.patch.object(BaseDatabaseWrapper, "cursor", ...)`` replaces the
    method on the class while the instance carries no ``cursor`` of its own.
    Re-wrapping it before Django's unwrap writes it onto the instance, so
    teardown must delete that instance attribute again: otherwise the
    instance keeps a frozen copy that outlives the class-level patch.
    """

    class _NarrowTest(TransactionTestCase):
        databases = set()  # exclude every alias including default

    connection = connections["default"]
    if "cursor" in vars(connection):
        # An earlier row's restore may have left a bound method on the instance.
        monkeypatch.delattr(connection, "cursor")
    sentinel = read_attr(mock.sentinel, "class_level_cursor")
    with mock.patch.object(BaseDatabaseWrapper, "cursor", sentinel):
        call_remove_databases_failures(_NarrowTest)
        assert "cursor" not in vars(connection)
        assert connection.cursor is sentinel


def test_apply_no_ops_when_toggle_disabled(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``APPLY_UPSTREAM_PATCHES = False`` makes ``apply()`` decline to install.

    The Trac #37064 patch is gated by the same flag as the package's
    other upstream patches, so a consumer who opts out of all
    monkey-patching gets none of them. ``apply()`` must return before
    re-installing when the flag is off, and resume installing when it
    is back on.
    """

    def _foreign(_cls: type[SimpleTestCase]) -> None:
        pass

    monkeypatch.setattr(SimpleTestCase, "_remove_databases_failures", classmethod(_foreign))
    assert _django_patches._patch_is_installed() is False

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
    _django_patches.apply()
    assert _django_patches._patch_is_installed() is False

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": True}
    _django_patches.apply()
    assert _django_patches._patch_is_installed() is True


def test_apply_no_ops_when_django_dependency_opted_out(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``{"APPLY_UPSTREAM_PATCHES": {"django": False}}`` disables only this module.

    The per-dependency escape: a mapping naming ``"django"`` makes this
    ``apply()`` decline to install, while a mapping naming only a SIBLING
    dependency leaves this module installing normally (each gate reads its own
    name).
    """

    def _foreign(_cls: type[SimpleTestCase]) -> None:
        pass

    monkeypatch.setattr(SimpleTestCase, "_remove_databases_failures", classmethod(_foreign))
    assert _django_patches._patch_is_installed() is False

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
    _django_patches.apply()
    assert _django_patches._patch_is_installed() is False

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}
    _django_patches.apply()
    assert _django_patches._patch_is_installed() is True


def test_reload_preserves_the_installed_patch_teardown(monkeypatch: pytest.MonkeyPatch) -> None:
    """``importlib.reload()`` must not break the RUNNING patch's teardown.

    ``importlib.reload()`` retains the module dictionary but re-executes the
    module while ``SimpleTestCase`` still points at the PREVIOUS generation of
    the patch - and that still-installed function delegates to Django through
    ``_original_remove_databases_failures``, which lives in that same
    re-executed dictionary. Re-capturing it from ``SimpleTestCase`` would
    capture the installed patch itself, so the running generation would
    delegate to itself instead of Django. ``_captured_upstream_descriptor``
    recovers Django's descriptor from the installed patch's stamp, so the
    running generation still unwraps through Django and the NEXT ``apply()``
    validates the same original.
    """
    # Re-setting the app-load generation's descriptor registers its restore; the
    # ``finally`` undoes it BEFORE ``apply()`` re-installs the current generation.
    monkeypatch.setattr(
        SimpleTestCase,
        "_remove_databases_failures",
        class_dict(SimpleTestCase)["_remove_databases_failures"],
    )
    try:
        assert _django_patches._patch_is_installed() is True

        importlib.reload(_django_patches)

        # The reload re-executed the module: its module-level function object is
        # a NEW generation, while the app-load generation remains installed.
        assert (
            read_attr(class_dict(SimpleTestCase)["_remove_databases_failures"], "__func__")
            is not _django_patches._patched_remove_databases_failures
        )
        assert _django_patches._patch_is_installed() is False

        class _NarrowReloaded(TransactionTestCase):
            databases = set()  # exclude every alias including default

        connection = connections["default"]
        original_cursor = connection.cursor
        sentinel = read_attr(mock.sentinel, "reload_survivor")
        monkeypatch.setattr(connection, "cursor", _database_failure(sentinel))
        try:
            # The still-installed PREVIOUS-generation function must unwrap
            # cleanly against the reloaded module dictionary.
            call_remove_databases_failures(_NarrowReloaded)
            assert connection.cursor is sentinel
        finally:
            connection.cursor = original_cursor

        # And the next ``apply()`` revalidates (against the recovered original)
        # and reinstalls a fresh generation of the CURRENT module object.
        _django_patches.apply()
        assert _django_patches._patch_is_installed() is True
        assert (
            read_attr(class_dict(SimpleTestCase)["_remove_databases_failures"], "__func__")
            is _django_patches._patched_remove_databases_failures
        )
    finally:
        monkeypatch.undo()
        _django_patches.apply()


def test_django_dependency_opt_out_silences_missing_method_list_abort(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The inherited escape-hatch coupling, resolved end to end.

    A Django that keeps its disallowed connection methods in neither known home
    aborts ``apply()`` with a ``RuntimeError`` whose text names the
    per-dependency escape - the exact surface where the trap fires on a consumer
    upgrading Django ahead of the package - and setting ``{"django": False}``
    then silences the abort (the gate precedes validation) without requiring the
    all-or-nothing global ``False`` that would also drop the production request
    hardening.
    """
    monkeypatch.setattr(BaseDatabaseFeatures, _FEATURE_METHODS, None, raising=False)
    monkeypatch.setattr(SimpleTestCase, _CLASS_METHODS, None, raising=False)
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {}
    with pytest.raises(RuntimeError, match=r'\{"django": False\}'):
        _django_patches.apply()

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
    _django_patches.apply()  # gated off per-dependency: no raise, no install attempt
