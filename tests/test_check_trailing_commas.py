"""Script tests for the ``source-layout`` gate in ``scripts/check_trailing_commas.py``.

Pins the anchored exclusion set (per-cycle docs/ artifacts and scratch subtrees
stay out; the standing docs beside them, tracked ``.py`` under ``docs/`` and a
same-named directory outside ``docs/`` are checked), the always-printed summary
line, the failure on a named path that contributes nothing, the ``--json``
document shape, the no-write guarantee of ``--diff``, and one positive plus one
negative control for the comma-layout and markdown-scaffold rules. Every case
runs against a throwaway tree under ``tmp_path`` with ``REPO_ROOT`` pointed at
it. The script inspects source files, not a GraphQL request, so there is no live
sibling in ``examples/fakeshop/test_query/``.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts import check_trailing_commas as ctc
from tests._idioms import json_at, json_list, json_loads, json_object

SCAFFOLD = "\n".join([ctc.LINK_DEF_HEADER, "", *ctc.LINK_DEF_CATEGORIES]) + "\n"
CLEAN_MD = "# Title\n\nBody.\n\n" + SCAFFOLD
CLEAN_PY = "VALUE = [1, 2]\n"


def _document(capsys: pytest.CaptureFixture[str]) -> dict[object, object]:
    """The one ``--json`` document the last ``main`` call printed."""
    return json_object(json_loads(capsys.readouterr().out))


def _records(document: dict[object, object], key: str) -> list[dict[object, object]]:
    """The per-violation records under ``document[key]``, each checked to be a JSON object."""
    return [json_object(record) for record in json_list(document, key)]


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A throwaway repo root with its own pyproject, git filter disabled, cwd inside it."""
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 99\n", encoding="utf-8")
    monkeypatch.setattr(ctc, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ctc, "git_visible_scope", lambda: None)
    monkeypatch.chdir(tmp_path)
    ctc.line_length.cache_clear()
    ctc.ruff_excluded_names.cache_clear()
    yield tmp_path
    ctc.line_length.cache_clear()
    ctc.ruff_excluded_names.cache_clear()


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _summary(stdout: str) -> str:
    return stdout.strip().splitlines()[-1]


EXCLUDED = (
    "docs/review/rev-optimizer__walker.mechanics.md",
    "docs/review/review-0_0_15.md",
    "docs/dry/dry-0_0_15.md",
    "docs/dry/dry-file-walker.md",
    "docs/builder/bld-final.md",
    "docs/builder/build-050-thing-0_0_15.md",
    "docs/bug_hunt/bug_hunt-0_0_15.md",
    "docs/review/temp-tests/test_probe.py",
    "docs/builder/temp-tests/nested/test_probe.py",
    "docs/dry/worker-memory/worker-1.md",
    "docs/shadow/current/walker.py",
    "docs/shadow/diff/walker.md",
    "docs/feedback.md",
)
CHECKED = (
    "docs/review/REVIEW.md",
    "docs/review/worker-0.md",
    "docs/dry/DRY.md",
    "docs/dry/export_dry_review.py",
    "docs/bug_hunt/HUNT.md",
    "docs/bug_hunt/dicta.md",
    "docs/builder/BUILD.md",
    "docs/builder/worker-3.md",
    "docs/README.md",
    # A per-cycle NAME outside its anchored subtree is ordinary source.
    "tests/review/rev-notes.md",
    "django_strawberry_framework/builder/review-helpers.py",
    "examples/fakeshop/apps/dry/dry-run.py",
    # ``*`` never crosses ``/``: a directory named like an artifact is not one.
    "docs/review/rev-cycle/notes.md",
)


@pytest.mark.parametrize("relative", EXCLUDED)
def test_per_cycle_artifact_is_excluded(repo: Path, relative: str) -> None:
    """Per-cycle artifacts and scratch subtrees under docs/ are excluded by anchored path."""
    assert ctc.is_excluded(_write(repo, relative, "x\n"))


@pytest.mark.parametrize("relative", CHECKED)
def test_standing_doc_and_same_named_source_are_checked(repo: Path, relative: str) -> None:
    """Standing docs, tracked docs/ .py and same-named dirs elsewhere stay in the gate."""
    assert not ctc.is_excluded(_write(repo, relative, "x\n"))


def test_walk_partitions_checked_and_excluded(repo: Path) -> None:
    """A tree walk processes exactly CHECKED and counts exactly EXCLUDED."""
    for relative in (*EXCLUDED, *CHECKED):
        _write(repo, relative, "x\n")
    selection = ctc.select_files(["."], ctc.SUFFIXES)
    assert {path.as_posix() for path in selection.files} == set(CHECKED)
    assert {path.as_posix() for path in selection.excluded} == set(EXCLUDED)
    assert selection.skipped == []
    assert selection.unmatched == []


def test_named_excluded_file_is_reported_not_checked(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A per-cycle artifact handed in by name prints the excluded line and is counted."""
    _write(repo, "docs/review/review-0_0_15.md", "no footer\n")
    assert ctc.main(["--check", "docs/review/review-0_0_15.md"]) == 0
    captured = capsys.readouterr()
    assert "docs/review/review-0_0_15.md: excluded from the source-layout rules" in captured.err
    assert _summary(captured.out).startswith("source-layout: checked 0 file(s); excluded 1;")


# Paths under a ``[tool.ruff] extend-exclude`` name, at the root and nested: ruff's
# ``force-exclude`` skips each one even when it is named, so ``--fix`` must skip it too.
RUFF_EXCLUDED = (
    ("hunt-ws/copy/pkg/wide.py", "def f(a, b, c, d):\n    return a\n"),
    ("hunt-ws/copy/docs/guide.md", "no footer\n"),
    ("pkg/hunt-ws/wide.py", "def f(a, b, c, d):\n    return a\n"),
)


@pytest.fixture
def ruff_excluding_repo(repo: Path) -> Path:
    """``repo`` whose pyproject excludes ``hunt-ws`` from ruff, as the real one does."""
    (repo / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 99\nextend-exclude = ["hunt-ws"]\nforce-exclude = true\n',
        encoding="utf-8",
    )
    ctc.ruff_excluded_names.cache_clear()
    return repo


@pytest.mark.parametrize(("relative", "text"), RUFF_EXCLUDED, ids=[r for r, _ in RUFF_EXCLUDED])
def test_named_ruff_excluded_file_is_left_untouched_by_fix(
    ruff_excluding_repo: Path,
    capsys: pytest.CaptureFixture[str],
    relative: str,
    text: str,
) -> None:
    """A file ruff's config excludes is reported excluded by name and never edited by --fix."""
    path = _write(ruff_excluding_repo, relative, text)
    assert ctc.main(["--fix", relative]) == 0
    assert path.read_text(encoding="utf-8") == text
    captured = capsys.readouterr()
    assert f"{relative}: excluded from the source-layout rules" in captured.err
    assert _summary(captured.out).startswith("source-layout: checked 0 file(s); excluded 1;")


def test_walk_prunes_ruff_excluded_trees(ruff_excluding_repo: Path) -> None:
    """A tree walk never descends into a directory ruff's config excludes."""
    for relative, text in RUFF_EXCLUDED:
        _write(ruff_excluding_repo, relative, text)
    _write(ruff_excluding_repo, "pkg/clean.py", CLEAN_PY)
    selection = ctc.select_files(["."], ctc.SUFFIXES)
    assert [path.as_posix() for path in selection.files] == ["pkg/clean.py"]
    # Pruned, not walked and then dropped: a walked-and-excluded file would be counted here.
    assert selection.excluded == []


def test_checkout_inside_a_ruff_excluded_name_still_checks_its_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Segments are matched on the repo-relative path: a checkout under ``hunt-ws/`` is checked."""
    root = tmp_path / "hunt-ws" / "copy"
    _write(root, "pyproject.toml", '[tool.ruff]\nline-length = 99\nextend-exclude = ["hunt-ws"]\n')
    _write(root, "pkg/clean.py", CLEAN_PY)
    monkeypatch.setattr(ctc, "REPO_ROOT", root)
    monkeypatch.setattr(ctc, "git_visible_scope", lambda: None)
    monkeypatch.chdir(root)
    ctc.ruff_excluded_names.cache_clear()
    try:
        selection = ctc.select_files(["."], ctc.SUFFIXES)
    finally:
        ctc.ruff_excluded_names.cache_clear()
    assert [path.as_posix() for path in selection.files] == ["pkg/clean.py"]


def test_fix_reflows_a_named_file_under_a_ruff_default_exclude(ruff_excluding_repo: Path) -> None:
    """A file only ruff's built-in excludes skip (``_build``) is still reflowed after ``--fix``."""
    path = _write(ruff_excluding_repo, "_build/wide.py", "def f(a, b, c, d):\n    return a\n")
    assert ctc.main(["--fix", "_build/wide.py"]) == 0
    assert path.read_text(encoding="utf-8") == (
        "def f(\n    a,\n    b,\n    c,\n    d,\n):\n    return a\n"
    )


def test_diff_shows_the_reflow_of_a_named_file_under_a_ruff_default_exclude(
    ruff_excluding_repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--diff`` on a file only ruff's built-in excludes skip (``_build``) shows the reflow."""
    text = "def f(a, b, c, d):\n    return a\n"
    path = _write(ruff_excluding_repo, "_build/wide.py", text)
    assert ctc.main(["--diff", "_build/wide.py"]) == 1
    out = capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == text
    assert "+def f(\n+    a,\n+    b,\n+    c,\n+    d,\n+):\n" in out


def test_anchored_ruff_exclude_entry_is_refused(repo: Path) -> None:
    """An anchored ``extend-exclude`` entry fails loudly instead of matching nothing."""
    (repo / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 99\nextend-exclude = ["docs/hunt-ws"]\n',
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="is anchored"):
        ctc.ruff_excluded_names()


def test_summary_counts_checked_excluded_and_violations(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The summary line is printed on every run and counts each population."""
    _write(repo, "pkg/clean.py", CLEAN_PY)
    _write(repo, "pkg/wide.py", "def f(a, b, c, d):\n    return a\n")
    _write(repo, "docs/guide.md", CLEAN_MD)
    _write(repo, "docs/review/rev-scratch.md", "no footer\n")
    assert ctc.main(["--check", "."]) == 1
    assert _summary(capsys.readouterr().out) == (
        "source-layout: checked 3 file(s); excluded 1; ignored 0; "
        "violations 1 (layout 1, non-ASCII 0); errors 0"
    )


def test_clean_run_still_prints_summary(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Negative control: a clean run exits 0 and still states its population."""
    _write(repo, "pkg/clean.py", CLEAN_PY)
    assert ctc.main(["--check", "pkg/clean.py"]) == 0
    assert _summary(capsys.readouterr().out) == (
        "source-layout: checked 1 file(s); excluded 0; ignored 0; "
        "violations 0 (layout 0, non-ASCII 0); errors 0"
    )


@pytest.mark.parametrize(
    ("setup", "argument", "reason"),
    [
        (None, "missing.md", "matches nothing"),
        (None, "missing_dir", "matches nothing"),
        ("empty_dir/.keep", "empty_dir", "directory yielded no checkable file (0 excluded)"),
        ("docs/shadow/a.py", "docs/shadow", "directory yielded no checkable file (1 excluded)"),
    ],
)
def test_path_contributing_nothing_fails(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    setup: str | None,
    argument: str,
    reason: str,
) -> None:
    """A named path that yields no file is an error under --check, not a silent pass."""
    if setup is not None:
        _write(repo, setup, "x\n")
    assert ctc.main(["--check", argument]) == 1
    captured = capsys.readouterr()
    assert f"{argument}: {reason} -- NOT checked" in captured.err
    assert _summary(captured.out).endswith("errors 1")


@pytest.mark.usefixtures("repo")
def test_unsupported_suffix_is_ignored_not_failed(capsys: pytest.CaptureFixture[str]) -> None:
    """An existing file no rule covers is reported as ignored and does not fail the run."""
    assert ctc.main(["--check", "pyproject.toml"]) == 0
    captured = capsys.readouterr()
    assert "pyproject.toml: no source-layout rule covers this suffix -- ignored" in captured.err
    assert "ignored 1;" in _summary(captured.out)


def test_json_document_shape(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--json prints one document: summary, path lists and uniform per-violation records."""
    _write(repo, "pkg/wide.py", f"def f(a, b, c, d):\n    return 'caf{chr(0xE9)}'\n")
    _write(repo, "docs/guide.md", "# Guide\n")
    _write(repo, "docs/dry/dry-0_0_15.md", "no footer\n")
    argv = [
        "--check",
        "--json",
        "pkg",
        "docs",
        "missing.md",
    ]
    assert ctc.main(argv) == 1
    document = _document(capsys)
    assert set(document) == {
        "mode",
        "paths",
        "summary",
        "checked",
        "excluded",
        "ignored",
        "violations",
        "errors",
    }
    assert document["mode"] == "check"
    assert document["paths"] == argv[2:]
    assert document["summary"] == {
        "checked": 2,
        "excluded": 1,
        "ignored": 0,
        "violations": 3,
        "errors": 1,
        "fixed": 0,
        "exit": 1,
    }
    assert document["excluded"] == ["docs/dry/dry-0_0_15.md"]
    keys = {
        "file",
        "line",
        "rule",
        "message",
        "fixable",
    }
    assert all(
        set(record) == keys
        for record in _records(document, "violations") + _records(document, "errors")
    )
    by_rule = {
        (v["file"], v["rule"]): (v["line"], v["fixable"]) for v in _records(document, "violations")
    }
    assert by_rule == {
        ("docs/guide.md", "md-scaffold"): (2, True),
        ("pkg/wide.py", "explode"): (1, True),
        ("pkg/wide.py", "non-ascii"): (2, False),
    }
    assert [(e["file"], e["rule"]) for e in _records(document, "errors")] == [
        ("missing.md", "unmatched-path"),
    ]


def test_diff_prints_fix_without_writing(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--diff shows the rewrite --fix would make and leaves the file byte-identical."""
    path = _write(repo, "docs/guide.md", "# Guide\n")
    before = path.read_bytes()
    assert ctc.main(["--diff", "docs/guide.md"]) == 1
    out = capsys.readouterr().out
    assert path.read_bytes() == before
    assert "--- a/docs/guide.md" in out
    assert f"+{ctc.LINK_DEF_HEADER}" in out
    assert f"+{ctc.LINK_DEF_CATEGORIES[-1]}" in out


@pytest.mark.usefixtures("repo")
def test_diff_rejects_fix() -> None:
    """--diff writes nothing, so pairing it with --fix is a usage error."""
    with pytest.raises(SystemExit):
        ctc.main(["--fix", "--diff", "."])


def test_fix_writes_what_diff_showed(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Positive control for --diff: --fix on the same file does write the scaffold."""
    path = _write(repo, "docs/guide.md", "# Guide\n")
    assert ctc.main(["--diff", "docs/guide.md"]) == 1
    proposal = capsys.readouterr().out
    assert path.read_bytes() == b"# Guide\n"
    assert ctc.main(["--fix", "docs/guide.md"]) == 0
    written = path.read_text(encoding="utf-8")
    added = [
        line[1:]
        for line in proposal.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    assert written == "# Guide\n" + "\n".join(added) + "\n"
    assert ctc._scaffold_in_canonical_order(written) is None
    assert "Fixed 1 file(s)." in capsys.readouterr().out


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("def f(a, b, c, d):\n    return a\n", [(1, "explode")]),
        ("def f(a, b, c):\n    return a\n", []),
    ],
)
@pytest.mark.usefixtures("repo")
def test_comma_layout_threshold(source: str, expected: list[tuple[int, str]]) -> None:
    """A single-line four-parameter def must explode; three parameters stay inline."""
    assert ctc._analyze(source, ctc.threshold_for(Path("pkg/mod.py")))[2] == expected


@pytest.mark.parametrize(
    ("text", "missing"),
    [
        ("# Guide\n", ctc.LINK_DEF_HEADER),
        ("# Guide\n\n" + SCAFFOLD.replace("<!-- tests/ -->\n", ""), "<!-- tests/ -->"),
        (CLEAN_MD, None),
    ],
)
@pytest.mark.usefixtures("repo")
def test_markdown_scaffold(text: str, missing: str | None) -> None:
    """The first missing scaffold marker is reported; the canonical footer passes."""
    assert ctc._scaffold_in_canonical_order(text) == missing


STRAWBERRY = "\U0001f353"
ATOM_EMOJI = "\u269b\ufe0f"  # the kanban parity marker: U+269B ATOM + U+FE0F


def _two_item_list(payload: str, code_points: int) -> str:
    """An exploded two-string list whose collapsed line is ``code_points`` code points long.

    Collapsed it reads ``X = ["<payload>", "<pad>"]``: 12 code points plus both strings.
    """
    pad = "p" * (code_points - 12 - len(payload))
    return f'X = [\n    "{payload}",\n    "{pad}",\n]\n'


@pytest.mark.parametrize(
    ("payload", "code_points", "expected"),
    [
        # 99 code points, 100 columns: the formatter would re-explode it.
        (STRAWBERRY, 99, []),
        # Control: the same length in ASCII fits the 99-column line length.
        ("s", 99, [(1, "collapse")]),
        # 100 code points, 99 columns: ATOM is one column, the selector zero.
        (ATOM_EMOJI, 100, [(1, "collapse")]),
    ],
)
@pytest.mark.usefixtures("repo")
def test_collapse_fit_counts_display_columns(
    payload: str,
    code_points: int,
    expected: list[tuple[int, str]],
) -> None:
    """The collapse fit counts formatter columns, not code points, at the line-length edge."""
    source = _two_item_list(payload, code_points)
    assert ctc._analyze(source, ctc.threshold_for(Path("pkg/mod.py")))[2] == expected


def test_display_width_matches_ruff_format(repo: Path) -> None:
    """Every non-ASCII character the ASCII rule allows has the width ``ruff format`` gives it.

    Two probe statements per character: collapsed, ``x = f("<char>", <name>)`` is 99
    columns at the table's width (ruff must join it) and 100 with a one-longer name
    (ruff must keep it split). Ruff's join-or-split decision reads its own width back.
    """
    allowed = [
        chr(cp)
        for cp in (*range(0x2600, 0x2700), *range(0x1F000, 0x1FB00), *range(0xFE00, 0xFE10))
        if ctc._is_emoji(cp)
    ]
    names: list[tuple[str, str]] = []
    statements: list[str] = []
    for index, char in enumerate(allowed):
        fits = f"v{index}_".ljust(88 - ctc._display_width(char), "z")
        names.append((fits, f"{fits}y"))
        statements.extend(f'x = f(\n    "{char}", {name}\n)\n' for name in names[-1])
    formatted = ctc._ruff_format_text("".join(statements), repo / "probe.py")
    assert formatted is not None
    joined = {
        line.rsplit(", ", 1)[1].removesuffix(")")
        for line in formatted.splitlines()
        if line.startswith('x = f("')
    }
    mismatched = [
        f"U+{ord(char):04X}"
        for char, (fits, overflows) in zip(allowed, names, strict=True)
        if fits not in joined or overflows in joined
    ]
    assert len(allowed) == 3088
    assert mismatched == []


@pytest.mark.parametrize(
    ("source", "fixed"),
    [
        # A bare tuple of parenthesized items: its brackets are its elements'.
        ("BARE = (1, 2), (3, 4), (5, 6), (7, 8)\n", None),
        ("BARE = (a), (b, c)\n", None),
        # Controls: the tuple's own parentheses, with and without parenthesized items.
        ("P = ((1, 2), (3, 4), (5, 6), (7, 8))\n", "P = ((1, 2), (3, 4), (5, 6), (7, 8),)\n"),
        ("P = ((a), b, c, d)\n", "P = ((a), b, c, d,)\n"),
        # Only the four-item element of a bare tuple explodes, inside its own brackets.
        ("Q = (a), (b, c, d, e)\n", "Q = (a), (b, c, d, e,)\n"),
    ],
)
@pytest.mark.usefixtures("repo")
def test_explode_comma_lands_inside_the_tuples_own_parentheses(
    source: str,
    fixed: str | None,
) -> None:
    """A comma is added before a tuple's closing parenthesis only when the tuple owns it."""
    analysis = ctc._analyze(source, ctc.threshold_for(Path("pkg/mod.py")))
    assert analysis.violations == ([] if fixed is None else [(1, "explode")])
    assert ctc._apply(source, analysis.inserts, analysis.deletes) == (fixed or source)


SUPPRESSIONS = (
    "# noqa: T201",
    "# NOQA",
    "# pyright: ignore[reportUnusedCallResult]",
    "# type: ignore",
)


@pytest.mark.parametrize("comment", SUPPRESSIONS)
def test_explode_refuses_to_strand_a_trailing_suppression(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    comment: str,
) -> None:
    """--fix leaves a line ending in a suppression unexploded and fails with the location."""
    source = f"X = [print(1), print(2), print(3), print(4)]  {comment}\n"
    path = _write(repo, "pkg/mod.py", source)
    assert ctc.main(["--fix", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert path.read_text(encoding="utf-8") == source
    assert [(v["rule"], v["line"], v["fixable"]) for v in _records(document, "violations")] == [
        ("explode", 1, False),
    ]
    assert [(e["file"], e["rule"], e["line"]) for e in _records(document, "errors")] == [
        ("pkg/mod.py", "unfixable", 1),
    ]
    assert json_at(document, "errors", 0, "message") == ctc.STRANDED_MESSAGE
    assert json_at(document, "summary", "fixed") == 0
    # --check reports the same explode as not fixable, and no error.
    assert ctc.main(["--check", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert [(v["rule"], v["fixable"]) for v in _records(document, "violations")] == [
        ("explode", False),
    ]
    assert document["errors"] == []
    # --diff raises the error --fix does.
    assert ctc.main(["--diff", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert [(e["rule"], e["line"], e["message"]) for e in _records(document, "errors")] == [
        ("unfixable", 1, ctc.STRANDED_MESSAGE),
    ]
    assert path.read_text(encoding="utf-8") == source


@pytest.mark.parametrize(
    "tail",
    ["  # a plain comment", ', "# noqa: T201"'],
)
def test_explode_with_a_trailing_non_suppression_is_fixed(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    tail: str,
) -> None:
    """Negative control: a plain comment or a ``# noqa`` inside a string does not block it."""
    path = _write(repo, "pkg/mod.py", f"X = [print(1), print(2), print(3), print(4)]{tail}\n")
    assert ctc.main(["--fix", "--json", "pkg/mod.py"]) == 0
    document = _document(capsys)
    assert document["errors"] == []
    assert json_at(document, "summary", "fixed") == 1
    assert "    print(1),\n" in path.read_text(encoding="utf-8")


NESTED = "X = [\n    [\n        1,\n        2,\n    ],\n    [\n        3,\n        4,\n    ],\n]\n"


def test_fix_reaches_the_fixpoint_in_one_run(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An outer construct that collapses only after its children have is fixed in one --fix."""
    path = _write(repo, "pkg/mod.py", NESTED)
    assert ctc.main(["--fix", "--json", "pkg/mod.py"]) == 0
    document = _document(capsys)
    assert path.read_text(encoding="utf-8") == "X = [[1, 2], [3, 4]]\n"
    # Two inner collapses in round 1, the outer one in round 2.
    assert [(v["rule"], v["line"]) for v in _records(document, "violations")] == [
        ("collapse", 2),
        ("collapse", 6),
        ("collapse", 1),
    ]
    assert document["errors"] == []
    assert ctc.main(["--check", "pkg/mod.py"]) == 0


def test_diff_shows_the_fixpoint(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--diff runs the same rounds in memory, so it shows the text --fix leaves."""
    path = _write(repo, "pkg/mod.py", NESTED)
    assert ctc.main(["--diff", "pkg/mod.py"]) == 1
    assert "+X = [[1, 2], [3, 4]]\n" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == NESTED


@pytest.mark.parametrize("mode", ["--fix", "--diff"])
def test_fix_without_a_fixpoint_is_an_error(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    """A file still changing after the round bound fails the run instead of passing."""
    monkeypatch.setattr(ctc, "MAX_FIX_ROUNDS", 1)
    _write(repo, "pkg/mod.py", NESTED)
    assert ctc.main([mode, "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert [
        (
            e["file"],
            e["rule"],
            e["line"],
            e["message"],
        )
        for e in _records(document, "errors")
    ] == [
        (
            "pkg/mod.py",
            "unfixable",
            1,
            ctc.NO_FIXPOINT_MESSAGE,
        ),
    ]


def _stranded_after_reflow(comment: str) -> tuple[str, str]:
    """A source whose explode is stranded only once ``ruff format`` collapses it, and the text it settles to.

    Line 1 is a multi-line list with the suppression after its closing bracket, so
    round 1 sees no violation there; line 4's collapse makes round 1 write the file,
    the reflow joins the list onto line 1, and round 2 finds the explode withheld.
    """
    source = f"X = [\n    print(1), print(2), print(3), print(4)\n]  {comment}\nY = [1, 2,]\n"
    settled = f"X = [print(1), print(2), print(3), print(4)]  {comment}\nY = [1, 2]\n"
    return source, settled


@pytest.mark.parametrize("comment", SUPPRESSIONS)
def test_fix_fails_on_an_explode_a_later_round_strands(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    comment: str,
) -> None:
    """A suppression stranded by the reflow fails --fix with the round-1 error, and --check agrees."""
    source, settled = _stranded_after_reflow(comment)
    path = _write(repo, "pkg/mod.py", source)
    assert ctc.main(["--fix", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert path.read_text(encoding="utf-8") == settled
    assert [(v["rule"], v["line"], v["fixable"]) for v in _records(document, "violations")] == [
        ("collapse", 4, True),
        ("explode", 1, False),
    ]
    assert [
        (
            e["file"],
            e["rule"],
            e["line"],
            e["message"],
        )
        for e in _records(document, "errors")
    ] == [
        (
            "pkg/mod.py",
            "unfixable",
            1,
            ctc.STRANDED_MESSAGE,
        ),
    ]
    assert json_at(document, "summary", "exit") == 1
    # The settled file is exactly what --check rejects: the same line, not fixable.
    assert ctc.main(["--check", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert [(v["rule"], v["line"], v["fixable"]) for v in _records(document, "violations")] == [
        ("explode", 1, False),
    ]
    assert document["errors"] == []


def test_fix_reports_a_later_round_stranded_explode_in_human_output(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without --json the later-round refusal is the round-1 line on stderr, and the run fails."""
    source, _ = _stranded_after_reflow(SUPPRESSIONS[0])
    _ = _write(repo, "pkg/mod.py", source)
    assert ctc.main(["--fix", "pkg/mod.py"]) == 1
    captured = capsys.readouterr()
    assert f"pkg/mod.py:1: {ctc.STRANDED_MESSAGE}" in captured.err.splitlines()
    assert "1 error(s): file(s) not checked or not fully fixed" in captured.out
    assert "errors 1" in _summary(captured.out)


def test_diff_fails_on_an_explode_a_later_round_strands(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--diff runs the same rounds in memory, so it raises the error --fix would and writes nothing."""
    source, settled = _stranded_after_reflow(SUPPRESSIONS[0])
    path = _write(repo, "pkg/mod.py", source)
    assert ctc.main(["--diff", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert path.read_text(encoding="utf-8") == source
    assert [
        (
            e["file"],
            e["rule"],
            e["line"],
            e["message"],
        )
        for e in _records(document, "errors")
    ] == [
        (
            "pkg/mod.py",
            "unfixable",
            1,
            ctc.STRANDED_MESSAGE,
        ),
    ]
    diff = json_at(document, "diffs", "pkg/mod.py")
    assert isinstance(diff, str)
    assert f"+{settled.splitlines()[0]}\n" in diff


def test_stranded_explode_below_a_reflowed_construct_is_reported_once_at_its_settled_line(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A round-1 stranded line that the reflow moves up is one error, at its line in the settled file.

    Round 1 strands line 5 and collapses the list above it; the reflow joins that list
    onto line 1, so the construct settles on line 2. --diff raises the same errors as
    --fix, and --check on the settled file names the same line.
    """
    stranded = "X = [print(1), print(2), print(3), print(4)]  # noqa: T201\n"
    source = "Y = [\n    1,\n    2,\n]\n" + stranded
    path = _write(repo, "pkg/mod.py", source)
    expected = [
        (
            "pkg/mod.py",
            "unfixable",
            2,
            ctc.STRANDED_MESSAGE,
        ),
    ]
    assert ctc.main(["--diff", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert [
        (
            e["file"],
            e["rule"],
            e["line"],
            e["message"],
        )
        for e in _records(document, "errors")
    ] == expected
    # --diff's violations describe the file as it stands.
    assert [(v["rule"], v["line"], v["fixable"]) for v in _records(document, "violations")] == [
        ("collapse", 1, True),
        ("explode", 5, False),
    ]
    assert path.read_text(encoding="utf-8") == source
    assert ctc.main(["--fix", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert path.read_text(encoding="utf-8") == "Y = [1, 2]\n" + stranded
    assert [
        (
            e["file"],
            e["rule"],
            e["line"],
            e["message"],
        )
        for e in _records(document, "errors")
    ] == expected
    assert [(v["rule"], v["line"], v["fixable"]) for v in _records(document, "violations")] == [
        ("collapse", 1, True),
        ("explode", 2, False),
    ]
    assert ctc.main(["--check", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert [(v["rule"], v["line"], v["fixable"]) for v in _records(document, "violations")] == [
        ("explode", 2, False),
    ]


def test_fix_reports_an_edit_that_would_break_syntax(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A comma edit that would not parse is an error and is not written.

    ``_python_pass`` re-parses every edit as a safety net no real layout reaches, so
    ``_apply`` is made to return unparseable text.
    """

    def unparseable(text: str, _inserts: list[int], _deletes: list[int]) -> str:
        return text + "(\n"

    monkeypatch.setattr(ctc, "_apply", unparseable)
    path = _write(repo, "pkg/mod.py", "Y = [1, 2,]\n")
    assert ctc.main(["--fix", "--json", "pkg/mod.py"]) == 1
    document = _document(capsys)
    assert path.read_text(encoding="utf-8") == "Y = [1, 2,]\n"
    assert [(e["rule"], e["line"]) for e in _records(document, "errors")] == [("unfixable", None)]
    assert str(json_at(document, "errors", 0, "message")).startswith(
        "comma fix would break syntax (",
    )
    assert [(v["rule"], v["fixable"]) for v in _records(document, "violations")] == [
        ("collapse", False),
    ]
