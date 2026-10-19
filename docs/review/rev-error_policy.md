# Review: `django_strawberry_framework/error_policy.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: cold - resolution/validation at schema construction and import; new_correlation_id once per masked error on the exceptional path only

## Implementation (Worker-2)

Pass 1, shared tree, by hand. Read in order: AGENTS.md, START.md,
REVIEW.md, worker-2.md, the plan (`docs/review/review-0_0_15.md`, run
0.0.15 2026-09-28-3, `## Owned changes`), this artifact, all three axis
records with every Handoff and Cross-axis section (Performance and
Mechanics carry no Cross-axis sections; Comments carries none either),
then the target whole, the own test module whole, and the live-tier
module at every finding site plus a call-site census of `_masked_error`.

Attribution before editing: both files this pass touches equal
ITEM_BASELINE byte for byte (`git diff 59dad4a5 --` the two files plus
the target is empty; live fingerprints `0f0fec24`, `6763a581`,
`57a0bed1` match all three records' Trace), so no hunk appeared since
dispatch. Their `git diff HEAD` hunks are the run-3 drift state the
item baseline captured (plan item: "dirty: run-3 Drift lines"); the
plan's `## Owned changes` holds no row for either path. Zero
unattributable hunks, so no stop condition. The target
`django_strawberry_framework/error_policy.py` is untouched, as
dispatched (it grades true throughout).

### Performance (no findings)

Nothing to implement. No number was owed and none moves: the landed
change is ten docstring/comment hunks, one test-function rename, and
one added assertion, all in the item's two test modules.

### Mechanics (no findings)

Nothing to implement. No owner move, no behavior change. The four
rejections and the glossary Routed lead stand as recorded.

### Comments

All 5 Medium findings implemented; all 6 Lows ride (each sits in a
file a Medium changes, so the Severity ride rule implements every
one). Mediums first, in record order:

- M1, `tests/test_error_policy.py::test_the_policy_is_frozen_so_a_resolver_cannot_widen_its_own_request`
  (frozen docstring + test name invert the copy-boundary mechanism):
  **implemented** as recommended. Verified first: the old node id
  occurs nowhere else in the repo (one repo-wide grep; hits only the
  `def` line and the Comments record's own prose), and the new name
  `test_the_policy_is_frozen_so_a_plain_assignment_raises` collides
  with nothing. Docstring restates the accident-vs-adversary
  distinction in the file's double-backtick convention; the body is
  untouched.
- M2, `test_the_schema_resolves_and_exposes_its_policy_once`
  ("the single resolved object"): **implemented** verbatim to the
  text-after, wrapped across two summary lines for the 99-column
  gate. Test name kept, as the record directs.
- M3, `_run_teardown` (sync early-return mechanism stale on both
  ends of the supported engine range): **implemented** verbatim to
  the text-after, wrapped for the column gate. The rewrite stays
  version-agnostic per the dispatch: its only engine claim is
  `engine-version behavior`, which the record's probe pair proves.
- M4, live-tier `_masked_error` (docstring claims three enforced
  things, helper asserts two): **implemented** via the preferred
  fix - added `assert set(error["extensions"]) == {key}, error`
  after the fullmatch line, docstring unchanged. Verified first:
  all 12 call sites use the default key (regex census; only the
  `def` line carries extra arguments), so the assertion is uniform.
- M5, `test_debug_true_restores_the_original_message_end_to_end`
  (false "which this row proves" read-time claim):
  **implemented** verbatim to the text-after (false clause dropped;
  the true system-property sentences stay). The build-under-one-value
  / request-under-another row the record notes for judgment is not
  added: this item's fence is the recorded findings, and the Proof
  requires only the clause's removal.
- L1, `_HostileMessage` ("consumer code in every dunder"):
  **implemented** verbatim to the text-after; rides on M1/M2/M3's
  file.
- L2, `_UnreadableSettings` ("an unconfigured process answers"):
  **implemented** verbatim to the text-after (motivation paragraph
  only; first line kept); rides on M1/M2/M3's file.
- L3, `HOOK_HALVES` comment ("Every hook and half ... can fail
  at"): **implemented** verbatim to the text-after; rides on
  M4/M5's file.
- L4, hook test ("each escapes from a DIFFERENT place"):
  **implemented** verbatim to the text-after ("different half"
  plus the corrected enumeration); rides on M4/M5's file.
- L5, globalid test ("byte-identically apart from path"):
  **implemented** verbatim to the text-after; rides on M4/M5's
  file.
- L6, opt-out test ("to own your own masking"): **implemented**
  verbatim to the text-after (third person, wrapped across two
  summary lines); rides on M4/M5's file.

Files changed and why: `tests/test_error_policy.py` (5 hunks: M1
docstring + rename, M2, M3, L1, L2) and
`examples/fakeshop/test_query/test_error_policy_api.py` (6 hunks:
L3, M4 assertion, M5, L6, L4, L5) only - the two files every finding
lives in. The target is untouched (no finding names it); TREE.md is
untouched (no module first line changed).

Before/after numbers: none owed (Comments findings; Performance
closed no-findings). No workspace run ids exist for this pass; every
instrument below is static in the shared tree, plus two focused
`--no-cov` module suites.

Permanent tests: none owed (Comments findings owe no permanent
test). Change-safety evidence instead, in the apps.py shape:

- Whole-file `--code-digest` exits 1 on both files, as designed:
  own file `sha256:d6861ddb...` (baseline) vs `sha256:e3e57697...`
  (live); live file `sha256:a5b4beed...` vs `sha256:9a19bd5e...`.
  The deltas are exactly the M1 rename and the M4 assertion.
- Reconstruction `docs/review/temp-tests/error_policy/implement/recon_rename_only.py`
  (ITEM_BASELINE own-test text plus only the `def` rename; its
  diff against the baseline is that one line):
  `--code-digest <recon> tests/test_error_policy.py` exits 0 with
  two equal digests (`sha256:e3e57697...` both). All five docstring
  hunks moved no code.
- Reconstruction `docs/review/temp-tests/error_policy/implement/recon_assert_only.py`
  (ITEM_BASELINE live text plus only the assert line; its diff
  against the baseline is that one line):
  `--code-digest <recon> examples/fakeshop/test_query/test_error_policy_api.py`
  exits 0 with two equal digests (`sha256:9a19bd5e...` both). All
  five prose hunks moved no code.
- Record Proofs, all holding: M1a/M1b/M2/M3/M5/L1/L2/L3/L4/L5/L6
  greps print 0; M4 disjunction succeeds via the preferred disjunct
  (`no other extension keys` count 1 kept, `assert .*extensions.*key`
  count 1 added); the new M1 node id is collected exactly once.
- Suite results unchanged: `uv run pytest tests/test_error_policy.py
  --no-cov` reports 66 passed (the rename cannot change pass/fail,
  proven by the scoped digest; collection holds the new node id
  once); `uv run pytest
  examples/fakeshop/test_query/test_error_policy_api.py --no-cov`
  reports 74 passed, so the added key-set assertion holds on every
  one of the 12 `_masked_error` call sites. An added assert is
  monotonic (pass-to-fail only), and it reads only `error[
  "extensions"]` (already read on the line above) and the in-scope
  `key`; no production path is touched.

Failability proofs: none owed (no gate relied upon).

Formatter result: on both touched paths explicitly, `uv run ruff
check --fix` (0 fixed), `uv run python
scripts/check_trailing_commas.py` (0 violations), `uv run ruff format`
(unchanged); verify pass `ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` all green, and `uv run python
scripts/check_citations.py --check` green on the whole tree (1297
citations resolve).

Item-scoped diff check: `git diff
59dad4a566f3718e6d99572ef853455d0aabc101 --` the two files holds
exactly the eleven hunks above (+32/-23); the target is absent from
it. No hunk I did not make.

Scratch paths (all under `docs/review/temp-tests/error_policy/implement/`):
`baseline_test_error_policy.py` and
`baseline_test_error_policy_api.py` (`git show ITEM_BASELINE:...`,
proving the files pre-edit equaled the baseline),
`recon_rename_only.py` and `recon_assert_only.py` (the scoped-digest
reconstructions). No workspace run ids (no workspace runs; static
instruments plus the two shared-tree module suites only).

Fingerprints (`git hash-object`, post-edit): `tests/test_error_policy.py`
`9a72cdb83d4739be4018a3c58d0bf2736b63f569` (touched);
`examples/fakeshop/test_query/test_error_policy_api.py`
`071b113feeaf9cee30ccda5941614c423251459c` (touched);
`django_strawberry_framework/error_policy.py`
`57a0bed1ba730f8e4c1f4c879d852274eac39f12` (read whole, unchanged -
matches all three records' Trace, so nothing drifted under this
pass); `scripts/review_inspect.py`
`d00ccd080d8ec07a20787ae83fed01f00d5d8f34` (digest instrument).

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `tests/test_error_policy.py` | error_policy.py | Comments | `test_the_policy_is_frozen_so_a_resolver_cannot_widen_its_own_request` renamed to `test_the_policy_is_frozen_so_a_plain_assignment_raises` (docstring); `test_the_schema_resolves_and_exposes_its_policy_once`, `_run_teardown`, `_HostileMessage`, `_UnreadableSettings` (docstrings) |
| `examples/fakeshop/test_query/test_error_policy_api.py` | error_policy.py | Comments | `_masked_error` (key-set assertion); `test_debug_true_restores_the_original_message_end_to_end`, `test_the_explicit_opt_out_returns_the_original_message_under_debug_false`, `test_an_exception_from_a_consumer_hook_is_masked_like_a_resolver_exception`, `test_a_malformed_relation_globalid_is_masked_with_a_correlation_id` (docstrings); `HOOK_HALVES` (comment) |

Handoff: All 11 findings landed - 5 Mediums as recommended (M4 via
the preferred assertion, M1 with the rename), 6 Lows riding their
files, zero deferrals and zero disputes. Two judgment calls for the
verifier: the M1 docstring's second sentence ("touches only the
object held, never the stored enforcement record") generalizes the
record's text-after slightly so it holds for the template object
this test actually writes, not only for a resolver-held copy; and
the M5 noted-but-not-required build-then-flip row was deliberately
not added (outside the recorded Proof). The two AST-significant
test-code lines (rename, assert) are isolated by single-hunk
reconstructions with `--code-digest` identity on the remainder,
plus unchanged green suites and monotonicity reasoning. No defects
met, pre-existing or otherwise; no open threads beyond the record's
two Routed leads, which belong to other items.
