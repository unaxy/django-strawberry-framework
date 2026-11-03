"""Readers for the CI workflows under ``.github/workflows/``: YAML walkers, ``run`` commands, uv.

The YAML loader hands back untyped nodes, so each walker checks the node kind it
reads. ``shell_commands`` splits a ``run`` script into its simple commands and
``uv_command`` reads one command's uv subcommand and uv's own words, the reading
the uv lock and sync rows go through. ``matrix_node_lists`` and ``at_floor``
locate the matrix nodes of a job by their content. Shared by
``tests/test_ci_governance.py`` and ``tests/test_workspace.py``, which both read
``django.yml``.
"""

import re
from pathlib import Path
from typing import TypeAlias

import yaml

from django_strawberry_framework.utils.typing import object_result
from tests._idioms import (
    is_object_dict,
    is_object_list,
    json_at,
    json_list,
    json_loads,
    json_object,
)

WORKFLOW_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"

# A YAML mapping's keys are not all strings: the bare ``on:`` trigger key parses as ``True``.
YAMLMapping: TypeAlias = "dict[object, object]"


def parse_workflow(text: str, name: str = "workflow") -> YAMLMapping:
    """Parse one workflow's text, which is a mapping at its root; ``name`` labels a failure."""
    workflow = object_result(yaml.safe_load, text)
    assert is_object_dict(workflow), f"{name} is not a mapping"
    return workflow


def load_workflow(path: Path) -> YAMLMapping:
    """Parse one workflow file (``parse_workflow`` over its text)."""
    return parse_workflow(path.read_text(encoding="utf-8"), path.name)


def yaml_mapping(node: object) -> YAMLMapping:
    """Read a YAML node as a mapping; an absent or empty node reads as an empty one."""
    if not node:
        return {}
    assert is_object_dict(node), f"expected a YAML mapping, got {node!r}"
    return node


def workflow_jobs(workflow: YAMLMapping) -> dict[object, YAMLMapping]:
    """A workflow's jobs by job name, each job a mapping."""
    return {name: yaml_mapping(job) for name, job in yaml_mapping(workflow.get("jobs")).items()}


def job_steps(job: YAMLMapping) -> list[YAMLMapping]:
    """A job's ``steps`` sequence, each step a mapping."""
    steps = job.get("steps")
    if not steps:
        return []
    assert is_object_list(steps), f"expected a YAML sequence of steps, got {steps!r}"
    return list(map(yaml_mapping, steps))


def step_script(step: YAMLMapping) -> str:
    """A workflow step's ``run`` script with its backslash-newline continuations joined."""
    return str(step.get("run", "")).replace("\\\n", " ")


#: The control operators that end a simple command, each before any operator it begins.
_SHELL_OPERATORS = (
    "&&",
    "||",
    ";",
    "|",
    "&",
)
#: A simple command of a shell line, or the operator that ends it; a quoted string and a
#: redirection's ``&`` (``2>&1``, ``>&2``, ``&>file``) stay inside the command.
_SHELL_PART = re.compile(
    r"""(?:"[^"]*"|'[^']*'|\d*[<>]&\d*-?|&>|[^"';&|])+|"""
    + "|".join(map(re.escape, _SHELL_OPERATORS)),
)
#: A quoted string (group 1, kept whole) or a ``#`` comment, which opens at a word start.
_SHELL_COMMENT = re.compile(r"""("[^"]*"|'[^']*')|(?:^|(?<=\s))#.*""")


#: A ``uv`` word and a later ``sync`` word (never the ``sync`` of ``--no-sync``).
_UV_SYNC_WORDS = re.compile(r"\buv\b.*(?<![\w-])sync\b")
#: uv's global options that take the next word as their value at runtime, hidden and alias
#: names included (``--python-fetch``, ``--python-preference``, ``--preview-features``,
#: ``--trusted-host``); the subcommand follows.
UV_VALUED_GLOBALS = frozenset(
    {
        "--allow-insecure-host",
        "--cache-dir",
        "--color",
        "--config-file",
        "--directory",
        "--preview-features",
        "--project",
        "--python-fetch",
        "--python-preference",
        "--trusted-host",
    },
)
#: The options ``uv run`` takes the next word as the value of at runtime, its own and the
#: globals, hidden names included (``--max-recursion-depth``); the child command follows.
UV_RUN_VALUED = UV_VALUED_GLOBALS | frozenset(
    {
        "--config-setting",
        "--config-settings-package",
        "--default-index",
        "--env-file",
        "--exclude-newer",
        "--exclude-newer-package",
        "--extra",
        "--extra-index-url",
        "--find-links",
        "--fork-strategy",
        "--group",
        "--index",
        "--index-strategy",
        "--index-url",
        "--keyring-provider",
        "--link-mode",
        "--max-recursion-depth",
        "--no-binary-package",
        "--no-build-isolation-package",
        "--no-build-package",
        "--no-editable-package",
        "--no-extra",
        "--no-group",
        "--no-sources-package",
        "--only-group",
        "--package",
        "--prerelease",
        "--prerelease-package",
        "--python",
        "--python-platform",
        "--refresh-package",
        "--reinstall-package",
        "--resolution",
        "--upgrade-group",
        "--upgrade-package",
        "--with",
        "--with-editable",
        "--with-requirements",
        "-C",
        "-P",
        "-f",
        "-i",
        "-p",
        "-w",
    },
)
#: The uv subcommands a workflow runs besides ``sync``; a ``sync`` word after one is an argument.
_UV_OTHER_SUBCOMMANDS = frozenset(
    {
        "build",
        "lock",
        "pip",
        "python",
        "run",
        "tool",
        "venv",
    },
)
#: The uv subcommands that edit ``pyproject.toml`` and ``uv.lock``; CI runs neither.
UV_PROJECT_EDITS = frozenset({"add", "remove"})
#: The uv subcommands that lock the project first unless told ``--locked`` / ``--frozen``.
UV_RELOCKING = frozenset({"export", "tree"})
#: The uv subcommand that re-locks only when it writes a version (a value or ``--bump``) without
#: ``--locked`` / ``--frozen``; a bare ``uv version`` reads the version and leaves ``uv.lock``.
UV_VERSION = "version"


def shell_commands(script: str) -> list[tuple[str, str]]:
    """The simple commands of a joined ``run`` script in order, each with the operator after it.

    Each line loses a trailing ``#`` comment (a ``#`` inside quotes stays), then splits at
    ``&&``, ``||``, ``;``, ``|`` and ``&`` outside quotes and outside a redirection
    (``2>&1``, ``&>file``), whitespace runs collapsed. A command ending its line is
    followed by ``""``.
    """
    commands: list[tuple[str, str]] = []
    for line in script.splitlines():
        stripped = _SHELL_COMMENT.sub(lambda match: match.group(1) or "", line)
        parts = [
            match.group() for match in _SHELL_PART.finditer(stripped) if match.group().strip()
        ]
        commands.extend(
            (" ".join(part.split()), parts[index + 1] if index + 1 < len(parts) else "")
            for index, part in enumerate(parts)
            if part not in _SHELL_OPERATORS
        )
    return commands


def shell_segments(script: str) -> list[str]:
    """The simple commands of a joined ``run`` script, in order (``shell_commands`` sans operator)."""
    return [command for command, _after in shell_commands(script)]


def skip_options(words: list[str], index: int, valued: frozenset[str]) -> int:
    """The index of the first word from ``index`` on that is no option and no option's value.

    A ``--`` ends the options: the index stops on it.
    """
    while index < len(words) and words[index].startswith("-") and words[index] != "--":
        index += 2 if words[index] in valued else 1
    return index


def uv_command(segment: str) -> tuple[str, list[str]]:
    """A segment's uv subcommand and uv's own words after its first ``uv`` word.

    Whatever precedes ``uv`` (``VAR=val`` assignments, ``env``) and uv's global
    options are skipped. The subcommand reads ``"pip sync"`` / ``"pip install"`` for
    those (``pip``'s global options skipped too), ``"?"`` for a segment naming ``uv``
    and ``sync`` with no subcommand this check knows, and ``""`` for a segment running
    no uv command it judges. A ``uv run``'s words end at its child command, so the
    child's own ``--locked`` / ``--no-sync`` is never read as uv's.
    """
    words = segment.split()
    rest = words[words.index("uv") + 1 :] if "uv" in words else []
    index = skip_options(rest, 0, UV_VALUED_GLOBALS)
    subcommand = rest[index] if index < len(rest) else ""
    if subcommand == "pip":
        action = skip_options(rest, index + 1, UV_VALUED_GLOBALS)
        if rest[action : action + 1] in (["sync"], ["install"]):
            return f"pip {rest[action]}", rest
    if subcommand == "run":
        return subcommand, rest[: skip_options(rest, index + 1, UV_RUN_VALUED)]
    if subcommand in {
        "sync",
        *_UV_OTHER_SUBCOMMANDS,
        *UV_PROJECT_EDITS,
        *UV_RELOCKING,
        UV_VERSION,
    }:
        return subcommand, rest
    return ("?" if _UV_SYNC_WORDS.search(segment) else ""), rest


def job_commands(job: YAMLMapping) -> list[tuple[str, str]]:
    """``shell_commands`` over every ``run`` script of ``job``, in step order."""
    return [command for step in job_steps(job) for command in shell_commands(step_script(step))]


def job_segments(job: YAMLMapping) -> list[str]:
    """The simple commands of every ``run`` script of ``job``, in step order."""
    return [command for command, _after in job_commands(job)]


def matrix_node_lists(job: YAMLMapping) -> list[list[dict[object, object]]]:
    """The node lists ``job``'s ``strategy.matrix.include`` embeds, one per ``fromJSON('[...]')``."""
    include = str(json_at(job, "strategy", "matrix", "include"))
    texts: list[str] = re.findall(r"fromJSON\('(\[.*?\])'\)", include, re.DOTALL)
    return [list(map(json_object, json_list(json_loads(text)))) for text in texts]


def at_floor(node: dict[object, object], python: str, django: str) -> bool:
    """Whether a matrix node runs the floor ``(python, django)``, read from its content."""
    return (node.get("python"), node.get("django")) == (python, django)
