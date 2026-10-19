# DRY review: `cells`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Item baseline `be24042f`, address `dry/cells/run`, role `run` accepted (no `consolidate` fallback).
Enumerated fresh from all 240 `docs/dry/dry-*.md` `## Pending execution` sections: exactly 3
cell-gated sharded commands (U-qs-1, U-perm-1, U-ca-1 trio), matching the verified run-13 gate
record and the plan's "cells unverified" line; the superseded `dry-gate-rerun.md` draft was not
read for commands. Everything else is `inapplicable by construction` notes, blocked default-mode
proofs runnable only after their unblock landing, or pg prose with no command. Ran each via
`heavy workspace.py run dry/cells/run --cell sharded -- pytest ...` (cell sets
`FAKESHOP_SHARDED=1`; `-n0` added per machine rules), one at a time, machine GREEN, package
digest `2d87dc60` unchanged across all runs. Plus the brief-ordered run of the two
module-skipped sharded files. No source edits, so basedpyright/ruff are vacuous and were not run.

## Results

- U-ca-1 trio `test_multi_db.py::{rejection,inherit,routed-parent-follow}` (`dry-20261010T193001-af41c8`): exit 0, 3 passed, deferred proof now executed green.
- U-qs-1 `test_query -k prefetch` (`dry-20261010T193035-b88064`): exit 0, 44 passed / 2009 deselected, D1 cross-connection consequence now executed green.
- U-perm-1 `tests/test_permissions.py -k "multi_db or alias or pinned"` (`dry-20261010T193310-024e58`): exit 0, 6 passed / 76 deselected, F2 cross-connection consequence now executed green.
- Sharded-marked files `test_multi_db.py + test_generic_connection_sharded.py` (`dry-20261010T193327-c1de68`): exit 0, 20 passed, both module-skipped files execute green under sharded mode.
- pg cell (U-ca-1 "any PG cell" + per-artifact pg notes; no artifact names a pg pytest command): authorized, not runnable on the remote host (no docker); stays unverified.

## Defects

None. All four sharded runs exited 0; no new failure, no fix-batch join.

## Judgment

All 3 cell-gated sharded proofs plus the 2 sharded-marked files execute green (73 passed total,
0 failures); the D1-fix and alias-inheritance sharded consequences are verified for the first
time. pg stays unverified (authorized, unrunnable here). Nothing defers, nothing is item-back.

## Independent verification (Worker-2)

Own enumeration (heading-anchored extraction over all 241 `dry-*.md`, superseded
`dry-gate-rerun.md` excluded → 240 swept; 28 no-section incl. 5 plans + this artifact,
remainder inapplicable-by-construction notes, default-cell folder `gate:` witnesses for 6f,
blocked B-* `proof:` runs, or unverified-cell prose with no command): exactly 3 Pending
sections name a runnable sharded command — U-qs-1 (`dry-file-utils__querysets.md` entry 1,
`proof:`, `test_query -k prefetch`), U-perm-1 (`dry-file-permissions.md` entry 1,
`tests/test_permissions.py -k "multi_db or alias or pinned"`), U-ca-1
(`dry-rule-child-queryset-alias-inheritance.md`, `test_multi_db.py` trio + any PG cell).
Reconciles exactly with W1's 3, the verified run-13 gate record (`dry-gate.md` "3
cell-gated entries unverified"), and the plan's "Cells unverified" line; no miss, no
fourth command exists (e8/f63 sharded notes ride their blocked consolidations).
Zero-edit confirmed: tracked diff vs `be24042f` is plan prose only; sole new file is this
artifact; zero package/tests/examples bytes changed. Fresh verify-1 re-runs, one at a time
via `heavy`, machine GREEN: trio `dry-20261010T193833-10122d` exit 0 / 3 passed; U-qs-1
`dry-20261010T193907-8a0319` exit 0 / 44 passed + 2009 deselected — both match W1 exactly
(same digest `2d87dc60`, both DBs in-copy). U-perm-1 + marked-files spot-checked from W1
evidence (`runs.jsonl` cell=sharded, exit 0, correct commands; log tails 6+76d / 20;
provenance headers fresh-copy, shared unmoved) — no doubt, no re-run. `docker` absent
from PATH (checked, not trusted); pg line correctly applied per run-15 5a. No failure
misgraded: all exits 0 with log-confirmed counts summing to 73. Shape within 4C caps.
No (Worker-2) defects. Verdict: verified.
