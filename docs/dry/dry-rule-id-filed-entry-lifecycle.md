# DRY review: `id-filed-entry-lifecycle`

Status: verified
Run: 0.0.15 2026-10-01-12

Item kind: FAMILY (responsibility family). Fresh expectation-first trace at
current bytes; confirmed consolidation implemented at the owner with
permanent structural gates in the same change.

## System trace

The rule, re-derived (not inherited): entries filed under `id(owner)`
beside a weak reference to the owner; every read answering only while that
reference still points at the asker; the reference's own death callback
removing the entry only while the filed reference is still the dead one (the
key may already name a successor that reused the address). At WT-before
bytes the lifecycle is spelled independently in each of `PrivateAuthority`
(`settle` files, `settled` + `recall` verify) and `PrivateMembership`
(`accept` files, `recall` verifies), both in
`django_strawberry_framework/utils/private_state.py`.

Fingerprints (HEAD blob / baseline / WT per the finding record):

- HEAD `dd0b6691` (unmoved throughout; detached, intended).
- HEAD blob `ec4d8fc8`; ITEM_BASELINE `cf52e8ba2f34ccea308f203c323e7a13bbae3e8f`
  blob `613a28ca`, identical to WT-before `613a28ca` (diff vs baseline
  empty pre-edit: the dirt predates dispatch). WT-after `78d6692f`
  (this item's consolidation).
- Hunk attribution vs HEAD: exactly one pre-existing hunk, at
  `PrivateMembership.accept` (the `owner.__dict__[...]` write becomes a
  two-line comment plus `object.__setattr__`); present at baseline, and no
  `## Owned changes` ledger row names this file, so concurrent-external.
  Post-edit diff vs baseline shows those lines as context (byte-identical);
  the consolidation replaces only the filing tail beneath them. Never
  edited, reverted, or tidied.

Whole-package sweep for the mechanism (every hit triaged; §Enumeration):

- `weakref|ReferenceType` census: 13 hits — the target (8), the one-arg
  lease payload in `extensions/operation_state.py`, slot declarations,
  prose.
- Builtin-`id(` census: 64 hits — the target's 5 code sites + prose;
  every other hit a non-store (seen-sets, loop guards, sort keys, reprs)
  or an out-of-contract memo/stash (each excluded under R2/R3/R5 with its
  contract difference).
- Two-argument `ref(` census: exactly the 2 filing sites pre-change,
  exactly the driver's 1 site post-change (a gate pins this).
- `WeakKeyDictionary|WeakValueDictionary|WeakSet|weakref.|finalize`
  census: zero weak containers package-wide (`finalize` hits are all the
  type-finalizer vocabulary).
- Third filing site: none. Nearest same-word neighbor is `IdentityMap`
  in `django_strawberry_framework/utils/truth.py` (WT `711352b1`,
  untracked concurrent work — read for the sweep, never touched):
  id-keyed, strong keys, no verify, no callback (R2).

Consumer census (fresh `PrivateAuthority|PrivateMembership|private_state|
_settled|_accepted` grep over package + tests + examples): exactly 5
production importers, all composing `settle`/`settled`/`recall`/`accept`
by name — `schema.py` (`_SCHEMA_ENFORCEMENT`, `_SCHEMA_EXTENSIONS`),
`extensions/operation_state.py` (`_OPERATION_CARRIERS`,
`_PACKAGE_MANAGED`), `extensions/resource_policy.py`
(`_EXPLICIT_POLICY`), `extensions/debug.py` (`_ACKNOWLEDGEMENT`),
`optimizer/extension.py` (`_OPTIMIZER_CONFIGURATION`). Zero touches of
`_settled`/`_accepted` outside the target (the test-tree hits are
`*_accepted` test-name noise). Zero test imports of `private_state`.
Projection: the kanban tracked-path constants row (mechanical listing).

Oracles (all pre-existing, none moved): the box-immutability row, the
optimizer-tamper row, the settle-once rows, the collectability rows, the
carrier-dies-with-it row, the explicit-policy read-out row, and the live
`test_extension_isolation_api` + `test_resource_policy_api` modules (node
ids under Behavioral proof). Projections: the module docstring's
`id()`-filing paragraph (`private_state.py:64-74`, already single-owned —
still true verbatim post-change), both class docstrings, the five
consumers' rationale paragraphs, spec-047 (design record; grep finds no
`forget`/`id(owner)`/`_settled`/`_accepted` pin — the two-spelling shape
is nowhere normative).

Connected reads: the schema enforcement-record prose (`schema.py:471-524`,
the R1 boundary re-derived), the three `_Accepted*` payload records (all
primitives — §R1), `operation_state.py:673` (lease payload),
`truth.py:625-708` (`IdentityMap`), `walker.py:307-326` (strong-hold
memo), `filters/sets.py:2990-3035` (call stash), `extension.py:1600-1623`
+ `selections.py:196-205` (frame memos), `types/base.py:1279` (loop
dedup, representative non-store read), `rev-schema.comments.md` R13
(standing trigger "private-state mechanics changing": judged UNFIRED —
the weak-ref-to-owner edge both sentences rest on still verifies in both
classes' read paths, now via composition; the two tests it names are in
the seam scope and pass).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Discharged by census. Five
   consumers across engine/runner/policy/disclosure/optimizer, all
   composing by name; no flavor-local twin. Same-word candidates
   excluded: `IdentityMap` (R2), the operation lease (no `id(`/`ref(`
   calls — slots-only weakref mention; standing rejection trigger
   re-checked unfired), the boundary marks (`_boundary_ordering.py`
   clean at `197eea8e`, still cooperative signals; standing trigger
   unfired), the policy-copy handout (the recall-then-copy seam is
   intact — `recall` still answers the filed object itself).
2. **Sync/async twins.** Inapplicable with reason (re-derived from the
   bodies): pure in-memory dict/weakref work, no I/O, no lock, no await
   point; called from sync constructors and both-colored read paths.
   Coloring the driver would put an await point inside
   construction-time settlement.
3. **Derived rather than repeated knowledge.** THE find, consolidated.
   "Which record belongs to this owner" was derived twice (`id()` +
   weakref verify + guarded callback per class); now once in
   `_IdFiledEntries`. Nothing outside the file re-derives owner identity
   (§Enumeration).
4. **Inverse / round-trip pairs.** `settle`/`recall` (authority) and
   `accept`/`recall` (membership) stay per-class pairs: the payload
   halves differ (R1), so they are not cross-class halves. `settled()`
   is a construction record, not a read half; `forget` is lifetime
   cleanup, not an inverse. No pair spans modules.
5. **Contracts restated in another medium.** Counted, all
   zero-definition: the module/class docstrings + consumer rationale
   paragraphs (projections, unmoved — the filing paragraph stays true
   verbatim), the oracle rows above (assert tamper/refusal/
   collectability through public seams, never the filing spelling). A
   lifecycle change now moves 1 definition + zero oracles (oracles assert
   behavior, which is unchanged).
6. **Enforcement by omission.** The id-keyed-store family enumerated via
   the `id(` census (64 hits): the two member stores compose the driver
   post-change; every other hit is out of the driver's contract by
   construction (strong keys, scope-bound keys, or not a store —
   R2/R3/R5). No member lacks a guard the contract requires. No defect.

### Enumeration

Instruments (all at WT bytes): `weakref|ReferenceType` census (13
hits); builtin-`id(` census (64 hits, comments included, triaged by
mechanism); two-arg `ref(` census (2 sites pre-change, 1 post-change);
`_settled|_accepted` + importer census; `Weak*` container census (0).
Every hit homed:

- Definitions pre-change (2): the authority filing half
  (`settle`+`settled`+`recall` filing lines), the membership filing half
  (`accept`+`recall` filing lines). Post-change (1): `_IdFiledEntries`
  (`file`+`has`+`verified`+`_live_entry`+`forget`).
- Consumers (7 stores / 5 files, §System trace): zero moves — the
  public `settle`/`settled`/`recall`/`accept` signatures and contracts
  are unchanged.
- Oracles (7 seam nodes + 2 live modules, §System trace): zero moves.
- Exclusions: `IdentityMap` (R2); the walker memo, the frame memos
  (extension, selections), the filters call stash, the lateral local map
  (R3); the lease payload (R4); seen-sets / loop guards / sort keys /
  reprs / prose (~40 hits, R5). Comment/prose hits are never sites.

### Challenges

Lifecycle axes (before → after; consumers, oracles, projections listed,
never counted):

- C1 key derivation (file under a different key / add a key component):
  2 → 1 (`settle`+`accept` file sites → `file`).
- C2 read-verify semantics (verify differently): 2 → 1 (authority's two
  read predicates + membership's one → `_live_entry`, the single
  predicate `has`/`verified` share).
- C3 death-callback guard (drop/alter the `entry[0] is dead` check):
  2 → 1 (both `forget` closures → the driver's one).
- C4 locking (thread the entry dicts): 2 → 1.
- C5 construction-record semantics (`settled()` stops answering for
  empty payloads): 1 → 1 (authority only — non-goal control proving
  `settled()` stayed authority's).
- C6 evidence resolve (partial answer on dead evidence): 1 → 1
  (membership only — non-goal control proving the R1 carve).
- Payload carve (R1, re-derived): a strong-hold change moves authority
  only; an evidence/box/resolve change moves membership only. The merge
  was attempted both directions and fails: filing the extension sequence
  as an authority payload roots the schema forever (bound-method
  factories + execution contexts reach it back — `schema.py:517-524`);
  answering a policy through evidence is incoherent (a policy is one
  primitives record, not a sequence, and ints/strings admit no weakref).

Disproof attempts on the filing consolidation (inputs, outputs, errors,
state transitions, timing, hooks, reasons to change): file/verify/forget
shapes identical modulo the owning dict; neither path raises anything of
its own (an unweakrefable owner raises `TypeError` identically — both
call `ref(owner, ...)`); overwrite-on-file identical (settle-overwrite,
accept-replaces); callback timing identical; no extension points in
either; no one-sided filing change found ("accept stops replacing" moves
the evidence/attribute write and still ends in one `file` call; "settle
refuses double-settle internally" is a guard, not filing — and the
driver deliberately refuses nothing, R6).

## Findings

### F1 `id-filed-entry-lifecycle` (CONFIRMED consolidation — landed)

- **Contract + variation.** Entries filed under `id(owner)` beside a
  weakref; reads answer only while it points at the asker; the death
  callback removes only while the filed ref is still the dead one.
  Varies on payload type only (`Generic[PayloadT]`).
- **Sites + roles.** Definition post-change: `_IdFiledEntries` (plus
  `_Entry` + `PayloadT`). Both former definitions are now one-line
  compositions. Consumers: 7 stores / 5 files (zero moves). Oracles:
  §System trace (zero moves). Projections: the module filing paragraph
  (unmoved, still verbatim true), class docstrings, consumer rationale
  paragraphs, spec-047.
- **Challenges.** C1–C4 count 2 → 1; C5–C6 count 1 → 1 as controls.
  Counts are definitions; the 7 consumers + 9 oracle rows + projections
  move zero.
- **Owner + lifetime.** `_IdFiledEntries` in
  `django_strawberry_framework/utils/private_state.py` (principle 7:
  narrowest cohesive owner both consumers already live in; no dependency
  reversal — same module; no other module needs it — the census finds
  exactly two filing sites package-wide). Principle 4: owner = each
  store's `_filed` driver holding `_entries`; validity key = the filed
  weakref still resolving to the asking owner; publish point =
  `settle`/`accept`; who may mutate = `file` (overwrite) + `forget`
  (guarded removal); invalidation = owner death via the callback, only
  while the entry is still the filed one.
- **Migration.** `PrivateAuthority.__init__` holds
  `_IdFiledEntries[StateT]`; `settled` → `has`, `settle` → `file`,
  `recall` → `verified` (docstrings stay — the construction-record and
  never-settled contracts are authority's own). `PrivateMembership`
  holds `_IdFiledEntries[tuple[_Evidence[MemberT], ...]]`; `accept`
  keeps evidence-taking + the attribute write and files via `file`;
  `recall` resolves the `verified()` payload through the unchanged
  loop. `_settled`/`_accepted`/`_Accepted` deleted (zero external
  touches by census; only regenerable scratch cited `_Accepted`). Net
  +64/−30 production; behavior identical line-for-line (moved bodies
  verbatim modulo the dict-attribute rename inside the driver).
- **Distinct behavior.** Everything per-class stays per-class: write
  policy (caller-guarded settle vs replacing accept — the driver
  refuses nothing), `None` meanings (authority: never-settled;
  membership: never/reused/gone; driver: no live entry for this
  identity), retention (strong vs evidence), the resolve loop, the box
  machinery, the `settled()` record. Recorded in the driver docstring +
  the untouched class docstrings (R1/R6; principle 10).
- **Behavioral proof.**
  - Static-reviewed: each touched method is a by-name composition of a
    moved-identical body (diff-verified: the `forget` closure, the
    verify predicate, and the file line moved verbatim; only the
    owning-dict attribute renamed). Rejects a composition that
    reorders, rewords, or re-keys the lifecycle.
  - Execution-verified (workspace run `dry-20261002T032247-cfc652`,
    prove exit 0): baseline 13/13 green; the negative-control mutant
    (dead bypass copy of the driver's body inside `PrivateAuthority`)
    fails exactly the 2 gate rows while all 11 seam rows pass →
    "pinned".
  - Execution-verified (same run): the driver-break mutant
    (`verified` → `None`) fails 9 seam rows (box ×3, tamper,
    read-out-once, collectability ×3, slotted-not-root) and passes 2
    (the None-expecting shape, the non-recall carrier row) →
    "pinned": the oracles exercise the driver.
  - Execution-verified (workspace run `dry-20261002T032315-ff9c63`):
    live `test_extension_isolation_api` +
    `test_resource_policy_api`, 210/210 green.
  - Execution-verified (workspace run `dry-20261002T032433-396fb8` +
    follow-up): the seam scope covers every driver line, and the full
    `tests/test_schema.py` covers `private_state.py` 72/72 = 100% —
    coverage transfers to the existing suites, no new behavior rows
    owed.
  - Shared-tree focused run (the one authorized `--no-cov` run):
    13/13 green (2 gate + 11 seam cases).
  - Seam node ids (7 nodes, 11 cases): the schema suite rows
    (box-immutability, collectability, slotted-not-root), the optimizer
    extension rows (tamper, zero-argument shape), the operation-state
    carrier row, the resource-policy read-out-once row — full ids in the
    prove manifest (§Implementation).
- **Structural gate.** `tests/utils/test_private_state.py`:
  `test_entry_filing_is_spelled_only_in_the_driver` (no bare `id(`/`ref(`
  calls in either store class) +
  `test_death_callback_filing_has_exactly_one_site` (package-wide
  two-arg `ref(` census == the driver's `file`). Population:
  package-wide two-arg `ref(` — the death-callback shape; plausible
  bypass: a third store, or a filing re-spelled beside a new consumer.
  Negative control: the dead-bypass mutant above — both gate rows fail
  while all 11 behavior rows pass (entry 1 "pinned", restore
  byte-proved, blob `78d6692f` before/after). One-arg `ref(` sites
  (lease payload, member/box evidence) are a different mechanism by
  shape and stay invisible by design (stated in the test).
- **Coupling.** None. Adjacency note: the `accept` edit sits directly
  beneath the concurrent-external `object.__setattr__` hunk; those lines
  are byte-identical pre/post (context-only vs ITEM_BASELINE), never
  edited, reverted, or tidied — attribution by diff content.
- **Freshness.** Target HEAD `ec4d8fc8` / baseline `613a28ca` (==
  WT-before) / WT-after `78d6692f`; HEAD `dd0b6691` unmoved. Consumers
  (WT): `schema.py` `7390c985`, `operation_state.py` `5f6f255d`,
  `resource_policy.py` `2971618b`, `debug.py` `b26a7897`, `extension.py`
  `8e3fe7c1`. Exclusions (WT): `truth.py` `711352b1` (untracked),
  `operation_lease.py` `d1d272c5`, `_boundary_ordering.py` `197eea8e`
  (clean), `walker.py` `b71db9e0`, `filters/sets.py` `17dae905`.
  Searched populations: §Enumeration instruments with hit counts. Any
  fingerprint change reopens.

### R1 strong-hold vs evidence payload halves (rejected — re-derives the nominating R-SPLIT)

Considered: one store for both payload kinds. Rejected on the lifetime
split, re-verified against current bodies AND current consumers: every
settled authority payload points at nothing (`_SchemaEnforcement` — a
policy of primitives + flag, `schema.py:471-478`; `_AcceptedPolicy` —
ints + a float; `_AcceptedDisclosure` — one bool;
`_AcceptedOptimizerConfiguration` — two primitives; `ContextVar`;
`bool`), while the accepted extension sequence reaches its schema back
(bound-method factories, execution contexts — `schema.py:517-524`), so
one object cannot hold both ways. Counts: a retention change moves one
side only (C5/C6 + the payload carve under §Challenges). Trigger: a
settled payload that must point at its owner, or evidence that must
survive its member's collection. Durable home: the module docstring
split paragraph + both class docstrings (standing) + the driver
docstring's opacity clause (this item).

### R2 strong-key identity map (rejected — fresh exclusion)

`IdentityMap` (`utils/truth.py:625-708`, untracked concurrent work):
id-keyed like the driver, but holds its keys STRONGLY — the opposite
lifetime answer, sound because its keys are process-lived classes, so no
verify predicate and no death callback exist or are owed. Merging would
couple the collectable-owner lifecycle to a registry that must never
collect. Trigger: `IdentityMap` gaining weak keys with death cleanup.
Durable home: its class docstring (its owner's file, concurrent — this
artifact records the exclusion; no edit there).

### R3 scope-bound id memos (rejected — fresh exclusion)

`walker.py` `_forward_names_memo` (each entry holds its converter
strongly so the `id` cannot recycle; cleared on the subsystem bus),
`optimizer/extension.py` + `optimizer/selections.py` per-execution memos
(the operation/field nodes outlive the frame memo), `filters/sets.py`
`id(child_input)` call stash (children held by the filterset's own data
for the call), `lateral_fetch.py` local name map: in each, the key object
outlives the store, so id-reuse is impossible by scope and no
verify/callback is owed. Trigger per site: the store outliving its keys'
scope. Durable home: each site's own comment (the walker memo already
states its hold; frame/call scopes stated at their readers).

### R4 lease-payload weakref (rejected — fresh exclusion)

`extensions/operation_state.py:673` (`OperationLease(ref(state))`): a
weakref as a revocation payload, with no `id()` filing, no read verify,
no entry cleanup — revocation, not an identity store. Trigger: the lease
gaining an identity-keyed entry table. Durable home: the operation-state
module (standing lease prose).

### R5 local identity bookkeeping (rejected — fresh exclusion)

Loop-dedup sets (`types/base.py:1279`, `mutations/sets.py:1819-1820`,
`registry.py:597-598`, `extensions/debug.py:340-347`), freeze-walk
sets/memos (`rest_framework/resolvers.py:513-546`, `859-915`),
unhashable markers + seen-sets (`utils/inputs.py:519-613`, `1639-1873`),
sort keys (`utils/canonical.py:101`), label strings
(`utils/write_transaction.py:978`), reprs (`utils/querysets.py:3157`):
function-local correlation with no stored lifecycle — not stores. No
trigger (nothing stored, nothing to outlive). No durable home owed beyond
this row.

### R6 write policy + None-meanings per class (intentional separation — recorded at the owner)

The driver refuses nothing and answers one `None` ("no live entry for
this identity"). `settled()`'s construction record (answering for
payloads of every shape including deliberate absence), each caller's
typed double-settle refusal, `accept`'s replace semantics, and the two
`recall` `None` contracts stay per-class: folding refusal into the
driver would couple it to every payload's construction policy (and
`accept` explicitly replaces). Counts: C5/C6 1 → 1. Trigger: a second
store needing the same construction record (then `settled()`-shaped
policy, not filing, is the family). Durable home: the driver docstring's
refusal paragraph (this item) + the untouched `settled()`/`recall`
docstrings.

## Defects

None. No contract-row break found; nothing routes to the maintainer. Soundness notes
closed during the trace (not defects): `IdentityMap` reads skip the `is`
re-check — sound by its strong-hold invariant, which is what makes the key
unrecyclable; the walker memo's `id` key — sound by its stated strong hold;
frame/call memos — sound by scope. The axis-6 store census closes the one
enforcement question this family raises.

## Pending execution

None. Every proof above is execution-verified in the runs cited; no `proof:`
or `gate:` entry is owed. Sharded/PG cells: inapplicable by construction —
the target's code path reaches no database, alias, or dialect decision (pure
in-memory dict/weakref; the live runs used the copy's own default SQLite
only as the app's database, never through the driver). Worker-2 judges the
claim.

## Judgment

CONFIRM and landed. The id-filed entry lifecycle was one rule in two
spellings (C1–C4 all count 2, re-derived fresh); it is now one driver,
`_IdFiledEntries`, composed by both stores, with the payload halves (R1),
the write policy (R6), and five out-of-contract neighbors (R2–R5) excluded
with triggers. Public API, exceptions, callback timing, and `None`
contracts unchanged; 7 consumers + 9 oracle rows + all projections move
zero. Gates: basedpyright 0/0/0, check_any clean, truthful-reads 0 errors,
ruff + commas clean on touched paths. Failability: the gates fail exactly
their 2 rows on a behavior-identical bypass mutant; the seam oracles fail 9
rows on a broken driver; 210 live rows green; the consolidated file at 100%
under the existing schema suite.

## Implementation (Worker-1)

Tracked changes (2 files):

- `django_strawberry_framework/utils/private_state.py` (+64/−30): new
  `PayloadT` + `_Entry` + `_IdFiledEntries` (`file`/`has`/`verified`/
  `_live_entry` + the single `forget`); both stores compose it;
  `_settled`/`_accepted`/`_Accepted` deleted. The pre-existing
  concurrent-external `accept` hunk (`object.__setattr__`, in
  ITEM_BASELINE, no ledger row) preserved byte-identical — diff vs
  baseline shows it as context; diff vs HEAD merges it with the adjacent
  filing replacement, attributable by content.
- `tests/utils/test_private_state.py` (new, +106): the two structural
  gates above; no behavior rows (the existing suites cover the file
  100%).

Untracked scratch (Worker-0 removes by explicit path post-verification):
`docs/dry/temp-tests/dry-idfiled-f53/manifest.json` (the prove manifest
with full seam node ids; evidence in the workspace evidence store under
runs `dry-20261002T032247-cfc652`, `dry-20261002T032315-ff9c63`,
`dry-20261002T032433-396fb8`).

Commit-time note (no action): the new test file sits under a kanban
tracked-path constants root, so hook 1 will rewrite
`examples/fakeshop/apps/kanban/constants.py` when it is staged — the
maintainer's normal stage flow; not run here (unstaged by design, never
commit).

## Index rows for Worker-0

| `id-filed-entry-lifecycle` | `django_strawberry_framework/utils/private_state.py::_IdFiledEntries` (file/has/verified lifecycle; both stores compose by name; R1 payload carve + R6 write-policy separation recorded at the owner) | `django_strawberry_framework/utils/private_state.py` | Family `id-filed-entry-lifecycle` | consolidated |
| `private-filing-payload-carve` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; re-derives the nominating R-SPLIT on fresh evidence — strong-hold vs evidence retention; trigger: an owner-pointing payload or must-survive evidence) | `django_strawberry_framework/utils/private_state.py` | Family `id-filed-entry-lifecycle` | rejected |
| `private-filing-vs-strong-key-identity-map` | `django_strawberry_framework/utils/truth.py::IdentityMap` (rejection recorded here; fresh exclusion — strong keys for process-lived classes, no verify/callback by construction; untracked concurrent work, read-only; trigger: weak keys with death cleanup) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/utils/truth.py` | Family `id-filed-entry-lifecycle` | rejected |
| `private-filing-vs-scope-bound-id-memos` | `django_strawberry_framework/optimizer/walker.py` (rejection recorded here; fresh exclusion — keys outlive the store in the walker memo, the per-execution memos, the filters call stash, the lateral local map; trigger per site: the store outliving its keys' scope) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/selections.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/optimizer/lateral_fetch.py` | Family `id-filed-entry-lifecycle` | rejected |
| `private-filing-vs-lease-payload-weakref` | `django_strawberry_framework/extensions/operation_state.py` (rejection recorded here; fresh exclusion — revocation payload, no id filing; trigger: the lease gaining an identity-keyed entry table) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/extensions/operation_state.py` | Family `id-filed-entry-lifecycle` | rejected |
| `private-filing-vs-local-identity-bookkeeping` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; fresh exclusion — function-local correlation, not stores; no trigger) | `django_strawberry_framework/utils/private_state.py` | Family `id-filed-entry-lifecycle` | rejected |
| `private-filing-vs-write-policy` | `django_strawberry_framework/utils/private_state.py::_IdFiledEntries` (intentional separation recorded here; fresh — the driver refuses nothing, construction policy stays per-class; trigger: a second store needing the same record) | `django_strawberry_framework/utils/private_state.py` | Family `id-filed-entry-lifecycle` | rejected |

## Independent verification (Worker-2)

Pass 1, fresh. The trace below (sites, roles, counts, owner) was
derived from the target, the item-scoped diff, and my own censuses
BEFORE reading `## Findings`; reconciliation follows it. Address
`dry/idfiled-f53/verify-1`; HEAD `dd0b6691` unmoved throughout.

### Own trace (pre-read)

Rule re-derived: entries filed under `id(owner)` beside a weakref to
the owner; reads answer only while the ref still points at the asker;
the ref's death callback removes the entry only while the filed ref is
still the dead one. At baseline bytes the lifecycle is spelled twice
in `django_strawberry_framework/utils/private_state.py`: the authority
half (`PrivateAuthority.settle` files, `settled` + `recall` verify,
`_settled` dict) and the membership half (`PrivateMembership.accept`
files, `recall` verifies, `_accepted` dict + `_Accepted` alias). The
two `forget` closures and the three read predicates are token-identical
modulo the owning dict.

- Sites + roles. Definitions pre-change: 2 (the two filing halves).
  Consumers: 7 stores in 5 files, all composing
  `settle`/`settled`/`recall`/`accept` by name —
  `schema.py` (`_SCHEMA_ENFORCEMENT`, `_SCHEMA_EXTENSIONS`),
  `extensions/operation_state.py` (`_OPERATION_CARRIERS`,
  `_PACKAGE_MANAGED`), `extensions/resource_policy.py`
  (`_EXPLICIT_POLICY`), `extensions/debug.py`
  (`_ACKNOWLEDGEMENT`), `optimizer/extension.py`
  (`_OPTIMIZER_CONFIGURATION`). Zero touches of
  `_settled`/`_accepted`/bare `_Accepted` outside the target; zero test
  imports of `private_state`. Oracles: seam rows in `tests/test_schema.py`,
  `tests/optimizer/test_extension.py`,
  `tests/extensions/test_operation_state.py`,
  `tests/test_resource_policy.py` plus the live
  `test_extension_isolation_api` + `test_resource_policy_api` modules.
  Projections: module/class docstrings, consumer rationale paragraphs,
  the kanban constants listing.
- Mechanism censuses (own instruments, current WT bytes). Bare `ref(`:
  exactly 4 — the driver's two-arg `ref(owner, forget)` plus three
  one-arg sites (`_accepted_member` ×2, `operation_state.py:673`
  lease payload); no `ReferenceType(` construction, no `callback=`
  keyword form, no `weakref.ref(` attribute form, no weak containers
  (the one `WeakKeyDictionary` hit is docstring prose). Builtin `id(`:
  79 lines; the only store-shaped code sites in the target are the
  driver's two (`_live_entry`, `file`); the nearest same-word neighbor
  is `utils/truth.py::IdentityMap` (id-keyed, STRONG `(key, value)`
  holds, explicit `pop`/`__delitem__` removal, no verify, no
  callback — opposite lifetime answer). `weakref|ReferenceType`: 11
  lines — target 6 (import, `_Entry`, `forget` annotation, box,
  `_Evidence`, one docstring line), lease import 1, slots/prose 4.
- Definition counts (own challenges). C1 key derivation 2→1; C2
  read-verify predicate 2→1 (three read predicates, two spellings);
  C3 death-callback guard 2→1; C4 file line 2→1; C5
  construction-record semantics 1→1 (authority-only control); C6
  evidence resolve 1→1 (membership-only control).
- Owner I would choose: a private generic driver in the same module
  both classes already live in — narrowest cohesive owner, no
  dependency reversal, payload opaque (`Generic[PayloadT]`), write
  policy and retention left per-class. That is `_IdFiledEntries`.

### Reconciliation (every difference)

- Census counts (record slips, cured here — no finding changes). (i)
  `weakref|ReferenceType`: W1's "13, target (8)" is the
  BASELINE/WT-before count (re-derived exactly: 13 via `git grep` at
  `cf52e8ba`); at WT-after it is 11 (target 6 — the consolidation
  removed the second `forget` annotation + the `_Accepted` alias
  spellings). The artifact's "all at WT bytes" overstates; the
  before→after is 13→11. (ii) Builtin `id(`: W1's "64" is
  irreproducible with a line-based grep — baseline-tracked 71,
  +9 untracked `truth.py` = 80 at WT-before, 79 at WT-after (target
  net −1: −3 code sites, +2 driver-docstring prose lines). Fully
  attributed, zero concurrent drift: all 11 W1 freshness blobs match
  current bytes and HEAD is unmoved. (iii) 11 code sites are not
  line-named in W1's R3/R5 rows but were triaged by body in this pass
  and are all out-of-contract: `utils/querysets.py` graph-walk
  `begin(id)` guards ×6 (call-scoped cycle/revisit bookkeeping — R5),
  the `_reconstructed_value` memo (call-scoped — R3),
  `optimizer/extension.py` freeze ids ×2 (function-local cycle set —
  R5), `rest_framework/inputs.py:258` mapping guard (recursion guard —
  R5), `utils/write_transaction.py:1030` container guard (walk guard —
  R5). The "no third filing site" conclusion additionally rests on the
  EXACT two-arg `ref(` census (2 pre → 1 post, re-derived) and the
  weakref-creation census (4 `ref(` sites, all homed; a verified store
  needs a weakref per entry, so no filing site can hide from it).
- C4 axis: W1 posits locking, I posit the file line; both count 2→1.
  No disagreement.
- Ledger numbers: W1's `## Implementation` +64/−30 is WT-vs-HEAD
  (includes the pre-existing concurrent hunk). Item-scoped
  baseline→WT is +61/−29 (numstat-verified). The ledger uses +61/−29.
- All other counts, roles, rejections, triggers, and the owner choice
  agree with no correction.

### Rulings on the Worker-0 check-points

- (a) C1–C4 2→1, C5–C6 1→1: CONFIRM (own recount agrees on all six).
- (b) R1 carve + both-directions merge-fails: CONFIRM — every settled
  payload re-verified primitives-or-worse (`_SchemaEnforcement`,
  `_AcceptedPolicy`, `_AcceptedDisclosure`,
  `_AcceptedOptimizerConfiguration`, `ContextVar`, `bool`) while the
  extension sequence reaches its schema back (`schema.py:517-524`);
  both merge directions fail as recorded; durable home at the owner
  (driver opacity clause + standing class docstrings).
- (c) Principle-8 equivalence: CONFIRM by inspection (bodies moved
  verbatim modulo the dict-attribute rename; identical short-circuit
  order, `TypeError` on unweakrefable owners with no partial filing,
  callback timing, overwrite-wins, `None` contracts incl. the
  None-payload/empty-accept edges, per-instance table isolation) AND
  execution — fresh differential scratch
  `docs/dry/temp-tests/idfiled-f53-verify-1/test_equivalence.py`
  (read-only): 34/34 probes pass with byte-identical output on WT
  bytes and on `cf52e8ba` baseline bytes.
- (d) Gate census exactness + mutants: CONFIRM by re-execution at my
  address (run `dry-20261002T033443-3bb8ac`, exit 0): entry 1 pinned
  (baseline 13/13; mutant fails exactly the 2 gate rows, 11 pass);
  entry 2 pinned (baseline 11/11; mutant fails 9 seam rows — box ×3,
  collectability ×3, slotted-not-root, tamper, read-out-once — 2 pass
  as explained); both restores byte-proved (blob `78d6692f`
  before/after, filecmp + sha256). Gate expectations re-derived
  exact: sole two-arg `ref(` is the driver's `file`; no `id(`/`ref(`
  under either store class. (`expect_failing: ["*"]` on entry 2
  means ≥1 attributable failure, so 9-fail/2-pass satisfies it; the
  record names all 9 rows.)
- (e) 72/72 coverage transfer: CONFIRM by re-execution (run
  `dry-20261002T033509-607967`): `private_state.py` 72/0/100% under
  `tests/test_schema.py` (132 passed). Zero new behavior rows owed.
- (f) Live 210/210: CONFIRM by re-execution (run
  `dry-20261002T033524-4599e8`, exit 0, 210 passed).
- (g) Concurrent-hunk preservation: CONFIRM — the
  `object.__setattr__` + comment lines are byte-identical context vs
  ITEM_BASELINE (the only HEAD-vs-baseline hunk on this file); never
  edited, reverted, or tidied.
- (h) +64/−30 vs +61/−29: RULED above — ledger uses +61/−29.
- (i) `tests/` tier for the census gates: CONFIRM — gates assert over
  package source (the target is the package itself); a structural
  property unreachable from any GraphQL query, so no live tier is
  owed. No behavior row lives in the gate file (stated in its
  docstring; behavior stays with the seam/live suites).
- (j) Orphan sweep: CONFIRM — zero `._settled`/`._accepted`/bare
  `_Accepted` in source (remaining matches are `_accepted_member`,
  `_accepted_globalid_type_names`, the three `_Accepted*` payload
  records, the `extensions_settled` field, and test-name noise).
  Tracked test-tree diff vs baseline is empty: no oracle rewritten.
- (k) Sharded/pg inapplicable: CONFIRM — pure in-memory
  dict/weakref, no database/alias/dialect decision; sync/async
  inapplicability likewise sound (no I/O, lock, or await point;
  called from sync constructors and both-colored read paths).

### Gates, pins, verdict inputs

- `uv run basedpyright`: 0 errors, 0 warnings, 0 notes.
- `uv run python scripts/check_any.py`: 128 allowed at 89 sites
  (unchanged; the diff adds no `Any`, `cast`, or suppression).
- `uv run python scripts/check_truthful_reads.py --check`: errors 0.
  mypy never run, never cited.
- `uv run ruff format --check` + `uv run ruff check` +
  `check_trailing_commas.py --check` on both touched paths: all
  clean.
- AGENTS.md prose: no process provenance in code; `path::Symbol`
  citations in the gate file; raw `path:NN` only in this per-cycle
  artifact (permitted); no feedback-mention; no CHANGELOG; no commit.
- Pins: HEAD `dd0b6691` unmoved; target WT-after `78d6692f`;
  all 11 W1 freshness blobs re-verified identical (consumers
  `7390c985`/`5f6f255d`/`2971618b`/`b26a7897`/`8e3fe7c1`,
  exclusions `711352b1`/`d1d272c5`/`197eea8e`/`b71db9e0`/`17dae905`).
- Item-scoped tracked diff is exactly the target (+61/−29) plus
  W0's plan notes; the gate file + artifact are new (untracked);
  scratch is untracked/ignored.
- `## Pending execution` correctly lists nothing: every proof above
  is execution-verified (re-run at this address where it matters)
  and the cell typing is judged inapplicable, not deferred.

No (Worker-2) defects. Verdict: verified.

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
