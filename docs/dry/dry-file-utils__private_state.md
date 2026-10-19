# DRY review: `utils/private_state.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits, zero plan edits.

## System trace

Target `django_strawberry_framework/utils/private_state.py`: HEAD blob
`08088b820ac20579e471915644a931953362fca8` (287 lines) is what this
artifact traces; worktree blob `b3c45503c3e2f648640b95ecad4d71a8315abb51`
(289 lines) carries exactly one hunk against HEAD (3+/1-, at
`PrivateMembership.accept`: HEAD `:247`
`owner.__dict__[self._attribute] = ...` becomes a two-line comment plus
`object.__setattr__(owner, self._attribute, ...)`). Content attribution:
`ITEM_BASELINE` bytes hash to `b3c45503...`, identical to the worktree, so
the hunk predates this dispatch; the plan's `## Owned changes` ledger
carries no row naming this file. The hunk is therefore
concurrent-external: described here, fingerprinted in Freshness, homed
nowhere, and no tracked path touched. HEAD is `0c0537e2`, unmoved since
dispatch. Dirt elsewhere is concurrent work, left alone; every dirty
connected file was diffed against HEAD and its hunks verified disjoint
from the cited lines (see Freshness).

What the target owns: the two tamper-proof configuration stores.
`PrivateAuthority` files a payload itself, strongly, under `id(owner)`,
answering nothing through any attribute on the owner — the home of
settled policies (primitives only). `PrivateMembership` files one weak
piece of evidence per member of an accepted sequence and answers reads
from that evidence, never from the owner attribute — the home of the
schema's accepted extension configuration (an arbitrary object graph,
whose strong hold must live on the owner for lifetime). A member no
weak reference can be taken of (a `__slots__` factory Strawberry still
runs) is answered through a `MethodType` box the interpreter refuses to
rewrite. Both stores key on `id()` (never hash/eq, which consumer code
may define), verify the filed weak reference on every read, and drop an
entry only while it is still the one its callback was filed under.

Consumer census (repo-wide grep for `PrivateAuthority` /
`PrivateMembership` / `private_state`, `.pyc` excluded): exactly five
production importers, all composing by name:

- [schema][schema] — `_SCHEMA_ENFORCEMENT`
  (`PrivateAuthority[_SchemaEnforcement]`) settled once in
  `DjangoSchema.__init__` behind a `settled()` guard, and
  `_SCHEMA_EXTENSIONS` (`PrivateMembership[Any]` under
  `"_django_extensions"`) accepted once from the `extensions` setter
  behind the `extensions_settled` flag; `extensions` property,
  `resource_policy` / `error_policy` copies, and `get_extensions`
  refusal all read through `recall`.
- [operation-state][operation-state] — `_OPERATION_CARRIERS`
  (`PrivateAuthority[ContextVar[Any]]`) settled in
  `_OperationBoundExtension.__init__` behind a `settled()` guard, and
  `_PACKAGE_MANAGED` (`PrivateAuthority[bool]`) settled idempotently;
  `_carrier` refuses a subclass that skipped the constructor.
- [resource-policy-ext][resource-policy-ext] — `_EXPLICIT_POLICY`
  (`PrivateAuthority[_AcceptedPolicy]`), settled in `__init__` after
  `super().__init__()`; `_policy` recalls and hands out a copy.
- [debug-ext][debug-ext] — `_ACKNOWLEDGEMENT`
  (`PrivateAuthority[_AcceptedDisclosure]`), settled in `__init__`
  after `super().__init__()`; `_acknowledged` recalls.
- [optimizer-extension][optimizer-extension] —
  `_OPTIMIZER_CONFIGURATION`
  (`PrivateAuthority[_AcceptedOptimizerConfiguration]`), settled in
  `__init__` after `super().__init__()`; `_configuration` recalls
  with a safe default for none.

Oracles: no test imports `private_state` directly (grep over `tests/`
and `examples/` empty). Behavior is pinned at the consumer seams:
[test-schema][test-schema]`::test_the_box_a_slotted_entry_is_answered_through_cannot_be_rebound`
(box immutability),
[test-optimizer-extension][test-optimizer-extension]`::test_a_resolver_cannot_rewrite_the_optimizer_configuration_for_a_later_request`
(authority tamper), plus the settle-path suites (`test_operation_state`,
resource-policy, schema) and two live `test_query` modules
(`test_extension_isolation_api`, `test_resource_policy_api`).
Projections: the 75-line module docstring plus both class docstrings,
each consumer's rationale paragraph, [spec-047][spec-047] (the design
record citing both classes), and the kanban tracked-path constants row
(mechanical listing, not a consumer).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Discharged by search. The target is
   flavor-neutral infrastructure with five consumers across the engine,
   the runner, two policy/disclosure extensions, and the optimizer; no
   flavor carries a local tamper-proof twin. The same-word candidates
   were traced and rejected: the operation lease (R-LEASE, converge),
   the boundary marks (R-MARKS, converge), and the policy-copy handout
   (R-COPY, fresh). No second unforgeable-store owner exists.
2. **Sync/async twins.** Inapplicable with reason: every method is pure
   in-memory dict/weakref work with no I/O, no lock, and no await
   point, deliberately uncolored — called from sync constructors and
   from both sync and async read paths (`get_extensions` resolves
   under either executor). Coloring the store would put an await
   point inside construction-time settlement.
3. **Derived rather than repeated knowledge.** Discharged, with one
   real find. "Which record belongs to this owner" is derived once
   per class as `id()` + weakref verification — but the filing half
   (key, `forget` callback, read-verify predicate) is spelled
   independently in EACH class (FAM, named below as an open family).
   Nothing outside the file re-derives owner identity by another
   means; the `__self__` box read is the one answer path for boxed
   members.
4. **Inverse / round-trip pairs.** Two pairs, one per class, each
   complete inside its class: `settle`/`recall` (authority) and
   `accept`/`recall` (membership). They are not cross-class halves:
   `settled()` is a construction record, not a read half, and the
   `forget` callbacks are lifetime cleanup, not inverses. No pair
   spans modules.
5. **Contracts restated in another medium.** Counted, all
   zero-definition: the module/class docstrings, five consumer
   rationale paragraphs, and [spec-047][spec-047] are projections;
   the test rows above are oracles asserting tamper/refusal behavior
   through public seams. A wording change moves one definition per
   rule (FAM's filing change moves two — that count is the family
   evidence) plus projections, never a second implementation.
6. **Enforcement by omission.** Settle-once obligation enumerated over
   all seven settle/accept sites — no gap, no defect. `schema.py:881`
   is guarded at `:866`; `schema.py:962` (the deliberate
   same-construction `extensions_settled` update) is guarded by the
   setter's flag refusal; [operation-state][operation-state]`:476`
   is guarded at `:474` and `:415` at `:414`; the remaining three
   (`optimizer-extension:960`, `resource-policy-ext:1427`,
   `debug-ext:700`) settle after `super().__init__()`, and all three
   classes extend `_OperationBoundExtension`, whose `__init__`
   raises on reconstruction before any subclass settle line runs.
   The single `accept` site (schema setter `:963`) is guarded by
   the same flag. The `settled()` docstring (owner prose) is the
   contract source, and every member enforces it.

### Enumeration

Instrument: every name in `ast.Module.body` at HEAD bytes (`08088b82`,
287 lines). Count: 16 top-level statements. Every member homed; no
sampling.

| # | Member | Home |
|---|---|---|
| 1 | Module docstring (authority-vs-lifetime split, `id()` filing rule) | FL3 (durable home of R-SPLIT's recorded split) |
| 2 | `from __future__ import annotations` | FL3 |
| 3 | `from collections.abc import Iterable` | FL3 |
| 4 | `from types import MethodType` | FL3 |
| 5 | `from typing import Any, Generic, NamedTuple, TypeVar` | FL3 |
| 6 | `from weakref import ReferenceType, ref` | FL3 |
| 7 | `__all__ = ("PrivateAuthority", "PrivateMembership")` | FL3 |
| 8 | `StateT = TypeVar("StateT")` (unexported; zero external importers by grep) | FL1 |
| 9 | `MemberT = TypeVar("MemberT")` (unexported; zero external importers by grep) | FL2 |
| 10 | `class PrivateAuthority`: docstring, `__init__`, `settled`, `settle`, `recall` | FL1 + FAM (filing halves) |
| 11 | `def _boxed_member` (the never-called bind function) | FL2 |
| 12 | `class _BoxedMember` (NamedTuple evidence + `box` slot) | FL2 |
| 13 | `_Evidence` (member evidence union alias) | FL2 |
| 14 | `_Accepted` (one owner's filed evidence alias) | FL2 |
| 15 | `def _accepted_member` (weakref-or-box per-member evidence) | FL2 |
| 16 | `class PrivateMembership`: docstring, `__init__`, `accept`, `recall` | FL2 + FAM (filing halves) |

16/16 homed: 3 file-local rows, 1 new family, 6 rejections below.

### Challenges

- **FL1, unforgeable authority.** (a) `recall` gains a third answer
  (e.g. distinguishing never-settled): 1 definition. (b) `settled()`
  stops answering for empty payloads: 1 definition; the seven guard
  sites are re-examined as consumers (listed, not counted). (c) A
  sixth authority kind (a new `PrivateAuthority[...]` at a new
  owner): 0 definitions move — it composes by name.
- **FL2, evidence membership.** (a) `recall` answers a partial
  sequence instead of `None` on dead evidence: 1 definition (here;
  the schema `:1063` refusal is the consumer). (b) Box mechanism
  change (`MethodType` → another immutable carrier): 1 definition
  (`_accepted_member` + `_BoxedMember` + recall's resolve arm move
  together as one mechanism). (c) `accept` stops replacing and
  merges: 1 definition.
- **FL3, module mechanics.** Export a `TypeVar`, admit a third name,
  or reword the contract prose: 1 definition each.
- **FAM, entry lifecycle.** (a) `id()`-reuse guard semantics change
  (verify differently, file under a different key): 2 definitions
  (both classes' read-verify predicates plus both `forget`
  callbacks). (b) Lock the entry dicts for threaded settlement: 2
  definitions. (c) `forget` stops checking `entry[0] is dead`: 2
  definitions. Consumers move zero — no consumer touches `_settled`
  / `_accepted`.
- **R-SPLIT.** Strong-hold change (payload retention, reachability):
  authority only. Evidence change (weak forms, box, resolve):
  membership only. The module docstring's lifetime paragraph is the
  recorded reason.
- **R-LEASE / R-MARKS / R-MANIFEST.** Standing triggers re-checked
  unfired on fresh bytes (see Findings); each posited change still
  moves one side only.
- **R-COPY.** Copy-on-handout change (deep vs shallow, which fields):
  [policies][policies] only. Filing change (who may read which
  record): here only. The schema `resource_policy` property composes
  both (recall, then copy), proving the seam.
- **R-FLAG.** Membership recall gains a never-accepted-vs-gone third
  answer: the flag MIGHT collapse — the one trigger that names a
  real future; today the two answers stay separate (see Findings).

## Findings

### FL1 `private-authority-unforgeable-store` (file-local)

- **Contract + variation.** One kind of settled authority for every
  object of one kind that carries it: `settle` files the payload
  itself, strongly, under `id(owner)` with a death callback;
  `recall` answers it only while the filed weakref still points at
  the asker, else `None` (never-settled, never lost-while-alive);
  `settled()` is the whole construction record, answering for
  payloads of every shape including deliberate absence. Payloads
  must point at nothing. Varies on payload type only
  (`Generic[StateT]`).
- **Sites + roles.** Definition: target `PrivateAuthority` + `StateT`
  (sole; the filing halves converge in FAM below). Consumers: the
  five `PrivateAuthority[...]` owners above (six stores: schema,
  two in operation-state, resource-policy, debug, optimizer). \
  Oracles: the tamper/refusal rows in System trace. Projections:
  class docstring, consumer rationale paragraphs, [spec-047][spec-047].
- **Challenges.** Above; counts 1 / 1 / 0.
- **Owner + lifetime.** Owner is the target (principle 7: narrowest
  module every legitimate consumer already imports; zero production
  imports of its own beyond stdlib). Principle 4: owner = this
  module's `_settled` dict; validity key = the filed weakref still
  resolving to the asking owner; publish point = the owner's
  constructor via `settle`; who may mutate = nobody after settle
  (re-settlement refused at every guarded call site); invalidation
  = owner death, via the callback, which removes only while the
  entry is still the one filed.
- **Migration.** None — file item, no consolidation; the rule is
  already single-owned and every site already composes it by name.
- **Distinct behavior.** No attribute on the owner answers with the
  payload (neither replaceable, deletable, nor reachable for
  in-place write); each caller raises its own typed reconstruction
  refusal so the message names the object held.
- **Behavioral proof.** Static-reviewed: zero-edit trace; the
  resolver-rewrite and reconstruction oracles reject a store that
  answers past tamper. No execution run (entry authorizes none for
  this trace; nothing was changed to prove).
- **Structural gate.** None proposed. Owner already single; a
  would-be gate ("every process-lived configuration is filed
  here") needs the folder item's enumerated configuration
  population plus negative controls, which this file item cannot
  justify. Not claimed as gate-only.
- **Coupling.** FAM (the filing halves shared with FL2).
- **Freshness.** Target HEAD `08088b820ac2` traced; worktree
  `b3c45503c3e2` differs by the one concurrent-external hunk at
  FL2's `accept` only — no FL1 line is touched by it. Consumers:
  [schema][schema] worktree `84f2d5aa51` vs HEAD `e6b52335b1`,
  [operation-state][operation-state] `d9ed9cc67f` vs `b2674a22d2`,
  [resource-policy-ext][resource-policy-ext] `0134d83a9a` vs
  `19e2309d06`, [debug-ext][debug-ext] `054e04df59` vs
  `bf25c14611`, [optimizer-extension][optimizer-extension]
  `39a8739c7e` vs `e0e53a8e10`; concurrent hunks verified disjoint
  from every cited line (zero added/removed lines mention settle,
  recall, authority, or membership except one `truth.describe`
  rename inside a schema refusal f-string, prose context only).
  Searched population: whole-package grep for `PrivateAuthority`
  / `PrivateMembership` / `private_state` (5 production importers
  + definition + kanban constants projection + spec prose,
  `.pyc`/sqlite excluded).

### FL2 `private-membership-evidence-sequence` (file-local)

- **Contract + variation.** One accepted sequence for every object of
  one kind that carries one: `accept` takes per-member evidence
  first (weakref where the layout admits one, else a `MethodType`
  box held by the owner), writes the strong hold to the owner's
  attribute, then files the evidence under `id(owner)`; `recall`
  resolves each member from its own evidence and answers `None`
  when none was accepted, the identity was reused, or any evidence
  stopped resolving. The attribute is the strong hold and nothing
  else — never read. Varies on member type only
  (`Generic[MemberT]`).
- **Sites + roles.** Definition: target `PrivateMembership` +
  `MemberT` + `_Evidence` + `_Accepted` + `_accepted_member` +
  `_BoxedMember` + `_boxed_member` (sole; filing halves converge
  in FAM). Consumers: exactly one, [schema][schema]`::_SCHEMA_EXTENSIONS`
  (accept at the `extensions` setter, recall at the property and
  `:1063`). Oracles: the box-rebind test plus the schema
  extension-settlement suites. Projections: class + box
  docstrings, the schema setter rationale, [spec-047][spec-047].
- **Challenges.** Above; counts 1 / 1 / 1.
- **Owner + lifetime.** Owner is the target (principle 7, same
  reasoning as FL1). Principle 4: owner = this module's `_accepted`
  dict for the evidence, the schema's attribute for the strong
  hold; validity key = every evidence resolving; publish point =
  the base constructor's one `extensions` write via `accept`; who
  may mutate = nothing may substitute (writes to the attribute are
  never answered with); invalidation = any evidence death, reported
  as `None` for the caller to refuse on — nothing substitutes for
  what is gone.
- **Migration / Distinct behavior / Coupling.** None, except FAM
  (filing halves) — see FL1. A write dropping the last strong hold
  ends the sequence by construction; an accepted class its defining
  module still names survives an attribute write.
- **Behavioral proof.** Static-reviewed (zero-edit trace). The
  concurrent-external worktree hunk touches `accept`'s hold-write
  line only; HEAD bytes traced, both fingerprinted, nothing edited.
- **Freshness.** Same target fingerprints as FL1; the hunk is at
  this finding's `accept` (HEAD `:247`, worktree comment +
  `object.__setattr__`), attributed concurrent-external by content
  (present in `ITEM_BASELINE`, absent from the ledger).

### FL3 `private-state-module-mechanics` (file-local)

- **Contract + variation.** Two-name manifest (`__all__` admits only
  the two stores), unexported `StateT` / `MemberT`, annotation-only
  stdlib imports, and the module docstring as the contract's prose
  projection — including the authority-vs-lifetime split that
  durably homes R-SPLIT. No variation axis; the manifest is this
  module's surface by construction.
- **Sites + roles.** Definition: target members 1–7. No consumers of
  the `TypeVar`s (grep: zero external importers). No oracles; the
  manifest is stated, not behavior.
- **Challenges.** Above; count 1 per change.
- **Owner + lifetime.** Owner is the target; no stored derivation.
- **Migration / Distinct behavior / Coupling.** None; see FL1. The
  split paragraph stays here per principle 10 (grammar at the
  owner, already present — verified against both bodies, see
  R-SPLIT).
- **Behavioral proof.** Static-reviewed (zero-edit trace).
- **Freshness.** Same target fingerprints as FL1.

### FAM `id-filed-entry-lifecycle` (new family, open)

One rule with two independently maintained spellings: entries filed
under `id(owner)` beside a weakref to the owner; every read
verifying the weakref still points at the asker; the death callback
removing the entry only while the filed ref is still the dead one
(the key may already name an id-reusing successor). Authority
spells it at `:124-125` (verify), `:131-134` (`forget`),
`:146-147` (verify); membership at `:250-255` (`forget`),
`:274-276` (verify). The read-verify predicate alone has three
spellings (`is owner and`, `None if ... is not`, early-return).
Challenge counts are 2 / 2 / 2 (see Challenges); consumers touch
neither dict, so a consolidation would move the two classes only.
Disproof attempted and failed for the FILING half: payload handling
genuinely differs (strong hold vs evidence resolution — that split
is R-SPLIT, rejected), but the filing/verify/forget lifecycle is
one contract with one reason to change. Holding item: Family
`id-filed-entry-lifecycle`, which chooses the owner (a shared
entry-lifecycle driver the two classes compose, or a rejection with
trigger at the owner). Not consolidated here: no consolidation
inside a file item.

### R-SPLIT `private-authority-vs-membership-merge` (rejected, fresh)

Considered: one store for both — file the extension sequence's
payload the way a policy is filed, or answer a policy through
evidence. Rejected on the module docstring's lifetime paragraph,
verified against both bodies: a policy is primitives, so holding it
strongly retains nothing but the policy; an extension configuration
reaches its schema back (bound-method factories, execution
contexts), so holding it strongly roots the schema, its last
context, and that request's variables for the life of the process —
and a weak KEY does not help when the chain runs through the value.
Merging asks one object to hold strongly and weakly at once.
Reconsideration trigger: a settled payload that must point at its
owner, or evidence that must survive its member's collection.

### R-LEASE `private-authority-vs-operation-lease` (rejected, CONVERGE)

CONVERGE with the verified `operation-lease-vs-private-authority`
rejection (File [operation-lease][operation-lease]) on fresh
evidence. Trigger re-checked unfired: [operation-state][operation-state]
still files the carrier variable behind `PrivateAuthority` (`:476`,
guarded `:474`) while binding state behind `OperationLease`, on
bytes whose concurrent drift is verified disjoint from both lines.
Forgery resistance vs revocation is still load-bearing. Durable
home: that artifact plus this file's module docstring. Standing
trigger stands: a store that must be both unforgeable-by-identity
and revocable-by-scope in one object.

### R-MARKS `private-authority-vs-boundary-marks` (rejected, CONVERGE)

CONVERGE with the verified `Attribute marks vs PrivateAuthority`
rejection (File `_boundary_ordering.py`) on fresh evidence. Trigger
re-checked unfired: the boundary file is CLEAN at `197eea8e01`, and
the marks are still cooperative signals that must stay readable and
writable by every party (deployment `functools.wraps` copies, the
resolver-held callback). Opposite threat models, unchanged. Durable
home: that artifact plus the boundary owner's prose. Standing
trigger stands: a mark whose readers must be protected from
consumer writes (a mark that becomes a policy).

### R-MANIFEST `private-state-manifest-vs-sibling-manifests` (rejected, CONVERGE)

CONVERGE with the verified `operation-lease-manifest-vs-sibling-manifests`
rejection (File [operation-lease][operation-lease]), whose population
names this file, on fresh evidence. This module's `__all__` admits
only its two stores and both `TypeVar`s have zero external
importers (fresh grep over package + tests + examples); a manifest
change here still moves this module alone. Standing trigger
re-checked unfired: no lint/gate treats the sibling spellings
identically.

### R-COPY `authority-recall-vs-policy-copy` (rejected, fresh)

[policies][policies]`::copy_policy` duplicates a policy on handout;
`PrivateAuthority.recall` answers the filed object itself. Same
read path, disjoint contracts: the authority owns unforgeable
FILING (which record this owner reads), the copy owns aliasing
defense (the reader must not mutate shared state — a frozen
dataclass still admits `__dict__` writes). The schema
`resource_policy` property composes both (recall, then copy),
proving the seam load-bearing; folding the copy into `recall`
would couple the identity store to every payload's copy semantics
(and `_OPERATION_CARRIERS` files a `ContextVar`, which has none).
Reconsideration trigger: a filed payload whose handout must be the
stored object itself, mutated through the recall.

### R-FLAG `settle-record-vs-extensions-settled-flag` (rejected, fresh)

`PrivateAuthority.settled()` answers "constructed" for the
authority, while [schema][schema]`::_SchemaEnforcement.extensions_settled`
answers it for the membership — two construction records because
membership `recall` returning `None` is ambiguous (never accepted
vs accepted-but-gone), while authority `recall` returning `None`
means never settled by construction. The flag is filed INSIDE the
authority record so deleting the accepted entries cannot make a
schema look unconstructed and admit a replacement list. Per-store
record vs cross-store disambiguator, not two spellings of one
check. Reconsideration trigger: membership recall gains a third
answer distinguishing never-accepted from gone, collapsing the
need for the flag.

## Defects

None. No contract-row break found; nothing routes to the maintainer. The axis-6
settle-once census (all seven sites guarded, three via the
`_OperationBoundExtension.__init__` carrier refusal) closes the one
enforcement question this file's contract raises. The worktree
`accept` hunk is concurrent-external work in flight, not a defect
in the traced HEAD bytes, and is not homed here.

## Judgment

Zero-edit file item, complete. HEAD bytes traced at `08088b82` with
the one concurrent-external hunk attributed by content
(`ITEM_BASELINE` == worktree, no ledger row) and both states
fingerprinted; 16/16 enumerated statements homed (3 file-local, 1
new family, 6 rejections: 3 converges on verified verdicts with
fresh trigger checks, 3 fresh with triggers); no defects; no
pending execution. The stores are already single-owned and every
production site already composes them by name; the one genuine
second spelling (the entry lifecycle) is named as an open family
for its holding item.

## Index rows for Worker-0

| `private-authority-unforgeable-store` | `django_strawberry_framework/utils/private_state.py::PrivateAuthority` | `django_strawberry_framework/utils/private_state.py` | File `utils/private_state.py` | file-local |
| `private-membership-evidence-sequence` | `django_strawberry_framework/utils/private_state.py::PrivateMembership` | `django_strawberry_framework/utils/private_state.py` | File `utils/private_state.py` | file-local |
| `private-state-module-mechanics` | `django_strawberry_framework/utils/private_state.py` (`__all__`, `StateT` / `MemberT`, imports, contract docstring) | `django_strawberry_framework/utils/private_state.py` | File `utils/private_state.py` | file-local |
| `id-filed-entry-lifecycle` | TBD by family item (candidates: a shared entry-lifecycle driver in `django_strawberry_framework/utils/private_state.py` composed by both classes) | `django_strawberry_framework/utils/private_state.py` | Family `id-filed-entry-lifecycle` | open |
| `private-authority-vs-membership-merge` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/private_state.py` | File `utils/private_state.py` | rejected |
| `private-authority-vs-operation-lease` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; CONVERGE with verified `operation-lease-vs-private-authority` on fresh evidence, trigger re-checked unfired) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/utils/operation_lease.py` | File `utils/private_state.py` | rejected |
| `private-authority-vs-boundary-marks` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; CONVERGE with verified Attribute-marks-vs-`PrivateAuthority` on fresh evidence, trigger re-checked unfired) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/_boundary_ordering.py` | File `utils/private_state.py` | rejected |
| `private-state-manifest-vs-sibling-manifests` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; CONVERGE with verified `operation-lease-manifest-vs-sibling-manifests` on fresh evidence, trigger re-checked unfired) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/utils/operation_lease.py`, `django_strawberry_framework/utils/policies.py` | File `utils/private_state.py` | rejected |
| `authority-recall-vs-policy-copy` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/utils/policies.py` | File `utils/private_state.py` | rejected |
| `settle-record-vs-extensions-settled-flag` | `django_strawberry_framework/utils/private_state.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/private_state.py`, `django_strawberry_framework/schema.py` | File `utils/private_state.py` | rejected |

## Independent verification (Worker-2)

Traced expectation-first: required docs, full target read at both
states, own AST enumeration over HEAD bytes, whole-package
`PrivateAuthority` / `PrivateMembership` / `private_state` census,
consumer call-site reads, the three converged-from artifacts, and the
plan ledger — all before this artifact's `## Findings`. HEAD
`0c0537e2` unmoved at finish; window diff vs `ITEM_BASELINE` names
only the plan, the concurrent review file, and this untracked
artifact.

My trace. Enumeration instrument: `ast.Module.body` over HEAD bytes
(`08088b82`, 287 lines) — 16 statements (docstring, 5 imports,
`__all__`, 2 TypeVars, 2 classes, 2 helpers, 2 aliases), matching W1's
table member by member with no sampling. Hunk attribution:
`ITEM_BASELINE` bytes hash to `b3c45503`, identical to the worktree,
and the `## Owned changes` ledger carries zero rows naming this file
— the `accept` hold-write hunk predates the item and is
concurrent-external, confirmed by content, not by status. Consumers:
exactly five production importers, all composing `settle` /
`settled` / `recall` / `accept` by name; no consumer touches either
entry dict. The `id()`-filing + read-verify + `forget`-guard
lifecycle is spelled in both classes and nowhere else in the package
(the only other `ref(` site composes a weakref as a lease payload,
not a second store) — one mechanism, two spellings, same reasons to
change, so a holding family is the right route and no consolidation
is owed here. Reconciliation: every W1 home, count, trigger, and
fingerprint below agrees with my trace except O1, which touches no
judgment.

(1) Enumeration: 16/16 stands — order, members, and homes (FL3 =
1–7, FL1 = StateT + authority, FL2 = MemberT + membership machinery,
FAM = filing halves) all confirmed on HEAD bytes. (2) Hunk
attribution stands per the paragraph above. (3) FAM
`id-filed-entry-lifecycle`: ENDORSED as an open family — the filing
contract (identity key, verify-on-read, remove-only-while-filed
callback) is genuinely one rule; the 2/2/2 challenge counts hold
because each posited lifecycle change moves both classes and zero
consumers; R-SPLIT correctly carves the payload half out. The family
item owns the driver-vs-rejection decision. (4) Rejections, each
probed on fresh bytes: R-SPLIT stands (lifetime paragraph verified
against both bodies; trigger names a real future). R-LEASE CONVERGE
stands — operation-state still composes carrier-behind-authority with
state-behind-lease, no combined store exists, trigger unfired.
R-MARKS CONVERGE stands — boundary file clean at `197eea8e01`, marks
still cooperative and wraps-copied, trigger unfired. R-MANIFEST
CONVERGE stands — zero external TypeVar importers by fresh
import-grep, no `__all__`-unifying gate in `scripts/`, trigger
unfired. R-COPY stands — `copy_policy` exists, the schema
`resource_policy` property composes recall-then-copy with the seam
documented at the owner, and `_OPERATION_CARRIERS` files a
`ContextVar` with no copy semantics; trigger sound. R-FLAG stands —
flag filed inside the authority record with the anti-replacement
rationale at the site, setter refusal and `:1063` disambiguation both
read; trigger (a third recall answer) is the honest collapse
condition. (5) Zero-defect call stands: the axis-6 settle-once census
closes — schema `:881` guarded at `:866`, `:962`/`:963` behind the
setter flag refusal, operation-state `:476`/`:415` guarded at
`:474`/`:414`, and the remaining three settles run after
`super().__init__()` in verified `_OperationBoundExtension`
subclasses whose base `__init__` raises on reconstruction. Consumer
drift disjointness re-verified: across all five consumer diffs the
only settle/recall/authority/membership/accept-adjacent delta is the
one `truth.describe` rename in a schema refusal f-string. Both named
oracle tests exist at the cited modules. Matrix: all six axes
discharged against the real surface; the axis-2 inapplicability
reason (uncolored construction-time settlement, await-hostile) is
sound. No `## Defects` entry: nothing found. No pending execution.

O1 (Worker-2, record accuracy, verdict-neutral): FAM cites the
membership read-verify as `:274-276`, which is the worktree
numbering; on the traced HEAD bytes it is `:272-274` (the `+2` worktree
shift starts at the `accept` hunk). Every other cited span is
HEAD-correct, the predicate and its three spellings are as described,
and no count or home depends on the number — noted for Worker-0, no
resubmission owed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[operation-lease]: dry-file-utils__operation_lease.md

<!-- docs/SPECS/ -->
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[debug-ext]: ../../django_strawberry_framework/extensions/debug.py
[operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[policies]: ../../django_strawberry_framework/utils/policies.py
[resource-policy-ext]: ../../django_strawberry_framework/extensions/resource_policy.py
[schema]: ../../django_strawberry_framework/schema.py

<!-- tests/ -->
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-schema]: ../../tests/test_schema.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
