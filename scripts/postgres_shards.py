"""Assign every test module of the Postgres tier to exactly one ``postgres.yml`` shard.

``postgres.yml`` runs the DB-touching tests as path-disjoint matrix shards on
independent runners. This script owns which paths each shard runs:

- ``library-api`` and ``products-api``: the two largest live-API modules, one
  module per shard;
- ``other-live-1`` .. ``other-live-N``: every other module under
  ``examples/fakeshop/test_query``, split by longest-processing-time-first over
  the measured weights in ``scripts/postgres_shard_weights.json`` (worker
  seconds per module on the Postgres tier). A module the weights file does not
  name weighs the median of the named ones, so a new module is always assigned
  and only its balance waits for a refresh;
- ``package-core`` and ``example-non-live``: whole directories.

The module inventory is pytest's own: a ``pytest --collect-only`` run over
``pytest.ini``'s ``testpaths`` loads this module as a plugin, records every file
pytest would collect (its ``python_files``, ``norecursedirs``, conftest
``collect_ignore`` and every other collection rule applied by pytest itself)
and hands pytest no collectors, so no test module is imported. ``paths`` checks
the partition before it prints a shard's paths: every collected module belongs
to exactly one shard, or the job fails. Whether the workflow's matrix names
exactly these shards is pinned by ``tests/test_postgres_shards.py``. The
collection loads the root ``conftest.py``, whose guard refuses the shared
checkout: run the commands in a ``scripts/work.py`` copy.

Commands::

    python scripts/postgres_shards.py paths <shard>   # the shard's pytest paths, one per line
    python scripts/postgres_shards.py list            # every shard, its modules and weight
    python scripts/postgres_shards.py check           # the partition check alone
    python scripts/postgres_shards.py refresh <log>...  # rewrite the weights from job logs

``refresh`` reads the ``gh run view --job <id> --log`` output of every
``other-live-*`` shard of one finished Postgres run (the pytest run is ``-v``
under xdist, so each result line carries its worker and a timestamp) and
charges each module the time between a worker's previous result and the
module's result on that worker, setup and teardown included. A log without the
xdist workers line, without a result, or without pytest's closing summary
line (a cancelled or timed-out job) is refused before anything is written. A
module with no test selected by the tier's ``-m`` filter never prints a result
and keeps the median weight.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

try:
    import _git
except ModuleNotFoundError:  # imported as ``scripts.postgres_shards`` (repo root on path)
    from scripts import _git

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Sequence

    from typing_extensions import TypeIs

REPO_ROOT = _git.CHECKOUT_ROOT
WEIGHTS_FILE = "scripts/postgres_shard_weights.json"
LIVE_ROOT = "examples/fakeshop/test_query"
OTHER_LIVE_PREFIX = "other-live-"
OTHER_LIVE_SHARDS = 3
LEADING_FIXED_SHARDS: dict[str, tuple[str, ...]] = {
    "library-api": (f"{LIVE_ROOT}/test_library_api.py",),
    "products-api": (f"{LIVE_ROOT}/test_products_api.py",),
}
TRAILING_FIXED_SHARDS: dict[str, tuple[str, ...]] = {
    "package-core": ("tests",),
    "example-non-live": ("examples/fakeshop/apps", "examples/fakeshop/tests"),
}
# The collection subprocess writes the files it recorded to the path this names.
RECORD_ENV = "DSF_POSTGRES_SHARDS_RECORD"
# The outer pytest run's knobs a nested collection must not inherit; the ini names the settings.
_INHERITED_PYTEST_ENV = re.compile(
    r"PYTEST_ADDOPTS|PYTEST_XDIST_\w+|PYTEST_CURRENT_TEST|COV_CORE_\w+|DJANGO_SETTINGS_MODULE",
)

# ``json.loads`` returns ``Any``; this alias hands callers an ``object`` to narrow.
_loads: Callable[[str], object] = json.loads

_WORKERS_LINE = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.\d+)?Z \d+ workers \[")
_RESULT_LINE = re.compile(
    r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)Z \[(gw\d+)\] \[\s*\d+%\] "
    r"(?:PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS) ([^\s:]+\.py)",
)
# pytest's closing line, e.g. ``==== 4 failed, 8409 passed in 1643.78s (0:27:23) ====``.
_SUMMARY_LINE = re.compile(r"=+ .* in \d+(?:\.\d+)?s(?: \([\d:]+\))? =+\s*$")

_recorded: set[Path] = set()


class ShardError(RuntimeError):
    """A partition or input error the caller fixes before CI can run."""


@pytest.hookimpl(wrapper=True)
def pytest_collect_file(file_path: Path) -> Generator[None, list[object], list[object]]:
    """Record a file pytest would collect, then hand pytest no collector for it."""
    collectors = yield
    if collectors:
        _recorded.add(file_path)
    return []


def pytest_collection_finish() -> None:
    """Write the recorded files where ``collected_modules`` reads them."""
    if target := os.environ.get(RECORD_ENV):
        lines = sorted(str(path) for path in _recorded)
        _ = Path(target).write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def collected_modules(root: Path) -> set[str]:
    """Return the repo-relative test modules pytest collects from ``root`` with no path arguments."""
    env = {
        key: value for key, value in os.environ.items() if not _INHERITED_PYTEST_ENV.fullmatch(key)
    }
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO_ROOT), env.get("PYTHONPATH")]))
    with tempfile.TemporaryDirectory() as scratch:
        record = Path(scratch) / "collected.txt"
        env[RECORD_ENV] = str(record)
        command = [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
            "-p",
            "scripts.postgres_shards",
        ]
        result = subprocess.run(
            command,
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        # Exit 5 is "no tests collected": the plugin hands pytest no collectors by design.
        if result.returncode not in {0, 5} or not record.exists():
            message = f"pytest collection failed (exit {result.returncode}):\n{result.stdout}{result.stderr}"
            raise ShardError(message)
        lines = record.read_text(encoding="utf-8").splitlines()
    resolved_root = root.resolve()
    return {Path(line).resolve().relative_to(resolved_root).as_posix() for line in lines}


def _is_json_object(value: object) -> TypeIs[dict[str, object]]:
    """Return whether ``value`` is a decoded JSON object (whose keys are always strings)."""
    return isinstance(value, dict)


def load_weights(root: Path) -> dict[str, float]:
    """Return the measured worker seconds per module from the weights file."""
    data = _loads((root / WEIGHTS_FILE).read_text(encoding="utf-8"))
    if not _is_json_object(data):
        message = f"{WEIGHTS_FILE} is not a JSON object"
        raise ShardError(message)
    weights: dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
            message = f"{WEIGHTS_FILE}: {key!r} needs a non-negative number of seconds"
            raise ShardError(message)
        weights[key] = float(value)
    return weights


def split(modules: Iterable[str], weights: dict[str, float], count: int) -> list[list[str]]:
    """Split ``modules`` into ``count`` bins, heaviest first onto the lightest bin.

    A module ``weights`` does not name weighs the median of the named modules
    present. Ties break by module path and bin index, so one input always gives
    one split.
    """
    modules = sorted(modules)
    known = [weights[module] for module in modules if module in weights]
    default = statistics.median(known) if known else 1.0
    loads = [0.0] * count
    bins: list[list[str]] = [[] for _ in range(count)]
    for module in sorted(modules, key=lambda name: (-weights.get(name, default), name)):
        index = min(range(count), key=lambda i: (loads[i], i))
        loads[index] += weights.get(module, default)
        bins[index].append(module)
    return [sorted(modules_in_bin) for modules_in_bin in bins]


def other_live_modules(universe: Iterable[str]) -> set[str]:
    """Return the collected live-API modules no fixed shard names."""
    fixed_live = {path for paths in LEADING_FIXED_SHARDS.values() for path in paths}
    return {module for module in universe if module.startswith(f"{LIVE_ROOT}/")} - fixed_live


def shards(universe: Iterable[str], weights: dict[str, float]) -> dict[str, tuple[str, ...]]:
    """Return every shard's pytest paths, in matrix order."""
    bins = split(other_live_modules(universe), weights, OTHER_LIVE_SHARDS)
    return {
        **LEADING_FIXED_SHARDS,
        **{f"{OTHER_LIVE_PREFIX}{index}": tuple(modules) for index, modules in enumerate(bins, 1)},
        **TRAILING_FIXED_SHARDS,
    }


def partition_problems(universe: set[str], assignment: dict[str, tuple[str, ...]]) -> list[str]:
    """Return why ``assignment`` is not an exact partition of the collected modules ``universe``.

    A file path owns itself; a directory path owns every collected module under it.
    """
    owners: dict[str, list[str]] = {}
    problems: list[str] = []
    for name, paths in assignment.items():
        for path in paths:
            if "\n" in path:
                problems.append(f"shard {name} path {path!r} holds a line break")
            owned = (
                {path} if path in universe else {m for m in universe if m.startswith(f"{path}/")}
            )
            if not owned:
                problems.append(f"shard {name} path {path} holds no collected module")
            for module in owned:
                owners.setdefault(module, []).append(name)
    problems += [f"{module} is in no shard" for module in sorted(universe - owners.keys())]
    problems += [
        f"{module} is in shards {', '.join(names)}"
        for module, names in sorted(owners.items())
        if len(names) > 1
    ]
    return problems


def checked_shards(root: Path = REPO_ROOT) -> dict[str, tuple[str, ...]]:
    """Return the shards of ``root``, raising ``ShardError`` unless they partition it exactly."""
    universe = collected_modules(root)
    assignment = shards(universe, load_weights(root))
    if problems := partition_problems(universe, assignment):
        raise ShardError("\n".join(problems))
    return assignment


def log_weights(texts: Iterable[str]) -> dict[str, float]:
    """Return the worker seconds each module took across the finished pytest job logs ``texts``."""
    totals: defaultdict[str, float] = defaultdict(float)
    for number, text in enumerate(texts, 1):
        start: dt.datetime | None = None
        previous: dict[str, dt.datetime] = {}
        finished = False
        for line in text.splitlines():
            if start is None:
                if match := _WORKERS_LINE.search(line):
                    start = dt.datetime.fromisoformat(match[1])
                continue
            if match := _RESULT_LINE.search(line):
                stamp = dt.datetime.fromisoformat(match[1][:26])
                totals[match[3]] += (stamp - previous.get(match[2], start)).total_seconds()
                previous[match[2]] = stamp
            elif _SUMMARY_LINE.search(line):
                finished = True
        if start is None:
            message = f"log {number} has no xdist 'N workers [' line; pass whole pytest job logs"
            raise ShardError(message)
        if not previous:
            message = f"log {number} has no test result line"
            raise ShardError(message)
        if not finished:
            message = f"log {number} ends before pytest's summary line (cancelled or truncated)"
            raise ShardError(message)
    return dict(totals)


def refresh(root: Path, log_paths: Sequence[Path]) -> list[str]:
    """Rewrite the weights file from ``log_paths``; return the split modules the logs never ran."""
    other_live = other_live_modules(collected_modules(root))
    measured = log_weights(
        path.read_text(encoding="utf-8", errors="replace") for path in log_paths
    )
    weights = {
        module: round(seconds) for module, seconds in measured.items() if module in other_live
    }
    if not weights:
        message = "the logs measure no other-live module; pass the other-live-* job logs"
        raise ShardError(message)
    text = json.dumps(dict(sorted(weights.items())), indent=2) + "\n"
    _ = (root / WEIGHTS_FILE).write_text(text, encoding="utf-8")
    return sorted(other_live - weights.keys())


class _Args(argparse.Namespace):
    """The parsed command line: one field per ``_parse_args`` argument."""

    command: str
    shard: str
    logs: list[Path]


def _parse_args(argv: Sequence[str] | None) -> _Args:
    parser = argparse.ArgumentParser(
        description="Assign Postgres-tier test modules to postgres.yml shards.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    paths_parser = commands.add_parser("paths", help="print one shard's pytest paths")
    _ = paths_parser.add_argument("shard")
    _ = commands.add_parser("list", help="print every shard with its modules and weight")
    _ = commands.add_parser("check", help="check the partition")
    refresh_parser = commands.add_parser("refresh", help="rewrite the weights from job logs")
    _ = refresh_parser.add_argument("logs", nargs="+", type=Path)
    return parser.parse_args(argv, namespace=_Args())


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line."""
    args = _parse_args(argv)
    command = args.command
    try:
        if command == "refresh":
            for module in refresh(REPO_ROOT, args.logs):
                print(f"no result for {module}; it keeps the median weight")
            return 0
        assignment = checked_shards()
    except ShardError as error:
        print(f"postgres_shards: {error}", file=sys.stderr)
        return 1
    if command == "paths":
        shard = args.shard
        if shard not in assignment:
            print(
                f"postgres_shards: unknown shard {shard!r}; one of {', '.join(assignment)}",
                file=sys.stderr,
            )
            return 2
        print("\n".join(assignment[shard]))
    elif command == "list":
        weights = load_weights(REPO_ROOT)
        for name, paths in assignment.items():
            seconds = sum(weights.get(path, 0.0) for path in paths)
            print(f"{name}: {len(paths)} paths, {seconds / 60:.0f} measured worker minutes")
            for path in paths:
                print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
