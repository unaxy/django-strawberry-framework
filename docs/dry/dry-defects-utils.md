# DRY review: `defects-utils`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Batch: 18 rows (16 + 19-22 + 24-29 + 32 + 34 + 35 + 51 + 54 + 63 + 64) across
10 package files (9 in `utils/` + `optimizer/extension.py` for row 35 only).
Read every row's `## Defects` entry in full + the folder-utils adjudication
(member verdicts, FF-1..FF-17, riding/closed/narrowed lists) before touching
anything; re-checked each against current worktree bytes. Attribution: full
vs-HEAD diff read hunk by hunk — `utils/__init__.py` CLEAN (0 hunks, newly
dirtied only by this item); the other 9 carry hunt truth-migration dirt plus
the f66 ledger pair (seal-carry write, G1 read, `_queryset_private` pair).
Every touch line verified HEAD-identical context first (unified-0 zero
overlap with hunt hunks). Cross-cutting: table summaries for rows 20
("config annotates ints") and 27 ("aliasing-no-write") are phantom phrases
(0 hits each); the verified entries governed. Folder-utils row-19(b)
"20/23 named" is not borne out (9/22 on the clean file); fixed per the
entry. Developed in slot-2, gated, ported byte-identical (`cmp` clean 8/8).

## Verification

### Matrix

1. Cross-flavor mirroring — each fix is site-local prose; no second site states the same claim.
2. Sync/async twins — prose-only delta; no await boundary, no twin surface.
3. Derived knowledge — every replacement claim verified at its owner body/call census.
4. Round-trip pairs — none owed; no encode/decode grammar touched.
5. Other media — glossary term + spec-034 clause read for row 27; HEAD oracle run for row 51.
6. Omission — census removals (rows 20, 26) close the class instead of recounting it.

### Freshness

HEAD `23b5f421`, ITEM_BASELINE `5ebbc229`. Post-edit WT blobs: `__init__`
`1a18f85e`, directives `bbd85c32`, errors `ddec038a`, inputs `3d99df6c`,
input_values `b0a2c66a` (untouched), permissions `dbb8f602`, relations
`b0cc6c33`, querysets `395cb2cf`, _queryset_private `61527cd9`
(untouched), extension `501c29d4`. Slot-2 runs `ca7fb0`/`62035b` (ruff),
`6d0776` (AST), `f5e9c6`/`bc5387` (basedpyright), `2a58af` (truthful),
`828829` (layout), `979375` (row-51 oracle).

## Findings

| # | row | verdict | change |
|---|---|---|---|
| 16 | relations D1 | FIXED | parenthetical retargeted to `field_meta.py::FieldMeta` |
| 19 | `__init__` D1 | FIXED | PINNED paragraph: leaf/held/nominal-bullets/`__all__`-where-defined |
| 20 | directives D1 | FIXED | factory enumeration removed, universal kept (9/9 route through) |
| 21 | errors D2 | FIXED | "call DIRECTLY" -> route through the write_values decode spine |
| 22 | inputs D1c | FIXED | "repr-sorted" -> sorted by the canonical key |
| 24 | permissions D1 | BLOCKED-ON-HUNT | both sentences are hunt `+` lines (hunks below) |
| 25 | permissions O1 | FIXED | re-export comment names the test suite, not filters/sets.py |
| 26 | relations D2 | FIXED | 3-site census removed instead of extended to the forms 4th |
| 27 | querysets D2 | ALREADY-FIXED | glossary + spec-034 already state the `_SealPolicy` spelling |
| 28 | querysets D4 | ALREADY-FIXED | ORDER clause absent at WT and at HEAD |
| 29 | seal O1 | FIXED | owned two-clause repair (cause list + combined text) |
| 32 | e3 D1 | FIXED | extinct cite reworded to `errors.py::relation_field_error` |
| 34 | e6 D1 | NOT-A-DEFECT | owner extinct package-wide (FF-8); no docstring omits the record |
| 35 | e6 D2 | FIXED | unwrap/re-wrap clause added beside the `_optimize` steps |
| 51 | orm-lookup D1 | ALREADY-FIXED | `3594e599` code + oracle at HEAD; oracle green in slot-2 |
| 54 | traversal D1 | BLOCKED-ON-HUNT | `input_values.py @@ -244,23 +228,16 @@` (hunt `+` conditional) |
| 63 | querysets D5 | ALREADY-FIXED | `5741eaa6` at HEAD; dead arms gone, docstring enumerates `combined` |
| 64 | f66 D1 | BLOCKED-ON-HUNT | `_queryset_private.py @@ -7,6 +7,13 @@` (refresh must rewrite :7) |

24: `input_values.py @@ -316,18 +292,13 @@` + `permissions.py @@ -826,38 +785,27 @@`;
the UNBOUND claim still contradicts the dict-only body, but both sentences are
hunt-rewritten `+` lines. Ready shape: narrow each to dict-vs-other-mapping.
27: `allow_sliced` is 0 hits package-wide, glossary-wide and spec-wide; the
Prefetch-alias-threading term and spec-034:353 both state `reject_sliced=False`.
34: `is_async_queryset_adapter` 0 hits in package + tests + examples
(`899cb35b` deleted it); the principle-11 record requirement has no owner.
51: screen is `isinstance(candidate, ForeignObjectRel)` at HEAD and WT; the
`_RAW` oracle rows (Book/TaggedItem/Branch misses) pass — no code or test owed.
63: the three message dicts carry type/table/untrusted (+sliced/combined/
projection where reachable); no `routing`/`evaluated`/`combined`-dead arm remains.

## Defects

None. No new defect found; the three blocks ride their exact hunks above.
None (Worker-2): no new defect in trace or gates; slips ride the
verification section, no card owed.

## Judgment

10 rows FIXED (prose-only, 8 files), 4 ALREADY-FIXED by committed evolution,
1 NOT-A-DEFECT on an extinct owner, 3 BLOCKED-ON-HUNT with exact hunks. Zero
executable delta (AST-identical 8/8); all gates green. No test file touched:
row 51's oracle already exists at HEAD, so no REROUTE is owed.

## Implementation (Worker-1)

Landed (slot-2 -> shared tree byte-identical, `cmp` clean; +38/-27 over
ITEM_BASELINE; status 551 = 550 + `__init__.py` newly dirtied by this item):
relations.py rows 16 + 26; `__init__.py` row 19; directives.py row 20;
errors.py row 21; inputs.py row 22; permissions.py row 25; querysets.py rows
29 + 32; extension.py row 35 (only file outside `utils/`, per brief).
Gates in slot-2 via `heavy`: ruff check --fix + format clean (8 files);
docstring-stripped AST vs pre-edit shared bytes IDENTICAL 8/8 (vs HEAD
differs only by pre-existing hunt executable dirt); basedpyright 0/0/0 both
passes; truthful-reads tier-1 0; trailing-commas 0; row-51 oracle 1 passed.
No new cast/suppression/pragma; `@override` untouched; citations
`path::Symbol`. No scratch under the repo; slot-2 holds the pre-port bytes.

## Independent verification (Worker-2)

Expectation-first: each verdict derived from its source entry +
HEAD/worktree bytes before the Findings table was opened. Own
verdicts — FIXED: 16 (FieldMeta reads kind; record carries none),
19 (oracle pins seven; notable-selection; where-defined), 20 (9
factories independently enumerated, 9/9 route through), 21 (leaf
called only from the write_values spine; aliases extinct), 22
(body sorts by canonical_sort_key), 25 (filters/sets.py imports
direct; only the test suite uses the path), 26 (forms 4th site
confirmed; generic sentence true), 29 (both constants
multi-composed; owned clause landed), 32 (old name 0 hits in .py;
cite live), 35 (unwrap on entry, all 4 exits re-wrap).
ALREADY-FIXED: 27 (glossary + spec-034 spent at HEAD + WT;
allow_sliced extinct), 28 (5741eaa6 dropped the clause), 51
(3594e599 + oracle green), 63 (5741eaa6; arms re-derived clean).
NOT-A-DEFECT: 34 (is_ deleted by 899cb35b; 0 residue). BLOCKED:
24 (both UNBOUND sentences hunt-rewritten; fork live both
states), 54 (cap_detail condition + cap read both hunt-changed;
any knob read couples to the migration), 64 (fix must rewrite
:7 inside the cited hunk span).
Reconciliation: concur 18/18. Row-20 9/9 borne out (auth third
factory is current_user via _make_auth_field). Row-24 hunk is
+784,27 not +785 (HEAD side -826,38; carry corrected). Row-19b:
9/22 named re-derived; folder's 20/23 wrong both halves, fix
stands per the entry. -U0 zero-overlap consistent with merged
default hunks, all separated by content. Net +33/-27 recounted;
W1's +38 a verdict-neutral record slip (bytes right).
Gates (verify-1 slot-3): ruff format --check + ruff check clean
(8 paths); basedpyright 0/0/0 both passes (215043, 215158);
truthful-reads errors 0 (215309); prose-only + AST-identical 8/8
(own probe /tmp/w2-prose-check.py); row-51 oracle 1 passed on
Django 6.1.2 (214447). Every touched line HEAD-verbatim; hunt
adjacencies (errors deletion, inputs truth-migration, directives
line-1 word) preserved byte-identical. Verdict: verified.
