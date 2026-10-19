# Review · Comments: `django_strawberry_framework/apps.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=d4ff8d5067f177b771ba3870240d266cdc285f86

## Trace

Read the whole live target (`django_strawberry_framework/apps.py`, 47 lines:
module docstring, `DjangoStrawberryFrameworkConfig` class docstring,
`ready()` docstring, zero inline comments) and the whole own test module
(`tests/test_apps.py`: module docstring, 3 test docstrings, 2 comment blocks).
No sibling axis records existed at dispatch (only `rev-apps.md`, `Status:
reviewing`); required reading was AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan, and `rev-apps.md`.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/apps/comments/inspect/`
(`django_strawberry_framework__apps.overview.md`,
`django_strawberry_framework__apps.stripped.py`,
`docs/review/temp-tests/apps/comments/apps.json`).
`build_tree_md.py --list-docstrings` passes on the target and on
`tests/test_apps.py` (1 module, 0 breaking, each). `check_citations.py
--paths <file> --substrings --json` reports 0 citations in each (the
`:mod:`/`:meth:`/:func:` references are Sphinx form, ungated, and every
named symbol resolves). Provenance sweep (REVIEW.md pattern, regex mode)
prints nothing on the target; on `tests/test_apps.py` the only hits are
"same worker" / "worker's run" (pytest-xdist workers, a technical term,
not review attribution).

Contract trace, each claim checked against its body and one real caller:
all four `apply()` bodies + docstrings (`_django_patches.py`,
`_strawberry_patches.py`, `_cross_web_patches.py`,
`_graphql_core_patches.py`); `conf.py::upstream_patches_enabled`
(`APPLY_UPSTREAM_PATCHES` defaults True; bool-or-mapping shape); the
installed-at-collection assertions and `test_apply_is_idempotent` file
order in the four patch test suites; `docs/SPECS/spec-021-apps-0_0_7.md`
Decisions 2/5/8 (label / `default_auto_field` / `default` mapping);
live-tier pins named by the test module docstring
(`test_products_api.py` GET `parse_query_params` shield tests exist;
`test_transport_api.py` body-cap, UTF-8, and opt-out tests exist);
example-app `apps.py` class-docstring mood (all six carry no class
docstring, so no convention competes with REVIEW.md's class rule).

Cells: `inapplicable by construction` — the target runs at app load,
imports nothing at module scope beyond `AppConfig`, and reaches no
database, alias, or dialect decision; every instrument above is static
(no workspace runs, no run ids).

Fingerprints (`git hash-object`): target `8ae1a3a3`;
`tests/test_apps.py` `5ca8b62c`; `_django_patches.py` `6918a213`;
`_strawberry_patches.py` `90f711fb`; `_cross_web_patches.py`
`52bf8f57`; `_graphql_core_patches.py` `90ac4f3c`; `conf.py`
`ae3de0a3`; `tests/test_django_patches.py` `6e62c784`;
`tests/test_strawberry_patches.py` `c06add91`;
`tests/test_cross_web_patches.py` `70c16389`;
`tests/test_graphql_core_patches.py` `53dca517`;
`docs/SPECS/spec-021-apps-0_0_7.md` `ddd2a450`;
`test_products_api.py` `fe78cf9d`; `test_transport_api.py`
`6d65274f`; example `products/scalars/library/accounts/kanban/glossary`
`apps.py` `f2cb05c1` / `68f93023` / `f5c2ea04` / `87e32081` /
`f4910f6f` / `53bb2c3d` (7-char prefixes; full ids in the shell
history). A finding's Freshness lists only files beyond these: none.

## Findings

### High

None.

### Medium

- Observation: `tests/test_apps.py::test_ready_dispatches_all_four_patch_appliers_and_refires_safely`
  docstring states the per-suite installed assertions "are masked by the
  direct ``apply()`` calls ``test_apply_is_idempotent`` makes earlier in
  file order on the same worker". That mechanism holds for three suites
  only. `tests/test_graphql_core_patches.py` defines no
  `test_apply_is_idempotent`; its combined
  `test_patch_is_installed_at_app_load_and_apply_is_idempotent` asserts
  installed first (line 50) and calls `apply()` after (line 51), so no
  earlier-in-file `apply()` call masks it, and a `ready()` that lost the
  graphql-core dispatch line would fail that assertion rather than
  "still pass them".
- Evidence: the three split suites each define
  `test_apply_is_idempotent` earlier in file order than their
  installed-assertion test (`tests/test_django_patches.py:62` vs
  `:114`; `tests/test_strawberry_patches.py:82` vs `:106`;
  `tests/test_cross_web_patches.py:55` vs `:79`), and each calls
  `apply()`; `tests/test_graphql_core_patches.py` has one combined
  test asserting `_patch_is_installed()` before any `apply()` call in
  the file.
- Impact: wrong stated reason for the dispatch test's existence on one
  of four members (DRY principle 10: worse than none); a reader
  trusting the sentence misjudges which suites pin the dispatch
  contract.
- Severity: Medium (stale behavioral claim in test prose about the
  target's symbol).
- Recommendation: qualify the sentence to the three split suites and
  name the graphql-core exception; see text-after.
- Must not change: n/a.
- Proof: `grep -c "those assertions are masked" tests/test_apps.py`
  prints `0`; the rewritten paragraph earns grade true (the masking
  mechanism stated matches all four suites, naming the graphql-core
  combined test's assert-before-apply order).
- Freshness: none beyond Trace.
- Symbol: `tests/test_apps.py::test_ready_dispatches_all_four_patch_appliers_and_refires_safely`.
- Grade: stale.
- Text-before:
  `The patch-module suites each pin "installed at collection via ready()", but those assertions are masked by the direct apply() calls test_apply_is_idempotent makes earlier in file order on the same worker - a ready() that lost a dispatch line would still pass them.`
- Text-after:
  `The patch-module suites each pin "installed at collection via ready()", but in the three suites that split that assertion from idempotence the direct apply() calls test_apply_is_idempotent makes earlier in file order on the same worker mask it - a ready() that lost one of those three dispatch lines would still pass them. (The graphql-core suite's combined test asserts installed before applying.) This test owns the dispatch contract deterministically for every member: ...` (remainder unchanged).

### Low

- Observation: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig`
  class docstring is imperative ("Register ..."). REVIEW.md requires a
  description for a class; ruff's Google convention leaves mood
  unchecked, so the reviewer is the gate. Content is true; only the
  mood is wrong.
- Evidence: the docstring first line; REVIEW.md "First lines, by kind";
  no competing convention (all six example-app configs carry no class
  docstring).
- Impact: bounded clarity; TREE.md-adjacent prose consistency for the
  package's only AppConfig.
- Severity: Low.
- Recommendation: recast as a description; see text-after.
- Must not change: n/a.
- Proof: `grep -c '"""Register django-strawberry-framework' django_strawberry_framework/apps.py`
  prints `0`; the rewritten class docstring earns grade true
  (description, states the registration).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig`.
- Grade: duplicates the code (mood defect; imperative restating what a
  description must reframe — graded here as the class-first-line rule
  violation).
- Text-before:
  `"""Register django-strawberry-framework with Django's app loader."""`
- Text-after:
  `"""App configuration registering django-strawberry-framework with Django's app loader."""`

- Observation: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
  docstring enumerates the four patch modules with two conjunctions:
  "`(Strawberry), and ... (``cross_web``), and ...
  (``graphql-core``)". A four-item list takes one conjunction before
  the last item; the first "and" is an editing slip.
- Evidence: target lines 15-21 read verbatim.
- Impact: bounded clarity in the dispatcher's only inventory sentence.
- Severity: Low.
- Recommendation: drop the first "and" so the list reads "`(Django),
  (Strawberry), (``cross_web``), and (``graphql-core``)"; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "(Strawberry), and" django_strawberry_framework/apps.py`
  prints `0`; the rewritten enumeration earns grade true (one
  conjunction, same four modules in the same order).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`.
- Grade: stale (ungrammatical as written; not what the author means).
- Text-before:
  `:mod:`django_strawberry_framework._strawberry_patches` (Strawberry), and :mod:`django_strawberry_framework._cross_web_patches` (``cross_web``), and :mod:`django_strawberry_framework._graphql_core_patches` (``graphql-core``).`
- Text-after:
  `:mod:`django_strawberry_framework._strawberry_patches` (Strawberry), :mod:`django_strawberry_framework._cross_web_patches` (``cross_web``), and :mod:`django_strawberry_framework._graphql_core_patches` (``graphql-core``).`

- Observation: `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`
  parametrize reasons cite bare "Decision 2", "Decision 5", "Decision
  8" with no spec anchor anywhere in the file, and the `why` string is
  the pytest fail message, so a failing reader meets the bare numeral
  first. Sibling suites anchor the same form (`tests/test_strawberry_patches.py`
  "(spec-046 Decision 9)"). The mapping itself is true (spec-021
  Decisions 2/5/8 pin label / `default_auto_field` / `default`).
- Evidence: `grep -c '"Decision [258]' tests/test_apps.py` prints `3`
  today; no "spec-021" string in the file; START.md "Bare `Decision N`
  ... defect only when nothing on the reader's path establishes which
  spec"; `docs/SPECS/spec-021-apps-0_0_7.md` Decisions 2/5/8 verified
  against the three reasons.
- Impact: bounded clarity; the fail message names the contract source.
- Severity: Low.
- Recommendation: prefix each reason with the spec; see text-after.
- Must not change: n/a.
- Proof: `grep -c '"Decision [258]' tests/test_apps.py` prints `0`;
  the rewritten reasons earn grade true (kept spec-Decision pointers,
  same three forbiddances).
- Freshness: none beyond Trace.
- Symbol: `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`.
- Grade: stale (incomplete pointer; the anchor the convention requires
  is missing).
- Text-before:
  `("label", "Decision 2 (default last-segment label is already unique)"), ("default_auto_field", "Decision 5 (package ships zero Django models)"), ("default", "Decision 8 (no `default` attribute at any value)")`
- Text-after:
  `("label", "spec-021 Decision 2 (default last-segment label is already unique)"), ("default_auto_field", "spec-021 Decision 5 (package ships zero Django models)"), ("default", "spec-021 Decision 8 (no `default` attribute at any value)")`

## Rejected

- R1 — Dispatch-test "reverts all four patches to the captured
  upstream originals" (5 slots reverted, not 7: the two multipart
  members stay installed): true at the unit it quantifies over — each
  of the four patches transitions installed to uninstalled, which the
  test then asserts. Trigger: a rewrite quantifying over slots.
- R2 — `_cross_web_patches.py` module docstring "applied once from
  ...ready": describes the single-caller install relationship (one
  production caller; `apply()` idempotent), not a call count. True; no
  Routed lead. Trigger: a second production caller of `apply()`.
- R3 — `testing/_wrap.py` module docstring AppConfig.ready claim
  ("installs unconditionally"): already routed in the plan's
  `## Decisions` (owner: `testing/_wrap.py`); not re-raised.
  Trigger: that item closing without touching it.
- R4 — spec-021 slice text prescribing a non-parametrized
  negative-shape test vs the implemented `parametrize` fan-out: the
  spec is an archived record and no prose in the target or its tests
  claims the non-parametrized shape. Out of axis (test structure, not
  prose truth). Trigger: none in this flow.
- R5 — Sphinx `:mod:`/`:meth:` references in the target (full dotted
  paths, ungated non-`path::Symbol` form): every named symbol
  resolves today. Trigger: a cited symbol being renamed.
- R6 — ready() docstring "some Django test runners fire it more than
  once", repeated in two test docstrings and the `_django_patches`
  `apply()` docstring: consistent everywhere, standard Django
  behavior. True. Trigger: a Django floor whose test runner
  guarantees single-fire.

Handoff: I graded every prose unit in the target (3
docstrings, 0 comments) and its own test module (module docstring, 3
test docstrings, 2 comment blocks) plus the installed-via-ready prose
in the four patch test suites: 1 Medium (F1, masking mechanism false
for the graphql-core suite) and 3 Lows (F2 class-docstring mood, F3
double conjunction, F4 bare Decision numerals). Everything else grades
true, including the "each apply() self-gates / is idempotent and
self-healing" paragraph (verified per-module: all four gate via
`upstream_patches_enabled`, all four carry the idempotent reinstall
pattern and reload-retaining captures) and the `_PATCHED_SLOTS`
"every slot" comment (7 table entries equal the union of the four
`apply()` bodies' class-attribute writes, counted 1+4+1+1). No Routed
leads beyond the already-homed `testing/_wrap.py` item; no cross-axis
findings (cold 47-line dispatcher; nothing per request). Proofs are
static `grep -c` lines runnable in the shared tree; verifier pairs
each with the stated grade. Watch on verify: F1's fix must keep the
deterministic-dispatch claim intact, and F4's reworded fail messages
must stay under the line-length gate.

## Verification (Comments)

Step 1: `git diff d4ff8d5067f177b771ba3870240d266cdc285f86 --
tests/test_apps.py django_strawberry_framework/apps.py` hashes equal
to `docs/review/temp-tests/apps/diff/pass-1.diff` (sha256
`aba74b2ec756b8442902e5adcfa51c5d9796190ad3da447ef8995f23ee1a23ef`
both sides, `diff` empty, 2151 bytes each). The tree did not move
under the pass; grading proceeds. (Ordering note: the record-mandated
reading order placed `## Implementation (Worker-2)` before the Proof
runs below; every Proof still ran verbatim and its result is recorded
beside it, so the inversion is moot.)

Proof lines, all run verbatim in the shared tree (static `grep -c`,
per REVIEW.md; a count of 0 exits 1, which is the expected shell
status for "landed"):

- Medium: `grep -c "those assertions are masked"
  tests/test_apps.py` prints `0`. Pass.
- F4: `grep -c '"Decision [258]' tests/test_apps.py` prints `0`.
  Pass.
- F2 (deferred): `grep -c '"""Register
  django-strawberry-framework' django_strawberry_framework/apps.py`
  prints `1` — the old text stands, correct for a deferral (judged
  below).
- F3 (deferred): `grep -c "(Strawberry), and"
  django_strawberry_framework/apps.py` prints `1` — the old text
  stands, correct for a deferral.
- Other records' `## Cross-axis (for Comments)`: none exist
  (`grep -rn "^## Cross-axis"` over all three axis records prints
  nothing; both sibling Handoffs confirm they place none). No
  further Proof owed.

Grades (each changed line as the whole docstring it sits in):

- Medium docstring
  (`tests/test_apps.py::test_ready_dispatches_all_four_patch_appliers_and_refires_safely`,
  live lines 122-136): **true**. First line states the behavior
  ("installs all four upstream patches; a re-fire is safe") and the
  body does exactly that (revert, drive `ready()`, assert all four
  installed, re-fire). The rewritten masking paragraph now matches
  all four suites: the three split suites each define
  `test_apply_is_idempotent` earlier in file order than their
  installed-assertion test (django 62 vs 107, strawberry 82 vs 105,
  cross_web 55 vs 78) and each idempotent body calls `apply()`
  directly, so a `ready()` losing one of those three dispatch lines
  would still pass them; the graphql-core suite defines no
  `test_apply_is_idempotent` and its combined test (first `def` in
  the file, line 49) asserts `_patch_is_installed()` at line 50
  before `apply()` at line 51, exactly the parenthesised exception.
  The deterministic-dispatch claim the review Handoff flagged is
  intact ("owns the dispatch contract deterministically for every
  member"). Double-backtick convention kept; no "Tests that" /
  "Ensures" opening; grammar holds ("calls ... test ...
  makes" is the same relative-clause shape as the original).
- F4 literals (live lines 67-69): **true** — the grade the Proof
  requires ("kept spec-Decision pointers, same three forbiddances").
  Each reason now reads "spec-021 Decision N (...)"; the mapping is
  verified against `docs/SPECS/spec-021-apps-0_0_7.md` (Decision 2 =
  label default-unique, Decision 5 = zero-models
  `default_auto_field`, Decision 8 = no `default` at any value) and
  the "spec-NNN Decision N" shape matches the sibling suite's
  "(spec-046 Decision 9)" form. Same three forbiddances, same keys,
  node `ids` untouched. Longest line 89 chars (line 68), under the
  99 gate — Worker-2's report says 87, off by two, no gate impact.
- Untouched prose in touched symbols: the negative-shape test's own
  docstring (lines 74-81) is in the F4-touched symbol but the
  literal prefix cannot falsify it — still true. Nothing else in a
  touched symbol changed meaning.

F4 proof-shape judgment: sound. Whole-file `--code-digest` identity
cannot hold for a fail-message-literal edit (the instrument strips
docstring statements only; string literals are AST-significant), so
the reconstruction-scoped proof is the correct shape, and every leg
reproduces from an independently built reconstruction
(`verify-comments-1/recon_f4_only.py`, baseline plus only the three
literal swaps): baseline-vs-live exits 1 (`3e41253c...` vs
`075c6d2f...`, both prefixes exactly Worker-2's); recon-vs-live
exits 0 (`075c6d2f...` both); recon-vs-live `diff` shows solely the
Medium docstring hunk. Single consumer holds (`grep -n "why"` shows
lines 65/73/83 only: parametrize header, signature, fail-message
f-string), so pass/fail behavior is identical; the suite confirms
it — `review-20260928T232626-46a18f` (`pytest
tests/test_apps.py --no-cov -q` at
`review/apps.py/verify-comments-1`, fresh copy, package digest
`sha256:41e15d13...` matching the reviewer's, shared tree unmoved)
reports 14 passed, identical to the pre-change
`review-20260928T230611-2a3962` (14 passed).

Deferral judgment (F2, F3): ride rule correctly applied. Per REVIEW.md
Severity a Low rides only on a file already changing for a higher
finding; the Medium lives in `tests/test_apps.py` while F2/F3 live
in `django_strawberry_framework/apps.py`, which no higher finding
touches. Both are recorded `deferred` with the reason in `##
Implementation (Worker-2)` and visible for `## Outcomes`;
`apps.py` is byte-identical to ITEM_BASELINE (0-byte diff, hash
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f` both sides). F4 riding
the Medium's file is likewise correct.

Instruments (shared tree): `build_tree_md.py --list-docstrings`
passes on both files (1 module, 0 breaking, each); no module first
line changed (both first lines byte-equal to ITEM_BASELINE), so no
TREE.md row is owed and none appears. `check_citations.py --paths
tests/test_apps.py --substrings --json` reports 0 citations, 0
violations. The prose diff (`review_changed_python_diffs_against_head.py
ITEM_BASELINE --against worktree --prose --include-tests
--include-init --path <both item paths>`, output under
`verify-comments-1/diff/`) carries exactly one file with exactly
the Medium docstring hunk and no `[code changed too]` marker; the
F4 literals correctly absent (code, not prose).

Diff hygiene: no process provenance (provenance-sweep hits on the
diff are only the kept "spec-021 Decision N" pointers and the
pre-existing "same worker" pytest-xdist term, both discharged);
no line-number citation in added prose; no `we`/`you`/`I` in added
lines. The landed text matches the record's text-afters verbatim
modulo the file's double-backtick convention, which Worker-2
correctly kept.

Sibling verifiers: Performance verify and Mechanics verify both
report `verified` with explicitly zero gaps routed to Comments
("No Routed gaps, no cross-axis text placed or owed"; "No new
findings, no gaps"). Both independently concur on the F4 proof
shape and the F2/F3 deferrals.

Attacks (all passing, recorded, nothing owed):

- A1 masking mechanism, per suite: each `test_apply_is_idempotent`
  body calls `apply()` directly (django lines 69-70, strawberry and
  cross_web lines 3-4 of their bodies) and precedes its suite's
  installed-assertion test in file order — the landed "mask it"
  claim holds for each of the three, not just on average.
- A2 graphql-core masking from any earlier test: the combined test
  is the first `def` in its file (line 49), so no earlier-in-file
  `apply()` call exists anywhere in that module to mask the line-50
  assertion. The exception is airtight, not just first-in-test.
- A3 "for every member": the dispatch body reverts, drives, and
  asserts all four members and re-fires; the R1 unit-of-quantification
  discharge ("reverts all four patches" true per patch) still covers
  the carried-over sentence.
- A4 fail-message reach: `why` flows only into the assert f-string;
  bare `"Decision [258]` count is 0 file-wide, so no second bare
  numeral hides outside the three rows.
- A5 record imprecision (not a landed defect): the review record's
  Evidence cites the django installed test at `:114`; baseline and
  live both place it at `:107`. The ordering claim holds either way
  and no line number landed in prose. Likewise Worker-2's "87
  chars" vs actual 89. Both noted, neither graded.

Disputes: none recorded (`disputed` absent from `rev-apps.md`;
Worker-2's "Proof-shape qualification" is explicitly not a dispute —
correct classification, judged sound above). Nothing to block on.

Cells unverified: none. Every Comments instrument is static; the
target runs at app load and reaches no database, alias, or dialect
decision, and the change is test docstring plus fail-message
literals. Sharded and pg `inapplicable by construction`, concurring
with the reviewer and both sibling verifiers. Default cell ran
(1/1 run above).

Scratch: `docs/review/temp-tests/apps/verify-comments-1/`
(`baseline_test_apps.py`, `recon_f4_only.py`, `diff/`). Runs:
`review-20260928T232626-46a18f` (14 passed). Fingerprints
(`git hash-object`): `tests/test_apps.py`
`fe912987087b560314b04274ffca6ad8a1ca7f02` (matches Worker-2
post-edit); `django_strawberry_framework/apps.py`
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f` (unchanged vs reviewer
and ITEM_BASELINE); `tests/test_django_patches.py` `6e62c784...`,
`tests/test_strawberry_patches.py` `c06add91...`,
`tests/test_cross_web_patches.py` `70c16389...`,
`tests/test_graphql_core_patches.py` `53dca517...`,
`docs/SPECS/spec-021-apps-0_0_7.md` `ddd2a450...` (all match the
review Trace — nothing drifted under the pass).

Verdict: `verified`. Both implemented findings landed true; both
deferrals are rule-correct; the prose-only identity that can hold
does hold, and the part that cannot is proven by the correct
scoped shape.

Handoff: Comments verify is closed with no open threads. What a
re-pass would need: the four Proof counts above (Medium 0, F4 0,
F2/F3 1-each-by-deferral), the independently built
`recon_f4_only.py` plus its two digest exits (1 and 0), and the
14-passed run id. The only numbers worth distrusting on re-read
are second-hand numerals that never landed: the record's django
`:114` (live `:107`) and Worker-2's "87 chars" (live 89). The two
deferred Lows (class-docstring mood, `ready()` double conjunction)
stay live for the next item that touches `apps.py`. No Routed
leads; no cross-axis text placed or owed.
