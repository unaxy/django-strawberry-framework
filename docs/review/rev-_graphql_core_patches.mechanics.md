# Review · Mechanics: `django_strawberry_framework/_graphql_core_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e4385002efab0df029451349a7738a02e19928e2

## Trace

Target read whole at blob `a188b290` (live; equals ITEM_BASELINE;
HEAD and CYCLE_BASELINE are `1cd579fb`). The HEAD-to-live delta is
the truthful-reads switch at two sites (`owner.__dict__.get` and
`ExecutionContext.__dict__.get` become
`django_strawberry_framework/utils/truth.py::class_dict`) plus the
`truth` import; the dispatch notes the target dirty with concurrent
work, and this review fingerprints the live text it graded.
Orientation: `review_inspect.py` into
`docs/review/temp-tests/_graphql_core_patches/mechanics/inspect/`
(json
`docs/review/temp-tests/_graphql_core_patches/mechanics/_graphql_core_patches.json`),
leads only.

Callers and contracts followed:
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
(dispatches
`django_strawberry_framework/_graphql_core_patches.py::apply` fourth
of four, behind function-local imports);
`django_strawberry_framework/conf.py::upstream_patches_enabled` (the
`APPLY_UPSTREAM_PATCHES` gate, its mapping contract, and the
per-dependency independence comment naming this key);
`django_strawberry_framework/utils/truth.py::class_dict` scope and
`django_strawberry_framework/utils/__init__.py` plus its leaves
(`relations`, `strings`, `typing`: `exceptions` / `truth` /
Django-ORM / function-local imports only, no cycle back to `conf` or
the patch); sibling scaffolds
`django_strawberry_framework/_strawberry_patches.py::apply` (with the
same-named
`django_strawberry_framework/_strawberry_patches.py::_captured_upstream_method`
twin),
`django_strawberry_framework/_django_patches.py::apply` (with
`django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor`),
and
`django_strawberry_framework/_cross_web_patches.py::apply` (with
`django_strawberry_framework/_cross_web_patches.py::_captured_upstream_body_getter`)
for capture, validation, installed-check, and gate comparison;
`django_strawberry_framework/__init__.py` (imports no patch module:
the module loads only via `ready()`); the package's own
`django_strawberry_framework/schema.py::DjangoMutationExecutionContext`
(a graphql-core `ExecutionContext` subclass that inherits the patched
slot and overrides no `complete_list_value` of its own — the
package-wide grep below shows the only writer is this module's
`apply()`); the second `is_awaitable` site
`django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_async`
(change-challenge peer, not a twin);
`django_strawberry_framework/utils/querysets.py::is_async_only_iterable`
(guard-predicate change-challenge peer). Oracles read whole or in
the rows named:
`tests/test_graphql_core_patches.py` (whole: 10 rows — install at
load plus idempotence, self-heal, retirement sentinel, drift
refusal, three missing-symbol refusals, independent gate, global
disable, None-owner capture),
`tests/test_apps.py` (dispatch plus the four-module double-reload
capture-retention rows),
`examples/fakeshop/test_query/test_list_field_async_api.py`
(`test_async_iterable_with_awaitable_children_completes_over_http`
plus the sync-children queryset rows it contrasts with). Standing
contracts: spec-050 Decision 13 (module home, independent gate key,
retirement sentinel) plus its rationale; `docs/GLOSSARY.md` anchors
"defensive upstream patches" (four appliers, validate-before-replace,
idempotent), "kill switch" (whole-mapping validation, `graphql_core`
owns only executor completion), "Django AppConfig" (four-module
dispatch order), and the async list adapter entry (naming this key);
`docs/README.md` (production error policy and mutation envelope:
neither reaches an app-load patch path); the card-050 floor record
(`tests/test_graphql_core_patches.py` in the 27-path floor scope,
3600 passed, none of the 37 skips in this suite — the sentinel and
the wrapper hold at strawberry-graphql 0.310-floor 0.316.0).
Installed seams read in `.venv` at graphql-core 3.2.8 /
strawberry-graphql 0.324.0: `ExecutionContext.complete_list_value`
(the `not is_iterable` / `isinstance(result, AsyncIterable)`
dispatch, the un-awaited recursive completion inside
`async_iterable_to_list`, the sync branch resolving to a plain list)
and `graphql.pyutils.is_iterable` (`Iterable` minus bytes /
bytearray / memoryview / str / Mapping). Plan
`docs/review/review-0_0_15.md` `## Owned changes` holds no
`_graphql_core_patches.py` rows (item `reviewing`). Sibling axis
records absent at read time (only
`docs/review/rev-_graphql_core_patches.md` skeleton exists): no
Handoff or Cross-axis sections to absorb. Also read (no fingerprint
owed — review inputs, not change inputs): the plan, REVIEW.md, the
role file, and `docs/review/rev-_django_patches.mechanics.md` for
shared-family consistency (its R1/R2/R4/R5/R9 shape this record's
R1/R3/R4 and the discharge list).

Workspace runs, address `review/_graphql_core_patches.py/mechanics`,
cell `default`, each copy `fresh`, shared tree unmoved since sync:

- `review-20260928T214029-52c192`:
  `pytest tests/test_graphql_core_patches.py tests/test_apps.py
  --no-cov -q`, 24 passed.
- `review-20260928T214039-96f260`:
  `python .../mechanics/probe_capture_strictness.py`, ALL OK (6/6:
  own-stamp recovery identical in both twins; sibling-stamp
  divergence pinned — this module unwraps to the sibling's original,
  the twin keeps the stamped method).
- `review-20260928T214050-50242f`:
  `pytest
  examples/fakeshop/test_query/test_list_field_async_api.py::test_async_iterable_with_awaitable_children_completes_over_http
  --no-cov -q`, 1 passed.

Cells: `sharded` and `pg` inapplicable by construction. The module
delegates one executor method, captures at import, installs at app
load; it opens no database, names no alias, reads no vendor flag,
and branches on nothing dialect- or alias-count-dependent. The
verifier judges.

Fingerprints (`git hash-object`):

`django_strawberry_framework/_graphql_core_patches.py`
a188b290b24bce07198611cef7c37935f7a437d1;
`django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`django_strawberry_framework/utils/__init__.py`
1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee;
`django_strawberry_framework/utils/querysets.py`
8fc556d582b313e4aed7cddaa15f9a8480d88a46;
`django_strawberry_framework/_strawberry_patches.py`
2b39199bb2de42e40ae49d62bd24cc8a7a962c1b;
`django_strawberry_framework/_django_patches.py`
6918a213170ea902386a5845da8c6cd1f901baf2
(drifted past the sibling record's `63f3fa9c` by that item's
prose-only implementation pass; the cited capture/gate lines
re-verified identical);
`django_strawberry_framework/_cross_web_patches.py`
52bf8f5712d632817587f93c4eeb881fd74ffaae;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`django_strawberry_framework/schema.py`
84f2d5aa51a1b42ad50835f68c5f6e7380dac7c1;
`tests/test_graphql_core_patches.py`
53dca51737e6163c09549d015713ebf9dfcdec88;
`tests/test_apps.py` 5ca8b62c53185343ebfec95315f59ec6104fc851;
`examples/fakeshop/test_query/test_list_field_async_api.py`
49e423ea593b8883c4c07593accd822390e82468;
`docs/spec-050-list_field_arguments-0_0_15.md`
73fe1127a280bfcf791632f2b40dfd2f805b12ec;
`docs/spec-050-list_field_arguments-0_0_15-rationale.md`
491570623d8f6efb1654ccdc75b7b2e0565d2278;
`docs/GLOSSARY.md` 3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd;
`docs/README.md` 30978c34f63a833ffcc0fa11c80b773d241921be;
`docs/builder/DONE/build-050-list_field_arguments-0_0_15.md`
bdb7a11559ea86ff2151557c182d49d1019dfd5e;
installed `graphql/execution/execute.py`
869f59f3f5662fc55e3dbb48023e6879dab40a8a;
installed `graphql/pyutils/is_iterable.py`
142c3a14699a6a205882cb479b9a6a8ea3b69cc9.

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

- **R1: capture accepts any `django_strawberry_framework.*`
  owner where the three siblings require exact equality.** No
  contract source establishes cross-module wrapper recovery, and no
  two modules patch the same method — the package-wide grep shows
  `complete_list_value` written only by this module's
  `django_strawberry_framework/_graphql_core_patches.py::apply`,
  and each module's stamp attribute is read only beside its own
  constants — so both checks behave identically on every real
  input; the reload rows pin the reachable (own-owner) half for
  all four modules. The probe
  (`review-20260928T214039-96f260`) pins what the unreachable half
  would do: under a hypothetical second package writer to this
  slot, this module's prefix arm unwraps the sibling's installed
  fix back to the sibling's original at the next capture (a
  reinstall then silently replaces the sibling's fix), while the
  twin's exact spelling keeps the stamped method and would
  delegate through it — the looser arm is the worse hypothetical,
  but the collision cannot occur while the slots stay disjoint.
  Reopen: a second package writer to
  `ExecutionContext.complete_list_value`, or a retirement moving a
  patch across modules.
- **R2: the guard's third conjunct (`self.is_awaitable(res)`)
  never filters with the real upstream.** The async branch is an
  `async def` factory, so a non-raising async-iterable call always
  returns a coroutine. It is fail-safe, not dead code: if a future
  upstream returned a completed list synchronously within the
  pinned signature, the wrapper would delegate it through
  untouched instead of wrapping a plain value in a coroutine. The
  `if` itself has both outcomes pinned (sync inputs delegate;
  async-iterable inputs wrap). Reopen: upstream returning a sync
  value for async-only input, or a row pinning the conjunct
  false.
- **R3: the `_patch_is_installed` None half is unreachable from
  `apply()` and unpinned.** `apply()` validates before the
  installed check, and validation raises while `ExecutionContext`
  is `None`, so the `is not None` short-circuit can only answer
  `False` to direct callers. Correct and fail-closed (an absent
  owner reports "not installed"); statement coverage passes and
  the gap is hardening, not a code defect, so no finding — the
  sibling item's R9 shape. Reopen: a direct caller needing the
  `None` path pinned, or branch coverage enforced.
- **R4: the ImportError fallback never runs on supported
  envs.** It is a drift guard, not dead code: without it an env
  missing the symbols fails at `ready()` import time with a bare
  ImportError instead of the targeted RuntimeError naming the
  per-dependency opt-out. The refusal it enables is pinned via
  monkeypatch (the three missing-symbol rows). Reopen: a
  supported env missing the symbols.
- **R5: the shape check pins arity and kinds but not parameter
  names, and would false-positive on POSITIONAL_ONLY params.**
  The delegation call is positional, so names genuinely cannot
  break it; kinds pin the audited shape, and refusing an unseen
  shape is the house fail-closed stance (a positional-only
  upstream raises the drift RuntimeError naming the opt-out
  rather than patching blind). Reopen: an upstream signature
  drift — validation raises per contract, and the sentinel
  process owns the re-audit.
- **R6: shape-only validation cannot see an upstream body change
  behind the pinned signature (a fix, or a dispatch reorder).**
  The wrapper needs no body pin by construction — it delegates,
  so bodies flow through — and each change class has its
  behavioral tripwire: a fix fails the retirement sentinel (the
  module is then deleted per Decision 13); a dispatch reorder
  moving both-iterables onto the async branch fails the live
  queryset rows, which assert completed data the escaping
  residual could not produce. Speculative upstream change with no
  reachable input today, so no finding. Reopen: a graphql-core
  release changing the dispatch (re-audit floor-to-latest per the
  house stance) or the sentinel failing.
- **R7: `apply()` validates the capture, not the live slot, so a
  third-party wrapper is replaced rather than chained.** No
  contract source requires preserving unknown third-party
  wrappers; the self-heal contract covers reverts (pinned by the
  revert row), and all four siblings share the shape. Reopen: a
  supported third-party wrapper on this slot.

Looks-for discharge (REVIEW.md "Mechanics"):

- rule at a caller instead of its owner: none. The gate lives in
  each `apply()` via
  `django_strawberry_framework/conf.py::upstream_patches_enabled`,
  not in the `ready()` dispatcher; residual-awaiting lives in the
  wrapper that owns the slot; validation lives in
  `django_strawberry_framework/_graphql_core_patches.py::_validate_upstream_shape`,
  not at callers; the retirement rule lives in the sentinel test
  per Decision 13.
- policy in an adapter / mechanism in a policy layer: none. The
  module is pure mechanism; gating policy lives in `conf`; the
  per-dependency independence holds (this key drops only executor
  completion, with no HTTP-view lifecycle coupling, per Decision
  13 and the `conf` independence comment).
- contract sources vs body: none. Spec-050 Decision 13 plus its
  rationale, the four GLOSSARY anchors, the module and `apply()`
  docstrings, and all three oracle files match the body;
  `docs/README.md` error and mutation contracts reach no app-load
  path.
- branch no real path reaches: none. Every branch has a pinned or
  guarded path: ImportError fallback is the R4 drift guard; owner
  `None` via its row; own-owner recovery via the reload rows
  (sibling-owner half unreachable, R1); both validation tiers via
  the drift and missing-symbol rows; both guard outcomes via sync
  delegation and the live async-iterable row (third conjunct R2);
  both residual outcomes via the async-children live row and the
  sync-children queryset rows; both gate outcomes via the global
  and per-dependency rows; both install outcomes via the
  idempotence and revert rows (None half R3).
- mode flag standing in for a named adapter: none (the mapping
  keys are the adapter names per the one-module-per-dependency
  rule).
- state owned in two places: none. The import-time capture
  (validation/delegation source), the function-carried original
  (reload channel), and the live class attribute (install state)
  are three roles joined by the reload protocol, pinned by the
  reload and double-reload rows.
- dependency direction: none. Target to `conf` and to
  stdlib-only `truth` (no cycle; the `utils` package `__init__`
  pulls only relations/strings/typing, none importing back;
  `conf` never imports the patch); no `TYPE_CHECKING`;
  function-local `ready()` imports keep the package import free
  of the patch.
- `django.conf.settings` at import: none (no `django.conf`
  import; the setting is read inside `apply()` through the
  gate).
- `__all__` vs public surface: none. The private module carries
  no `__all__`, like all three siblings; `apply` is exported for
  `ready()` and the regression tests, and no star-import surface
  exists.
- two sites implementing one rule: none. DRY change challenges
  run, each count 1: the guard predicate vs
  `django_strawberry_framework/utils/querysets.py::is_async_only_iterable`
  (different contracts — the guard must mirror upstream's
  `is_iterable`, whose str/mapping exclusion the stdlib spelling
  lacks, or an upstream-async-branch value would escape the wrap;
  upstream's branch owns one, the package's sync/async dispatch
  owns the other); the residual double-await vs
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_async`'s
  single await (executor-completion rule vs mutation-window
  field-result rule; an upstream fix moves only the former); the
  stamp-attribute literals (per-module constants, no cross-module
  reader of the attribute name — the sibling item's R1, same
  trigger); capture/validate/install/`apply` scaffolds vs the
  strawberry twin (different method, arity, and retirement; the
  sibling item's R2, same trigger); refusal wordings (each pins
  its own dependency key plus shape clause, oracles pin the
  fragments; a shared helper would couple retirement
  lifecycles).
- sync/async twins: none (no twins; the async closure mirrors
  upstream's own `await_completed` shape, and two awaits are
  exactly sufficient — the residual inner coroutine resolves to a
  plain list in the installed body, so a `while` loop would
  behave identically on every producible value).
- guard one flavor has and a sibling lacks: none. Capture,
  validation, and installed-check differences track descriptor
  kinds and delegator-vs-reimplementer depths (shape-only is
  correct here because delegation forwards bodies); the
  owner-breadth difference is R1, established by no contract
  source as a missing guard.

Handoff: read beyond the record the installed graphql-core 3.2.8
`complete_list_value` and `is_iterable` bodies (why the guard
mirrors upstream predicate-for-predicate and why two awaits are
exact), the card-050 floor record (why no floor probe was owed —
the sentinel suite already passed at the 0.316.0 floor), the
`conf` gate implementation with its whole-mapping validation, and
the sibling `_django_patches` mechanics record (why R1/R3/R4 share
its triggers). Conclusions the rejections do not state: the
wrapper is fix-idempotent — on a fixed upstream the guard still
wraps the (now self-completing) coroutine and the inner check
returns the plain list, so retirement is deletion with no
behavior delta; the HEAD-to-live truthful-reads switch preserves
behavior (all 24 unit rows plus the live residual row green on the
live text); the most likely future edits — an upstream dispatch
change and a second writer to the slot — fail loud or trip a
behavioral oracle today rather than silently. Open threads: none
on this axis. One lead for the Comments sibling (not a finding):
the strawberry twin documents its capture's reload contract in a
docstring while
`django_strawberry_framework/_graphql_core_patches.py::_captured_upstream_method`
carries none — grade as that axis sees fit. No Mechanics lead
routes to another item, and no Cross-axis finding. Scratch kept:
`docs/review/temp-tests/_graphql_core_patches/mechanics/`
(`inspect/`, `_graphql_core_patches.json`,
`probe_capture_strictness.py`).

## Verification (Mechanics)

Address `review/_graphql_core_patches.py/verify-mechanics-1`, cell
`default` throughout. Sharded and pg stay `inapplicable by
construction` (the module runs zero queries, reads no alias, makes no
dialect decision — the hot path evaluates three pure predicates); the
verifier concurs with all three records.

Step 1 (frozen diff): `git diff
e4385002efab0df029451349a7738a02e19928e2 --
django_strawberry_framework/_graphql_core_patches.py` hash-equals
`docs/review/temp-tests/_graphql_core_patches/diff/pass-1.diff`
(sha256 `d3ffd314...`, 1100 bytes both sides, `cmp` clean) at pass
open and again at close. The tree did not move under the pass.

Proof lines: none. This record carries zero Proof lines (no
findings; R1-R7 rejections carry reopen triggers, not Proofs). The
Performance record places no cross-axis text (its Handoff says so);
the Comments `## Cross-axis` is explicit None ("found no performance
or mechanics issue"). There was nothing to run verbatim before
reading `## Implementation (Worker-2)` — stated as required.

Numbers for this axis: none claimed (Mechanics no-findings), so
nothing to reproduce. The timing pair below is reproduced anyway as
the behavior-preservation instrument, using the Performance record's
probe (blob `3c415038`, verified identical in my scratch).

Behavior preservation — revert in copy, pre-fix was worse (slower,
identical trigger set):

- Post-fix, copy fresh, digest `sha256:a5e0fd4e...`: probe
  `review-20260928T215619-30a5a5` gives sync 209.6 vs 87.9 ns median
  (delta 121.7 ns; ranges 204.5-211.4 vs 87.0-89.8,
  non-overlapping), async 174.7 vs 170.7 ns (delta 4.0 ns noise);
  the probe's own order-agreement asserts pass. `10 passed`
  (`review-20260928T215633-ff526e`); the two decisive live rows
  (async-children wrap, sync-queryset delegate) `2 passed`
  (`review-20260928T215639-6dcae7`).
- Reverted copy (`patch -R` of the reorder hunk only, copy
  `modified: 1`, digest `sha256:6497d770...`, line 94 confirmed the
  pre-fix order, shared tree untouched): `10 passed`
  (`review-20260928T215718-7b446c`); `2 passed`
  (`review-20260928T215727-9de98d`); probe
  `review-20260928T215741-9daea7` reproduces the same pair (209.7 vs
  89.3 ns, delta 120.4 ns, non-overlapping).
- 12/12 behavior rows green on both sides with the only delta the
  conjunct order, and the order the reverted file selects is the
  ~120 ns slower one. The reorder preserves observable behavior;
  the pre-fix selection was the worse one.

Item diff through the Mechanics axis (exactly the two hunks, no
unexplained line):

- Line 25 pragma wording: comment-only; moves no rule, changes no
  contract, touches no behavior. The new wording matches the three
  siblings byte-for-byte and agrees with R4's own text ("pinned via
  monkeypatch").
- Line 94 guard reorder: `A and B and C` to `B and A and C` where
  both reordered conjuncts are pure (no side effects, no exceptions
  on any input — see the 18-value attack below). Delegate-first
  call, third conjunct (still last), and residual double-await are
  byte-identical. No owner, dependency, state, or symbol change of
  any kind.
- R1-R7 all still hold verbatim against the landed text: R1
  (capture breadth — untouched lines), R2 (third conjunct still
  present, still last, still fail-safe), R3 (None half untouched),
  R4 (fallback untouched; comment now names the true mechanism),
  R5 (shape check untouched), R6 (behavioral tripwires untouched —
  the live queryset rows passed above), R7 (replace-not-chain
  untouched).
- No symbol moved or renamed, so `--cited-by` is owed nothing
  (gated or ungated).

Attacks on this axis (passing attacks recorded; no failing one):

1. Trigger-equivalence battery over 18 values — sync/empty/tuple,
   async-only, doubly-iterable, async generator, str/bytes/
   bytearray/memoryview/dict exclusion members, int/None/object/
   coroutine non-iterables, hostile `__iter__`/`__aiter__` raisers:
   both orders agree on result AND exception on all 18, 0
   mismatches (`review-20260928T215832-f67e00`). The first run
   (`review-20260928T215816-8b4c9a`, exit 1) failed on my probe's
   own wrong hardcoded assertion (an
   `__aiter__`-only hostile is async-only-shaped, hence True in
   both orders — the assumption was the bug, fixed; upstream
   delegation raises first on the real path in any case).
2. Revert parity above: a behavior delta in either direction would
   have failed the reverted-copy runs; both suites stayed green.
3. Diff-read confirmation that the third conjunct, delegate-first
   ordering, and residual double-await are untouched — nothing to
   execute beyond the read.

Disputes: none. The main artifact carries zero `disputed:` lines
(Mechanics had no findings to dispute); nothing to judge.

Test tier and failability:

- Tier: no new tests, correctly. Wrapper behavior is pinned at the
  live tier (`test_list_field_async_api.py`, the strongest
  reachable tier per AGENTS.md live-first); install lifecycle at
  the package tier (`tests/test_graphql_core_patches.py`: app-load
  path, unreachable from a real query). 118 ns is unpinnable by
  test (timing-flaky by construction; the `utils/strings.py` L1
  precedent).
- Failability at my address: `workspace.py prove
  review/_graphql_core_patches.py/verify-mechanics-1
  <root>/verify-mechanics-1/failability_manifest.json`,
  `review-20260928T215839-f13591`, exit 0. Guard-narrowed mutant
  fails exactly the async-children live row (the coroutine leaks
  to JSON serialization — the upstream bug itself); guard-widened
  mutant fails exactly the sync-queryset live row (GraphQL error).
  Both restores byte-proved (blob `90ac4f3c` before and after); 0
  errors, 0 pre-existing failures. Both gates can fail, each
  distortion failing exactly its direction's row.

Lint gates (`--check` forms only, all green): `ruff check` on the
touched path (All checks passed); `ruff format --check` (1 file
already formatted; the COM812 notice is a pre-existing config
advisory, not a failure); `check_trailing_commas.py --check` (0
violations); `check_citations.py --check` tree-wide (OK, 1297
citations resolve).

New problems: none on this axis. No `verify 1` findings, no named
gaps for Worker-0 to route, nothing for `## Decisions`. Rejections
R1-R7 stand with their recorded triggers.

Fingerprints (`git hash-object`, close of pass):
`django_strawberry_framework/_graphql_core_patches.py`
`90ac4f3cc15be1c24dc1f0281206e260d7555cb6` (equals Worker-2's: no
drift during verify); `tests/test_graphql_core_patches.py`
`53dca517...`; `test_list_field_async_api.py` `49e423ea...`;
`pass-1.diff` `f6c95291...`; this record `83f48fe0...` (pre-append).

Scratch kept under
`docs/review/temp-tests/_graphql_core_patches/verify-mechanics-1/`:
`probe_predicate_order.py` (blob `3c415038`), `probe_postfix.json` /
`.stderr`, `parity_unit_postfix.log` / `.stderr`,
`parity_live_keys_postfix.log` / `.stderr`,
`reorder_forward.diff` (reverse-applied in-copy only),
`parity_unit_prefix.log` / `.stderr`,
`parity_live_keys_prefix.log` / `.stderr`, `probe_prefix.json` /
`.stderr`, `probe_trigger_equivalence.py`,
`attack_trigger_equivalence.log` / `.stderr`,
`failability_manifest.json`, `prove.log` / `.stderr`.

Handoff: I verified a no-findings axis over a two-hunk item owned by
the sibling axes, so the whole verdict turns on one claim — the
reorder is behavior-identical — proved three independent ways
(revert parity 12/12, 18-value trigger battery, two-direction mutant
prove). Beyond the record I read the full item diff, the live
target, the main artifact's Implementation, both sibling records
whole, and the installed `is_iterable` shape the battery mirrors.
Conclusions not in the checks: the mutants' failure modes are the
strongest evidence in the pass (narrowed guard reproduces the exact
upstream bug, coroutine-to-JSON); the `aiter-raises` probe fix is a
reminder that `isinstance` never calls the dunder it detects, which
is also why the reorder cannot introduce an exception-order delta.
Open threads: none on Mechanics. The copy at
`review/_graphql_core_patches.py/verify-mechanics-1` is fresh
(post-fix) after the final `--fresh`; Worker-0 may release it.
