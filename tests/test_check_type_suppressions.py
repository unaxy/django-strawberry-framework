"""Script tests for the ``check-type-suppressions`` gate in ``scripts/check_type_suppressions.py``.

Pins what the gate refuses (an ignore comment naming a locked rule, alone or beside other
rules or after another comment; every file-level ``pyright:`` directive; a site's ignore or
``typing.cast`` count off its ledger entry either way, including a suppression moved to a
site the ledger does not list), what it leaves alone (an unlocked rule's ignore, a bare
ignore, which basedpyright's own ``reportIgnoreCommentWithoutRule`` refuses, comment text
quoted in a string or docstring, a ``cast`` that is not ``typing``'s), how a suppression
is keyed to its site, how the ledger is read and written (``--write`` only lowers it;
``--allow-new`` records growth), the exit codes, and that the tree itself passes. The
script inspects source files, not a GraphQL request, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

import re
from collections import Counter
from pathlib import Path

import pytest

from scripts import check_type_suppressions as cts

_LOCKED = frozenset({"reportUnusedVariable", "reportRedeclaration"})

_PYPROJECT = """\
[tool.other]
reportOutside = "error"  # Locked

[tool.basedpyright]
reportRedeclaration = "error"  # Locked
reportAny = "none"

[[tool.basedpyright.executionEnvironments]]
reportAfter = "error"  # Locked
"""

_FIX = "fix the new diagnostic instead of suppressing it"
_WRITE = "run `scripts/check_type_suppressions.py --write`"


def _messages(source: str) -> list[tuple[int, str]]:
    return [(v.line, v.message) for v in cts.comment_violations("probe.py", source, _LOCKED)]


@pytest.mark.parametrize(
    "line",
    [
        "x = f()  # pyright: ignore[reportUnusedVariable]",
        "x = f()  # pyright: ignore[reportArgumentType, reportUnusedVariable]",
        "x = f()  # noqa: F841  # pyright: ignore[reportUnusedVariable]",
        "x = f()  #pyright:ignore[ reportUnusedVariable ]",
    ],
)
def test_an_ignore_naming_a_locked_rule_is_refused(line: str) -> None:
    """The locked rule is reported on the comment's line, whatever else the comment names."""
    assert _messages(f"import os\n{line}\n") == [
        (2, "`reportUnusedVariable` is locked: fix the diagnostic, never suppress it"),
    ]


@pytest.mark.parametrize(
    "directive",
    [
        "basic",
        "standard",
        "reportAttributeAccessIssue=false",
        "strict",
    ],
)
def test_every_file_level_directive_is_refused(directive: str) -> None:
    """pyproject.toml owns rule levels; no file may raise or lower one by comment."""
    assert _messages(f"# pyright: {directive}\nx = 1\n") == [
        (1, f"file-level `# pyright: {directive}` directive (pyproject.toml owns rule levels)"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        "x = f()  # pyright: ignore[reportArgumentType]\n",
        "x = f()  # pyright: ignore\n",
        's = "# pyright: basic"\n',
        '"""Quote ``# pyright: ignore[reportUnusedVariable]`` in prose."""\n',
        "# basedpyright: the reason line above a suppression\n",
    ],
)
def test_what_the_comment_check_leaves_alone(source: str) -> None:
    """An unlocked rule's ignore, a bare ignore, and quoted comment text are not violations."""
    assert _messages(source) == []


def test_ignored_rules_names_each_rule_once_per_comment() -> None:
    """A comment naming two rules counts once for each; a bare ignore and a string count none."""
    source = (
        "a = f()  # pyright: ignore[reportArgumentType, reportCallIssue]\n"
        "b = f()  # noqa: F841  # pyright: ignore[reportArgumentType]\n"
        "c = f()  # pyright: ignore\n"
        's = "# pyright: ignore[reportCallIssue]"\n'
    )

    assert list(cts.ignored_rules(source)) == [
        (1, "reportArgumentType"),
        (1, "reportCallIssue"),
        (2, "reportArgumentType"),
    ]


def test_cast_lines_finds_typing_cast_under_every_alias() -> None:
    """``typing.cast`` counts however it is imported; a same-named function of another module does not."""
    source = (
        "import typing\n"
        "import typing_extensions as te\n"
        "from typing import cast\n"
        "from typing_extensions import cast as widen\n"
        "from mylib import cast as other\n"
        "a = cast(int, x)\n"
        "b = typing.cast(int, x)\n"
        "c = te.cast(int, x)\n"
        "d = widen(int, x)\n"
        "e = other(int, x)\n"
        "f = mylib.cast(int, x)\n"
    )

    assert sorted(cts.cast_lines(source)) == [
        6,
        7,
        8,
        9,
    ]


def test_suppressions_key_each_one_to_its_innermost_symbol(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A site is the citation key of the innermost symbol: method, nested function, attribute, module."""
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)
    source = (
        "from typing import cast\n"
        "\n"
        "TOP = cast(int, 1)\n"
        "cast(int, 2)\n"
        "\n"
        "\n"
        "class Box:\n"
        "    size = f()  # pyright: ignore[reportAny]\n"
        "\n"
        "    @decorate  # pyright: ignore[reportUntypedFunctionDecorator]\n"
        "    def open(self) -> int:\n"
        "        def inner() -> int:\n"
        "            return cast(int, 3)\n"
        "\n"
        "        return cast(int, inner())  # pyright: ignore[reportCallIssue]\n"
    )
    _ = (tmp_path / "pkg").mkdir()
    _ = (tmp_path / "pkg" / "mod.py").write_text(source)

    assert list(cts.suppressions("pkg/mod.py", source)) == [
        (3, ("pkg/mod.py::TOP", "cast")),
        (4, ("pkg/mod.py", "cast")),
        (8, ("pkg/mod.py::Box.size", "reportAny")),
        (10, ("pkg/mod.py::Box.open", "reportUntypedFunctionDecorator")),
        (13, ("pkg/mod.py::Box.open.inner", "cast")),
        (15, ("pkg/mod.py::Box.open", "cast")),
        (15, ("pkg/mod.py::Box.open", "reportCallIssue")),
    ]


_SITE_A = ("a.py::f", "cast")
_SITE_B = ("b.py::g", "cast")


@pytest.mark.parametrize(
    ("measured", "ledger", "expected"),
    [
        ([("a.py", 3, _SITE_A)], {_SITE_A: 1}, []),
        (
            [("a.py", 3, _SITE_A), ("a.py", 4, _SITE_A)],
            {_SITE_A: 1},
            [("a.py", 3, f"`cast` at `a.py::f`: 2, ledger 1: {_FIX}")],
        ),
        (
            [("a.py", 3, _SITE_A)],
            {_SITE_A: 2},
            [(cts.LEDGER, 1, f"`cast` at `a.py::f`: 1, ledger 2: {_WRITE}")],
        ),
        (
            [("b.py", 7, _SITE_B)],
            {_SITE_A: 1},
            [
                (cts.LEDGER, 1, f"`cast` at `a.py::f`: 0, ledger 1: {_WRITE}"),
                ("b.py", 7, f"`cast` at `b.py::g`: 1, ledger 0: {_FIX}"),
            ],
        ),
    ],
    ids=[
        "even",
        "over",
        "under",
        "moved",
    ],
)
def test_ledger_violations_hold_every_site_to_its_entry(
    measured: list[tuple[str, int, cts.Entry]],
    ledger: dict[cts.Entry, int],
    expected: list[tuple[str, int, str]],
) -> None:
    """Over and under both fail per site, so a suppression cannot move by giving one up elsewhere."""
    violations = cts.ledger_violations(measured, Counter(ledger))

    assert [(v.path, v.line, v.message) for v in violations] == expected


def test_render_ledger_round_trips_through_load_ledger(tmp_path: Path) -> None:
    """The generated ledger sorts its sites and reads back as the counts it was written from."""
    counts: Counter[cts.Entry] = Counter(
        {
            ("z.py", "cast"): 1,
            ("a.py::f", "reportAny"): 2,
            ("a.py::f", "cast"): 1,
            ("m.py::g", "reportCallIssue"): 0,
        },
    )
    text = cts.render_ledger(counts)
    ledger = tmp_path / "ledger.toml"
    _ = ledger.write_text(text)

    assert text.splitlines()[-2:] == [
        '"a.py::f" = { cast = 1, reportAny = 2 }',
        '"z.py" = { cast = 1 }',
    ]
    assert cts.load_ledger(ledger, _LOCKED) == +counts


def test_load_ledger_reads_an_absent_file_as_empty(tmp_path: Path) -> None:
    """No ledger yet is an empty one: every suppression is new until ``--write --allow-new``."""
    assert cts.load_ledger(tmp_path / "missing.toml", _LOCKED) == Counter()


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('"a.py" = 1\n', "`a.py` must be a table of counts"),
        ('"a.py" = { cast = 0 }\n', "`a.py` `cast` must be a positive integer"),
        ('"a.py" = { cast = true }\n', "`a.py` `cast` must be a positive integer"),
        ('"a.py" = { reportRedeclaration = 1 }\n', "lists `reportRedeclaration`, which is locked"),
    ],
    ids=[
        "not-a-table",
        "zero",
        "boolean",
        "locked",
    ],
)
def test_load_ledger_refuses_an_invalid_entry(tmp_path: Path, text: str, message: str) -> None:
    """A site that is not a table, a count below one, or a locked rule is refused."""
    ledger = tmp_path / "ledger.toml"
    _ = ledger.write_text(text)

    with pytest.raises(cts.LedgerError, match=re.escape(message)):
        _ = cts.load_ledger(ledger, _LOCKED)


def test_load_locked_reads_only_the_marked_basedpyright_lines(tmp_path: Path) -> None:
    """Only ``# Locked`` lines inside ``[tool.basedpyright]`` lock a rule; none locked is refused."""
    pyproject = tmp_path / "pyproject.toml"
    _ = pyproject.write_text(_PYPROJECT)

    assert cts.load_locked(pyproject) == frozenset({"reportRedeclaration"})

    _ = pyproject.write_text(
        _PYPROJECT.replace('"error"  # Locked\nreportAny', '"error"\nreportAny'),
    )
    with pytest.raises(cts.LedgerError, match="marks no rule"):
        _ = cts.load_locked(pyproject)


def _tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, files: dict[str, str]) -> Path:
    """Lay out a checkout of ``files`` with the fixture pyproject; return the ledger path."""
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cts, "tracked_python_files", lambda: sorted(files))
    _ = (tmp_path / "pyproject.toml").write_text(_PYPROJECT)
    _ = (tmp_path / "scripts").mkdir()
    for path, source in files.items():
        _ = (tmp_path / path).write_text(source)
    return tmp_path / cts.LEDGER


_CASTING = "from typing import cast\n\n\ndef f() -> int:\n    return cast(int, 1)\n"


def test_main_exits_one_and_lists_each_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A violating tree fails the run with each ``path:line`` and the summary line."""
    ledger = _tree(
        tmp_path,
        monkeypatch,
        {"bad.py": "x = 1  # pyright: ignore[reportRedeclaration]\n", "good.py": _CASTING},
    )
    _ = ledger.write_text('"good.py::f" = { cast = 2 }\n')

    assert cts.main([]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "bad.py:1: `reportRedeclaration` is locked: fix the diagnostic, never suppress it",
        f"{cts.LEDGER}:1: `cast` at `good.py::f`: 1, ledger 2: {_WRITE}",
        "type-suppressions: checked 2 file(s); ignore comments 0, casts 1; violations 2",
    ]


def test_write_lowers_the_ledger_but_refuses_growth_without_allow_new(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--write`` drops a cleared entry; a new one fails and leaves the ledger as it was."""
    ledger = _tree(tmp_path, monkeypatch, {"good.py": _CASTING})
    _ = ledger.write_text('"good.py::f" = { cast = 2 }\n"gone.py" = { cast = 1 }\n')

    assert cts.main(["--write"]) == 0
    assert cts.load_ledger(ledger, _LOCKED) == Counter({("good.py::f", "cast"): 1})

    _ = (tmp_path / "more.py").write_text("from typing import cast\n\nTOP = cast(int, 2)\n")
    monkeypatch.setattr(cts, "tracked_python_files", lambda: ["good.py", "more.py"])
    before = ledger.read_text()
    assert cts.main(["--write"]) == 1
    assert ledger.read_text() == before

    assert cts.main(["--write", "--allow-new"]) == 0
    assert cts.load_ledger(ledger, _LOCKED) == Counter(
        {("good.py::f", "cast"): 1, ("more.py::TOP", "cast"): 1},
    )
    assert cts.main([]) == 0


@pytest.mark.parametrize(
    ("files", "ledger"),
    [({"missing.py": None}, ""), ({}, '"a.py" = { cast = 0 }\n')],
    ids=["missing-file", "invalid-ledger"],
)
def test_main_exits_two_when_it_cannot_measure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, None],
    ledger: str,
) -> None:
    """A missing file or an invalid ledger is a measurement failure, not a pass."""
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cts, "tracked_python_files", lambda: list(files))
    _ = (tmp_path / "pyproject.toml").write_text(_PYPROJECT)
    _ = (tmp_path / "scripts").mkdir()
    _ = (tmp_path / cts.LEDGER).write_text(ledger)

    assert cts.main([]) == 2


def test_the_tracked_tree_matches_its_ledger() -> None:
    """Every git-tracked ``.py`` file passes and every site matches the ledger, as CI requires."""
    assert cts.main([]) == 0
