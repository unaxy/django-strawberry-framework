# DRY review: `defects-filters-orders`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Batch: 11 doc-only rows (table rows 1-10 + 23) across 7 package files
(`filters/{base,inputs,sets}.py`, `orders/{base,factories,inputs,sets}.py`).
Read all 8 source `## Defects` entries in full + the folder-orders adjudication
before touching anything; re-checked each against current worktree bytes and HEAD.
Attribution: full vs-HEAD diff of all 7 files read hunk by hunk -- 6 files carry
hunt truth-migration dirt (`truth.*` rewrites, hostile-container reversals);
`orders/factories.py` is clean; `filters/sets.py` additionally carries ledgered
f51 + filters-FAM-1/2/3 hunks (buildable, untouched by these fixes).
Cross-cutting: the homing-table summaries for rows 4-10 + 23 name phrases
("final say", "single sequence", "CopyFrom", "dynamically interns alias
triples", "second defensible reading") verified by `rg` to occur NOWHERE --
zero hits in the package and the source artifacts at both HEAD `23b5f421`
and worktree bytes. The W2-verified artifact entries (confirmed by the folder
adjudication's "all seven member D1s re-verified persisting") governed instead;
every one of them was live in current bytes, on clean lines except row-1 limb c.
Connected reads: spec-028 Decisions 5/8/13 + Edge cases, spec-030 Decision 11
(P1-B census 0), production caller censuses per limb, the `read_set_meta_fields`
-> `canonical_sort_key` chain. Developed in slot-2, gated, ported byte-identical.

## Verification

### Matrix

1. Cross-flavor mirroring -- orders/filters twin prose pairs re-read (alias comments, BFS docstrings, normalize docstrings); each defect is family-local wording, no twin shares the false sentence.
2. Sync/async twins -- inapplicable: prose-only batch, no executable surface, no await boundary crossed.
3. Derived knowledge -- every replacement cite verified at its owner (spec decisions read in full; caller censuses re-derived; sort-key chain walked to the body).
4. Round-trip pairs -- inapplicable: no encode/decode pair in the batch surface.
5. Contracts in another medium -- spec-028/spec-030 re-read to verify each re-pointed home; two spec-side echoes carried as card notes, not fixed (out of scope).
6. Enforcement by omission -- inapplicable: prose corrections, no guard added or removed.

### Freshness

HEAD `23b5f421` unmoved; ITEM_BASELINE `a5210307` (= tree at dispatch; pre-edit
diff over the 7 files empty). Post-edit worktree blobs: filters/base `d864e527`,
filters/inputs `4114d171`, filters/sets `c9fbcd84`, orders/base `a62683ff`,
orders/factories `364e05bb`, orders/inputs `26c0e658`, orders/sets `79c369b3`.
Specs: spec-028 `2afbe930`, spec-030 `295f9cfb`. Slot-1 before == shared
pre-edit; slot-2 post-edit == shared post-edit (`cmp` identical all 7).
Evidence: sync `dry-20261010T202836-537e44`, ruff `dry-20261010T203053-c34b0f` +
`dry-20261010T203102-a16114`, basedpyright `dry-20261010T203107-3e5c6d`, floor
`dry-20261010T203218-7ffdc8`, truthful `dry-20261010T203330-ab46e7`,
trailing-commas `dry-20261010T203337-060a25`, citations OK 89/89.

## Findings

| # | defect | verdict | change |
|---|---|---|---|
| 1 | s7/base D1 (5 censuses) | FIXED 4/5 + BLOCKED-ON-HUNT limb c | censuses removed at 4 docstrings; materialize limb rides the hunt hunk |
| 2 | s8/inputs D1a+D1b | FIXED | guard + normalize censuses removed |
| 3 | s9/sets D1 (4 projections) | FIXED | GlobalID-only wordings widened to both identity primitives |
| 4 | orders base D1 | FIXED | metaclass-mutation sentence restated as ergonomic relaxation + triples fallback |
| 5 | orders factories D1 | FIXED | BFS path restated as inputs hook + shared base constructor |
| 6 | orders inputs D1 | FIXED | alias consumer map restated (tests + `__init__` + intra-module) |
| 7 | orders inputs D2 | FIXED | Decision 13 cite re-pointed at D5 + D8 steps 6/7 + Edge cases |
| 8 | orders sets D1 | FIXED | Decision 13 cite re-pointed at D8 step 7 + Edge cases |
| 9 | orders sets D2 | FIXED | both P1-B cites re-pointed at spec-030 Decision 11 paragraph |
| 10 | orders sets D3 | FIXED | "verbatim port" restated as direct port + collector/promote deltas |
| 23 | utils inputs D2 | FIXED | `repr`-sorted claim restated as canonical-key order |

Row 1: limbs a/b/d/e fixed on clean lines (current callers 4/4/5/5 vs named 2/2/3/2;
drift continued past filing -- the predicate now serves 5). Limb c ("three consumers",
serves 4) sits on `+` lines of the hunt's hostile-container hunk (exact hunk below).
Row 7: cites D8 steps 6/7, not the filed 3/6/7 -- step 3's current text carries no walk
semantics; the nested-RelatedOrder walk lives in step 7.

## Defects

None.

## Judgment

10.5 of 11 rows fixed doc-only on clean lines with inverse proof; the half row
(row-1 limb c) is blocked on one named hunt hunk whose landed rewrite kept the
stale census. No behavior changed, no tests owed, no new defects. The batch's
table summaries for rows 4-10 + 23 name phantom phrases; the fixes follow the
verified artifact entries instead.

## Implementation (Worker-1)

Landed (all prose-only; slot-2 -> shared tree byte-identical, `cmp` clean):
`filters/base.py` comment block + `_marked_pk_field_name` (2 sites) +
`_match_none_queryset` + `_apply_lookup_predicate` docstrings;
`filters/inputs.py` `_require_list_container` + `normalize_input_value`
docstrings; `filters/sets.py` FilterOrigin comment + provenance docstring +
origins comment + `_generation_origin_for_field` docstring; `orders/base.py`
module docstring; `orders/factories.py` module docstring; `orders/inputs.py`
alias comment + normalize docstring; `orders/sets.py` module docstring +
`_expand_meta_fields` + `_resolve_order_expressions` + `apply_sync` docstrings.
Net over ITEM_BASELINE: +62/-49 across the 7 files, zero executable bytes.
Gates in slot-2 via `heavy`: ruff check + format clean; basedpyright 0/0/0 both
passes; truthful-reads tier-1 0; trailing-commas 0; citations 89/89 resolve;
inverse proof (docstring-stripped AST slot-1 vs slot-2) IDENTICAL all 7.

BLOCKED-ON-HUNT row-1 limb c (`filters/base.py::_materialize_list_shaped_values`
"Shared by ... the three list-shaped consumers", serves 4 -- the sentence sits on
`+` lines of this concurrent hunk, `git diff HEAD`, `@@ -243,22 +239,15 @@`):

```
     caller's coded GraphQL error instead of leaking a raw ``TypeError`` from a
     ``len()`` / iteration the shape can never satisfy.

-    The materialization itself is contained: a ``list`` SUBCLASS whose
-    ``__iter__`` raises mid-iteration passes the ``isinstance`` gate and would
-    otherwise detonate inside ``list(value)`` -- the same hostile-container
-    class ``orders/sets.py::OrderSet._expand_meta_fields`` closes structurally
-    -- so a lying container degrades to the same coded reject as a wrong
-    shape. Shared by ``_globalid_multiple_choice_values`` (the GlobalID
-    multi-value gate), ``ListFilter.filter``, and ``IntegerInFilter.filter``
-    so the fail-closed contract cannot drift between the three list-shaped
-    consumers.
+    Iterating an accepted ``list`` / ``tuple`` (subclass included) is the
+    value's own behaviour, so whatever its ``__iter__`` raises propagates.
+    Shared by ``_globalid_multiple_choice_values`` (the GlobalID multi-value
+    gate), ``ListFilter.filter``, and ``IntegerInFilter.filter`` so the
+    fail-closed contract cannot drift between the three list-shaped consumers.
     """
     if not isinstance(value, (list, tuple)):
         raise GraphQLError(message, extensions=coded_error_extensions(code))
-    try:
-        return list(value)
-    except Exception as exc:
-        raise GraphQLError(message, extensions=coded_error_extensions(code)) from exc
+    return list(value)
```

Repair when the hunt lands: drop the consumer enumeration ("Shared by the
list-shaped consumers so the fail-closed contract cannot drift between them").

Carried to the homing card (recorded in the source entries, outside this
batch's files): spec-028 slice-2 BFS-path echo (factories D1 bilateral);
spec-028 Edge-case None-locus wording vs the `_active_order_terms` filter arm
(sets D1 observation).

## Independent verification (Worker-2)

Sequencing: System-trace + tail exposure before writing (head/tail for
structure); all verdicts below from own fresh reads (source entries + WT
bodies + HEAD + baseline bytes) predating any Findings read. Reconciliation
appended after Findings read.
Own verdicts (source entry + current body fresh, per row):
1 s7/base D1: FIXED x4 (ATTR comment, _marked, _match_none, _apply_lookup all
de-counted, prose matches bodies) + BLOCKED x1 (limb c _materialize Shared-by-3
persists; hunk @@ -243,22 +239,15 @@ rewrites paragraph + body).
2 s8/inputs D1a+D1b: FIXED (both de-counted; enum arm live in body).
3 s9/sets D1: FIXED (all 4 widened to relation-identity; both primitives built).
4 orders base D1: FIXED (ergonomic + fallback + no-assign; 1 self-store only).
5 orders factories D1: FIXED (BFS path corrected; base call verified).
6 orders inputs D1: FIXED (consumer map; all five test imports + init + intra).
7 orders inputs D2: FIXED (D13 -> D5/D8+Edge; D13 is coverage plan).
8 orders sets D1: FIXED (D13 -> D8s7+Edge; None-filter arm verified).
9 orders sets D2: FIXED (P1-B -> D11 paragraph; P1-B 0 in spec).
10 orders sets D3: FIXED (verbatim -> direct + deltas; metaclass calls verified).
23 utils inputs D2: FIXED (repr-sorted -> canonical-key; chain verified).
Phantom: own rg at HEAD + WT — "final say", "single sequence",
"callable-narrowing", "CopyFrom", "dynamically interns", "alias triples",
"second defensible reading" all 0 hits (package-wide for CopyFrom). Table
summaries phantom; artifact entries live at baseline, fixed now.
Gates (slot-3 verify-1, fresh): AST strip-identical 7/7; ruff format 7 clean;
ruff check pass; basedpyright 0/0/0 both passes; truthful-reads tier-1 0.
Attribution: W1 hunks vs hunt hunks (HEAD-vs-baseline) zero overlap all 7
files (unified-0 ranges); factories 0 hunt hunks. Limb-c hunk exact in
HEAD-vs-baseline; Shared sentence inside it, unlandable without touch.
Reconciliation (post-Findings read): zero verdict differences — all 11 rows
match exactly (row 1 mixed FIXED+ BLOCKED, rest FIXED). Row-1 counts concur
(predicate 5 verified at 5 call sites; drift-continued note accurate). Row-7
D8 6/7-not-3/6/7 deviation CORRECT (step 3 is the call step, walk lives in
step 7 — verified in spec). N2/N3 (spec-028 BFS echo + None-locus) outside
batch files, correctly carried. Freshness blobs 9/9 match. Figures +62/-49
match. Removed censuses non-contract (consumer enumerations, rationale
preserved). No defects found (Worker-2). Verdict: verified.
