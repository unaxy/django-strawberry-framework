# Review: `django_strawberry_framework/_django_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: cold - every executable line runs at process start (import/ready()), test-class teardown, or consumer test setup; nothing per request, resolver, row, connection or outbound message

## Implementation (Worker-2)

Pass 1. Performance and Mechanics both closed no-findings, so there is
nothing to implement on those axes; Comments recorded 5 Medium + 2 Low,
all prose-only. Implemented in axis order (nothing, nothing, Comments).
Every finding below is prose-only, so each owes steps 2 and 6 plus the
inverse `--code-digest` proof alone: no before/after, no permanent
test, no failability.

Attribution (before the first edit): `git diff HEAD` on the target
shows exactly the concurrent truth-helper migration (the `truth`
import plus the three `_captured_upstream_descriptor` /
`_validate_upstream_shape` / `_patch_is_installed` hunks), which
predates ITEM_BASELINE and is named on the run-3 Drift line covering
this file; `git diff <ITEM_BASELINE>` on all three touched paths was
empty, and both test files are clean vs HEAD. Every hunk matched, so
no stop. All edits below are comment/docstring lines only; the truth
hunks are preserved byte-for-byte (the target digest proves it: code
identical, prose moved).

### Performance — no findings, nothing implemented

Zero findings; the record's five rejections (R1-R5) stand as written.
No disposition owed, no number moved, no bench figure touched.

### Mechanics — no findings, nothing implemented

Zero findings; the record's ten rejections (R1-R10) stand as written.
No disposition owed. R9's hardening note (a dedicated non-classmethod
oracle) is explicitly not a defect and this pass touches no code, so
no test was added for it.

### Comments — 7/7 implemented

- F1 (Medium, audited-set comment) — implemented, as the text-after
  proposes: the sibling enumeration is gone, the contrast is now
  reimplement-vs-delegator as mechanisms. The splice keeps the
  reviewer's four lines verbatim; the pre-existing line-163 tail
  ("the audited set - a renamed ...") continues underneath unchanged.
- F2 (Medium, `_validate_upstream_shape` docstring) — implemented
  verbatim as the text-after proposes.
- F3 (Medium, composition-test first line) — implemented verbatim as
  the text-after proposes ("unwraps Django's wrapper, restoring the
  original method").
- F4 (Medium, idempotence-test pointer) — implemented verbatim as the
  text-after proposes (names `_patch_is_installed`).
- F5 (Medium, reload-test pointer) — implemented with a reflow the
  record's single text-after line needs: the record ends its line at
  "``_captured_upstream_descriptor```" with no continuation, which
  would strand the existing "NEXT ``apply()`` ..." sentence. Landed:
  "the reload-safety promise in the /
  ``_captured_upstream_descriptor`` docstring held for the" + the
  existing NEXT sentence. Same pointer, grammatical, within line
  length. The Proof line still governs.
- L1 (Low, `_patched_remove_databases_failures` first line) —
  implemented verbatim as the text-after proposes (imperative).
- L2 (Low, "documented contract") — implemented verbatim as the
  text-after proposes ("the symmetric contract the pair implements").

F1/F2 truth check (Worker-2's own read, not the record's): the
sibling bodies corroborate the new mechanism-framed wording —
`_strawberry_patches.py` pins a superseded body source for
`_patched_parse_query_params` (reimplementer) while
`_patched_parse_json` delegates; `_cross_web_patches.py`
`_patched_body` stamps but never calls its captured original;
`_graphql_core_patches.py` is "The delegating wrapper". Sibling
fingerprints match the record's, so the same text was graded.

Proof lines (all seven, shared tree, each prints `0`; the exit 1 is
grep's no-match status, expected):
`grep -c "delegating siblings"`, `grep -c "sibling patches'
delegation"`, `grep -c "Defensive replacement for"`, `grep -c
"documented contract"` on the target; `grep -c "restores the
wrapper"` on `tests/testing/test_wrap.py`; `grep -c 'ensure current
state" contract called out in the module'` and `grep -c "module
docstring's reload-safety promise"` on `tests/test_django_patches.py`.

Inverse proof (prose-only identity, exit 0, equal digests, all three):
`uv run python scripts/review_inspect.py --code-digest
<ITEM_BASELINE>:<path> <path>` with ITEM_BASELINE 8482f9a9 —
target `sha256:ae7b3d6e...c6009`, `tests/test_django_patches.py`
`sha256:8970b55a...6473815`, `tests/testing/test_wrap.py`
`sha256:169dd93c...257515`, both sides equal on each file. No code
moved.

Before/after numbers: none owed (prose-only). Permanent tests: none
owed (prose-only; no test file gained or lost a node). Failability:
none owed (no gate relied on). Bench deltas: none (no number moved;
`## Bench baseline` untouched).

Files changed and why:
- `django_strawberry_framework/_django_patches.py` — F1, F2, L1, L2
  prose (the audited-set comment, two docstrings). The only package
  file; no code hunk.
- `tests/test_django_patches.py` — F4, F5 test-docstring pointers
  (the target's own test module, graded whole by the axis).
- `tests/testing/test_wrap.py` — F3 composition-test first line (prose
  another test module holds about the target's symbol, in scope for
  the axis).

No module first line changed, so no TREE.md render owed.

Formatter result (explicit touched paths, in gate order, all green):
`uv run ruff check --fix` (All checks passed), `uv run python
scripts/check_trailing_commas.py` (0 violations, ASCII clean), `uv run
ruff format` (3 files left unchanged); verify pass `ruff check`,
`ruff format --check`, `check_trailing_commas.py --check` all pass,
and `uv run python scripts/check_citations.py --check` passes on the
whole tree (1297 citations resolve).

Item-scoped diff check: `git diff <ITEM_BASELINE>` over the three
paths holds exactly the seven prose hunks above (3 files, +18/-16)
and no foreign hunk; the concurrent truth migration sits below
ITEM_BASELINE, outside the item diff.

Scratch paths and run ids: `docs/review/temp-tests/_django_patches/implement/`
(created, empty — no probe was needed: every instrument here is
static). No `workspace.py` run was made (prose grading opens no
database; cells inapplicable by construction, as the Comments
record states), so no run id is cited.

Fingerprints (`git hash-object`):
- Touched, before -> after: `django_strawberry_framework/_django_patches.py`
  63f3fa9cba4369ce485a311c8d4f16e78c921768 ->
  6918a213170ea902386a5845da8c6cd1f901baf2;
  `tests/test_django_patches.py`
  e26a26099c12efb2e2cab1e324b73226eab5dd76 ->
  6e62c784389b0490e174ae5825d9ebdb9428199a;
  `tests/testing/test_wrap.py`
  4d3c1351254377197994ee577e4f77844c7c309b ->
  6818d96b50e848393592be1a84e84be836545ec01
  (before hashes equal the records' `## Trace` fingerprints: the tree
  reviewed is the tree edited).
- Read for the F1/F2 truth check (unchanged, equal to the record's):
  `django_strawberry_framework/_strawberry_patches.py`
  2b39199bb2de42e40ae49d62bd24cc8a7a962c1b;
  `django_strawberry_framework/_cross_web_patches.py`
  52bf8f5712d632817587f93c4eeb881fd74ffaae;
  `django_strawberry_framework/_graphql_core_patches.py`
  a188b290b24bce07198611cef7c37935f7a437d1.
- Also read (no fingerprint owed — review inputs, not change inputs):
  the plan `docs/review/review-0_0_15.md`, the three axis records,
  this artifact's skeleton, and the F3/F4/F5 test bodies.

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `django_strawberry_framework/_django_patches.py` | _django_patches.py | Comments | audited-set comment block (F1); `_validate_upstream_shape` docstring (F2); `_patched_remove_databases_failures` docstring first line (L1) and symmetry sentence (L2) |
| `tests/test_django_patches.py` | _django_patches.py | Comments | `test_apply_is_idempotent` docstring (F4); `test_reload_preserves_the_installed_patch_teardown` docstring (F5) |
| `tests/testing/test_wrap.py` | _django_patches.py | Comments | `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth` docstring first line (F3) |

Handoff: Pass 1 is prose-only end to end: seven findings, seven
`implemented`, zero code bytes moved (three equal `--code-digest`
pairs). The one judgment call is the F5 reflow, recorded above with
its reason; everything else is the record's text-after verbatim. The
concurrent truth-helper dirt on the target predates ITEM_BASELINE and
is untouched — a verifier diffing vs HEAD will see it, but it is
outside the item diff. No open threads: no disputed, deferred,
blocked, or stopped row; no missing fixture; the routed
`testing/_wrap.py` "installs unconditionally" lead already sits in the
plan's `## Decisions` and was not touched (out of this item's fence).

## Defects

None. No correctness defect was found or fixed on any axis, and no
pre-existing failure was met (no test was run: prose-only pass).
