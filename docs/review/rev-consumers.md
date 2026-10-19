# Review: `django_strawberry_framework/consumers.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - admission runs once per operation (revalidate_operation_actor), the outbound checkpoint once per outbound frame

## Implementation (Worker-2)

Pass 1. All three records read whole with every Handoff and Cross-axis
section, then the whole live target (1715 lines) plus the neighbour facts
each finding turns on. Every finding in this item is prose-only, so there
are no before/after numbers, no permanent tests, and no failability proofs;
each file carries the inverse `--code-digest` identity instead.

Attribution (before the first edit): `git diff HEAD --` on the two touched
paths shows concurrent work predating ITEM_BASELINE
(`consumers.py` +96/-483 with `test_routers.py`, both files named on the
run-3 Drift line for this item); `git diff cf28b509 --` on
`consumers.py`, `test_routers.py`, `test_consumers.py` was empty (0 bytes)
and all three `git hash-object` values equalled the records' Trace
fingerprints (`67887b5b`, `36c962b1`, `7dee4bed`), so the tree reviewed is
the tree edited and no stop was owed. All concurrent hunks preserved
byte-for-byte; the item-scoped diff below holds exactly the 12 prose hunks.

### Performance - no findings, nothing to implement

The record is `no-findings` (Path class hot, R1-R8 rejections stand). No
file moved for this axis.

### Mechanics - no in-axis findings; C2 + C1 implemented with Comments

No in-axis findings (R1-R10 stand). The two `## Cross-axis (for Comments)`
findings are implemented here with the Comments axis, which owns their
Proofs and grades:

- C2 (Medium, `tests/test_routers.py` non-string-query comment) -
  implemented as proposed. Note for the verifier: the record's Observation
  calls the text a test docstring, but the Proof's string lives in the
  inline comment at old :6332-:6333, so the reword landed there; the
  Proof (`grep -n "upstream's to send"` prints nothing) governs and now
  holds. The following sentences ("What this row pins...") are preserved
  verbatim, reflowed only.
- C1 (Low, three `__all__` sentences in `consumers.py`) - implemented.
  Shape note: site 2 kept its ``routers.py::__all__`` half, because that
  half is true (`routers.py:69` defines
  `__all__ = ("DjangoGraphQLProtocolRouter",)`); only the false local-list
  half ("no ``__all__`` entry here") was reworded to
  documentation-contract language. The file's sole remaining `__all__`
  mention is that true routers reference (new :1673).

### Comments - 9/9 implemented, 0 deferred

- Medium (module-docstring import-graph enumeration) - implemented
  verbatim: `utils/sessions.py` was read and does `import dataclasses`
  (:100) beside `__future__`/`asyncio`/`contextlib` plus typing names
  (`collections.abc` AsyncIterator/MutableMapping, `typing.Any`), so the
  enumeration now names `dataclasses`. Proof `grep -c 'dataclasses'`
  prints 1.
- Low (`_contain_message_loop_failure` translation paragraph) -
  implemented verbatim: per-protocol disposition with the
  `ignore_parsing_errors=True` mechanism. Proof prints 1.
- Low (`_actor_is_current` anonymous-carve-out comment) - implemented
  verbatim: claim scoped to the plain-attribute core, naming the elided
  legacy-callable and awaitable arms. The arms were verified live in
  `auth/mutations.py` (:473-:477). Proof prints 1.
- Low (`DjangoWebSocketHostValidator` class first line) - implemented
  with a shorter shape than proposed: the reviewer's sentence is 111
  characters on its `"""` line, past the 110 E501 grace, so it landed as
  "An ASGI middleware denying the handshakes Django's own boundary
  refuses." Description mood, same contract; the Proof
  (`grep -c 'Deny a WebSocket handshake'` prints 0) governs and holds.
- Low (`revalidate_operation_actor` first line) - implemented verbatim
  (imperative). Proof prints 0.
- Low (legacy `handle` first line) - implemented verbatim (imperative,
  matching the transport-ws twin). Proof prints 0.
- Low (module-docstring "of your own") - implemented verbatim. Proof
  prints 0.
- Low (`test_a_subscribe_before_connection_init_...` docstring) -
  implemented verbatim ("not a revocation", "upstream without the
  revalidating subclass"), reflowed to hold line length. Proof prints 0.
- Low (`test_the_legacy_graphql_ws_protocol_...` docstring) -
  implemented verbatim (present-tense rule). Proof prints 0.

Severity ride rule: `consumers.py` is touched by the Comments Medium, so
all six Comments Lows plus C1 ride on it; `tests/test_routers.py` is
touched by the C2 Medium, so both Comments Lows there ride on it. Zero
deferred, zero disputed, zero `discharged by`.

Files changed and why each moved:

- `django_strawberry_framework/consumers.py` - 9 prose hunks: the Medium
  plus all 7 riding Lows (6 Comments + C1's 3 sites). No code, no
  test-module, no TREE.md row (no module first line changed).
- `tests/test_routers.py` - 3 prose hunks: the C2 Medium plus the 2
  riding Comments Lows. Prose about this module's admission checkpoint
  and admission close, owned by this item's Comments phase.
- `tests/test_consumers.py` - hash-checked for attribution (`7dee4bed`,
  unchanged), untouched: no finding names it.

Before/after numbers with run ids: none - prose-only change, no
measurement exists to compare. No workspace run was made at either
address (`review/consumers.py/before`, `review/consumers.py/implement`):
every Proof is a static grep plus a grade judgment, and sharded/pg stay
`inapplicable by construction` per the Comments record (no
database-reaching probe; the verifier judges). No run id is cited because
none exists.

Permanent tests with focused results: none owed and none added
(prose-only per REVIEW.md "Comments"). No pytest run was made.

Failability proofs: none owed (no gate relied on). Bench deltas for the
plan's `## Bench baseline`: none - a docstring-stripped-AST-identical
diff moves no figure.

Inverse proofs (`review_inspect.py --code-digest <ITEM_BASELINE>:<path>
<path>`, exit 0, equal digests, re-run after lint):

- `consumers.py`: `sha256:cf167fe8...48afe` both sides.
- `test_routers.py`: `sha256:a7be3a89...439` both sides.

Proof-grep results (post-edit, all 13 as the records require):
`dataclasses` 1, `ignore_parsing_errors` 1, `plain-attribute core` 1,
`Deny a WebSocket handshake` 0, `may a NEW operation start` 0,
`identical loop containment` 0, `of your own` 0, `merely absent from` /
`no __all__ entry here` / `an __all__ and documentation contract` all
absent, `upstream's to send` absent,
`our rejection|un-patched package` 0, `used to carry` in
`test_routers.py` 0.

Formatter result (explicit paths only, in worker-2.md order):
`ruff check --fix` 0 fixed, `check_trailing_commas.py` 0 violations,
`ruff format` unchanged; then `ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` all pass on both paths, and
`check_citations.py --check` passes on the whole tree (1297 citations
resolve, same count as the pre-edit baseline). Pre-edit citer sweep: no
standing doc or code comment quotes any reworded line (only regenerable
copies under `docs/dry/temp-tests/` and `docs/shadow/` carry the old
text). No added line exceeds 99 columns; the three >99 lines in the two
files are pre-existing at ITEM_BASELINE.

Item-scoped diff: `git diff cf28b509 -- <both paths>` = 12 `@@` hunks,
44 insertions, 37 deletions, every hunk one of the findings above, saved
to scratch. `git status` names no new file from this pass.

Scratch paths (all under `docs/review/temp-tests/consumers/implement/`):
`attribution-diff-head-stat.txt`, `attribution-diff-item-baseline.txt`
(0 bytes), `attribution-fingerprints-before.txt`,
`code-digest-consumers.txt`, `code-digest-test_routers.txt`,
`item-diff-pass1.txt`. Run ids: none (no workspace runs).

Fingerprints: touched - `consumers.py` `0791c04a...` (pre `67887b5b...`),
`test_routers.py` `f513d869...` (pre `36c962b1...`); read -
`test_consumers.py` `7dee4bed...` (unchanged),
`utils/sessions.py` `21041723...`, `routers.py` `e18772f7...`,
`auth/mutations.py` `84183c89...` (all equal the records' Trace values);
plus the three axis records, the plan, and this artifact.

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/consumers.py` | consumers.py | Comments | module docstring (import-graph enumeration, `__all__` site 1, `your own` voice); `revalidate_operation_actor` docstring first line; `_actor_is_current` comment; `_contain_message_loop_failure` docstring; `build_revalidating_consumer_class._RevalidatingGraphQLWSHandler.handle` docstring first line; `DjangoWebSocketHostValidator` docstring (first line, `__all__` sites 2-3; C1 via Mechanics cross-axis) |
| `tests/test_routers.py` | consumers.py | Comments | `test_the_legacy_graphql_ws_protocol_is_revalidated_at_handle_start` docstring; `test_a_subscribe_before_connection_init_is_closed_by_upstream_without_revalidating` docstring; `test_a_non_string_query_delivered_over_a_socket_does_not_break_the_loop` comment (C2 via Mechanics cross-axis) |

Handoff: Pass 1 is complete and fully mechanical: 11 prose-only findings
(2 Medium, 9 Low), all implemented, digest-proven, lint-green, no
judgment left open except the two recorded shape notes (the shortened
Host-validator first line and the kept-true `routers.py::__all__`
half of C1 site 2), which the Comments verifier grades like the
proposals. The C2 docstring-vs-comment location note is above; the Proof
governs. If the concurrent `consumers.py` work lands new hot-path
readers the Performance record already asks for a re-review. No defects
found, no pre-existing failure met (no test run made or owed), no
`## Pending execution`, no missing fixture, nothing disputed or blocked.
