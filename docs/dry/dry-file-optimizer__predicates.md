# DRY review: `optimizer/predicates.py`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

Target: [predicates][predicates] (174 lines, blob `4e87c733`,
worktree == `HEAD` == `ITEM_BASELINE`; target worktree-clean confirmed
three ways: `git status --short -- <item paths>` empty,
`git diff HEAD -- <target>` empty,
`git diff <ITEM_BASELINE> -- <target>` empty, all at `HEAD bfaee91d`).

What the target owns: the row-preserving to-many predicate primitive. A
caller builds a predicate body against `correlated_inner_root(queryset)`
(an unevaluated, pk-correlated inner root) and attaches it with
`attach_exists(queryset, inner)` (one `.alias()` + a returned positive
`Q(<alias>=True)` the caller applies). The module builds NO predicate
bodies, does NO `OR` grouping, never calls `.filter()` / `.exclude()` /
`.distinct()` on the outer queryset. Predicate meaning stays with the
callers: the FilterSet flat-leaf applicator
(`filters/sets.py::FilterSet._apply_flat_leaves`, the only production
caller: import + 2 call sites, consumed by name, never restated) and the
search-fields feature (`spec-060`, same-value disjunctions built
caller-side). Full body read; connected sources read at worktree:
[filters-sets][filters-sets] applicator + `_apply_related_constraints`
(`pk__in` sibling) + tree composer (`Q(pk__in=...)` per branch),
[exceptions][exceptions] guard catalog, [orders-sets][orders-sets]
`_dst_order_` alias grammar, [nested-fetch][nested-fetch] combinator
refusal, [write-tx][write-tx] + [rf-resolvers][rf-resolvers]
`_base_manager` readers, [lateral-fetch][lateral-fetch] +
[plans][plans] annotation-namespace readers. Oracles read:
[test-predicates][test-predicates] (11 tests) + live SQL-shape pins in
`examples/fakeshop/test_query/test_library_api.py` (2 tests, cited by
the oracle module docstring). Projections read: module docstring
(contract + 5 intentional-separation clauses), `spec-060-search_fields`,
`docs/row-preserving-predicates-part1-plan.md` (Slice B: this module's
enactment record). Prior records used as triggers only, re-verified:
[filters-sets-artifact][filters-sets-artifact] (predicates consumed by
name) and [exceptions-artifact][exceptions-artifact] (3 guards as
`OptimizerError` coherence) — both claims re-derived below, nothing
inherited.

`## Owned changes` ledger check: no row names `optimizer/predicates.py`,
`tests/optimizer/test_predicates.py`, or the artifact path (ledger holds
the walker D1 fix, gate-only pins, and docstring trigger clauses on
other families). Concurrent work noted, untouched (zero edits owed):
`filters/sets.py` carries a staged operator-bag hunk (~line 2357,
worktree `4a40e51b` vs `HEAD 4ab65a26`, far from the predicate call
sites at ~3028-3041); every claim below was read at worktree and holds
independently of that hunk.

## Verification

### Matrix

Each axis discharged against the target's real surface (117 `.py`
package population, census per axis):

1. **Cross-flavor mirroring.** Searched all six public surfaces for a
   second row-preserving predicate compiler. `Exists(` producers
   package-wide: this file (code) + [filters-sets][filters-sets] line
   3006 (docstring prose `Exists(none) == False`, projection, not code).
   `OuterRef(` producers: this file only. `.alias(` call sites: this
   file only (`orders/sets.py` builds an `annotations` dict it passes
   to `annotate()`, a different mechanism — see R1). Orders to-many
   handling is `Min`/`Max` aggregate annotations (row-preserving by
   aggregation, not by existence test — distinct contract). Forms,
   rest_framework, mutations, types carry no predicate compiler. One
   production consumer total (`_apply_flat_leaves`). No mirror.
2. **Sync/async twins.** Zero `async def` in the target; all four
   functions are pure ORM-object construction (no I/O, no await
   points). The sole caller `_apply_flat_leaves` is sync-only (single
   `def`, called from sync `filter_queryset`; the async write path
   reaches it through the consolidated one-sync-boundary, never a
   second predicate body). No twin.
3. **Derived, not repeated.** The alias is recomputed from the live
   queryset on every attachment (`_next_reserved_alias` reads
   `_effective_alias_names(queryset)` per call — pure derivation, no
   cache, no lifetime to name per principle 4). The db-alias pin is
   read off the outer queryset (`queryset.db`), never re-derived from
   the router at attach time; the mismatch guard snapshots both
   resolutions before comparing (message formatted from snapshots —
   proven by `test_alias_mismatch_message_reports_the_compared_values`).
   No second derivation site.
4. **Inverse / round-trip pairs.** `attach_exists` returns
   `(new_queryset, Q(<alias>=True))`; boolean placement (caller-side
   `.filter(positive)`, negation inside the caller's original
   invocation via `split_exclude`) is deliberately caller-owned per the
   module docstring's "No `negated` parameter" clause. No decode half
   exists in this file; the `Q` has no parser twin to diverge from.
5. **Contracts in another medium.** Production (1 def site per rule) /
   oracles ([test-predicates][test-predicates] 11 tests spelling
   behavior literally, never importing privates except the two
   underscore helpers it pins by contract; 2 live SQL-shape tests) /
   projections (module docstring, `exceptions.py` guard catalog lines
   409-414, spec-060 + part1-plan prose, pg-explain doc). Roles
   tagged per finding; oracles never read the owner they check (the
   alias tests assert emitted SQL / `cond.children` literals).
6. **Enforcement by omission.** The three `attach_exists` guards run on
   the single entry path — there is no second entry and no empty/no-op
   input by construction (identity short-circuits live in the caller,
   documented on BOTH sides: here + `_apply_flat_leaves` docstring).
   Family enumerated (model states × db aliases × combinator
   present/absent) and each member checked: no partial enforcement.
   The caller's identity-skip is deliberate delegation with a stated
   reason (tautological `EXISTS` avoidance + restrictive-empty
   `in: []` semantics), not a gap — no contract source demands the
   skip live here.

### Enumeration

Instrument: `ast` parse of `ast.Module.body`
(`docs/dry/temp-tests/dry-file-optimizer__predicates/probe_enumeration.py`,
`ENUMERATION-OK`). Count: **11** top-level statements = module
docstring + 2 imports (`annotations`, `TYPE_CHECKING`) + 1 Django
import (`Exists, OuterRef, Q`) + 1 `OptimizerError` import + 1
`TYPE_CHECKING` guard + **1 module constant**
(`_RESERVED_ALIAS_PREFIX`) + **4 function defs** (all sync, no async).
Rule-bearing members (6): the docstring contract/projection + the
constant + the 4 defs. Imports/guard carry no rule. Every rule-bearing
member lands below: F1 (2 defs, one family) | FL1 (constant + 2 defs,
one file-local kit) | R1–R5 (rejections of predicate-adjacent rules
noted anywhere, each re-verified, never inherited).

### Challenges

Change challenges with definition counts (consumers, oracles,
projections listed, never counted). Singularity census:
`docs/dry/temp-tests/dry-file-optimizer__predicates/probe_singularities.py`
(`SINGULARITY-OK`, 117-file population): one `def` site package-wide
for each of `correlated_inner_root`, `_effective_alias_names`,
`_next_reserved_alias`, `attach_exists`; one `_RESERVED_ALIAS_PREFIX`
assignment; `OuterRef(` produced only here.

- **C1 — new correlation shape** (e.g. a relation whose correlation
  cannot ride `pk`, or a composite-pk compilation change): moves
  `correlated_inner_root` only. Count **1**. Consumers also moving
  (not counted): `_apply_flat_leaves` (passes the root through
  unchanged), oracles (`test_composite_pk_correlation_executes_on_composite_fixture`
  pins the single `pk=OuterRef("pk")` term structurally +
  executionally). Allocator/attach untouched (allocator reads only the
  outer namespace; attach never inspects the correlation term).
- **C2 — new caller-contract violation** (e.g. a 4th guard such as a
  sliced-outer or `values()`-projectioned outer): moves `attach_exists`
  only. Count **1**. The three live guards verified independent: model
  identity (`is`, mirrors `Query.combine` semantics per the related
  `ConfigurationError` precedent in `_apply_related_constraints`),
  db-alias equality (snapshot-compare), combinator presence. No second
  site enforces any of the three (seal/combinator readers elsewhere
  are distinct contracts — see R4).
- **C3 — new alias-collision namespace** (e.g. Django adds an
  annotation-adjacent namespace, or `extra(select=)` gains a sibling):
  moves `_effective_alias_names` only. Count **1**.
  `_next_reserved_alias` composes it by name (in-file consumer, not a
  second definition). Proven by
  `probe_alias_allocator.py` (`ALIAS-ALLOCATOR-OK`: occupied
  annotation + `extra` names skipped, counter advances `0 -> 2`).
- **C4 — reserved-prefix rename or second prefix consumer** (e.g.
  `_dst_predicate_` collides with a future Django namespace):
  moves `_RESERVED_ALIAS_PREFIX` only. Count **1**. `_dst_order_*`
  is a separate grammar under separate ownership (R1), not a consumer
  of this prefix.
- **C5 — attachment SQL-shape change** (`Exists` -> another
  row-preserving construct): moves the `queryset.alias(**{alias:
  Exists(inner)})` line in `attach_exists` only. Count **1**.
  `correlated_inner_root` unchanged (correlation root is
  mechanism-independent — the `pk__in` sibling (R2) already proves an
  equivalent test can sit on a different construct with the same
  correlation idea). Per-axis counts are each 1; no change touches two
  authoritative definitions.

Execution note: all challenges discharged by inspection + the three
read-only probes above (no DB, no source mutation). No shared-tree
pytest run: execution would not beat inspection (guards, allocation,
and singularity are all statically pinned by the oracle file's 11
tests, which already execute every challenged path).

## Findings

### F1 `row-preserving-predicate-attachment` (NEW family for Worker 0; owner `optimizer/predicates.py`)

- **Contract + variation.** Correlate (`correlated_inner_root`) +
  attach (`attach_exists`) = the one row-preserving to-many predicate
  primitive. Varies on: inner predicate body (caller-built, any
  to-many lookup), outer model (any model), database alias (pinned
  pair). Never varies on: boolean placement (caller owns it), predicate
  semantics (caller owns them), outer mutation beyond one `.alias()`.
- **Sites + roles.** Definitions: `correlated_inner_root`,
  `attach_exists` (both here, two halves of one primitive, one owner).
  Consumer: `filters/sets.py::FilterSet._apply_flat_leaves` (import +
  2 call sites: root construction per routed leaf, attach per
  non-identity result; applies the returned `Q` via its own
  `.filter(positive)`). Oracles: [test-predicates][test-predicates]
  (11 tests: no-`DISTINCT`, alias-not-selected, 5-arm allocation,
  3 guards incl. snapshot-message test, evaluated-outer parity,
  composite-pk execution, base-manager start) + 2 live SQL-shape tests
  (`test_genre_connection_flat_leaf_sql_shape_is_row_preserving`,
  `test_library_loans_deep_leaf_sql_shape_is_row_preserving` —
  names per the oracle module docstring). Projections: module
  docstring (multiset contract, `Exists`/`pk__in` sibling clause,
  inner-never-executes invariant, no-`negated` clause, no-noop-input
  clause), `exceptions.py` guard catalog, spec-060 + part1-plan prose.
- **Challenges.** C1 (correlation) -> 1; C2 (guards) -> 1; C5
  (attachment shape) -> 1. Per-axis count 1.
- **Owner + lifetime.** Owner is this module by responsibility
  (principle 7): the narrowest cohesive owner every legitimate
  consumer can depend on without reversing a dependency
  (filters-side; the selection optimizer never imports it, keeping
  request values out of the cross-request plan cache — a dependency
  direction constraint only this placement satisfies). No stored
  derivation: alias recomputed per call, `Q` built fresh, db pin read
  off the outer queryset — principle 4 "pure derivation says not
  cached" holds, no lifetime fields owed.
- **Migration.** None (file item: no consolidation; family item, if
  opened, would find the primitive already single-sited).
- **Distinct behavior.** The `pk__in` sibling stays separate (R2); the
  caller's identity short-circuit stays caller-side (axis 6).
- **Behavioral proof.** `static-reviewed`: bodies read in full at
  worktree; caller composition read at `_apply_flat_leaves`
  (3028-3041); oracle file read in full (every challenged path has an
  executing test). `execution-deferred`: none (no behavior change
  proposed; existing oracles already execute the paths).
- **Structural gate.** Existing: `test_alias_allocation` (5 arms pin
  the allocator against preoccupied namespaces) +
  `test_evaluated_outer_parity` + composite-pk execution test. A
  hand-copy bypass of the owner would still pass these (correct copy)
  — a future family item owes the negative-control statement, not
  this item.
- **Coupling.** None.
- **Freshness.** Target `4e87c733` (worktree == HEAD == ITEM_BASELINE);
  consumer [filters-sets][filters-sets] worktree `4a40e51b` (HEAD
  `4ab65a26`; concurrent operator-bag hunk at ~2357 verified far from
  call sites 3028-3041); oracle `b308c8c4` (clean); plan
  `3abb57ca`; HEAD `bfaee91d`; population 117 `.py`.

### FL1 Reserved-alias allocation kit (file-local; challenge-proved)

- **Contract.** `_RESERVED_ALIAS_PREFIX` (`"_dst_predicate_"`) +
  `_effective_alias_names` (field names + attnames + `"pk"` +
  `query.annotations` + `query.extra` + `query.values_select`) +
  `_next_reserved_alias` (first-free `_dst_predicate_<n>`, recomputed
  per attachment). One deterministic-counter mechanism, single site.
- **Challenge that proved it.** C3 + C4 -> 1 each; census: no second
  `def` of either helper, no second prefix assignment, no second
  `.alias(` call site package-wide. Nearest neighbors re-verified as
  different rules: `_dst_order_` grammar (R1), lateral/single-parent
  annotation readers (recognizer refusal contracts, never an allocator
  — `lateral_fetch.py` lines 602-610, 1008-1010 read annotations to
  REFUSE, not to allocate), `permissions.py` line 520
  (`attname in annotations/extra` collision *detection* for attestation
  naming, not allocation).
- **Owner + lifetime.** Here; pure derivation, no cache (recomputed so
  repeated attachments and pre-existing `_dst_order_*`/window aliases
  coexist — stated in the docstring, pinned by allocation arms (d)+(e)).
- **Proof.** `static-reviewed` + `ALIAS-ALLOCATOR-OK` (real functions,
  stub querysets, no DB). Gate: `test_alias_allocation` arms (a)-(e).
- **Freshness.** Same as F1.

### Rejections (predicate-adjacent rules noted anywhere; each re-verified, never inherited)

- **R1 — `_dst_order_` aggregate-order alias grammar
  ([orders-sets][orders-sets] line 729:
  `f"_dst_order_{index}_{flatten_lookup_path(field_path)}"`). Contract
  difference: per-term `Min`/`Max` aggregate annotations for to-many
  ordering (row-preserving by aggregation) vs per-attachment `Exists`
  existence tests (row-preserving by semi-join); different prefix,
  different counter (positional `index`, no occupancy scan), different
  owner (order expression resolution). Shared form considered: one
  reserved-alias counter for both grammars. Count if merged: the
  allocator would own 1 counter + 2 prefix/namespace policies with
  nothing shared except the word "alias" — remainder (aggregate choice
  per direction, lookup-path mangle with its single-owner note,
  existence correlation) keeps both call sites. Trigger: a third
  reserved-alias grammar, or Django rejecting one prefix, forcing a
  joint registry. Home: `orders/sets.py` (owner of the order grammar).
- **R2 — `Exists`/`pk__in` equivalence
  (`filters/sets.py::FilterSet._apply_related_constraints` +
  `_q_for_branch`/`_evaluate_logic_tree`). Contract difference: the
  sibling expresses "outer row has a qualifying related row" as a
  parent-pk `IN` subquery over `<rel>__in=<intersected>`; this
  primitive as a correlated `EXISTS`. The target's own docstring
  records them as semantically equivalent siblings that must neither
  rewrite the other nor silently diverge. Shared form considered: one
  "has-qualifying-related-row" helper. Count if merged: 1 helper body
  + 2 irreducibly different SQL shapes at every consumer + the
  visibility/manager-seeding differences (`_apply_related_constraints`
  derives from `constrained` itself for manager filtering + alias
  carry-through; the primitive pins `_base_manager` + outer `.db`) —
  the helper would be a mode flag over two bodies (principle 5).
  Trigger: measured divergence (plan/shape or row-semantics) between
  the idioms, or one idiom proving unexpressible for a new relation
  shape. Home: the two owners jointly (`optimizer/predicates.py` +
  `filters/sets.py`), clause already at the target docstring.
- **R3 — `_base_manager` second readers.** [write-tx][write-tx] lines
  1103/1188 (`_base_manager.using(alias).select_for_update()` /
  `.filter(pk=...).exists()` — write-pipeline lock scope + presence
  check, both EXECUTE immediately) and [rf-resolvers][rf-resolvers]
  line 1977 (post-save FK attestation `.values(...).get(pk=...)`,
  executes immediately). Contract difference: executing write-path
  reads on the operation's alias vs an unevaluated read-side
  correlation root that must never execute independently. Shared form
  considered: a "base-manager start" helper. Count if merged: 1 trivial
  line + 3 divergent tails (lock, attestation projection, correlation)
  with different execution contracts — inlining the one line is
  correct, extracting it couples write and read paths (principle 11:
  deletion-grade helper, not an extraction). Trigger: a fourth
  base-manager start whose tail matches one of the three. Home: each
  reader's owner.
- **R4 — combinator readers.** `utils/querysets.py` seal policy
  (`reject_combined`, execution-seal contract: model rows / no slice /
  no combinator for sealed execution) and
  [nested-fetch][nested-fetch] line 127 (whole-relation planning
  refusal, `combined` reason). Contract difference: sealing what may
  EXECUTE (or plan) vs refusing a meaningless ATTACHMENT (aliases
  cannot attach to a combined queryset — runtime caller-contract
  misuse, `OptimizerError` family). The three guards here are one
  function's misuse contract; the seal is a cross-cutting execution
  policy with its own rejected/open families in the index. Shared form
  considered: one "combined-queryset guard". Count if merged: 1 `if`
  + 3 different verdicts (raise misuse / refuse-to-seal / refuse-whole-relation)
  + different error families. Trigger: a new combined-queryset
  attachment path outside `attach_exists`. Home: `utils/querysets.py`
  (seal), `optimizer/nested_fetch.py` (planning refusal).
- **R5 — `OptimizerError` raising (consumer, not definition).**
  The three guards raise `OptimizerError` — they are enforcement sites
  of [exceptions][exceptions]`::OptimizerError`, whose taxonomy owner
  is `exceptions.py` (catalog lines 409-414 describe exactly these
  three guards; re-read at worktree, not inherited from
  [exceptions-artifact][exceptions-artifact]). No second definition of
  the error or its wording lives here (messages are per-guard
  caller-contract text, distinct inputs/errors per guard). Not a
  family, not file-local: reuse, owner `exceptions.py`.

## Defects

None. Tracing found no docstring-vs-body contradiction, no missing
guard a contract source demands (axis 6 enumerated full), no layering
claim the imports contradict (filters-side primitive imported only by
filters-side applicator; the optimizer selection path never imports
it — verified by import census: `from ..optimizer.predicates import`
appears only in `filters/sets.py` line 53).

(Worker 2) Phase 2: agree — no defects. Row-cardinality audit (GOAL.md
correct-row-counts sensitivity) proves each predicate preserves rows
(see `## Independent verification (Worker 2)` + `## Iterations`); no
finding meets the trust-boundary triple.

## Pending execution

None. Zero edits; all proofs `static-reviewed` or read-only-probe
verified (`ENUMERATION-OK`, `SINGULARITY-OK`, `ALIAS-ALLOCATOR-OK` —
commands in `## Freshness fingerprints`). No `proof:` entries, no
`gate:` entries. No shared-tree pytest run (inspection beats execution
here; the 11 oracle tests already execute every challenged path and
were read, not re-run, per the item's no-test-run fence).

## Judgment

Zero-edit file item. Enumeration closed (11 members, 6 rule-bearing,
every one homed: 1 new family F1, 1 file-local kit FL1,
5 rejections R1–R5 with contract differences + triggers + homes).
Strongest result: the primitive (F1) and its allocator (FL1) are each
single-sited with per-variation-axis definition counts of 1; every
predicate-adjacent rule in the package (order aliases, `pk__in`
sibling, `_base_manager` readers, combinator guards, error taxonomy)
was re-verified as a distinct contract, not a second definition. No
consolidation owed here by construction (file items never
consolidate); F1 named for Worker 0 to index.

## Freshness fingerprints

HEAD `bfaee91d` (item paths verified clean at close: `git status
--short -- <item paths>` empty; artifact created by this item, target
untouched). `git hash-object` (worktree) at read time:

- `django_strawberry_framework/optimizer/predicates.py` `4e87c733`
  (== HEAD blob == ITEM_BASELINE; target worktree-clean)
- `django_strawberry_framework/filters/sets.py` `4a40e51b` (HEAD
  `4ab65a26`; staged concurrent operator-bag hunk ~2357, far from
  predicate call sites 3028-3041 — read at worktree, claims
  independent of it)
- `django_strawberry_framework/exceptions.py` `e06b0b7f`
- `django_strawberry_framework/orders/sets.py` `6044ab1a`
- `django_strawberry_framework/optimizer/nested_fetch.py` `29ce5201`
- `django_strawberry_framework/optimizer/lateral_fetch.py` `db1ea315`
- `django_strawberry_framework/optimizer/plans.py` `cce98531`
- `django_strawberry_framework/utils/write_transaction.py` `eca9ad4d`
- `django_strawberry_framework/rest_framework/resolvers.py`
  (lines 1965-1994 read at worktree)
- `tests/optimizer/test_predicates.py` `b308c8c4`
- `docs/dry/dry-0_0_15.md` `3abb57ca` (plan: item line 191,
  `## Owned changes` ledger, responsibility index to F1's
  neighborhood)
- Population: 117 `.py` under `django_strawberry_framework/`
  (probe census). Excluded by body read (no second site on the
  strength of the body): `optimizer/walker.py`, `optimizer/extension.py`,
  `optimizer/selections.py`, `optimizer/single_parent_fetch.py`,
  `optimizer/join_taxonomy.py`, `optimizer/field_meta.py`,
  `utils/querysets.py` (seal only), `permissions.py`, `list_field.py`,
  `keyset.py`, `utils/connections.py`, forms/rest_framework/mutations
  flavor modules (no `Exists(`/`OuterRef(` producers per census).

Read-only probes (no DB, no source mutation, no pytest):

- `uv run python docs/dry/temp-tests/dry-file-optimizer__predicates/probe_enumeration.py`
  → `ENUMERATION-OK` (11 members, 4 defs asserted)
- `uv run python docs/dry/temp-tests/dry-file-optimizer__predicates/probe_singularities.py`
  → `SINGULARITY-OK` (1 def site per rule; `OuterRef(` 1 producer;
  `Exists(` code-producer 1 + docstring-prose 1; `.alias(` 1 call site)
- `uv run python docs/dry/temp-tests/dry-file-optimizer__predicates/probe_alias_allocator.py`
  → `ALIAS-ALLOCATOR-OK` (real `_effective_alias_names` /
  `_next_reserved_alias` on stub querysets)

Any fingerprint change reopens this item. Scratch paths (closeout
removal by explicit path, verified only — Worker 0): 
`docs/dry/temp-tests/dry-file-optimizer__predicates/probe_enumeration.py`,
`docs/dry/temp-tests/dry-file-optimizer__predicates/probe_singularities.py`,
`docs/dry/temp-tests/dry-file-optimizer__predicates/probe_alias_allocator.py`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[exceptions-artifact]: dry-file-exceptions.md
[filters-sets-artifact]: dry-file-filters__sets.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[lateral-fetch]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[predicates]: ../../django_strawberry_framework/optimizer/predicates.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[write-tx]: ../../django_strawberry_framework/utils/write_transaction.py

<!-- tests/ -->
[test-predicates]: ../../tests/optimizer/test_predicates.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Phase 1 only. Worker 1's sections were not opened; no status is set and no
verdict on Worker 1's work is proposed. File item: no production edit is owed;
candidates below are routed to holding families.

### Target confirmation

- HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e`; current branch kept, no
  commit, no switch.
- `django_strawberry_framework/optimizer/predicates.py`: 174 lines,
  worktree-clean (worktree `4e87c733` == `HEAD:predicates.py` `4e87c733`;
  `git diff HEAD -- <target>` empty).

### Enumeration (instrument + count + assignment)

Instrument: every node in `ast.Module.body` of the target (docstring `Expr`
included), parsed with `python3 -c` + `ast`. Count: 11 top-level members.

| # | Member | Kind | Worker-2 home |
|---|--------|------|---------------|
| 1 | module docstring (multiset contract, Exists/pk__in sibling note, inner-never-executes invariant, no-negated-param, no-noop-input) | projection of the rules below | projection (owner-adjacent prose; spec-060 ref resolves, see matrix axis 5) |
| 2 | `from __future__ import annotations` | import | file-local (no second site) |
| 3 | `from typing import TYPE_CHECKING` | import | file-local |
| 4 | `from django.db.models import Exists, OuterRef, Q` | Django vocabulary import | file-local (consumer of Django, not a package rule) |
| 5 | `from ..exceptions import OptimizerError` | error-owner import | consumer of `exceptions.py::OptimizerError` (that module owns the exception) |
| 6 | `if TYPE_CHECKING:` block (`QuerySet` import) | typing-only | file-local (`pragma: no cover` type-checking import) |
| 7 | `_RESERVED_ALIAS_PREFIX = "_dst_predicate_"` | constant | holding family HF-alias-namespace (definition, with 9/10) |
| 8 | `correlated_inner_root` | FunctionDef (public) | holding family HF-row-existence (definition: correlated root builder) |
| 9 | `_effective_alias_names` | FunctionDef (private) | holding family HF-alias-namespace (definition: namespace derivation) |
| 10 | `_next_reserved_alias` | FunctionDef (private) | holding family HF-alias-namespace (definition: counter derivation, consumes 9 by name) |
| 11 | `attach_exists` | FunctionDef (public) | holding family HF-row-existence (definition: attachment) + HF-predicate-guards (the three guard arms) |

No member is left unassigned. No consolidation is performed inside this file
item; consolidation lives in the holding families named below.

Holding families routed (Worker-2 naming, `_WORKER2` suffix implied):

- HF-row-existence: one rule, "attach a to-many relational predicate without
  changing outer row multiplicity". Definitions: `attach_exists`,
  `correlated_inner_root`. Consumers: `filters/sets.py::FilterSet._apply_flat_leaves`
  (builds `correlated_inner_root(queryset)`, invokes the leaf through
  `_invoke_suppressing_framework_distinct`, attaches via `attach_exists`, applies
  the returned positive `Q` with `.filter()`), `tests/optimizer/test_predicates.py::_compose`
  (test-local mirror of the caller shape). Sibling idiom held here for the
  family item, not merged: `filters/sets.py::FilterSet._apply_related_constraints`
  (`pk__in=<parent-pk subquery>`) and `FilterSet._q_for_branch`
  (`Q(pk__in=child_qs.values("pk"))`) — see Challenges change D.
- HF-alias-namespace: one rule, "reserved `_dst_predicate_N` aliases never
  collide with any effective alias name". Definitions: `_RESERVED_ALIAS_PREFIX`,
  `_effective_alias_names`, `_next_reserved_alias`. Consumer: `attach_exists`.
  Coexistence-only (projections, not definitions): `optimizer/plans.py`
  `WINDOW_ROW_NUMBER`/`WINDOW_TOTAL_COUNT`/`WINDOW_ROW_NUMBER_REVERSED`/
  `WINDOW_ROW_NUMBER_ABS`/`WINDOW_KEYSET_SEEK_COUNT`, `orders/sets.py`
  `_dst_order_*` aliases — separate rules sharing only the `_dst_*` collision
  avoidance posture; `_next_reserved_alias` docstring already names the
  coexistence, and `test_alias_allocation` arm (e) proves it by execution.
- HF-predicate-guards: one rule per arm, "caller-contract violations in runtime
  query state fail loud as `OptimizerError`". Definitions (all three arms live
  in `attach_exists`): model-mismatch, database-alias-mismatch (snapshot-then-
  compare), combinator-set. Projection: `exceptions.py::OptimizerError`
  docstring arm listing these three guards. Sibling `OptimizerError` raise
  sites (`plans.py::window_partition_for_prefetch`,
  `plans.py::apply_window_pagination` keyset+reverse, `utils/connections.py::
  assert_window_fetch_mode`/`window_range_plan`, walker hint errors) are
  distinct contracts — rejections, not members (trigger that would merge: a
  single documented caller-contract grammar spanning planning and predicate
  attachment, which does not exist today).

Worker-2 rejections (with trigger):

- R1 Exists-vs-pk__in unification ("rewrite `_apply_related_constraints` /
  `_q_for_branch` through `attach_exists`"). Rejected: the module docstring
  states the deliberate sibling equivalence ("neither should rewrite the
  other, and they must not silently diverge") — different variation axes
  (flat-leaf correlated adapter vs related-branch parent-pk restriction vs
  logic-branch composition). Trigger: a semantic change to "outer row has a
  qualifying related row" (e.g. NULL/three-valued-logic handling) that must
  move all spellings together — that change is posited as Challenge D and
  routed to the family item, not decided here.
- R2 async twin of the predicates ("add `aattach_exists`"). Rejected:
  inapplicable by construction (matrix axis 2) — pure unevaluated-ORM
  construction with no await points; the async caller reuses the sync body
  inside `run_in_one_sync_boundary`.
- R3 search-disjunction sharing (spec-060 `Meta.search_fields` same-value
  disjunctions). Rejected as future-caller, not current duplication: the
  surface is staged-but-unbuilt (`filters/sets.py` `TODO(spec-060 Slice 1)`,
  prefix map + `construct_search` landed, consumer surface owned by spec-060).
  Trigger: spec-060 Slice 1 landing a second EXISTS-attachment spelling.

### Matrix (all six axes discharged against the real surface)

1. Cross-flavor policy mirroring — SEARCHED. Greps: `Exists\(|OuterRef|
   attach_exists|correlated_inner_root|pk__in` over `django_strawberry_framework/`;
   `_dst_predicate_|_dst_order_|_dst_row_number|WINDOW_ROW_NUMBER|reserved alias`
   over the package. Result: exactly one EXISTS-predicate definition
   (`predicates.py`); `walker.py`/`plans.py` never import the target (their
   imports are plans/hints/join-taxonomy/selections only). `pk__in` sites found
   (`relay.py` node batching, `rest_framework/resolvers.py` + `utils/querysets.py`
   + `utils/write_values.py` visibility/existence checks, `filters/base.py`
   `pk__in="26"` CSV grammar, `filters/sets.py` related/logic branches) are
   distinct rules (visibility batching, input grammar, branch composition),
   except the two `filters/sets.py` sibling idioms routed to HF-row-existence
   above. Orders/aggregates do not mirror this rule (to-many ordering uses
   aggregates e.g. `Min`, per `tests/orders/test_sets.py` row-preserving
   heading). No hidden second owner.
2. Sync/async twins — SEARCHED, inapplicable by construction with reason.
   `grep -n "async|await" predicates.py`: zero hits. Callers:
   `FilterSet.apply_sync` (direct) / `FilterSet.apply_async` (derives
   visibility async, then `_apply_common_prelude` shared, then
   `_apply_common_finalize` inside `run_in_one_sync_boundary`) converge on the
   single sync `_apply_flat_leaves` body, which runs inside the `.qs` read
   within the one boundary — the DRY.md principle-5 write-pipeline shape
   (one sync body in one boundary), not the `connection.py` two-colored-body
   shape. No twin exists to drift; no test executes a second spelling because
   there is none.
3. Derived rather than repeated knowledge — SEARCHED. The target's four
   derivations each have one site: alias namespace (`_effective_alias_names`
   reads field names + attnames + `"pk"` + `query.annotations` +
   `query.extra` + `query.values_select`), counter (`_next_reserved_alias`
   recomputed from the live queryset per attachment), root
   (`correlated_inner_root`: `model._base_manager.using(queryset.db).filter(
   pk=OuterRef("pk"))`), db-pair snapshot (`attach_exists` reads each `.db`
   once into locals before comparing/formatting — the stateful-router fix
   pinned by `test_alias_mismatch_message_reports_the_compared_values`).
   Greps for `.db`, `_base_manager`, `OuterRef(`, `values_select`,
   `query.annotations` show no second derivation of any of these facts in the
   package. The `.db` re-resolution pitfall is derived once here, not
   re-derived per caller.
4. Inverse / round-trip pairs — RULED INAPPLICABLE with reason. The module
   builds one direction only: `(new_queryset, Q(alias=True))`; boolean
   placement and negation belong to the caller by stated contract ("No
   `negated` parameter", "the caller owns boolean placement"). No
   encode/decode, pack/unpack, build/parse surface exists in the target
   (grep for `negat|decode|parse` in module: only the docstring's negation
   sentence). Nothing to pair.
5. Contracts restated in another medium — SEARCHED, sites tagged:
   - Definitions: `predicates.py` (4 functions + prefix).
   - Consumer: `filters/sets.py::FilterSet._apply_flat_leaves` (+
     `_invoke_suppressing_framework_distinct`, `filter_queryset` multiset
     docstring) — invokes by name, never restates.
   - Oracles (read, not modified): `tests/optimizer/test_predicates.py`
     (guards, alias allocation a–e, no-DISTINCT, evaluated-outer parity,
     composite execution, base-manager start); `tests/filters/test_sets.py`
     1915–2064 (distinct-suppression restore incl. exception path,
     one-active-leaf attaches exactly one EXISTS/alias, sixteen-inactive-leaves
     attach nothing and match empty-filter SQL); live
     `examples/fakeshop/test_query/test_library_api.py::
     test_genre_connection_flat_leaf_total_count_is_row_preserving` and
     `::test_genre_connection_expanded_origin_pagination_is_row_preserving`
     (totalCount 1 / 2, cursor slices over preserved roots) plus
     `::test_library_loans_filter_by_deep_to_many_email_is_row_preserving_over_http`;
     `test_query/test_multi_db.py::
     test_row_preserving_relational_leaf_predicate_executes_on_shard_b_alias`
     (alias-pinned EXISTS, no DISTINCT); `tests/test_predicate_pg_explain.py`
     (no outer fan-out). No oracle was rewritten to read from the owner: the
     SQL-shape/count/row assertions observe behavior; the white-box
     `_effective_alias_names`/`_next_reserved_alias` pins are coverage of the
     owner itself, not checks of another site through the owner.
   - Projections: target module docstring (multiset contract, sibling note,
     invariants), `exceptions.py::OptimizerError` docstring arm,
     `filters/sets.py` applicator docstrings, `scripts/
     capture_pg_predicate_explain.py` comment. `docs/SPECS/
     spec-060-search_fields-0_1_2.md` exists (spec-060 ref resolves; the
     TODO at `filters/sets.py` Slice 1 is staged-but-unbuilt with a
     source-site anchor, per convention).
6. Enforcement by omission — SEARCHED, family enumerated. Routable population:
   every framework-generated leaf name gets at most one
   `CandidateFilterMetadata` row; rows exist ONLY for
   `framework_default`/`package_replacement` origins; `declared`/
   `override_generated`/unstamped leaves get NO row (fail closed at
   `_candidate_metadata_for`); `routable` additionally requires
   many-side path + no consumer `method` + audited family profile + owning-
   and-generating-class capability + audited django-filter release
   (`_AUDITED_DJANGO_FILTER_RANGE`, import-time verdict). Each member checked:
   non-routable names run the ORIGINAL `filter_instance.filter(queryset,
   value)` byte-for-byte (JOIN + legacy DISTINCT preserved) — the designed
   decline, with contract sources `filters/sets.py::_apply_flat_leaves`
   docstring + `CandidateFilterMetadata` docstring + audited-range gate, so the
   omission is a specified non-route, not a gap. Alleged no-guard surfaces
   judged on reason: inner-never-executes is enforced by construction
   (`OuterRef` correlation is unresolvable outside the subquery); no
   empty/no-op input is the stated contract with the identity short-circuit
   owned by the caller (`result is inner_root` → attach nothing, pinned by the
   sixteen-inactive-leaves test); evaluated-outer needs no guard (pinned by
   `test_evaluated_outer_parity`). No omission defect.

### Challenges (definition counts for rules I found)

- C1 alias-namespace change: "a new effective-alias namespace member must be
  avoided (e.g. a new projection list or `_dst_*` family)". Definitions forced:
  `_effective_alias_names` (1). `_next_reserved_alias` and `attach_exists`
  consume by name; tests/live SQL-shape are oracles. Count = 1 (no
  duplication).
- C2 correlation change: "correlation key or root pinning changes (non-pk
  correlation, extra tenant guard, different manager)". Definitions forced:
  `correlated_inner_root` (1). The composite-pk variation is already
  discharged by the SAME single implementation (`pk=OuterRef("pk")` → tuple
  comparison, proven executing on `RpCompositeParent` with `ColPairs` pin +
  `codes == ["MATCH"]`, `count == 1`). Count = 1.
- C3 guard change: "a new caller-contract guard (e.g. reject sliced outer) or
  a changed mismatch message". Definitions forced: `attach_exists` (1);
  `exceptions.py` arm is a docstring projection (listed, not counted).
  Count = 1.
- C4 existence-semantics change (cross-idiom, routed not decided): "the
  meaning of 'outer row has a qualifying related row' changes (NULL /
  three-valued-logic handling, sharded correlation)". Definitions that would
  move together: `attach_exists` EXISTS spelling (1) +
  `_apply_related_constraints` `pk__in` restriction (1) + `_q_for_branch`
  `pk__in` composition (1) → count = 3 IF the change is semantic. Per the
  module's stated sibling contract this is the holding question for the family
  item (HF-row-existence): whether the three spellings share one change
  obligation or are intentionally separate decisions with a parity suite. I
  posit it and route it; I do not consolidate (file item).

### Owners I would choose (DRY.md principle 7; lifetimes principle 4)

- Row-existence attachment + correlated root + alias allocation: keep in
  `optimizer/predicates.py` (narrowest cohesive owner every legitimate
  consumer can depend on without reversing a dependency: `filters/sets.py`
  already imports it; the selection optimizer (`walker.py`/`plans.py`) never
  does — moving the rule there would force the filter pipeline to import
  optimizer machinery for its semantics, reversing the dependency; module size
  is not a criterion). Lifetime (principle 4): pure derivation, explicitly
  NOT cached — the docstring keeps request values out of the cross-request
  `OptimizationPlan` cache; the alias is published at attach time on the
  returned queryset, mutated by no one else, never invalidated (per-queryset
  value). `attach_exists` returning `(queryset, Q)` keeps boolean composition
  (a caller decision with proven semantics) out of the primitive.
- Guard exception type: `exceptions.py::OptimizerError` already owns the
  exception (existing owner with that responsibility); guard BODIES stay at
  the attachment site (runtime query-state violations, not consumer
  configuration — matching the family's stated coherence).
- Behavior preservation (principle 8) and existence-question (principle 11)
  are discharged under Defects/row-cardinality below: the primitive's
  observable contract is "outer occurrences retained exactly once or removed,
  never multiplied; no injected DISTINCT; no dedup of consumer duplicates",
  and every attachment site is a real caller (`_apply_flat_leaves`), so the
  abstraction is load-bearing, not a one-caller wrapper.

### Defects (Worker 2) — none found

Row-cardinality hazard audit (GOAL.md: correct row counts; pagination
correctness depends on it) — each predicate proven row-preserving or the
defect would be filed here with contract row + reaching input:

- `correlated_inner_root`: builds the INNER only; the outer queryset object is
  never mutated (new object returned; `test_base_manager_start_does_not_leak_outer_filters`
  pins a single WHERE child and no outer-filter leak). Cannot duplicate or
  drop outer rows by construction.
- `_effective_alias_names` / `_next_reserved_alias`: pure set/string
  derivations; no queryset mutation at all. Trivially preserving.
- `attach_exists`: the ONLY outer mutation is `.alias(**{alias: Exists})`,
  which adds a non-selected annotation (oracle:
  `test_reserved_alias_not_selected` — alias absent from `values_select`,
  `annotation_select`, and the SELECT clause), plus the caller-applied
  `.filter(Q(alias=True))` selection. No JOIN is added (no fan-out source), no
  DISTINCT is injected (oracle: `test_primitive_injects_no_distinct`), no
  consumer `distinct()` is added or removed (the framework-added DISTINCT is
  suppressed inside the INNER invocation by the caller's helper, with
  restore-in-`finally` pinned incl. the exception path). Multi-child parents
  return once (composite oracle: `codes == ["MATCH"]`, `result.count() == 1`,
  `EXISTS` in SQL; evaluated-outer parity oracle equal). Live pagination
  oracles run counts/slices over preserved roots
  (`totalCount == 1` single-genre; `first: 1` → one edge + `hasNextPage true`
  + `totalCount == 2`, cursor → second genre). A duplicating/dropping
  predicate would break these oracles; none does.
- Omission sweep for cardinality: the three `OptimizerError` arms reject
  misuse instead of mis-filtering (model/alias/combinator); the identity
  short-circuit attaches nothing for no-op invocations (sixteen-inactive
  oracle: zero EXISTS, SQL identical to the empty filter); restrictive-empty
  composes as `Exists(none) == False` with no special case (no row leak);
  negation stays inside the invocation (`split_exclude` in the subquery; two
  leaves never share one inner body, preserving cross-row AND).

No finding meets the GOAL.md trust-boundary triple (contract row + feasible
project shape under supported public API + reaching wire/configuration
input). In particular: the spec-060 docstring reference resolves
(`docs/SPECS/spec-060-search_fields-0_1_2.md` exists); the Slice-1 TODO is a
convention-conformant staged-but-unbuilt anchor; the `filters/sets.py` and
`tests/filters/test_sets.py` worktree dirt is concurrent and
predicates-irrelevant (attributed below). Therefore: no defect entries.

### Freshness fingerprints (blob ids; `git hash-object` worktree, `HEAD:` clean)

- `django_strawberry_framework/optimizer/predicates.py`: worktree
  `4e87c733f19b43b67c67d3b97d920013e164bb1f` == HEAD (clean).
- `django_strawberry_framework/optimizer/walker.py`: `9b111ed938951a073a9226ccbcfacabc3af981e8` == HEAD (clean; traced: no import of target, no predicate twin).
- `django_strawberry_framework/optimizer/plans.py`: `cce985319c8833f3660653327d3003f1f03655a5` == HEAD (clean; traced: `WINDOW_*` namespace holders only).
- `django_strawberry_framework/exceptions.py`: `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` == HEAD (clean; `OptimizerError` arm is projection).
- `django_strawberry_framework/filters/sets.py`: worktree
  `4a40e51b288cad04cce3124697874c399d33f0fc` vs HEAD
  `4ab65a26b0ccf56f7f40f4938282bba9690673d1` — DIRTY-CONCURRENT. Attribution:
  the single hunk (circa 2357, declared-filter operator-bag multi-lookup
  `ConfigurationError` guard) is predicates-irrelevant: `git diff HEAD --
  filters/sets.py | grep predicates|correlated_inner_root|attach_exists|
  _apply_flat_leaves|Exists|OuterRef` returns zero lines. Consumer call sites
  (`correlated_inner_root`/`attach_exists` at 3028–3041) are HEAD-clean.
- `tests/optimizer/test_predicates.py`: `b308c8c4ba65b6e5c4c5211a18d4d35a1c4ec4b5` == HEAD (clean; read whole, 225 lines).
- `tests/filters/test_sets.py`: worktree `a624a78df64bd1234d0f14da9b0e360801629d9b`
  vs HEAD `85d31c4bc1e69102a049a2ba2908b0c3343ee764` — DIRTY-CONCURRENT (34-line
  `test_normalize_input_operator_bag_over_declared_filter_with_two_lookups_raises`
  addition). Predicates-irrelevant: diff-grep for
  `predicates|correlated_inner_root|attach_exists|EXISTS|_dst_predicate_|
  _invoke_suppressing|inner_root` returns zero lines. Oracle regions read at
  worktree: 1915–2064.
- `examples/fakeshop/test_query/test_library_api.py`: `0e032df0913bb32613c28523447b972fa258118e` == HEAD (clean; row-preservation oracles read at 3380–3499).
- `GOAL.md`: `7dfbef5c784519d5f95311aaeb8c6766ee966b02` == HEAD.
- `docs/dry/DRY.md`: `e8151123ff7e129fe9881ec342231e9e1795148e` == HEAD.
- `docs/dry/worker-2.md`: `4f089ea4a58d73295638e83abf8c612bf31487f8` == HEAD.
- `docs/SPECS/spec-060-search_fields-0_1_2.md`: `4a05a12b14b0975c7de50a5973ace3655d16bf98` (existence check for the docstring ref).
- Searches run (populations): package-wide `Exists\(|OuterRef|attach_exists|
  correlated_inner_root|pk__in`; `_dst_predicate_|_dst_order_|_dst_row_number|
  WINDOW_ROW_NUMBER|reserved alias`; `async def|sync_to_async|
  run_in_one_sync_boundary` (caller-shape check); `search_fields|split_exclude|
  _apply_flat_leaves` (caller/future-caller check); `row_preserv|SELECT
  DISTINCT|EXISTS|fan-out|pagination` in `test_query/` and `tests/` (oracle
  sweep). Any fingerprint change above reopens this trace.

## Iterations

### Phase 2 reconciliation (Worker 2, Run 0.0.15 2026-09-19-1, HEAD `bfaee91d`)

**Phase-1 integrity: intact.** Phase 1 was recorded blind: the artifact was
appended via shell heredoc without reading any Worker-1 section; the
enumeration was derived independently (`python3 -c` + `ast`, same instrument
as the probe by convergent choice, not by copying — the probe files were
never opened in Phase 1); neighbors were traced from the target's own imports
and docstring references. No Phase-1 claim required un-reading; nothing below
rewrites it, only collapses its holding routings into Worker 1's record.

**Enumeration: 11 = 11, full member map.** Six rule-bearing members agree
(docstring projection + `_RESERVED_ALIAS_PREFIX` + 4 defs); imports/`If`
file-local agree. Per-member: docstring → F1 projection (+ R2 sibling clause);
`_RESERVED_ALIAS_PREFIX`, `_effective_alias_names`, `_next_reserved_alias` →
FL1 (my HF-alias-namespace collapses here); `correlated_inner_root`,
`attach_exists` (incl. its three guard arms) → F1 (my HF-row-existence
collapses here; my HF-predicate-guards dissolves: arms are F1/C2, taxonomy is
R5); `OptimizerError` import → R5 consumer; `__future__`/`TYPE_CHECKING`
imports + `If` block → file-local, no rule.

**Family-grouping verdict: Worker 1's grouping stands; all three Worker-2
holdings collapse, zero index corrections.**

- HF-row-existence → COLLAPSE into F1 `row-preserving-predicate-attachment`
  (identical definitions, consumer, owner; already indexed open at plan line
  466). Its `pk__in`-sibling tail → R2.
- HF-alias-namespace → COLLAPSE into FL1 (identical members and C3/C4 → 1;
  file-local, no index row owed).
- HF-predicate-guards → DISSOLVE (wrong shape for a family: three arms of one
  function already in F1/C2; error side is R5 reuse; neighboring combinator
  readers are R4). No row anywhere.
- Worker 0 action: none on the index (row 466 stays `open` under holding item
  File `optimizer/predicates.py`); no `## Families` artifact is owed by this
  zero-edit file item beyond the existing index row.

**C4 collision settled (numbering overlapped, substance differs).** Worker 1's
C4 (prefix rename → `_RESERVED_ALIAS_PREFIX` only, count 1) is ADOPTED — the
correct per-axis challenge of the allocator kit; Phase 1 never posited it.
Worker-2's C4 (existence-semantics change → 3 IF semantic) is WITHDRAWN as a
duplication count and re-expressed as R2's already-recorded rejected shared
form (1 helper + 2 SQL shapes + seeding differences, trigger: measured
divergence). Net: the allocator kit is one rule; no undecided rows remain.
C1/C2/C3/C5 counts (each 1) are mutually confirmed — my C1↔their C3
(namespace), my C2↔their C1 (correlation), my C3↔their C2 (guards) agree.

**Rejection map: all adopted, three spot-verified by fresh reads.**

- My R1 (Exists/`pk__in` unification) → theirs R2: ADOPT R2 (fuller
  shared-form count + joint home; sibling clause already at the docstring).
- My async-twin rejection → matrix axis 2 "No twin": same verdict, keep the
  matrix form (no numbered rejection needed).
- My R3 (spec-060 future caller) → ACCEPTED as complementary trigger (home:
  spec-060; consumer note already in F1; `TODO(spec-060 Slice 1)` anchor
  conforms to staged-but-unbuilt convention).
- Their R1 (`_dst_order_` grammar): ADOPTED — verified at `orders/sets.py`
  lines 726-734 (`Min`/`Max` per-term aggregates, positional index, no
  occupancy scan; distinct contract).
- Their R3 (`_base_manager` readers): ADOPTED — verified at
  `utils/write_transaction.py` lines 1091-1106 (immediate `SELECT ... FOR
  UPDATE` lock scope) and `rest_framework/resolvers.py` lines 1975-1980
  (immediate post-save attestation `.get`); both executing write-path reads
  vs the unevaluated correlation root (principle 11: extraction would couple).
- Their R4 (combinator readers): ADOPTED — verified at
  `optimizer/nested_fetch.py` lines 122-134 (`"combined"` whole-relation
  planning-refusal reason, a verdict distinct from the misuse raise).
- Their R5 (taxonomy reuse, owner `exceptions.py`): ADOPTED — matches my
  member-5 assignment.

**No-defect agreement: both verdicts hold, complementary.** Their
filters-side-only-use + import-census layering proof and my per-predicate
row-cardinality + GOAL pagination-sensitivity proof establish different
halves of "nothing broken"; neither contradicts the other. No defects.

**Proof adequacy: `## Pending execution: None` ACCEPTED, static adequate.**
Predicate SQL is backend-observable, but this zero-edit item changes no
ordering, transactional, or async behavior, so execution cannot beat
inspection here: every challenged path (correlation, guards incl. the
stateful-router snapshot message, allocation arms a–e, parity, composite
execution, base-manager start) already has an EXECUTING oracle in the suite,
and the three read-only probes were verified by reading (no DB, no mutation,
no pytest: AST census, regex singularity census over 117 files, stub-QS
allocator exercise). Gate-run oracles (final `uv run pytest` executes them):
`tests/optimizer/test_predicates.py` (11 tests),
`tests/filters/test_sets.py` predicates regions (≈1915–2064),
`examples/fakeshop/test_query/test_library_api.py` row-preservation tests,
`examples/fakeshop/test_query/test_multi_db.py` shard-`EXISTS` test. PG cells
stay gate-noted, not gap: `tests/test_predicate_pg_explain.py` is wholly
`@pytest.mark.pg` (auto-skipped on SQLite per root conftest) — the SQLite
oracles above pin the same row contract; the PG EXPLAIN twin observes planner
rows, not a new behavior. No `proof:` entries owed; no `gate:` entries owed.

**AGENTS.md prose on the empty diff: conforms.** Item-scoped diff is empty
(zero production/test edits; artifact + 3 probes are untracked, owned by this
item). Ruff: no `.py` paths touched → `ruff check` / `ruff format --check`
vacuous (nothing to run). Citations use `path::Symbol` + reference-style links
with one link-definition block; no process provenance; no test-tier question
(no tests added — correct, oracles pre-exist).

**Freshness re-hashed (Phase 2, HEAD still `bfaee91d`).** Finding inputs
UNCHANGED: target `4e87c733`, `filters/sets.py` `4a40e51b` (same concurrent
bag-guard hunk, still far from call sites 3028-3041),
`exceptions.py` `e06b0b7f`, `orders/sets.py` `6044ab1a` (prefix-stable),
`nested_fetch.py` `29ce5201` (prefix-stable), `lateral_fetch.py` `db1ea315`
(prefix-stable), `plans.py` `cce98531`, `write_transaction.py` `eca9ad4d`
(prefix-stable), `test_predicates.py` `b308c8c4`. Plan
`docs/dry/dry-0_0_15.md` drifted `3abb57ca` → `14609d96` (concurrent Worker-0
ticks of sibling items, e.g. lateral_fetch/plans lines) — the plan is not a
finding input; no finding reopens. Probe scratch still present (3 files, paths
in `## Freshness fingerprints`). Concurrent dirt elsewhere untouched.

**Verdict: `Status: verified`** (set above). Zero edits, no pending execution.

