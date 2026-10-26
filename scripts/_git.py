"""The one git runner the repository's scripts read their checkout through.

A script's answer about this checkout (a status baseline, the untracked files a
gate reads, the blob id of a working file, the paths a pathspec names) is a
property of the repository, never of who runs it. Every git call a script makes
about the checkout therefore runs in :func:`repository_env`: the caller's
global and system config, the system attributes file, the XDG global ignore
and attributes files and every stray ``GIT_*`` variable (``GIT_CONFIG_COUNT``/``KEY``/``VALUE``,
``GIT_CONFIG_PARAMETERS``, ``GIT_LITERAL_PATHSPECS``, ...) are dropped, and the
repository's own ``.gitignore``, ``.gitattributes``, ``.git/info/exclude`` and
``.git/config`` are honoured. A file only a caller-global rule hides is a gap in
the repository's ``.gitignore``, not something a script works around.

Two things stay the caller's. The variables that locate the repository
(``GIT_DIR``, ``GIT_WORK_TREE``, ``GIT_INDEX_FILE``, ...) pass through, so a
generator run from a hook, or against a private index, reads the index it was
pointed at. And the ownership trust git decides through ``safe.directory`` stays
the caller's decision: the values the caller set in system, global or command
scope are handed on as command scope (:func:`caller_safe_directory_env`), so a
checkout the caller marked safe stays readable and nothing is trusted that the
caller did not trust.

``GIT_OPTIONAL_LOCKS=0`` keeps a ``git status`` from refreshing and rewriting
``.git/index``, which another session's commit may be reading.

Standard library only and no Django import, so every script, ``workspace.py``
included, imports it before anything else is set up, on the oldest supported
Python too.
"""

from __future__ import annotations

import functools
import os
import subprocess
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

#: The caller's global and system git config, the system attributes file, the XDG config
#: directory (global ignore and attributes files) and the optional index refresh never reach a
#: result.
REPOSITORY_CONFIG_ONLY: Mapping[str, str] = MappingProxyType(
    {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "XDG_CONFIG_HOME": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    },
)
#: The ``GIT_*`` variables that say which repository, index and object store a command reads.
#: Every other ``GIT_*`` variable is dropped: an allowlist, so a variable git adds later is
#: dropped too.
REPOSITORY_LOCATING_NAMES = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    },
)
#: The config scopes git reads ``safe.directory`` from (its protected configuration).
PROTECTED_SCOPES = frozenset({"system", "global", "command"})
#: The caller variables git's protected configuration is read from; the ``safe.directory`` read
#: sees only these (and ``PATH``) and is cached per their values. ``GIT_CONFIG`` is not one:
#: git never reads trust from it.
PROTECTED_CONFIG_NAMES = frozenset(
    {
        "HOME",
        "XDG_CONFIG_HOME",
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
    },
)
PROTECTED_CONFIG_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")


def caller_safe_directories(base: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """Return the ``safe.directory`` values the caller set in protected scope, in git's order.

    Read from the caller's protected-config sources in ``base`` (default ``os.environ``,
    :data:`PROTECTED_CONFIG_NAMES`), outside any repository, keeping only system, global and
    command scope: a value a repository's own config sets is never trust. An empty value
    (git's list reset) is kept in place, and so is a value that is not valid UTF-8: on POSIX
    ``os.fsdecode`` keeps its bytes (surrogateescape) and they reach git unchanged. Git
    absent or no value set gives ``()``; the ``ValueError`` catch is only a guard.
    """
    source = os.environ if base is None else base
    key = tuple(
        sorted(
            (name, value)
            for name, value in source.items()
            if name in PROTECTED_CONFIG_NAMES or name.startswith(PROTECTED_CONFIG_PREFIXES)
        ),
    )
    try:
        return _read_safe_directories(key, source.get("PATH", os.defpath))
    except (OSError, ValueError):
        return ()


@functools.lru_cache(maxsize=8)
def _read_safe_directories(key: tuple[tuple[str, str], ...], search_path: str) -> tuple[str, ...]:
    """Run the protected-scope ``safe.directory`` read for one caller environment ``key``.

    Each value is decoded with ``os.fsdecode``, which on POSIX keeps undecodable bytes
    (surrogateescape) so they round-trip to git. A missing ``git`` raises ``OSError``, which
    the cache never keeps.
    """
    completed = subprocess.run(
        [
            "git",
            "config",
            "--show-scope",
            "-z",
            "--get-all",
            "safe.directory",
        ],
        cwd=os.sep,
        env={**dict(key), "PATH": search_path},
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return ()
    fields = [os.fsdecode(field) for field in completed.stdout.split(b"\0")]
    # Only system, global and command scope are trust. From ``cwd=/`` git reads a local or
    # worktree scope only when ``/`` is itself inside a repository the caller owns, and git
    # ignores a ``safe.directory`` set there.
    return tuple(
        value
        for scope, value in zip(fields[0::2], fields[1::2], strict=False)
        if scope in PROTECTED_SCOPES
    )


def caller_safe_directory_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return the caller's ``safe.directory`` trust as ``GIT_CONFIG_COUNT`` command scope.

    Empty when the caller trusts nothing beyond git's own ownership rule, so git then refuses
    a checkout another user owns exactly as it would for the caller.
    """
    values = caller_safe_directories(base)
    env = {"GIT_CONFIG_COUNT": str(len(values))} if values else {}
    for index, value in enumerate(values):
        env[f"GIT_CONFIG_KEY_{index}"] = "safe.directory"
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    return env


def repository_env(base: Mapping[str, str] | None = None, /, **extra: str) -> dict[str, str]:
    """Return ``base`` (default ``os.environ``) as a repository-only git environment, plus ``extra``.

    Every ``GIT_*`` variable outside :data:`REPOSITORY_LOCATING_NAMES` is dropped, then
    :data:`REPOSITORY_CONFIG_ONLY` (which replaces ``XDG_CONFIG_HOME``) and the caller's
    ``safe.directory`` trust (read from ``os.environ``) are laid over, then ``extra`` (a
    private ``GIT_INDEX_FILE``, an identity) last.
    """
    source = os.environ if base is None else base
    env = {
        name: value
        for name, value in source.items()
        if not name.startswith("GIT_") or name in REPOSITORY_LOCATING_NAMES
    }
    env.update(REPOSITORY_CONFIG_ONLY)
    env.update(caller_safe_directory_env())
    env.update(extra)
    return env


def run_git(
    root: Path | str,
    *args: str,
    stdin: str | None = None,
    check: bool = False,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``git -C root --no-pager args`` in :func:`repository_env` and return the result.

    Text in and out, output captured; ``env`` adds variables last. ``check`` raises
    ``subprocess.CalledProcessError`` on a non-zero exit, and a missing ``git`` raises
    ``OSError`` either way: each caller keeps its own failure contract.
    """
    return subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "--no-pager",
            *args,
        ],
        capture_output=True,
        text=True,
        input=stdin,
        env=repository_env(**dict(env or {})),
        check=check,
    )
