# DRY review: `defects-optimizer-middleware`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Batch: 11 defect rows (table rows 30 + 36 + 38 + 39 + 47 + 53 + 66 +
68 + 69 + 70 + 71) across 6 package files
(`optimizer/{hints,walker,plans,nested_planner,nested_fetch}.py`,
`middleware/request_body.py`; `_boundary_ordering.py` read-only for the
mark count). Read all 11 source `## Defects`/`O1` entries in full first;
the verified entries govern, not the table summaries. Re-checked each
against current bytes: 6 FIX (5 prose + 1 wording-only message), 3
ALREADY-FIXED (spent by committed evolution), 2 BLOCKED-ON-HUNT.
Developed in `dry/defects-optimizer-middleware/consolidate` (slot-2,
fresh, shared unmoved), proved there, ported byte-identical (4/4
`cmp` clean). Gates green both trees: ruff check + format clean (4
paths), both basedpyright 0/0/0, truthful-reads tier-1 0. No test
edits (row 68 has zero residue; row 53 pins no oracle); no REROUTE.

## Verification

### Matrix

1. Cross-flavor: no twin rule across surfaces; each fix is file-local prose or one call site.
2. Sync/async: walker has zero `async def`; row 53 recourse names the sync-only walk.
3. Derived knowledge: row 38/39/47 censuses removed or corrected to the live derivation.
4. Round-trip: none; no encode/decode pair in the batch surface.
5. Other media: specs cite no stale sentence touched here; oracles pin none of the old wordings.
6. Omission: row 68 sweep finds zero shim residue package-wide; row 53 has no second call site.

### Freshness

`ITEM_BASELINE=2c9b476c`, `HEAD=23b5f421` unmoved; post-edit blobs:
`request_body.py cb663863`, `plans.py 7009047b`, `hints.py fdfff2e9`,
`walker.py 80c2b9fc`; `nested_planner.py` + `nested_fetch.py` untouched
(clean-line reads only). Pre-edit `HEAD:` + diffs at
`$TMPDIR/dry-defects-optimizer-middleware/pre-edit/`. Slot-2 runs:
`dry-20261010T223731-093516` (pyright), `dry-20261010T223842-c06037`
(floor), `dry-20261010T223957-014cdc` (truthful-reads).

## Findings

| # | verdict | change |
|---|---|---|
| 30 | FIXED | `request_body.py:46` "two marks" → "the marks" (count-free). |
| 36 | FIXED | `plans.py::deferred_loading_of` census parenthetical removed. |
| 38 | FIXED | `hints.py::hint_is_skip` walker-half comment corrected to `hints_map.get`. |
| 39 | FIXED | `walker.py::_absorb_child_plan` "no separate line" claim removed. |
| 47 | FIXED | `plans.py::order_entry_name_and_direction` 3-consumer census removed. |
| 53 | FIXED | walker passes `_WALKER_ASYNC_RECOURSE` (wording-only, no test). |
| 66 | ALREADY-FIXED | annotation already `ConnectionWindowBounds` at current bytes. |
| 68 | ALREADY-FIXED | both shims deleted by `899cb35b`; zero hits, no orphans. |
| 69 | BLOCKED-ON-HUNT | `_require_prefetch` hunk `@@ -71,11 +72,13 @@` (truth rewrite). |
| 70 | BLOCKED-ON-HUNT | `resolve_strategy` hunks `@@ -448,30 +450,26 @@` + `@@ -481,24 +479,17 @@`. |
| 71 | ALREADY-FIXED | M2M silence arm + test landed at HEAD. |

36: entry suggests naming the fourth consumer; the count is not a contract,
so the parenthetical is removed per the worker rule (single-reader claim kept).
47: same — "three" is not a contract; the "cannot disagree" rule sentence kept.
53: raise still fires fail-closed; only guidance changes. No oracle pins the old
Relay wording for the walker path (zero hits), so wording-only, no test owed.
66: run-8 s10 already closed D2; current `:934` reads
`tuple[ConnectionWindowBounds, KeysetSeek | None] | None`.
68: `rg` finds zero `_connector_only_field(`/`window_partition_for_prefetch(`
package-wide; only the distinct `_ensure_connector_only_fields` writer survives.
69: HEAD has unguarded `isinstance(obj, Prefetch)`; worktree rewrites it to
`truth.is_instance` — the defect lines sit inside the hunt hunk, no clean fix.
70: HEAD has both unguarded gates; worktree rewrites both to truth helpers —
same, no clean-line fix.
71: HEAD `:631-636` + `:672-673` carry the through-table silence + docstring;
`TestAdvisoryReadsThePartitionColumn` pins it. Fixed-concurrent, landed.

## Defects

None new. All 11 rows dispositioned above; no second defect found while tracing.

- D-W2-1 (Worker-2; minor, prose): prefetch R2 trigger clause unlanded at
  its specified home (wrapper docstring / `merge_metadata_from`), landable
  now row 39 fixed D1. Owner: `optimizer/walker.py::_absorb_child_plan`.

## Judgment

Six rows fixed at the root on clean lines (5 prose, 1 message), three spent
by committed evolution with evidence, two genuinely hunt-blocked with exact
hunks for Worker-0 to home on 053. Four files, all gates green, zero
concurrent overlap. Ready for independent verification.

## Implementation (Worker-1)

Tracked edits vs `ITEM_BASELINE=2c9b476c` (4 files, +17/-14; 7 hunks,
exactly the 6 fixes; ported byte-identical from slot-2, `cmp` 4/4):

- `django_strawberry_framework/middleware/request_body.py` — row 30: `:46`
  "two marks" → "the marks".
- `django_strawberry_framework/optimizer/plans.py` — rows 36 + 47: two
  docstring censuses removed (`deferred_loading_of`, `order_entry_name_and_direction`).
- `django_strawberry_framework/optimizer/hints.py` — row 38: `hint_is_skip`
  comment walker-half corrected.
- `django_strawberry_framework/optimizer/walker.py` — rows 39 + 53:
  `_absorb_child_plan` docstring corrected; new `_WALKER_ASYNC_RECOURSE` +
  one `async_recourse=` argument at the visibility call.

## Independent verification (Worker-2)

Own verdicts re-derived from each source entry + current bytes with fresh
searches (artifact file first opened whole; reconciliation below is
explicit): 30 FIXED, 36 FIXED, 38 FIXED, 39 FIXED, 47 FIXED, 53 FIXED, 66
ALREADY-FIXED, 68 ALREADY-FIXED, 69 BLOCKED-ON-HUNT, 70 BLOCKED-ON-HUNT, 71
ALREADY-FIXED. 11/11 concur with W1's table; evidence per row follows.

30: four marks + METHOD-not-a-mark verified; "the marks" count-free, "two
marks" zero hits. 36: 4 `deferred_loading_of` callers, one attribute read
(plans.py:633); census deletion leaves a true sentence; "spec-041" 0 hits
(table summary phantom, fix follows the D1 entry). 38: walker
`hints_map.get` (:957/:973), audit `hints.get(field_name)`
(extension.py:1519); comment true; W2-corrected scope honored. 39:
planner's separate merge survives (nested_planner.py:1540); false claim
gone, remainder true. 47: 5 call sites compose by name; rule sentence kept
and true; "logger" 0 hits (table summary phantom, fix follows D-1). 53:
callee takes `async_recourse` (querysets.py:4550) as guidance-only
(`recourse=`, :4612), raise fires unchanged; walker zero `async def`; no
oracle pins the Relay wording on the walker path (exact + fragment sweeps,
all hits adjudicated unrelated); `_WALKER_ASYNC_RECOURSE` justified —
sixth member of the per-surface-recourse-constant family, not 4A
machinery. 66: `999a1aab` diff read; current :934 matches the body. 68:
`899cb35b` deletes both defs (message names both, board discharged);
per-tree zeros for both names with `_ensure_connector_only_fields` present
as positive control; `__all__`, GLOSSARY, TREE, KANBAN, spec-033 clean
(only regenerable shadow snapshots mention them); survivor is the distinct
writer (plan + log-and-skip, walker.py:1689). 69/70: HEAD unguarded shapes
confirmed; cited hunks verbatim in the HEAD-diff, absent from the item
diff, defect lines inside — no clean-line fix. 71: silence arm +
docstring at HEAD bytes (:672-673, :631-636); landed by `269b80c0`
(ancestor of HEAD); pinning class run green, 14 passed.

Attribution: every item minus-line HEAD-identical at baseline; walker
additions touch no hunt line (kwarg beside the hunt `model=` line,
constant disjoint from predirt). AST: docstring-normalized code-identical
on 3 prose files; walker scope exactly one Assign + one keyword at one
call site. Gates: ruff format --check + ruff check clean (4 paths);
basedpyright 0/0/0 both passes; truthful-reads --check exit 0 tier-1 0 at
verify-1 (fresh slot-3 copy, shared unmoved). Removed phrases score zero
oracle hits. Blobs match W1's pins; HEAD `23b5f421` unmoved; item diff
exactly the 4 files + plan; no test edits, no REROUTE.
