# DRY review: `prepared-view-handoff-reopen`

Status: verified
Run: 0.0.15 2026-10-12-22

Re-derivation of the handoff grammar (middleware pack + views unpack)
at new bytes. `ITEM_BASELINE=b8c09a0c` (stash of HEAD `c37a08a0`;
HEAD unmoved since). The prior shape artifact is trigger input only;
every verdict re-derived fresh. Never read any `worker-memory/`.
Verdict: F1 CONFIRMED count-2 and LANDED fenced — both halves move
to `_boundary_ordering.py` via stamp + consume helpers; the dirty
mount-read line and its gate stay untouched. Copy only; port pending.

## System trace

After `process_view` builds a view instance and runs its boundary, it
stamps `(mount token, prepared view instance)` under the mark; the
`as_view` closure dispatches on that instance instead of building a
second one — only for a well-formed pair carrying its own mount,
consumed exactly once. Pack `:250`-`:251` (read `:249` above it is
concurrent dirt); unpack `views.py:583`-`:588` (arms `:602`, `:612`);
mint `:579`, callback stamp `:621`; names + prose in the owner.
Sweep over 121 WT files: every executable hit in the three indexed
files — one construction, one validation, one `delattr`, one mint.
Attribution vs HEAD: owner clean; `views.py` dirt all at/above `:219`
(1 f39-ledgered + 3 foreign); middleware 8 hunks all foreign, none
ledgered; `:250`-`:252` byte-identical. Oracle file churning; untouched.

## Verification

### Matrix

1. Cross-flavor: one closure, one `process_view`; no other surface.
2. Sync/async: no twin — arms share the closure; twins publish only
the ContextVar. 3. Derived: order at pack, indexes at unpack, no
shared owner (F1); token by identity, never re-materialized.
4. Round-trip: this axis IS the family. 5. Media: O1 (`:291`) + O3
(live `:3267`) pin behavior; O2 HEAD-only; zero standing prose.
6. Omission: all mounts share the closure; declines + stampless
paths take designed fallbacks. No guard missing.

### Enumeration

Mark executable 3 (write/read/delete), def 1, imports 2; mount
executable 2 (stamp/read), def 1, mint 1; construction 1;
validation 1; gate 1; closure 1+2 calls; `setattr(request` 3;
`getattr(request, _BOUNDARY` 4; `(mount` 2 + 1 prose false
positive; `prepared[0]` elsewhere are resolver-source pairs.

### Challenges

C1 reshape: pack + unpack, count 2. C2 token: mint only, 1. C3
strictness: closure only, 1. C4 absent-mount: read+gate only, 1.

## Findings

### F1 — handoff grammar (CONFIRMED count-2, LANDED fenced)

- Contract: 2-tuple stamped iff mounted, honored iff exact + own
  token, consumed once. Varies on shape; posture fixed.
- Sites: defs 2 (pack `:250`-`:251`, unpack `:583`-`:588`); now
  adjacent in the owner, call sites consumers. Oracles O1/O3 + 2
  new rows; projections: owner prose, `as_view` paragraph.
- Owner: `_boundary_ordering.py`, pure per-request helpers. No new
  edge; `views.py` excluded by dependency direction, middleware by
  responsibility. Lifetime: protocol-owned, mount-identity key,
  post-boundary publish, helpers-only mutation, consume invalidates.
- Migration (LANDED): helpers added; `:251` one stamp call (read +
  gate stay — C4 facet fenced off dirt); closure one consume call.
  C1 now one edit. Mint/read/gate/boundary/CSRF stay put.
- Proof (execution-verified): 4/4 rows pass migrated; O1+O3 passed
  pre-edit; 5/5 failability mutations fail exactly their declared
  row, restores byte-compared. Rejects: swapped slots,
  inverted/dropped token match, missing consume, consumed decline.
- Negative control: any inline copy diverging from either helper
  body fails the same rows the E1–E5 mutations fail.
- Coupling: none; pack call correct under any read binding `mount`.
- Freshness: owner `f91ccd73`→`cd4bd6af`; views `72ec3e2d`→
  `82e95fa1`; middleware `cb663863`→`37c10b2f`; new test
  `ecef43df`. BASE==WT; HEAD unmoved; pop. 121; O1 file
  `6461503f` (churning, pinned now), O3 file `ce099d5a`.
- Trigger (spent): read-guard fenced out; re-verify pack call only
  if a future read changes what `mount` binds.

### R1–R9 — rejections (difference + trigger each)

- R1 completion stamp: boolean record, ignored by closure. T: payload.
- R2 method name: identity from one constant. T: per-mount variance.
- R3 marker bit: boolean recognition. T: more than presence.
- R4 arms: one closure, transport split. T: arms diverging.
- R5 ContextVar publish: exemption only. T: needing the instance.
- R6 recognition: builds, never packs/validates. T: packing itself.
- R7 toolbar tag: intra-module persistent bool. T: crossing/token/use.
- R8 oracle spelling: literal by principle. No trigger.
- R9 policy: branches on R1 stamp only. T: branching on the pair.
No sub-rule decomposed (C2/C4/C3 are single-owned facets).

## Defects

None. No ticked row proven wrong. (O2 deletion + oracle-file churn
are concurrent foreign work, not tree defects.)

## Pending execution

Nothing deferred. Cells inapplicable by construction (attributes +
tuple + identity only; Worker-2 judges). No `gate:` owed.

## Judgment

F1 CONFIRMED (C1 count 2, same contract/reasons) and LANDED fenced:
halves owned adjacently, dirt byte-untouched; nine rejections with
triggers (R8 principal). 4 rows pass; 5 failability entries exact.
Ready for independent verification.

## What shrinks

Rule: the prepared-view handoff payload grammar — the `(mount
token, prepared view instance)` pair the boundary middleware stamps
and the `as_view` wrapper consumes.
Change: both halves (pack construction in `process_view`, the
unpack/validate/consume closure body) move into
`_boundary_ordering.py` as `stamp_prepared_view` +
`consume_prepared_view`. The pack call site keeps its mount read +
`None`-gate (the C4 facet, fenced off concurrent dirt); the closure
keeps its two arm callers. Two branch rows land in package tier:
malformed and foreign-token stamps are unreachable from a real
query (the middleware stamps well-formed pairs only), so they are
forged directly like O1.
Owner before: none (parallel spelling across two modules). Owner
after: `django_strawberry_framework/_boundary_ordering.py`.
Net lines over ITEM_BASELINE: package +30 (owner +34 with
docstrings, `views.py` -4, `middleware/request_body.py` 0); tests
+76 (one new module, zero existing tests touched).
Machinery attestation: no driver, registry, mode flag, or record
type — two pure per-request functions, the minimum vehicle for two
grammar halves. One-caller wrappers kept under principle 11 as
boundary names: each names the half it owns, and inlining either
re-spans the rule across modules. No new dependency edge; no
behavior change (moved expressions byte-identical).

## Implementation (Worker-1)

Copy `slot-5` (`dry/prepared-view-handoff-reopen/consolidate`;
shared tree unmoved at every run). Edits on byte-clean lines with
byte-identical adjacency: owner +34 (helpers after the method
name); closure body 5→1 + import swap; pack `:251` 1-line swap +
import swap; new `tests/test_prepared_view_handoff.py` (76 lines,
2 rows; no banned words). Manifest `failability-handoff.json` sits
at the copy root. Runs: baseline `...064042-c3c2b9` 2 passed;
basedpyright `...064350-0df274` 0/0/0; floor `...064400-bf173b`
0/0/0; truthful-reads `...064429-c94512` tier-1 0 (=== baseline);
commas `...064431-e0fed4` 0; citations `...064439-d87c38` 3349 OK;
post `...064454-d99adb` 4 passed; prove `...064646-54b660` 5/5,
restores byte-compared. Ruff fix + format clean on all four paths.
Live tree holds the artifact only. Port: apply the copy's 3-file
diff + new test file as-is; every concurrent hunk preserved (no
edited line is a dirt line). Ledger rows owed: 3 package paths +
new test (`stamp_prepared_view`, `consume_prepared_view`, closure
body, pack call site, 2 branch rows).

## Independent verification (Worker-2)

Own trace, derived first-hand from the before (slot-4) and
consolidate (slot-5) copies before opening `## Findings`
(disclosure: one read window overshot into F1's first lines;
every count below was re-derived, never inherited).

Sites + roles. D1 pack (definition):
`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`
#`setattr(request, _BOUNDARY_PREPARED_VIEW, (mount, view))` —
the shape/slot-order definition, sole writer. D2 unpack
(definition): `views.py::_RequestBodyBoundaryMixin.as_view::prepared_view`
— getattr + 3-clause guard (exact-type tuple, len 2, `is`
own mount) + delattr + `[1]`; the shape/identity/consume
definition. Consumers: both `as_view` arms call the one
closure (shared body, not twins); post-edit the pack
call-site and closure compose by name. Single-owned
adjacent, correctly untouched: mint (`as_view`
`mount = object()` + callback stamp — sole mint
package-wide); mount read+gate (`truth.static_attr` +
`is not None` — sole read); `_BOUNDARY_ENFORCED`
stamp/reads; `_BOUNDARY_METHOD` probe+invoke. Oracles:
async-arm `tests/test_views.py:291` (fresh + matching-pair
consume + exactly-once delete); the live fakeshop suite
(middleware installed, so every live query runs pack + sync
consume); 2 new sync ignore-arm rows. Projections: owner
module docstring, `as_view` handoff paragraph.

Counts (own challenges). MC1 reshape (add/reorder a slot):
D1+D2 = 2 — pack carries the slot order, unpack the
guard+indexes+consume; each real logic. MC2 token identity
(`is`→`==`): D2 only = 1. MC3 consume (delete→peek): D2
only = 1. MC4 absent-mount (read/gate change): middleware
read+gate only = 1, single-owned and correctly left behind
— the fence is sound. MC5 guard strictness: D2 = 1.
Mechanism census re-derived: one `delattr(request`, one
`(mount, view)` pack, one `is not mount`, one mint, one
mount read package-wide; other `is not tuple` hits are
unrelated rules. No second unpack definition exists. Owner:
`_boundary_ordering.py` by principle 7 — the documented
protocol owner both sides already import; `views.py` or
middleware would reverse the no-import-either-way
dependency. Own verdict (pre-Findings): LAND.

Reconciliation (no material difference). F1: concur on
contract, sites, owner, lifetime, migration. "4 rows" = O1
+ O3 + 2 new (W1's post command recovered from evidence,
re-run below). Enumeration verified member by member: mark
3+def+2 imports, mount 2+def+mint,
construction/validation/gate/closure, `setattr(request` 3
(pack, ENFORCED, toolbar R7), `getattr(request, _BOUNDARY`
4, `prepared[0]` elsewhere = resolver-source pairs
(`connection.py`, `list_field.py` bodies read),
population 121 re-derived by count. Nit (not
verdict-bearing): "`(mount` 2 + 1 FP" reproduces under no
single pattern tried (pre: 1 exec + 2 prose; post
word-boundary: 3 + 2) — but every hit homes to F1, an
oracle, or a projection; no unhomed member. Matrix: all 6
concur, incl. ax2 (twins publish only the ContextVar) and
ax5 (O1 + live O3 read; O2 confirmed HEAD-only:
`test_middleware_ignores_an_unreadable_optional_mount_handoff`,
deleted with the foreign read-rewrite; "zero standing
prose" read as zero stale prose). R1–R9: each carries
difference + trigger (R8 triggerless-principal, run-9
precedent); R4/R5/R6/R7/R9 spot-verified against bodies.
Equivalence (principle 8): pack is the identical
expression; unpack a byte-identical predicate with
identical short-circuit order, delete, and return; O1 pins
async incl. delete, O3 live pins the sync round trip incl.
setup-once; declines degrade to fresh, pinned by the 2 new
rows; ENFORCED/METHOD/CSRF/fallback paths have zero diff
lines. Oracles: zero existing tests touched (`copy_edits`
= exactly the 4 files); new rows spell literals and import
only the 2 constants — no oracle reads the owner.
Behavioral + tier correct: malformed/foreign unreachable
from a real query (sole writer stamps well-formed pairs
only). E1–E5 guard swapped slots, inverted/dropped token,
missing consume, consumed decline — each fails exactly its
declared row (re-run below). Pending execution: nothing
deferred; cells inapplicable by construction endorsed
(attribute + tuple + identity only); no `gate:` owed.
Attribution: live == before on all 3 paths; owner clean vs
HEAD; every W1 hunk lands on HEAD-clean lines (both import
dirts sit below the paren-close; the pack dirt is the read
lines above, preserved byte-identical); adjacency
byte-identical; all four fingerprints match byte for byte.
Prose rules: 9-word banned sweep clean on new tests; no
process provenance in prod diff ("first slot" is domain
language); `path::Symbol` citation in the test docstring;
no spec/GLOSSARY/KANBAN/START sentence mentions the
handoff, so none is falsified. Bar met: real change
obligation (C1=2), no machinery (two pure functions, P11
attestation recorded, swaps inside existing import blocks
— no new edge). Runs (all via `heavy` + `workspace.py`):
4/4 re-run green in slot-5 (`dry-20261012T065747-660abd`,
exit 0); full 5/5 failability re-pinned at verify-1 on
seeded bytes (`dry-20261012T065817-90390e`, exit 0, every
restore byte-compared); `ruff format --check` (4 already
formatted) + `ruff check` (clean) on all four paths. No
defects found; no `## Defects` entry owed (the `(mount`
nit is not routable to an owner). Verdict: `verified`. No
revision candidate: no second unpack definition exists
package-wide, the fence is sound, the port is the copy's
3-file diff + new test file as-is.
