# DRY review: `async-only-queryset-row-adapter`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Posited rule (index row; owner
candidate [querysets.py][querysets]
`::_AsyncQuerySetRows`; indexed files
[querysets.py][querysets],
[list-field.py][list-field],
[extension.py][extension],
[resource-policy.py][resource-policy],
[connection.py][connection]): a final
sliced QuerySet handed to async GraphQL
completion travels inside one
`__aiter__`-only adapter, and one
predicate spells which values count as
async-only. No prior family artifact
exists; this trace is fresh at HEAD
bytes, census-first (the 5 indexed
files were not assumed complete -- the
package-wide AST census proves the
definitions complete inside them and
finds the lookalikes outside them:
[graphql-patches.py][graphql-patches]
and
[operation-state.py][operation-state],
neither indexed).

Verdict: CONFIRM the consolidation.
The family is one rule with a single
owner and zero second bodies: the
adapter class plus its wrap / unwrap /
is trio (F-adapt) and the async-only
predicate plus its in-module guard
consumer (F-pred), all defined once in
[querysets.py][querysets], every other
site composing by name. Four rejections
exclude the lookalikes on contract
differences with triggers
(R-conn, R-patch, R-stream, R-await).
Zero production edits; one doc-only
defect filed (D1). The File-side
consumer claims (list F3, extension,
resource F2) and the File-side
rejections (connection F4, querysets
F10, patches R1) are all re-tested
from the family side and endorsed; the
principle-11 question File F9 routed
here (`is_async_queryset_adapter` has
no production reader) is decided KEEP
with reasoning, its owner-docstring
clause homed to closeout as D1.

- F-adapt: the completion adapter --
  [querysets.py][querysets]
  `::_AsyncQuerySetRows` (`:442`) plus
  `::wrap_async_queryset_adapter`
  (`:468`), `::unwrap_async_queryset_adapter`
  (`:475`),
  `::is_async_queryset_adapter`
  (`:463`). Zero second adapter bodies
  package-wide (probe R1/R2: exactly
  two `__aiter__` defs, the other
  excluded in R-stream; zero direct
  constructions outside the owner;
  zero external `._queryset` reads).
- F-pred: the async-only vocabulary --
  [querysets.py][querysets]
  `::is_async_only_iterable` (`:426`,
  `AsyncIterable and not Iterable`)
  plus its in-module guard consumer
  `::reject_async_iterable_in_sync_context`
  (`:482`). Zero second spellings
  (probe R1: five composed calls, all
  by name; the five `isinstance`
  async-shape sites each classified --
  the predicate body itself plus the
  four excluded in R-conn / R-patch).
- R-conn (rejected merge):
  [connection.py][connection]'s two
  dispatch checks (`:1097` / `:1143`)
  ask "may the async executor stream
  this" (inclusive -- must answer yes
  for a QuerySet) and the admission
  guard (`:1637`) asks "is this
  paginatable" (a three-arm union) --
  the opposite questions from the
  predicate's difference. Converges
  with File rows connection-F4 and
  querysets-F10 from the family side.
- R-patch (rejected merge):
  [graphql-patches.py][graphql-patches]
  `:121` (`not is_iterable(result) and
  isinstance(result, AsyncIterable)`)
  mirrors upstream's own branch with
  upstream's own `is_iterable` and
  must move iff graphql-core's branch
  moves -- including on shapes where
  the two spellings behaviorally fork.
  Converges with File row patches-R1
  from the family side.
- R-stream (rejected merge):
  [operation-state.py][operation-state]
  `::_ResumedStream` (`:848`) binds an
  operation scope around subscription
  frames -- a different subject and
  contract from row completion. New
  rejection row named below.
- R-await (rejected merge): the three
  awaitable guards (`:185` / `:4729` /
  `:4748`) refuse single awaitables
  from hook returns; the family guard
  refuses async-iterable streams from
  resolver sources. Converges with
  verified Family
  `awaitable-refusal-and-disposal`
  (e1), which owns the awaitable side.

Sites and roles (all re-derived at HEAD
`83998e08` bytes; probe-pinned):

- Definitions (F-adapt, all at the
  owner, one body each):
  `::_AsyncQuerySetRows` (`:442`-`:460`:
  `TypeError` gate `:453`-`:458`,
  `__aiter__` delegate `:459`-`:460`,
  `__slots__`, deliberate `__iter__`
  omission); `::wrap_async_queryset_adapter`
  (`:468`-`:471`: QuerySet wraps,
  non-queryset passes through);
  `::unwrap_async_queryset_adapter`
  (`:475`-`:478`: `(inner, True)` /
  `(val, False)`);
  `::is_async_queryset_adapter`
  (`:463`-`:465`: the boundary read of
  the private type; zero production
  callers, 16 oracle mentions -- KEEP
  per F-adapt).
- Definitions (F-pred, at the owner):
  `::is_async_only_iterable`
  (`:426`-`:439`); the guard
  `::reject_async_iterable_in_sync_context`
  (`:482`-`:513`, predicate call
  `:509`) -- this family owns its
  async-shape MECHANISM (the predicate
  composition); e5 owns its recourse
  WORDING (layering note in F-pred, no
  clash: each challenge counts 1 at
  its own owner).
- Wrap consumers (5 calls, all by
  name): [list-field.py][list-field]
  `:1466` / `:1495` (sync pipeline,
  both gated on `is_async_context`) /
  `:1512` / `:1541` (async pipeline,
  unconditional);
  [extension.py][extension] `:1217`
  (the `finish` re-wrap).
- Unwrap consumers (1 call):
  [extension.py][extension] `:1214`
  (`_optimize` entry; the
  `was_adapted` flag drives `:1217`).
- Predicate consumers (5 calls, all by
  name): the in-module guard (`:509`);
  [list-field.py][list-field] `:1361` /
  `:1365` (both rejecting exits close
  an async-only source) / `:1771`
  (sync-wrap async-only branch);
  [resource-policy.py][resource-policy]
  `:1258` (async-window dispatch:
  async-only materializes through the
  async iterator, everything else --
  including querysets, keeping SQL
  `LIMIT` -- falls back to the sync
  body).
- Guard consumers (2 calls, both by
  name): [list-field.py][list-field]
  `:1772` (flavor `DjangoListField`);
  [connection.py][connection] `:2072`
  (flavor `connection`) -- the ONLY
  family references connection.py
  holds (probe absence check: zero
  adapter / predicate refs there).
- Transitive consumers (never name the
  family): [types-resolvers.py][types-resolvers]
  `:448` / `:620` (`bounded_rows_async`
  over querysets, then `async for` --
  the seam keeps querysets on the sync
  bound path by the predicate's `not
  Iterable` half, which is why no
  sync-iterable fallback is reachable
  there).
- Intentional non-members: the
  connection dispatch pair + union
  guard (R-conn); the patch conjuncts
  (R-patch); `_ResumedStream`
  (R-stream); the awaitable guards
  (R-await); the cleanup pair
  (`_cleanup_rejected_async_iterable` /
  `_close_async_iterator` -- close an
  already-classified value, classify
  nothing; neighbor protocol owned in
  [resource-policy.py][resource-policy]);
  `normalize_query_source` /
  `_coerced_manager_queryset` /
  `normalized_row_source` (the
  is-queryset decision and the sync
  rebuild rules -- different
  mechanisms, each single, out of
  family scope).
- Oracles: adapter semantics --
  [test-list-field.py][test-list-field]
  `:672`-`:711` (passthrough,
  `TypeError` prefix pin,
  `__aiter__`-yes / `__iter__`-no
  pins, `for`-raises-`TypeError` pin,
  async materialization,
  unwrap-identity pair); optimizer
  re-wrap -- [test-extension.py][test-extension]
  `:5512`-`:5594` (unadapted
  passthrough + 3 adapted preserves:
  evaluated, unresolved-type,
  optimized tail);
  list-optimizer round-trip --
  [test-list-field.py][test-list-field]
  `:1442`-`:1485`; predicate arms --
  [test-querysets.py][test-querysets]
  `:4559`-`:4564` (async-only True;
  QuerySet / list / None False -- the
  QuerySet-False arm is the carve-out
  pin R-conn leans on); bound seam --
  [test-resource-policy.py][test-resource-policy]
  (the `bounded_rows_async` suite:
  prefix close, source-error
  precedence, hostile notes / aclose,
  deadline rejection, cancellation);
  live async execution --
  `test_list_field_async_api.py`
  (async list queries through the
  wrap path; sync-misuse message pin
  `:2350`) and
  [test-relations-async.py][test-relations-async]
  (the `bounded_rows_async`
  no-visibility branch). Cited by
  content at HEAD bytes; no pytest
  run (dispatch forbids it).
- Projections (verified against their
  bodies): the predicate docstring
  (the one-spelling + QuerySet
  carve-out + three-sharer list --
  holds: guard, list branch, async
  seam); the adapter docstring (the
  `__aiter__`-only + graphql-core
  rationale -- holds, pinned by the
  no-`__iter__` oracle); the list
  factory comment (`:1626`-`:1644`,
  the per-resolver commitment +
  wrap-trio mention -- holds: the sync
  wrapper in a loop returns the
  adapter at `:1466` / `:1495`); the
  optimizer `_optimize` docstring
  (unwrap / `finish` re-wrap -- holds
  at `:1214` / `:1217`); the
  connection resolver docstrings (lazy
  queryset under both colors -- holds,
  and is why connection wraps
  nothing); the `_windowed_rows_async`
  docstring (coordinates + early
  close -- holds). All sharing and
  separation claims hold; D1 files the
  one missing clause.

Dirt attribution (by diff content vs `git
show HEAD:`, not by dirty status; the
ledger names one indexed file --
[list-field.py][list-field]'s adopted-orphan
prose, located below; everything else is
concurrent-external):

- [querysets.py][querysets] (505 changed
  lines): truth-migration renames +
  except-narrowing + docstring rewords.
  Exactly ONE hunk lands in the family
  range (`:426`-`:513`): the adapter
  `TypeError` f-string
  (`_safe_type_name(queryset)` ->
  `truth.kind(queryset)`, HEAD `:455`) --
  same hostile-safe kind role, same
  sentence; the oracle pins the
  `requires a QuerySet` prefix only.
  Predicate, trio, guard logic
  byte-identical (probe identical both
  states).
- [list-field.py][list-field] (228):
  relay-target validation rework +
  truth-migration + prose. Family
  ranges intact: all 4 wrap sites
  (no hunk HEAD `:1347`-`:1576`), the
  sync-wrap branch (no hunk past
  `:1620`), the cleanup predicate
  pair (`:1361` / `:1365`). Nearest
  hunk is docstring prose (HEAD
  `:1347`: `Decision 8` ->
  `spec-050 Decision 8`). LEDGER
  adopted orphan
  `relay-node-target-guard` trigger
  docstring at worktree `:220`-`:224`
  (pure additive, in
  `_validate_relay_djangotype_target`)
  -- prose, disjoint from every
  family range.
- [extension.py][extension] (90):
  variable-freeze rework + import
  churn + prose. Unwrap `:1214` /
  re-wrap `:1217` / imports `:61`-`:62`
  byte-identical (no hunk touches
  them; nearest are `:1001` /
  `:1544`).
- [resource-policy.py][resource-policy]
  (71): except-narrowing in the
  cleanup pair + truth-migration +
  prose. Dispatch `:1258` + import
  `:81` byte-identical. The `:1218`
  hunk narrows the `aiter` acquire
  guard (`BaseException` + diagnostic
  test -> `Exception`) -- neighbor
  cleanup protocol, not the family
  dispatch; verdict-neutral.
- [connection.py][connection] (256):
  window/fallback rework + N1-check
  threading + truth-migration + spec-cite
  prose. Dispatch `:1097` / `:1143`
  byte-identical (no hunk HEAD
  `:1020`-`:1308` past the `:1018`
  docstring reword). The `:1637` hunk
  hardens the union guard's getitem
  arm (`hasattr(source,
  "__getitem__")` ->
  `truth.own_attr(type(source),
  "__getitem__") is not None`) plus
  the kind render -- the three-arm
  UNION contract is unchanged, so
  R-conn holds in both states.
- Cited files:
  [graphql-patches.py][graphql-patches]
  / [operation-state.py][operation-state]
  / [types-resolvers.py][types-resolvers]
  (concurrent-external; patch guard,
  stream dunders, seam calls intact --
  probe counts identical both
  states).
- Oracles (concurrent-external; cited
  at HEAD bytes; verdict counts
  definitions only): all four oracle
  files dirty; the key pins survive
  in the worktree (adapter semantics,
  predicate arms, 4 optimizer
  adapter tests, the
  `bounded_rows_async` suite --
  re-grepped, present).
- Decision impact: none. The probe ran
  both states to prove the point
  (identical ALL OK, counts equal,
  only line numbers shifted).

Three-state fingerprints (indexed files):

- [querysets.py][querysets]: HEAD
  `392e50d0`, worktree `cfc773ba`,
  `9aaaad5d` `8fc556d5`.
- [list-field.py][list-field]: HEAD
  `77ddb86c`, worktree `1dcb0c43`,
  `9aaaad5d` `f5b0183e`.
- [extension.py][extension]: HEAD
  `6a6465f2`, worktree `dd9ad009`,
  `9aaaad5d` `39a8739c`.
- [resource-policy.py][resource-policy]:
  HEAD `47befb3f`, worktree `927b89a2`,
  `9aaaad5d` `5b4a80f0`.
- [connection.py][connection]: HEAD
  `3d6dd424`, worktree `64b85d0e`,
  `9aaaad5d` `1fca6266`.
- Snapshot comparison (`9aaaad5d`):
  owner-region logic identical
  (predicate body, adapter body, trio
  bodies byte-equal modulo
  annotations -- snapshot predates
  the `TypeGuard` / `_T` typing pass
  and already carries `truth.kind`);
  census counts identical (adapter
  refs 10 / 6 / 4, predicate refs 2 /
  4 / 2 per file, same files).
- Nothing moved since `ITEM_BASELINE`
  (`7788046f...` -- window diff on
  package/tests/examples is empty);
  HEAD
  `83998e08d48c911199527ed0411ab8041805c8b5`;
  snapshot
  `9aaaad5de73f6ff36eea3264e5b085fef1b046cc`.
- Cited files (HEAD / worktree):
  [graphql-patches.py][graphql-patches]
  `dae51064` / `cd1ad72e`,
  [operation-state.py][operation-state]
  `8df7d2e6` / `50526c85`,
  [types-resolvers.py][types-resolvers]
  `574e9768` / `7a953c53`.
  Oracles (HEAD / worktree):
  [test-list-field.py][test-list-field]
  `9efccda3` / `6d74fcd1`,
  [test-extension.py][test-extension]
  `9d57709f` / `173c14b6`,
  [test-resource-policy.py][test-resource-policy]
  `9206e812` / `a52bfb89`,
  [test-querysets.py][test-querysets]
  `3ff4094a` / `b1fc954b`,
  [test-relations-async.py][test-relations-async]
  `7f5492b4` (clean).

Prior records used as triggers only: the
File rows list-F3 (consumer census 4 +
6 -- re-derived: 4 predicate + 6 wrap
occurrences incl. imports, confirmed),
extension (unwrap-entry / wrap-finish --
confirmed), resource-F2 (1 import + 1
call, zero construction -- confirmed),
connection-F4 and querysets-F10 (the
union-vs-difference rejection --
re-tested fresh in R-conn and
endorsed), patches-R1 (the
upstream-mirror rejection, incl. its
probe-verified str/mapping fork --
trigger state re-checked in R-patch
and endorsed), querysets-F9 (the
principle-11 keep-or-delete routing --
decided KEEP in F-adapt), and the e1 +
e5 family verdicts (converge claims
re-tested from this side in R-await
and F-pred). The s13 standing note
(directory pathspec for censuses) was
honored for every census below.

## Verification

### Matrix

1. Cross-flavor mirroring: the list
   flavor wraps its final queryset (4
   composed calls); the connection
   flavor wraps nothing -- by contract
   (its resolver returns a LAZY
   queryset `ListConnection`
   materializes per color), not by
   omission (axis 6). The relation
   flavor consumes the seam
   transitively (2 calls, never names
   the family). No flavor carries a
   second spelling of another's
   mechanism.
2. Sync/async twins: the adapter exists
   to force ONE color (async-only) at
   the completion boundary; there is
   no sync twin (sync completion
   consumes the queryset directly).
   The `_windowed_rows` /
   `_windowed_rows_async` color pair
   shares its bound seam by call
   (`_raw_list_bound`) and differs
   only in iteration color -- the
   DRY-principle-5 split, already
   single, not a twin of the adapter.
3. Derived knowledge: the async-only
   question is asked by calling the
   predicate (5 sites), never
   re-derived from `__aiter__` /
   `__iter__` presence; the
   is-adapter question by calling
   `is_` / reading unwrap's flag,
   never re-derived from the private
   type (zero external `._queryset`
   reads in production).
4. Round-trip pairs: wrap / unwrap are
   the pair -- one grammar, two
   halves, both at the owner (F-adapt).
   The guard's prefix (owner.method
   returned kind in a sync context)
   plus per-site recourse is e5's
   composition, layered (F-pred
   note).
5. Other media: production (1 class +
   3 trio + 1 predicate + 1 guard),
   oracles (listed above -- contract
   pins plus trio-consistency pins;
   the predicate arms pin the
   QuerySet-False carve-out),
   projections (docstrings, verified;
   1 missing clause filed as D1).
   Listed, not counted.
6. Enforcement by omission: every
   handoff that must adapt was
   enumerated -- list sync/async
   pipelines (4 wraps), the optimizer
   middleware (unwrap + re-wrap),
   the async window dispatch (1
   predicate call), both guard flavors
   (2 calls). Connection needs no
   wrap (lazy-queryset contract,
   stated at its resolver docstring);
   types-resolvers needs no direct
   reference (transitive seam
   consumer). No member lacks a
   mechanism its contract requires.

### Enumeration

Instruments: `git grep -n <pat> HEAD --
django_strawberry_framework` (directory
pathspec, never `**/*.py`) plus the
AST census probe `/tmp/e6_probe.py`
(run against `git archive HEAD` bytes
and worktree bytes; both ALL OK --
see Pending execution) plus
full-body reads of every hit file at
HEAD bytes.

- `_AsyncQuerySetRows`: 1 class def
  (owner `:442`) + 1 construction
  (wrap `:471`) + 1 `isinstance`
  (is_ `:465`) + 1 `isinstance`
  (unwrap `:477`) + prose. Zero
  constructions outside the owner;
  zero external `._queryset` reads.
- `wrap_async_queryset_adapter`: 1 def
  + 5 calls (list 4 / extension 1)
  + 2 imports + prose.
- `unwrap_async_queryset_adapter`:
  1 def + 1 call (extension) + 1
  import + prose.
- `is_async_queryset_adapter`: 1 def
  + 0 production calls + 16 oracle
  mentions (imports + pins, 2 files).
- `is_async_only_iterable`: 1 def +
  5 calls (owner 1 / list 3 /
  resource 1) + 2 imports + prose.
- `reject_async_iterable_in_sync_context`:
  1 def + 2 calls (list / connection)
  + prose.
- `__aiter__` defs package-wide: 2
  (adapter + `_ResumedStream`,
  latter excluded in R-stream).
  `__anext__` defs: 1
  (`_ResumedStream`).
- `isinstance` async-shape sites: 5,
  each classified -- predicate body
  `:439`, connection `:1097` /
  `:1143` / `:1637` (R-conn), patch
  `:121` (R-patch).
- `aiter(` sites: 2, both inside the
  resource cleanup / window pair
  (consumers of classified values,
  not classifiers).
- connection.py family refs: 0
  (adapter / predicate / trio all
  absent; the guard call is e5's
  flavor composition layered on this
  family's mechanism).
- Snapshot census (`9aaaad5d`):
  identical counts, same files.

### Challenges

Each rule in the family: changes posited,
definition counts; the probe runs are
the execution leg (`execution-verified`
for the census counts;
`static-reviewed` for the contract
differences, each verified against
both bodies).

- C1 (adapter shape): the adapter must
  refuse sync iteration explicitly
  (raise in `__iter__`) instead of by
  omission. Forced moves: **1** (the
  class); the trio + all 6 consumer
  calls follow by name. (F-adapt)
- C2 (wrap contract): `wrap_` must
  also adapt a new source shape.
  Forced moves: **1** (`wrap_`); the
  5 call sites follow. (F-adapt)
- C3 (predicate): a new async-only
  shape must be recognized (the
  querysets-file C8 challenge,
  re-derived). Forced moves: **1**
  (the predicate); the guard + 4
  consumer calls follow; connection's
  3 branches do NOT move (which is
  R-conn's proof). (F-pred)
- C4 (principle 11): remove
  `is_async_queryset_adapter` and
  inline it. Forced moves: **0** in
  production, 16 oracle rewrites plus
  a new private-class import in a
  second test file -- for zero
  change-obligation relief. KEEP
  (F-adapt; D1 homes the
  owner-docstring clause).
- C5 (guard coverage): a third read
  flavor needs the iterable refusal.
  Forced moves: **0** new defs (the
  new site composes the guard; proves
  the guard is the single spelling).
  (F-pred)
- C6 (round-trip): unwrap's tuple
  gains a member. Forced moves: **1**
  (`unwrap_`) + its 1 consumer
  (extension `finish`). (F-adapt)
- R-C1 (route connection through the
  predicate): **refused** -- would
  misroute every queryset down the
  sync branch under async execution
  (R-conn).
- R-C2 (route the patch guard through
  the predicate): **refused** -- must
  stay branch-faithful to upstream
  (R-patch).
- R-C3 (one `__aiter__` adapter with
  the stream): **refused** -- different
  subject and contract (R-stream).
- R-C4 (one async refusal with the
  awaitable guards): **refused** --
  awaitable vs stream subjects, e1's
  side owned elsewhere (R-await).

## Findings

### F-adapt -- CONFIRMED: one completion adapter, one trio, zero twins

Contract + variation: a final sliced
QuerySet under async execution
completes through an object exposing
ONLY `__aiter__`, so graphql-core
cannot select synchronous ORM
iteration in an event-loop thread.
Varies on source shape (wrap's
QuerySet-vs-passthrough arm) and
completion color (wrap iff async).
Sites + roles: definitions -- the
class (`:442`-`:460`) + trio
(`:463`-`:478`), all at the owner.
Consumers -- 5 wrap calls + 1 unwrap
call (System trace above). Oracles -- the
semantics / re-wrap / round-trip /
live pins (System trace above).
Challenges: C1 / C2 / C4 / C6, each
count 1 (C4 counts 0 in production,
which is the KEEP evidence).
Owner + lifetime: [querysets.py][querysets]
owns it (narrowest module every
consumer -- list flavor, optimizer
middleware -- already imports for
queryset machinery; no dependency
reversal; the adapter is pure
delegation, nothing stored beyond
the inner queryset, no lifetime
beyond the completion). The class
stays private with the trio as its
vocabulary: wrap constructs (sole
construction site), unwrap
destructures with the flag
production branches on, is_ names
the type for external readers.
Principle-11 decision (F9's routing):
KEEP `is_async_queryset_adapter` --
zero production readers is by
construction (unwrap fuses the flag),
not by accident; 16 oracle sites
depend on the boundary name as
trio-consistency pins; deletion
relieves no change obligation (a
3-line `isinstance` has no drift
surface) while adding the
private-class import to a second
test file. Recorded here; the
one-line owner clause is D1.
Migration: none -- already single
(every link composes by name,
probe-pinned both states).
Distinct behavior kept: the
non-queryset passthrough (callers
never pre-check); the `(val, False)`
arm (extension's `finish` is a
conditional re-wrap); the `TypeError`
gate (constructor misuse fails at
construction, prefix-pinned).
Behavioral proof:
execution-verified (probe R1/R2 both
states ALL OK -- defs, calls,
absence, encapsulation) + the
committed oracles above (cited by
content, no pytest per dispatch).
Structural gate: none proposed --
bypass means a second `__aiter__`
queryset wrapper or an inline
async-only spelling, whose
future-site population cannot be
enumerated without a bespoke
existence test per helper (DRY.md:
never); the no-`__iter__` oracle +
the predicate-arms oracle + the
probe census pin the composition
instead. The census stands as trace
evidence, not a committed gate. A
red result would be a defect, not a
gate.
Coupling: D1 (doc-only clause) --
lands wherever prose lands; no
behavioral coupling.
Freshness: fingerprints in System
trace (all three states for indexed;
HEAD/worktree for cited + oracles).

### F-pred -- CONFIRMED: one async-only spelling, composed everywhere

Contract + variation: async-only ==
`AsyncIterable and not Iterable`,
with the `not Iterable` half
carrying the QuerySet carve-out (a
QuerySet is both and must never
classify). Varies on recognized
shapes only; the carve-out is
fixed. Sites + roles: definition --
the predicate (`:426`-`:439`) at
the owner. Consumers -- the
in-module guard (`:509`) + 4
composed calls (System trace above) +
2 transitive seam reads. Oracles --
the arms pin (QuerySet-False) + the
bound-seam suite + the guard-shape
pins (System trace above; guard wording
pins are e5's).
Challenges: C3 (count 1, connection
excluded by non-movement) / C5
(count 0 new -- proves single
spelling).
Owner + lifetime: [querysets.py][querysets]
owns it (the queryset-machinery
module; every consumer already
imports it; pure predicate, nothing
stored).
Layering note (no ownership clash):
the guard body `:482`-`:513` sits
under TWO rules -- this family owns
its MECHANISM (the `:509` predicate
composition: a shape change counts
1 here), e5 owns its WORDING (the
recourse f-string: a wording change
counts 1 there). Each challenge
moves exactly one owner; neither
family can absorb the body without
splitting it.
Migration: none -- already single.
Distinct behavior kept: the sync
fallback in `_windowed_rows_async`
(querysets keep SQL `LIMIT`); the
guard's no-op under async execution
(the native executor consumes the
value itself).
Behavioral proof:
execution-verified (probe R1 both
states -- 1 def, 5 calls, 5
classified shape sites) + oracles
by content. Structural gate: none
proposed, same reasoning as F-adapt
(the arms oracle pins the
carve-out; a red census would be a
defect). Coupling: none.
Freshness: as F-adapt.

### R-conn -- REJECTED: connection's async-shape branches are not the predicate

Shared form considered: routing
[connection.py][connection] `:1097` /
`:1143` / `:1637` through
`is_async_only_iterable`.
Contract differences (each
independently fatal):

1. The dispatch pair asks "may the
   async executor stream this" and
   must answer YES for a QuerySet
   (the branch it takes -- the async
   page iterates `fetch_queryset`
   and counts via `acount`);
   the predicate answers NO for a
   QuerySet by construction. R-C1
   misroutes every queryset.
2. The admission guard is a three-arm
   UNION (`Iterable` OR
   `AsyncIterable` OR `__getitem__`)
   answering "is this paginatable";
   the predicate is a DIFFERENCE
   answering "is this ONLY
   async-iterable". Opposite
   questions, opposite queryset
   answers.
3. Lifecycle: the dispatch mirrors
   `ListConnection.resolve_connection`
   (stated at the `:1018` docstring);
   it moves with the Relay
   pagination shape, not with the
   package's misuse vocabulary.

Reconsideration trigger: the
connection field ever needs to tell
an async-only consumer source apart
from a queryset (e.g. a new
async-only branch beside the lazy
path) -- that new site composes the
shared predicate; it is not a
fourth spelling. (Worktree note:
the `:1637` getitem-arm hardening
preserves the union; trigger
unfired in both states.)
Disposition: converges with File
rows connection-F4 + querysets-F10
(re-tested fresh here -- counts,
branches, and the queryset fork
re-derived; no new index row).
Challenges: R-C1 refused; C3's
non-movement is the positive
proof. Freshness: as F-adapt.

### R-patch -- REJECTED: the executor-branch mirror is not the predicate

Shared form considered: routing
[graphql-patches.py][graphql-patches]
`:121` through
`is_async_only_iterable`.
Contract differences (each
independently fatal):

1. Vocabulary ownership: the mirror's
   first half MUST be upstream's own
   `is_iterable` (branch fidelity:
   it moves iff graphql-core's
   `complete_list_value` branch
   moves); the predicate's second
   half MUST be `collections.abc`
   `Iterable` (the QuerySet
   carve-out). Neither side may take
   the other's token.
2. Behavioral fork (prior
   probe-verified, trigger state
   re-checked): graphql's
   `is_iterable` excludes str /
   mapping where `collections.abc`
   includes them, so an async-str
   shape takes the upstream branch
   while failing the package
   predicate -- the conjuncts are
   observably different predicates,
   not two spellings.
3. Import direction: the patch
   module is version-pinned
   upstream-mirroring code that
   cannot import package queryset
   machinery (its lifecycle is
   owned by the patch-application
   path, spec-050 Decision 13).

Reconsideration trigger: upstream
retires the branch the patch
mirrors (patch deleted -- nothing
to route) or adopts the package
spelling as its own branch (then
one rule -- consolidate). Trigger
state re-checked fresh: the guard
still mirrors at `:121` (worktree
`:122`), upstream branch intact.
Disposition: converges with File
row patches-R1 (re-tested fresh
here; no new index row).
Challenges: R-C2 refused both
directions (neither direction's
change may move the other; a
shared form would own 0 lines both
sides could keep). Freshness: as
F-adapt.

### R-stream -- REJECTED: the subscription stream is not a row adapter

Shared form considered: one
`__aiter__`-adapter rule covering
`_AsyncQuerySetRows` and
[operation-state.py][operation-state]
`::_ResumedStream` (the only other
`__aiter__` def package-wide).
Contract differences (each
independently fatal):

1. Subject: an AsyncGenerator of
   subscription FRAMES (transport
   stream) vs a final sliced
   QuerySet (row completion). No
   caller of one could call the
   other.
2. Mechanism: scope binding -- every
   driver method (`__anext__`,
   `asend`, `athrow`, `aclose`)
   re-binds the operation in the
   calling task -- vs color
   restriction (sole `__aiter__`,
   no `__iter__`). The stream
   answers `__aiter__` with ITSELF
   (it IS the iterator); the
   adapter delegates to the inner
   queryset's.
3. Reasons to change: transport /
   operation-binding lifecycle vs
   GraphQL completion color. A
   frame-binding change and a
   row-completion change never
   co-move.

Reconsideration trigger: a
queryset-row path needs operation
binding around its iteration (or a
subscription path starts
completing queryset rows) -- then
the new site COMPOSES the two
(one wraps the other), still not
one merged adapter; only a shared
subject would merge them.
Disposition: NEW rejection row for
Worker-0 (`subscription-stream-scope-binding-vs-row-adaptation`,
owner
[operation-state.py][operation-state]
`::_ResumedStream`, files
`operation_state.py` +
`querysets.py`, rejected with the
trigger above).
Challenges: R-C3 refused.
Freshness: as F-adapt.

### R-await -- REJECTED: the awaitable guards are not the iterable guard

Shared form considered: one async
refusal covering the family guard
(`:482`) and the awaitable trio
(`:185` / `:4729` / `:4748`).
Contract differences (each
independently fatal):

1. Subject: a single awaitable VALUE
   (coroutine / future from a hook
   return) vs an async-iterable
   STREAM (rows from a resolver
   source). Different shapes,
   different call sites (hook
   returns vs resolver sources),
   different remedies.
2. Ownership: the awaitable side is
   owned by verified Family
   `awaitable-refusal-and-disposal`
   (e1 -- disposal + refusal
   vocabulary); absorbing it here
   would split e1's rule.
3. Error-class fork inside the
   awaitable side itself
   (`SyncMisuseError` vs the
   residual `ConfigurationError`)
   -- the trio is already two
   rules, not one, and neither is
   the stream rule.

Reconsideration trigger: a refusal
site must reject BOTH shapes
through one entry -- then a thin
composing wrapper calls both
guards; the predicates stay
separate (an awaitable is never
async-iterable and vice versa).
Disposition: converges with the e1
family row (no new index row; the
exclusion is recorded here).
Challenges: R-C4 refused.
Freshness: as F-adapt.

## Defects

### D1 -- owner docstring should record the `is_` KEEP (doc-only, homed to closeout)

DRY.md principle 11 requires a KEEP
to be recorded at the owner so the
question is not re-raised; F-adapt
decides KEEP for
`::is_async_queryset_adapter` (zero
production readers by construction
-- unwrap fuses the flag; 16 oracle
sites depend on the boundary name;
deletion relieves no change
obligation). The one-line clause
belongs on the `:463` docstring.
Doc-only, zero behavioral risk;
this item lands no tracked edits
per dispatch, so the clause is
homed to closeout. No other
defects found: the matrix is
discharged, every handoff
enumerated, all projections hold.

### D2 -- `_optimize` docstring should record the unwrap / re-wrap contract
(Worker-2) (doc-only, homed to closeout)

`optimizer/extension.py::_optimize`
unwraps the family adapter at entry
(`:1214`) and conditionally re-wraps at
`finish` (`:1217`), but its docstring
(Steps 1-5) never states the contract --
the artifact's Projections bullet claims
it does (see the Worker-2 correction A).
Behavior is oracle-pinned (the 4
optimizer adapter tests plus the
list-field round-trip test); only the
prose is missing. One clause beside the
existing steps, same shape as D1.
Doc-only, zero behavioral risk; homed to
closeout with D1.

## Pending execution

- `proof:` `uv run python
  scripts/workspace.py run
  dry/asyncrows-e6/consolidate -- sh -c
  'python3 /tmp/e6_probe.py head-tree'` --
  execution-verified (run
  `dry-20261001T014044-2a5afd`, exit 0,
  `E6-PROBE ALL OK`; discharges the
  F-adapt / F-pred census counts,
  the R-conn absence check, and the
  R-stream / R-patch population
  pins at HEAD bytes). `<copy>` =
  `/private/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/dsf-ws/0b901faeac791a7b/dry/slots/slot-2`.
  The `head-tree/` extraction +
  `/tmp/e6_probe.py` stay on disk
  for Worker-2; remove by explicit
  path after verification.
- Worktree comparison (same command,
  `.` as the tree): run
  `dry-20261001T014047-69fdc8`,
  exit 0, identical ALL OK (same
  counts, shifted lines) --
  decision-neutral drift proved.
  Informational; discharges nothing.
- Shared-tree authorization unspent:
  zero edits landed, no oracle
  added, no pytest run -- no `gate:`
  command owed. Sharded / pg cells
  inapplicable by construction (the
  finding is code singularity over
  pure classification / delegation;
  no database, alias, or dialect
  decision varies it).

## Judgment

The async-only queryset row adaptation
is one rule with a single owner: the
adapter class + wrap / unwrap / is
trio and the async-only predicate +
guard consumer are each defined once
in [querysets.py][querysets], with 5
wrap calls, 1 unwrap call, 5 predicate
calls, and 2 guard calls composing by
name across 4 consumer files, and zero
second bodies package-wide (AST census:
6 family defs at 1 site each, 2
`__aiter__` defs classified, 5
async-shape sites classified, 0
external private reads). The
lookalikes are distinct per-site rules
-- the inclusive connection branches,
the upstream-faithful patch mirror,
the subscription scope binder, and the
awaitable guards -- each single-owned,
each excluded on contract differences
with a trigger. Zero production edits;
one doc-only defect filed. The family
is CONFIRMED as consolidated.

Index impact for Worker-0: flip
`async-only-queryset-row-adapter` to
`consolidated` (recommend files-covered
5 -> 8 with roles: 4 consumer files +
2 transitive/excluded-production files
([types-resolvers.py][types-resolvers],
[graphql-patches.py][graphql-patches])
+ [operation-state.py][operation-state];
all defs in [querysets.py][querysets]);
add the R-stream rejection row named
above; R-conn / R-patch / R-await are
converges (no new rows).

Item-scoped diff state: no tracked edits;
one new untracked artifact (this file).

## Independent verification (Worker-2)

Trace re-derived at HEAD `83998e08`
bytes with independent instruments
(directory-pathspec `git grep` censuses
plus own AST probe
`/tmp/e6_verify_probe.py`, written fresh
for this pass -- W1's probe never
opened). Counts below are the probe's;
every prose claim was checked against
full-body reads at HEAD bytes. Three
artifact blemishes found (A/B/C below),
all verdict-neutral, corrected on the
record here; one filed as D2. Nothing
else differs.

### Trace (mine)

Owner:
`utils/querysets.py::_AsyncQuerySetRows`
-- the narrowest module every consumer
already imports for queryset machinery
(imports verified at list-field,
extension, resource-policy, connection).
Definitions, all at the owner, one body
each: the class (`:442`), `wrap_`
(`:468`), `unwrap_` (`:475`), `is_`
(`:463`), the predicate (`:426`), the
guard (`:482`). Consumers by name: 5
wrap calls (list `:1466` / `:1495`
sync-gated, `:1512` / `:1541` async;
extension `:1217`), 1 unwrap call
(`:1214`, flag drives `:1217`), 5
predicate calls (owner `:509`, list
`:1361` / `:1365` / `:1771`, resource
`:1258`), 2 guard calls (list `:1772`,
connection `:2072`). Zero second
bodies: exactly two `__aiter__` defs
(adapter `:459`, stream `:848`), one
`__anext__` (`:852`), zero adapter
`__iter__`, 1 construction (in `wrap_`),
2 adapter `isinstance` (in `is_` /
`unwrap_`), 2 `._queryset` loads + 1
store all in-owner, 5 `isinstance`
async-shape sites each classified, 2
`aiter(` calls in the cleanup pair.
`is_`: 0 production calls, 16 oracle
lines in 2 files (recounted).
Rejections: connection dispatch + union
guard (inclusive, must-answer-yes),
patch mirror (upstream token), stream
binder (frames, self-iterator),
awaitable trio (single values,
e1-owned). Same owner, same counts,
same roles as W1.

### Reconciliation

- F-adapt CONFIRM. Every census above
matches; the KEEP rationale holds
(unwrap fuses the flag, so 0 production
readers is by construction; 16 oracle
sites plus the second-file private
import cost verified).
- F-pred CONFIRM. 5 composed calls; the
e5 layering (mechanism here, wording
there) checked against the verified e5
artifact, which cites the same `:510` /
`:1772` / `:2072` lines. No clash.
- R-conn endorsed (converges
connection-F4 + querysets-F10 -- both
rows exist, substance matches; F10's
older blobs re-derived fresh here). All
three differences verified: dispatch
takes the `acount` branch for querysets,
union vs difference, the
`ListConnection` mirror sentence at the
`:1020` docstring.
- R-patch endorsed (converges
patches-R1 -- exists, mapping-fork
substance matches). Upstream token
import, the str/mapping fork (rechecked
against installed graphql-core 3.2.8
source: "not a string or a mapping"),
and the shape-validating mirror module
all verified; trigger unfired (guard at
`:121` / worktree `:122`, upstream
branch intact).
- R-stream endorsed. The NEW row
`subscription-stream-scope-binding-vs-row-adaptation`
fits the index rejection form with
complete fields (owner, both files,
trigger). All three differences
verified against the `_ResumedStream`
body.
- R-await endorsed (converges verified
e1, which owns all four awaitable
names). Trio lines and the
`SyncMisuseError` vs `ConfigurationError`
fork verified.
- C1-C6 counts and R-C1-R-C4 refusals
all agree. Matrix axes 1-4 and 6 agree.
- D1 endorsed: the `:463` docstring is
one line with no KEEP clause; doc-only
homed to closeout is the correct
routing for a zero-edit item.
- Index instructions judged as exact
replacement text: flip to
`consolidated`; 5 -> 8 arithmetic holds
(owner + 4 consumers + transitive + 2
excluded-production); converges need no
rows. Sound for Worker-0 to transcribe.
- Structural-gate reasoning agreed: no
committed gate (future bypasses
unenumerable; bespoke existence tests
forbidden); oracles pin the composition.
The census stays trace evidence.

### Corrections (blemishes, verdict-neutral)

A. The Projections bullet claiming an
optimizer `_optimize` docstring unwrap /
`finish` re-wrap clause is false: no
unwrap / re-wrap / finish / adapt prose
exists anywhere in
`optimizer/extension.py` (grep-verified;
only the import, the code, and unrelated
`unwrap_graphql_type`). The behavior
holds (code + 4 optimizer tests +
round-trip oracle); the docstring clause
does not exist. Filed as D2 above --
doc-only, closeout alongside D1. "All
claims hold" stands corrected to
all-but-this-bullet.
B. Dirt range labels are off by one in
two places (substance verified):
list-field prose hunks sit AT `:1347`
(Decision 8 cite), `:1574`-`:1579`
(tiebreaker), `:1609`-`:1614` and
`:1618`-`:1622` (factory comments) --
inside the cited "no hunk" ranges, all
prose, family code intact; the resource
narrowing hunk is `@@ -1217,9`, not
`:1218`.
C. "Patch guard intact" glosses the
worktree conjunct reorder (`:121` checks
`not is_iterable` first, matching
upstream; worktree `:122` checks
`isinstance` first). Token/set fidelity
intact, R-patch holds in both states --
verdict-neutral concurrent dirt, named
here for precision.

### Proof

- Own probe, three states, all green:
`E6-VERIFY ALL OK` on head-tree (run
`dry-20261001T015754-dd7947`), worktree
`.` (run `dry-20261001T015801-75853e`,
119 files -- the 2 extra are untracked
`utils/lazy.py` + `utils/truth.py`,
proven family-free), snap-tree
`9aaaad5d` (run
`dry-20261001T015811-a80724`). Trees
extracted in run
`dry-20261001T015720-ad6fed`. 23 checks
each: 6 defs at 1, calls 5/1/0/5/2,
dunders 2/1/0, queryset attr 2 loads +
1 store + 0 external, shape sites 5,
`aiter(` 2, oracle 16 lines / 2 files.
- Fingerprints: all 13 HEAD/worktree
pairs plus 5 snapshot blobs re-hashed
-- match W1 exactly. Snapshot carries
`truth.kind` with 0 `TypeGuard`; HEAD
the reverse; census identical across
the fork.
- Zero-edit: `git diff 7788046f --stat`
on package/tests/examples is empty;
status count 453 unchanged since
dispatch; only drift is plan-file
bookkeeping. Item diff is the untracked
artifact only.
- No pytest (dispatch forbids; censuses
are static; oracles cited by content).
- Environment note for Worker-0 (not
e6): slots 1-3 venvs carry
site-packages damage since Sep 30
~03:35 local (dunder sources deleted;
shared venv and slot-4 intact).
AST-only runs are unaffected (both
probes green); import-executing runs
there fail. Provenance does not catch
it (it never imports third-party
packages).

Verdict: every row survives on
independent evidence. `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection.py]: ../../django_strawberry_framework/connection.py
[extension.py]: ../../django_strawberry_framework/optimizer/extension.py
[graphql-patches.py]: ../../django_strawberry_framework/_graphql_core_patches.py
[list-field.py]: ../../django_strawberry_framework/list_field.py
[operation-state.py]: ../../django_strawberry_framework/extensions/operation_state.py
[querysets.py]: ../../django_strawberry_framework/utils/querysets.py
[resource-policy.py]: ../../django_strawberry_framework/resource_policy.py
[types-resolvers.py]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-extension.py]: ../../tests/optimizer/test_extension.py
[test-list-field.py]: ../../tests/test_list_field.py
[test-querysets.py]: ../../tests/utils/test_querysets.py
[test-relations-async.py]: ../../examples/fakeshop/test_query/test_relations_async_api.py
[test-resource-policy.py]: ../../tests/test_resource_policy.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
