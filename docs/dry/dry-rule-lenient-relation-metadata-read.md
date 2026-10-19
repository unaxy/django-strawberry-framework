# DRY review: `lenient-relation-metadata-read`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule as the holding file item framed it: read one relation-metadata
attribute, degrading to the caller's default when the read is unanswerable
(`getattr` with default + `except BaseException` → default), with the
`lenient=` policy axis and the `safe_truthy` truth-test guard selecting that
policy. The file item nominated two definitions: the owner candidate
[utils-relations][utils-relations]`::relation_attr` (+ lenient
`::relation_bool`) and the inline rungs in
[definition][definition]`::DjangoTypeDefinition.related_target_for`.

Verdict: REJECT — zero authoritative definitions survive at current bytes.
Both nominated definitions were deleted by the maintainer's concurrent
truth-migration + `except BaseException` deletion rewrite: `relation_attr`
and `safe_truthy` are absent package-wide (0 hits), `relation_bool` is
strict-only (non-`bool` raises `ConfigurationError`), and
`related_target_for` reads `model_field.is_relation` /
`model_field.related_model` bare. A whole-package AST census over 120 files
finds 68 three-arg `getattr` sites on 18 relation attribute names with zero
under any `try`, and all 11 surviving `except BaseException` sites are
compensate/cleanup + re-raise, none on relation metadata. The change
challenges count 0/0. Nothing to consolidate; zero-edit.

Concurrency: both indexed files are fully concurrent-dirty and neither has
an `## Owned changes` row covering the rewrite. Every hunk below is
attributed by diff content vs `git show HEAD:<path>`; nothing was edited,
reverted, or tidied.

`utils/relations.py` (WT `a6692e4d` / HEAD `e64a7a8f`): the
`classify_path` "Four other `_meta` path walkers" docstring paragraph is
LEDGERED (adopted orphan `orm-lookup-path-resolution` — the one hunk this
item could build on, untouched). Everything else is concurrent: the
`relation_attr`/`safe_truthy` deletion + `relation_bool` strict rewrite +
`relation_name` re-spell, the `truth` import and `_safe_type_name` →
`truth.kind` swaps, every `except BaseException` arm deletion
(`is_many_side_relation_kind`, `_resolve_segment_field`,
`_is_traversable_relation`, `classify_path` body, `_traverses_to_many`,
`path_traverses_to_many` hash gate, `is_forward_concrete_relation`,
`instance_accessor`, `has_composite_pk`), the `_lenient_traverses_to_many`
restructure, and the maintainer's `validate_lookup_expr` re-derivation
(column cursor, `truth.is_instance`, deleted arms). No hunk is unattributed.

[definition][definition] (WT `e79d7129` / HEAD `ff80ef02`): all hunks are
the same concurrent rewrite — the two inline lenient rungs
(`getattr(model_field, "is_relation", False)` /
`getattr(model_field, "related_model", None)` in `try`/`except
BaseException`) replaced by bare reads, every other hostile-read arm
deleted, `truth.*` swaps, plus the new `_unwrap_method` helper. No hunk is
unattributed. The oracles moved in the same rewrite:
[test-def-rel][test-def-rel] lost 140 lines including the whole
hostile-metadata family and the "never an exception" rule (contract
inverted to propagate).

Baselines: `ITEM_BASELINE=9f11157f0afcdee4a49dceed2255c291a42b7801`
(resolves, type `commit`); `git diff <baseline> -- <both indexed paths>`
is empty — the tree did not move under this item. HEAD `dd0b6691`
unmoved throughout. Dispatch pins verified at task start: relations WT
`a6692e4d` / HEAD `e64a7a8f`, definition WT `e79d7129` / HEAD `ff80ef02`.
Address `dry/lenient-f43/consolidate` (slot-2; all proofs ran there).

## Verification

### Matrix

Each axis was searched against the rule's mechanism (a raising
relation-metadata read degrading to a default), not the targets'
neighbours.

1. Cross-flavor policy mirroring — searched. No flavor carries a lenient
   policy. The strict readers are shared leaf-ward and every flavor
   consumes them by name: [field-meta][field-meta] composes
   `relation_bool` / `relation_name` / `relation_kind` /
   `instance_accessor` (8 strict call sites, bodies read); filters,
   mutations, forms, connection, permissions, keyset, plans, querysets
   use bare `getattr(..., default)` (omitted → default, raising reads
   propagate — R1) or bare attribute reads; [join-taxonomy][join-taxonomy]
   reads through unguarded `_attr` / `_flag` under the module doctrine
   "an attribute a shape omits takes the default, and nothing is
   guarded" (R3). No mirror of the lenient policy in any flavor.
2. Sync/async twins — inapplicable with reason: token grep for `async
   def` / `await ` / `sync_to_async` / `asyncio` over the five reader
   modules (relations, definition, join_taxonomy, field_meta, truth)
   returns 0; metadata reads are sync-only at both HEAD and WT, and the
   deleted lenient readers were sync-only too. No twin exists to drift.
3. Derived rather than repeated knowledge — searched. No site derives
   the lenient verdict by other means. The nearest shapes are different
   rules: `_lenient_traverses_to_many` derives a path-level to-many
   answer (R4); `_flag` coerces truth where `relation_bool` requires
   `bool` (R3 — opposite contracts, not two spellings of one); bare
   `getattr` with defaults is stdlib omitted→default vocabulary with a
   crash-open contract on raising reads (R1). Deriving no lenient
   verdict anywhere is the point: the policy is gone.
4. Inverse / round-trip pairs — none owned. The rule is a read with no
   inverse half. `truth.static_attr` is not a lenient-reader twin: it
   deliberately never invokes descriptors, so it cannot read Django
   relation metadata at all (R5, body read).
5. Contracts restated in another medium — classified, never counted.
   Oracles: the hostile-metadata rows are deleted from
   [test-def-rel][test-def-rel] (−140, concurrent) and no
   `relation_attr` / `safe_truthy` / lenient-flag test survives anywhere
   live (`tests/`, `examples/`, `scripts/` all grep 0 outside prior DRY
   artifacts and another item's frozen `temp-tests` copy, which is not
   live code). The surviving `lenient` tokens name different rules: the
   to-many walk, the import attr-lenient wrapper, the input-shape
   attr-lenient probe (R8). Projections: closed-cycle prose in
   `docs/bug_hunt/bug_hunt-0_0_15-historical.md` /
   `bug_hunt-0_0_13.md` (committed history, left alone) and the
   regenerable `docs/shadow/current/` snapshot (its generator's to
   refresh, left alone); standing docs (`GLOSSARY.md`, `KANBAN.md`,
   `TREE.md`) grep 0.
6. Enforcement by omission — family enumerated, each member checked.
   The population is every relation-metadata read: 68 three-arg
   `getattr` sites (AST census, 0 under `try`), the bare attribute
   reads, the `relation_bool` / `relation_name` strict consumers, and
   the `_attr` / `_flag` taxonomy readers. Zero carry the lenient
   policy. The absences are no-rule, not gaps: the policy was deleted
   and its oracles updated in the same maintainer rewrite, so no
   contract source establishes that any member owes a lenient read.
   Filing a "missing guard" here would re-litigate the maintainer's
   concurrent contract change, not this family's rule.

### Enumeration

Instrument one: AST census `/tmp/f43-census.py` over
`django_strawberry_framework/**/*.py` (120 files, 0 unparseable,
`__pycache__` excluded) for 3-arg `getattr` on 18 relation attribute
names (`is_relation`, `related_model`, the five cardinality flags,
`m2m`, the generic slots, `accessor_name`, `get_accessor_name`,
`path_infos`, `column`, `target_field`, `remote_field`, `through`,
`attname`): 68 hits in 20 files, 0 under any `Try` with handlers.
Instrument two: `/tmp/f43-census2.py` for bare attribute reads of the
same names under `try`: 1 hit —
[resolvers][resolvers]`:174` (`getattr(root, field_meta.attname)`
under `except AttributeError` → `None`), a ROW-VALUE read under the
FK-id elision rule, excluded (R6). Instrument three: grep censuses —
`relation_attr|safe_truthy` 0 package-wide; `_safe_getattr|_safe_getbool`
0; `except BaseException` 11, each body read, all compensate/cleanup +
re-raise (R7); `relation_bool(`/`relation_name(` 23 strict call sites
in 2 files (R2). Every hit is homed: F1 owns the (absent) rule; R1–R9
carry the exclusions.

### Challenges

The rule's variation axes, re-derived from the file item's #39/#40 at
current bytes. Counts are authoritative definitions of the LENIENT
policy (a raising relation-metadata read degrading to a default).
Strict readers, bare readers, oracles, projections listed under F1,
never counted.

- C1 mechanism change (route raising relation-metadata reads through a
  default again): 0 definitions implement the policy — count 0. No two
  sites must move together; there is not one.
- C2 lenient-outcome change (a third outcome, e.g. log-and-default): 0
  definitions select a lenient outcome — count 0. The `lenient=`
  parameter no longer exists on any signature.
- C3 (variation-axis completeness: strictness change — non-`bool` flag
  verdict): moves exactly the one strict body,
  [utils-relations][utils-relations]`::relation_bool` — count 1, and it
  is the strict rule (verified single-owned under
  `relation-kind-taxonomy`), not this family. Confirms the family has
  no member even on its closest axis.

## Findings

### F1 — the lenient relation-metadata read (REJECTED, zero definitions)

- **Contract + variation.** As framed at HEAD bytes (`e64a7a8f` /
  `ff80ef02`): read one relation-metadata attribute, degrading to the
  caller's default when the read is unanswerable, guarding both the
  read and (via `safe_truthy`) the truth test; varied as the read
  mechanism and the lenient outcome. At WT bytes no site implements
  this contract: the policy axis is deleted, not relocated.
- **Sites + roles.** Former definitions (both deleted, quoted from
  HEAD): `relation_attr` (+ `safe_truthy`, + lenient `relation_bool`)
  in [utils-relations][utils-relations], and the two inline rungs in
  [definition][definition]`::related_target_for`. Current roles:
  `relation_bool` / `relation_name` are the STRICT owner (definition
  of a different, verified-single-owned rule — listed, not counted);
  field_meta's 8 call sites + the in-module classifier calls are its
  consumers; the 68 bare `getattr` sites + bare attribute reads are
  omitted→default / crash-open readers (R1); `_attr` / `_flag` are the
  taxonomy's unguarded readers (R3). Oracles: deleted (see Matrix 5).
  Projections: closed-cycle hunt prose + regenerable shadow output
  (Matrix 5).
- **Challenges.** C1 counts 0, C2 counts 0, C3 counts 1 on the strict
  rule. The file item's #39/#40 count-2 verdict does not survive the
  concurrent rewrite: both counted sites are gone.
- **Owner + lifetime.** None. Principle 7 chooses among owners of a
  SHARED responsibility; no responsibility is shared here, so no owner
  is owed. The index-row candidate
  (`utils/relations.py::relation_attr`) was re-derived, not inherited:
  the symbol does not exist at WT bytes, and reviving it to host a
  policy the maintainer just deleted — with oracles updated to assert
  propagation — would reverse a concurrent contract change, not
  consolidate a rule.
- **Migration.** None — zero-edit. No production, test, or doc line
  moves.
- **Distinct behavior.** The strict readers stay single-owned under the
  verified `relation-kind-taxonomy` and `relation-instance-accessor`
  families; the path-level fail-open walk stays under
  `orm-lookup-path-resolution` territory (R4). Nothing is shared with
  them beyond the attribute names.
- **Behavioral proof.** `static-reviewed`. Symbol absence, body
  comparison, and AST-closed censuses decide; nothing ordering-,
  transactional-, or async-sensitive was judged. Wrong result (a)
  "a lenient site survives somewhere" is rejected by the 68/0
  try-census + the 11-site except census (all re-raise, each body
  read) + the package-wide `relation_attr|safe_truthy` 0-hit grep.
  Wrong result (b) "bare `getattr(..., default)` sites are lenient
  definitions" is rejected by body semantics (no except arm: a
  raising descriptor propagates — the crash-open contract the file
  item itself classified as outside this rule) and by the standing J1
  direction (per-site except arms with per-site verdicts are not one
  rule; here there are not even arms).
- **Structural gate.** None owed. There is no owner to bypass, and a
  "rule stays extinct" census would be a bespoke existence test, which
  [dry][dry] forbids. The mechanism class is already enforced standing:
  `scripts/check_truthful_reads.py` (tier-1, exit 0 in this item's
  copy — run id below) forbids `except BaseException` swallow
  handlers package-wide, so the except-arm half of the lenient
  spelling cannot be reintroduced without reddening CI. No negative
  control is owed for a gate not added.
- **Coupling.** D1 (this artifact): the file item's coupled D3 is
  overtaken by the same rewrite — see `## Defects`. No landing
  dependency: the finding is zero-edit either way.
- **Freshness.** WT (`git hash-object`) / HEAD (`git rev-parse
  HEAD:<path>`), same-kind pairs: relations `a6692e4d` /
  `e64a7a8f`, definition `e79d7129` / `ff80ef02`, join_taxonomy
  `aa289013` / `8026dc8d`, field_meta `99f7b1d3` / `7c9afe35`,
  filters/sets `14884190` / `76abccb0`, filters/base `9edbef64` /
  `058fcfb1`, auth/mutations `8d9e8561` / `101dbf82`,
  resource_policy `f95f1580` / `9faff1a8`, operation_state `5f6f255d`
  / `009714fd`, list_field `b534ea32` / `3842542a`, schema `c3f267aa`
  / `f3b6df8f`, test_relations `549feada` / `e51cebaa`,
  test_definition_relations `fee20cf8` / `196e783d`. Untracked truth
  `711352b1` (WT only — no HEAD blob exists). Census population:
  120 package files, 0 unparseable. Excluded-by-body modules:
  resolvers (`types/resolvers.py` R6/R9), imports, inputs, exceptions
  (R8) — bodies read, pins below in R8. Any fingerprint change
  reopens the finding.

### R1 — bare three-arg `getattr` on relation attributes (excluded)

68 sites in 20 files (AST census). Contract difference: omitted →
default only; a raising descriptor propagates (stdlib vocabulary,
crash-open contract). The lenient rule additionally contained the
raising read; without an except arm these sites answer differently on
exactly the inputs the rule varied on. Reconsideration trigger: any
site gains raising-read containment with a default verdict — that
site + any second such site reopen the family.

### R2 — strict `relation_bool` / `relation_name` (excluded)

23 call sites in relations.py + field_meta.py, composing the one
strict body by name. Contract difference: opposite failure posture —
absent/`None` takes the default but any other non-`bool` (non-`str`
for names) RAISES `ConfigurationError`, and a raising read
propagates. The strict rule is verified single-owned under
`relation-kind-taxonomy`. Reconsideration trigger: a `lenient=` axis
(or equivalent raising-read containment) returns to either body.

### R3 — taxonomy `_attr` / `_flag` (excluded)

[join-taxonomy][join-taxonomy]`:92–99`: `_attr` is bare
`getattr(value, name, default)`; `_flag` is `bool(getattr(value, name,
False))`. Contract difference: unguarded by stated module doctrine
("nothing is guarded" — 0 `try:` / 0 `except` in the file), and
`_flag` COERCES truth where `relation_bool` REQUIRES `bool` — the
two answer differently on a truthy non-`bool` by design. Replaces
the deleted `_safe_getattr` / `_safe_getbool` lenient pair.
Reconsideration trigger: guards return to the taxonomy, or the
coerce-vs-require fork collapses into one verdict.

### R4 — `_lenient_traverses_to_many` path walk (excluded)

[utils-relations][utils-relations]`:442`: a PATH-level fail-open
walk (`FieldDoesNotExist` → `False`, many-side short-circuit),
running only when strict `classify_path` raises. Contract
difference: per-path verdict over a classifier failure, not a
per-attribute read degrading on an unanswerable attribute; its one
remaining except arm catches the typed `FieldDoesNotExist`, never a
raising read. Owned in `orm-lookup-path-resolution` territory (the
ledgered `classify_path` rationale names the walker split).
Reconsideration trigger: per-attribute except arms return inside the
walk.

### R5 — `truth.static_attr` / `truth.own_attr` (excluded)

[truth][truth]`:437–475` (untracked concurrent module, bodies read).
Contract difference: reads the real namespaces WITHOUT invoking
descriptors — the opposite mechanism from a relation-metadata read,
which must invoke Django's field descriptors; subjects are identity
facts (`__mro__`, `__dict__`, names), never relation metadata (0
relation tokens in the file). It cannot serve a relation read by
construction. Reconsideration trigger: `truth` gains a
descriptor-invoking relation reader.

### R6 — elision row-value read under `except AttributeError` (excluded)

[resolvers][resolvers]`:173–176`: `getattr(root, field_meta.attname)`
→ `None` on `AttributeError`. Contract difference: the subject is
ROW DATA (an instance's FK column value), not field METADATA; the
except is the narrow `AttributeError`, and the verdict feeds the
FK-id elision rule (verified family territory), not a metadata
default. The sole bare-read-under-`try` hit in the package.
Reconsideration trigger: none foreseeable — subject differs
permanently; a metadata read with a default verdict would be a new
site, not this one.

### R7 — the 11 surviving `except BaseException` sites (excluded)

auth/mutations `:691/:737/:904/:975` (compensate + re-raise),
resource_policy `:1380/:1413` (iterator cleanup + re-raise),
operation_state `:681/:798/:812` (unbind + re-raise), list_field
`:1310` (async-iterable cleanup + re-raise), schema `:352` (atomic
exit + re-raise). Each body read. Contract difference: every one
re-raises — none answers a default, none guards a relation-metadata
read. The standing truthful-reads gate pins this shape.
Reconsideration trigger: any site gains a default verdict on a
metadata read.

### R8 — other `lenient` senses (excluded)

`utils/imports.py:10` (attr-lenient IMPORT wrapper — different
subject, its own test at `tests/utils/test_inputs.py:282`),
`utils/inputs.py:1657` (attr-lenient input SHAPE probe — different
subject), `exceptions.py:103–106` (prose ABOUT the R4 walk —
projection, not a definition). Contract difference: different
subjects/rules sharing only the token. Freshness (WT/HEAD):
imports `3ea52b16` / `3ea52b16` (clean), inputs `0826c9d4` /
`0b7d353c`, exceptions `34e2e6be` / `7a4fb661`.
Reconsideration trigger: per subject — a second site sharing that
subject's own contract.

### R9 — resolver `hasattr` test-double fallback (excluded)

[resolvers][resolvers]`:417–426`: `if not hasattr(field,
"is_relation")` → build via the shared shape helper with
`is_relation=True` hard-coded. Contract difference: a PRESENCE
probe routing test doubles (which lack the attribute) to the shared
builder — not a read degrading on an unanswerable attribute; the
verdict is a build path, and production fields always carry the
attribute. Freshness (WT/HEAD): `b37b85d6` / `2c588030`.
Reconsideration trigger: the fallback starts containing raising
reads with a default verdict.

## Defects

### D1 Overtaken: the file item's coupled D3 (no family action)

- **What.** File `types/definition.py` D3 filed a hostile-truthiness
  escape: the `:319` truthiness test sat outside the `:315–318`
  read guard, so a field double whose `is_relation` VALUE had a
  raising `__bool__` escaped `related_target_for` raw — the one
  unreadable step of seven not degrading to `None`.
- **Overtaken, not fixed.** At WT bytes the filed shape cannot occur:
  the read guards are gone (bare `model_field.is_relation` at `:325`),
  the 7-arm fail-soft posture is gone with them, and the contract
  source — the "Every unreadable step of the target walk degrades to
  `None`, never an exception" oracle — is deleted from
  [test-def-rel][test-def-rel] (−140 lines, concurrent), whose
  docstring now pins the INVERTED contract ("a raising consumer
  `resolve_id_attr` propagating"). The maintainer's rewrite changed
  the method's contract from fail-soft to bare-read-with-propagation
  and updated the oracles in the same rewrite.
- **No new defect filed.** The bare-read posture is the maintainer's
  concurrent contract, established together with its oracles; there
  is no surviving contract source it breaks. Re-litigating it here
  would reverse concurrent work, not trace this family.
- **Owner.** Worker-0: retire the coupled D3 (or re-home if the
  closeout homing already recorded it — the coupling clause in
  F-RELTARGET/FAM-LENIENT is discharged by this finding).
- **Freshness.** Definition `e79d7129` / `ff80ef02`; oracles
  `fee20cf8` / `196e783d`.

No other defect found while tracing. The `_MISSING` sentinel,
`relation_name`, and the strict bodies were read in full; their
contracts match their docstrings at WT bytes.

## Pending execution

None. Every verdict is `static-reviewed` (symbol absence, body
comparison, AST-closed censuses, pinned oracles — inspection
decides; nothing ordering-, transactional-, or async-sensitive was
judged). No `proof:` entry: no failability probe exists for a rule
with zero sites. No `gate:` entry: zero-edit, no regression witness
needed. Sharded and PG cells are inapplicable by construction: the
traced surface is pure relation-metadata reads (attribute probes +
registry dict lookups), reaching no database, alias, or dialect
decision — stated for Worker-2 to judge.

## Judgment

REJECT-single-owned (zero definitions — a fortiori): the lenient
relation-metadata read has no surviving site package-wide. Both
nominated definitions were deleted by the maintainer's concurrent
truth-migration + `except BaseException` deletion rewrite, the
oracles were updated in the same rewrite to assert propagation, and
the whole-package censuses (68 three-arg `getattr` sites with 0
under `try`, 11 re-raising except sites, 0 `relation_attr` /
`safe_truthy` hits) close the population. The strict readers stand
single-owned under their verified families; every nearby shape is
excluded with a contract difference + trigger (R1–R9). Zero-edit,
no sub-rule rows named, one coupled defect retired.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for
verification). Item-scoped attribution vs
`ITEM_BASELINE=9f11157f0afcdee4a49dceed2255c291a42b7801`: `git diff
<baseline> -- django_strawberry_framework/utils/relations.py
django_strawberry_framework/types/definition.py` is empty — the
HEAD-vs-worktree dirt on both targets predates the baseline window
and was never touched; the artifact itself is a new untracked file,
the item's only output. The [plan][plan] `## Owned changes` ledger
gains no row from this item (no row names either target for this
item; verified by reading). No `uv run ruff` run (no `.py`
touched; `.md` is outside ruff format scope; the two census scripts
live in `/tmp`, outside the repo). No shared-tree pytest run (no
behavioral proof needs execution — see `## Pending execution`;
static review + pinned oracles suffice). No `docs/dry/temp-tests/`
scratch created. Three workspace runs at
`dry/lenient-f43/consolidate`, all green: `basedpyright` 0 errors /
0 warnings / 0 notes (`dry-20261001T180854-47d372`), `check_any`
128 uses at 89 sites exit 0 (`dry-20261001T180914-bbac29`),
`check_truthful_reads --check` tier-1 0 / errors 0 over 119 files
(`dry-20261001T180916-14cf8e`) — tree-state results, zero-edit item.
No new cast / `Any` / suppression (no code changed; `ALLOWED_ANY`
untouched). No commit. mypy never run, never cited.

Worker-0 instructions: (a) tick the plan item Family
`lenient-relation-metadata-read` as verified under Run `0.0.15
2026-10-01-11` once Worker 2 agrees; (b) transcribe the `## Responsibility index` row for
`lenient-relation-metadata-read` to
`rejected` with the F1 trigger (a second raising-read-containment
site on relation metadata reopens the family); (c) retire the
coupled File `types/definition.py` D3 per D1 above (or confirm its
closeout homing already recorded — either way the coupling is
discharged); (d) no `## Owned changes` row, no sub-rule rows.

## Independent verification (Worker-2)

Traced expectation-first at HEAD `dd0b6691` + WT bytes with my own
instruments (`/tmp/w2_census_*.py`, fresh greps — Worker-1's `/tmp`
scripts never opened) before reading `## Findings`.

### Own trace

- Nominated definition 1 (HEAD): [utils-relations][utils-relations]
  `::relation_attr` (+ `::safe_truthy`, + lenient `::relation_bool`)
  — confirmed present at `git show HEAD:` (`safe_truthy` :63,
  `relation_attr` :78, lenient `relation_bool` :113), deleted at WT.
- Nominated definition 2 (HEAD): [definition][definition]
  `::related_target_for` inline rungs (`getattr(...,
  "is_relation", False)` / `getattr(..., "related_model", None)`
  under `except BaseException` → default, plus 3 further arms) —
  confirmed at `git show HEAD:`, replaced by bare reads at WT
  (`model_field.is_relation` :325, `model_field.related_model`
  :326, typed `FieldDoesNotExist` → `None` only).
- HEAD lenient consumer: [join-taxonomy][join-taxonomy]
  `_safe_getattr` / `_safe_flag` / `_safe_truthy`
  (`lenient=True`, the only two such call sites package-wide at
  HEAD) — rewritten at WT to unguarded `_attr` / `_flag` /
  plain-truth `_first_truthy` ("nothing is guarded").
- Oracles: hostile doubles deleted and the contract inverted to
  propagation in the same rewrite ([test-def-rel][test-def-rel]
  −140 removed lines by content count, `pytest.raises(RuntimeError,
  match="resolver exploded")` now pins propagation;
  `tests/utils/test_relations.py` −208/+100 with every
  hostile-containment test deleted or renamed to the strict shape).
- Whole-package closure: no live lenient site under any spelling
  (censuses below). Owner I would choose: none — an extinct rule
  has no shared responsibility to own (principle 7 chooses among
  owners; zero definitions → no owner owed). Challenges: C1 0, C2
  0 (nothing implements the policy, so no site moves under any
  posited lenient change).

Reconciliation: full agreement with F1/R1–R9/D1 on every material
claim. Census-total deltas are instrument-list choices, all
reconciled below; none move the verdict.

### Census reproduction (all counts re-derived, never sampled)

- 68 three-arg `getattr` on W1's exact 18-name list: REPRODUCED
  exactly (68 hits, 20 files, 0 under `try`) with my own AST walk.
  My broader 18-name list (superset incl. generic `name`/`field`,
  97 hits) also yields 0 under `try` — closure holds under both
  instruments, so no spelling on W1's list was missed and the
  generic-name tail adds no lenient site.
- 11 `except BaseException`: REPRODUCED (auth/mutations ×4,
  operation_state ×3, resource_policy ×2, list_field, schema);
  every body read — all compensate/cleanup + re-raise, none on
  relation metadata, none answering a default.
- 23 strict call sites: RECONCILED exactly — 23
  `relation_bool` MENTIONS decompose to 19 call sites + def +
  `__all__` + import + docstring ref, and `relation_name` adds 4
  call sites: 19 + 4 = 23 strict CALLS in 2 files, 0 with a
  `lenient` argument (the parameter no longer exists on any
  signature). field_meta's 8 = 6 `relation_bool` + 2
  `relation_name`.
- 0-hit greps: `relation_attr` 0, `safe_truthy` 0,
  `_safe_getattr|_safe_getbool` 0 package-wide; live
  `relation_attr|safe_truthy` 0 in `tests/`/`examples/`/`scripts`;
  the only remaining tokens are frozen `head-tree` copies under
  another item's `docs/dry/temp-tests/` (not live code).
- Broader swallower sweep (my own, beyond W1's instruments): every
  non-reraising `except` in the package censused (~120); each
  relation-adjacent one classified by body as a different contract
  (path-existence `FieldDoesNotExist` typed catches incl. the R4
  walk, instance row-data reads, speculative serializer-shape
  probes, import/context/settings reads, FK-elision model
  instantiation). `truth.py` carries 0 `except` statements;
  `static_attr`/`own_attr` take 0 relation-name arguments
  package-wide.
- Population: 120 `.py` files, 0 unparseable, `__pycache__`
  excluded. join_taxonomy: 0 `try:`/0 `except`. Axis-2 token grep
  over the 5 reader modules: 0/0/0/0/0.

### Point (a): the extinction claim — CONFIRMED

HEAD-side nominated definitions confirmed via `git show HEAD:`;
their deletion + the −140 oracle inversion confirmed by WT-vs-HEAD
diff content; zero survivors confirmed by the reproduced censuses
plus the broader spelling sweep above. The verdict "F1 REJECTED
with zero surviving definitions" is re-derived, not inherited.

### Point (b): the D1/D3 overtaken-and-retire call — CONFIRMED

Read the File `types/definition.py` artifact's D3 + coupling
clause first-hand. D3's contract sources (the degrade-to-`None`
oracle rule, the 7-arm fail-soft posture, the owner's lenient
doctrine) were all deleted by the same rewrite; at WT bytes a
raising truth test propagates exactly like every other raising
step of the method, so no hole remains to fix and the filed fix
(adopt the lenient reader) would reintroduce the extinct policy.
"Overtaken" is right; nothing is still owed. The ticked File row
(plan :241) stays factually true and stays shut: it records a run-7
verification at blob `fa6c4d33` with D3 "pending closeout homing"
— closeout is exactly where retire-vs-home is decided, so the row
is satisfied by recording the retirement, not by homing live work.
The retirement must be recorded at closeout in the plan's
`## Outcomes` defects-homed section (naming D3 retired-per-f43-D1);
no prior line is edited. Worker-0 note: the File item's `fa6c4d33`
pin predates the concurrent rewrite (current HEAD blob
`ff80ef02`) — re-reconciliation scope is Worker-0's call; this
family item discharges the FAM-LENIENT transcription either way.

### Steps 2–7 checks

- Matrix: all six axes discharged against the rule's mechanism.
  Axis-2 inapplicability judged on its reason (sync-only reads,
  0 async tokens in all 5 reader modules — reproduced). Axis-5:
  oracles deleted, surviving `lenient` tokens homed (R4/R8),
  projections correctly left alone (committed hunt history +
  regenerable shadow output). Axis-6: absences are no-rule, not
  gaps — no contract source owes any member a lenient read.
- Roles: strict readers are the definition of different verified
  rules (listed, not counted); bare readers are R1-excluded
  omitted→default vocabulary; oracles deleted by concurrent work,
  none rewritten by this item.
- Zero-edit: item diff vs `9f11157f…` is the plan edit alone
  (Worker-0 dispatch + submission notes) plus the untracked
  artifact as the only new file (status count 494 = 493 + the
  artifact, HEAD unmoved). `git diff <baseline> -- <both indexed
  paths>` empty — reproduced. The −140 oracle rewrite is WT-vs-HEAD
  dirt predating the baseline window, confirmed concurrent by
  content. Independent consolidation search (above) finds no live
  site — nothing reopens the verdict.
- R1–R9: each carries a contract difference + trigger; homes
  verified against standing records: R2 → verified
  `relation-kind-taxonomy` (+ `relation-instance-accessor`, plan
  :1338–:1339); R4 → `orm-lookup-path-resolution` territory
  (verified + landed, plan :1317, ledger row present); R6 → FK-id
  elision family territory; R7 → the standing truthful-reads gate;
  R3/R5/R8/R9 → their in-module doctrines / named subjects / the
  R8 test pin (`tests/utils/test_inputs.py:282`, exists). R6's
  "none foreseeable — subject differs permanently" is an adequate
  trigger for a permanently-different subject. The J1
  per-site-arms direction is standing (6+ CONVERGE rows).
- Freshness: all 18 pins re-hashed same-kind
  (`git hash-object` WT vs `git rev-parse HEAD:`) — 18/18 exact,
  incl. dispatch pins relations `a6692e4d`/`e64a7a8f` and
  definition `e79d7129`/`ff80ef02`, plus untracked truth
  `711352b1` (WT-only, correctly fingerprinted as such).
- No-gate call: CORRECT. No owner exists to bypass, and a
  rule-stays-extinct census is exactly the bespoke existence test
  [dry][dry] forbids. The standing gate DOES pin the except-arm
  half of the nominated spelling: `check_truthful_reads.py`
  TR002 (tier-1, failing) forbids `except BaseException` swallow
  handlers, TR004 the `suppress()` twin. Nuance (verdict-neutral):
  an `except Exception` → default re-spelling would trip only
  tier-2 TR105 (heuristic, never failing) — but no such site
  exists (swallower sweep above), and the F1/R1 triggers reopen
  the family if one ever appears; the next cycle, not this item,
  owns that.
- Pending-None: CORRECT. Every verdict is `static-reviewed`
  (symbol absence, body comparison, AST-closed censuses, pinned
  oracles); nothing ordering-, transactional-, or async-sensitive
  was judged; no failability probe exists for zero sites, so no
  `proof:` is owed; zero-edit, so no `gate:` witness is owed.
  Plan item reads plain `verified`.
- Coupling: F1 names D1; D1 discharges the file-item coupling
  clause. Marked so neither lands alone — satisfied (both land
  in this verdict).
- Concurrency attribution: AGREED by diff content — the
  `classify_path` four-walkers paragraph is the ledgered adopted
  orphan (ledger row verified present, hunk untouched); all other
  relations.py hunks + all definition.py hunks + both oracle
  rewrites are the concurrent truth-migration/except-deletion
  work. No hunk unattributed; nothing edited/reverted/tidied.
- AGENTS.md prose: artifact carries no process provenance beyond
  DRY-authorized run-id records, `path::Symbol` citations
  throughout, no tests owed (zero-edit), link scaffold intact
  (all 10 canonical group headers present; trailing-comma
  `--check` exit 0, file excluded-and-clean). No banned-word
  violation (no new test/production code; `.md` hits are prose).
- Ruff: vacuous by observation — `ruff check` on the touched
  path reports "No Python files found / All checks passed".
- Type gates re-run by Worker-2 in the shared tree: basedpyright
  0 errors / 0 warnings / 0 notes; `check_any` 128 uses at 89
  sites, exit 0; `check_truthful_reads --check` tier-1 0 /
  errors 0 over 119 files (+1 exempt = 120). All match the run-11
  baseline. mypy never run, never cited.
- Sharded/PG `inapplicable by construction`: AGREED on its
  reason — the traced surface is attribute probes + registry
  dict lookups reaching no database, alias, or dialect decision.

### Defects

None found by Worker-2. No pending execution.

Verdict: `verified` (plain — no `proof:` entry remains).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[plan]: dry-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[definition]: ../../django_strawberry_framework/types/definition.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py
[truth]: ../../django_strawberry_framework/utils/truth.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-def-rel]: ../../tests/types/test_definition_relations.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
