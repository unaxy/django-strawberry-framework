# DRY review: `drymd-standing`

Status: verified
Run: 0.0.15 2026-10-11-16

## System trace

Standing-doc adoption into `docs/dry/DRY.md` only: seven edits (consolidation
bar, behavioral proof replacing census, artifact caps, foreign-rule exclusion,
shrinkage record, drift closure, freshness scoping). Read DRY.md in full plus
the plan dispatch and the owned-changes ledger before touching anything. Dirt
attribution: live `docs/dry/DRY.md` vs `git show HEAD:` shows exactly one hunk
(the worked-example oracle sentence), matching the ledgered run-15 batch-7 row
for DRY.md section 2; nothing else dirty on the path. All edits landed in the
workspace copy; the live tree is untouched.

## Verification

### Matrix

1. Cross-flavor mirroring -- inapplicable: standing prose, no public surface.
2. Sync/async twins -- inapplicable: no await boundary in the edited sections.
3. Derived knowledge -- the edited rules state procedures; no fact is re-derived.
4. Round-trip pairs -- inapplicable: no encode/decode pair in the edited sections.
5. Contracts in another medium -- the edits change the standing contract itself; no second medium restates these sentences.
6. Enforcement by omission -- inapplicable: no family membership changes; prose adoption only.

### Freshness

Target `docs/dry/DRY.md` blob `d9493ea6` before, `f6f051ec` after (HEAD
`c37a08a0`); item baseline `a8bdfafd`; searched population = the one target
file in full; contract sources = the dispatch brief plus the ledger. Excluded
modules: none named -- the item is scoped to the one standing file by the
brief. Both proof gates ran in the copy and went green (details under
Findings); independent re-read checks ran on the live side.

## Findings

F1 -- adopt the seven standing edits (one adoption, seven hunks, single
owner `docs/dry/DRY.md`).

Contract + variation -- the standing rules for what a DRY item may
consolidate, how it proves sameness, and how it records the result. Varies
only by future maintainer edits to this file.

Sites + roles -- one definition (the seven hunks in the copy's DRY.md);
no consumers, oracles, or projections touched.

Challenges -- standing prose, not package logic: no change challenge counts
definitions. The adoption removes no package change obligation and adds no
machinery; its bar is the file's own gates plus independent re-read.

Owner + lifetime -- `docs/dry/DRY.md`, the standing owner of DRY procedure.
No stored derivation; no lifetime fields owed.

Migration -- principle 9 replaced in place (1-8, 10-11 untouched); the
census-based gate bullet replaced by the negative-control bullet; the
gate-only outcome dropped with the census gate it required; four appended
sentences across three sections; two new/rewritten record bullets.

Shrinkage -- net +29/-18 lines over the live file; deleted: the census
principle, the census gate bullet with its name-assertion example, the
gate-only outcome. Machinery attestation: no new helper, wrapper, or
constant; the added sentences are plain standing prose.

Behavioral proof -- doc-only item: proof is the file's own gates, both run
in the copy via the workspace runner. `check_trailing_commas.py --check
docs/dry/DRY.md` exit 0, violations 0 (run dry-20261011T061521-a9027d).
`check_citations.py` exit 0, 3351 citations resolve
(run dry-20261011T061524-5b5315). Both runs report the copy modified on
exactly one path (`docs/dry/DRY.md`).

Negative control -- none: bypass is not the threat for a standing-prose edit.

Re-read -- link-definitions block byte-identical to live (all 10 group
headers, order, defs); zero new non-ASCII bytes across all added lines; zero
new cross-file links; every added line within 99 chars; principles 1-11
otherwise unrenumbered; no gate-only / census-gate remnants.

## Defects

None found.

D-W2-1 (Worker-2): `docs/dry/worker-2.md:33` still says "each structural gate
fails its negative control" -- cites the deleted field, contradicts canonical
DRY.md. Follow-up standing reword; out of this DRY.md-only item.
D-W2-2 (Worker-2): `docs/dry/export_dry_review.py:284` brief template still says
"a structural gate with its negative control" -- future plans inherit stale
vocabulary. Owner: DRY planner; follow-up item. (spec-059 "gate-only" checked:
fieldset-domain term, not stale.)

## Judgment

The seven edits land exactly as briefed, gates green, scaffold intact, prose
plain and ASCII-only. Ready for independent verification; port is one file.

## Implementation (Worker-1)

Landed all seven edits in the copy's `docs/dry/DRY.md` (+29/-18 vs live,
blob `d9493ea6` -> `f6f051ec`); live tree untouched. No `.py` touched, so no
ruff, pytest, or basedpyright runs. Port: copy the file to the live tree.

## What shrinks

| edit | rule | change | owner | net | machinery attestation |
|---|---|---|---|---|---|
| 1 | consolidation bar | bar sentence appended to the change challenge | `docs/dry/DRY.md` change challenge | +4 | no new machinery; one prose paragraph |
| 2 | sameness proof | census principle replaced by behavioral proof; census gate bullet replaced by negative control; gate-only dropped | `docs/dry/DRY.md` principle 9 + finding record | +6/-14 | no new machinery; net deletion of the census shape |
| 3 | artifact caps | caps sentence appended to the artifact section | `docs/dry/DRY.md` artifact | +4 | no new machinery; one prose paragraph |
| 4 | foreign-rule exclusion | exclusion sentence appended to the change challenge | `docs/dry/DRY.md` change challenge | +4 | no new machinery; one prose paragraph |
| 5 | shrinkage record | shrinkage bullet added after migration | `docs/dry/DRY.md` finding record | +3 | no new machinery; one record bullet |
| 6 | drift closure | closure sentence appended to baseline and ownership | `docs/dry/DRY.md` baseline and ownership | +4 | no new machinery; one prose paragraph |
| 7 | freshness scoping | freshness bullet rescoped to owner + touch paths + proving tests | `docs/dry/DRY.md` finding record | +4/-4 | no new machinery; bullet rewrite in place |

## Independent verification (Worker-2)

Own trace (live file + `git diff a8bdfafd -- docs/dry/DRY.md`, before Findings):

| # | section | content |
|---|---|---|
| E1 | Design principles | principle 9 replaced in place by behavioral-proof rule |
| E2 | Finding a candidate | Bar + foreign-rule exclusion appended (one block) |
| E3 | Finding record | Shrinkage bullet added after Migration |
| E4 | Finding record | Structural-gate bullet replaced by Negative-control bullet |
| E5 | Finding record | Freshness bullet rescoped to owner + touch paths + tests |
| E6 | Baseline and ownership | Drift-reopens-nothing paragraph appended |
| E7 | Artifact | Caps paragraph appended |

8th change: none. Diff is exactly these hunks, +29/-18; the plan +12 beside it
is Worker-0 dispatch bookkeeping. Blobs d9493ea6 -> f6f051ec match W1 pins.
Principles 1-11 intact; added lines ASCII-only, <=99, zero new links/defs, zero
process-history tokens; link block byte-identical (10 headers, order, alpha
defs); Structural-gate/gate-only vocabulary fully gone from DRY.md.
Gates fresh: commas exit 0 / 0 violations (dry-20261011T062254-c9cbd6);
citations exit 0, 3351/3351 (dry-20261011T062258-0e043c). W1 run ids
dry-20261011T061521-a9027d + dry-20261011T061524-5b5315 both on disk, verdicts
reproduced. Pending execution absent (= empty); coupling none (single finding).

Reconciliation: W1's 1-7 group the same bytes by rule (Bar/exclusion split, P9 +
gate-bullet + gate-only merged) -- cosmetic, coverage identical. Three
divergences: W1's "no remnants" misses two stale sentences and one orphan def.

R1 STALE (Tests, DRY.md:282): "Every gate ..." points at a deleted field while P9
bars census gates. Replace L282-283 with (92 + 62 chars):
independently legible. Every behavioral proof a finding relies on must be shown able to fail
for the divergence it guards (`scripts/prove_failability.py`).
R2 STALE (Workers, DRY.md:439): "each gate fails its negative control" dangles with
wrong polarity (bullet demands refuse, or none). Replace L439 with (87 chars):
   reason); confirms each negative control refuses; checks the item-scoped diff against
R3 ORPHAN (DRY.md:566): `[test-resolvers]` has zero uses; START.md demands "every
def a use". Delete the one def line; `<!-- tests/ -->` header stays.

Re-pass: apply R1 + R2 + R3 in DRY.md only, re-run both gates, resubmit to this
verifier. Verdict: revision-needed.

## Iterations

Pass 2: R1 Tests sentence -> behavioral proof, R2 Workers sentence -> refuses
polarity, R3 orphan `[test-resolvers]` def deleted (header kept); nothing else
touched. Gates re-run in the copy, both green: commas exit 0 / 0 violations
(dry-20261011T062808-3e1944), citations exit 0 / 3351 (dry-20261011T062820-59c75d).

Verify-2 (Worker-2 pass 2): R1/R2/R3 verbatim (92+62, 87 chars; def gone,
header kept); reverse-applying exactly those three to live 68df913d rebuilds
pass-1 pin f6f051ec, so the 7 sites are byte-identical (+29/-18) and nothing
else moved. Coherence: zero stale gate/census/structural/gate-only tokens
(P9 "never by census" + "gates are barred" are the prohibition, not remnants);
15 defs / 15 uses balanced, zero orphans; principles 1-11 intact (only P9
changed); added lines ASCII-only, <=99, zero new links, zero history tokens;
link block 10 headers in order, alpha defs. Fresh gates in verify-2 copy
(slot-3, 68df913d, identical to live): commas exit 0 / 0 violations
(dry-20261011T063206-f3e6f9), citations exit 0 / 3351
(dry-20261011T063210-f5ff31). All six prior run logs on disk. Verdict:
verified.
