# DRY review: `optimizer/__init__.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

Target `django_strawberry_framework/optimizer/__init__.py` (29 lines, read in
full) owns no behavior. It is a two-name leaf manifest: it composes
`DjangoOptimizerExtension` by name from its home module
`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension`
and re-exports the framework-wide `logger` by name from its sole definition
at `django_strawberry_framework/__init__.py::logger`, with `__all__`
mirroring exactly those two bindings. Its docstring is prose projection:
the re-export contract (paragraph 1), the deliberate omission of
`OptimizationPlan` / `plan_optimizations` from the leaf (paragraph 2), and
the single-sourcing rationale plus the future-subpackage pickup permission
(paragraph 3).

Sites found re-deriving from this side (never inherited from the root
`__init__.py` item's F1 — its record was used only as a trigger to check):

- *Definition (logger):* `django_strawberry_framework/__init__.py::logger`
  (sole `getLogger(` call package-wide; full-package search returns exactly
  one site).
- *Consumer row (logger):* this file's `from .. import logger` (statement 2)
  plus `__all__` entry.
- *Intra-subpackage logger consumers through this re-export* (`from . import
  logger`): `optimizer/extension.py`, `optimizer/walker.py`,
  `optimizer/nested_planner.py`, **and** `optimizer/single_parent_fetch.py`
  (four sites — the root item's F1 lists three; this side's sweep finds the
  fourth; the claim below holds a fortiori, see `## Defects`).
- *Cross-subpackage logger consumers through the leaf path* (`from
  ..optimizer import logger`): `types/resolvers.py` (aliased
  `_resolver_logger`, the N+1-warning surfacing site) and `types/finalizer.py`.
  Direct-root consumers that never touch the leaf (`schema.py`,
  `consumers.py`, `_request_body.py`, `extensions/debug.py`,
  `extensions/error_policy.py` via `from .` / `from .. import logger`) were
  read as population, not members.
- *Definition (extension):*
  `optimizer/extension.py::DjangoOptimizerExtension` (subclasses
  `extensions/operation_state.py::_OperationBoundExtension`; that mechanism
  was read for candidacy and has no surface here — C6).
- *Second-layer consumer (extension):* the package root
  `django_strawberry_framework/__init__.py` (`from .optimizer import
  DjangoOptimizerExtension` + `__all__` entry).
- *Oracles (independent — they spell the contract without reading the leaf
  manifest):* `tests/base/test_init.py::test_logger_name_is_django_strawberry_framework`
  (spells the string), `::test_optimizer_subpackage_reexports_top_level_logger`
  (`is` identity), `::test_public_api_surface_is_pinned` (exact root tuple;
  pins `logger`'s absence from root `__all__`),
  `::test_reexported_types_resolve_to_canonical_subpackage_definitions`
  (leaf-vs-root `is` row for the extension); the `tests/optimizer/*`
  pass-through imports (`from django_strawberry_framework.optimizer import
  logger` in `test_walker.py`, `test_nested_index_advisory.py`,
  `test_extension.py`) exercise the binding on every suite run.
- *Projections:* this file's docstring, the root's in-file logger comment,
  the `DjangoOptimizerExtension` glossary anchor and usage blocks
  (`docs/GLOSSARY.md`, `docs/README.md`, `TODAY.md`), both example import
  paths (`from django_strawberry_framework import DjangoOptimizerExtension`
  and `from django_strawberry_framework.optimizer import
  DjangoOptimizerExtension` in `examples/fakeshop/`).
- *Non-site (deliberate omission):* `OptimizationPlan`
  (`optimizer/plans.py::OptimizationPlan`) and `plan_optimizations`
  (`optimizer/walker.py::plan_optimizations`) live only at their dotted
  paths, consumed by `extension.py` and tests directly; neither the leaf
  nor the root re-exports them (root `__all__` confirmed by full read).

Connected upstream: none — the logger rule is package-internal; upstream
`strawberry_django/optimizer.py` carries no subpackage-manifest rule and
was not needed beyond that determination.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched every sibling leaf manifest
   (`filters`, `types`, `mutations`, `auth`, `extensions`, `forms`,
   `middleware`, `management`, `rest_framework`, `testing`, `utils`, `orders`
   `__init__.py` — `filters/__init__.py` + `types/__init__.py` read in full,
   remainder swept for `logger` re-export vocabulary): no second leaf
   re-exports `logger`; other subpackages consume the root directly or not
   at all. One rule, one leaf re-export. No surface beyond F1.
2. **Sync/async twins.** No `def`, no `await`, no `async`, no
   `sync_to_async` in the target (full-read confirmed). Import-time bindings
   only. No surface.
3. **Derived rather than repeated knowledge.** Both bindings compose by name
   (two `from`-imports + `__all__` mirror); no concatenation, no `_meta`
   read, no settings derivation. The one literal the file touches (the
   logger name) lives once at the root; this file spells no string. No
   surface.
4. **Inverse / round-trip pairs.** Import binding → `__all__` membership →
   consumer import is one direction with a single author (this file), not
   two halves. No surface.
5. **Contracts restated in another medium.** Media inventoried: code
   (bindings + manifest); docstring projection; root second-layer consumer
   rows; oracles (name, identity, exact-tuple pin, leaf-vs-root `is` rows,
   pass-through imports); docs projections (glossary anchor, README/TODAY
   usage blocks); example import paths. A change moves once at its home
   module; leaf, root, and oracles follow by name (C1–C5). Counted at the
   owners, never here.
6. **Enforcement by omission.** Two deliberate omission sets, both carrying
   in-file contract prose: (a) `OptimizationPlan` / `plan_optimizations`
   stay on their dotted paths (docstring paragraph 2 — internal details
   consumed by `extension.py` and tests); (b) `logger` is in the leaf
   `__all__` but deliberately absent from the root `__all__` (star-import
   must not rebind a consumer's `logger`; pinned by the root exact-tuple
   oracle, owned at the root). Every member the surface requires is present
   (both names bound, `__all__` names exactly those two). No missing guard.

### Enumeration

Instrument: `ast.parse` over the working file, counting `ast.Module.body`
members — **4 top-level statements**. Every member lands below; every
challenge in `### Challenges` ends in a family row, a file-local row, or a
rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (subsystem + re-export-contract + omission + single-sourcing paragraphs) | (none) | prose projection, F1/F2 |
| 2 | `from .. import logger` | 1 name | F1 (consumer) |
| 3 | `from .extension import DjangoOptimizerExtension` | 1 name | F2 (consumer) |
| 4 | `__all__ = ("DjangoOptimizerExtension", "logger")` | 2-member tuple | F1 + F2 |

Rules: R1 logger re-export (statements 1–2, 4) → existing indexed family
`logger-single-sourcing` (consumer row from this side, status stays `open`);
R2 extension re-export + two-member manifest + dotted-path omission prose
(statements 1, 3–4) → new file-local row `optimizer-leaf-manifest`;
R3 operation-bound extension mechanism → checked, no surface (C6, do not
inherit); R4 package-root public surface → rejected with this leaf's own
contract difference + trigger (R1 below, do not inherit). Indexed families
swept with no vocabulary in the target (full 29-line read is the closed
population): `version-single-sourcing`, `drf-soft-export-guard`,
`subsystem-clear-lifecycle` (zero `register_subsystem_clear` tokens),
`type-registry-*`, `sealed-authorization-source`, mutation/filter/form
families — no member unassigned.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 rename | rename the logger to `"dsf"` | **1** (the root `getLogger` call; leaf import + six consumer imports + oracles + downstream `LOGGING` configs follow by name) | independent here |
| C2 | R1 second definition | paste `logging.getLogger("django_strawberry_framework")` into the leaf | **2** (root + leaf) — proves the current count is 1; the hand copy passes the name oracle and fails the identity oracle, so the identity test is the gate | independent here |
| C3 | R2 add member | re-export `OptimizationPlan` at the leaf | **1** (home `optimizer/plans.py::OptimizationPlan`; leaf + root + oracle rows follow) | independent here |
| C4 | R2 rename | rename `DjangoOptimizerExtension` | **1** (home `optimizer/extension.py`; leaf + root + example/test imports follow) | independent here |
| C5 | R2 un-root | root stops exporting the extension (leaf stays) | **0 here** (root import + `__all__` + pin/identity oracles move; this file does not) | independent — proves separation |
| C6 | R3 mechanism | change the `_OperationBoundExtension` per-operation-state contract | **0 here** (owned at `extensions/operation_state.py::_OperationBoundExtension`; defined behavior lives in `optimizer/extension.py`, never the leaf — no hook, binding, or state token in this file) | no surface — do not inherit |
| C7 | R4 root surface | add a new root-level public symbol | **0 here** unless routed through this leaf; leaf membership vs root manifest are different contracts (see R1 rejection) | no surface — do not inherit |
| C8 | clear-bus sweep | change the `register_subsystem_clear` bus contract | **0 here** (bus at `registry.py`; zero registration tokens in this file — full read) | no surface — do not inherit |

No executable proof was run: the target has no runtime semantics beyond
import-time binding (no branches, no awaits, no queryset/transport code),
so there is no behavior an execution could distinguish. The read-only
`ast.parse` enumeration above ran in the shared tree (non-mutating; the
workspace recipe authorizes mutating proofs, of which this item has none).
Every binding is exercised by consumer imports on every suite run
(`tests/base/test_init.py`, `tests/optimizer/*`, fakeshop suites). All
claims below are therefore `static-reviewed`; there is no
`execution-deferred` proof and no `docs/dry/temp-tests/` scratch was
created — inspection suffices, and a probe could distinguish nothing. No
shared-tree pytest run.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site.

### F1 — logger single-sourcing (existing family `logger-single-sourcing`, consumer row, status stays `open`)

- **Contract + variation.** The string `"django_strawberry_framework"`
  lives in exactly one source location; every in-package handle to the
  canonical logger composes it by name. Consumer-facing (the `LOGGING`-dict
  key), so the name is pinned, not just the object. No legitimate
  variation: one package, one logger.
- **Sites + roles.** *Definition:*
  `django_strawberry_framework/__init__.py::logger` (sole `getLogger(` call
  package-wide, re-verified by search from this side: exactly one hit).
  *Consumer rows (this side):* this file's statement 2 + `__all__` entry;
  four intra-subpackage `from . import logger` consumers
  (`optimizer/extension.py`, `optimizer/walker.py`,
  `optimizer/nested_planner.py`, `optimizer/single_parent_fetch.py`); two
  cross-subpackage `from ..optimizer import logger` consumers
  (`types/resolvers.py` as `_resolver_logger`, `types/finalizer.py`).
  *Oracles:* `tests/base/test_init.py::test_logger_name_is_django_strawberry_framework`
  + `::test_optimizer_subpackage_reexports_top_level_logger` (both spell the
  contract without reading the definition). *Projections:* the root in-file
  comment + this file's docstring paragraphs 1 and 3.
- **Challenges.** C1, C2 → 1 definition each (C2's count-2 state is the
  not-current control that proves today's 1).
- **Owner + lifetime.** Existing owner by responsibility: the package root
  — every legitimate consumer, including future subpackages per this file's
  docstring, can import it without reversing a dependency. No stored
  derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owner stands; this leaf
  stays a by-name re-export.
- **Distinct behavior.** `logger` is deliberately ABSENT from the root
  `__all__` while present in the leaf `__all__` (star-import must not
  rebind a consumer's `logger`); that asymmetry is pinned by the root
  exact-tuple oracle and belongs to the root owner.
- **Behavioral proof.** `static-reviewed` (import-graph + literal search;
  re-derived from this side, not inherited). Rejects "the optimizer
  re-export is a second logger" (C2 control shape).
- **Structural gate.** The two oracle tests above (pre-existing, not new).
  Negative control, re-derived: a behavior-preserving hand copy
  (`logging.getLogger("django_strawberry_framework")` pasted into the leaf)
  passes the name test but fails the identity test — so the identity test,
  not the name test, is the gate that owns this finding.
- **Coupling.** None.
- **Freshness.** Target `d400569adf8ba801ff2293b6abddfd414fa18858`
  (identical to the hash the root item recorded — unchanged since),
  `django_strawberry_framework/__init__.py`
  `0ef72601ecac300ac87ff993af1b04a4f1bc335a`,
  `django_strawberry_framework/optimizer/extension.py`
  `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a`,
  `django_strawberry_framework/optimizer/walker.py`
  `9b111ed938951a073a9226ccbcfacabc3af981e8`,
  `django_strawberry_framework/optimizer/nested_planner.py`
  `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04`,
  `django_strawberry_framework/optimizer/single_parent_fetch.py`
  `e995270af9b213b7f931c03d7dc8f7c084819e1b`,
  `django_strawberry_framework/types/resolvers.py`
  `f3341e6a9f52659925762bce097033bac67e3b51`,
  `django_strawberry_framework/types/finalizer.py`
  `77fd9a2dd229eb9de5f29188c5058035d3606323`,
  `tests/base/test_init.py`
  `4cc121057689409213beb5ec31772130cdacb975`;
  searched populations: `getLogger` package-wide (1 site), `from . import
  logger` intra-optimizer (4 sites), `from ..optimizer import logger`
  cross-subpackage (2 sites), sibling-leaf `logger` vocabulary (0 sites).

### F2 — optimizer leaf manifest (file-local)

- **Contract + variation.** The optimizer subpackage's public surface is
  exactly two names, each composed by name from its home
  (`DjangoOptimizerExtension` from
  `optimizer/extension.py::DjangoOptimizerExtension`, `logger` from the
  package root), with `__all__` mirroring the bindings in-file; plan
  internals (`OptimizationPlan`, `plan_optimizations`) deliberately stay on
  their dotted paths. Legitimate variation: set membership only (a 3rd name
  adds one import line + one tuple entry here, plus consumer rows at the
  root).
- **Sites + roles.** *Definitions:*
  `optimizer/extension.py::DjangoOptimizerExtension`,
  `django_strawberry_framework/__init__.py::logger`. *Consumer rows:* this
  file's statements 3–4 (+ statement 2 shared with F1); the package root
  `from .optimizer import` block + `__all__` entry (second layer, extension
  only). *Oracles:* `tests/base/test_init.py` exact-tuple pin (spells the
  root tuple without reading this file) + the leaf-vs-root `is` identity
  row for the extension (resolves through this file without reading the
  manifest) + the logger identity row (shared with F1) — independent, never
  rewritten to read the owner. *Projections:* statement-1 paragraphs 1–2,
  the glossary optimizer anchor + README/TODAY usage blocks, both example
  import paths.
- **Challenges.** C3, C4 → 1 definition each; C5 → 0 here (separation
  proof).
- **Owner + lifetime.** Per-symbol home modules (declaration, behavior, and
  machinery all live there); this file composes by name (principle 6). No
  stored derivation.
- **Migration.** None (zero-edit item).
- **Distinct behavior.** The dotted-path omission (`OptimizationPlan` /
  `plan_optimizations` not re-exported) is part of this rule's membership
  contract, stated in-file; promoting either is a C3 change (1 definition
  at home, one row here follows).
- **Behavioral proof.** `static-reviewed`. Rejects "a re-export shadows
  its owner" (identity holds by construction of the import system;
  exercised by every suite run's consumer imports) and "the omission hides
  a second definition" (both names resolve once, at their homes — C3).
- **Structural gate.** Pre-existing oracles named above (exact-tuple pin +
  `is` identity rows); standing cover is mechanical, not bespoke: a dropped
  binding fails loudly (`ImportError`) at explicit consumer imports on
  every suite run. No bespoke per-leaf existence test owed (principle 9
  gate-only economy). No failability run owed by this zero-edit item.
- **Coupling.** None.
- **Freshness.** Target + root + `optimizer/extension.py` + `tests/base/test_init.py`
  as in F1, plus `django_strawberry_framework/filters/__init__.py`
  `86b258186638c96995e31919346f44d7951c65ea` and
  `django_strawberry_framework/types/__init__.py`
  `24e8ec204a781e2014565523cdcd97b840104cac` (sibling-leaf shape
  comparison: eager re-export + manifest, distinct membership contracts).

### R1 — `package-root-public-surface` (rejected, nested)

Same eager-re-export + manifest shape as the indexed family, not the same
contract: that family owns the *root* manifest (which symbols the package
root publishes, pinned by the exact-tuple oracle), while this leaf owns
*which optimizer names leave the subpackage* (two-member surface + the
dotted-path omission, pinned in-file). A root-surface change that never
routes through this leaf (e.g. adding an unrelated root symbol) moves zero
definitions here (C7); the one overlapping change (root drops the
extension) is C5's 0-here separation proof. Reconsideration trigger: a
future rule that derives leaf membership from the root manifest (or vice
versa) by construction rather than by parallel by-name rows — then the two
contracts become one. Durable home if ever re-litigated: this file's
docstring paragraph 2 (the omission clause) + the F2 row above.

## Defects

None. Every docstring claim re-checked first-hand and held: both names
resolvable by identity through the leaf; `OptimizationPlan` /
`plan_optimizations` reachable only at their dotted paths (neither leaf nor
root re-exports them); the "sole definition at root" sentence matches the
one-hit `getLogger` sweep. One imprecision noted and ruled not-a-defect:
paragraph 1 names three intra-subpackage logger consumers
(`extension.py`, `walker.py`, `nested_planner.py`) while the sweep finds a
fourth (`single_parent_fetch.py`, same `from . import logger` shape). The
sentence claims no exhaustiveness ("sibling production modules X, Y, Z
consume"), and the load-bearing consequent — removing the re-export breaks
production siblings, not just tests — holds a fortiori with four. No
contract row broken, no guard missing, no layering contradiction.

## Pending execution

None. No `execution-deferred` proof: the target has no runtime semantics
beyond import-time binding, all bindings resolve through consumer imports
on every suite run, and the only instrument used (`ast.parse`) is
non-mutating.

## Judgment

Zero-edit file item. Two rules traced: F1 routes to the existing indexed
family `logger-single-sourcing` (consumer record re-derived from this
side — four intra-subpackage + two cross-subpackage consumers, one more
intra-subpackage site than the root item listed; status stays `open`), F2
is a new file-local row `optimizer-leaf-manifest` with proving challenges
(C3–C5); one nested rejection with contract difference + trigger
(`package-root-public-surface`, R1); `operation-bound-extension-mechanism`
checked with no surface (C6, do not inherit). Enumeration 4/4, all
freshness fingerprints recorded, no defects, no pending execution, no
production edits.

Worker-0 instructions: (a) tick the plan item `File optimizer/__init__.py
— [dry-file-optimizer____init__.md][dry-file-optimizer-init]` as verified
under Run `0.0.15 2026-09-18-1` once Worker 2 agrees; (b) add this one
`## Responsibility index` row (`file-local`, holding item `File
optimizer/__init__.py`):

| `optimizer-leaf-manifest` | per-symbol home modules (`__all__` manifest at `django_strawberry_framework/optimizer/__init__.py`) | `django_strawberry_framework/optimizer/__init__.py` (+2 owner modules) | File `optimizer/__init__.py` | file-local |

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `c4d6a6f121385008150ae4ad07f9b60d81782190`:
`git diff <baseline> -- django_strawberry_framework/optimizer/__init__.py`
empty — target blob `d400569adf8ba801ff2293b6abddfd414fa18858` matches both
`HEAD:django_strawberry_framework/optimizer/__init__.py` and the recorded
`ITEM_BASELINE` file content; target CLEAN. The artifact itself
(`docs/dry/dry-file-optimizer____init__.md`) is a new untracked file, the
item's only output. No `uv run ruff format .` / `ruff check` run (no `.py`
touched; `.md` outside ruff scope). Concurrent dirt (`connection.py` +
`extensions/resource_policy.py` + `filters/sets.py` + `forms/inputs.py` +
`mutations/fields.py` + `mutations/sets.py` hunks, the `filters/inputs.py`
in-flight hunk, `tests/` companions, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` in-flight
edits, the `utils/querysets` duplicate-trace collision, sibling untracked
`dry-file-*.md` artifacts) was never read for content beyond the ledger
paths and left untouched; the `## Owned changes` ledger (walker D1 fix + 2
live test files) gains no row from this item.

## Independent verification (Worker 2)

Own trace, re-derived first-hand from the tree (own searches, own
`ast.parse`, own re-hashes) before reconciling with `## Findings`.

### Own leaf rules

R-A logger re-export consumer. One definition package-wide:
`django_strawberry_framework/__init__.py::logger` (own `getLogger(`
search over `django_strawberry_framework/`: exactly one site).
Consumer census from an own `import logger` sweep (code sites only;
docstring and comment mentions excluded):

- leaf re-export: `optimizer/__init__.py` (`from .. import logger`);
- intra-subpackage via the leaf (`from . import logger`), each verified
  to call the handle: `optimizer/extension.py::DjangoOptimizerExtension`
  module (`logger.debug` at the extension body),
  `optimizer/walker.py` (`logger.debug` at two walk sites),
  `optimizer/nested_planner.py` (`logger.warning`/`logger.debug`
  advisory sites), `optimizer/single_parent_fetch.py` (`logger.debug`
  at the fetch body) — 4 sites;
- cross-subpackage via the leaf path (`from ..optimizer import
  logger`): `types/resolvers.py` (aliased `_resolver_logger`, N+1
  warning call) and `types/finalizer.py` (`logger.warning` call) —
  2 sites;
- direct-root consumers never touching the leaf (`from . import logger`
  / `from .. import logger`): `schema.py`, `consumers.py`,
  `_request_body.py`, `extensions/debug.py`,
  `extensions/error_policy.py` — 5 sites.

Total: 1 definition + 12 import sites. Owner I would choose: the
package root — every legitimate consumer, in any subpackage, can
import it without reversing a dependency; no narrower owner is
importable from everywhere. Same owner as W1.

R-B 2-name manifest + dotted-path omission. Own `ast.parse` of the
target: 4 `ast.Module.body` members (docstring, two `from`-imports,
one `__all__` assign). `__all__` names exactly the two imported
bindings; no string literal beyond binding names (the logger-name
literal lives once at the root). Root `__all__` read in full:
contains `DjangoOptimizerExtension`, omits `logger`,
`OptimizationPlan`, and `plan_optimizations` — both omission claims
hold. Owner I would choose: per-symbol home modules, leaf composes
by name (principle 6). Same as W1 F2.

### Reconciliation vs W1

Agree on every site and role: W1's 4 intra + 2 cross match my 4 + 2
(call sites confirmed above); W1 named the same 5 direct-root
consumers as population. Two differences, both ruled non-material:

- D1 consumer-count vs root F1. The root item's F1 lists three
  intra-subpackage consumers; this side finds four
  (`single_parent_fetch.py` included). Load-bearing root claims are
  invariant: sole `getLogger(` site (re-verified: 1 hit), owner,
  C1/C2 definition counts (consumers listed, never counted), identity
  gate. The closed census belongs to the open family item
  `logger-single-sourcing`, not to either file item. Ruling: no
  amendment to the verified root artifact; no extension of the index
  row (still root + leaf) — extending it now on a partial census
  (direct-root sites unfingerprinted) would enshrine a half-census.
  The family item reconciles from this artifact plus this section.
  Neither consumers-via-leaf-path nor consumers-via-direct-root
  change any definition count.
- D2 challenge parenthetical. W1 C1 says "leaf import + six consumer
  imports": six = the leaf-path consumers only, omitting the five
  direct-root import sites. The verdict (1 definition) is correct;
  the parenthetical is illustrative. Not a defect; no count changes.

### Enumeration check

Member-by-member vs own count (4): docstring prose projection
(F1/F2); `from .. import logger` (F1 consumer); `from .extension
import DjangoOptimizerExtension` (F2 consumer); `__all__` 2-tuple
(F1 + F2). All members assigned; indexed families with zero target
vocabulary correctly carry no member. Agree 4/4.

### Counts, roles, oracles

C1 1, C2 2-control / 1-current, C3 1, C4 1, C5 0-here, C6 0, C7 0,
C8 0 — all agree. Roles agree: one definition, remainder
consumers / oracles / projections. Oracle bodies read first-hand:
`test_logger_name_is_django_strawberry_framework` spells the string;
`test_optimizer_subpackage_reexports_top_level_logger` asserts `is`
identity; `test_public_api_surface_is_pinned` pins the exact root
tuple — none reads the owner it checks. Pass-through leaf imports in
`tests/optimizer/*` and the leaf-vs-root extension `is` row
confirmed present. No oracle rewritten.

### Equivalence, fingerprints, gates, pending

Principle 8: zero-edit, nothing to prove equivalent. No probe is
adequate: import-time bindings only (no branches, awaits, queryset
or transport code); every binding resolves through consumer imports
on each suite run. Database cells inapplicable by construction
(target reaches no database); W1 stated the reason, judged sound.
`## Pending execution` absent — correct, no `execution-deferred`
proof exists (only instrument was non-mutating `ast.parse`).

Fingerprints re-hashed, all 11 match W1 exactly: target
`d400569a…`, root `0ef72601…`, extension `49667a93…`, walker
`9b111ed9…`, nested_planner `0ad8ff5d…`, single_parent_fetch
`e995270a…`, types/resolvers `f3341e6a…`, types/finalizer
`77fd9a2d…`, test_init `4cc12105…`, filters leaf `86b25818…`,
types leaf `24e8ec20…` (abbreviated; full ids in F1/F2 above).

F1 negative control (hand copy passes name, fails identity) stands
reasoned, unexecuted — adequate for a file item; execution is owed
at the open family item `logger-single-sourcing`
(`scripts/prove_failability.py`), per the `mutations/fields.py`
precedent recorded in the plan. F2 standing cover (loud
`ImportError` on a dropped binding + exact-tuple pin) is mechanical,
not bespoke — principle 9 economy holds. R1 rejection carries its
contract difference (root manifest vs leaf membership) and trigger
(derivation by construction); C6 operation-mechanism checked with
genuinely no surface (no hook, binding, or state token in the
29-line target). Coupling: none, agree.

### AGENTS.md prose check

Item-scoped diff for the target path is empty (confirmed: `git diff`
vs `c4d6a6f12…` prints nothing for
`django_strawberry_framework/optimizer/__init__.py`; all other
`git status` dirt is concurrent work, untouched). No production
change to check; no tests owed by a zero-edit file item; no ruff
run owed (no `.py` touched). Artifact citations use
`path::Symbol` form throughout; no raw line refs; link-definition
block carries the canonical groups; no process provenance. Pass.

### Defects (Worker 2)

None. D1 and D2 above were investigated and ruled non-defects
(no contract row broken, no guard missing, no count changed).

### Verdict

`Status: verified`, no pending execution. Worker-0 rows are exact
in the return message: tick the item + add the one
`optimizer-leaf-manifest` file-local index row; leave the
`logger-single-sourcing` row and the verified root artifact
untouched; the family item inherits the reconciled census from
here.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-file-optimizer-init]: dry-file-optimizer____init__.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
