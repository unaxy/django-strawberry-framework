"""Script tests for the ``check-noqa-suppressions`` gate in ``scripts/check_noqa_suppressions.py``.

Pins what the gate refuses (a file-level ``ruff: noqa`` or ``flake8: noqa`` in any form, a
blanket ``# noqa``, a site's count of a code or of reasonless ``# noqa`` lines off its ledger
entry either way), what it counts (each code a ``# noqa`` names, after another comment too,
each code a ``# ruff: disable[...]`` fence opens, and ``bare`` for a ``# noqa`` with no reason),
what it leaves alone (comment text quoted in a string or docstring, prose that mentions noqa
mid-comment, a fence's ``enable``), how ``--write`` and ``--allow-new`` treat the ledger, the
``--since`` walk over the noqa ledger, the exit codes, and that the tree itself passes. The
script inspects source files, not a GraphQL request, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

from collections import Counter
from pathlib import Path

import pytest

from scripts import _git
from scripts import check_noqa_suppressions as cns
from scripts import check_type_suppressions as cts


def _refused(source: str) -> list[tuple[int, str]]:
    violations, _ = cns.scan("probe.py", source)
    return [(v.line, v.message) for v in violations]


def _found(source: str) -> list[tuple[int, str]]:
    _, found = cns.scan("probe.py", source)
    return found


@pytest.mark.parametrize(
    "comment",
    [
        "# ruff: noqa",
        "# ruff: noqa: E501",
        "# flake8: noqa",
        "# Ruff: NOQA",
    ],
)
def test_a_file_level_exemption_is_refused(comment: str) -> None:
    """pyproject.toml owns which rules a whole file skips; no comment may widen it."""
    assert _refused(f"{comment}\nx = 1\n") == [
        (1, f"file-level `{comment}` (pyproject.toml owns which rules a file skips)"),
    ]


@pytest.mark.parametrize("comment", ["# noqa", "# NOQA - no codes named"])
def test_a_blanket_noqa_is_refused(comment: str) -> None:
    """A ``# noqa`` that names no code suppresses everything on its line."""
    assert _refused(f"x = 1  {comment}\n") == [
        (1, "blanket `# noqa`: name the codes it suppresses"),
    ]


def test_each_named_code_counts_once_per_line() -> None:
    """Two codes on one line count once each; a second comment part is read on its own."""
    source = (
        "a = f()  # noqa: A002, FBT001 - the GraphQL argument is named id\n"
        "b = f()  # pyright: ignore[reportAny]  # noqa: ANN401 - a consumer hook\n"
        "c = f()  # noqa:E501 the citation cannot wrap\n"
    )

    assert _found(source) == [
        (1, "A002"),
        (1, "FBT001"),
        (2, "ANN401"),
        (3, "E501"),
    ]


@pytest.mark.parametrize(
    "comment",
    [
        "# noqa: A002",
        "# noqa: A002 - ",
        "# noqa: A002  # pyright: ignore[reportAny]",
        "# noqa: A002, FBT001",
    ],
)
def test_a_noqa_with_no_reason_also_counts_bare(comment: str) -> None:
    """Nothing but separators after the codes is no reason; ``bare`` counts once per line."""
    found = _found(f"x = 1  {comment}\n")

    assert found.count((1, cns.BARE)) == 1


def test_a_fence_counts_each_code_it_opens() -> None:
    """``# ruff: disable[...]`` counts each code; ``# ruff: enable[...]`` counts nothing."""
    source = "# ruff: disable[ERA001, E501]\n# x = 1\n# ruff: enable[ERA001, E501]\n"

    assert _found(source) == [(1, "ERA001"), (1, "E501")]


@pytest.mark.parametrize(
    "source",
    [
        's = "x = 1  # noqa: E501"\n',
        '"""Quote ``# noqa: A002`` in prose, or ``# ruff: noqa``."""\n',
        "# the noqa on the next line is load-bearing\n",
        "x = 1  # pyright: ignore[reportAny]\n",
    ],
)
def test_what_the_scan_leaves_alone(source: str) -> None:
    """Quoted comment text and prose that mentions noqa are neither refused nor counted."""
    assert cns.scan("probe.py", source) == ([], [])


def test_suppressions_key_each_one_to_its_innermost_symbol(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A site is the citation key of the innermost symbol: an import's binding, a method."""
    monkeypatch.setattr(cns, "REPO_ROOT", tmp_path)
    source = (
        "import os  # noqa: F401 - re-exported\n"
        "\n"
        "\n"
        "class C:\n"
        "    def m(self, id: int) -> None:  # noqa: A002 - the argument is named id\n"
        "        pass\n"
    )
    _ = (tmp_path / "mod.py").write_text(source)
    _, found = cns.scan("mod.py", source)

    assert list(cns.suppressions("mod.py", found)) == [
        (1, ("mod.py::os", "F401")),
        (5, ("mod.py::C.m", "A002")),
    ]


def _tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, files: dict[str, str]) -> Path:
    """Lay out a checkout of ``files``; return the ledger path."""
    monkeypatch.setattr(cns, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cts, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cts, "tracked_python_files", lambda: sorted(files))
    _ = (tmp_path / "scripts").mkdir(exist_ok=True)
    for path, source in files.items():
        _ = (tmp_path / path).write_text(source)
    return tmp_path / cns.LEDGER


_REASONED = "def f(id: int) -> None:  # noqa: A002 - the argument is named id\n    pass\n"
_BARE = "def g(id: int) -> None:  # noqa: A002\n    pass\n"


def test_main_exits_one_and_lists_each_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A new bare ``# noqa`` asks for its reason, a new code for a fix, a cleared one for --write."""
    ledger = _tree(tmp_path, monkeypatch, {"bare.py": _BARE, "good.py": _REASONED})
    _ = ledger.write_text('"good.py::f" = { A002 = 2 }\n')

    assert cns.main([]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "bare.py:1: `A002` at `bare.py::g`: 1, ledger 0: fix the new diagnostic instead of suppressing it",
        "bare.py:1: `bare` at `bare.py::g`: 1, ledger 0: give the `# noqa` its reason after the codes",
        f"{cns.LEDGER}:1: `A002` at `good.py::f`: 1, ledger 2: run `{cns.SCRIPT} --write`",
        "noqa-suppressions: checked 2 file(s); suppressed codes 2, bare 1; violations 3",
    ]


def test_write_lowers_the_ledger_but_refuses_growth_without_allow_new(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--write`` drops a cleared entry; a new one fails and leaves the ledger as it was."""
    ledger = _tree(tmp_path, monkeypatch, {"good.py": _REASONED})
    _ = ledger.write_text('"good.py::f" = { A002 = 2 }\n"gone.py" = { E501 = 1 }\n')

    assert cns.main(["--write"]) == 0
    assert cts.load_ledger(ledger, frozenset()) == Counter({("good.py::f", "A002"): 1})
    assert ledger.read_text().startswith("# Generated by scripts/check_noqa_suppressions.py")

    _ = _tree(tmp_path, monkeypatch, {"good.py": _REASONED, "bare.py": _BARE})
    before = ledger.read_text()
    assert cns.main(["--write"]) == 1
    assert ledger.read_text() == before

    assert cns.main(["--write", "--allow-new"]) == 0
    assert cts.load_ledger(ledger, frozenset()) == Counter(
        {("good.py::f", "A002"): 1, ("bare.py::g", "A002"): 1, ("bare.py::g", cns.BARE): 1},
    )
    assert cns.main([]) == 0


@pytest.mark.parametrize(
    ("files", "ledger"),
    [({"missing.py": None}, ""), ({}, '"a.py" = { A002 = 0 }\n')],
    ids=["missing-file", "invalid-ledger"],
)
def test_main_exits_two_when_it_cannot_measure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, None],
    ledger: str,
) -> None:
    """A missing file or an invalid ledger is a measurement failure, not a pass."""
    monkeypatch.setattr(cns, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(cts, "tracked_python_files", lambda: list(files))
    _ = (tmp_path / "scripts").mkdir()
    _ = (tmp_path / cns.LEDGER).write_text(ledger)

    assert cns.main([]) == 2


def _commit(root: Path, ledger: str, message: str) -> str:
    """Commit ``ledger`` as the noqa ledger of ``root``'s repository; return the new commit."""
    _ = (root / cns.LEDGER).write_text(ledger)
    _ = _git.run_git(root, "add", cns.LEDGER, check=True)
    _ = _git.run_git(
        root,
        "-c",
        "user.name=probe",
        "-c",
        "user.email=probe@example.com",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        message,
        check=True,
    )
    return _git.run_git(root, "rev-parse", "HEAD", check=True).stdout.strip()


def test_main_since_walks_the_noqa_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A commit raising a noqa total needs the consent trailer; the type ledger is not read."""
    _ = _tree(tmp_path, monkeypatch, {"good.py": _REASONED})
    _ = _git.run_git(tmp_path, "init", "-q", check=True)
    base = _commit(tmp_path, "", "base")
    grown = _commit(tmp_path, '"good.py::f" = { A002 = 1 }\n', "grow")

    assert cns.main(["--since", base]) == 1
    assert capsys.readouterr().out.splitlines()[0] == (
        f"{cns.LEDGER}:1: {grown[:12]} raises `A002` from 0 to 1 without a "
        f"`{cts.TRAILER}:` trailer (the maintainer's consent)"
    )

    _ = _commit(tmp_path, '"good.py::f" = { A002 = 1 }\n', "still")
    assert cns.main(["--since", grown]) == 0


def test_the_tracked_tree_matches_its_ledger() -> None:
    """Every git-tracked ``.py`` file passes and every site matches the ledger, as CI requires."""
    assert cns.main([]) == 0
