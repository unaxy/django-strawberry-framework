"""Shared fixtures for the auth test modules.

Holds the ``sync_boundary_spy`` fixture ``test_mutations`` and
``test_queries`` share. Plain, non-fixture helpers shared
across the modules live in ``tests/auth/_helpers.py``.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from django_strawberry_framework.auth import mutations as auth_mutations
from django_strawberry_framework.utils.querysets import run_in_one_sync_boundary


@pytest.fixture
def sync_boundary_spy(monkeypatch: pytest.MonkeyPatch) -> list[Callable[..., object]]:
    """Spy on ``run_in_one_sync_boundary`` so async-body entry is counted deterministically.

    Both ``login`` / ``logout`` and ``current_user`` ride the same
    ``_make_auth_field`` dispatch seam and cross this ONE shared
    ``run_in_one_sync_boundary`` worker - ``current_user`` through the
    ``_sync_bridged_async_body`` interim bridge, ``login`` / ``logout`` through
    their native async bodies. Counting its calls counts how many times an async
    body was awaited (and so proves which path resolved the field). The async closure
    resolves the module-global name at call time, so patching the module attribute
    is observed.
    """
    calls: list[Callable[..., object]] = []
    real = run_in_one_sync_boundary

    async def _spy(fn: Callable[..., object], *args: object, **kwargs: object) -> object:
        calls.append(fn)
        return await real(fn, *args, **kwargs)

    monkeypatch.setattr(auth_mutations, "run_in_one_sync_boundary", _spy)
    return calls
