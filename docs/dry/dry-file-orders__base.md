# DRY review: `django_strawberry_framework/orders/base.py`

Status: verified
Run: 0.0.15 2026-09-22-5

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is recorded file-local with its proving challenge, routed to an existing
family holding item, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Small target (151 lines at HEAD bytes): the ordering subsystem's Layer-1
primitive. It DEFINES three behaviors (the deferred `OrderSet` family-base
gate input, the per-family `OrderSet`-only target-type gate with its typed
rejection, the `field_name` optional-`None` constructor shape) and one piece
of declaration (the `RelatedSetTargetMixin` parameterization + thin-wrapper
adapter); everything else is by-name composition of the neutral mixin
machinery (`_bind_owner` / `_resolved_target` / `_set_target` /
`resolve_lazy_class`) and the shared `_safe_*` renderers. No queryset, no
transport, no sync/async machinery, no `Meta` handling, no lookup grammar, no
clear registration, no `__all__`: runtime effects are one class object, one
deferred import, and lazy per-read resolution through the mixin seam.

Connected code read for judgment, outside the item:
[filters-base][filters-base] (HEAD bytes: `RelatedFilter` + `_filter_set_class`
in full, read FIRST per axis 1), [sets-mixins][sets-mixins] (HEAD bytes: full
`RelatedSetTargetMixin` + `LazyRelatedClassMixin` bodies + module docstring),
[orders-sets][orders-sets] (HEAD bytes: metaclass collect call, `get_fields`
cache gate, `target_attr="orderset"` permission attrs),
[orders-inputs][orders-inputs] (HEAD bytes: triples emission, `normalize_input_value`
recursion, `entry.field_name or top_name` fallback),
[orders-factories][orders-factories] (HEAD bytes: `_related_target_attr`),
[orders-init][orders-init] (full: re-export consumer),
[utils-inputs][utils-inputs] (HEAD bytes: BFS `getattr(related,
_related_target_attr)` seam), [utils-permissions][utils-permissions] (HEAD
bytes: `getattr(related_obj, target_attr)` seams), [types-base][types-base]
(HEAD bytes: `_validate_orderset_class` + `_validate_filterset_class` twins),
[finalizer][finalizer] (HEAD bytes: subpass-2 `.orderset` walk),
[exceptions][exceptions] (HEAD bytes: `_safe_*` surface),
[types-converters][types-converters] (HEAD bytes: `<unbound>` model-label
fallback), the contract source [spec-028][spec-028] (Decision 2 + Decision 3
Layer 1-2 passages, read), oracles [test-order-base][test-order-base] (HEAD
bytes: full, read) + [test-order-inputs][test-order-inputs] (HEAD bytes: `None`
-force block, read) + [test-order-sets][test-order-sets] (HEAD bytes: bind
oracle, read), consumer declarations
[library-orders][library-orders] (HEAD bytes: every `RelatedOrder(...)` site),
projections [glossary][glossary] (`RelatedOrder` entry), and the verified
holding artifacts [dry-filters-base][dry-filters-base] (R1/R2/R3 + F-3 as
orientation triggers, re-derived fresh below) and
[dry-orders-init][dry-orders-init] (shape convention).

Dirt note (all hunt-dirtied paths read via `git show HEAD:<path>`, never
touched): the worktree target [orders-base][orders-base] (`afd55efd…`, +21/-4:
guarded `OrderSet`-family interrogation with `except BaseException` arms +
`__class__`-guard prose inside `_validate_target`) is concurrent-external
dirt — every judgment below is against HEAD bytes `4736fda0…`, which govern.
Sibling [orders-inputs][orders-inputs] (`889b5971…`), [orders-sets][orders-sets]
(`f09d9983…`), [utils-inputs][utils-inputs] (`47b2af21…`), and
[test-order-base][test-order-base] (`dac87bf7…`) are likewise hunt-dirtied and
were read at HEAD bytes only. Clean witnesses re-hashed both sides:
[orders-factories][orders-factories] (`4f35b66b…`),
[orders-init][orders-init] (`ed546f9c…`), [filters-base][filters-base]
(`ba52351c…`), [sets-mixins][sets-mixins] (`ad8987ea…`).

Excluded with reason: every other indexed family whose files-covered list was
scanned for this path — none lists `orders/base.py`. The two task-named
interplay families were judged on fresh evidence against this target's REAL
surface and both DIVERGE as membership (C10, C11): `field-value-coercion`
(rejected; owns literal→field-value mechanics the order side never performs —
leaf inputs are direction enums, never field values) and
`subsystem-clear-lifecycle` (verified; owns replay of module/class-level reset
rows — this file holds no ledger, cache, or guard, only per-instance slots and
class-level param strings). `one-sync-boundary`, `queryset-seed-and-model-read`,
`sync-boundary-recourse-wording`, and `child-queryset-alias-inheritance` were
likewise checked by mechanism and found to have no surface here (negatives
verified: zero `async`/`await`/`queryset`/`coerce`/`clear`/`model_for` tokens
in the target). No index row named `lazy-related-class-resolution` or
`related-set-target-lifecycle` exists in the current plan; the filters-twin
artifact's F-2/F-3 treatment was orientation only, and the mixin relationship
is re-derived fresh below as file-local adapter declarations over the existing
single-sited owner (F2).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Read [filters-base][filters-base]'s twin
first (full `RelatedFilter` + `_filter_set_class`): shared seam
(`RelatedSetTargetMixin` subclass, `_target_attr`/`_owner_attr` params,
`_bind_owner` / `_resolved_target` / `_set_target` thin wrappers, per-family
`_validate_target` gate, deferred sibling-`sets` import) with genuinely
different adapters — the order twin has no `lookups=` guard, no
`_has_explicit_queryset`, and no `get_queryset` (verified absent: zero tokens),
while the filter twin has no `field_name` constructor parameter (it rides
django-filter machinery). Each mirror pair is re-derived fresh with this
file's own difference: deferred bases → F1 nested rejection (CONVERGE with
verified filters R1); gate bodies → F3 nested rejection (CONVERGE with
verified filters R2); `get_queryset` absence → R1 (CONVERGE with verified
filters R3). The [types-base][types-base] Meta-validator twins
(`_validate_orderset_class` / `_validate_filterset_class`) share only the
deferral idiom with F1, not a responsibility (C1/C2: different seams, opposite
edge-change responses) — considered and distinct, no row.

**2. Sync/async twins.** Inapplicable with reason: the target defines no colored
pair — zero `async def` / `await` / `sync_to_async` tokens in the full HEAD
read, and no boundary call. The `apply_sync` / `apply_async` pair lives at
[orders-sets][orders-sets]; `one-sync-boundary` names that module, never this
file. Lazy resolution and gate firing are pure synchronous reads.

**3. Derived rather than repeated knowledge.** Every rendering composes its
owner by name: owner label via `_safe_class_name`, target rendering via
`_safe_type_name`, field rendering via `_safe_arg_repr` (all owned at
[exceptions][exceptions]); target resolution delegated to the mixin; gate base
via the single-sited F1 function. Nothing re-derives a field set from `_meta`,
rebuilds a name by concatenation, or recomputes a default. The slot-name
strings (`"_orderset"`, `"bound_orderset"`) are declared once as F2 params;
[orders-sets][orders-sets]' `should_cache_expansion(target_slot="_orderset")`
is a consumer that names the slot to query string-laziness (never reads a
class through it — no gate bypass), and test reads are oracles (C6).

**4. Inverse / round-trip pairs.** One pair, both halves in this file: the
`orderset` getter (resolve + validate + re-store via `_resolved_target`) and
setter (unvalidated store via `_set_target`). The validation asymmetry is
defined once at the mixin (`_set_target` docstring: deliberately unvalidated;
family-checked on the next read) — this file declares the family-named halves
(F2). String→class resolution is one-directional at the mixin. No other
encode/decode, pack/unpack, or build/parse surface.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (this file + the mixin machinery); authoritative
contract sources (spec-028 Decision 2 for the neutral-mixin home + collapsed
single-symbol port, Decision 3 Layers 1-2 for the acceptance shapes and
resolution discipline, Decision 8 for the queryset absence, the mixin
docstrings for the seam contracts); independent oracles (the 20 tests in
[test-order-base][test-order-base] spelling literals — class objects, import
paths, `"<unbound>"`, `"OrderSet subclass"` — plus the bind oracle in
[test-order-sets][test-order-sets], the `None`-skip oracle in
[test-order-inputs][test-order-inputs], and the live `orderBy:` walks over
[library-orders][library-orders]; none reads the gate body or the mixin to
compute expectations); projections (module/class docstrings, spec code blocks,
the GLOSSARY `RelatedOrder` entry). A new accepted reference shape moves the
mixin once; this file's docstring bullets and message parenthetical follow as
projections (C5/C8).

**6. Enforcement by omission.** Three deliberate order-side absences, each with
a contract source: no `lookups=` guard (no `lookups` parameter exists to guard
— the filter guard rejects a dead upstream kwarg; nothing to mirror); no
explicit-queryset intent and no `get_queryset` (spec-028 Decision 8: ordering
never re-derives child visibility querysets — R1); no lazy-mixin re-export
(the mixin home is [sets-mixins][sets-mixins]; filters re-exports for surface
continuity, orders never had that surface — F2 distinct behavior). Every read
of a resolved target routes through the gate: the four docstring-named
consumers (BFS enqueue via `_related_target_attr`, triples emission,
`normalize_input_value` recursion, permission-branch recursion) plus the
finalizer subpass-2 walk all read the `.orderset` property (verified by
`getattr` seam reads); the only direct `_orderset` production read is the
string-laziness check in the shared cache gate, which never consumes a class.
No member lacks a guard its contract requires.

### Enumeration

Instrument: `ast.parse` over the pinned HEAD blob, counting `ast.Module.body`
members — **7 top-level statements** — plus every member of the `RelatedOrder`
class body — **8 members** (docstring + 2 assigns + 5 defs). **9 named
rule-bearing members** in total. Every member lands below; every challenge in
`### Challenges` ends in a family row, a file-local row, a rejection, or a
verified no-surface routing.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (port notes + `field_name` relaxation + Decision 8 note) | (none) | prose projection, F2/F4 + D1 |
| 2 | `from __future__ import annotations` | (boilerplate) | — |
| 3 | `from typing import Any` | 1 name (annotation) | F3 annotation |
| 4 | `from ..exceptions import (...)` | 4 names (machinery) | F3 consumer rows |
| 5 | `from ..sets_mixins import RelatedSetTargetMixin` | 1 name (machinery) | F2 consumer row |
| 6 | `def _order_set_class` | 1 name | F1 + F1-nested rejection |
| 7 | `class RelatedOrder(RelatedSetTargetMixin)` | 1 name + 8 members | F2/F3/F4 + nested rejections, R1 |

| # | `RelatedOrder` member | Binds | Home |
|---|---|---|---|
| 7.1 | class docstring (acceptance shapes + gate rationale) | (none) | prose projection, F2/F3 |
| 7.2 | `_target_attr = "_orderset"` | slot-name param | F2 |
| 7.3 | `_owner_attr = "bound_orderset"` | slot-name param | F2 |
| 7.4 | `def __init__` (target store + `field_name` param) | 1 name | F2 (slot store) + F4 (shape) |
| 7.5 | `def bind_orderset` | 1 name | F2 |
| 7.6 | `def _validate_target` | 1 name | F3 + F3-nested rejection |
| 7.7 | `@property def orderset` (getter) | 1 name | F2 (round-trip half) |
| 7.8 | `@orderset.setter def orderset` | 1 name | F2 (round-trip half) |

Rules: R1 deferred order family base (statement 6); R2 lifecycle adapter
declarations (statements 5, 7.2–7.5, 7.7–7.8); R3 order target-type gate
(statements 3–4, 7.6); R4 `field_name` optional shape (statement 7.4). No NEW
family is named: every shared mechanism below already has its single-sited
owner (the mixin, the exceptions helpers, the cache gate), and every mirror
pair converges onto a verified separation on fresh evidence. Four file-local
index rows + four rejected index rows are named for Worker 0 (see
`## Index rows for Worker 0`).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed, never
counted. All bodies judged at HEAD bytes (the worktree dirt sits inside 7.6
only and changes no count — the HEAD gate shape is what is judged).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 rename | rename `OrderSet` → `DjangoOrderSet` | **1** (the F1 import; [types-base][types-base]'s validator import is a different responsibility — Meta-seam name consumption, listed not counted) | independent |
| C2 | R1 edge restructure | `orders.sets` stops importing `orders.base` at top (top import becomes safe) | **1 here** (the validator's `types→orders→types` edge is unaffected — opposite response proves distinct rules) | independent |
| C3 | R1 third family | an `AggregateSet` gate needs its base | **0 here** (new declaration; this file does not move) | independent — proves per-family base |
| C4 | R2 bind policy | first-bind-wins → last-bind-wins | **0 here, 1** at [sets-mixins][sets-mixins]`::_bind_owner` (both families' wrappers unchanged) | independent — proves single ownership |
| C5 | R2 reference shape | accept a new lazy shape (e.g. lazy object) | **0 here, 1** at `::resolve_lazy_class` (docstring bullets + message parentheticals follow as projections) | independent — proves single ownership |
| C6 | R2 slot rename | rename `_orderset` → `_target_orderset` | **1** (the 7.2 param; the [orders-sets][orders-sets] `target_slot=` consumer + test slot reads follow by name) | independent |
| C7 | R3 shape change | accept a new order-compatible target kind | **1 here** (the filter gate is a different family's rule — untouched) | independent |
| C8 | R3 reword | reword the order rejection message | **1 here** (filter message untouched); the shared parenthetical + `<unbound>` + owner-label line are per-family renderings of shared contracts (projections / display tokens), 0 rules | independent |
| C9 | R4 required | make `field_name` required positional (cookbook shape) | **1 here** (no filter counterpart — the filter side has no such parameter) | independent |
| C10 | `field-value-coercion` check | change literal→field-value mechanics | **0 here** (no import, no call, no `to_python`; leaf inputs are direction enums — DIVERGE, correctly absent) | no surface — do not inherit |
| C11 | `subsystem-clear-lifecycle` check | change the clear-bus contract | **0 here** (no registration, no ledger/cache/guard — DIVERGE as member, correctly absent) | no surface — do not inherit |
| C12 | boundary/seed checks | change `one-sync-boundary` / seed / recourse wording | **0 here** (no colored pair, no seed call, no recourse token — verified negatives) | no surface — do not inherit |

No executable proof was run: the target is a declaration + thin-wrapper +
single-predicate module whose every behavior is pinned by the 20 read oracles
in [test-order-base][test-order-base] plus the bind / `None`-skip / live
oracles, and every census above is a byte-level `git grep` over HEAD blobs or
an `ast.parse` enumeration — all read-only, none mutating, none capable of
distinguishing anything the cited oracles do not already pin. No
`docs/dry/temp-tests/` scratch was created. All claims below are therefore
`static-reviewed`; there is no `execution-deferred` proof.

## Findings

No production edit is owed by a file item; each finding records the rule with
the challenge that proved it has no second site.

### F1 — deferred order family base (file-local)

- **Contract + variation.** `_order_set_class()` returns the `OrderSet` family
  base for the R3 gate, importing it lazily so the `orders.sets →
  orders.base` module-load edge stays one-directional (`orders.sets` imports
  this module at module scope for the metaclass; a module-level import back
  would re-enter a partially-initialized `orders.sets`). Legitimate
  variation: the base identity only (one family, one base, one edge).
- **Sites + roles.** *Definition*: this file's statement 6. *Consumer*: 7.6
  (calls it per gated read — post-load, so the local import resolves
  cheaply). *Contract source*: spec-028 Decision 2 (subpackage layout) +
  the statement-6 docstring's cycle-keeping clause. *Projections*: the
  docstring's `types/base.py` cross-cite. No oracle pins the function
  directly; the four gate oracles pin it transitively (every rejection drove
  through the `issubclass` against its return).
- **Challenges.** C1 → 1 here; C2 → 1 here (validator edge unaffected); C3 →
  0 here.
- **Owner + lifetime.** This function (existing owner by responsibility: the
  narrowest site the gate can depend on without importing its sibling's
  machinery at module scope). No stored derivation; no lifetime fields owed.
- **Migration.** None (zero-edit item): single owner stands.
- **Distinct behavior.** The [types-base][types-base] `_validate_orderset_class`
  local import shares the deferral IDIOM, not the rule: different seam (Meta
  validation at `_validate_meta` time vs per-read gate base), different edge
  dodged (`types→orders→types` vs `orders.sets→orders.base`), opposite
  responses to edge restructures (C2). A global `OrderSet` rename moves both
  import statements, but that is name consumption across N package sites, not
  two definitions of one responsibility.
- **Behavioral proof.** `static-reviewed`. Rejects "the gate could import at
  module top" (verified: [orders-sets][orders-sets] imports this module at
  module scope, so the back-edge would re-enter it partially initialized)
  and "the validator call could replace this function" (different seam and
  timing; the validator returns validated Meta input, this returns the gate
  base).
- **Structural gate.** None owed: a one-call-site private helper with no
  plausible bypass (the only consumer is 7.6 in the same file; a second
  `OrderSet` import for gating purposes would be visible as a new import of
  `orders.sets` from this module, which the cycle forbids).
- **Coupling.** None.
- **Freshness.** Target HEAD `4736fda0228ee723aada11bfe374f81036ac4c30`
  (worktree `afd55efd65fa6fc2ac5a14865c3a040c5f560300` hunt dirt inside 7.6
  only — outside this finding's statement),
  `django_strawberry_framework/orders/sets.py` HEAD
  `6044ab1a11c77a42b715f0d0722fe7c9695064bc` (worktree `f09d9983…` hunt dirt
  in imports + `OrderSet` body — the module-top `RelatedOrder` import judged
  is the HEAD line), `django_strawberry_framework/types/base.py` HEAD
  `91c587477ff8257e80dbb9a9c79859f34c5b4c7e` (validator twins read),
  `django_strawberry_framework/filters/base.py` HEAD
  `ba52351c284425336262ae6c2b82b262f6586fc0` (clean; twin read),
  `tests/orders/test_base.py` HEAD
  `db14a99e878b5c502e2dddc1d9826435d6bfee9a` (worktree `dac87bf7…` hunt dirt —
  the judged gate oracles are the HEAD block),
  `docs/SPECS/spec-028-orders-0_0_8.md`
  `94a3141c02b92265779d8f3f7a2eefc019f765d8` (clean; Decision 2).
  Searched population for a second order-gate-base definition: whole package
  (every `OrderSet` import site is a consumer of the name, not of this edge).
- **Rejection (nested).** Considered: unify `_order_set_class` with the filter
  twin `_filter_set_class` into one shared deferred-base helper (same shape —
  the verified filters artifact rejected the same candidate as R1; compared
  fresh here, not inherited). Contract difference here: each function imports
  its OWN sibling `sets` module to keep its OWN load edge one-directional —
  one shared helper would couple the families through a single import site
  and close exactly the cycle each deferral exists to keep open (C3: a third
  family still declares its own). Different base, different edge, opposite
  reasons to change: same shape, not the same rule. CONVERGE with verified
  filters R1 on fresh evidence. Trigger to reconsider: the filter/order
  families merging into one set family, or both `sets` modules dropping their
  module-top `base` imports so neither edge needs deferring. Durable home:
  the statement-6 docstring (already states the edge) + this artifact. Named
  for Worker 0 as rejected index row `orders-deferred-base-vs-filter-twin`
  (no such row exists in the current plan).

### F2 — related-target lifecycle adapter declarations (file-local)

- **Contract + variation.** This file declares the order side of the shared
  lifecycle: the slot params (`_target_attr = "_orderset"`, `_owner_attr =
  "bound_orderset"`), the `__init__` target-slot store, and the family-named
  thin wrappers (`bind_orderset` over `_bind_owner`; `orderset` getter over
  `_resolved_target`; `orderset` setter over `_set_target`). All mechanics —
  idempotent bind, lazy string/callable resolution with module fallback,
  re-store-on-read, `None`-skip, setter-validated-on-next-read — are owned
  once at [sets-mixins][sets-mixins]`::RelatedSetTargetMixin` (+
  `::LazyRelatedClassMixin`). Legitimate variation: per-family slot names
  and wrapper spellings only.
- **Sites + roles.** *Machinery definitions*:
  [sets-mixins][sets-mixins]`::RelatedSetTargetMixin` (`_bind_owner`,
  `_resolved_target`, `_set_target`, abstract `_validate_target`) and
  `::LazyRelatedClassMixin::resolve_lazy_class`. *Parameter declarations*:
  this file's 7.2–7.3. *Wrapper declarations*: 7.5, 7.7–7.8 (+ the 7.4 slot
  store). *Sibling declarations*:
  [filters-base][filters-base]`::RelatedFilter` (different slots, same seam).
  *Metaclass consumer*: [orders-sets][orders-sets]`::OrderSetMetaclass` (binds
  via the shared `collect_related_declarations`). *Target consumers*: BFS
  enqueue, triples emission, `normalize_input_value` recursion, permission
  recursion, finalizer subpass 2 — all read 7.7 by name or `getattr`. *Cache
  consumer*: [orders-sets][orders-sets]' `should_cache_expansion` call (names
  the slot; never reads a class). *Oracles*: the bind-idempotency,
  class/absolute/unqualified/factory resolution, `ImportError`-passthrough,
  neutral-home, setter-storage, and `None`-placeholder tests — independent
  (they drive the property and spell literals, never read the mixin body).
  *Projections*: 7.1 acceptance-shape bullets, spec-028 Decision 3 Layers 1–2,
  GLOSSARY entry.
- **Challenges.** C4 → 0 here / 1 at the mixin; C5 → 0 here / 1 at the mixin;
  C6 → 1 here (consumers + oracles follow by name). The triple moves opposite
  sites under opposite changes: shared machinery, independent declarations.
- **Owner + lifetime.** The mixin owns the machinery (existing owner by
  responsibility: the neutral home Decision 2 mandates so sibling Layer-3
  packages never import each other); this file owns its slot params + wrapper
  spellings (principle 1 shape, already realized). No stored derivation
  beyond the per-instance slots, whose lifetime is the declaring instance
  (published at construction/bind, re-stored on first resolved read, never
  cleared — correctly outside `subsystem-clear-lifecycle`, C11).
- **Migration.** None (zero-edit item): the consolidation this shape invites
  landed with the neutral module; the families are declarations, not copies.
- **Distinct behavior.** Unlike [filters-base][filters-base], this file does
  NOT re-export `LazyRelatedClassMixin`: the mixin is composed by inheritance
  only. The filter re-export is surface continuity for that subsystem's
  public path; no contract requires the order leaf to carry it (verified: no
  in-tree consumer imports the mixin from `orders.base`), and a second
  re-export would be a second publication of one name, not a second
  definition of the rule. Observation (not a defect): 7.4's annotation spells
  `orderset: str | type`, excluding the `None` placeholder the 7.1 docstring
  blesses and the oracle pins — static-typing looseness only (runtime pinned;
  no contract row promises the annotation spells `None`), shared
  byte-identically with the filter twin's annotation.
- **Behavioral proof.** `static-reviewed`. Rejects "the wrappers duplicate the
  mixin" (each body is one delegation call; C4/C5 prove a machinery change
  touches one definition) and "a read can bypass the gate" (every production
  target read routes through 7.7; the only direct slot read is the shared
  cache gate's `isinstance(..., str)` check, which never consumes a class).
- **Structural gate.** The pre-existing oracles above (neutral-home pin,
  `ImportError`-passthrough pin, idempotency pin — no failability run owed by
  this zero-edit item); the abstract base `_validate_target` fails loud for a
  hookless future family by construction.
- **Coupling.** C6 couples to the [orders-sets][orders-sets] `target_slot=`
  keyword by slot-name; a slot rename moves that keyword in the same change.
  Named here so neither half lands alone.
- **Freshness.** Target HEAD `4736fda0…` (dirt as F1),
  `django_strawberry_framework/sets_mixins.py`
  `ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3` (clean; full mixin bodies),
  `django_strawberry_framework/filters/base.py` `ba52351c…` (clean; twin),
  `django_strawberry_framework/orders/sets.py` `6044ab1a…` (dirt as F1),
  `django_strawberry_framework/orders/inputs.py` HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (worktree `889b5971…` hunt dirt
  at the import block + `normalize_input_value` — outside the two `.orderset`
  read lines judged), `django_strawberry_framework/orders/factories.py`
  `4f35b66b06fe67e800ac43dabe8a1733b221168d` (clean; `_related_target_attr`),
  `django_strawberry_framework/utils/inputs.py` HEAD
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0` (worktree `47b2af21…` hunt dirt —
  the judged `getattr` seam is the HEAD line),
  `django_strawberry_framework/utils/permissions.py`
  `9889d6fe2a24a6e4f17325cbe3fc1955c0a18cec` (clean; `getattr` seams),
  `django_strawberry_framework/types/finalizer.py` HEAD
  `77fd9a2dd229eb9de5f29188c5058035d3606323` (subpass-2 walk read),
  `tests/orders/test_base.py` `db14a99e…` (dirt as F1),
  `tests/orders/test_inputs.py` HEAD
  `baf23440b8c1701b70b4c828e29c8eaf87626488` (`None`-force block read),
  `tests/orders/test_sets.py`
  `9e9bb5d980a546e530ec84d248a8ac5e80e5ee05` (clean; bind oracle),
  `docs/SPECS/spec-028-orders-0_0_8.md` `94a3141c…` (clean; Decisions 2–3).
  Searched population for a second lifecycle machinery definition:
  `resolve_lazy_class` / `_bind_owner` / `_resolved_target` / `_set_target`
  defined exactly once package-wide (the mixin); both families inherit.
- **Rejection (nested).** Considered: merge `RelatedOrder` with `RelatedFilter`
  into one shared related-declaration class (shared seam — same base,
  params, wrappers, gate slot). Contract difference here: different base
  classes (`RelatedSetTargetMixin` alone vs mixin + `ModelChoiceFilter` with
  its django-filter form machinery), different constructor contracts
  (`field_name` param vs `lookups=` guard + queryset intent), and
  mutually-absent members in both directions (`get_queryset` filter-only per
  Decision 8; `field_name` ctor param order-only). One class would need mode
  flags for which family it serves — the shape principle 5 forbids. Trigger
  to reconsider: the filter/order families merging into one set family.
  Durable home: spec-028 Decision 2 (neutral-machinery + per-family adapters)
  + the mixin docstring's adapter paragraph. Named for Worker 0 as rejected
  index row `orders-related-adapter-vs-filter-twin` (no such row exists in
  the current plan).

### F3 — order target-type gate (file-local)

- **Contract + variation.** 7.6 rejects every non-`None` resolved target that
  is not an `OrderSet` subclass (the cross-family `FilterSet`, a plain class,
  a factory returning a non-class) with a `ConfigurationError` naming the
  owning orderset (or `<unbound>`), the field, and the offending target. Fired
  by the mixin seam on every resolved read, so the mis-wiring detonates at
  first resolution instead of surviving to the BFS builder (`AttributeError`
  outside the subpass-2 rewrap, or a silent cross-family field walk).
  Legitimate variation: the order family's accepted base + rejection wording.
- **Sites + roles.** *Definition*: this file's 7.6 (predicate + rendering).
  *Firing seam*: [sets-mixins][sets-mixins]`::_resolved_target` (owns
  when-the-gate-fires + the `None`-skip; the predicate itself is the
  family-supplied hook). *Rendering helpers*: [exceptions][exceptions]
  `_safe_class_name` / `_safe_arg_repr` / `_safe_type_name` (composed by
  name). *Sibling definition*:
  [filters-base][filters-base]`::RelatedFilter._validate_target` (the
  FilterSet-only gate — a different family's rule, see nested rejection).
  *Oracles*: the four gate tests (plain class, `FilterSet` twin, bad factory,
  `<unbound>` owner) + the `ImportError`-preservation test pinning
  gate-after-resolution ordering — independent (they spell offending values
  and assert message fragments, never read the predicate). *Projection*: 7.1
  rationale paragraph + 7.6 docstring's consumer list.
- **Challenges.** C7 → 1 here (filter gate untouched); C8 → 1 here (filter
  message untouched). The pair moves opposite files under opposite changes:
  shared firing seam, independent family predicates.
- **Owner + lifetime.** This hook (existing owner by responsibility: the
  family-supplied gate the mixin seam calls; no narrower owner the seam's
  consumers could depend on exists). No stored derivation; no lifetime fields
  owed. A failed read leaves the slot resolved and re-raises on retry (mixin
  seam behavior, preserved from the pre-hook inline gates).
- **Migration.** None (zero-edit item): per-family hooks stand.
- **Distinct behavior.** The gate's shared fragments with its twin — the
  `(a class, an import-path string, or a zero-arg factory returning one)`
  parenthetical, the `<unbound>` token, the two-line owner-label derivation —
  are per-family RENDERINGS of shared contracts, not a separately-varying
  rule: the parenthetical renders the mixin's acceptance contract (a context
  projection, cf. the verified filters R4 treatment of message prefixes — it
  does not even state the full contract, omitting the `None` placeholder); the
  token + derivation render the unbound-owner state inside a message that must
  name its own family, twin, verb, and article. A shared message builder would
  parameterize more than it shares and re-couple the families for display
  text (principle 11). The third `<unbound>` site at
  [types-converters][types-converters] renders a different state (unreadable
  model in a field label, not an unbound declaration owner) — considered and
  distinct, no row.
- **Behavioral proof.** `static-reviewed`. Rejects "a `FilterSet` target could
  pass" (predicate requires `OrderSet` subclasshood; pinned by the twin
  oracle) and "an unresolvable string is preempted by the gate" (ordering
  pinned: resolution raises `ImportError` before the gate fires).
- **Structural gate.** The pre-existing gate oracles above (no failability run
  owed); the mixin seam guarantees every read fires the hook, so no bypass
  gate is needed — verified by the consumer census (all five production
  readers route through 7.7).
- **Coupling.** None.
- **Freshness.** Target HEAD `4736fda0…` (the judged body is the HEAD gate;
  worktree `afd55efd…` dirt adds guard arms + prose inside this finding's
  lines — concurrent-external, changes no count: the predicate, label
  derivation, and message skeleton judged are the HEAD bytes),
  `django_strawberry_framework/sets_mixins.py` `ad8987ea…` (clean; seam),
  `django_strawberry_framework/filters/base.py` `ba52351c…` (clean; twin
  gate read in full), `django_strawberry_framework/exceptions.py`
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` (clean; renderer surface),
  `django_strawberry_framework/types/converters.py`
  `9ceb34afec591a554fd71b7b3f3b9eae4f37fa75` (clean; third-token exclusion
  witness), `tests/orders/test_base.py` `db14a99e…` (dirt as F1).
  Searched population for a second order-target gate: `isinstance.*OrderSet`
  / `issubclass.*OrderSet` package-wide — every other hit validates a
  different seam (Meta sidecar, factory cache, `require_orderset_class`),
  never the related-target read.
- **Rejection (nested).** Considered: unify the two `_validate_target` gates
  into one shared family-parameterized gate (same predicate shape, same
  owner-label derivation, same message skeleton — the verified filters
  artifact rejected the same candidate as R2; compared fresh here, not
  inherited). Contract difference here: different accepted bases (`OrderSet`
  vs `FilterSet`), different named twins (each names the other as the
  rejected cross-family shape), different verbs and articles — the variation
  IS the message, and the shared fragments are projections of the mixin
  contract, not definitions (C7/C8 prove opposite change responses; a
  contract-shape change moves the mixin once, C5). Adapters by design, one
  per family, fired by the shared seam. CONVERGE with verified filters R2 on
  fresh evidence. Trigger to reconsider: the filter/order families merging
  into one set family, or a shared gate-message builder both families adopt.
  Durable home: the mixin docstring's family-hook paragraph (already states
  the hook shape) + this artifact. Named for Worker 0 as rejected index row
  `orders-target-gate-vs-filter-twin` (no such row exists in the current
  plan).

### F4 — `field_name` optional-`None` constructor shape (file-local)

- **Contract + variation.** 7.4 takes `field_name: str | None = None` (the
  cookbook's required positional, relaxed): the consumer declaration surface
  always passes one explicitly (verified: every `RelatedOrder(...)` site in
  [library-orders][library-orders] names `field_name=`), while a bare
  construction reads `None` and flows to the two readers that tolerate it —
  the input-triples fallback (`entry.field_name or top_name`) and the gate
  rendering (`_safe_arg_repr(None)`). Legitimate variation: the default and
  the parameter's existence only.
- **Sites + roles.** *Definition*: this file's 7.4 (+ the 7.1/store at 7.4
  body). *Readers*: [orders-inputs][orders-inputs] triples builder
  (`or top_name` fallback), 7.6 message rendering. *Oracles*: the default-`None`
  test + every declaration in [library-orders][library-orders] (explicit
  form) + the live `orderBy:` walks. No filter counterpart exists (the filter
  side has no such parameter — `field_name` there rides django-filter
  machinery and is rebased by expansion, a seam the order side has no
  equivalent of). *Projection*: module-docstring relaxation paragraph (whose
  stated reason is D1 below).
- **Challenges.** C9 → 1 here (no second site: the filter constructor takes
  no `field_name`; nothing else in the package declares an order-branch
  label).
- **Owner + lifetime.** This constructor (existing owner: the declaration
  shape lives where the declaration is built). Stored per instance at
  construction; never mutated afterwards (verified: zero post-construction
  assignment sites package-wide — the fact D1 turns on).
- **Migration.** None (zero-edit item).
- **Distinct behavior.** The `or top_name` fallback is what makes the `None`
  default load-bearing rather than vestigial: without it an omitted
  `field_name` would render a nameless branch. The fallback, not any
  metaclass step, is the relaxation's real consumer.
- **Behavioral proof.** `static-reviewed`. Rejects "omitting `field_name`
  breaks the branch" (fallback covers it; pinned by the default-`None` oracle
  resolving `.orderset` fine) and "the metaclass fills it" (no assignment
  site exists — see D1).
- **Structural gate.** The pre-existing default-`None` oracle (no failability
  run owed).
- **Coupling.** None.
- **Freshness.** Target HEAD `4736fda0…` (dirt as F1 — outside this finding's
  lines), `django_strawberry_framework/orders/inputs.py` `6f6ec946…` (dirt as
  F2 — outside the fallback line judged),
  `examples/fakeshop/apps/library/orders.py`
  `a4a8bcd68b2e3859775e637bd3bfc7187883c74f` (clean; declaration census),
  `tests/orders/test_base.py` `db14a99e…` (dirt as F1).
  Searched population for a post-construction `field_name` write:
  `.field_name =` package-wide — exactly one hit in this subsystem (the 7.4
  self-store); the filter-side rebasing hit is a different subsystem's rule.

### R1 — `get_queryset` absence is intentional separation (rejection)

- **Contract difference.** [filters-base][filters-base]`::RelatedFilter`
  carries `get_queryset` (target-model-derived branch queryset with
  explicit-queryset intent); this file carries no queryset surface at all
  (verified: zero `queryset` tokens). The absence is the contract, not a gap:
  spec-028 Decision 8 (ordering never re-derives child visibility querysets;
  resolvers run `get_queryset` visibility scoping BEFORE `apply_*`, and no
  symmetric `apply` dispatcher ships because the filter side's async-misuse
  path has no order equivalent). Different responsibilities, opposite
  reasons to change: posit queryset-derivation semantics changing → the
  filter member moves, this file does not. CONVERGE with verified filters R3
  on fresh evidence (that artifact's trigger stands: orders gaining
  querysets, for which no spec exists).
- **Trigger to reconsider.** A decision that ordering re-derives branch
  querysets (a `get_queryset` on `RelatedOrder` or its consumers).
- **Durable home.** Spec-028 Decision 8 (already states the no-queryset
  posture) + this artifact. Named for Worker 0 as rejected index row
  `orders-no-queryset-vs-filter-get-queryset` (no such row exists in the
  current plan).
- **Freshness.** Target HEAD `4736fda0…`,
  `django_strawberry_framework/filters/base.py` `ba52351c…` (clean; member
  read), `docs/SPECS/spec-028-orders-0_0_8.md` `94a3141c…` (clean; Decision
  8). Searched population: `get_queryset` / `queryset` / `base_queryset` /
  `model_for` tokens in the target — zero (axis-6 sweep complete, no missing
  guard).

## Defects

### D1 — module docstring names a `field_name` mutation that never happens (HEAD defect, clean lines — file for normal homing)

- **What.** The statement-1 paragraph claims the `field_name` relaxation
  exists "so the metaclass's collection step can mutate it later if needed".
  Verified against HEAD bodies: NOTHING in the order subsystem assigns
  `RelatedOrder.field_name` after construction — the package-wide
  `.field_name =` census finds exactly one hit in this subsystem (the 7.4
  self-store); `collect_related_declarations` binds the owner only, and
  `get_fields` / `_expand_meta_fields` never touch the attribute. The
  relaxation's real consumer is the [orders-inputs][orders-inputs] fallback
  (`entry.field_name or top_name`, F4), not any metaclass step. The sentence
  states the filter/upstream shape (where expansion does rebase `field_name`)
  as this file's reason — a wrong stated reason, which principle 10 ranks
  below none: the next author honors it and may rely on the metaclass filling
  `field_name`, which never happens.
- **Lines.** Statement-1 docstring lines — CLEAN at HEAD (the concurrent dirt
  sits inside 7.6 only, verified by the item diff). HEAD defect on clean
  lines → normal closeout homing, no conditional.
- **Owner.** `django_strawberry_framework/orders/base.py` module docstring
  (fix = restate the reason as the ergonomic relaxation + the triples
  `or top_name` fallback; prose-only, no behavior change).
- **Freshness.** Target HEAD `4736fda0228ee723aada11bfe374f81036ac4c30`;
  `django_strawberry_framework/orders/inputs.py` HEAD
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516` (fallback line);
  `django_strawberry_framework/sets_mixins.py`
  `ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3` (collect step binds owner only).
- **Not fixed.** File items never fix; recorded for Worker 0 to home on a
  NAMED owning card at closeout.

No other defects. Every remaining docstring claim checked held: the deferred
cycle-keeping clause (module-top back-import verified), the four acceptance
shapes (all four exercised by oracles), the gate-fires-at-read clause (four
gate oracles + ordering oracle), the one-seam consumer list (all five
production readers verified through 7.7), the idempotency clause (pinned),
the `None`-skip clause (pinned), the re-export omission (verified no consumer
needs it), and the "always supplies one explicitly" clause (verified across
every declaration in [library-orders][library-orders]).

## Pending execution

None. No `execution-deferred` proof: all claims are `static-reviewed` from
HEAD bytes (byte-level greps, `ast.parse` enumeration, full-body reads), every
target behavior is pinned by executed oracles on every suite run, and no
probe was created that could distinguish anything further. Sharded / Postgres
cells are inapplicable by construction: the target reaches no database, alias,
or dialect decision (pure declaration + lazy resolution + single predicate;
zero queryset tokens).

## Judgment

Zero-edit file item. Four rules traced, all file-local with proving challenges
(F1 deferred base, C1–C3; F2 adapter declarations, C4–C6; F3 target-type gate,
C7–C8; F4 `field_name` shape, C9), three nested rejections each converging
onto a verified filters separation on fresh evidence (F1→R1, F3→R2, plus the
twin-merge rejection), one standalone rejection converging onto verified
filters R3 (R1 queryset absence), and three indexed families checked fresh
with no surface (`field-value-coercion` and `subsystem-clear-lifecycle`
DIVERGE as membership per the task brief; `one-sync-boundary` et al via C12).
Enumeration covers 7/7 statements and 9/9 named members. One HEAD defect on
clean lines (D1 wrong-rationale prose) filed for normal homing. No pending
execution, no production edits.

## Implementation (Worker 1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped diff vs `ITEM_BASELINE=63400e65a067db4fdba632ac8b93538af218618a`:
`git diff <baseline> -- django_strawberry_framework/orders/base.py` is EMPTY
(exit 0, zero hunks) — the baseline captured the concurrent hunt hunk inside
7.6, and the worktree blob is still byte-identical to the dispatch record
(`afd55efd…`); the target was never edited, reverted, or worked around. The
artifact itself
(`docs/dry/dry-file-orders__base.md`) is a new untracked file, the item's only
output. No `uv run ruff` run (no `.py` edits; `.md` is outside ruff format
scope; no `.py` scratch created). No shared-tree pytest run (static-decidable
— see `### Challenges` note; the entry command authorizes a focused `--no-cov`
run only where it could settle a judgment, and here it could settle nothing).
No `docs/dry/temp-tests/` scratch created. HEAD confirmed `5ee86193` at start
and at artifact completion. Concurrent dirt (hunt edits across
`django_strawberry_framework/orders/`, `django_strawberry_framework/utils/`,
`tests/orders/`, `docs/dry/dry-0_0_15.md`) left untouched; the
`## Owned changes` ledger gains no row from this item. No commit.

## Index rows for Worker 0

Worker-0 instructions: (a) tick the plan item
`File orders/base.py — dry-file-orders__base.md` as verified under Run
`0.0.15 2026-09-22-5` once Worker 2 agrees; (b) add these eight
`## Responsibility index` rows verbatim (holding item `File orders/base.py`);
(c) home D1 on a NAMED owning card at closeout (HEAD defect, clean lines —
normal homing, no conditional). No `## Families` item: zero new families were
named (every shared mechanism already has its single-sited owner).

| `orders-deferred-family-base` | `django_strawberry_framework/orders/base.py::_order_set_class` | `django_strawberry_framework/orders/base.py` | File `orders/base.py` | file-local |
| `orders-related-target-adapter-declarations` | `django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin` (machinery; order owns its param + wrapper declarations at `django_strawberry_framework/orders/base.py::RelatedOrder`) | `django_strawberry_framework/orders/base.py` | File `orders/base.py` | file-local |
| `orders-related-target-type-gate` | `django_strawberry_framework/orders/base.py::RelatedOrder._validate_target` | `django_strawberry_framework/orders/base.py` | File `orders/base.py` | file-local |
| `orders-related-field-name-optional` | `django_strawberry_framework/orders/base.py::RelatedOrder.__init__` | `django_strawberry_framework/orders/base.py` | File `orders/base.py` | file-local |
| `orders-deferred-base-vs-filter-twin` | `django_strawberry_framework/orders/base.py::_order_set_class` (rejection recorded here; CONVERGE with verified filters/base R1 on fresh evidence) | `django_strawberry_framework/orders/base.py`, `django_strawberry_framework/filters/base.py` | File `orders/base.py` | rejected |
| `orders-related-adapter-vs-filter-twin` | `django_strawberry_framework/orders/base.py::RelatedOrder` (rejection recorded here) | `django_strawberry_framework/orders/base.py`, `django_strawberry_framework/filters/base.py` | File `orders/base.py` | rejected |
| `orders-target-gate-vs-filter-twin` | `django_strawberry_framework/orders/base.py::RelatedOrder._validate_target` (rejection recorded here; CONVERGE with verified filters/base R2 on fresh evidence) | `django_strawberry_framework/orders/base.py`, `django_strawberry_framework/filters/base.py` | File `orders/base.py` | rejected |
| `orders-no-queryset-vs-filter-get-queryset` | `django_strawberry_framework/orders/base.py` (rejection recorded here; CONVERGE with verified filters/base R3 on fresh evidence) | `django_strawberry_framework/orders/base.py`, `django_strawberry_framework/filters/base.py` | File `orders/base.py` | rejected |

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-filters-base]: dry-file-filters__base.md
[dry-orders-init]: dry-file-orders____init__.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-init]: ../../django_strawberry_framework/orders/__init__.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py

<!-- tests/ -->
[test-order-base]: ../../tests/orders/test_base.py
[test-order-inputs]: ../../tests/orders/test_inputs.py
[test-order-sets]: ../../tests/orders/test_sets.py

<!-- examples/ -->
[library-orders]: ../../examples/fakeshop/apps/library/orders.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

HEAD pin confirmed: `git rev-parse --short HEAD` = `5ee86193` at start and at
verdict (re-checked before signing). Target fingerprints (both taken myself):
HEAD blob `4736fda0228ee723aada11bfe374f81036ac4c30` (151 lines, governs);
worktree blob `afd55efd65fa6fc2ac5a14865c3a040c5f560300` (+21/-4 inside
`_validate_target`: guarded OrderSet-family interrogation with `except
BaseException` arms + `__class__`-guard prose) — concurrent hunt dirt, never
traced, never touched. All trace reads below are `git show HEAD:<path>`.

### Own trace (recorded before opening `## Findings`)

Instrument of my own: `ast.Module.body` of the HEAD bytes = 7 nodes
(docstring Expr, 4 `ImportFrom`, `FunctionDef _order_set_class`, `ClassDef
RelatedOrder`). Named rule/value members: `_order_set_class` +
`RelatedOrder` + 7 class-level members (2 `Assign`, `__init__`,
`bind_orderset`, `_validate_target`, `orderset` getter + setter).

| # | Member | Sites + roles | Definitions per posited change | Owner I would choose |
|---|---|---|---|---|
| 1 | `_order_set_class` | DEFINITION: deferred `OrderSet` loader breaking the `orders.sets -> orders.base` module-load edge. Single consumer: `RelatedOrder._validate_target`. Twin: `filters/base.py::_filter_set_class` (verified R1). Cross-ref: `types/base.py::_validate_orderset_class` local import (same technique, different edge) | Posit unifying the two loaders -> each imports its own sibling `sets`; a shared helper couples the families and erases the edge documentation: 1 per family. Posit `orders.sets` dropping its module-scope import -> only this one inlines: 1 | Stays in `orders/base.py` (the cycle edge is this module's); mirror of verified R1 |
| 2 | `_target_attr` / `_owner_attr` | DECLARATIONS (`"_orderset"` / `"bound_orderset"`) consumed by shared owner `sets_mixins.py::RelatedSetTargetMixin` | Posit renaming a slot -> declaration here (1), mechanics follow by construction (mixin reads `self._target_attr`): 1 + shared 1 | Correct as-is (principle 1/6) |
| 3 | `__init__(orderset, field_name=None)` | DEFINITION of the order-side constructor shape. `field_name` writers: only here (no `.field_name =` in `orders/sets.py`; metaclass never mutates at HEAD). Readers: `orders/inputs.py:257` (`entry.field_name or top_name`), gate message, oracles | Posit requiring `field_name` -> only this signature + oracles move: 1. Twin `RelatedFilter.__init__` is a different shape (ModelChoiceFilter-based); `django_filters.Filter` is upstream, out of population | Stays; file-local |
| 4 | `bind_orderset` | Thin CONSUMER-wrapper over shared `_bind_owner` (principle-5 adapter; family-named surface). Production callers: NONE — metaclass path calls `_bind_owner` directly via shared `collect_related_declarations` (verified). Callers: oracle `test_related_order_bind_orderset_is_idempotent` + external consumers | Posit changing bind policy -> `_bind_owner` only (1, in `sets_mixins.py`); 0 policy definitions here — the wrapper defines only the family-local name | Stays (principle 11: kept for the boundary name); file-local adapter |
| 5 | `_validate_target` | Family ADAPTER definition (OrderSet-membership gate), fired by shared `_resolved_target` (verified seam; `None` never reaches it). Twin: `RelatedFilter._validate_target` (verified R2). Package has exactly 3 `_validate_target` defs: base hook + 2 family adapters (swept) | Posit accepting a new orders target shape -> only this gate: 1. Posit changing firing position -> `_resolved_target` (1, shared) | Stays at the family class per the mixin hook contract; mirror of verified R2 |
| 6 | `orderset` getter + setter | Thin CONSUMERS of shared `_resolved_target` / `_set_target`. `.orderset` readers: `orders/inputs.py:255` (emission lambda), `orders/inputs.py:322` (runtime recursion), `types/finalizer.py:1724` (bind audit) | Posit changing resolution semantics -> shared seam only: 0 here | Stays (family vocabulary name); file-local |
| 7 | Module + member docstrings | PROJECTION (spec-028 pointers, cookbook port notes). Twin prose excluded per verified R6 | 0 (prose is not a definition) | None (out of population) |

Matrix, discharged by me against the real surface: (1) cross-flavor SEARCHED —
read the whole `RelatedFilter` cluster at HEAD; the four twin pairs separate
exactly where verified R1/R2/R3/R6 drew the lines; (2) sync/async INAPPLICABLE
with reason — no `async def`/`await` in target, sync-only primitive;
(3) derived knowledge SEARCHED — slot params compose by name, `field_name`
stored not derived, the `field_name or top_name` fallback is defined once at
its single consumer (`orders/inputs.py:257`); (4) round-trip SEARCHED —
getter/setter compose one seam (`_set_target` deliberately unvalidated,
validation-on-read documented at the owner); (5) other media SEARCHED —
oracles in `tests/orders/test_base.py` pin behavior without reading owner
internals; examples always pass explicit `field_name`; (6) omission
ENUMERATED — `RelatedSetTargetMixin` subclass family = {`RelatedFilter`,
`RelatedOrder`}, both supply the gate; the base raises `NotImplementedError`
(fail-loud, verified). No missing member.

Second-site hunt (the hard challenge on the file-local-only claim): deferred
loader (twin only — R1 separation stands: different bases/edges); lifecycle
adapters (mechanics already owned by `RelatedSetTargetMixin`; wrappers are
family vocabulary); target-type gate (R2 adapter separation); `field_name`
shape (no in-package second site; twin inherits from upstream). NOTHING I
found routes to a holding family. Zero-family claim survives my hunt.

### Reconciliation (after reading `## Findings`)

Window at verdict: `git diff --name-only ITEM_BASELINE --
django_strawberry_framework tests examples` names TWO out-of-scope paths
(`django_strawberry_framework/types/base.py`,
`tests/types/test_base.py`) — attributed by content to concurrent hunt
hardening (`_detect_custom_get_queryset` `__mro__`-read `except
BaseException` arm + `_RaisingMROMeta` companion oracles), not this item's
(zero tracked edits by either worker). No scope violation.

Enumeration: my 7 top-level statements + 9 named members == Worker 1's
7 + 9, member by member (F1: stmt 6; F2: stmts 5, 7.2-7.5, 7.7-7.8;
F3: stmts 3-4, 7.6; F4: 7.4; R1: absence). My trace rows 1-7 map 1:1
onto F1/F2/F4-adapter/F4-shape/F3/F2-halves/prose. Definition counts
agree on every challenge (C1-C9 match my posited changes; C10-C12
negatives re-verified by my own token census: zero
`async`/`await`/`queryset`/`coerce`/`clear`/`model_for`/`get_queryset`/`lookups`
in the HEAD target). Roles agree: the four gate/oracle/bind consumer
sets check out, and oracles spell literals without reading the owner.
Matrix: all six discharged against the real surface; each claimed
inapplicability/absence carries a token- or body-verified reason.
Rejections: all four carry contract difference + trigger + durable
home; the three CONVERGE rows re-derive (not inherit) verified
filters R1/R2/R3 with strictly stronger triggers. Freshness: all 18
cited HEAD blobs re-hashed by me, byte-exact (incl. target
`4736fda0…`, twin `ba52351c…`, mixin `ad8987ea…`, spec-028
`94a3141c…`). Pending execution: none; sharded/Postgres
inapplicable-by-construction reason judged sound (pure declaration +
lazy resolution + predicate). Prose: no process-provenance words (sole
`retry` hit is behavioral prose), `path::Symbol` citations throughout,
all 10 link-scaffold groups present, no tests created (correct — file
item). Ruff on the touched path (the `.md` artifact, lint-excluded):
`ruff format --check` passes, `ruff check` passes ("No Python files
found"). No probes under `docs/dry/temp-tests/` were needed (all
evidence is read-only HEAD-blob greps, rev-parses, and body reads);
no `$TMPDIR/dry-ws` copy was taken; nothing to remove.

D1 homing judgment (strict): CORRECTLY filed as HEAD defect on clean
lines for normal homing. (a) The sentence sits in statement 1; the
concurrent dirt is confined to 7.6 (verified by item diff), so the
lines are clean. (b) Falsity proved by the package-wide
`.field_name =` census = exactly {`orders/base.py:91` self-store,
`filters/sets.py:1111` filter rebase} — reproduced independently by
me. (c) Exact contract rows broken: F4's owner/lifetime row ("never
mutated afterwards") + principle 10 (a wrong stated reason ranks below
none; the sentence states the filter/upstream rebasing shape as this
file's reason). DRY.md "Defects found while tracing" names
docstring-contradicting-body as a defect class, so no wire input is
owed. Owner named, fix sketched prose-only. No Worker-2 defect filed.

Reconciled differences: (1) MY TRACE GAP, corrected by Worker 1 — I
first found no `.orderset` read on the permission/BFS paths; Worker 1
is right: the BFS reads via `getattr(related,
self._related_target_attr, None)` (`utils/inputs.py:1775`) with
`orders/factories.py:95 _related_target_attr = "orderset"`, and
permission recursion via `getattr(related_obj, target_attr, None)`
(`utils/permissions.py:635,745`) with `orders/sets.py:394
target_attr="orderset"` — all four lines re-verified by me at HEAD
bytes. All five production readers route through 7.7 as claimed; my
candidate defect is WITHDRAWN. (2) ON-RECORD PRECISION, no leverage:
F2 says the `None`-excluding annotation looseness is "shared
byte-identically with the filter twin's annotation" — the twin spells
`str | type[BaseFilterSet]` vs `str | type` here; shared is the
`None`-exclusion, not the bytes. Substance stands. (3) ON-RECORD
CENSUS, no leverage: "20 tests" in `tests/orders/test_base.py`
should read 22 (HEAD bytes; counted twice). No assignment impact.
(4) RELEASED, not filed: the `bind_orderset` rationale clause naming
`OrderSetMetaclass.__new__` states the shared idempotency contract's
purpose (real — the metaclass rebinds through the same body), not a
call edge; no contract row breaks.

File-local-only-claim judgment: TESTED HARD and SURVIVES. I hunted
second sites for all four dispatch-named shapes in the filters twin
and package-wide (whole-file twin read, `_validate_target` sweep = 3
defs, deferred-loader sweep = 1 caller each, `.field_name =` sweep,
`.orderset` + `getattr` seam census, `orders.base` importer sweep =
zero): every mirror pair separates where verified R1/R2/R3/R6 drew
the lines, and nothing routes to a holding family. The zero-family
verdict with 4 file-local + 4 rejected rows is correct.

### Verdict

`verified` (zero-edit; no pending execution; Worker 0 ticks the row,
transcribes the eight index rows verbatim, homes D1 on a NAMED owning
card at closeout).
