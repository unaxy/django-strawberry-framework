"""Report how a range of commits changed the package's typing, beyond what the ledger counts.

``scripts/check_type_suppressions.py`` and its ledger count ``typing.cast`` calls and
``# pyright: ignore`` comments. Typing also weakens through channels that ledger cannot
see: a ``TypeIs`` predicate whose claim says more than its check proves, a parameter
widened to ``object``, a declared attribute read with a default, a suppression moved
into a helper whose ``object`` parameter lets one ignore cover every call, a new
``# truth: ok`` marker. This report reads two revisions and lists what the range did
to each channel, so a reviewer reads the typing change before a landing.

Both trees are read through git (``git ls-tree``, ``git cat-file``, through
``scripts/_git.py``) and parsed with ``ast``; nothing is imported or executed, and the
working tree is never read. The scope is ``django_strawberry_framework/`` unless
``--paths`` names the trees to read instead (``--paths django_strawberry_framework
tests examples`` widens it). Names are compared resolved through each module's
imports, so ``models.QuerySet`` and ``QuerySet`` imported from ``django.db.models`` are
one name, and a predicate's parameters are compared by position, not by spelling.

Sections, each listing its flagged rows first:

1. **Narrowing predicates.** Every function whose return annotation is ``TypeIs[...]``
   or ``TypeGuard[...]``: new, removed and changed (claim or body; a docstring is not
   the body). A new or changed one prints its claim and body, and is flagged when

   * its claim names a parameterized generic whose arguments a class or ``isinstance``
     check cannot prove: an argument other than ``object``, ``...`` or ``Model`` (the
     bound of Django's model generics), or a ``QuerySet`` missing its row argument
     (``QuerySet[Model]`` claims model rows; ``QuerySet[Model, object]`` does not).
     ``type[...]``, unions and ``Annotated`` are looked through, ``Literal`` is not a
     generic, and a module-level alias is expanded. A body that walks the elements
     (a loop, a comprehension, ``all``/``any``) can prove its arguments and is not
     flagged for them;
   * its body is a sole ``return other(args)`` delegating to a predicate in scope
     whose claim differs from its own (``_is_choice_rows`` claiming
     ``QuerySet[Model]`` while ``is_queryset`` proves ``QuerySet[Model, object]``);
   * another predicate in scope has the same body (a stub's ``...`` body excepted).

2. **Widened signatures.** For functions present at both revisions, each parameter or
   return whose annotation gained an ``object`` or ``Any`` (``int`` to ``object``,
   ``dict[str, int]`` to ``dict[str, object]``), lost its annotation, or is a new
   parameter typed ``object`` / ``Any`` itself. Then, separately, each new public package function (under
   ``django_strawberry_framework/``; no leading underscore on the function, its classes
   or its module, not nested in a function) whose parameter or return is ``object`` /
   ``Any`` itself (through unions and ``type[...]``; ``object`` as a type argument is the
   widest claim, not a widening): START.md forbids widening a public parameter to
   ``object``. Every row here is flagged.

3. **Declared-but-defaulted reads.** A class body annotation without a value
   (``name: T``) that the class's own methods read through ``getattr(self|cls, "name",
   default)``, ``read_attr(self|cls, "name", default)`` or ``hasattr(self|cls, "name")``:
   the declaration tells the checker the attribute always exists while the read says
   it may not. New sites are flagged.

4. **Ledger moves.** ``scripts/type_suppressions.toml`` at both revisions, whatever
   ``--paths`` says: totals per kind that changed, and each entry that appeared or
   vanished. A vanished unit and an appeared unit of one kind pair as a move (same
   file first); each move prints the new site's parameters, and a move into a function
   taking an ``object`` or ``Any`` parameter is flagged (one ignore there covers every
   call). An appeared unit with no partner is growth and is flagged; a vanished one is
   a cleared suppression.

5. **Other suppression channels.** Count deltas over the files the range changed:
   ``# truth: ok`` markers, ``noqa`` codes (per code), and ``# basedpyright:`` reason
   lines whose next logical line carries no ``pyright: ignore``. A rise in ``truth:
   ok`` markers, in orphan reason lines or in an ``ANN`` / ``PGH003`` code is flagged;
   other ``noqa`` moves are listed.

Usage::

    uv run python scripts/typing_delta.py <base-rev> [--head REV] [--paths P ...]
        [--json] [--fail-on-flags]

The text report ends with one line, ``typing-delta <base>..<head>: N flagged``.
``--json`` prints the same report as one JSON object. Exit code ``0`` unless
``--fail-on-flags`` is passed and a row is flagged (``1``); ``2`` when git cannot read
a revision or a file in scope does not parse.
"""

from __future__ import annotations

import argparse
import ast
import copy
import io
import json
import re
import subprocess
import sys
import tokenize
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

try:
    import _git
    import check_type_suppressions
except ModuleNotFoundError:  # imported as a ``scripts`` submodule (repo root on path)
    from scripts import _git, check_type_suppressions

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence

REPO_ROOT = _git.CHECKOUT_ROOT
#: The default scope, repo-relative.
PACKAGE = "django_strawberry_framework"
#: The suppression ledger, repo-relative.
LEDGER = check_type_suppressions.LEDGER

#: Resolved names an annotation widens through.
_WIDE_TYPES = frozenset(
    {
        "object",
        "builtins.object",
        "typing.Any",
        "typing_extensions.Any",
    },
)
#: Type arguments a class check proves: the widest each generic accepts.
_WIDE_ARGUMENTS = frozenset(
    {
        "object",
        "builtins.object",
        "django.db.models.Model",
        "django.db.models.base.Model",
    },
)
#: Generics whose trailing type parameters default to something narrower than ``object``.
_FULL_ARITY = {"django.db.models.QuerySet": 2, "django.db.models.query.QuerySet": 2}
#: Subscripted forms whose arguments are themselves the claim (looked through).
_TRANSPARENT = frozenset(
    {
        "type",
        "builtins.type",
        "typing.Type",
        "typing_extensions.Type",
        "typing.Union",
        "typing_extensions.Union",
        "typing.Optional",
        "typing_extensions.Optional",
    },
)
_ANNOTATED = frozenset({"typing.Annotated", "typing_extensions.Annotated"})
_LITERAL = frozenset({"typing.Literal", "typing_extensions.Literal"})
_NARROWING_FORMS = ("TypeIs", "TypeGuard")
#: Readers that answer a default when the attribute is missing: name, argument count.
_DEFAULTED_READERS = {"getattr": 3, "read_attr": 3, "hasattr": 2}
#: ``noqa`` codes whose rise is a typing change (``ANN`` prefixes match every ``ANN`` code).
_TYPING_NOQA = ("ANN", "PGH003")
#: The section 5 keys whose rise is flagged.
_TRUTH_KEY = "truth: ok"
_ORPHAN_KEY = "basedpyright reason without ignore"

_TRUTH = re.compile(r"#\s*truth:\s*ok\b")
_NOQA = re.compile(
    r"\bnoqa\b(?::\s*(?P<codes>[A-Z]+[0-9]+(?:\s*,\s*[A-Z]+[0-9]+)*))?",
    re.IGNORECASE,
)
_REASON = re.compile(r"^#\s*basedpyright:")
_IGNORE = re.compile(r"pyright:\s*ignore")

_FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class _Args(argparse.Namespace):
    """The parsed command line: one field per ``parse_args`` argument."""

    base: str
    head: str
    paths: list[str]
    json: bool
    fail_on_flags: bool


@dataclass(frozen=True)
class Module:
    """One parsed file at one revision, with the names its imports and definitions bind."""

    path: str
    name: str
    text: str
    tree: ast.Module
    #: Each bound name's dotted target (an import, or a module-level class or function).
    bindings: Mapping[str, str]
    #: Each module-level assignment's value (the ``if`` branch of an ``if``, never ``else``).
    aliases: Mapping[str, ast.expr]


@dataclass(frozen=True)
class Definition:
    """A function or class and where it sits: its qualified name and whether it is public."""

    qualname: str
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    public: bool


@dataclass(frozen=True)
class Predicate:
    """A ``TypeIs`` / ``TypeGuard`` function: its claim and body, as written and as compared."""

    path: str
    qualname: str
    dotted: str
    line: int
    claim: str
    claim_key: str
    body: str
    body_key: str
    stub: bool
    delegate: str | None
    unproven: tuple[str, ...]

    @property
    def site(self) -> str:
        """``path::QualifiedName``."""
        return f"{self.path}::{self.qualname}"


@dataclass(frozen=True)
class Slot:
    """One parameter (or ``return``) of a signature: its annotation and how many wide names it holds."""

    name: str
    annotation: str | None
    wide: int
    #: Whether the annotation itself is ``object`` / ``Any`` (through unions and ``type[...]``).
    top_wide: bool = False


@dataclass
class Row:
    """One reported item; ``flagged`` rows print first in their section."""

    title: str
    details: list[str] = field(default_factory=list)
    flagged: bool = field(default=False, kw_only=True)


@dataclass
class Section:
    """One report section: a one-line summary and its rows."""

    title: str
    summary: str
    rows: list[Row]


@dataclass
class Report:
    """The whole report for one range."""

    base: str
    head: str
    scope: tuple[str, ...]
    sections: list[Section]

    @property
    def flagged(self) -> int:
        """The number of flagged rows across every section."""
        return sum(row.flagged for section in self.sections for row in section.rows)

    def summary_line(self) -> str:
        """Return the report's last line."""
        return f"typing-delta {self.base}..{self.head}: {self.flagged} flagged"

    def text(self) -> str:
        """Return the plain-text report, flagged rows first in each section."""
        lines = [f"typing-delta {self.base}..{self.head} (scope: {', '.join(self.scope)})"]
        for section in self.sections:
            lines.extend(("", f"== {section.title}: {section.summary}"))
            for row in sorted(section.rows, key=lambda row: not row.flagged):
                lines.append(f"{'FLAG' if row.flagged else '    '} {row.title}")
                lines.extend(f"       {detail}" for detail in row.details)
        lines.extend(("", self.summary_line()))
        return "\n".join(lines) + "\n"

    def as_json(self) -> dict[str, object]:
        """Return the report as one JSON-ready object."""
        return {
            "base": self.base,
            "head": self.head,
            "scope": list(self.scope),
            "flagged": self.flagged,
            "sections": [
                {
                    "title": section.title,
                    "summary": section.summary,
                    "rows": [
                        {"flagged": row.flagged, "title": row.title, "details": row.details}
                        for row in sorted(section.rows, key=lambda row: not row.flagged)
                    ],
                }
                for section in self.sections
            ],
        }


# --- parsing and name resolution -------------------------------------------------------


def module_name(path: str) -> str:
    """Return the dotted module name of a repo-relative ``.py`` path."""
    name = path.removesuffix(".py").replace("/", ".")
    return name.removesuffix(".__init__")


def _import_base(node: ast.ImportFrom, module: str, path: str) -> str:
    """Return the module an ``ImportFrom`` reads from, a relative import resolved."""
    if not node.level:
        return node.module or ""
    package = module if path.endswith("__init__.py") else module.rpartition(".")[0]
    parts = package.split(".")
    anchor = ".".join(parts[: len(parts) - (node.level - 1)])
    return f"{anchor}.{node.module}" if node.module else anchor


def _module_statements(body: Iterable[ast.stmt]) -> Iterator[ast.stmt]:
    """Yield module-level statements, descending into ``if`` bodies (never ``else``) and ``try``."""
    for statement in body:
        yield statement
        if isinstance(statement, (ast.If, ast.Try)):
            yield from _module_statements(statement.body)


def parse_module(path: str, text: str) -> Module:
    """Parse ``text`` (the file at ``path``) and collect its bindings and aliases.

    Raises:
        SyntaxError: ``text`` does not parse.

    """
    tree = ast.parse(text, filename=path)
    name = module_name(path)
    bindings: dict[str, str] = {}
    aliases: dict[str, ast.expr] = {}
    for statement in _module_statements(tree.body):
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bindings[statement.name] = f"{name}.{statement.name}"
        elif isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                _ = aliases.setdefault(target.id, statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            _ = aliases.setdefault(statement.target.id, statement.value)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    bindings[alias.asname] = alias.name
                else:
                    head = alias.name.partition(".")[0]
                    bindings[head] = head
        elif isinstance(node, ast.ImportFrom):
            base = _import_base(node, name, path)
            for alias in node.names:
                bindings[alias.asname or alias.name] = f"{base}.{alias.name}"
    return Module(path, name, text, tree, bindings, aliases)


def _resolved(expr: ast.expr, module: Module) -> str | None:
    """Return the dotted name a ``Name`` / ``Attribute`` chain resolves to, else ``None``."""
    if isinstance(expr, ast.Name):
        return module.bindings.get(expr.id, expr.id)
    if isinstance(expr, ast.Attribute):
        head = _resolved(expr.value, module)
        return None if head is None else f"{head}.{expr.attr}"
    return None


def _annotation(node: ast.expr | None) -> ast.expr | None:
    """Return an annotation as an expression, a string annotation parsed."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            return ast.parse(node.value, mode="eval").body
        except SyntaxError:
            return None
    return node


def _canonical(node: ast.AST, module: Module, params: Mapping[str, str] | None = None) -> ast.AST:
    """Return a copy of ``node`` with names resolved and parameters renamed by position."""
    clone = copy.deepcopy(node)
    for child in ast.walk(clone):
        if isinstance(child, ast.Name):
            child.id = (params or {}).get(child.id) or module.bindings.get(child.id, child.id)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            parsed = _annotation(child)
            if parsed is not None and parsed is not child:
                child.value = ast.unparse(_canonical(parsed, module, params))
    return clone


def symbols(tree: ast.Module, module: str) -> Iterator[Definition]:
    """Yield every function and class with its qualified name, as the ledger keys sites.

    A name defined twice in one scope (an overload, a ``TYPE_CHECKING`` stub and its
    runtime twin) gets ``#2``, ``#3`` ... after the first. A function, class or module
    with a leading underscore, and anything nested in a function, is not public.
    """
    module_public = not any(part.startswith("_") for part in module.split("."))
    seen: Counter[str] = Counter()

    def walk(body: Iterable[ast.stmt], prefix: str, *, public: bool) -> Iterator[Definition]:
        for statement in body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualname = f"{prefix}{statement.name}"
                seen[qualname] += 1
                key = qualname if seen[qualname] == 1 else f"{qualname}#{seen[qualname]}"
                visible = public and not statement.name.startswith("_")
                yield Definition(key, statement, visible)
                nested_public = visible and isinstance(statement, ast.ClassDef)
                yield from walk(statement.body, f"{qualname}.", public=nested_public)
            else:
                nested = [
                    child
                    for child in ast.iter_child_nodes(statement)
                    if isinstance(child, ast.stmt)
                ]
                for handler in ast.iter_child_nodes(statement):
                    if isinstance(handler, ast.ExceptHandler):
                        nested.extend(handler.body)
                yield from walk(nested, prefix, public=public)

    yield from walk(tree.body, "", public=module_public)


def _functions(module: Module) -> dict[str, Definition]:
    """Return every function definition in ``module`` by qualified name."""
    return {
        definition.qualname: definition
        for definition in symbols(module.tree, module.name)
        if not isinstance(definition.node, ast.ClassDef)
    }


def _body(node: _FunctionNode) -> list[ast.stmt]:
    """Return a function's statements without its docstring."""
    body = node.body
    first = body[0] if body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return body[1:]
    return body


def _parameters(node: _FunctionNode) -> list[ast.arg]:
    """Return a function's parameters in declaration order."""
    arguments = node.args
    return [
        *arguments.posonlyargs,
        *arguments.args,
        *([arguments.vararg] if arguments.vararg else []),
        *arguments.kwonlyargs,
        *([arguments.kwarg] if arguments.kwarg else []),
    ]


# --- section 1: narrowing predicates ---------------------------------------------------


def _narrowing_claim(node: _FunctionNode, module: Module) -> ast.expr | None:
    """Return the ``X`` of a ``TypeIs[X]`` / ``TypeGuard[X]`` return annotation, else ``None``."""
    returns = _annotation(node.returns)
    if not isinstance(returns, ast.Subscript):
        return None
    form = _resolved(returns.value, module)
    if form is None or form.rpartition(".")[2] not in _NARROWING_FORMS:
        return None
    return returns.slice


def _is_wide_argument(argument: ast.expr, module: Module) -> bool:
    """Return whether a type argument is one a class check proves (``object``, ``...``, ``Model``)."""
    if isinstance(argument, ast.Constant) and argument.value is Ellipsis:
        return True
    return _resolved(argument, module) in _WIDE_ARGUMENTS


def unproven_arguments(claim: ast.expr, module: Module, depth: int = 0) -> list[str]:
    """Return each generic in ``claim`` whose type arguments a class check cannot prove."""
    if depth > 4:
        return []
    if isinstance(claim, ast.BinOp) and isinstance(claim.op, ast.BitOr):
        return [
            *unproven_arguments(claim.left, module, depth + 1),
            *unproven_arguments(claim.right, module, depth + 1),
        ]
    if isinstance(claim, ast.Name) and claim.id in module.aliases:
        return unproven_arguments(module.aliases[claim.id], module, depth + 1)
    if isinstance(claim, ast.Constant) and isinstance(claim.value, str):
        parsed = _annotation(claim)
        return [] if parsed is None else unproven_arguments(parsed, module, depth + 1)
    if not isinstance(claim, ast.Subscript):
        return []
    head = _resolved(claim.value, module) or ast.unparse(claim.value)
    arguments = list(claim.slice.elts) if isinstance(claim.slice, ast.Tuple) else [claim.slice]
    if head in _LITERAL:
        return []
    if head in _ANNOTATED:
        return unproven_arguments(arguments[0], module, depth + 1)
    if head in _TRANSPARENT:
        return [
            found
            for argument in arguments
            for found in unproven_arguments(argument, module, depth + 1)
        ]
    short = len(arguments) < _FULL_ARITY.get(head, 0)
    if short or not all(_is_wide_argument(argument, module) for argument in arguments):
        return [ast.unparse(claim)]
    return []


def _inspects_elements(body: Sequence[ast.stmt]) -> bool:
    """Return whether a body walks a value's elements (a loop, a comprehension, ``all``/``any``)."""
    for statement in body:
        for node in ast.walk(statement):
            if isinstance(
                node,
                (
                    ast.For,
                    ast.AsyncFor,
                    ast.comprehension,
                    ast.While,
                ),
            ):
                return True
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"all", "any"}
            ):
                return True
    return False


def _delegate(body: Sequence[ast.stmt], module: Module, names: Iterable[str]) -> str | None:
    """Return the dotted callee of a sole ``return f(params)`` body, else ``None``."""
    if len(body) != 1:
        return None
    statement = body[0]
    if not isinstance(statement, ast.Return) or not isinstance(statement.value, ast.Call):
        return None
    call = statement.value
    parameters = set(names)
    if not all(isinstance(arg, ast.Name) and arg.id in parameters for arg in call.args):
        return None
    return _resolved(call.func, module)


def predicates(module: Module) -> dict[str, Predicate]:
    """Return every narrowing predicate in ``module`` by qualified name."""
    found: dict[str, Predicate] = {}
    for qualname, definition in _functions(module).items():
        node = definition.node
        if isinstance(node, ast.ClassDef):
            continue
        claim = _narrowing_claim(node, module)
        if claim is None:
            continue
        names = [argument.arg for argument in _parameters(node)]
        renamed = {name: f"${index}" for index, name in enumerate(names)}
        body = _body(node)
        stub = all(
            isinstance(statement, ast.Pass)
            or (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and statement.value.value is Ellipsis
            )
            for statement in body
        )
        canonical_body = ast.Module(
            body=[
                statement
                for statement in (_canonical(each, module, renamed) for each in body)
                if isinstance(statement, ast.stmt)
            ],
            type_ignores=[],
        )
        found[qualname] = Predicate(
            path=module.path,
            qualname=qualname,
            dotted=f"{module.name}.{qualname}",
            line=node.lineno,
            claim=ast.unparse(claim),
            claim_key=ast.unparse(_canonical(claim, module)),
            body="\n".join(ast.unparse(statement) for statement in body),
            body_key=ast.dump(canonical_body),
            stub=stub,
            delegate=_delegate(body, module, names),
            unproven=() if _inspects_elements(body) else tuple(unproven_arguments(claim, module)),
        )
    return found


def _follow(
    dotted: str,
    index: Mapping[str, Predicate],
    modules: Mapping[str, Module],
) -> Predicate | None:
    """Return the predicate ``dotted`` names, following re-exports through module bindings."""
    for _ in range(5):
        if dotted in index:
            return index[dotted]
        owner, _, name = dotted.rpartition(".")
        module = modules.get(owner)
        if module is None or name not in module.bindings:
            return None
        target = module.bindings[name]
        if target == dotted:
            return None
        dotted = target
    return None


def _predicate_row(
    status: str,
    predicate: Predicate,
    index: Mapping[str, Predicate],
    modules: Mapping[str, Module],
) -> Row:
    """Return the row for a new or changed predicate, flagged by the claim, delegation and duplicate rules."""
    flags: list[str] = (
        [
            f"claim names type arguments a class check cannot prove: {', '.join(predicate.unproven)}",
        ]
        if predicate.unproven
        else []
    )
    if predicate.delegate is not None:
        delegate = _follow(predicate.delegate, index, modules)
        if delegate is not None and delegate.claim_key != predicate.claim_key:
            flags.append(
                f"delegates to {delegate.site}, whose claim is {delegate.claim}, "
                f"while claiming {predicate.claim}",
            )
    if not predicate.stub:
        flags.extend(
            f"same body as {other.site} (claim {other.claim})"
            for other in index.values()
            if other.body_key == predicate.body_key and other.dotted != predicate.dotted
        )
    details = [f"- {flag}" for flag in flags]
    details.append(f"claim: {predicate.claim}")
    body_lines = predicate.body.splitlines()
    details.append("body:")
    details.extend(f"  {line}" for line in body_lines[:15])
    if len(body_lines) > 15:
        details.append(f"  ... ({len(body_lines) - 15} more lines)")
    return Row(f"{status} {predicate.site} (line {predicate.line})", details, flagged=bool(flags))


def predicate_section(
    base: Mapping[str, Module],
    head: Mapping[str, Module],
    changed: Iterable[str],
) -> Section:
    """Section 1: new, removed and changed narrowing predicates in the changed files."""
    head_predicates = {path: predicates(module) for path, module in head.items()}
    index = {
        predicate.dotted: predicate
        for found in head_predicates.values()
        for predicate in found.values()
    }
    modules = {module.name: module for module in head.values()}
    rows: list[Row] = []
    counts: Counter[str] = Counter()
    for path in sorted(changed):
        before = predicates(base[path]) if path in base else {}
        after = head_predicates.get(path, {})
        for qualname, predicate in after.items():
            old = before.get(qualname)
            if old is None:
                status = "new"
            elif (old.claim_key, old.body_key) != (predicate.claim_key, predicate.body_key):
                status = "changed"
            else:
                continue
            counts[status] += 1
            rows.append(_predicate_row(status, predicate, index, modules))
        for qualname, predicate in before.items():
            if qualname not in after:
                counts["removed"] += 1
                rows.append(Row(f"removed {predicate.site} (claim {predicate.claim})"))
    summary = f"{counts['new']} new, {counts['changed']} changed, {counts['removed']} removed"
    return Section("1. Narrowing predicates", summary, rows)


# --- section 2: widened signatures -----------------------------------------------------


def _wide_count(node: ast.expr | None, module: Module) -> int:
    """Return how many ``object`` / ``Any`` names an annotation holds (string parts parsed)."""
    expr = _annotation(node)
    if expr is None:
        return 0
    count = 0
    for child in ast.walk(expr):
        if (
            isinstance(child, (ast.Name, ast.Attribute))
            and _resolved(child, module) in _WIDE_TYPES
        ):
            count += 1
        elif (
            isinstance(child, ast.Constant) and isinstance(child.value, str) and child is not expr
        ):
            count += _wide_count(child, module)
    return count


def _is_top_wide(node: ast.expr | None, module: Module, depth: int = 0) -> bool:
    """Return whether an annotation is ``object`` / ``Any`` itself, through unions and ``type[...]``.

    ``object`` as a type argument (``QuerySet[Model, object]``, ``Info[object, object]``)
    is the widest claim a generic can make, not a widened parameter.
    """
    expr = _annotation(node)
    if expr is None or depth > 4:
        return False
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.BitOr):
        return _is_top_wide(expr.left, module, depth + 1) or _is_top_wide(
            expr.right,
            module,
            depth + 1,
        )
    if isinstance(expr, ast.Subscript) and (_resolved(expr.value, module) or "") in _TRANSPARENT:
        arguments = list(expr.slice.elts) if isinstance(expr.slice, ast.Tuple) else [expr.slice]
        return any(_is_top_wide(argument, module, depth + 1) for argument in arguments)
    return _resolved(expr, module) in _WIDE_TYPES


def signature(node: _FunctionNode, module: Module) -> list[Slot]:
    """Return a function's parameters and its return as slots, a bare ``self``/``cls`` dropped."""
    slots: list[Slot] = []
    for position, argument in enumerate(_parameters(node)):
        if position == 0 and argument.annotation is None and argument.arg in {"self", "cls"}:
            continue
        annotation = None if argument.annotation is None else ast.unparse(argument.annotation)
        slots.append(
            Slot(
                argument.arg,
                annotation,
                _wide_count(argument.annotation, module),
                top_wide=_is_top_wide(argument.annotation, module),
            ),
        )
    returns = None if node.returns is None else ast.unparse(node.returns)
    slots.append(
        Slot(
            "return",
            returns,
            _wide_count(node.returns, module),
            top_wide=_is_top_wide(node.returns, module),
        ),
    )
    return slots


def _widened(before: Sequence[Slot], after: Sequence[Slot]) -> list[str]:
    """Return a line per slot of ``after`` that is wider than its ``before`` twin."""
    old = {slot.name: slot for slot in before}
    lines: list[str] = []
    for slot in after:
        previous = old.get(slot.name)
        if previous is None:
            if slot.top_wide:
                lines.append(f"new parameter {slot.name}: {slot.annotation}")
        elif previous.annotation is not None and slot.annotation is None:
            lines.append(f"{slot.name}: {previous.annotation} -> (unannotated)")
        elif slot.wide > previous.wide:
            lines.append(f"{slot.name}: {previous.annotation} -> {slot.annotation}")
    return lines


def signature_section(
    base: Mapping[str, Module],
    head: Mapping[str, Module],
    changed: Iterable[str],
) -> Section:
    """Section 2: widened signatures, then new public functions taking or returning a wide type."""
    widened: list[Row] = []
    public: list[Row] = []
    for path in sorted(changed):
        if path not in head:
            continue
        module = head[path]
        before = _functions(base[path]) if path in base else {}
        for qualname, definition in _functions(module).items():
            node = definition.node
            if isinstance(node, ast.ClassDef):
                continue
            slots = signature(node, module)
            old = before.get(qualname)
            if old is not None and not isinstance(old.node, ast.ClassDef):
                lines = _widened(signature(old.node, base[path]), slots)
                if lines:
                    widened.append(Row(f"widened {path}::{qualname}", lines, flagged=True))
            elif old is None and definition.public and path.startswith(f"{PACKAGE}/"):
                wide = [slot for slot in slots if slot.top_wide]
                if wide:
                    public.append(
                        Row(
                            f"new public {path}::{qualname}",
                            [f"{slot.name}: {slot.annotation}" for slot in wide],
                            flagged=True,
                        ),
                    )
    summary = f"{len(widened)} widened, {len(public)} new public with object/Any"
    return Section("2. Widened signatures", summary, widened + public)


# --- section 3: declared-but-defaulted reads -------------------------------------------


def _shallow_walk(root: ast.ClassDef) -> Iterator[ast.AST]:
    """Yield every node under a class body without entering a nested class."""
    stack: list[ast.AST] = list(root.body)
    while stack:
        node = stack.pop()
        yield node
        stack.extend(
            child for child in ast.iter_child_nodes(node) if not isinstance(child, ast.ClassDef)
        )


def defaulted_reads(module: Module) -> dict[tuple[str, str, str], list[int]]:
    """Return ``(class, attribute, reader) -> lines`` for each declared attribute read with a default."""
    found: dict[tuple[str, str, str], list[int]] = {}
    for definition in symbols(module.tree, module.name):
        node = definition.node
        if not isinstance(node, ast.ClassDef):
            continue
        declared = {
            statement.target.id
            for statement in node.body
            if isinstance(statement, ast.AnnAssign)
            and statement.value is None
            and isinstance(statement.target, ast.Name)
        }
        if not declared:
            continue
        for child in _shallow_walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            reader = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else ""
            )
            if _DEFAULTED_READERS.get(reader) != len(child.args):
                continue
            owner, attribute = child.args[0], child.args[1]
            if (
                isinstance(owner, ast.Name)
                and owner.id in {"self", "cls"}
                and isinstance(attribute, ast.Constant)
                and isinstance(attribute.value, str)
                and attribute.value in declared
            ):
                key = (definition.qualname, attribute.value, reader)
                found.setdefault(key, []).append(child.lineno)
    return found


def defaulted_section(
    base: Mapping[str, Module],
    head: Mapping[str, Module],
    changed: Iterable[str],
) -> Section:
    """Section 3: new reads of a declared attribute through a defaulting reader."""
    rows: list[Row] = []
    for path in sorted(changed):
        if path not in head:
            continue
        before = defaulted_reads(base[path]) if path in base else {}
        for (owner, attribute, reader), lines in sorted(defaulted_reads(head[path]).items()):
            if len(lines) > len(before.get((owner, attribute, reader), [])):
                rows.append(
                    Row(
                        f"{path}::{owner} declares `{attribute}` and reads it through "
                        f"{reader}(self, ...) (line {', '.join(map(str, sorted(lines)))})",
                        flagged=True,
                    ),
                )
    return Section("3. Declared-but-defaulted reads", f"{len(rows)} new", rows)


# --- section 4: ledger moves -----------------------------------------------------------


def _site_parameters(site: str, read: Callable[[str], str | None]) -> tuple[list[str], bool]:
    """Return a ledger site's parameters (``name: annotation``) and whether one is wide."""
    path, _, qualname = site.partition("::")
    if not qualname:
        return ["(module-level site)"], False
    text = read(path)
    if text is None:
        return [f"({path} is absent at the head revision)"], False
    module = parse_module(path, text)
    definition = next(
        (each for each in symbols(module.tree, module.name) if each.qualname == qualname),
        None,
    )
    if definition is None:
        return [f"({qualname} not found at the head revision)"], False
    if isinstance(definition.node, ast.ClassDef):
        return ["(class site)"], False
    slots = signature(definition.node, module)[:-1]
    shown = [f"{slot.name}: {slot.annotation or '(unannotated)'}" for slot in slots]
    return shown or ["(no parameters)"], any(slot.top_wide for slot in slots)


def _pair(
    vanished: list[str],
    appeared: list[str],
) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """Pair vanished and appeared sites of one kind, same file first; return pairs and leftovers."""
    remaining = sorted(vanished)
    pairs: list[tuple[str, str]] = []
    unpaired: list[str] = []
    for new in sorted(appeared):
        path = new.partition("::")[0]
        match = next((old for old in remaining if old.partition("::")[0] == path), None)
        if match is None and remaining:
            match = remaining[0]
        if match is None:
            unpaired.append(new)
        else:
            remaining.remove(match)
            pairs.append((match, new))
    return pairs, unpaired, remaining


def ledger_section(
    base_ledger: str | None,
    head_ledger: str | None,
    read_head: Callable[[str], str | None],
) -> Section:
    """Section 4: ledger totals, moves (with the new site's parameters), growth and clears."""
    before = check_type_suppressions.parse_ledger(base_ledger or "", frozenset())
    after = check_type_suppressions.parse_ledger(head_ledger or "", frozenset())
    old_totals = check_type_suppressions.kind_totals(before)
    new_totals = check_type_suppressions.kind_totals(after)
    vanished: dict[str, list[str]] = {}
    appeared: dict[str, list[str]] = {}
    for site, kind in sorted(before.keys() | after.keys()):
        delta = after[site, kind] - before[site, kind]
        target = appeared if delta > 0 else vanished
        target.setdefault(kind, []).extend([site] * abs(delta))
    rows: list[Row] = []
    for kind in sorted(vanished.keys() | appeared.keys()):
        pairs, grown, cleared = _pair(vanished.get(kind, []), appeared.get(kind, []))
        for old, new in pairs:
            shown, wide = _site_parameters(new, read_head)
            details = [f"from {old}", f"parameters: {', '.join(shown)}"]
            if wide:
                details.insert(
                    0,
                    "- moved into a function taking object/Any: one ignore covers every call",
                )
            rows.append(Row(f"move `{kind}` -> {new}", details, flagged=wide))
        for new in grown:
            shown, _ = _site_parameters(new, read_head)
            rows.append(
                Row(f"new `{kind}` at {new}", [f"parameters: {', '.join(shown)}"], flagged=True),
            )
        rows.extend(Row(f"cleared `{kind}` at {old}") for old in cleared)
    moved = [
        f"{kind} {old_totals[kind]} -> {new_totals[kind]}"
        for kind in sorted(old_totals.keys() | new_totals.keys())
        if old_totals[kind] != new_totals[kind]
    ]
    summary = (
        f"total {sum(old_totals.values())} -> {sum(new_totals.values())}"
        f"{'; ' + ', '.join(moved) if moved else ''}"
    )
    return Section("4. Ledger moves", summary, rows)


# --- section 5: other suppression channels ---------------------------------------------


def channel_counts(text: str) -> Counter[str]:
    """Count ``# truth: ok`` markers, ``noqa`` codes and orphan ``# basedpyright:`` reason lines.

    Raises:
        tokenize.TokenError: ``text`` does not tokenize.

    """
    counts: Counter[str] = Counter()
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    for position, token in enumerate(tokens):
        if token.type != tokenize.COMMENT:
            continue
        if _TRUTH.search(token.string):
            counts[_TRUTH_KEY] += 1
        for match in _NOQA.finditer(token.string):
            codes = match.group("codes")
            for code in codes.split(",") if codes else ["(bare)"]:
                counts[f"noqa {code.strip().upper()}"] += 1
        if _REASON.match(token.string) and token.line.lstrip().startswith("#"):
            later = tokens[position + 1 :]
            start = next(
                (
                    index
                    for index, each in enumerate(later)
                    if each.type not in {tokenize.COMMENT, tokenize.NL}
                ),
                len(later),
            )
            covered = False
            for each in later[start:]:
                if each.type == tokenize.COMMENT and _IGNORE.search(each.string):
                    covered = True
                    break
                if each.type in {tokenize.NEWLINE, tokenize.ENDMARKER}:
                    break
            if not covered:
                counts[_ORPHAN_KEY] += 1
    return counts


def _flags_rise(key: str) -> bool:
    """Return whether a rise in ``key``'s count is flagged."""
    if key in {_TRUTH_KEY, _ORPHAN_KEY}:
        return True
    code = key.removeprefix("noqa ")
    return key.startswith("noqa ") and code.startswith(_TYPING_NOQA)


def channel_section(
    base: Mapping[str, Module],
    head: Mapping[str, Module],
    changed: Iterable[str],
) -> Section:
    """Section 5: count deltas of the channels the ledger does not read."""
    before: Counter[str] = Counter()
    after: Counter[str] = Counter()
    for path in changed:
        if path in base:
            before.update(channel_counts(base[path].text))
        if path in head:
            after.update(channel_counts(head[path].text))
    rows = [
        Row(
            f"{key}: {before[key]} -> {after[key]} ({after[key] - before[key]:+d})",
            flagged=after[key] > before[key] and _flags_rise(key),
        )
        for key in sorted(before.keys() | after.keys())
        if after[key] != before[key]
    ]
    return Section("5. Other suppression channels", f"{len(rows)} count(s) moved", rows)


# --- assembly --------------------------------------------------------------------------


def build_report(
    labels: tuple[str, str],
    scope: Sequence[str],
    sources: tuple[Mapping[str, str], Mapping[str, str]],
    ledgers: tuple[str | None, str | None],
    read_head: Callable[[str], str | None],
) -> Report:
    """Build the report from each revision's scoped sources (path to text) and ledger text.

    ``read_head`` reads a file at the head revision outside the scope (a ledger site).

    Raises:
        SyntaxError: A changed file in scope does not parse.
        tokenize.TokenError: A changed file in scope does not tokenize.
        ValueError: A ledger is invalid.

    """
    base_sources, head_sources = sources
    changed = sorted(
        path
        for path in base_sources.keys() | head_sources.keys()
        if base_sources.get(path) != head_sources.get(path)
    )
    head = {path: parse_module(path, text) for path, text in head_sources.items()}
    base = {
        path: parse_module(path, base_sources[path]) for path in changed if path in base_sources
    }
    return Report(
        labels[0],
        labels[1],
        tuple(scope),
        [
            predicate_section(base, head, changed),
            signature_section(base, head, changed),
            defaulted_section(base, head, changed),
            ledger_section(ledgers[0], ledgers[1], read_head),
            channel_section(base, head, changed),
        ],
    )


def _commit(rev: str) -> str:
    """Return the commit ``rev`` names.

    Raises:
        subprocess.CalledProcessError: ``rev`` names no commit.

    """
    return _git.run_git(
        REPO_ROOT,
        "rev-parse",
        "--verify",
        f"{rev}^{{commit}}",
        check=True,
    ).stdout.strip()


def _blobs(commit: str, paths: Sequence[str]) -> dict[str, str]:
    """Return each ``.py`` file under ``paths`` at ``commit``, path to blob id.

    Raises:
        subprocess.CalledProcessError: git cannot list the tree.

    """
    listing = _git.run_git(
        REPO_ROOT,
        "ls-tree",
        "-r",
        "-z",
        commit,
        "--",
        *paths,
        check=True,
    ).stdout
    blobs: dict[str, str] = {}
    for entry in listing.split("\0"):
        meta, _, path = entry.partition("\t")
        fields = meta.split()
        if len(fields) == 3 and fields[1] == "blob" and path.endswith(".py"):
            blobs[path] = fields[2]
    return blobs


def _read_blobs(ids: Iterable[str]) -> dict[str, str]:
    """Return each blob's text, read in one ``git cat-file --batch``.

    Raises:
        subprocess.CalledProcessError: git fails.
        ValueError: git reports a blob missing, or a blob is not UTF-8.

    """
    ordered = sorted(set(ids))
    if not ordered:
        return {}
    output = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "--no-pager",
            "cat-file",
            "--batch",
        ],
        input="".join(f"{blob}\n" for blob in ordered).encode(),
        capture_output=True,
        env=_git.repository_env(),
        check=True,
    ).stdout
    texts: dict[str, str] = {}
    position = 0
    for blob in ordered:
        end = output.index(b"\n", position)
        header = output[position:end].split()
        if len(header) != 3 or header[1] != b"blob":
            raise ValueError(f"git cannot read blob {blob}")
        start = end + 1
        texts[blob] = output[start : start + int(header[2])].decode("utf-8")
        position = start + int(header[2]) + 1
    return texts


def _show(commit: str, path: str) -> str | None:
    """Return ``path`` at ``commit``, or ``None`` when the commit has no such file."""
    result = _git.run_git(REPO_ROOT, "show", f"{commit}:{path}")
    return None if result.returncode else result.stdout


def main(argv: Sequence[str] | None = None) -> int:
    """Print the typing report for ``base..head``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    _ = parser.add_argument("base", help="the revision the range starts from")
    _ = parser.add_argument(
        "--head",
        default="HEAD",
        help="the revision it ends at (default HEAD)",
    )
    _ = parser.add_argument(
        "--paths",
        nargs="+",
        default=[PACKAGE],
        help=f"the trees to read (default {PACKAGE}); the ledger section always reads the whole ledger",
    )
    _ = parser.add_argument("--json", action="store_true", help="print the report as JSON")
    _ = parser.add_argument(
        "--fail-on-flags",
        action="store_true",
        help="exit 1 when any row is flagged",
    )
    args = parser.parse_args(argv, namespace=_Args())
    try:
        base_commit, head_commit = _commit(args.base), _commit(args.head)
        base_blobs, head_blobs = _blobs(base_commit, args.paths), _blobs(head_commit, args.paths)
        texts = _read_blobs([*base_blobs.values(), *head_blobs.values()])
        report = build_report(
            (args.base, args.head),
            args.paths,
            (
                {path: texts[blob] for path, blob in base_blobs.items()},
                {path: texts[blob] for path, blob in head_blobs.items()},
            ),
            (_show(base_commit, LEDGER), _show(head_commit, LEDGER)),
            lambda path: _show(head_commit, path),
        )
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"typing-delta: git cannot read the range: {error}", file=sys.stderr)
        return 2
    except (SyntaxError, ValueError, tokenize.TokenError) as error:
        print(f"typing-delta: cannot read a file in the range: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report.as_json(), indent=2))
    else:
        print(report.text(), end="")
    return 1 if args.fail_on_flags and report.flagged else 0


if __name__ == "__main__":
    sys.exit(main())
