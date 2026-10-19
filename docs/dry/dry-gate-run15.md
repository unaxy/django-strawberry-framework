# DRY review: `gate-run15`

Status: verified
Run: 0.0.15 2026-10-10-15

Freshness: HEAD 23b5f421 (detached, unmoved); status 565 at start, 566 at end (+1 = this
artifact, untracked); tracked bytes identical (`git diff` vs gate-start stash empty);
pyproject 21cccc6d, uv.lock 8fb5f01c; package digest sha256:5bbda356 on all 8 runs
(moved since run-14 gate 2d87dc60: run-15 repairs landed); gate bound 2efd8b6b,
result gate-dry-20261011T014120-c5c57d.json.

## System trace

`heavy workspace.py gate dry --suites lint,default,floor,sharded` in the gate copy, then
4 pending proofs via `heavy workspace.py run dry/gate-run15/consolidate --cell sharded`,
one flow at a time, machine GREEN throughout. Fresh pending sweep: 249 artifacts swept
(dry-gate-rerun.md superseded, excluded); 213 carry `## Pending execution`; exactly 3 name
a runnable sharded command (U-ca-1 trio, U-qs-1, U-perm-1) — reconciles with the verified
cells enumeration; rest = inapplicable-by-construction, blocked B-* proofs riding unlanded
consolidations, default-cell witnesses (strict subsets of the default suite, discharged by
it), or pg prose with no command. Run-15 defect artifacts carry no Pending section.

## Results

- lint (dry-20261011T003322-9e8480): exit 0, passed.
- default (dry-20261011T003637-61936c): exit 0, 10418 passed, 43 skipped, coverage 100.00%.
- floor (dry-20261011T005423-e362c3): exit 0, 10415 passed, 46 skipped.
- sharded (dry-20261011T012353-13ce01): exit 0, 10439 passed, 40 skipped.
- Skips reconcile: sharded = default − 2 module skips − 1 pin-skip (pin runs); floor =
  default + 3 (2 postgres-import skips + 1 Django<6.1 skipif); collected 10461/10461/10479.
- U-ca-1 trio (dry-20261011T014141-7cc67a): exit 0, 3 passed, deferred proof now re-proved.
- U-qs-1 prefetch (dry-20261011T014226-f8d244): exit 0, 44 passed / 2009 deselected.
- U-perm-1 (dry-20261011T014509-0b1285): exit 0, 6 passed / 76 deselected.
- Marked files (dry-20261011T014529-6e8006): exit 0, 20 passed (19 + 1).
- Pending total 73 passed, 0 failures, counts match the cells item exactly; all digests
  5bbda356 = gate suites; shared_moves only this artifact's own interim edits.

## Defects

None. Zero failures across 4 suites + 4 pending proofs; no item-back, no new rows.
- D-W2-1 (Worker-2, record-only, verdict-neutral): `## Pending execution` blocked list omits f40/f42 (meets-bar stays-blocked, same status as listed f38/e8/e9) + f41 (retired, same status as the 6 listed retired peers) vs the run-13 B-* record; completion recorded in `## Independent verification (Worker-2)`, routes to Worker-0's closeout Outcomes.

## Pending execution

- pg cell (U-ca-1 "any PG cell" + per-artifact pg notes; no artifact names a pg pytest
  command): authorized, not runnable on the remote host (no docker; `command -v docker` empty).
- Blocked B-* proofs (f36/f37/f38/f46/f60/f63/f64/e8/e9 + post-set/async/sync-boundary):
  still ride unlanded consolidations; unrunnable until unblock lands, listed not run.

## Judgment

GREEN: lint + default (100.00%) + floor + sharded all exit 0 on final run-15 bytes, every
surviving proof executed (73/73 pending green), pg stays the sole authorized-unrunnable
cell (deferred to maintainer per 5j only if a pg verdict is ever required). Gate record:
8/8 runs green, zero drift, verdict ready for Worker-2.

## Independent verification (Worker-2)

Own sweep (249 artifacts = 250 `dry-*.md` minus superseded `dry-gate-rerun.md` minus this
artifact; 213 carry `## Pending execution`): exactly 3 name a runnable sharded command —
U-qs-1 (`dry-file-utils__querysets.md` entry 1, `proof:`), U-perm-1
(`dry-file-permissions.md` entry 1), U-ca-1 trio (named in
`dry-rule-child-queryset-alias-inheritance.md`). Reconciles with W1's 4: my 3 = W1's
trio+prefetch+perm; the 4th (marked files) is the brief-ordered D1-fix/sharded-files run,
not a `proof:` entry — same 4 as the verified cells item, same order.
Evidence integrity (all 8 run ids in `runs.jsonl` + logs present): exits all 0, digests
all `5bbda356`, provenance headers fresh-copy, default log carries `100.00%` coverage;
skips reconcile (43 = 41 individual + 2 module; sharded 40 = 43−2−1 pin; floor 46 =
43+3). W1's "collected 10461" is outcomes (passed+skipped); xdist items are 10459
(module-skips are outcomes, not items) — reconciled, verdict-neutral.
Re-ran fresh at `dry/gate-run15/verify-1` via `heavy`, one flow at a time, GREEN: lint
13/13 (8 in-copy green — ruff×2, basedpyright×2, public-types, commas, truthful-reads,
citations — plus 5 git-bound checks green read-only in the shared tree; the copy has no
`.git`, so the chained run `dry-20261011T015851-7c574e` exits 2 at step 9 — environmental,
every step green); trio `dry-20261011T020232-b54b8b` 3 passed; prefetch
`dry-20261011T020306-8b4b2a` 44/2009d; perm `dry-20261011T020541-a74131` 6/76d; marked
`dry-20261011T020557-7683e1` 20 passed — all exit 0, counts exactly W1's, all digest
`5bbda356`. Full lint/default/floor/sharded suites taken from evidence, not re-run.
Drift: status 566 = gate end; tracked delta vs gate stash `2efd8b6b` is exactly W0's 2
plan-prose lines (submission receipt + this dispatch) — prose, non-invalidating per
DRY.md; pyproject/uv.lock blobs match; my session added zero worktree dirt.
Digest delta attribution: `git diff be24042f` (cells baseline) touches 32 package files,
set-matching the run-15 ledger union exactly (0 concurrent); non-package delta is 20
files, all ledgered (6e KANBAN×2, batch-6 conftest+3 tests+2 live, relay-pk test+2
specs, batch-7 3 specs+DRY.md, mop-up 3 tests) + plan prose + `db.sqlite3`
(suite-regenerated).
Defect sweep: 75/75 table rows carry run-15 outcome annotations, distribution
58/9/1/6/1 matches the homing line exactly; N1–N5 outcomes all recorded (N1 FIXED, N2
FIXED, N3 ALREADY-FIXED, N4 FIXED via mop-up F2, N5 FIXED via mop-up F4).
Ledger audit 3/3: batch-4 window exactly +29/-8 over its 3 files; batch-1 window +62/-51
= ledger +62/-49 + mop-up F4 N5 hunk (content-verified in `orders/inputs.py`); relay-pk
window exactly +140/-69 over its 5 files, N1 one-word + F1 hunks isolated by baseline.
Concurrent-work audit: sampled `types/base.py` (39 removed lines) + `utils/querysets.py`
(2 removed lines) — every run-15 removed line exists verbatim in HEAD, so no
hunt-added/modified line was touched; querysets hunks are the 3 ledgered prose hunks.
pg: `docker` absent from PATH (checked); pg line stands. Blocked-list completion (D-W2-1):
+ f40/f42 stays-blocked + f41 retired; E-e2/e3/e4/seal executed-stands per the run-13
record; f28 P1 moot per 5c. No runnable proof hidden — pre-landing green runs discharge
nothing — so the gap is record-only and completed here, not a revision.
`$TMPDIR` (164 entries; DELETE NOTHING — for Worker-0's 6g): 19 REFERENCED stay —
`aliasf65-manifest.json`, `ast-ident.py`, `attachlook-f61-manifest.json`,
`defects-mopup-failability.json`, `dry-defects-filters-orders/`,
`dry-defects-optimizer-middleware/`, `dry-folder-forms/`, `dry-folder-mgmtcmds/`,
`dry15-homing.py`, `f66-result-cache-manifest.json`, `fam3-failability.json`,
`folder-filters-failability.json`, `folder_types_p1.py`, `row49-oracle-probe.py`,
`row50-oracle-probe.py`, `row55-oracle-probe.py`, `row56-sim.py`,
`w2-f58-independent-trace-prefindings.md`, `w2-f66-manifest.json` — and 145
UNREFERENCED delete, roster at `$TMPDIR/w2-tmpdir-marks.txt` (incl. W1's
`gate15-pending-scan.txt`, `g15-skip-*.txt` and my `w2-*` scratch).
Verdict: verified. Gate GREEN stands on final run-15 bytes: 8/8 evidence runs exit 0,
every runnable proof re-proved fresh at matching counts/digests, zero invalidating
drift, all 75+N5 rows dispositioned, closeout audits pass.
