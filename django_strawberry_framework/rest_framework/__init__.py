"""DRF serializer mutations: generated inputs, conversion, binding, and execution behind an import guard.

``djangorestframework`` is a SOFT dependency: ``import django_strawberry_framework``
must succeed without it, and ``from django_strawberry_framework import *`` must stay
DRF-free (``SerializerMutation`` is resolved by name through the root
``__getattr__``, never added to ``__all__``). This package gates the DRF
import behind one guard so every ``rest_framework/`` module + the root
``__getattr__`` route a DRF-absent build through the SAME install-hint
``ImportError``.

The install hint names the verified floor, interpolated from
``utils/imports.py::DRF_FLOOR``. The floor is written in three gated places
that must agree: that constant, the ``[dependency-groups].dev`` row in
``pyproject.toml``, and the ``_HINT_SUBSTRING`` literal re-typed in
``tests/rest_framework/test_soft_dependency.py``. ``tests/test_ci_governance.py``
compares the constant to the dependency row and the soft-dependency tests
compare the hint to the literal, so none of the three can move alone.
spec-039 Decision 12 records why the floor is where it is; it is the
rationale, not a gated site, and like any other restatement it is gated by
nothing, so a floor bump sweeps the tree for the package name and reads each
hit. Importing THIS package runs ``require_drf()`` as its guard, so ``import
django_strawberry_framework.rest_framework`` raises the guarded ``ImportError``
when DRF is absent. Generalizes the ``types/converters.py`` soft-import
precedent (return-``None``) to a RAISING guard.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django_strawberry_framework.utils.imports import DRF_FLOOR, require_optional_module

if TYPE_CHECKING:
    from types import ModuleType

# The single DRF install-hint string (spec-039 carry-forward, Decision 12).
# Every DRF-absent raise routes through ``require_drf()`` so the hint lives in
# exactly one source location and names the verified floor.
_DRF_INSTALL_HINT: str = (
    "SerializerMutation requires djangorestframework, which is not installed. Install it "
    f"with `pip install 'djangorestframework>={DRF_FLOOR}'` (the package's verified DRF floor)."
)


def require_drf() -> ModuleType:
    """Import + return the DRF ``rest_framework`` package, or raise the install hint.

    The shared soft-dependency guard (spec-039 Decision 12): every serializer-mutation
    module + the root ``__getattr__`` call this before importing a DRF class. When DRF
    is present it returns the imported ``rest_framework`` module; when absent it raises
    an ``ImportError`` carrying the single ``_DRF_INSTALL_HINT`` string (the original
    chained), so a DRF-absent consumer sees a clear, actionable install message rather
    than a bare ``ModuleNotFoundError``. No memoization - each call re-runs the import so
    the absent-DRF test can evict ``sys.modules`` and re-hit the guard in one process.

    Delegates to ``utils/imports.py::require_optional_module`` exactly as
    ``routers.py::require_channels`` and
    ``middleware/debug_toolbar.py::require_debug_toolbar`` do - the three soft-dependency
    guards are identical thin wrappers over the one raising primitive. The absence test
    simulates DRF absence with the importlib-native ``sys.modules[...] = None`` sentinel
    (``tests/rest_framework/test_soft_dependency.py``), which raises for the delegated
    ``importlib.import_module`` call.
    """
    return require_optional_module("rest_framework", install_hint=_DRF_INSTALL_HINT)


# Guard on import: ``import django_strawberry_framework.rest_framework`` raises the
# guarded ``ImportError`` when DRF is absent (the root ``__getattr__`` reaches
# ``rest_framework.sets`` through this package, so the guard fires before the
# DRF-importing submodule loads).
_drf = require_drf()
del _drf  # only the raise is wanted; the module stays out of this namespace
