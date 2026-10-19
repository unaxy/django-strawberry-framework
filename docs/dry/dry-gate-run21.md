# Gate (run 21, redo) — dry 0.0.15

Run: `docs/dry/dry-0_0_15.md::Run 0.0.15 2026-10-11-21`
HEAD: `c37a08a0` (detached, unmoved) — 3 LANDED (A: walker.py + spec-035; B:
nested_planner.py + connection.py; C1: keyset.py + tests/test_keyset.py), 7 zero-edit.
Attempt: SECOND — first gate worker stalled (110 min, no artifact); results re-run in full.
Mode: shared-tree gate via `scripts/workspace.py gate dry`; TMPDIR=~/dry/tmp.
pg NOT runnable on the remote host — not attempted.

Plan: `lint,default,floor,sharded` in order, then 4 pending commands (A: 2x `proof:`;
#9: 2x `gate:`, prove expected to fail — consolidate address released at close).

## lint
Cmd: `heavy uv run python scripts/workspace.py gate dry --suites lint` — exit 0 PASS.
ruff format 506 ok; basedpyright 0/0/0; floor 0/0/0; verifytypes 100% (2 allowlisted);
trailing-commas 0; truthful-reads tier-1 0; citations 3347; tracked-paths ok;
kanban md/html, glossary, tree `--check` all up to date. Evidence:
`gate-dry-20261012T050106-30456b.json`.

## default
Cmd: `heavy uv run python scripts/workspace.py gate dry --suites default` — exit 0 PASS.
10565 passed, 43 skipped, 0 failed in 1105.04s. Coverage TOTAL 20100 stmts, 0 missed,
100.00% (fail_under met). Evidence: `gate-dry-20261012T051943-f3cee1.json`.

## floor
Cmd: `heavy uv run python scripts/workspace.py gate dry --suites floor` — exit 0 PASS.
10562 passed, 46 skipped, 0 failed in 1853.45s. Evidence:
`gate-dry-20261012T055047-b6c1b6.json`.

## sharded
Cmd: `heavy uv run python scripts/workspace.py gate dry --suites sharded` — exit 0 PASS.
10586 passed, 40 skipped, 0 failed in 1117.67s. Evidence:
`gate-dry-20261012T060936-c5d506.json`.

## Pending execution
A1 `proof:` 289-test selection — exit 0, 289 passed in 9.68s. RE-RUN PASS (discharges F1).
A2 `proof:` surface probe — exit 0, `post-edit surface: 7 gone, 7 keeps present`. RE-RUN PASS.
#9a `gate:` 26-node witness — exit 0, 26 passed in 0.50s. RE-RUN PASS (routes nowhere).
#9b `gate:` prove re-run — exit 0, 3/3 boundaries pinned (2/3/1 rows exactly
`expect_failing`, 0 errors, SHA-verified restores; run `dry-20261012T061056-4c30fb`,
slot-1 fresh sync). RE-RUN PASS — the expected released-address failure did NOT
materialize (`workspace.py` re-bound the address). Routes nowhere.

## Verdict
**PASS.** lint exit 0; default 10565 passed/43 skipped, coverage 100.00% (20100/20100,
fail_under met); floor 10562/46; sharded 10586/40. Pending: A1 289/289, A2 surface
7-gone-7-kept, #9a 26/26, #9b 3/3 pinned. Zero failures — no triage owed. pg not run
(not runnable on the remote host). No live-source edits made; artifact only.

## Gate completion (Worker-2)

Evidence checked, no suite re-run, no source touched. (1) All 4 `gate-dry-*.json`
exist under the dry evidence dir, each exit 0, head `c37a08a0` (live HEAD unmoved):
lint `30456b` (log re-read: ruff 506 formatted, both basedpyrights 0/0/0,
verifytypes 100% + 2 allowlisted, trailing-commas 0, truthful-reads tier-1 0,
citations 3347, kanban/glossary/tree up to date); default `f3cee1` (10565 passed,
43 skipped in 1105.04s, coverage TOTAL 20100/0/100.00%); floor `b6c1b6` (10562/46
in 1853.45s, pins py3.10/Django 5.2.16/strawberry 0.322.2); sharded `c5d506`
(10586/40 in 1117.67s, cell sharded). (2) Pending: #9b run `dry-20261012T061056-4c30fb`
exists in runs.jsonl + logs, exit 0, slot-1 fresh sync, 3/3 pinned (2/3/1 rows
exactly `expect_failing`, 0 collection/setup errors, SHA-256 restores); A1/A2/#9a
are shared-tree runs with no durable log — recorded outputs match item-time numbers
exactly (289 post-port, 7-gone-7-kept, 26). (3) Scope: all 10 run-21 artifacts
Status verified; Pending re-read in each — A 2x `proof:`, #9 2x `gate:`,
B/C1/F/G section absent, D/H1/H2/I None — all 4 commands re-run here, nothing owed.
(4) No live-source edits: all 6 run-21 ledger paths + spec-035 last modified pre-gate
(Oct-11 21:24-22:22 EDT vs gate window Oct-12 01:01-02:11); this artifact (02:11:26)
is the gate's only write; no new untracked source. Verdict concurred: **COMPLETE**,
PASS stands, pg non-run disclosed, zero failures, no triage owed.
