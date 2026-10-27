"""Tests for KANBAN markdown glossary inlining: existing links and the term boundary.

Repo tooling: these rows pin ``scripts/build_kanban_md.py::GlossaryInliner``,
which runs at render time against an in-process glossary snapshot. A live
``/graphql/`` request has no wire shape for the markdown link a rendered card
carries, so none of these rows can move. There is no live sibling in
``examples/fakeshop/test_query/``.
"""

import pytest

from scripts.build_kanban_md import GLOSSARY_MD_PATH, GlossaryInliner

LINKED = f"[`DjangoListField`]({GLOSSARY_MD_PATH}#djangolistfield)"
BARE_LINKED = f"[DjangoListField]({GLOSSARY_MD_PATH}#djangolistfield)"
# cmark and markdown-it keep a link destination nested 32 parens deep, not 33.
DEEPEST = 32
TOO_DEEP = 33


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(
            "See [`DjangoListField`][list-field].",
            "See [`DjangoListField`][list-field].",
            id="reference-link-label",
        ),
        pytest.param(
            "See [`DjangoListField`][].",
            "See [`DjangoListField`][].",
            id="collapsed-link-label",
        ),
        pytest.param(
            "See [DjangoListField][list-field].",
            "See [DjangoListField][list-field].",
            id="reference-link-bare-title-label",
        ),
        pytest.param(
            "See [`DjangoListField`](docs/README.md).",
            "See [`DjangoListField`](docs/README.md).",
            id="inline-link-label",
        ),
        pytest.param(
            "See [the [DjangoListField] API][field].",
            "See [the [DjangoListField] API][field].",
            id="nested-brackets-in-reference-text",
        ),
        pytest.param(
            "See [the [DjangoListField] API](docs/x.md).",
            "See [the [DjangoListField] API](docs/x.md).",
            id="nested-brackets-in-inline-text",
        ),
        pytest.param(
            r"See [a \] DjangoListField b](docs/x.md).",
            r"See [a \] DjangoListField b](docs/x.md).",
            id="escaped-close-in-link-text",
        ),
        pytest.param(
            "See [a `]` DjangoListField b](docs/x.md).",
            "See [a `]` DjangoListField b](docs/x.md).",
            id="code-span-bracket-in-link-text",
        ),
        pytest.param(
            "See [DjangoListField] today.",
            "See [DjangoListField] today.",
            id="shortcut-reference",
        ),
        pytest.param(
            'See [the API](docs/x.md "see (a) DjangoListField").',
            'See [the API](docs/x.md "see (a) DjangoListField").',
            id="parenthesised-destination",
        ),
        pytest.param(
            'See [the API](docs/x.md "DjangoListField ((a))").',
            'See [the API](docs/x.md "DjangoListField ((a))").',
            id="title-with-nested-parens",
        ),
        pytest.param(
            'See [the API](docs/x(a(b)).md "DjangoListField").',
            'See [the API](docs/x(a(b)).md "DjangoListField").',
            id="destination-with-nested-parens",
        ),
        pytest.param(
            'See [the API](<docs/x (y.md> "DjangoListField").',
            'See [the API](<docs/x (y.md> "DjangoListField").',
            id="angle-destination-unbalanced-paren",
        ),
        pytest.param(
            "See [the API](docs/x.md 'DjangoListField [b] ) c').",
            "See [the API](docs/x.md 'DjangoListField [b] ) c').",
            id="single-quoted-title-with-close-paren",
        ),
        pytest.param(
            'See [the API](docs/x.md "DjangoListField `q") and `z`.',
            'See [the API](docs/x.md "DjangoListField `q") and `z`.',
            id="title-with-lone-backtick",
        ),
        pytest.param(
            'See [the API](docs/x.md "t [ (") then DjangoListField b] later.',
            f'See [the API](docs/x.md "t [ (") then {BARE_LINKED} b] later.',
            id="live-text-after-title-with-brackets",
        ),
        pytest.param(
            'See [the API](docs/x(y.md "DjangoListField") now.',
            f'See [the API](docs/x(y.md "{BARE_LINKED}") now.',
            id="unbalanced-destination-is-not-a-link",
        ),
        pytest.param(
            "[DEFERRED - DjangoListField ships]",
            "[DEFERRED - DjangoListField ships]",
            id="literal-bracket-run",
        ),
        pytest.param(
            "See <https://example.com/?q=DjangoListField> then DjangoListField now.",
            f"See <https://example.com/?q=DjangoListField> then {BARE_LINKED} now.",
            id="uri-autolink",
        ),
        pytest.param(
            "Mail <DjangoListField@example.com> then DjangoListField now.",
            f"Mail <DjangoListField@example.com> then {BARE_LINKED} now.",
            id="email-autolink",
        ),
        pytest.param(
            "See <irc://example.com/?q=DjangoListField> then DjangoListField now.",
            f"See <irc://example.com/?q=DjangoListField> then {BARE_LINKED} now.",
            id="uri-autolink-any-scheme",
        ),
        pytest.param(
            "Mail <DjangoListField!x@example.com> then DjangoListField now.",
            f"Mail <DjangoListField!x@example.com> then {BARE_LINKED} now.",
            id="email-autolink-full-local-part",
        ),
        pytest.param(
            'A <span title="DjangoListField">x</span> then DjangoListField now.',
            f'A <span title="DjangoListField">x</span> then {BARE_LINKED} now.',
            id="raw-html-attribute",
        ),
        pytest.param(
            "Gates check_<DjangoListField>_permission then DjangoListField now.",
            f"Gates check_<DjangoListField>_permission then {BARE_LINKED} now.",
            id="raw-html-tag-placeholder",
        ),
        pytest.param(
            "A <!-- DjangoListField --> then DjangoListField now.",
            f"A <!-- DjangoListField --> then {BARE_LINKED} now.",
            id="raw-html-comment",
        ),
        pytest.param(
            "A <!--> DjangoListField --> then DjangoListField now.",
            f"A <!--> {BARE_LINKED} --> then DjangoListField now.",
            id="raw-html-empty-comment",
        ),
        pytest.param(
            "A <!---> DjangoListField --> then DjangoListField now.",
            f"A <!---> {BARE_LINKED} --> then DjangoListField now.",
            id="raw-html-empty-comment-three-dashes",
        ),
        pytest.param(
            'A <x title="DjangoListField"/> then DjangoListField now.',
            f'A <x title="DjangoListField"/> then {BARE_LINKED} now.',
            id="raw-html-self-closing-tag",
        ),
        pytest.param(
            'A <x title="DjangoListField" /> then DjangoListField now.',
            f'A <x title="DjangoListField" /> then {BARE_LINKED} now.',
            id="raw-html-self-closing-tag-spaced",
        ),
        pytest.param(
            "A <?x DjangoListField ?> then DjangoListField now.",
            f"A <?x DjangoListField ?> then {BARE_LINKED} now.",
            id="raw-html-processing-instruction",
        ),
        pytest.param(
            "A <?> DjangoListField ?> then DjangoListField now.",
            f"A <?> DjangoListField ?> then {BARE_LINKED} now.",
            id="raw-html-closer-after-the-opener",
        ),
        pytest.param(
            "A <?>DjangoListField?> then DjangoListField now.",
            f"A <?>DjangoListField?> then {BARE_LINKED} now.",
            id="raw-html-closer-after-the-opener-unspaced",
        ),
        pytest.param(
            "A <!X DjangoListField> then DjangoListField now.",
            f"A <!X DjangoListField> then {BARE_LINKED} now.",
            id="raw-html-declaration",
        ),
        pytest.param(
            "A <![CDATA[ x ]] DjangoListField ]]> then DjangoListField now.",
            f"A <![CDATA[ x ]] DjangoListField ]]> then {BARE_LINKED} now.",
            id="raw-html-cdata",
        ),
        pytest.param(
            "A <b>DjangoListField</b> now.",
            f"A <b>{BARE_LINKED}</b> now.",
            id="prose-between-tags",
        ),
        pytest.param(
            "Ship ``DjangoListField`` then DjangoListField now.",
            f"Ship ``DjangoListField`` then {BARE_LINKED} now.",
            id="double-backtick-span",
        ),
        pytest.param(
            "Ship ``a ` b DjangoListField`` then DjangoListField now.",
            f"Ship ``a ` b DjangoListField`` then {BARE_LINKED} now.",
            id="double-backtick-span-holding-a-tick",
        ),
        pytest.param(
            "Ship ` a `` DjangoListField b ` then DjangoListField now.",
            f"Ship ` a `` DjangoListField b ` then {BARE_LINKED} now.",
            id="code-span-holding-a-double-tick",
        ),
        pytest.param(
            "Ship `a\nDjangoListField b` then DjangoListField now.",
            f"Ship `a\nDjangoListField b` then {BARE_LINKED} now.",
            id="code-span-across-a-newline",
        ),
        pytest.param(
            "Use ` here.\n\nThen `a DjangoListField b` then DjangoListField now.",
            f"Use ` here.\n\nThen `a DjangoListField b` then {BARE_LINKED} now.",
            id="code-span-never-crosses-a-blank-line",
        ),
        pytest.param(
            "Use ` here.\r\n\r\nThen `a DjangoListField b` then DjangoListField now.",
            f"Use ` here.\r\n\r\nThen `a DjangoListField b` then {BARE_LINKED} now.",
            id="code-span-never-crosses-a-crlf-blank-line",
        ),
        pytest.param(
            "Use ` here.\n \t\nThen `a DjangoListField b` then DjangoListField now.",
            f"Use ` here.\n \t\nThen `a DjangoListField b` then {BARE_LINKED} now.",
            id="code-span-never-crosses-a-whitespace-blank-line",
        ),
        pytest.param(
            "See [a\n\nb DjangoListField c] now.",
            f"See [a\n\nb {BARE_LINKED} c] now.",
            id="link-text-never-crosses-a-blank-line",
        ),
        pytest.param(
            'A <span\n\ntitle="DjangoListField">x</span> now.',
            f'A <span\n\ntitle="{BARE_LINKED}">x</span> now.',
            id="raw-html-never-crosses-a-blank-line",
        ),
        pytest.param(
            'A <span\r\n\r\ntitle="DjangoListField">x</span> now.',
            f'A <span\r\n\r\ntitle="{BARE_LINKED}">x</span> now.',
            id="raw-html-never-crosses-a-crlf-blank-line",
        ),
        pytest.param(
            'A <span\n  \ntitle="DjangoListField">x</span> now.',
            f'A <span\n  \ntitle="{BARE_LINKED}">x</span> now.',
            id="raw-html-never-crosses-a-whitespace-blank-line",
        ),
        pytest.param(
            "Ship ``DjangoListField` next.",
            f"Ship ``{BARE_LINKED}` next.",
            id="unmatched-backtick-runs-stay-whole",
        ),
        pytest.param(
            "Ship `DjangoListField`` next.",
            f"Ship `{BARE_LINKED}`` next.",
            id="unmatched-backtick-runs-stay-whole-closing",
        ),
        pytest.param(
            r"See \`DjangoListField` now.",
            rf"See \`{BARE_LINKED}` now.",
            id="escaped-backtick-stays-whole",
        ),
        pytest.param(
            r"Ship \`DjangoListField` then DjangoListField now.",
            rf"Ship \`{BARE_LINKED}` then DjangoListField now.",
            id="escaped-backtick-stays-whole-before-prose",
        ),
        pytest.param(
            'See [a](x "`") `DjangoListField` now.',
            f'See [a](x "`") {LINKED} now.',
            id="backtick-in-link-title-opens-no-span",
        ),
        pytest.param(
            "See https://example.com/?q=DjangoListField then DjangoListField now.",
            f"See https://example.com/?q=DjangoListField then {BARE_LINKED} now.",
            id="bare-url",
        ),
        pytest.param(
            "See <https://example.com/?q=DjangoListField then DjangoListField now.",
            f"See <https://example.com/?q=DjangoListField then {BARE_LINKED} now.",
            id="bare-url-after-unclosed-angle",
        ),
        pytest.param(
            "See www.example.com/?q=DjangoListField then DjangoListField now.",
            f"See www.example.com/?q=DjangoListField then {BARE_LINKED} now.",
            id="bare-www-url",
        ),
        pytest.param(
            "Mail DjangoListField@example.com then DjangoListField now.",
            f"Mail DjangoListField@example.com then {BARE_LINKED} now.",
            id="bare-email",
        ),
        pytest.param(
            "See `https://example.com/?q=`DjangoListField now.",
            f"See `https://example.com/?q=`{BARE_LINKED} now.",
            id="url-in-code-span-ends-with-it",
        ),
        pytest.param(
            "See [a](https://example.com/x)DjangoListField now.",
            f"See [a](https://example.com/x){BARE_LINKED} now.",
            id="url-in-link-destination-ends-with-it",
        ),
        pytest.param(
            "Go [see <https://e.com/a]b> DjangoListField x](d.md) then DjangoListField now.",
            f"Go [see <https://e.com/a]b> DjangoListField x](d.md) then {BARE_LINKED} now.",
            id="autolink-bracket-closes-no-link-text",
        ),
        pytest.param(
            'Go [see <i title="a]b"> DjangoListField</i> x](d.md) then DjangoListField now.',
            f'Go [see <i title="a]b"> DjangoListField</i> x](d.md) then {BARE_LINKED} now.',
            id="attribute-bracket-closes-no-link-text",
        ),
        pytest.param(
            "<https://e.com/a[b> then DjangoListField] stray.",
            f"<https://e.com/a[b> then {BARE_LINKED}] stray.",
            id="autolink-bracket-opens-no-link-text",
        ),
        pytest.param(
            "Ship `DjangoListField` next.",
            f"Ship {LINKED} next.",
            id="plain-mention",
        ),
        pytest.param(
            r"See \[DjangoListField\](docs/x.md).",
            rf"See \[{BARE_LINKED}\](docs/x.md).",
            id="escaped-brackets-are-literal",
        ),
        pytest.param(
            f"See [a]({'(' * DEEPEST}DjangoListField{')' * DEEPEST}) then DjangoListField now.",
            f"See [a]({'(' * DEEPEST}DjangoListField{')' * DEEPEST}) then {BARE_LINKED} now.",
            id="destination-at-max-nesting-stays-one-link",
        ),
        pytest.param(
            f"See [a]({'(' * TOO_DEEP}DjangoListField{')' * TOO_DEEP}) then DjangoListField now.",
            f"See [a]({'(' * TOO_DEEP}{BARE_LINKED}{')' * TOO_DEEP}) then DjangoListField now.",
            id="destination-past-max-nesting-protects-only-label",
        ),
    ],
)
def test_inliner_leaves_existing_links_intact(text: str, expected: str) -> None:
    """A term inside a bracket group, link, code span, autolink, raw HTML or bare URL stays put.

    A plain mention is linked, including the next one after a mention a construct holds.
    """
    inliner = GlossaryInliner([{"title": "`DjangoListField`", "anchor": "djangolistfield"}])
    assert inliner.inline(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(
            "Ship DjangoListField.",
            f"Ship {BARE_LINKED}.",
            id="sentence-final-period",
        ),
        pytest.param(
            "Ship `DjangoListField`.",
            f"Ship {LINKED}.",
            id="sentence-final-code-span",
        ),
        pytest.param(
            "Ship DjangoListField: the list field.",
            f"Ship {BARE_LINKED}: the list field.",
            id="clause-colon",
        ),
        pytest.param(
            "Ship DjangoListField, then the rest.",
            f"Ship {BARE_LINKED}, then the rest.",
            id="clause-comma",
        ),
        pytest.param(
            "Call DjangoListField.get then DjangoListField now.",
            f"Call DjangoListField.get then {BARE_LINKED} now.",
            id="dotted-continuation",
        ),
        pytest.param(
            "A DjangoListField-style field then DjangoListField now.",
            f"A DjangoListField-style field then {BARE_LINKED} now.",
            id="hyphen-compound",
        ),
        pytest.param(
            "See DjangoListField/x then DjangoListField now.",
            f"See DjangoListField/x then {BARE_LINKED} now.",
            id="path-continuation",
        ),
        pytest.param(
            "Ship DjangoListFieldSet then DjangoListField now.",
            f"Ship DjangoListFieldSet then {BARE_LINKED} now.",
            id="identifier-suffix",
        ),
        pytest.param(
            "Ship DjangoListField_x then DjangoListField now.",
            f"Ship DjangoListField_x then {BARE_LINKED} now.",
            id="underscore-suffix",
        ),
        pytest.param(
            "Ship DjangoListField-2 then DjangoListField now.",
            f"Ship DjangoListField-2 then {BARE_LINKED} now.",
            id="hyphen-then-digit",
        ),
        pytest.param(
            "Ship DjangoListField.5 then DjangoListField now.",
            f"Ship DjangoListField.5 then {BARE_LINKED} now.",
            id="period-then-digit",
        ),
        pytest.param(
            "Ship DjangoListField._x then DjangoListField now.",
            f"Ship DjangoListField._x then {BARE_LINKED} now.",
            id="period-then-underscore",
        ),
        pytest.param(
            "Ship DjangoListField--next then DjangoListField now.",
            f"Ship DjangoListField--next then {BARE_LINKED} now.",
            id="punctuation-run-then-word",
        ),
        pytest.param(
            "Ship DjangoListField. Then DjangoListField again.",
            f"Ship {BARE_LINKED}. Then DjangoListField again.",
            id="sentence-final-first-mention-takes-the-link",
        ),
    ],
)
def test_inliner_links_a_term_at_a_prose_boundary(text: str, expected: str) -> None:
    """A term followed by punctuation that ends its token is linked; one opening a path is not.

    A ``.``, ``:``, ``/`` or ``-`` run after the term bars the link only when an identifier
    character follows the run, so the first mention ending a sentence or clause takes the link.
    """
    inliner = GlossaryInliner([{"title": "`DjangoListField`", "anchor": "djangolistfield"}])
    assert inliner.inline(text) == expected
