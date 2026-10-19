# DRY review: `queryset-result-cache-access`

Status: verified
Run: 0.0.15 2026-10-09-13
Item: Family `queryset-result-cache-access` (queue item f66, run 13)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `8d8ee2953e85b5b8aedbcd584d3c966015ca9579` (resolves as commit)
HEAD: `23b5f42106ffd14805936560f5155dd90d7568da` (unmoved the whole item)
Slot: slot-2 `dry/f66-result-cache/consolidate`
(`~/dry/ws/c3af387fc1324a21/dry/slots/slot-2`)

## System trace

The family target is external access to Django's
`QuerySet._result_cache` slot: the fetched-rows list Django sets to
`None` in `QuerySet.__init__` (installed 6.1.2, `query.py:372`) and
populates on evaluation. The nomination (folder FAM-2, endorsed with
read-half adjudication CC-2) was re-derived fresh at current bytes and
CONFIRMED count-2, both committed lines:

- `utils/querysets.py:3991` (pre-change numbering) `sealed._result_cache
  = cast(...)` -- the seal rebuild write under the
  `carry_result_cache` policy: rows the source already fetched travel
  onto the framework-owned rebuild so a windowing surface re-queries
  nothing.
- `optimizer/extension.py:1203` `if getattr(inner_result,
  "_result_cache", None) is not None` -- the G1 evaluated-queryset
  guard (spec-035 Decision 3): a consumer-evaluated root queryset
  passes through unchanged so `apply_to` never re-executes its SQL.

Post-change both compose the new owner pair in
`utils/_queryset_private.py::queryset_result_cache` /
`::set_queryset_result_cache` (this item, `:151`-`:167`); the
extension `getattr` spelling is extinct and the seal assignment is a
one-line owner call. The module's charter ("spelled here once ...
every caller goes through these functions") now holds for this slot
the way it already does for the 10 covered siblings.

Two facts the trace established beyond the nomination. First,
django-stubs DECLARES this slot (`query.pyi:84`: `_result_cache:
list[_Row] | None`) -- the only one of the 11 owner slots it does, so
the new pair carries no suppression while its 14 siblings do. The
checker proved it: the first basedpyright run failed exactly the two
copied ignore comments as unnecessary, and the direct call
type-checks. Second, the read-half adjudication resolves to
typed-access, not a getter-with-default and not a narrowed write-only
family: the `normalize_query_source` gate above `:1203` returns every
non-queryset early and its discriminated `NormalizedSource` union
narrows `inner_result` to `QuerySet` -- the direct owner call
type-checks with no new cast, guard, or widening, which is the
mechanical proof the `getattr` default arm was dead defense. A new
boundary test pins that a non-queryset never reaches the owner.

Dirt attribution by content, all vs `git show HEAD:` (HEAD unmoved):
every line this item edits is committed content. The seal block
(`:3982`-`:3991`) sits 10 lines above the nearest hunt hunk (new-file
`4001+14`, `_row_source_model` truth-migration); the extension guard
(`:1192`-`:1203`) sits between hunt hunks at `967` and `1515`; the
owner append lands at EOF while the module's single hunt hunk is the
docstring `@@ -7,6 +7,13`; both test insertions land in
hunk-free regions (`test_extension.py` nearest hunks `1869+`,
`test_querysets.py` gap `4870`-`5898`). Two import insertions sit
adjacent to hunt-added lines without modifying them -- the querysets
import name lands between committed context lines of a hunt hunk, the
extension import between the hunt `truth` line and a committed line --
the exact shape verified for f61. No ledger row names any of the six
touched paths (checked `## Owned changes`); no hunt line is edited,
reverted, or consolidated onto. The one prose refresh the change
wants (the module docstring's universal stubs claim) CANNOT land
without touching the hunt hunk, so it is filed as D1, doc-only and
hunt-blocked, with the exception recorded meanwhile in per-function
comments on the pair itself.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched. No second live
   read or write of the slot exists in any flavor: the package-wide
   literal census (### Enumeration) finds executable attribute
   spellings only at the owner pair and the excluded subclass
   protocol, and the dispatch census finds zero `getattr` /
   `setattr` / `hasattr` spellings. `nested_fetch.py` manages its
   own slot inside its `_fetch_all` override (R4);
   `types/resolvers.py:715` consumes `materialized_rows`, the
   excluded no-dispatch read (R2).
2. **Sync/async twins.** Inapplicable with reason: a pure
   synchronous attribute access admits no async twin, and no
   `async def` reader of this slot exists. The async optimizer path
   inherits the guard by calling the same `_optimize` (oracle:
   `test_resolve_async_passes_through_evaluated_queryset`).
3. **Derived rather than repeated knowledge.** Searched. The seal's
   two snapshot-key reads derive nothing: they read a different
   population (the no-dispatch instance snapshot) under their own
   trust contract (R1, R2). The `carry_result_cache` policy field
   is policy vocabulary sharing a substring, not a slot access.
4. **Inverse / round-trip pairs.** Read and write halves are
   co-owned in one module post-change; no second writer exists.
   The old seal write spelling and the old extension read spelling
   are both extinct (one `Attribute` node each removed; the
   dispatch census proves the `getattr` gone).
5. **Contracts restated in another medium.** Oracles never read the
   owner they check: G1 behavioral tests assert passthrough
   identity and cache state, carry tests assert row travel by
   identity, the live HTTP test asserts one query. Tests that
   spell the slot do so to PLANT hostile state (`qs._result_cache
   = ...`) or to assert what landed -- setup and oracle, which must
   name the slot to sabotage or witness it and would go circular
   through the owner (f61 Matrix-5 precedent). The wording oracle
   pins the R3 f-string. Docstring projections: the owner
   docstrings are new and exact; the module-docstring universal
   claim is D1.
6. **Enforcement by omission.** The family enumerates every live
   access (### Enumeration); pre-change the two holdouts did not
   compose the owner. Post-change every live access composes it;
   no member lacks the rule. No behavior defect under this axis.

### Enumeration

Instrument: `rg -n "_result_cache" django_strawberry_framework/`
(34 hits, 6 files, post-change bytes) plus an evasion sweep for
computed spellings (`getattr` / `setattr` / `hasattr` /
`attrgetter` with the slot, `del` / `pop` / `delattr`,
`__dict__` / `vars(` keys). Pre-change count was 26 hits over 5
files with 1 evasion hit (the extension `getattr`); the delta is
+6 owner lines, +1 import line per consumer, and the guard's
`getattr`-to-call swap. Every hit homed:

| # | Site | Home |
|---|---|---|
| 1 | `_queryset_private.py` 2 defs + 2 bodies | F1 owner definitions |
| 2 | `_queryset_private.py` 2 one-line comments | projection (suppression-absence rationale) |
| 3 | `querysets.py:115` import + `:3992` call | F1 consumers (write half) |
| 4 | `extension.py:58` import + `:1206` call | F1 consumers (read half) |
| 5 | `nested_fetch.py:222` + `:225` `self` pair | R4 (subclass protocol, excluded) |
| 6 | `querysets.py:3909` seal snapshot-key read | R1 (seal discipline, excluded) |
| 7 | `querysets.py:4095` exact-type snapshot read | R2 (no-dispatch read, excluded) |
| 8 | `querysets.py:3918` f-string wording | R3 (error vocabulary, excluded) |
| 9 | `carry_result_cache` policy field ×6 | out of mechanism (distinct identifier) |
| 10 | prose ×13 (comments, docstrings ×2 files + querysets ×9 + extension ×2) | projections |
| 11 | evasion sweep: 0 hits | F1 (dispatch extinct; never other forms) |

No third live-access site exists. The `materialized_rows`
callers, the policy field, and the test spellings from the
broader `result_cache` sweep are homed in rows 7/9 and Matrix-5.

### Challenges

Counts count authoritative definitions only; consumers, oracles
and projections are listed under F1, not counted. "Before" =
pre-change bytes, "after" = this item's tree.

- C1 (Django renames `_result_cache`; the FAM-2 rerun). Before:
  2 live spellings move (the seal write, the extension
  `getattr`). After: 1 (the owner pair, one module, one edit);
  both consumers, every test, and the census follow by name. The
  subclass pair (R4) moves under the subclass-protocol contract,
  the snapshot keys (R1/R2) under seal discipline, the wording
  (R3) under error vocabulary. Count: 2 -> 1.
- C2 (Django changes the stored shape, e.g. a tuple). Moves: the
  owner signatures alone, before (seal write + cast) and after
  (owner pair). The extension read never moves (a `None` check is
  shape-agnostic). The seal's exact-`list` gate (`:3910`) moves
  under its own validation contract either way -- validating
  untrusted state vs accessing owned state stay separate.
  Count: 1 -> 1.
- C3 (the non-queryset failure mode changes). Moves: the
  `normalize_query_source` gate alone, before and after; the
  strict owner is untouched. The old `getattr` default arm was
  dead defense, never a failure-mode contract: the gate returns
  non-querysets early, pinned by the new boundary test.
  Count: 1 -> 1.

## Findings

### F1 -- `_result_cache` live access (CONFIRMED, consolidated 2 -> 1)

- **Contract + variation.** One rule: a live read or write of the
  fetched-rows slot Django keeps on a queryset spells
  `QuerySet._result_cache` exactly once, in the strict typed owner;
  both consumers compose it by name. Varies on: the Django-private
  spelling (owner bodies), the stored shape (owner signatures:
  `list[object] | None`, matching the stubs' `list[_Row] | None`
  at this queryset's row type).
- **Sites + roles.**
  - Definitions (owner, new): `utils/_queryset_private.py::
    queryset_result_cache` (`:151`, body `:158`) and
    `::set_queryset_result_cache` (`:160`, body `:167`).
  - Definitions (converted to consumers): the seal carry write
    (`utils/querysets.py:3992`, was `:3991`) and the G1 guard
    read (`optimizer/extension.py:1206`, was `:1203`).
  - Consumers: the two call sites above (imports `:115` / `:58`).
  - Oracles: the 2 round-trip pins + 2 census rows (new file),
    the 2 spy rows + 1 boundary row (new), the pre-existing G1
    rows (`test_optimize_returns_same_instance...`,
    `test_evaluated_root_queryset...`,
    `test_resolve_async...`, adapter rows, non-queryset
    passthrough), the carry rows
    (`test_seal_carry_result_cache_...` ×2), and the live HTTP
    `test_library_evaluated_queryset_not_re_executed_over_http`
    -- all independent literal expectations, none reading the
    owner.
  - Projections: the new docstrings, the rewritten guard
    comment, the per-function suppression notes, this record.
- **Challenges.** C1 2 -> 1, C2 1 -> 1, C3 1 -> 1 (### Challenges).
- **Owner + lifetime.** Owner by responsibility:
  `_queryset_private` already owns every sibling private-attribute
  spelling with the same read/write-pair shape, both consumer
  modules import from it (querysets since before this item,
  extension new), and the dependency runs optimizer -> utils with
  no cycle (the owner imports stdlib + Django only). Adjudication
  (CC-2, owed): typed-access. A getter-with-default would push
  leniency into the strict owner, which f61's W2 rejected as a
  shape; narrowing to the write half would leave a live spelling
  the gate already proves safe to type. The gate above the read
  returns every non-queryset early and its discriminated union
  narrows the survivor to `QuerySet` -- proved mechanically: the
  direct owner call type-checks with no new cast, guard, or
  widening, where the replaced `getattr` needed none either. No
  stored derivation: both functions are pure accesses ("not
  cached", principle 4).
- **Migration.** The owner pair is appended at the module's EOF on
  committed lines; the seal write becomes
  `set_queryset_result_cache(sealed, cast(...))` (the pre-existing
  cast is kept, narrowing the snapshot's `object` exactly as
  before); the guard becomes `if queryset_result_cache(
  inner_result) is not None` with the `getattr` rationale
  sentence rewritten to the gate-proves-queryset reasoning. No
  new cast, widening, or suppression anywhere: the replaced code
  needed none and neither does the replacement -- and the one
  surprise ran the other way (the stubs declare this slot, so two
  copied suppressions were deleted, checker-forced).
- **Distinct behavior.** What stays separate: the strict owner
  fails loud (`AttributeError`) where the old `getattr` answered
  `None`. The dropped tolerance is twofold, both undocumented
  incidental behavior, never a contract (f61-shaped justification):
  (a) a `QuerySet` instance missing the slot -- reachable only via
  explicit `del`, which zero tests pin (census: no `del` / `pop`
  of the slot anywhere) and no production path performs (Django
  sets it in `__init__` on every construction); (b) a
  non-queryset slipping the `isinstance` gate via `__class__`
  spoof -- a contract-violating input that crashed one line later
  before (`apply_to` reads `.query`) and crashes at the guard
  now, same exception family. The gate still returns every
  honest non-queryset before the owner could see it (new
  boundary test). Recorded here and in the guard comment.
- **Behavioral proof.** `execution-verified` throughout, all in
  slot-2 via `workspace.py` (run ids under ## Implementation):
  7/7 new rows green; 925 green across the two consumer files,
  the new file, `test_list_field.py`, `test_resource_policy.py`,
  and the live G1 HTTP oracle; both basedpyright passes 0;
  truthful-reads 0; public-types OK; trailing-commas 0; coverage
  pin shows zero missing lines in `:151`-`:167`. Failability
  (`dry-20261010T080532-f5e757`, manifest
  `$TMPDIR/f66-result-cache-manifest.json`, all restores
  byte-proved): E1 restores the inline `getattr` (behavior-
  preserving hand copy) -> exactly the spy + dispatch-census
  rows fail while both behaviorals pass; E2 restores the inline
  assignment -> exactly the seal spy + attribute census fail
  while the carry behavioral passes; E3 corrupts the getter to
  `None` -> exactly the round-trip + async-tripwire + attribute
  census fail; E4 neuters the setter to `pass` -> exactly the
  round-trip + carry-behavioral + attribute census fail. All
  four `pinned`.
- **Structural gate.** The two census rows (exact 4-hit attribute
  population incl. the homed R4 pair; zero dispatch spellings)
  plus the two spy rows jointly gate the by-name composition:
  E1/E2 prove a bypass fails exactly these rows while every
  behavioral row passes. The gate ran green on the consolidated
  tree first (the 7-row run); E1/E2 are its negative controls. A
  name/existence assertion alone would pass those controls, so
  none is used.
- **Coupling.** None. FAM-3 (`_iterable_class`) extends the same
  module but neither landing moves the other's lines; D1 rides
  to closeout homing without blocking this item.
- **Freshness.** HEAD `23b5f421` (unmoved). WT / HEAD / slot-2
  (post-change): `_queryset_private.py` `a26a8d43` / `ff8b2b46`
  / `61527cd9`; `querysets.py` `e6660894` / `4d8a3d39` /
  `641b158e`; `extension.py` `49346716` / `e18210e5` /
  `f7790033`; `test_extension.py` `4f935214` / `ee77ddf3` /
  `a0d12f89`; `test_querysets.py` `f986a690` / `498c31df` /
  `0a2e52bf`; `test_queryset_private.py` NEW / `b30e4365`.
  Population: full-package `rg` census (34 hits + evasion 0,
  post-change) + broader `result_cache` sweep incl. tests and
  examples, upstream `query.py` + `query.pyi` at installed
  Django 6.1.2 / django-stubs, `f2f18ba6` charter commit, f61 +
  f65 family records (precedent shapes, re-verified not
  inherited). Any fingerprint change reopens.

### R1 -- seal snapshot-key read `:3909` (rejected; distinct contract)

Reads the `_result_cache` key of the instance-namespace snapshot
the seal took without dispatching consumer code, not the live
attribute. Under a Django rename it moves, but under the seal's
snapshot-discipline contract, not this family's live-access rule
(f61 R1 precedent; folder FR-7 home). Trigger: the seal starts
reading live queryset attributes; that read joins F1.

### R2 -- `materialized_rows` exact-type read `:4095` (rejected; distinct contract)

Reads the slot out of the instance dictionary of an EXACT
queryset precisely so no attribute dispatch can answer -- its
docstring states the no-dispatch posture as the load-bearing
reason. Converting it to the typed owner call would change the
observation mechanism at a trust boundary (principle 8):
attribute access dispatches, instance-dict reads do not, and the
equivalence on exact querysets relies on lookup semantics the
snapshot read does not need. Same FR-7 home as R1. Trigger: the
seal discipline adopts typed reads for exact querysets -- a
folder-level decision, not this item's.

### R3 -- seal wording `:3918` (rejected; error vocabulary, not access)

`f"{cls_name}._result_cache is a ..."` names the slot in a defect
message; it reports Django state, it does not touch it. Moves
under the error-wording contract with its oracle
(`test_seal_carry_result_cache_refuses...`), not the access rule.
Trigger: the wording is generated from an owner constant.

### R4 -- subclass `self` pair `:222` / `:225` (rejected; subclass protocol)

`RecognizedFetchQuerySet._fetch_all` overrides Django's own
`_fetch_all`, whose protocol IS this slot: it reads its own cache
and interoperates with `super()._fetch_all()`, which reads the
same slot directly. Managing inherited storage inside the
subclass that owns the override is the class's own protocol
conformance, not external private-state access -- the same reason
`super()._clone()` at `:185` stays spelled locally. Under a
Django rename it moves under the subclass-protocol contract
(which must re-verify the whole `super()` interplay), not this
family's rule. Recorded in the census test's class docstring as
well as here. Trigger: the subclass stops being a `QuerySet`
and becomes an external manipulator of one.

### R5 -- `carry_result_cache` policy vocabulary (rejected; distinct identifier)

The `_SealPolicy` field shares a substring with the slot but
names a policy ("carry rows forward"), never the storage. Same
file, same subsystem, different mechanism entirely (f61 R3
precedent). Trigger: none within this family.

## Defects

- D1 (doc-only; NEW): the owner module's docstring claims every
  covered slot is undeclared by django-stubs ("so every direct
  access is an unknown attribute to the type checker"). This item
  makes that universal false: the stubs declare `_result_cache`
  (`list[_Row] | None`), which is why the new pair carries no
  suppression. The refresh wants one sentence but cannot land
  here: it must rewrite `:5`-`:7`, and `:7` sits inside the hunt
  hunk `@@ -7,6 +7,13 @@` (the `truth.instance_state` +7
  paragraph, no ledger row). Filed hunt-blocked with the exact
  hunk; meanwhile the exception is recorded at the owner in the
  per-function comments this item adds. Owner:
  `utils/_queryset_private.py` module docstring. Blocks nothing;
  home at closeout (or when the hunt lands).

No new defects beyond D1. No pre-existing failures: the baseline
scope (526 rows) ran green before the first edit.

## Pending execution

None. Every F1 proof executed in slot-2 on final bytes (run ids
under ## Implementation); no `proof:` entry is owed. No `gate:`
entry is owed.

Cells: `--cell sharded` and `--cell pg` are inapplicable by
construction (Worker-2 judges): the consolidated code is a pure
attribute-read/write branch with no database, alias, or dialect
decision, and the slot mechanics it relies on (Django sets
`None` in `__init__`, evaluation stores an exact `list`) hold
identically on every backend. The new tests evaluate querysets
only to populate the slot, on the default cell.

## Judgment

CONFIRM-consolidated. The nomination's count-2 re-derived
exactly at current bytes, both committed lines; the read-half
adjudication resolves to typed-access with a mechanical proof
(the gate narrows; the direct call type-checks clean) and a
boundary pin. The consolidation layers the two genuine halves
(seal write, guard read) over one spelling in the chartered
owner, keeps every intentional separation with a trigger, and is
proved behavior-preserving with gates that fail exactly the rows
a regression must fail. One doc-only defect filed (D1,
hunt-blocked); five rejections carry triggers.

## Implementation (Worker-1)

Tracked change (slot-2 vs worktree; the worktree carries no
`.py` edits -- this brief gave copy-only rights, so Worker-0
ports these six paths):

- `django_strawberry_framework/utils/_queryset_private.py`
  (+17/-0): the `queryset_result_cache` /
  `set_queryset_result_cache` pair appended at EOF.
- `django_strawberry_framework/utils/querysets.py` (+2/-1): seal
  write composes the setter; owner import gains one name.
- `django_strawberry_framework/optimizer/extension.py` (+4/-1):
  guard read composes the getter; owner import added; comment
  rewritten (gate-proves-queryset reasoning).
- `tests/utils/test_queryset_private.py` (NEW, +125/-0):
  round-trip pins + the two census rows.
- `tests/optimizer/test_extension.py` (+40/-0): G1 spy row + the
  gate-boundary row, inside the G1 section.
- `tests/utils/test_querysets.py` (+30/-0): seal-carry spy row
  beside the carry test.

Production net +23/-2 across the 3 package files; the rest is
tests. No test needed a banned-provenance word, a `pragma`, an
`Any`, or a new cast/widening/suppression; both new public
symbols carry docstrings; no overrides added.

Proof commands (all through `heavy`; pytest/basedpyright/prove
in slot-2 at `dry/f66-result-cache/consolidate`):

- Baseline (pre-edit):
  `pytest -n0 tests/optimizer/test_extension.py
  tests/utils/test_querysets.py --no-cov -q` -> 526 passed
  (`dry-20261010T074910-5f7563`).
- New rows: `pytest -n0 tests/utils/test_queryset_private.py +
  3 new node ids --no-cov -q` -> 7 passed
  (`dry-20261010T075311-7ca78c`).
- Regression (final bytes): the two consumer files + new file +
  `test_list_field.py` + `test_resource_policy.py` + the live G1
  HTTP oracle -> 925 passed
  (`dry-20261010T081021-1973b3`; first green
  `dry-20261010T075330-0d8de5` pre-dates the layout collapse).
- `basedpyright -p pyproject.toml` -> 0 errors
  (`dry-20261010T081126-5fd6a7`). First attempt
  (`dry-20261010T075442-bd8ab7`) failed 4: two unnecessary
  ignores (proving the stubs-declared fact) + two
  `reportPrivateLocalImportUsage` on test-side re-export reads
  (fixed by importing the real functions from the owner, the
  f65-forced shape).
- `basedpyright -p pyrightconfig.floor.json` -> 0 errors
  (`dry-20261010T081254-52925b`).
- `python scripts/check_truthful_reads.py --check` -> 120 files,
  tier-1 0 (`dry-20261010T081423-ac05fb`).
- `python scripts/check_public_types.py` -> OK, 2 allowlisted
  pre-existing diagnostics (`dry-20261010T080044-0c9068`;
  collapse touched tests only, outside its scope).
- `python scripts/check_trailing_commas.py --check` on all six
  paths -> 0 violations (`dry-20261010T081425-d13225`); the
  first run flagged 2 over-exploded 2-param test defs, fixed
  via the script's own `--fix` (single-param owner defs are
  exempt by its `params >= 2` rule).
- `prove dry/f66-result-cache/consolidate
  ~/dry/tmp/f66-result-cache-manifest.json` -> all 4
  entries `pinned`, restores byte-proved
  (`dry-20261010T080532-f5e757`; first attempt exposed 3
  wrongly-declared rows -- the census also pins the owner's own
  spelling presence -- corrected and re-proved).
- Coverage pin (focused scope, `--cov-fail-under=0`): owner
  module 35 stmts / 10 miss, missing `42, 48, 54, 63, 69, 87,
  106, 116, 144, 150` -- zero missing in `:151`-`:167`.
- After every edit: `uv run ruff check --fix <paths>` then `uv
  run ruff format <paths>` on exactly the touched paths, format
  last; final `ruff check` + `ruff format --check` clean.
- No shared-tree pytest: the shared tree holds no `.py` change
  under this brief, so there was nothing to run there.

Ledger rows owed to Worker-0 (`## Owned changes`):

- `django_strawberry_framework/utils/_queryset_private.py` --
  Family `queryset-result-cache-access` (f66) --
  `queryset_result_cache` + `set_queryset_result_cache` pair.
- `django_strawberry_framework/utils/querysets.py` -- Family
  `queryset-result-cache-access` (f66) -- seal carry write
  composes the setter; import.
- `django_strawberry_framework/optimizer/extension.py` -- Family
  `queryset-result-cache-access` (f66) -- G1 read composes the
  getter; import; guard comment.
- `tests/utils/test_queryset_private.py` -- Family
  `queryset-result-cache-access` (f66) -- NEW: round-trip pins +
  spelling census.
- `tests/optimizer/test_extension.py` -- Family
  `queryset-result-cache-access` (f66) -- G1 spy + gate-boundary
  rows.
- `tests/utils/test_querysets.py` -- Family
  `queryset-result-cache-access` (f66) -- seal-carry spy row.

## Independent verification (Worker-2)

Verdict: verified. The consolidation is sound at
the ported bytes: count-2 CONFIRMED by an
independent census, both halves compose the new
owner pair by name, equivalence holds on every
principle-8 axis, the gates fail exactly the rows
a bypass must fail (re-proved in my own copy with
a wider scope than W1's), the five rejections
carry real contract differences with triggers, D1
is confirmed hunt-blocked, and no third live site
exists. All gates re-ran green in slot-3 at
`dry/f66-result-cache/verify-1`. Six CC record
corrections below; none touches code or the
consolidation, so none blocks verification.

Copy: slot-3 synced fresh from the ported WT on
first run (`dry-20261010T082821-7ae80b`), then
byte-compared on all six touched paths (all SAME)
before any gate ran. WT equals slot-2 byte-exact
on all six, so the port is faithful. HEAD
`23b5f421` unmoved; every current-WT fingerprint
matches W1's third column exactly
(`61527cd9`, `641b158e`, `f7790033`,
`a0d12f89`, `0a2e52bf`, new file `b30e4365`).

Sequencing deviation, disclosed: this brief
ordered the full artifact (including Findings)
as required reading before any tracing, so
blind expectation-first tracing was impossible.
Mitigation: every count, pin, exclusion, and
gate below was re-derived from current bytes
with my own instruments before comparison, the
failability scope was widened past W1's, and
the two disagreements found (CC-1, CC-4) are
recorded with exact fixes.

### Own trace (my instruments, ported bytes)

- Literal census `rg -n "_result_cache"` over
  the package: 34 hits in 6 files
  (`4+2+1+1+6+20`), every hit homed: owner
  2 defs + 2 comments + 2 bodies, 2 consumer
  imports + 2 calls, the R4 `self` pair, R1/R2
  snapshot reads, the R3 f-string, 6 policy
  fields, 13 prose lines. No hit left over.
- Before-copy census (slot-1): 26 hits in 5
  files plus exactly 1 evasion hit (the
  extension `getattr` at `:1203`); the seal
  write at `:3991`. Delta `+8` = 6 owner lines
  + 2 import lines, arithmetic exact.
- Evasion sweep: zero `getattr` / `setattr` /
  `hasattr` / `delattr` / `attrgetter`
  spellings of the slot; zero subscript reads;
  zero `del` statements in the four family
  modules; the one `.pop(` in range names an
  unrelated key. Dispatch extinct, no other
  form ever existed.
- Owner shape: pair appended at EOF, typed
  `(QuerySet) -> list[object] | None` and
  `(QuerySet, list[object] | None) -> None`,
  no suppression; the 14 sibling functions
  each carry exactly one ignore (`rg -c` = 14).
  Upstream pins confirmed at installed bytes:
  django-stubs `query.pyi:84`
  (`_result_cache: list[_Row] | None`),
  Django 6.1.2 `query.py:372` (`None` in
  `__init__`), evaluation stores an exact
  `list` (`:2287`).
- Compositions by name: seal write at
  `:3992` (same `cast`, same value),
  guard read at `:1206` (`is not None` kept).
  Gate mechanics confirmed: `NormalizedSource`
  is a discriminated union whose doc comment
  states the narrowing, `normalize_query_source`
  returns every non-queryset flagged `False`,
  the extension returns early on that flag.
  The main basedpyright 0-error run below is
  the mechanical proof the direct call needs
  no new cast or guard.
- No third site: the only `materialized_rows`
  callers are the two `types/resolvers.py`
  locals; the only other `result_cache` tokens
  are locals and prose; examples carry prose
  only. Test-side spellings plant hostile
  state or assert what landed; the two spies
  wrap the owner but assert the call, never
  derive an expectation from it.
- Owner choice, judged independently:
  `utils/_queryset_private.py` is the right
  owner (10 sibling slots, same pair shape,
  stdlib-plus-Django-only imports so the
  optimizer -> utils edge cannot cycle).
  `utils/querysets.py` ownership would split
  the private-state responsibility the
  charter already centralizes.

### Equivalence (principle 8)

- Seal write: identical assignment, same cast,
  same target object; `__setattr__` dispatch
  is bytecode-identical inside or outside a
  function. Unchanged, period.
- Guard read on evaluated (incl. empty),
  unevaluated, and honest non-queryset
  inputs: identical values. Empty-list
  passthrough is pinned by
  `test_optimizer_preserves_async_adapter_evaluated_cache`
  (plants `[]`); non-queryset return is pinned
  by the new boundary test plus the
  pre-existing passthrough rows.
- Dropped tolerance (slot deleted off a
  `QuerySet`; `__class__`-spoofed
  non-queryset): both undocumented incidental
  behavior, correctly analyzed. `del` of the
  slot is absent package-wide and no
  production path performs one; the spoof
  crashed one line later before (`apply_to`
  reads `.query`) and crashes at the guard
  now, same exception family. Recorded in the
  artifact and the guard comment.
- My V1 hand-copy control (inline `getattr`
  restored) passed all four behavioral rows
  in scope while failing exactly the spy +
  dispatch-census rows: the two spellings
  agree observably, and only the gate rows
  distinguish them.

### Reconciliation with W1 (CC corrections)

CC-1 (counts): extension.py is `+7/-4`, not
`+4/-1` (numstat; the comment rewrite is
`-3/+5` plus the call swap plus the import),
so production net is `+26/-5`, not `+23/-2`.
Fix the two figures under `## Implementation`.
The plan run-13 submission line repeats them;
history, note only.

CC-2 (owner def lines): the defs sit at `:153`
and `:161`, not `:151`/`:160` (bodies `:158`/
`:167` as cited). Fix the two def cites in F1
`Sites + roles`; the `:151`-`:167` append
range stays (it covers the leading blanks).

CC-3 (rejection pins): R1 `:3909` -> `:3910`,
R3 `:3918` -> `:3919`, R2 `:4095` -> `:4096`
for the code line (`:4095` is its comment).
Fix Enumeration rows 6/7/8 and the three
`### R-N` headings.

CC-4 (ledger sentence): "No ledger row names
any of the six touched paths" is false: one
adopted-orphan row names
`tests/optimizer/test_extension.py` (the
`optimizer-execution-frame` 51+/0- frame
gate). Fix the sentence to name it. No
attribution impact: ledger-listed paths are
explicitly buildable, and f66's hunks there
are pure insertions in a disjoint region.

CC-5 (index row, transcribable): Worker-0 rows
the Responsibility-index row exactly as:

```text
| `queryset-result-cache-access` | `utils/_queryset_private.py::queryset_result_cache` + `::set_queryset_result_cache` | `utils/_queryset_private.py`, `utils/querysets.py`, `optimizer/extension.py`, `optimizer/nested_fetch.py` (R4 subclass-protocol exclusion), `types/resolvers.py` (R2 consumer) | Family `queryset-result-cache-access` | consolidated (f66: F1 2->1 over the seal carry write + G1 guard read; R1-R5 exclusions with triggers; D1 doc-only hunt-blocked) |
```

CC-6 (Families row): tick the f66 checkbox
with the artifact link and `run 13 W2-1
verified (CONFIRM-consolidated 2->1, owner
pair + 2 by-name composers, 7 new rows,
failability 4 pinned in-copy, R1-R5 with
triggers, D1 hunt-blocked, CC-1..CC-4 record
fixes, zero defects)`.

The six ledger rows under `## Implementation`
are confirmed verbatim; no correction owed.
No D-N defect: the only observation (the seal
carry arm has no dedicated live-tier oracle)
is pre-existing status quo, not new tier debt
-- the consolidation changes the spelling, not
the reachability, and live reachability of
that arm through fakeshop is unproven either
way.

### Gates re-run in slot-3 (all green)

- New rows (4 file rows + 3 node ids):
  7 passed (`dry-20261010T082831-5040f0`).
- Regression (both consumer files + new file
  + `test_list_field.py` + `test_resource_policy.py`
  + live G1 HTTP oracle): 925 passed
  (`dry-20261010T082849-61b3b0`), exact count
  match.
- `basedpyright -p pyproject.toml`: 0 errors
  (`dry-20261010T082957-6c7aa9`).
- `basedpyright -p pyrightconfig.floor.json`:
  0 errors (`dry-20261010T083125-7c7620`).
- `check_truthful_reads.py --check`: 120
  files, tier-1 0 (`dry-20261010T083254-44497a`).
- `check_public_types.py`: OK, 2 allowlisted
  pre-existing (`dry-20261010T083259-d74b58`).
- `check_trailing_commas.py --check` on all
  six paths: 0 violations
  (`dry-20261010T083310-882cf7`).
- `ruff check` + `ruff format --check` on all
  six paths: clean, 6 formatted
  (`dry-20261010T083316-0c6c31` /
  `dry-20261010T083316-be6de7`).
- Failability re-proof, my manifest
  `$TMPDIR/w2-f66-manifest.json`
  (`dry-20261010T083357-7ae29f`): all 4
  entries pinned, restores byte-proved, copy
  re-compared SAME on all six after. V1/V2
  are the behavior-preserving hand-copy
  controls (exactly the gate rows fail); V3/V4
  break the owner getter/setter (exactly the
  round-trip + tripwire/behavioral + census
  rows fail). V1's scope is wider than W1's E1
  (async + plan-miss behaviorals added), all
  passing under the hand copy.
- Banned-word scan of the item diff plus the
  new file: clean. Item diff vs baseline is
  exactly the five tracked files plus plan
  lines (104+/5-); test diffs are pure
  insertions (0 minus-lines), so no oracle
  was rewritten.

### Judgments

- Matrix: all six axes discharged against the
  real surface; M2 inapplicability reason
  accepted (pure synchronous attribute
  access; the async path shares `_optimize`,
  oracle green).
- Cells: sharded/pg inapplicable by
  construction, AGREED. The consolidated code
  branches on a pure attribute read/write
  with no database, alias, or dialect
  decision; the slot mechanics hold
  identically on every backend; the new tests
  touch the default cell only.
- Rejections: R1/R2 (dict reads, different
  mechanism -- R2's no-dispatch posture is
  load-bearing per its docstring), R3
  (wording), R4 (subclass protocol;
  additionally forced, since
  `super()._fetch_all()` spells the slot and
  cannot compose the owner), R5 (distinct
  identifier). Triggers present throughout.
- D1: confirmed -- the universal stubs claim
  at `:5`-`:7` overlaps hunt hunk
  `@@ -7,6 +7,13 @@`, exact hunk verified;
  doc-only, hunt-blocked, exception recorded
  in the per-function comments. Rides to
  closeout homing.
- Import adjacency: both import insertions sit
  beside hunt `+` lines without modifying
  them (extension `truth` line above,
  querysets hunt-hunk context around),
  verified vs HEAD and vs baseline.
- Coupling: none blocking. FAM-3 appends to
  the same EOF after this item lands.

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
