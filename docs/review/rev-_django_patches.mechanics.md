# Review · Mechanics: `django_strawberry_framework/_django_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8482f9a925f3c073013b20e7ef783e9dc5c1ac3e

## Trace

Target read whole at blob `63f3fa9c` (live; equals ITEM_BASELINE; HEAD and
CYCLE_BASELINE are `ba98f585`). The HEAD-to-live delta is the truthful-reads
switch at three sites (`SimpleTestCase.__dict__.get` plus
`getattr(..., "__func__", None)` becomes `truth.class_dict` plus
`truth.is_instance`), plus the `truth` import; the dispatch notes the target
dirty with concurrent work, and this review fingerprints the live text it
graded. Orientation: `review_inspect.py` into
`docs/review/temp-tests/_django_patches/mechanics/inspect/` (json
`docs/review/temp-tests/_django_patches/mechanics/_django_patches.json`),
leads only.

Callers and contracts followed: `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
(dispatches `django_strawberry_framework/_django_patches.py::apply` first of
four, behind function-local imports);
`django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method`
(imports `django_strawberry_framework/_django_patches.py::_is_database_failure`;
wrap-time half); `django_strawberry_framework/testing/__init__.py`
(re-export); `django_strawberry_framework/conf.py::upstream_patches_enabled`
(the `APPLY_UPSTREAM_PATCHES` gate plus its mapping contract);
`django_strawberry_framework/utils/truth.py` (`class_dict`, `is_instance`
scope) and `django_strawberry_framework/utils/__init__.py` (cycle check);
sibling scaffolds `django_strawberry_framework/_strawberry_patches.py::apply`,
`django_strawberry_framework/_cross_web_patches.py::apply` (with
`_captured_upstream_body_getter`), and
`django_strawberry_framework/_graphql_core_patches.py::apply` (with
`_captured_upstream_method`) for capture, validation, installed-check, and
gate comparison; `django_strawberry_framework/__init__.py` (no patch import:
the module loads only via `ready()`). Oracles read whole:
`tests/test_django_patches.py` (25 rows: idempotence, self-heal, hierarchy
inheritance, unwrap-vs-skip, crash-pin against the installed Django,
symbol/signature/body drift, both audited bodies, both read paths,
unvalidated-shape raise, sourceless raise, global and per-dependency gates,
reload preservation, drift-plus-opt-out coupling), `tests/test_apps.py`
(dispatch plus double-reload capture retention), `tests/testing/test_wrap.py`
(wrap-time half plus the decline case and the symbol-missing case), and the
`upstream_patches_enabled` rows of `tests/base/test_conf.py`. Standing
contracts: `docs/GLOSSARY.md` anchors "Django Trac #37064 hardening",
"Upstream patches", and "`safe_wrap_connection_method`"; `docs/README.md`
(error policy and mutation envelope: no decision reaches test teardown);
`docs/TREE.md` rows. Installed Django 6.1 seam read in `.venv`
(`_DatabaseFailure`, `_add_databases_failures`, `_remove_databases_failures`:
feature-flag shape, class attribute gone). Plan `docs/review/review-0_0_15.md`
`## Owned changes` holds no `_django_patches.py` rows (item `reviewing`).
Sibling axis records absent at read time (only `docs/review/rev-_django_patches.md`
skeleton exists): no Handoff or Cross-axis sections to absorb.

Workspace runs, address `review/_django_patches.py/mechanics`, package digest
`sha256:c9db5de2850d3927acc630e053b2bb80ccd439b8471dfdaca71257bb0eae97c9`,
cell `default`, each copy `fresh`, shared tree unmoved since sync:

- `review-20260928T210107-1b5cda`:
  `pytest tests/test_django_patches.py --no-cov -q`, 25 passed.
- `review-20260928T210127-17a895`:
  `pytest tests/test_apps.py tests/testing/test_wrap.py --no-cov -q`, 23 passed.

Cells: `sharded` and `pg` inapplicable by construction. The module iterates
the connection registry uniformly (`for alias in connections`, every alias
outside `cls.databases` handled identically), emits no SQL, reads no vendor
flag, and branches on nothing dialect- or alias-count-dependent: the
`isinstance` guard and the validated-body read-path discriminator behave
identically per alias on every vendor. The verifier judges.

Fingerprints (`git hash-object`):
`django_strawberry_framework/_django_patches.py`
63f3fa9cba4369ce485a311c8d4f16e78c921768;
`django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/testing/_wrap.py`
0df97813659bea9ed2002f64e6885896c5cabd6f;
`django_strawberry_framework/testing/__init__.py`
48b45d1b433283c40bf8d602d71a26d261a833b2;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`django_strawberry_framework/utils/__init__.py`
1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee;
`django_strawberry_framework/_strawberry_patches.py`
2b39199bb2de42e40ae49d62bd24cc8a7a962c1b;
`django_strawberry_framework/_cross_web_patches.py`
52bf8f5712d632817587f93c4eeb881fd74ffaae;
`django_strawberry_framework/_graphql_core_patches.py`
a188b290b24bce07198611cef7c37935f7a437d1;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`tests/test_django_patches.py`
e26a26099c12efb2e2cab1e324b73226eab5dd76;
`tests/test_apps.py` 5ca8b62c53185343ebfec95315f59ec6104fc851;
`tests/testing/test_wrap.py` 4d3c1351254377197994ee577e4f77844c7c309b;
`tests/base/test_conf.py` 55b333eb2fff714365058d0a8651fc3a57c603e3;
`docs/GLOSSARY.md` 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd;
`docs/README.md` 30978c34f63a833ffcc0fa11c80b773d241921be;
`docs/TREE.md` 769c274392d055c566a2b2d3006afc7baa5d0a9c.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

- **R1: patch-owner attribute literals repeated across the four patch
  modules.** Each module defines its own `_PATCH_OWNER_ATTRIBUTE` /
  `_PATCH_ORIGINAL_ATTRIBUTE` with the same string values. DRY change
  challenge ("rename the protocol attribute"): each module's capture,
  stamp, and installed-check reference only its own module's constants,
  and no two modules patch the same upstream method, so each can rename
  alone — a stale in-flight wrapper under the old name misreads as
  upstream and fails loud at validation rather than silently corrupting.
  The four need not change together for correctness, only for cosmetics,
  and a shared owner would couple the one-module-per-dependency
  retirement lifecycles (each module deletes outright when its upstream
  retires). Reopen: a second protocol attribute appears, or two modules
  patch one method.
- **R2: capture, validation, installed-check, and `apply` scaffolds look
  alike across siblings.** They pin different upstream contracts:
  different methods, arities (`(cls)`, `(self)`, six-param list
  completion), descriptor types (classmethod, plain method, property),
  and validation depths (delegators pin call shape; reimplementers pin
  body source — this module's
  `django_strawberry_framework/_django_patches.py::_validate_upstream_shape`
  pins both audited bodies because
  `django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures`
  supersedes the loop). Similar shape, separate reasons to change.
  Reopen: a shared helper that preserves per-module retirement and the
  delegator-vs-reimplementer depth distinction.
- **R3: `testing/_wrap.py` imports private `_is_database_failure` from
  private `_django_patches`.** The predicate has one owner (this module,
  which also owns the `_DatabaseFailure` import fallback), so the
  wrap-time and unwrap-time halves cannot drift on what counts as the
  wrapper; the direction is subpackage to root with no cycle (`truth`
  is stdlib-only, `conf` never imports the patch). Duplicating the
  two-line check or minting a third owner for one predicate is worse.
  Reopen: a second predicate consumer outside this defense-in-depth pair.
- **R4: sibling capture accepts any `django_strawberry_framework.*`
  owner; this module requires its exact owner.** No contract source
  establishes cross-module wrapper recovery, and no two modules patch
  the same method today, so both checks behave identically on every real
  input; the exact match here is the fail-closed one (a sibling wrapper
  would validate as drift and raise rather than unwrap foreign state).
  Reopen: two modules patch one method, or a retirement moves a patch
  across modules.
- **R5: the `_DatabaseFailure` ImportError fallback never runs on
  supported Django.** It is a drift guard, not dead code: without it a
  future Django missing the symbol fails at `ready()` import time with a
  bare ImportError instead of the targeted RuntimeError naming the
  per-dependency opt-out. The `None`-value handling it enables is pinned
  via monkeypatch (`test_apply_fails_loudly_when_database_failure_symbol_missing`,
  the wrap helper's symbol-missing row). Reopen: Django removes the
  symbol (the branch runs) or the package decides import failure is an
  acceptable diagnostic.
- **R6: the validated-source string discriminator is not a mode flag.**
  `django_strawberry_framework/_django_patches.py::_disallowed_connection_methods`
  branches on the validated audited body itself, which carries the proof
  and raises fail-closed on any third value; an enum would lose the
  proof, and the per-connection string comparison runs at teardown
  frequency only. Reopen: a third audited shape, or per-shape reads grow
  past one helper.
- **R7: `apply()` validates and stores before the installed check, so a
  re-entrant call revalidates rather than pure-no-op.** Correct: drift
  fails loud even when the patch is already installed, and a failed
  validation raises before the store, preserving the prior validated
  value for the running teardown. The "no-op" contract means "no
  reinstall", which the installed check delivers. Reopen: validation
  cost matters (it runs at app-load cold frequency).
- **R8: disallowed-method and connection reads use plain attribute
  lookup, not truthful reads.** `cls._disallowed_connection_methods`,
  `connection.features.*`, and the per-method `getattr`/`setattr` are
  Django and test-case objects, not consumer identity facts; `truth`
  scope is consumer classes. The installed-Django 6.1 `_add` path
  confirms the symmetry claim (feature flag only; a legacy class
  attribute would be ignored upstream, so the validated-body
  discriminator must ignore it too). Reopen: the truthful-reads gate
  flags these sites, or a hostile-metaclass test case becomes a
  supported input.
- **R9: the non-classmethod descriptor sub-branch has no dedicated
  oracle.** `test_apply_fails_loudly_when_database_failure_symbol_missing`
  pins the combined `or` via the `None`-symbol half; no row feeds a
  non-classmethod (or absent) `_original_remove_databases_failures`
  alone. The code is still correct and fail-closed (a future
  descriptor-type drift raises the classmethod RuntimeError rather than
  reaching `inspect.signature` on `None`), and statement coverage
  passes; the gap is hardening, not a code defect, so no finding.
  Reopen: a refactor touches the condition, or branch coverage is
  enforced.
- **R10: `_is_database_failure` returns False when the symbol is
  missing.** Correct for both callers: the patch never installs in that
  state (validation raises first), and the wrap helper must install when
  there is no wrapper to preserve (pinned by the symbol-missing wrap
  row). Reopen: a caller needs to distinguish "unknown" from "absent".

Looks-for discharge (REVIEW.md "Mechanics"):

- rule at a caller instead of its owner: none. The unwrap guard lives in
  the teardown replacement that owns the unwrap step (callers cannot be
  trusted to cooperate); the gate lives in each `apply()` via
  `django_strawberry_framework/conf.py::upstream_patches_enabled`, not in
  the `ready()` dispatcher; the read path lives in
  `django_strawberry_framework/_django_patches.py::_disallowed_connection_methods`;
  validation lives in
  `django_strawberry_framework/_django_patches.py::_validate_upstream_shape`,
  not at callers.
- policy in an adapter / mechanism in a policy layer: none. The module is
  pure mechanism; gating policy lives in `conf`; the test-only versus
  production-hardening split is respected (this key drops only this
  module).
- contract sources vs body: none. The three GLOSSARY anchors, every owner
  docstring (module plus all seven functions), and all four oracle files
  match the body; `docs/README.md` error and mutation contracts reach no
  test-teardown path.
- branch no real path reaches: none. Every branch has a pinned path:
  ImportError fallback is the R5 drift guard; reload recovery via the
  reload row; all three validation tiers via drift, signature, and
  sourceless rows; all three read-path outcomes via the two shape rows
  plus the unvalidated raise row; both guard outcomes via the unwrap and
  skip rows; all three installed states via installed, foreign, and
  absent rows; both gate outcomes via the global and per-dependency rows
  (R9 names the one unpinned sub-condition, whose drift path is real).
- mode flag standing in for a named adapter: none (R6; the mapping keys
  are the adapter names per the one-module-per-dependency rule).
- state owned in two places: none. The import-time capture, the
  function-carried original, and the live class attribute are three
  distinct roles joined by the reload protocol (pinned by the reload and
  double-reload rows); the validated source is a derived cache written
  only by `apply()` and read only at teardown, preserved across reload
  by construction (R1, R2 for the shared literals and scaffolds).
- dependency direction: none. Root to `conf` and to stdlib-only `truth`
  (no cycle; `utils/__init__.py` pulls only relations, strings, typing,
  none of which import back); testing to root per R3; no `TYPE_CHECKING`;
  function-local `ready()` imports keep the package import free of the
  patch and its Django test imports.
- `django.conf.settings` at import: none (no `django.conf` import; the
  setting is read inside `apply()` through the gate).
- `__all__` vs public surface: none. The private module carries no
  `__all__`, like all three siblings; `apply` is exported for `ready()`
  and the regression tests, `_is_database_failure` shared with the wrap
  helper, and no star-import surface exists.
- two sites implementing one rule: none. DRY challenges run: attribute
  literals (R1), scaffolds (R2), the isinstance predicate (single-owned
  per R3), the audited-body set (single-owned; test shapes are oracles,
  not definitions), the signature-check idiom (different contracts per
  method).
- sync/async twins: none (one sync classmethod replacement; no async
  twin exists).
- guard one flavor has and a sibling lacks: none. Capture, validation,
  and installed-check differences track descriptor types and
  delegator-versus-reimplementer depths; the owner-breadth difference is
  R4 and the truth-scope difference is R8, neither established by a
  contract source as a missing guard.

Handoff: read beyond the record the full `truth` scope contract (why R8
holds), the `_strawberry_patches` retirement lifecycles (why R2 holds),
the `conf` gate implementation plus its whole-mapping validation rows,
and the installed-Django 6.1 `_add`/`_remove` pair (why the
validated-body discriminator, not attribute presence, is the correct
symmetry). Conclusions the rejections do not state: every drift seam in
the file fails loud with the opt-out named; the HEAD-to-live
truthful-reads switch preserves behavior (both oracle runs green on the
live text); the two most likely future edits — a third upstream body and
a protocol-attribute rename — both fail loud today rather than silently.
Open threads: R9's dedicated non-classmethod oracle is the only
hardening I would accept on a touch of that condition; R4 could unify
if the patch family ever shares a method. No Mechanics lead routes to
another item, and no Cross-axis finding: Performance and Comments
siblings were absent at read time, and nothing observed belongs to them.
Scratch kept: `docs/review/temp-tests/_django_patches/mechanics/`
(`inspect/`, `_django_patches.json`); no probe scripts — the two oracle
suite runs above are the evidence.

## Verification (Mechanics)

Step 1 (the tree carries the sent change): `git diff
8482f9a925f3c073013b20e7ef783e9dc5c1ac3e --
django_strawberry_framework/_django_patches.py
tests/test_django_patches.py tests/testing/test_wrap.py` hashes equal
to `docs/review/temp-tests/_django_patches/diff/pass-1.diff` (sha256
77d81a7d1f05ecb50021a910de4860313499016a3c1f8375a165f04c6e899871,
5775 bytes on both sides). Pass; grading proceeds.

Proof lines: none owed, none run. This record holds zero findings, so
it carries no Proof line; the Performance record states no finding
carries one; the Comments record's `## Cross-axis` is None, so no
foreign Proof names this axis. No `workspace.py` run was made at
`review/_django_patches.py/verify-mechanics-1`; every check below is
static in the shared tree. No run ids.

Numbers reproduced: Worker-2 reports no Mechanics number (prose-only
pass: no before/after, no bench delta, `## Bench baseline`
untouched). The behavior-preservation evidence is the inverse
`--code-digest` proof, reproduced verbatim for all three item paths,
exit 0 with both digests equal on each, matching Worker-2's prefixes:
the target `sha256:ae7b3d6e...c6009`,
`tests/test_django_patches.py` `sha256:8970b55a...6473815`,
`tests/testing/test_wrap.py` `sha256:169dd93c...257515`. Log:
`docs/review/temp-tests/_django_patches/verify-mechanics-1/code-digest.log`.

Whole-diff reading (Mechanics): `pass-1.diff` holds 3 files and 7
hunks, each landing inside a comment or a docstring (F1 audited-set
comment; F2 `_validate_upstream_shape` docstring; L1/L2
`_patched_remove_databases_failures` docstring; F4/F5
`tests/test_django_patches.py` docstrings; F3
`tests/testing/test_wrap.py` docstring). No owner move, no
contract-behavior change, no new dependency, no state-ownership
change, no symbol renamed or moved. The F5 reflow changes docstring
wording only. Worker-2's proposed `## Owned changes` rows match the
diff's paths, axis, and symbols exactly. The concurrent
truth-migration dirt sits below ITEM_BASELINE and is byte-preserved:
the baseline blobs equal this record's `## Trace` fingerprints.

Attacks (all pass, no new finding):

- Symbol and node stability: the `def`/`class` add/del count over the
  diff is 0, so no function, method, or class was added, removed, or
  renamed and no test node was gained or lost. Stripped-AST digest
  equality independently implies an identical code AST including all
  names, so no `--cited-by` sweep is owed.
- Rejections R1-R10 and every looks-for discharge grade code or
  code-shape facts; the code is identical, so all stand. R9's reopen
  trigger (a refactor touches the condition) is not tripped: the
  combined-or condition is untouched.
- Docstring consumers: no `__doc__`, `doctest`, or `getdoc`
  reference in the four oracle files, and no `getsource`/`getcomments`
  read of this module's own text there, so no oracle can observe the
  new prose. No column-0 docstring hunk exists in the diff, so no
  module first line changed and no TREE.md render is owed.
- Revert proof: vacuous. No production code hunk exists to
  reverse-apply, so no `prove` manifest is owed or run.

Disputes: none recorded (`disputed:` matches nothing in the main
artifact); nothing to judge.

Lint gates (`--check` forms only; log
`docs/review/temp-tests/_django_patches/verify-mechanics-1/lint.log`):
`ruff check` on the three touched paths passes; `ruff format --check`
passes (3 files already formatted);
`check_trailing_commas.py --check` on the three paths passes (0
violations); `check_citations.py --check` tree-wide passes (1297
citations resolve).

Cells: sharded and pg remain inapplicable by construction (this
record's reason stands; a prose change reaches no database path). No
cells unverified.

Fingerprints (`git hash-object`, live):
`django_strawberry_framework/_django_patches.py`
6918a213170ea902386a5845da8c6cd1f901baf2;
`tests/test_django_patches.py`
6e62c784389b0490e174ae5825d9ebdb9428199a;
`tests/testing/test_wrap.py`
6818d96b50e848393592be1a84e4be836545ec01. All equal Worker-2's
reported after-hashes.

Verdict: verified. Zero Mechanics findings stood, zero needed
implementation, and the prose-only pass moved no code.

Handoff: Beyond this record's trace I read the whole item diff, the
whole live target, the Performance and Comments records with their
handoffs (both place no Mechanics cross-axis text), the artifact's
`## Implementation (Worker-2)` and `## Defects`, and the plan's
`## Owned changes` (which holds no `_django_patches.py` rows yet;
Worker-2's proposal matches the diff). Conclusions the checks do not
state: the F5 reflow is the only judgment call in the pass and is
behaviorally inert; the baseline-vs-HEAD truth delta is concurrent
work outside the item fence and is preserved byte-for-byte. Open
threads: none on Mechanics. Scratch kept:
`docs/review/temp-tests/_django_patches/verify-mechanics-1/`
(`code-digest.log`, `lint.log`); no workspace copy was bound.
