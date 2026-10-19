# DRY review: `optimizer-hint-skip-predicate`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is the optimizer hint skip predicate: how SKIP-ness
is read and decided wherever hints gate planning. The owner candidate
from the plan, `optimizer/hints.py::hint_is_skip`, is re-derived below,
not inherited.

Traced at HEAD bytes (`5c3496e0`) through `git show HEAD:<path>` and
`git grep ... HEAD`. That instrument choice is load-bearing: all four
indexed files are dirty in the working tree with the concurrent
bug-hunt truth migration plus the maintainer `except BaseException`
deletions (none of it in the plan's `## Owned changes` ledger), and the
dirt touches the owner function itself (WT drops the HEAD
`try/except BaseException` around the attribute read -- hunt-owned,
verdict-neutral: it adds and removes no SKIP-ness read site). Every
line cited below is a HEAD line; every fingerprint is a HEAD blob
except the worktree/ITEM_BASELINE pins recorded for attribution. The
working tree equals ITEM_BASELINE (`5fed3b2a...`) on all four indexed
files, so every dirty hunk predates dispatch. Prior file/family
records were read as orientation and adjudicated fresh; nothing below
is inherited.

Sites found, by role. One definition; every planning gate composes it
by name.

- Definition. `django_strawberry_framework/optimizer/hints.py::hint_is_skip`
  (`:254`: `None` -> `False`, `is OptimizerHint.SKIP` -> `True`, else
  the `.skip` attribute read with a `False` default; the HEAD body
  additionally absorbs `BaseException` from a hostile attribute read,
  which the WT hunt hunk removes).
- Consumers. `optimizer/walker.py::_apply_hint` (`:1275`, first dispatch
  arm, returns handled); `optimizer/nested_planner.py`
  (`:1166`, relation-level gate returning an unplanned result before
  any queryset is built); `optimizer/extension.py::check_schema`
  (`:1554`, audit skip before the unregistered-target warning). Each
  call site passes `hints.get(name)` / the fetched hint straight
  through; no call site restates any arm.
- In-owner validation reads (same module, sibling-owned contract).
  `OptimizerHint.__post_init__` reads `self.skip` twice (`:178`,
  `:201`) to reject conflicting constructions. These validate the
  value being built; they never gate planning. The sibling
  `optimizer-hint-shape` family (f15, verified) owns that contract.
- Excluded reads (different decision, recorded under Findings, never
  absorbed). The walker presence gates (`:888` `is None`,
  `:904`-`:906` fetch-then-dispatch); the planner strategy read
  (`::_select_nested_strategy` `:224` via
  `getattr(hint, "nested_strategy", None)`, call site `:1426`, running
  strictly after the skip gate); the GraphQL `@skip`/`@include`
  directive reads in `optimizer/selections.py` (`:395`, `:438`-`:440`);
  the `SKIP`/`skip` mention comments carrying no read
  (`lateral_fetch.py:57`, `nested_fetch.py:8`, `filters/base.py:557`,
  `utils/querysets.py:4838`, `mutations/inputs.py:849`).
- Oracles. `tests/optimizer/test_hints.py::TestSkipPredicate`
  (None/sentinel/shape/unknown truth table, each verdict spelled as a
  literal); `tests/optimizer/test_extension.py` (predicate truth table
  `:4485` plus the audit B6 skip row `:2962`); `tests/optimizer/test_walker.py`
  (walker branch suppression `:1582`, primary SKIP `:2357`, window
  suppression `:4348`); `tests/types/test_base.py` (SKIP accepted as a
  hint value `:1260`); the live `test_library_api.py` non-sentinel
  `skip=True` row over `/graphql` on the shipped `LoanType` patron
  hint (`apps/library/schema.py:164`). Every oracle spells its own
  expectation; none reads the owner.
- Projections. The predicate docstring plus its two call-path comments;
  the consumer docstrings restating "SKIP" gating (`walker.py:1263`,
  `nested_planner.py:1008`, `extension.py:1508`-`:1514`); GLOSSARY,
  specs, KANBAN, and the `test_query/README.md` suite map.

Connected behavior examined: the sibling hint shape (f15, verified --
  the value contract this predicate reads), the sibling strategy
selection (`nested_fetch.py::resolve_strategy` plus
`StrategySelection`), the sibling hint dispatch
(`walker.py::_apply_hint` with its plan-time refusals), and the
sibling prefetch-lookups read. Each is excluded with a contract
difference under Findings, never absorbed; the f15 R3-R6 boundary
("predicate read vs shape") is confirmed exact, never re-litigated.

## Verification

### Matrix

1. Cross-flavor policy mirroring. SEARCHED, complete. No other public
   surface carries a per-field skip/override vocabulary: filters,
   orders, mutations, forms, and rest_framework hold per-subject
   records with no skip member, and the `skip=` hits in
   forms/rest_framework resolvers are unrelated filter lambdas. The
   only same-named rule is GraphQL `@skip` in `selections.py`, a
   per-selection directive evaluation with different inputs (directive
   arguments), a different subject (selection visibility, not plan
   gating), and different change reasons -- excluded in R4.
2. Sync/async twins. INAPPLICABLE with reason: the target has no async
   surface. The predicate is a pure synchronous function and all three
   call sites run in synchronous planning or schema audit; the only
   `async def`/`await` hits among the four indexed files live in
   `extension.py` subscription machinery the audit path never enters.
3. Derived rather than repeated knowledge. SEARCHED, complete. The
   HEAD-wide census finds exactly one `is OptimizerHint.SKIP` code
   site (inside the predicate), exactly two `.skip` attribute reads
   (both inside `__post_init__`, in-owner validation), and exactly
   three `hint_is_skip` call sites. No consumer rebuilds SKIP-ness
   from the sentinel, the flag, or the map; the strategy read touches
   a different field for a different decision.
4. Inverse / round-trip pairs. INAPPLICABLE with reason: SKIP-ness has
   no serialized form. Nothing encodes, packs, parses, or inverts a
   skip directive; the predicate is a one-way read.
5. Contracts restated in another medium. SEARCHED, complete.
   Production (the predicate), oracles (truth tables plus per-site
   skip-honored rows plus the live row), example declarations, and
   projections (docstrings, GLOSSARY/specs/KANBAN, suite map) are
   classified above; each medium moves for its own reason and only
   the production definition is counted.
6. Enforcement by omission. SEARCHED, complete. Every hint-gated
   planning path was enumerated and each consults the predicate before
   doing the work the skip must suppress: the walker checks the skip
   arm first inside `_apply_hint`; the planner gates at `:1166`
   before the queryset build and the `:1426` strategy read; the audit
   skips before warning. No planning path honors hints while bypassing
   the skip read, so there is no omission gap; the strategy-only read
   cannot observe a skipped relation because the gate runs first.

### Enumeration

Instrument: `git grep` censuses over HEAD blobs across all 117 package
`.py` files, plus a full HEAD read of `optimizer/hints.py` and region
reads of every file a hit implicates. Populations censused, not
sampled: `hint_is_skip` mentions (1 definition + 3 call sites + 3
imports + 1 docstring cross-reference, across exactly the 4 indexed
files); `is OptimizerHint.SKIP` (1 code site); `== OptimizerHint.SKIP`
(0); `.skip` attribute reads (2, both in `__post_init__`);
`hints_map.get` / `hints.get` planning reads (walker presence `:888`,
walker dispatch `:904`, planner skip `:1166`, planner strategy
`:1426`, audit `:1554`); `hints.items()` / `hints_map.items()`
iteration (0 production sites -- D1); `nested_strategy` reads (1, the
strategy sibling); `@skip` directive reads (1 module, excluded).
Every member lands in F1, an R-exclusion, or D1; nothing is
unassigned.

### Challenges

Each challenge posits a change on one of the rule's variation axes and
counts authoritative definitions that must move. Consumers, oracles,
and projections that also move are listed, never counted.

- C1 (absent-input axis): change what "no hint" means (None must raise
  instead of reading `False`). Moves only the predicate's None arm;
  all three call sites keep passing their `.get()` result through
  unchanged. Oracles spelling `None -> False` move as oracles.
  Count: 1.
- C2 (sentinel axis): drop the identity fast-path (dataclass equality
  makes `is SKIP` redundant) or replace the sentinel spelling. Moves
  only the predicate's identity arm; the call sites follow by name
  and the f15-owned sentinel assignment moves as the sibling shape.
  Count: 1.
- C3 (unknown-shape axis): unknown shapes must raise `AttributeError`
  instead of reading `False` (narrow the audit's never-raises
  contract). Moves only the getattr-default arm; the oracles pinning
  `object() -> False` move as oracles. Count: 1.
- C4 (read-vs-application separation control): change a planning
  effect of SKIP (the audit must warn despite SKIP; the walker must
  record a marker for skipped relations). Moves only the affected
  consumer; the predicate and the other two consumers move nowhere.
  This confirms the intentional separation between the read this
  family owns and the plan effects the dispatch sibling owns.

All counts are 1. No posited change moves two definitions of one
contract.

## Findings

### F1: the skip predicate is single-owned at `hint_is_skip` (CONFIRM single ownership)

Contract + variation: one read deciding SKIP-ness for every hint-gated
planning path -- `None` (no hint configured) reads `False`, the
`SKIP` sentinel reads `True` by identity, any other value reads its
`.skip` attribute with a `False` default so a shape that does not
carry the attribute reads `False` rather than raising. Varies on the
absent-input, sentinel, and unknown-shape axes (C1-C3).

Sites + roles: definition `optimizer/hints.py::hint_is_skip`;
consumers compose by name (walker skip arm, planner relation gate,
audit skip); oracles spell verdicts independently (truth tables,
per-site skip-honored rows, the live non-sentinel row); projections
describe (docstrings, GLOSSARY/specs/KANBAN, suite map).

Challenges: C1-C3 count 1 definition each; C4 confirms the
read-vs-application separation. Consumers, oracles, and projections
that move with an intentional contract change are listed in each
challenge, never counted.

Owner + lifetime: `optimizer/hints.py::hint_is_skip` by responsibility
(principle 7): the narrowest module holding the shape it reads, which
every legitimate consumer already imports downward with no reversal,
so one edit moves the whole read. No stored derivation: a pure
function of its argument with no cache, no publish point, and no
invalidation.

Migration: none owed; every site already composes the owner by name.

Distinct behavior: the hint value contract (sibling shape), strategy
resolution (sibling selection), plan-time application (sibling
dispatch), and Prefetch-lookup derivation (sibling lookups) stay
outside; R1-R7 record each boundary.

Behavioral proof: static-reviewed. Nothing moves, so no equivalence
proof is owed; the census (one predicate, one identity site, three
by-name call sites) plus the challenge counts decide the verdict. The
oracles that would catch a behavioral drift already exist in-tree
(the `TestSkipPredicate` truth table, the three per-site
skip-honored rows, the live non-sentinel row).

Structural gate: no new gate owed, and the rule currently holds (the
HEAD census above is the first-run check). The plausible bypass is a
fourth planning gate inlining the `is SKIP` / `.skip` read; all three
existing gates compose the documented helper by name, including the
most recent (the planner gate), so the bypass has no precedent, and a
bespoke per-helper existence test is the forbidden shape. The
in-tree oracles pin both verdicts of the contract (skip honored at
all three sites, non-skip planned normally) independently of the
owner's spelling.

Coupling: none. No defect blocks landing because nothing lands.

Freshness: input pins under Judgment; any fingerprint change reopens
the finding.

### Rejections and exclusions (contract difference + trigger each)

- R1. The f15 hint shape (`OptimizerHint`, sentinel, factories,
  `__post_init__`). Verified sibling `optimizer-hint-shape`.
  Difference: the value contract being read (fields, defaults,
  construction-time conflict rejection) versus the read itself; the
  predicate validates nothing and constructs nothing. The f15 R3
  boundary ("predicate read vs shape") is confirmed exact against the
  bodies. Trigger: `skip` leaves the record (the predicate has
  nothing left to read).
- R2. Strategy selection (`resolve_strategy` plus `StrategySelection`
  plus the planner `_select_nested_strategy` read). Queued sibling
  `nested-connection-strategy-selection`. Difference: which fetch
  scheme serves a connection (name-to-instance resolution with a
  plan-time default fallback) versus whether the relation is planned
  at all; the strategy read touches a different field and runs
  strictly after the skip gate. Trigger: one decision starts
  answering the other's question (a strategy value that means skip).
- R3. Hint dispatch (`walker.py::_apply_hint` beyond its skip arm).
  Queued sibling `optimizer-hint-dispatch`. Difference: plan-time
  application with plan-time refusals (to_attr, many-side
  select_related, pk-set rewrite) versus the skip read the dispatch
  consumes by name as its first arm; C4 moves each alone. Trigger:
  dispatch stops calling the predicate and inlines the read.
- R4. Prefetch-lookup derivation (reads off the hinted `Prefetch`
  object). Queued sibling `attached-prefetch-lookups-read`.
  Difference: lookup strings derived from the carried `Prefetch`
  object versus SKIP-ness of the hint carrying it. Trigger: lookup
  derivation starts branching on skip.
- R5. The `__post_init__` `self.skip` reads. In-owner construction
  validation, sibling-shape contract. Difference: rejecting an
  invalid value being built (same module as the predicate, owned by
  f15) versus gating planning on a landed hint; no planning path
  consults these arms. Trigger: a planning gate starts importing a
  validation arm instead of the predicate.
- R6. The walker presence gates (`hints_map.get(...) is None`). Same
  file, dispatch-owned. Difference: whether a hint is configured at
  all (routing to cardinality dispatch) versus whether the configured
  hint is a skip; presence moves alone under "unhinted relations
  change default" and skip moves alone under C1-C3. Trigger: absence
  starts meaning skip.
- R7. GraphQL `@skip`/`@include` in `selections.py`. Difference:
  per-selection directive evaluation over directive arguments versus
  per-relation plan gating over `Meta` hints; different inputs,
  subject, and change reasons. Converges with the standing hints-R6
  rejection, checked fresh. Trigger: the two vocabularies merge into
  one skip spelling.

Convergences checked fresh, none re-litigated: f15 R3-R6 (all four
name real queued/open plan rows and each contract difference matches
the bodies read); the hints-file R-6 `@skip` rejection; the planner
row's windowed SKIP/strategy split (the gate-then-read order
`:1166`-before-`:1426` is the split made mechanical). No new index
rows are owed: the family row exists, the four siblings are queued,
and every R-exclusion above is a boundary, not a family.

## Defects

- D1 (minor, doc-only, HEAD defect, owner `optimizer/hints.py`): the
  `hint_is_skip` comment claims "the walker usually receives concrete
  hint values from `hints.items()`", but no production site iterates
  a hints map -- the walker fetches per name via
  `hints_map.get(django_name)` and passes a non-None hint into
  `_apply_hint`. The audit half of the comment (probing `.get` for
  every exposed relation) matches its body. Verdict-neutral (the
  predicate body and all three call sites are as censused); routed
  for closeout homing, unfixed per method.

No already-ticked row was found factually wrong: the run-5 naming
(owner candidate, four indexed files) matches HEAD, and the blob
drift since is typing plus the truth/hardening migration with no
second SKIP-ness read, so per the drift rule nothing reopens.

## Pending execution

None. The verdict is static-decidable (definition counts from source
census plus challenges); no equivalence proof is owed because nothing
moves. No pytest ran: executing oracles can only confirm the suite is
green, which proves nothing about definition count. The entry's one
authorized focused test was not spent. No workspace copy was created
(no source-mutating proof ran); census probes were read-only greps
plus source reads in the shared tree. The `--cell sharded` and
`--cell pg` cells are inapplicable by construction: the target
reaches no database, alias, or dialect decision (a pure in-memory
predicate plus three synchronous call sites; the PG-marked live
strategy rows pin sibling fetch behavior with hints as input, and no
claim here depends on their execution).

## Judgment

The optimizer hint skip read is already one rule in one body:
`optimizer/hints.py::hint_is_skip` holds the None/sentinel/attribute
decision, and the walker, the nested planner, and the schema audit
each compose it by name at the exact point where their SKIP-ness
verdict is needed. Everything that looks like a second definition is
the sibling value contract being read (R1), a different field read
for a different decision (R2), the plan-time application consuming
the read (R3), derivation off the carried object (R4), in-owner
construction validation (R5), a presence gate (R6), or the unrelated
GraphQL directive (R7). CONFIRM single ownership, zero edits, no new
index rows owed.

Type gates (shared venv, tree-state -- zero edits, so these record
the concurrently-dirty tree, not a change): `uv run mypy` clean (119
files), `uv run basedpyright` 0 errors / 0 warnings / 0 notes, `uv run
python scripts/check_any.py` 130 uses at 90 sites (matches the run-9
baseline).

Freshness (full input pins; `git hash-object` WT vs `git rev-parse
HEAD:path`; HEAD `5c3496e0`; ITEM_BASELINE
`5fed3b2aaef8487fee0bc1b19f7209083df010c3` equals WT on all four
indexed files):

- Indexed 4: `optimizer/hints.py` WT `ee68ae03` HEAD `f6776564`;
  `optimizer/walker.py` WT `4fd8077f` HEAD `13e1be20`;
  `optimizer/nested_planner.py` WT `b6ff0a0e` HEAD `8c3a45f5`;
  `optimizer/extension.py` WT `8e3fe7c1` HEAD `b7b6c434`.
- Read neighbors (HEAD): `__init__.py` `8b165672`;
  `optimizer/_context.py` `274a138b`; `optimizer/field_meta.py`
  `7c9afe35`; `optimizer/join_taxonomy.py` `8026dc8d`;
  `optimizer/lateral_fetch.py` `a48cb0a4`;
  `optimizer/nested_fetch.py` `bedaa76e`; `optimizer/plans.py`
  `97a524e2`; `optimizer/predicates.py` `965d1282`;
  `optimizer/selections.py` `f49ea7fa`;
  `optimizer/single_parent_fetch.py` `3a4bb89b`;
  `filters/base.py` `6b952d4d`; `mutations/inputs.py` `d11b8745`;
  `types/base.py` `e8416cc0`; `types/definition.py` `fd339a7c`;
  `utils/querysets.py` `69ac3ea3`.
- Oracles/examples (HEAD): `tests/optimizer/test_hints.py` `d3e413bd`;
  `tests/optimizer/test_extension.py` `9d57709f`;
  `tests/optimizer/test_walker.py` `ca5c32d7`;
  `tests/types/test_base.py` `0d070aee`;
  `examples/fakeshop/apps/library/schema.py` `75d358f8`;
  `test_query/test_library_api.py` `91f0238b`;
  `test_query/README.md` `43ca1251`.
- Searched population: all 117 package `.py` files via HEAD greps
  (predicate, sentinel, attribute-read, map-read, iteration,
  strategy-read, directive, and async censuses above); every other
  package module is excluded on the strength of its census silence
  for this mechanism.

## Independent verification (Worker-2)

Recorded BEFORE reading `## Findings` (sections `## System trace`,
`## Verification`, `## Findings`, `## Defects`, `## Pending execution`
unopened at write time; `## Judgment` + the dispatch brief's claim
summary seen, so shape-level contamination is possible and the
reconciliation below re-checks every claim against fresh bytes rather
than W1's prose). Instruments: WT greps over all 117 package `.py`
files for `hint_is_skip`, `\.skip\b`, `SKIP`, `@skip`, `hints.items`,
`hints_map.get`, `hints.get`, `getattr.*skip`, `nested_strategy`;
`git show HEAD:<path>` / `git grep HEAD` cross-checks for every cited
site; full read of `optimizer/hints.py` WT.

### Own trace (WT bytes, HEAD cross-checked)

Posited rule: the SKIP-ness read - given one hint-map value (or the
absence of one), decide "skip this relation".

- **Definition (count 1)** -
  `django_strawberry_framework/optimizer/hints.py::hint_is_skip` (WT
  lines 253-268; HEAD lines 254-272, body differs by concurrent dirt,
  see below). WT decision: `None` -> `False`; `is OptimizerHint.SKIP`
  -> `True`; else `bool(getattr(hint, "skip", False))`. HEAD adds a
  `try/except BaseException -> False` around the attribute arm plus a
  longer docstring. Single body at both states; the dirt changes the
  owner's text, not the count.
- **Consumers, all by name (count 3, identical set at HEAD)**:
  1. `optimizer/walker.py::_apply_hint` line 1277 (HEAD 1275):
     `if hint_is_skip(hint): return True`. Reached only for non-None
     hints: caller gates `hint = hints_map.get(django_name)` then
     `if hint is not None` (WT 906-907; HEAD 904 + same gate), with
     `hints_map` from `_resolve_optimizer_hints` (WT 740). The
     predicate's `None` arm is dead on this path by construction.
  2. `optimizer/nested_planner.py` line 1176 (HEAD 1166):
     `if hint_is_skip(hints_map.get(relation_field_name)): return
     NestedConnectionPlanResult(plan=plan)`. Passes possibly-`None`
     straight through, so the `None` arm is load-bearing here.
  3. `optimizer/extension.py::check_schema` line 1543 (HEAD 1554):
     `if hint_is_skip(hints.get(field_name)): continue`. Schema audit;
     possibly-`None`; its never-raises contract depends on the
     `getattr`-default arm.
- **Oracles (independent, literal expectations)**: 
  `tests/optimizer/test_hints.py::TestSkipPredicate::test_skip_shapes`
  and
  `tests/optimizer/test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes`.
  Both spell `None`/`SKIP`/record/`object()` expectations without
  reading the owner. Behavioral oracles at
  `tests/optimizer/test_extension.py` line 2962 (SKIP suppresses audit
  warning) and `tests/optimizer/test_walker.py` line 1582 (SKIP
  suppresses branch) exercise two of the three consumers end to end.
  No test restates the predicate body; `test_hints.py` `.skip`
  attribute asserts are shape asserts on the record, not a second
  skip-decision.
- **Projections**: SKIP mentions in `nested_fetch.py`, 
  `lateral_fetch.py`, `nested_planner.py` docstrings describe the
  refusal arm; they decide nothing.
- **Exhaustiveness**: package-wide grep finds no other production
  `hint_is_skip` call, no other `getattr(..., "skip", ...)` (sole
  site: `hints.py` WT 268), no `is/== OptimizerHint.SKIP` outside the
  owner, no `.skip` attribute read outside the owner +
  `__post_init__` + tests. `utils/querysets.py` line 3045
  `orig_hints.items()` is DB-routing hints, a different population.

### Rejections derived independently (before reading W1's R1-R7)

- **J1 - Meta value-type validation** (`types/base.py` WT 1568,
  HEAD 1575): `hints.items()` iteration rejecting non-`OptimizerHint`
  values at type-build time. Different contract (admission: every
  value must be the record type) vs the read (one value's
  SKIP-ness). Trigger: Meta validation starts branching on
  per-value skip semantics rather than the value type.
- **J2 - strategy read** (`nested_planner.py::_select_nested_strategy`
  WT 225-240, HEAD 224+): reads the DIFFERENT field
  (`nested_strategy`, `getattr` with default, `None`-tolerant) for the
  DIFFERENT decision (which fetch strategy object, not a bool).
  Same call shape, disjoint field + disjoint return contract.
  Trigger: skip and strategy merge into one tri-state read.
- **J3 - sibling-shape application** (`walker.py::_apply_hint`
  `prefetch_obj`/`force_select`/`force_prefetch` arms): plan-time
  application consuming sibling fields AFTER the skip read returns
  `False`. Consumer of the read's negative outcome, not a second
  read. Trigger: a sibling arm starts re-testing SKIP-ness instead
  of trusting the earlier return.
- **J4 - `to_attr` derivation** (`walker.py::_apply_hint`, 
  `getattr(hint.prefetch_obj, "to_attr", None)`): derivation off the
  CARRIED `Prefetch` object enforcing the consumer-assigned
  attribute contract. Different object, different decision.
  Trigger: the attribute contract moves onto the hint record
  itself.
- **J5 - construction validation** (`hints.py::OptimizerHint.__post_init__`
  WT 177-208): in-owner BUILD-time rejection of conflicting flag
  combos (`skip` + force/prefetch/strategy). Admission vs read;
  folding it into the predicate would move build-time errors to
  query time. Trigger: the read must tolerate conflicting shapes.
- **J6 - presence gates** (walker WT 890/906-907 `hints_map.get(...) is
  None`): presence ("enter `_apply_hint` at all") vs SKIP-ness.
  Note the deliberate asymmetry: walker pre-gates `None` while the
  planner and audit pass `None` through to the predicate's `None`
  arm - two heterogeneous call contexts sharing one read.
  Trigger: the walker drops its gate and relies on the predicate's
  `None` arm (then the gate row evaporates; count still 1).
- **J7 - GraphQL `@skip`/`@include`** 
  (`selections.py::should_include` WT 424-448, HEAD 422+): evaluates
  converted-selection directive payloads per GraphQL spec. Disjoint
  population (AST directives vs hint records), disjoint contract
  (response inclusion vs optimization opt-out). No plausible merge
  trigger; coupling them would tie optimizer internals to spec
  semantics.

### Challenges (definition counts, owner = `hints.py::hint_is_skip`)

- **C1 - fourth SKIP-ness input shape** (e.g. a string alias or second
  sentinel): one new arm inside `hint_is_skip`; all three call
  sites pass values through unchanged. Count 1. (`types/base.py`
  admission would also move to admit the shape - a sibling-contract
  update, not a second skip definition.)
- **C2 - fold the predicate into the container gate** (pre-filter the
  hints map, or inline the `None`/sentinel/attribute dispatch at
  each caller): forces 3 coordinated caller edits + owner deletion
  for zero change-obligation relief, against heterogeneous call
  contexts (pre-gated vs pass-through `None`). Not landable as a
  consolidation; count stays 1 by refusing the fold.
- **C3 - per-caller skip override** (e.g. audit warns even on SKIP,
  walker force-plans despite SKIP): lands as a caller-side adapter
  (`if not override and hint_is_skip(...)`), owner untouched.
  Count 1 + 1 legitimate adapter (principle 7: distinct decisions
  stay at adapters).
- **C4 - rename/invert the `.skip` attribute**: the `getattr` arm in
  `hint_is_skip` + the `__post_init__` field + `SKIP` construction
  move together inside the one owner module (one edit region);
  call sites unchanged. Count 1.

### Owner choice (principle 7, re-derived)

`optimizer/hints.py::hint_is_skip`. The module already owns the
hint-shape contract (record, `SKIP` sentinel, factories,
construction validation); all three consumers already import from
it with no cycle; it is the narrowest cohesive owner every
legitimate consumer can depend on without reversing a dependency.
No other candidate: the walker cannot own a rule the schema audit
needs (audit must not import walker machinery), and the planner
sits beside - not above - both.

### Matrix (own discharge, before reading W1's)

1. Cross-flavor: optimizer-only rule; package grep shows no
   types/filters/orders/mutations/forms/rest mirror of SKIP-ness.
   Discharged by search.
2. Sync/async: pure synchronous predicate, no awaits, no twin.
   Inapplicable by construction (no async surface).
3. Derived knowledge: single `getattr(hint, "skip", ...)` site;
   no second derivation. Discharged by search.
4. Round-trip: no encode/decode pair for a bool read.
   Inapplicable by construction.
5. Other media: oracles spell literals (independent); doc
   mentions are projections. Discharged by read.
6. Enforcement by omission: census of skip consumers = exactly
   the 3 by-name call sites; no direct `.skip` read outside the
   owner. Discharged by search.

### Reconciliation (read `## Findings` + all other W1 sections after recording the above)

- **F1 count-1 + owner: CONFIRM.** Own trace agrees on every
  member: 1 definition, the same 3 by-name consumers (walker
  `:1275`, planner `:1166`, audit `:1554` at HEAD; WT `:1277`,
  `:1176`, `:1543`), same principle-7 owner. W1's C1-C3
  (absent/sentinel/unknown axes) and my C1-C4 (fourth shape,
  container-fold, per-caller override, rename) all count 1; the
  three stress axes the brief requires are covered by my C1-C3.
  No landable consolidation exists: the fold (my C2) forces 3
  coordinated caller edits for zero relief against heterogeneous
  `None` contexts, and the override (my C3) is a legitimate
  caller adapter, not a second definition.
- **R1-R7: each CONFIRMED** (contract difference + trigger check
  out against the bodies): R1 shape-vs-read, R2 strategy
  (different field, runs after the gate - verified order
  `:1166`-before-`:1426` at both states), R3 dispatch
  application, R4 carried-object derivation, R5 in-owner
  validation, R6 presence-vs-skip, R7 GraphQL directive. Map to
  my J1-J7 one-for-one in substance (my J1 names the Meta
  validation site explicitly; see D1 correction).
- **Matrix: CONFIRM discharge**, with one scratch cross-ref slip
  noted: axis 1 cites "excluded in R4" for `@skip`, but the
  directive exclusion is R7 (R4 is prefetch-lookup derivation).
  Verdict-neutral scratch prose; not spent.
- **D1: routing + verdict-neutral CONFIRMED, supporting census
  CORRECTED (Worker-2).** The defect's core stands: the
  `hint_is_skip` comment's walker half ("receives concrete hint
  values from `hints.items()`") is false at both HEAD and WT -
  the walker fetches per name (`hints_map.get(django_name)`,
  WT `:890`/`:906`, HEAD `:888`/`:904`) and only non-`None`
  values reach the predicate; the audit half matches its body.
  Owner `optimizer/hints.py` is correct (owns the comment) and
  verdict-neutral is correct (doc-only). BUT the supporting
  sentence "no production site iterates a hints map" (repeated
  in `### Enumeration` as "`hints.items()` iteration (0
  production sites)") is factually overbroad: 
  `types/base.py::_validate_optimizer_hints` iterates the Meta
  hints map in production (WT `:1568` `hints.items()` value-type
  admission; HEAD `:1575`; plus key iteration WT `:1548`/`:1558`
  via `set(hints)`). Corrected scope for closeout homing: no
  production site iterates a hints map *to feed a skip
  decision*; the walker specifically fetches per name. The
  missed site is my J1 - sibling admission contract owned by
  consolidated f15 ("container enforces value type") - not a
  skip read, so F1's count, the owner, and "no new index rows
  owed" are all unaffected. (`utils/querysets.py:3045`
  `.items()` is DB-routing hints, a different population, and
  does not falsify even the unscoped sentence under its plain
  "hints map" reading for optimizer hints.)
- **Enumeration counts: CONFIRM except the iteration row**
  (corrected to 1 production site, excluded as J1/R1-boundary
  as above). All other populations re-censused fresh and match:
  1 definition + 3 call sites + 3 imports, 1 `is SKIP` code
  site, 0 `== SKIP`, 2 `.skip` reads in `__post_init__`, 5
  planning `.get` reads, 1 `nested_strategy` read, 1 directive
  module.
- **No new index rows owed: ENDORSED.** Family row exists
  (plan `:382`); all four named siblings are rowed
  (`optimizer-hint-shape` consolidated; 
  `nested-connection-strategy-selection`,
  `attached-prefetch-lookups-read`, `optimizer-hint-dispatch`
  open); J1 lives inside f15's consolidated value contract.
- **Pending-"None": CORRECT → plain `verified`.** Static-decidable
  (counts from census + challenges); nothing moves so no
  `proof:` is owed; the focused test is correctly unspent and
  no workspace copy was needed (read-only probes only).
- **Cells inapplicable by construction: CONFIRM.** Pure
  in-memory predicate + three synchronous call sites; no
  database, alias, or dialect decision on the target path.
- **Structural gate: ADEQUATE.** No new gate owed; first-run
  check shown (HEAD census); the three per-site skip-honored
  oracle rows verified to exist (audit B6
  `test_extension.py:2962`, walker `test_walker.py:1582`,
  planner `test_fallback_not_planned_skip_hint` window
  suppression), pinning both verdicts independently of the
  owner's spelling. Bespoke existence test correctly refused.
- **No-ticked-row-wrong: AGREE.** Run-5 naming matches HEAD;
  HEAD-vs-WT dirt (typing + truth migration + the WT removal
  of the `except BaseException` arm) adds and removes no
  SKIP-ness site - verified by census at both states.
- **Freshness: pins present and comparable.** Re-hashed: 4/4 WT
  pins match dispatch (`ee68ae03`, `4fd8077f`, `b6ff0a0e`,
  `8e3fe7c1`); 5/5 HEAD spot-checks match W1's pins
  (`hints.py` `f6776564`, `selections.py` `f49ea7fa`,
  `types/base.py` `e8416cc0`, `test_hints.py` `d3e413bd`,
  `test_extension.py` `9d57709f`); live library row confirmed
  (`apps/library/schema.py:164`, `test_library_api.py`
  carries `skip=True` rows).
- **Zero-edit checks (all re-verified):** no `## Implementation`
  section; item diff vs ITEM_BASELINE `5fed3b2a…` is the plan
  edit alone (`git diff … --name-only` → 
  `docs/dry/dry-0_0_15.md` only); `git status --short` count
  464 with the f16 artifact untracked; WT equals ITEM_BASELINE
  on all four indexed files (every dirty hunk predates
  dispatch, concurrent hunt/typing work, attributed by
  content).
- **AGENTS.md prose rules:** tracked diff is empty (nothing to
  check citations/provenance/tiers against); artifact is
  per-cycle scratch (raw `path:NN` allowed). Ruff on touched
  tracked paths: VACUOUS (zero-edit, no touched tracked paths;
  no repo-wide run - concurrent dirt out of scope). Type gates
  re-run whole-package in the shared venv (slots 1-3 damaged
  per brief; no workspace copy exists for this item):
  `uv run mypy` clean (119 files), `uv run basedpyright` 0
  errors / 0 warnings / 0 notes, `uv run python
  scripts/check_any.py` 130 uses at 90 sites - all match W1's
  record.
- **W2 defects:** none. No production defect found; the D1
  census correction above is recorded here, not under
  `## Defects`, and changes no homing except the corrected
  scope sentence Worker-0 should carry.

Verdict: `verified` (plain - no `proof:` correctly remains).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
