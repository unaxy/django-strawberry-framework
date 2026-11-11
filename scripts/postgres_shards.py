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

The split is computed from the files on disk at run time, so it never needs a
hand-kept module list. ``paths`` checks the partition before it prints a shard's
paths: every test file under ``pytest.ini``'s ``testpaths`` (matched by its
``python_files``) belongs to exactly one shard, or the job fails. Whether the
workflow's matrix names exactly these shards is pinned by
``tests/test_postgres_shards.py``.

Commands::

    python scripts/postgres_shards.py paths <shard>   # the shard's pytest paths, one per line
    python scripts/postgres_shards.py list            # every shard, its modules and weight
    python scripts/postgres_shards.py check           # the partition check alone
    python scripts/postgres_shards.py refresh <log>...  # rewrite the weights from job logs

``refresh`` reads the ``gh run view --job <id> --log`` output of every
``other-live-*`` shard of one Postgres run (the pytest run is ``-v`` under
xdist, so each result line carries its worker and a timestamp) and charges each
module the time between a worker's previous result and the module's result on
that worker, setup and teardown included. A module with no test selected by the
tier's ``-m`` filter never prints a result and keeps the median weight.
"""

from __future__ import annotations

import argparse
import configparser
import datetime as dt
import fnmatch
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import _git
except ModuleNotFoundError:  # imported as ``scripts.postgres_shards`` (repo root on path)
    from scripts import _git

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

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
# pytest's default ``norecursedirs``; ``pytest.ini`` does not override it.
NORECURSE_PATTERNS = (
    "*.egg",
    ".*",
    "_darcs",
    "build",
    "CVS",
    "dist",
    "node_modules",
    "venv",
    "{arch}",
)

# ``json.loads`` returns ``Any``; this alias hands callers an ``object`` to narrow.
_loads: Callable[[str], object] = json.loads

_WORKERS_LINE = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.\d+)?Z \d+ workers \[")
_RESULT_LINE = re.compile(
    r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)Z \[(gw\d+)\] \[\s*\d+%\] "
    r"(?:PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS) ([^\s:]+\.py)",
)


class ShardError(RuntimeError):
    """A partition or input error the caller fixes before CI can run."""


def pytest_settings(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return ``(testpaths, python_files)`` as ``pytest.ini`` declares them."""
    parser = configparser.ConfigParser(interpolation=None)
    _ = parser.read(root / "pytest.ini", encoding="utf-8")
    section = parser["pytest"]
    return tuple(section["testpaths"].split()), tuple(section["python_files"].split())


def _recursable(relative_dir: Path) -> bool:
    return not any(
        fnmatch.fnmatchcase(part, pattern) or part == "__pycache__"
        for part in relative_dir.parts
        for pattern in NORECURSE_PATTERNS
    )


def collected_files(root: Path, target: str, patterns: Sequence[str]) -> set[str]:
    """Return the repo-relative test files pytest collects from ``target`` (a file or directory)."""
    path = root / target
    if path.is_file():
        return {target}
    if not path.is_dir():
        message = f"shard target {target} does not exist"
        raise ShardError(message)
    return {
        candidate.relative_to(root).as_posix()
        for candidate in path.rglob("*.py")
        if _recursable(candidate.parent.relative_to(path))
        and any(fnmatch.fnmatchcase(candidate.name, pattern) for pattern in patterns)
    }


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


def shards(root: Path = REPO_ROOT) -> dict[str, tuple[str, ...]]:
    """Return every shard's pytest paths, in matrix order."""
    _testpaths, patterns = pytest_settings(root)
    fixed_live = {path for paths in LEADING_FIXED_SHARDS.values() for path in paths}
    other_live = collected_files(root, LIVE_ROOT, patterns) - fixed_live
    bins = split(other_live, load_weights(root), OTHER_LIVE_SHARDS)
    return {
        **LEADING_FIXED_SHARDS,
        **{f"{OTHER_LIVE_PREFIX}{index}": tuple(modules) for index, modules in enumerate(bins, 1)},
        **TRAILING_FIXED_SHARDS,
    }


def partition_problems(root: Path, assignment: dict[str, tuple[str, ...]]) -> list[str]:
    """Return why ``assignment`` is not an exact partition of the collected test files."""
    testpaths, patterns = pytest_settings(root)
    universe: set[str] = set()
    for testpath in testpaths:
        universe |= collected_files(root, testpath, patterns)
    owners: dict[str, list[str]] = {}
    problems: list[str] = []
    for name, paths in assignment.items():
        if not paths:
            problems.append(f"shard {name} runs nothing")
        for path in paths:
            if re.search(r"\s", path):
                problems.append(f"shard {name} path {path!r} holds whitespace")
            for module in collected_files(root, path, patterns):
                owners.setdefault(module, []).append(name)
    problems += [f"{module} is in no shard" for module in sorted(universe - owners.keys())]
    problems += [
        f"{module} is in shards {', '.join(names)}"
        for module, names in sorted(owners.items())
        if len(names) > 1
    ]
    problems += [
        f"{module} (shard {owners[module][0]}) is outside pytest.ini's testpaths"
        for module in sorted(owners.keys() - universe)
    ]
    return problems


def checked_shards(root: Path = REPO_ROOT) -> dict[str, tuple[str, ...]]:
    """Return ``shards(root)``, raising ``ShardError`` unless it partitions the suite exactly."""
    assignment = shards(root)
    if problems := partition_problems(root, assignment):
        raise ShardError("\n".join(problems))
    return assignment


def log_weights(texts: Iterable[str]) -> dict[str, float]:
    """Return the worker seconds each module took across the pytest job logs ``texts``."""
    totals: defaultdict[str, float] = defaultdict(float)
    for text in texts:
        start: dt.datetime | None = None
        previous: dict[str, dt.datetime] = {}
        for line in text.splitlines():
            if start is None:
                if match := _WORKERS_LINE.search(line):
                    start = dt.datetime.fromisoformat(match[1])
                continue
            if match := _RESULT_LINE.search(line):
                stamp = dt.datetime.fromisoformat(match[1][:26])
                totals[match[3]] += (stamp - previous.get(match[2], start)).total_seconds()
                previous[match[2]] = stamp
        if start is None:
            message = "a log has no xdist 'N workers [' line; pass whole pytest job logs"
            raise ShardError(message)
    return dict(totals)


def refresh(root: Path, log_paths: Sequence[Path]) -> list[str]:
    """Rewrite the weights file from ``log_paths``; return the split modules the logs never ran."""
    _testpaths, patterns = pytest_settings(root)
    fixed_live = {path for paths in LEADING_FIXED_SHARDS.values() for path in paths}
    other_live = collected_files(root, LIVE_ROOT, patterns) - fixed_live
    measured = log_weights(
        path.read_text(encoding="utf-8", errors="replace") for path in log_paths
    )
    weights = {
        module: round(seconds) for module, seconds in measured.items() if module in other_live
    }
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
