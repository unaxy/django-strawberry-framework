"""Enforce truthful identity reads across the package source.

Every fact the framework records about a consumer-supplied object (its name,
qualname, module, MRO, bases, namespace, class, whether it subclasses a
framework base, a declared ``Meta`` value) is read from the interpreter
through ``django_strawberry_framework/utils/truth.py``, never asked of the
object by attribute lookup a metaclass or instance can intercept. And
nothing swallows ``SystemExit`` / ``KeyboardInterrupt`` / ``GeneratorExit``
(no handler, ``suppress`` or ``finally`` exit): consumer exceptions propagate
to the schema's error policy. This script is the
gate for both halves. It parses each file with ``ast`` (never imports it) and
finds comments with ``tokenize``.

Names are resolved within the module only: an import binds its local name to
the dotted target (``from builtins import BaseException as BE``, ``import
contextlib as cl``), and every ``=`` / annotated / ``:=`` assignment to a
plain name, in any scope of the module, adds its value to what that name may
mean (``BE = BaseException``, ``CATCH = (BaseException,)``, ``ALL = CATCH +
(OSError,)``). A name neither imported nor assigned is a builtin. Out of reach:
a value imported from another module and then read through that module
(``errors.CATCH``), an attribute (``self.CATCH``), a parameter, a function's
return, and a string built at run time (``getattr(x, name)``).

Tier 1 -- fails the gate:

* **TR001** attribute access (load, store or del) to ``__class__``,
  ``__name__``, ``__qualname__``, ``__module__``, ``__mro__``, ``__bases__``,
  ``__dict__`` or ``__subclasses__``. A bare name such as module-level
  ``__name__`` is not an attribute access and is not flagged. Replacement: the
  matching ``truth`` call (``truth.class_of``, ``truth.name``, ...).
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
* **TR003** any use of ``getattr_static`` (import, attribute or name). A
  metaclass ``__getattribute__`` intercepts its ``entry.__dict__`` read, so it
  is not a static read; ``truth.static_attr`` is the replacement.
* **TR004** a ``contextlib.suppress(...)`` call (``from contextlib import
  suppress`` and any alias included) whose arguments resolve, as for TR002,
  to an uncatchable class. ``suppress`` never re-raises, so there is no
  cleanup-then-reraise form.
* **TR005** a ``return``, or a ``break`` / ``continue`` aimed at a loop outside
  the block, inside a ``finally`` block (nested scopes skipped). Leaving a
  ``finally`` that way discards the exception in flight, cancellation
  included. Flagged on the exiting statement's line.
* **TR006** an identity dunder (the TR001 set) read by a string naming it:
  ``getattr(x, "<dunder>"[, default])``, ``hasattr(x, "<dunder>")``,
  ``operator.attrgetter("<dunder>")`` (a dotted path with a dunder segment
  included; ``from operator import attrgetter`` and aliases too), and any
  ``<receiver>.__getattribute__(..., "<dunder>")`` such as
  ``object.__getattribute__(x, "__dict__")`` or ``type.__getattribute__(cls,
  "__name__")``. Each asks the object (a class-level ``__dict__`` property or
  a metaclass slot answers), which is what TR001 forbids spelled differently.
* **TR007** ``vars(x)``: it reads ``x.__dict__`` through the object.
  ``truth.class_dict`` reads a class's real namespace. ``vars()`` with no
  argument reads the caller's locals and is not flagged.
* **TR008** an ``.mro`` attribute (``cls.mro()``, ``type.mro(cls)``): a
  metaclass may override ``mro``. ``truth.mro`` (any ``truth.<name>``
  function) is the replacement and is not flagged.
* **TR009** an ``in`` / ``not in`` test whose left operand is a class read:
  a direct ``type(x)`` / ``truth.class_of(x)`` call, a walrus around one, or a
  plain name the same scope assigns one to (``value_type = type(value)`` ...
  ``value_type in TYPES``). Nothing else is followed: not a parameter, a name
  bound in another function or a closure, a loop target, tuple unpacking, a
  subscript, ``.get`` / ``__contains__``, or ``==``. Membership hashes and
  compares the class through its metaclass; ``truth.is_exact_one_of`` against a
  ``truth.IdentitySet`` (or ``truth.is_among`` for a sequence) decides it by
  identity.
* **TR010** an ``is`` / ``is not`` comparing two reads of a class's attribute
  (``truth.static_attr`` / ``truth.mro_attr`` / ``getattr``, each possibly inside
  ``truth.stored_function``): the hand-spelled "does the subclass override the
  base's hook" test, which compares the stored wrappers rather than the
  functions they hold. ``truth.overrides(cls, base, *names)`` decides it. An
  attribute-syntax compare (``type(x).hook is Base.hook``) is outside the gate:
  it is syntactically indistinguishable from an enum member or type compare.
* **TR900** a ``# truth: ok`` marker with no reason text. It suppresses
  nothing.

Tier 2 -- heuristics, printed by ``--report`` and counted by the default mode,
never failing:

* **TR101** ``isinstance(<x>, type)`` (``type`` alone or in a tuple) ->
  ``truth.is_type``.
* **TR102** any ``issubclass(...)`` call -> ``truth.is_subclass``.
* **TR103** a ``hash(...)`` call -> ``truth.IdentityMap``.
* **TR104** ``getattr`` / ``hasattr`` whose second argument is a string
  literal naming a dunder outside the TR001 set (those are TR006), ``"Meta"``
  or ``"_meta"`` -> ``truth.static_attr``.
* **TR105** an ``except Exception`` handler (alone, ``builtins.Exception`` or
  in a tuple) whose ``try`` body calls ``getattr`` / ``hasattr`` /
  ``isinstance`` / ``issubclass`` or reads a TR001 dunder: likely containment
  of an identity read, which the truthful read makes unnecessary.

Suppression: a ``# truth: ok <reason>`` comment on the flagged line (for
TR002 and TR105, the ``except`` line; for TR001 and TR008, the line holding the
attribute name; for TR005, the exiting statement's line; for a call, the line
the call starts on) suppresses every finding on that line, both tiers. The marker may sit
after other comment text (``# noqa: X  # truth: ok <reason>``). Keep markers
rare: ``--report`` lists every one with its reason and flags a marker that
suppresses nothing, so exceptions stay visible.

Configuration is read at run time from ``pyproject.toml``::

    [tool.truthful_reads]
    paths = ["django_strawberry_framework"]      # scanned when no path is named
    exempt = ["django_strawberry_framework/utils/truth.py"]

``exempt`` entries are repo-relative ``fnmatch`` patterns (an exact path is a
pattern), matched against a file and against each of its parent directories.
The table is parsed with ``tomli`` on every Python (the stdlib ``tomllib`` is
3.11+).

Usage::

    python scripts/check_truthful_reads.py [paths...]           # gate + tier-2 counts
    python scripts/check_truthful_reads.py --check [paths...]   # gate only (pre-commit, CI)
    python scripts/check_truthful_reads.py --report [paths...]  # full inventory, exit 0

``paths`` may be files or directories (directories are walked for ``*.py``,
skipping ``__pycache__``); with none, the configured ``paths`` are scanned.
Findings print one per line, sorted, as ``path:line:col: CODE message`` with
repo-relative paths and 1-based columns.

Modes:

* ``--check`` prints tier-1 findings and exits 1 if there is any.
* No flag behaves like ``--check`` and also prints one line of tier-2 counts
  per code, so a local run shows the heuristic worklist size without its
  detail.
* ``--report`` prints every finding of both tiers, every marker with its
  reason, per-code counts and per-file counts, and exits 0 whatever it found
  (it is an inventory, not a gate).

Every mode ends with one summary line (files checked, files exempt, tier-1,
tier-2, markers, errors), so a clean pass and a pass over nothing never look
alike. An exempt file named explicitly is reported as exempt and not checked.
A named path that matches nothing, a named directory that yields no checkable
file, a file that cannot be read or parsed, or an unreadable configuration is
an error and exits 1 in every mode: a gate run over an empty population is not
a pass.
"""

from __future__ import annotations

import argparse
import ast
import functools
import io
import re
import sys
import tokenize
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import TypeAlias, TypeGuard

import tomli

REPO_ROOT = Path(__file__).resolve().parent.parent
TABLE = "tool.truthful_reads"

IDENTITY_DUNDERS = frozenset(
    {
        "__class__",
        "__name__",
        "__qualname__",
        "__module__",
        "__mro__",
        "__bases__",
        "__dict__",
        "__subclasses__",
    },
)
UNCATCHABLE = frozenset(
    {
        "BaseException",
        "SystemExit",
        "KeyboardInterrupt",
        "GeneratorExit",
    },
)
STATIC_LOOKUP = "getattr_static"
TRUTH_MODULE = "truth"
IDENTITY_CALLS = frozenset(
    {
        "getattr",
        "hasattr",
        "isinstance",
        "issubclass",
    },
)
DECLARED_ATTR_LITERALS = frozenset({"Meta", "_meta"})
DUNDER = re.compile(r"__\w+__")
MARKER = re.compile(r"#\s*truth:\s*ok\b(?P<reason>.*)$")

TIER_1 = frozenset(
    {
        "TR001",
        "TR002",
        "TR003",
        "TR004",
        "TR005",
        "TR006",
        "TR007",
        "TR008",
        "TR009",
        "TR010",
        "TR900",
    },
)

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


class ConfigError(RuntimeError):
    """The ``[tool.truthful_reads]`` table is missing or malformed."""


@dataclass(frozen=True, order=True)
class Finding:
    """One flagged site; ordering is the output order."""

    path: str
    line: int
    col: int
    code: str
    message: str

    @property
    def tier(self) -> int:
        """Return 1 for a gate finding, 2 for a heuristic."""
        return 1 if self.code in TIER_1 else 2

    def render(self) -> str:
        """Return the ``path:line:col: CODE message`` line."""
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


@dataclass(frozen=True, order=True)
class Marker:
    """One ``# truth: ok`` comment."""

    path: str
    line: int
    reason: str
    used: bool


@dataclass
class Selection:
    """The files a run checks, the exempt files it skipped and the paths that matched nothing."""

    files: list[Path] = field(default_factory=list)
    exempt: list[Path] = field(default_factory=list)
    unmatched: list[tuple[str, str]] = field(default_factory=list)


# --------------------------------------------------------------------------- config


def _read_table(text: str) -> dict[str, object]:
    """Return the raw ``[tool.truthful_reads]`` table (KeyError when absent)."""
    # ``tomli.loads`` returns ``dict[str, Any]``; this alias hands the walk an ``object``.
    toml_loads: Callable[[str], dict[str, object]] = tomli.loads
    return _subtable(_subtable(toml_loads(text), "tool"), "truthful_reads")


def _subtable(document: object, key: str) -> dict[str, object]:
    """Return the table at ``document[key]`` (KeyError when absent or not a table)."""
    if not _is_exact_table(document):
        raise KeyError(key)
    value = document[key]
    if not _is_exact_table(value):
        raise KeyError(key)
    return value


def _is_exact_table(value: object) -> TypeGuard[dict[str, object]]:
    """Return whether a parsed TOML value is exactly a table."""
    return type(value) is dict


def _is_exact_list(value: object) -> TypeGuard[list[object]]:
    """Return whether a parsed TOML value is exactly an array."""
    return type(value) is list


def _is_string_array(value: object) -> TypeGuard[list[str]]:
    """Return whether a parsed TOML value is exactly an array of exact strings."""
    return _is_exact_list(value) and all(type(item) is str for item in value)


def _string_list(table: dict[str, object], key: str, pyproject: Path) -> tuple[str, ...]:
    value = table.get(key)
    if not _is_string_array(value):
        raise ConfigError(f"[{TABLE}] {key} must be an array of strings in {pyproject}")
    return tuple(value)


@functools.cache
def config() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return ``(paths, exempt)`` from ``[tool.truthful_reads]`` in pyproject.toml.

    Read lazily and cached, not at import, so the module imports from anywhere
    (a REPL, a test that points ``REPO_ROOT`` at a throwaway tree).
    """
    pyproject = REPO_ROOT / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError as error:
        raise ConfigError(f"cannot read {pyproject}: {error}") from error
    try:
        table = _read_table(text)
    except KeyError as error:
        raise ConfigError(f"[{TABLE}] missing from {pyproject}") from error
    except ValueError as error:
        raise ConfigError(f"cannot parse {pyproject}: {error}") from error
    paths = _string_list(table, "paths", pyproject)
    if not paths:
        raise ConfigError(f"[{TABLE}] paths is empty in {pyproject}")
    return paths, _string_list(table, "exempt", pyproject)


# --------------------------------------------------------------------------- selection


def _relative(path: Path) -> str:
    """Return ``path`` repo-relative in posix form, or as given when outside the repo."""
    resolved = path.resolve()
    if resolved.is_relative_to(REPO_ROOT.resolve()):
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    return path.as_posix()


def is_exempt(path: Path) -> bool:
    """Return whether ``path`` or one of its parent directories matches an ``exempt`` pattern."""
    relative = _relative(path)
    parts = relative.split("/")
    candidates = ["/".join(parts[:index]) for index in range(1, len(parts) + 1)]
    return any(
        fnmatchcase(candidate, pattern) for candidate in candidates for pattern in config()[1]
    )


def _walk(directory: Path) -> Iterator[Path]:
    for path in sorted(directory.rglob("*.py")):
        if "__pycache__" not in path.parts and path.is_file():
            yield path


def select_files(raw_paths: Sequence[str]) -> Selection:
    """Resolve the named paths (or the configured ones) into the files to check."""
    selection = Selection()
    named = list(raw_paths)
    targets = named or [str(REPO_ROOT / entry) for entry in config()[0]]
    seen: set[Path] = set()
    for raw in targets:
        path = Path(raw)
        if path.is_dir():
            walked = list(_walk(path))
            kept = [candidate for candidate in walked if not is_exempt(candidate)]
            if not kept:
                exempted = len(walked) - len(kept)
                reason = f"directory yielded no checkable file ({exempted} exempt)"
                selection.unmatched.append((raw, reason))
            selection.exempt.extend(candidate for candidate in walked if is_exempt(candidate))
        elif path.is_file() and path.suffix == ".py":
            if is_exempt(path):
                selection.exempt.append(path)
                continue
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


def _markers(source: str) -> dict[int, tuple[int, str]]:
    """Map each line carrying a ``# truth: ok`` marker to its column and reason (maybe empty)."""
    found: dict[int, tuple[int, str]] = {}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            match = MARKER.search(token.string)
            if match is not None:
                reason = match.group("reason").strip(" \t-:")
                found[token.start[0]] = (token.start[1], reason)
    return found


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


_MODULE_ROOTS = frozenset({"builtins", "contextlib", "operator"})
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


def _call_name(node: ast.Call) -> str | None:
    return node.func.id if type(node.func) is ast.Name else None


def _reads_identity(nodes: Sequence[ast.stmt]) -> bool:
    """Return whether ``nodes`` call an identity builtin or read an identity dunder."""
    for statement in nodes:
        for node in ast.walk(statement):
            if type(node) is ast.Call and _call_name(node) in IDENTITY_CALLS:
                return True
            if type(node) is ast.Attribute and node.attr in IDENTITY_DUNDERS:
                return True
    return False


def _uses_type(node: ast.expr) -> bool:
    members = node.elts if type(node) is ast.Tuple else [node]
    return any(type(member) is ast.Name and member.id == "type" for member in members)


def _string(node: ast.expr) -> str | None:
    """Return the value of a string literal, else None."""
    return node.value if type(node) is ast.Constant and type(node.value) is str else None


def _scan_node(node: ast.AST, names: _Names, emit: Emit) -> None:
    """Emit every finding rooted at ``node`` through ``emit(line, col, code, message)``."""
    if type(node) is ast.Attribute:
        # basedpyright: typeshed's ``ast.expr`` types end positions ``int | None`` since a
        # hand-built node may omit them; ``ast.parse`` sets both on every node it returns
        end_lineno: int = node.end_lineno  # pyright: ignore[reportAssignmentType]
        # basedpyright: same ``ast.expr`` end-position declaration as ``end_lineno`` above
        end_col_offset: int = node.end_col_offset  # pyright: ignore[reportAssignmentType]
        col = end_col_offset - len(node.attr)
        if node.attr in IDENTITY_DUNDERS:
            emit(end_lineno, col, "TR001", f"identity dunder `.{node.attr}` read by lookup")
        elif node.attr == STATIC_LOOKUP:
            emit(end_lineno, col, "TR003", _TR003)
        elif node.attr == "mro" and not _is_truth_call(names.targets(node)):
            emit(end_lineno, col, "TR008", "`.mro` asks the class for its MRO; use truth.mro")
    elif (type(node) is ast.Name and node.id == STATIC_LOOKUP) or (
        type(node) is ast.alias and node.name.split(".")[-1] == STATIC_LOOKUP
    ):
        emit(node.lineno, node.col_offset, "TR003", _TR003)
    elif type(node) is ast.Try:
        for handler in node.handlers:
            _scan_handler(node, handler, names, emit)
        for statement in node.finalbody:
            for exit_node in _exits(statement, in_loop=False):
                keyword = _EXIT_KEYWORDS[type(exit_node)]
                message = f"`{keyword}` in `finally` discards the in-flight exception"
                emit(exit_node.lineno, exit_node.col_offset, "TR005", message)
    elif type(node) is ast.Call:
        _scan_call(node, names, emit)
    elif type(node) is ast.Compare:
        _scan_hook_comparison(node, names, emit)
    if type(node) is ast.Module or isinstance(node, _NESTED_SCOPES):
        _scan_class_membership(node, names, emit)


def _scan_class_membership(scope: ast.AST, names: _Names, emit: Emit) -> None:
    """Emit TR009 for every ``in`` / ``not in`` of a class read in ``scope``'s own body."""
    nodes = [node for child in ast.iter_child_nodes(scope) for node in _scope_nodes(child)]
    local: dict[str, list[ast.expr]] = {}
    for node in nodes:
        if type(node) is ast.Assign:
            for target in node.targets:
                if type(target) is ast.Name:
                    local.setdefault(target.id, []).append(node.value)
        elif (type(node) is ast.AnnAssign or type(node) is ast.NamedExpr) and (
            type(node.target) is ast.Name and node.value is not None
        ):
            local.setdefault(node.target.id, []).append(node.value)
    for node in nodes:
        if type(node) is not ast.Compare:
            continue
        left = node.left
        for op, right in zip(node.ops, node.comparators, strict=True):
            membership = type(op) is ast.In or type(op) is ast.NotIn
            if membership and _is_class_read(left, names, local):
                message = "`in` on a class read runs its metaclass; use truth.is_exact_one_of"
                emit(left.lineno, left.col_offset, "TR009", message)
            left = right


def _is_class_read(
    node: ast.expr,
    names: _Names,
    local: dict[str, list[ast.expr]],
    seen: frozenset[str] = _NO_NAMES,
) -> bool:
    """Return whether ``node`` is ``type(x)`` / ``truth.class_of(x)`` or a local name bound to one."""
    if type(node) is ast.NamedExpr:
        return _is_class_read(node.value, names, local, seen)
    if type(node) is ast.Call and len(node.args) == 1 and not node.keywords:
        targets = names.targets(node.func)
        return "builtins.type" in targets or any(
            target.split(".")[-2:] == [TRUTH_MODULE, "class_of"] for target in targets
        )
    if type(node) is ast.Name and node.id not in seen:
        return any(
            _is_class_read(value, names, local, seen | {node.id})
            for value in local.get(node.id, ())
        )
    return False


def _scan_hook_comparison(node: ast.Compare, names: _Names, emit: Emit) -> None:
    """Emit TR010 for every ``is`` / ``is not`` between two class-attribute reads."""
    left = node.left
    for op, right in zip(node.ops, node.comparators, strict=True):
        identity = type(op) is ast.Is or type(op) is ast.IsNot
        if identity and _is_attribute_read(left, names) and _is_attribute_read(right, names):
            message = "`is` between two attribute reads of a class; use truth.overrides"
            emit(left.lineno, left.col_offset, "TR010", message)
        left = right


def _is_attribute_read(node: ast.expr, names: _Names) -> bool:
    """Return whether ``node`` reads a class attribute, directly or inside ``truth.stored_function``."""
    if type(node) is not ast.Call:
        return False
    targets = names.targets(node.func)
    if any(target.split(".")[-2:] == [TRUTH_MODULE, "stored_function"] for target in targets):
        return len(node.args) == 1 and _is_attribute_read(node.args[0], names)
    return "builtins.getattr" in targets or any(
        target.split(".")[-2:] in ([TRUTH_MODULE, "static_attr"], [TRUTH_MODULE, "mro_attr"])
        for target in targets
    )


def _is_truth_call(targets: set[str]) -> bool:
    """Return whether ``targets`` name a function of the ``truth`` module (``truth.mro``)."""
    return any(target.split(".")[-2:-1] == [TRUTH_MODULE] for target in targets)


_TR003 = "`getattr_static` is intercepted by a metaclass `__getattribute__`; use truth.static_attr"


def _scan_handler(
    try_node: ast.Try,
    handler: ast.ExceptHandler,
    names: _Names,
    emit: Emit,
) -> None:
    caught = _caught_names(handler)
    spelled = sorted(caught & UNCATCHABLE)
    swallowed = sorted(names.uncatchable(handler.type)) if handler.type is not None else []
    if (handler.type is None or swallowed) and not _reraises(handler):
        if handler.type is None:
            what = "bare `except:`"
        elif swallowed == spelled:
            what = f"`except {', '.join(spelled)}`"
        else:
            what = f"`except {ast.unparse(handler.type)}` (catches {', '.join(swallowed)})"
        emit(handler.lineno, handler.col_offset, "TR002", f"{what} does not re-raise")
    if "Exception" in caught and _reads_identity(try_node.body):
        message = "`except Exception` around an identity read (likely containment)"
        emit(handler.lineno, handler.col_offset, "TR105", message)


def _identity_literal(nodes: Sequence[ast.expr], *, dotted: bool) -> str | None:
    """Return the first string literal in ``nodes`` naming an identity dunder."""
    for node in nodes:
        value = _string(node)
        if value is None:
            continue
        parts = value.split(".") if dotted else [value]
        if any(part in IDENTITY_DUNDERS for part in parts):
            return value
    return None


def _scan_call(node: ast.Call, names: _Names, emit: Emit) -> None:
    args = node.args
    line, col = node.lineno, node.col_offset
    if names.calls(node, "contextlib.suppress"):
        swallowed = sorted({name for arg in args for name in names.uncatchable(arg)})
        if swallowed:
            message = f"`suppress({', '.join(swallowed)})` swallows cancellation"
            emit(line, col, "TR004", message)
        return
    literal = None
    if names.calls(node, "operator.attrgetter"):
        literal = _identity_literal(args, dotted=True)
    elif type(node.func) is ast.Attribute and node.func.attr == "__getattribute__":
        literal = _identity_literal(args, dotted=False)
    elif names.calls(node, "builtins.getattr") or names.calls(node, "builtins.hasattr"):
        literal = _identity_literal(args[1:2], dotted=False)
    if literal is not None:
        spelled = ast.unparse(node.func)
        message = f'`{spelled}(..., "{literal}")` reads an identity dunder by name; use truth'
        emit(line, col, "TR006", message)
        return
    if names.calls(node, "builtins.vars") and args:
        emit(line, col, "TR007", "`vars(x)` asks the object for its namespace; use truth")
        return
    name = _call_name(node)
    if name == "isinstance" and len(args) == 2 and _uses_type(args[1]):
        emit(line, col, "TR101", "`isinstance(x, type)`; use truth.is_type")
    elif name == "issubclass":
        emit(line, col, "TR102", "`issubclass(...)`; use truth.is_subclass")
    elif name == "hash":
        emit(line, col, "TR103", "`hash(...)` asks the object")
    elif name in {"getattr", "hasattr"} and len(args) >= 2:
        value = _string(args[1])
        if value is not None and (DUNDER.fullmatch(value) or value in DECLARED_ATTR_LITERALS):
            message = f'`{name}(x, "{value}")` asks the object; use truth.static_attr'
            emit(line, col, "TR104", message)


def scan_source(source: str, display: str) -> tuple[list[Finding], list[Marker]]:
    """Return the findings and markers of one module's source (raises SyntaxError)."""
    tree = ast.parse(source, filename=display)
    markers = _markers(source)
    names = _Names(tree)
    raw: list[Finding] = []

    def emit(
        line: int,
        col: int,
        code: str,
        message: str,
    ) -> None:
        raw.append(Finding(display, line, col + 1, code, message))

    for node in ast.walk(tree):
        _scan_node(node, names, emit)
    reasons = {line: reason for line, (_col, reason) in markers.items() if reason}
    findings = [finding for finding in raw if finding.line not in reasons]
    used = {finding.line for finding in raw if finding.line in reasons}
    findings.extend(
        Finding(display, line, col + 1, "TR900", "`# truth: ok` marker without a reason")
        for line, (col, reason) in markers.items()
        if not reason
    )
    marker_rows = [
        Marker(display, line, reason, line in used) for line, (_col, reason) in markers.items()
    ]
    return sorted(set(findings)), sorted(marker_rows)


# --------------------------------------------------------------------------- CLI


def _counts_line(counter: Counter[str], codes: Sequence[str]) -> str:
    return ", ".join(f"{code} {counter.get(code, 0)}" for code in codes)


TIER_2_CODES = (
    "TR101",
    "TR102",
    "TR103",
    "TR104",
    "TR105",
)
TIER_1_CODES = (
    "TR001",
    "TR002",
    "TR003",
    "TR004",
    "TR005",
    "TR006",
    "TR007",
    "TR008",
    "TR009",
    "TR010",
    "TR900",
)


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
        help="tier-1 gate only; exit 1 on a finding",
    )
    _ = mode.add_argument(
        "--report",
        action="store_true",
        help="print every finding, marker and count; exit 0 unless a path or file errors",
    )
    _ = parser.add_argument(
        "paths",
        nargs="*",
        help="files/dirs to scan (default: [tool.truthful_reads] paths)",
    )
    args = parser.parse_args(argv, namespace=_Args())
    try:
        selection = select_files(args.paths)
    except ConfigError as error:
        print(f"truthful-reads: {error}", file=sys.stderr)
        return 1

    errors = 0
    for raw, reason in selection.unmatched:
        print(f"{raw}: {reason} -- NOT checked", file=sys.stderr)
        errors += 1
    if args.paths:
        for path in selection.exempt:
            print(
                f"{_relative(path)}: exempt from the truthful-reads rules -- not checked",
                file=sys.stderr,
            )

    findings: list[Finding] = []
    markers: list[Marker] = []
    for path in selection.files:
        display = _relative(path)
        try:
            source = path.read_text(encoding="utf-8")
            file_findings, file_markers = scan_source(source, display)
        except (
            OSError,
            UnicodeDecodeError,
            SyntaxError,
            tokenize.TokenError,
        ) as error:
            print(f"{display}: cannot scan: {error}", file=sys.stderr)
            errors += 1
            continue
        findings.extend(file_findings)
        markers.extend(file_markers)

    tier_1 = [finding for finding in findings if finding.tier == 1]
    tier_2 = [finding for finding in findings if finding.tier == 2]
    by_code = Counter(finding.code for finding in findings)

    for finding in findings if args.report else tier_1:
        print(finding.render())
    if args.report:
        print(f"\nmarkers ({len(markers)}):")
        for marker in markers:
            note = "" if marker.used else "  [suppresses nothing]"
            print(f"{marker.path}:{marker.line}: truth: ok {marker.reason or '<no reason>'}{note}")
        print("\ncounts by code:")
        for code in (*TIER_1_CODES, *TIER_2_CODES):
            print(f"  {code} {by_code.get(code, 0)}")
        print("\ncounts by file (tier-1 / tier-2):")
        per_file: dict[str, list[int]] = {}
        for finding in findings:
            per_file.setdefault(finding.path, [0, 0])[finding.tier - 1] += 1
        ranked = sorted(per_file.items(), key=lambda item: (-item[1][0], -item[1][1], item[0]))
        for path, (first, second) in ranked:
            print(f"  {first:4d} / {second:4d}  {path}")
        print()
    elif not args.check:
        print(f"truthful-reads tier 2 (report-only): {_counts_line(by_code, TIER_2_CODES)}")

    exempt_count = len(selection.exempt)
    print(
        f"truthful-reads: checked {len(selection.files)} file(s); exempt {exempt_count}; "
        f"tier-1 {len(tier_1)} ({_counts_line(by_code, TIER_1_CODES)}); "
        f"tier-2 {len(tier_2)}; markers {len(markers)}; errors {errors}",
    )
    if errors:
        return 1
    if args.report:
        return 0
    return 1 if tier_1 else 0


if __name__ == "__main__":
    raise SystemExit(main())
