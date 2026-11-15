"""Refuse package code that swallows cancellation.

Nothing in the package swallows ``BaseException`` / ``SystemExit`` /
``KeyboardInterrupt`` / ``GeneratorExit``: no handler, ``suppress`` or
``finally`` exit drops them, so consumer exceptions and cancellation propagate
to the schema's error policy. This script is the gate. It parses each file
with ``ast`` (never imports it).

Names are resolved within the module only: an import binds its local name to
the dotted target (``from builtins import BaseException as BE``, ``import
contextlib as cl``), and every ``=`` / annotated / ``:=`` assignment to a
plain name, in any scope of the module, adds its value to what that name may
mean (``BE = BaseException``, ``CATCH = (BaseException,)``, ``ALL = CATCH +
(OSError,)``). A name neither imported nor assigned is a builtin. Out of reach:
a value imported from another module and then read through that module
(``errors.CATCH``), an attribute (``self.CATCH``), a parameter, a function's
return, and a string built at run time.

* **TR002** a handler that catches ``BaseException``, ``SystemExit``,
  ``KeyboardInterrupt`` or ``GeneratorExit`` (a bare name, ``builtins.<X>``,
  a name that resolves to one, or any of those inside a tuple, a starred
  member or a ``+`` of tuples), or a bare ``except:``, unless the handler
  re-raises: its last top-level statement is a bare ``raise``, or ``raise
  <as-name>`` where the handler never rebinds or deletes ``<as-name>`` before
  it (no ``from`` either way), and nothing in its body leaves the handler
  early (a ``return``, or a ``break`` / ``continue`` aimed at a loop outside
  the handler). Cleanup-then-reraise stays; anything else swallows
  cancellation or raises something other than what was caught.
* **TR004** a ``contextlib.suppress(...)`` call (``from contextlib import
  suppress`` and any alias included) whose arguments resolve, as for TR002,
  to an uncatchable class. ``suppress`` never re-raises, so there is no
  cleanup-then-reraise form.
* **TR005** a ``return``, or a ``break`` / ``continue`` aimed at a loop outside
  the block, inside a ``finally`` block (nested scopes skipped). Leaving a
  ``finally`` that way discards the exception in flight, cancellation
  included. Flagged on the exiting statement's line.

Usage::

    python scripts/check_truthful_reads.py [--check] [paths...]   # gate (pre-commit, CI)
    python scripts/check_truthful_reads.py --report [paths...]    # findings + counts, exit 0

``paths`` may be files or directories (directories are walked for ``*.py``,
skipping ``__pycache__``); with none, ``PACKAGE`` is scanned. Findings print
one per line, sorted, as ``path:line:col: CODE message`` with repo-relative
paths and 1-based columns. ``--check`` (and no flag) exits 1 on a finding;
``--report`` adds per-code counts and exits 0 whatever it found.

Every mode ends with one summary line (files checked, findings, errors), so a
clean pass and a pass over nothing never look alike. A named path that matches
nothing, a named directory that yields no ``.py`` file, or a file that cannot
be read or parsed is an error and exits 1 in every mode: a gate run over an
empty population is not a pass.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias, TypeGuard

try:
    import _git
except ModuleNotFoundError:  # imported as ``scripts.check_truthful_reads`` (repo root on path)
    from scripts import _git

REPO_ROOT = _git.CHECKOUT_ROOT
#: The package scanned when no path is named, repo-relative.
PACKAGE = "django_strawberry_framework"

UNCATCHABLE = frozenset(
    {
        "BaseException",
        "SystemExit",
        "KeyboardInterrupt",
        "GeneratorExit",
    },
)
CODES = ("TR002", "TR004", "TR005")

_NESTED_SCOPES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
    ast.ClassDef,
)
_LOOPS = (ast.For, ast.AsyncFor, ast.While)

Emit = Callable[
    [
        int,
        int,
        str,
        str,
    ],
    None,
]


@dataclass(frozen=True, order=True)
class Finding:
    """One flagged site; ordering is the output order."""

    path: str
    line: int
    col: int
    code: str
    message: str

    def render(self) -> str:
        """Return the ``path:line:col: CODE message`` line."""
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


@dataclass
class Selection:
    """The files a run checks and the paths that matched nothing."""

    files: list[Path] = field(default_factory=list)
    unmatched: list[tuple[str, str]] = field(default_factory=list)


# --------------------------------------------------------------------------- selection


def _relative(path: Path) -> str:
    """Return ``path`` repo-relative in posix form, or as given when outside the repo."""
    resolved = path.resolve()
    if resolved.is_relative_to(REPO_ROOT.resolve()):
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    return path.as_posix()


def _walk(directory: Path) -> Iterator[Path]:
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" not in path.parts and path.is_file():
            yield path


def select_files(raw_paths: Sequence[str]) -> Selection:
    """Resolve the named paths (or ``PACKAGE``) into the files to check."""
    selection = Selection()
    targets = list(raw_paths) or [str(REPO_ROOT / PACKAGE)]
    seen: set[Path] = set()
    for raw in targets:
        path = Path(raw)
        if path.is_dir():
            kept = list(_walk(path))
            if not kept:
                selection.unmatched.append((raw, "directory yielded no checkable file"))
        elif path.is_file() and path.suffix == ".py":
            kept = [path]
        elif path.is_file():
            selection.unmatched.append((raw, "not a .py file"))
            continue
        else:
            selection.unmatched.append((raw, "matches nothing"))
            continue
        for candidate in kept:
            key = candidate.resolve()
            if key not in seen:
                seen.add(key)
                selection.files.append(candidate)
    return selection


# --------------------------------------------------------------------------- analysis


def _builtin_name(node: ast.expr) -> str | None:
    """Return ``X`` for ``X`` or ``builtins.X``, else None."""
    if type(node) is ast.Name:
        return node.id
    if (
        type(node) is ast.Attribute
        and type(node.value) is ast.Name
        and node.value.id == "builtins"
    ):
        return node.attr
    return None


def _caught_names(handler: ast.ExceptHandler) -> set[str]:
    """Return the builtin names an ``except`` clause spells out (tuple members included)."""
    if handler.type is None:
        return set()
    members = handler.type.elts if type(handler.type) is ast.Tuple else [handler.type]
    return {name for name in map(_builtin_name, members) if name is not None}


_MODULE_ROOTS = frozenset({"builtins", "contextlib"})
_UNCATCHABLE_TARGETS = frozenset(f"builtins.{name}" for name in UNCATCHABLE)
_NO_NAMES: frozenset[str] = frozenset()


class _Names:
    """What each name of one module may be bound to, for resolving an alias.

    ``imports`` maps a local name to the dotted targets its imports bind
    (``from builtins import BaseException as BE`` binds ``BE`` to
    ``builtins.BaseException``). ``bindings`` maps a name to every expression
    assigned to it (``=``, an annotated assignment, ``:=``) anywhere in the
    module, whatever the scope: a name bound to an uncatchable class in one
    function and to something else in another resolves to both.
    """

    def __init__(self, tree: ast.AST) -> None:
        self.imports: dict[str, set[str]] = {}
        self.bindings: dict[str, list[ast.expr]] = {}
        for node in ast.walk(tree):
            if type(node) is ast.Import:
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    target = alias.name if alias.asname else local
                    self.imports.setdefault(local, set()).add(target)
            elif type(node) is ast.ImportFrom:
                package = "." * node.level + (f"{node.module}." if node.module else "")
                for alias in node.names:
                    target = f"{package}{alias.name}"
                    self.imports.setdefault(alias.asname or alias.name, set()).add(target)
            elif type(node) is ast.Assign:
                for target_node in node.targets:
                    self._bind(target_node, node.value)
            elif (type(node) is ast.AnnAssign or type(node) is ast.NamedExpr) and (
                node.value is not None
            ):
                self._bind(node.target, node.value)

    def _bind(self, target: ast.expr, value: ast.expr) -> None:
        if type(target) is ast.Name:
            self.bindings.setdefault(target.id, []).append(value)

    def targets(self, node: ast.expr, seen: frozenset[str] = _NO_NAMES) -> set[str]:
        """Return the dotted names ``node`` may refer to (an unbound name is a builtin)."""
        if type(node) is ast.Attribute:
            return {f"{base}.{node.attr}" for base in self.targets(node.value, seen)}
        if type(node) is not ast.Name or node.id in seen:
            return set()
        found = set(self.imports.get(node.id, ()))
        for value in self.bindings.get(node.id, ()):
            found |= self.targets(value, seen | {node.id})
        if node.id not in self.imports and node.id not in self.bindings:
            found.add(node.id if node.id in _MODULE_ROOTS else f"builtins.{node.id}")
        return found

    def uncatchable(self, node: ast.expr, seen: frozenset[str] = _NO_NAMES) -> set[str]:
        """Return the uncatchable classes ``node`` names, through tuples and name bindings."""
        if type(node) is ast.Tuple:
            return {name for member in node.elts for name in self.uncatchable(member, seen)}
        if type(node) is ast.Starred:
            return self.uncatchable(node.value, seen)
        if type(node) is ast.BinOp and type(node.op) is ast.Add:
            return self.uncatchable(node.left, seen) | self.uncatchable(node.right, seen)
        found = {
            target.removeprefix("builtins.")
            for target in self.targets(node, seen)
            if target in _UNCATCHABLE_TARGETS
        }
        if type(node) is ast.Name and node.id not in seen:
            for value in self.bindings.get(node.id, ()):
                found |= self.uncatchable(value, seen | {node.id})
        return found

    def calls(self, node: ast.Call, target: str) -> bool:
        """Return whether ``node`` calls ``target`` (a dotted name) under any alias."""
        return target in self.targets(node.func)


_Exit: TypeAlias = ast.Return | ast.Break | ast.Continue
_EXIT_KEYWORDS = {ast.Return: "return", ast.Break: "break", ast.Continue: "continue"}


def _exits(node: ast.AST, *, in_loop: bool) -> Iterator[_Exit]:
    """Yield each ``return``, and each ``break``/``continue`` leaving the block under ``node``.

    Nested scopes are skipped: their ``return`` leaves the nested function.
    """
    if isinstance(node, _NESTED_SCOPES):
        return
    if type(node) is ast.Return:
        yield node
        return
    if type(node) is ast.Break or type(node) is ast.Continue:
        if not in_loop:
            yield node
        return
    if isinstance(node, _LOOPS):
        for child in node.body:
            yield from _exits(child, in_loop=True)
        for child in node.orelse:
            yield from _exits(child, in_loop=in_loop)
        return
    for child in ast.iter_child_nodes(node):
        yield from _exits(child, in_loop=in_loop)


def _leaves_early(nodes: Sequence[ast.stmt]) -> bool:
    """Return whether ``nodes`` hold a ``return``, or a ``break``/``continue`` leaving them."""
    return any(True for node in nodes for _exit in _exits(node, in_loop=False))


def _scope_nodes(node: ast.AST) -> Iterator[ast.AST]:
    """Yield ``node`` and its descendants in the same scope (a nested scope node, not its body)."""
    yield node
    if not isinstance(node, _NESTED_SCOPES):
        for child in ast.iter_child_nodes(node):
            yield from _scope_nodes(child)


_NAMING_NODES = frozenset(
    {
        ast.ExceptHandler,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.MatchAs,
        ast.MatchStar,
    },
)
_NamingNode: TypeAlias = (
    ast.ExceptHandler
    | ast.FunctionDef
    | ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.MatchAs
    | ast.MatchStar
)


def _is_naming_node(node: ast.AST) -> TypeGuard[_NamingNode]:
    """Return whether ``node`` is exactly one of the ``_NAMING_NODES`` classes."""
    return type(node) in _NAMING_NODES


def _rebinds(nodes: Sequence[ast.stmt], name: str) -> bool:
    """Return whether ``nodes`` assign, delete or otherwise rebind ``name`` in their scope."""
    for statement in nodes:
        for node in _scope_nodes(statement):
            if type(node) is ast.Name and node.id == name and type(node.ctx) is not ast.Load:
                return True
            if type(node) is ast.alias and (node.asname or node.name.split(".")[0]) == name:
                return True
            if _is_naming_node(node) and node.name == name:
                return True
            if type(node) is ast.MatchMapping and node.rest == name:
                return True
    return False


def _reraises(handler: ast.ExceptHandler) -> bool:
    """Return whether ``handler`` always ends by re-raising what it caught."""
    last = handler.body[-1]
    if type(last) is not ast.Raise or last.cause is not None:
        return False
    if last.exc is not None and not (
        handler.name is not None
        and type(last.exc) is ast.Name
        and last.exc.id == handler.name
        and not _rebinds(handler.body[:-1], handler.name)
    ):
        return False
    return not _leaves_early(handler.body[:-1])


def _scan_node(node: ast.AST, names: _Names, emit: Emit) -> None:
    """Emit every finding rooted at ``node`` through ``emit(line, col, code, message)``."""
    if type(node) is ast.Try:
        for handler in node.handlers:
            _scan_handler(handler, names, emit)
        for statement in node.finalbody:
            for exit_node in _exits(statement, in_loop=False):
                keyword = _EXIT_KEYWORDS[type(exit_node)]
                message = f"`{keyword}` in `finally` discards the in-flight exception"
                emit(exit_node.lineno, exit_node.col_offset, "TR005", message)
    elif type(node) is ast.Call and names.calls(node, "contextlib.suppress"):
        swallowed = sorted({name for arg in node.args for name in names.uncatchable(arg)})
        if swallowed:
            message = f"`suppress({', '.join(swallowed)})` swallows cancellation"
            emit(node.lineno, node.col_offset, "TR004", message)


def _scan_handler(handler: ast.ExceptHandler, names: _Names, emit: Emit) -> None:
    spelled = sorted(_caught_names(handler) & UNCATCHABLE)
    swallowed = sorted(names.uncatchable(handler.type)) if handler.type is not None else []
    if (handler.type is None or swallowed) and not _reraises(handler):
        if handler.type is None:
            what = "bare `except:`"
        elif swallowed == spelled:
            what = f"`except {', '.join(spelled)}`"
        else:
            what = f"`except {ast.unparse(handler.type)}` (catches {', '.join(swallowed)})"
        emit(handler.lineno, handler.col_offset, "TR002", f"{what} does not re-raise")


def scan_source(source: str, display: str) -> list[Finding]:
    """Return the findings of one module's source (raises SyntaxError)."""
    tree = ast.parse(source, filename=display)
    names = _Names(tree)
    findings: list[Finding] = []

    def emit(
        line: int,
        col: int,
        code: str,
        message: str,
    ) -> None:
        findings.append(Finding(display, line, col + 1, code, message))

    for node in ast.walk(tree):
        _scan_node(node, names, emit)
    return sorted(set(findings))


# --------------------------------------------------------------------------- CLI


class _Args(argparse.Namespace):
    """The parsed command line, typed field by field after ``main``'s ``add_argument`` calls."""

    check: bool
    report: bool
    paths: list[str]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; see the module docstring for the modes."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group()
    _ = mode.add_argument(
        "--check",
        action="store_true",
        help="gate (the default); exit 1 on a finding",
    )
    _ = mode.add_argument(
        "--report",
        action="store_true",
        help="print every finding and per-code counts; exit 0 unless a path or file errors",
    )
    _ = parser.add_argument("paths", nargs="*", help=f"files/dirs to scan (default: {PACKAGE})")
    args = parser.parse_args(argv, namespace=_Args())
    selection = select_files(args.paths)

    errors = 0
    for raw, reason in selection.unmatched:
        print(f"{raw}: {reason} -- NOT checked", file=sys.stderr)
        errors += 1

    findings: list[Finding] = []
    for path in selection.files:
        display = _relative(path)
        try:
            findings.extend(scan_source(path.read_text(encoding="utf-8"), display))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            print(f"{display}: cannot scan: {error}", file=sys.stderr)
            errors += 1

    by_code = Counter(finding.code for finding in findings)
    counts = ", ".join(f"{code} {by_code.get(code, 0)}" for code in CODES)
    for finding in findings:
        print(finding.render())
    if args.report:
        print("\ncounts by code:")
        for code in CODES:
            print(f"  {code} {by_code.get(code, 0)}")
        print()
    print(
        f"truthful-reads: checked {len(selection.files)} file(s); "
        f"findings {len(findings)} ({counts}); errors {errors}",
    )
    if errors:
        return 1
    return 0 if args.report or not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
