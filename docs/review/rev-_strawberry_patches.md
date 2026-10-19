# Review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: hot - the installed wrappers run once per request body, query-param or multipart parse on every operation served by the installed Strawberry (sync and async)

## Implementation (Worker-2)

Pass 1. Performance and Mechanics both closed no-findings, so there
is nothing to implement on those axes; Comments recorded 10 Medium +
6 Low, all prose-only. Implemented in axis order (nothing, nothing,
Comments). Every finding below is prose-only, so each owes steps 2
and 6 plus the inverse `--code-digest` proof alone: no before/after,
no permanent test, no failability.

Attribution (before the first edit): `git diff HEAD` on the target
shows exactly the concurrent truth-helper migration (the `truth`
import plus the `_captured_upstream_method` /
`_patch_is_installed` hunks), which predates ITEM_BASELINE and is
named on the run-3 Drift lines covering this file; `git diff
<ITEM_BASELINE>` on all five touched paths was empty. Two test files
are dirty vs HEAD with concurrent work, both named on the run-3 Drift
lines and both far from this item's sentences:
`test_products_api.py` carries one hunk (the
`test_update_item_via_form_explicit_null_category_id_is_the_form_required_error`
docstring + asserts, form-error-key concurrent work);
`tests/test_views.py` carries the truth migration plus stream-fixture
removals. Every hunk matched, so no stop. All edits below are
comment/docstring lines only; the concurrent hunks are preserved
byte-for-byte (the item diff below holds exactly this pass's 15
prose hunks).

### Performance — no findings, nothing implemented

Zero findings; the record's six rejections (R1-R6) stand as written.
No disposition owed, no number moved, no bench figure touched. The
hot-path deltas the record measured (+32 ns object parse, ~18
ns/batch element, +126 ns multipart) are the feature's own cost and
this pass moves no code, so they stand.

### Mechanics — no findings, nothing implemented

Zero findings; the record's fifteen rejections (R1-R15) stand as
written. No disposition owed. The record's Handoff names the F8
parenthetical as the one stale sentence on its axis; F8 below lands
it.

### Comments — 16/16 implemented

- F1 (Medium, module-docstring shield paragraph) — implemented
  verbatim as the text-after proposes (routes the nested parses
  through `:func:`_translated_parse_json`, drops the
  exact-upstream claim). Four lines replace three; the existing
  "body/multipart sites." continuation follows unchanged.
- F2 (Medium, `_patched_parse_json` guard-coverage paragraph) —
  implemented verbatim as the text-after proposes (routes through
  the shared translator instead of the guard); the existing "Both
  views inherit the single ..." continuation follows on the same
  line, 89 chars.
- F3 (Medium, own test module shield sentence) — implemented
  verbatim as the text-after proposes (around the guard through
  the shared gap-1 translator).
- F4 (Medium, live object-variables row) — implemented verbatim as
  the text-after proposes.
- F5 (Medium, live malformed-param row) — implemented with a
  continuation reflow the record's two text-after lines need: they
  end at "... via the shared gap-1 translator, so an", which would
  strand the existing "same body an unparseable POST body does."
  line as "so an same body ...". Landed the reviewer's two lines
  verbatim, then restored the dropped clause ("unparseable GET
  param answers with the same body an unparseable POST body does.")
  and reflowed the "A shield that swallowed ..." sentence. Same
  claim, grammatical. The Proof line still governs.
- F6 (Medium, `tests/test_views.py` opt-out helper) — implemented
  verbatim as the text-after proposes (delegates stay installed,
  unreachable here, JSON-body-path scoping).
- F7 (Medium, live opt-out helper) — implemented verbatim as the
  text-after proposes; the first line rebreaks ("... ``apply()``
  during the / block stays a no-op. ...") to keep the reviewer's
  sentence intact.
- F8 (Medium, "(the latest release)" parenthetical) — implemented
  verbatim as the text-after proposes; the existing
  "``BaseView.parse_json``" continuation stays on the second line.
- F9 (Medium, gap-1 summary) — implemented verbatim as the
  text-after proposes (both escapes named).
- F10 (Medium, rows-inventory cause clause) — implemented with a
  rewording the Proof line forces: the recommended text-after
  ("validator), the UnicodeDecodeError and RecursionError
  ``__cause__`` values") still contains the Proof's own pattern
  ("validator), the UnicodeDecodeError"), so it prints 1, not 0 —
  verified before repairing. Landed "validator), the ``__cause__``
  values for UnicodeDecodeError and RecursionError", which names
  both causes (grade true) and lets the governing Proof print 0.
- L1 (Low, `_translated_parse_json` first line) — implemented
  verbatim as the text-after proposes (imperative). One 104-char
  line: prose the formatter cannot break, inside the 110 E501
  grace, and every gate below passes.
- L2 (Low, `_patched_parse_json` first line) — implemented
  verbatim as the text-after proposes (imperative).
- L3 (Low, `_patched_parse_query_params` first line) —
  implemented verbatim as the text-after proposes (imperative,
  97 chars).
- L4 (Low, coverage-map pointer verb) — implemented verbatim as
  the text-after proposes ("row lives in").
- L5 (Low, bare `(spec-046)`) — implemented verbatim as the
  text-after proposes (`(spec-046 Decision 9)`, the kept form).
- L6 (Low, "Before spec-046" anchor) — implemented verbatim as
  the text-after proposes (rule-anchored, 107 chars, inside the
  110 grace; the file already carries 32 such lines).

Truth check (Worker-2's own read, not the record's): the shield
body calls `_translated_parse_json` at both nested sites; both
opt-out helpers restore only the `BaseView` pair and no using row
posts multipart; the installed upstream is 0.324.0 while the audit
note stays dated history. The new wording matches the bodies.

Proof lines (all sixteen, shared tree, each prints `0`; the exit 1
is grep's no-match status, expected): the record's F1, F2, F8, L1,
L2, L3 patterns on the target; F3, F9, F10, L4 on
`tests/test_strawberry_patches.py`; F6 on `tests/test_views.py`;
F4, F5, L6 on `test_products_api.py`; F7, L5 on
`test_transport_api.py`. The F10 Proof initially printed 1 (see
above); after the rewording all sixteen print 0.

Inverse proof (prose-only identity, exit 0, equal digests, all
five): `uv run python scripts/review_inspect.py --code-digest
<ITEM_BASELINE>:<path> <path>` with ITEM_BASELINE f3d32be1 —
target `sha256:6d124535...6f4b61e`,
`tests/test_strawberry_patches.py` `sha256:9cd25a75...2a220ca`,
`tests/test_views.py` `sha256:98eeaeb6...6d7ad0ec`,
`test_products_api.py` `sha256:c4bc802f...6d7ee`,
`test_transport_api.py` `sha256:f282ed6d...1963b3d`, both sides
equal on each file. No code moved. Full output kept at
`docs/review/temp-tests/_strawberry_patches/implement/code-digests.txt`.

Before/after numbers: none owed (prose-only). Permanent tests:
none owed (prose-only; no test file gained or lost a node).
Failability: none owed (no gate relied on). Bench deltas: none (no
number moved; `## Bench baseline` untouched).

Files changed and why:

- `django_strawberry_framework/_strawberry_patches.py` — F1, F2,
  F8, L1, L2, L3 prose (module docstring shield + currency
  paragraphs, three function first lines, one guard paragraph).
  The only package file; no code hunk.
- `tests/test_strawberry_patches.py` — F3, F9, F10, L4 module
  docstring prose (the target's own test module, graded whole by
  the axis).
- `tests/test_views.py` — F6 opt-out-helper docstring (prose
  another test module holds about the target's symbols, in scope
  for the axis per the `_django_patches.py` F3 precedent).
- `examples/fakeshop/test_query/test_products_api.py` — F4, F5,
  L6 live-row docstrings (same in-fence rule).
- `examples/fakeshop/test_query/test_transport_api.py` — F7, L5
  live docstrings (same in-fence rule).

No module first line changed, so no TREE.md render owed.

Formatter result (explicit touched paths, in gate order, all
green): `uv run ruff check --fix` (All checks passed), `uv run
python scripts/check_trailing_commas.py` (0 violations, ASCII
clean), `uv run ruff format` (5 files left unchanged); verify pass
`ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` all pass, and `uv run python
scripts/check_citations.py --check` passes on the whole tree (1297
citations resolve). Added-line sweep: no standalone `we` / `you`,
no bare spec number (only `(spec-046 Decision 9)`, the kept form),
no line-number citation, no provenance verb.

Item-scoped diff check: `git diff <ITEM_BASELINE>` over the five
paths holds exactly this pass's 15 prose hunks (F10+L4 share one
hunk; 5 files, +36/-29) and no foreign hunk; the concurrent truth
migration and test-file dirt sit below ITEM_BASELINE or in
untouched regions, outside the item diff.

Scratch paths and run ids:
`docs/review/temp-tests/_strawberry_patches/implement/` (created;
holds `code-digests.txt`, the five inverse-proof outputs). No
`workspace.py` run was made (prose grading opens no database;
cells inapplicable by construction, as the Comments record
states), so no run id is cited.

Fingerprints (`git hash-object`):

- Touched, before -> after:
  `django_strawberry_framework/_strawberry_patches.py`
  2b39199bb2de42e40ae49d62bd24cc8a7a962c1b ->
  90f711fb420b8902434406735c2e367f011e4177;
  `tests/test_strawberry_patches.py`
  94a5bfa489029328cda91dff893882bf8fc93e6f ->
  c06add916e033bd1e8e43211541d21bb1619ab14;
  `tests/test_views.py`
  c542cf1b21c5f275eae171108bdcad0a369afa3d ->
  3f9c81153f4fa742479d1b8d7792a18e294e6253;
  `examples/fakeshop/test_query/test_products_api.py`
  f57d9a0a602ee349316b3346f47102d50c4b81bd ->
  fe78cf9d4862123442611444d44bf81b5187ec6d;
  `examples/fakeshop/test_query/test_transport_api.py`
  b1681e8c725ceb46a0243c770a7dcd295edefc06 ->
  6d65274f9e7b5589d60777d7e0484b3ad10df394
  (before hashes equal the records' `## Trace` fingerprints, and
  `git diff <ITEM_BASELINE>` was empty on all five paths before
  the first edit: the tree reviewed is the tree edited).
- Read for the truth check (unchanged, equal to the records'):
  `django_strawberry_framework/apps.py`
  8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
  `django_strawberry_framework/conf.py`
  ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
  `django_strawberry_framework/views.py`
  48ee582ecdba41d49beb2434f2a9e0af992d39d4;
  `django_strawberry_framework/_cross_web_patches.py`
  52bf8f5712d632817587f93c4eeb881fd74ffaae.
- Also read (no fingerprint owed — review inputs, not change
  inputs): the plan `docs/review/review-0_0_15.md`, the three axis
  records with every Handoff (no Cross-axis sections exist on any
  axis), this artifact's skeleton, `REVIEW.md`, `worker-2.md`,
  and the F4-F7/L5/L6 test bodies.

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/_strawberry_patches.py` | _strawberry_patches.py | Comments | module docstring shield paragraph (F1) and Upstream-status currency (F8); `_patched_parse_json` docstring first line (L2) and guard-coverage paragraph (F2); `_translated_parse_json` docstring first line (L1); `_patched_parse_query_params` docstring first line (L3) |
| `tests/test_strawberry_patches.py` | _strawberry_patches.py | Comments | module docstring gap-1 summary (F9), shield sentence (F3), coverage-map pointer (L4) and cause inventory (F10) |
| `tests/test_views.py` | _strawberry_patches.py | Comments | `_strawberry_patch_opted_out` docstring (F6) |
| `examples/fakeshop/test_query/test_products_api.py` | _strawberry_patches.py | Comments | `test_get_query_with_object_variables_executes_like_upstream` docstring (F4); `test_get_query_with_malformed_variables_param_is_the_upstream_parse_400` docstring (F5); `test_post_utf16_json_body_is_rejected_as_400` docstring (L6) |
| `examples/fakeshop/test_query/test_transport_api.py` | _strawberry_patches.py | Comments | `_strawberry_patch_opted_out` docstring (F7); `test_the_utf8_wire_contract_survives_the_upstream_patch_kill_switch` docstring (L5) |

Handoff: Pass 1 is prose-only end to end: sixteen findings,
sixteen `implemented`, zero code bytes moved (five equal
`--code-digest` pairs). Two judgment calls, both recorded above
with reasons: the F5 continuation reflow (the record's two lines
verbatim, plus the restored clause) and the F10 rewording (the
record's text-after matches its own Proof pattern, so the
governing Proof forced the "``__cause__`` values for X and Y"
shape). Everything else is the record's text-after verbatim. The
concurrent dirt on the target (truth migration) and on two test
files predates ITEM_BASELINE or sits in untouched regions and is
preserved byte-for-byte — a verifier diffing vs HEAD will see it,
but the item diff holds exactly this pass. No open threads: no
disputed, deferred, blocked, or stopped row; no missing fixture;
no bench or TREE.md movement; Performance R1-R6 and Mechanics
R1-R15 stand untouched.

## Defects

None. No correctness defect was found or fixed on any axis, and no
pre-existing failure was met (no test was run: prose-only pass).
