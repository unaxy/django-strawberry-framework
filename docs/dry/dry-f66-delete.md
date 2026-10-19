# DRY review: `f66-delete: queryset-result-cache pair`

Status: verified
Run: 0.0.15 2026-10-11-16
Item: `f66-delete` (queue item 1, run 16; principle-11 deletion)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `344049a31ada884da966a0cf55fef6f5db862d0d`
HEAD: `c37a08a085113d628a554ee199f4d741d7c86cdf` (unmoved the whole item)
Slot: slot-2 `dry/f66-delete/consolidate`
(`~/dry/ws/c3af387fc1324a21/dry/slots/slot-2`)

## System trace

f66 appended a `queryset_result_cache` / `set_queryset_result_cache` pair to
`utils/_queryset_private.py` (EOF, +17) with exactly two call sites: the seal
carry write in `utils/querysets.py` and the G1 evaluated-root read in
`optimizer/extension.py`. Census over the copy `*.py` pre-edit: the pair
definition + 2 imports + 2 call sites + the pair-only test module
`tests/utils/test_queryset_private.py` (untracked, 30 lines) — nothing else
names the pair, in any tier. Every other member of `_queryset_private.py`
exists to carry a suppression for a slot django-stubs omits; this pair
carries none — its own comments say django-stubs declares `_result_cache`
(`django-stubs` `query.pyi`: `_result_cache: list[_Row] | None`). HEAD
already spelled the seal write directly; f66 only wrapped it. The G1 site
differs: HEAD read leniently (`getattr` with default), f66 made it strict;
the strictness is pinned by oracles and the inline keeps it line for line.

## Verification

### Matrix

Cross-flavor: no sibling surface spells this slot (the seal string-key reads
are a different mechanism — instance-dict reads that must not dispatch).
Sync/async: no twin; both call sites are sync straight-line code. Derived
knowledge: the seal also reads the slot via `state.get("_result_cache")`; a
Django rename moves those string keys with or without the pair. Round-trip:
the pair IS the round-trip (getter + setter); deleting both halves together
leaves no half behind. Other media: only the closed f66 record names the
pair (history, left alone). Enforcement by omission: `_iterable_class` (also
stubs-declared) stays a direct write at the seal per adjudicated f67 — the
pair is the anomaly, not the norm.

### Challenges

C1 Django renames `_result_cache`: the seal `state.get` string reads move
regardless; the pair relieves 0 of them. C2 django-stubs drops the
declaration: speculative; today it declares it, and basedpyright 0/0/0
post-delete proves direct access clean. C3 strict-to-lenient flip at G1:
decided at the call site by comment + oracles, identical under either
spelling. No posited change touches fewer definitions with the pair than
without it: 0 obligations removed. Verdict: principle-11 abstraction with no
responsibility — delete.

## Findings

F1 `queryset-result-cache-access` pair — DELETE (2 definitions to 0).
Contract: typed `_result_cache` read/write for proved querysets. Variation:
none observed — one caller per half, no suppression, no guard, no logic.
Sites: 2 definitions (the pair) / 2 consumers (seal write, G1 read) / oracles
below / projections: the G1 guard comment + the closed f66 record. Owner
after deletion: none — direct access; Django owns the spelling. Lifetime:
n/a (no stored derivation). Migration: pair deleted; seal write inlined to
the exact HEAD bytes; G1 read inlined strict; pair-only test module deleted;
the G1 comment clause naming the deleted owner reworded (2 lines, disclosed
in Implementation). Distinct behavior kept: strict G1 read, seal `cast`,
evaluated-but-empty `is not None` semantics. Behavioral proof (all
execution-verified): 5 G1 oracles + seal-carry identity oracle + refusal
trio + live one-query HTTP oracle green post-delete; failability pinned both
halves (guard inversion fails exactly the 3 named rows; carry drop fails the
identity row; restores byte-identical). Structural gate: none — the only
failure mode is re-adding the wrapper, and the run bar forbids exactly the
census/source-reading gate that could catch it; behavior stays pinned by the
oracles. Coupling: none. Freshness: post-edit blobs `a26a8d43...`
(`_queryset_private.py`; equals the pre-f66 bytes — the hunt paragraph above
untouched), `1b0cf162...` (`querysets.py`), `36a733df...` (`extension.py`);
census population = copy `*.py` minus `.venv`; HEAD `c37a08a0`; live tree
equaled the copy on all 4 paths at sync and every run header reports shared
unmoved.

## Defects

None new. f66 D1 (module docstring universal stubs claim) is mooted as a
consequence — the pair was its counterexample — but the docstring hunk is
hunt-owned and untouched; Worker-0 routes the mootness at closeout.

## Pending execution

None. Every proof executed in the copy. Sharded/pg cells: inapplicable by
construction — the inlined lines read/write an already-fetched slot and reach
no database, alias, or dialect decision; oracles ran under default sqlite.
Worker-2 judges.

## Judgment

The pair is one-caller-each indirection carrying no suppression, no guard,
and no logic over a stubs-declared slot Django owns. Deletion removes the
abstraction and keeps every behavior pinned. f66's `consolidated` index row
needs a Worker-0 revision at verification (this deletion supersedes it).

## Implementation (Worker-1)

In the copy only (Worker-0 ports): `_queryset_private.py` −17 (pair at EOF
deleted, file ends at `chain_queryset`); `querysets.py` −1 import line,
setter line inlined to the exact HEAD bytes; `extension.py` −1 import line
(the shared hunk's hunt `truth` line kept), G1 line inlined strict plus a
2-line comment reflow dropping the `shared owner` clause that named the
deleted pair — that clause sits 100% on f66-ledgered lines; Worker-2 rules
whether it exceeds the one-line fence, revert is trivial.
`tests/utils/test_queryset_private.py` deleted (untracked, 30 lines, zero
importers). Attribution: all 154 WT-vs-HEAD hunks across the 3 tracked files
= 5 f66-ledgered + 3 run-15-ledgered (rows 29, 32, 35) + 146 hunt (truth
migration, exception narrowing, posture prose, freeze fix); zero unexplained.
Runs (all via `heavy` + `workspace.py`): ruff check
`dry-20261011T053921-61ef34`, ruff format `dry-20261011T053925-3bd3b3` (zero
drift, md5-verified), basedpyright `dry-20261011T053932-50f15d` (0 errors, 0
warnings, 0 notes), G1 5/5 `dry-20261011T054100-58c22c`, seal + live 5/5
`dry-20261011T054116-46f17a`, failability 2 pinned `dry-20261011T054222-2d9d1c`;
post-prove re-grep confirms the edit intact.

## What shrinks

Production −20 lines, tests −30 lines, 2 definitions to 0:

- `django_strawberry_framework/utils/_queryset_private.py` −17: the
  `queryset_result_cache` / `set_queryset_result_cache` pair deleted at EOF
  (2 blank + 6-line getter + 2 blank + 7-line setter). Post-edit blob
  `a26a8d430718a06c5292b15e3533eebed43597e3` equals the pre-f66 bytes — the
  hunt docstring paragraph above (WT-vs-HEAD hunk 1 of 2) is byte-identical,
  never touched.
- `django_strawberry_framework/utils/querysets.py` −1 + one-line swap: the
  `set_queryset_result_cache,` import name deleted (pure-addition hunk
  `112a115`); the carry write inlined to `sealed._result_cache =
  cast("list[object] | None", result_cache)`, byte-identical to HEAD
  (single-line hunk `4042c3995`). Adjacent hunt hunks (`truth.kind` wording,
  `truth.name` projection) untouched.
- `django_strawberry_framework/optimizer/extension.py` −2 + one-line swap:
  the `from ..utils._queryset_private import queryset_result_cache` line
  deleted from the shared hunk `57a57,58` (the hunt `from ..utils import
  truth` line above it kept); the G1 guard inlined to `if
  inner_result._result_cache is not None:`; the guard comment reflowed from
  3 lines to 2, `the typed read through the shared owner is exact` becoming
  `the typed read is exact`, since the owner no longer exists. All touched
  comment bytes sit inside f66's own hunk `1211,1214c1207,1212`.
- `tests/utils/test_queryset_private.py` deleted whole (untracked, 30
  lines): both rows tested only the pair (fresh-cache `None`, setter/getter
  round-trip by identity). Zero importers anywhere (`*.py`, `*.toml`,
  `*.ini`, CI yaml, manifests all grepped). The file's own docstring named
  the surviving call-site oracles; each still pins the behavior:

| Oracle | Wrong result it rejects |
|---|---|
| `test_extension.py::test_evaluated_root_queryset_does_not_record_a_plan_cache_miss` | guard not firing: plan miss recorded, SQL re-executed (2 queries, no JOIN) |
| `test_extension.py::test_optimize_returns_same_instance_for_evaluated_queryset` | guard cloning instead of passing through (identity) |
| `test_extension.py::test_resolve_async_passes_through_evaluated_queryset` | guard reached past return-type resolution (tripwire raises) |
| `test_extension.py::test_optimizer_preserves_async_adapter_evaluated_cache` | adapter path dropping the evaluated passthrough |
| `test_extension.py::test_optimizer_unadapted_non_queryset_passthrough` | gate regression for non-querysets (unchanged arm) |
| `test_querysets.py::test_seal_carry_result_cache_carries_the_rows_the_source_holds` | carry dropping rows (`is held` identity) or default policy carrying (`is None`) |
| `test_querysets.py::test_seal_carry_result_cache_refuses_a_cache_that_is_not_an_exact_list` (3 params) | non-list cache carried instead of refused with the typed defect |
| `test_library_api.py::test_library_evaluated_queryset_not_re_executed_over_http` (live) | re-execution over HTTP (2 branch queries instead of 1) |

Obligations examined and found empty: (1) checker suppression — the slot is
stubs-declared, both inlined accesses pass basedpyright with no new
suppression, and the seal oracle itself reads `sealed._result_cache`
suppression-free; (2) spelling ownership — Django owns `_result_cache`, and
a rename would move the seal `state.get("_result_cache")` string keys that
cannot go through the pair anyway; (3) strict-vs-lenient ownership — f66's
read-half adjudication chose strict, recorded at the call site and pinned by
the oracles above, identical under either spelling. f67's adjudicated
verdict (declared `_iterable_class` stays a direct seal write; a 1-to-1 move
is a principle-11 one-caller wrapper) is the same rule applied to the twin
slot. What remains: two direct accesses over a declared slot, each pinned at
the AGENTS.md tier by tests that fail on real wrong results, proved by
`prove_failability.py` (guard inversion: 3 failed / 3 passed baseline;
carry drop: 1 failed / 1 passed baseline; both restores byte-identical).

Attribution census (WT-vs-HEAD, copy equals live tree on all 4 paths):
154 hunks = 5 f66-ledgered (pair EOF, qs import, qs setter line, ext import
line, G1 comment + guard) + 3 run-15-ledgered (qs row 29 clause-texts
docstring, qs row 32 live-cite docstring, ext row 35 unwrap docstring) + 146
hunt (truth-migration one-liners incl. the shared ext import hunk, `except
Exception` narrowing with `OverflowError`, `Mapping` exactness typing,
frozenset-to-tuple membership, origin-param drop, posture prose, the
`_freeze_variable_value` mapping-keys fix). Zero unexplained; my 6 touched
regions sit 100% on f66-ledgered lines.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

### Own trace (recorded before opening `## Findings`)

Knowledge boundary at write time: source bytes (before-copy census,
`git diff`/`git show` vs ITEM_BASELINE, stubs + Django runtime reads, oracle
bodies, fresh runs + own mutants below) plus this artifact's `## System
trace`, `### Matrix`, `### Challenges`, and the `## What shrinks` oracle
table/census. `## Findings`, `## Defects`, `## Pending execution`,
`## Judgment`, `## Implementation (Worker-1)` not yet opened. (Whole-tree
search output also incidentally exposed ~10 one-line artifact snippets; the
trace derives from the source reads, not those snippets.)

Sites (before-copy `slot-1` regex census over `*.py`, re-derived):

- Definitions: `django_strawberry_framework/utils/_queryset_private.py::queryset_result_cache`
  + `::set_queryset_result_cache` (EOF pair, 17 lines). One-line bodies
  (`return queryset._result_cache` / `queryset._result_cache = rows`); own
  comments state django-stubs declares the slot — verified first-hand at
  `django-stubs` `query.pyi:84` (`_result_cache: list[_Row] | None`).
- Consumers, exactly one caller each: `django_strawberry_framework/utils/querysets.py::_seal_or_defect`
  carry write under `if policy.carry_result_cache:` (was `:3995`);
  `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`
  G1 guard `if ... is not None:` after the `normalize_query_source` gate
  (was `:1212`).
- Oracles, none naming the pair: `tests/utils/test_querysets.py`
  (carry identity + default-None; exact-list refusal x3 keyed on
  populated-not-None; evaluated defect) and `tests/optimizer/test_extension.py`
  (plan-miss 0 + 1 SQL with JOIN; same-instance identity; async tripwire
  mirror; evaluated-empty `[]` adapter passthrough; non-queryset gate arm),
  plus the live exactly-1-SQL HTTP oracle in
  `examples/fakeshop/test_query/test_library_api.py`. The deleted
  `tests/utils/test_queryset_private.py` (30 lines, untracked, package tier)
  tested the pair against itself (setter-then-getter round-trip); its two
  distinct behaviors survive as assertions inside the behavioral oracles
  (None-on-fresh in the require-unevaluated + default-policy asserts;
  carry-identity in the carry oracle).
- Excluded with contract differences: `utils/querysets.py` `state.get("_result_cache")`
  x2 (untrusted/exact-type instance-namespace inspection that must not
  dispatch — different mechanism); `optimizer/nested_fetch.py::RecognizedFetchQuerySet._fetch_all`
  `self._result_cache` (own-attribute fetch protocol); `materialized_rows`
  exact-type read (same no-dispatch family); f-string wording + docstrings
  (projections).

Definition counts per posited change:

- C1 Django renames `_result_cache`: with the pair, the 2 pair bodies move;
  without it, the 2 inlined spellings move. Either way the seal string keys,
  the nested_fetch own-attribute, the f-string, and the test plantings move
  regardless — the pair never covered them (they bypass by construction).
  Obligations removed by keeping the pair: 0.
- C2 a third proved-queryset site appears: spells the Django-owned attribute
  directly. Precedent in the same function: `sealed._iterable_class =
  iterable` over a stubs-declared slot (`query.pyi:83`), no owner. One
  attribute, one owner (Django); no divergence risk.
- C3 seal refusal / G1 strictness semantics change: decided in
  `_seal_or_defect` / the guard comment + oracles; the pair is transparent
  (pure passthrough, byte-verified). Identical under either spelling.

P11 responsibility check: no suppression carried (all 12 surviving
`_queryset_private.py` members carry
`pyright: ignore[reportAttributeAccessIssue]`; the pair carried none); no
validation, narrowing, or default; no boundary name external callers depend
on; no effect isolation; no extension point. One caller per function.

Verdict I would reach: DELETE. The pair is a principle-11 abstraction with
no responsibility, relieving zero change obligations.

### Reconciliation with `## Findings` (every difference explicit)

Read `## Findings`, `## Defects`, `## Pending execution`, `## Judgment`,
`## Implementation (Worker-1)` after recording the trace above. Reconciliation:

- Sites/roles/counts/verdict: FULL AGREE. 2 definitions to 0, one caller per
  half, no suppression/guard/logic, owner-after none (Django owns the
  spelling). My C1 matches W1 C1 (string keys move regardless, 0 obligations
  relieved); my C3 matches W1 C3 (strictness decided at the call site).
  Challenge sets differ in one member (mine C2: a third site appears; W1 C2:
  stubs drops the declaration as speculative) — both support delete, no
  conflict.
- Matrix: AGREE on all six axes. Sync/async: W1 "no twin"; I add precision —
  the async path shares the same guard (`_async_optimize` awaits then calls
  `_optimize`), pinned by the tripwire mirror test. Same conclusion.
- Sharded/pg `inapplicable by construction`: SOUND on its reason. The 3 hunks
  move an in-memory list reference (seal) and an `is not None` check (G1);
  no query construction, no alias, no dialect decision. Default-cell oracles
  exercise identical in-memory semantics.
- No oracle rewritten to a deleted owner: CONFIRMED. Live whole-tree regex
  census: zero `.py` references to either pair name in package, tests, or
  examples. Surviving oracles spell the slot directly and are untouched by
  this item's diff.
- P8 equivalence: CONFIRMED on live bytes. G1 strict `is not None` kept
  (`extension.py:1210`; Django's own `__getitem__` uses the same spelling);
  seal `cast("list[object] | None", ...)` kept (`querysets.py:3994`);
  evaluated-but-empty pinned by the `[]` adapter test + the falsy-caches
  refusal trio. Order, exceptions (slot always set — Django `query.py:372`;
  both sites hand proved querysets), query/tx effects (none), observation
  points: identical.
- Failability: CORROBORATED with own mutants in own copy (slot-3,
  `dry/f66-delete/verify-1`, via `heavy` + `workspace.py run`): G1
  `if False` mutant → live HTTP oracle FAILED (`test_library_api.py:497`,
  run `dry-20261011T055109-6c61c6`); seal carry-drop mutant → carry oracle
  FAILED (`test_querysets.py:5784`, run `dry-20261011T055129-b85f2d`); both
  restores byte-identical (`cmp` vs live). Counts differ from W1's
  prove-run (they failed 3 G1 rows; I ran the single wire-level oracle) —
  convergent, no conflict: both halves fail without the inlined behavior.
- Fresh oracle re-runs (slot-3, all via `heavy`): `test_querysets.py` 344
  passed (`dry-20261011T054934-719582`); `test_extension.py` 182 passed
  (`dry-20261011T054952-e8543a`); live G1 HTTP oracle 1 passed
  (`dry-20261011T055026-2181ff`). No collection errors: no orphan importers.
- Comment reflow ruling: INSIDE the item fence. The dropped clause ("the
  typed read through the shared owner is exact") names the deleted pair —
  leaving it asserts a falsehood, so the reword is required by the deletion,
  not polish; all touched bytes sit in f66's G1 hunk (baseline `:1208-1212`
  → live `:1208-1210`); the 3→2 rewrap is the minimal mechanical reflow.
  Revert would reintroduce a false statement — rejected.
- Freshness: live `git hash-object` re-derived —
  `a26a8d430718a06c5292b15e3533eebed43597e3`,
  `1b0cf16277b3cb82e98359979f933ca22456bcd5`,
  `36a733df75891247e5226421efd7921cb30798fa` — match W1's cited blobs
  (full + prefixes). HEAD `c37a08a0` unmoved. Live == slot-3 on all 4
  paths (`cmp` identical ×3, deleted test absent both). Post-edit
  `_queryset_private` blob equals the pre-f66 WT bytes (f66-nomination pin
  `a26a8d43` vs HEAD `ff8b2b46`; single creating commit `f2f18ba6`).
- Pending execution empty, coupling none: AGREE. Every proof executed (W1's
  runs + my re-runs); the pair has zero live referrers, so nothing couples.
- Structural gate none: JUSTIFIED, not a gap. Deletion to zero definitions
  leaves no owner to bypass; re-adding a wrapper is new code, which review
  (not a census gate the run bar forbids) catches. Behavior stays pinned by
  the oracles.
- AGENTS.md prose rules on the diff: PASS. No process provenance (reflowed
  comment is technical); no citations added or broken; tiers correct —
  deleted file was package-tier `tests/` (right for package internals), and
  surviving pins sit at `tests/` (seal internals, identity/cache-state with
  no wire shape) + live tier (G1 one-query, wire shape).
- Ruff (required runs, live tree): `ruff format --check` →
  "3 files already formatted"; `ruff check` → "All checks passed!" on the 3
  touched package paths. Both exit 0.
- Defects: concur — none new, no `(Worker-2)` entry. The module docstring's
  remaining universal claims hold for all 12 surviving members (each carries
  its suppression; `_result_cache` is outside the enumerated "these"), so
  f66 D1's mootness stands as W1 recorded it; its closeout routing is
  Worker-0's action, already named.
- Bar: HOLDS. P11 deletion with 0 obligations (verified, not asserted); net
  −20 production / −30 tests, zero added machinery; all 10 oracles
  behavioral at the AGENTS.md tier, failing on real wrong results (query
  counts, identity, tripwire, defect tuples); no AST/census tests added
  (none added at all). W1's submission shape: 141 non-`What shrinks` lines
  ≤ 150 (this Worker-2 appendix is DRY.md-mandated and outside the cap).
- Scope note: basedpyright not re-run by Worker-2 (not in this brief's job
  list). W1's 0/0/0 stands corroborated in-source: the G1 read sits past the
  discriminated-`NormalizedSource` gate (flag narrows `[0]` to `QuerySet`)
  over a stubs-declared slot, with the same-function `_iterable_class`
  direct write as precedent.

Touches this pass: this artifact only (Status + this section). No
production edits. Scratch: `~/dry/tmp/w2_f66_mutant.py` (kept per
run-15 custody rule 5b). Verdict: verified.
