# DRY review: `gate-run16`

Status: verified-green
Run: 0.0.15 2026-10-11-16

Rebuilt post-closeout from retained evidence (gate JSON + 4 suite logs +
4 pending run logs + recorded pass-1 verification, all verbatim) after a
late write by the cancelled first worker replaced these bytes on disk.

Freshness: HEAD c37a08a0 (detached, unmoved); status 570 at start (+4 vs
run-16 dispatch = this run's 4 artifacts, untracked); tracked delta vs gate
stash `d3d6c1e0` exactly the 1-line WEDGE plan receipt (prose,
non-invalidating per DRY.md); mine `a07656d5`; pyproject 21cccc6d, uv.lock
8fb5f01c; package digest sha256:6425d797 live = gate evidence on all 8 runs;
gate bound 1b6d85, result gate-dry-20261011T075155-1b6d85.json.

## System trace

Adopted the wedged worker's 4 suites (evidence re-read first-hand end to
end, no re-run), then ran the 4 pending proofs fresh via `heavy
workspace.py run dry/gate-run16/consolidate --cell sharded`, one at a time,
machine GREEN throughout. Fresh pending sweep: 255 artifacts (219 carry
`## Pending execution`; superseded `dry-gate-rerun.md` excluded); exactly 3
name a runnable sharded command (U-ca-1 trio, U-qs-1, U-perm-1) — reconciles
with the verified cells item; 4th run is the cells-parity marked-files set.
Run-16 artifacts list none (f66/relay `None`, drymd absent=empty, spec039 no
section — all read). Rest = inapplicable notes, blocked B-* proofs riding
unlanded consolidations, default-cell witnesses (strict subsets of the
adopted default suite, discharged by it), executed-evidence records, or pg
prose with no command.

## Results

- lint (dry-20261011T064127-f34498): exit 0, 13/13 steps green, adopted.
- default (dry-20261011T064442-07d205): exit 0, 10562 passed, 43 skipped,
  10603 collected, coverage 100.00% (TOTAL 20125/0), adopted.
- floor (dry-20261011T070311-65ee2c): exit 0, 10559 passed, 46 skipped,
  pins py3.10.22 / Django 5.2.16 / strawberry 0.322.2 (venv-read), adopted.
- sharded (dry-20261011T073355-3c8bfc): exit 0, 10583 passed, 40 skipped,
  10623 collected, adopted.
- Log bodies: 0 FAILED / 0 ERROR / 0 XFAIL / 0 XPASS in all three; PASSED
  line counts equal the summaries; skips reconcile (default 41+2 module,
  floor 44+2 module, sharded 40 = default −3; floor = default +3).
- U-ca-1 trio (dry-20261011T081028-77fbe2): exit 0, 3 passed, fresh copy.
- U-qs-1 prefetch (dry-20261011T081101-7c235d): exit 0, 47 passed / 2046
  deselected (run-15: 44/2009d; +3/+37 = suite growth, corroborated: 47
  PASSED prefetch rows in the adopted sharded log).
- U-perm-1 (dry-20261011T081356-3d7efb): exit 0, 6 passed / 76 deselected.
- Marked files (dry-20261011T081413-b65db8): exit 0, 20 passed.
- Pending total 76 passed, 0 failures; all 4 digests 6425d797 = gate
  suites; shared_moves empty, copy_edits empty on all 4.

## Defects

None. Zero failures across 4 adopted suites + 4 fresh pending proofs; no
item-back, no new rows. Failure routing untriggered (no path failure, no
`proof:` failure, nothing to reproduce against `git show HEAD:`).
- D-W2-1 (Worker-2, record-only, verdict-neutral): executed-stands
  parenthetical omits e4 + seal (named in run-15 D-W2-1 per run-13);
  G-gid-1 node still absent (standing run-13 exit-4-per-D2); G-ms-1
  probe stands DECIDED (refresh homed to 053). Completed here.

## Pending execution

- pg cell (U-ca-1 "any PG cell" + per-artifact pg notes; no artifact names a
  pg pytest command): authorized, not runnable on the remote host (no docker;
  `command -v docker` empty, checked not trusted).
- Blocked B-* proofs (f36/f37/f38/f40/f42/f46/f60/f63/f64/e8/e9; f41
  retired; e2/e3/e5/e6/e7 executed-stands): still ride unlanded
  consolidations or land-owed manifests; unrunnable until unblock lands,
  listed not run. Reconciles with the run-15 record + D-W2-1 completion.
- Unrunnable-as-listed (record-only): querysets item-3
  `probe_defect_arms.py` — exact path absent from temp-tests (adjud2/adjud3
  variants exist, the listed file does not); nothing else references it.

## Judgment

GREEN: lint + default (100.00%) + floor + sharded all exit 0 on final
run-16 bytes by verified adoption (zero binding mismatch), every surviving
proof executed fresh (76/76 pending green), pg stays the sole
authorized-unrunnable cell. Gate record: 8/8 runs green, zero drift, verdict
ready for Worker-2.

## Independent verification (Worker-2)

Own re-derivation, W1's counts never trusted. Bound inputs: HEAD
`c37a08a0` unmoved; tracked delta vs `d3d6c1e0` exactly plan prose
(+3/-1 WEDGE + submission + dispatch); pyproject/uv.lock full-hash
match; live package digest `sha256:6425d797...` full match. Suites:
lint 13/13 read whole, exit 0; default 10562/43/10603 + 100.00%
(20125/0, 121 files at 100%, zero non-100); floor 10559/46, pins
venv-read 3.10.22 / 5.2.16 / 0.322.2; sharded 10583/40/10623; zero
FAILED/ERROR/XFAIL/XPASS, PASSED lines equal summaries; skips
default 41+2 module (both gates in source), floor +3 (2 converters
PG + 1 resolvers MTI), sharded minus 2 module minus 1 perm pin.
Pending: 255 files / 219 occurrences reproduced (3 doubles + 1
variant header declaring empty); runnable = exactly the 3 sharded
artifacts + brief-ordered marked set; 4 fresh runs confirmed
(3 / 47+2046d / 6+76d / 20 = 76), digests match, selections match
listings; U-qs-1 corroborated by my own 47-row count in the
sharded log. Every default witness verified collected+green in
the default log; type gates green in lint; blocked entries each
carry once-clears/do-not-run language and blocks persist
(`truth.py`/`lazy.py` untracked, no run-16 unblock); f41 retired,
f28 moot per 5c; probe path absent, adjud2/adjud3 exist; pg
names no command, `docker` absent (checked, exit 127). Spot:
trio re-run `dry-20261011T082645-bb6aad` exit 0 / 3 passed,
digest match — agrees. Routing untriggered; no item owed a
return. Verdict: verified-green.
