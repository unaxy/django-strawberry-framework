# Review: `django_strawberry_framework/apps.py`

Status: verified
Run: 0.0.15 2026-09-28-3
Path class: cold - every executable line runs at process start (app-loader ready()); nothing per request, resolver, row, connection or outbound message

## Implementation (Worker-2)

Pass 1, shared tree, by hand. Read in order: AGENTS.md, START.md,
REVIEW.md, worker-2.md, the plan (`docs/review/review-0_0_15.md`, run
0.0.15 2026-09-28-3, `## Owned changes`), this artifact, all three axis
records with every Handoff and Cross-axis section (Performance and
Mechanics carry no Cross-axis sections; Comments carries none either),
then the target whole plus `tests/test_apps.py` whole, the four patch
test suites' installed/idempotence tests, and spec-021 Decisions 2/5/8.

Attribution before editing: `tests/test_apps.py` and
`django_strawberry_framework/apps.py` were both clean vs HEAD (`git
diff HEAD --stat` empty on both) and vs ITEM_BASELINE (baseline blob of
the test file hashes `5ca8b62c`, equal to the live pre-edit hash), and
the plan's `## Owned changes` holds no row for either path. Zero hunks
to attribute, so no stop condition. The tree-wide dirty list is
concurrent work in other items' files; none of it was touched.

### Performance (no findings)

Nothing to implement. No number was owed and none moves: the landed
change is one docstring paragraph plus three fail-message string
literals in the item's own test module.

### Mechanics (no findings)

Nothing to implement. No owner move, no behavior change.

### Comments

- Medium, `tests/test_apps.py::test_ready_dispatches_all_four_patch_appliers_and_refires_safely`
  docstring (masking sentence stale for the graphql-core suite):
  **implemented** as recommended, keeping the file's double-backtick
  literal convention. Verified first: the three split suites define
  `test_apply_is_idempotent` earlier in file order than their
  installed-assertion tests (django 62 vs 107, strawberry 82 vs 105,
  cross_web 55 vs 78), while `tests/test_graphql_core_patches.py`
  defines no `test_apply_is_idempotent` and its combined test asserts
  `_patch_is_installed()` (line 50) before calling `apply()` (line
  51). The rewrite qualifies the masking claim to those three suites,
  names the graphql-core assert-before-apply exception, and keeps the
  deterministic-dispatch claim intact ("for every member").
- Low F2, `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig`
  class docstring mood: **deferred**. No higher finding touches
  `django_strawberry_framework/apps.py`, so the Severity ride rule
  leaves the file byte-identical (same ground as the run-1 F8
  deferral). Reason recorded here and visible for `## Outcomes`.
- Low F3, `...::DjangoStrawberryFrameworkConfig.ready` docstring double
  conjunction: **deferred**, same reason as F2 (same untouched file).
- Low F4, `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`
  parametrize reasons (bare "Decision 2/5/8"): **implemented**; rides
  on the Medium's file. Verified first: no "spec-021" string in the
  file, and spec-021 Decisions 2/5/8 pin label / `default_auto_field` /
  `default` respectively. Each reason now reads "spec-021 Decision N
  (...)"; longest line 87 chars, under the gate.

Files changed and why: `tests/test_apps.py` only (two hunks: the
Medium docstring paragraph, the F4 `why` literals). It moved because
it is the file both implemented findings live in. The target
`django_strawberry_framework/apps.py` is untouched (its two Lows
deferred); TREE.md is untouched (no module first line changed).

Before/after numbers: none owed (prose-only; Performance closed
no-findings). No workspace run ids exist for this pass; every
instrument below is static in the shared tree.

Permanent tests: none owed (Comments findings owe no permanent test).
Change-safety evidence instead: `uv run pytest tests/test_apps.py
--no-cov` in the shared tree reports 14 passed, identical to the
Mechanics record's pre-change workspace run
`review-20260928T230611-2a3962` (14 passed) on the unedited file.

Failability proofs: none owed (no gate relied upon; the F4 literals
feed only the assert fail-message f-string, shown by the `why` grep
below to have exactly one consumer).

Proof-shape qualification (not a dispute of any finding): the dispatch
memo states an inverse `--code-digest` proof for each finding. That
holds for the Medium but cannot hold whole-file for F4, whose
text-after edits three runtime string literals: `code_digest`
(`scripts/review_inspect.py`) strips docstring statements only, so the
F4 literals are AST-significant by construction. Evidence as run:

- `uv run python scripts/review_inspect.py --code-digest
  d4ff8d5067f177b771ba3870240d266cdc285f86:tests/test_apps.py
  tests/test_apps.py` exits 1: `sha256:3e41253c...` (baseline) vs
  `sha256:075c6d2f...` (live). The delta is exactly the F4 literals.
- Reconstruction `docs/review/temp-tests/apps/implement/recon_f4_only.py`
  (ITEM_BASELINE text plus only the F4 hunks; `diff` against live
  shows solely the Medium docstring hunk): `--code-digest
  <recon> tests/test_apps.py` exits 0 with two equal digests
  (`sha256:075c6d2f...` both). The Medium hunk moved no code.
- Record Proofs: `grep -c "those assertions are masked"
  tests/test_apps.py` prints 0; `grep -c '"Decision [258]'
  tests/test_apps.py` prints 0.
- `grep -n "why" tests/test_apps.py` shows the F4 strings' only
  consumer is the fail-message f-string on line 83, so pass/fail
  behavior is identical (confirmed by the 14-passed run above).

Formatter result: on `tests/test_apps.py` explicitly, `uv run ruff
check --fix` (0 fixed), `uv run python
scripts/check_trailing_commas.py` (0 violations), `uv run ruff format`
(unchanged); verify pass `ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` all green, and `uv run python
scripts/check_citations.py --check` green on the whole tree (1297
citations resolve).

Item-scoped diff check: `git diff
d4ff8d5067f177b771ba3870240d266cdc285f86 -- tests/test_apps.py
django_strawberry_framework/apps.py` holds exactly the two hunks
above; no hunk I did not make.

Scratch paths (all under `docs/review/temp-tests/apps/implement/`):
`baseline_test_apps.py` (`git show ITEM_BASELINE:tests/test_apps.py`,
hash `5ca8b62c`, proving the file pre-edit equaled the baseline),
`recon_f4_only.py` (baseline plus the F4 hunks only, for the scoped
digest proof). No workspace run ids (no workspace runs; static
instruments only).

Fingerprints (`git hash-object`, post-edit): `tests/test_apps.py`
`fe912987087b560314b04274ffca6ad8a1ca7f02` (touched);
`django_strawberry_framework/apps.py`
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f` (read, unchanged);
`tests/test_django_patches.py`
`6e62c784389b0490e174ae5825d9ebdb9428199a`;
`tests/test_strawberry_patches.py`
`c06add916e033bd1e8e43211541d21bb1619ab14`;
`tests/test_cross_web_patches.py`
`70c16389aa5d2a14746dba1612c909263bffd822`;
`tests/test_graphql_core_patches.py`
`53dca51737e6163c09549d015713ebf9dfcdec88`;
`docs/SPECS/spec-021-apps-0_0_7.md`
`ddd2a45085c3b4c92bc4d65dd535299341c56b29`;
`scripts/review_inspect.py`
`d00ccd080d8ec07a20787ae83fed01f00d5d8f34`. The six `8ae1a3a3` /
`6e62c784` / `c06add91` / `70c16389` / `53dca517` / `ddd2a450`
prefixes match the Comments record's Trace, so nothing drifted under
this pass.

Proposed owned changes:

| Path | Item | Axis | Symbols changed |
|---|---|---|---|
| `tests/test_apps.py` | apps.py | Comments | `test_ready_dispatches_all_four_patch_appliers_and_refires_safely` (docstring masking paragraph); `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` (parametrize `why` literals) |

Handoff: Both implemented findings landed verbatim to their
text-afters (modulo the file's double-backtick convention). The two
deferred Lows keep `apps.py` byte-identical; a future item touching
that file should pick them up (class-docstring mood, ready()
conjunction). The one judgment call for the verifier is the F4 proof
shape: a fail-message literal change cannot carry whole-file
`--code-digest` identity, so the Medium's identity is proven against
the F4-only reconstruction and F4 itself by diff plus the
single-consumer grep plus the unchanged 14-passed suite. No open
threads beyond that; no defects met, pre-existing or otherwise.
