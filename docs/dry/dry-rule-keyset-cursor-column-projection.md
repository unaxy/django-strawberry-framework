# DRY review: `keyset-cursor-column-projection`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

Target: the keyset-cursor column projection — how cursor
columns survive an existing `.only()` / `.defer()` mask so
keyset edge-minting reads ordering-column values off loaded
rows instead of lazy-loading per edge (sync) or raising
`SynchronousOnlyOperation` (async).

Contract: given a queryset and cursor-column attnames, (a)
with no readable mask, or full coverage already, return the
queryset unchanged (identity arms); (b) under `.only()`,
re-apply the UNION of the existing load-only set and the
missing cursor attnames (Django chaining replaces, so the
union is reload-bearing); (c) under `.defer()`, clear the
mask and re-apply every deferred field EXCEPT the cursor
columns. Varies over mask modes (none / only / defer /
unreadable); the column source is threaded by each caller
(keyset-owned vocabulary), never derived here.

Traced at WT bytes (HEAD `5c3496e0` + worktree). All line
numbers below are WT lines. Fingerprints (WT `git
hash-object` / HEAD `git rev-parse HEAD:` / baseline
`ITEM_BASELINE=e3269f18` `git show` + `git hash-object
--stdin`; baseline is the item `git stash create` commit,
taken at dispatch):

| File | WT | HEAD | Baseline |
|---|---|---|---|
| `optimizer/nested_planner.py` | `b6ff0a0e` | `8c3a45f5` | `b6ff0a0e` |
| `connection.py` | `48de0243` | `99969652` | `48de0243` |
| `optimizer/plans.py` | `2e962ae2` | `97a524e2` | `2e962ae2` |
| `optimizer/lateral_fetch.py` | `a48cb0a4` | `a48cb0a4` | `a48cb0a4` |
| `optimizer/walker.py` (alias) | `4fd8077f` | `13e1be20` | `4fd8077f` |
| `keyset.py` (codec/mint) | `7d43c6b1` | `6af980b8` | `7d43c6b1` |
| `tests/test_keyset_connection.py` | `70db0483` | `70db0483` | `70db0483` |
| `test_query/test_keyset_api.py` | `315c0372` | `315c0372` | `315c0372` |

WT == baseline on every fingerprinted file (no bytes moved
since dispatch); WT == dispatch pins on the four indexed
files. `git status --short` count 477 at trace time, HEAD
`5c3496e0` unmoved.

Dirt attribution (every hunk diffed vs `git show HEAD:`,
none in the plan `## Owned changes` ledger, all concurrent
work — read for census only, untouched):

- `nested_planner.py`: 3 hunks — `truth` import (line 28),
  M2M-advisory silence + guard (line 643), `truth.name`
  in the strategy-refusal log (line 1488). Zero hunks
  touch F1 lines (owner body 742-773, call site 1386-1389);
  a diff grep for the F1 vocabulary counts 0.
- `connection.py`: 31 hunks (143+/128-), all concurrent
  (`truth` migration, guard reorder at 583, `_KeysetPage`
  docstring at 1014, `_keyset_connection_context`
  `truth.class_dict` rewrite at 210). No hunk edits the
  two `_extend_only_projection` call sites (961-964,
  1011), the import (86), or either mint site (612, 1181);
  the three diff mentions of the family names are hunk
  headers only.
- `plans.py`: 3 hunks — `truth` import, `truth.name` in
  `resolver_key`, `truth.static_attr` in
  `ends_in_unique_column`. None touches the unpack
  (581-604), its readers (607-704), or the plan writers.
- `lateral_fetch.py`: clean. Both test files: clean.
- `walker.py` / `keyset.py` dirt was not diffed hunk by
  hunk (out-of-index inputs); the alias lines
  (walker 95-111) and the mint body (keyset 515-547) were
  read at WT bytes and carry the shapes the trace cites.

Sites and roles (re-derived fresh, not inherited):

- D1, the one definition:
  `optimizer/nested_planner.py::_extend_only_projection`
  (742-773): the union/invert rewrite. Reads the mask
  through the shared `deferred_loading_of` unpack.
- C1, consumer: the planner keyset branch
  (nested_planner 1380-1389) — threads
  `keyset_context.columns` attnames. The extended child
  queryset feeds `NestedConnectionRequest` (1462-1477),
  so windowed AND lateral strategies inherit it.
- C2/C3, consumers: `connection.py::_keyset_order_state`
  declared-order arm (961-964) and `orderBy:` arm (1011)
  — threads declared / per-order local attnames. Serves
  root connections and every per-parent fallback
  (`_resolve_keyset_connection` 1095, `_consume_fallback`
  846-855).
- U1, composed unpack owner:
  `optimizer/plans.py::deferred_loading_of` (581-604) —
  the single reader of `query.deferred_loading`, with
  exactly 4 production callers (AST census below).
- Oracles: `test_extend_only_projection_passthrough_arms`
  (package identity + union/invert arms, asserting spelled
  `(names, defer_flag)` sets through the shared unpack),
  plus live `test_nested_keyset_unselected_cursor_column_is_not_lazy_loaded_per_edge`
  (test_keyset_api 619) and async
  `test_async_keyset_deferred_cursor_column_is_loaded`
  (test_keyset_api 1072).
- Projections: the owner docstring (mask-mode rationale),
  the `_keyset_order_state` docstring (projection clause),
  the planner-branch comment (1381-1385).

Mint-path audit (every cursor mint must sit downstream of
the owner): production `encode_keyset_cursor` callers are
exactly connection 612 (`_resolve_from_window`, planned
windows — rows carry the C1 extension) and connection 1181
(`_resolve_keyset_connection._build` — rows carry the
C2/C3 extension via line 1095). No other production mint
exists (keyset tests call the codec directly). The
scalar-only keyset shape mints nothing (no edges selected)
and already carries order columns; backward / unwindowable
shapes fall back per-parent through C2/C3.

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched. No other
   public surface extends a projection for cursor needs:
   list fields mint no cursors, node refetch mints none,
   mutations apply NO `.only()` (G2 gate), filters/orders
   shape rows not masks. No mirror exists.
2. Sync/async twins: inapplicable with reason. The owner
   is sync queryset-shaping with no await point; both
   execution colors share it upstream of the sync/async
   fetch split (the slicer dispatches at connection
   1161-1171 on the already-extended queryset). No twin.
3. Derived rather than repeated knowledge: searched. The
   `column.field.attname` read appears at C1, C2, and
   (as `field.attname` over raw fields, locals-only) C3;
   recorded as exclusion R9 (attribute access on the
   shared `CursorColumn` record, not a derivation). The
   mask itself is never re-derived: all four readers
   compose U1 (AST census: exactly 4 callers).
4. Inverse / round-trip pairs: the keyset codec pair
   (encode/decode) belongs to keyset.py, not this family;
   the union is one-way mask widening with no inverse.
   No pair inside the family.
5. Contracts restated in another medium: the three prose
   projections (owner docstring, order-state docstring,
   branch comment) describe the rule; all match their
   bodies. `diff_plan_for_queryset` prose names
   `query.deferred_loading` but its body composes
   `_consumer_only_fields` (R11). No second implementation
   hides in prose, tests, or docs.
6. Enforcement by omission: enumerated. Mint sites: 2,
   both downstream of the owner (audit above). The G2
   gate needs no consultation: on an unmasked queryset
   the owner no-ops (identity arms), so operation-wide
   suppression and per-mask extension cannot disagree.
   No member lacks an applicable guard.

### Enumeration

Instrument: stdlib AST walk over all 119 package `.py`
files (`/tmp/f30_mask_census.py`, read-only), counting
executable `Call` nodes — prose mentions excluded by
construction.

- `.only()` call sites: exactly 3 —
  nested_planner 739 (scalar-only fresh write, sibling
  family), nested_planner 773 (the F1 union), plans 334
  (plan-apply fresh write). No second union exists.
- `.defer()` call sites: exactly 2 — nested_planner
  766-767 (the F1 invert). No second invert exists.
- `deferred_loading_of` call sites: exactly 4 — plans
  617 (`_consumer_only_fields`), plans 698
  (`_consumer_projection`), lateral 1230
  (`_select_columns`), nested_planner 758 (F1). The
  unpack docstring names 3 of 4 (D1).
- `query.deferred_loading` direct reads: exactly 1 —
  plans 597 (inside U1). No bypass exists.
- `_extend_only_projection` production readers: exactly
  3 call sites (C1-C3) + the walker alias (zero readers
  through it — connection and tests import from
  nested_planner directly, grep-verified).

Every enumerated member lands: F1 (D1+C1+C2+C3+U1),
exclusions R1-R12, or the D1 defect. Nothing unassigned.

### Challenges

Each change posited on the rule's variation axes; count =
authoritative definitions forced (consumers / oracles /
projections listed, not counted).

- C-A, mask-mode axis: Django gains a third loading mode
  (or the unreadable-`None` arm needs a loud refusal).
  Forced: D1 only (the mode dispatch lives in its body;
  U1's `(names, defer_flag)` shape is the unpack's own
  contract, challenged under R1). Count 1.
- C-B, union-semantics axis: the `.only()` union must
  change (e.g. dotted-entry normalization, ordering
  guarantee, empty-`attnames` refusal). Forced: D1 only
  (lines 768-773; C1-C3 pass attnames through
  unchanged). Count 1.
- C-C, invert-semantics axis: the `.defer()` clear-and-
  reapply must change (e.g. preserve defer order, refuse
  when every field is a cursor column). Forced: D1 only
  (lines 762-767). Count 1.
- C-D, caller-shape axis: a fourth cursor-minting path
  appears (new strategy, new fallback). Forced: 0
  definitions — the new path composes D1 by name (C1-C3
  precedent); a hand-rolled second union would be a new
  definition, which the Enumeration census would catch.
  Count 0 moves, 1 composition.
- C-E, exclusion probes (each must force count 1 outside
  F1 or fail to move F1): consumer-prune policy change
  moves `_consumer_projection` only (R2); lateral select-
  list change moves `_select_columns` only (R3); plan-
  apply ordering change moves `OptimizationPlan.apply`
  only (R4); scalar-only column-set change moves the
  sibling owner only (R5); connector-list change moves
  the taxonomy + `_ensure_connector_only_fields` only
  (R6); order-ladder change moves
  `effective_connection_order` only (R8). F1 unmoved in
  all six.

Behavioral proof: `execution-verified` — the package
oracle ran green in the shared venv (Pending execution);
the static censuses above are inventory-shaped (no wrong
result to reject beyond miscount, discharged by the AST
instrument over 119 files).

## Findings

### F1 keyset-cursor-column-projection — CONFIRM, single-owned, zero-edit

Contract + variation: as stated in System trace; varies
over mask modes only, column source threaded.

Sites + roles: D1 one definition; C1-C3 three consumers
composing by name; U1 one composed unpack; 2 mint sites
both downstream; oracles 1 package + 2 live; projections 3,
all accurate.

Challenges: C-A-C-D above, counts 1/1/1/0 — every
variation axis challenges to exactly the owner.

Owner + lifetime: `_extend_only_projection` in
`optimizer/nested_planner.py` — the narrowest module all
three call sites already import (connection.py imports
from nested_planner directly; the walker alias exists but
carries zero readers). No stored derivation: pure
queryset-shaping, explicitly not cached (principle 4:
"not cached" holds — each call reshapes its input).

Migration: none — single ownership already holds by
construction. No call, declaration, or deletion is owed.

Distinct behavior: the locals-only vs related-annotation
split in C3 stays in `_keyset_order_state` (column
selection, not mask extension); the declared-vs-per-order
column choice stays at each consumer. Where recorded: the
`_keyset_order_state` docstring and R9 below.

Behavioral proof: `execution-verified` (package oracle 1
passed, shared venv) + `static-reviewed` (AST censuses;
import moves N/A — nothing moved). Each rejects the wrong
result named in Challenges (a second union/invert body or
an uncovered mint path).

Structural gate: none landed. The plausible bypass — a
second union body at a new mint site — is inventory-
shaped, and the scalar-only sibling (identical shape: one
writer + consumers) set the zero-edit precedent this run.
A per-helper existence test is barred by DRY.md; a
mechanism census gate over all `.only()` writers would
guard three families at once, which no single family item
owns. The Enumeration AST command above is the re-run
recipe.

Coupling: none. Freshness: fingerprints in System trace;
any change reopens.

Finding line estimate: +0/-0 (zero-edit verdict; the
artifact is the only new file, untracked).

### Exclusions (rejected candidates — contract difference + trigger)

- R1 `deferred_loading_of` unpack (plans 581-604):
  mask READ into `(names, defer_flag)` vs mask REWRITE.
  Same owner composed, opposite directions. Trigger: a
  caller needing read-then-rewrite in one pass under one
  contract (prior R13 trigger, re-derived fresh).
- R2 `_consumer_only_fields` / `_consumer_projection`
  (plans 607-704): consumer-projection reads feeding
  prune/diff verdicts vs cursor-column rewrite. Trigger:
  a prune decision needing to widen the mask it reads.
- R3 lateral `_select_columns` (lateral 1216-1247):
  projection read into an SQL `(attname, column)` select
  list vs queryset-mask rewrite; a `defer()` shape
  downgrades rather than rewrites. Trigger: the lateral
  backend widening a mask instead of downgrading.
- R4 `OptimizationPlan.apply` (plans 324-339): FIRST-write
  `.only(*only_fields)` application vs union with an
  existing mask (consumer-wins diffing drops plan fields
  instead of merging). Trigger: apply preserving a
  pre-existing mask.
- R5 `_project_scalar_only_window` (nested_planner
  701-739): fresh minimal projection on an unprojected
  scalar-only child vs extension of an existing mask;
  owned by the consolidated sibling family. Trigger: a
  scalar-only child arriving pre-masked.
- R6 `walker._ensure_connector_only_fields` (walker
  1578-1613): plan-list append at construction time vs
  applied-queryset rewrite. Trigger: the connector
  guarantee moving to applied-mask time.
- R7 walker `_extend_only_projection` alias (walker 106):
  pure alias with zero readers through it, not a
  definition. Trigger: a reader importing through walker
  (then a re-export question, still not a second body).
- R8 `effective_connection_order` / `deterministic_order`
  (plans 918-966): ORDER selection (which ORDER BY) vs
  COLUMN projection (which columns load). Trigger: order
  derivation needing loaded-column knowledge.
- R9 attname reads at C1/C2/C3 (`column.field.attname`):
  attribute access on the shared `CursorColumn` record
  (principle 1: the record is the shared meaning), not an
  independently maintained derivation; C3 additionally
  filters locals-only over raw fields. Trigger: the
  attname source gaining logic — then the record owns a
  property and all three compose it.
- R10 keyset codec (keyset 380-547, 652-731): value
  serialization / seek predicates vs column loading. The
  mint reads `column.value_source` off rows the owner
  already loaded. Trigger: the codec needing mask
  awareness.
- R11 `diff_plan_for_queryset` prose (plans 1349-1351):
  names `query.deferred_loading` in prose, but the body
  composes `_consumer_only_fields` (1394). Projection,
  not a reader. Trigger: the body inlining the unpack.
- R12 G2 gate (`_enable_only_for_operation`, walker
  145-160): operation-wide projection suppression vs
  per-mask extension; the owner no-ops on unmasked
  querysets so the two cannot disagree. Trigger: the
  owner gaining behavior on unmasked querysets.

## Defects

- D1 (minor, doc-only): `deferred_loading_of` docstring
  census is stale — "Every consumer builds on this one
  unpack (``_consumer_only_fields``, ``_consumer_projection``,
  the lateral backend's projection read)" names 3 of the
  4 production callers, omitting
  `optimizer/nested_planner.py::_extend_only_projection`
  (call at nested_planner 758; AST census: exactly 4
  callers). Owner: `optimizer/plans.py::deferred_loading_of`.
  Fix shape: one parenthetical clause naming the fourth
  consumer; count-free, behavior-neutral. Left unfixed
  per the defects rule; for Worker-0 homing.

No other defect: every other docstring read matches its
body, no family member lacks an applicable guard (axis 6
enumerated with the contract source for each deliberate
omission), and all WT dirt in the indexed files is
concurrent work per the attribution above.

## Pending execution

None. No `proof:` entry (the verdict is inventory-shaped;
the one behavioral probe already ran green) and no
`gate:` entry. Default cell: executed — `uv run pytest
-n0
tests/test_keyset_connection.py::test_extend_only_projection_passthrough_arms
--no-cov` → 1 passed in the shared venv (slots 1-3 venvs
are damaged per KNOWN, so the shared venv carried the
probe; the `dry/keysetcol-f30/consolidate` copy itself
was obtainable — slot-2, fresh, shared unmoved — and ran
a trivial command exit 0, run id
`dry-20261001T113138-ae3308`). Sharded/PG cells:
`inapplicable by construction` — the rule is pure
queryset-shaping (lazy `.only()` / `.defer()`
construction plus `deferred_loading` attribute reads; no
queryset execution, no alias, no dialect decision),
stated for Worker-2 to judge (f29 precedent, accepted).
`--cell` runs were not authorized.

## Judgment

CONFIRM single-owned-zero-edit. The keyset-cursor column
projection lives once, in
`optimizer/nested_planner.py::_extend_only_projection`,
with three consumers composing by name, one composed
unpack, both mint sites downstream, and twelve exclusions
each carrying its contract difference and trigger. No
consolidation lands, no test is added, no ledger row is
owed. The artifact submits as `ready-for-verification/1`.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (own greps + own AST
censuses at WT bytes, HEAD `5c3496e0` unmoved). W1 sections
below stay byte-intact; reconciliation follows the trace.

### Own trace

Rule posited: keyset cursor columns must survive an existing
`.only()` / `.defer()` mask — the mask-extension rule (union
for `.only()`, invert for `.defer()`).

Sites (fresh evidence, WT bytes):

- Definition: `django_strawberry_framework/optimizer/nested_planner.py::_extend_only_projection`
  (`:742`-`:773`). Reads the existing mask through the shared
  unpack (`:758`); invert arm `:762`-`:767` (clear + re-defer
  the remainder); union arm `:768`-`:773`
  (`.only(*names, *missing)`); passthrough arms for
  unreadable / empty / fully-covered / no-op-defer shapes.
- Consumers, production Call census by AST over package +
  tests + examples (exactly 3 production sites, all compose
  by name, no inlined union/invert anywhere):
  1. `django_strawberry_framework/connection.py::_keyset_order_state` `:961`
     (declared-order fast path, attnames from `state.columns`).
  2. `django_strawberry_framework/connection.py::_keyset_order_state` `:1011`
     (orderBy arm, local attnames only; related-path values
     ride `F()` annotations instead).
  3. `django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation`
     `:1386` (planner keyset branch, attnames from
     `keyset_context.columns`).
- Alias, not a definition: `django_strawberry_framework/optimizer/walker.py:106`
  (`_extend_only_projection = _nested_planner._extend_only_projection`),
  module-documented as a no-reader compat re-export; grep
  confirms no production or test reader imports it from walker.
- Composed unpack: `django_strawberry_framework/optimizer/plans.py::deferred_loading_of`
  (`:581`-`:604`). THE single raw reader of the
  Django-private contract: the only
  `getattr(query, "deferred_loading", None)` in the package
  is `:597`. Production Call census by AST: exactly 4 —
  `plans.py:617` (`_consumer_only_fields`), `plans.py:698`
  (`_consumer_projection`), `nested_planner.py:758`
  (`_extend_only_projection`), `lateral_fetch.py:1230`
  (`_select_columns`). Test oracle reads at
  `tests/test_keyset_connection.py:494,501`.
- Mint sites, downstream (read values the projection keeps
  loaded; the mint `keyset.py::encode_keyset_cursor`
  `:515`-`:546` is itself single-owned): exactly 2
  production callers — `connection.py:612` (window path) and
  `connection.py:1181` (root/fallback `_build`).
- Test oracle: `tests/test_keyset_connection.py::test_extend_only_projection_passthrough_arms`
  (`:475`-`:503`): 7 direct calls covering every arm, with
  union/invert outcomes asserted through unpack reads
  (`defer_flag` + concrete frozensets — independently
  spelled expectations, not owner-derived).

Change challenges (mine; each names the definitions forced):

1. Union-rule change (e.g. `.only()` chaining semantics
   shift, or name-order preservation): only `:773` moves.
   Count = 1.
2. Invert-rule change (e.g. defer-clear must preserve a
   marker): only `:766`-`:767` moves. Count = 1.
   Splitting union from invert would be an internal refactor
   of the one body, not a second definition — both arms are
   one contract's two modes.
3. Django-private unpack change (`deferred_loading`
   rename/reshape): only `deferred_loading_of` `:596`-`:604`
   moves; all 4 consumers follow by name. Count = 1.
4. Second mask-extension site hunt: every other
   `.only(`/`.defer(` writer in the package is a
   first-writer that never reads an existing mask —
   `_project_scalar_only_window` `:739` (fresh window
   write), `OptimizationPlan.apply` (`plans.py:334`, fresh
   write after the consumer-wins diff guarantees no
   pre-existing `.only()`). No second read-then-extend site.
   Count = 1.
5. Third mint path needing cursor columns loaded: a new
   consumer calls the owner by name; the owner is unchanged.
   Count = 1 (no new definition forced).

Owner I would choose:
`optimizer/nested_planner.py::_extend_only_projection` —
re-derived, not inherited. It is the narrowest cohesive
owner both consumer domains can depend on without reversing
a dependency: root resolution (`connection.py`) already
imports from `nested_planner`, and the nested planner is the
owner's home module; `plans.py` owns only the lower-level
unpack the owner composes. Coincides with the dispatch
candidate.

Neighbors excluded by my own contract-difference pass:

- `_project_scalar_only_window` — first-write of a fresh
  window mask; never reads an existing mask.
- `OptimizationPlan.apply` — first-write of planned fields.
- `_consumer_only_fields` / `_consumer_projection` /
  `diff_plan_for_queryset` — detect/reconcile; compose the
  unpack; never extend.
- `prune_unsupportable_select_related` /
  `_select_path_traversable` — `select_related` pruning, a
  different directive.
- Lateral `_select_columns` — derives a SQL select list FROM
  the mask (downstream reader); never mutates a mask.
- `walker._ensure_connector_only_fields` — appends to the
  plan list at construction time; never touches a live
  queryset mask.
- `encode_keyset_cursor` / `decode_keyset_cursor` — the
  keyset codec family (mint/decode); the projection is its
  upstream precondition, not its twin.
- `effective_connection_order` — window-order derivation.
- `_concrete_order_columns` — order-to-column resolution
  consumed BY projection writers, not a projection itself.

Freshness fingerprints (Worker-2, WT bytes at verify time):

- `django_strawberry_framework/optimizer/nested_planner.py` WT
  `b6ff0a0e998291c5acdf204fd363fd015bb1e1bb`, HEAD
  `8c3a45f55533cbaf9697013e5d87f599aae65adb`.
- `django_strawberry_framework/connection.py` WT
  `48de0243613555312478aaeb7b1a2f198923e91a`, HEAD
  `999696529e18160aff1e465951ebe7e88dd4613b`.
- `django_strawberry_framework/optimizer/plans.py` WT
  `2e962ae2dd0a5be4d05a52cc48334904e1511249`, HEAD
  `97a524e2a8ec0a160f1ed649bb96df019928d6bc`.
- `django_strawberry_framework/optimizer/lateral_fetch.py` WT
  `a48cb0a45dc228dfa55d9bbe5b0a6dfb9a35848c`, HEAD identical
  (clean vs HEAD).
- All four match the dispatch pins; item-scoped diff
  `git diff e3269f18b3931d2f7c15dc38f298455ba055b61f --name-only`
  is the plan edit alone
  (`docs/dry/dry-0_0_15.md`); the artifact itself is
  untracked scratch. Zero-edit confirmed independently.

### Reconciliation vs Findings (Worker-2)

Read `## Findings` only after the trace above was on disk.
Verdict-by-verdict adjudication on fresh evidence:

- F1 count-1 + owner: AGREE. My trace re-derived the same
  owner (`_extend_only_projection` `:742`-`:773`), the same
  3 consumers at the same lines (`:961`, `:1011`, `:1386`),
  the same composed unpack with the same 4 callers, and the
  same 2 downstream mint sites (`:612`, `:1181`). My
  challenges 1/2/3/5 match C-B/C-C/C-A/C-D at counts
  1/1/1/0. Owner reasoning coincides (narrowest importable
  owner; `connection.py` already imports from
  `nested_planner`). No difference.
- 12 exclusions: AGREE on all. My 9-neighbor pass maps onto
  R2/R3/R4/R5/R6/R8/R9/R10 with the same contract
  differences; W1's further rows R1 (unpack read-vs-rewrite),
  R7 (walker alias, which I independently grep-verified as
  zero-reader), R11 (diff prose — body at `plans.py:1394`
  composes, verified by my own read), and R12 (G2 gate —
  consistent with the probe's identity arms on unmasked
  querysets) are each sound and each carries a contract
  difference + trigger. W1 is a superset of my pass; no row
  is wrongly excluded or thinly triggered.
- D1: AGREE. My AST census independently says exactly 4
  production callers; the quoted docstring text matches
  `plans.py:588`-`:590` verbatim; the omission of
  `_extend_only_projection` is genuine staleness. Routing
  (minor doc-only, left unfixed, Worker-0 homing) is
  correct per DRY.md "never fixed inside the item" (the f16
  homing precedent is consistent; the rule alone decides it).
- No-other-defect: AGREE (spot-checked the owner docstring,
  the `_keyset_order_state` projection clause, the planner
  branch comment, and the 2-mint audit against my own
  census — all match).
- Matrix: AGREE on all six axes. Axis-2 inapplicability
  reason is sound (no await; extension precedes the fetch
  split). Axis-5 oracle independence holds: the probe
  asserts independently spelled frozensets; its unpack reads
  are shared read infrastructure, not the owner it checks.
- Structural gate none-landed: ACCEPT. A per-helper
  existence test is barred by DRY.md; a mechanism census
  over all `.only()` writers would span three families no
  single item owns; the re-run recipe is given — and I
  effectively re-ran it (my AST censuses above). No negative
  control is owed for a gate that does not exist.
- Pending-execution "None": CORRECT. No `proof:` is owed
  (inventory-shaped verdict; the one behavioral probe ran
  green twice — W1's run plus my re-run below). Plain
  `verified`, not pending-execution.
- Cells: default EXECUTED (my re-run:
  `tests/test_keyset_connection.py::test_extend_only_projection_passthrough_arms`,
  1 passed, shared venv); sharded/pg `inapplicable by
  construction` is RIGHT — the rule is pure queryset-shaping
  (lazy `.only()`/`.defer()` construction + attribute
  reads; the owner body reaches no database, alias, or
  dialect decision), within the f18 ruling and the accepted
  f29 precedent.
- Index rows owed: NONE — endorsed. The family row already
  exists; no new family is named; D1 routes to Worker-0
  homing, not the index.
- Freshness: W1's 8-row table corroborated in full — every
  WT pin re-derived identical, baseline == WT on all seven
  baseline-checked files, dispatch pins match, item diff is
  the plan edit alone, no `## Implementation` section,
  status count 478 stable.
- Dirt attribution: corroborated mechanically — 31/3/3 hunk
  headers as claimed, zero hunk ranges overlapping any F1
  line (nearest miss: the `connection.py` 1014-1020 docstring
  hunk starts 3 lines below the `:1011` call site), zero F1
  vocabulary mentions in any diff body.

Gates (Worker-2, fresh runs):

- `ruff format --check` + `ruff check` on the four indexed
  files: both pass (4 files already formatted; all checks
  passed). The tracked diff is empty, so this is the
  vacuous-but-recorded form.
- `uv run mypy`: Success, no issues in 119 files, exit 0.
- `uv run basedpyright`: 0 errors, 0 warnings, 0 notes,
  exit 0.
- `uv run python scripts/check_any.py`: 130 allowed uses at
  90 sites, exit 0.
- Probe re-run in the shared venv (slots 1-3 venvs damaged
  per KNOWN): 1 passed.
- Workspace copy at `dry/keysetcol-f30/verify`: OBTAINABLE
  (slot-3, fresh, shared unmoved, trivial command exit 0,
  run id `dry-20261001T113814-1e74e4`). No source-mutating
  proof was needed for this inventory-shaped item.

No new defect found; no `(Worker-2)` entry is owed under
`## Defects`. W1 sections untouched (this section appended
after `## Judgment`; the `Status:` line below is the only
other flip).

Worker-2 verdict: `verified` (plain).
