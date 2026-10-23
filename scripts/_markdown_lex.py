"""CommonMark lexing for the scripts that write glossary links into markdown.

Stdlib only, so ``check_spec_glossary.py`` (which must not import Django) and
``build_kanban_md.py`` (which does, through ``_kanban_lib``) share one lexer. Two layers:

- ``_protected_regions`` lexes the inline constructs (CommonMark 6.1-6.6 plus GitHub's bare
  autolinks) into the regions a term link may not overlap (``Regions.opaque``) or may take
  only whole (``Regions.atoms``).
- ``block_regions`` finds the block constructs a term link may not land in at all (CommonMark
  4.2-4.7): ATX and setext headings, link reference definitions (label, destination and
  title), fenced code (backtick or tilde, inside list items and block quotes too), indented
  code and HTML blocks. ``mask_blocks`` blanks them, keeping every offset and line break, so
  the inline lexer reads each masked line as a paragraph break.

``first_open_match`` is the search a writer runs over the lexed text: the first match that
overlaps no opaque region and cuts no atom, retried past every mention a region holds. The
term boundaries pair a standalone-token rule before the term with one of two rules after it.
"""

from __future__ import annotations

import re
from typing import NamedTuple

# A glossary term is inlined only as a standalone token: not glued to an identifier
# character, a dotted/``::``-qualified path, or a path separator on either side.
TERM_BOUNDARY_BEFORE = r"(?<![A-Za-z0-9_.:/\-])"
TERM_BOUNDARY_AFTER = r"(?![A-Za-z0-9_.:/\-])"
# The prose variant of ``TERM_BOUNDARY_AFTER``: a ``.``, ``:``, ``/`` or ``-`` run after the
# term bars it only when an identifier character follows the run, so a term may end a
# sentence or open a clause (``... via Meta.fields.``) but never starts a longer path
# (``Meta.fields.get``, ``DjangoType-style``).
PROSE_TERM_BOUNDARY_AFTER = r"(?![A-Za-z0-9_])(?![.:/\-]+[A-Za-z0-9_])"
# Regions a term match may not overlap at all: a ``#"substring"`` citation pinpoint (it
# must stay byte-exact), any balanced ``[...]`` group with its trailing
# ``(destination "title")`` or ``[label]`` (an existing link of any shape keeps its text),
# a URI or email autolink and raw HTML (CommonMark 6.5, 6.6: a link written there lands in
# an href, an attribute or hidden markup), and the URL, ``www.`` or email GitHub links
# bare. Regions a match takes whole or not at all: a code span, an unmatched backtick
# run and a backslash escape (a term is linked when it IS the span, never inside a longer
# literal, and never so it splits a run or an escape). ``_protected_regions`` lexes them
# left to right the way CommonMark does before it pairs link brackets.
PINPOINT_RE = re.compile(r"#\"[^\"\n]*\"")
ESCAPE_RE = re.compile(r"\\[\s\S]")
BACKTICK_RUN_RE = re.compile(r"`+")
INLINE_TOKEN_RE = re.compile(r"\\[\s\S]?|`+|[<\[\]]")
# A paragraph: inline constructs never cross a blank line (``\r\n`` endings included).
PARAGRAPH_RE = re.compile(r"(?:[^\n]|\n(?![ \t\r]*(?:\n|$)))+")
AUTOLINK_RE = re.compile(
    r"<[A-Za-z][A-Za-z0-9+.\-]{1,31}:[^<>\x00-\x20]*>"
    r"|<[A-Za-z0-9.!#$%&'*+/=?^_`{|}~\-]+@[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?)*>",
)
HTML_ATTRIBUTE = (
    r"\s+[A-Za-z_:][A-Za-z0-9_.:\-]*(?:\s*=\s*(?:[^\"'=<>`\x00-\x20]+|'[^']*'|\"[^\"]*\"))?"
)
# Raw HTML (CommonMark 6.6): an open or closing tag or an empty comment by regex; a
# comment, processing instruction, CDATA section or declaration runs from its opener to
# the first closer after it (``HTML_DELIMITED``), found by ``_raw_html_end``.
HTML_TAG_RE = re.compile(
    rf"<[A-Za-z][A-Za-z0-9\-]*(?:{HTML_ATTRIBUTE})*\s*/?>|</[A-Za-z][A-Za-z0-9\-]*\s*>|<!---?>",
)
HTML_DELIMITED = (
    (re.compile(r"<!--"), "-->"),
    (re.compile(r"<\?"), "?>"),
    (re.compile(r"<!\[CDATA\["), "]]>"),
    (re.compile(r"<![A-Za-z]"), ">"),
)
# GitHub's extended autolinks, over-matched so a link GitHub draws is always covered: any
# start character (GitHub links ``<https://...`` with no closing ``>``), no trailing trim.
GFM_AUTOLINK_RE = re.compile(
    r"(?:(?:https?|ftp)://|www\.)[^\s<]*"
    r"|(?<![\w.+\-])[\w.+\-]+@[\w.\-]+",
)
LINK_LABEL_RE = re.compile(r"\[[^\[\]]*\]")
LINK_ANGLE_DESTINATION_RE = re.compile(r"<[^<>\n]*>")
LINK_TITLE_RE = re.compile(r"\"[^\"]*\"|'[^']*'|\([^()]*\)")
# Deepest paren nesting a whitespace-free link destination may carry, as cmark and
# markdown-it do (both fail the link past 32 levels).
LINK_DESTINATION_MAX_NESTING = 32

# Block starts (CommonMark 4, 5), each matched on a line's content after its block-quote
# markers, list markers and indentation. A backtick fence's info string carries no backtick.
LIST_MARKER_RE = re.compile(r"(?:[-+*]|(?P<number>\d{1,9})[.)])(?=[ \t]|$)")
ATX_HEADING_RE = re.compile(r"#{1,6}(?:[ \t]|$)")
SETEXT_UNDERLINE_RE = re.compile(r"(?:=+|-+)[ \t\r]*$")
CODE_FENCE_RE = re.compile(r"(?:`{3,}(?=[^`]*$)|~{3,})")
CODE_FENCE_CLOSE_RE = re.compile(r"(?:`{3,}|~{3,})[ \t\r]*$")
LINK_DEFINITION_RE = re.compile(r"\[(?:\\[\s\S]|[^\\\[\]])+\]:")
LINK_DEFINITION_TITLE_RE = re.compile(r"(?:\"[^\"]*\"|'[^']*'|\([^()]*\))[ \t\r]*$")
HTML_BLOCK_NAMES = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|"
    "details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|"
    "h1|h2|h3|h4|h5|h6|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|"
    "noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|"
    "thead|title|tr|track|ul"
)
# HTML block starts (CommonMark 4.6 kinds 1-6) with the closer that ends each, ``None``
# for a block a blank line ends. Kind 7, a complete tag alone on its line
# (``HTML_BLOCK_TAG_LINE_RE``), also ends at a blank line but cannot interrupt a paragraph.
HTML_BLOCK_STARTS: tuple[tuple[re.Pattern[str], re.Pattern[str] | None], ...] = (
    (
        re.compile(r"<(?:script|pre|style|textarea)(?:[ \t>]|$)", re.IGNORECASE),
        re.compile(r"</(?:script|pre|style|textarea)>", re.IGNORECASE),
    ),
    (re.compile(r"<!--"), re.compile(r"-->")),
    (re.compile(r"<\?"), re.compile(r"\?>")),
    (re.compile(r"<![A-Za-z]"), re.compile(r">")),
    (re.compile(r"<!\[CDATA\["), re.compile(r"\]\]>")),
    (re.compile(rf"</?(?:{HTML_BLOCK_NAMES})(?:[ \t>]|/>|$)", re.IGNORECASE), None),
)
HTML_BLOCK_TAG_LINE_RE = re.compile(
    rf"(?:<[A-Za-z][A-Za-z0-9\-]*(?:{HTML_ATTRIBUTE})*\s*/?>|</[A-Za-z][A-Za-z0-9\-]*\s*>)"
    r"[ \t\r]*$",
)
# Columns a tab advances indentation to the next multiple of (CommonMark 2.2).
TAB_STOP = 4
# Indentation from which a line that opens no other block is indented code (CommonMark 4.4).
CODE_INDENT = 4

Spans = list[tuple[int, int]]


class Regions(NamedTuple):
    """Where a glossary term match may land in one text (the comment above ``PINPOINT_RE``)."""

    opaque: Spans
    atoms: Spans


def _skip_space(raw: str, j: int) -> int:
    """Return the first index at or after ``j`` that is not whitespace."""
    while j < len(raw) and raw[j].isspace():
        j += 1
    return j


def _link_tail_end(raw: str, i: int) -> int | None:
    """End of the ``[label]`` or ``(destination "title")`` link tail at ``raw[i]``, else None.

    ``raw`` has only its backslash escapes masked. A destination is ``<...>`` or a
    whitespace-free run with balanced parens (possibly empty) nested at most
    ``LINK_DESTINATION_MAX_NESTING`` deep, the limit cmark and markdown-it apply; a title
    is ``"..."``, ``'...'`` or ``(...)`` after whitespace. The limit also cuts short the
    scan of an unclosed destination, which each later ``](`` in the same run starts
    again, so many unclosed tails lex in linear time.
    """
    if raw.startswith("[", i):
        label = LINK_LABEL_RE.match(raw, i)
        return label.end() if label else None
    if not raw.startswith("(", i):
        return None
    j = _skip_space(raw, i + 1)
    if raw.startswith("<", j):
        angle = LINK_ANGLE_DESTINATION_RE.match(raw, j)
        if angle is None:
            return None
        j = angle.end()
    else:
        depth = 0
        while j < len(raw) and not raw[j].isspace() and (depth or raw[j] != ")"):
            depth += (raw[j] == "(") - (raw[j] == ")")
            if depth > LINK_DESTINATION_MAX_NESTING:
                return None
            j += 1
        if depth:
            return None
    k = _skip_space(raw, j)
    title = LINK_TITLE_RE.match(raw, k) if k > j else None
    if title:
        k = _skip_space(raw, title.end())
    return k + 1 if raw.startswith(")", k) else None


def _closing_run(
    text: str,
    start: int,
    end: int,
    width: int,
) -> int | None:
    """End of the first backtick run exactly ``width`` long in ``text[start:end]``, else None."""
    for run in BACKTICK_RUN_RE.finditer(text, start, end):
        if run.end() - run.start() == width:
            return run.end()
    return None


def _raw_html_end(
    text: str,
    start: int,
    end: int,
    closers: dict[str, int],
) -> int | None:
    """End of the raw HTML at ``text[start]`` inside ``text[:end]``, else None.

    ``closers`` maps each closer to its last found index in the paragraph (-1: none
    left). The scan moves left to right, so a found closer past the opener is reused and
    a missing one stays missing: an unclosed opener costs one search per paragraph, not
    one per opener.
    """
    tag = HTML_TAG_RE.match(text, start, end)
    if tag:
        return tag.end()
    for opener, closer in HTML_DELIMITED:
        head = opener.match(text, start, end)
        if head is None:
            continue
        hit = closers.get(closer)
        if hit is None or 0 <= hit < head.end():
            hit = text.find(closer, head.end(), end)
            closers[closer] = hit
        return hit + len(closer) if hit >= 0 else None
    return None


def _protected_regions(text: str) -> Regions:
    """Lex ``text`` into the regions a term match must respect, CommonMark-first.

    One left-to-right pass per paragraph, leftmost construct first (CommonMark 6.1-6.6):
    a backslash escape, a backtick run (a code span through the next run of equal length,
    else the run alone is literal), a URI or email autolink or raw HTML at ``<``, then
    bracket pairing over what is left, each ``]`` taking its link tail scanned whole with
    only escapes masked. GitHub's bare autolinks are found last, in text no earlier
    region covers.
    """
    opaque = [m.span() for m in PINPOINT_RE.finditer(text)]
    atoms: Spans = []
    code: Spans = []
    raw = ESCAPE_RE.sub(lambda m: "." * len(m.group()), text)
    for paragraph in PARAGRAPH_RE.finditer(text):
        end = paragraph.end()
        openers: list[int] = []
        closers: dict[str, int] = {}
        token = INLINE_TOKEN_RE.search(text, paragraph.start(), end)
        while token is not None:
            start, nxt = token.span()
            mark = token.group()
            if mark[0] == "\\":
                atoms.append((start, nxt))
            elif mark[0] == "`":
                close = _closing_run(text, nxt, end, len(mark))
                if close is None:
                    atoms.append((start, nxt))
                else:
                    code.append((start, close))
                    nxt = close
            elif mark == "<":
                autolink = AUTOLINK_RE.match(text, start, end)
                tag_end = autolink.end() if autolink else _raw_html_end(text, start, end, closers)
                if tag_end is not None:
                    nxt = tag_end
                    opaque.append((start, nxt))
            elif mark == "[":
                openers.append(start)
            elif openers:
                nxt = _link_tail_end(raw, nxt) or nxt
                opaque.append((openers.pop(), nxt))
            token = INLINE_TOKEN_RE.search(text, nxt, end)
    bare = list(text)
    for lo, hi in opaque + code:
        bare[lo:hi] = " " * (hi - lo)
    opaque += [m.span() for m in GFM_AUTOLINK_RE.finditer("".join(bare))]
    return Regions(opaque, atoms + code)


def first_open_match(
    pattern: re.Pattern[str],
    text: str,
    regions: Regions,
) -> re.Match[str] | None:
    """First match, at any start, that overlaps no opaque region and cuts no atom."""
    match = pattern.search(text)
    while match is not None:
        lo, hi = match.span()
        overlaps = any(a < hi and lo < b for a, b in regions.opaque)
        cuts = any(a < hi and lo < b and not (lo <= a and b <= hi) for a, b in regions.atoms)
        if not (overlaps or cuts):
            return match
        match = pattern.search(text, lo + 1)
    return None


class _Fence(NamedTuple):
    """An open fenced code block: its marker, the container column and block-quote depth."""

    char: str
    width: int
    base: int
    quote: int


class _HtmlBlock(NamedTuple):
    """An open HTML block: what ends it (``None``: a blank line), the container column and depth."""

    closer: re.Pattern[str] | None
    base: int
    quote: int


def _indent(line: str, i: int, column: int = 0) -> tuple[int, int]:
    """Return ``(width, index)`` of the whitespace run at ``line[i]``, which sits at ``column``.

    A tab advances to the next multiple of ``TAB_STOP`` counted from the line start, so the
    run's width depends on the column it starts at.
    """
    start = column
    while i < len(line) and line[i] in " \t":
        column = column + TAB_STOP - column % TAB_STOP if line[i] == "\t" else column + 1
        i += 1
    return column - start, i


def _quote_markers(line: str) -> tuple[int, int, int, int]:
    """Read the block-quote markers opening ``line`` (CommonMark 5.1).

    A marker is ``>`` indented under ``CODE_INDENT`` columns; the space after it belongs to
    it, and a tab after it gives it one column, the rest staying indentation (a nested
    ``>`` may follow that rest). Returns ``(depth, index, column, credit)``: the index and
    column past the last marker, and the column (0 or 1) a tab there still owes it.
    """
    depth, i, column, credit = 0, 0, 0, 0
    while True:
        width, j = _indent(line, i, column)
        if width - credit >= CODE_INDENT or not line.startswith(">", j):
            return depth, i, column, credit
        depth, i, column, credit = depth + 1, j + 1, column + width + 1, 0
        if line.startswith(" ", i):
            i, column = i + 1, column + 1
        elif line.startswith("\t", i):
            credit = 1


def _html_block(content: str, *, interrupts: bool) -> tuple[bool, re.Pattern[str] | None] | None:
    """Return ``(closed, closer)`` for the HTML block ``content`` opens, else None.

    ``closed`` says the block also ends on this line; ``closer`` is what ends it later
    (``None``: a blank line). ``interrupts`` says a paragraph is open, which a complete
    tag alone on its line (kind 7) cannot interrupt.
    """
    for opener, closer in HTML_BLOCK_STARTS:
        head = opener.match(content)
        if head is not None:
            return closer is not None and bool(closer.search(content, head.end())), closer
    if not interrupts and HTML_BLOCK_TAG_LINE_RE.match(content):
        return False, None
    return None


def _open_list_items(
    line: str,
    at: int,
    indent: int,
    lists: list[int],
    *,
    origin: int,
    in_paragraph: bool,
) -> tuple[int, int, bool]:
    """Open the list items whose markers start at ``line[at]`` (indented ``indent`` columns).

    ``origin`` is the line column ``indent`` counts from, so a tab after a marker is
    measured from the marker's real column.

    Each item pops the open items at its column or deeper and pushes its content column
    on ``lists``: past the marker and the spaces after it, or one space past the marker
    when nothing follows it or more than ``CODE_INDENT`` spaces do (the rest is then
    indented code). An ordered item numbered other than 1 cannot interrupt a paragraph.
    Returns the ``(indent, at)`` of what follows the last marker and whether one opened.
    """
    base = lists[-1] if lists else 0
    opened = False
    while indent - base < CODE_INDENT and (item := LIST_MARKER_RE.match(line, at)) is not None:
        number = item.group("number")
        if not opened and in_paragraph and number is not None and int(number) != 1:
            break
        column = indent + item.end() - at
        gap, at = _indent(line, item.end(), origin + column)
        empty = at >= len(line.rstrip("\r"))
        while lists and lists[-1] > indent:
            _ = lists.pop()
        base = column + (1 if empty or gap > CODE_INDENT else gap)
        lists.append(base)
        indent, opened = column + gap, True
    return indent, at, opened


def block_regions(text: str, *, headings: bool = True) -> Spans:
    """Spans of the block constructs no term link may land in, CommonMark 4.2-4.7.

    One pass over the lines. Each line drops its block-quote markers, then the list
    markers that open items on it (a list item's content column is the container base a
    later line's indentation is read against, until a line outside a paragraph is
    indented less); what is left may open indented code (indented ``CODE_INDENT`` columns
    past the base, never inside a paragraph), underline the open paragraph as a setext
    heading, or open an ATX heading, a code fence (closed by a matching fence or by its
    container closing, else running to the end of the text), an HTML block (ended by its
    closer or a blank line, or by its container closing) or a link
    reference definition (whose title may sit alone on the next line). A span covers a
    whole line, the paragraph a setext underline turns into a heading included.
    ``headings=False`` leaves both heading forms out of the spans: a link written in a
    heading still renders as one.
    """
    spans: Spans = []
    # Content columns of the open list items, innermost last.
    lists: list[int] = []
    fence: _Fence | None = None
    html: _HtmlBlock | None = None
    paragraph: int | None = None
    definition = False
    previous_quote = 0
    offset = 0
    for line in text.split("\n"):
        start, end = offset, offset + len(line)
        offset = end + 1
        after_definition, definition = definition, False
        quote, body, origin, credit = _quote_markers(line)
        if quote > previous_quote:
            paragraph = None
        previous_quote = quote
        indent, at = _indent(line, body, origin)
        indent, origin = indent - credit, origin + credit
        blank = at >= len(line.rstrip("\r"))
        if fence is not None:
            if quote >= fence.quote and (blank or indent >= fence.base):
                spans.append((start, end))
                close = CODE_FENCE_CLOSE_RE.match(line, at)
                if (
                    close is not None
                    and indent - fence.base < CODE_INDENT
                    and line[at] == fence.char
                    and len(close.group().rstrip(" \t\r")) >= fence.width
                ):
                    fence = None
                continue
            fence = None
        if html is not None:
            if blank and html.closer is None:
                html = None
            elif quote >= html.quote and (blank or indent >= html.base):
                spans.append((start, end))
                if html.closer is not None and html.closer.search(line, body):
                    html = None
                continue
            else:
                html = None
        if blank:
            paragraph = None
            continue
        if paragraph is None:
            while lists and indent < lists[-1]:
                _ = lists.pop()
        base = lists[-1] if lists else 0
        if paragraph is None and indent - base >= CODE_INDENT:
            spans.append((start, end))
            continue
        rest = line[at:]
        if (
            paragraph is not None
            and indent - base < CODE_INDENT
            and SETEXT_UNDERLINE_RE.match(rest)
        ):
            if headings:
                spans.append((paragraph, end))
            paragraph = None
            continue
        indent, at, opened = _open_list_items(
            line,
            at,
            indent,
            lists,
            origin=origin,
            in_paragraph=paragraph is not None,
        )
        if opened:
            base, paragraph = lists[-1], None
        rest = line[at:]
        if not rest.strip():
            continue
        if indent - base >= CODE_INDENT:
            # Paragraph continuation, or indented code opened past a list marker.
            if paragraph is None:
                spans.append((start, end))
            continue
        if ATX_HEADING_RE.match(rest):
            if headings:
                spans.append((start, end))
            paragraph = None
            continue
        if (marker_run := CODE_FENCE_RE.match(rest)) is not None:
            # A fence interrupting a list paragraph closes the items it is indented below.
            while lists and indent < lists[-1]:
                _ = lists.pop()
            spans.append((start, end))
            fence = _Fence(rest[0], len(marker_run.group()), lists[-1] if lists else 0, quote)
            paragraph = None
            continue
        if (
            rest.startswith("<")
            and (block := _html_block(rest, interrupts=paragraph is not None)) is not None
        ):
            while lists and indent < lists[-1]:
                _ = lists.pop()
            spans.append((start, end))
            closed, closer = block
            html = None if closed else _HtmlBlock(closer, lists[-1] if lists else 0, quote)
            paragraph = None
            continue
        if paragraph is None and LINK_DEFINITION_RE.match(rest):
            spans.append((start, end))
            definition = True
            continue
        if after_definition and LINK_DEFINITION_TITLE_RE.match(rest):
            spans.append((start, end))
            continue
        if paragraph is None:
            paragraph = start
    return spans


def mask_blocks(text: str, *, headings: bool = True) -> str:
    """Return ``text`` with every ``block_regions`` span blanked to spaces, line breaks kept.

    Offsets are unchanged, so a match found in the masked text indexes the original; a
    masked line is blank, so the inline lexer reads it as a paragraph break.
    """
    chars = list(text)
    for lo, hi in block_regions(text, headings=headings):
        chars[lo:hi] = [char if char == "\n" else " " for char in text[lo:hi]]
    return "".join(chars)
