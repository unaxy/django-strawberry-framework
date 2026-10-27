r"""Validate that a spec's project-specific terms are glossary-anchored.

The companion ``*-terms.csv`` carries one row per anchor: a second row
naming an anchor already used fails the run, since
``manage.py import_spec_terms`` keys each done card's glossary rows by
anchor and refuses the CSV. Variant spellings of one symbol share the
anchor's single row (its ``notes`` cell can name them).

Two checks per term in the spec's companion ``*-terms.csv``:

1. ``docs/GLOSSARY.md`` has a ``## <heading>`` whose GitHub auto-anchor
   matches the term's ``anchor`` column.
2. The spec markdown links to that anchor by either form:

   - **Inline**: an ``](...GLOSSARY.md#<anchor>)`` reference (legacy /
     mixed-style support).
   - **Reference-style** (the current convention - see ``START.md``'s
     "Markdown link convention" section): a ``[text][ref-id]`` use in
     the body whose matching ``[ref-id]: ...GLOSSARY.md#<anchor>`` def
     lives in the unified link-definitions block at the bottom.

   A use counts only where it renders as a link: the ``scripts/_markdown_lex.py``
   lexer must pair it as a ``[...]`` group with its link tail, so one inside
   fenced or indented code, a code span, an HTML block, raw HTML or an
   autolink is no link to the anchor. A link in a heading renders, so it
   counts, although ``--auto-link`` never writes one there.

Exits 0 when every term passes both checks and no anchor repeats, 1 when
any term fails or an anchor repeats, and 2 on a CLI / file-not-found error.

Usage::

    uv run python scripts/check_spec_glossary.py \
        --spec docs/spec-018-meta_primary-0_0_6.md \
        --terms docs/spec-018-meta_primary-0_0_6-terms.csv \
        --glossary docs/GLOSSARY.md \
        --auto-link

Only ``--spec`` is required. ``--terms`` defaults to the spec path with
``-terms.csv`` appended to the stem (e.g.
``docs/spec-018-meta_primary-0_0_6.md`` ->
``docs/spec-018-meta_primary-0_0_6-terms.csv``). An archived spec keeps
its companions one level down in ``appx/`` (e.g.
``docs/SPECS/spec-018-meta_primary-0_0_6.md`` ->
``docs/SPECS/appx/spec-018-meta_primary-0_0_6-terms.csv``), so the
sibling is preferred when it exists and ``appx/`` is the fallback.
``--glossary`` defaults to ``docs/GLOSSARY.md`` and accepts an override
for testing or for validating against a fork's renamed glossary.

Pass ``--auto-link`` to also rewrite the spec in place: for every term
listed as missing a link, the script finds the first non-code,
non-link, non-heading mention, wraps it as a **reference-style**
``[term][glossary-<anchor>]`` link, and inserts the matching
``[glossary-<anchor>]: <path>/GLOSSARY.md#<anchor>`` def under the
``<!-- docs/ -->`` group in the spec's link-definitions block (at its
label's alphabetical place; the group's other lines keep their order). A
mention is one the ``scripts/_markdown_lex.py`` lexer leaves open:
outside a heading, a link reference definition, fenced or indented code
and an HTML block; not overlapping an existing link of any shape, an
autolink, raw HTML, a bare URL or a ``#"..."`` pinpoint; not cutting a
code span, a backtick run or an escape; and a standalone token (no
identifier, ``.``, ``:``, ``/`` or ``-`` character before it, no
identifier character after it, nor a ``.``, ``:``, ``/`` or ``-`` run
leading into one). A mention that fails any of these is passed over for
the next one. The backtick-wrapped
form is preferred when the spec already says e.g. ``Meta.fields`` in
inline code - the rewrite becomes ``[`Meta.fields`][glossary-metafields]``
with the inline-code backticks preserved inside the link label. The run
is idempotent. ``--auto-link`` requires the spec to already carry a
``<!-- docs/ -->`` group in its link-definitions block; if the block is
missing, the term is skipped and reported.

The CSV is the source of truth: trim it when a term does not warrant a
glossary entry, extend it when a new term needs one.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path

try:
    from _markdown_lex import (
        TERM_BOUNDARY_AFTER,
        TERM_BOUNDARY_BEFORE,
        _protected_regions,
        first_open_match,
        mask_blocks,
    )
except ModuleNotFoundError:  # imported as ``scripts.check_spec_glossary`` (repo root on path)
    from scripts._markdown_lex import (
        TERM_BOUNDARY_AFTER,
        TERM_BOUNDARY_BEFORE,
        _protected_regions,
        first_open_match,
        mask_blocks,
    )

HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
LINK_PATTERN = re.compile(r"\]\([^)]*GLOSSARY\.md#([^)]+)\)")
# Reference-style link defs at the bottom of a spec: `[ref-id]: target`
REF_DEF_PATTERN = re.compile(r"^\[([^\[\]]+)\]:\s+(.+)$", re.MULTILINE)
# Reference-style link uses in the body: `[text][ref-id]`
REF_USE_PATTERN = re.compile(r"\]\[([^\[\]]+)\]")
# Glossary anchor extracted from a ref-def target (any path prefix accepted)
REF_TARGET_GLOSSARY_ANCHOR = re.compile(r"GLOSSARY\.md#(\S+)")
# Docs/ group header inside the unified link-definitions block
DOCS_GROUP_HEADER = "<!-- docs/ -->"
# Subfolder holding an archived spec's companion files, beside the archived spec
COMPANION_DIRNAME = "appx"
# A heading that is itself a link slugs from its visible text, so both link
# forms are rendered down to that text before the heading is slugged.
HEADING_INLINE_LINK = re.compile(r"\[([^\[\]]*)\]\([^()]*\)")
HEADING_REFERENCE_LINK = re.compile(r"\[([^\[\]]*)\]\[[^\[\]]*\]")


def github_anchor(heading: str) -> str:
    """Approximate GitHub's H2 auto-anchor slugger for ``docs/GLOSSARY.md``.

    Renders both markdown link forms down to their visible text, drops
    backticks, lowercases, strips non-word characters other than
    whitespace and hyphens, then collapses whitespace runs to single
    hyphens. Underscores and existing hyphens are preserved. Matches the
    anchor form GitHub renders for headings like ``## `Meta.primary``` ->
    ``metaprimary``, ``## Relation handling`` -> ``relation-handling``,
    and ``## [Scalar field conversion][glossary-scalar-field-conversion]``
    -> ``scalar-field-conversion``. Slugging the raw markup instead would
    fold the link target into the anchor, which matches no rendered page.
    """
    text = HEADING_INLINE_LINK.sub(r"\1", heading)
    text = HEADING_REFERENCE_LINK.sub(r"\1", text)
    text = text.replace("`", "").lower()
    text = re.sub(r"[^\w\s\-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


def load_terms(csv_path: Path) -> list[tuple[str, str]]:
    """Return ``[(term, anchor), ...]`` from the terms CSV.

    Rows missing either column are silently skipped - the CSV uses a
    header row (``term,anchor,notes``); blanks in the body are tolerated
    so the file can carry trailing-comma whitespace from spreadsheet
    exports without confusing the checker.
    """
    rows: list[tuple[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            term = (row.get("term") or "").strip()
            anchor = (row.get("anchor") or "").strip()
            if term and anchor:
                rows.append((term, anchor))
    return rows


def glossary_anchors(glossary_path: Path) -> dict[str, str]:
    """Return ``{anchor: heading_text}`` for every H2 in ``GLOSSARY.md``."""
    anchors: dict[str, str] = {}
    with glossary_path.open(encoding="utf-8") as handle:
        for line in handle:
            match = HEADING_PATTERN.match(line)
            if match:
                heading = match.group(1).strip()
                anchors[github_anchor(heading)] = heading
    return anchors


def spec_link_anchors(spec_path: Path) -> set[str]:
    """Return the set of ``GLOSSARY.md`` anchors referenced from the spec.

    Recognizes two link forms:

    - **Inline** ``](...GLOSSARY.md#<anchor>)`` - legacy / mixed-style.
    - **Reference-style** ``[text][ref-id]`` where the matching
      ``[ref-id]: ...GLOSSARY.md#<anchor>`` def at the bottom of the
      file resolves to a GLOSSARY anchor. This is the current convention
      (see ``START.md``'s "Markdown link convention" section).

    Either use counts only inside a link ``_link_groups`` finds.
    """
    text = spec_path.read_text(encoding="utf-8")
    body = mask_blocks(text, headings=False)
    groups = _link_groups(body)
    anchors: set[str] = set()
    # Inline form.
    anchors.update(
        match.group(1) for match in LINK_PATTERN.finditer(body) if _in_link(match, groups)
    )
    # Reference-style form: build the ref-id -> target map from the
    # link-definitions block, then resolve every `[text][ref-id]` body
    # use whose target is a GLOSSARY anchor.
    defs = {match.group(1): match.group(2).strip() for match in REF_DEF_PATTERN.finditer(text)}
    if defs:
        for match in REF_USE_PATTERN.finditer(body):
            if not _in_link(match, groups):
                continue
            target = defs.get(match.group(1), "")
            anchor_match = REF_TARGET_GLOSSARY_ANCHOR.search(target)
            if anchor_match:
                anchors.add(anchor_match.group(1))
    return anchors


def _link_groups(body: str) -> list[tuple[int, int]]:
    """Spans of the ``[...]`` groups ``_protected_regions`` pairs in block-masked ``body``.

    Every other opaque region starts with ``<`` (an autolink or raw HTML), ``#`` (a
    pinpoint) or a URL or email character, and the lexer pairs no bracket inside a code
    span, an autolink or raw HTML; a masked block holds no bracket at all.
    """
    return [(lo, hi) for lo, hi in _protected_regions(body).opaque if body.startswith("[", lo)]


def _in_link(match: re.Match[str], groups: list[tuple[int, int]]) -> bool:
    """Whether the ``]...`` link-tail ``match`` closes inside one bracket group."""
    lo, hi = match.span()
    return any(start < lo and hi <= end for start, end in groups)


def duplicate_anchor_rows(terms: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return every ``(term, anchor)`` row whose anchor an earlier row already carries."""
    seen: set[str] = set()
    duplicates: list[tuple[str, str]] = []
    for term, anchor in terms:
        if anchor in seen:
            duplicates.append((term, anchor))
        seen.add(anchor)
    return duplicates


def check_terms(
    terms: list[tuple[str, str]],
    glossary_index: dict[str, str],
    spec_anchors: set[str],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return ``(missing_glossary, missing_links)`` lists of ``(term, anchor)``."""
    missing_glossary: list[tuple[str, str]] = []
    missing_links: list[tuple[str, str]] = []
    for term, anchor in terms:
        if anchor not in glossary_index:
            missing_glossary.append((term, anchor))
        if anchor not in spec_anchors:
            missing_links.append((term, anchor))
    return missing_glossary, missing_links


def first_mention(text: str, term: str) -> tuple[int, int] | None:
    r"""Span of the mention of ``term`` the auto-linker wraps, else None.

    The backtick-wrapped form ``\`term\``` first, then the plain form; for each form the
    first match in the block-masked text that ``first_open_match`` leaves open, bounded
    by ``TERM_BOUNDARY_BEFORE`` and ``TERM_BOUNDARY_AFTER``. A plain mention inside
    a code span cuts it, so the plain form never lands in code.
    """
    body = mask_blocks(text)
    regions = _protected_regions(body)
    for form in (f"`{term}`", term):
        pattern = re.compile(TERM_BOUNDARY_BEFORE + re.escape(form) + TERM_BOUNDARY_AFTER)
        match = first_open_match(pattern, body, regions)
        if match is not None:
            return match.span()
    return None


def _glossary_ref_id(anchor: str) -> str:
    """Derive a stable reference-style ID from a glossary anchor.

    The convention used by the unified link-definitions block prefixes
    every glossary ref-id with ``glossary-`` and normalizes underscores
    in the anchor to dashes. So ``bigint-scalar`` -> ``glossary-bigint-scalar``,
    ``finalize_django_types`` -> ``glossary-finalize-django-types``.
    """
    return f"glossary-{anchor.replace('_', '-')}"


def _insert_glossary_ref_def(text: str, ref_id: str, target: str) -> str | None:
    """Insert ``[ref_id]: target`` under the ``<!-- docs/ -->`` group.

    Returns the rewritten text on success, or ``None`` when the spec has
    no ``<!-- docs/ -->`` group to insert into (auto-link should not
    materialize a link-definitions block from scratch; that is the
    initial-conversion script's job, not the glossary checker's).

    The new line goes before the group's first def whose label (the text
    between the leading ``[`` and the first ``]``) sorts after ``ref_id``
    by codepoint, or at the group's end when none does. Every existing
    line keeps its order and bytes: the writer never re-sorts lines it
    did not write, so a hand-ordered group stays as its author left it.

    Idempotent - if a def for ``ref_id`` already exists anywhere in the
    file, the input text is returned unchanged.
    """
    if re.search(rf"^\[{re.escape(ref_id)}\]:\s", text, re.MULTILINE):
        return text
    lines = text.split("\n")
    try:
        header_idx = next(i for i, line in enumerate(lines) if line.strip() == DOCS_GROUP_HEADER)
    except StopIteration:
        return None
    # Collect any existing defs starting on the line after the header
    # (defs are `[id]: target`; the group ends at the first non-def line).
    end_idx = header_idx + 1
    while end_idx < len(lines) and lines[end_idx].startswith("["):
        end_idx += 1
    insert_idx = next(
        (i for i in range(header_idx + 1, end_idx) if lines[i][1:].partition("]")[0] > ref_id),
        end_idx,
    )
    return "\n".join(
        [*lines[:insert_idx], f"[{ref_id}]: {target}", *lines[insert_idx:]],
    )


def auto_link_terms(
    spec_path: Path,
    glossary_path: Path,
    missing_links: list[tuple[str, str]],
) -> tuple[list[str], list[str]]:
    """Insert reference-style glossary links + matching defs in-place.

    For each ``(term, anchor)`` in ``missing_links``:

    1. Compute ``ref_id = glossary-<anchor with _ -> ->`` and
       ``ref_target = <relpath to GLOSSARY.md>#<anchor>``.
    2. Locate the mention ``first_mention`` picks (the backtick-wrapped
       form first, then the plain form) and wrap it as ``[`term`][ref_id]``
       or ``[term][ref_id]``, so inline-code formatting survives inside
       the link label.
    3. A term with no open mention in either form is skipped.
    4. Insert ``[ref_id]: ref_target`` under the ``<!-- docs/ -->``
       group in the spec's link-definitions block, at its label's
       alphabetical place without moving the group's other lines. If the
       def already exists, no-op.

    The spec file is re-read between terms so each replacement sees a
    freshly lexed text (cheap for spec-sized files, avoids the
    range-shifting bookkeeping after an edit).

    Returns ``(linked, skipped)`` - both lists of term names. A term is
    skipped when no open mention exists OR the spec has no
    ``<!-- docs/ -->`` group to insert the def into.
    """
    linked: list[str] = []
    skipped: list[str] = []
    for term, anchor in missing_links:
        ref_id = _glossary_ref_id(anchor)
        ref_target = f"{os.path.relpath(glossary_path, spec_path.parent)}#{anchor}"
        text = spec_path.read_text(encoding="utf-8")
        span = first_mention(text, term)
        if span is None:
            skipped.append(term)
            continue
        lo, hi = span
        new_text = f"{text[:lo]}[{text[lo:hi]}][{ref_id}]{text[hi:]}"

        with_def = _insert_glossary_ref_def(new_text, ref_id, ref_target)
        if with_def is None:
            # No <!-- docs/ --> group to insert the def into; do NOT
            # write the wrap, which would leave an orphaned ref-id.
            skipped.append(term)
            continue
        _ = spec_path.write_text(with_def, encoding="utf-8")
        linked.append(term)
    return linked, skipped


def _print_section(title: str, entries: list[tuple[str, str]], hint: str) -> None:
    print(title)
    for term, anchor in entries:
        print(f"  - {term} (anchor: {anchor}) - {hint.format(anchor=anchor)}")
    print()


class _Args(argparse.Namespace):
    """The parsed command line, typed field by field after ``_parse_args``'s ``add_argument`` calls."""

    spec: Path
    terms: Path | None
    glossary: Path
    auto_link: bool


def _parse_args(argv: list[str] | None) -> _Args:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _ = parser.add_argument(
        "--spec",
        required=True,
        type=Path,
        help="Path to the spec markdown file.",
    )
    _ = parser.add_argument(
        "--terms",
        type=Path,
        default=None,
        help=(
            "Path to the spec's companion `*-terms.csv` (columns: term, anchor, notes). "
            "Defaults to `<spec-stem>-terms.csv` alongside the spec."
        ),
    )
    _ = parser.add_argument(
        "--glossary",
        type=Path,
        default=Path("docs/GLOSSARY.md"),
        help="Path to the glossary (default: docs/GLOSSARY.md).",
    )
    _ = parser.add_argument(
        "--auto-link",
        action="store_true",
        help=(
            "Rewrite the spec in place: for each term in the missing-link list, "
            "wrap the first non-code, non-link, non-heading mention as the reference-style "
            "[term][glossary-anchor] and insert the matching "
            "[glossary-anchor]: GLOSSARY.md#anchor definition. Idempotent."
        ),
    )
    return parser.parse_args(argv, namespace=_Args())


def _default_terms_path(spec_path: Path) -> Path:
    """Derive ``<spec-stem>-terms.csv`` for the spec when ``--terms`` is omitted.

    A live spec keeps its companion beside it; an archived one keeps it in the
    spec directory's ``appx/`` subfolder. The sibling wins when it exists, so a
    missing companion is reported at the authoring location.
    """
    sibling = spec_path.with_name(f"{spec_path.stem}-terms.csv")
    if sibling.is_file():
        return sibling
    archived = spec_path.parent / COMPANION_DIRNAME / sibling.name
    return archived if archived.is_file() else sibling


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: validate (and optionally auto-link) the spec's glossary references."""
    args = _parse_args(argv)
    if args.terms is None:
        args.terms = _default_terms_path(args.spec)

    for path in (args.spec, args.terms, args.glossary):
        if not path.exists():
            print(f"error: missing file: {path}", file=sys.stderr)
            return 2

    terms = load_terms(args.terms)
    if not terms:
        print(f"error: no terms loaded from {args.terms}", file=sys.stderr)
        return 2

    glossary_index = glossary_anchors(args.glossary)
    spec_anchors = spec_link_anchors(args.spec)
    missing_glossary, missing_links = check_terms(terms, glossary_index, spec_anchors)

    if args.auto_link and missing_links:
        linked, skipped = auto_link_terms(args.spec, args.glossary, missing_links)
        if linked:
            print(f"auto-link: inserted {len(linked)} link(s) into {args.spec}:")
            for term in linked:
                print(f"  + {term}")
        if skipped:
            print(
                f"auto-link: {len(skipped)} term(s) had no non-code, non-link, "
                "non-heading mention:",
            )
            for term in skipped:
                print(f"  - {term}")
        if linked or skipped:
            print()
        # Re-read spec so the post-rewrite missing-link list is accurate.
        spec_anchors = spec_link_anchors(args.spec)
        missing_glossary, missing_links = check_terms(terms, glossary_index, spec_anchors)

    if missing_glossary:
        _print_section(
            f"Missing glossary entries in {args.glossary}:",
            missing_glossary,
            "add `## <heading>` whose slug is `{anchor}`",
        )
    if missing_links:
        _print_section(
            f"Spec terms missing a link to {args.glossary.name}:",
            missing_links,
            "add at least one link to anchor `{anchor}` - inline `](GLOSSARY.md#{anchor})` "
            "or reference-style `[text][glossary-...]` (with matching def in the link-definitions block)",
        )

    duplicates = duplicate_anchor_rows(terms)
    if duplicates:
        _print_section(
            f"Rows repeating an anchor in {args.terms}:",
            duplicates,
            "fold this term into the first `{anchor}` row; the CSV carries one row per anchor",
        )

    if missing_glossary or missing_links or duplicates:
        return 1

    print(f"OK: {len(terms)} terms - all have glossary entries and at least one spec link.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
