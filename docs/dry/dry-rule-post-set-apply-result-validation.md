# DRY review: `post-set-apply-result-validation`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Posited rule (index row; owner
candidate [querysets.py][querysets]
`::_validate_post_orderset_result`;
indexed files [querysets.py][querysets],
[list-field.py][list-field],
[connection.py][connection]): what a
field pipeline demands of a public
`FilterSet.apply_*` /
`OrderSet.apply_*` return before any
later step sees it -- routing intent
frozen before the override runs,
awaitable-shape arms per color, then
one seal plus one per-code wording map.
No prior family artifact exists; this
trace is fresh at HEAD `83998e08`
bytes, census-first (the 3 indexed
files were not assumed complete -- the
package-wide AST census proves the
sealed population complete inside them
and finds the unsealed lookalikes
outside them: the filter-child
derivation in [filters-sets.py][filters-sets]
and the consumer-side `FilterSet.apply`
dispatcher, neither indexed).

Verdict: CONFIRM the consolidation.
The family is one rule with a single
owner and zero second bodies: the
validator (F-val), the sync/async
sidecar twins (F-side), and the four
public appliers plus the orderset-class
gate (F-app), all defined once in
[querysets.py][querysets], with all 3
field-by-sidecar combos (list-order,
connection-filter, connection-order)
in both colors composing by name
through 4 call expressions. One
rejection excludes the child-derivation
pair on contract differences with a
trigger (R-child, NEW row) and routes
its one open facet to the maintainer (O1); five
converges re-test prior verdicts from
the family side and need no rows
(s17 seal mechanics, e1 disposal, e5
R-inline wording posture, the e2
resolver-wire split, s16 O2 stale-spec
routing, the run-7 connection D3
consumer census, and the per-site
wording-map split -- seven converges).
Zero production edits; zero defects.

- F-val: the validator --
  [querysets.py][querysets]
  `::_validate_post_orderset_result`
  (`:3078`): captured-model read,
  the one `_SIDECAR_RESULT_POLICY`
  seal call (`:3104`, s17's
  `:3104` shape re-pinned), one
  shape sentence for 6 codes
  (`:3134`), the combined arm
  (`:3148`), the routing arm
  (`:3151`), no `alias` arm (routing
  subsumes -- proof in the
  docstring). Zero second
  validators (probe R1/R2: 1 def,
  2 calls, both in-owner).
- F-side: the twins --
  `::_apply_sidecar_sync` (`:3175`)
  and `::_apply_sidecar_async`
  (`:3218`): freeze (`:3201` /
  `:3234`, the only two
  `_snapshot_routing_intent` calls
  package-wide), invoke the public
  method (`:3202` / `:3235`),
  color arms (sync awaitable
  refusal `:3204`-`:3208`; async
  non-awaitable `:3236`-`:3240`
  and residual `:3242`-`:3246`),
  delegate to the validator
  (`:3209` / `:3248`). The pure
  decision is shared; only the
  await placement differs.
- F-app: the entries --
  `::apply_orderset_sync` (`:3257`)
  / `::apply_orderset_async`
  (`:3275`) /
  `::apply_filterset_sync`
  (`:3296`) /
  `::apply_filterset_async`
  (`:3321`) plus
  `::require_orderset_class`
  (`:3158`, 2 calls `:3271` /
  `:3285`). Four thin declarations
  over the two twin bodies; the
  `None`-gate exists once, on the
  order side only (the connection
  gate guarantees the filter
  class).
- R-child (rejected merge, NEW
  row):
  [filters-sets.py][filters-sets]
  `:2761` / `:2796` invoke
  `child_filterset.apply_sync` /
  `apply_async` with no post-apply
  seal. Different validation
  inputs (per-branch child model +
  parent shard, not the field's
  captured pair), different
  downstream (subquery-RHS
  composition -- nothing windows,
  recomposes, or prefetches
  through it), closed-or-permitted
  posture by construction (Django
  `In.process_rhs` cross-database
  refusal, `Query.combine` model /
  slice checks, single-connection
  execution, narrowing latitude),
  outer contract intact (the
  parent return is sealed at the
  field boundary). O1 routes the
  one open facet (wrong-table
  child served silently via
  coinciding pk subquery) to the maintainer:
  a new-guard question with no
  contract row, not a defect and
  not a merge.
- Converges (no rows): the seal
  body + policy declaration are
  s17's; the 2 dispose calls are
  e1's; the sync-arm wording's
  per-site posture is e5
  R-inline's; the resolver-return
  seal is e2's wire-guard side;
  the spec-050 Edge / test-plan
  pins are confirmed stale with
  s16 O2's routing standing; the
  run-7 connection D3 consumer
  claim is re-derived (kind
  dispatch `:1907` / `:1954`).

Sites and roles (all re-derived at
HEAD `83998e08` bytes; probe-pinned;
WT line in parens where shifted):

- Definitions (F-val, at the
  owner, one body): the validator
  (`:3078`-`:3156`; seal call
  `:3104`; shape map `:3124`-`:3146`;
  combined `:3148`; routing
  `:3151`). Its name says
  orderset; its docstring states
  the contract covers both
  sidecars (naming note in F, no
  row -- renaming is unrelated
  cleanup).
- Definitions (F-side, at the
  owner, one body each): the
  twins (`:3175`-`:3216`,
  `:3218`-`:3255`).
- Definitions (F-app, at the
  owner, one body each): the 4
  appliers + the gate (`:3257`-`:3345`,
  `:3158`-`:3173`).
- Consumers (compose by name, 4
  call expressions / 3 combos /
  6 executions):
  [list-field.py][list-field]
  `:1474` (WT `:1416`) /
  `:1520` (WT `:1462`);
  [connection.py][connection]
  `:1907` (WT `:1916`) /
  `:1954` (WT `:1963`) via
  `::_sidecar_steps` (`:1821`)
  kind dispatch. Downstream
  sealed-output readers (not
  validators):
  `::_check_nonzero_offset_guard`,
  `::_finalize_queryset`.
- Composed-by-name machinery
  (owned elsewhere, converges):
  `::_seal_or_defect` +
  `::_SIDECAR_RESULT_POLICY`
  (s17); `::_snapshot_routing_intent`
  (file-local row, 2 calls both
  here); `::_captured_model`;
  `::_dispose_sync_awaitable`
  (`:3204` / `:3243`, e1);
  `::_defect_message` +
  `::_COMBINED_WHAT` +
  `::_UNSEALABLE_STATE_CAUSES`
  (seal-defect-code-wording /
  s18).
- Excluded callers (R-child):
  [filters-sets.py][filters-sets]
  `:2761` (WT `:2851`) /
  `:2796` (WT `:2886`); the
  `::apply` dispatcher
  delegation `:3652` (WT
  `:3742`) with 0 production
  callers.
- Oracles (independent, literal
  wordings, all present at HEAD
  bytes): unit per-code pins in
  [test-querysets.py][test-querysets]
  (13 wording hits at HEAD:
  type x2, table, evaluated,
  sliced, projection, combined,
  routing x4+); combo pins in
  [test-connection.py][test-connection]
  (8 hits: order sync/async +
  filter sync/async) and
  [test-list-field.py][test-list-field]
  (routing); live pins in
  [test-list-field-api.py][test-list-field-api]
  (order sync, 3 arms),
  [test-list-field-async-api.py][test-list-field-async-api]
  (order async, 3 arms),
  [test-connection-pagination-api.py][test-connection-pagination-api]
  (order sync/async + filter
  async, 3 arms each),
  [test-library-api.py][test-library-api]
  (filter sync, 3 arms),
  [test-multi-db.py][test-multi-db]
  (routing x5),
  [test-combined-visibility-api.py][test-combined-visibility-api]
  (hook-side combined lead --
  supports the per-site split).
- Projections (describe, never
  own): [connection.py][connection]
  `:1837`-`:1839` /
  `:1879`-`:1887` /
  `:1933`-`:1935` (post-sidecar
  seal clauses);
  `::_SealPolicy.require_unevaluated`
  docstring paragraph (s17's
  owner); spec-030 Decision 7
  (composition pipeline,
  narrow-only --
  [spec-030][spec-030]); spec-050
  Edge + test-plan pins (stale,
  routed -- [spec-050][spec-050]).

Freshness (three states;
`ITEM_BASELINE=99c6ec2e80ad8909ae6eb21ad4c429eea153fbbc`
resolves; baseline == worktree
where dirty, by the stash-create
design):

- [querysets.py][querysets]:
  base `cfc773ba` / HEAD
  `392e50d0` / WT `cfc773ba`.
- [list-field.py][list-field]:
  base `1dcb0c43` / HEAD
  `77ddb86c` / WT `1dcb0c43`.
- [connection.py][connection]:
  base `64b85d0e` / HEAD
  `3d6dd424` / WT `64b85d0e`.
- [filters-sets.py][filters-sets]:
  base `ec278851` / HEAD
  `3d307402` / WT `ec278851`.
- [orders-sets.py][orders-sets]:
  base `125d808c` / HEAD
  `c4564c08` / WT `125d808c`.
- Oracles:
  [test-querysets.py][test-querysets]
  `b1fc954b` / `3ff4094a` /
  `b1fc954b`;
  [test-connection.py][test-connection]
  `f80a7f5a` / `615866f6` /
  `f80a7f5a`;
  [test-list-field.py][test-list-field]
  `6d74fcd1` / `9efccda3` /
  `6d74fcd1`;
  [test-library-api.py][test-library-api]
  `099e25b9` / `91f0238b` /
  `099e25b9`; the other 5 live
  files clean (base == HEAD ==
  WT:
  [test-multi-db.py][test-multi-db]
  `893956aa`,
  [test-connection-pagination-api.py][test-connection-pagination-api]
  `dc98a773`,
  [test-list-field-api.py][test-list-field-api]
  `cc1838ce`,
  [test-list-field-async-api.py][test-list-field-async-api]
  `4a570915`,
  [test-combined-visibility-api.py][test-combined-visibility-api]
  `1648cc48`).
- Contract sources:
  [spec-050][spec-050] `73fe1127`
  clean all three states;
  [spec-030][spec-030] `0f7db072`
  clean all three states.
- Installed Django 6.1 (posture
  evidence for R-child):
  `related_lookups.py`
  `639c29d7ba4c`,
  `lookups.py` `eef7bc93a5ce`
  (`git hash-object`, 12-char).
- Population: 117 `.py` at HEAD,
  119 in WT (untracked
  `utils/truth.py` 700 lines +
  `utils/lazy.py` 40 lines;
  probe R1 pins zero family
  defs in them).

Dirt attribution (by content;
judgment at HEAD bytes; zero
tracked edits, so no ledger row
is owed or touched -- and no
`## Owned changes` row covers
these paths):

- [querysets.py][querysets]
  family region: exactly 6
  one-line truth-reader swaps
  (HEAD `:3110` / `:3168` /
  `:3198` / `:3233` / `:3237` /
  `:3244`): `_safe_class_name`
  -> `truth.name` (x2),
  `set_class.__name__` ->
  `truth.name` (x2),
  `_safe_type_name` ->
  `truth.kind` (x2). Concurrent
  `utils/truth.py` migration
  (untracked source; the plan
  records it BLOCKED). Same
  call positions, same
  contracts, same census
  (probe ALL OK both states);
  the 4 applier bodies are
  byte-identical across the
  fork (FPRINTs match).
  Verdict-neutral.
- [list-field.py][list-field]
  (25 hunks),
  [connection.py][connection]
  (31),
  [filters-sets.py][filters-sets]
  (32),
  [orders-sets.py][orders-sets]
  (12): zero dirt lines touch a
  family token (grep-verified);
  family sites byte-identical.
  Imports, validation helpers,
  window/edge machinery,
  metaclasses, ledgers --
  concurrent truth-migration +
  typing work. Verdict-neutral.

## Verification

### Matrix

Each axis discharged package-wide
at HEAD bytes (117 `.py`; probe
`/tmp/e7_probe.py` + full-body
reads; WT re-run identical).

1. Cross-flavor policy mirroring
   -- SEARCHED. FilterSet and
   OrderSet returns answer to
   the ONE validator by design
   (docstring: "the wording is
   the same for both because
   the contract is"; Decision 8
   in the policy comment: "a
   second constant would differ
   on nothing"). The `.apply`
   dispatcher exists only on
   `FilterSet` (`:3637`, 0
   production callers, probe
   R2/R6): the order path never
   calls `get_queryset`, so it
   cannot raise the
   `SyncMisuseError` the
   dispatcher translates -- the
   asymmetry is a contract
   difference, one line, no
   row. No second validation
   body in any flavor (R1/R4).
2. Sync/async twins -- SEARCHED.
   The sidecar twins share the
   validator (the pure
   decision); the arms differ
   only where color forces it
   (refuse-awaitable vs
   require-awaitable-then-refuse-residual;
   the `await` is written where
   it happens, the same
   principle the connection
   pipeline docstring states).
   The 4 appliers pair by
   color; oracles pin all 6
   executions (3 combos x 2
   colors). Intentional split,
   shared core (principle 5).
3. Derived rather than repeated
   knowledge -- SEARCHED.
   `method_name` is derived
   once per twin from
   `set_class.__name__`
   (`:3198` / `:3233`) and
   threaded into the validator;
   no site re-derives it (R2:
   2 validator calls, both
   in-owner). Wordings spelled
   once each (R4: 5 tokens x1;
   3 combined leads
   classified). Oracles spell
   every wording literally
   (independent -- none reads
   the owner). No second
   derivation.
4. Inverse / round-trip pairs --
   INAPPLICABLE with reason:
   the rule is a one-way gate
   (validate + seal a return),
   not an encode/decode,
   pack/unpack, or build/parse
   pair; no grammar has two
   halves to separate. One
   line, no surface exists.
5. Contracts restated in another
   medium -- SEARCHED. Media
   census: 1 validator body +
   2 twin bodies + 4 applier
   decls (definitions); 4 call
   expressions (consumers); 9
   oracle files (independent,
   literal); 5 projection
   sites (3 connection
   docstring clauses, 1 policy
   docstring paragraph, spec-030
   D7) + 1 stale projection set
   (spec-050 pins, routed).
   Each medium classified; the
   contract is stated once, at
   the owner.
6. Enforcement by omission --
   SEARCHED. Complete
   `apply_*` invocation census
   (R2: 3 sync + 2 async, all
   classified): 2 sealed
   (`set_class`, in-owner), 2
   unsealed (`child_filterset`,
   R-child), 1 internal
   delegation (`cls`, 0
   production callers).
   `OrderSet` has no inner
   apply recursion (its
   docstring states the
   contrast; probe-pinned 0
   calls). No member lacks a
   guard a contract source
   requires (axis-6 bar --
   R-child records the
   differences, O1 routes the
   open facet).

### Enumeration

Instrument: `/tmp/e7_probe.py`
(AST def/call census + production
token search over all 117 package
`.py`; no Django import) run at
HEAD bytes (ALL OK) and WT
(ALL OK, shifted lines) -- see
`## Pending execution`. Every
member lands below; nothing
sampled.

- Family defs (R1): 8 names x
  exactly 1 def, all in
  [querysets.py][querysets]
  (validator `:3078`,
  twins `:3175` / `:3218`,
  appliers `:3257` / `:3275` /
  `:3296` / `:3321`, gate
  `:3158`; async color
  re-checked per def).
- Validator calls (R2): exactly
  2, both in-owner (`:3209` /
  `:3248`).
- Public-method invocations
  (R2): `apply_sync` x3
  (sealed `:3202`, child
  `:2761`, delegation
  `:3652`), `apply_async` x2
  (sealed `:3235`, child
  `:2796`). `.apply(` x2, both
  optimizer plans -- 0
  `FilterSet.apply` production
  callers.
- Consumer refs (R2): 4 call
  expressions -- list direct
  x2 (`:1474` / `:1520`),
  connection kind-dispatched
  x2 (`:1907` / `:1954`
  binding both appliers each)
  -- covering 3 combos x 2
  colors = 6 executions. The
  owed 3-combo re-census:
  CONFIRMED, all through the
  one seal.
- Seal composition (R3): 1 of
  5 `_seal_or_defect` calls
  carries
  `_SIDECAR_RESULT_POLICY`
  (`:3104`); policy defs x1
  (`:2915`); freeze calls x2,
  both in the twins (`:3201` /
  `:3234`); gate calls x2
  (`:3271` / `:3285`); dispose
  calls in the twins x2
  (`:3204` / `:3243`,
  grep-pinned -- the probe's
  INFO prefix missed the
  `32xx` arm).
- Wording tokens (R4,
  production only): 5 x
  single-site (shape `:3134`,
  routing `:3151`, gate
  `:3170`, sync-arm `:3206`,
  residual `:3245`); combined
  leads x3 (`:3148` validator,
  `:4146` hook,
  `permissions.py:453`
  cascade) + the
  `apply_type_visibility`
  source lead (distinct
  prefix, 4th tail consumer).
- Dispatchers (R6):
  `FilterSet.apply` x1,
  `OrderSet.apply` x0.
- FPRINTs (normalized AST
  dump, HEAD -> WT): 4
  appliers IDENTICAL
  (`55851059` / `88c04cc4` /
  `9ac43d4f` / `fe9c5b51`);
  validator + twins + gate
  differ by exactly the 6
  truth-reader swaps (dirt
  attribution above).

### Challenges

Each change posited +
authoritative-definition count
(consumers / oracles /
projections listed, never
counted). All counts at HEAD
bytes.

- C1 (defect-code axis): a 9th
  seal code starts arriving
  (new `_seal_or_defect`
  defect). Moves: the
  validator's map (+1 arm) --
  count 1. By construction a
  code with no arm still
  self-names via
  `_defect_message` as a
  framework defect (fail
  loud, never silent).
  Oracles +1 pin (not
  counted).
- C2 (wording axis): reword
  the shape sentence / the
  routing arm / the combined
  lead. Moves: 1 site each
  (`:3134` / `:3151` /
  `:3148`; the combined tail
  moves once in
  `_COMBINED_WHAT`, owned by
  the wording family).
  Count 1 + layered. No
  second spelling exists
  (R4).
- C3 (combo axis): a 4th
  field-by-sidecar combo (new
  field or new sidecar kind).
  Moves: 0 existing defs -- a
  new applier composes the
  twins + validator by name;
  `method_name` derives from
  the new class (no branch
  to extend). Count 0
  (pure addition proves the
  boundary).
- C4 (color axis): change the
  async residual policy / the
  sync-misuse recourse.
  Moves: 1 arm each (`:3242`
  / `:3204`; the sync wording
  posture converges e5
  R-inline). Count 1 each.
  Merging the twins would
  hide the `await` (refused).
- C5 (routing-input axis):
  change freeze semantics
  (new intent field). Moves:
  `::_snapshot_routing_intent`
  (file-local owner) 1; the
  validator's pin
  pass-through 0
  shape-change. Count 1,
  layered -- freezing is
  composed, not owned here.
- C-alias (subsumption): render
  `alias` distinctly at the
  validator. Moves: 0 --
  the code cannot arrive
  (routing subsumes it at
  THIS site only; proof in
  the docstring). Refused by
  construction, not by
  taste.
- M-child (merge challenge):
  seal the child derivation
  through the validator.
  REFUSED (R-child): the
  validator's inputs do not
  fit (D1), the downstream
  differs (D2), the posture
  is closed-or-permitted
  (D3), the outer contract
  holds (D4). Count:
  not-one-rule (0 shared
  definitions to merge).

Every challenge ends count <=
1 with the change landing in
exactly one definition (or
zero, by construction). No
challenge forces two
definitions to move together.

## Findings

### F -- CONFIRMED: the one post-sidecar seal

- Contract + variation: a
  public `FilterSet.apply_*`
  / `OrderSet.apply_*`
  return received by a field
  pipeline must still be a
  lazy, unsliced queryset of
  the captured model's rows
  on the frozen connection
  (combinator served as its
  pk set or refused when the
  rewrite would lose rows),
  else a typed
  `ConfigurationError`
  naming the method. Varies
  on: defect code (8 arms),
  sidecar kind x color (3
  combos x 2), color
  awaitable-shape arms. The
  `None`-orderset direct-call
  gate rides the order
  entries.
- Sites + roles: 8
  definitions, all at the
  owner (see System trace);
  4 consumer call
  expressions (list x2,
  connection kind dispatch
  x2); 9 oracle files; 5 +
  1 projections. The
  validator's name says
  orderset while covering
  both sidecars -- the
  docstring states the
  shared contract, and the
  policy comment cites
  Decision 8; renaming is
  unrelated cleanup, out of
  scope (no row, no
  defect -- the prose is
  accurate).
- Challenges: C1-C5 +
  C-alias, all count <= 1
  (see above).
- Owner + lifetime:
  [querysets.py][querysets]
  -- the narrowest module
  every consumer already
  imports for queryset
  machinery (imports
  verified at list-field
  `:96`-`:97`, connection
  `:128`-`:131`), holding
  the seal, the freeze, the
  captured-model seam, and
  the defect grammar it
  composes (principle 7;
  dependency direction
  wins -- neither field
  module can own what both
  import). No stored
  derivation (the frozen
  intent is a call-local
  record: owner the twin
  frame, validity the one
  apply call, no mutation,
  no cache -- principle 4
  pure).
- Migration: none -- the
  consolidation already
  holds (single bodies,
  by-name composition).
  Zero edits.
- Distinct behavior: the
  per-site wording-map
  split stays (converge,
  see below); the twin
  color split stays (C4);
  the order-only `None`
  gate stays (the filter
  class is guaranteed by
  `::_sidecar_steps` -- a
  gate-vs-guard contract
  difference); the child
  derivation stays
  unsealed (R-child).
- Behavioral proof:
  static-reviewed -- zero
  edits, so no observable
  change exists to prove;
  every combo x arm is
  oracle-pinned (System
  trace oracle census;
  each pin names the
  wrong result it
  rejects). No execution
  converts to a proof
  run; the probe runs
  are census evidence
  (see Pending
  execution).
- Structural gate:
  gate-only finding with
  justification, no new
  test. Behavioral pins
  already cover every
  combo + arm (live
  oracles); the plausible
  bypass (a new pipeline
  calling `apply_*`
  without the seal) is
  not gate-shaped -- a
  call-shape gate over
  the 5 apply invocations
  would fire on the 2
  legitimate child sites
  (R-child), and a gate
  born red is a defect,
  not a gate. No bespoke
  existence test per
  helper.
- Coupling: none (zero
  edits; nothing must
  land together).
- Freshness: all
  fingerprints in System
  trace; probe FPRINTs
  pin the 8 bodies at
  both states.

### R-child -- REJECTED: seal the child derivation here (NEW row)

Shared form considered:
routing
[filters-sets.py][filters-sets]
`:2761` / `:2796`
(`child_filterset.apply_*`)
through
`::_validate_post_orderset_result`
(or a twin of it).

Contract differences:

- D1 (inputs): the validator
  takes the FIELD's
  `(target_type, captured
  model, frozen routing)`;
  the child answers to a
  per-branch (child model,
  parent shard) pair. The
  owner as written cannot
  be called -- sealing the
  child needs a new call
  shape with new inputs,
  not composition.
- D2 (downstream): the
  field seal's axes exist
  to protect recomposition
  (window, paginate,
  refilter, prefetch). The
  child result is composed
  as an `__in` RHS
  subquery and nothing
  recomposes onto it: a
  slice is narrowing
  (permitted -- the seal
  passes `.none()` and
  arbitrary pk sets), an
  evaluated qs re-executes
  (benign cost, the policy
  docstring's own
  cost-not-seal reasoning),
  a combinator is a
  servable set.
- D3 (posture): closed or
  permitted by
  construction, verified
  in installed Django 6.1
  source: cross-database
  subqueries refuse
  (`In.process_rhs`,
  `lookups.py:521`-`:526`);
  `explicit & child_qs`
  refuses model / slice
  mismatch
  (`Query.combine`,
  `query.py:710` /
  `:712`); single-column
  projections refuse
  (`_subquery_fields_len`,
  `lookups.py:508`-`:512`;
  multi-column refuses,
  single-column is served
  as narrowing);
  direct-value returns are
  explicit narrowing
  (within override
  latitude). No new
  `except` arm, no new
  gate -- the composition
  operators own these.
- D4 (outer contract): the
  parent `apply_*` return
  IS sealed at the field
  boundary -- the rule
  holds end to end where
  its contract sources
  place it (owner
  docstring: "the list
  field and the Relay
  connection field";
  spec-030 D7: steps
  AFTER a sidecar -- the
  derivation runs INSIDE
  it).

Challenges: M-child
refused (not-one-rule).
No contract source
extends the seal inward
(spec-027 D8 describes
the derivation without
one; s16 O2's spec-050
pins are stale and
routed).

Reconsideration trigger:
a child-apply return
shape that Django's
`__in` composition
SERVES while violating
the sealed row-set
guarantees -- a nested
override escaping into
served rows where the
field seal would refuse
-- or a spec row
extending the post-sidecar
seal to inner derivation.

Durable home: this
artifact's R-child row
(the plan index); the
validator docstring
already scopes the seal
to the two fields (no
prose edit owed --
zero-edit item).

O1 (ROUTED TO MAINTAINER, not
a defect -- no contract
row names the child):
the table facet is the
one silent shape.
`In.get_prep_lookup`
(`lookups.py:505`-`:515`)
adds `pk` to a plain-qs
RHS with NO model check,
so a child override
returning a wrong-table
qs is served as `IN
(SELECT wrong.id ...)`
matching coincidental pk
overlap -- silent wrong
rows. Feasible shape:
RelatedFilter + child
`apply_sync` override
returning a foreign qs +
nested filter input on
that branch (wire-reachable).
A child-side table
guard would be a NEW
rule (new inputs per
D1, new wording, new
error) -- a feature
decision for the maintainer, not
a merge into this
family. Trigger: the maintainer's
ruling, or the R-child
trigger firing.

### Converges (no new rows)

Each re-tested from the
family side at HEAD
bytes; each endorsed as
written.

- s17 (sealed-execution-queryset):
  the seal body, the 6
  policy declarations
  incl.
  `_SIDECAR_RESULT_POLICY`
  (`:2915`), and the 5
  call shapes incl. the
  `:3104` sidecar shape
  are s17's consolidated
  holding. Re-derived:
  5 seal calls, 1
  sidecar-shaped (R3).
  e7 owns the
  surrounding validator
  + wording + twins +
  appliers only. No
  overlap, no row.
- e1 (awaitable-refusal-and-disposal):
  the twin dispose
  calls (`:3204` /
  `:3243`) compose
  `::_dispose_sync_awaitable`
  by name. e1 names the
  sidecar arms as
  composers (its `:32`
  + `:95` + `:325`
  pins re-checked).
  No row.
- e5 R-inline
  (sync-boundary-recourse-wording):
  the sync-arm wording
  (`:3206`: names
  `apply_sync` + the
  sync-resolver context)
  is e5's censused
  sidecar inline; its
  per-site verdict +
  trigger ("subject or
  remedy generalizes")
  stand -- unfired
  (the async arms are
  shape refusals, not
  recourse, and stay
  per-site here under
  the same posture).
  No row.
- e2 split
  (recomposition-illegal-source-rejection):
  the resolver-return
  seals
  (`post_process_queryset_result_*`,
  `prepared_resolver_source`)
  guard consumer
  `resolver=` values,
  a different subject
  from public apply
  returns. Converges
  e2's seal-vs-wire-guard
  split. No row.
- s16 O2 (spec-050 stale
  pins): re-checked --
  the Edge sentences
  ("non-combined ... plain
  queryset") and the
  test-plan sentence
  ("mechanically
  validated as ...
  non-combined") pin the
  pre-rewrite refusal
  rule and contradict
  HEAD's serve-or-refuse-by-rewrite
  (`:3148` + pk-set
  rewrite; oracles pin
  both the serving and
  the refusal). Stale
  confirmed; routing to
  the spec-050 card
  stands. No row.
- run-7 connection D3:
  re-derived -- the
  connection is a
  CONSUMER via kind
  dispatch (`:1907` /
  `:1954`, both
  appliers bound each);
  the owed 3-combo
  re-census is CONFIRMED
  (list-order,
  connection-filter,
  connection-order, all
  through the one seal,
  both colors). No row.
- Per-site wording maps
  (validator `:3100` vs
  hook `:4120` vs source
  `:4240` vs cascade):
  each renders the
  subset it can reach
  (validator: +routing,
  -alias; hook: +alias,
  -routing/-evaluated)
  over shared tails
  (`_COMBINED_WHAT`,
  `_UNSEALABLE_STATE_CAUSES`,
  `_defect_message`).
  The split is recorded
  at the validator
  docstring (durable
  home in-tree); tails
  belong to
  seal-defect-code-wording
  / s18. No row.

## Defects

None. The trace found no
non-duplication bug: the
validator docstring's
`alias`-subsumption proof
was re-checked against
the seal order (routing
before alias) and holds;
the stale spec-050 pins
are routed, not defects
of this family; O1 routes
to the maintainer as a newly-proposed
guard (no contract row),
not a defect.

## Pending execution

- `proof:` `uv run python
  scripts/workspace.py run
  dry/postset-e7/consolidate
  -- sh -c 'rm -rf head-tree
  && mkdir head-tree &&
  git --git-dir=~/.t3/worktrees/django-strawberry-framework/dry-0015/.git
  archive HEAD
  django_strawberry_framework
  | tar -x -C head-tree &&
  python3 /tmp/e7_probe.py
  head-tree'` --
  execution-verified (run
  `dry-20261001T021510-89921c`,
  exit 0, `E7-PROBE ALL OK`;
  discharges the F def/call
  counts, the R2 5-site
  apply census, the R3 seal
  composition, the R4
  wording singularity, and
  the R6 dispatcher census
  at HEAD bytes). `<copy>` =
  `/private/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/dsf-ws/0b901faeac791a7b/dry/slots/slot-2`.
  The `head-tree/`
  extraction + `/tmp/e7_probe.py`
  stay on disk for Worker-2;
  remove by explicit path
  after verification. (An
  earlier run,
  `dry-20261001T021454-956fb3`,
  failed before any census
  -- the copy is not a git
  repo, so bare `git
  archive` errored; harness
  misconfiguration, no
  evidence drawn,
  superseded.)
- Worktree comparison (same
  address, `sh -c 'python3
  /tmp/e7_probe.py .'`):
  run
  `dry-20261001T021537-78cd09`,
  exit 0, identical ALL OK
  (same counts, shifted
  lines; 4 applier FPRINTs
  byte-identical, 4 bodies
  differ by exactly the 6
  truth-reader swaps) --
  decision-neutral drift
  proved. Informational;
  discharges nothing.
- Shared-tree authorization
  unspent: zero edits
  landed, no oracle added,
  no pytest run -- no
  `gate:` command owed.
  Sharded / pg cells
  inapplicable by
  construction (the finding
  is code singularity over
  def/call/wording counts;
  no database, alias, or
  dialect decision varies
  them; the routing
  behavior itself is
  covered by the existing
  `test_multi_db.py` live
  oracles, not by this
  finding).

## Judgment

The post-set-apply result
validation is one rule
with a single owner: the
validator + wording map,
the freeze-call-arm-validate
twins, and the four
applier entries plus the
orderset-class gate are
each defined once in
[querysets.py][querysets],
with 2 validator calls, 2
freeze calls, 2 gate
calls, 2 dispose calls,
and 4 consumer call
expressions covering all
3 combos in both colors
composing by name, and
zero second bodies
package-wide (AST census:
8 family defs at 1 site
each, 5 apply invocations
classified, 5 wording
tokens single-sited, 3
combined leads
classified, 0 production
`FilterSet.apply`
callers). The lookalikes
are distinct: the child
derivation pair stays
unsealed on contract
differences with a
trigger (R-child, NEW
row; O1 routes the
table facet to the maintainer),
and the seal mechanics,
disposal, wording
posture, wire-guard
split, stale-spec
routing, and consumer
census all converge on
prior verdicts. Zero
production edits; zero
defects. The family is
CONFIRMED as
consolidated.

Index impact for Worker-0
(exact replacement text;
Worker-0 alone edits the
plan):

- Flip the family row to
  (single table row):

  ```text
  | `post-set-apply-result-validation` | `utils/querysets.py::_validate_post_orderset_result` | `utils/querysets.py`, `list_field.py`, `connection.py`, `filters/sets.py` (R-child exclusion), `orders/sets.py` (apply defs, no inner recursion) | Family `post-set-apply-result-validation` | consolidated (e7: 8 defs single-owned -- validator + wording map + twins + 4 appliers + gate; 4 call expressions / 3 combos / 6 executions compose by name; 0 second bodies; 1 new rejection row, 7 converges) |
  ```

- Add the R-child rejection
  row (single table row,
  immediately below the
  family row):

  ```text
  | `child-derivation-unsealed` | `django_strawberry_framework/filters/sets.py::_derive_related_visibility_querysets_sync` (+ `_async` twin; child `apply_*` returns `:2761` / `:2796` unsealed -- different inputs, subquery-RHS downstream, closed-or-permitted posture, outer seal intact; merge excluded with trigger; O1 table-facet silence routed to the maintainer; named by Family `post-set-apply-result-validation` e7) | `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/utils/querysets.py` | Family `post-set-apply-result-validation` | rejected |
  ```

- All 7 converges (s17,
  e1, e5 R-inline, e2
  split, s16 O2, run-7
  D3, per-site maps)
  need no rows.

Item-scoped diff state:
no tracked edits; one
new untracked artifact
(this file).

## Independent verification (Worker-2)

Instrument: `/tmp/e7_w2_probe.py`
(independent AST + text
census, no Django import;
expectations encoded from
my own reads, not W1's).
Runs at
`dry/postset-e7/verify`
(slot-3, digest
`sha256:792478cb...`,
same tree W1 audited):
HEAD `83998e08` bytes
`dry-20261001T022821-464915`
(first run: 2 of MY
expectations wrong --
`combined-what-loads-4`,
`apply-defs-filterset-only`
-- disclosed, corrected,
re-run) and
`dry-20261001T022948-737f22`
(`W2-PROBE ALL OK`, 117
`.py`); worktree
`dry-20261001T022955-2b8ee5`
(`W2-PROBE ALL OK`, 119
`.py`, shifted lines).
W1's cited runs audited
3/3 ok (`audit`:
`...021510` exit 0,
`...021454` exit 1
honest harness failure,
`...021537` exit 0).

### Own trace

Owner I would choose:
[querysets.py][querysets]
-- both field modules
already import queryset
machinery from it (list
`:95`-`:97`, connection
`:127`-`:131`), and it
holds the seal, the
freeze, the captured-model
seam, and the defect
grammar (principle 7;
dependency direction
wins). Same owner as W1.

My counts at HEAD bytes
(probe + full-body
reads): 8 family defs at
1 site each, all in the
owner (validator `:3078`
sync; twins `:3175` sync
/ `:3218` async; gate
`:3158`; appliers `:3257`
/ `:3275` / `:3296` /
`:3321` with matching
colors); 2 validator
calls, both in the twins
(`:3209` / `:3248`); 2
freeze calls, both in the
twins (`:3201` / `:3234`;
def x1 `:2985`,
package-wide); 2 gate
calls in the order
appliers (`:3271` /
`:3285`); 2 dispose
calls in the twins
(`:3204` / `:3243`;
package-wide x4, the
other two unrelated);
5 `apply_*` invocations:
3 sync (sealed
`set_class` `:3202`,
child `:2761`,
dispatcher `cls`
`:3652`) + 2 async
(sealed `:3235`, child
`:2796`); `.apply(` x2,
both optimizer plans
(`extension.py:1336`,
`walker.py:1237`), so 0
`FilterSet.apply`
production callers;
applier names: 2 direct
calls (list `:1474` /
`:1520`) + 4 ternary
loads (connection
`:1907` x2 / `:1954`
x2) = 4 call expressions
/ 3 combos / 6
executions through the
one seal; 5 seal calls
(`:2608` prefetch,
`:3104` sidecar-shaped
+ the one
`expected_routing`,
`:3897` raw-list,
`:4234` source,
`:4340` result),
1 sidecar-shaped;
policy def x1 (`:2915`),
6 constructions;
wording tokens x1 each
(shape `:3134`, routing
`:3151`, gate `:3170`,
sync-arm `:3206`,
non-awaitable `:3238`,
residual `:3245`;
combined lead
`returned a combined
queryset` x3 at
`:3148` / `:4146` /
`permissions.py:453`);
no `filterset_class`
gate (0 hits);
`FilterSet.apply` def
x1, `OrderSet.apply`
x0; `orders/sets.py`
inner apply calls 0
(its `apply_sync` /
`apply_async` defs at
`:788` / `:821`).
Zero second bodies:
no other def of any
family name, no other
sidecar-shaped seal
call, no second
spelling of any
family wording.

Roles: 8 definitions
at the owner;
consumers compose by
name (list direct,
connection kind
dispatch via
`::_sidecar_steps`
`:1821`, whose
supplied-AND-declared
gate guarantees the
filter class -- the
order-only-`None`-gate
contract difference);
oracles pin every
code x color literally
for family-owned
wordings (see W2-E4
for the shared-tail
qualification);
projections describe
(connection docstring
clauses, policy
paragraph, spec-030
D7; spec-050 pins
stale, routed).

### Reconciliation

Agreements: every
count above reproduces
W1's pins exactly;
the seal order
(type-table-untrusted-routing-
evaluated-sliced-projection-
combined-alias) and
the alias-subsumption
proof re-derived from
the seal body hold in
BOTH freeze cases
(routed: candidate
pinned to
`intent.db`; unrouted:
candidate `None`,
required alias a
resolved string --
neither fires the
alias arm); the
per-site wording
split holds
(validator 8 arms
+routing -alias, hook
7 +alias
-routing/-evaluated,
source 6, cascade
root 5 / edge 6,
walker direct);
all 7 converges
endorsed on the
merits (s17: 6
constructions / 5
shapes / `:3104`
re-pinned by my
probe; e1 names the
twins as composers;
e5 R-inline censuses
the sidecar inline
with trigger
unfired -- the async
arms raise
`ConfigurationError`,
not recourse; e2 R1
guard-vs-seal split,
resolver-source
guards a different
subject; s16 O2
first-recorded,
spec sentences
re-read stale;
run-7 D3 re-census
CONFIRMED by P5;
per-site maps, see
W2-E2); zero
production defects.

Differences (5,
all verdict-neutral;
exact replacements
under Errata): W2-E1
D3 inverted adjective;
W2-E2 tail-consumer
undercount (6, not
4); W2-E3 dirt pins
off-by-2 (4 of 6);
W2-E4 oracle
independence
overclaim; W2-E5
index-row long paths.

### Enumeration

Checked member by
member against my
probe: family defs
8/8, validator calls
2/2, apply
invocations 5/5
with receivers,
consumer refs 2+4,
seal calls 5/5
classified,
freeze/gate/dispose
2/2/2, wording
tokens 6x1 + lead
x3, dispatchers
scoped
(`FilterSet` x1 /
`OrderSet` x0 / 5
other-family `def
apply`), FPRINTs
(HEAD vs WT: 4
appliers identical
under my scheme,
validator + twins
+ gate differ).
Two members missed
by W1's lead census
(W2-E2); all other
members land.

### Matrix (Worker-2)

1. Cross-flavor --
SEARCHED. One
validator, both
sidecars (docstring:
"the wording is the
same for both
because the contract
is"). Dispatcher
asymmetry is a
contract difference
(order path never
calls `get_queryset`
-- 1 docstring-only
ref -- so cannot
raise the
`SyncMisuseError`
the dispatcher
translates). No
second body.
2. Twins -- SEARCHED.
Shared validator;
arms differ only at
the await boundary.
Intentional
(principle 5).
3. Derived knowledge
-- SEARCHED.
`method_name`
derived once per
twin; wordings x1
(6 tokens + lead
x3); combined tail
consumed by name by
6 sites (W2-E2).
4. Round-trip --
INAPPLICABLE: one-way
gate, no
encode/decode pair.
5. Media -- SEARCHED.
8 defs; 4 consumer
expressions; 9
oracle files
(family wordings
literal; shared
tail composed by
name -- W2-E4); 5
projections + 1
stale set, routed.
6. Omission --
SEARCHED. 5 apply
invocations
classified (2
sealed, 2 R-child,
1 dispatcher with 0
callers); no inner
order recursion.
No member lacks a
required guard.

### Challenges (Worker-2)

C1 count 1 (fail-loud
default verified in
`::_defect_message`);
C2 count 1 per site
+ tail single-owned
(def x1 `:3973`);
C3 count 0 (thin
declarations,
derived
`method_name`);
C4 count 1 each
(`:3242` / `:3204`
arms); C5 count 1
layered (freeze
file-local, plan
row; def x1, calls
2 in-twins);
C-alias count 0
(proved both cases);
M-child REFUSED
(not-one-rule).
Every challenge
ends count <= 1.

### R-child + O1 (Worker-2)

D1 (field's captured
pair vs per-branch
child model +
parent shard),
D2 (`<rel>__in`
RHS via
`::_apply_related_constraints`,
nothing
recomposes), D3
(closed-or-permitted:
Django 6.1
`In.process_rhs`
cross-db refusal,
`Query.combine`
model/slice
refusals, field-count
refusal -- see
W2-E1; in-tree
explicit-mix typed
guard), D4 (parent
return sealed at
the field boundary;
spec-027 D8
describes the
derivation with no
inner seal) all
re-derived from
primary sources.
Trigger sound (a
served shape
violating sealed
row-set guarantees,
or a spec row
extending the seal
inward). Name
`child-derivation-unsealed`
free (no HEAD
collision) and
well-formed. O1
routing correct:
not a defect (no
contract row names
the child -- the
validator docstring
scopes the seal to
the two fields),
not a merge
(inputs do not
fit), so a
new-guard question
for the maintainer; the
silence chain
(no-model-check pk
completion in
`In.get_prep_lookup`,
verified) is
wire-reachable as
described.

### Freshness (Worker-2)

All 16 file
fingerprints
reproduced exactly
(base/HEAD/WT):
querysets
`cfc773ba` /
`392e50d0` /
`cfc773ba`,
list-field
`1dcb0c43` /
`77ddb86c` /
`1dcb0c43`,
connection
`64b85d0e` /
`3d6dd424` /
`64b85d0e`,
filters-sets
`ec278851` /
`3d307402` /
`ec278851`,
orders-sets
`125d808c` /
`c4564c08` /
`125d808c`,
oracles
`b1fc954b` /
`3ff4094a`,
`f80a7f5a` /
`615866f6`,
`6d74fcd1` /
`9efccda3`,
`099e25b9` /
`91f0238b`, five
clean (`893956aa`,
`dc98a773`,
`cc1838ce`,
`4a570915`,
`1648cc48`),
specs `73fe1127` /
`0f7db072` clean.
Django 6.1 hashes
match (`639c29d7ba4c`,
`eef7bc93a5ce`);
`query.py`
`22dd479d67d9`
(my combine
citation).
Population 117
HEAD / 119 WT
(untracked
`truth.py` +
`lazy.py`; probe
pins zero family
defs in them).

### Dirt (Worker-2)

Zero-edit CONFIRMED:
`ITEM_BASELINE` ->
WT is plan
bookkeeping only
(`dry-0_0_15.md`
+47, Worker-0
dispatch notes);
HEAD -> WT is
concurrent dirt
(193 files). Family
region diff is
exactly 6 one-line
truth-reader swaps
(my region diff;
applier span
untouched); 18
family tokens grep
0 in the other
four files' diffs;
7 call lines
byte-identical,
shifted (WT pins
all match W1's).
Census-neutral
(WT probe ALL OK).
`truth.*`
semantic
equivalence belongs
to the migration
review, not e7;
verdict-neutral
here. Line pins:
see W2-E3.

### Structural gate (Worker-2)

Gate-only with
justification,
endorsed. Would-be
population (5 apply
invocations) run
against the tree is
red on the 2
legitimate child
sites -- born red,
correctly refused
per DRY.md (a red
result is a defect,
not a gate; e2
deferred the same
shape with reason).
No gate relied on,
so no
`prove_failability`
owed. Behavioral
pins cover every
combo x arm (unit
per-code tests +
twin-arm pins at
unit and live
tiers, verified by
token census).
No pytest owed:
zero-edit, AST-only
census, no
DB/alias/dialect
surface; sharded/pg
inapplicable by
construction.
`## Pending
execution` shape
correct (`proof:`
census runs, both
exit 0 + 1 honest
environment
failure; no `gate:`
owed).

### Prose + tool gates (Worker-2)

No process
provenance (run ids
+ probe paths are
DRY-required
evidence citations);
`path::Symbol`
citations + `:NN`
pins allowed in
`docs/dry/dry-*.md`
scratchpads; no new
tests owed
(zero-edit); ASCII
only (no owned
`.py` text).
Ruff on the
artifact: N/A
(Python-only tool,
markdown path).
Markdown scaffold:
`check_trailing_commas.py
--check` on the
artifact exits 0
(path excluded from
the source-layout
rules; this section
adds no link refs
and the canonical
footer stays last
regardless).

### Errata (Worker-2, verdict-neutral)

Apply at merge
(exact replacements;
W1 resubmission not
required -- no row
changes):

- W2-E1 (D3 prose):
"single-column
projections refuse
(`_subquery_fields_len`,
`lookups.py:508`-`:512`;
multi-column refuses,
single-column is served
as narrowing)" --
the lead clause is
inverted (Django
refuses the COUNT
MISMATCH). Replace
"single-column
projections refuse"
with "multi-column
projections refuse".
The parenthetical
already states the
correct rule; the
posture conclusion
stands.
- W2-E2 (R4 + per-site
converge): "combined
leads x3 ... + the
source lead (distinct
prefix, 4th tail
consumer)" names 4
of 6 `_COMBINED_WHAT`
consumers. Add: the
cascade ROOT map
(`permissions.py:387`,
"got a combined root
queryset") and the
optimizer walker
plan-time refusal
(`walker.py:1424`,
"the hinted Prefetch
queryset is combined").
Both fit the same
per-site pattern
(own lead, shared
tail); no row owed.
- W2-E3 (dirt pins):
HEAD swap lines
`:3110` / `:3168` /
`:3237` / `:3244`
read `:3112` /
`:3170` / `:3239` /
`:3246` (grep-pinned;
`:3198` / `:3233`
correct; W1's own
R4 `:3170` / `:3245`
agree with mine).
Substance (6
one-line swaps)
confirmed.
- W2-E4 (oracle
wording): "Oracles
spell every wording
literally
(independent --
none reads the
owner)" overclaims:
combined
expectations spell
the family-owned
LEAD literally and
compose the shared
tail via
`_COMBINED_WHAT.format`
(correct layering,
principle 6; e.g.
`test_querysets.py:5671`-`:5674`).
Replace with
"family-owned
wordings literal;
the shared tail
portion composes
`_COMBINED_WHAT` by
name". No oracle
change owed (tail
single-owned; a
literal tail pin, if
wanted, belongs to
the wording family,
not e7).
- W2-E5 (index text):
the R-child row uses
long
`django_strawberry_framework/...`
paths; every table
row (incl. e6's
rejection row) uses
short paths.
Worker-0: emit
`filters/sets.py::_derive_related_visibility_querysets_sync`
and
`filters/sets.py`,
`utils/querysets.py`
in the files column.

### Verdict (Worker-2)

F CONFIRMED (8 defs
single-owned, 4
call expressions /
3 combos / 6
executions compose
by name, 0 second
bodies); R-child
NEW rejection row
endorsed (name,
trigger, O1 routing
to the maintainer); 7
converges need no
rows; zero
production defects.
The family is
CONFIRMED as
consolidated.
Worker-0: flip the
family row with
W1's text, add the
R-child row with
W2-E5 short paths,
apply W2-E1..E4
prose corrections,
tick the plan item
(Worker-0 alone
edits the plan).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md

<!-- docs/SPECS/ -->
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection.py]: ../../django_strawberry_framework/connection.py
[filters-sets.py]: ../../django_strawberry_framework/filters/sets.py
[list-field.py]: ../../django_strawberry_framework/list_field.py
[orders-sets.py]: ../../django_strawberry_framework/orders/sets.py
[querysets.py]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[test-connection.py]: ../../tests/test_connection.py
[test-list-field.py]: ../../tests/test_list_field.py
[test-querysets.py]: ../../tests/utils/test_querysets.py

<!-- examples/ -->
[test-combined-visibility-api.py]: ../../examples/fakeshop/test_query/test_combined_visibility_api.py
[test-connection-pagination-api.py]: ../../examples/fakeshop/test_query/test_connection_pagination_api.py
[test-library-api.py]: ../../examples/fakeshop/test_query/test_library_api.py
[test-list-field-api.py]: ../../examples/fakeshop/test_query/test_list_field_api.py
[test-list-field-async-api.py]: ../../examples/fakeshop/test_query/test_list_field_async_api.py
[test-multi-db.py]: ../../examples/fakeshop/test_query/test_multi_db.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
