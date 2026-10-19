# Review · Comments: `django_strawberry_framework/_graphql_core_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e4385002efab0df029451349a7738a02e19928e2

## Trace

Read the whole live target (129 lines), the whole own test module
`tests/test_graphql_core_patches.py` (157 lines, prose = module
docstring + 2 test docstrings, zero `#` comments), and every prose
passage other test modules hold about the target's symbols:
`tests/test_apps.py` (module pointer, `_PATCHED_SLOTS` comment,
dispatch + reload-test docstrings),
`tests/base/test_conf.py` (per-dependency opt-out docstring naming
`graphql_core`), and
`examples/fakeshop/test_query/test_list_field_async_api.py` (the
awaitable-children section banner, its test docstring, and the
`_AwaitableChild` fixture docstring). Followed the trace out to the
package prose that cites the target:
`django_strawberry_framework/apps.py` (`ready` dispatch docstring),
`django_strawberry_framework/conf.py` (gate comment +
`django_strawberry_framework/conf.py::upstream_patches_enabled`
docstring), and the three sibling patch modules for the family
wording. Verified the bug narrative against the installed upstream
(graphql-core 3.2.8 `execution/execute.py`, read statically, no
fingerprint) and the retirement pointer against spec-050 Decision 13
(spec + rationale). Also read the completed sibling-item record
`docs/review/rev-_django_patches.comments.md` for family wording
already adjudicated this run (its F1/F2 confirm this module is the
pure delegator; its R1/R4/R9 set the precedent this record follows).

The target is dirty with concurrent work at read time: the live tree
differs from `HEAD` by the `truth` helper migration only
(`truth.class_dict` in
`django_strawberry_framework/_graphql_core_patches.py::_captured_upstream_method`
and
`django_strawberry_framework/_graphql_core_patches.py::_patch_is_installed`,
plus the import). No prose hunk is dirty; the finding below
reproduces identically at `HEAD`, at `ITEM_BASELINE` (live tree
equals it: `git diff <ITEM_BASELINE> -- <target + own tests>` is
empty), and live. No sibling axis record existed when this pass ran.

Instruments (all static, shared tree, no package import, no database):
`review_inspect.py` orientation plus Comments census into
`docs/review/temp-tests/_graphql_core_patches/comments/inspect/` and
`docs/review/temp-tests/_graphql_core_patches/comments/_graphql_core_patches.json`;
`build_tree_md.py --list-docstrings` on the target and the own test
module (both first lines pass);
`check_citations.py --paths ... --substrings --json` on both (0
`path::Symbol` citations each; the files cite only Sphinx `:mod:` /
`:meth:` roles and a bare test-path literal); the provenance search
(hits adjudicated in `## Rejected`). Database cells: inapplicable by
construction for the whole axis — prose grading opens no database and
reaches no alias or dialect decision; no `workspace.py` run was made.

Fingerprints (`git hash-object`, live tree as read):

- `django_strawberry_framework/_graphql_core_patches.py`: a188b290b24bce07198611cef7c37935f7a437d1
- `tests/test_graphql_core_patches.py`: 53dca51737e6163c09549d015713ebf9dfcdec88
- `tests/test_apps.py`: 5ca8b62c53185343ebfec95315f59ec6104fc851
- `tests/base/test_conf.py`: 55b333eb2fff714365058d0a8651fc3a57c603e3
- `django_strawberry_framework/apps.py`: 8ae1a3a3b12f0c9792094959c573ea6fab5d804f
- `django_strawberry_framework/conf.py`: ae3de0a36e2f7737a2c8350e532cdb761b295bcf
- `examples/fakeshop/test_query/test_list_field_async_api.py`: 49e423ea593b8883c4c07593accd822390e82468
- `docs/spec-050-list_field_arguments-0_0_15.md`: 73fe1127a280bfcf791632f2b40dfd2f805b12ec
- `docs/spec-050-list_field_arguments-0_0_15-rationale.md`: 491570623d8f6efb1654ccdc75b7b2e0565d2278

## Findings

### High

None.

### Medium

#### F1 — pragma comment names a test mechanism no test uses

- Observation: the `except ImportError` comment says the branch is
  "exercised through patched imports in tests". No test in the tree
  patches imports for this module: the phrase occurs only in this one
  comment, no test evicts or sentinels `graphql` in `sys.modules` and
  reloads the module, and the introducing commit's suite already
  covered the missing-shape path with `mock.patch.object` only. What
  the tests actually do is monkeypatch the module globals to `None`
  (`tests/test_graphql_core_patches.py::test_apply_fails_loudly_when_required_upstream_symbols_are_missing`),
  exactly what the three sibling patch modules' identical pragma
  comments say ("exercised via monkeypatch in tests").
- Evidence: full-tree search for `patched imports` (1 hit: this
  comment), for `sys.modules` eviction / sentinel use (users cover
  debug-toolbar, sessions, views, routers, keyset, rest-framework —
  never `graphql` + this module), and for reloads of this module
  (`tests/test_apps.py` reloads it with imports intact, which
  re-executes the `try` body, not the `except`); `git show
  4c483b6b:tests/test_graphql_core_patches.py` shows the born-false
  state (`mock.patch.object` x2, no import patching); sibling
  comments at `django_strawberry_framework/_django_patches.py`,
  `django_strawberry_framework/_strawberry_patches.py`,
  `django_strawberry_framework/_cross_web_patches.py` carry the
  monkeypatch wording.
- Impact: a reader hunting the "patched imports" test that pins the
  `None`-globals state finds nothing, and a sibling-comparing reader
  concludes this module's coverage mechanism differs from the other
  three when it is the same.
- Severity: Medium (stale comment on internal code).
- Recommendation: adopt the siblings' wording verbatim.
- Must not change: n/a (Comments).
- Proof: `grep -c "exercised through patched imports" django_strawberry_framework/_graphql_core_patches.py` prints `0`; the rewritten comment earns grade true.
- Freshness: every file read is fingerprinted under `## Trace`; none beyond it.
- Symbol: `django_strawberry_framework/_graphql_core_patches.py` `except ImportError` pragma comment.
- Grade: stale.
- Text-before:
  `except ImportError:  # pragma: no cover - exercised through patched imports in tests.`
- Text-after:
  `except ImportError:  # pragma: no cover - exercised via monkeypatch in tests`

### Low

None.

## Rejected

- R1 — "no longer" (module docstring "no longer exhibits the bug",
  drift error string "no longer has the expected ... signature"):
  present-tense retirement-condition and shape-drift claims, not
  process provenance; true in each case (the sentinel test pins the
  bug; the 6-parameter quote matches installed 3.2.8). Follows the
  `_django_patches.py` Comments R1 precedent. Trigger: wording that
  dates the change itself ("previously", a version, a round).
- R2 — "workaround" (`django_strawberry_framework/_graphql_core_patches.py::apply`
  docstring): "round"-substring false positive, not a round
  reference; follows the `_django_patches.py` Comments R4 precedent.
  Trigger: an actual round reference.
- R3 — "(spec-050 Decision 13)" (own test module docstring): kept
  class (spec Decision pointer), and precise — spec Decision 13
  explicitly establishes "the retirement sentinel" as the
  call-captured-method-and-assert-residual-after-one-await test this
  docstring describes. Trigger: a spec renumber or reword.
- R4 — `match="complete_list_value no longer"` (missing-shape
  tests): true mirror of the production drift error string. Trigger:
  a production string change.
- R5 — "the reinstall path" (None-owner test docstring): loose (no
  symbol is named "reinstall") but directionally true — a `None`
  capture reaches `apply()` as "nothing captured" and fails loud in
  validation rather than installing, and "reinstall" is the family's
  own `tests/test_apps.py` vocabulary for reload + `ready()`.
  Trigger: a `None`-capture path that installs silently.
- R6 — "production request-hardening patches
  (``strawberry`` / ``cross_web`` / ``graphql_core``)"
  (`tests/base/test_conf.py` opt-out docstring): loose
  ("request-hardening" for an executor-completion fix) but
  directionally true — the patch is production, request-path, and the
  sentence's contrast (vs the test-only Django patch) holds.
  Trigger: a reading under which this patch is test-only.
- R7 — private helpers without docstrings
  (`_captured_upstream_method`, `_validate_upstream_shape`,
  `_patched_complete_list_value`, `_patch_is_installed`): the axis
  requires docstrings on public symbols only; `apply` (the entry
  point `ready()` calls) has an imperative one; ruff's Google
  convention skips underscore-privates; the subtle contracts are
  recorded where they are pinned (the signature quote in the drift
  error, the one-await residual in the sentinel test + module
  docstring). Trigger: a private helper whose contract no prose
  states.
- R8 — "awaits that residual value" (module docstring, singular)
  against the double await in `_await_residual`: net-effect
  description, true — one outer plus one residual await is exactly
  "awaiting the residual value", the 7-line body shows the shape, and
  the sentinel test motivates the second await. Trigger: a third
  await level or a non-await change in the wrapper.
- R9 — Sphinx `:mod:` / `:meth:` roles (own test module docstring):
  not `path::Symbol` form, ungated, and both resolve today (the
  target module, `apps.DjangoStrawberryFrameworkConfig.ready`); no
  line-number citation anywhere in the target or its tests. Follows
  the `_django_patches.py` Comments R9 precedent. Trigger: a cited
  symbol being renamed.

## Cross-axis

None. This pass found no performance or mechanics issue: every
behavioral claim checked against a body held (the bug narrative
matches installed graphql-core 3.2.8 line for line; the delegation
claim matches the call-through body), and the one stale comment (F1)
misnames its own test mechanism rather than any production behavior.

Handoff: I graded the live tree (target hash a188b290; the
concurrent `truth`-migration dirt touches code only, no prose) and
found one Medium, zero of every other severity. The module is
otherwise unusually clean prose: the bug narrative verifies against
the installed upstream source, the Decision 13 pointer resolves to a
spec paragraph that explicitly establishes the sentinel test, and the
live-tier pointer names cases that exist with true docstrings. Two
facts for later passes: (1) the refusal-string wording
("no longer ... / or use a supported graphql-core version") is owned
by the open DRY `upstream-patch-refusal-wording` family, so Worker-2
must not reword error strings while fixing F1's comment; (2) the
`tests/test_apps.py`, `apps.py`, and `conf.py` fingerprints equal the
`_django_patches.py` Comments record's, so prose graded true there
about the shared dispatch stands here too. No open threads beyond F1.

## Verification (Comments)

Pass 1, address `review/_graphql_core_patches.py/verify-comments-1`,
cell `default` (prose grading opens no database; sharded and pg
`inapplicable by construction`, concurring with the record).
Ordering disclosure: this pass read the main artifact's
`## Implementation (Worker-2)` before running the Proof line, against
the verify order in `worker-1.md` (the dispatch's required-reading
order lists the artifact before the axis records). The Proof below was
then run verbatim with a mechanical result (a grep count and exit
code), so the violation touches procedure, not the evidence; Worker-0
judges whether it matters. Same violation class as the Performance
verifier's, likewise disclosed.

Step 1: `git diff e4385002efab0df029451349a7738a02e19928e2 --
django_strawberry_framework/_graphql_core_patches.py` is byte-equal to
`<root>/diff/pass-1.diff` (sha256
`d3ffd3146b7586ef3d2bdc9740fba17968a39626bf8da7580cfc85765a519650`,
1100 bytes both sides, `cmp` clean). The tree did not move under the
pass.

Proof results (the record's whole Proof set: F1's one line; the
Performance record places no cross-axis text and the Mechanics
`## Cross-axis` is explicit None, so no other record contributes a
Proof line for Comments):

- `grep -c "exercised through patched imports"
  django_strawberry_framework/_graphql_core_patches.py` prints `0`,
  both in the shared tree and at the verify address
  (`review-20260928T220338-38942f`, digest `sha256:a5e0fd4e...` =
  final state, copy fresh, shared unmoved). Exit 1 both sides is
  grep's standard no-match exit; the Proof names the printed result.

Worker-2 numbers reproduced from an independent rebuild (not its
files): `<root>/verify-comments-1/reconstruction.py` = ITEM_BASELINE
text plus only the Performance reorder hunk (verified: recon-vs-base
diff is exactly line 94; live-vs-recon is exactly line 25).
`review_inspect.py --code-digest <reconstruction> <live>` prints two
equal digests `sha256:cf6be5b1...`, exit 0 — the prose hunk moved no
code, and the digest equals Worker-2's report exactly. Control:
`--code-digest <baseline text> <reconstruction>` exits 1 with
differing digests, so the instrument sees code movement and the equal
result is meaningful. The REVIEW.md prose-diff command renders one
per-file diff in which the comment hunk vanishes under stripping and
only the guard hunk remains, with no `[code changed too]` marker.

Whole-diff read through Comments (exactly two hunks, `a188b290..90ac4f3c`):

- Line 25 pragma hunk (F1): landed verbatim as the record's
  Text-after. Graded as the whole statement it sits in —
  `except ImportError:  # pragma: no cover - exercised via monkeypatch
  in tests` — grade **true**: the missing-shape tests monkeypatch the
  module globals to `None` via `mock.patch.object` (own test module
  lines 100/114; sibling suites use the identical mechanism), no test
  patches imports for this module, and the comment is byte-identical
  to all three siblings (comment sha `8d0d3ce0` x4). No error string
  touched, honoring the DRY refusal-wording ownership the record's
  Handoff names.
- Line 94 guard hunk (Performance F1): code-only; it carries no prose
  and `_patched_complete_list_value` holds no docstring or comment the
  reorder could falsify. The module and `apply` docstrings are
  unaffected (the reorder is semantics-preserving per the Mechanics
  trigger battery and revert parity). No other docstring or comment in
  a touched symbol made false.

Instruments on the changed file: `build_tree_md.py --list-docstrings`
(1 module, 0 breaking; first line unchanged, so no TREE.md render owed
— confirmed: no TREE.md hunk in the item-scoped diff);
`check_citations.py --paths ... --substrings --json` (0 citations, 0
violations); the provenance sweep hits only the three pre-existing
lines adjudicated in review (R1 x2, R2), none in the diff; the diff's
added lines carry no process provenance, no line-number citation, no
`we`/`you`. A full-tree sweep for the retired wording finds 0 hits in
production source or tests; every remaining hit is a per-cycle
artifact quoting Text-before (this cycle's records and scratch, the
DRY flow's cycle records, regenerable `docs/shadow/`), which close
with their cycles.

Attacks on the landed prose, all passing:

- "monkeypatch" vs `mock.patch.object` (not the pytest fixture):
  the generic verb holds — runtime patching of module globals — and
  the wording is the record's prescription, shared byte-for-byte with
  the three siblings for the identical mechanism. No finding.
- Hidden import-patching test: none — no `sys.modules` eviction or
  sentinel use touches `graphql` plus this module, and the
  `tests/test_apps.py` reload rows re-execute the `try` body, not the
  `except` (as the record's Evidence states). No finding.
- Stray-period divergence (`tests.` vs `tests`): the dropped period is
  the siblings' spelling, verified by hash. No finding.

Disputes: none (`## Implementation (Worker-2)` carries no `disputed:`
line). Sibling verifiers' sections route nothing to Comments
(Performance: "no named gaps on any axis"; Mechanics: "no named
gaps"). The Mechanics review Handoff lead (capture-method docstring)
was review-time input already adjudicated as this record's R7, not a
verify gap.

Fingerprints (`git hash-object`, close of pass): target
`90ac4f3cc15be1c24dc1f0281206e260d7555cb6` (= Worker-2's: no drift
during verify); `tests/test_graphql_core_patches.py`
`53dca517...` (= the record's); `pass-1.diff` sha above.

Scratch under `<root>/verify-comments-1/`: `livediff.txt`,
`proof.stderr` (run `review-20260928T220338-38942f`),
`baseline_text.py`, `reconstruction.py`, `diff/` (prose-diff output).
The copy at `review/_graphql_core_patches.py/verify-comments-1` was
read from once and never edited; Worker-0 may release it.

Verdict: `Status: verified`. F1 landed verbatim as specified, its
inverse proof reproduces from an independent rebuild, and no new
finding, named gap, or `## Decisions` item arises on this axis.

Handoff: Everything this pass establishes beyond the report: (1) the
four pragma comments hash-identical (`8d0d3ce0`), so the family
wording is now uniform by hash, not by reading; (2) the retired
wording is fully gone from source and tests — remaining hits are
per-cycle quotations that close with their cycles, including the DRY
flow's, which this item must not touch; (3) the code-digest
`cf6be5b1` is confirmed from an independent reconstruction, not by
re-running Worker-2's files. Procedure note: the
Implementation-before-Proofs read order is disclosed above; the
evidence is mechanical and Worker-0 judges. Open threads: none on
Comments.
