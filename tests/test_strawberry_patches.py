"""Tests for the Strawberry connection-page rebind.

System-under-test: :mod:`django_strawberry_framework._strawberry_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The rebind's outcome - a page whose ``edges`` / ``pageInfo`` a ``NameConverter``
respells still reads its rows - is earned over real HTTP in
``examples/fakeshop/test_query/test_library_api.py``
(``test_snake_case_page_info_only_page_reports_has_next_page``) and
``examples/fakeshop/test_query/test_connection_names_api.py``. The rows here pin
its install lifecycle, the upstream call shape it refuses to run without, and the
``APPLY_UPSTREAM_PATCHES`` opt-out.
"""

import pytest
import pytest_django
from strawberry.relay import types as relay_types
from strawberry.relay import utils as relay_utils

from django_strawberry_framework import _strawberry_patches as patches
from django_strawberry_framework.utils._narrowing import read_attr


def _installed_check() -> object:
    return read_attr(relay_types, patches._EDGES_CHECK)


def test_ready_rebinds_the_types_global_and_leaves_utils_alone() -> None:
    """By collection, ``AppConfig.ready()`` has rebound ``strawberry.relay.types`` only."""
    assert _installed_check() is patches._patched_should_resolve_list_connection_edges
    assert relay_utils.should_resolve_list_connection_edges is not _installed_check()


def test_apply_is_idempotent_and_rebinds_a_restored_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """A repeated ``apply()`` keeps the one rebind; one after a third-party restore rebinds it."""
    patches.apply()
    patches.apply()
    assert _installed_check() is patches._patched_should_resolve_list_connection_edges

    monkeypatch.setattr(
        relay_types,
        patches._EDGES_CHECK,
        relay_utils.should_resolve_list_connection_edges,
    )
    patches.apply()

    assert _installed_check() is patches._patched_should_resolve_list_connection_edges


class _InlinedCheckConnection:
    """A ``resolve_connection`` that no longer reads the module global."""

    @classmethod
    def resolve_connection(cls) -> bool:
        return False


def test_apply_fails_loudly_when_resolve_connection_stops_calling_the_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A release that inlines the check would leave the rebind installed and inert."""
    monkeypatch.setattr(
        relay_types.ListConnection,
        "resolve_connection",
        _InlinedCheckConnection.resolve_connection,
    )
    with pytest.raises(RuntimeError, match="no longer calls") as excinfo:
        patches.apply()
    assert 'APPLY_UPSTREAM_PATCHES = {"strawberry": False}' in str(excinfo.value)


@pytest.mark.parametrize(
    "toggle",
    [False, {"strawberry": False}],
    ids=["global-off", "dependency-off"],
)
def test_apply_respects_the_upstream_patch_opt_out(
    settings: pytest_django.Settings,
    monkeypatch: pytest.MonkeyPatch,
    toggle: object,
) -> None:
    """Opting out leaves upstream's connection-page check in place."""
    monkeypatch.setattr(
        relay_types,
        patches._EDGES_CHECK,
        relay_utils.should_resolve_list_connection_edges,
    )
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": toggle}

    patches.apply()

    assert _installed_check() is relay_utils.should_resolve_list_connection_edges
