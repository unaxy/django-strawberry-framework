# DRY review: gate-rerun

Status: investigating
Run: 0.0.15 2026-10-10-14

## System trace

Gate Worker-1 (queue item `gate` re-run, run 14) for DRY cycle 0.0.15.
Worktree `~/projects/worktrees/django-strawberry-framework/dry-0015`,
HEAD `23b5f42106ffd14805936560f5155dd90d7568da` unmoved at dispatch and gate time.
`ITEM_BASELINE=a7269b21f9c63c66fad699bbccc0d15d534d6ee3` (slot-1 `dry/gate/before`
ready, matches dispatch). Own copy `dry/gate/consolidate` on slot-2, synced via
`workspace.py run` through `heavy` (run `dry-20261010T155313-3173d6`, copy fresh,
shared unmoved since sync, package digest
`sha256:2d87dc608b6baf58101e5d19f608dd673a28e3243dcaabe0a33a653557dbc50b` —
identical to the run-13 gate: package untouched since).
Gate = `workspace.py gate dry --suites lint,default,floor` in the gate copy plus
every `## Pending execution` command from every artifact, run as listed. No maintainer
authorization for sharded/pg exists (plan carries it as owed); no `--cell` run was
made and every cell-gated entry reads unverified. No source edit was made or is
owed by this item. Run-13 `docs/dry/dry-gate.md` preserved as evidence; every entry
below was re-enumerated and re-verified first-hand, nothing inherited.
Shell outage: after the gate suites completed green, this session's shell driver
began failing every `muse.bash` call with
`CallerInvalid("nested spawn session/run is not durably attested to its caller
Agent")` (first failure on reading the gate output; subagent spawn likewise
rejected with `lineage_integrity_failed`). Suite-log verification below was
re-derived through the file-search tool instead; pending executions need the
shell and are dispositioned under `## Pending results`.

## Results

- lint `dry-20261010T155440-84eae9` exit 0 196s: GREEN 13/13 (ruff check; format
  505 files; both basedpyright 0/0/0; public-types 100% + 2 allowlisted;
  trailing-commas 0; truthful-reads tier-1 0; citations 3316; 5 generators up
  to date).
- default `dry-20261010T155756-47f908` exit 0 1065s: 10413 passed, 43 skipped, 0
  failed; collected 10454; 0 ERROR/XPASS/XFAIL/INTERNALERROR; coverage TOTAL
  19994/0/100.00% (`fail_under=100` reached; `filters/base.py` 397/0/100%).
- floor `dry-20261010T161541-44b7af` exit 0 1759s (Python 3.10.22, Django
  5.2.16): 10410 passed, 46 skipped, 0 failed; collected 10454; 0
  ERROR/XPASS/XFAIL/INTERNALERROR; no coverage gate on this cell.
- Skip reconciliation: default 41 SKIPPED lines + 2 module-level collection
  skips (`test_multi_db.py`, `test_generic_connection_sharded.py`, 0 hits each
  in the log) = 43; floor = default's 41 + exactly 3 version-gated rows (2
  postgres-converter, 1 MTI prefetch) + the same 2 module skips = 46.
- Collected 10482 -> 10454 (-28): -31 cleanup removals (T1 11 + T2 9 + T3 net 11)
  +1 D2 test = -30 known; +2 residual concurrent additions (nodes unidentified:
  shell outage blocked the collection diff; re-derive on re-gate).
- D1 fixed: range test PASSED both suites (default :10784, floor :10717) on input
  `{"window": {"exact": [1, 5]}}`. D2 fixed: new malformed-GlobalID test PASSED both
  suites (:8311/:8167); `filters/base.py:941` covered (0 misses file-wide).

## Binding

- `ITEM_BASELINE=a7269b21f9c63c66fad699bbccc0d15d534d6ee3` (dispatch; slot-1).
- Gate-time stash: `cefa78ea8481142f42fbb979968cfe05af40a9f9` (from the result
  file; completion stash uncut: shell outage blocks `git stash create`).
- Blobs: `pyproject.toml` `21cccc6d0caceb0cc91ff9ccafaa470a936c3ade`, `uv.lock`
  `8fb5f01c99f332731ad121be4b01b9b4c3a4443e` (identical to run-13 gate).
- Tree digest `sha256:263794fbd70b9a9afeb98cffdda238405f531e23c4b530430b9685c481583972`
  (moved vs run-13 `44b4e557…`: test-only drift — gate-fixes + T1/T2/T3 + hunt;
  package digest `sha256:2d87dc60…c50b` unmoved).
- Result file `dry/evidence/gate-dry-20261010T164501-1dc02f.json`; cells default
  throughout; floor pins Django 5.2.16 / python 3.10 / strawberry-graphql
  0.322.2 (key `c4fed73b…`, `reused: true`).

## Pending census

- 214 exact sections across 234 artifacts (239 `dry-*.md` - 5 plans - this draft):
  210x1 + 2x2 + 22x0, machine-counted. Delta vs run-13's 211: +3 (`dry-gate.md` now
  counted + `dry-gate-fixes.md` + `dry-blocked-triage.md`; all no-owed, read in full).
- Two-section files: `dry-file-consumers.md`, `dry-rule-relation-kind-taxonomy.md`
  (all four `None`). Zero-section files: the same 22 as run-13, re-swept (every hit a
  none-owed statement, field label, or already-ran-green replay; witness contexts read).
  Near-miss `dry-file-_boundary_ordering.md:1698` read, not counted. Every section read
  first-hand; sections not named below owe no command.

## Pending results

- EXECUTED: `basedpyright` exit 0, 0/0/0 (`dry-20261010T155313-3173d6`, the slot-2
  sync run) — discharges G-auth-1/G-ext-1/G-fil-1/G-for-1/G-mcmd-1 (every entry
  naming it).
- BLOCKED-ON-ENVIRONMENT (E1; exact re-dispatch list, all in slot-2 via
  `workspace.py run dry/gate/consolidate -- <inner>` through `heavy`, one at a
  time): statics `basedpyright -p pyrightconfig.floor.json` and
  `python scripts/check_truthful_reads.py --check` (each discharges all entries
  naming it); `python scripts/build_tree_md.py --check` in the SHARED tree (slot-2
  has no `.git`, verified by `ls`; G-mgmt-2/G-mw-4). Pytest witnesses: auth
  `tests/auth/test_{queries,mutations,sessions}.py`; ext
  `tests/extensions/test_{debug,operation_state}.py` +
  `tests/test_{error,resource}_policy.py`; fil `tests/filters/test_sets.py`; forms
  `tests/forms/test_{converter,inputs,resolvers,sets}.py`; mgmt
  `tests/management/test_imports.py`; mcmd imports + export_schema + inspect file +
  `examples/fakeshop/tests/test_inspect_django_type.py::test_inspect_connection_only_relation_shape_renders_row`
  (node present); mw toolbar + views + live toolbar-api; mut inputs + sets + fields +
  resolvers+permissions + live products-api; opt `tests/optimizer`; ord `tests/orders`;
  rf `tests/rest_framework`; tst `tests/testing tests/test_multipart.py`; typ
  `tests/types` + inspect-variant; qs-2 `tests/utils/test_querysets.py
  tests/test_list_field.py tests/optimizer/test_extension.py`; gid-1 hostile-repr node
  (0 refs in tests/examples: expect exit 4); f38 3-node selection (all nodes present).
  Prove: G-fil `workspace.py prove dry/gate/consolidate
  ~/dry/tmp/folder-filters-failability.json` (manifest on disk). Probes: P1
  `python ~/dry/tmp/folder_types_p1.py <slot-2 root>` (script on disk); P3
  `probe_safe_name_coverage.py` staged byte-identically into slot-2 (D3 ruling applies).
  N-opt/N-ord/N-rf/N-tst/N-typ: green in the bound default log (global 0 FAILED).
- RETIRED BY MAINTAINER TEST CLEANUP: P-f28 (manifest entry-1 scope/expect node
  `test_window_to_attr_grammar_has_exactly_one_producer` T3-removed, 0 refs in tests/;
  entry-2 nodes live, anchor live — the command retires as listed per the brief).
- RETIRED BY 5c BELOW-BAR (plan Families rows verbatim "retired, not run at the
  gate"): B-f36, B-f37, B-f41, P-f46, P-f64, B-f60, B-f63 — not run.
- NOT-RUN, CELL-GATED (no maintainer word; plan carries it as owed; pool 311/311 runs
  `cell=default`; brief authorizes default only): U-qs-1, U-perm-1, U-ca-1 — unverified.
- NOT-RUN, BLOCKS PERSIST (rows re-read at current bytes: open/blocked-on-hunt, zero
  edits, verified-pending-execution): B-f42, B-f40, B-e9, B-e8, B-f38-2 (the
  landing-forbidden `<manifest>` line: its record forbids running before the landing
  pass authors the manifest).
- NOT-RUN, ALREADY-EXECUTED (all 6 run ids verbatim in their artifacts; probe scripts
  lived on another machine's `/tmp` or removed workspaces, absent here): E-e2/e3/e4/e5/e6/e7,
  E-seal — records stand.
- NOT-RUN, UNRUNNABLE (`probe_defect_arms.py` + the r2 successor both absent; the w2 dir
  holds only the three `w2_*` files): G-qs-3 — the revision-1 measurement stands.

## Defects

- D1/D2 (run-13): GONE, visibly. D1's test passes in both suites on the retargeted
  input; `filters/base.py:941` is covered with 0 misses file-wide and TOTAL 100.00%.
  Nothing item-back (0 failures); no new homing owed beyond run-13's record.
- D3 (run-13 P3 probe): OPEN pending the blocked P3 re-run — whether `(742, 'built')`
  still hits at current bytes is unmeasured. Rides to the re-dispatch; reopens no item
  (witness-class per the settle ruling).
- E1 (environment): this session's shell driver fails every call (`CallerInvalid: not
  durably attested`; spawn `lineage_integrity_failed`), blocking 39 executions. Routes
  to Worker-0/the maintainer: re-dispatch from a shell-healthy session; row blocked on E1, suites green.

## Pending execution

The 39 blocked commands under `## Pending results` (2 statics + shared-tree build_tree
+ 33 pytest + 1 prove + 2 probes; basedpyright already executed). The gate item itself
lands no edit and owes nothing else.

## Judgment

Suites GREEN on all three cells, coverage 100.00%: D1/D2 visibly fixed, nothing
item-back, every retirement and not-run reason re-verified first-hand. The gate RESULT
is BLOCKED on environment failure E1 (shell attestation outage): 39 pending executions
enumerated exactly but unrun; basedpyright executed green. Worker-0: re-dispatch the
blocked list from a shell-healthy session, then Worker-2 completes the row per DRY.md.
