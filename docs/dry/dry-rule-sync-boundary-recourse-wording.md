# DRY review: `sync-boundary-recourse-wording`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Posited rule (index row; owner candidate
[querysets.py][querysets]
`::sync_pipeline_recourse`; indexed files
[querysets.py][querysets],
[mutations-resolvers.py][mutations-resolvers],
[forms-resolvers.py][forms-resolvers],
[rf-resolvers.py][rf-resolvers],
[permissions.py][permissions],
[mut-permissions.py][mut-permissions],
[gate-permissions.py][gate-permissions]):
every `SyncMisuseError` raised at a sync
boundary carries the same recourse wording,
single-sourced from the one template. No
prior family artifact exists; this trace is
fresh at HEAD bytes, census-first (the 7
indexed files were not assumed complete --
and the census proves them incomplete:
[relay.py][relay] owns the node wording and
[execution-mode.py][execution-mode] the
executor wording, neither indexed). The
index row's pre-run-8 `rejected` status
is treated as prior record, not
evidence; the verdict below adjudicates
fresh and sets the final status.

Verdict: REJECT the broad consolidation.
The sync-boundary recourse is twelve
wordings -- eight constants (the
template's three flavor outputs plus
five literals) and four inlines -- each
single-owned. The template triple
inside it (F-pipe) is CONFIRMED
already-single and needs no edit; seven
rejections exclude the rest on contract
differences with triggers. Both
File-side converge claims are re-tested
from the family side and endorsed, with
one walker exception filed as D1.

- F-pipe: the pipeline template --
  [querysets.py][querysets]
  `::sync_pipeline_recourse` (`:405`) plus
  its 3 flavor constants (model / form /
  serializer), each computed from the
  template by call. Zero second template
  bodies package-wide (probe R1/R5).
- R-relay (rejected merge): the Relay
  default [querysets.py][querysets]
  `::_RELAY_ASYNC_RECOURSE` (`:398`) --
  async-possible remedy (TWO recourses incl.
  the async entry), the opposite polarity
  of the template's sync-only sentence.
  Default for 6 signatures, taken by 10
  omission call sites.
- R-perm (rejected merge):
  [mut-permissions.py][mut-permissions]
  `::_PERMISSION_ASYNC_RECOURSE` (`:71`) --
  about `has_permission` /
  `check_permission` + the bool contract,
  not `get_queryset`. One constant shared
  by both write seams.
- R-gate (rejected merge):
  [gate-permissions.py][gate-permissions]
  `::_GATE_ASYNC_RECOURSE` (`:65`) -- the
  read-side gate twin; four clauses differ
  from R-perm (verified clause by clause
  below). Converges with the existing File
  row `permissions-gate-recourse-vs-mutation-twin`
  from the family side.
- R-cascade (rejected merge):
  [permissions.py][permissions]
  `::_ASYNC_RECOURSE` (`:143`) -- no
  async-native walk plus the `fields=`
  alternative. Its oracle pins the
  Relay-wording negative.
- R-node (rejected merge):
  [relay.py][relay]
  `::_SYNC_RESOLVER_RECOURSE` (`:95`, a
  NON-indexed file the census found) --
  about consumer `resolve_node(s)`
  overrides + the `execute_sync` entry,
  not `get_queryset`.
- R-inline (rejected merge): the 4 inline
  `SyncMisuseError` wordings -- the
  flavor-parameterized async-iterable guard
  (`:482`), the sidecar refusal (`:3205`),
  the awaitable-source refusal (`:4739`),
  and the executor/loop refusal
  ([execution-mode.py][execution-mode]
  `:149`). Each single-sited with its own
  subject and remedy.
- R-omit (rejected merge): per-surface
  async-possible wordings for the 7
  non-Relay omission sites -- that change
  would ADD seven definitions, not remove
  one. Converges with the existing File
  row `types-resolvers-recourse-omission`
  from the family side (D1 records the one
  site where the omission is wrong).

Sites and roles (all re-derived at HEAD
`83998e08` bytes):

- Definition (F-pipe, one template body):
  `::sync_pipeline_recourse` (`:405`-`:424`:
  the `flavor_noun` interpolation `:421`,
  fixed sync-only body `:422`-`:423`).
- Flavor constants, all computed by call,
  zero literal wordings (probe R1 pins all
  three): `::_MUTATION_ASYNC_RECOURSE`
  (`:207`, noun `"DjangoMutation"`),
  `::_FORM_ASYNC_RECOURSE` (`:142`, noun
  `"form mutation"`),
  `::_SERIALIZER_ASYNC_RECOURSE` (`:227`,
  noun `"serializer mutation"`).
- Flavor threading, all by name: model
  single `:623` + model M2M `:659` (via
  the [write-values.py][write-values]
  spine), model locate `:717`
  (positional into
  `apply_type_visibility_sync`); form
  single `:222` (via the spine; form multi
  maps the single per element); serializer
  single `:264` + serializer multi `:293`
  (via the spine), serializer scope-specs
  `:1523` (positional into
  `related_visibility_queryset`, keeps its
  own `None`-skip per the e3 verdict).
- Neighbor definitions (each single-owned,
  each excluded): Relay `:398` + 6
  defaulted signatures (`:4372` / `:4454` /
  `:4478` / `:4507` / `:4580` / `:4624`,
  plus `...` overloads `:4352` / `:4362`)
  + 10 omission takers (below); cascade
  `:143` + 1 caller (`:715`); permission
  `:71` + 1 caller (`:93`, via
  `::_require_sync_bool_auth_result`
  `:88`, itself called by both seams);
  gate `:65` + 1 caller (`:438`);
  node `:95` + 2 callers (`:520` /
  `:642`, via the `:515` / `:637`
  guards).
- Omission takers (10 call sites taking
  the Relay default; probe R5 pins the
  3+10 split): [types-relay.py][types-relay]
  `:984` / `:1051` / `:1053`
  (subject-correct Relay sites),
  [list-field.py][list-field] `:1463`
  (sync pipeline; async twin `:1509`),
  [connection.py][connection] `:1900`
  (sync pipeline; async twin `:1947`),
  [filters-sets.py][filters-sets] `:2760`
  (sync twin; async twin `:2795`),
  [types-resolvers.py][types-resolvers]
  `:428` / `:452` (both behind
  `async_execution()` twins),
  [querysets.py][querysets] `:4838`
  (`post_process_queryset_result_sync`;
  async sibling `:4864`),
  [walker.py][walker] `:629` (NO twin --
  D1).
- Explicit passers (3 call sites): model
  locate `:717`, cascade `:715`, and the
  internal
  `visibility_scoped_related_queryset`
  pass-through `:4467`.
- Inline wordings (each 1 def, each its
  own enforcement sites):
  `reject_async_iterable_in_sync_context`
  (`:482`-`:511`, flavor param, sites
  [list-field.py][list-field] `:1772` +
  [connection.py][connection] `:2072`);
  `reject_awaitable_sync_source`
  (`:4729`-`:4745`, passed as
  `async_guard` at `:1785` / `:1893` +
  the post-process head);
  `_apply_sidecar_sync` (`:3175`-`:3210`,
  the one post-sidecar seal);
  `async_execution`
  ([execution-mode.py][execution-mode]
  `:130`-`:158`).
- Intentional non-members: the
  cross-alias `recourse=` halves
  ([write-transaction.py][write-transaction]
  `:669`,
  [rf-resolvers.py][rf-resolvers] `:2114`
  -- a DIFFERENT `recourse` kwarg on
  `make_cross_alias_save_guard`, a
  `ConfigurationError` about write-alias
  routing, never a `SyncMisuseError`);
  `reject_residual_async_source`
  (`:4748` -- raises `ConfigurationError`,
  not `SyncMisuseError`, by the
  sync-boundary reservation contract).
- Oracles: cascade --
  [test-permissions.py][test-permissions]
  `:1700`-`:1731` (cascade recourses
  present, `"Relay node defaults"`
  ABSENT -- the negative pin this family
  generalizes); guard shapes --
  [test-querysets.py][test-querysets]
  `:247`-`:257` (coroutine shape +
  catch-shape), `:1877`-`:1879`
  (awaitable shape), `:4568`-`:4576`
  (iterable flavor nouns),
  `:4618` (sidecar shape),
  `:4704`-`:4710` (awaitable-source
  shape); sidecar prefixes --
  [test-connection.py][test-connection]
  `:1875` / `:3315`; gate --
  [test-gate-permissions.py][test-gate-permissions]
  `:376` (method-name shape);
  write-permission --
  [test-mut-permissions.py][test-mut-permissions]
  `:475` (`has_perm`); executor --
  [test-execution-mode.py][test-execution-mode]
  `:106`-`:120` (refusal surfaces);
  spine threading --
  [test-write-values.py][test-write-values]
  (the `async_recourse=` pass-through
  params). The template / Relay / node /
  permission wordings carry NO literal
  pins (behavior-typed, wording-free) --
  consistent with per-site prose
  ownership. Cited by content at HEAD
  bytes; no pytest run (dispatch forbids
  it).
- Projections (verified against their
  bodies): the template docstring (the
  three-flavor single-sourcing claim
  holds -- probe R1; the NOT-used-for
  Relay + permission clause holds -- both
  are literals, zero template calls);
  the flavor comments (`:200`-`:206` /
  `:137`-`:141` / `:221`-`:226`); the
  permission four-clause comment
  (`:62`-`:70`, verified clause by clause
  in R-gate); the gate mirror comment
  (`:60`-`:64`); the visibility-sync
  docstring (`:4399`-`:4405`, the
  surface-specific + cascade rationale --
  holds, and D1 is its walker-shaped
  consequence); the cascade / node /
  iterable / sidecar / executor
  docstrings; the spec-039 cites (shipped
  spec, template scope). One stale
  subject found (D1, filed below); all
  other sharing and separation claims
  hold.

Dirt attribution (by diff content vs `git
show HEAD:`, not by dirty status; the
ledger names one cited file --
[relay.py][relay]'s adopted-orphan prose,
located below; everything else is
concurrent-external):

- [querysets.py][querysets] (503 changed
  lines): truth-migration renames
  (`_safe_class_name` -> `truth.name` and
  kin) + except-narrowing + docstring
  rewords. Recourse ranges (`:185`-`:216`,
  `:391`-`:424`, `:482`-`:511`,
  `:3175`-`:3210`, `:4352`-`:4641`,
  `:4729`-`:4745`, `:4838`) have ZERO
  hunks -- template, Relay constant,
  defaults, and all 4 inline wordings
  byte-identical (probe digest identical
  both states).
- [mutations-resolvers.py][mutations-resolvers]
  (77): truth-migration + prose. Const
  `:207` + all 3 threading sites intact.
- [forms-resolvers.py][forms-resolvers]
  (25): `_form_errors_to_field_errors`
  signature narrowing + prose. Const
  `:142` + threading `:222` intact.
- [rf-resolvers.py][rf-resolvers] (242):
  truth-migration + except-narrowing +
  prose. Const `:227` + all 3 threading
  sites intact.
- [permissions.py][permissions] (78):
  truth-migration + spec-cite shortening.
  Const `:143`-`:148` + caller `:715`
  intact.
- [mut-permissions.py][mut-permissions]
  (14): truth-migration only
  (`truth.is_instance` / `truth.render` /
  `truth.name` / `truth.static_attr`).
  Const + `:88`-`:94` guard intact.
- [gate-permissions.py][gate-permissions]
  (180): truth-migration + `lazy`
  unwrap + guard-shape rewords. Const
  `:65`-`:69` + caller `:438` intact.
- Cited files:
  [relay.py][relay] (252: NodeID batching
  restructure + truth-migration; LEDGER
  adopted orphan `typed-globalid-decode`
  trigger docstring at worktree `:444`
  -- prose, disjoint from the `:95`-`:99`
  / `:515` / `:637` ranges, which are
  byte-identical modulo line numbers),
  [write-values.py][write-values] (99:
  NodeID batching + truth-migration;
  spine params + pass-throughs intact),
  [types-resolvers.py][types-resolvers]
  (LEDGER adopted `one-sync-boundary`
  orphan arms + deadline + truth --
  per the e3 record; twin `:428` /
  `:452` logic intact),
  [list-field.py][list-field] /
  [connection.py][connection] /
  [walker.py][walker] /
  [filters-sets.py][filters-sets] /
  [types-relay.py][types-relay] /
  [write-transaction.py][write-transaction]
  (concurrent-external; omission /
  twin / exclusion sites intact --
  probe R5 counts identical both
  states),
  [execution-mode.py][execution-mode]
  (CLEAN -- worktree == HEAD).
- Decision impact: none. The probe ran
  both states to prove the point
  (identical ALL OK, identical digest).

Three-state fingerprints (indexed files):

- [querysets.py][querysets]: HEAD
  `392e50d0`, worktree `cfc773ba`,
  `9aaaad5d` `8fc556d5`;
  `b85f4e1f` == worktree.
- [mutations-resolvers.py][mutations-resolvers]:
  HEAD `7a25afea`, worktree `dd00ec6e`,
  `9aaaad5d` `c9cff059`;
  `b85f4e1f` == worktree.
- [forms-resolvers.py][forms-resolvers]:
  HEAD `ea839d84`, worktree `6e613333`,
  `9aaaad5d` `a1000f21`;
  `b85f4e1f` == worktree.
- [rf-resolvers.py][rf-resolvers]: HEAD
  `420fc3ca`, worktree `3fc6a366`,
  `9aaaad5d` `c49ce3c2`;
  `b85f4e1f` == worktree.
- [permissions.py][permissions]: HEAD
  `d77c5050`, worktree `42c3c19c`,
  `9aaaad5d` `6c97d887`;
  `b85f4e1f` == worktree.
- [mut-permissions.py][mut-permissions]:
  HEAD `f23eb540`, worktree `35a48499`,
  `9aaaad5d` `55e5edf8`;
  `b85f4e1f` == worktree.
- [gate-permissions.py][gate-permissions]:
  HEAD `e2b46fd7`, worktree `a23d32f0`,
  `9aaaad5d` `1c9cfd39`;
  `b85f4e1f` == worktree.
- Nothing moved since `ITEM_BASELINE`
  (`b85f4e1f3d78a2f431e5662ad3d1a7fb4a202e6e`
  -- window diff on package/tests/examples
  is empty); HEAD
  `83998e08d48c911199527ed0411ab8041805c8b5`;
  snapshot
  `9aaaad5de73f6ff36eea3264e5b085fef1b046cc`.
- Cited files (HEAD / worktree):
  [relay.py][relay] `a09485a1` /
  `fd88aafa`,
  [execution-mode.py][execution-mode]
  `b86a08cd` (clean),
  [write-values.py][write-values]
  `01a3318c` / `4fa8118d`,
  [types-resolvers.py][types-resolvers]
  `574e9768` / `7a953c53`,
  [types-relay.py][types-relay]
  `968fb95a` / `6c2e8c20`,
  [list-field.py][list-field] `77ddb86c` /
  `1dcb0c43`,
  [connection.py][connection] `3d6dd424` /
  `64b85d0e`, [walker.py][walker]
  `bdd9c2f1` / `9130aceb`,
  [filters-sets.py][filters-sets]
  `3d307402` / `ec278851`,
  [write-transaction.py][write-transaction]
  `c0a12b34` / `49102e69`.
  Oracles (HEAD / worktree):
  [test-permissions.py][test-permissions]
  `14961acd` / `7cf7b3af`,
  [test-querysets.py][test-querysets]
  `3ff4094a` / `b1fc954b`,
  [test-connection.py][test-connection]
  `615866f6` / `f80a7f5a`,
  [test-mut-permissions.py][test-mut-permissions]
  `2082d9e4` / `a4472aee`,
  [test-gate-permissions.py][test-gate-permissions]
  `abf30ad3` / `71e1ff4b`,
  [test-execution-mode.py][test-execution-mode]
  `bbe5f97e` (clean),
  [test-write-values.py][test-write-values]
  `8d09921b` / `9f459e2f`.

Prior records used as triggers only: the
pre-run-8 `rejected` status itself
(adjudicated fresh -- the verdict below
re-sets it on this trace's evidence), the
File rows `types-resolvers-recourse-omission`
(R8) and
`permissions-gate-recourse-vs-mutation-twin`
(R1) -- both converge claims re-tested
from the family side before being relied
on (R-omit, R-gate) -- and the e3 spine
record (threading census re-derived
above). The s13 standing note (directory
pathspec for censuses) was honored for
every census below.

## Verification

### Matrix

1. Cross-flavor mirroring: the 3 write
   flavors share the template by call (3
   constants, 0 literal wordings); the
   read flavors take the Relay default by
   omission (10 sites, 1 wording); the
   permission flavors each own theirs
   (write vs gate, 4 clauses apart). No
   flavor carries a second spelling of
   another's wording.
2. Sync/async twins: the async-possible
   vs sync-only split IS the family's
   central contract difference, compared
   by remedy, not shape. Nine omission
   takers + 4 inlines offer a live async
   remedy (each verified against its
   twin or executor branch); the
   template triple + cascade are
   sync-only by pipeline design; the
   walker site is sync-only but takes
   the async-possible default (D1).
3. Derived knowledge: flavor nouns are
   per-caller data (3 call sites, each
   naming its own surface), never
   derived from the caller's module or
   class; subjects name their own
   surface at each wording. One template
   fact, composed -- not re-derived.
4. Round-trip pairs: the recourse has no
   inverse (one-way consumer guidance).
   The guard prefix (`owner.method`
   returned `kind` in a sync `context`)
   is the shared half every wording
   completes; the completion is the
   per-site half. Different halves, one
   composition -- not two definitions.
5. Other media: production (1 template +
   6 constants + 4 inlines), oracles
   (listed above -- the cascade negative
   pin plus shape/prefix pins; the
   template / Relay / node / permission
   wordings deliberately wording-free),
   projections (docstrings, verified;
   1 stale subject filed as D1).
   Listed, not counted.
6. Enforcement by omission: all 13
   `apply_type_visibility_sync` call
   sites enumerated -- 3 explicit, 10
   default-takers. Nine takers are
   remedy-correct omissions (async
   remedy live at each); the tenth
   (walker) is D1, established by the
   owner's own cascade rationale plus
   the cascade negative oracle. No other
   member lacks a wording its contract
   requires.

### Enumeration

Instruments: `git grep -n <pat> HEAD --
django_strawberry_framework` (directory
pathspec, never `**/*.py`) plus
full-body reads of every hit file at HEAD
bytes; the R5 AST census re-pins the
call-site counts.

- `sync_pipeline_recourse`: 1 def
  (`:405`) + 3 calls (`:207` / `:142` /
  `:227`) + 3 imports + prose. Zero
  other callers package-wide.
- `ASYNC_RECOURSE`: 7 constant defs
  (Relay `:398`, mutation `:207`, form
  `:142`, serializer `:227`, cascade
  `:143`, permission `:71`, gate `:65`)
  + 10 threading sites + prose.
- `_SYNC_RESOLVER_RECOURSE` (non-indexed
  [relay.py][relay]): 1 def (`:95`) + 2
  callers (`:520` / `:642`) + prose.
  The census-first find.
- `async_recourse`: 6 defaulted defs +
  2 overloads + 3 explicit passers + 2
  spine params + 2 spine pass-throughs
  + prose (27 lines, every one read).
- `recourse=`: 5 shared-guard
  enforcement lines (`:4434`
  visibility, `:93` permission, `:438`
  gate, `:520` / `:642` node x2) + 6
  spine threadings (`async_recourse=`)
  + 2 cross-alias exclusions
  (different kwarg, classified out).
- `raise SyncMisuseError`: 5 sites --
  the shared guard `:214` (recourse
  param), the iterable `:510`, the
  sidecar `:3205`, the awaitable-source
  `:4739`, the executor `:149`. Every
  site classified; zero missed raises
  (`SyncMisuseError(` census: 1 class
  def + these 5).
- `apply_type_visibility_sync(` calls:
  3 explicit + 10 omission (probe R5;
  matches the grep census exactly).
- `reject_async_iterable_in_sync_context`
  callers: 2 (`:1772` / `:2072`) +
  prose. `reject_awaitable_sync_source`
  as `async_guard`: 2 (`:1785` /
  `:1893`) + the post-process head.
- Every member lands in F-pipe, R-relay,
  R-perm, R-gate, R-cascade, R-node,
  R-inline, R-omit, D1, or the exclusion
  list above. Nothing unassigned.

### Challenges

Merge tests (posit a change to the SHARED
rule; count definitions forced to move
together):

- M1 -- reword the shared pipeline
  sentence (e.g. the `sync_to_async`
  execution shape changes): the template
  body alone (1 + its oracles). Relay
  (opposite remedy), permission / gate
  (different hooks), cascade (no async
  walk + `fields=`), node (different
  entry), and all 4 inlines never move.
  Count: 1.
- M2 -- a fourth pipeline flavor: 1
  call site (noun + constant), 0 bodies
  (principle 5 -- the three existing
  constants are the worked examples).
- M3 -- the Relay remedy changes: the
  Relay constant alone (1); all 10
  takers follow by default. The template
  triple never moves (opposite
  polarity).
- M4 -- the permission wording changes:
  the permission constant alone (1);
  the gate twin never moves (4 clauses
  apart -- and vice versa). Count: 1
  per side.
- M5 -- the cascade `fields=`
  alternative is retired: the cascade
  constant alone (1).
- M6 -- any inline reword (sidecar /
  awaitable-source / executor /
  iterable): its own body alone (1
  each); the iterable's flavor axis
  stays a parameter (2 nouns, 0 new
  bodies).
- M7 -- per-surface async-possible
  subjects (the R8 trigger): would ADD
  7 wordings (one per omission site).
  An anti-consolidation by DRY's own
  counting -- recorded to show the
  work, trigger unfired.

Per-rule challenges:

- C1 -- a fourth flavor noun: 1 call
  site, 0 bodies.
- C2 -- the invalid-remedy polarity
  flips (pipelines go async-capable):
  the template alone (1) -- and that
  change is the R-relay trigger, which
  would re-open the Relay merge.
- C3 -- an async permission hook gains
  meaning: permission + gate each move
  alone (1 + 1, different remedies).
- C4 -- the cascade gains an async walk:
  the cascade constant alone (1) --
  the R-cascade trigger.
- C5 -- a third node-resolver seam: 1
  caller of the existing node constant,
  0 bodies.
- C6 -- the walker gains a twin or its
  own wording: D1's fix, 1 site.

Every genuine rule change moves at most
1 definition. By DRY's counting rule
that is independence, even where the
stated sync-boundary reason coincides.

Probe (execution-verified, disposable
copy; read-only -- string, signature,
and AST checks plus in-memory coroutine
rejections; zero SQL, zero writes):
`/tmp/e5_probe.py` over a `git archive
HEAD` tree inside the copy (run
`dry-20261001T011302-edd678`, exit 0,
package `__file__` under `head-tree/`),
plus the copy's own worktree bytes (run
`dry-20261001T011308-9cfd3f`, exit 0,
identical ALL OK, identical digest
`509594ae1978`). Slot venv lacks locked
deps (standing s13 infra finding); both
runs used the disclosed
`sys.path`-appended shared-venv
site-packages shim with the probed
package first on `sys.path` (asserted
in-probe).

- R0: all 9 recourse wordings resolve
  by name.
- R1: the 3 flavor constants equal the
  template output; bodies identical
  modulo the noun.
- R2: the 6 wordings pairwise distinct;
  6 key substrings (`Relay node
  default`, `ORM pipeline`, `fields=`,
  `has_permission / check_permission`,
  `check_<field>_permission`,
  `execute_sync`) each exclusive to
  its owner.
- R3: 6 Relay defaults identical; 2
  spine params required (threaded,
  never defaulted).
- R4: 6/6 wordings raise through the
  shared guard with text intact
  (mutation stands for the template
  triple); non-awaitable passthrough
  intact.
- R5: AST census 3 explicit + 10
  omission call sites, per-file counts
  match the grep census exactly, both
  states.
- R6: 4 inline wordings pinned in the
  probed bytes; the iterable guard
  executes both flavor nouns + the
  async no-op.

## Findings

### F-pipe -- CONFIRMED already-single, no edit

Contract + variation: a sync write
pipeline meeting an `async def
get_queryset` names the sync-only
recourse -- the pipeline runs
synchronously (under one `sync_to_async`
call on the async surface), so the
target hook must go sync. Varies by
flavor noun only (each caller's genuine
surface); the sentence is fixed.
Sites + roles: definition = the one
template (`:405`-`:424`); composers = 3
flavor constants by call (`:207` / `:142`
/ `:227`); downstream links = 7
threading sites (model x3, form x1,
serializer x3).
Challenges: M1 = 1 (this contract
alone); M2 / C1 = 0 bodies; C2 = 1.
Owner + lifetime (principles 7/4): the
template owns the sentence (the
narrowest cohesive owner every flavor
already imports -- all three flavors
depend on `utils/querysets` without
cycles); flavors own their nouns; per
call, nothing stored.
Migration: none -- already single
(every link composes by call,
re-derived at every level,
probe-pinned).
Distinct behavior kept: per-caller
nouns (`"DjangoMutation"` /
`"form mutation"` / `"serializer
mutation"`, each naming its own
surface); the locate + scope-specs
positional shapings (call shape, 0
wording).
Behavioral proof: execution-verified
(probe R0/R1 + R4) + static (one
template body, zero second bodies
package-wide) + the threading oracles.
Structural gate: none proposed --
bypass means inlining a new literal
wording, whose future-site population
cannot be enumerated without a bespoke
existence test per helper; the R1
equality stands as trace evidence, not
a committed gate. A red result would be
a defect, not a gate.
Freshness: fingerprints in System trace
(all three states for indexed files;
HEAD/worktree for cited + oracles).

### R-relay -- REJECTED: Relay-default merge

Shared form considered: treating
`::_RELAY_ASYNC_RECOURSE` as a second
definition of the pipeline recourse, or
routing one through the other.
Contract differences (each independently
fatal):

1. Remedy polarity: async-POSSIBLE (two
   recourses -- invoke from an async
   resolver, or go sync) vs sync-ONLY
   (one recourse). Routing the pipeline
   through the Relay wording would point
   pipeline consumers at an async entry
   that cannot help -- the cascade
   oracle's exact negative pin,
   generalized.
2. Subject: the Relay node defaults (a
   read surface) vs a write pipeline
   flavor. The 3 subject-correct takers
   are Relay sites; the template names
   no read surface.
3. Default posture: the Relay wording is
   the DEFAULT 10 sites take by
   omission; the template is
   never a default (every use passes a
   noun). Opposite composition shapes.

Challenges: M1/M2 never move it; M3 = 1
(this wording alone + its 10 takers by
default).
Reconsideration trigger: the pipelines
go async-capable (the template remedy
converges to async-possible) or the
Relay defaults go sync-only.
Durable home: already at the owner --
the template docstring declines this
wording by name with the reason. No
edit owed.

### R-perm -- REJECTED: permission-hook merge

Shared form considered: treating
`::_PERMISSION_ASYNC_RECOURSE` as a
second pipeline recourse, or routing it
through the template.
Contract differences: subject is the
PERMISSION hooks (`has_permission` /
`check_permission`), not `get_queryset`;
the remedy adds the bool contract
(`user.has_perm` / auth backends must
return a bool -- an authorization
bypass otherwise); the enforcement
context is `"mutation"` permission
checking, not the ORM pipeline. A
template call would need a second
sentence, pinning nothing.
Challenges: M1/M4 move 1 per side; no
shared change exists.
Reconsideration trigger: the permission
hooks merge into the `get_queryset`
hook (single hook population).
Durable home: already at both owners --
the template docstring declines the
permission recourse, and the permission
comment records the four-clause split
from R-gate. No edit owed.

### R-gate -- REJECTED: gate-twin merge

Shared form considered: one template
for the gate + permission wordings, or
routing one through the other.
Contract differences, clause by clause
(the "four clauses differ" comment
re-derived, not inherited):

1. Subject: `A DjangoMutation runs its
   permission check` vs `A FilterSet /
   OrderSet permission gate runs`.
2. Hook noun: `an async permission
   hook` vs `an async hook`.
3. Remedy method: `has_permission /
   check_permission ... returning a
   bool` vs `check_<field>_permission
   ... (def, not async def)`.
4. Trailing clause: `and ensure
   user.has_perm / auth backends return
   a bool` vs absent.

A template would take a parameter per
clause and pin nothing (probe R2
executes the exclusivity). The gate's
own check-vs-gate split (gate vs
non-callable-slot wording at `:433` /
`:428`) stays inside the gate file.
Challenges: M4 = 1 per side; C3 = 1 +
1.
Reconsideration trigger: either wording
generalized to the other's subject
(the File R1 trigger, judged sound
from this side).
Durable home: already at both owners --
the mirror comments each name the twin
plus the template decline. This R-gate
is the family-side convergence the
File row
`permissions-gate-recourse-vs-mutation-twin`
names: same pair, same trigger.
Endorsed. No edit owed.

### R-cascade -- REJECTED: cascade merge

Shared form considered: treating
`::_ASYNC_RECOURSE` as a pipeline
recourse, or routing it through the
template.
Contract differences: no async-native
walk (the async twin wraps the same
sync walk, so the async remedy is dead
-- the owner prose states this
explicitly); the alternative remedy is
`fields=` scoping, a surface only the
cascade offers; the subject names the
cascade functions, not a pipeline.
The oracle pins the Relay negative for
exactly this reason. A template call
would need both the polarity flip and
the `fields=` clause -- a second
sentence.
Challenges: M1 never moves it; M5 / C4
= 1 (this wording alone).
Reconsideration trigger: the cascade
gains an async-native walk, or
`fields=` scoping is retired.
Durable home: already at the owner --
the visibility-sync docstring records
the cascade as the worked example of a
caller passing its own. No edit owed.

### R-node -- REJECTED: node-resolver merge

Shared form considered: treating
`::_SYNC_RESOLVER_RECOURSE` as a
pipeline recourse, or routing it
through the template.
Contract differences: subject is the
consumer `resolve_node(s)` OVERRIDES
(a read-refetch dispatch), not a
`get_queryset` hook; the entry is
`schema.execute_sync()` (the remedy
offers the async schema run); the
enforcement context is `"Relay
refetch"`. Different hook, different
entry, different surface -- the only
shared token is the guard prefix,
which is the shared half by design.
Challenges: M1 never moves it; C5 = 0
bodies.
Reconsideration trigger: the node
dispatch merges into the `get_queryset`
visibility seam.
Durable home: the constant's two
callers already compose it by name;
the separation is recorded here (the
template docstring's NOT-used-for
clause covers Relay only by its
default; this row extends the record
to the node dispatch). No edit owed.

### R-inline -- REJECTED: inline-wording merge

Shared form considered: folding the 4
inline `SyncMisuseError` wordings into
the template (or into one shared
inline).
Contract differences, per inline: the
iterable guard is ALREADY the shared
shape (flavor param, 2 nouns, 0 new
bodies -- a second parameterization
would be machinery); the sidecar names
`apply_sync` + the sync-resolver
context (a seal seam, not a pipeline);
the awaitable-source names the
consumer `resolver=` + the visibility
reason (a source-shape seam); the
executor names the sync executor +
running loop (an execution-mode seam,
a different module). Four subjects,
four remedies, four owners; each is 1
def + its own sites today.
Challenges: M6 = 1 each; no shared
change exists.
Reconsideration trigger: any inline's
subject or remedy generalizes to
another's (per-inline; the iterable's
is a third flavor noun, which stays a
parameter).
Durable home: each wording already
recorded at its owner (guard
docstrings state their seam). No edit
owed.

### R-omit -- REJECTED: per-surface omission wordings

Shared form considered: a
surface-specific `async_recourse` for
each of the 7 non-Relay omission
sites.
Contract differences: the default's
REMEDY shape is correct at 6 of the 7
(async IS possible -- list, connection,
filters, both `_visible_*` helpers,
and post-process each have a live
async twin or branch, verified site by
site above); only the subject noun
names Relay. Minting 7 wordings would
ADD seven definitions to fix a
subject-only gap -- an
anti-consolidation (M7). The seventh
site (walker) is not remedy-correct
and is filed as D1 instead of folded
here.
Challenges: M7 = +7 definitions;
M3 moves all 10 takers by default
today.
Reconsideration trigger: a spec row
requiring per-surface async-possible
recourse subjects (a cross-surface
card, not any one file's defect --
the File R8 trigger, judged sound
from this side).
Durable home: the visibility-sync
docstring (default + cascade-example
clauses) already records the posture.
This R-omit is the family-side
convergence the File row
`types-resolvers-recourse-omission`
names: same direction (no per-surface
wording), same trigger. Endorsed --
with D1 as the walker-shaped
exception, which R8's worktree census
did not isolate. No edit owed.

Worker-0 index rows (this family item
names; plan edits are Worker-0's):

- Family `sync-boundary-recourse-wording`
  -> status `rejected` (F-pipe
  already-single -- 1 template + 3
  flavor constants, 0 second bodies;
  R-relay / R-perm / R-gate / R-cascade
  / R-node / R-inline / R-omit
  exclusions with triggers; D1 walker
  wording filed). This verdict
  re-sets the pre-run-8 `rejected`
  status on fresh HEAD-bytes evidence;
  the old status carried no artifact
  and was treated as prior record, not
  evidence.
- Files-covered: REVISE to 9 -- the 7
  indexed files plus [relay.py][relay]
  (owns the node wording, R-node) and
  [execution-mode.py][execution-mode]
  (owns the executor wording,
  R-inline). Threading / omission
  consumers ([write-values.py][write-values],
  [types-relay.py][types-relay],
  [list-field.py][list-field],
  [connection.py][connection],
  [walker.py][walker],
  [filters-sets.py][filters-sets],
  [types-resolvers.py][types-resolvers])
  compose by default-or-pass and stay
  in prose, not the row.
- No new rows (R-gate converges with
  `permissions-gate-recourse-vs-mutation-twin`,
  R-omit converges with
  `types-resolvers-recourse-omission`,
  both judged from the family side;
  R-relay / R-perm / R-cascade /
  R-node / R-inline carry their
  triggers in-artifact).

## Defects

- D1 (error-path guidance, owner
  [walker.py][walker] `::_build_child_queryset`
  `:629`): the walker takes the Relay
  default recourse for a walk that is
  sync-only on BOTH surfaces. The
  walker has no async twin (zero
  `async def` in the module; the one
  visibility call is the sync
  function, unconditionally) and the
  plan build runs synchronously under
  async execution too
  ([extension.py][extension]
  `::_optimize` is sync-called from
  both colors -- the `:1171` async
  wrapper awaits the root result, then
  runs the sync `_optimize`). An
  `async def get_queryset` on a
  prefetch-child target therefore
  raises on both surfaces with a
  recourse whose async remedy ("invoke
  ... from an async resolver") is a
  dead end and whose subject names
  Relay. Contract sources: the
  `apply_type_visibility_sync`
  docstring's own cascade rationale
  ("callers whose recourse differs
  pass their own ... no async-native
  walk"), which the walker matches,
  plus the cascade negative oracle
  ([test-permissions.py][test-permissions]
  `:1729`-`:1731`). Minor: the raise
  still fires (fail-closed, no bypass,
  no leak); only the guidance
  misdirects. Fix direction (for the
  closer, not this item): pass a
  walker-specific sync-only recourse
  at `:629`, mirroring the cascade.
  Persists in the worktree (call
  intact; probe R5 counts identical).
  Route: closeout defect-homing pass.

## Pending execution

- `proof:` `uv run python
  scripts/workspace.py run
  dry/syncrecourse-e5/consolidate --
  python /tmp/e5_probe.py head-tree
  <shared-venv>` -- execution-verified
  (run `dry-20261001T011302-edd678`,
  exit 0, `E5-PROBE ALL OK`, package
  `__file__` under `head-tree/`
  holding `git archive HEAD` bytes;
  discharges F-pipe R0/R1/R4, R-relay
  R3/R5, R-gate R2, R-inline R6,
  R-omit R5). `<copy>` =
  `/private/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/dsf-ws/0b901faeac791a7b/dry/slots/slot-2`,
  `<shared-venv>` =
  `~/.t3/worktrees/django-strawberry-framework/dry-0015/.venv/lib/python3.14/site-packages`.
  The `head-tree/` extraction +
  `/tmp/e5_probe.py` stay on disk for
  Worker-2; remove by explicit path
  after verification.
- Worktree comparison (same command,
  `.` as the tree): run
  `dry-20261001T011308-9cfd3f`, exit 0,
  identical ALL OK, identical digest
  `509594ae1978` --
  decision-neutral drift proved
  behaviorally. Informational;
  discharges nothing.
- Shared-tree authorization unspent:
  zero edits landed, no oracle added,
  no pytest run -- no `gate:` command
  owed. Sharded and Postgres cells are
  inapplicable by construction: the
  probe issues zero SQL (string,
  signature, AST, and in-memory
  coroutine checks only).

## Judgment

The sync-boundary recourse is not one
wording: it is twelve wordings -- eight
constants plus four inlines -- each
single-owned, each differing on subject,
remedy polarity, or hook.
The template triple at the family's
center is already single -- one body,
three nouns, zero second wordings --
and every neighbor merge fails on an
independently fatal contract
difference: the Relay opposite remedy,
the permission bool contract, the
four-clause gate split, the cascade's
missing async walk plus `fields=`,
the node dispatch's entry, the four
inline seams, and the omission posture
whose per-surface fix would add seven
definitions. Both File-side converge
claims hold from the family side with
matching triggers; the one
remedy-wrong omission (walker) is
filed as D1. Zero production edits.
The family is REJECTED as a
consolidation -- re-set on this
trace's fresh evidence, the
artifact-less pre-run-8 record
superseded, not inherited.

Item-scoped diff state: no tracked
edits; one new untracked artifact
(this file). `git diff b85f4e1f
--stat` on package/tests/examples is
empty; all package dirt pre-dates the
baseline (verified `b85f4e1f` tree
bytes == worktree bytes on all seven
indexed files). Scratch:
`<copy>/head-tree/` (HEAD-bytes
extraction, copy-only) + `/tmp/e5_probe.py`
(read-only probe, OS temp).

## Independent verification (Worker-2)

Trace basis: HEAD `83998e08` bytes via
a `git archive HEAD` extraction inside
the verify copy (`head-tree/`); worktree
bytes from the copy itself. Every census
below is mine, run with a directory
pathspec
(`django_strawberry_framework`) at HEAD
bytes; W1's numbers were the CLAIM,
never evidence. Owner choice, derived
before reconciling: keep
[querysets.py][querysets]
`::sync_pipeline_recourse` as the F-pipe
owner (every flavor already imports it,
zero cycles) and REJECT the broad
consolidation -- same verdict as W1, on
independent counts.

My population census (HEAD bytes):
`sync_pipeline_recourse` 1 def (`:405`)
+ 3 calls + 3 imports + prose, zero other
callers; `ASYNC_RECOURSE` 7 const defs
(Relay `:398`, mutation `:207`, form
`:142`, serializer `:227`, cascade
`:143`, permission `:71`, gate `:65`) +
10 threading sites + prose;
`_SYNC_RESOLVER_RECOURSE` 1 def
([relay.py][relay] `:95`) + 2 callers
(`:520` / `:642`); `async_recourse` 27
lines: 6 defaulted defs + 2 overloads +
2 spine params + 2 spine pass-throughs +
6 `async_recourse=` kwarg threadings (5
spine + cascade `:715`) + 5 internal
positional pass-throughs (`:4471` /
`:4501` / `:4519` / `:4615` / `:4641`) +
1 enforcement (`:4434`) + 3 prose
(`:4399` / `:4464` / `:4601`);
`recourse=` 13 lines: 5 shared-guard
enforcements + 6 spine threadings + 2
cross-alias exclusions
([write-transaction.py][write-transaction]
`:669`,
[rf-resolvers.py][rf-resolvers] `:2114`,
a different `recourse` kwarg, never a
`SyncMisuseError`); `raise
SyncMisuseError` 5 sites (`:214` guard,
`:510` iterable, `:3205` sidecar,
`:4739` awaitable-source,
[execution-mode.py][execution-mode]
`:149`); `SyncMisuseError(` 1 class def
(`:144`) + those 5;
`apply_type_visibility_sync(` 19 lines:
13 call sites (3 explicit --
[mutations-resolvers.py][mutations-resolvers]
`:713`, [permissions.py][permissions]
`:711`, [querysets.py][querysets]
`:4467` -- plus 10 omission) + 3 defs +
3 prose. Twelve wordings: 8 constants (3
flavor outputs + 5 literals) + 4
inlines, each single-owned. The 7
indexed files are incomplete:
[relay.py][relay] owns the node wording
and [execution-mode.py][execution-mode]
the executor wording (both found by the
package-wide census, neither indexed).

Reconciliation (every difference from
W1's text is a narration defect with
zero row impact; corrections recorded
here, no resubmission needed):

- D-W2-1 (dirt narration overstated,
  Worker-2): the "ZERO hunks /
  byte-identical" sentence is false at
  source level. Five hunks overlap the
  stated ranges: `-164` (deletes the
  local `_safe_class_name`; guard body
  untouched), `-390` (except-narrowing
  ending `:396`; Relay `:398`+
  untouched), `-3195` (`method_name`
  interpolation rename; sidecar wording
  lines `:3205`-`:3208` untouched),
  `-4428` (`owner` interpolation rename;
  the `recourse=` line `:4434` is
  context), `-4737` (MODIFIES the
  awaitable wording line `:4740`:
  `_safe_class_name` -> `truth.name`).
  Same-class renames also touch the
  permission bool-check, the gate caller
  `owner=`, and both node-guard `owner=`
  lines (every `recourse=` line
  context-preserved); the `:637` node
  call is additionally re-indented under
  a new `isawaitable` conditional. My
  probe measures the effect exactly:
  literal-prose digest IDENTICAL both
  states (`e4f5e389d7604bf1`), rendered
  digest IDENTICAL (`0bf79eb88e0509b0`);
  only the awaitable raise-node digest
  differs (`9946..` vs `80f4..`) plus
  the sidecar/awaitable function-node
  digests. Rendered wordings agree on
  all probed (benign) inputs, and the
  rename moves no wording between
  buckets. Decision impact: none.
- D-W2-2 (Enumeration partition,
  Worker-2): the `async_recourse`
  "6+2+3+2+2+prose = 27" partition is
  arithmetically loose (it implies 12
  prose lines; 3 exist). My partition
  above sums to 27 exactly; the 9 lines
  W1's sentence does not name are the 5
  F-pipe spine threadings (named in
  W1's Sites-and-roles) plus the 4
  internal R-relay delegation lines
  (`:4501` / `:4519` / `:4615` /
  `:4641`, pure parameter plumbing
  inside the 6 defaulted signatures --
  read, no wordings). Nothing
  unassigned under my count.
- D-W2-3 (trivial, Worker-2): the node
  census "+ prose" names no line (the
  identifier has exactly 3 hits: 1 def
  + 2 callers). Substance holds.
- D-W2-4 (Matrix-5 arithmetic,
  Worker-2): "1 template + 6 constants
  + 4 inlines" fits neither the 12
  wordings (8 constants + 4 inlines)
  nor the 10 bodies (1 template + 5
  literals + 4 inlines). Summary-line
  slip; the Enumeration and every row
  use the right numbers.

Rows (each re-derived from the bodies):

- F-pipe CONFIRMED already-single: one
  template body, 3 consts equal its
  output (probe V1 both states), zero
  other callers, 7 threading sites
  re-read (model `:623` / `:659` /
  `:717`, form `:222` + multi-maps-
  single, serializer `:264` / `:293` /
  `:1523` with its own `None`-skip).
  No structural gate proposed (a red
  result would be a defect, not a
  gate) -- judged sound; the family's
  negative control is the cascade
  oracle's Relay-negative pin, re-read
  below.
- R-relay / R-perm / R-gate / R-cascade
  / R-node / R-inline / R-omit: all 7
  rejections re-derived. Relay polarity
  (two recourses incl. the async entry)
  vs template sync-only; permission
  subject + bool contract; gate
  4-clause split re-derived clause by
  clause (subject / hook noun / remedy
  method / trailing clause -- matches
  W1) and executed by probe V2; cascade
  no async-native walk + `fields=` with
  the oracle pinning the Relay
  negative; node `resolve_node(s)`
  overrides + `execute_sync` entry;
  4 inlines each 1 def + own sites;
  omission 9 remedy-correct (every twin
  re-read: the async visibility awaits
  the hook, so each async remedy is
  live) with per-surface wordings an
  anti-consolidation (+7 definitions).
  Every trigger judged sound.
- Converge `permissions-gate-recourse-
  vs-mutation-twin` (File R1):
  ENDORSED -- same pair, same
  direction, verbatim-identical
  trigger, same 4-clause evidence
  re-read at HEAD bytes.
- Converge `types-resolvers-recourse-
  omission` (File R8): ENDORSED -- same
  direction (no per-surface wording),
  identical trigger. R8's "7-site"
  parenthetical counts FUNCTIONS (7
  elsewhere-functions, composition
  identical to mine); the fresh census
  counts CALL SITES (10). Same
  population, different granularity --
  no contradiction (code-motion
  ruled out: counts stable across
  recent HEADs). R8 never adjudicated
  the walker's remedy, so D1 refines
  without contradicting. Coupled with
  R-omit via the D1 exception, marked.
- D1 ([walker.py][walker] `:629`):
  CONFIRMED on all prongs -- zero
  `async def` / `await` in the module,
  the one visibility call
  unconditional, the plan build
  sync-called from both colors
  ([extension.py][extension] `:1171`-
  `:1175` awaits the root result then
  runs sync `_optimize`), the taken
  default's subject naming Relay and
  its async remedy dead. Fail-closed
  (the raise still fires), so minor.
  Fix direction (walker-specific
  sync-only recourse mirroring the
  cascade) and closeout routing judged
  sound. Persists in the worktree (no
  hunk covers `:629`; worktree `:628`,
  same call).
- Index rows: all three bullets ENDORSED
  as exact replacement text (family ->
  `rejected` on fresh evidence; files
  REVISE 7 -> 9 with threading /
  omission consumers staying in prose;
  no new rows).

Execution (my probe, fresh design; W1's
probe never opened): `/tmp/v2_e5_probe.py`
(pure ASCII, read-only, zero SQL) over
`head-tree/` (run
`dry-20261001T012942-ef431b`, exit 0,
`V2-PROBE ALL OK`) and `.` (run
`dry-20261001T012954-5cc107`, exit 0,
`V2-PROBE ALL OK`), both with the
disclosed shared-venv `sys.path` shim
and an in-probe package-under-tree
assertion. V0 provenance, V1 template
equality + bodies-modulo-noun, V2
distinctness + 6 exclusive substrings +
4-clause execution, V3 6 identical
defaults + 2 required spine params, V4
8/8 recourses through the guard +
passthrough, V5 iterable both nouns +
async no-op + awaitable rendered, V6 AST
3 explicit + 10 omission (per-file
counts match the grep census both
states) + 1 template + 3 calls + 7+1
consts + 5 raisings + 1 class -- plus
the three digests that pin the dirt to
interpolation renames. No pytest
(read-only evidence sufficed; oracles
verified by content at HEAD bytes --
guard shapes, iterable nouns, sidecar
prefixes, gate method-name,
write-permission `has_perm`, executor
refusal, spine threading, and the
cascade negative pin at
[test-permissions.py][test-permissions]
`:1729`-`:1731`).

Freshness (independently
fingerprinted): all 7 indexed + 11
cited + 7 oracle HEAD/worktree hashes
recomputed -- every value matches W1's
record; `b85f4e1f` tree bytes ==
worktree bytes on all 7 indexed files;
window diff on package/tests/examples is
empty (the only post-baseline tracked
change is Worker-0's dispatch paragraph
in `dry-0_0_15.md`). Zero-edit
confirmed; no missed consolidation
(the 12 wordings are each single-owned,
and the only candidate not already
single -- the template triple -- is
CONFIRMED already-single). The `proof:`
commands for this verification are the
two probe runs above; no `gate:` owed
(zero edits, no oracles added, no
pytest run).

Prose/lint: artifact is prose-only;
`ruff check` and `ruff format --check`
on the artifact are clean (vacuous for
`.md`); the markdown scaffold keeps the
10 canonical group headers and reuses
existing ref-ids only (no new link
definitions added). `path::Symbol`
cites throughout; no process provenance.

Verdict: verified. Every row survives
on independent evidence; the four
(Worker-2) defects are narration-only
with corrections recorded above. Plan
tick is Worker-0's; untouched here.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection.py]: ../../django_strawberry_framework/connection.py
[execution-mode.py]: ../../django_strawberry_framework/utils/execution_mode.py
[extension.py]: ../../django_strawberry_framework/optimizer/extension.py
[filters-sets.py]: ../../django_strawberry_framework/filters/sets.py
[forms-resolvers.py]: ../../django_strawberry_framework/forms/resolvers.py
[gate-permissions.py]: ../../django_strawberry_framework/utils/permissions.py
[list-field.py]: ../../django_strawberry_framework/list_field.py
[mut-permissions.py]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers.py]: ../../django_strawberry_framework/mutations/resolvers.py
[permissions.py]: ../../django_strawberry_framework/permissions.py
[querysets.py]: ../../django_strawberry_framework/utils/querysets.py
[relay.py]: ../../django_strawberry_framework/relay.py
[rf-resolvers.py]: ../../django_strawberry_framework/rest_framework/resolvers.py
[types-relay.py]: ../../django_strawberry_framework/types/relay.py
[types-resolvers.py]: ../../django_strawberry_framework/types/resolvers.py
[walker.py]: ../../django_strawberry_framework/optimizer/walker.py
[write-transaction.py]: ../../django_strawberry_framework/utils/write_transaction.py
[write-values.py]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-connection.py]: ../../tests/test_connection.py
[test-execution-mode.py]: ../../tests/utils/test_execution_mode.py
[test-gate-permissions.py]: ../../tests/utils/test_permissions.py
[test-mut-permissions.py]: ../../tests/mutations/test_permissions.py
[test-permissions.py]: ../../tests/test_permissions.py
[test-querysets.py]: ../../tests/utils/test_querysets.py
[test-write-values.py]: ../../tests/utils/test_write_values.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->


