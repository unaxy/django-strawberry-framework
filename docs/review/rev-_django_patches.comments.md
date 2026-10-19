# Review · Comments: `django_strawberry_framework/_django_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8482f9a925f3c073013b20e7ef783e9dc5c1ac3e

## Trace

Read the whole live target (427 lines), the whole own test module
`tests/test_django_patches.py` (755 lines), and every prose passage other
test modules hold about the target's symbols: `tests/test_apps.py`
(AppConfig dispatch docstrings), `tests/testing/test_wrap.py` (module
docstring plus the defense-in-depth composition test), and the
`_django_patches` precedent citation in
`tests/test_strawberry_patches.py`. Followed the trace out to the
package modules that cite the target:
`django_strawberry_framework/apps.py` (`ready` dispatch),
`django_strawberry_framework/conf.py` (gate names),
`django_strawberry_framework/testing/_wrap.py` and
`django_strawberry_framework/testing/__init__.py` (wrap-time half prose),
and the three sibling patch modules for the delegation-shape claims.
Verified upstream facts against the installed third party in `.venv`
(Django 6.1.0 `testcases.py` / `features.py`, debug-toolbar 7.1.1
`tracking.py` / `cache.py`); those reads are static and carry no
fingerprint.

The target is dirty with concurrent work at read time: the live tree
differs from `HEAD` by the `truth` helper migration only
(`truth.class_dict` / `truth.is_instance` in
`django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor`,
`django_strawberry_framework/_django_patches.py::_validate_upstream_shape`
and `django_strawberry_framework/_django_patches.py::_patch_is_installed`,
plus the import). No prose hunk is dirty; every finding below reproduces
identically at `HEAD` and at `ITEM_BASELINE`. No sibling axis record
existed when this pass ran.

Instruments (all static, shared tree, no package import, no database):
`review_inspect.py` orientation plus Comments census into
`docs/review/temp-tests/_django_patches/comments/inspect/` and
`docs/review/temp-tests/_django_patches/comments/_django_patches.json`;
`build_tree_md.py --list-docstrings` on the target (module first line
passes); `check_citations.py --paths ... --substrings --json` on the
target (0 `path::Symbol` citations; the file cites only Sphinx
`:func:` / `:meth:` / `:mod:` roles); the provenance `grep` (hits
adjudicated in `## Rejected`). Database cells: inapplicable by
construction for the whole axis — prose grading opens no database and
reaches no alias or dialect decision; no `workspace.py` run was made.

Fingerprints (`git hash-object`, live tree as read):

- `django_strawberry_framework/_django_patches.py`: 63f3fa9cba4369ce485a311c8d4f16e78c921768
- `tests/test_django_patches.py`: e26a26099c12efb2e2cab1e324b73226eab5dd76
- `tests/testing/test_wrap.py`: 4d3c1351254377197994ee577e4f77844c7c309b
- `tests/test_apps.py`: 5ca8b62c53185343ebfec95315f59ec6104fc851
- `tests/test_strawberry_patches.py`: 94a5bfa489029328cda91dff893882bf8fc93e6f
- `django_strawberry_framework/apps.py`: 8ae1a3a3b12f0c9792094959c573ea6fab5d804f
- `django_strawberry_framework/conf.py`: ae3de0a36e2f7737a2c8350e532cdb761b295bcf
- `django_strawberry_framework/testing/_wrap.py`: 0df97813659bea9ed2002f64e6885896c5cabd6f
- `django_strawberry_framework/testing/__init__.py`: 48b45d1b433283c40bf8d602d71a26d261a833b2
- `django_strawberry_framework/_strawberry_patches.py`: 2b39199bb2de42e40ae49d62bd24cc8a7a962c1b
- `django_strawberry_framework/_cross_web_patches.py`: 52bf8f5712d632817587f93c4eeb881fd74ffaae
- `django_strawberry_framework/_graphql_core_patches.py`: a188b290b24bce07198611cef7c37935f7a437d1

## Findings

### High

None.

### Medium

#### F1 — audited-set comment names both siblings "delegating"; neither is (only)

- Observation: the comment block above
  `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` contrasts this module's
  reimplementation with "the delegating siblings
  (``_cross_web_patches``/``_strawberry_patches``)". Both names are
  wrong as blanket labels today, and the parenthetical omits the one
  sibling that does purely delegate,
  `django_strawberry_framework/_graphql_core_patches.py`
  ("The delegating wrapper below").
- Evidence: `django_strawberry_framework/_strawberry_patches.py` is
  mixed. `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json`
  delegates (`_translated_parse_json` calls
  `_original_parse_json(self, data)`), but
  `django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params`
  never calls its captured original (zero references in its body) and
  pins the superseded body source exactly like this module ("the
  reimplementer's contract", citing the `_django_patches` precedent).
  `django_strawberry_framework/_cross_web_patches.py::_patched_body`
  returns `self.request.body` directly and never calls
  `_original_body_fget`: a behavior replacement, not a delegation, and
  one that pins no body. So an upstream body change flows through
  neither sibling the way the comment claims; the parse-query-params
  shield needs the same re-audit this comment says only this module
  needs.
- Impact: a reader widening the audited set follows the comment's
  mental model of the patch family and misjudges which siblings absorb
  upstream body changes. The comment guards the set's widening rule,
  so its framing is load-bearing.
- Severity: Medium (stale comment on internal code).
- Recommendation: drop the sibling enumeration; the contrast the
  comment needs is reimplement-vs-delegate as mechanisms, which cannot
  rot when a sibling gains a second patch.
- Must not change: n/a (Comments).
- Proof: `grep -c "delegating siblings" django_strawberry_framework/_django_patches.py` prints `0`; the rewritten block earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_django_patches.py` audited-set comment block.
- Grade: stale.
- Text-before:
  `# :func:`_patched_remove_databases_failures` REIMPLEMENTS upstream's whole loop`
  `# instead of wrapping and delegating to it, an upstream body change does not`
  `# flow through the patch the way it does for the delegating siblings`
  `# (``_cross_web_patches``/``_strawberry_patches``). ``_validate_upstream_shape``
- Text-after:
  `# :func:`_patched_remove_databases_failures` REIMPLEMENTS upstream's whole loop`
  `# instead of wrapping and delegating to it, an upstream body change does not`
  `# flow through the patch the way it does for a delegating wrapper.`
  `# ``_validate_upstream_shape`` therefore pins these sources so any body OUTSIDE`

#### F2 — `_validate_upstream_shape` docstring claims every sibling only pins the call shape

- Observation: "The body pin is the reimplementer's equivalent of the
  sibling patches' delegation: they only need their call shape
  validated because upstream body changes flow through the delegated
  call". "They" is every sibling patch; the claim is false for two of
  the three siblings.
- Evidence: same bodies as F1.
  `django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params`
  pins its superseded body source on top of the call shape, so it does
  not "only need [its] call shape validated". And
  `django_strawberry_framework/_cross_web_patches.py::_patched_body`
  never calls its captured original, so no upstream body change "flows
  through the delegated call" there — there is no delegated call. Only
  the `parse_json`, multipart, and `complete_list_value` wrappers fit
  the sentence.
- Impact: states the wrong validation contract for the patch family on
  the exact docstring a maintainer reads before touching validation.
  A reader trusting "they only need the call shape" would weaken the
  query-params body pin as redundant.
- Severity: Medium (stale docstring on an internal symbol).
- Recommendation: restate the contrast as mechanisms (reimplementer vs
  delegator) without quantifying over the siblings.
- Must not change: n/a (Comments).
- Proof: `grep -c "sibling patches' delegation" django_strawberry_framework/_django_patches.py` prints `0`; the rewritten docstring earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_django_patches.py::_validate_upstream_shape`.
- Grade: stale.
- Text-before:
  `The body pin is the reimplementer's equivalent of the sibling patches'`
  `delegation: they only need their call shape validated because`
  `upstream body changes flow through the delegated call, while this`
  `module supersedes the whole body and must re-audit whenever that body`
  `changes.`
- Text-after:
  `The body pin is the reimplementer's equivalent of a delegator's`
  `call-shape check: a delegating wrapper only needs its call shape`
  `validated because upstream body changes flow through the delegated`
  `call, while this module supersedes the whole body and must re-audit`
  `whenever that body changes.`

#### F3 — composition test first line says the patch "restores the wrapper"; it removes it

- Observation: the docstring first line of the wrap/unwrap
  composition test in `tests/testing/test_wrap.py` states the
  observable backwards: the patch unwraps (removes) Django's wrapper
  and restores the original method, exactly as the test body asserts
  and as the docstring's own second paragraph says.
- Evidence: the body ends with `assert connection.cursor is
  sentinel_original` — the `_DatabaseFailure` is gone. The second
  paragraph agrees: "The wrapper is unwrapped exactly as upstream
  would do". Only the first line says "restores the wrapper".
- Impact: the first line is what a failure summary and a skim reader
  see; it teaches the inverse of the target symbol's contract.
- Severity: Medium (stale behavioral claim in test prose about the target's symbol).
- Recommendation: state the unwrap direction the body pins.
- Must not change: n/a (Comments).
- Proof: `grep -c "restores the wrapper" tests/testing/test_wrap.py` prints `0`; the rewritten first line earns grade true (it states the wrapper is removed and the original restored).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/testing/test_wrap.py::test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth`.
- Grade: stale.
- Text-before:
  `pair runs, the package's unwrap-time patch`
  `(:func:`_django_patches._patched_remove_databases_failures`)`
  `restores the wrapper without any work from the consumer.`
- Text-after:
  `pair runs, the package's unwrap-time patch`
  `(:func:`_django_patches._patched_remove_databases_failures`)`
  `unwraps Django's wrapper, restoring the original method, without any`
  `work from the consumer.`

#### F4 — idempotence test cites the module docstring for a contract named elsewhere

- Observation: `tests/test_django_patches.py::test_apply_is_idempotent`
  says it pins "the "ensure current state" contract called out in the
  module docstring". The phrase appears nowhere in the module
  docstring (lines 1-114); it is named in the
  `django_strawberry_framework/_django_patches.py::_patch_is_installed`
  docstring ("enforce the "ensure current state" contract").
- Evidence: `grep -n 'ensure current'` on the target matches only the
  `_patch_is_installed` docstring, in the live tree, at `HEAD`, and at
  `ITEM_BASELINE` alike.
- Impact: sends the reader to the wrong docstring for the contract the
  test pins.
- Severity: Medium (stale location claim in the target's own test module).
- Recommendation: name the docstring that actually states the contract.
- Must not change: n/a (Comments).
- Proof: `grep -c 'ensure current state" contract called out in the module' tests/test_django_patches.py` prints `0`; the rewritten docstring earns grade true (it names `_patch_is_installed`).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/test_django_patches.py::test_apply_is_idempotent`.
- Grade: stale.
- Text-before:
  `Pins the "ensure current state" contract called out in the module`
  `docstring. AppConfig.ready() may run more than once under some`
- Text-after:
  `Pins the "ensure current state" contract called out in the`
  `_patch_is_installed docstring. AppConfig.ready() may run more than`
  `once under some`

#### F5 — reload test cites the module docstring for the reload-safety promise

- Observation: the reload test's docstring refers to "the module
  docstring's reload-safety promise". The module docstring never
  mentions reloading; the promise lives in the
  `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor`
  docstring ("retaining it across an in-process reload ... so reload
  can recover and revalidate") plus the `_validated_...` comment
  block's carried-value reasoning.
- Evidence: `grep -n -i 'reload'` on the target matches only the
  `_captured_upstream_descriptor` docstring and the
  `_validated_remove_databases_failures_source` comment, in the live
  tree, at `HEAD`, and at `ITEM_BASELINE` alike.
- Impact: same as F4 — the pointer aims at a docstring that does not
  contain the promise.
- Severity: Medium (stale location claim in the target's own test module).
- Recommendation: point at the docstring that makes the promise.
- Must not change: n/a (Comments).
- Proof: `grep -c "module docstring's reload-safety promise" tests/test_django_patches.py` prints `0`; the rewritten docstring earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `tests/test_django_patches.py::test_reload_preserves_the_installed_patch_teardown`.
- Grade: stale.
- Text-before:
  ```apply()`` - the module docstring's reload-safety promise held for the`
- Text-after:
  ```apply()`` - the reload-safety promise in the ``_captured_upstream_descriptor```

### Low

#### L1 — `_patched_remove_databases_failures` first line is a description, not an imperative

- Observation: the function docstring opens "Defensive replacement
  for ...", a description. The axis requires the imperative mood for
  functions and methods ("Return ...", "Build ..."); ruff leaves D401
  unchecked, so the reviewer is the gate. Every other function in the
  module opens imperative.
- Evidence: first line of
  `django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures`;
  contrast the imperative opens of `_captured_upstream_descriptor`,
  `_validate_upstream_shape`, `_is_database_failure`,
  `_disallowed_connection_methods`, `_patch_is_installed`, `apply`.
- Impact: bounded clarity; the summary line states what the object
  is rather than what it does.
- Severity: Low.
- Recommendation: open with the behavior the body implements.
- Must not change: n/a (Comments).
- Proof: `grep -c "Defensive replacement for" django_strawberry_framework/_django_patches.py` prints `0`; the rewritten first line earns grade true (imperative, states the unwrap-and-skip behavior).
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures`.
- Grade: duplicates the code (states the object's role, which the name plus the second paragraph already establish, instead of its behavior).
- Text-before:
  `Defensive replacement for ``SimpleTestCase._remove_databases_failures``.`
- Text-after:
  `Remove Django's disallowed-database wrappers, leaving foreign replacements untouched.`

#### L2 — "Django's documented contract" overclaims for private methods

- Observation: the `_patched_remove_databases_failures` docstring
  says the skip "mirrors Django's documented contract that
  `_add_databases_failures` / `_remove_databases_failures` operate
  symmetrically". Both methods are underscore-private and carry no
  docstring in the installed Django 6.1.0; the symmetry is the pair's
  evident implementation contract, not a documented one.
- Evidence: installed
  `.venv/lib/python3.14/site-packages/django/test/testcases.py`
  defines both methods with no docstring and no symmetry comment; the
  symmetry holds (the 6.1 `_add_databases_failures` wraps exactly the
  feature-flag list the teardown reads), but "documented" is doing
  work no document does.
- Impact: bounded precision; a reader hunting the cited documentation
  finds nothing.
- Severity: Low.
- Recommendation: claim the symmetry the code shows, not documentation.
- Must not change: n/a (Comments).
- Proof: `grep -c "documented contract" django_strawberry_framework/_django_patches.py` prints `0`; the rewritten sentence earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures`.
- Grade: stale (one word of a true sentence).
- Text-before:
  `fails and the (foreign) replacement is left untouched. This`
  `mirrors Django's documented contract that`
  ```_add_databases_failures`` / ``_remove_databases_failures```
  `operate symmetrically on the methods they themselves wrapped, and`
- Text-after:
  `fails and the (foreign) replacement is left untouched. This`
  `mirrors the symmetric contract the pair implements -`
  ```_add_databases_failures`` / ``_remove_databases_failures```
  `operate on the methods they themselves wrapped - and`

## Rejected

- R1 — "no longer" (module docstring "no longer crashes", `_validate_upstream_shape` first line, both drift error strings): present-tense behavioral claims about what the patch does / when validation fires, not process provenance. True in each case. Trigger: wording that dates the change itself ("previously", a version, a round).
- R2 — "cache-panel fix for Sentry" (module docstring): upstream-rationale narrative, in the kept class (upstream fixes and tickets), not this package's process. The installed debug-toolbar 7.1.1 corroborates both halves: `wrap_cursor` returns early on `isinstance(connection.cursor, _DatabaseFailure)`, and the cache panel keeps its wrappers installed while toggling the `_djdt_panel` owner marker. Trigger: naming this package's own card, round, or worker.
- R3 — "legacy attribute" (`_disallowed_connection_methods` docstring) and "A legacy override may survive a Django upgrade" (feature-flag test comment): technical descriptors with the referent defined in place, verified against Django 6.1.0 whose `_add_databases_failures` reads only the feature flag. Trigger: a bare "legacy" with no defined referent.
- R4 — "round" substring hits ("workaround", "around every request"): vocabulary false positives, not round references.
- R5 — module docstring "applied once from ... ready()": reads as one call site, and `apply`'s docstring plus the idempotence test cover the refire-tolerance explicitly. `ready` does call `apply_django()`. Trigger: evidence `apply` is not idempotent.
- R6 — reload test's past-tense hazard narrative ("therefore turned every subsequent tearDownClass into a RuntimeError"): describes the mechanism the carried-value initialization defeats, with the conditional "Without the reload-aware initialization" beside it; names no change vehicle. Trigger: naming the card, round, or commit that introduced it.
- R7 — "If the patch were still installed on TransactionTestCase" (direct-subclass test): counterfactual about placement, not history. Trigger: an explicit claim about where the patch used to live.
- R8 — "The inherited escape-hatch coupling, resolved end to end" (opt-out test first line): terse but behavioral — the body exhibits the drift abort and its per-dependency silencing. Trigger: a reading under which "inherited"/"resolved" names a prior change rather than the exhibited coupling.
- R9 — Sphinx short-path citations (`:meth:`apps.DjangoStrawberryFrameworkConfig.ready`` and siblings): not `path::Symbol` form, ungated, and every named symbol resolves today (`apps.ready`, `conf.upstream_patches_enabled`, `testing.safe_wrap_connection_method`, debug-toolbar `wrap_cursor`). No line-number citations anywhere in the target or its tests. Trigger: a cited symbol being renamed.
- R10 — `_captured_upstream_descriptor` "false upstream-drift error": loose (a mis-capture fails tier 1, the classmethod check, rather than the body pin), but directionally true — a loud false failure at the next `apply`. Not worth churning the sentence. Trigger: a reload path where a mis-capture passes validation silently.
- R11 — hierarchy "(SimpleTestCase -> TransactionTestCase -> TestCase)" omitting `LiveServerTestCase`: the chain shown is the inheritance spine the tests pin, and `LiveServerTestCase` inherits the patch through `TransactionTestCase`, so "a single patch covers every test-case class" still holds. Trigger: a test-case class outside that spine.
- R12 — "This package does NOT wrap any connection method itself": true. The only `setattr(connection, ...)` sites in the package are this module's unwrap (`method.wrapped`), the pinned upstream-body constants, and the consumer-facing `safe_wrap_connection_method` helper, which no package code calls (callers are tests and the helper's own docstring example); `schema.py` resets a closed handle and `extensions/debug.py` toggles a boolean flag, neither a method wrap. Trigger: a package-internal call site of the helper.
- R13 — test-module docstring's sharded note ("do not require FAKESHOP_SHARDED=1") against the feature-flag test's sharded comment: consistent — the test loops all aliases and restores each, so it passes either way. Trigger: a sharded-cell failure.
- R14 — test file's repeated "exclude every alias including default" comments and the `frozenset()` call sites: each states the allow-list's intent at the site that needs it; deleting any one loses the reason the class exists. True, not duplication. Trigger: a site where the comment restates the adjacent line with no intent added.

## Cross-axis

None. This pass found no performance or mechanics issue: every
behavioral claim checked against a body held (the two sibling-shape
claims in F1/F2 are prose stale against sibling bodies, with no
behavioral defect implied at either side), and the inverted test
first line in F3 contradicts its own passing body rather than any
production behavior.

Handoff: I graded the live tree (target hash 63f3fa9c; the concurrent
`truth`-migration dirt touches code only, no prose). The five Mediums
cluster into two themes: the patch family outgrew this module's prose
(F1, F2 — the `_strawberry_patches` query-params shield now
reimplements with its own body pin, and `_cross_web_patches` never
delegated), and test docstrings pointing at "the module docstring"
for contracts stated in narrower docstrings (F3–F5 are three separate
sites, each with its own text-after). The one lead I could not home
here is the `testing/_wrap.py` module-docstring "installs
unconditionally" claim — it is a Routed lead for the `testing/_wrap`
item, recorded below in my report, not a finding in this record. If a
verifier re-checks the debug-toolbar cache-panel narrative, the
corroboration is the installed 7.1.1 sources read statically, not the
linked main-branch URLs. No open threads beyond the seven findings.

## Verification (Comments)

Step 1: `git diff 8482f9a925f3c073013b20e7ef783e9dc5c1ac3e --
django_strawberry_framework/_django_patches.py
tests/test_django_patches.py tests/testing/test_wrap.py` is
byte-identical to `docs/review/temp-tests/_django_patches/diff/pass-1.diff`
(both 5775 bytes, `sha256:77d81a7d...899871`); the tree did not move
under the pass. Every Proof below ran at
`review/_django_patches.py/verify-comments-1` BEFORE this verifier
read `## Implementation (Worker-2)`.

Proof lines (all seven, verbatim, each prints `0`; exit 1 is grep's
no-match status, expected). Copy slot-3, `fresh` on every run, shared
tree unmoved, package digest `sha256:c5a27421...f789c` (equals the
Performance verifier's; it differs from the reviewer's `c9db5de2...`
by the pass-1 prose bytes only — triple `--code-digest` identity
below is the binding proof):

- F1 `grep -c "delegating siblings"
  django_strawberry_framework/_django_patches.py` → `0`
  (`review-20260928T212830-f39044`).
- F2 `grep -c "sibling patches' delegation"
  django_strawberry_framework/_django_patches.py` → `0`
  (`review-20260928T212835-139f61`).
- F3 `grep -c "restores the wrapper" tests/testing/test_wrap.py` →
  `0` (`review-20260928T212840-33d786`).
- F4 `grep -c 'ensure current state" contract called out in the
  module' tests/test_django_patches.py` → `0`
  (`review-20260928T212842-6fb8af`).
- F5 `grep -c "module docstring's reload-safety promise"
  tests/test_django_patches.py` → `0`
  (`review-20260928T212845-5324f1`).
- L1 `grep -c "Defensive replacement for"
  django_strawberry_framework/_django_patches.py` → `0`
  (`review-20260928T212849-88f072`).
- L2 `grep -c "documented contract"
  django_strawberry_framework/_django_patches.py` → `0`
  (`review-20260928T212851-c0056c`).

No other Proof names this axis: neither the Performance nor the
Mechanics record carries a `## Cross-axis` section, and this
record's own `## Cross-axis` is None.

Numbers: none owed (prose-only pass; Worker-2 claims none and
`## Bench baseline` is untouched).

Whole-diff reading, graded as the whole docstring or comment block
each hunk sits in:

- F1 audited-set comment block (target lines 158-179): true. The new
  contrast ("the way it does for a delegating wrapper") quantifies
  over the mechanism, not the siblings, so no sibling gaining a
  second patch can rot it; the reflowed tail ("pins these sources so
  any body OUTSIDE the audited set ... fails loudly at apply()
  time") matches the `_validate_upstream_shape` raise. First-line,
  imperative-mood, and provenance rules do not apply to `#` blocks;
  the block states rationale, not code.
- F2 `_validate_upstream_shape` docstring (lines 234-247): true. The
  new mechanism sentence ("The body pin is the reimplementer's
  equivalent of a delegator's call-shape check ...") claims nothing
  about any sibling; the "Three tiers" lead and the drift tail match
  the three raises. The reflowed line 244 is 90 chars, within limit.
- L1/L2 `_patched_remove_databases_failures` docstring (lines
  317-352): true. New first line is imperative ("Remove ...") and
  states the body's behavior (unwrap `_DatabaseFailure` instances,
  leave foreign replacements); the new symmetry sentence ("the
  symmetric contract the pair implements - ... operate on the methods
  they themselves wrapped") claims the implementation contract the
  installed Django 6.1 pair shows, not documentation.
- F4 `test_apply_is_idempotent` docstring (lines 63-68): true. The
  pointer names `_patch_is_installed`, whose docstring is the only
  site of "ensure current" in the target (live line 376); the module
  docstring holds none. First line states behavior, not "Tests that".
- F5 reload-test docstring as landed, reflow included (lines 671-687):
  true. "The reload-safety promise in the
  ``_captured_upstream_descriptor`` docstring held for the NEXT
  ``apply()``" is grammatical and the pointer resolves: that
  docstring promises reload recovery (live lines 139-145), and
  `grep -i reload` on the target matches only it and the
  `_validated_...` comment — never the module docstring.
- F3 composition-test docstring (lines 118-131): true. "Unwraps
  Django's wrapper, restoring the original method" matches the body
  (`assert connection.cursor is sentinel_original`, line 162) and
  the second paragraph, and now agrees with the pre-existing inline
  comments ("Should restore the original cursor cleanly", "Wrapper
  unwrapped to the sentinel original").

Instruments (all static, shared tree):

- `build_tree_md.py --list-docstrings` on the three changed files:
  3 modules, 0 breaking the first-line rule.
- `check_citations.py --paths <three files> --substrings --json`:
  0 citations, 0 violations (the files cite only Sphinx roles, as at
  review).
- `review_inspect.py --code-digest 8482f9a9...:<path> <path>`:
  exit 0, both digests equal, on all three files (target
  `ae7b3d6e...c6009`, `tests/test_django_patches.py`
  `8970b55a...6473815`, `tests/testing/test_wrap.py`
  `169dd93c...257515`), matching Worker-2's and both sibling
  verifiers' prefixes. Direct baseline comparison: both other axes
  closed no-findings, so no reconstruction is owed.
- Prose diff (`review_changed_python_diffs_against_head.py
  8482f9a9 --against worktree --prose ... --path <each file>`,
  under `verify-comments-1/diff/`): zero `[code changed too]`
  markers; the F5 hunk lands exactly the reflow Worker-2 records.

Diff hygiene (on the 18 added lines of `pass-1.diff`): the REVIEW.md
provenance `grep` (spec/card/round/worker/legacy/moved-from/no-longer/
previously/now/fix-for) matches nothing; no `we`/`you`/`I`; no
line-number citation (`:[0-9]+`, `line N`). No module first line
changed on any of the three files (live `head -3` identical to
`ITEM_BASELINE`), and `git diff <ITEM_BASELINE> -- docs/TREE.md` is
empty, so no render was owed. Worker-2's proposed `## Owned changes`
rows match the diff's paths, axis, and symbols (the plan ledger holds
no `_django_patches.py` rows yet).

Attacks on the landed prose (all pass, no new finding):

- F1/F2 mechanism framing: grounded in a real delegator —
  `_graphql_core_patches.py` line 6 ("The delegating wrapper") and
  `_patched_complete_list_value` calling its captured original, so
  upstream body changes do flow through that delegated call. Sibling
  fingerprints equal the record's (`2b39199b...`, `52bf8f57...`,
  `a188b290...`): the same text was graded.
- L1 first-line scope ("foreign replacements"): a never-wrapped
  method is also left untouched but is not a "foreign replacement";
  the first line summarizes truly as far as it states, and the
  docstring body ("declines to crash on a method the pair never
  owned") covers the remainder. Not stale.
- F4/F5 pointer exclusivity re-derived live (paragraph above), not
  trusted from the record.
- No touched symbol holds other prose the change could falsify: the
  diff moves zero code, so every unchanged line in the six graded
  units keeps the truth value the review pass gave it.

Disputes: none — `## Implementation (Worker-2)` carries zero
`disputed:` lines; nothing to judge. Sibling verifiers route
nothing to Comments (Performance: "Nothing routes elsewhere";
Mechanics: "Open threads: none"). No new problem on this axis, no
`verify 1` finding, no gap for `## Decisions`.

Cells: default only; sharded and pg remain inapplicable by
construction (prose grading opens no database; the seven workspace
runs are static greps). Cells unverified: none. No failability or
test-tier proof owed (prose-only; no node gained or lost — the
`def`/`class` add/del count over the diff is 0).

Fingerprints (`git hash-object`, live tree as verified):
`django_strawberry_framework/_django_patches.py`
6918a213170ea902386a5845da8c6cd1f901baf2;
`tests/test_django_patches.py`
6e62c784389b0490e174ae5825d9ebdb9428199a;
`tests/testing/test_wrap.py`
6818d96b50e848393592be1a84e4be836545ec01 — all equal Worker-2's
after-hashes and both sibling verifiers'.

Scratch: `docs/review/temp-tests/_django_patches/verify-comments-1/`
(prose `diff/` render only). The copy at
`review/_django_patches.py/verify-comments-1` was never edited (every
header reads `fresh`).

Non-blocking observation (not a finding): F4 names its target in
single underscores ("_patch_is_installed docstring") while F5 uses a
double-backtick literal; both pointers resolve and read true, and
markup consistency is style, which is not a finding.

Verdict: verified. Seven findings implemented, every landed unit
grades true, prose-only identity proven three ways (hash-equal item
diff, triple `--code-digest` equality, zero-marker prose diff).

Handoff: Verification is complete with no new finding: seven proofs
run before reading the implementation report, six prose units graded
whole against live bodies and pointer targets, attacks pass, no
dispute to judge, no cell left unverified. The one fact a later pass
must not misread is the package-digest change (`c9db5de2...` →
`c5a27421...`): it is the pass-1 prose bytes, not a code change. The
routed `testing/_wrap.py` "installs unconditionally" lead already
sits in the plan's `## Decisions` and was correctly left untouched
(out of this item's fence). Nothing routes elsewhere; no open thread
on Comments.
