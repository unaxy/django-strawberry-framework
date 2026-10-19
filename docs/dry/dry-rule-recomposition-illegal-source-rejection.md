# DRY review: `recomposition-illegal-source-rejection`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Posited rule (naming findings: File `utils/querysets.py` F4,
File `connection.py` F3): a source a surface will recompose onto
(reorder, refilter, window) may not arrive already sliced, because
Django forbids reordering a sliced query and the next transform would
raise a raw `TypeError` outside the typed contract. Owner candidate
[querysets.py][querysets] `::_SealPolicy`; indexed files
[querysets.py][querysets], [connection.py][connection],
[nested-fetch.py][nested-fetch]. No prior family artifact exists;
this trace is fresh at HEAD bytes.

Verdict: REJECT the consolidation. The sweep finds two per-site
rules, each already single-owned, plus two correctly-excluded
neighbors. There is no second definition of either rule anywhere
in the package.

- F-seal: the visibility boundary's sliced-shape refusal --
  [querysets.py][querysets] `::_SealPolicy.reject_sliced` plus the
  `sliced` arm of `::_seal_or_defect`. One arm, one policy field,
  six policy declarations. Surfaces raise `ConfigurationError`
  naming the `get_queryset` / sidecar-result contract.
- F-guard: the connection surface's resolver-contract triage --
  [connection.py][connection] `::_guard_source_not_pre_sliced`.
  One body, two call sites. Raises `GraphQLError` naming the
  `resolver=` contract, before visibility runs.
- R1 (rejected merge): routing the guard through the seal, or
  deleting the guard as a copy. Four contract differences
  (subject, error class, stage, read discipline); every genuine
  rule change moves exactly one side.
- R2 (rejected merge, standing): the optimizer classifier
  [nested-fetch.py][nested-fetch]
  `::unwindowable_child_queryset_reason` degrades plans and never
  rejects; owned by open family
  `unwindowable-child-queryset-classification`.
- R3 (rejected third definition): the slice check inside
  [querysets.py][querysets] `::_combined_lost_property` feeds the
  `combined` defect (rewrite fidelity), never the `sliced` defect.

Sites and roles (all re-derived at HEAD `83998e08` bytes):

- Definitions (2, distinct rules): seal arm
  [querysets.py][querysets] `::_seal_or_defect` (`:3755`-`:3756`);
  guard [connection.py][connection]
  `::_guard_source_not_pre_sliced` (`:1648`-`:1688`).
- Consumers of F-seal: five `sliced` message renderers composing
  `_defect_message` by name -- source wording
  (`:4138`-`:4144`), hook-result wording (`:4259`-`:4265`),
  sidecar shape map (`:3133`-`:3147`, raise `:3152`), cascade root renderer
  [permissions.py][permissions] `::_root_error_renderer`
  (`:380`-`:384`), cascade edge renderer `::_edge_error_renderer`
  (`:445`-`:450`). Policy declarers: six `_SealPolicy` constants
  (`:2880`-`:2932`, two with `reject_sliced=False`, each with its
  downstream-answer prose); [walker.py][walker]
  `::_build_child_queryset` policy selection plus
  `::_build_connection_child_queryset` (seal by name, both
  colors). All wording renderers belong to open family
  `seal-defect-code-wording`; the seal body to consolidated
  `sealed-execution-queryset`.
- Consumers of F-guard: pipeline head
  [connection.py][connection] `::_prepare_pipeline_source`
  (`queryset_guard=` at `:1817`, both colored pipelines) and the
  keyset slicer entry (`:1030`, reached via the
  `_consume_window` / `_consume_fallback` tail whose input does
  not always pass the pipeline head).
- Excluded with reason: classifier (R2); combined-rewrite check
  (R3); [resource-policy.py][resource-policy] slicing (the
  framework's own row bounding, never a rejection -- six prose
  lines, zero `is_sliced` reads); [plans.py][plans] `:1108`-`:1110`
  and [nested-planner.py][nested-planner] `:1271` (prose-only);
  [list-field.py][list-field] (zero `sliced` lines -- seals only,
  absence is coverage not a gap); [utils-connections.py][utils-connections]
  `:162` (page-slice docstring).
- Oracles: guard side --
  [test-connection.py][test-connection] `:2144` (GraphQLError,
  "already-sliced"), `:2455` + `:2468` (hostile query /
  `is_sliced` fail-soft), live [test-keyset-api.py][test-keyset-api]
  `:999` (keyset entry over HTTP); seal side --
  [test-querysets.py][test-querysets] `:1570` + `:1582`
  (ConfigurationError) and the `:5127`-`:5136` matrix rows,
  [test-permissions.py][test-permissions] `:1072` + `:1399`
  (cascade renderers), live sidecar shape rows in
  [test-connection-pagination-api.py][test-connection-pagination-api]
  and [test-list-field-api.py][test-list-field-api]; classifier --
  [test-nested-fetch.py][test-nested-fetch] `:303` matrix,
  [test-walker.py][test-walker] `:1440`-`:1465` + `:5690`.
  Cited by content at HEAD bytes; no pytest run (dispatch
  forbids it).
- Projections: the guard docstring, the `reject_sliced` field
  prose, the seal `sliced` arm prose, the walker child-policy
  comment, the classifier docstring. Verified against their
  bodies before designing on them.

Dirt attribution (by diff content vs `git show HEAD:`, not by
dirty status; no ledger row names the three indexed files, so
every hunk below is concurrent-external):

- [connection.py][connection]: the guard's fail-soft
  unreadable-state arm is REMOVED in the worktree (bare `if
  source.query.is_sliced:`); the `already-sliced` rejection and
  both call sites are intact. Vocabulary (`truth.kind`,
  `truth.own_attr`) marks the hunk as the concurrent `truth`
  migration. The two hostile oracles (`:2455`, `:2468`) are gone
  from worktree [test-connection.py][test-connection] with it;
  the `:2144` oracle survives (`:2233`).
- [querysets.py][querysets]: zero added/removed lines touch the
  slice rule (all `sliced` / `reject_sliced` diff lines are
  context for adjacent `truth.` renames). Seal arm, policy
  field, both `False` declarations, all three message maps
  byte-identical in logic.
- [nested-fetch.py][nested-fetch]: classifier `sliced` arm
  untouched (only the `values` arm line rewritten to
  `truth.is_subclass`, plus the `resolve_strategy` truth
  migration). Matrix oracle survives.
- Decision impact: none. The family question (guard vs seal as
  definitions) is intact in both states; the worktree drift
  widens the read-discipline difference rather than collapsing
  it. Traced at HEAD bytes throughout; the probe ran both
  states to prove the point.

Three-state fingerprints (indexed files):

- [querysets.py][querysets]: HEAD `392e50d0`, worktree
  `cfc773ba`, `9aaaad5d` `8fc556d5`; `dd9c8804` == worktree.
- [connection.py][connection]: HEAD `3d6dd424`, worktree
  `64b85d0e`, `9aaaad5d` `1fca6266`; `dd9c8804` == worktree.
- [nested-fetch.py][nested-fetch]: HEAD `304e2f3e`, worktree
  `b74539d1`, `9aaaad5d` `1678609e`; `dd9c8804` == worktree.
- Nothing moved since `ITEM_BASELINE`
  (`dd9c88040487fadaa82127cbf43f2f7c1cf41c72`); HEAD
  `83998e08d48c911199527ed0411ab8041805c8b5`; snapshot
  `9aaaad5de73f6ff36eea3264e5b085fef1b046cc`.
- Cited files (HEAD / worktree): [permissions.py][permissions]
  `d77c5050` / `42c3c19c`, [walker.py][walker] `bdd9c2f1` /
  `9130aceb`, [nested-planner.py][nested-planner] `3637dc3a` /
  `e5daffc5`, [lateral-fetch.py][lateral-fetch] `583f6d7b`
  (clean), [single-parent-fetch.py][single-parent-fetch]
  `3a4bb89b` (clean), [plans.py][plans] `fdc4b1b0` /
  `3e005158`, [resource-policy.py][resource-policy] `47befb3f`
  / `927b89a2`, [utils-connections.py][utils-connections]
  `735aa454` (clean), [list-field.py][list-field] `77ddb86c`
  / `1dcb0c43`. Oracles (HEAD / worktree):
  [test-connection.py][test-connection] `615866f6` /
  `f80a7f5a`, [test-querysets.py][test-querysets] `3ff4094a`
  / `b1fc954b`, [test-nested-fetch.py][test-nested-fetch]
  `7fbd957b` / `0b65aa96`, [test-walker.py][test-walker]
  `3f5e19a5` (clean), [test-permissions.py][test-permissions]
  `14961acd` / `7cf7b3af`, [test-keyset-api.py][test-keyset-api]
  `315c0372` (clean),
  [test-connection-pagination-api.py][test-connection-pagination-api]
  `dc98a773` (clean),
  [test-list-field-api.py][test-list-field-api] `cc1838ce`
  (clean).

Prior records (run-8 s1 / s16 re-traces, run-5 nested_fetch)
used as triggers only: guard pins `:1648` / `:1030` / `:1817`,
seal-arm and classifier intactness, and the "count 2" holdings
were all re-derived above from HEAD bytes before being relied
on. The s13 standing note (directory pathspec for censuses)
was honored for every census below.

## Verification

### Matrix

1. Cross-flavor mirroring: list field seals without guarding;
   connection guards then seals; cascade seals under its own
   policy; walker children seal under per-path policies; sidecar
   results seal under the sidecar policy. One guard body, one
   seal arm -- no flavor carries a second of either.
2. Sync/async twins: the guard is color-agnostic (one body
   reached from both pipelines through the `queryset_guard`
   parameter, plus the shared keyset entry); the seal is one
   body reached from both colored runners. Compared by
   behavior via the probe (rows 2/4); no drift.
3. Derived knowledge: `is_sliced` is read four ways -- guard
   attribute read, seal rebuilt-state read, classifier
   `getattr` default, combined-outer check. Each read serves a
   different contract (triage / proof / degrade / rewrite
   fidelity). Deriving one Django fact four times is not four
   definitions of one rule.
4. Round-trip pairs: rejection has no inverse. The classifier's
   reason strings are telemetry-stable vocabulary (docstring),
   keyed only by `is not None` at all three call sites -- no
   rejection keys off a string.
5. Other media: production (two owners), oracles (listed above,
   both contracts pinned independently), projections
   (docstrings, verified). Listed, not counted.
6. Enforcement by omission: every recomposing surface seals or
   guards -- relay node, list field, connection (both), cascade
   (both ends), walker children (both policies), sidecar
   results (both kinds). The two `reject_sliced=False`
   declarations each name their downstream answer in prose
   (nested-connection gate degrades; raw-list window composes
   nothing). No member lacks a guard its contract requires.

### Enumeration

Instruments: `git grep` censuses with the directory pathspec
(`django_strawberry_framework`, never `**/*.py`) plus
full-body reads of every hit file at HEAD bytes.

- `is_sliced`: 6 lines / 3 files = 4 read sites (guard
  `:1665`, classifier `:133`, combined check `:3398`, seal arm
  `:3755`) + 1 branch use (`:1680`) + 1 comment (`:3355`).
  Exhaustive: no other file reads sliced state.
- `sliced` word: 95 lines / 9 files (connection 18,
  nested_fetch 3, nested_planner 1, plans 3, walker 8,
  permissions 14, resource_policy 6, utils/connections 1,
  querysets 41). Every line classified: 2 rejection bodies,
  1 classifier arm, 1 rewrite-fidelity check, 5 message
  renderers, 6 policy declarations + selection prose, oracles
  excluded (other media), remainder prose/comments.
- `_guard_source_not_pre_sliced`: 1 def + 2 package call
  sites + 2 oracle functions. Zero `_seal_or_defect` /
  `_defect_message` references in [connection.py][connection]
  (the guard does not compose the seal -- static proof).
- `_SealPolicy`: 1 class + 1 field + 6 constants, all in
  [querysets.py][querysets]; `reject_sliced=False` exactly
  twice (prefetch child, raw-list row source).
- `already-sliced` string: 4 lines / 1 file (guard docstring,
  message, head prose) -- the wire wording is single-sited.
- Classifier: 1 def + 3 callers
  ([nested-planner.py][nested-planner] `:1282`,
  [lateral-fetch.py][lateral-fetch] `:636`,
  [single-parent-fetch.py][single-parent-fetch] `:244`), all
  degrade (`return None` / unplanned plan), zero raise.
- Every member lands in F-seal, F-guard, R1, R2, R3, or the
  exclusion list above. Nothing unassigned.

### Challenges

Merge tests (posit a change to the SHARED rule; count
definitions forced to move together):

- P1 -- tolerate a sliced source where nothing recomposes:
  seal side moves 0 (already declared per-policy -- the two
  `False` constants); guard side is N/A (the connection
  reorders and slices on EVERY request, "fires regardless"
  per its docstring -- tolerating there is a different
  decision about pagination, not this axis). Count: 0 / N/A.
- P2 -- change the rejection's error class: the wire contract
  moves the guard alone (1 body + its oracles); the boundary
  contract moves the seal's raisers alone. No single reason
  moves both. Count: 1 per contract.
- P3 -- refine the trigger (e.g. only outer slices count):
  the seal arm moves alone (1); the guard moves alone (1)
  only if the wire contract adopts the same carve-out for
  its own resolver-facing reason. Count: 1 per rule.

Per-rule challenges:

- C1 -- a new surface needs sliced tolerance: 1 new
  `_SealPolicy` declaration, 0 bodies (principle 1 -- the
  `_LIST_RELATION_CHILD_POLICY` split is the worked example:
  it differs from `_PREFETCH_CHILD_POLICY` on this axis and
  no other).
- C2 -- the seal's trigger refines: 1 arm (`:3755`).
- C3 -- a new connection slicing entry: 1 call site; a wire
  message change: 1 body.
- C4 -- a new unwindowable shape: 1 classifier arm (its own
  open family; cited, not counted here).
- C5 -- a rewrite-tolerance change: 1 check
  (`::_combined_lost_property`; the `combined` rule; cited,
  not counted here).

Every genuine rule change moves at most 1 definition. By
DRY's counting rule that is independence, even where the
stated Django reason coincides.

Probe (execution-verified, disposable copy; read-only, 0 SQL
-- any query would have raised `OperationalError` with no
tables present): `/tmp/e2_probe.py` over a `git archive
HEAD` tree inside the copy (run `dry-20260930T232512-466a50`,
exit 0, package `__file__` under `head-tree/`), plus the
copy's own worktree bytes (run `dry-20260930T232528-612678`,
exit 0). Slot venv lacks locked deps (standing s13 infra
finding); both runs used the disclosed
`PYTHONPATH=<shared-venv>/site-packages` shim with the
probed package first on `sys.path`.

- Rows 1-2: guard admits unsliced, raises `GraphQLError`
  "already-sliced" naming "connection resolver".
- Row 3: HEAD fail-soft arm converts unreadable state to
  `GraphQLError`; worktree leaks raw (concurrent arm
  removal -- traced, decision-neutral).
- Row 4: the seal emits `('sliced', 'rows 0:5')` for the SAME
  source the guard rejects -- the guard is not load-bearing
  for fail-closed behavior, proved behaviorally. This row is
  also the F-guard negative control (seal-alone bypass
  simulation: every oracle passes except the wire-wording
  rows).
- Rows 5-6: seal admits unsliced with a fresh `QuerySet`;
  classifier returns `"sliced"` / `None` and raises nothing.

## Findings

### F-seal -- CONFIRMED single-owned, no edit

Contract + variation: a queryset a recomposing surface will
compose onto must be unsliced; varies per surface by declared
policy only (`reject_sliced`, default on).
Sites + roles: definition = the arm (`:3755`-`:3756`) plus
the field (`:2870`); declarations = six constants; consumers
= five message renderers + walker policy selection (roles
above).
Challenges: C1 = 1 declaration / 0 bodies; C2 = 1 arm; P1 =
0 (pre-declared); P2/P3 = 1 (this contract alone).
Owner + lifetime (principles 7/4): stays at
[querysets.py][querysets] `::_seal_or_defect` /
`::_SealPolicy` -- the narrowest cohesive owner every
consumer already imports; per-call lifetime, nothing stored.
Migration: none -- already single (the sealed-execution
family's consolidation; this finding re-proves the sliced
axis of it at HEAD bytes).
Distinct behavior kept: the two `False` declarations and
their downstream answers (gate degrades / nothing
recomposes), recorded at the constants.
Behavioral proof: execution-verified (probe rows 4-5) +
static (one arm, one field, zero second bodies
package-wide).
Structural gate: none proposed here -- bypass means not
calling the seal, whose future-surface population cannot be
enumerated; the consolidated `sealed-execution-queryset`
family already deferred this gate with reason, which stands.
Freshness: fingerprints in System trace (all three states
for the owner file; HEAD/worktree for consumers).

### F-guard -- CONFIRMED single-owned, no edit

Contract + variation: a connection source must be unsliced
because the field owns pagination; invariant across
`filter:` / `orderBy:` input (no variation -- the connection
reorders and slices on every request).
Sites + roles: definition = the one body; consumers = the
two call sites (pipeline head both colors, keyset entry).
Challenges: C3 = 1 call site / 1 body; P1 = N/A (no
variation exists); P2/P3 = 1 (this contract alone).
Owner + lifetime: stays at [connection.py][connection] --
the surface whose `resolver=` contract it polices; per-call,
nothing stored.
Migration: none -- already single.
Distinct behavior kept: wire-flavored `GraphQLError` naming
`resolver=` (vs the seal's author-facing
`ConfigurationError`), pre-visibility timing, attribute-read
triage with the HEAD fail-soft arm.
Behavioral proof: execution-verified (probe rows 1-3) +
static (pipeline order `:1890` -> `:1900` / `:1937` ->
`:1947` proves guard-before-seal on both colors).
Structural gate: none proposed -- the existing oracles pin
both wordings (pipeline + live keyset); probe row 4 is the
executed negative control (seal-alone bypass keeps
fail-closed but loses exactly the pinned wording).
Freshness: fingerprints in System trace.

### R1 -- REJECTED: guard-seal merge

Shared form considered: (a) delete the guard as a copy of
the seal arm; (b) route the guard through `_seal_or_defect`
translating `("sliced", detail)` to `GraphQLError`.
Contract differences (each independently fatal):

1. Subject: the guard polices the connection `resolver=`
   RETURN ("A connection resolver returned ..."); the seal
   polices `get_queryset` hook returns and sidecar results
   ("{name}.get_queryset returned ..."). Form (a) misattributes
   every sliced connection source to a hook the consumer may
   never have written.
2. Error class: `GraphQLError` (wire, client-facing) vs
   `ConfigurationError` (author-facing). Deleting the guard
   changes the client-visible class -- observable behavior
   change, not behavior-preserving (principle 8).
3. Stage: the guard runs pre-visibility at the pipeline head
   and at the keyset tail entry (whose input does not always
   pass the head); the seal runs during/after visibility
   composition. Different points, different inputs.
4. Read discipline: the guard triages the consumer object
   through attribute access (HEAD fail-soft arm; the 5-tuple
   matches the package's uniform triage idiom); the seal
   proves dispatch-free state off a rebuilt genuine query.
   Form (b) would drag the wire triage through the seal's
   extraction machinery, which fails closed on shapes the
   guard must pass through (only `sliced` would translate;
   the other six codes would need pass-through) -- coupling
   independent domains to share one Django attribute read,
   which DRY forbids as machinery.

Challenges: P1 = 0/N/A, P2 = 1 per contract, P3 = 1 per
rule (above). The shared Django premise ("reordering a
sliced query raises") is platform knowledge, not a package
rule -- like two sites both knowing a QuerySet is lazy.
Reconsideration trigger: one subject/error contract -- the
guard raising `ConfigurationError` off the seal's defect
tuple, the seal gaining a wire-flavored `resolver=` arm, or
the connection ceasing to recompose unconditionally (then
the guard's unconditional premise collapses into the seal's
policy axis).
Durable home: OWED, recorded here, edit deferred -- one
clause at the guard docstring (exact ASCII text):

    `The visibility seal rejects this shape one step later
    with author-facing ConfigurationError; this guard stays
    because the resolver= contract owes the wire its own
    GraphQLError before visibility runs (DRY e2: intentional
    split, not a copy).`

plus the mirror half-sentence at the seal's `sliced` arm
prose. Deferred because [connection.py][connection] is
externally dirty (concurrent `truth` migration) and this
item lands zero production edits by dispatch; the
`prepared_resolver_source` docstring (`:4801`) already
records the guard as the surface's own check, so the split
is half-homed. A later item touching the guard applies the
clause verbatim; until then this finding is the home.

### R2 -- REJECTED: classifier merge (standing, re-derived)

Shared form considered: treating
`::unwindowable_child_queryset_reason`'s `sliced` arm as a
third definition of sliced rejection.
Contract difference: the classifier returns a reason STRING
and never raises; all three call sites degrade (fetch-time
`return None` twice, planner whole-relation unplanned once).
Its five arms answer "which shapes can no strategy window"
for plan selection -- a new arm (e.g. locking) changes
planning, never rejection. Merging would route a
never-raises planning vocabulary through a raising
contract.
Challenges: C4 = 1 arm in its own family; P1-P3 do not move
it (tolerating slices for planning vs rejecting them for
execution are opposite decisions).
Reconsideration trigger: the classifier gains a raising
consumer, or a rejection site keys off a specific reason
string (today all callers key off `is not None` only).
Durable home: already at the owner -- the classifier
docstring states degradation ("WHOLE-RELATION refusal ...
raises ITS OWN error at the field"), and the walker's
child-policy comment + `_PREFETCH_CHILD_POLICY` prose state
the seal-gate division of labor. No edit owed.

### R3 -- REJECTED: combined-rewrite check as third definition

Shared form considered: the `if query.is_sliced` check in
`::_combined_lost_property` (`:3398`-`:3399`) as a third
sliced rejection.
Contract difference: it feeds `(None, ("combined",
"<combinator>: <lost property>"))` -- the `combined`
defect, whose rule is rewrite fidelity ("the pk-set rewrite
must preserve the row set"), not slice refusal. A sliced
outer combinator cannot ride inside the pk subquery even
where plain slices are tolerated (raw-list policy keeps
`rewrite_combined=False` independently of its
`reject_sliced=False`). The check moves only with the
combinator rule (C5 = 1).
Reconsideration trigger: the rewrite starts emitting
`sliced` instead of `combined`.
Durable home: already at the owner -- the function
docstring + `_pk_membership_query_or_defect` return
contract name the `combined` code. No edit owed.

Worker-0 index rows (this family item names; plan edits are
Worker-0's):

- Family `recomposition-illegal-source-rejection` -> status
  `rejected` (R1 per-site rules with trigger; R2/R3
  exclusions; F-seal/F-guard each single-owned, no edit).
- `connection-pre-sliced-source-guard` | owner
  [connection.py][connection]
  `::_guard_source_not_pre_sliced` | files `connection.py` |
  holding item Family `recomposition-illegal-source-rejection`
  | status `file-local` (one body, two call sites, no second
  site after this sweep; seal + classifier excluded with
  contract differences above).
- No new rows for F-seal (covered by consolidated
  `sealed-execution-queryset`), the five renderers (covered
  by open `seal-defect-code-wording`), R2 (covered by open
  `unwindowable-child-queryset-classification`), or R3
  (covered by `sealed-execution-queryset`'s combined arm).

## Defects

None. Tracing found no non-duplication bug: the guard's
pre-boundary attribute read is deliberate triage whose
5-tuple matches the package's uniform triage idiom, the
worktree fail-soft removal is concurrent-external work
(traced, not judged), and the by-design unconditional guard
timing is its contract, not an overreach.

## Pending execution

- `proof:` `uv run python scripts/workspace.py run
  dry/recomp-reject-e2/consolidate -- sh -c
  'PYTHONPATH=<shared-venv>/site-packages python
  /tmp/e2_probe.py <copy>/head-tree'` -- execution-verified
  (run `dry-20260930T232512-466a50`, exit 0, `E2-PROBE ALL
  OK`, package `__file__` under `head-tree/` holding `git
  archive HEAD` bytes; discharges F-seal, F-guard, R1 rows
  1-6). `<copy>` =
  `/private/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/dsf-ws/0b901faeac791a7b/dry/slots/slot-2`,
  `<shared-venv>` =
  `~/.t3/worktrees/django-strawberry-framework/dry-0015/.venv/lib/python3.14/site-packages`.
  The `head-tree/` extraction + `/tmp/e2_probe.py` stay on
  disk for Worker-2; remove by explicit path after
  verification.
- Worktree comparison (same command, `<copy>` as the tree):
  run `dry-20260930T232528-612678`, exit 0 -- rows 1-2/4-6
  identical, row 3 shows the concurrent arm removal.
  Informational; discharges nothing.
- Shared-tree authorization unspent: zero edits landed, no
  oracle added, no pytest run -- no `gate:` command owed.

## Judgment

The illegal-source rejection population is two per-site
rules, each already single-owned: the seal's `sliced` arm
(visibility-boundary contract, `ConfigurationError`) and
the connection guard (`resolver=` wire contract,
`GraphQLError` before visibility). The posited merge fails
on four independent contract differences, and every genuine
rule change moves at most one side. The classifier and the
combined-rewrite check are correctly excluded neighbors
with their own owners. Zero production edits; one durable
home clause owed to a later item touching the guard. The
family is REJECTED with triggers, not consolidated.

Item-scoped diff state: no tracked edits; one new untracked
artifact (this file). `git diff dd9c8804 --stat` names no
package/test path from this item (all dirt pre-dates the
baseline -- verified `dd9c8804` tree bytes == worktree bytes
on all three indexed files at dispatch time). Scratch:
`<copy>/head-tree/` (HEAD-bytes extraction, copy-only) +
`/tmp/e2_probe.py` (read-only probe, OS temp).

## Independent verification (Worker-2)

Re-derived expectation-first at HEAD `83998e08` bytes (directory pathspec
`django_strawberry_framework` throughout); W1's sections read only after my
own trace below was fixed. Addresses `dry/recomp-reject-e2/verify`.

My trace: package-wide `is_sliced` census gives 6 lines / 3 files --
guard read `:1665` + branch `:1680`, classifier `:133`, combined check
`:3398`, seal arm `:3755`, comment `:3355`. No other file reads sliced
state. `sliced`-word census gives 95 lines / 9 files with per-file counts
18/3/1/3/8/14/6/1/41; I read the content of every line I had not otherwise
covered (connection `:1630`/`:1882`, all 8 non-renderer permissions lines,
15 querysets prose lines incl. the `:443` async-adapter docstring) and each
lands in a rejection body, the classifier arm, the rewrite check, a
message renderer, policy prose, or prose/comments. There is no second
sliced-rejection body anywhere: the only raisers are the guard (1 body,
2 call sites `:1030`/`:1817`, zero seal refs in connection.py) and the
seal arm (1 arm + 1 field + 6 constants, `False` exactly twice). Owner
choice matches W1: keep both where they are (surface police vs boundary
proof); the merge fails on subject, error class, stage, and read
discipline, each re-derived below. Verdict: REJECT the consolidation.

Row reconciliation (every row survives on my evidence):

- F-seal: arm `:3755`-`:3756` + field `:2870` confirmed; six constants
  `:2880`-`:2932` with the two `False` declarations and their downstream
  prose confirmed; five renderers confirmed (source `:4138`-`:4144`,
  hook-result `:4259`-`:4265`, sidecar map `:3133`-`:3147` + raise
  `:3152`, cascade root `:380`-`:384`, cascade edge `:445`-`:450`).
- F-guard: body `:1648`-`:1688` + call sites `:1030`/`:1817` confirmed;
  guard-before-seal both colors (`:1890` -> `:1900`, `:1937` -> `:1947`)
  confirmed; `prepared_resolver_source` invokes `queryset_guard` on the
  queryset branch and its docstring names the connection's pre-sliced
  rejection (W1's half-home) confirmed.
- R1 differences: (1) subject texts confirmed on both messages;
  (2) `GraphQLError` vs `ConfigurationError` confirmed; (3) pre-visibility
  head vs during/after-visibility seal confirmed; (4) attribute read with
  the HEAD 5-tuple fail-soft arm vs dispatch-free read off the rebuilt
  genuine query confirmed, and the 5-tuple matches the package triage
  idiom (same set at the `_consume_fallback` handler).
- R2: classifier returns a reason string, never raises; all three call
  sites (`:1282`, `:636`, `:244`) key off `is not None` and degrade
  (unplanned plan / `return None` twice) confirmed.
- R3: `:3398` feeds `("combined", ...)` emitted inside
  `_pk_membership_query_or_defect` (`:3449`); raw-list policy keeps
  `rewrite_combined=False` independently of its `reject_sliced=False`
  confirmed.
- Challenges: P1 (0/N/A) holds via the two pre-declared `False`
  constants and the guard's every-request docstring premise; P2/P3 move
  one contract each; C1 holds (the list-relation policy differs from the
  prefetch-child policy on `reject_sliced` and no other axis); C2-C5 are
  one site each. Genuine changes move at most one definition.
- Oracles (by content): guard `:2144`-region + `:2455`/`:2468` + live
  keyset `:999`-region; seal `:1570`/`:1582` + `:5127`-`:5136` matrix +
  cascade `:1072`/`:1399` + live sidecar `sliced` rows; classifier
  `:303` matrix (`:316`) + walker `:1440`-`:1465`/`:5690`. All present.
- Dirt: the `## Owned changes` ledger names none of the three indexed
  files (full-ledger scan); the worktree guard hunk is the fail-soft-arm
  removal with the rejection and both call sites intact; querysets and
  nested_fetch diffs carry zero `sliced` lines (context only; the
  nested_fetch `values` arm goes to `truth.is_subclass`); the hostile
  oracles are gone from worktree tests while the `:2144` oracle survives
  at `:2233`. Concurrent-external stands.
- Fingerprints: all three states re-hashed for the indexed files and
  both states for all 18 cited files -- every short hash and clean flag
  matches W1 exactly; `dd9c8804` tree bytes == worktree on all three
  indexed files; nothing moved since `ITEM_BASELINE`.
- Zero-edit: `git diff dd9c8804 --stat` names only `docs/dry/dry-0_0_15.md`
  (+42 concurrent ledger lines); this artifact is the only new file from
  this item (untracked).
- Execution (my own probe `/tmp/e2_w2_probe.py`, written fresh, run via
  `dry-20260930T233923-66d8d4`, exit 0, package `__file__` under a
  `git archive HEAD` tree): guard admits unsliced; guard raises
  `GraphQLError` naming the resolver contract on `qs[:5]`; the seal
  emits `('sliced', 'rows 0:5')` for the SAME source (negative control --
  the guard is not load-bearing for fail-closed); the seal admits
  unsliced with a fresh `QuerySet`; the classifier returns
  `"sliced"`/`None` and raises nothing. 0 SQL.
- Durable home: the guard clause is pure ASCII (byte scan) and lands
  cleanly -- I applied it to the guard docstring in the disposable copy
  and `check_trailing_commas.py --check` reports 0 violations with
  `ruff check` / `ruff format --check` green.
- Index rows: family -> `rejected` plus one `file-local` guard row match
  the table's shape exactly; the no-new-row claims hold
  (`sealed-execution-queryset` consolidated, `seal-defect-code-wording`
  and `unwindowable-child-queryset-classification` open).

Precision notes (Worker-2; none touches a verdict, trigger, or index
row -- recorded, not revision-demanding):

- P-a: R1-4's "the other six codes" undercounts -- the seal's canonical
  ordering (`_seal_or_defect` docstring) runs type -> table -> untrusted
  -> routing -> evaluated -> sliced -> projection -> combined -> alias
  (9 codes, 8 besides `sliced`). The coupling objection stands as
  written; only the arithmetic is off.
- P-b: the walker parenthetical "(seal by name, both colors)" misattaches
  -- the walker calls `apply_type_visibility_sync` only (sync-only
  walker, stated in its own docstring). Both-colors holds of the seal
  generally, not of the walker path.
- P-c: the `:1030` gloss ("input does not always pass the pipeline
  head") needs its reading fixed: resolver flows hit the head first (the
  live keyset oracle exercises the head site, not `:1030`); `:1030`
  guards the distinct post-pipeline value and direct-call paths (tests
  call `_consume_window` directly). One body + two call sites is textual
  fact either way.
- P-d: the owed mirror half-sentence at the seal arm prose has a
  location but no exact text -- only the guard clause is verbatim-ready.

Scratch: `/tmp/e2_w2/` (my HEAD-tree extraction) + `/tmp/e2_w2_probe.py`
(my probe); W1's `/tmp/e2_probe.py` + `<copy>/head-tree/` untouched.
Remove all by explicit path after Worker-0 closeout.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection.py]: ../../django_strawberry_framework/connection.py
[lateral-fetch.py]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[list-field.py]: ../../django_strawberry_framework/list_field.py
[nested-fetch.py]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[nested-planner.py]: ../../django_strawberry_framework/optimizer/nested_planner.py
[permissions.py]: ../../django_strawberry_framework/permissions.py
[plans.py]: ../../django_strawberry_framework/optimizer/plans.py
[querysets.py]: ../../django_strawberry_framework/utils/querysets.py
[resource-policy.py]: ../../django_strawberry_framework/resource_policy.py
[single-parent-fetch.py]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[utils-connections.py]: ../../django_strawberry_framework/utils/connections.py
[walker.py]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-connection.py]: ../../tests/test_connection.py
[test-nested-fetch.py]: ../../tests/optimizer/test_nested_fetch.py
[test-permissions.py]: ../../tests/test_permissions.py
[test-querysets.py]: ../../tests/utils/test_querysets.py
[test-walker.py]: ../../tests/optimizer/test_walker.py

<!-- examples/ -->
[test-connection-pagination-api.py]: ../../examples/fakeshop/test_query/test_connection_pagination_api.py
[test-keyset-api.py]: ../../examples/fakeshop/test_query/test_keyset_api.py
[test-list-field-api.py]: ../../examples/fakeshop/test_query/test_list_field_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
