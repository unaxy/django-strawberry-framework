"""Shared fresh-interpreter isolation for tests whose claim is about a clean process.

One home for the ``sys.executable -c <script>`` run + exit-code assertion that the
import-surface, registry-clear and soft-dependency suites each hand-rolled. A separate
process is what makes a ``sys.modules`` or import-time assertion deterministic: inside the
test worker the module under test is long since imported by the test files' own imports,
and ``importlib.reload`` does not reload submodules.

``sys.executable`` is the venv's Python under ``uv run pytest``, so the child inherits the
editable package install without ``PATH`` / ``PYTHONPATH`` munging. The child's claim is
its exit status: the body asserts (or exits non-zero), and ``run_in_fresh_process`` fails
the test with the child's stdout and stderr when the status is not ``0``.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

_FAKESHOP = Path(__file__).resolve().parents[1] / "examples" / "fakeshop"

_FAKESHOP_PROLOGUE = (
    "import django\n"
    "import os\n"
    f"import sys; sys.path.insert(0, {str(_FAKESHOP)!r})\n"
    "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')\n"
    "django.setup()\n"
)


def run_in_fresh_process(
    body: str,
    *,
    fakeshop: bool = True,
    interpreter_flags: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
) -> None:
    """Run ``body`` in a fresh interpreter and assert it exits ``0``.

    With ``fakeshop`` (the default) a prologue puts ``examples/fakeshop`` on ``sys.path``,
    points ``DJANGO_SETTINGS_MODULE`` at its settings unless the inherited environment
    already names one, and calls ``django.setup()``; ``body`` follows it verbatim. Pass
    ``fakeshop=False`` for a body that must start from a bare interpreter (a root-package
    import probe, or a body that configures Django itself). ``interpreter_flags`` go
    before ``-c`` (``-W error::DeprecationWarning``); ``env`` replaces the inherited
    environment; ``timeout`` bounds the child.
    """
    script = _FAKESHOP_PROLOGUE + body if fakeshop else body
    result = subprocess.run(
        [
            sys.executable,
            *interpreter_flags,
            "-c",
            script,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
