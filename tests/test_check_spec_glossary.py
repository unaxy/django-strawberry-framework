"""Script tests for the spec terms-CSV glossary gate.

Repo tooling: these rows pin ``scripts/check_spec_glossary.py``'s one-row-per-anchor rule,
its exit codes, which glossary links count as a spec's link to an anchor, and where
``--auto-link`` writes a link: the mention the ``scripts/_markdown_lex.py`` lexer leaves open
(no heading, link reference definition, code or HTML block; no existing link, autolink, raw
HTML, bare URL or pinpoint; no cut code span) and the prose term boundary picks, retried past
every mention that fails. A CLI that reads spec, CSV and glossary text has no ``/graphql/``
wire shape, so there is no live sibling in ``examples/fakeshop/test_query/``.

Every row writes its spec, CSV and glossary under ``tmp_path``, so no row reads the real
repository.
"""

from pathlib import Path

import pytest

from scripts import check_spec_glossary

GLOSSARY = "## `DjangoType`\n\nBody.\n\n## Relay Node integration\n\nBody.\n"
SPEC = (
    "Uses [`DjangoType`][glossary-djangotype] and [Relay][glossary-relay-node-integration].\n"
    "\n"
    "<!-- LINK DEFINITIONS -->\n"
    "\n"
    "<!-- docs/ -->\n"
    "[glossary-djangotype]: GLOSSARY.md#djangotype\n"
    "[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration\n"
)
TERM = "DjangoListField"
ANCHOR = "djangolistfield"
REF_ID = "glossary-djangolistfield"
LINK = f"[{TERM}][{REF_ID}]"
TICKED_LINK = f"[`{TERM}`][{REF_ID}]"
TITLE = "# Spec 999\n\n"
# The spec's link-definitions block: the 10 group headers, ``{docs}`` under ``docs/`` and
# ``{ext}`` under ``External``.
LINK_DEFINITIONS = (
    "\n<!-- LINK DEFINITIONS -->\n\n<!-- Root -->\n\n<!-- docs/ -->\n{docs}\n"
    "<!-- docs/SPECS/ -->\n\n<!-- docs/builder/ -->\n\n<!-- django_strawberry_framework/ -->\n\n"
    "<!-- tests/ -->\n\n<!-- examples/ -->\n\n<!-- scripts/ -->\n\n<!-- .venv/ -->\n\n"
    "<!-- External -->\n{ext}"
)


def _run(tmp_path: Path, csv_body: str) -> int:
    """Write the fixture trio under ``tmp_path`` and run the gate on it."""
    spec = tmp_path / "spec-099-example-0_0_9.md"
    _ = spec.write_text(SPEC, encoding="utf-8")
    _ = (tmp_path / "spec-099-example-0_0_9-terms.csv").write_text(
        "term,anchor,notes\n" + csv_body,
        encoding="utf-8",
    )
    glossary = tmp_path / "GLOSSARY.md"
    _ = glossary.write_text(GLOSSARY, encoding="utf-8")
    return check_spec_glossary.main(
        [
            "--spec",
            str(spec),
            "--glossary",
            str(glossary),
        ],
    )


def test_one_row_per_anchor_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_body = "`DjangoType`,djangotype,\nRelay Node integration,relay-node-integration,\n"

    assert _run(tmp_path, csv_body) == 0
    assert "OK: 2 terms" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("csv_body", "repeats", "kept"),
    [
        pytest.param(
            "`DjangoType`,djangotype,\n"
            "Relay Node integration,relay-node-integration,\n"
            "`GlobalID`,relay-node-integration,\n",
            ["`GlobalID` (anchor: relay-node-integration)"],
            ["Relay Node integration (anchor"],
            id="adjacent-repeat",
        ),
        pytest.param(
            "Relay Node integration,relay-node-integration,\n"
            "`DjangoType`,djangotype,\n"
            "Relay Node integration,relay-node-integration,second note\n",
            ["Relay Node integration (anchor: relay-node-integration)"],
            ["`DjangoType` (anchor"],
            id="same-term-repeated-after-another-row",
        ),
        pytest.param(
            "`DjangoType`,djangotype,\n"
            "`DjangoTypes`,djangotype,\n"
            "Relay Node integration,relay-node-integration,\n"
            "`GlobalID`,relay-node-integration,\n",
            ["`DjangoTypes` (anchor: djangotype)", "`GlobalID` (anchor: relay-node-integration)"],
            ["`DjangoType` (anchor", "Relay Node integration (anchor"],
            id="two-anchors-each-repeated",
        ),
    ],
)
def test_a_second_row_for_one_anchor_fails_naming_it(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    csv_body: str,
    repeats: list[str],
    kept: list[str],
) -> None:
    assert _run(tmp_path, csv_body) == 1
    out = capsys.readouterr().out
    assert "Rows repeating an anchor in" in out
    for row in repeats:
        assert row in out
    for row in kept:
        assert row not in out


def _spec(body: str, docs: str = "", ext: str = "") -> str:
    """A spec carrying ``body`` (under a title unless it opens with a heading) and the defs block."""
    head = "" if body.startswith("#") else TITLE
    return head + body + LINK_DEFINITIONS.format(docs=docs, ext=ext)


def _row(
    row_id: str,
    body: str,
    linked: str | None = None,
    *,
    term: str = TERM,
    anchor: str = ANCHOR,
    docs: str = "",
    ext: str = "",
) -> object:
    """One auto-link row: ``linked`` is the body after the write, None when nothing is written."""
    return pytest.param(body, linked, term, anchor, docs, ext, id=row_id)


@pytest.mark.parametrize(
    (
        "body",
        "linked",
        "term",
        "anchor",
        "docs",
        "ext",
    ),
    [
        # Inline constructs a term link may not overlap or cut.
        _row("code-span-sentence", f"Call `x = {TERM}(a)` now.\n"),
        _row("code-span-longer-identifier", f"Use `{TERM}Extra` here.\n"),
        _row("double-backtick-inner-tick", f"Use ``a ` {TERM}`` here.\n"),
        _row("double-backtick-span", f"Use ``{TERM}`` here.\n"),
        _row("reference-link-text", f"See [{TERM}][other] now.\n", docs="[other]: ../x.md\n"),
        _row("collapsed-reference-link", f"See [{TERM}][] now.\n", docs=f"[{TERM}]: ../x.md\n"),
        _row("shortcut-reference-link", f"See [{TERM}] now.\n", docs=f"[{TERM}]: ../x.md\n"),
        _row("reference-label", f"See [text][{TERM}] now.\n", docs=f"[{TERM}]: ../x.md\n"),
        _row("inline-link-text", f"[{TERM}](y.md)\n"),
        _row("inline-link-destination", f"[x]({TERM}.md)\n"),
        _row("inline-link-title", f'[x](y.md "{TERM}")\n'),
        _row("inline-link-title-nested-parens", f'[x](y.md "t ({TERM}) u")\n'),
        _row("link-text-across-lines", f"[see\n{TERM}](x.md)\n"),
        _row("link-text-code-span-bracket", f"[`a]` {TERM}](x.md)\n"),
        _row("image-alt", f"![{TERM}](a.png)\n"),
        _row("autolink", f"Go <https://example.com/{TERM}> now.\n"),
        _row("raw-html-attribute", f'Use <a href="x" title="{TERM}">y</a> now.\n'),
        _row("raw-html-comment", f"Use <!-- {TERM} --> now.\n"),
        _row("bare-url", f"See https://example.com/{TERM} now.\n"),
        _row("pinpoint", f'See the module #"call {TERM} here" now.\n'),
        _row("citation-code-span", f"See `a/b.py::{TERM}` now.\n"),
        # Block constructs a term link may not land in.
        _row("atx-heading", f"## {TERM}\n\nBody.\n"),
        _row("atx-heading-code", f"## `{TERM}`\n\nBody.\n"),
        _row("atx-heading-closing-hashes", f"## Foo {TERM} ##\n\nBody.\n"),
        _row("atx-heading-title", f"# {TERM} spec\n\nBody.\n"),
        _row("setext-heading", f"{TERM}\n===\n\nBody.\n"),
        _row("setext-heading-dashes", f"{TERM}\n---\n\nBody.\n"),
        _row("setext-heading-two-lines", f"Some\n{TERM} words\n===\n"),
        _row("fence-backtick", f"```\n{TERM}\n```\n"),
        _row("fence-tilde", f"~~~\n{TERM}\n~~~\n"),
        _row("fence-four-backticks-nested", f"````\n```\n{TERM}\n```\n````\n"),
        _row("fence-in-list-item", f"- item\n\n  ```python\n  {TERM}()\n  ```\n"),
        _row("fence-on-list-marker-line", f"- ```\n  {TERM}()\n  ```\n"),
        _row("fence-in-blockquote", f"> ```\n> {TERM}\n> ```\n"),
        _row("fence-unterminated", f"```\n{TERM}\n"),
        _row("indented-code", f"para\n\n    {TERM}()\n\nafter\n"),
        _row("indented-code-tab", f"para\n\n\t{TERM}()\n"),
        _row("indented-code-in-list-item", f"- item\n\n        {TERM}()\n"),
        _row("indented-code-past-list-marker", f"-      {TERM}()\n"),
        _row("indented-code-past-sibling-list-marker", f"- a\n-      {TERM}()\n"),
        _row("list-item-then-column-0-fence", f"- item\n```py\n{TERM}()\n```\n"),
        _row("ordered-item-then-column-0-tilde-fence", f"1. item\n~~~\n{TERM}()\n~~~\n"),
        _row("list-continuation-then-column-0-fence", f"- a\n  b\n```\n{TERM}()\n```\n"),
        _row(
            "nested-item-then-outer-item-fence",
            f"- outer\n  - inner para\n  ```\n  {TERM}()\n  ```\n",
        ),
        _row("indented-fence-marker-inside-fence", f"```\n    ```\n{TERM}\n```\n"),
        _row("tab-after-blockquote-marker-code", f">\t\t{TERM}()\n"),
        _row("space-then-tab-after-blockquote-marker-code", f"> \t  {TERM}()\n"),
        _row("ordered-item-tab-in-blockquote-then-code", f"> 1.\titem\n> \n>     x {TERM}\n"),
        _row("nested-blockquote-after-tab-code", f">\t>     {TERM}()\n"),
        _row("nested-blockquote-after-tab-fence", f">\t> ```\n>\t> {TERM}\n>\t> ```\n"),
        _row("nested-blockquote-after-tab-space-code", f">\t >     {TERM}()\n"),
        _row("html-comment-block", f"<!--\n{TERM}\n-->\n"),
        _row("html-block-div", f"<div>\n{TERM}\n</div>\n"),
        _row("html-block-pre", f"<pre>\n\n{TERM}\n</pre>\n"),
        _row("html-block-tag-line", f"<custom-tag>\n{TERM}\n"),
        _row("definition-label", "Body.\n", ext=f"[{TERM}]: https://example.com/x\n"),
        _row("definition-destination", "Body.\n", ext=f"[ext]: https://example.com/{TERM}\n"),
        _row("definition-title", "Body.\n", ext=f'[ext]: https://example.com/x "{TERM}"\n'),
        _row(
            "definition-title-next-line",
            "Body.\n",
            ext=f'[ext]: https://example.com/x\n"{TERM}"\n',
        ),
        _row(
            "definition-path",
            "Body.\n",
            docs=f"[src]: ../django_strawberry_framework/{TERM}.py\n",
        ),
        # The term boundary.
        _row("identifier-suffix", f"Use {TERM}Extra here.\n"),
        _row("identifier-prefix", f"Use My{TERM} here.\n"),
        _row("plural", f"Use {TERM}s here.\n"),
        _row("code-span-plural", f"Several `{TERM}`s here.\n"),
        _row("dotted-prefix", f"Use utils.{TERM} here.\n"),
        _row("dotted-suffix", f"Use {TERM}.method here.\n"),
        _row("path-like", f"See docs/{TERM}.md here.\n"),
        _row("path-citation", f"See a/b.py::{TERM} now.\n"),
        _row("leading-hyphen", f"A non-{TERM} thing.\n"),
        _row("trailing-hyphen-word", f"A {TERM}-style thing.\n"),
        _row("slash-then-identifier", f"Use {TERM}/Foo here.\n"),
        _row("sentence-period", f"Use {TERM}.\n", f"Use {LINK}.\n"),
        _row("clause-colon", f"{TERM}: does x.\n", f"{LINK}: does x.\n"),
        _row("comma", f"Use {TERM}, then.\n", f"Use {LINK}, then.\n"),
        _row(
            "dotted-term-identifier-after",
            "Use Meta.fields_class here.\n",
            term="Meta.fields",
            anchor="metafields",
        ),
        _row(
            "dotted-term-code-span-identifier-after",
            "Use `Meta.fields_class` here.\n",
            term="Meta.fields",
            anchor="metafields",
        ),
        _row(
            "dotted-term-attribute-after",
            "Read Meta.fields.get here.\n",
            term="Meta.fields",
            anchor="metafields",
        ),
        _row(
            "dotted-term-inside-longer-path",
            "Read Foo.Meta.fields here.\n",
            term="Meta.fields",
            anchor="metafields",
        ),
        _row(
            "dotted-term-sentence-end",
            "Declared via Meta.fields.\n",
            "Declared via [Meta.fields][glossary-metafields].\n",
            term="Meta.fields",
            anchor="metafields",
        ),
        _row(
            "dotted-term-code-span",
            "Use `Meta.fields` here.\n",
            "Use [`Meta.fields`][glossary-metafields] here.\n",
            term="Meta.fields",
            anchor="metafields",
        ),
        _row(
            "underscore-term",
            "Use finalize_django_types here.\n",
            "Use [finalize_django_types][glossary-finalize-django-types] here.\n",
            term="finalize_django_types",
            anchor="finalize_django_types",
        ),
        _row(
            "underscore-term-identifier-after",
            "Use finalize_django_types_now here.\n",
            term="finalize_django_types",
            anchor="finalize_django_types",
        ),
        # Prose a link lands in.
        _row("prose", f"Use {TERM} here.\n", f"Use {LINK} here.\n"),
        _row("prose-code-span", f"Use `{TERM}` here.\n", f"Use {TICKED_LINK} here.\n"),
        _row("prose-parentheses", f"Use ({TERM}) here.\n", f"Use ({LINK}) here.\n"),
        _row("prose-possessive", f"Use {TERM}'s here.\n", f"Use {LINK}'s here.\n"),
        _row("prose-emphasis", f"Use *{TERM}* here.\n", f"Use *{LINK}* here.\n"),
        _row("table-cell", f"| {TERM} | x |\n|---|---|\n", f"| {LINK} | x |\n|---|---|\n"),
        _row("list-item", f"- {TERM} is.\n", f"- {LINK} is.\n"),
        _row("blockquote", f"> Use {TERM} here.\n", f"> Use {LINK} here.\n"),
        _row(
            "lazy-continuation-indented",
            f"Use a\n        {TERM} here.\n",
            f"Use a\n        {LINK} here.\n",
        ),
        _row(
            "nested-list-continuation-indented",
            f"- a\n  - b\n        {TERM} here.\n",
            f"- a\n  - b\n        {LINK} here.\n",
        ),
        _row(
            "numbered-step-then-column-0-fence-then-prose",
            f"1. Run the checker:\n```shell\nuv run {TERM} --check\n```\n\nThen {TERM}.\n",
            f"1. Run the checker:\n```shell\nuv run {TERM} --check\n```\n\nThen {LINK}.\n",
        ),
        _row(
            "blockquote-fence-then-prose",
            f"> ```\n> x\n> ```\nUse {TERM} here.\n",
            f"> ```\n> x\n> ```\nUse {LINK} here.\n",
        ),
        _row(
            "unclosed-blockquote-fence-then-prose",
            f"> ```\n> x\nUse {TERM} here.\n",
            f"> ```\n> x\nUse {LINK} here.\n",
        ),
        _row(
            "tab-after-list-marker-then-paragraph",
            f"-\tfoo\n\n    Use {TERM} here.\n",
            f"-\tfoo\n\n    Use {LINK} here.\n",
        ),
        _row(
            "tab-then-space-after-blockquote-marker",
            f">\t {TERM} here.\n",
            f">\t {LINK} here.\n",
        ),
        _row(
            "ordered-item-tabs-in-blockquote-then-paragraph",
            f">\t10)\titem\n>\t\n>\t    x {TERM}\n",
            f">\t10)\titem\n>\t\n>\t    x {LINK}\n",
        ),
        _row(
            "list-item-html-block-then-outdented-paragraph",
            f"- item\n\n  <div>\n  x\nUse {TERM} here.\n",
            f"- item\n\n  <div>\n  x\nUse {LINK} here.\n",
        ),
        _row(
            "blockquote-html-block-then-paragraph",
            f"> <div>\n> x\nUse {TERM} here.\n",
            f"> <div>\n> x\nUse {LINK} here.\n",
        ),
        _row(
            "blockquote-marker-space-then-paragraph-indent",
            f">    {TERM} here.\n",
            f">    {LINK} here.\n",
        ),
        _row(
            "blank-line-ends-blockquote-fence",
            f"> ```\n> code\n\n> more {TERM}\n",
            f"> ```\n> code\n\n> more {LINK}\n",
        ),
        _row(
            "blank-line-ends-blockquote-html-comment",
            f"> <!--\n> x\n\n> more {TERM}\n",
            f"> <!--\n> x\n\n> more {LINK}\n",
        ),
        _row(
            "tab-after-blockquote-marker-space",
            f"> \tUse {TERM} here.\n",
            f"> \tUse {LINK} here.\n",
        ),
        _row(
            "thematic-break-after-blank",
            f"Intro.\n\n---\n\nUse {TERM} here.\n",
            f"Intro.\n\n---\n\nUse {LINK} here.\n",
        ),
        _row(
            "backtick-info-string-is-no-fence",
            f"``` a`b\n{TERM}\n",
            f"``` a`b\n{LINK}\n",
        ),
        _row(
            "tag-line-inside-paragraph",
            f"Use\n<span>\n{TERM} here.\n",
            f"Use\n<span>\n{LINK} here.\n",
        ),
        # A failing mention is passed over for the next one.
        _row(
            "code-span-then-prose",
            f"`x {TERM} y` then {TERM} here.\n",
            f"`x {TERM} y` then {LINK} here.\n",
        ),
        _row(
            "link-then-prose",
            f"[{TERM}](y.md) then {TERM} here.\n",
            f"[{TERM}](y.md) then {LINK} here.\n",
        ),
        _row(
            "linked-code-span-then-prose",
            f"See [`{TERM}`](x.md) then {TERM} here.\n",
            f"See [`{TERM}`](x.md) then {LINK} here.\n",
        ),
        _row(
            "heading-then-prose",
            f"## {TERM}\n\nUse {TERM} here.\n",
            f"## {TERM}\n\nUse {LINK} here.\n",
        ),
        _row(
            "identifier-then-prose",
            f"Use {TERM}Extra and {TERM} here.\n",
            f"Use {TERM}Extra and {LINK} here.\n",
        ),
        _row(
            "fence-closed-by-list-end-then-prose",
            f"- item\n\n  ```\n  {TERM}\n\nUse {TERM} here.\n",
            f"- item\n\n  ```\n  {TERM}\n\nUse {LINK} here.\n",
        ),
        _row(
            "html-block-then-prose",
            f"<div>\n{TERM}\n</div>\n\nUse {TERM} here.\n",
            f"<div>\n{TERM}\n</div>\n\nUse {LINK} here.\n",
        ),
        _row(
            "html-comment-block-then-prose",
            f"<!--\n{TERM}\n-->\nUse {TERM} here.\n",
            f"<!--\n{TERM}\n-->\nUse {LINK} here.\n",
        ),
        _row(
            "code-span-preferred-over-earlier-prose",
            f"Use {TERM} and `{TERM}` here.\n",
            f"Use {TERM} and {TICKED_LINK} here.\n",
        ),
    ],
)
def test_auto_link_writes_the_first_open_mention(
    tmp_path: Path,
    body: str,
    linked: str | None,
    term: str,
    anchor: str,
    docs: str,
    ext: str,
) -> None:
    spec = tmp_path / "spec-999-example-0_0_9.md"
    glossary = tmp_path / "GLOSSARY.md"
    _ = glossary.write_text(f"## {term}\n\nBody.\n", encoding="utf-8")
    before = _spec(body, docs, ext)
    _ = spec.write_text(before, encoding="utf-8")

    written, skipped = check_spec_glossary.auto_link_terms(spec, glossary, [(term, anchor)])

    after = spec.read_text(encoding="utf-8")
    if linked is None:
        assert (written, skipped, after) == ([], [term], before)
    else:
        ref_id = f"glossary-{anchor.replace('_', '-')}"
        expected = _spec(linked, f"[{ref_id}]: GLOSSARY.md#{anchor}\n{docs}", ext)
        assert (written, skipped, after) == ([term], [], expected)


def _check(tmp_path: Path, body: str, *, auto_link: bool = False) -> int:
    """Run the CLI on a one-term spec carrying ``body`` and the ``djangolistfield`` def."""
    spec = tmp_path / "spec-999-example-0_0_9.md"
    _ = spec.write_text(_spec(body, f"[{REF_ID}]: GLOSSARY.md#{ANCHOR}\n"), encoding="utf-8")
    _ = (tmp_path / "spec-999-example-0_0_9-terms.csv").write_text(
        f"term,anchor,notes\n{TERM},{ANCHOR},\n",
        encoding="utf-8",
    )
    glossary = tmp_path / "GLOSSARY.md"
    _ = glossary.write_text(f"## {TERM}\n\nBody.\n", encoding="utf-8")
    return check_spec_glossary.main(
        [
            "--spec",
            str(spec),
            "--glossary",
            str(glossary),
            *(["--auto-link"] if auto_link else []),
        ],
    )


@pytest.mark.parametrize(
    ("body", "counts"),
    [
        pytest.param(f"Use {LINK} here.\n", True, id="reference-link"),
        pytest.param(f"Use [{TERM}](GLOSSARY.md#{ANCHOR}) here.\n", True, id="inline-link"),
        pytest.param(f"## {LINK}\n\nBody.\n", True, id="heading-link"),
        pytest.param(f"{LINK}\n===\n\nBody.\n", True, id="setext-heading-link"),
        pytest.param(f"- a\n  - b\n        {LINK}\n", True, id="list-continuation-link"),
        pytest.param(f"-\tfoo\n\n    see {LINK}\n", True, id="tab-after-list-marker-link"),
        pytest.param(
            f"- item\n\n  <div>\n  x\nsee {LINK}\n",
            True,
            id="link-after-list-item-html-block",
        ),
        pytest.param(f"Use `{LINK}` here.\n", False, id="reference-in-code-span"),
        pytest.param(
            f"Use `[{TERM}](GLOSSARY.md#{ANCHOR})` here.\n",
            False,
            id="inline-in-code-span",
        ),
        pytest.param(f"```\n{LINK}\n```\n", False, id="reference-in-fence"),
        pytest.param(f"para\n\n    {LINK}\n", False, id="reference-in-indented-code"),
        pytest.param(f"<!--\n{LINK}\n-->\n", False, id="reference-in-html-comment"),
        pytest.param(f'Use <a title="{LINK}">x</a> here.\n', False, id="reference-in-raw-html"),
        pytest.param(f"Use [{TERM}][glossary-other] here.\n", False, id="undefined-reference"),
    ],
)
def test_a_link_counts_only_where_it_renders(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    body: str,
    *,
    counts: bool,
) -> None:
    assert _check(tmp_path, body) == (0 if counts else 1)
    out = capsys.readouterr().out
    assert ("OK: 1 terms" in out) is counts
    assert (f"{TERM} (anchor: {ANCHOR})" in out) is not counts


def test_auto_link_cli_links_an_open_mention(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _check(tmp_path, f"## {TERM}\n\nUse `{TERM}` here.\n", auto_link=True) == 0
    out = capsys.readouterr().out
    assert f"auto-link: inserted 1 link(s) into {tmp_path / 'spec-999-example-0_0_9.md'}:" in out
    assert f"  + {TERM}" in out
    assert "OK: 1 terms" in out
    text = (tmp_path / "spec-999-example-0_0_9.md").read_text(encoding="utf-8")
    assert text.startswith(f"## {TERM}\n\nUse {TICKED_LINK} here.\n")


def test_auto_link_cli_reports_a_term_with_no_open_mention(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    body = f"## {TERM}\n\nCall `{TERM}()`, see <https://example.com/{TERM}>.\n"

    assert _check(tmp_path, body, auto_link=True) == 1
    out = capsys.readouterr().out
    assert "auto-link: 1 term(s) had no non-code, non-link, non-heading mention:" in out
    assert f"  - {TERM}\n" in out
    assert f"{TERM} (anchor: {ANCHOR}) - add at least one link" in out
    assert (tmp_path / "spec-999-example-0_0_9.md").read_text(encoding="utf-8") == _spec(
        body,
        f"[{REF_ID}]: GLOSSARY.md#{ANCHOR}\n",
    )
