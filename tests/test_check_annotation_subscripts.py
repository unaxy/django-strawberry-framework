"""Script tests for the ``annotation-subscripts`` gate in ``scripts/check_annotation_subscripts.py``.

Pins the name resolution (aliased, dotted and relative imports, module-level names,
builtins, an unresolvable name), the evaluated / never-evaluated split
(``TYPE_CHECKING`` spelled through ``typing``, ``typing_extensions`` and an alias,
its negation, function-local annotations, a function-local class body), string
annotations (parsed, ``Literal`` and ``Annotated`` metadata skipped, unparseable), a
``TypeAlias`` value (visited at run time, skipped under ``TYPE_CHECKING``),
``typing.cast`` (unquoted visited, quoted skipped), the tables (a hit, an unseen
target, a checker-only target, a version-gated verdict, an audited site, an
over-count and a stale entry), the ``requires-python`` floor read, and the CLI exit
codes. ``tests/base/test_init.py`` audits the tables against the running
interpreter. The script inspects source files, not a GraphQL request, so there is no
live sibling in ``examples/fakeshop/test_query/``.
"""

import textwrap
from pathlib import Path

import pytest

from scripts import check_annotation_subscripts as cas

OPTIONS = "django.db.models.options.Options"
PYPROJECT = '[project]\nname = "pkg"\nrequires-python = ">=3.10"\n'


def _findings(
    root: Path,
    source: str,
    *,
    relative: str = "pkg/mod.py",
    table: dict[str, bool | tuple[int, int]] | None = None,
    audited: dict[tuple[str, str], int] | None = None,
    checker_only: frozenset[str] | None = None,
    floor: tuple[int, int] = (3, 10),
) -> list[str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    text = textwrap.dedent(source)
    path.write_text(text, encoding="utf-8")
    found = cas.findings(
        cas.scan_source(text, relative),
        root,
        {OPTIONS: False, "builtins.list": True} if table is None else table,
        {} if audited is None else audited,
        frozenset() if checker_only is None else checker_only,
        floor,
    )
    return [finding.render() for finding in found]


def test_table_hit_passes(tmp_path: Path) -> None:
    source = """
        from django.db.models import QuerySet

        def f(rows: QuerySet[int]) -> list[int]: ...
    """
    table: dict[str, bool | tuple[int, int]] = {
        "django.db.models.QuerySet": True,
        "builtins.list": True,
    }
    assert _findings(tmp_path, source, table=table) == []


def test_unseen_target_fails_closed(tmp_path: Path) -> None:
    source = """
        from vendor.models import Thing

        def f(thing: Thing[int]) -> None: ...
    """
    (line,) = _findings(tmp_path, source)
    assert line.startswith("pkg/mod.py:4: `vendor.models.Thing` (parameter annotation)")
    assert "neither SUBSCRIPTABLE nor CHECKER_ONLY" in line


def test_evaluated_false_target_fails(tmp_path: Path) -> None:
    source = """
        from django.db.models.options import Options

        def f() -> Options[int]: ...
    """
    (line,) = _findings(tmp_path, source)
    assert f"`{OPTIONS}` has no runtime subscript hook and this return annotation" in line


@pytest.mark.parametrize(
    ("imports", "spelling"),
    [
        ("from django.db.models.options import Options as Opts", "Opts"),
        ("from django.db.models import options as opts", "opts.Options"),
        ("import django.db.models.options", "django.db.models.options.Options"),
        ("import django.db.models.options as opts", "opts.Options"),
    ],
)
def test_aliased_and_dotted_imports_resolve(tmp_path: Path, imports: str, spelling: str) -> None:
    source = f"{imports}\n\nvalue: {spelling}[int]\n"
    (line,) = _findings(tmp_path, source)
    assert f"`{OPTIONS}` has no runtime subscript hook and this variable annotation" in line


def test_relative_import_resolves_against_the_package(tmp_path: Path) -> None:
    source = """
        from ..models import Thing as T

        def f(thing: T[int]) -> None: ...
    """
    (line,) = _findings(tmp_path, source, relative="pkg/sub/mod.py")
    assert "`pkg.models.Thing`" in line


def test_module_level_name_resolves_to_the_module(tmp_path: Path) -> None:
    source = """
        class Box: ...

        def f(box: Box[int]) -> None: ...
    """
    (line,) = _findings(tmp_path, source)
    assert "`pkg.mod.Box`" in line


def test_unresolvable_name_fails_closed(tmp_path: Path) -> None:
    (line,) = _findings(tmp_path, "def f(thing: Mystery[int]) -> None: ...\n")
    assert "`Mystery` (parameter annotation) resolves to no import" in line


@pytest.mark.parametrize(
    "guard",
    [
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:",
        "import typing\nif typing.TYPE_CHECKING:",
        "import typing as t\nif t.TYPE_CHECKING:",
        "from typing_extensions import TYPE_CHECKING as TC\nif TC:",
        "from typing import TYPE_CHECKING\nif not TYPE_CHECKING:\n    pass\nelse:",
    ],
)
def test_type_checking_body_is_never_evaluated(tmp_path: Path, guard: str) -> None:
    source = f"from django.db.models.options import Options\n{guard}\n    value: Options[int]\n"
    (line,) = _findings(tmp_path, source)
    assert "(`if TYPE_CHECKING:` body): `pkg/mod.py::value` holds 1, AUDITED_SITES 0" in line
    assert _findings(tmp_path, source, audited={("pkg/mod.py::value", OPTIONS): 1}) == []


@pytest.mark.parametrize(
    "guard",
    [
        "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    pass\nelse:",
        "from typing import TYPE_CHECKING\nif not TYPE_CHECKING:",
        "TYPE_CHECKING = False\nif TYPE_CHECKING:",
    ],
)
def test_runtime_branch_is_evaluated(tmp_path: Path, guard: str) -> None:
    source = f"from django.db.models.options import Options\n{guard}\n    value: Options[int]\n"
    (line,) = _findings(tmp_path, source)
    assert "this variable annotation can be evaluated" in line


def test_function_local_annotation_is_audited_by_count(tmp_path: Path) -> None:
    source = """
        from django.db.models.options import Options

        def f(model: object) -> None:
            meta: Options[int] = model._meta
            other: Options[int] = model._meta
    """
    site = ("pkg/mod.py::f", OPTIONS)
    assert _findings(tmp_path, source, audited={site: 2}) == []
    (over,) = _findings(tmp_path, source, audited={site: 1})
    assert over.startswith("pkg/mod.py:5: ")
    assert "(function-local annotation): `pkg/mod.py::f` holds 2, AUDITED_SITES 1" in over


def test_stale_audited_site_fails(tmp_path: Path) -> None:
    audited = {("pkg/mod.py::gone", OPTIONS): 1}
    (line,) = _findings(tmp_path, "value: list[int] = []\n", audited=audited)
    assert line == (
        f"pkg/mod.py:1: AUDITED_SITES records 1 `{OPTIONS}` at `pkg/mod.py::gone`, the tree "
        "holds 0: drop the stale entry"
    )


def test_function_local_class_body_is_evaluated(tmp_path: Path) -> None:
    source = """
        from django.db.models.options import Options

        def f() -> None:
            class Local:
                meta: Options[int]
    """
    (line,) = _findings(tmp_path, source)
    assert "this variable annotation can be evaluated" in line


def test_string_annotation_is_parsed(tmp_path: Path) -> None:
    source = """
        from django.db.models.options import Options

        def f(model: "list[Options[int]]") -> None: ...
    """
    (line,) = _findings(tmp_path, source)
    assert line.startswith(f"pkg/mod.py:4: `{OPTIONS}` has no runtime subscript hook")


@pytest.mark.parametrize("value", ['"Options[int]"', 'list["Options[int]"]'])
def test_runtime_type_alias_value_is_evaluated(tmp_path: Path, value: str) -> None:
    source = f"""
        from typing import TypeAlias
        from django.db.models.options import Options

        Alias: TypeAlias = {value}
    """
    (line,) = _findings(tmp_path, source)
    assert line.startswith(f"pkg/mod.py:5: `{OPTIONS}` has no runtime subscript hook")
    assert "this type alias value can be evaluated" in line


def test_type_checking_alias_value_is_not_visited(tmp_path: Path) -> None:
    source = """
        from typing import TYPE_CHECKING, TypeAlias
        from django.db.models.options import Options

        if TYPE_CHECKING:
            Alias: TypeAlias = Options[int]
        else:
            Alias = Options
    """
    assert _findings(tmp_path, source) == []


def test_literal_and_annotated_metadata_are_not_parsed(tmp_path: Path) -> None:
    source = """
        from typing import Annotated, Literal

        def f(kind: Literal["Options[int]", "not valid("]) -> Annotated[int, "meta("]: ...
    """
    table: dict[str, bool | tuple[int, int]] = {"typing.Literal": True, "typing.Annotated": True}
    assert _findings(tmp_path, source, table=table) == []


def test_unparseable_string_annotation_fails(tmp_path: Path) -> None:
    (line,) = _findings(tmp_path, 'def f(thing: "not valid(") -> None: ...\n')
    assert "string parameter annotation 'not valid(' does not parse" in line


@pytest.mark.parametrize(
    ("imports", "call"),
    [
        ("from typing import cast", "cast"),
        ("import typing", "typing.cast"),
        ("from typing_extensions import cast as narrow", "narrow"),
    ],
)
def test_unquoted_cast_argument_is_evaluated(tmp_path: Path, imports: str, call: str) -> None:
    source = f"""
        {imports}
        from django.db.models.options import Options

        def f(model: object) -> object:
            return {call}(Options[int], model)
    """
    (line,) = _findings(tmp_path, source)
    assert "this `cast` argument can be evaluated" in line


def test_quoted_cast_argument_is_not_visited(tmp_path: Path) -> None:
    source = """
        from typing import cast
        from django.db.models.options import Options

        def f(model: object) -> object:
            return cast("Options[int]", model)
    """
    assert _findings(tmp_path, source) == []


def test_checker_only_target_passes(tmp_path: Path) -> None:
    source = """
        from pkg.hooks import _Builder

        def f(builder: _Builder[int]) -> None: ...
    """
    assert _findings(tmp_path, source, checker_only=frozenset({"pkg.hooks._Builder"})) == []


@pytest.mark.parametrize(("floor", "count"), [((3, 13), 1), ((3, 14), 0)])
def test_version_gated_verdict_follows_the_floor(
    tmp_path: Path,
    floor: tuple[int, int],
    count: int,
) -> None:
    source = "def f(method: classmethod[object, ..., object]) -> None: ...\n"
    table: dict[str, bool | tuple[int, int]] = {"builtins.classmethod": (3, 14)}
    assert len(_findings(tmp_path, source, table=table, floor=floor)) == count


def test_python_floor_reads_requires_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    assert cas.python_floor(tmp_path) == (3, 10)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nrequires-python = "~=3.10"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="requires-python is not"):
        _ = cas.python_floor(tmp_path)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway repo root with an empty package and no audited sites."""
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (tmp_path / cas.PACKAGE).mkdir()
    monkeypatch.setattr(cas, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cas, "AUDITED_SITES", {})
    return tmp_path


def test_cli_passes_a_clean_package(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _ = (repo / cas.PACKAGE / "mod.py").write_text("value: list[int] = []\n", encoding="utf-8")
    assert cas.main([]) == 0
    assert capsys.readouterr().out == (
        "annotation-subscripts: checked 1 file(s); 1 subscript(s); 0 finding(s)\n"
    )


def test_cli_fails_on_a_finding(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = "from django.db.models.options import Options\n\nvalue: Options[int]\n"
    _ = (repo / cas.PACKAGE / "mod.py").write_text(source, encoding="utf-8")
    assert cas.main([]) == 1
    assert f"{cas.PACKAGE}/mod.py:3: `{OPTIONS}`" in capsys.readouterr().out


@pytest.mark.usefixtures("repo")
def test_cli_fails_on_an_empty_package(capsys: pytest.CaptureFixture[str]) -> None:
    assert cas.main([]) == 1
    assert "checked 0 file(s)" in capsys.readouterr().out


def test_cli_refuses_an_unparseable_file(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _ = (repo / cas.PACKAGE / "mod.py").write_text("def broken(:\n", encoding="utf-8")
    assert cas.main([]) == 2
    assert f"{cas.PACKAGE}/mod.py: cannot scan:" in capsys.readouterr().err


def test_the_package_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert cas.main([]) == 0
    assert capsys.readouterr().out.endswith(" 0 finding(s)\n")
