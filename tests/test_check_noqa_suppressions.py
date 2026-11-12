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

import json
import subprocess
from collections import Counter
from collections.abc import Callable
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


@pytest.mark.parametrize(
    "comment",
    [
        "# noqa",
        "# NOQA - no codes named",
        "# noqa : F401",
        "# noqa F401",
        "# noqa:f401",
        "# noqa:",
    ],
)
def test_a_blanket_or_malformed_noqa_is_refused(comment: str) -> None:
    """A ``# noqa`` naming no code, or naming codes ruff may read as none, is refused."""
    assert _refused(f"x = 1  {comment}\n") == [
        (1, "blanket or malformed `# noqa`: name its codes as `# noqa: E501, F401`"),
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
    source = "# ruff: disable[ERA001, E501] - quoted code\n# x = 1\n# ruff: enable[ERA001, E501]\n"

    assert _found(source) == [(1, "ERA001"), (1, "E501")]


@pytest.mark.parametrize(
    "comment",
    ["# ruff: disable[F401]", "#ruff:disable[F401]  ", "# ruff : disable [ F401 ] -"],
)
def test_a_fence_in_any_spacing_with_no_reason_also_counts_bare(comment: str) -> None:
    """Ruff reads a fence spaced any way; one with nothing after its codes counts ``bare``."""
    assert _found(f"{comment}\nimport os\n# ruff: enable[F401]\n") == [(1, "F401"), (1, cns.BARE)]


#: Each comment form, on an unused import: what ruff honours must be counted or refused.
_FORMS = [
    "import os  # noqa: F401",
    "import os  #noqa:F401",
    "import os  # NOQA: F401",
    "import os  # noqa : F401",
    "import os  # noqa F401",
    "import os  # noqa:F401,E501",
    "import os  # foo # noqa: F401",
    "import os  # foo noqa: F401",
    "import os  # noqa:f401",
    "import os  # noqa: F401 reason text",
    "import os  # noqa: F4",
    "import os  # type: ignore # noqa: F401",
    "import os  # noqa",
    "import os  # noqa:",
    "import os  # noqa - reason",
    "import os  # noqa: E501 # noqa: F401",
    "import os  #\tnoqa:\tF401",
    "import os  # noqa:F401:reason",
    "import os  # noqa: F401; reason",
    "import os  # noqa-F401",
    "import os  # noqa: ALL",
    "import os  # ruff: noqa: F401",
    "import os  # flake8: noqa: F401",
    "# ruff: noqa: F401\nimport os",
    "# flake8: noqa\nimport os",
    "#ruff:noqa:F401\nimport os",
    "# RUFF: NOQA: F401\nimport os",
    "# ruff: disable[F401]\nimport os\n# ruff: enable[F401]",
    "# ruff: disable[F401]\nimport os",
    "#ruff:disable[F401]\nimport os",
    "# ruff : disable [F401]\nimport os",
    "#  ruff\t:\tdisable\t[F401]\nimport os",
    "# ruff:  disable  [ F401 , E501 ]\nimport os",
    "# ruff: disable[F401] - reason\nimport os",
    "# RUFF: disable[F401]\nimport os",
    "# ruff: DISABLE[F401]\nimport os",
    "# ruff: disable\nimport os",
    "# ruff: disable[ALL]\nimport os",
    "import os  # ruff: disable[F401]",
    'import os; x = """\na\n"""  # noqa: F401',
    "import os, \\\n  sys  # noqa: F401",
]


def test_no_form_ruff_honours_passes_uncounted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every comment form that silences ruff's F401 is counted as F401 or refused.

    The forms run through the installed ruff, so a ruff release that reads a new spelling
    fails here rather than letting that spelling pass the gate.
    """
    monkeypatch.setattr(cns, "REPO_ROOT", tmp_path)
    for index, form in enumerate(_FORMS):
        _ = (tmp_path / f"form_{index}.py").write_text(f"{form}\n")
    report = cns._ruff(
        "check",
        "--isolated",
        "--select",
        "F401",
        "--exit-zero",
        "--output-format",
        "concise",
        ".",
    )
    reported = {Path(line.split(":")[0]).name for line in report.splitlines() if " F401 " in line}
    honoured = [form for index, form in enumerate(_FORMS) if f"form_{index}.py" not in reported]
    assert len(honoured) > 20

    for form in honoured:
        refused, found = cns.scan("form.py", f"{form}\n")
        assert refused or "F401" in {kind for _, kind in found}, form


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
    monkeypatch.setattr(cns, "tracked_files", lambda: sorted(files))
    monkeypatch.setattr(cns, "ruff_config", lambda: _config(linted=frozenset(files)))
    _ = (tmp_path / "scripts").mkdir(exist_ok=True)
    _ = (tmp_path / cns.CONFIG).write_text(_PYPROJECT)
    for path, source in files.items():
        _ = (tmp_path / path).write_text(source)
    return tmp_path / cns.LEDGER


_PYPROJECT = '[tool.ruff.lint]\nignore = ["E501"]\n\n[tool.ruff.lint.per-file-ignores]\n"t/*.py" = ["S101"]\n'


_NONE: frozenset[str] = frozenset()


def _config(
    *,
    linted: frozenset[str] = _NONE,
    lint_exclude: tuple[str, ...] = (),
    off: frozenset[str] = _NONE,
    per_file: tuple[tuple[str, str], ...] = (),
) -> cns.RuffConfig:
    return cns.RuffConfig(linted=linted, lint_exclude=lint_exclude, off=off, per_file=per_file)


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
        (
            "bare.py:1: `bare` at `bare.py::g`: 1, ledger 0: "
            "give the `# noqa` or fence its reason after the codes"
        ),
        f"{cns.LEDGER}:1: `A002` at `good.py::f`: 1, ledger 2: run `{cns.SCRIPT} --write`",
        (
            "noqa-suppressions: checked 2 file(s); suppressed codes 2, bare 1; config off 0, "
            "per-file 0; violations 3"
        ),
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
    _ = _tree(tmp_path, monkeypatch, {})
    monkeypatch.setattr(cns, "tracked_files", lambda: list(files))
    _ = (tmp_path / cns.LEDGER).write_text(ledger)

    assert cns.main([]) == 2


def test_main_exits_two_when_ruff_cannot_report_its_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ruff that fails, or prints its settings in an unknown form, fails the run."""
    _ = _tree(tmp_path, monkeypatch, {"good.py": _REASONED})

    def unreadable() -> cns.RuffConfig:
        raise cns.RuffConfigError("ruff's settings print no `linter.rules.enabled`")

    monkeypatch.setattr(cns, "ruff_config", unreadable)
    assert cns.main([]) == 2
    assert "linter.rules.enabled" in capsys.readouterr().err

    def failing() -> cns.RuffConfig:
        raise subprocess.CalledProcessError(2, ["ruff"])

    monkeypatch.setattr(cns, "ruff_config", failing)
    assert cns.main([]) == 2


def _commit(
    root: Path,
    text: str,
    message: str,
    *,
    ledger: str = cns.LEDGER,
) -> str:
    """Commit ``text`` as ``ledger`` in ``root``'s repository; return the new commit."""
    _ = (root / ledger).write_text(text)
    _ = _git.run_git(root, "add", ledger, check=True)
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


_SETTINGS = """\
linter.exclude = []
linter.rules.enabled = [
\tunused-import (F401),
\tline-too-long (E501),
\tpytest-fixture-autouse,
]
linter.per_file_ignores = {
\tabsolute_matcher = "/repo/t/*.py"
basename_matcher = "t/*.py"
negated = false
data = [
\tassert (S101),
]

\tabsolute_matcher = "/repo/keep.py"
basename_matcher = "keep.py"
negated = true
data = [
\tunused-import (F401),
]
}
"""


def test_the_settings_readers_take_ruffs_printed_settings() -> None:
    """Enabled rules by code (a code-less rule by name), per-file ignores with negation."""
    assert cns.enabled_rules(_SETTINGS) == {"F401", "E501", "pytest-fixture-autouse"}
    assert cns.per_file_ignores(_SETTINGS) == (("!keep.py", "F401"), ("t/*.py", "S101"))
    catalog = json.dumps(
        [
            {"code": "F401", "name": "unused-import", "status": {"Stable": {"since": "0"}}},
            {"code": "W291", "name": "trailing-whitespace", "status": "Stable"},
            {"code": None, "name": "pytest-fixture-autouse", "status": {"Preview": {}}},
            {"code": "X100", "name": "gone", "status": {"Removed": {}}},
        ],
    )
    assert cns.stable_rules(catalog) == {"F401", "W291"}


@pytest.mark.parametrize(
    ("reader", "text"),
    [
        (cns.enabled_rules, "linter.rules.enabled = [\n]\n"),
        (cns.enabled_rules, "linter.rules.enabled = [\n\tunused import F401\n]\n"),
        (cns.enabled_rules, "linter.rules.enabled = [\n\tunused-import (F401),\n"),
        (cns.enabled_rules, "linter.rules = []\n"),
        (cns.per_file_ignores, "linter.per_file_ignores = {\ndata = [\n\tassert (S101),\n]\n}\n"),
        (cns.stable_rules, "{}"),
        (cns.stable_rules, "[1]"),
        (cns.stable_rules, '[{"code": null, "name": null, "status": "Stable"}]'),
        (cns.stable_rules, '[{"code": "F401", "name": "x", "status": "Preview"}]'),
    ],
    ids=[
        "no-rule-enabled",
        "unreadable-rule",
        "never-closed",
        "missing",
        "no-matcher",
        "catalog-not-a-list",
        "catalog-entry-not-an-object",
        "rule-without-key",
        "no-stable-rule",
    ],
)
def test_the_settings_readers_refuse_a_form_they_do_not_know(
    reader: Callable[[str], object],
    text: str,
) -> None:
    """A ruff that prints its settings differently fails loudly instead of reading as empty."""
    with pytest.raises(cns.RuffConfigError):
        _ = reader(text)


def test_ruff_config_reads_the_effective_config_from_ruff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unselected and ignored rules are off, a prefix per-file ignore expands, excludes show."""
    monkeypatch.setattr(cns, "REPO_ROOT", tmp_path)
    _ = (tmp_path / "pyproject.toml").write_text(
        "[tool.ruff]\n"
        'extend-exclude = ["skipped.py"]\n'
        "[tool.ruff.lint]\n"
        'select = ["E", "F"]\n'
        'ignore = ["E501"]\n'
        'exclude = ["unlinted.py"]\n'
        "[tool.ruff.lint.per-file-ignores]\n"
        '"t/*.py" = ["F4"]\n'
        '"!keep.py" = ["E701"]\n',
    )
    for name in ("kept.py", "skipped.py", "unlinted.py"):
        _ = (tmp_path / name).write_text("x = 1\n")

    config = cns.ruff_config()

    assert {"E501", "W291", "S101"} <= config.off
    assert not {"F401", "E701"} & config.off
    assert ("t/*.py", "F401") in config.per_file
    assert ("t/*.py", "F403") in config.per_file
    assert ("!keep.py", "E701") in config.per_file
    assert config.lint_exclude == ('"unlinted.py"',)
    assert "kept.py" in config.linted
    assert "skipped.py" not in config.linted


def test_coverage_refuses_every_way_a_file_escapes_ruff(tmp_path: Path) -> None:
    """An unlinted file, a nested config, a notebook and ``lint.exclude`` are each refused."""
    _ = (tmp_path / "sub").mkdir()
    _ = (tmp_path / "sub" / "pyproject.toml").write_text("[tool.ruff.lint]\nignore = []\n")
    _ = (tmp_path / "other").mkdir()
    _ = (tmp_path / "other" / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    tracked = [
        "a.py",
        "b.pyi",
        "gone.py",
        "nb.ipynb",
        "pkg/ruff.toml",
        ".ruff.toml",
        "sub/pyproject.toml",
        "other/pyproject.toml",
        "pyproject.toml",
    ]
    config = _config(linted=frozenset({"a.py", "b.pyi"}), lint_exclude=('"x.py"',))

    assert [
        (v.path, v.message.split(":")[0])
        for v in cns.coverage_violations(tracked, config, tmp_path)
    ] == [
        ("pyproject.toml", '`lint.exclude` skips "x.py"'),
        ("gone.py", "ruff never lints this file (an exclude or .gitignore skips it)"),
        ("nb.ipynb", "a tracked notebook"),
        ("pkg/ruff.toml", "a nested ruff config overrides pyproject.toml for its tree"),
        (".ruff.toml", "a nested ruff config overrides pyproject.toml for its tree"),
        ("sub/pyproject.toml", "a nested ruff config overrides pyproject.toml for its tree"),
    ]


def test_main_holds_the_config_to_its_ledger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A rule newly off, everywhere or per glob, is refused at its config line; --write lowers."""
    _ = _tree(tmp_path, monkeypatch, {"good.py": _REASONED})
    _ = (tmp_path / cns.LEDGER).write_text('"good.py::f" = { A002 = 1 }\n')
    config_ledger = tmp_path / cns.CONFIG_LEDGER
    _ = config_ledger.write_text(f'"{cns.OFF_SITE}" = {{ E501 = 1, W291 = 1 }}\n')
    configured = _config(
        linted=frozenset({"good.py"}),
        off=frozenset({"E501"}),
        per_file=(("t/*.py", "S101"),),
    )
    monkeypatch.setattr(cns, "ruff_config", lambda: configured)

    assert cns.main([]) == 1
    assert capsys.readouterr().out.splitlines()[:2] == [
        f"{cns.CONFIG_LEDGER}:1: `W291` at `{cns.OFF_SITE}`: 0, ledger 1: run `{cns.SCRIPT} --write`",
        (
            f"{cns.CONFIG}:5: `S101` at `{cns.CONFIG}::lint.per-file-ignores[t/*.py]`: 1, "
            "ledger 0: keep the rule on and fix its diagnostics"
        ),
    ]
    assert cns.main(["--write"]) == 1

    monkeypatch.setattr(cns, "ruff_config", lambda: configured._replace(per_file=()))
    assert cns.main(["--write"]) == 0
    assert cts.load_ledger(config_ledger, frozenset()) == Counter({(cns.OFF_SITE, "E501"): 1})


def test_main_since_refuses_a_config_entry_moved_to_a_wider_glob(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The config ledger is walked per entry: a per-file ignore moved keeps no total."""
    _ = _tree(tmp_path, monkeypatch, {"good.py": _REASONED})
    _ = _git.run_git(tmp_path, "init", "-q", check=True)
    _ = _commit(tmp_path, '"good.py::f" = { A002 = 1 }\n', "noqa ledger")
    narrow = '"pyproject.toml::lint.per-file-ignores[t/*.py]" = { S101 = 1 }\n'
    base = _commit(tmp_path, narrow, "config ledger born", ledger=cns.CONFIG_LEDGER)
    wide = '"pyproject.toml::lint.per-file-ignores[**]" = { S101 = 1 }\n'
    moved = _commit(tmp_path, wide, "move", ledger=cns.CONFIG_LEDGER)
    monkeypatch.setattr(
        cns,
        "ruff_config",
        lambda: _config(linted=frozenset({"good.py"}), per_file=(("**", "S101"),)),
    )
    _ = (tmp_path / cns.CONFIG).write_text('"**" = ["S101"]\n')

    assert cns.main(["--since", base]) == 1
    assert capsys.readouterr().out.splitlines()[0] == (
        f"{cns.CONFIG_LEDGER}:1: {moved[:12]} raises `S101` at "
        f"`pyproject.toml::lint.per-file-ignores[**]` from 0 to 1 without a "
        f"`{cts.TRAILER}:` trailer (the maintainer's consent)"
    )
    assert cns.main(["--since", moved]) == 0
