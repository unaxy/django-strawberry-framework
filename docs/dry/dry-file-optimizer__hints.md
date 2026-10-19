# DRY review: `optimizer/hints.py`

Status: verified
Run: 0.0.15 2026-09-22-5

## System trace

Target `django_strawberry_framework/optimizer/hints.py` owns the
`Meta.optimizer_hints` VALUE contract: the `OptimizerHint` record (five
fields, frozen), the `SKIP` sentinel, the four factory classmethods, and
construction-time rejection (`__post_init__` conflict matrix plus the two
`_require_*` guards) that makes every invalid shape raise
`ConfigurationError` at type-creation time. It also owns the single
skip-read predicate `hint_is_skip` and consumes two neighboring owners by
name: `nested_fetch.py::resolve_strategy` (+ the `StrategySelection`
alias) for strategy validation, and `exceptions.py::_safe_type_name` for
rejection labels.

Trace subject is HEAD bytes only (`da46ef89`, 271 lines). The worktree
file (`8064af14`) carries concurrent hunt dirt (a guarded `isinstance`
arm plus docstring in `_require_prefetch`) that is NOT traced, NOT
edited, and NOT worked around; both fingerprints are recorded under
Freshness in every finding.

Sites and roles, HEAD bytes:

- Definition `optimizer/hints.py::OptimizerHint` (+ `_require_prefetch`,
  `_require_strategy`, post-body `SKIP` assignment): the value contract.
- Definition `optimizer/hints.py::hint_is_skip`: the skip read. Sole
  production callers, each composing by name: `optimizer/walker.py`
  (`_apply_hint` entry), `optimizer/nested_planner.py` (relation-level
  gate, before any strategy read), `optimizer/extension.py`
  (`check_schema` never-raises audit). Package-wide census: no direct
  `.skip` attribute read and no `is SKIP` check exists outside the
  target; every other `SKIP` mention is prose.
- Shape consumers composing by name: `optimizer/walker.py::_apply_hint`
  (sole reader of `force_select` / `force_prefetch` / `prefetch_obj`;
  census-verified), `optimizer/nested_planner.py::_select_nested_strategy`
  (sole reader of `nested_strategy`, via `getattr`), 
  `types/base.py::_validate_optimizer_hints` (shape-agnostic
  `isinstance(v, OptimizerHint)` value gate; the container half —
  mapping shape, key checks, field-surface checks — is `types/base.py`'s
  own rule, held for File `types/base.py`), `types/definition.py`
  (`optimizer_hints: dict[str, OptimizerHint]` annotation), the package
  root (`OptimizerHint` re-export), and example schemas (glossary,
  kanban, library — including a non-sentinel `OptimizerHint(skip=True)`
  in the library schema, which is why the predicate reads the attribute
  and not just the identity).
- Strategy consumers composing by name: every `resolve_strategy` caller
  (`optimizer/extension.py` twice for the extension-wide default,
  `_require_strategy`, `nested_planner.py::_select_nested_strategy`)
  and every `StrategySelection` annotation site (the three consumer
  seams the alias comment names plus the internal `_require_strategy`
  return) name the single `optimizer/nested_fetch.py` definition.
- Oracles: `tests/optimizer/test_hints.py` at HEAD (414 lines, 9
  classes: sentinel, three force factories, strategy factory incl.
  hostile-selection rows, frozen immutability, equality, invalid-state
  rejection, skip predicate) spells every expectation independently
  (literal message fragments, inline hostile classes); it imports the
  API to execute it, never reads an owner table. Live pins:
  `test_library_api.py` (skip + prefetch observable over HTTP, incl.
  the non-sentinel skip) and `test_optimizer_auto_api.py` (per-field
  `strategy(...)` overrides over HTTP).
- Projections: the target module/class/helper docstrings, the GLOSSARY
  `OptimizerHint` and `Meta.optimizer_hints` anchors (shipped `0.0.3`),
  the `docs/README.md` strategy-override paragraph, TREE module lines,
  and the consumer-side docstrings that restate the composition
  (`walker.py::_apply_hint` priority order, `nested_planner.py`
  build-time-validation note, `nested_fetch.py` alias comment).

Established inputs (verified rows, used as triggers to check, never
re-litigated): File `_request_body.py` J2 (shared exact-type gate
rejected), File `optimizer/selections.py` R-6 (GraphQL `@skip` vs hint
`skip` rejected, home this file), File `utils/policies.py` R3
(per-subject rejection grammars rejected). `optimizer/walker.py`
findings are prior evidence only (REOPENED): the validation-vs-dispatch
split is re-verified fresh below as R6, not inherited.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. Sibling Meta-value
   surfaces carry no parallel typed-wrapper rule: `ErrorPolicy` /
   `ResourcePolicy` are deployment dataclasses resolved through the
   `utils/policies.py` ladder (a different contract: precedence +
   canonical copies, not per-field directives + conflict matrix);
   `NestedConnectionStrategy` / `OptimizationPlan` / `FieldMeta` are
   fetch backends, plan records, and field descriptors, not consumer
   Meta values. The exact-bool gate is one instance of the rejected
   shared exact-type population (R2, trigger checked, not met). The
   `SKIP` deferred-assignment sentinel is unique package-wide (R8).
   No mirrored second definition.
2. Sync/async twins — NO SUCH SURFACE. The target holds zero `async
   def`, zero `await`, zero executor import; it is construction-time
   validation plus in-memory predicate reads. There is no colored twin
   to drift.
3. Derived rather than repeated knowledge — SEARCHED. Every derivation
   composes its owner by name: `__post_init__` reuses `_require_prefetch`
   / `_require_strategy` (never re-spells either invariant); the walker
   dispatches validated shapes (R6); the planner re-resolves an
   already-validated name through the same `resolve_strategy` (R7);
   `types/base.py` gates values by `isinstance`, never by re-listing
   shapes; rejection labels render through `exceptions.py::_safe_type_name`.
   The dual skip read (identity OR attribute) is one predicate, not two
   derivations: direct `OptimizerHint(skip=True)` construction is
   documented and shipped in the example, so identity alone would miss
   real skips. No reconstructed fact found a second spelling.
4. Inverse / round-trip pairs — NO SUCH SURFACE. Factories construct,
   dispatchers read; nothing encodes for a later decode, packs for a
   later unpack, or parses back a rendered form. The `SKIP` assignment
   plus identity check is single-module sentinel mechanics, not a
   grammar with two halves.
5. Contracts restated in another medium — SEARCHED. Every medium a
   change moves is classified in System trace: oracles (9 package
   classes + 2 live suites, all independent spellings) and projections
   (target docstrings, 2 GLOSSARY anchors, README paragraph, TREE
   lines, 3 consumer-side composition notes). The bilateral
   import-rationale prose (target comment + alias comment) is one
   edge decision projected twice, one definition (R4).
6. Enforcement by omission — SEARCHED. Family enumerated, each member
   enforced somewhere exactly once: `force_select`, `force_prefetch`,
   `prefetch_obj` (post-init arms + walker arms); `skip` (post-init arm
   + all three `hint_is_skip` consumers); `nested_strategy` (post-init
   arm + `_require_strategy` + planner read on connection paths only,
   the non-connection silence being factory-docstring-stated);
   `SKIP` honored at all three skip readers (census: no bypassing
   read); four factories each pin one shape with no-other-flags
   oracles; the empty form is allowed and falls through to cardinality
   dispatch by stated walker contract. No member lacks its guard; no
   gap found, no defect filed on this axis.

### Enumeration

Instrument: every name in `ast.Module.body` of the HEAD bytes
(`da46ef89`, 271 lines), read via `git show HEAD:` plus an AST dump.
Count: 12 nodes. Every member lands below; nothing is unassigned.

| # | Member | Home |
|---|---|---|
| 0 | Module docstring (consumer-surface contract prose) | Projection at the owner; supports F1/F2/F3 (prose, not a definition) |
| 1-4 | `__future__`, `dataclasses`, `typing`, `django.db.models` imports | Mechanics L1; no rule |
| 5 | `..exceptions` import (`ConfigurationError`, `_safe_type_name`) | Consumer link to `exceptions.py`-owned rules; no rule here (L1) |
| 6 | `.nested_fetch` import (`StrategySelection`, `resolve_strategy`) | F3 (consumer); runtime direction pinned by oracle (L1 mechanics) |
| 7 | `_require_prefetch` | F1 (`optimizer-hint-shape`) |
| 8 | `_require_strategy` | F1 (None arm + message) + F3 (delegates to `resolve_strategy`) |
| 9 | `OptimizerHint` (5 fields, `SKIP` declaration, `__post_init__`, `strategy`, `select_related`, `prefetch_related`, `prefetch`) | F1 (`optimizer-hint-shape`) |
| 10 | `hint_is_skip` | F2 (`optimizer-hint-skip-predicate`) |
| 11 | `OptimizerHint.SKIP = OptimizerHint(skip=True)` post-body assignment | F1 (sentinel half of the shape) |

### Challenges

Each rule, changes posited on its variation axes, authoritative
definitions counted (consumers, oracles, projections listed, never
counted):

- Shape record: posit a sixth field / fifth directive — 1 definition
  (`OptimizerHint` + its factory + post-init arms move as one).
  Consumers extend without restating (walker arm, planner read).
- Conflict matrix: posit flipping one verdict (e.g. allow
  `skip` + `force_prefetch`) — 1 definition (the post-init arm).
  Posit admitting truthy non-bools — 1 definition (the bool gate).
  Pair-completeness verified: all six pairs among `skip`,
  `force_select`, `force_prefetch`, `prefetch_obj`, `nested_strategy`
  carry an arm except the two intentional allowances (`force_prefetch`
  + `nested_strategy`, and the empty form), each stated in its
  docstring with its reason.
- Factory None-guards: posit a factory that must accept `None` — 1
  definition per invariant (`_require_prefetch`, `_require_strategy`
  each own exactly one invariant for two call sites: factory +
  post-init). The two helpers share a pattern, not a contract (R1).
- Skip predicate: posit raising on `None` instead of `False` — 1
  definition (`hint_is_skip`); the three consumers pass values
  through and move zero. Posit a fourth skip signal — 1 definition.
- Strategy selection: posit a fourth registered name — 1 definition
  (`optimizer/nested_fetch.py` registry + `resolve_strategy`); all
  four call sites and all annotation sites move zero (names pass
  through). Posit changing `None`-means-setting — 1 definition
  (`resolve_strategy`); the `_require_strategy` explicit-`None`
  rejection is the deliberate counter-rule, recorded in F1.
- Sentinel mechanics: posit a second member sentinel — 1 place (the
  post-body assignment site); the `ClassVar` declaration shape is
  forced by dataclass semantics (R8).

No read-only probe was needed: every claim above is decided statically
against HEAD bytes (AST census, package-wide reader censuses, body
reads), so no `docs/dry/temp-tests/dry-file-optimizer__hints/` scope
was created and no pytest ran.

## Findings

### F1 — Meta.optimizer_hints value contract (NEW family `optimizer-hint-shape`, open)

Contract: one frozen record with five fields (`force_select`,
`force_prefetch`, `prefetch_obj`, `skip`, `nested_strategy`), one
sentinel (`SKIP`), four factories each pinning exactly one shape, and
construction-time rejection of every other shape: non-bool flags,
`skip` combined with anything, `force_select` + `force_prefetch`,
`prefetch_obj` of non-`Prefetch` type or combined with force flags,
`nested_strategy` combined with `skip` / `prefetch_obj` /
`force_select` or failing `resolve_strategy`. The two deliberate
allowances are the empty no-op form (walker falls through to
cardinality dispatch) and `force_prefetch` + `nested_strategy`
(redundant-but-harmless, stated). The factory-side `_require_*` checks
exist because `None` is each field's legitimate default: without them
`prefetch(None)` / `strategy(None)` would collapse into the no-op hint.

Sites and roles: definition `optimizer/hints.py::OptimizerHint` (+
`_require_prefetch`, `_require_strategy`, post-body `SKIP` assignment;
HEAD `da46ef89`). Consumers composing by name: `optimizer/walker.py`
(dispatch + plan-time refusals), `optimizer/nested_planner.py`
(strategy read), `types/base.py` (shape-agnostic value gate; container
validation held for File `types/base.py`), `types/definition.py`
(annotation), the package root (re-export), example schemas. Oracles:
`tests/optimizer/test_hints.py` minus the predicate class, plus both
live suites. Projections: target docstrings, GLOSSARY anchors, README
paragraph.

Challenges: all shape rows in `### Challenges` count 1 definition;
no second shape, sentinel, factory, or conflict arm exists. Owner by
responsibility: `OptimizerHint` — the narrowest module every consumer
already imports downward with no reversal (the walker-side reason the
class lives in the optimizer subpackage is stated in the module
docstring). The family item audits the contract whole (shape,
sentinel, factories, matrix, both `_require_*` helpers, every
consumer's read discipline) and decides the structural gate; this file
item makes no edit.

Freshness: target HEAD
`da46ef891ccd8a2d42c8ac7519d9f42c9cb73b74` (worktree
`8064af14930636d6b12a538a996603ccadfdb420`, concurrent hunt dirt in
`_require_prefetch` + docstring — NOT traced);
`optimizer/walker.py` HEAD `e8d800052cc87ca77070290c4c2f396061259b81`,
`optimizer/nested_planner.py` HEAD
`b4dfd4a6f61044c6b5dca6ed9fa07d74f52d846d`, `types/base.py` HEAD
`91c587477ff8257e80dbb9a9c79859f34c5b4c7e`, `types/definition.py`
HEAD `fa6c4d330e72d7dceb5f2af7f56e460c6cf72383`,
`django_strawberry_framework/__init__.py` HEAD
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
`tests/optimizer/test_hints.py` HEAD
`d3e413bdc0e93d791399c023a442f6701416b5a1` (worktree `90253a19`,
hunt dirt +24, NOT traced), `test_library_api.py` HEAD `1f107fff`,
`test_optimizer_auto_api.py` HEAD `ca9fea06`, GLOSSARY HEAD
`d3ef357c` (anchors read, not line-pinned), `docs/README.md` HEAD
`c32da236`.

### F2 — Hint skip predicate (NEW family `optimizer-hint-skip-predicate`, open)

Contract: one three-arm read — `None` (no hint configured) is `False`,
the `SKIP` identity is `True`, anything else reads `.skip` through a
guarded `getattr` coerced with `bool`, and any `BaseException` from a
hostile shape is `False` so the schema audit keeps its never-raises
contract. The identity arm is the fast path for the common sentinel;
the attribute arm is load-bearing because direct
`OptimizerHint(skip=True)` construction is documented and ships in the
example (equal to `SKIP`, not identical).

Sites and roles: definition `optimizer/hints.py::hint_is_skip` (HEAD
`da46ef89`); consumers `optimizer/walker.py::_apply_hint`,
`optimizer/nested_planner.py` relation gate (returns before any
strategy read), `optimizer/extension.py::check_schema`; oracle
`tests/optimizer/test_hints.py::TestSkipPredicate` (hostile-attribute
/ hostile-bool rows spell `False` independently); projection the
helper docstring. No direct `.skip` read and no second `is SKIP`
check exist package-wide (census).

Challenges: both predicate rows count 1 definition. Owner:
`hint_is_skip` — the narrowest module all three consumers already
import. The family item verifies the consumer census holds and owns
the gate (a bypassing skip read is the plausible divergence); this
file item makes no edit.

Freshness: target HEAD `da46ef89` (worktree `8064af14` hunt dirt, NOT
traced); `optimizer/walker.py` `e8d80005`,
`optimizer/nested_planner.py` `b4dfd4a6`, `optimizer/extension.py`
HEAD `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a`,
`tests/optimizer/test_hints.py` HEAD `d3e413bd` (worktree `90253a19`
dirt NOT traced).

### F3 — Nested-connection strategy selection (NEW family `nested-connection-strategy-selection`, open)

Contract candidate: one alias (`StrategySelection = str |
NestedConnectionStrategy`) plus one resolver
(`optimizer/nested_fetch.py::resolve_strategy`) accepting a registered
name, `"auto"`, or a strategy instance, with `None` reading the
`NESTED_CONNECTION_STRATEGY` setting; hostile dunders degrade to the
typed `ConfigurationError` via base-`str`-slot reads, a linear
registry scan (no hash dispatch), an absorbing `plan` read, and a
guarded message renderer. Hints.py is pure consumer here: the
`nested_strategy` field type, the `strategy()` factory parameter, and
the `_require_strategy` delegation all name the single definition;
the `_require_strategy` explicit-`None` rejection is hints.py's own
counter-rule (F1), needed exactly because the owner treats `None` as
valid.

Sites and roles: definition `optimizer/nested_fetch.py`
(`StrategySelection`, `resolve_strategy`; HEAD `4d8d37a7`);
consumers `optimizer/hints.py` (field, factory, `_require_strategy`),
`optimizer/extension.py` (constructor kwarg annotation + two resolve
calls), `optimizer/nested_planner.py::_select_nested_strategy`,
`conf.py::nested_connection_strategy_setting` (the setting read;
HEAD `c6ad46aa`); oracles the strategy + hostile-selection test
classes and the live override suite; projections the alias comment,
the target import comment, GLOSSARY strategy prose, the README
paragraph.

Challenges: both strategy rows count 1 definition; no second
registry, resolver, or alias exists. Owner: `resolve_strategy` beside
the alias and the strategy protocol. The family item (or the
`optimizer/nested_fetch.py` file item first, in queue order) sweeps
the rule whole; this file item records the consumer side and makes no
edit.

Freshness: target HEAD `da46ef89` (worktree `8064af14` hunt dirt, NOT
traced); `optimizer/nested_fetch.py` HEAD
`4d8d37a7f52cf94d2916f17db3a8a21393e28d57`,
`optimizer/extension.py` `49667a93`, `optimizer/nested_planner.py`
`b4dfd4a6`, `conf.py` HEAD
`c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`,
`tests/optimizer/test_hints.py` HEAD `d3e413bd` (worktree dirt NOT
traced), `test_optimizer_auto_api.py` HEAD `ca9fea06`.

### L1 — Module mechanics (file-local)

Frozen dataclass form, the `ClassVar[OptimizerHint]` declaration, the
post-body `SKIP` assignment with its `type: ignore[misc]` (mypy
rebind note), the `Prefetch`-at-runtime import (the `isinstance`
check needs it), the `StrategySelection`/`resolve_strategy`
runtime import direction (pinned by the `get_type_hints` regression
oracle), and the `ConfigurationError` / `_safe_type_name` consumer
link to `exceptions.py` (one of 20+ composing consumers; owner
`exceptions.py`, HEAD `e06b0b7f`). Single definition each, single
module, no second site. Challenge: posit a second frozen hint record
or a second runtime-import-direction rule — none exists
(package-wide census).

Freshness: target HEAD `da46ef89`; `exceptions.py` HEAD
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`.

### R1 — The two `_require_*` factory guards (rejected)

`_require_prefetch` (isinstance-type invariant) and `_require_strategy`
(explicit-`None` rejection plus delegated resolution) share the
factory-before-construction pattern and nothing else: `None` is
invalid at both factories but for opposite downstream reasons (the
dataclass default vs the delegated `None`-means-setting), and the
validation itself is a local type test in one and a named-owner
resolution in the other. Contract difference: Prefetch-type invariant
vs strategy-selection invariant. Reconsideration trigger: a third
factory guard appears with the same factory-plus-post-init call shape
(the trio, not the pair, would be one rule), or both helpers converge
on one validation mechanism.

### R2 — Exact-bool gate vs the shared exact-type population (rejected, standing)

File `_request_body.py` J2 (verified) already rejects one shared
exact-type gate across the 116-site `type(x) is` population:
different validated domains, different reasons to change. This
file's `type(...) is not bool` gate (dispatch truthiness: truthy
non-bools must not steer the walker) is one more per-domain instance.
Trigger checked against HEAD, not met: no new foreign-object protocol
needing exclusion inside a boundary. The standing rejection and its
trigger stand; nothing here reopens them.

### R3 — Hint `skip` vs GraphQL `@skip` (rejected, standing)

File `optimizer/selections.py` R-6 (verified) already rejects sharing
between the optimizer-hint `skip` vocabulary and the GraphQL `@skip`
directive, homed at this file. Trigger checked against HEAD, not met:
the target has no directive surface (import census: future,
dataclasses, typing, Prefetch, exceptions, nested_fetch — no
directive machinery, no document reads). The standing rejection and
its trigger stand.

### R4 — Bilateral import-rationale prose (rejected)

The target's runtime-import comment and the `nested_fetch.py` alias
comment both state the import direction and the no-cycle fact. That
is one edge decision projected twice; the definition (the import
statement) exists once, and a contract change moves production +
prose together legitimately. Contract difference: none in behavior —
prose is not a definition. Reconsideration trigger: the two blocks
state different invariants (one claims a property the other denies).

### R5 — Per-message rejection grammars (rejected)

Each `ConfigurationError` message names its own subject (Prefetch
type, strategy name, bool flags, three combination wordings). No
package-wide message grammar is owned anywhere (File
`utils/policies.py` R3 precedent: per-subject grammars rejected).
Contract difference: per-site framing with a local subject vs one
parameterized grammar. Reconsideration trigger: the package adopts
one owned rejection-message grammar.

### R6 — Construction-time matrix vs walker dispatch order (rejected, re-verified fresh)

`OptimizerHint.__post_init__` owns shape validity (all conflicting
pairs unconstructible, pair-completeness verified); `walker.py::
_apply_hint` owns plan-time dispatch over validated shapes, and both
docstrings state the priority order is documentation, not collision
arbitration. The walker's own refusals (many-side `force_select`,
`to_attr` without a consumer-assigned resolver, lookup-must-target
the hinted relation) need plan-time inputs — field cardinality,
resolver assignment, relation path — that construction cannot see.
Contract difference: validity of the value vs application to the
plan. (The REOPENED walker artifact's matching split was used as a
trigger only; every claim above was re-verified against HEAD bodies.)
Reconsideration trigger: a post-init arm and a walker arm reject the
same shape on the same inputs — then one is redundant.

### R7 — Planner re-resolution vs validation (rejected)

`nested_planner.py::_select_nested_strategy` calls the same
`resolve_strategy` on an already-validated name. That is one owner
composed twice, not two definitions; re-resolution cannot raise on a
landed schema (stated at both ends, and construction already passed
through `_require_strategy`). Reconsideration trigger: the planner
catches or branches on a resolve failure — then it treats validation
as its own rule.

### R8 — SKIP sentinel vs other ClassVar sentinels (rejected)

`SKIP` is the only post-body-assigned dataclass-member sentinel
package-wide; every other `ClassVar` assigns inline (registries,
snapshots, config). The deferred assignment is forced by dataclass
semantics (the class cannot reference itself inside its own body).
Contract difference: member identity vs registry/config storage.
Reconsideration trigger: a second deferred-assignment member sentinel
appears.

## Defects

### D1 — HEAD `_require_prefetch` lets a raising `__class__` escape raw (observed; concurrent hunt owns these lines — NOT homed)

At HEAD bytes, `optimizer/hints.py::_require_prefetch` calls
`isinstance(obj, Prefetch)` unguarded while its contract reads
"Return `obj` when it is a `Prefetch`; else raise
`ConfigurationError`." `isinstance` consults `__class__`, so a value
whose `__class__` raises escapes as the raw exception instead of the
typed rejection. The worktree already carries the concurrent hunt
session's fix on these exact lines (try/`except BaseException` arm +
docstring paragraph, the `+12/-1` recorded under Freshness) plus its
pin (`tests/optimizer/test_hints.py::`
`test_prefetch_obj_rejects_class_liar_safely`, the `+24` on that
file). Worker 0: home on a card ONLY if the hunt does not land its
fix; if it lands, close as fixed-concurrent. Owner if homed:
`optimizer/hints.py::_require_prefetch` (this file). Untouched per
protocol — recorded, never edited, never worked around.

Near-misses considered against HEAD bytes and NOT filed: (a)
`_require_strategy` returns the original selection (not the resolved
instance) after validating — deliberate, pinned by the carried
hostile-`__eq__` oracle; the planner re-resolves. (b) `hint_is_skip`
absorbs `BaseException` — the deliberate never-raises audit contract,
pinned by `TestSkipPredicate`. (c) `types/base.py` checks
`optimizer_hints` key-stringness in both `_meta_optimizer_hints` and
`_validate_optimizer_hints` — both sites live in `types/base.py`;
held for File `types/base.py` (undispatched, later in queue), not
adjudicated here. (d) The stored `Prefetch` is referenced, not
snapshotted — no contract source promises snapshot semantics.

## Pending execution

None. All conclusions are static against HEAD bytes; no probe, no
pytest, no scratch scope. Sharded and Postgres cells are inapplicable
by construction: the target reaches no database, alias, or dialect
decision (construction-time validation plus in-memory reads; the
PG-marked live strategy rows pin `nested_fetch.py` behavior with
hints as input, and no claim here depends on their execution).

## Judgment

Zero-edit file item: the target single-owns the hint value contract
and the skip predicate, consumes the strategy and safe-naming owners
by name everywhere it must hold, with three new families named for
Worker 0 (`Index rows` below), one file-local row, and eight
rejections (three standing rejections trigger-checked, one
re-verified fresh against a reopened neighbor). One hunt-owned
observation recorded unhomed under `## Defects`. No pending
execution, no production edit, no test edit. HEAD stayed `5ee86193`
throughout; the item touched nothing tracked.

## Index rows for Worker 0

(Worker 0 alone edits the plan; rows named here for transcription.)

- Family `optimizer-hint-shape` | Owner
  `optimizer/hints.py::OptimizerHint` (with `_require_prefetch`,
  `_require_strategy`, post-body `SKIP`) | Files
  `optimizer/hints.py`, `optimizer/walker.py`,
  `optimizer/nested_planner.py`, `types/base.py`, `types/definition.py`
  | Holding item Family `optimizer-hint-shape` | open
- Family `optimizer-hint-skip-predicate` | Owner
  `optimizer/hints.py::hint_is_skip` | Files `optimizer/hints.py`,
  `optimizer/walker.py`, `optimizer/nested_planner.py`,
  `optimizer/extension.py` | Holding item Family
  `optimizer-hint-skip-predicate` | open
- Family `nested-connection-strategy-selection` | Owner
  `optimizer/nested_fetch.py::resolve_strategy` (with
  `StrategySelection`) | Files `optimizer/nested_fetch.py`,
  `optimizer/hints.py`, `optimizer/extension.py`,
  `optimizer/nested_planner.py`, `conf.py` | Holding item Family
  `nested-connection-strategy-selection` | open
- Module mechanics (frozen form, `ClassVar` declaration, post-body
  `SKIP` assignment, runtime import directions, exceptions consumer
  link) | `optimizer/hints.py` | `optimizer/hints.py` | File
  `optimizer/hints.py` | file-local
- The two `_require_*` factory guards |
  `optimizer/hints.py::_require_prefetch` (rejection recorded here) |
  `optimizer/hints.py` | File `optimizer/hints.py` | rejected
- Exact-bool gate vs the shared exact-type population |
  `optimizer/hints.py::OptimizerHint.__post_init__` (standing J2
  trigger-checked here) | `optimizer/hints.py`,
  `django_strawberry_framework/_request_body.py` | File
  `optimizer/hints.py` | rejected
- Hint `skip` vs GraphQL `@skip` |
  `optimizer/hints.py::hint_is_skip` (standing R-6 trigger-checked
  here) | `optimizer/hints.py`, `optimizer/selections.py` | File
  `optimizer/hints.py` | rejected
- Bilateral import-rationale prose |
  `optimizer/hints.py` (rejection recorded here) |
  `optimizer/hints.py`, `optimizer/nested_fetch.py` | File
  `optimizer/hints.py` | rejected
- Per-message rejection grammars | `optimizer/hints.py` (rejection
  recorded here) | `optimizer/hints.py` | File `optimizer/hints.py` |
  rejected
- Construction-time matrix vs walker dispatch order |
  `optimizer/hints.py::OptimizerHint.__post_init__` (rejection
  recorded here, re-verified fresh) | `optimizer/hints.py`,
  `optimizer/walker.py` | File `optimizer/hints.py` | rejected
- Planner re-resolution vs validation |
  `optimizer/nested_fetch.py::resolve_strategy` (rejection recorded
  here) | `optimizer/nested_fetch.py`, `optimizer/nested_planner.py`,
  `optimizer/hints.py` | File `optimizer/hints.py` | rejected
- SKIP sentinel vs other ClassVar sentinels |
  `optimizer/hints.py::OptimizerHint.SKIP` (rejection recorded here) |
  `optimizer/hints.py` | File `optimizer/hints.py` | rejected

## Independent verification (Worker 2)

### Part A — Own trace (recorded before opening `## Findings`)

HEAD pinned: `git rev-parse --short HEAD` = `5ee86193` (full
`5ee8619330e7e236b61060a1ec9cb9e62b7061aa`), confirmed before any read.
Trace subject is HEAD bytes
`git show HEAD:django_strawberry_framework/optimizer/hints.py` (blob
`da46ef891ccd8a2d42c8ac7519d9f42c9cb73b74`, 271 lines). Worktree file
(`8064af14930636d6b12a538a996603ccadfdb420`) carries the concurrent hunt's
`_require_prefetch` guarded-`isinstance` arm + docstring (+12/-1 vs HEAD);
confirmed by diff content, never traced, never touched. Window tracked diff
vs `ITEM_BASELINE=8261f5f52334dfc521393ff317f599a8b8b012b5` names only
`docs/dry/dry-0_0_15.md` (Worker 0 dispatch records); zero package/test
paths from this item. `tests/optimizer/test_hints.py` worktree dirt (+24:
`test_prefetch_obj_rejects_class_liar_safely`) is hunt content by the same
attribution, not Worker 1's. Oracle reads below use HEAD bytes
(`d3e413bdc0e93d791399c023a442f6701416b5a1`, 414 lines).

Instrument: `ast.parse` over `/tmp/hints_HEAD.py` (HEAD bytes):
`ast.Module.body` = **12 members** (index 0 module docstring; 1–6 six
`ImportFrom`: `__future__`, `dataclasses`, `typing`, `django.db.models`,
`..exceptions`, `.nested_fetch`; 7 `_require_prefetch`; 8
`_require_strategy`; 9 `OptimizerHint`; 10 `hint_is_skip`; 11 post-body
`SKIP` assignment). `OptimizerHint` body: 5 field `AnnAssign`
(`force_select`, `force_prefetch`, `prefetch_obj`, `skip`,
`nested_strategy`), 1 `ClassVar` `SKIP` declaration, `__post_init__`, 4
factory classmethods (`strategy`, `select_related`, `prefetch_related`,
`prefetch`). Imports are composition, the docstring is projection; neither
is a rule. Rule-bearing surface: the 2 module guards, the class record +
matrix + factories, the skip predicate, the sentinel assignment.

Sites and roles (all production cites re-checked at HEAD via
`git show HEAD:<path>` / `git grep HEAD`, because `types/base.py`,
`types/definition.py`, `optimizer/nested_fetch.py`, and
`optimizer/nested_planner.py` worktrees are hunt-dirty):

- Definition `django_strawberry_framework/optimizer/hints.py::OptimizerHint`
  (+ `_require_prefetch`, `_require_strategy`, post-body `SKIP` assignment):
  the `Meta.optimizer_hints` value contract — five-field frozen record,
  four factories, construction-time conflict matrix. Sole owner.
- Definition `django_strawberry_framework/optimizer/hints.py::hint_is_skip`:
  the skip read (`None` → `False`; `is SKIP` → `True`; `getattr(hint,
  "skip", False)` with `except BaseException` → `False`). Sole production
  callers, each composing by name: `optimizer/walker.py::_apply_hint`
  (`walker.py:1120`), `optimizer/nested_planner.py`
  (`nested_planner.py:1120` HEAD), `optimizer/extension.py::check_schema`
  (`extension.py:1448`). Zero direct `.skip` reads outside `hints.py` at
  HEAD (`git grep "\.skip\b"` hits only `hints.py` internals).
- Consumer `django_strawberry_framework/optimizer/walker.py::_apply_hint`:
  dispatches the four hint shapes after `hint_is_skip`; reads
  `hint.prefetch_obj` / `hint.force_select` / `hint.force_prefetch` once
  each; owns the hinted-`to_attr` plan-time rejection (generated-resolver
  cache contract, distinct from the hint value contract).
- Consumer `django_strawberry_framework/optimizer/nested_planner.py::_select_nested_strategy`:
  `getattr(hint, "nested_strategy", None)` then `resolve_strategy(name)`
  by name; falls back to `active_strategy()`. Re-resolution, not
  re-validation.
- Consumer `django_strawberry_framework/optimizer/extension.py::check_schema`:
  `hint_is_skip(hints.get(field_name))` audit gate; never-raises contract
  preserved by the predicate's fail-closed shape.
- Consumer `django_strawberry_framework/types/base.py::_meta_optimizer_hints`
  + `::_validate_optimizer_hints`: the `Meta` container layer (mapping
  shape, key-is-`str`, key-on-model, key-selected-relation,
  value-is-`OptimizerHint`). Distinct layer from the value contract:
  changing a hint field never moves these, and vice versa.
- Upstream owner `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`
  (+ `StrategySelection` alias beside `NestedConnectionStrategy`): the
  strategy vocabulary. Composed by name from four sites: `hints.py`
  (`_require_strategy`), `nested_planner.py`, `extension.py` (×2:
  constructor settle + `_configuration` fallback). `None`-reads-setting
  lives there; `_require_strategy` explicitly rejects `None` rather than
  delegating, which is its own contract (factory-`None`-must-not-silent),
  not a second setting read.
- Upstream owner `django_strawberry_framework/exceptions.py::_safe_type_name`
  (+ `ConfigurationError`): rejection labels and error type. `hints.py`
  consumes both by name.
- Re-export `django_strawberry_framework/__init__.py` (`OptimizerHint`):
  composition, not a definition.
- Oracles (independent: spell literals, never import `_require_*`):
  `tests/optimizer/test_hints.py` HEAD (414 lines; module import is
  `OptimizerHint` only; `hint_is_skip` imported inside test bodies);
  `tests/optimizer/test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes`
  (HEAD); live
  `examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_hints_are_observable_over_http`
  and `test_optimizer_auto_api.py` strategy-override rows (consumer-shape
  oracles).
- Projections: module docstring consumer example; `nested_fetch.py` /
  `nested_planner.py` / `walker.py` / `lateral_fetch.py` docstring mentions
  of `OptimizerHint.*` (all prose, zero value reads);
  `examples/fakeshop/test_query/README.md` optimizer-hints section.

Change challenges (each with the definition count I derive):

- C1 new hint field (e.g. a sixth directive): moves `OptimizerHint` record
  + `__post_init__` matrix only → **count 1** (`hints.py`). Walker gains a
  consumer branch; that is enforcement extension, not a second definition.
- C2 Prefetch-rejection change (type rule or message): moves
  `_require_prefetch` only → **count 1**. `utils/querysets.py:2465` HEAD
  `isinstance(entry, Prefetch)` is a different population (queryset-seal
  entries: `str`-or-`Prefetch` with exact-`str` rule) with a different
  trigger; positing the C2 change there moves nothing.
- C3 strategy-vocabulary change (new backend name): moves `nested_fetch.py`
  registry + `resolve_strategy` → **count 1 outside hints**; `hints.py`
  needs no edit (delegation by name). Confirms `nested_fetch.py` owns the
  vocabulary and `hints.py` is a consumer.
- C4 skip-read semantics change (e.g. `None` means skip): moves
  `hint_is_skip` only → **count 1**; the three callers follow by
  construction.
- C5 bool-flag strictness change (e.g. accept truthy): moves
  `__post_init__` only → **count 1**. Sibling exact-type gates
  (`error_policy.py`, `conf.py`, `utils/relations.py`,
  `resource_policy.py`, `mutations/sets.py`, `extensions/debug.py`,
  `utils/querysets.py`) each own their own record's field contract with
  distinct messages and triggers; the shared `type(x) is not bool` idiom
  is not a shared rule.

Owners I would choose: hint value contract + conflict matrix →
`optimizer/hints.py::OptimizerHint`; skip read →
`optimizer/hints.py::hint_is_skip`; strategy vocabulary →
`optimizer/nested_fetch.py::resolve_strategy`; `Meta` container shape →
`types/base.py`; rejection labels → `exceptions.py`. No consolidation owed
inside this file item; any cross-file candidate routes to its holding
family by name.

Six-axis matrix, discharged against the target's real surface:

1. Cross-flavor policy mirroring — SEARCHED: sibling `Meta` validators
   (`types/base.py` for `optimizer_hints`; filters/orders/forms/mutations
   sets for their own keys) each validate their own family's keys in local
   vocabulary. No shared `Meta`-validation rule; the hint VALUE contract
   is optimizer-local. No consolidation.
2. Sync/async twins — INAPPLICABLE BY CONSTRUCTION: HEAD bytes contain
   zero `async`/`await` (grep-verified). Pure dataclass + predicates; no
   I/O or await boundary exists to twin across.
3. Derived rather than repeated knowledge — SEARCHED: `StrategySelection`,
   `resolve_strategy`, `_safe_type_name`, `ConfigurationError` all
   imported by name from their owners; no name concatenation, no `_meta`
   re-derivation, no settings re-read (`None` handling split is contractual,
   see `_require_strategy` role above). `nested_planner.py` duck-reads
   `nested_strategy` via `getattr` with a `None` default — a tolerant read,
   not a rebuild. No consolidation.
4. Inverse / round-trip pairs — INAPPLICABLE BY REASON: the target is a
   construction-validated record plus predicates; it encodes, decodes,
   packs, parses, or shapes nothing across a boundary. No pair exists.
5. Contracts restated in another medium — SEARCHED: test oracles spell
   literal expectations (`match="Prefetch"`, flag assertions) and import
   only the public names; live-query oracles assert SQL/window behavior,
   not helper bodies; docstring/README prose describes without owning.
   Each medium classified above; no restatement needs consolidation.
6. Enforcement by omission — SEARCHED: enumerated every production skip
   read (3/3 via `hint_is_skip`), every `nested_strategy` read
   (`hints.py` validates, `nested_planner.py` re-resolves by name),
   every `force_*`/`prefetch_obj` read (only `walker.py::_apply_hint`).
   No missing member, no bypass, no gap. (A `to_attr` rejection exists
   only in `walker.py::_apply_hint`; the `nested_fetch.py` `to_attr` row
   contract is a different rule about strategy row landing, not a missing
   second guard.)

### Part B — Findings reconciliation and verdict

Read after Part A was recorded: `## System trace` (lines 6–78),
`## Verification` (79–189), `## Findings` (190–430), `## Defects`
(431–461), `## Pending execution` (462–470), `## Judgment` (471–482),
`## Index rows for Worker 0` (483–537). Every difference from Part A
is reconciled here; everything else is agreed.

(a) Enumeration — AGREE, member by member. Worker 1's 12-node table
matches my independent AST census exactly (0 docstring; 1–4 plain
imports; 5 `..exceptions`; 6 `.nested_fetch`; 7 `_require_prefetch`;
8 `_require_strategy`; 9 `OptimizerHint`; 10 `hint_is_skip`; 11
post-body `SKIP` assignment). The split home of member 8 (F1 for the
`None` arm + message, F3 for the delegation) matches my Part A role
analysis. Nothing unassigned.

(b) Matrix — AGREE on all six axes. Axis 1: Worker 1 searched sibling
Meta-value surfaces as typed wrappers (deployment dataclasses via the
policies ladder; strategy/plan/descriptor records) while I searched
sibling Meta validators — complementary disproof populations, same
discharged conclusion, no conflict. Axis 2: `NO SUCH SURFACE` is
correct; I independently grep-verified zero `async`/`await` in HEAD
bytes. Axis 3: the dual skip read as one predicate is correct, and
the load-bearing claim (non-sentinel `OptimizerHint(skip=True)` ships
in the example) is confirmed at
`examples/fakeshop/apps/library/schema.py:156` HEAD. Axis 4: `NO SUCH
SURFACE` is correct for a construction-validated record plus
predicates. Axis 5: the medium census is accurate — 9 test classes
(counted), 2 live suites, 2 GLOSSARY anchors (`OptimizerHint`,
`Meta.optimizer_hints`, shipped `0.0.3`), the `docs/README.md`
strategy-override paragraph (lines 334–346 HEAD), TREE module lines,
3 consumer-side composition notes. Axis 6: the per-member census is
accurate — 3/3 production skip reads via `hint_is_skip`
(probe `skip-caller-census`), sole `force_*`/`prefetch_obj` reader
`walker.py::_apply_hint`, sole `nested_strategy` reader
`nested_planner.py::_select_nested_strategy`, stated allowances (empty
form, `force_prefetch` + `nested_strategy`). No gap, no bypass.

(c) Challenges and definition counts — AGREE on every count (all 1),
with ONE prose correction on record (W2 correction, following the
run-5 `utils/policies.py` precedent of verifying with the correction
in the artifact). Worker 1's Conflict-matrix row says "all six pairs
among `skip`, `force_select`, `force_prefetch`, `prefetch_obj`,
`nested_strategy` carry an arm except the two intentional allowances".
Five members yield TEN pairs, not six; the correct census against
HEAD `__post_init__` is: 9 of 10 pairs carry arms (skip×3 in arm 1;
`force_select`×`force_prefetch` in arm 2; `prefetch_obj`×2 in arm 3;
`nested_strategy`×3 in arm 4 — probe `matrix-nine-pairs-present`
re-derives this), the 10th pair
(`force_prefetch` + `nested_strategy`) is the one intentional pair
allowance (stated redundant-but-harmless), and the empty no-op form
is a separately allowed non-pair. Corrected sentence: "all ten pairs
among the five members carry an arm except the one intentional
allowance (`force_prefetch` + `nested_strategy`), plus the separately
allowed empty form." This changes no home, no count, no owner, and no
verdict; the matrix-completeness conclusion stands.

(d) Findings F1/F2/F3/L1 — AGREE, including owners. F1
(`optimizer-hint-shape`, owner `hints.py::OptimizerHint`) correctly
excludes `extension.py` (a skip-only consumer, homed in F2). F2
(`optimizer-hint-skip-predicate`, owner `hints.py::hint_is_skip`)
correctly notes the planner gate returns before any strategy read
(HEAD `nested_planner.py:1120` precedes `:1380`). F3
(`nested-connection-strategy-selection`, owner
`nested_fetch.py::resolve_strategy`) correctly records hints as pure
consumer; the extension "annotation + two resolve calls" claim is
confirmed (`extension.py:926`, `:961`, `:987`, clean tree). L1
correctly pins the runtime-import direction to the `get_type_hints`
oracle and the exceptions link as one of 20+ consumers (30 files at
HEAD — the claim is conservative and true).

(e) Rejections R1–R8 — AGREE; each carries a contract difference and
a reconsideration trigger. Standing rejections verified to exist and
correctly used as trigger-checks only: `_request_body.py` J2
(artifact line 771 + index row 907) and `selections.py` R-6 (artifact
lines 141/582/1013, homed at this file). R8 census footnote (nearest
rival examined): `nested_fetch.py:160` `_dst_spec_attr:
ClassVar[str]` is a bare declaration but assigns inline in subclasses
(`lateral_fetch.py:463`, `single_parent_fetch.py:175`) and is a
per-subclass config name, not a post-body member sentinel — R8's
"only post-body-assigned member sentinel" claim stands.

(f) Freshness — AGREE; every pin re-hashed and matched: target
`da46ef89` / worktree `8064af14`; `walker.py` `e8d80005`;
`nested_planner.py` `b4dfd4a6`; `nested_fetch.py` `4d8d37a7`;
`extension.py` `49667a93`; `types/base.py` `91c58747`;
`types/definition.py` `fa6c4d33`; root `__init__.py` `0ef72601`;
`test_hints.py` `d3e413bd` / worktree `90253a19`; `test_library_api.py`
`1f107fff`; `test_optimizer_auto_api.py` `ca9fea06`; GLOSSARY
`d3ef357c`; `docs/README.md` `c32da236`; `conf.py` `c6ad46aa`;
`exceptions.py` `e06b0b7f` (probe pins + direct `git rev-parse`
checks). Hunt dirt on both fingerprints is recorded NOT-traced in
every finding.

(g) D1 handling — CORRECTLY RECORDED, no correction needed. D1
observes HEAD behavior precisely (unguarded `isinstance` vs the "else
raise `ConfigurationError`" contract), attributes the worktree fix to
the concurrent hunt by diff content without touching it, names the
owner-if-homed (`hints.py::_require_prefetch`, this file), and gives
Worker 0 a closeout-conditional homing instruction (home only if the
hunt does not land; else fixed-concurrent) — matching the run-5
standing protocol for hunt-owned lines and DRY.md (defects homed by
Worker 0, never fixed inside the item). Near-misses (a)–(d) are each
correctly not filed: (a) original-selection return is deliberate with
planner re-resolution; (b) the `BaseException` absorb is the pinned
never-raises audit contract; (c) the dual key-stringness checks both
live in `types/base.py` at HEAD (`:1027`, `:1450`) and are correctly
held for File `types/base.py`, not adjudicated here; (d) no contract
source promises snapshot semantics. Worker 2 files no additional
defect entries: none found.

(h) Pending execution — AGREE: none. The sharded/Postgres
inapplicable-by-construction reason is judged correct: the target
reaches no database, alias, or dialect decision (construction-time
validation plus in-memory reads; the PG-marked live rows pin
`nested_fetch.py` behavior with hints as input). No mutating proof
was needed, so no `$TMPDIR/dry-ws` copy was taken and the
package-`__file__` + DB-`NAME` gate was not triggered; every claim
above is static against HEAD bytes.

(i) Prose and gates — CLEAN. No process-provenance words (the
`Worker 0` mentions are DRY-mandated routing + the `## Index rows`
convention, matching the verified `utils/policies.py` precedent; no
pass/phase/session/first-person prose); `path::Symbol` citations
throughout; test tier N/A (no tests created or run, explicitly
stated). Ruff on the item's touched path (the `.md` artifact):
`uv run ruff format --check` → `1 file already formatted`, exit 0;
`uv run ruff check` → `No Python files found under the given path(s)
/ All checks passed!`, exit 0 — the artifact is `.md`, ruff-excluded
in effect. Probe
`docs/dry/temp-tests/dry-file-optimizer__hints-w2/census.py` is
read-only, HEAD-pinned, ruff-clean (`All checks passed!`, formatted),
17/17 PASS, `FAILURES: none`. `docs/dry/` is excluded from
`scripts/check_trailing_commas.py` (`EXCLUDE_SCRATCH_DIRS`), and the
artifact uses zero reference-style links, so no link scaffold is owed.

VERDICT: `verified`. Zero-edit file item: 12/12 members homed (3 new
families F1–F3, 1 file-local L1, 8 rejections R1–R8), matrix
discharged on all six axes, every definition count independently
re-derived at 1, every site role confirmed, one W2 prose correction
(pair census, part (c)) on record changing nothing structural, D1
correctly observed-not-homed, no W2 defects, no pending execution.
No production edit is owed or demanded; Worker 0 ticks the row and
transcribes the 12 index rows in `## Index rows for Worker 0` above
(verified verbatim, no corrections).
