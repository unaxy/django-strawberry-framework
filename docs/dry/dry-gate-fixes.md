# DRY review: gate-fixes

Status: verified
Run: 0.0.15 2026-10-10-14

## System trace

Worker-1 for run 14, item gate-fixes: maintainer-authorized test-only gate
repair for the dry-gate defects D1 + D2. Zero package edits. Edit rights cover
exactly the two gate-fix tests, in the workspace copy only, at address
dry/gate-fixes/consolidate (slot-2). The live tree was read freely; its .py
files are untouched for Worker-0 to port.

## D1 fix

Retargeted, not weakened. A declared package RangeFilter carries lookup_expr
exact, so the lookup table groups the window head under the single exact slot;
the old input names a range lookup the head has no entry for, and the per-lookup
raise in sets.py `_leaf_form_entries` fires before normalization. The new input
takes the operator-bag branch to the head's real slot, so the normalizer
dispatches the RangeFilter to the range arm with the list value, which rejects
it. The assertion is unchanged. The arm is proven reached: the contiguous
string range input is raised only by inputs.py `_normalize_range_value` (its
unknown-axes and non-range-value arms), and a list takes the latter.

## D2 test

One plain behavioral test in the existing tests/filters/test_base.py (no new
file, no tracked-path-constants regen):
`test_filter_non_string_global_id_value_rejected_as_malformed` passes 42 to
`_decode_and_validate_global_id` and asserts the caller-observed GraphQLError
matching not a valid GlobalID with extensions code GLOBALID_INVALID. No
hostile-repr machinery. Tier is tests/ by construction: the wire types every
GlobalID filter input as String and the filter's form field is CharField, so a
non-string value is reachable only from a direct-Python caller.

## Freshness

HEAD 23b5f42106ffd14805936560f5155dd90d7568da, unmoved since dispatch.
ITEM_BASELINE 28cb9b32af4e1189229296b19f4a15b4ec438c81. Copy bytes vs HEAD
for every input read (copy = slot-2, live = live tree at proof time):

tests/filters/test_inputs.py copy 9e69f40e1e3a114ea1d565e6ef13c422c9767583
tests/filters/test_inputs.py live 9fcf8145e918ea6895a6dd3c0bb5de0c1b93d9e2
tests/filters/test_inputs.py HEAD 873b854bdced822e7df57373b4e449c4910bac31
tests/filters/test_base.py copy dd2adbea88e627708dc4c4559281ef506eb29c88
tests/filters/test_base.py live c702a0cfe377010ac29e43515350a2c443c77dfa
tests/filters/test_base.py HEAD 221362f80432eaabb2e0ed950d1e36908424f7ad
filters/base.py live 77c2e7a64a4f580537ed96b0f2538d59b064cf2d
filters/base.py HEAD a43513a72c11767cf05a45ee9d2bd9457fdbe06e
filters/inputs.py live a269a3fe4c22814f0fedc2eaea89ba1924820107
filters/inputs.py HEAD d77a113ce96ded69d7dd9ec7e25c4de4050b6d8b
filters/sets.py live d6bb78d1024c2ef8061dce8a5a0e83321cc7e900
filters/sets.py HEAD b87401870638da52208bc3e047cceb7b62f9bea3

## Implementation (Worker-1)

Copy root ~/dry/ws/c3af387fc1324a21/dry/slots/slot-2. Exactly two
files differ from the live tree: tests/filters/test_inputs.py (line 946, one
token: range to exact) and tests/filters/test_base.py (fourteen added lines:
the D2 test after test_filter_wrong_model_rejected). Net copy-vs-live: two
files, fifteen insertions, one deletion. Every other path read is
byte-identical between copy and live.

Attribution: every hunk in both files was diffed vs git show HEAD and matches
known concurrent work (hostile-guard cleanup, the D2 deletion, the D1 test's
own landing); no unattributed hunk; nothing else touched.

Proofs, all in the copy through heavy, sequential, machine GREEN throughout.
D1 pre-fix repro red as routed (dry-20261010T151834-801fb8); post-fix single
green (dry-20261010T151941-debd66); both focused files 241 passed
(dry-20261010T152152-7c70a2). Coverage file run 136 passed with 941 absent
from the missing list (dry-20261010T152215-aecedc); D2 single-test run 1
passed with 941 covered by that test alone (dry-20261010T152247-3667c3).
Failability prove pinned: mutant DID NOT RAISE, baseline passed, restore
byte-identical (dry-20261010T152804-701d3b; one earlier attempt exited 1 on a
mutation that fell through to from_id, then corrected). Static: ruff check
clean (dry-20261010T152034-67f745), ruff format no-op
(dry-20261010T152037-fab1e3), basedpyright 0/0/0
(dry-20261010T152345-a58904), floor 0/0/0 (dry-20261010T152520-dfdc7d),
truthful-reads tier-1 0 (dry-20261010T152658-83485a).

## Pending execution

None expected: every proof ran now, in the copy, as listed above.

## Judgment

Both halves fixed, test-only, zero package bytes changed. D1's retarget reaches
the range arm it was written against; D2's behavioral test covers base.py:941
alone and fails exactly the divergence it guards. Ready for Worker-0 port and
Worker-2 verification.

## Independent verification (Worker-2)

Pass 1 at `dry/gate-fixes/verify-1` (slot-3, synced after the port).

D1 own trace. Declared `window = RangeFilter` carries `lookup_expr`
"exact" (django default; the package subclass sets none), so the
grouping rule (`inputs.py::filter_lookup_table` declared branch) puts
head "window" under a single "exact" slot. `{"exact": [1, 5]}` has
every key in `_LOOKUP_PYTHON_ATTRS`, so it takes the operator-bag
branch; `_leaf_form_entries` finds the real slot and
`normalize_input_value` dispatches the RangeFilter to the `_range`
arm with the list. A list is not a dict and has no `start`/`end`
attrs, so `_normalize_range_value` raises `ConfigurationError`
("consumes a range input with ...") from its non-range-value arm.
"range input" raise text exists only in that function's two arms; a
list can take only the latter, and the sets.py miss-raise lacks the
text. The unchanged assertion is satisfiable exactly there: reach
site `filters/inputs.py::_normalize_range_value`, non-range-value
arm. Reach: yes.

D2 own trace. `_decode_and_validate_global_id(42, f)`: 42 is neither
`GlobalID` nor `str`, so line 941 raises `ValueError`, caught and
re-raised as `GraphQLError` ("not a valid GlobalID",
`GLOBALID_INVALID`) — exactly the caller-observed error the test
asserts (message regex plus extensions code). Plain behavioral: no
source reads, no census, no name pins. Tier `tests/`: the wire
annotation is `str` and the form field is `CharField`, so non-str
is direct-Python-only — the strongest reachable tier, same as the
neighboring direct-call tests. No census-gate machinery.

Reconciliation: W1's D1/D2 sections agree on every load-bearing
claim (exact-slot grouping, operator-bag branch, range arm,
list-to-non-range-value-arm, behavioral D2 at `tests/` tier).
Verdict-neutral context: HEAD's `_normalize_range_value` has no
fail-loud arm (a list yields a silent `{}`), so the retarget passes
only with the concurrent production arm — consistent with a
test-only item against the current tree. No verdict-affecting
difference.

Proofs, all re-run through `heavy` in slot-3: focused files 241
passed (`dry-20261010T153855-084817`); D2 alone 1 passed with 941
absent from the missing list (`dry-20261010T153915-f317ba`, row
re-captured `dry-20261010T153926-c110b7`); failability with my own
mutant (guard becomes `return value`): baseline 1 passed, mutant
fails exactly D2, verdict pinned, restore blob-identical
(`dry-20261010T154023-b0cda0`); ruff format check plus ruff check
clean on both paths; basedpyright 0/0/0 both passes
(`dry-20261010T154042-f25fb7`, `dry-20261010T154153-057a27`);
truthful-reads tier-1 0 (`dry-20261010T154306-1804bd`). Item diff
vs baseline is exactly the two test hunks; package plus examples
diff empty; every other vs-HEAD hunk predates the baseline
(concurrent); added lines carry no banned word or provenance.
Fingerprints: copy equals live on both files (`9e69f40e`,
`dd2adbea` — W1's copy hashes, port verified); HEAD pins match the
artifact (`873b854b`, `221362f8`).

Verdict: verified. Test-only; no pending execution remains.
