"""Script tests for the every-spec glossary gate in ``scripts/check_all_spec_glossaries.py``.

Repo tooling: these rows pin which specs and terms CSVs the sweep enumerates, which CSV
each spec is checked against, the terms CSVs it reports as owned by no spec, that it never
rewrites a spec, and its exit codes. The per-spec checks themselves are
``tests/test_check_spec_glossary.py``'s rows. A CLI that reads markdown and CSV text has
no ``/graphql/`` wire shape, so there is no live sibling in
``examples/fakeshop/test_query/``.

Every row writes its tree under ``tmp_path``, so no row reads the real repository.
"""

from pathlib import Path

import pytest

from scripts import check_all_spec_glossaries

GLOSSARY = "## `DjangoType`\n\nBody.\n\n## Relay Node integration\n\nBody.\n"
LINK_DEFS = (
    "\n<!-- LINK DEFINITIONS -->\n\n<!-- docs/ -->\n"
    "[glossary-djangotype]: GLOSSARY.md#djangotype\n"
    "[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration\n"
)
LINKED = (
    "Uses [`DjangoType`][glossary-djangotype] and [Relay][glossary-relay-node-integration].\n"
    + LINK_DEFS
)
TERMS = (
    "term,anchor,notes\n`DjangoType`,djangotype,\nRelay Node integration,relay-node-integration,\n"
)
LIVE_SPEC = "docs/spec-002-live-0_0_2.md"
ARCHIVED_SPEC = "docs/SPECS/spec-001-archived-0_0_1.md"
ARCHIVED_TERMS = "docs/SPECS/appx/spec-001-archived-0_0_1-terms.csv"


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(text, encoding="utf-8")


def _tree(root: Path, *, archived_spec: str = LINKED, archived_terms: str = TERMS) -> None:
    """One live spec with its sibling companions, one archived spec with its ``appx/`` ones."""
    _write(root, "docs/GLOSSARY.md", GLOSSARY)
    _write(root, LIVE_SPEC, LINKED)
    _write(root, "docs/spec-002-live-0_0_2-terms.csv", TERMS)
    _write(root, "docs/spec-002-live-0_0_2-rationale.md", "Rationale.\n")
    _write(root, ARCHIVED_SPEC, archived_spec)
    _write(root, "docs/SPECS/appx/spec-001-archived-0_0_1-rationale.md", "Rationale.\n")
    _write(root, ARCHIVED_TERMS, archived_terms)
    _write(root, "docs/SPECS/NEXT.md", "Process.\n")


def _run(root: Path) -> int:
    return check_all_spec_glossaries.main(["--root", str(root)])


def test_every_spec_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Both specs are read (the rationale companions and ``NEXT.md`` are not specs)."""
    _tree(tmp_path)

    assert _run(tmp_path) == 0
    assert capsys.readouterr().out == (
        "OK: 2 specs - every terms CSV matches the glossary and its spec.\n"
    )


@pytest.mark.parametrize(
    ("archived_spec", "archived_terms", "reported"),
    [
        pytest.param(
            LINKED,
            TERMS + "DjangoType,djangotype,\n",
            "Rows repeating an anchor",
            id="repeated-anchor",
        ),
        pytest.param(
            # A CSV row whose term the body no longer links: the definition alone stays.
            "Uses [`DjangoType`][glossary-djangotype] and the Relay integration.\n" + LINK_DEFS,
            TERMS,
            "Relay Node integration (anchor: relay-node-integration)",
            id="definition-left-after-the-body-link-went",
        ),
        pytest.param(
            LINKED,
            TERMS + "DjangoListField,djangolistfield,\n",
            "Missing glossary entries",
            id="term-with-no-glossary-heading",
        ),
    ],
)
def test_a_failing_spec_is_named_and_the_others_are_not(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    archived_spec: str,
    archived_terms: str,
    reported: str,
) -> None:
    _tree(tmp_path, archived_spec=archived_spec, archived_terms=archived_terms)

    assert _run(tmp_path) == 1
    out = capsys.readouterr().out
    assert f"{ARCHIVED_SPEC} (exit 1):" in out
    assert reported in out
    assert "spec-002-live" not in out
    assert out.endswith(
        "FAILED: 1 of 2 spec(s) fail the glossary gate, 0 terms CSV(s) have no spec.\n",
    )


def test_a_renamed_glossary_heading_fails_every_spec_linking_it(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(tmp_path)
    _write(tmp_path, "docs/GLOSSARY.md", GLOSSARY.replace("## Relay Node integration", "## Relay"))

    assert _run(tmp_path) == 1
    out = capsys.readouterr().out
    assert f"{LIVE_SPEC} (exit 1):" in out
    assert f"{ARCHIVED_SPEC} (exit 1):" in out
    assert "FAILED: 2 of 2 spec(s)" in out


def test_the_sweep_never_rewrites_a_spec(tmp_path: Path) -> None:
    """A spec missing a link fails as it stands; the sweep runs without ``--auto-link``."""
    unlinked = "Uses [`DjangoType`][glossary-djangotype] and Relay Node integration.\n" + LINK_DEFS
    _tree(tmp_path, archived_spec=unlinked)

    assert _run(tmp_path) == 1
    assert (tmp_path / ARCHIVED_SPEC).read_text(encoding="utf-8") == unlinked


def test_a_spec_with_no_terms_csv_fails_with_the_missing_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _tree(tmp_path)
    (tmp_path / ARCHIVED_TERMS).unlink()

    assert _run(tmp_path) == 1
    out = capsys.readouterr().out
    assert f"{ARCHIVED_SPEC} (exit 2):" in out
    assert "missing file" in out


@pytest.mark.parametrize(
    "orphan",
    [
        pytest.param("docs/spec-009-orphan-0_0_9-terms.csv", id="live-dir"),
        pytest.param("docs/SPECS/spec-009-orphan-0_0_9-terms.csv", id="archive-dir"),
        pytest.param("docs/SPECS/appx/spec-009-orphan-0_0_9-terms.csv", id="appx-dir"),
        # The archived spec of that stem exists, but a CSV in docs/ is the live spec's.
        pytest.param("docs/spec-001-archived-0_0_1-terms.csv", id="live-dir-archived-stem"),
        # The live spec of that stem exists, but a CSV under appx/ is an archived spec's.
        pytest.param("docs/SPECS/appx/spec-002-live-0_0_2-terms.csv", id="appx-dir-live-stem"),
    ],
)
def test_a_terms_csv_with_no_spec_fails_by_name(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    orphan: str,
) -> None:
    _tree(tmp_path)
    _write(tmp_path, orphan, TERMS)

    assert _run(tmp_path) == 1
    out = capsys.readouterr().out
    assert f"Terms CSVs with no spec:\n  - {orphan}\n" in out
    assert out.endswith(
        "FAILED: 0 of 2 spec(s) fail the glossary gate, 1 terms CSV(s) have no spec.\n",
    )


def test_no_spec_is_an_error_not_a_pass(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write(tmp_path, "docs/GLOSSARY.md", GLOSSARY)
    _write(tmp_path, "docs/SPECS/NEXT.md", "Process.\n")

    assert _run(tmp_path) == 2
    captured = capsys.readouterr()
    assert captured.err == f"error: no spec found under {tmp_path.resolve()}\n"
    assert captured.out == ""
