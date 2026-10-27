"""CommonMark lexing for the scripts that write glossary links into markdown.

Stdlib only, so ``check_spec_glossary.py`` (which must not import Django) and
``build_kanban_md.py`` (which does, through ``_kanban_lib``) share one lexer. Two layers:

- ``_protected_regions`` lexes the inline constructs (CommonMark 6.1-6.6 plus GitHub's bare
  autolinks) into the regions a term link may not overlap (``Regions.opaque``) or may take
  only whole (``Regions.atoms``).
- ``block_regions`` finds the block constructs a term link may not land in at all (CommonMark
  4.1-4.7): ATX and setext headings, link reference definitions (label, destination and
  title, each may open a line of its own; a label or title may span lines), fenced code
  (backtick or tilde), indented code and HTML blocks, inside block quotes and list items
  nested in any order (5.1-5.3). ``mask_blocks`` blanks them, keeping every offset and line
  break, so the inline lexer reads each masked line as a paragraph break.

``first_open_match`` is the search a writer runs over the lexed text: the first match that
overlaps no opaque region and cuts no atom, retried past every mention a region holds. The
term boundaries pair a standalone-token rule before the term with a prose rule after it.
"""

from __future__ import annotations

import re
from typing import NamedTuple

# A glossary term is inlined only as a standalone token. Before it: no identifier
# character, ``.``, ``:``, ``/`` or ``-``, so it never ends a dotted/``::``-qualified path or
# a hyphen compound. After it: no identifier character, and a ``.``, ``:``, ``/`` or ``-``
# run only when no identifier character follows the run, so a term may end a sentence or
# open a clause (``... via Meta.fields.``) but never starts a longer path
# (``Meta.fields.get``, ``DjangoType-style``).
TERM_BOUNDARY_BEFORE = r"(?<![A-Za-z0-9_.:/\-])"
TERM_BOUNDARY_AFTER = r"(?![A-Za-z0-9_])(?![.:/\-]+[A-Za-z0-9_])"
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

# Block starts (CommonMark 4, 5), each matched where a line's content starts, past the
# markers and indentation its open containers take. A backtick fence's info string carries
# no backtick; a thematic break (4.1) wins over a list item (5.2). The ``\r`` a CRLF line
# keeps ends a marker as the line end does.
LIST_MARKER_RE = re.compile(r"(?:[-+*]|(?P<number>\d{1,9})[.)])(?=[ \t\r]|$)")
THEMATIC_BREAK_RE = re.compile(r"(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})\r?$")
ATX_HEADING_RE = re.compile(r"#{1,6}(?:[ \t\r]|$)")
SETEXT_UNDERLINE_RE = re.compile(r"(?:=+|-+)[ \t\r]*$")
CODE_FENCE_RE = re.compile(r"(?:`{3,}(?=[^`]*$)|~{3,})")
CODE_FENCE_CLOSE_RE = re.compile(r"(?:`{3,}|~{3,})[ \t\r]*$")
# A link reference definition (CommonMark 4.7), read over its paragraph's lines joined: a
# label of at most ``LINK_LABEL_MAX`` characters, not all whitespace, with no unescaped
# bracket (it may span lines); a ``<...>`` destination on one line, else a bare one
# (``_bare_destination_end``); a title in double quotes, single quotes or parentheses that
# may span lines. A backslash escapes a delimiter in each.
LINK_DEFINITION_RE = re.compile(r"\[(?:\\[\s\S]|[^\\\[\]])+\]:")
LINK_LABEL_MAX = 999
LINK_DEFINITION_ANGLE_RE = re.compile(r"<(?:\\[^\n]|[^\\<>\n])*>")
LINK_DEFINITION_TITLE_RE = re.compile(
    r"\"(?:\\[\s\S]|[^\\\"])*\"|'(?:\\[\s\S]|[^\\'])*'|\((?:\\[\s\S]|[^\\()])*\)",
)
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


class _Container(NamedTuple):
    """An open container block (CommonMark 5.1, 5.2): a block quote or a list item.

    ``width`` is the columns a list item's content sits past where its parent's content
    starts (0 for a block quote); ``empty`` says the item opened with nothing after its marker
    and holds nothing yet, so a blank line closes it (CommonMark 5.2).
    """

    item: bool
    width: int
    empty: bool


class _Fence(NamedTuple):
    """An open fenced code block: its marker character and run length."""

    char: str
    width: int


class _HtmlBlock(NamedTuple):
    """An open HTML block: what ends it (``None``: a blank line)."""

    closer: re.Pattern[str] | None


def _indent(line: str, i: int, column: int = 0) -> tuple[int, int]:
    """Return ``(width, index)`` of the whitespace run at ``line[i]``, which sits at ``column``.

    A tab advances to the next multiple of ``TAB_STOP`` counted from the line start, so the
    run's width depends on the column it starts at; ``column`` may sit inside the tab at
    ``line[i]`` when a container took only part of it.
    """
    start = column
    while i < len(line) and line[i] in " \t":
        column = column + TAB_STOP - column % TAB_STOP if line[i] == "\t" else column + 1
        i += 1
    return column - start, i


def _consume(
    line: str,
    i: int,
    column: int,
    columns: int,
) -> tuple[int, int]:
    """Return the ``(index, column)`` ``columns`` columns of whitespace past ``line[i]``.

    The run at ``line[i]`` (at ``column``) is at least that wide. A tab the count ends inside
    stays at the returned index, with the column inside it (CommonMark 2.2).
    """
    target = column + columns
    while column < target:
        stop = column + TAB_STOP - column % TAB_STOP if line[i] == "\t" else column + 1
        if stop > target:
            return i, target
        i, column = i + 1, stop
    return i, column


def _quote_marker(line: str, i: int, column: int) -> tuple[int, int] | None:
    """Return the ``(index, column)`` past the block-quote marker at ``line[i]``, else None.

    A marker is ``>`` indented under ``CODE_INDENT`` columns; one column of whitespace after
    it belongs to it, so a tab there gives it one column and the rest stays indentation
    (CommonMark 5.1).
    """
    width, j = _indent(line, i, column)
    if width >= CODE_INDENT or not line.startswith(">", j):
        return None
    i, column = j + 1, column + width + 1
    if line.startswith((" ", "\t"), i):
        i, column = _consume(line, i, column, 1)
    return i, column


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


def _match_containers(line: str, stack: list[_Container]) -> tuple[int, int, int]:
    """Match ``line`` against the open containers, outermost first (CommonMark appendix A).

    A block quote continues on a line carrying its marker; a list item on a blank line
    (unless it is still empty) or on one indented at least its ``width``, which it takes.
    The first container a line fails ends the match. A list item matched on a non-blank
    line is no longer empty. Returns ``(matched, index, column)``: how many containers
    matched and where the line's content starts past them.
    """
    i = column = 0
    for matched, container in enumerate(stack):
        if not container.item:
            marker = _quote_marker(line, i, column)
            if marker is None:
                return matched, i, column
            i, column = marker
            continue
        width, j = _indent(line, i, column)
        if j >= len(line.rstrip("\r")):
            if container.empty:
                return matched, i, column
            continue
        if width < container.width:
            return matched, i, column
        i, column = _consume(line, i, column, container.width)
        stack[matched] = container._replace(empty=False)
    return len(stack), i, column


def _open_containers(
    line: str,
    i: int,
    column: int,
    *,
    in_paragraph: bool,
) -> tuple[list[_Container], int, int]:
    """Open the block quotes and list items whose markers start at ``line[i]`` (``column``).

    Markers nest in any order (CommonMark 5.1, 5.2): a ``>`` indented under ``CODE_INDENT``
    columns opens a block quote; a list marker opens an item whose content sits past the
    marker and the spaces after it, or one column past the marker when nothing follows it
    or more than ``CODE_INDENT`` columns do (the rest is then indented code). A thematic
    break is no list item. ``in_paragraph`` says the line would otherwise continue an open
    paragraph, which a first item that is empty or numbered other than 1 cannot interrupt
    (CommonMark 5.3). Returns the opened containers, outermost first, and the
    ``(index, column)`` past the last marker.
    """
    opened: list[_Container] = []
    while True:
        marker = _quote_marker(line, i, column)
        if marker is not None:
            opened.append(_Container(item=False, width=0, empty=False))
            i, column = marker
            continue
        width, j = _indent(line, i, column)
        item = LIST_MARKER_RE.match(line, j)
        if width >= CODE_INDENT or item is None or THEMATIC_BREAK_RE.match(line, j):
            return opened, i, column
        marker_end = column + width + item.end() - j
        gap, k = _indent(line, item.end(), marker_end)
        empty = k >= len(line.rstrip("\r"))
        number = item.group("number")
        if not opened and in_paragraph and (empty or (number is not None and int(number) != 1)):
            return opened, i, column
        pad = 1 if empty or gap > CODE_INDENT else gap
        opened.append(_Container(item=True, width=marker_end - column + pad, empty=empty))
        if empty:
            return opened, k, marker_end + gap
        i, column = _consume(line, item.end(), marker_end, pad)


def _starts_block(line: str, j: int, width: int) -> bool:
    """Whether ``line[j:]``, indented ``width`` columns, opens a block that ends a paragraph."""
    rest = line[j:]
    return width < CODE_INDENT and bool(
        ATX_HEADING_RE.match(rest)
        or CODE_FENCE_RE.match(rest)
        or THEMATIC_BREAK_RE.match(rest)
        or (rest.startswith("<") and _html_block(rest, interrupts=True) is not None),
    )


def _skip_inline_space(text: str, i: int) -> int:
    """Return the first index at or after ``i`` that is not a space or tab."""
    while text.startswith((" ", "\t"), i):
        i += 1
    return i


def _bare_destination_end(text: str, i: int) -> int | None:
    """End of the bare link destination at ``text[i]``, else None (CommonMark 6.3).

    A non-empty run with no space or control character whose unescaped parentheses balance,
    nested at most ``LINK_DESTINATION_MAX_NESTING`` deep; an unmatched ``)`` ends it.
    """
    depth = 0
    j = i
    while j < len(text) and text[j] > " " and text[j] != "\x7f":
        if text[j] == "\\" and j + 1 < len(text) and text[j + 1] > " ":
            j += 2
            continue
        if text[j] == ")":
            if not depth:
                break
            depth -= 1
        elif text[j] == "(":
            depth += 1
            if depth > LINK_DESTINATION_MAX_NESTING:
                return None
        j += 1
    return j if j > i and not depth else None


def _definition_end(text: str, i: int) -> int | None:
    """End of the link reference definition starting at ``text[i]``, else None (CommonMark 4.7).

    ``text`` is a paragraph's lines joined by line feeds. The label is followed by ``:``, then
    whitespace holding at most one line ending, the destination, and an optional title
    separated from it by whitespace holding at most one line ending; only spaces and tabs
    may follow on the line where it ends. A title that does not end its line leaves the
    definition ending at its destination when that ends a line, and fails it otherwise.
    The end returned is the line feed (or text end) closing the definition's last line.
    """
    label = LINK_DEFINITION_RE.match(text, i)
    if label is None:
        return None
    inner = label.group()[1:-2]
    if len(inner) > LINK_LABEL_MAX or not inner.strip():
        return None
    j = _skip_inline_space(text, label.end())
    if text.startswith("\n", j):
        j = _skip_inline_space(text, j + 1)
    if text.startswith("<", j):
        angle = LINK_DEFINITION_ANGLE_RE.match(text, j)
        destination = angle.end() if angle is not None else None
    else:
        destination = _bare_destination_end(text, j)
    if destination is None:
        return None
    k = _skip_inline_space(text, destination)
    line_end = k if k == len(text) or text[k] == "\n" else None
    title_at = _skip_inline_space(text, k + 1) if line_end is not None and k < len(text) else k
    title = LINK_DEFINITION_TITLE_RE.match(text, title_at) if title_at > destination else None
    if title is not None:
        after = _skip_inline_space(text, title.end())
        if after == len(text) or text[after] == "\n":
            return after
    return line_end


def _definition_lines(text: str, paragraph: list[tuple[int, int, int]]) -> int:
    """How many of ``paragraph``'s leading lines are link reference definitions.

    ``paragraph`` holds each line's ``(start, end, content)`` offsets in ``text``. Its
    lines are read joined, each from its content start, so definitions, one after another
    from the paragraph's start, may span lines; the count runs through the line each one
    ends on.
    """
    joined = "\n".join(text[content:end].removesuffix("\r") for _, end, content in paragraph)
    lines = i = 0
    while i <= len(joined) and (stop := _definition_end(joined, i)) is not None:
        lines += joined.count("\n", i, stop) + 1
        i = stop + 1
    return lines


def _close_paragraph(text: str, paragraph: list[tuple[int, int, int]], spans: Spans) -> None:
    """End the open ``paragraph``: span its leading definition lines, then forget it."""
    spans.extend((start, end) for start, end, _ in paragraph[: _definition_lines(text, paragraph)])
    paragraph.clear()


def block_regions(text: str, *, headings: bool = True) -> Spans:
    """Spans of the block constructs no term link may land in, CommonMark 4.1-4.7 and 5.1-5.3.

    One pass over the lines, the parsing strategy of CommonMark's appendix A over the open
    containers (block quotes and list items, nested in any order). Each line first matches
    the open containers (``_match_containers``); while a fenced code block or HTML block is
    open, a line matching every container continues it, else the block ends (a fence by a
    matching closing fence too, else at the end of the text; an HTML block by its closer
    or a blank line). A line that fails a container and opens none is a lazy continuation
    of the open paragraph when it opens no other block; otherwise the unmatched containers
    close. The line then opens new containers (``_open_containers``), and what is left
    may open indented code (indented ``CODE_INDENT`` columns past its container, never
    inside a paragraph), underline the open paragraph as a setext heading, or open an ATX
    heading, a code fence, an HTML block or a thematic break; else it is paragraph text.
    A paragraph's leading lines that make up link reference definitions (label,
    destination and title, each possibly on its own line, a title spanning lines) are
    spanned when the paragraph ends; a setext underline after nothing but definitions is
    no heading. A span covers a whole line, the paragraph a setext underline turns into a
    heading included. Spans come in text order: a paragraph's definition lines are spanned
    before any later line is. ``headings=False`` leaves both heading forms out of the
    spans: a link written in a heading still renders as one.
    """
    spans: Spans = []
    # Open containers, outermost first.
    stack: list[_Container] = []
    fence: _Fence | None = None
    html: _HtmlBlock | None = None
    # The open paragraph's lines: ``(start, end, content)`` offsets in ``text``.
    paragraph: list[tuple[int, int, int]] = []
    offset = 0
    for line in text.split("\n"):
        start, end = offset, offset + len(line)
        offset = end + 1
        matched, i, column = _match_containers(line, stack)
        complete = matched == len(stack)
        width, j = _indent(line, i, column)
        blank = j >= len(line.rstrip("\r"))
        if fence is not None:
            if complete:
                spans.append((start, end))
                close = CODE_FENCE_CLOSE_RE.match(line, j)
                if (
                    close is not None
                    and width < CODE_INDENT
                    and line[j] == fence.char
                    and len(close.group().rstrip(" \t\r")) >= fence.width
                ):
                    fence = None
                continue
            fence = None
        if html is not None:
            if blank and html.closer is None:
                html = None
            elif complete:
                spans.append((start, end))
                if html.closer is not None and html.closer.search(line, i):
                    html = None
                continue
            else:
                html = None
        if blank:
            _close_paragraph(text, paragraph, spans)
            del stack[matched:]
            continue
        if (
            paragraph
            and complete
            and width < CODE_INDENT
            and SETEXT_UNDERLINE_RE.match(line, j)
            and (defined := _definition_lines(text, paragraph)) < len(paragraph)
        ):
            spans.extend((lo, hi) for lo, hi, _ in paragraph[:defined])
            if headings:
                spans.append((paragraph[defined][0], end))
            paragraph.clear()
            continue
        opened, i, column = _open_containers(
            line,
            i,
            column,
            in_paragraph=bool(paragraph) and complete,
        )
        width, j = _indent(line, i, column)
        if not opened and not complete and paragraph and not _starts_block(line, j, width):
            paragraph.append((start, end, start + j))
            continue
        if opened or not complete:
            _close_paragraph(text, paragraph, spans)
            del stack[matched:]
            stack.extend(opened)
        rest = line[j:]
        if not rest.strip():
            continue
        if width >= CODE_INDENT:
            # Paragraph continuation, or indented code.
            if paragraph:
                paragraph.append((start, end, start + j))
            else:
                spans.append((start, end))
            continue
        if ATX_HEADING_RE.match(rest):
            _close_paragraph(text, paragraph, spans)
            if headings:
                spans.append((start, end))
            continue
        if (marker_run := CODE_FENCE_RE.match(rest)) is not None:
            _close_paragraph(text, paragraph, spans)
            spans.append((start, end))
            fence = _Fence(rest[0], len(marker_run.group()))
            continue
        if (
            rest.startswith("<")
            and (block := _html_block(rest, interrupts=bool(paragraph))) is not None
        ):
            _close_paragraph(text, paragraph, spans)
            spans.append((start, end))
            closed, closer = block
            html = None if closed else _HtmlBlock(closer)
            continue
        if THEMATIC_BREAK_RE.match(rest):
            _close_paragraph(text, paragraph, spans)
            continue
        paragraph.append((start, end, start + j))
    _close_paragraph(text, paragraph, spans)
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
