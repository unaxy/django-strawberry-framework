# DRY review: `sidecar-sync-refusal-vs-generic`

Status: verified
Run: 0.0.15 2026-10-11-18

## System trace

Target: [querysets.py][querysets] `::_apply_sidecar_sync` bespoke arm (WT
:3324-3329: `isawaitable` + `_dispose_sync_awaitable` + `SyncMisuseError`
with uniform "an awaitable" + sidecar recourse). Candidate owner: generic
`::reject_async_in_sync_context` (:202-234, kind-distinguishing, 5 call
sites: relay :681/:834, write-permissions :105, read-gate :408, get_queryset
:4615). `isawaitable` census, all 15 classified: 5 refusals (generic :228,
sidecar :3324, async-twin :3357/:3363, nested :4966), 7 completions that
await, 2 generic pre-guards (relay :680/:833), substrate :253. Disposal
single-owned (:259, e1 verified). Second uniform site:
`::reject_awaitable_sync_source` (:4988, coroutine-tested oracle). Oracles:
generic kind arms 2+2 (coroutine :331 pkg + :4020 live;
custom-awaitable :2006 pkg + :4052 live); sidecar uniform 4x, all coroutine
input (:1996/:3129 pkg, :669/:2660 live). History: template single-sited
`e6faac7b` ("cannot drift"); kind vocab `733091ac` (Jul 13, compat); sidecar
uniform `89ee8ac5` (Sep 4, knowing generic), moved unchanged `fee87ac4`;
source uniform `80961a23` predates kind vocab (general guard, general noun).
No spec pins either wording (spec-030 behavior-level; glossary type-level).

## Verification

### Matrix

1. Cross-flavor: 3 write flavors route via generic consumers (`*_ASYNC_RECOURSE`
   compose `sync_pipeline_recourse`); read flavors via visibility runners;
   relay via 2 direct generic calls. No flavor restates the sidecar arm.
2. Sync/async twins: twins share freeze/invoke/validate, differ by color
   in suffix + error arms by construction (principle 5); async arms
   excluded on error-type contract (e1-recorded split).
3. Derived knowledge: kind computed once (generic :229); sidecar has no kind
   logic (uniform literal); method grammar spelled once per twin suffix;
   `inspect.isawaitable` is stdlib-owned, not our rule.
4. Round-trip: refusal (sync) vs require-awaitable-then-refuse-residual
   (async) are inverse shapes with different error types; no shared half.
5. Other media: 10 oracles pin both contracts (4 sidecar + 2+2 generic +
   1 source + 1 noop); prose pins behavior/type, never wording.
6. Omission: every sync-context awaitable boundary refuses (generic x5,
   sidecar, sync-source, auth collapse, routers, async arms); child
   absence is e7-recorded by-construction. No gap.

### Challenges

- C1 new dispose discipline (e.g. stop cancelling futures): D=1
  (`::_dispose_sync_awaitable`; all sites compose). No second def.
- C2 new kind vocabulary (e.g. "a future" arm, or drop distinguishing):
  D=1 (generic :229 only; sidecar has no kind logic and does not move).
- C3 new recourse template: D=1 per seam (e5-rejected: recourses are
  genuinely per-surface wordings; generic takes recourse as a parameter).
- C4 new method_name grammar (e.g. qualify sidecar method): D=1 (sidecar
  line only; generic takes owner/method as params, owns no grammar).
- C5 new error type (e.g. split `SyncMisuseError`): D=1 (the class; both
  sites raise it by name — already composed at type level).
- C6 template reword: touches 3 wording sites — but texts differ because
  contracts differ (compat vs general, each oracle-pinned); no shared
  rule forces joint movement.

## Findings

- F1 (REJECTED — intentional separation, uniform vs kind-distinguishing):
  Generic promises kind-distinguishing for compatibility ("Native-coroutine
  error text is preserved for compatibility"); sidecar promises the general
  noun uniformly (no compat burden), a 2-site contract shared with
  `::reject_awaitable_sync_source`. Sites: D-generic (:202), D-sidecar
  (:3324), D-source (:4988), substrate D0 (:259); 5 generic-call consumers
  + 2 `async_guard=` factories; 10 oracles (trace); behavior-level
  projections. C1-C6 all count 1. Owner: wording stays per-seam
  (principles 3+7); migration none. Coroutine input renders "a coroutine"
  at generic seams, "an awaitable" at sidecar/source seams. Proof:
  static-reviewed (composing flips 4 sidecar oracles red — coroutine-input
  fixtures read, no execution needed). Coupling: none. Freshness:
  querysets.py `f9267729` (WT post-clause), test_connection `da8ac393`,
  test_querysets `f986a690`, pagination live `eaa9259f`, list-field live
  `7b7e85e4`; HEAD `c37a08a0`. Triggers: (T1) wire/template-unification
  requirement; (T2) generic drops distinguishing; (T3) uniform population
  changes. Index rows: `sidecar-sync-refusal-vs-generic` (rejected, T1-T3);
  `sidecar-method-name-grammar` (file-local, `.apply_sync` once, twin
  differs by color); recourse converges on e5 (no new row).

## Defects

None. No non-duplication bug found while tracing; the uniform wording is the
rejected candidate itself, not a defect (2-site contract, 5 oracles).

D1 (Worker-2): `reject_async_in_sync_context` docstring counts "Three
sync pipeline seams" but five call sites compose it
(`utils/querysets.py` :4615, `relay.py` :681/:834,
`utils/permissions.py` :408, `mutations/permissions.py` :105). The
"Three" prose dates to `e6faac7b` (Jun 20); the gate (Jul 15),
write-auth (Jul 16), and relay (Aug 16) adoptions postdate it and
never updated the count. Doc-only; owner
`django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`;
routes to Worker-0 for homing. Does not touch the F1 rejection.

## Pending execution

None.

## Judgment

Zero-edit rejection: the sidecar refusal is intentionally uniform (general
guard, no compat burden) while the generic kind-distinguishes for
compatibility — two contracts, every change axis counts 1, composing breaks
4 oracle-pinned messages for no removable change obligation. One durable
owner clause landed (comment-only, AST-identical); triggers T1-T3 recorded.

## Implementation (Worker-1)

One docstring paragraph at the owner (`_apply_sidecar_sync` :3301-3305);
no behavior change. Own hunk `@@ -3344,6 +3298,12 @@` verified separate
from external hunt hunks (content-untouched); all other file hunks are
concurrent truth-migration (neither ledger nor cycle baseline). Gates: ruff
clean no-churn; basedpyright main + floor 0/0/0; commas 0, citations OK,
truth tier-1 0; public-types skipped (private, comment-only). Inverse proof:
AST digest identical pre/post (`2a148c2f…`). One authorized oracle
(`test_connection_seals_a_malformed_apply_sync_result[awaitable-in-sync]`):
1 passed.

## What shrinks

Nothing shrinks by line count, honestly recorded: the finding is a
rejection, and the only tracked change is the 6-line durable owner clause
(+6/-0 package, +0 tests — existing oracles already pin both wordings, so
no new test is owed). What the cycle gains instead of shrinkage:

- The `reject_async_in_sync_context` vs `_apply_sidecar_sync` merge question
  is closed with evidence (10-oracle map, commit-dated intent chain
  `e6faac7b` -> `733091ac`/`80961a23` -> `89ee8ac5` -> `fee87ac4`, six
  change challenges each counting 1), so no future cycle re-traces it
  without firing T1/T2/T3.
- The intentional separation now lives at its owner (the sidecar
  docstring), not only in this per-cycle artifact: the next author sees
  uniform-vs-kind-distinguishing as a recorded contract pair, not as
  drift to "fix" by composing.
- The whole-package refusal census (15 `isawaitable` sites classified,
  5 generic call sites, 8 refusal raises by error type, axis-6 boundary
  enumeration with zero gaps) stands as the re-usable population for the
  next family that touches this mechanism.

## Independent verification (Worker-2)

### Pre-read trace (formed before opening `## Findings`)

Sites: generic
`django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`
(:202-234, kind-distinguishing template, `SyncMisuseError`);
bespoke arm in `::_apply_sidecar_sync` (:3324-3329, uniform
"an awaitable", fixed sidecar recourse, `SyncMisuseError`);
second-uniform `::reject_awaitable_sync_source` (:4988-5004,
uniform, `SyncMisuseError`); substrate
`::_dispose_sync_awaitable` (:259) + `::_disposed_awaitable`
(:237); async contrast arms (`::_apply_sidecar_async`
:3357/:3363, nested :4966-4973, `::reject_residual_async_source`,
all `ConfigurationError`); sibling `SyncMisuseError` sites
(`::reject_async_iterable_in_sync_context`,
`utils/execution_mode.py::async_execution` mode-mismatch with
no awaitable value).
Roles: generic = shared helper (defines kind-distinguishing
wording); bespoke arm = defines uniform sidecar wording (not a
generic consumer); second-uniform = defines uniform
resolver-source wording (2-site uniform population with the
sidecar arm); 5 generic call sites = consumers (get_queryset,
relay x2, read gate, write auth); 2 `async_guard=` factories =
second-uniform consumers; oracles = message pins; projections =
docstrings + specs (behavior/type level, never wording).
Definition counts per posited change: dispose discipline 1
(change future-cancel -> substrate only; all 9 use sites
compose it); kind vocabulary 1 (generic :229 only; uniform
sites carry no kind logic); recourse template 1 per seam
(generic takes recourse as a param; sidecar/source recourses
are fixed per-surface wordings, e5-standing); method_name
grammar 1 (generic owns none; sidecar `.apply_sync` spelled
once, twin differs by color); error type 1 (the class; both
sites raise it by name). A template-reword posit touches 3
wording sites but each is oracle-pinned to a different
contract (compat vs general) -- no joint-movement rule.
Owner I would choose: wording stays per-seam (generic owns
kind-distinguishing, `_apply_sidecar_sync` owns its uniform
arm, `::reject_awaitable_sync_source` owns resolver-source
uniform); no new owner, no migration.
Own verdict: SEPARATE (rejection). Composing flips the kind
word on coroutine input at a seam whose 4 oracles pin
uniform-on-coroutine -- observable change (principle 8) for
no removable change obligation.

Own hunt (all negative): (a) third refusal spelling that
WOULD compose -- whole-package `awaitable` sweep: every other
refusal differs in error type (Config residual arms),
predicate (async-iterable, executor-mode), or outcome (auth
collapse-to-None, routers factory-contract Config); no third
spelling shares the generic's template shape. (b) shareable
kind vocabulary -- `iscoroutine(` has exactly 2 sites (generic
:229 + dispose :268); a kind-word helper would hand the
uniform sites a compat burden they deliberately lack. (c) P11
deletion -- generic has 5 callers, dispose pair 9 uses, sidecar
arm carries the uniform contract + fixed recourse; no
no-responsibility abstraction.

### Reconciliation

Full agreement with F1 on rejection, sites, roles, counts,
owner, and triggers. Claim-by-claim: 15-site `isawaitable`
census re-derived exactly (same 6/4/3/1/1 per-file split); 8
refusal raises confirmed as the awaitable-refusal population
(4 `SyncMisuseError` + 4 `ConfigurationError`; executor-mode
correctly excluded -- mode mismatch, no awaitable value); 5
generic call sites confirmed (same five); 10-oracle map
confirmed (4 sidecar uniform all on coroutine input via
async-def `_awaitable_queryset`, 2+2 generic kind arms, 1
source uniform on coroutine, 1 noop); intent chain confirmed
commit-by-commit (`e6faac7b` single-site, `80961a23` Jul-13
14:40 ancestor-of `733091ac` Jul-13 21:51, `89ee8ac5` Sep-4
sidecar-uniform knowing generic, `fee87ac4` Sep-21 move);
second-uniform :4988 + coroutine-tested oracle confirmed.
Two notes, both verdict-neutral: (1) my AST digest
`92b4b74f...` differs from W1's `2a148c2f...` by stripping
method, but both show before==after -- equality is the claim,
confirmed, with the item-baseline blob (truth-dirt included)
as reference, never bare HEAD. (2) W1 records zero defects; I
file D1 above (generic "Three" stale vs 5 call sites).
Doc-only, rejection untouched.

### Checks

Scoped diff is exactly the 6-line docstring hunk (`git diff
63991bbd -- utils/querysets.py`, `@@ -3298,6 +3298,12 @@`);
`--diff-filter=A` empty; `--name-only` adds only the plan file
(W0 dispatch lines); no test file changed; no oracle
rewritten. Behavior-preserving: docstring-stripped AST
digests equal pre/post (`92b4b74f...` both); spec grep for
the new prose's distinctive phrases across `docs/spec-*.md`
`docs/SPECS/` returns nothing. Prose OWED (not gratuitous):
same file, same error type, same dispose call, overlapping
"in a sync resolver context" suffix -- without the clause the
next author re-litigates uniform-vs-distinguishing as drift;
no drop. Contract difference + T1-T3 carried; freshness
re-hashed, all five blobs + HEAD match (`f9267729`,
`da8ac393`, `f986a690`, `eaa9259f`, `7b7e85e4`, `c37a08a0`);
no proof:/gate: entries (static-reviewed oracle-flip proof);
coupling none. Gates re-run on the touched file: `ruff
format --check` pass, `ruff check` pass, trailing-commas 0
violations, citations OK (20 resolve). Basedpyright not
re-run per brief (comment-only, no typing doubt). Heavy IS
present in my env; W1's absent-wrapper fallback (direct
serialized + explicit SAY-SO) complies with the RUNS binding
and its single focused test is entry-authorized without
heavy -- no invalidation. AGENTS.md prose rules: new
docstring carries no process provenance; same-file symbol
cited bare per durable-home precedent (no line numbers); no
test-tier issue. Matrix judged axis-by-axis against the real
surface -- all six sound.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[querysets]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
