"""Run ``scripts/check_spec_glossary.py`` over every spec and its terms CSV.

``check_spec_glossary.py --spec <path>`` checks one spec: every ``term`` / ``anchor`` row
of its ``*-terms.csv`` must name a ``## <heading>`` of ``docs/GLOSSARY.md``, the spec
must link each anchor, and no anchor may repeat. A glossary heading rename or a spec
edit that drops the last link to an anchor fails a spec nobody staged, so this gate
runs that check over the whole corpus.

The population is every ``docs/spec-*.md`` and ``docs/SPECS/spec-*.md`` (rationale
companions excluded), each checked by ``check_spec_glossary.main`` in this process
with its own spec, its default terms CSV (beside the spec, else under ``appx/``) and
the checkout's ``docs/GLOSSARY.md``, never with ``--auto-link``. A spec with no terms
CSV fails. A terms CSV fails by name when no spec owns it: one in ``docs/`` belongs to
the ``docs/`` spec of its stem, one in ``docs/SPECS/`` or ``docs/SPECS/appx/`` to the
``docs/SPECS/`` spec of its stem. An empty population fails rather than reading as a
pass.

Usage::

    uv run python scripts/check_all_spec_glossaries.py

``--root <dir>`` checks another checkout (default: this one). Exits 0 when every spec
passes, 1 when any spec fails or a terms CSV has no spec, and 2 when no spec is found.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
from pathlib import Path

try:
    import check_spec_glossary
except ModuleNotFoundError:  # imported as a ``scripts`` submodule (repo root on path)
    from scripts import check_spec_glossary

REPO_ROOT = Path(__file__).resolve().parent.parent
#: The live spec's directory and the archive, each relative to the checkout root.
LIVE_DIR = "docs"
ARCHIVE_DIR = "docs/SPECS"
TERMS_SUFFIX = "-terms.csv"


class _Args(argparse.Namespace):
    """The parsed command line."""

    root: Path


def _parse_args(argv: list[str] | None) -> _Args:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _ = parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Checkout whose specs are checked (default: this repository).",
    )
    return parser.parse_args(argv, namespace=_Args())


def spec_paths(root: Path) -> list[Path]:
    """Every spec markdown under ``root``, rationale companions excluded."""
    return sorted(
        path
        for directory in (LIVE_DIR, ARCHIVE_DIR)
        for path in (root / directory).glob("spec-*.md")
        if not path.stem.endswith("-rationale")
    )


def orphan_terms_csvs(root: Path, specs: list[Path]) -> list[Path]:
    """Every terms CSV under ``root`` that no spec in ``specs`` owns.

    A CSV in ``docs/`` belongs to the ``docs/`` spec of its stem; one in
    ``docs/SPECS/`` or its ``appx/`` to the ``docs/SPECS/`` spec of its stem.
    """
    known = set(specs)
    archive = root / ARCHIVE_DIR
    homes = {
        root / LIVE_DIR: root / LIVE_DIR,
        archive: archive,
        archive / check_spec_glossary.COMPANION_DIRNAME: archive,
    }
    return sorted(
        path
        for directory, home in homes.items()
        for path in directory.glob(f"spec-*{TERMS_SUFFIX}")
        if home / f"{path.name.removesuffix(TERMS_SUFFIX)}.md" not in known
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: run the per-spec glossary gate over every spec."""
    root = _parse_args(argv).root.resolve()
    specs = spec_paths(root)
    if not specs:
        print(f"error: no spec found under {root}", file=sys.stderr)
        return 2

    glossary = root / "docs" / "GLOSSARY.md"
    failed: list[Path] = []
    for spec in specs:
        report = io.StringIO()
        with contextlib.redirect_stdout(report), contextlib.redirect_stderr(report):
            code = check_spec_glossary.main(
                [
                    "--spec",
                    str(spec),
                    "--glossary",
                    str(glossary),
                ],
            )
        if code != 0:
            failed.append(spec)
            print(f"{spec.relative_to(root)} (exit {code}):")
            print(report.getvalue().rstrip())
            print()

    orphans = orphan_terms_csvs(root, specs)
    if orphans:
        print("Terms CSVs with no spec:")
        for path in orphans:
            print(f"  - {path.relative_to(root)}")
        print()

    if failed or orphans:
        print(
            f"FAILED: {len(failed)} of {len(specs)} spec(s) fail the glossary gate, "
            f"{len(orphans)} terms CSV(s) have no spec.",
        )
        return 1
    print(f"OK: {len(specs)} specs - every terms CSV matches the glossary and its spec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
