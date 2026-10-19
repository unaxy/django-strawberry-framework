# DRY review: `walker-planner-dead-aliases`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Target: planner alias block in [walker.py][walker]
(live `:90-107`; HEAD `:99-116` — the -9 is the
ledgered run-20 deletion + the concurrent `:17`
hunk above). Region diff vs `git show HEAD:` is
empty: touch lines HEAD-clean; spec-035 clean.
Two instruments over 506 `.py` (497 tracked + 9
untracked): word-exact `rg` (`\b`, longer-name-first
alternation defeats the `_relation_connection_to_attr`
prefix trap) and an AST visitor (503/503 parsed, 0
failures; Name/Attribute/import roles; 3 out-of-tree
files zero-hit). Code readers through walker, all
seven: zero. `_extend_only_projection`,
`_keyset_window_slice_from_arguments`,
`_relation_connection_to_attr`,
`_relation_connection_to_attr_for_key`: every live
importer binds from [nested_planner.py][nested-planner] directly
([connection.py][connection] `:84-87`, test_keyset `:72-74`);
the other three have no importer anywhere — def +
one internal call each. Positive control: the two
keeps (`_concrete_order_columns` test_walker `:2934`;
`_relay_max_results_from_info` `:3565`) read through
walker, found by BOTH instruments; all five
selections aliases keep body/test readers. No
star-from-walker, no `walker._X` code read, no
getattr/string/`__all__`/TYPE_CHECKING reader.
`_nested_planner` import stays (kept alias `:99`
binds through it). Specs: zero `walker.py::ALIAS`
cites; spec-035 `:75` + `:177` assert the walker
re-export in prose (rewritten here); all other
bare-name cites name the planner function, stay.

## Verification

### Matrix

1/2/4 inapplicable (import-time one-way bindings, no twin, no await).
3: walker aliases, never re-derives; deletion
removes bindings, zero logic. 5: 2 spec sentences
falsified, rewritten here; oracles literal. 6: full
block enumerated (2 kept, 7 dead).

### Challenges

- C1 (planner rename/removal): each dead binding
breaks walker at import — obligation, no
responsibility (principle-11 horn).
- C2 (signature change): count 0, confirming zero
logic. C3 (future reader via walker): deletion
closes the bless-a-dead-spelling trap. Control:
deleting `_concrete_order_columns` breaks `:2934`.

## Findings

### F1: seven dead planner aliases — deleted

- Contract: transparent private re-exports, no axes.
- Sites: walker `:100-106` dead definitions;
`:90-98` + spec-035 `:75` `:177` projections,
rewritten; [nested_planner.py][nested-planner] = owner,
untouched; direct imports/calls = oracles.
- Bar: principle-11 horn via C1-C3, no machinery.
- Owner/lifetime: [nested_planner.py][nested-planner] (kept relay
spelling: `utils/connections.py`); import-time
bindings, no stored derivation.
- Migration: 7 bindings deleted, comment restated
for the 2 keeps; nothing becomes a call. Index row
for Worker-0: `walker-planner-dead-aliases`, owner
nested_planner, files walker/nested_planner/
connection, `consolidated`.
- Shrinkage: -11 walker + 2 spec sentences; see
`## What shrinks`.
- Distinct: 2 + 5 kept aliases (readers each);
nested_planner to-attr delegates stay for item B.
- Proof: before-suite execution-verified (289
green); post-port suite + surface probe `proof:`
below. Census failability: keep-2 positive control
found by both instruments. No new tests: a
non-existence assertion is a barred census test
(run-20 precedent, W2-concurred); the temp import
probe pins absence instead.
- Negative control: none; bypass not the threat.
- Coupling: item B conditions on this landing
(post-port each delegate has exactly 1 reader);
ordered ports, B's census reruns post-port.
- Freshness: HEAD `c37a08a0`, baseline `73db965f`;
walker live `5577636a` / HEAD `ddb35b44`;
nested_planner `dc0c401c`; spec-035 `118b394e`;
tests `b1607a02` / `0bca5629` / `6f8e5c33`.

## Defects

None.

### Worker-2 errata (verdict-neutral; no code change)

- D-W2-1 (Worker-2): What shrinks claims `_connection_window_slice_from_arguments`
  "store + docstring prose gone" and `_project_scalar_only_window` "store + 2
  docstring mentions gone". Only the stores + covering-comment lines are gone;
  the docstrings survive at live walker `:1735` `:1742` `:1882` (baseline `:1746`
  `:1753` `:1893`, shifted by the -11 port). They are bare-name refs to live
  nested_planner defs, still true — no projection needs rewriting. Owner: this
  artifact (Worker-0 may fold into Outcomes or leave as scratch errata).
- D-W2-2 (Worker-2): What shrinks "Net package change ... +0/-11 lines" vs
  numstat `+5/-16` (5 restated comment lines added, 9 comment + 7 binding lines
  removed). Net -11 is correct and the parenthetical discloses the 9->5
  restatement; the `+0` add-count is shorthand, not numstat. Suggest "+5/-16,
  net -11". Owner: this artifact, same homing.

## Pending execution

- `proof: uv run pytest --no-cov -q -n0 tests/optimizer/test_walker.py tests/test_keyset_connection.py tests/test_relay_connection.py` — post-port rerun, 289 passed (199/23/67), discharges F1.
- `proof: uv run python -c "import django_strawberry_framework.optimizer.walker as w; dead=['_connection_window_slice_from_arguments','_extend_only_projection','_keyset_window_slice_from_arguments','_order_entry_field_name','_project_scalar_only_window','_relation_connection_to_attr','_relation_connection_to_attr_for_key']; kept=['_concrete_order_columns','_relay_max_results_from_info','_should_include','_is_fragment','_response_key','_response_keys','_included_field_selections']; assert not any(hasattr(w,n) for n in dead), 'alias survives'; assert all(hasattr(w,n) for n in kept), 'keep lost'; print('post-edit surface: 7 gone, 7 keeps present')"` — post-port surface, discharges F1.

## Judgment

Seven dead bindings, two instruments, positive
control, two spec sentences rewritten. Ready to port.

## Implementation (Worker-1)

Pool full (5/5 before-copies): no consolidate copy,
zero live-tree edits. Worker-0 ports these two diffs
exactly (ruff + gates rerun at port).

```diff
--- a/django_strawberry_framework/optimizer/walker.py
+++ b/django_strawberry_framework/optimizer/walker.py
@@ -90,18 +90,7 @@
-# Aliases for private names that predate the connection-planner extraction; the
-# implementations live in ``optimizer/nested_planner.py``. Only
-# ``_concrete_order_columns`` and ``_relay_max_results_from_info`` are read
-# through this module, both imported from ``optimizer.walker`` by
-# ``tests/optimizer/test_walker.py``. The other seven have NO reader here:
-# ``connection.py`` and ``tests/test_keyset_connection.py`` import
-# ``_extend_only_projection`` / ``_keyset_window_slice_from_arguments`` /
-# ``_relation_connection_to_attr`` / ``_relation_connection_to_attr_for_key``
-# from ``optimizer/nested_planner.py`` directly.
+# Two underscore aliases with live test readers (both imported from
+# ``optimizer.walker`` by ``tests/optimizer/test_walker.py``):
+# ``_concrete_order_columns`` is implemented in ``optimizer/nested_planner.py``;
+# ``_relay_max_results_from_info`` binds ``utils/connections.py``'s
+# ``relay_max_results_from_info``.
 _concrete_order_columns = _nested_planner._concrete_order_columns
-_connection_window_slice_from_arguments = _nested_planner._connection_window_slice_from_arguments
-_extend_only_projection = _nested_planner._extend_only_projection
-_keyset_window_slice_from_arguments = _nested_planner._keyset_window_slice_from_arguments
-_order_entry_field_name = _nested_planner._order_entry_field_name
-_project_scalar_only_window = _nested_planner._project_scalar_only_window
-_relation_connection_to_attr = _nested_planner._relation_connection_to_attr
-_relation_connection_to_attr_for_key = _nested_planner._relation_connection_to_attr_for_key
 _relay_max_results_from_info = relay_max_results_from_info
```

spec-035, two substring deletions (one sentence each):

- `:75`: delete `, which \`walker.py\` re-exports under a module-level alias` (before `) are the projection writers G2 gates`).
- `:177`: delete `(which keeps only a module-level alias to it)` (keeping `` `walker.py`, `` … `,` so the gate reads `does not live in \`walker.py\`, so the gate has to travel`).

## What shrinks

Net package change over ITEM_BASELINE: +0/-11 lines in
[walker.py][walker] (7 dead bindings, 9 comment lines
restated as 5). No machinery added: no new driver,
registry, flag, helper, wrapper, or constant; no test
added (a non-existence test would be a barred census
test); spec-035 loses two relative clauses (one
sentence each at `:75` and `:177`), nothing else in
the spec corpus moves. What the deletion removes: one
import-time change obligation per alias (a rename or
removal in [nested_planner.py][nested-planner] can no longer
break walker at import for helpers walker never calls),
plus the trap where a future reader imports a dead
spelling from walker and silently blesses it as API.
Reader counts before → after, word-exact over 506
`.py` (code reads through walker → 0 for all seven;
owner defs, internal calls, and direct-importer calls
unchanged): `_connection_window_slice_from_arguments`
store + docstring prose gone, def `:860` + internal
`:1056` stay; `_extend_only_projection` store +
comment mention gone, def `:760` + internal `:1427` +
[connection.py][connection] `:943` `:1001` + 7 test_keyset calls
stay; `_keyset_window_slice_from_arguments` store +
comment mention gone, def `:931` + internal `:1047` +
7 test_keyset calls stay; `_order_entry_field_name`
store gone, def `:172` + internal `:200` stay;
`_project_scalar_only_window` store + 2 docstring
mentions gone, def `:717` + internal `:1415` stay;
`_relation_connection_to_attr` store + comment mention
gone, delegate `:809` + [connection.py][connection] `:2305` stay;
`_relation_connection_to_attr_for_key` store + comment
mention gone, delegate `:814` + [connection.py][connection] `:2315`
stay. The keeps (`_concrete_order_columns`,
`_relay_max_results_from_info`, all five selections
aliases) hold their bindings with the readers evidenced
in F1, and the `_nested_planner` module import stays
for the kept planner alias. Post-port, item B's
precondition holds: each nested_planner to-attr
delegate has exactly one reader ([connection.py][connection]).
Behavioral equivalence: the 289-test touching selection
(walker 199, keyset 23, relay 67) is green pre-edit and
must rerun identical post-edit; the import probe asserts
the exact post-edit surface; both type gates and the
public-surface gate verify the reduced module at port;
the keep-2 positive control (both instruments found the
live walker-through readers) proves the zero is
measured, not assumed.

## Independent verification (Worker-2)

Verdict: verified. Both `proof:` entries re-run green (shared tree; pool
deviation disclosed below); entries stay for the gate, so the plan marker is
`verified, pending execution` (Worker-0's edit, not mine).

### Own trace (recorded before reading ## Findings)

Two instruments at ITEM_BASELINE `73db965f`, whole tree:

- A: per-alias `git grep -w -n` (`-w` defeats the `_relation_connection_to_attr`
  prefix trap, `_response_key`/`_response_keys`, `_order_entry_field_name`;
  trap pairs return disjoint hit sets). KANBAN.html excluded as generated board
  text (its one hit is prose consistent with the deletion); `db.sqlite3` is a
  binary fixture, not a reader.
- B: import/attribute vectors — every `from ...walker import` site (extension,
  bench x2, test_definition_order, test_field_meta x2, test_multi_db,
  test_walker header + 8 function-local), every `walker.`/`walker_mod.` code
  read (bench `plan_optimizations`; memo probes), plus star/getattr/quoted-
  name/`__all__`/vars/dir sweeps: all empty for the 7.

Census (readers through walker): the 7 dead have zero; `_concrete_order_columns`
(test_walker `:2934`+call) and `_relay_max_results_from_info` (`:3565`+3 asserts)
keep test readers; all 5 selections aliases keep body readers (`:749` `:806`
`:1681` `:1791` `:1802` `:1814` `:1840` `:1845` `:1875`) and/or test readers
(`:44` `:52`). Direct importers bind from nested_planner (connection `:84-87`,
test_keyset `:72-74`). Counts: 7 dead defs (zero-logic rebinds), 2+5 keeps,
2 spec projections. Owner: nested_planner (8 impls), utils/connections
(relay_max), selections (5 primitives); walker keeps 7 re-exports, deletes 7
(principle-11, no responsibility, no machinery).

### Reconciliation

Every difference vs ## Findings / What shrinks: (1) "docstring mentions gone"
is wrong on record — walker `:1746` `:1753` `:1893` survive at live `:1735`
`:1742` `:1882` (bare-name refs to live owner defs, still true; D-W2-1).
Substance unaffected. (2) `+0/-11` vs numstat `+5/-16`: net -11 correct,
add-count understated (D-W2-2). (3) "Region diff vs HEAD empty" holds for the
touch block only (`:90-107` == HEAD `:99-116`, byte-identical); the wider
region carries the ledgered run-20 deletion above. Verdict-neutral phrasing.
(4) All What-shrinks pins (`:860`/`:1056` etc.) are current in live — owner
and consumers untouched since baseline. (5) System trace ~30 lines vs ~25 cap:
over, verdict-neutral. (6) 506-file/AST figures not re-derived (different
instruments, time-varying untracked set); both my instruments agree with W1 on
every reader verdict. (7) `docs/shadow` pre-port copies are regenerable
snapshots, not readers.

### Matrix, counts, oracles

Axes 1/2/4 inapplicable accepted (private import-time bindings; no twin, await,
or round-trip); 3 concur (pure rebinds, C2 count 0); 5 concur (2 spec sentences
rewritten; keep-oracles assert literals, `:2936` `:3568-74`); 6 concur (full
block enumerated). 7 dead / 2+5 keeps / 2 projections confirmed; no oracle
rewritten (all 3 test blobs hold). C1 is the principle-11 horn, C3 closes the
bless-a-dead-spelling trap, and the `:2934` control is real.

### Proofs

`workspace.py run dry/walker-planner-dead-aliases/verify-1` refused: pool 6/6
bound (exit 125); I released nothing. Live tracked tree == baseline + port +
plan bookkeeping (3-file diff; owner/test blobs == W1 pins), so shared-tree
runs are faithful post-port proofs, authorized by DRY.md "Tests" (focused
`--no-cov` suite + read-only probes; nothing mutated): surface probe verbatim
-> `post-edit surface: 7 gone, 7 keeps present`; 289 selection verbatim ->
`289 passed in 10.31s`; my strengthened probe -> keeps `is`-identical to
owners, 7 owner defs callable.

### Port, freshness, coupling, gates

W1 hunk content == live item diff hunk-by-hunk (header `-18/+7` vs `-23/+12`
is context-window rendering only); spec `:75`/`:177` substrings match to the
character. HEAD `c37a08a0` unmoved; walker `5577636a`->`5508e486` and spec
`118b394e`->`5808ce6d` are exactly the port (no reopen); nested_planner
`dc0c401c` + test pins hold. No rejections (all-7 delete); Pending 2x `proof:`
correctly typed, kept for the gate. Coupling precondition HOLDS: each to-attr
delegate's only live reader is connection.py (import + 1 call); walker reads
deleted. Diff prose: no provenance, no new tests (absence assertion would be a
barred census test; keeps covered by existing tests) — rationale accepted.
`ruff format --check` + `ruff check` on both paths pass. Artifact: Run line ok,
10-group scaffold ok, W1 body exactly 150 lines pre-shrinks (scaffold read as
mandatory boilerplate outside the cap; my additions are the mandated record).
Trailing-commas exclusion confirmed in `EXCLUDE_SCRATCH_DIRS` and judged
correct (per-cycle scratch, permitted `:NN` cites). Record errata D-W2-1/D-W2-2
are filed under Defects above, verdict-neutral.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
