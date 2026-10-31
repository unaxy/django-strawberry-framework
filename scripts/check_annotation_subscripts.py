"""Refuse a package annotation that subscripts a class with no runtime subscript hook.

django-stubs makes ``Options``, ``Field``, ``Lookup``, ``ModelForm`` and other Django
classes generic for the type checker, but at run time only ``django_stubs_ext.monkeypatch()``
gives them ``__class_getitem__``, and a consumer's process never runs that patch. An
annotation ``Options[Model]`` is harmless while nothing evaluates it and raises
``TypeError`` the moment ``typing.get_type_hints`` (Strawberry's resolver introspection
included) does. ``tests/base/test_init.py::test_annotations_evaluate_without_django_stubs_ext_patch``
evaluates the module-level annotations an introspector can reach, in the slow test
cells; this gate reads the same shape statically, in the lint job, and also where that
evaluation does not reach: a function or class defined inside a function, a
function-local variable annotation, anything under ``if TYPE_CHECKING:``, and an
unquoted ``typing.cast`` type argument, which runs on every call.

Each ``.py`` under ``django_strawberry_framework/`` is parsed with ``ast`` (never
imported). The sweep visits every annotation (parameter, return, and annotated
assignment at any scope), every string inside one parsed as an expression (the
arguments of ``Literal`` and the metadata of ``Annotated`` excepted), and the unquoted
first argument of a call that resolves to ``typing.cast`` / ``typing_extensions.cast``
(a quoted one is text nothing evaluates or introspects). A ``TypeAlias`` value outside
``if TYPE_CHECKING:`` and outside a function body is visited as an evaluated annotation,
since an annotation naming the alias evaluates to it, a string value included; under
``if TYPE_CHECKING:`` it is not visited: a module-private alias there with a bare-class
``else:`` is the package's one home for a subscript of such a class.
Each subscripted name resolves to the dotted target it is bound to in the module: an
import in any scope (``import x as y``, relative imports resolved against the module's
package), a module-level class or assignment, else a builtin; an attribute chain
resolves through its head (``models.QuerySet`` is ``django.db.models.QuerySet``). A
name bound to several targets is checked against each.

Every target must appear in ``SUBSCRIPTABLE``, the audited table of whether it has a
runtime subscript hook (``__class_getitem__``, or ``__getitem__`` on its type) in a
process ``django_stubs_ext`` never patched (a target that gains one in a later Python
records that version, and counts as without one while ``requires-python`` is below
it), or in ``CHECKER_ONLY``, the package classes defined only under ``if
TYPE_CHECKING:`` (no runtime object to subscript). A target neither lists fails
closed: audit it and add it. ``tests/base/test_init.py`` checks every row of both
against the running interpreter in an unpatched process, so each CI cell (the floor
and the latest cell included) re-audits them. A target the table marks without a
hook fails at a site something can evaluate (an annotation outside ``if
TYPE_CHECKING:`` and outside a function body, or a ``cast`` argument); at a site
nothing evaluates (a function-local annotation, an ``if TYPE_CHECKING:`` body) it
fails unless ``AUDITED_SITES`` records that site with the exact count, keyed as a
citation names it (``path::QualifiedName``, ``path`` alone at module level). A
recorded count the tree no longer holds fails as stale.

Usage::

    uv run python scripts/check_annotation_subscripts.py

Exit code ``1`` (each finding listed) on any finding or when no file was scanned, ``2``
when a file cannot be read or parsed.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import tomli
from typing_extensions import TypeIs, override

try:
    import check_citations
except ModuleNotFoundError:  # imported as a ``scripts`` submodule (repo root on path)
    from scripts import check_citations

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
#: The package the sweep reads, repo-relative.
PACKAGE = "django_strawberry_framework"

#: Whether each subscripted target has a runtime subscript hook without ``django_stubs_ext``.
#: ``True``: the class defines or inherits ``__class_getitem__`` (or its type defines
#: ``__getitem__``) on every supported Python and Django; ``False``: it does not; a
#: ``(major, minor)`` pair: from that Python on, so ``False`` while the floor is below it.
SUBSCRIPTABLE: dict[str, bool | tuple[int, int]] = {
    # Builtins and the standard library: PEP 585 generics and typing special forms.
    "asyncio.Future": True,
    "asyncio.Task": True,
    "builtins.classmethod": (3, 14),
    "builtins.dict": True,
    "builtins.frozenset": True,
    "builtins.list": True,
    "builtins.set": True,
    "builtins.staticmethod": (3, 14),
    "builtins.tuple": True,
    "builtins.type": True,
    "collections.OrderedDict": True,
    "collections.abc.AsyncGenerator": True,
    "collections.abc.AsyncIterable": True,
    "collections.abc.AsyncIterator": True,
    "collections.abc.Awaitable": True,
    "collections.abc.Callable": True,
    "collections.abc.Collection": True,
    "collections.abc.Container": True,
    "collections.abc.Coroutine": True,
    "collections.abc.Generator": True,
    "collections.abc.ItemsView": True,
    "collections.abc.Iterable": True,
    "collections.abc.Iterator": True,
    "collections.abc.Mapping": True,
    "collections.abc.MutableMapping": True,
    "collections.abc.Sequence": True,
    "collections.abc.Set": True,
    "contextlib.AbstractContextManager": True,
    "contextvars.ContextVar": True,
    "contextvars.Token": True,
    "types.MappingProxyType": True,
    "typing.Annotated": True,
    "typing.ClassVar": True,
    "typing.Final": True,
    "typing.Literal": True,
    "typing.TypeGuard": True,
    "typing_extensions.TypeForm": True,
    "typing_extensions.TypeIs": True,
    "typing_extensions.Unpack": True,
    "weakref.ReferenceType": True,
    "weakref.WeakKeyDictionary": True,
    "weakref.ref": True,
    # Django: ``QuerySet`` and ``BaseManager`` (so ``Manager``) define ``__class_getitem__``;
    # ``MultiValueDict`` inherits ``dict``'s. The rest are generic only in django-stubs.
    "django.db.models.Field": False,
    "django.db.models.Manager": True,
    "django.db.models.QuerySet": True,
    "django.db.models.lookups.Lookup": False,
    "django.db.models.manager.BaseManager": True,
    "django.db.models.options.Options": False,
    "django.forms.ModelForm": False,
    "django.utils.datastructures.MultiValueDict": True,
    "django.utils.functional.LazyObject": False,
    # graphql-core and Strawberry: ``Generic`` classes and ``typing`` aliases.
    "graphql.GraphQLList": True,
    "graphql.GraphQLNonNull": True,
    "graphql.pyutils.AwaitableOrValue": True,
    "strawberry.Info": True,
    "strawberry.LazyType": True,
    "strawberry.Parent": True,
    "strawberry.http.async_base_view.AsyncBaseHTTPView": True,
    "strawberry.http.sync_base_view.SyncBaseHTTPView": True,
    "strawberry.relay.Edge": True,
    "strawberry.relay.types.ListConnection": True,
    "strawberry.relay.types.NodeIterableType": True,
    "strawberry.types.Info": True,
    "strawberry.types.info.Info": True,
    "strawberry.utils.await_maybe.AwaitableOrValue": True,
    # The package's own ``Generic`` classes and generic aliases.
    "django_strawberry_framework.connection.DjangoConnection": True,
    "django_strawberry_framework.extensions.operation_state._OperationBoundExtension": True,
    "django_strawberry_framework.extensions.operation_state._ResumedStream": True,
    "django_strawberry_framework.optimizer.plans._IndexedList": True,
    "django_strawberry_framework.sets_mixins.RelatedSetTargetMixin": True,
    "django_strawberry_framework.testing.client.Response": True,
    "django_strawberry_framework.testing.client._GraphQLTestClientBase": True,
    "django_strawberry_framework.types.finalizer._SidecarBindingSpec": True,
    "django_strawberry_framework.utils.inputs.GeneratedInputArgumentsFactory": True,
    "django_strawberry_framework.utils.operation_lease.OperationLease": True,
    "django_strawberry_framework.utils.private_state.PrivateAuthority": True,
    "django_strawberry_framework.utils.private_state.PrivateMembership": True,
    "django_strawberry_framework.utils.private_state._Entry": True,
    "django_strawberry_framework.utils.private_state._Evidence": True,
    "django_strawberry_framework.utils.private_state._IdFiledEntries": True,
    "django_strawberry_framework.utils.querysets._SealPolicy": True,
    "django_strawberry_framework.utils.truth.IdentityMap": True,
    "django_strawberry_framework.utils.truth.IdentitySet": True,
    "django_strawberry_framework.write_mixins.DeclarationRegistry": True,
}

#: Package classes defined only under ``if TYPE_CHECKING:``: no runtime object exists to
#: subscript, so any subscript of one passes.
CHECKER_ONLY: frozenset[str] = frozenset(
    {
        "django_strawberry_framework.forms.resolvers._FormBuilder",
        "django_strawberry_framework.mutations.resolvers._AsyncResolverEntry",
        "django_strawberry_framework.mutations.resolvers._SyncResolverEntry",
        "django_strawberry_framework.write_mixins._BindTarget",
        "django_strawberry_framework.write_mixins._BoundDeclaration",
    },
)

#: Sites nothing evaluates that subscript a ``False`` target: ``(site, target)`` -> count.
AUDITED_SITES: dict[tuple[str, str], int] = {
    # Function-local variable annotations: never evaluated or stored (PEP 526).
    (
        "django_strawberry_framework/forms/resolvers.py::_coerced_null_fields",
        "django.db.models.Field",
    ): 1,
    (
        "django_strawberry_framework/utils/querysets.py::resolve_order_name",
        "django.db.models.options.Options",
    ): 1,
    (
        "django_strawberry_framework/utils/relations.py::_resolve_segment_field",
        "django.db.models.options.Options",
    ): 1,
    (
        "django_strawberry_framework/utils/write_values.py::unstorable_columns",
        "django.db.models.Field",
    ): 1,
    # ``if TYPE_CHECKING:`` bodies: never executed.
    (
        "django_strawberry_framework/forms/sets.py::_ModelFormConstructionHooks.get_form",
        "django.forms.ModelForm",
    ): 1,
    (
        "django_strawberry_framework/utils/lazy.py::_LAZY_OBJECT",
        "django.utils.functional.LazyObject",
    ): 1,
    (
        "django_strawberry_framework/utils/lazy.py::unwrap_lazy_object",
        "django.utils.functional.LazyObject",
    ): 1,
    (
        "django_strawberry_framework/utils/querysets.py::_PathStep.to_opts",
        "django.db.models.options.Options",
    ): 1,
}

#: The dotted targets ``if TYPE_CHECKING:`` and ``typing.cast`` resolve to.
_TYPE_CHECKING = frozenset({"typing.TYPE_CHECKING", "typing_extensions.TYPE_CHECKING"})
_CAST = frozenset({"typing.cast", "typing_extensions.cast"})
_LITERAL = frozenset({"typing.Literal", "typing_extensions.Literal"})
_ANNOTATED = frozenset({"typing.Annotated", "typing_extensions.Annotated"})
_TYPE_ALIAS = frozenset({"typing.TypeAlias", "typing_extensions.TypeAlias"})


@dataclass(frozen=True)
class Subscript:
    """One subscripted name the sweep found: where, what it resolves to, and the context."""

    path: str
    line: int
    name: str
    targets: frozenset[str]
    evaluated: bool
    context: str
    parsed: bool = True


@dataclass(frozen=True)
class Finding:
    """One refusal: where, and why."""

    path: str
    line: int
    message: str

    def render(self) -> str:
        """Return the ``path:line: message`` line the CLI prints."""
        return f"{self.path}:{self.line}: {self.message}"


def module_identity(relative: str) -> tuple[str, str]:
    """Return ``(module, package)`` for a repo-relative ``.py`` path."""
    parts = Path(relative).with_suffix("").parts
    if parts[-1] == "__init__":
        module = ".".join(parts[:-1])
        return module, module
    module = ".".join(parts)
    return module, module.rpartition(".")[0]


def _import_base(node: ast.ImportFrom, package: str) -> str:
    """Return the absolute module a ``from ... import`` statement reads from."""
    if not node.level:
        return node.module or ""
    parts = package.split(".")
    if node.level > 1:
        parts = parts[: -(node.level - 1)]
    return ".".join([*parts, *([node.module] if node.module else [])])


def _module_level(statements: Iterable[ast.stmt]) -> Iterator[ast.stmt]:
    """Yield the module's statements, descending into ``if`` / ``try`` / ``with`` blocks."""
    for statement in statements:
        if isinstance(statement, ast.If):
            yield from _module_level(statement.body)
            yield from _module_level(statement.orelse)
        elif isinstance(statement, ast.Try):
            yield from _module_level(statement.body)
            for handler in statement.handlers:
                yield from _module_level(handler.body)
            yield from _module_level(statement.orelse)
            yield from _module_level(statement.finalbody)
        elif isinstance(statement, ast.With):
            yield from _module_level(statement.body)
        else:
            yield statement


def bindings(tree: ast.Module, module: str, package: str) -> dict[str, set[str]]:
    """Map each name the module binds to the dotted targets it may stand for.

    Imports count in every scope; classes and assignments at module level only.
    """
    bound: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    bound.setdefault(alias.asname, set()).add(alias.name)
                else:
                    head = alias.name.partition(".")[0]
                    bound.setdefault(head, set()).add(head)
        elif isinstance(node, ast.ImportFrom):
            base = _import_base(node, package)
            for alias in node.names:
                bound.setdefault(alias.asname or alias.name, set()).add(f"{base}.{alias.name}")
    for statement in _module_level(tree.body):
        names: list[str] = []
        if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(statement.name)
        elif isinstance(statement, ast.Assign):
            names.extend(target.id for target in statement.targets if isinstance(target, ast.Name))
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            names.append(statement.target.id)
        for name in names:
            bound.setdefault(name, set()).add(f"{module}.{name}")
    return bound


class _Sweep(ast.NodeVisitor):
    """Collect every subscripted name in an annotation context of one module."""

    def __init__(self, path: str, bound: Mapping[str, set[str]]) -> None:
        self.path: str = path
        self.bound: Mapping[str, set[str]] = bound
        self.found: list[Subscript] = []
        self.type_checking: bool = False
        self.in_function: bool = False

    def resolve(self, node: ast.expr) -> frozenset[str]:
        """Return the dotted targets a ``Name`` / ``Attribute`` chain may stand for."""
        if isinstance(node, ast.Name):
            if node.id in self.bound:
                return frozenset(self.bound[node.id])
            if hasattr(builtins, node.id):
                return frozenset({f"builtins.{node.id}"})
            return frozenset()
        if isinstance(node, ast.Attribute):
            return frozenset(f"{head}.{node.attr}" for head in self.resolve(node.value))
        return frozenset()

    def _is_type_checking(self, test: ast.expr) -> bool:
        return bool(self.resolve(test) & _TYPE_CHECKING)

    def annotation(
        self,
        node: ast.expr,
        *,
        evaluated: bool,
        context: str,
        line: int | None = None,
    ) -> None:
        """Record each subscript inside ``node``, string annotations parsed in place.

        ``line`` is the source line of the string a parsed ``node`` came from.
        """
        at = node.lineno if line is None else line
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                parsed = ast.parse(node.value.strip(), mode="eval").body
            except SyntaxError:
                self.found.append(
                    Subscript(
                        self.path,
                        at,
                        node.value,
                        frozenset(),
                        evaluated,
                        context,
                        parsed=False,
                    ),
                )
                return
            self.annotation(parsed, evaluated=evaluated, context=context, line=at)
            return
        children: list[ast.expr] = [
            child for child in ast.iter_child_nodes(node) if isinstance(child, ast.expr)
        ]
        if isinstance(node, ast.Subscript):
            targets = self.resolve(node.value)
            self.found.append(
                Subscript(self.path, at, ast.unparse(node.value), targets, evaluated, context),
            )
            arguments = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            if targets & _LITERAL:
                arguments = []
            elif targets & _ANNOTATED:
                arguments = arguments[:1]
            children = [node.value, *arguments]
        for child in children:
            self.annotation(child, evaluated=evaluated, context=context, line=line)

    def _context(self, default: str, *, evaluated: bool) -> str:
        if self.type_checking:
            return "`if TYPE_CHECKING:` body"
        return default if evaluated else "function-local annotation"

    @override
    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        negated = isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not)
        test = node.test.operand if isinstance(node.test, ast.UnaryOp) else node.test
        guarded = self._is_type_checking(test)
        outer = self.type_checking
        self.type_checking = outer or (guarded and not negated)
        for statement in node.body:
            self.visit(statement)
        self.type_checking = outer or (guarded and negated)
        for statement in node.orelse:
            self.visit(statement)
        self.type_checking = outer

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        evaluated = not self.type_checking
        arguments = node.args
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            arguments.vararg,
            arguments.kwarg,
        ):
            if argument is not None and argument.annotation is not None:
                self.annotation(
                    argument.annotation,
                    evaluated=evaluated,
                    context=self._context("parameter annotation", evaluated=evaluated),
                )
        if node.returns is not None:
            self.annotation(
                node.returns,
                evaluated=evaluated,
                context=self._context("return annotation", evaluated=evaluated),
            )
        for expression in (*node.decorator_list, *arguments.defaults, *arguments.kw_defaults):
            if expression is not None:
                self.visit(expression)
        outer = self.in_function
        self.in_function = True
        for statement in node.body:
            self.visit(statement)
        self.in_function = outer

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node)

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function(node)

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for expression in (*node.decorator_list, *node.bases, *node.keywords):
            self.visit(expression)
        outer = self.in_function
        self.in_function = False
        for statement in node.body:
            self.visit(statement)
        self.in_function = outer

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        evaluated = not self.type_checking and not self.in_function
        self.annotation(
            node.annotation,
            evaluated=evaluated,
            context=self._context("variable annotation", evaluated=evaluated),
        )
        self.visit(node.target)
        if node.value is None:
            return
        if evaluated and self.resolve(node.annotation) & _TYPE_ALIAS:
            # A runtime alias is an annotation by proxy: ``typing.get_type_hints`` reads
            # the value an annotation naming it evaluates to, a string value included.
            self.annotation(node.value, evaluated=True, context="type alias value")
        else:
            self.visit(node.value)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        if self.resolve(node.func) & _CAST:
            typed = [keyword.value for keyword in node.keywords if keyword.arg == "typ"]
            first = node.args[0] if node.args else (typed[0] if typed else None)
            if first is not None and not (
                isinstance(first, ast.Constant) and isinstance(first.value, str)
            ):
                evaluated = not self.type_checking
                self.annotation(
                    first,
                    evaluated=evaluated,
                    context=self._context("`cast` argument", evaluated=evaluated),
                )
        self.generic_visit(node)


def scan_source(source: str, relative: str) -> list[Subscript]:
    """Return every subscripted name in an annotation context of one module's source."""
    tree = ast.parse(source)
    module, package = module_identity(relative)
    sweep = _Sweep(relative, bindings(tree, module, package))
    sweep.visit(tree)
    return sweep.found


def site_of(subscript: Subscript, root: Path) -> str:
    """Return the citation key of the symbol holding ``subscript`` (``path`` at module level)."""
    symbol = check_citations.enclosing_symbol(root / subscript.path, subscript.line)
    return subscript.path if symbol is None else f"{subscript.path}::{symbol}"


def findings(
    subscripts: Iterable[Subscript],
    root: Path,
    table: Mapping[str, bool | tuple[int, int]] = SUBSCRIPTABLE,
    audited: Mapping[tuple[str, str], int] = AUDITED_SITES,
    checker_only: frozenset[str] = CHECKER_ONLY,
    floor: tuple[int, int] | None = None,
) -> list[Finding]:
    """Return every refusal for ``subscripts`` against the table and the audited sites.

    ``floor`` is the lowest supported Python, read from ``requires-python`` when omitted.
    """
    floor = python_floor(root) if floor is None else floor
    refused: list[Finding] = []
    counts: Counter[tuple[str, str]] = Counter()
    first: dict[tuple[str, str], Subscript] = {}
    for subscript in subscripts:
        if not subscript.parsed:
            refused.append(
                Finding(
                    subscript.path,
                    subscript.line,
                    f"string {subscript.context} {subscript.name!r} does not parse as an "
                    "expression, so the sweep cannot audit it",
                ),
            )
            continue
        if not subscript.targets:
            refused.append(
                Finding(
                    subscript.path,
                    subscript.line,
                    f"`{subscript.name}` ({subscript.context}) resolves to no import, "
                    "module-level name or builtin: bind it so the sweep can audit it",
                ),
            )
            continue
        for target in sorted(subscript.targets):
            if target in checker_only:
                continue
            verdict = table.get(target)
            if isinstance(verdict, tuple):
                verdict = verdict <= floor
            if verdict is None:
                refused.append(
                    Finding(
                        subscript.path,
                        subscript.line,
                        f"`{target}` ({subscript.context}) is in neither SUBSCRIPTABLE nor "
                        "CHECKER_ONLY: audit whether it has a runtime subscript hook without "
                        "django_stubs_ext on the floor and the latest Django, then add it",
                    ),
                )
            elif not verdict:
                if subscript.evaluated:
                    refused.append(
                        Finding(
                            subscript.path,
                            subscript.line,
                            f"`{target}` has no runtime subscript hook and this "
                            f"{subscript.context} can be evaluated: subscript it only in a "
                            "module-private `if TYPE_CHECKING:` alias with a bare-class "
                            "`else:`",
                        ),
                    )
                else:
                    key = (site_of(subscript, root), target)
                    counts[key] += 1
                    _ = first.setdefault(key, subscript)
    for key in sorted(counts.keys() | audited.keys()):
        site, target = key
        count, allowed = counts[key], audited.get(key, 0)
        if count == allowed:
            continue
        if key in first:
            subscript = first[key]
            refused.append(
                Finding(
                    subscript.path,
                    subscript.line,
                    f"`{target}` has no runtime subscript hook ({subscript.context}): "
                    f"`{site}` holds {count}, AUDITED_SITES {allowed}; use a module-private "
                    "`if TYPE_CHECKING:` alias, or record the site once audited",
                ),
            )
        else:
            refused.append(
                Finding(
                    site.partition("::")[0],
                    1,
                    f"AUDITED_SITES records {allowed} `{target}` at `{site}`, the tree holds "
                    "0: drop the stale entry",
                ),
            )
    return refused


def _is_table(value: object) -> TypeIs[dict[str, object]]:
    """Return whether a decoded TOML value is a table (TOML table keys are always strings)."""
    return isinstance(value, dict)


def python_floor(root: Path) -> tuple[int, int]:
    """Return the lowest supported Python, ``(major, minor)``, from ``requires-python``.

    Raises:
        ValueError: ``requires-python`` is not a single ``>=X.Y`` bound.

    """
    # ``tomli.loads`` returns ``dict[str, Any]``; this alias hands the read an ``object``.
    toml_loads: Callable[[str], dict[str, object]] = tomli.loads
    project = toml_loads((root / "pyproject.toml").read_text(encoding="utf-8")).get("project")
    spec = project.get("requires-python") if _is_table(project) else None
    match = re.fullmatch(r">=\s*(\d+)\.(\d+)", spec.strip()) if isinstance(spec, str) else None
    if match is None:
        raise ValueError(f"requires-python is not `>=X.Y`: {spec!r}")
    return int(match.group(1)), int(match.group(2))


def package_files(root: Path) -> list[Path]:
    """Every ``.py`` file under the package, sorted."""
    return sorted((root / PACKAGE).rglob("*.py"))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; see the module docstring."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _ = parser.parse_args(argv)
    files = package_files(REPO_ROOT)
    subscripts: list[Subscript] = []
    for path in files:
        relative = path.relative_to(REPO_ROOT).as_posix()
        try:
            subscripts.extend(scan_source(path.read_text(encoding="utf-8"), relative))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            print(f"{relative}: cannot scan: {error}", file=sys.stderr)
            return 2
    refused = findings(
        subscripts,
        REPO_ROOT,
        SUBSCRIPTABLE,
        AUDITED_SITES,
        CHECKER_ONLY,
        python_floor(REPO_ROOT),
    )
    for finding in refused:
        print(finding.render())
    print(
        f"annotation-subscripts: checked {len(files)} file(s); "
        f"{len(subscripts)} subscript(s); {len(refused)} finding(s)",
    )
    return 1 if refused or not files else 0


if __name__ == "__main__":
    raise SystemExit(main())
